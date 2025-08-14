from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
import logging

from .models import (
    Grade, Student, Semester, AcademicYear, FeeStructure, 
    FeePayment, Programme, Enrollment, StudentNotification
)

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Grade)
def promote_student_on_grade_completion(sender, instance, created, **kwargs):
    """
    Signal to automatically promote students based on:
    1. Academic performance (max 2 failed units per year)
    2. Fee payment completion (except scholarship students)
    3. Programme structure (2 or 3 semesters per year)
    """
    if not created:
        return
    
    try:
        with transaction.atomic():
            student = instance.enrollment.student
            current_semester = instance.enrollment.semester
            
            # Only process if this is an active student
            if student.status != 'active':
                return
            
            # Check if student has completed all courses for current academic year
            if _has_completed_current_year(student, current_semester):
                _process_student_promotion(student, current_semester)
                
    except Exception as e:
        logger.error(f"Error in student promotion signal for student {instance.enrollment.student.student_id}: {str(e)}")


def _has_completed_current_year(student, current_semester):
    """
    Check if student has grades for all enrolled courses in the current academic year
    """
    current_year = student.current_year
    academic_year = current_semester.academic_year
    
    # Get all semesters for the current academic year based on programme structure
    year_semesters = Semester.objects.filter(
        academic_year=academic_year,
        semester_number__lte=student.programme.semesters_per_year
    )
    
    # Get all enrollments for current academic year
    enrollments = Enrollment.objects.filter(
        student=student,
        semester__in=year_semesters,
        is_active=True
    )
    
    # Check if all enrollments have grades
    for enrollment in enrollments:
        if not hasattr(enrollment, 'grade'):
            return False
    
    return len(enrollments) > 0


def _process_student_promotion(student, current_semester):
    """
    Main promotion logic
    """
    current_year = student.current_year
    current_academic_year = current_semester.academic_year
    programme = student.programme
    
    # Check academic eligibility
    failed_units = _count_failed_units_in_year(student, current_academic_year)
    
    # Check fee clearance
    fee_cleared = _check_fee_clearance(student, current_academic_year, current_year)
    
    # Determine if student can be promoted
    can_promote = failed_units <= 2 and fee_cleared
    
    if can_promote:
        _promote_student(student, current_semester)
        _create_promotion_notification(student, "promoted", current_year, failed_units)
    else:
        reasons = []
        if failed_units > 2:
            reasons.append(f"{failed_units} failed units")
        if not fee_cleared:
            reasons.append("outstanding fees")
        
        _create_promotion_notification(student, "not_promoted", current_year, failed_units, reasons)
        
        # Handle repeat students
        if failed_units > 2:
            _handle_repeat_student(student, current_semester, failed_units)


def _count_failed_units_in_year(student, academic_year):
    """
    Count failed units in the current academic year
    """
    year_semesters = Semester.objects.filter(
        academic_year=academic_year,
        semester_number__lte=student.programme.semesters_per_year
    )
    
    failed_grades = Grade.objects.filter(
        enrollment__student=student,
        enrollment__semester__in=year_semesters,
        is_passed=False,
        grade__in=['D+', 'D', 'F']  # Define failed grades
    )
    
    return failed_grades.count()


def _check_fee_clearance(student, academic_year, current_year):
    """
    Check if student has cleared fees for the academic year
    Exempt scholarship students from fee requirements
    """
    # Exempt scholarship students
    if student.sponsor_type in ['scholarship', 'bursary', 'government']:
        return True
    
    try:
        # Get fee structure for the year
        fee_structures = FeeStructure.objects.filter(
            programme=student.programme,
            academic_year=academic_year,
            year=current_year
        )
        
        total_required = sum(fs.net_fee() for fs in fee_structures)
        
        if total_required <= 0:  # No fees required
            return True
        
        # Calculate total payments made
        payments = FeePayment.objects.filter(
            student=student,
            fee_structure__in=fee_structures,
            payment_status='completed'
        )
        
        total_paid = sum(payment.amount_paid for payment in payments)
        
        # Allow small variance for rounding (KES 100)
        return total_paid >= (total_required - Decimal('100.00'))
        
    except Exception as e:
        logger.warning(f"Error checking fee clearance for student {student.student_id}: {str(e)}")
        return False


def _promote_student(student, current_semester):
    """
    Promote student to next year or semester
    """
    programme = student.programme
    current_year = student.current_year
    current_sem = student.current_semester
    
    # Determine next year and semester based on programme structure
    if current_sem < programme.semesters_per_year:
        # Move to next semester in same year
        new_year = current_year
        new_semester = current_sem + 1
    else:
        # Move to next year, first semester
        new_year = current_year + 1
        new_semester = 1
    
    # Check if student has reached maximum years for programme
    if new_year > programme.duration_years:
        # Student should graduate
        _handle_graduation_eligible(student)
        return
    
    # Update student's current year and semester
    student.current_year = new_year
    student.current_semester = new_semester
    student.save()
    
    # Auto-enroll in next semester's courses (if next semester exists)
    _auto_enroll_next_semester(student)
    
    logger.info(f"Promoted student {student.student_id} to Year {new_year}, Semester {new_semester}")


def _handle_repeat_student(student, current_semester, failed_units):
    """
    Handle students who need to repeat due to failed units
    """
    # Keep student in current year and semester
    # They will need to re-enroll in failed courses
    
    # Get failed courses for re-enrollment
    year_semesters = Semester.objects.filter(
        academic_year=current_semester.academic_year,
        semester_number__lte=student.programme.semesters_per_year
    )
    
    failed_enrollments = Enrollment.objects.filter(
        student=student,
        semester__in=year_semesters,
        grade__is_passed=False,
        grade__grade__in=['D+', 'D', 'F']
    )
    
    # Mark failed courses for repeat
    for enrollment in failed_enrollments:
        # Create repeat enrollment for next academic year
        next_academic_year = _get_next_academic_year(current_semester.academic_year)
        if next_academic_year:
            next_semester = Semester.objects.filter(
                academic_year=next_academic_year,
                semester_number=enrollment.semester.semester_number
            ).first()
            
            if next_semester:
                Enrollment.objects.get_or_create(
                    student=student,
                    course=enrollment.course,
                    semester=next_semester,
                    defaults={
                        'is_repeat': True,
                        'lecturer': enrollment.lecturer
                    }
                )
    
    logger.info(f"Student {student.student_id} marked for repeat due to {failed_units} failed units")


def _auto_enroll_next_semester(student):
    """
    Automatically enroll student in courses for next semester
    """
    try:
        # Get next academic year and semester
        next_academic_year = _get_next_academic_year_for_student(student)
        if not next_academic_year:
            return
        
        next_semester = Semester.objects.filter(
            academic_year=next_academic_year,
            semester_number=student.current_semester
        ).first()
        
        if not next_semester:
            return
        
        # Get programme courses for the student's current year and semester
        from .models import ProgrammeCourse
        programme_courses = ProgrammeCourse.objects.filter(
            programme=student.programme,
            year=student.current_year,
            semester=student.current_semester,
            is_active=True
        )
        
        # Enroll student in courses
        for pc in programme_courses:
            Enrollment.objects.get_or_create(
                student=student,
                course=pc.course,
                semester=next_semester,
                defaults={'is_active': True}
            )
        
        logger.info(f"Auto-enrolled student {student.student_id} in {programme_courses.count()} courses")
        
    except Exception as e:
        logger.error(f"Error in auto-enrollment for student {student.student_id}: {str(e)}")


def _handle_graduation_eligible(student):
    """
    Handle students who are eligible for graduation
    """
    # Update student status
    student.status = 'graduated'
    student.expected_graduation_date = timezone.now().date()
    student.save()
    
    _create_promotion_notification(
        student, 
        "graduation_eligible", 
        student.current_year, 
        0
    )
    
    logger.info(f"Student {student.student_id} marked as graduation eligible")


def _get_next_academic_year(current_academic_year):
    """
    Get the next academic year
    """
    try:
        return AcademicYear.objects.filter(
            start_date__gt=current_academic_year.end_date
        ).order_by('start_date').first()
    except:
        return None


def _get_next_academic_year_for_student(student):
    """
    Get next academic year for student enrollment
    """
    try:
        current_year = AcademicYear.objects.get(is_current=True)
        return _get_next_academic_year(current_year)
    except AcademicYear.DoesNotExist:
        return None


def _create_promotion_notification(student, notification_type, year, failed_units, reasons=None):
    """
    Create notification for student about promotion status
    """
    if notification_type == "promoted":
        title = f"Promoted to Year {student.current_year}"
        message = f"Congratulations! You have been promoted to Year {student.current_year}, Semester {student.current_semester}."
        if failed_units > 0:
            message += f" Note: You had {failed_units} failed unit(s) but can proceed with supplementary exams."
    
    elif notification_type == "not_promoted":
        title = f"Academic Progression Update - Year {year}"
        message = f"You have not been promoted due to: {', '.join(reasons)}."
        if failed_units > 2:
            message += f" You have {failed_units} failed units (maximum allowed: 2)."
        message += " Please contact the academic office for guidance."
    
    elif notification_type == "graduation_eligible":
        title = "Graduation Eligibility"
        message = "Congratulations! You have completed all requirements and are eligible for graduation. Please contact the registry for graduation procedures."
    
    try:
        StudentNotification.objects.create(
            student=student,
            title=title,
            message=message,
            notification_type='academic_progression'
        )
    except Exception as e:
        logger.error(f"Error creating notification for student {student.student_id}: {str(e)}")


# Additional utility signal for semester completion
@receiver(post_save, sender=Semester)
def check_semester_completion(sender, instance, created, **kwargs):
    """
    Check all students when a semester ends
    """
    if not created and not instance.is_current:
        # Semester has ended, check all active students
        active_students = Student.objects.filter(status='active')
        
        for student in active_students:
            if _has_completed_current_year(student, instance):
                _process_student_promotion(student, instance)