from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login , logout
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Student, Enrollment,  Semester, Grade
from decimal import Decimal
from .models import *
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse, HttpResponseForbidden
import json
from django.contrib.auth import get_user_model
User = get_user_model()

#student login view using student ID as username and password eg ( SC211/0540/2025)
""" This view logs in 3 user types student , lecturer and hostel warden """

def login_view(request):
    """Custom login view for students"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Redirect based on user_type
            if user.user_type == 'student':
                return redirect('student_dashboard')
            elif user.user_type == 'lecturer':
                return redirect('lecturer_dashboard')
            elif user.user_type == 'hostel_warden':
                return redirect('hostel_dashboard')
            else:
                messages.error(request, 'Unauthorized user type.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'student/auth/login.html')



def logout_view(request):
    logout(request)
    messages.success(request, "logged out sucessfully !")
    return redirect('login_view')  # This should match your login URL name


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime, timedelta
from .models import (
    Student, Semester, AcademicYear, Enrollment, 
    FeeStructure, FeePayment
)

@login_required
def student_dashboard(request):
    """Main dashboard for logged-in students"""
    if request.user.user_type != 'student':
        return redirect('login_view')
    
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Initialize variables
    current_enrollments = []
    is_on_holiday = False
    next_semester_date = None
    fee_balance = Decimal('0.00')
    
    # Check if student is on holiday (semester mismatch logic)
    if current_semester and student.programme.semesters_per_year >= current_semester.semester_number:
        # Student is in a valid semester period
        if student.current_semester != current_semester.semester_number:
            # Check if student is ahead (on holiday)
            if student.current_semester > current_semester.semester_number:
                is_on_holiday = True
                # Calculate approximate next semester start date
                next_semester_date = current_semester.end_date + timedelta(days=30)  # Approximate
                messages.info(
                    request, 
                    f"🌴 Happy holidays! Enjoy your break. The next semester is expected to start around {next_semester_date.strftime('%B %d, %Y')}."
                )
    
    # Get current semester enrollments (only if not on holiday)
    if not is_on_holiday and current_semester:
        current_enrollments = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('course')
    
    # Calculate fee balance for current semester and academic year
    if current_academic_year:
        # Get fee structure for current student's year, semester, and programme
        fee_structure = FeeStructure.objects.filter(
            programme=student.programme,
            academic_year=current_academic_year,
            year=student.current_year,
            semester=student.current_semester
        ).first()
        
        if fee_structure:
            # Calculate total fee required
            total_fee_required = fee_structure.net_fee()  # This includes subsidies
            
            # Calculate total payments made for this fee structure
            total_payments = FeePayment.objects.filter(
                student=student,
                fee_structure=fee_structure,
                payment_status='completed'
            ).aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal('0.00')
            
            # Calculate balance (negative means overpayment)
            fee_balance = total_fee_required - total_payments
        else:
            # No fee structure found - check if there are any payments
            # for current academic year and student's current semester
            fee_structures = FeeStructure.objects.filter(
                programme=student.programme,
                academic_year=current_academic_year,
                year=student.current_year
            )
            
            if fee_structures.exists():
                # Use the first available fee structure as fallback
                fee_structure = fee_structures.first()
                total_fee_required = fee_structure.net_fee()
                
                total_payments = FeePayment.objects.filter(
                    student=student,
                    fee_structure__in=fee_structures,
                    payment_status='completed'
                ).aggregate(
                    total=Sum('amount_paid')
                )['total'] or Decimal('0.00')
                
                fee_balance = total_fee_required - total_payments
    
    # Calculate semester progress
    total_semesters = student.programme.total_semesters
    completed_semesters = (student.current_year - 1) * student.programme.semesters_per_year + (student.current_semester - 1)
    progress_percentage = (completed_semesters / total_semesters) * 100 if total_semesters > 0 else 0
    
    # Add contextual message for fee balance
    if fee_balance == 0:
        fee_status_message = "✅ Fees fully paid for current semester"
        messages.success(request, fee_status_message)
    elif fee_balance < 0:
        overpayment = abs(fee_balance)
        fee_status_message = f"💰 You have an overpayment of KES {overpayment:,.2f}"
        messages.info(request, fee_status_message)
    else:
        fee_status_message = f"⚠️ Outstanding fee balance: KES {fee_balance:,.2f}"
        if fee_balance > 10000:  # High balance warning
            messages.warning(request, "Please settle your fee balance to avoid academic holds.")
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
        'current_enrollments': current_enrollments,
        'progress_percentage': round(progress_percentage, 1),
        'completed_semesters': completed_semesters,
        'total_semesters': total_semesters,
        'fee_balance': fee_balance,
        'is_on_holiday': is_on_holiday,
        'next_semester_date': next_semester_date,
        'total_enrolled_units': len(current_enrollments),
    }
    
    return render(request, 'student/dashboard.html', context)




@login_required
def student_profile(request):
    try:
        student = request.user.student_profile
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('login_view')  # or wherever you want to redirect
    
    if request.method == 'POST':
        # Handle AJAX profile picture upload
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'profile_picture' in request.FILES:
            try:
                request.user.profile_picture = request.FILES['profile_picture']
                request.user.save()
                return JsonResponse({'success': True, 'message': 'Profile picture updated successfully!'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error updating profile picture: {str(e)}'})
        
        # Handle profile picture upload (non-AJAX)
        if 'profile_picture' in request.FILES:
            try:
                request.user.profile_picture = request.FILES['profile_picture']
                request.user.save()
                messages.success(request, 'Profile picture updated successfully!')
                return redirect('student_profile')
            except Exception as e:
                messages.error(request, f'Error updating profile picture: {str(e)}')
                return redirect('student_profile')
        
        # Handle custom password change (allows any password)
        if 'current_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            # Check if current password is correct
            if not authenticate(username=request.user.username, password=current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('student_profile#Password')
            
            # Check if new passwords match
            if new_password1 != new_password2:
                messages.error(request, 'New passwords do not match.')
                return redirect('student_profile#Password')
            
            # Check if new password is not empty
            if not new_password1:
                messages.error(request, 'New password cannot be empty.')
                return redirect('student_profile#Password')
            
            # Set the new password (bypassing Django's default validators)
            try:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep user logged in
                messages.success(request, 'Password changed successfully!')
                return redirect('student_profile')
            except Exception as e:
                messages.error(request, f'Error changing password: {str(e)}')
                return redirect('student_profile#Password')
        
        # Handle profile updates
        try:
            # Update User model fields
            user_fields = {
                'first_name': request.POST.get('first_name', '').strip(),
                'last_name': request.POST.get('last_name', '').strip(),
                'email': request.POST.get('email', '').strip(),
                'phone': request.POST.get('phone', '').strip(),
                'address': request.POST.get('address', '').strip(),
            }
            
            # Only update fields that have values in the POST data
            for field, value in user_fields.items():
                if field in request.POST:
                    setattr(request.user, field, value)
            
            # Update Student model fields
            student_fields = {
                'guardian_name': request.POST.get('guardian_name', '').strip(),
                'guardian_phone': request.POST.get('guardian_phone', '').strip(),
                'guardian_relationship': request.POST.get('guardian_relationship', '').strip(),
                'guardian_address': request.POST.get('guardian_address', '').strip(),
                'emergency_contact': request.POST.get('emergency_contact', '').strip(),
                'blood_group': request.POST.get('blood_group', '').strip(),
                'medical_conditions': request.POST.get('medical_conditions', '').strip(),
            }
            
            # Only update fields that have values in the POST data
            for field, value in student_fields.items():
                if field in request.POST:
                    setattr(student, field, value)
            
            # Save both models
            request.user.save()
            student.save()
            messages.success(request, 'Profile updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('student_profile')
    
    # GET request - display the profile
    context = {
        'student': student,
    }
    return render(request, 'student/student_profile.html', context)



from django.utils import timezone
from django.db import transaction

from .models import Student, Semester, Course, ProgrammeCourse, Enrollment

from django.utils import timezone
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import JsonResponse

from .models import Student, Semester, Course, ProgrammeCourse, Enrollment

@login_required
def student_units_view(request):
    """
    View for student course enrollment, history, and curriculum display
    """
    # Get student profile
    try:
        student = Student.objects.select_related(
            'user', 'programme', 'programme__department', 'programme__faculty'
        ).get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Check if registration is open
    show_registration = False
    if current_semester:
        today = timezone.now().date()
        show_registration = (
            current_semester.registration_start_date <= today <= current_semester.registration_end_date
        )
    
    # Get ALL courses the student has ever enrolled in (across all semesters)
    all_enrolled_course_ids = Enrollment.objects.filter(
        student=student
    ).values_list('course_id', flat=True)
    
    # Get available courses for registration
    available_courses = []
    if show_registration and current_semester:
        # Get programme courses for student's current year and semester
        programme_courses = ProgrammeCourse.objects.select_related('course').filter(
            programme=student.programme,
            year=student.current_year,
            semester=student.current_semester,
            is_active=True,
            course__is_active=True
        )
        
        # Get already enrolled courses for current semester
        current_semester_enrolled_course_ids = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).values_list('course_id', flat=True)
        
        # Filter out courses already enrolled in current semester AND courses ever enrolled
        for programme_course in programme_courses:
            course = programme_course.course
            
            # Check if student has ever taken this course (across all semesters)
            has_ever_taken = course.id in all_enrolled_course_ids
            
            # Check if currently enrolled in this course this semester
            currently_enrolled = course.id in current_semester_enrolled_course_ids
            
            if not currently_enrolled:
                # Add course with information about previous enrollment
                course.previously_enrolled = has_ever_taken
                available_courses.append(course)
    
    # Get enrollment history (include both active and inactive enrollments)
    enrollments = Enrollment.objects.select_related(
        'course', 'semester', 'semester__academic_year', 'lecturer'
    ).filter(
        student=student
    ).order_by('-semester__academic_year__year', '-semester__semester_number', 'course__code')
    
    # Group enrollments by academic year and semester
    enrollment_history = {}
    for enrollment in enrollments:
        year_key = enrollment.semester.academic_year.year
        sem_key = f"Semester {enrollment.semester.semester_number}"
        
        if year_key not in enrollment_history:
            enrollment_history[year_key] = {}
        if sem_key not in enrollment_history[year_key]:
            enrollment_history[year_key][sem_key] = []
            
        enrollment_history[year_key][sem_key].append(enrollment)
    
    # Get complete curriculum
    curriculum_data = {}
    programme_courses = ProgrammeCourse.objects.select_related('course').filter(
        programme=student.programme,
        is_active=True,
        course__is_active=True
    ).order_by('year', 'semester', 'course__name')
    
    for programme_course in programme_courses:
        year_key = programme_course.year
        sem_key = f"Semester {programme_course.semester}"
        
        if year_key not in curriculum_data:
            curriculum_data[year_key] = {}
        if sem_key not in curriculum_data[year_key]:
            curriculum_data[year_key][sem_key] = []
            
        # Mark if student has taken this course (any semester)
        course = programme_course.course
        course.enrolled = course.id in all_enrolled_course_ids
        curriculum_data[year_key][sem_key].append(course)
    
    # Handle POST request for course enrollment
    if request.method == 'POST':
        return handle_course_enrollment(request, student, current_semester, available_courses, all_enrolled_course_ids)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'show_registration': show_registration,
        'available_units': available_courses,
        'enrollment_history': enrollment_history,
        'curriculum_data': curriculum_data,
        'all_enrolled_course_ids': list(all_enrolled_course_ids),
    }
    
    return render(request, 'student/units.html', context)


def handle_course_enrollment(request, student, current_semester, available_courses, all_enrolled_course_ids):
    """
    Handle course enrollment logic with duplicate prevention
    """
    if not current_semester:
        messages.error(request, 'No active semester found.')
        return redirect('student_units')
    
    # Check if registration is still open
    today = timezone.now().date()
    if not (current_semester.registration_start_date <= today <= current_semester.registration_end_date):
        messages.error(request, 'Registration period has ended.')
        return redirect('student_units')
    
    # Get selected course IDs
    selected_course_ids = request.POST.getlist('units')
    
    if not selected_course_ids:
        messages.error(request, 'Please select at least one course to register.')
        return redirect('student_units')
    
    # Validate selected courses
    valid_course_ids = [course.id for course in available_courses]
    invalid_selections = [course_id for course_id in selected_course_ids 
                         if int(course_id) not in valid_course_ids]
    
    if invalid_selections:
        messages.error(request, 'Some selected courses are not available for registration.')
        return redirect('student_units')
    
    # Check for prerequisite violations
    prerequisite_violations = []
    enrolled_courses = Enrollment.objects.filter(
        student=student,
        is_active=True
    ).values_list('course_id', flat=True)
    
    for course_id in selected_course_ids:
        try:
            course = Course.objects.get(id=course_id)
            missing_prerequisites = []
            
            for prerequisite in course.prerequisites.all():
                if prerequisite.id not in enrolled_courses:
                    missing_prerequisites.append(prerequisite.code)
            
            if missing_prerequisites:
                prerequisite_violations.append({
                    'course': course.code,
                    'missing': missing_prerequisites
                })
        except Course.DoesNotExist:
            continue
    
    if prerequisite_violations:
        violation_messages = []
        for violation in prerequisite_violations:
            violation_messages.append(
                f"{violation['course']}: Missing prerequisites {', '.join(violation['missing'])}"
            )
        messages.error(request, 'Prerequisite violations found: ' + '; '.join(violation_messages))
        return redirect('student_units')
    
    # Perform enrollment in a transaction
    try:
        with transaction.atomic():
            enrolled_count = 0
            failed_enrollments = []
            repeat_enrollments = []
            
            for course_id in selected_course_ids:
                try:
                    course = Course.objects.get(id=course_id)
                    
                    # Check if student has ever taken this course before (across all semesters)
                    previously_enrolled = int(course_id) in all_enrolled_course_ids
                    
                    # Check if already enrolled in current semester (double-check)
                    existing_enrollment = Enrollment.objects.filter(
                        student=student,
                        course=course,
                        semester=current_semester
                    ).first()
                    
                    if existing_enrollment:
                        if existing_enrollment.is_active:
                            failed_enrollments.append(f"{course.code} - Already enrolled this semester")
                        else:
                            # Reactivate inactive enrollment and mark as repeat if previously enrolled
                            existing_enrollment.is_active = True
                            existing_enrollment.is_repeat = previously_enrolled
                            existing_enrollment.enrollment_date = timezone.now().date()
                            existing_enrollment.save()
                            enrolled_count += 1
                            if previously_enrolled:
                                repeat_enrollments.append(course.code)
                    else:
                        # Create new enrollment and mark as repeat if previously enrolled
                        enrollment = Enrollment.objects.create(
                            student=student,
                            course=course,
                            semester=current_semester,
                            enrollment_date=timezone.now().date(),
                            is_active=True,
                            is_repeat=previously_enrolled
                        )
                        enrolled_count += 1
                        if previously_enrolled:
                            repeat_enrollments.append(course.code)
                        
                except Course.DoesNotExist:
                    failed_enrollments.append(f"Course ID {course_id} - Not found")
                except IntegrityError:
                    failed_enrollments.append(f"{course.code} - Duplicate enrollment detected")
                except Exception as e:
                    failed_enrollments.append(f"Course ID {course_id} - {str(e)}")
            
            # Provide feedback
            if enrolled_count > 0:
                success_message = f'Successfully enrolled in {enrolled_count} course{"s" if enrolled_count != 1 else ""}.'
                if repeat_enrollments:
                    success_message += f' Repeat courses: {", ".join(repeat_enrollments)}'
                messages.success(request, success_message)
            
            if failed_enrollments:
                messages.warning(
                    request, 
                    f'Failed enrollments: {"; ".join(failed_enrollments)}'
                )
            
            if enrolled_count == 0 and not failed_enrollments:
                messages.info(request, 'No new enrollments were processed.')
                
    except Exception as e:
        messages.error(request, f'Enrollment failed: {str(e)}')
    
    return redirect('student_units')


# Additional helper view for AJAX requests (optional)
@login_required
def check_prerequisites_ajax(request):
    """
    AJAX endpoint to check prerequisites for selected courses
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        student = Student.objects.get(user=request.user)
        course_ids = request.POST.getlist('course_ids')
        
        # Get student's completed/enrolled courses
        enrolled_courses = Enrollment.objects.filter(
            student=student,
            is_active=True
        ).values_list('course_id', flat=True)
        
        prerequisite_info = []
        
        for course_id in course_ids:
            try:
                course = Course.objects.get(id=course_id)
                missing_prerequisites = []
                
                for prerequisite in course.prerequisites.all():
                    if prerequisite.id not in enrolled_courses:
                        missing_prerequisites.append({
                            'code': prerequisite.code,
                            'name': prerequisite.name
                        })
                
                prerequisite_info.append({
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'missing_prerequisites': missing_prerequisites,
                    'can_enroll': len(missing_prerequisites) == 0
                })
                
            except Course.DoesNotExist:
                prerequisite_info.append({
                    'course_id': course_id,
                    'error': 'Course not found'
                })
        
        return JsonResponse({
            'success': True,
            'prerequisite_info': prerequisite_info
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# View for getting course details (optional)
@login_required
def course_details_ajax(request, course_id):
    """
    AJAX endpoint to get detailed course information
    """
    try:
        course = Course.objects.select_related('department').prefetch_related('prerequisites').get(
            id=course_id, 
            is_active=True
        )
        
        prerequisites = [
            {
                'id': prereq.id,
                'code': prereq.code,
                'name': prereq.name
            } for prereq in course.prerequisites.all()
        ]
        
        course_data = {
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'description': course.description,
            'credit_hours': course.credit_hours,
            'course_type': course.get_course_type_display(),
            'level': course.get_level_display(),
            'department': course.department.name if course.department else None,
            'prerequisites': prerequisites,
            'learning_outcomes': course.learning_outcomes,
            'assessment_methods': course.assessment_methods,
            'recommended_textbooks': course.recommended_textbooks,
        }
        
        return JsonResponse({
            'success': True,
            'course': course_data
        })
        
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Student, Semester, StudentReporting

@login_required
def student_reporting(request):
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    reports = StudentReporting.objects.filter(student=student).order_by('-reporting_date')
    
    # Check if student has already reported for current semester
    has_reported = False
    if current_semester:
        has_reported = StudentReporting.objects.filter(
            student=student,
            semester=current_semester
        ).exists()
    
    # Calculate student's current semester number (across all years)
    total_semesters_completed = StudentReporting.objects.filter(
        student=student, 
        status='approved'
    ).count()
    
    current_semester_number = total_semesters_completed + 1
    
    # Check if student can report to this semester based on programme limits
    can_report = True
    error_message = ""
    
    if current_semester:
        # Check if student has exceeded programme semester limit
        if current_semester_number > student.programme.total_semesters:
            can_report = False
            error_message = f"Cannot report. Your programme ({student.programme.name}) has a maximum of {student.programme.total_semesters} semesters."
        
        # Check if student is trying to report to a semester that doesn't match their programme structure
        programme_semesters_per_year = student.programme.semesters_per_year
        current_semester_in_year = (current_semester_number - 1) % programme_semesters_per_year + 1
        
        if current_semester.semester_number != current_semester_in_year:
            can_report = False
            error_message = f"Cannot report to Semester {current_semester.semester_number}. Your programme structure requires Semester {current_semester_in_year} at this stage."
    
    if request.method == 'POST':
        if not current_semester:
            messages.error(request, "No active semester found for reporting.")
            return redirect('student_dashboard')
        
        if has_reported:
            messages.error(request, f"You have already reported for {current_semester}.")
            return redirect('student_reporting')
        
        if not can_report:
            messages.error(request, error_message)
            return redirect('student_reporting')
        
        remarks = request.POST.get('remarks', '')
        
        try:
            # Create new reporting record
            StudentReporting.objects.create(
                student=student,
                semester=current_semester,
                reporting_type='online',
                remarks=remarks,
                status='approved'  # Auto-approve online reporting
            )
            
            messages.success(request, f"Successfully reported for {current_semester}!")
            return redirect('student_reporting')
            
        except Exception as e:
            messages.error(request, f"Error submitting report: {str(e)}")
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'reports': reports,
        'has_reported': has_reported,
        'can_report': can_report,
        'error_message': error_message,
        'current_semester_number': current_semester_number,
        'total_semesters_completed': total_semesters_completed,
        'programme_max_semesters': student.programme.total_semesters,
    }
    return render(request, 'student/student_reporting.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    Hostel, Room, Bed, HostelBooking, AcademicYear, 
    Semester, Student
)
import json


@login_required
def hostel_booking_eligibility(request):
    """Check if student is eligible for hostel booking"""
    try:
        student = request.user.student_profile
        
        # Check if student is in year 1
        if student.current_year != 1:
            messages.error(request, "Only first-year students are eligible for hostel booking.")
            return redirect('student_dashboard')
        
        # Check if student is active
        if student.status != 'active':
            messages.error(request, "Only active students can book hostels.")
            return redirect('student_dashboard')
        
        # Get current academic year
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_academic_year:
            messages.error(request, "No current academic year found.")
            return redirect('student_dashboard')
        
        # Check if student already has a booking for current academic year
        existing_booking = HostelBooking.objects.filter(
            student=student,
            academic_year=current_academic_year
        ).first()
        
        if existing_booking:
            messages.info(request, f"You already have a hostel booking for {current_academic_year.year}.")
            return redirect('hostel_booking_detail', booking_id=existing_booking.id)
        
        return redirect('hostel_list')
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def hostel_list(request):
    """Display available hostels based on student's gender"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        if not current_academic_year:
            messages.error(request, "No current academic year found.")
            return redirect('dashboard')
        
        # Determine hostel type based on student's gender
        if student.user.gender == 'male':
            hostel_type = 'boys'
        elif student.user.gender == 'female':
            hostel_type = 'girls'
        else:
            messages.error(request, "Please update your gender in profile to book hostel.")
            return redirect('student_profile')
        
        # Get active hostels for the student's school and gender
        hostels = Hostel.objects.filter(
            hostel_type=hostel_type,
            #school=student.programme.school,
            is_active=True
        )
        
        # Add availability information to each hostel
        hostel_data = []
        for hostel in hostels:
            total_beds = hostel.get_total_beds_count(current_academic_year)
            occupied_beds = hostel.get_occupied_beds_count(current_academic_year)
            available_beds = total_beds - occupied_beds
            
            hostel_data.append({
                'hostel': hostel,
                'total_beds': total_beds,
                'occupied_beds': occupied_beds,
                'available_beds': available_beds,
                'occupancy_rate': (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            })
        
        context = {
            'hostel_data': hostel_data,
            'student': student,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'hostels/hostel_list.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def room_list(request, hostel_id):
    """Display available rooms in selected hostel"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
        
        # Verify hostel matches student's gender and school
        hostel_type = 'boys' if student.user.gender == 'male' else 'girls'
        if hostel.hostel_type != hostel_type :
            messages.error(request, "You are not eligible for this hostel.")
            return redirect('hostel_list')
        
        # Get rooms with available beds
        rooms = Room.objects.filter(
            hostel=hostel,
            is_active=True
        ).order_by('floor', 'room_number')
        
        room_data = []
        for room in rooms:
            available_beds = room.get_available_beds_count(current_academic_year)
            occupied_beds = room.get_occupied_beds_count(current_academic_year)
            
            if available_beds > 0:  # Only show rooms with available beds
                room_data.append({
                    'room': room,
                    'available_beds': available_beds,
                    'occupied_beds': occupied_beds,
                    'total_capacity': room.capacity
                })
        
        context = {
            'hostel': hostel,
            'room_data': room_data,
            'student': student,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'hostels/room_list.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def bed_list(request, room_id):
    """Display available beds in selected room"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        room = get_object_or_404(Room, id=room_id, is_active=True)
        
        # Verify room's hostel matches student's eligibility
        hostel_type = 'boys' if student.user.gender == 'male' else 'girls'
        if (room.hostel.hostel_type != hostel_type ):
            messages.error(request, "You are not eligible for this room.")
            return redirect('hostel_list')
        
        # Get available beds
        available_beds = Bed.objects.filter(
            room=room,
            academic_year=current_academic_year,
            is_available=True,
            maintenance_status='good'
        ).order_by('bed_position')
        
        # Get occupied beds for display
        occupied_beds = Bed.objects.filter(
            room=room,
            academic_year=current_academic_year,
            is_available=False
        ).order_by('bed_position')
        
        context = {
            'room': room,
            'available_beds': available_beds,
            'occupied_beds': occupied_beds,
            'student': student,
            'academic_year': current_academic_year,
        }
        
        return render(request, 'hostels/bed_list.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def book_bed(request, bed_id):
    """Book a specific bed"""
    try:
        student = request.user.student_profile
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        bed = get_object_or_404(Bed, id=bed_id)
        
        # Verify bed eligibility
        hostel_type = 'boys' if student.user.gender == 'male' else 'girls'
        if (bed.room.hostel.hostel_type != hostel_type ):
            messages.error(request, "You are not eligible for this bed.")
            return redirect('hostel_list')
        
        # Check if bed is available
        if not bed.is_available or bed.maintenance_status != 'good':
            messages.error(request, "This bed is not available for booking.")
            return redirect('bed_list', room_id=bed.room.id)
        
        # Check if student already has a booking
        existing_booking = HostelBooking.objects.filter(
            student=student,
            academic_year=current_academic_year
        ).first()
        
        if existing_booking:
            messages.error(request, "You already have a hostel booking for this academic year.")
            return redirect('hostel_booking_detail', booking_id=existing_booking.id)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Create the booking
                    booking = HostelBooking.objects.create(
                        student=student,
                        bed=bed,
                        academic_year=current_academic_year,
                        booking_fee=5000.00,  # Default booking fee - you can make this configurable
                        booking_status='pending',
                        payment_status='pending'
                    )
                    
                    messages.success(request, f"Your hostel booking has been submitted successfully! Booking reference: {booking.id}")
                    return redirect('hostel_booking_detail', booking_id=booking.id)
                    
            except ValidationError as e:
                messages.error(request, f"Booking failed: {e}")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        
        context = {
            'bed': bed,
            'student': student,
            'academic_year': current_academic_year,
            'booking_fee': 5000.00,  # Make this configurable
        }
        
        return render(request, 'hostels/book_bed.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')


@login_required
def hostel_booking_detail(request, booking_id):
    """Display booking details"""
    try:
        student = request.user.student_profile
        booking = get_object_or_404(
            HostelBooking, 
            id=booking_id, 
            student=student
        )
        
        context = {
            'booking': booking,
            'student': student,
        }
        
        return render(request, 'hostels/booking_detail.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


@login_required
def cancel_booking(request, booking_id):
    """Cancel a hostel booking"""
    try:
        student = request.user.student_profile
        booking = get_object_or_404(
            HostelBooking, 
            id=booking_id, 
            student=student
        )
        
        # Only allow cancellation if booking is pending
        if booking.booking_status not in ['pending', 'approved']:
            messages.error(request, "This booking cannot be cancelled.")
            return redirect('hostel_booking_detail', booking_id=booking_id)
        
        if request.method == 'POST':
            booking.booking_status = 'cancelled'
            booking.save()
            messages.success(request, "Your hostel booking has been cancelled.")
            return redirect('hostel_list')
        
        context = {
            'booking': booking,
        }
        
        return render(request, 'hostels/cancel_booking.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')


# AJAX Views
@login_required
def get_rooms_ajax(request):
    """AJAX endpoint to get rooms for a hostel"""
    hostel_id = request.GET.get('hostel_id')
    if not hostel_id:
        return JsonResponse({'error': 'Hostel ID required'}, status=400)
    
    try:
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        rooms = Room.objects.filter(
            hostel_id=hostel_id,
            is_active=True
        ).order_by('floor', 'room_number')
        
        room_data = []
        for room in rooms:
            available_beds = room.get_available_beds_count(current_academic_year)
            if available_beds > 0:
                room_data.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'floor': room.floor,
                    'available_beds': available_beds,
                    'capacity': room.capacity
                })
        
        return JsonResponse({'rooms': room_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_beds_ajax(request):
    """AJAX endpoint to get beds for a room"""
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'error': 'Room ID required'}, status=400)
    
    try:
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        beds = Bed.objects.filter(
            room_id=room_id,
            academic_year=current_academic_year,
            is_available=True,
            maintenance_status='good'
        ).order_by('bed_position')
        
        bed_data = []
        for bed in beds:
            bed_data.append({
                'id': bed.id,
                'bed_number': bed.bed_number,
                'bed_position': bed.get_bed_position_display(),
                'maintenance_status': bed.get_maintenance_status_display()
            })
        
        return JsonResponse({'beds': bed_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def student_news(request):
    # Get all news articles, ordered by most recent first
    news_articles = NewsArticle.objects.filter(is_published=True).order_by('-publish_date')
    
    context = {
        'news_articles': news_articles,
        'featured_article': news_articles.first() if news_articles.exists() else None,
        'regular_articles': news_articles[1:4] if news_articles.count() > 1 else [],
        'older_articles': news_articles[4:] if news_articles.count() > 4 else []
    }
    return render(request, 'news/student_news.html', context)

from .models import Student, StudentComment
from .forms import StudentCommentForm

@login_required
def student_comments(request):
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        form = StudentCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.student = student
            comment.save()
            messages.success(request, 'Your comment has been submitted successfully!')
            return redirect('student_comments')
    else:
        form = StudentCommentForm()
    
    comments = StudentComment.objects.filter(student=student).order_by('-created_at')
    
    context = {
        'student': student,
        'form': form,
        'comments': comments,
    }
    return render(request, 'comments/comments.html', context)

@login_required
def faqs(request): 
    return render(request, 'settings/faqs.html')


from django.views.decorators.http import require_POST
import json
from .models import CommonQuestion, QuickLink

@login_required
def virtual_assistant(request):
    # Get the current user
    user = request.user
    
    # Fetch data from database models
    common_questions = CommonQuestion.objects.all()
    quick_links = QuickLink.objects.all()
    
    # Prepare context
    context = {
        'user': user,
        'common_questions': common_questions,
        'quick_links': quick_links,
    }
    
    return render(request, 'assistant/virtual_assistant.html', context)

@login_required
@require_POST
def process_assistant_query(request):
    try:
        data = json.loads(request.body)
        query = data.get('query', '').lower()
        
        # Simple response logic - would normally integrate with NLP/AI
        responses = {
            'results': 'Exam results are available on the student portal under "Academic Records".',
            'lecture': 'Lecture materials can be found on the LMS or by contacting your lecturer.',
            'hostel': 'Hostel applications open twice a year. Check the accommodation office for dates.',
            'fee': 'Fee payment can be made via MPesa or bank deposit. See the finance office for details.',
            'library': 'The library is open from 8am to 9pm weekdays, 9am to 4pm weekends.',
            'default': "I'm sorry, I didn't understand that. Could you rephrase your question?"
        }
        
        response_text = responses['default']
        for keyword in responses:
            if keyword in query and keyword != 'default':
                response_text = responses[keyword]
                break
        
        return JsonResponse({'response': response_text})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    


@login_required
def student_clubs(request):
    clubs = StudentClub.objects.filter(is_active=True).order_by('name')
    user_memberships = ClubMembership.objects.filter(student=request.user, is_active=True)
    
    # Create a dictionary to hold executive members for each club
    club_executives = {}
    for club in clubs:
        club_executives[club.id] = club.members.filter(is_executive=True)
    
    context = {
        'clubs': clubs,
        'user_memberships': user_memberships,
        'categories': dict(StudentClub.CATEGORY_CHOICES),
        'club_executives': club_executives
    }
    return render(request, 'clubs/student_clubs.html', context)


@login_required
def join_club(request, club_id):
    club = StudentClub.objects.get(id=club_id)
    if not ClubMembership.objects.filter(student=request.user, club=club).exists():
        ClubMembership.objects.create(student=request.user, club=club)
    return redirect('student_clubs')

@login_required
def leave_club(request, club_id):
    membership = ClubMembership.objects.filter(student=request.user, club_id=club_id).first()
    if membership:
        membership.delete()
    return redirect('student_clubs')


@login_required
def club_events(request, club_id=None):
    now = timezone.now()
    
    # Get events based on club_id or all clubs
    if club_id:
        club = StudentClub.objects.get(id=club_id)
        events = ClubEvent.objects.filter(club=club)
    else:
        club = None
        events = ClubEvent.objects.all()
    
    # Categorize events
    upcoming_events = events.filter(start_datetime__gt=now).order_by('start_datetime')
    latest_events = events.filter(start_datetime__lte=now, end_datetime__gte=now).order_by('start_datetime')
    past_events = events.filter(end_datetime__lt=now).order_by('-start_datetime')[:10]  # Last 10 past events
    
    context = {
        'club': club,
        'upcoming_events': upcoming_events,
        'latest_events': latest_events,
        'past_events': past_events,
    }
    
    return render(request, 'events/club_events.html', context)



@login_required
def student_events(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now(),
        is_public=True
    ).order_by('start_date')
    
    # Get registered events
    registered_events = EventRegistration.objects.filter(
        user=request.user
    ).select_related('event')
    
    context = {
        'student': student,
        'upcoming_events': upcoming_events,
        'registered_events': registered_events,
    }
    return render(request, 'student/events.html', context)

@login_required
def register_event(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        
        # Check if already registered
        if EventRegistration.objects.filter(user=request.user, event=event).exists():
            messages.error(request, 'You are already registered for this event')
        else:
            EventRegistration.objects.create(
                user=request.user,
                event=event
            )
            messages.success(request, 'Successfully registered for the event')
        
        return redirect('student_events')



from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect


from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login_view(request):
    """
    Admin login view with enhanced security and validation
    """
    # Redirect if already authenticated and is staff/admin
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')  # Replace with your admin dashboard URL
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('RememberMe') == 'on'
        
        # Basic validation
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'admin/admin_login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is admin/staff
            if user.is_staff or user.is_superuser:
                if user.is_active:
                    login(request, user)
                    
                    # Handle remember me functionality
                    if remember_me:
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)  # Browser close
                    
                    # Log successful login
                    logger.info(f"Admin login successful for user: {username}")
                    
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    
                    # Redirect to next page or dashboard
                    next_url = request.GET.get('next', 'admin_dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account has been deactivated. Please contact support.')
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                logger.warning(f"Non-admin user attempted admin login: {username}")
        else:
            messages.error(request, 'Invalid username or password.')
            logger.warning(f"Failed admin login attempt for username: {username}")
    
    return render(request, 'admin/admin_login.html')

@login_required
def admin_logout_view(request):
    """
    Admin logout view
    """
    username = request.user.username
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    logger.info(f"Admin logout for user: {username}")
    return redirect('admin_login')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q

from datetime import datetime, timedelta
import json
from django.utils import timezone
from .models import (
    User, Student, Lecturer, Staff, Faculty, Department, Programme, 
    Course, ProgrammeCourse, AcademicYear, Semester, Enrollment, 
    Grade, StudentReporting
)
from django.utils import timezone
from django.db.models import Avg
from django.contrib.auth import get_user_model

User = get_user_model()

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.user_type == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Admin dashboard with comprehensive statistics and charts
    """
    # Helper function to normalize datetime timezone awareness
    def normalize_datetime(dt):
        """Ensure datetime is timezone-aware"""
        if dt is None:
            return timezone.now()
        if timezone.is_naive(dt):
            return timezone.make_aware(dt)
        return dt
    
    def date_to_aware_datetime(date_obj):
        """Convert date to timezone-aware datetime"""
        if date_obj is None:
            return timezone.now()
        if isinstance(date_obj, datetime):
            return normalize_datetime(date_obj)
        # Convert date to datetime at start of day, then make timezone-aware
        dt = datetime.combine(date_obj, datetime.min.time())
        return timezone.make_aware(dt)
    
    # Get current date and academic year
    current_date = timezone.now().date()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Basic User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(created_at__date=current_date).count()
    
    # Student Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    new_students_today = Student.objects.filter(
        user__created_at__date=current_date
    ).count()
    
    # Faculty Statistics
    total_lecturers = Lecturer.objects.count()
    active_lecturers = Lecturer.objects.filter(is_active=True).count()
    
    # Staff Statistics
    total_staff = Staff.objects.count()
    active_staff = Staff.objects.filter(is_active=True).count()
    
    # Academic Overview
    total_faculties = Faculty.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    total_programmes = Programme.objects.filter(is_active=True).count()
    total_courses = Course.objects.filter(is_active=True).count()
    
    # Add these missing variables for the template
    total_schools = Faculty.objects.filter(is_active=True).count()  # Assuming Faculty = Schools
    total_units = Course.objects.filter(is_active=True).count()  # Assuming Course = Units
    active_placements = 0  # You'll need to define this based on your placement model
    completed_placements = 0  # You'll need to define this based on your placement model
    total_fee_payments = 0  # You'll need to define this based on your payment model
    today_fee_payments = 0  # You'll need to define this based on your payment model
    recent_payments = []  # You'll need to define this based on your payment model
    
    # Enrollment Statistics
    if current_semester:
        current_enrollments = Enrollment.objects.filter(
            semester=current_semester,
            is_active=True
        ).count()
        
        today_enrollments = Enrollment.objects.filter(
            enrollment_date=current_date,
            is_active=True
        ).count()
    else:
        current_enrollments = 0
        today_enrollments = 0
    
    # Gender Distribution Data for Donut Chart
    gender_data = Student.objects.filter(status='active').values(
        'user__gender'
    ).annotate(count=Count('id'))
    
    gender_chart_data = {
        'labels': [],
        'data': [],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56']
    }
    
    for item in gender_data:
        gender = item['user__gender']
        if gender == 'male':
            gender_chart_data['labels'].append('Male')
            gender_chart_data['data'].append(item['count'])
        elif gender == 'female':
            gender_chart_data['labels'].append('Female')
            gender_chart_data['data'].append(item['count'])
        elif gender == 'other':
            gender_chart_data['labels'].append('Other')
            gender_chart_data['data'].append(item['count'])
    
    # Student Admission Trends (Bar Chart) - Last 5 years
    current_year = current_date.year
    admission_years = []
    admission_counts = []
    
    for year in range(current_year - 4, current_year + 1):
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()
        count = Student.objects.filter(
            admission_date__range=[year_start, year_end]
        ).count()
        admission_years.append(str(year))
        admission_counts.append(count)
    
    admission_trend_data = {
        'labels': admission_years,
        'data': admission_counts
    }
    
    # FIXED: Student Enrollment by Programme (Horizontal Bar Chart)
    try:
        programme_enrollment = Programme.objects.filter(
            is_active=True
        ).annotate(
            student_count=Count('students', filter=Q(students__status='active'))
        ).order_by('-student_count')[:10]
        
        programme_chart_data = {
            'labels': [p.name[:25] + '...' if len(p.name) > 25 else p.name 
                      for p in programme_enrollment],
            'data': [p.student_count for p in programme_enrollment]
        }
        
        # Ensure we have data, if not provide default
        if not programme_chart_data['labels']:
            programme_chart_data = {
                'labels': ['No Data Available'],
                'data': [0]
            }
    except Exception as e:
        programme_chart_data = {
            'labels': ['No Data Available'],
            'data': [0]
        }
    
    # FIXED: Student Reporting in Last 6 Semesters
    try:
        last_6_semesters = Semester.objects.order_by('-academic_year__start_date', '-semester_number')[:6]
        reporting_data = []
        
        if last_6_semesters.exists():
            for semester in last_6_semesters:
                # Get total students who should report for this semester
                total_expected = Student.objects.filter(
                    status='active',
                    admission_date__lte=semester.end_date if hasattr(semester, 'end_date') else current_date
                ).count()
                
                # Get students who actually reported
                try:
                    reported = StudentReporting.objects.filter(
                        semester=semester,
                        status='approved'
                    ).count()
                except:
                    # If StudentReporting model doesn't exist or has different structure
                    # Use enrollment as a proxy for reporting
                    reported = Enrollment.objects.filter(
                        semester=semester,
                        is_active=True
                    ).count()
                
                reporting_data.append({
                    'semester': f"{semester.academic_year.year} S{semester.semester_number}",
                    'reported': reported,
                    'expected': total_expected,
                    'percentage': round((reported/total_expected * 100) if total_expected > 0 else 0, 1)
                })
        
        # Reverse to show chronologically
        reporting_data = list(reversed(reporting_data))
        
        reporting_chart_data = {
            'labels': [item['semester'] for item in reporting_data],
            'reported': [item['reported'] for item in reporting_data],
            'expected': [item['expected'] for item in reporting_data],
            'percentages': [item['percentage'] for item in reporting_data]
        }
        
        # Ensure we have data
        if not reporting_chart_data['labels']:
            reporting_chart_data = {
                'labels': ['No Data Available'],
                'reported': [0],
                'expected': [0],
                'percentages': [0]
            }
            
    except Exception as e:
        print(f"Error in reporting data: {e}")  # For debugging
        reporting_chart_data = {
            'labels': ['No Data Available'],
            'reported': [0],
            'expected': [0],
            'percentages': [0]
        }
    
    # Course Enrollment Trends (Last 12 months)
    twelve_months_ago = current_date - timedelta(days=365)
    try:
        monthly_enrollments = Enrollment.objects.filter(
            enrollment_date__gte=twelve_months_ago,
            is_active=True
        ).extra(
            select={'month': "strftime('%%Y-%%m', enrollment_date)"}
        ).values('month').annotate(
            enrollment_count=Count('id')
        ).order_by('month')
        
        enrollment_labels = []
        enrollment_counts = []
        
        for enrollment in monthly_enrollments:
            if enrollment['month']:  # Check if month is not None
                try:
                    month_year = datetime.strptime(enrollment['month'], '%Y-%m')
                    enrollment_labels.append(month_year.strftime('%b %Y'))
                    enrollment_counts.append(enrollment['enrollment_count'])
                except ValueError:
                    continue  # Skip invalid date formats
        
        enrollment_trend_data = {
            'labels': enrollment_labels,
            'data': enrollment_counts
        }
        
        # Ensure we have data
        if not enrollment_trend_data['labels']:
            enrollment_trend_data = {
                'labels': ['No Data Available'],
                'data': [0]
            }
    except Exception as e:
        enrollment_trend_data = {
            'labels': ['No Data Available'],
            'data': [0]
        }
    
    # Programme Performance (Average GPA by Programme)
    programme_performance = []
    for programme in Programme.objects.filter(is_active=True)[:10]:
        avg_gpa = Grade.objects.filter(
            enrollment__student__programme=programme,
            is_passed=True
        ).aggregate(avg_gpa=Avg('grade_points'))['avg_gpa']
        
        if avg_gpa:
            programme_performance.append({
                'programme': programme.name[:25] + '...' if len(programme.name) > 25 else programme.name,
                'avg_gpa': float(avg_gpa)
            })
    
    programme_performance.sort(key=lambda x: x['avg_gpa'], reverse=True)
    
    performance_chart_data = {
        'labels': [item['programme'] for item in programme_performance],
        'data': [item['avg_gpa'] for item in programme_performance]
    }
    
    # Department wise student distribution
    department_data = Department.objects.filter(is_active=True).annotate(
        student_count=Count('programmes__students', filter=Q(programmes__students__status='active'))
    ).order_by('-student_count')[:8]
    
    department_chart_data = {
        'labels': [dept.name[:20] + '...' if len(dept.name) > 20 else dept.name 
                  for dept in department_data],
        'data': [dept.student_count for dept in department_data]
    }
    
    # Programme type distribution
    programme_type_data = Programme.objects.filter(is_active=True).values(
        'programme_type'
    ).annotate(count=Count('id'))
    
    programme_type_chart_data = {
        'labels': [item['programme_type'].replace('_', ' ').title() for item in programme_type_data],
        'data': [item['count'] for item in programme_type_data],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    }
    
    # Recent Activities (Student Registrations, Enrollments, etc.) - ALL TIMEZONE-AWARE
    recent_activities = []
    
    # Recent student registrations
    recent_students = Student.objects.select_related('user', 'programme').order_by('-user__created_at')[:5]
    for student in recent_students:
        created_at = normalize_datetime(student.user.created_at)
        activity_date = created_at.date()
        
        recent_activities.append({
            'type': 'student_registration',
            'message': f"New student {student.user.get_full_name()} registered for {student.programme.name}",
            'date': activity_date,
            'datetime': created_at,  # timezone-aware
            'icon': 'fa-user-plus',
            'color': 'success'
        })
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.select_related(
        'student__user', 'course'
    ).order_by('-enrollment_date')[:5]
    for enrollment in recent_enrollments:
        # Convert enrollment date to timezone-aware datetime
        activity_datetime = date_to_aware_datetime(enrollment.enrollment_date)
        
        recent_activities.append({
            'type': 'course_enrollment',
            'message': f"{enrollment.student.user.get_full_name()} enrolled in {enrollment.course.name}",
            'date': enrollment.enrollment_date,
            'datetime': activity_datetime,  # timezone-aware
            'icon': 'fa-book',
            'color': 'info'
        })
    
    # Recent grade entries
    recent_grades = Grade.objects.select_related(
        'enrollment__student__user', 'enrollment__course'
    ).order_by('-id')[:5]
    current_datetime = timezone.now()  # already timezone-aware
    for grade in recent_grades:
        if grade.grade:
            recent_activities.append({
                'type': 'grade_entry',
                'message': f"Grade {grade.grade} recorded for {grade.enrollment.student.user.get_full_name()} in {grade.enrollment.course.code}",
                'date': current_datetime.date(),
                'datetime': current_datetime,  # timezone-aware
                'icon': 'fa-star',
                'color': 'warning'
            })
    
    # Sort activities by datetime (now all are consistently timezone-aware)
    try:
        recent_activities.sort(key=lambda x: x['datetime'], reverse=True)
        recent_activities = recent_activities[:10]
    except Exception as e:
        # If sorting still fails, just take first 10 without sorting
        recent_activities = recent_activities[:10]

    # Top Performing Students (by GPA)
    top_students = []
    try:
        active_students = Student.objects.filter(status='active').select_related('user')[:50]

        for student in active_students:
            avg_gpa = Grade.objects.filter(
                enrollment__student=student,
                is_passed=True
            ).aggregate(avg_gpa=Avg('grade_points'))['avg_gpa']
            
            if avg_gpa and avg_gpa > 0:
                top_students.append({
                    'student': student,
                    'gpa': round(float(avg_gpa), 2)  # Round to 2 decimal places
                })

        # Sort top students by GPA
        top_students.sort(key=lambda x: x['gpa'], reverse=True)
        top_students = top_students[:10]  # Limit to top 10
    except Exception as e:
        top_students = []
    
    # Grade distribution
    try:
        grade_distribution = Grade.objects.filter(
            grade__isnull=False
        ).exclude(grade__in=['I', 'W']).values('grade').annotate(
            count=Count('id')
        ).order_by('grade')
        
        grade_chart_data = {
            'labels': [item['grade'] for item in grade_distribution],
            'data': [item['count'] for item in grade_distribution]
        }
    except Exception as e:
        grade_chart_data = {
            'labels': [],
            'data': []
        }
    
    # User type distribution
    try:
        user_type_data = User.objects.filter(is_active=True).values(
            'user_type'
        ).annotate(count=Count('id'))
        
        user_type_chart_data = {
            'labels': [item['user_type'].replace('_', ' ').title() for item in user_type_data],
            'data': [item['count'] for item in user_type_data],
            'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#36A2EB']
        }
    except Exception as e:
        user_type_chart_data = {
            'labels': [],
            'data': [],
            'colors': []
        }
    
    context = {
        'current_date': current_date,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        
        # Basic Statistics
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'total_students': total_students,
        'active_students': active_students,
        'new_students_today': new_students_today,
        'total_lecturers': total_lecturers,
        'active_lecturers': active_lecturers,
        'total_staff': total_staff,
        'active_staff': active_staff,
        
        # Academic Overview
        'total_faculties': total_faculties,
        'total_departments': total_departments,
        'total_programmes': total_programmes,
        'total_courses': total_courses,
        'current_enrollments': current_enrollments,
        'today_enrollments': today_enrollments,
        
        # Missing template variables
        'total_schools': total_schools,
        'total_units': total_units,
        'active_placements': active_placements,
        'completed_placements': completed_placements,
        'total_fee_payments': total_fee_payments,
        'today_fee_payments': today_fee_payments,
        'recent_payments': recent_payments,
        
        # Chart Data (JSON)
        'gender_chart_data': json.dumps(gender_chart_data),
        'admission_trend_data': json.dumps(admission_trend_data),
        'programme_chart_data': json.dumps(programme_chart_data),
        'reporting_chart_data': json.dumps(reporting_chart_data),
        'enrollment_trend_data': json.dumps(enrollment_trend_data),
        'performance_chart_data': json.dumps(performance_chart_data),
        'department_chart_data': json.dumps(department_chart_data),
        'programme_type_chart_data': json.dumps(programme_type_chart_data),
        'grade_chart_data': json.dumps(grade_chart_data),
        'user_type_chart_data': json.dumps(user_type_chart_data),
        
        # Additional Data
        'recent_activities': recent_activities,
        'top_students': top_students,
        'programme_performance': programme_performance,
        'reporting_data': reporting_data,
    }
    
    return render(request, 'admin/dashboard.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

from django.views.decorators.http import require_http_methods
from .models import Student, Programme, Department, User
from django.urls import reverse


@login_required
def student_list(request):
    """
    Display a paginated list of students with search and filter functionality
    """
    # Get all students with related data to avoid N+1 queries
    students = Student.objects.select_related(
        'user', 'programme', 'programme__department'
    ).all()
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    programme_filter = request.GET.get('programme', '')
    school_filter = request.GET.get('department', '')
    year_filter = request.GET.get('year', '')
    semester_filter = request.GET.get('semester', '')
    admission_type_filter = request.GET.get('admission_type', '')
    sponsor_type_filter = request.GET.get('sponsor_type', '')
    
    # Apply search filter
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(programme__name__icontains=search_query) |
            Q(programme__code__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        students = students.filter(status=status_filter)
    
    # Apply programme filter
    if programme_filter:
        students = students.filter(programme_id=programme_filter)
    
    # Apply school filter
    if school_filter:
        students = students.filter(programme__school_id=school_filter)
    
    # Apply year filter
    if year_filter:
        students = students.filter(current_year=year_filter)
    
    # Apply semester filter
    if semester_filter:
        students = students.filter(current_semester=semester_filter)
    
    # Apply admission type filter
    if admission_type_filter:
        students = students.filter(admission_type=admission_type_filter)
    
    # Apply sponsor type filter
    if sponsor_type_filter:
        students = students.filter(sponsor_type=sponsor_type_filter)
    
    # Order students by registration number
    students = students.order_by('-admission_date', 'student_id')
    
    # Pagination
    paginator = Paginator(students, 20)  # Show 20 students per page
    page = request.GET.get('page', 1)
    
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    # Get data for filter dropdowns
    status_choices = Student.STATUS_CHOICES
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    schools = Department.objects.filter(is_active=True).order_by('name')
    admission_type_choices = Student.ADMISSION_TYPES
    sponsor_type_choices = Student.SPONSOR_TYPES
    
    # Year and semester choices (based on your model validators)
    year_choices = [(i, f'Year {i}') for i in range(1, 5)]  # 1-4 years
    semester_choices = [(i, f'Semester {i}') for i in range(1, 4)]  # 1-3 semesters
    
    context = {
        'students': students_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'programme_filter': programme_filter,
        'school_filter': school_filter,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'admission_type_filter': admission_type_filter,
        'sponsor_type_filter': sponsor_type_filter,
        
        # Filter options
        'status_choices': status_choices,
        'programmes': programmes,
        'schools': schools,
        'year_choices': year_choices,
        'semester_choices': semester_choices,
        'admission_type_choices': admission_type_choices,
        'sponsor_type_choices': sponsor_type_choices,
        
        # Statistics
        'total_students': students.count(),
        'active_students': Student.objects.filter(status='active').count(),
        'graduated_students': Student.objects.filter(status='graduated').count(),
    }
    
    return render(request, 'admin/students/student_list.html', context)


@login_required
def student_detail(request, student_id):
    """
    Display detailed information for a specific student
    """
    student = get_object_or_404(
        Student.objects.select_related(
            'user', 'programme', 'programme__department'
        ),
        student_id=student_id
    )
    
    context = {
        'student': student,
    }
    
    return render(request, 'admin/students/student_detail.html', context)


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import User, Student, Programme, Department
from .forms import UserForm, StudentForm


@login_required
def student_create(request):
    """
    Create a new student record
    """
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        student_form = StudentForm(request.POST)
        
        if user_form.is_valid() and student_form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = user_form.save(commit=False)
                    user.user_type = 'student'
                    
                    # Set password
                    password = user_form.cleaned_data.get('password')
                    if password:
                        user.password = make_password(password)
                    
                    user.save()
                    
                    # Create student profile
                    student = student_form.save(commit=False)
                    student.user = user
                    student.save()
                    
                    messages.success(request, f'Student {user.get_full_name()} created successfully!')
                    return redirect('student_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating student: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in student_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserForm()
        student_form = StudentForm()
    
    # Get data for form dropdowns
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    schools = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'action': 'Create',
        'programmes': programmes,
        'schools': schools,
        'status_choices': Student.STATUS_CHOICES,
        'admission_type_choices': Student.ADMISSION_TYPES,
        'sponsor_type_choices': Student.SPONSOR_TYPES,
        'gender_choices': User.GENDER_CHOICES,
    }
    
    return render(request, 'admin/students/student_form.html', context)


@login_required
def student_update(request, student_id):
    """
    Update an existing student record
    """
    student = get_object_or_404(Student, student_id=student_id)
    user = student.user
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=user, is_update=True)
        student_form = StudentForm(request.POST, instance=student)
        
        if user_form.is_valid() and student_form.is_valid():
            try:
                with transaction.atomic():
                    # Update user
                    user = user_form.save(commit=False)
                    
                    # Update password if provided
                    password = user_form.cleaned_data.get('password')
                    if password:
                        user.password = make_password(password)
                    
                    user.save()
                    
                    # Update student profile
                    student = student_form.save()
                    
                    messages.success(request, f'Student {user.get_full_name()} updated successfully!')
                    return redirect('student_detail', student_id=student_id)
                    
            except Exception as e:
                messages.error(request, f'Error updating student: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in student_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserForm(instance=user, is_update=True)
        student_form = StudentForm(instance=student)
    
    # Get data for form dropdowns
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    schools = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'student': student,
        'action': 'Update',
        'programmes': programmes,
        'schools': schools,
        'status_choices': Student.STATUS_CHOICES,
        'admission_type_choices': Student.ADMISSION_TYPES,
        'sponsor_type_choices': Student.SPONSOR_TYPES,
        'gender_choices': User.GENDER_CHOICES,
    }
    
    return render(request, 'admin/students/student_form.html', context)


@login_required
@require_http_methods(["POST"])
def student_delete(request, student_id):
    """
    Delete a student record
    """
    student = get_object_or_404(Student, student_id=student_id)
    
    try:
        student_name = student.user.get_full_name()
        student_reg_number = student.student_id
        
        # Delete the user account (this will cascade to delete student record)
        with transaction.atomic():
            student.user.delete()
        
        messages.success(request, f'Student {student_name} ({student_reg_number}) has been deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting student: {str(e)}')
    
    return redirect('student_list')


@login_required
def student_performance(request, student_id):
    """View specific student performance with all academic records"""
    
    # Get the student
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get all enrollments for this student
    enrollments = Enrollment.objects.filter(
        student=student
    ).select_related(
        'course', 'semester', 'semester__academic_year'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__start_date', 'semester__semester_number'
    )
    
    # Organize data by academic year and semester
    academic_data = []
    
    current_year = None
    current_semester = None
    year_data = None
    semester_data = None
    
    overall_stats = {
        'total_subjects': 0,
        'passed_subjects': 0,
        'failed_subjects': 0,
        'total_credits': 0,
        'earned_credits': 0,
        'overall_gpa': 0,
        'total_grade_points': 0
    }
    
    for enrollment in enrollments:
        academic_year = enrollment.semester.academic_year
        semester = enrollment.semester
        
        # Create new year data if needed
        if current_year != academic_year:
            if year_data:
                academic_data.append(year_data)
            year_data = {
                'academic_year': academic_year,
                'semesters': []
            }
            current_year = academic_year
            current_semester = None
        
        # Create new semester data if needed
        if current_semester != semester:
            if semester_data:
                # Calculate semester statistics
                total_subjects = len(semester_data['subjects'])
                passed_subjects = sum(1 for s in semester_data['subjects'] if s['is_passed'])
                failed_subjects = total_subjects - passed_subjects
                
                total_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'])
                earned_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'] if s['is_passed'])
                
                # Calculate GPA for semester
                total_grade_points = sum(
                    (s['grade_points'] or 0) * s['subject'].credit_hours 
                    for s in semester_data['subjects'] if s['grade_points'] is not None
                )
                semester_gpa = total_grade_points / total_credits if total_credits > 0 else 0
                
                semester_data['stats'] = {
                    'total_subjects': total_subjects,
                    'passed_subjects': passed_subjects,
                    'failed_subjects': failed_subjects,
                    'total_credits': total_credits,
                    'earned_credits': earned_credits,
                    'semester_gpa': round(semester_gpa, 2),
                    'total_grade_points': total_grade_points
                }
                
                year_data['semesters'].append(semester_data)
            
            semester_data = {
                'semester': semester,
                'subjects': [],
                'stats': {}
            }
            current_semester = semester
        
        # Get grade information
        grade_info = {
            'enrollment': enrollment,
            'subject': enrollment.course,
            'theory_marks': None,
            'practical_marks': None,
            'clinical_marks': None,
            'continuous_assessment': None,
            'final_exam_marks': None,
            'total_marks': None,
            'grade': None,
            'grade_points': None,
            'is_passed': False,
            'exam_date': None,
            'remarks': None
        }
        
        # Check if grade exists
        if hasattr(enrollment, 'grade'):
            grade = enrollment.grade
            grade_info.update({
                'theory_marks': grade.final_exam,
                'practical_marks': grade.practical_marks,
                'clinical_marks': grade.project_marks,
                'continuous_assessment': grade.continuous_assessment,
                'final_exam_marks': grade.final_exam,
                'total_marks': grade.total_marks,
                'grade': grade.grade,
                'grade_points': grade.grade_points,
                'is_passed': grade.is_passed,
                'exam_date': grade.exam_date,
                'remarks': grade.remarks
            })
        
        semester_data['subjects'].append(grade_info)
        
        # Add to overall statistics
        overall_stats['total_subjects'] += 1
        if grade_info['is_passed']:
            overall_stats['passed_subjects'] += 1
        else:
            overall_stats['failed_subjects'] += 1
        
        overall_stats['total_credits'] += enrollment.course.credit_hours
        if grade_info['is_passed']:
            overall_stats['earned_credits'] += enrollment.course.credit_hours
        
        if grade_info['grade_points'] is not None:
            overall_stats['total_grade_points'] += grade_info['grade_points'] * enrollment.course.credit_hours
    
    # Don't forget the last semester and year
    if semester_data:
        # Calculate final semester statistics
        total_subjects = len(semester_data['subjects'])
        passed_subjects = sum(1 for s in semester_data['subjects'] if s['is_passed'])
        failed_subjects = total_subjects - passed_subjects
        
        total_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'])
        earned_credits = sum(s['subject'].credit_hours for s in semester_data['subjects'] if s['is_passed'])
        
        total_grade_points = sum(
            (s['grade_points'] or 0) * s['subject'].credit_hours 
            for s in semester_data['subjects'] if s['grade_points'] is not None
        )
        semester_gpa = total_grade_points / total_credits if total_credits > 0 else 0
        
        semester_data['stats'] = {
            'total_subjects': total_subjects,
            'passed_subjects': passed_subjects,
            'failed_subjects': failed_subjects,
            'total_credits': total_credits,
            'earned_credits': earned_credits,
            'semester_gpa': round(semester_gpa, 2),
            'total_grade_points': total_grade_points
        }
        
        year_data['semesters'].append(semester_data)
    
    if year_data:
        academic_data.append(year_data)
    
    # Calculate overall GPA
    if overall_stats['total_credits'] > 0:
        overall_stats['overall_gpa'] = round(
            overall_stats['total_grade_points'] / overall_stats['total_credits'], 2
        )
    
    # Calculate completion percentage
    overall_stats['completion_percentage'] = round(
        (overall_stats['earned_credits'] / overall_stats['total_credits']) * 100, 2
    ) if overall_stats['total_credits'] > 0 else 0
    
    context = {
        'student': student,
        'academic_data': academic_data,
        'overall_stats': overall_stats,
        'programme': student.programme,
        'school': student.programme.department,
    }
    
    return render(request, 'admin/students/student_performance.html', context)


# AJAX view for dynamic filtering (optional)
@login_required
def get_programmes_by_school(request):
    """
    AJAX view to get programmes filtered by school
    """
    school_id = request.GET.get('school_id')
    programmes = Programme.objects.filter(
        school_id=school_id, is_active=True
    ).values('id', 'name', 'code').order_by('name')
    
    return JsonResponse(list(programmes), safe=False)


# marks_entry_view.py
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Student, Course, Enrollment, Grade, Semester, AcademicYear
from datetime import datetime
import json

def calculate_grade_and_points(total_marks):
    """
    Calculate grade, grade points, and pass status based on total marks
    Based on your Grade model's save method logic
    """
    if total_marks is None or total_marks == 0:
        return '', 0.0, False
    
    if total_marks >= 90:
        return 'A+', 4.0, True
    elif total_marks >= 80:
        return 'A', 4.0, True
    elif total_marks >= 75:
        return 'A-', 3.7, True
    elif total_marks >= 70:
        return 'B+', 3.3, True
    elif total_marks >= 65:
        return 'B', 3.0, True
    elif total_marks >= 60:
        return 'B-', 2.7, True
    elif total_marks >= 55:
        return 'C+', 2.3, True
    elif total_marks >= 50:
        return 'C', 2.0, True
    elif total_marks >= 45:
        return 'C-', 1.7, True
    elif total_marks >= 40:
        return 'D+', 1.3, False
    elif total_marks >= 35:
        return 'D', 1.0, False
    else:
        return 'F', 0.0, False

def calculate_total_marks(continuous_assessment, final_exam, practical_marks, project_marks):
    """
    Calculate total marks based on your Grade model logic
    CA (40%) + Final Exam (60%) + optional practical/project components
    """
    ca = continuous_assessment if continuous_assessment is not None else 0
    final_exam = final_exam if final_exam is not None else 0
    practical = practical_marks if practical_marks is not None else 0
    project = project_marks if project_marks is not None else 0
    
    # Base calculation: CA (40%) + Final Exam (60%)
    total = (ca * 0.4) + (final_exam * 0.6)
    
    # Add practical and project marks if applicable (10% each as per your model)
    if practical > 0:
        total += practical * 0.1
    if project > 0:
        total += project * 0.1
    
    return round(total, 2) if total > 0 else 0

@login_required
def admin_marks_entry(request, student_id=None):
    # Check if user is admin, lecturer, or registrar
    if request.user.user_type not in ['admin', 'lecturer', 'registrar']:
        return HttpResponseForbidden("Access denied. Authorized personnel only.")
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_academic_year or not current_semester:
        messages.error(request, "Please set current academic year and semester first.")
        return render(request, 'admin/admin_marks_entry.html', {'error': 'No current academic year/semester set'})
    
    student = None
    enrollments = []
    grades_data = {}
    
    # Handle student search - check both GET parameter and URL parameter
    search_student_id = student_id or request.GET.get('student_id')
    
    if search_student_id:
        try:
            student = Student.objects.get(student_id=search_student_id, status='active')
            
            # Get enrollments for current semester
            enrollments = Enrollment.objects.filter(
                student=student,
                semester=current_semester,
                is_active=True
            ).select_related('course', 'lecturer').order_by('course__code')
            
            # Get existing grades
            for enrollment in enrollments:
                try:
                    grade = Grade.objects.get(enrollment=enrollment)
                    grades_data[enrollment.id] = {
                        'continuous_assessment': float(grade.continuous_assessment) if grade.continuous_assessment else None,
                        'final_exam': float(grade.final_exam) if grade.final_exam else None,
                        'practical_marks': float(grade.practical_marks) if grade.practical_marks else None,
                        'project_marks': float(grade.project_marks) if grade.project_marks else None,
                        'total_marks': float(grade.total_marks) if grade.total_marks else None,
                        'grade': grade.grade,
                        'grade_points': float(grade.grade_points) if grade.grade_points else None,
                        'quality_points': float(grade.quality_points) if grade.quality_points else None,
                        'is_passed': grade.is_passed,
                        'exam_date': grade.exam_date.strftime('%Y-%m-%d') if grade.exam_date else '',
                        'remarks': grade.remarks or ''
                    }
                except Grade.DoesNotExist:
                    grades_data[enrollment.id] = {
                        'continuous_assessment': None,
                        'final_exam': None,
                        'practical_marks': None,
                        'project_marks': None,
                        'total_marks': None,
                        'grade': '',
                        'grade_points': None,
                        'quality_points': None,
                        'is_passed': False,
                        'exam_date': '',
                        'remarks': ''
                    }
            
        except Student.DoesNotExist:
            messages.error(request, f"Student with ID '{search_student_id}' not found or not active.")
    
    # Handle marks submission
    if request.method == 'POST' and 'save_marks' in request.POST:
        student_id_post = request.POST.get('student_id')
        if not student_id_post:
            messages.error(request, "Student ID is required.")
            return render(request, 'admin/admin_marks_entry.html', {})
        
        try:
            student = Student.objects.get(student_id=student_id_post, status='active')
            enrollments = Enrollment.objects.filter(
                student=student,
                semester=current_semester,
                is_active=True
            ).select_related('course')
            
            saved_count = 0
            
            with transaction.atomic():
                for enrollment in enrollments:
                    enrollment_id = str(enrollment.id)
                    
                    # Get form data
                    continuous_assessment = request.POST.get(f'continuous_assessment_{enrollment_id}')
                    final_exam = request.POST.get(f'final_exam_{enrollment_id}')
                    practical_marks = request.POST.get(f'practical_marks_{enrollment_id}')
                    project_marks = request.POST.get(f'project_marks_{enrollment_id}')
                    exam_date = request.POST.get(f'exam_date_{enrollment_id}')
                    remarks = request.POST.get(f'remarks_{enrollment_id}')
                    
                    # Convert to appropriate types with proper validation
                    def safe_float(value):
                        if value and value.strip():
                            try:
                                return float(value)
                            except ValueError:
                                return None
                        return None
                    
                    continuous_assessment = safe_float(continuous_assessment)
                    final_exam = safe_float(final_exam)
                    practical_marks = safe_float(practical_marks)
                    project_marks = safe_float(project_marks)
                    
                    # Validate mark ranges
                    def validate_mark_range(mark, max_value, field_name):
                        if mark is not None and (mark < 0 or mark > max_value):
                            raise ValidationError(f"{field_name} must be between 0 and {max_value}")
                    
                    try:
                        validate_mark_range(continuous_assessment, 100, "Continuous Assessment")
                        validate_mark_range(final_exam, 100, "Final exam marks")
                        validate_mark_range(practical_marks, 100, "Practical marks")
                        validate_mark_range(project_marks, 100, "Project marks")
                    except ValidationError as e:
                        messages.error(request, f"Validation error for course {enrollment.course.code}: {str(e)}")
                        continue
                    
                    # Handle exam date
                    exam_date_obj = None
                    if exam_date and exam_date.strip():
                        try:
                            exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
                        except ValueError:
                            pass  # Invalid date format, keep as None
                    
                    remarks = remarks.strip() if remarks else ''
                    
                    # Check if at least one mark is provided
                    has_marks = any([
                        continuous_assessment is not None,
                        final_exam is not None,
                        practical_marks is not None,
                        project_marks is not None
                    ])
                    
                    if has_marks:
                        # Create or update grade - let the model's save method handle calculations
                        grade_obj, created = Grade.objects.get_or_create(
                            enrollment=enrollment,
                            defaults={
                                'continuous_assessment': continuous_assessment,
                                'final_exam': final_exam,
                                'practical_marks': practical_marks,
                                'project_marks': project_marks,
                                'exam_date': exam_date_obj,
                                'remarks': remarks
                            }
                        )
                        
                        if not created:
                            # Update existing grade
                            grade_obj.continuous_assessment = continuous_assessment
                            grade_obj.final_exam = final_exam
                            grade_obj.practical_marks = practical_marks
                            grade_obj.project_marks = project_marks
                            grade_obj.exam_date = exam_date_obj
                            grade_obj.remarks = remarks
                            grade_obj.save()  # This will trigger the automatic calculations
                        
                        saved_count += 1
                
                if saved_count > 0:
                    messages.success(request, f"Marks saved successfully for {saved_count} courses for student {student.student_id}")
                    # Redirect to prevent re-submission  return redirect('student_performance', registration_number=registration_number)
                    return redirect('student_performance', student_id=student.student_id)
                else:
                    messages.warning(request, "No marks were provided to save.")
                
        except Student.DoesNotExist:
            messages.error(request, f"Student with ID '{student_id_post}' not found.")
        except Exception as e:
            messages.error(request, f"Error saving marks: {str(e)}")
            # For debugging - remove in production
            import traceback
            print(traceback.format_exc())
    
    # Get all active students for dropdown
    all_students = Student.objects.filter(status='active').select_related('user', 'programme').order_by('student_id')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'grades_data': grades_data,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'all_students': all_students,
    }
    
    return render(request, 'admin/admin_marks_entry.html', context)

@login_required
def get_student_info(request):
    """AJAX endpoint to get student information"""
    if request.user.user_type not in ['admin', 'lecturer', 'registrar']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({'error': 'Student ID required'}, status=400)
    
    try:
        student = Student.objects.get(student_id=student_id, status='active')
        current_semester = Semester.objects.filter(is_current=True).first()
        
        enrollments = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('course', 'lecturer')
        
        data = {
            'student': {
                'student_id': student.student_id,
                'name': student.user.get_full_name(),
                'programme': student.programme.name,
                'programme_code': student.programme.code,
                'current_year': student.current_year,
                'current_semester': student.current_semester,
                'department': student.programme.department.name,
                'faculty': student.programme.faculty.name,
            },
            'enrollments': [
                {
                    'id': enrollment.id,
                    'course_code': enrollment.course.code,
                    'course_name': enrollment.course.name,
                    'credit_hours': enrollment.course.credit_hours,
                    'lecture_hours': enrollment.course.lecture_hours,
                    'tutorial_hours': enrollment.course.tutorial_hours,
                    'practical_hours': enrollment.course.practical_hours,
                    'field_work_hours': enrollment.course.field_work_hours,
                    'course_type': enrollment.course.get_course_type_display(),
                    'level': enrollment.course.get_level_display(),
                    'lecturer': enrollment.lecturer.user.get_full_name() if enrollment.lecturer else 'Not Assigned',
                }
                for enrollment in enrollments
            ]
        }
        
        return JsonResponse(data)
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)

# Additional helper view for calculating GPA
@login_required
def calculate_student_gpa(request, student_id):
    """Calculate and update student's cumulative GPA"""
    if request.user.user_type not in ['admin', 'registrar']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        student = Student.objects.get(student_id=student_id, status='active')
        
        # Get all grades for the student
        grades = Grade.objects.filter(
            enrollment__student=student,
            enrollment__is_active=True,
            is_passed=True
        ).select_related('enrollment__course')
        
        total_quality_points = sum(grade.quality_points for grade in grades if grade.quality_points)
        total_credit_hours = sum(grade.enrollment.course.credit_hours for grade in grades)
        
        if total_credit_hours > 0:
            cumulative_gpa = total_quality_points / total_credit_hours
            student.cumulative_gpa = round(cumulative_gpa, 2)
            student.total_credit_hours = total_credit_hours
            student.save()
            
            return JsonResponse({
                'success': True,
                'cumulative_gpa': student.cumulative_gpa,
                'total_credit_hours': student.total_credit_hours
            })
        else:
            return JsonResponse({'error': 'No completed courses found'}, status=400)
            
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Avg, Sum, Count, Q
from collections import defaultdict
from decimal import Decimal
from .models import Student, Enrollment, Grade, AcademicYear, Semester

@login_required
def student_transcript(request, student_id=None):
    # Check if user is a student
    if not hasattr(request.user, 'student_profile'):
        return HttpResponseForbidden("Access denied. Students only.")
    
    student = request.user.student_profile

    # Get all enrollments for this student with related data
    enrollments = Enrollment.objects.filter(
        student=student,
        is_active=True
    ).select_related(
        'course',
        'semester',
        'semester__academic_year'
    ).prefetch_related(
        'grade'
    ).order_by('semester__academic_year__year', 'semester__semester_number', 'course__code')

    # Organize data by academic year and semester
    transcript_data = defaultdict(lambda: defaultdict(list))
    
    for enrollment in enrollments:
        year = enrollment.semester.academic_year.year
        semester_num = enrollment.semester.semester_number
        
        # Get grade information
        grade_info = None
        try:
            grade_info = enrollment.grade
        except Grade.DoesNotExist:
            pass
        
        # Calculate total marks
        total_marks = None
        if grade_info and grade_info.total_marks:
            total_marks = grade_info.total_marks
        elif grade_info:
            # Calculate from individual components if total_marks is not set
            marks = []
            if grade_info.theory_marks is not None:
                marks.append(grade_info.theory_marks)
            if grade_info.practical_marks is not None:
                marks.append(grade_info.practical_marks)
            if grade_info.clinical_marks is not None:
                marks.append(grade_info.clinical_marks)
            if grade_info.continuous_assessment is not None:
                marks.append(grade_info.continuous_assessment)
            if grade_info.final_exam_marks is not None:
                marks.append(grade_info.final_exam_marks)
            
            if marks:
                total_marks = sum(marks) / len(marks)
        
        subject_data = {
            'unit': enrollment.course,
            'enrollment': enrollment,
            'grade': grade_info,
            'theory_marks': grade_info.final_exam if grade_info else None,
            'practical_marks': grade_info.practical_marks if grade_info else None,
            'clinical_marks': grade_info.project_marks if grade_info else None,
            'continuous_assessment': grade_info.continuous_assessment if grade_info else None,
            'final_exam_marks': grade_info.total_marks if grade_info else None,
            'total_marks': total_marks,
            'grade_letter': grade_info.grade if grade_info else 'N/A',
            'grade_points': grade_info.grade_points if grade_info else None,
            'is_passed': grade_info.is_passed if grade_info else False,
            'status': 'Passed' if (grade_info and grade_info.is_passed) else 'Failed' if grade_info else 'Pending'
        }
        
        transcript_data[year][semester_num].append(subject_data)

    # Convert to regular dict and sort
    transcript_data = dict(transcript_data)
    for year in transcript_data:
        transcript_data[year] = dict(transcript_data[year])
        for semester in transcript_data[year]:
            transcript_data[year][semester].sort(key=lambda x: x['unit'].code)

    # Calculate GPA for each semester and overall
    semester_gpas = {}
    overall_credits = 0
    overall_grade_points = 0
    total_subjects = 0
    passed_subjects = 0
    
    for year in transcript_data:
        for semester_num in transcript_data[year]:
            semester_credits = 0
            semester_grade_points = 0
            
            for subject_data in transcript_data[year][semester_num]:
                total_subjects += 1
                if subject_data['is_passed']:
                    passed_subjects += 1
                    
                if subject_data['grade_points'] is not None:
                    credits = subject_data['unit'].credit_hours
                    grade_points = subject_data['grade_points']
                    
                    semester_credits += credits
                    semester_grade_points += (grade_points * credits)
                    
                    overall_credits += credits
                    overall_grade_points += (grade_points * credits)
            
            if semester_credits > 0:
                semester_gpa = semester_grade_points / semester_credits
                semester_gpas[f"{year}-{semester_num}"] = {
                    'gpa': round(semester_gpa, 2),
                    'credits': semester_credits
                }

    overall_gpa = round(overall_grade_points / overall_credits, 2) if overall_credits > 0 else 0
    
    # Calculate completion percentage based on programme requirements
    programme_units = student.programme.programme_courses.filter(is_active=True)
    total_programme_units = programme_units.count()
    completed_percentage = round((passed_subjects / total_programme_units) * 100, 1) if total_programme_units > 0 else 0
    
    # Determine academic standing
    if overall_gpa >= 3.5:
        academic_standing = "Excellent"
    elif overall_gpa >= 3.0:
        academic_standing = "Good"
    elif overall_gpa >= 2.5:
        academic_standing = "Satisfactory"
    elif overall_gpa >= 2.0:
        academic_standing = "Fair"
    else:
        academic_standing = "Poor"

    # Get academic year objects with their IDs for the dropdown
    academic_years_in_transcript = []
    for year_string in transcript_data.keys():
        try:
            # Find the academic year object by year string
            academic_year_obj = AcademicYear.objects.get(year=year_string)
            academic_years_in_transcript.append({
                'id': academic_year_obj.id,
                'year': year_string,
                'object': academic_year_obj
            })
        except AcademicYear.DoesNotExist:
            # If no exact match, you might need to handle this differently
            # depending on your AcademicYear model structure
            pass
    
    # Get all available academic years for the student
    available_years = AcademicYear.objects.filter(
        semesters__enrollments__student=student,
        semesters__enrollments__is_active=True
    ).distinct().order_by('-year')


    context = {
        'student': student,
        'transcript_data': transcript_data,
        'semester_gpas': semester_gpas,
        'overall_gpa': overall_gpa,
        'total_credits': overall_credits,
        'completed_percentage': completed_percentage,
        'academic_standing': academic_standing,
        'total_subjects': total_subjects,
        'passed_subjects': passed_subjects,

        'transcript_type': 'Complete Academic Transcript',
        'academic_year': None,
        'available_years': available_years,
        'academic_years_in_transcript': academic_years_in_transcript,  # New context variable
        'current_academic_year': AcademicYear.objects.filter(is_current=True).first(),
        'current_semester': Semester.objects.filter(is_current=True).first(),
        'generated_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
    }
    
    return render(request, 'student/student_transcript.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.db.models import Avg, Sum, Count, Q
from django.template.loader import get_template
from collections import defaultdict
from decimal import Decimal
import pdfkit
from django.conf import settings
import os
from .models import Student, Enrollment, Grade, AcademicYear, Semester

@login_required
def student_transcript_pdf(request, academic_year_id=None, semester_id=None):
    """
    Generate PDF transcript for student - either for specific semester or full academic year
    """
    # Check if user is a student
    if not hasattr(request.user, 'student_profile'):
        return HttpResponseForbidden("Access denied. Students only.")
    
    student = request.user.student_profile
    
    # Determine what to include in the transcript
    enrollments_filter = Q(student=student, is_active=True)
    
    if semester_id:
        # Specific semester transcript
        semester = get_object_or_404(Semester, id=semester_id)
        enrollments_filter &= Q(semester=semester)
        transcript_type = f"Semester {semester.semester_number}"
        academic_year = semester.academic_year
        pdf_filename = f"{student.student_id}_transcript_{semester.academic_year.year}_sem{semester.semester_number}.pdf"
    elif academic_year_id:
        # Full academic year transcript
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        enrollments_filter &= Q(semester__academic_year=academic_year)
        transcript_type = f"Academic Year {academic_year.year}"
        pdf_filename = f"{student.student_id}_transcript_{academic_year.year}.pdf"
    else:
        # Full transcript (all years)
        transcript_type = "Complete Academic Transcript"
        academic_year = None
        pdf_filename = f"{student.student_id}_complete_transcript.pdf"

    # Get enrollments based on filter
    enrollments = Enrollment.objects.filter(enrollments_filter).select_related(
        'course',
        'semester',
        'semester__academic_year',
        'lecturer'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__year', 
        'semester__semester_number', 
        'course__code'
    )

    if not enrollments.exists():
        return HttpResponse("No academic records found for the specified period.", status=404)

    # Organize data by academic year and semester
    transcript_data = defaultdict(lambda: defaultdict(list))
    
    for enrollment in enrollments:
        year = enrollment.semester.academic_year.year
        semester_num = enrollment.semester.semester_number
        
        # Get grade information
        grade_info = None
        try:
            grade_info = enrollment.grade
        except Grade.DoesNotExist:
            pass
        
        # Calculate total marks
        total_marks = None
        if grade_info and grade_info.total_marks:
            total_marks = grade_info.total_marks
        elif grade_info:
            # Calculate from individual components if total_marks is not set
            marks = []
            if grade_info.continuous_assessment is not None:
                marks.append(float(grade_info.continuous_assessment))
            if grade_info.final_exam is not None:
                marks.append(float(grade_info.final_exam))
            if grade_info.practical_marks is not None:
                marks.append(float(grade_info.practical_marks))
            if grade_info.project_marks is not None:
                marks.append(float(grade_info.project_marks))
            
            if marks:
                total_marks = sum(marks) / len(marks)
        
        subject_data = {
            'unit': enrollment.course,
            'enrollment': enrollment,
            'grade': grade_info,
            'continuous_assessment': grade_info.continuous_assessment if grade_info else None,
            'final_exam': grade_info.final_exam if grade_info else None,
            'practical_marks': grade_info.practical_marks if grade_info else None,
            'project_marks': grade_info.project_marks if grade_info else None,
            'total_marks': total_marks,
            'grade_letter': grade_info.grade if grade_info else 'N/A',
            'grade_points': grade_info.grade_points if grade_info else None,
            'quality_points': grade_info.quality_points if grade_info else None,
            'is_passed': grade_info.is_passed if grade_info else False,
            'status': 'Passed' if (grade_info and grade_info.is_passed) else 'Failed' if grade_info else 'Pending',
            'lecturer': enrollment.lecturer.user.get_full_name() if enrollment.lecturer else 'TBA'
        }
        
        transcript_data[year][semester_num].append(subject_data)

    # Convert to regular dict and sort
    transcript_data = dict(transcript_data)
    for year in transcript_data:
        transcript_data[year] = dict(transcript_data[year])
        for semester in transcript_data[year]:
            transcript_data[year][semester].sort(key=lambda x: x['unit'].code)

    # Calculate statistics
    semester_gpas = {}
    overall_credits = 0
    overall_grade_points = 0
    total_subjects = 0
    passed_subjects = 0
    total_quality_points = 0
    
    for year in transcript_data:
        for semester_num in transcript_data[year]:
            semester_credits = 0
            semester_quality_points = 0
            semester_subjects = 0
            semester_passed = 0
            
            for subject_data in transcript_data[year][semester_num]:
                total_subjects += 1
                semester_subjects += 1
                
                if subject_data['is_passed']:
                    passed_subjects += 1
                    semester_passed += 1
                    
                if subject_data['grade_points'] is not None and subject_data['quality_points'] is not None:
                    credits = subject_data['unit'].credit_hours
                    quality_points = float(subject_data['quality_points'])
                    
                    semester_credits += credits
                    semester_quality_points += quality_points
                    
                    overall_credits += credits
                    total_quality_points += quality_points
            
            if semester_credits > 0:
                semester_gpa = semester_quality_points / semester_credits
                semester_gpas[f"{year}-{semester_num}"] = {
                    'gpa': round(semester_gpa, 2),
                    'credits': semester_credits,
                    'subjects': semester_subjects,
                    'passed': semester_passed
                }

    overall_gpa = round(total_quality_points / overall_credits, 2) if overall_credits > 0 else 0
    
    # Calculate completion percentage
    programme_units = student.programme.programme_courses.filter(is_active=True)
    if semester_id:
        # For semester transcript, calculate based on that semester's expected units
        semester_obj = get_object_or_404(Semester, id=semester_id)
        expected_units = programme_units.filter(
            year=student.current_year,
            semester=semester_obj.semester_number
        ).count()
        completed_percentage = round((passed_subjects / expected_units) * 100, 1) if expected_units > 0 else 0
    else:
        total_programme_units = programme_units.count()
        completed_percentage = round((passed_subjects / total_programme_units) * 100, 1) if total_programme_units > 0 else 0
    
    # Determine academic standing
    if overall_gpa >= 3.5:
        academic_standing = "First Class Honours"
    elif overall_gpa >= 3.0:
        academic_standing = "Second Class Honours (Upper Division)"
    elif overall_gpa >= 2.5:
        academic_standing = "Second Class Honours (Lower Division)"
    elif overall_gpa >= 2.0:
        academic_standing = "Pass"
    else:
        academic_standing = "Fail"

    # Get university information (you might need to create a University model or use settings)
    university_info = {
        'name': getattr(settings, 'UNIVERSITY_NAME', 'MURANGA UNIVERSITY OF TECHNOLOGY'),
        'logo_url': getattr(settings, 'UNIVERSITY_LOGO_URL', '/static/logo.png'),
        'address': getattr(settings, 'UNIVERSITY_ADDRESS', '625 Kimathi Avenue, P.O. Box 45678, Nairobi, Kenya'),
        'phone': getattr(settings, 'UNIVERSITY_PHONE', '+254 757 790 877'),
        'email': getattr(settings, 'UNIVERSITY_EMAIL', 'info@murangauniversity.ac.ke'),
        'website': getattr(settings, 'UNIVERSITY_WEBSITE', 'www.murangauniversity.ac.ke'),
        'motto': getattr(settings, 'UNIVERSITY_MOTTO', 'Excellence in Education'),
    }

    context = {
        'student': student,
        'transcript_data': transcript_data,
        'semester_gpas': semester_gpas,
        'overall_gpa': overall_gpa,
        'total_credits': overall_credits,
        'completed_percentage': completed_percentage,
        'academic_standing': academic_standing,
        'total_subjects': total_subjects,
        'passed_subjects': passed_subjects,
        'transcript_type': transcript_type,
        'academic_year': academic_year,
        'university_info': university_info,
        'generated_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
    }
    
    # Render HTML template
    template = get_template('student/transcript_pdf.html')
    html = template.render(context)
    
    # Configure PDF options
    options = {
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None,
        'print-media-type': '',
        'disable-smart-shrinking': '',
        'zoom': '0.8',
    }
    
    try:
        # Generate PDF
        
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)
        pdf = pdfkit.from_string(html, False, options=options, configuration=config)
        
        # Create HTTP response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        
        return response
        
    except Exception as e:
        # Fallback: return HTML if PDF generation fails
        return HttpResponse(f"Error generating PDF: {str(e)}")


@login_required
def student_transcript_preview(request, academic_year_id=None, semester_id=None):
    """
    Preview the transcript before downloading (same logic as PDF but returns HTML)
    """
    # This uses the same logic as the PDF view but returns HTML for preview
    # You can reuse most of the code from student_transcript_pdf
    # Just return render instead of PDF generation
    pass

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.forms import ModelForm
from django import forms
import csv
from .forms import *
from .models import Lecturer, Department, Faculty, User

User = get_user_model()



# Views
@login_required
def lecturer_list(request):
    """List all lecturers with search, filter, and pagination"""
    lecturers = Lecturer.objects.select_related(
        'user', 'department', 'department__faculty'
    ).all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        lecturers = lecturers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(employee_number__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    # Filter by faculty
    faculty_filter = request.GET.get('faculty', '')
    if faculty_filter:
        lecturers = lecturers.filter(department__faculty_id=faculty_filter)
    
    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        lecturers = lecturers.filter(department_id=department_filter)
    
    # Filter by academic rank
    rank_filter = request.GET.get('academic_rank', '')
    if rank_filter:
        lecturers = lecturers.filter(academic_rank=rank_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        is_active = status_filter == 'active'
        lecturers = lecturers.filter(is_active=is_active)
    
    # Sorting
    order_by = request.GET.get('order_by', 'employee_number')
    if order_by:
        lecturers = lecturers.order_by(order_by)
    
    # Pagination
    paginator = Paginator(lecturers, 20)  # 20 lecturers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    faculties = Faculty.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'lecturers': page_obj,
        'page_obj': page_obj,
        'total_lecturers': lecturers.count(),
        'search_query': search_query,
        'faculty_filter': faculty_filter,
        'department_filter': department_filter,
        'rank_filter': rank_filter,
        'status_filter': status_filter,
        'order_by': order_by,
        'faculties': faculties,
        'departments': departments,
        'rank_choices': Lecturer.ACADEMIC_RANKS,
    }
    
    return render(request, 'lecturers/lecturer_list.html', context)

@login_required
def lecturer_create(request):
    """Create a new lecturer"""
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        lecturer_form = LecturerForm(request.POST)
        
        if user_form.is_valid() and lecturer_form.is_valid():
            try:
                # Create user
                user = user_form.save(commit=False)
                user.user_type = 'lecturer'
                
                # Set password if provided
                password = user_form.cleaned_data.get('password')
                if password:
                    user.set_password(password)
                else:
                    user.set_password('defaultpassword123')  # Set a default password
                
                user.save()
                
                # Create lecturer
                lecturer = lecturer_form.save(commit=False)
                lecturer.user = user
                lecturer.save()
                
                messages.success(request, f'Lecturer {user.get_full_name()} created successfully!')
                return redirect('lecturer_detail', employee_number=lecturer.employee_number)
                
            except Exception as e:
                messages.error(request, f'Error creating lecturer: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm()
        lecturer_form = LecturerForm()
    
    context = {
        'user_form': user_form,
        'lecturer_form': lecturer_form,
        'title': 'Add New Lecturer',
        'departments': Department.objects.filter(is_active=True),
    }
    
    return render(request, 'lecturers/lecturer_form.html', context)

@login_required
def lecturer_detail(request, employee_number):
    """View lecturer details"""
    lecturer = get_object_or_404(
        Lecturer.objects.select_related('user', 'department', 'department__faculty'),
        employee_number=employee_number
    )
    
    # Get lecturer's courses and enrollments
    enrollments = lecturer.enrollment_set.select_related(
        'course', 'semester', 'student'
    ).filter(is_active=True)[:10]  # Recent enrollments
    
    context = {
        'lecturer': lecturer,
        'enrollments': enrollments,
    }
    
    return render(request, 'lecturers/lecturer_detail.html', context)

@login_required
def lecturer_update(request, employee_number):
    """Update lecturer information"""
    lecturer = get_object_or_404(Lecturer, employee_number=employee_number)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES, instance=lecturer.user)
        lecturer_form = LecturerForm(request.POST, instance=lecturer)
        
        if user_form.is_valid() and lecturer_form.is_valid():
            try:
                # Update user
                user = user_form.save(commit=False)
                
                # Update password if provided
                password = user_form.cleaned_data.get('password')
                if password:
                    user.set_password(password)
                
                user.save()
                
                # Update lecturer
                lecturer_form.save()
                
                messages.success(request, f'Lecturer {user.get_full_name()} updated successfully!')
                return redirect('lecturer_detail', employee_number=lecturer.employee_number)
                
            except Exception as e:
                messages.error(request, f'Error updating lecturer: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=lecturer.user)
        lecturer_form = LecturerForm(instance=lecturer)
    
    context = {
        'user_form': user_form,
        'lecturer_form': lecturer_form,
        'lecturer': lecturer,
        'title': f'Edit Lecturer - {lecturer.user.get_full_name()}',
        'departments': Department.objects.filter(is_active=True),
    }
    
    return render(request, 'lecturers/lecturer_form.html', context)

@login_required
def lecturer_delete(request, employee_number):
    """Delete a lecturer"""
    lecturer = get_object_or_404(Lecturer, employee_number=employee_number)
    
    if request.method == 'POST':
        lecturer_name = lecturer.user.get_full_name()
        
        try:
            # Delete the user (cascade will delete lecturer)
            lecturer.user.delete()
            messages.success(request, f'Lecturer {lecturer_name} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting lecturer: {str(e)}')
    
    return redirect('lecturer_list')

@login_required
@require_POST
def lecturer_bulk_action(request):
    """Handle bulk actions for lecturers"""
    action = request.POST.get('action')
    lecturer_ids = request.POST.get('lecturer_ids', '').split(',')
    lecturer_ids = [id.strip() for id in lecturer_ids if id.strip()]
    
    if not action or not lecturer_ids:
        messages.error(request, 'Invalid action or no lecturers selected.')
        return redirect('lecturer_list')
    
    lecturers = Lecturer.objects.filter(employee_number__in=lecturer_ids)
    count = lecturers.count()
    
    try:
        if action == 'activate':
            lecturers.update(is_active=True)
            messages.success(request, f'{count} lecturer(s) activated successfully!')
            
        elif action == 'deactivate':
            lecturers.update(is_active=False)
            messages.success(request, f'{count} lecturer(s) deactivated successfully!')
            
        elif action == 'delete':
            # Delete users (cascade will delete lecturers)
            user_ids = lecturers.values_list('user_id', flat=True)
            User.objects.filter(id__in=user_ids).delete()
            messages.success(request, f'{count} lecturer(s) deleted successfully!')
            
        else:
            messages.error(request, 'Invalid action selected.')
            
    except Exception as e:
        messages.error(request, f'Error performing bulk action: {str(e)}')
    
    return redirect('lecturer_list')

@login_required
def lecturer_export(request):
    """Export lecturers to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lecturers.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Employee Number', 'First Name', 'Last Name', 'Email', 'Phone',
        'Department', 'Faculty', 'Academic Rank', 'Employment Type',
        'Joining Date', 'Highest Qualification', 'University Graduated',
        'Teaching Experience (Years)', 'Research Experience (Years)',
        'Office Location', 'Status'
    ])
    
    # Write data
    lecturers = Lecturer.objects.select_related(
        'user', 'department', 'department__faculty'
    ).all()
    
    for lecturer in lecturers:
        writer.writerow([
            lecturer.employee_number,
            lecturer.user.first_name,
            lecturer.user.last_name,
            lecturer.user.email,
            lecturer.user.phone,
            lecturer.department.name,
            lecturer.department.faculty.name,
            lecturer.get_academic_rank_display(),
            lecturer.get_employment_type_display(),
            lecturer.joining_date.strftime('%Y-%m-%d') if lecturer.joining_date else '',
            lecturer.highest_qualification,
            lecturer.university_graduated,
            lecturer.teaching_experience_years,
            lecturer.research_experience_years,
            lecturer.office_location,
            'Active' if lecturer.is_active else 'Inactive'
        ])
    
    return response

@login_required
@csrf_exempt
def lecturer_toggle_status(request, employee_number):
    """Toggle lecturer active status via AJAX"""
    if request.method == 'POST':
        try:
            lecturer = get_object_or_404(Lecturer, employee_number=employee_number)
            lecturer.is_active = not lecturer.is_active
            lecturer.save()
            
            return JsonResponse({
                'status': 'success',
                'is_active': lecturer.is_active,
                'message': f'Lecturer status updated to {"Active" if lecturer.is_active else "Inactive"}'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def get_departments_by_faculty(request):
    """Get departments filtered by faculty (AJAX endpoint)"""
    faculty_id = request.GET.get('faculty_id')
    departments = Department.objects.filter(
        faculty_id=faculty_id, is_active=True
    ).values('id', 'name', 'code')
    
    return JsonResponse({'departments': list(departments)})


# views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, Avg
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import (
    Programme, Course, ProgrammeCourse, Student, Enrollment, 
    Semester, AcademicYear, Faculty, Department
)

@login_required
def programme_list(request):
    """View to display all programmes with statistics"""
    programmes = Programme.objects.select_related(
        'department', 'faculty'
    ).prefetch_related(
        'students', 'programme_courses__course'
    ).filter(is_active=True)
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        programmes = programmes.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(faculty__name__icontains=search_query)
        )
    
    # Filter by faculty
    faculty_id = request.GET.get('faculty', '')
    if faculty_id:
        programmes = programmes.filter(faculty_id=faculty_id)
    
    # Filter by programme type
    programme_type = request.GET.get('programme_type', '')
    if programme_type:
        programmes = programmes.filter(programme_type=programme_type)
    
    # Add statistics for each programme
    programme_stats = []
    current_semester = Semester.objects.filter(is_current=True).first()
    
    for programme in programmes:
        total_courses = programme.programme_courses.filter(is_active=True).count()
        active_students = programme.students.filter(status='active').count()
        
        # Get enrolled students for current semester
        current_enrollments = 0
        if current_semester:
            current_enrollments = Enrollment.objects.filter(
                student__programme=programme,
                semester=current_semester,
                is_active=True
            ).values('student').distinct().count()
        
        programme_stats.append({
            'programme': programme,
            'total_courses': total_courses,
            'active_students': active_students,
            'current_enrollments': current_enrollments,
        })
    
    # Pagination
    paginator = Paginator(programme_stats, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    faculties = Faculty.objects.filter(is_active=True).order_by('name')
    programme_types = Programme.PROGRAMME_TYPES
    
    context = {
        'page_obj': page_obj,
        'faculties': faculties,
        'programme_types': programme_types,
        'search_query': search_query,
        'selected_faculty': faculty_id,
        'selected_programme_type': programme_type,
        'current_semester': current_semester,
    }
    
    return render(request, 'programmes/programme_list.html', context)


@login_required
def programme_detail(request, programme_id):
    """View to display programme details with courses organized by year and semester"""
    programme = get_object_or_404(
        Programme.objects.select_related('department', 'faculty'),
        id=programme_id,
        is_active=True
    )
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all programme courses organized by year and semester
    programme_courses = ProgrammeCourse.objects.select_related(
        'course', 'course__department'
    ).filter(
        programme=programme,
        is_active=True
    ).order_by('year', 'semester', 'course__name')
    
    # Organize courses by year and semester
    courses_by_year = {}
    years = []
    
    for pc in programme_courses:
        year = pc.year
        semester = pc.semester
        
        if year not in years:
            years.append(year)
        
        if year not in courses_by_year:
            courses_by_year[year] = {}
        
        if semester not in courses_by_year[year]:
            courses_by_year[year][semester] = []
        
        # Get enrollment count for current semester
        enrollment_count = 0
        if current_semester:
            enrollment_count = Enrollment.objects.filter(
                course=pc.course,
                semester=current_semester,
                student__programme=programme,
                is_active=True
            ).count()
        
        course_data = {
            'course': pc.course,
            'programme_course': pc,
            'enrollment_count': enrollment_count,
        }
        
        courses_by_year[year][semester].append(course_data)
    
    # Calculate programme statistics
    programme_stats = {
        'total_courses': programme_courses.count(),
        'total_credits': sum(pc.course.credit_hours for pc in programme_courses),
        'total_lecture_hours': sum(pc.course.lecture_hours for pc in programme_courses),
        'total_practical_hours': sum(pc.course.practical_hours for pc in programme_courses),
        'core_courses': programme_courses.filter(is_mandatory=True).count(),
        'elective_courses': programme_courses.filter(is_mandatory=False).count(),
        'active_students': programme.students.filter(status='active').count(),
    }
    
    context = {
        'programme': programme,
        'courses_by_year': courses_by_year,
        'years': sorted(years),
        'programme_stats': programme_stats,
        'current_semester': current_semester,
    }
    
    return render(request, 'programmes/programme_detail.html', context)

# views.py

# views.py - Fixed add_programme_year function
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q
import json
import logging
import uuid
from .models import Programme, Course, ProgrammeCourse, Department

# Set up logging
logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["POST"])
def add_programme_year(request):
    try:
        # Check if request is AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Invalid request type'
            }, status=400)
        
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        programme_id = data.get('programme_id')
        year = data.get('year')
        
        # Validate required fields
        if not programme_id:
            return JsonResponse({
                'success': False,
                'error': 'Programme ID is required'
            }, status=400)
        
        if not year:
            return JsonResponse({
                'success': False,
                'error': 'Year is required'
            }, status=400)
        
        # Validate programme exists
        try:
            programme = Programme.objects.get(id=programme_id)
        except Programme.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Programme not found'
            }, status=404)
        
        # Validate year
        if not isinstance(year, int) or year < 1 or year > programme.duration_years:
            return JsonResponse({
                'success': False,
                'error': f'Year must be between 1 and {programme.duration_years}'
            }, status=400)
        
        # Check if year already exists
        existing_year = ProgrammeCourse.objects.filter(
            programme=programme,
            year=year
        ).exists()
        
        if existing_year:
            return JsonResponse({
                'success': False,
                'error': f'Year {year} already exists for this programme'
            }, status=400)
        
        # Create entries for each semester WITHOUT creating placeholder courses
        semesters = range(1, programme.semesters_per_year + 1)
        created_semesters = []
        
        with transaction.atomic():
            # Just create the year structure without courses
            # The frontend will handle showing empty semesters
            for semester in semesters:
                # We don't create any ProgrammeCourse entries yet
                # The year structure will be created when courses are added
                created_semesters.append(semester)
        
        logger.info(f"Year {year} structure created for programme {programme.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Year {year} created successfully with {len(created_semesters)} semesters',
            'year': year,
            'semesters': created_semesters,
            'programme_id': programme_id
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in add_programme_year: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_programme_semester(request):
    """Add a new semester to a specific year in a programme"""
    try:
        # Check if request is AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Invalid request type'
            }, status=400)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        programme_id = data.get('programme_id')
        year = data.get('year')
        semester = data.get('semester')
        
        try:
            programme = get_object_or_404(Programme, id=programme_id)
        except Programme.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Programme not found'
            }, status=404)
        
        # Validate inputs
        if not year or not isinstance(year, int) or year < 1 or year > 8:
            return JsonResponse({
                'success': False,
                'error': 'Year must be between 1 and 8'
            }, status=400)
        
        # Get semesters_per_year from programme or default to 2
        max_semesters = getattr(programme, 'semesters_per_year', 2)
        
        if not semester or not isinstance(semester, int) or semester < 1 or semester > max_semesters:
            return JsonResponse({
                'success': False,
                'error': f'Semester must be between 1 and {max_semesters}'
            }, status=400)
        
        # Check if semester already exists for this year
        existing_semester = ProgrammeCourse.objects.filter(
            programme=programme,
            year=year,
            semester=semester
        ).exists()
        
        if existing_semester:
            return JsonResponse({
                'success': False,
                'error': f'Semester {semester} already exists for Year {year}'
            }, status=400)
        
        logger.info(f"Semester {semester} added to Year {year} in programme {programme.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester} added to Year {year} successfully',
            'year': year,
            'semester': semester
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in add_programme_semester: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def add_programme_course(request):
    """Add a course to a specific year and semester of a programme"""
    try:
        # Check if request is AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Invalid request type'
            }, status=400)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        programme_id = data.get('programme_id')
        course_id = data.get('course_id')
        year = data.get('year')
        semester = data.get('semester')
        is_mandatory = data.get('is_mandatory', True)
        
        try:
            programme = get_object_or_404(Programme, id=programme_id)
            course = get_object_or_404(Course, id=course_id)
        except (Programme.DoesNotExist, Course.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Programme or Course not found'
            }, status=404)
        
        # Validate inputs
        if not year or not isinstance(year, int) or year < 1 or year > 8:
            return JsonResponse({
                'success': False,
                'error': 'Year must be between 1 and 8'
            }, status=400)
        
        max_semesters = getattr(programme, 'semesters_per_year', 2)
        if not semester or not isinstance(semester, int) or semester < 1 or semester > max_semesters:
            return JsonResponse({
                'success': False,
                'error': f'Semester must be between 1 and {max_semesters}'
            }, status=400)
        
        # Check if course already exists in this programme, year, and semester
        existing_course = ProgrammeCourse.objects.filter(
            programme=programme,
            course=course,
            year=year,
            semester=semester
        ).exists()
        
        if existing_course:
            return JsonResponse({
                'success': False,
                'error': f'{course.name} already exists in Year {year}, Semester {semester}'
            }, status=400)
        
        # Create the programme course
        with transaction.atomic():
            programme_course = ProgrammeCourse.objects.create(
                programme=programme,
                course=course,
                year=year,
                semester=semester,
                is_mandatory=is_mandatory
            )
        
        logger.info(f"Course {course.name} added to programme {programme.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'{course.name} added successfully to Year {year}, Semester {semester}',
            'course_data': {
                'id': programme_course.id,
                'course_id': course.id,
                'course_name': course.name,
                'course_code': course.code,
                'credit_hours': course.credit_hours,
                'lecture_hours': getattr(course, 'lecture_hours', 0),
                'practical_hours': getattr(course, 'practical_hours', 0),
                'department': course.department.name,
                'is_mandatory': is_mandatory,
                'year': year,
                'semester': semester
            }
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in add_programme_course: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_available_courses(request):
    """Get available courses for a programme (not already added to specific year/semester)"""
    try:
        programme_id = request.GET.get('programme_id')
        year = request.GET.get('year')
        semester = request.GET.get('semester')
        search = request.GET.get('search', '')
        
        try:
            programme = get_object_or_404(Programme, id=programme_id)
        except Programme.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Programme not found'
            }, status=404)
        
        # Get courses from the same department or faculty
        available_courses = Course.objects.filter(
            department__faculty=programme.faculty,
            is_active=True
        )
        
        # Filter out courses already in this programme for this year/semester
        if year and semester:
            existing_course_ids = ProgrammeCourse.objects.filter(
                programme=programme,
                year=year,
                semester=semester
            ).values_list('course_id', flat=True)
            available_courses = available_courses.exclude(id__in=existing_course_ids)
        
        # Apply search filter
        if search:
            available_courses = available_courses.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) |
                Q(department__name__icontains=search)
            )
        
        # Limit results
        available_courses = available_courses[:20]
        
        courses_data = []
        for course in available_courses:
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'credit_hours': course.credit_hours,
                'level': getattr(course, 'level', ''),
                'department': course.department.name,
                'course_type': getattr(course, 'get_course_type_display', lambda: 'N/A')()
            })
        
        return JsonResponse({
            'success': True,
            'courses': courses_data
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in get_available_courses: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["DELETE"])
def remove_programme_course(request):
    """Remove a course from a programme"""
    try:
        # Check if request is AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Invalid request type'
            }, status=400)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        programme_course_id = data.get('programme_course_id')
        
        try:
            programme_course = get_object_or_404(ProgrammeCourse, id=programme_course_id)
        except ProgrammeCourse.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Programme course not found'
            }, status=404)
        
        # Check if there are any enrollments
        try:
            from .models import Enrollment
            enrollment_count = Enrollment.objects.filter(
                course=programme_course.course,
                student__programme=programme_course.programme
            ).count()
        except ImportError:
            # If Enrollment model doesn't exist, assume no enrollments
            enrollment_count = 0
        
        if enrollment_count > 0:
            return JsonResponse({
                'success': False,
                'error': f'Cannot remove course. {enrollment_count} students are enrolled.'
            }, status=400)
        
        course_name = programme_course.course.name
        programme_course.delete()
        
        logger.info(f"Course {course_name} removed from programme")
        
        return JsonResponse({
            'success': True,
            'message': f'{course_name} removed successfully'
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in remove_programme_course: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@login_required
def course_enrollments(request, programme_id, course_id):
    """View to display students enrolled in a specific course for a programme"""
    programme = get_object_or_404(Programme, id=programme_id, is_active=True)
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Verify the course is part of this programme
    programme_course = get_object_or_404(
        ProgrammeCourse,
        programme=programme,
        course=course,
        is_active=True
    )
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get enrollments for current semester
    enrollments = Enrollment.objects.select_related(
        'student__user', 'student__programme', 'lecturer__user'
    ).filter(
        course=course,
        student__programme=programme,
        is_active=True
    )
    
    # Filter by semester
    semester_id = request.GET.get('semester', '')
    if semester_id:
        enrollments = enrollments.filter(semester_id=semester_id)
    elif current_semester:
        enrollments = enrollments.filter(semester=current_semester)
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        enrollments = enrollments.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(student__user__username__icontains=search_query)
        )
    
    # Filter by year
    year_filter = request.GET.get('year', '')
    if year_filter:
        enrollments = enrollments.filter(student__current_year=year_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        enrollments = enrollments.filter(student__status=status_filter)
    
    enrollments = enrollments.order_by(
        'student__current_year', 
        'student__user__last_name', 
        'student__user__first_name'
    )
    
    # Pagination
    paginator = Paginator(enrollments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    available_semesters = Semester.objects.filter(
        enrollments__course=course,
        enrollments__student__programme=programme,
        enrollments__is_active=True
    ).distinct().order_by('-academic_year__start_date', '-semester_number')
    
    years_with_enrollments = enrollments.values_list(
        'student__current_year', flat=True
    ).distinct().order_by('student__current_year')
    
    # Calculate statistics
    enrollment_stats = {
        'total_enrolled': enrollments.count(),
        'by_year': {},
        'by_status': {},
        'repeat_students': enrollments.filter(is_repeat=True).count(),
        'audit_students': enrollments.filter(is_audit=True).count(),
    }
    
    # Group by year
    for year in years_with_enrollments:
        enrollment_stats['by_year'][year] = enrollments.filter(
            student__current_year=year
        ).count()
    
    # Group by status
    for status, _ in Student.STATUS_CHOICES:
        count = enrollments.filter(student__status=status).count()
        if count > 0:
            enrollment_stats['by_status'][status] = count
    
    context = {
        'programme': programme,
        'course': course,
        'programme_course': programme_course,
        'page_obj': page_obj,
        'enrollment_stats': enrollment_stats,
        'available_semesters': available_semesters,
        'years_with_enrollments': years_with_enrollments,
        'current_semester': current_semester,
        'search_query': search_query,
        'selected_semester': semester_id,
        'selected_year': year_filter,
        'selected_status': status_filter,
        'student_status_choices': Student.STATUS_CHOICES,
    }
    
    return render(request, 'programmes/course_enrollments.html', context)


@login_required
def student_enrollment_detail(request, student_id, course_id):
    """View to display detailed information about a student's enrollment in a course"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        id=student_id
    )
    course = get_object_or_404(Course, id=course_id)
    
    # Get all enrollments for this student in this course
    enrollments = Enrollment.objects.select_related(
        'semester__academic_year', 'lecturer__user'
    ).filter(
        student=student,
        course=course
    ).order_by('-semester__academic_year__start_date', '-semester__semester_number')
    
    # Get the most recent enrollment
    current_enrollment = enrollments.first()
    
    context = {
        'student': student,
        'course': course,
        'enrollments': enrollments,
        'current_enrollment': current_enrollment,
    }
    
    return render(request, 'programmes/student_enrollment_detail.html', context)


# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Avg, Count, Sum
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.template.loader import render_to_string
from .models import (
    Grade, Student, AcademicYear, Semester, Programme, 
    Department, Faculty, Course, Enrollment
)
import json
from decimal import Decimal

@login_required
def grades_list(request):
    """
    Display grades list with filtering options
    """
    # Get filter parameters
    academic_year_id = request.GET.get('academic_year')
    semester_id = request.GET.get('semester')
    programme_id = request.GET.get('programme')
    department_id = request.GET.get('department')
    student_search = request.GET.get('student_search', '').strip()
    course_search = request.GET.get('course_search', '').strip()
    grade_filter = request.GET.get('grade_filter')
    
    # Base queryset
    grades = Grade.objects.select_related(
        'enrollment__student__user',
        'enrollment__student__programme',
        'enrollment__course',
        'enrollment__semester__academic_year',
        'enrollment__lecturer__user'
    ).order_by(
        'enrollment__semester__academic_year__year',
        'enrollment__semester__semester_number',
        'enrollment__student__user__last_name',
        'enrollment__student__user__first_name',
        'enrollment__course__code'
    )
    
    # Apply filters
    if academic_year_id:
        grades = grades.filter(enrollment__semester__academic_year_id=academic_year_id)
    
    if semester_id:
        grades = grades.filter(enrollment__semester_id=semester_id)
    
    if programme_id:
        grades = grades.filter(enrollment__student__programme_id=programme_id)
    
    if department_id:
        grades = grades.filter(enrollment__course__department_id=department_id)
    
    if student_search:
        grades = grades.filter(
            Q(enrollment__student__user__first_name__icontains=student_search) |
            Q(enrollment__student__user__last_name__icontains=student_search) |
            Q(enrollment__student__student_id__icontains=student_search)
        )
    
    if course_search:
        grades = grades.filter(
            Q(enrollment__course__name__icontains=course_search) |
            Q(enrollment__course__code__icontains=course_search)
        )
    
    if grade_filter:
        grades = grades.filter(grade=grade_filter)
    
    # Group grades by student for better organization
    students_grades = {}
    for grade in grades:
        student = grade.enrollment.student
        student_key = student.student_id
        
        if student_key not in students_grades:
            students_grades[student_key] = {
                'student': student,
                'grades': [],
                'total_credits': 0,
                'total_quality_points': Decimal('0.00'),
                'gpa': Decimal('0.00')
            }
        
        students_grades[student_key]['grades'].append(grade)
        students_grades[student_key]['total_credits'] += grade.enrollment.course.credit_hours
        if grade.quality_points:
            students_grades[student_key]['total_quality_points'] += grade.quality_points
    
    # Calculate GPA for each student
    for student_data in students_grades.values():
        if student_data['total_credits'] > 0:
            student_data['gpa'] = student_data['total_quality_points'] / student_data['total_credits']
        student_data['gpa'] = round(student_data['gpa'], 2)
    
    # Pagination
    paginator = Paginator(list(students_grades.values()), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    academic_years = AcademicYear.objects.all().order_by('-year')
    semesters = Semester.objects.all().order_by('-academic_year__year', '-semester_number')
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    # Statistics
    total_students = len(students_grades)
    total_grades = grades.count()
    average_gpa = sum([s['gpa'] for s in students_grades.values()]) / total_students if total_students > 0 else 0
    
    # Grade distribution
    grade_distribution = {}
    for grade in grades:
        if grade.grade:
            grade_distribution[grade.grade] = grade_distribution.get(grade.grade, 0) + 1
    
    context = {
        'students_grades': page_obj,
        'academic_years': academic_years,
        'semesters': semesters,
        'programmes': programmes,
        'departments': departments,
        'total_students': total_students,
        'total_grades': total_grades,
        'average_gpa': round(average_gpa, 2),
        'grade_distribution': grade_distribution,
        'filters': {
            'academic_year_id': academic_year_id,
            'semester_id': semester_id,
            'programme_id': programme_id,
            'department_id': department_id,
            'student_search': student_search,
            'course_search': course_search,
            'grade_filter': grade_filter,
        },
        'grade_choices': Grade.GRADE_CHOICES,
    }
    
    return render(request, 'grades/grades_list.html', context)

@login_required
def get_semesters_by_year(request):
    """
    AJAX view to get semesters for a specific academic year
    """
    academic_year_id = request.GET.get('academic_year_id')
    semesters = []
    
    if academic_year_id:
        semesters = list(
            Semester.objects.filter(academic_year_id=academic_year_id)
            .values('id', 'semester_number', 'start_date', 'end_date')
            .order_by('semester_number')
        )
    
    return JsonResponse({'semesters': semesters})

@login_required
def download_grades_pdf(request):
    """
    Generate and download PDF report of grades
    """
    # Get the same filters as the main view
    academic_year_id = request.GET.get('academic_year')
    semester_id = request.GET.get('semester')
    programme_id = request.GET.get('programme')
    department_id = request.GET.get('department')
    
    # Get filtered data
    grades = Grade.objects.select_related(
        'enrollment__student__user',
        'enrollment__student__programme',
        'enrollment__course',
        'enrollment__semester__academic_year',
        'enrollment__lecturer__user'
    ).order_by(
        'enrollment__student__user__last_name',
        'enrollment__student__user__first_name',
        'enrollment__course__code'
    )
    
    # Apply filters
    if academic_year_id:
        grades = grades.filter(enrollment__semester__academic_year_id=academic_year_id)
    if semester_id:
        grades = grades.filter(enrollment__semester_id=semester_id)
    if programme_id:
        grades = grades.filter(enrollment__student__programme_id=programme_id)
    if department_id:
        grades = grades.filter(enrollment__course__department_id=department_id)
    
    # Group grades by student
    students_grades = {}
    for grade in grades:
        student = grade.enrollment.student
        student_key = student.student_id
        
        if student_key not in students_grades:
            students_grades[student_key] = {
                'student': student,
                'grades': [],
                'total_credits': 0,
                'total_quality_points': Decimal('0.00'),
                'gpa': Decimal('0.00')
            }
        
        students_grades[student_key]['grades'].append(grade)
        students_grades[student_key]['total_credits'] += grade.enrollment.course.credit_hours
        if grade.quality_points:
            students_grades[student_key]['total_quality_points'] += grade.quality_points
    
    # Calculate GPA for each student
    for student_data in students_grades.values():
        if student_data['total_credits'] > 0:
            student_data['gpa'] = student_data['total_quality_points'] / student_data['total_credits']
        student_data['gpa'] = round(student_data['gpa'], 2)
    
    # Get filter context for the PDF
    academic_year = None
    semester = None
    programme = None
    department = None
    
    if academic_year_id:
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    if programme_id:
        programme = get_object_or_404(Programme, id=programme_id)
    if department_id:
        department = get_object_or_404(Department, id=department_id)
    
    context = {
        'students_grades': list(students_grades.values()),
        'academic_year': academic_year,
        'semester': semester,
        'programme': programme,
        'department': department,
        'total_students': len(students_grades),
        'total_grades': grades.count(),
    }
    
    return render(request, 'grades/grades_pdf.html', context)


@login_required
def course_grades(request, course_id):
    """
    View grades for a specific course across all students
    """
    course = get_object_or_404(Course, id=course_id)
    semester_id = request.GET.get('semester')
    
    # Base queryset
    grades = Grade.objects.filter(
        enrollment__course=course
    ).select_related(
        'enrollment__student__user',
        'enrollment__student__programme',
        'enrollment__semester__academic_year',
        'enrollment__lecturer__user'
    )
    
    if semester_id:
        grades = grades.filter(enrollment__semester_id=semester_id)
    
    grades = grades.order_by('enrollment__student__user__last_name')
    
    # Statistics
    total_students = grades.count()
    passed_students = grades.filter(is_passed=True).count()
    failed_students = total_students - passed_students
    
    # Grade distribution
    grade_distribution = {}
    total_marks_sum = 0
    marks_count = 0
    
    for grade in grades:
        if grade.grade:
            grade_distribution[grade.grade] = grade_distribution.get(grade.grade, 0) + 1
        
        if grade.total_marks:
            total_marks_sum += float(grade.total_marks)
            marks_count += 1
    
    average_marks = total_marks_sum / marks_count if marks_count > 0 else 0
    pass_rate = (passed_students / total_students * 100) if total_students > 0 else 0
    
    # Get semesters for filtering
    semesters = Semester.objects.filter(
        enrollments__course=course
    ).distinct().order_by('-academic_year__year', '-semester_number')
    
    context = {
        'course': course,
        'grades': grades,
        'semesters': semesters,
        'selected_semester': semester_id,
        'statistics': {
            'total_students': total_students,
            'passed_students': passed_students,
            'failed_students': failed_students,
            'pass_rate': round(pass_rate, 1),
            'average_marks': round(average_marks, 1),
            'grade_distribution': grade_distribution,
        }
    }
    
    return render(request, 'grades/course_grades.html', context)

@login_required
def grades_analytics(request):
    """
    Analytics dashboard for grades
    """
    # Get filter parameters
    academic_year_id = request.GET.get('academic_year')
    programme_id = request.GET.get('programme')
    department_id = request.GET.get('department')
    
    # Base queryset
    grades = Grade.objects.select_related(
        'enrollment__student__programme',
        'enrollment__course__department',
        'enrollment__semester__academic_year'
    )
    
    # Apply filters
    if academic_year_id:
        grades = grades.filter(enrollment__semester__academic_year_id=academic_year_id)
    if programme_id:
        grades = grades.filter(enrollment__student__programme_id=programme_id)
    if department_id:
        grades = grades.filter(enrollment__course__department_id=department_id)
    
    # Overall statistics
    total_grades = grades.count()
    total_students = grades.values('enrollment__student').distinct().count()
    
    # Grade distribution
    grade_distribution = {}
    for grade_choice in Grade.GRADE_CHOICES:
        grade_code = grade_choice[0]
        count = grades.filter(grade=grade_code).count()
        if count > 0:
            grade_distribution[grade_code] = {
                'count': count,
                'percentage': round((count / total_grades * 100), 1) if total_grades > 0 else 0
            }
    
    # Performance by programme
    programme_performance = {}
    for programme in Programme.objects.filter(is_active=True):
        programme_grades = grades.filter(enrollment__student__programme=programme)
        if programme_grades.exists():
            passed = programme_grades.filter(is_passed=True).count()
            total = programme_grades.count()
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            programme_performance[programme.name] = {
                'total_grades': total,
                'passed': passed,
                'pass_rate': round(pass_rate, 1)
            }
    
    # Performance by department
    department_performance = {}
    for department in Department.objects.filter(is_active=True):
        dept_grades = grades.filter(enrollment__course__department=department)
        if dept_grades.exists():
            passed = dept_grades.filter(is_passed=True).count()
            total = dept_grades.count()
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            department_performance[department.name] = {
                'total_grades': total,
                'passed': passed,
                'pass_rate': round(pass_rate, 1)
            }
    
    # GPA distribution
    gpa_ranges = {
        '3.5-4.0': 0, '3.0-3.49': 0, '2.5-2.99': 0,
        '2.0-2.49': 0, '1.5-1.99': 0, 'Below 1.5': 0
    }
    
    # Calculate student GPAs (simplified)
    student_gpas = {}
    for grade in grades:
        student_id = grade.enrollment.student.id
        if student_id not in student_gpas:
            student_gpas[student_id] = {'quality_points': 0, 'credits': 0}
        
        if grade.quality_points and grade.enrollment.course.credit_hours:
            student_gpas[student_id]['quality_points'] += float(grade.quality_points)
            student_gpas[student_id]['credits'] += grade.enrollment.course.credit_hours
    
    for student_data in student_gpas.values():
        if student_data['credits'] > 0:
            gpa = student_data['quality_points'] / student_data['credits']
            if gpa >= 3.5:
                gpa_ranges['3.5-4.0'] += 1
            elif gpa >= 3.0:
                gpa_ranges['3.0-3.49'] += 1
            elif gpa >= 2.5:
                gpa_ranges['2.5-2.99'] += 1
            elif gpa >= 2.0:
                gpa_ranges['2.0-2.49'] += 1
            elif gpa >= 1.5:
                gpa_ranges['1.5-1.99'] += 1
            else:
                gpa_ranges['Below 1.5'] += 1
    
    # Get filter options
    academic_years = AcademicYear.objects.all().order_by('-year')
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'total_grades': total_grades,
        'total_students': total_students,
        'grade_distribution': grade_distribution,
        'programme_performance': programme_performance,
        'department_performance': department_performance,
        'gpa_ranges': gpa_ranges,
        'academic_years': academic_years,
        'programmes': programmes,
        'departments': departments,
        'filters': {
            'academic_year_id': academic_year_id,
            'programme_id': programme_id,
            'department_id': department_id,
        }
    }
    
    return render(request, 'grades/analytics.html', context)


# views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Avg, Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Programme, FeeStructure, AcademicYear, Student

@login_required
def fee_structure_list(request):
    """Display all programmes with their fee information"""
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get all active programmes with their fee statistics
    programmes = Programme.objects.filter(is_active=True).select_related(
        'faculty', 'department'
    ).prefetch_related('fee_structures')
    
    programme_data = []
    
    for programme in programmes:
        # Get fee structures for current academic year
        fee_structures = FeeStructure.objects.filter(
            programme=programme,
            academic_year=current_academic_year
        ) if current_academic_year else FeeStructure.objects.filter(programme=programme)
        
        # Calculate total fees for all years/semesters
        total_programme_fee = fee_structures.aggregate(
            total=Sum('tuition_fee')
        )['total'] or 0
        
        # Get average semester fee
        avg_semester_fee = fee_structures.aggregate(
            avg=Avg('tuition_fee')
        )['avg'] or 0
        
        # Count active students
        active_students = Student.objects.filter(
            programme=programme,
            status='active'
        ).count()
        
        # Get fee range (min and max)
        fee_range = fee_structures.aggregate(
            min_fee=Sum('tuition_fee'),
            max_fee=Sum('tuition_fee')
        )
        
        programme_info = {
            'programme': programme,
            'total_programme_fee': total_programme_fee,
            'avg_semester_fee': avg_semester_fee,
            'active_students': active_students,
            'fee_structures_count': fee_structures.count(),
            'has_fee_structure': fee_structures.exists(),
            'min_semester_fee': fee_structures.aggregate(min_fee=Sum('tuition_fee'))['min_fee'] or 0,
            'max_semester_fee': fee_structures.aggregate(max_fee=Sum('tuition_fee'))['max_fee'] or 0,
        }
        programme_data.append(programme_info)
    
    context = {
        'programme_data': programme_data,
        'current_academic_year': current_academic_year,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
    }
    
    return render(request, 'admin/fee_structure_list.html', context)

@login_required
def programme_fee_detail(request, programme_id):
    """Display detailed fee structure for a specific programme"""
    
    programme = get_object_or_404(Programme, id=programme_id, is_active=True)
    
    # Get selected academic year from GET parameter, default to current
    selected_year_id = request.GET.get('academic_year')
    if selected_year_id:
        selected_academic_year = get_object_or_404(AcademicYear, id=selected_year_id)
    else:
        selected_academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not selected_academic_year:
            selected_academic_year = AcademicYear.objects.first()
    
    # Get all academic years for the dropdown
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    # Get fee structures for the selected academic year
    fee_structures = FeeStructure.objects.filter(
        programme=programme,
        academic_year=selected_academic_year
    ).order_by('year', 'semester')
    
    # Organize fee structures by year and semester - Fixed structure
    fees_by_year = {}
    total_programme_cost = 0
    programme_years = list(range(1, programme.duration_years + 1))
    semesters_range = list(range(1, programme.semesters_per_year + 1))
    
    for year in programme_years:
        fees_by_year[year] = {}
        year_total = 0
        
        for semester in semesters_range:
            fee_structure = fee_structures.filter(year=year, semester=semester).first()
            
            if fee_structure:
                semester_total = fee_structure.total_fee()
                semester_net = fee_structure.net_fee()
                year_total += semester_net
                
                # Ensure the data structure is consistent
                fees_by_year[year][semester] = {
                    'fee_structure': fee_structure,
                    'total_fee': float(semester_total) if semester_total else 0,
                    'net_fee': float(semester_net) if semester_net else 0,
                    'government_subsidy': float(fee_structure.government_subsidy) if fee_structure.government_subsidy else 0,
                    'scholarship_amount': float(fee_structure.scholarship_amount) if fee_structure.scholarship_amount else 0,
                    'exists': True
                }
            else:
                # Provide a consistent structure even when no fee structure exists
                fees_by_year[year][semester] = {
                    'fee_structure': None,
                    'total_fee': 0,
                    'net_fee': 0,
                    'government_subsidy': 0,
                    'scholarship_amount': 0,
                    'exists': False
                }
        
        total_programme_cost += year_total
    
    # Calculate programme statistics
    programme_stats = {
        'total_fee_structures': fee_structures.count(),
        'total_programme_cost': total_programme_cost,
        'average_semester_fee': total_programme_cost / (programme.total_semesters) if programme.total_semesters > 0 else 0,
        'active_students': Student.objects.filter(programme=programme, status='active').count(),
        'total_students': Student.objects.filter(programme=programme).count(),
    }
    
    # Get student enrollment statistics by year
    student_stats_by_year = {}
    for year in programme_years:
        student_count = Student.objects.filter(
            programme=programme,
            current_year=year,
            status='active'
        ).count()
        student_stats_by_year[year] = student_count
    
    context = {
        'programme': programme,
        'selected_academic_year': selected_academic_year,
        'academic_years': academic_years,
        'fees_by_year': fees_by_year,
        'programme_years': programme_years,
        'programme_stats': programme_stats,
        'student_stats_by_year': student_stats_by_year,
        'semesters_range': semesters_range,
    }
    
    return render(request, 'admin/programme_fee_detail.html', context)


@login_required
def fee_structure_comparison(request):
    """Compare fee structures across programmes"""
    
    selected_programmes = request.GET.getlist('programmes')
    selected_year_id = request.GET.get('academic_year')
    
    # Get academic year
    if selected_year_id:
        academic_year = get_object_or_404(AcademicYear, id=selected_year_id)
    else:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    comparison_data = []
    
    if selected_programmes:
        for programme_id in selected_programmes:
            programme = get_object_or_404(Programme, id=programme_id)
            
            # Get fee structures for this programme
            fee_structures = FeeStructure.objects.filter(
                programme=programme,
                academic_year=academic_year
            )
            
            total_cost = sum(fs.net_fee() for fs in fee_structures)
            avg_semester_fee = total_cost / programme.total_semesters if programme.total_semesters > 0 else 0
            
            comparison_data.append({
                'programme': programme,
                'total_cost': total_cost,
                'avg_semester_fee': avg_semester_fee,
                'fee_structures': fee_structures.order_by('year', 'semester'),
                'student_count': Student.objects.filter(programme=programme, status='active').count(),
            })
    
    context = {
        'programmes': programmes,
        'selected_programmes': [int(p) for p in selected_programmes] if selected_programmes else [],
        'academic_year': academic_year,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'comparison_data': comparison_data,
    }
    
    return render(request, 'admin/fee_structure_comparison.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

@login_required
def lecturer_dashboard(request):
    # Check if user is a lecturer
    if not hasattr(request.user, 'lecturer_profile') or request.user.user_type not in ['lecturer', 'professor']:
        messages.error(request, "Access denied. You must be a lecturer to view this page.")
        return redirect('home')
    
    lecturer = request.user.lecturer_profile
    
    # Get current semester and academic year
    current_semester = Semester.objects.filter(is_current=True).first()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get lecturer's course assignments for current semester
    current_assignments = LecturerCourseAssignment.objects.filter(
        lecturer=lecturer,
        semester=current_semester,
        is_active=True
    ).select_related('course', 'academic_year') if current_semester else LecturerCourseAssignment.objects.none()
    
    # Get total students taught by this lecturer in current semester
    total_students = Enrollment.objects.filter(
        lecturer=lecturer,
        semester=current_semester,
        is_active=True
    ).count() if current_semester else 0
    
    # Get courses taught this semester with detailed statistics
    courses_with_stats = []
    total_credit_hours = 0
    
    for assignment in current_assignments:
        course = assignment.course
        enrollments = Enrollment.objects.filter(
            course=course,
            lecturer=lecturer,
            semester=current_semester,
            is_active=True
        )
        
        student_count = enrollments.count()
        grades_completed = Grade.objects.filter(
            enrollment__in=enrollments,
            grade__isnull=False
        ).count()
        
        # Calculate average grade for this course
        avg_grade_points = Grade.objects.filter(
            enrollment__in=enrollments,
            grade_points__isnull=False
        ).aggregate(avg_gpa=Avg('grade_points'))['avg_gpa'] or 0
        
        # Get attendance statistics
        attendance_sessions = AttendanceSession.objects.filter(
            timetable_slot__course=course,
            lecturer=lecturer,
            semester=current_semester
        )
        
        total_sessions = attendance_sessions.count()
        total_attendance_records = Attendance.objects.filter(
            attendance_session__in=attendance_sessions,
            status='present'
        ).count()
        
        # Calculate attendance rate
        expected_attendance = student_count * total_sessions
        attendance_rate = (total_attendance_records / expected_attendance * 100) if expected_attendance > 0 else 0
        
        courses_with_stats.append({
            'assignment': assignment,
            'course': course,
            'student_count': student_count,
            'grades_completed': grades_completed,
            'grading_progress': (grades_completed / student_count * 100) if student_count > 0 else 0,
            'avg_grade_points': round(avg_grade_points, 2),
            'attendance_rate': round(attendance_rate, 1),
            'total_sessions': total_sessions
        })
        
        total_credit_hours += course.credit_hours
    
    # Get recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        lecturer=lecturer,
        semester=current_semester,
        is_active=True
    ).select_related('student__user', 'course').order_by('-enrollment_date')[:8] if current_semester else []
    
    # Calculate overall grading statistics
    total_grades_pending = Enrollment.objects.filter(
        lecturer=lecturer,
        semester=current_semester,
        is_active=True
    ).exclude(grade__isnull=False).count() if current_semester else 0
    
    total_grades_completed = Grade.objects.filter(
        enrollment__lecturer=lecturer,
        enrollment__semester=current_semester
    ).count() if current_semester else 0
    
    total_enrollments = total_grades_pending + total_grades_completed
    grading_progress = (total_grades_completed / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Get attendance analytics for charts
    attendance_data = []
    weekly_attendance = []
    
    if current_semester:
        # Get weekly attendance data for the last 12 weeks
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=12)
        
        for week in range(12):
            week_start = start_date + timedelta(weeks=week)
            week_end = week_start + timedelta(days=6)
            
            week_attendance = Attendance.objects.filter(
                timetable_slot__course__in=[cs['course'] for cs in courses_with_stats],
                attendance_session__session_date__range=[week_start, week_end],
                status='present'
            ).count()
            
            week_total = Attendance.objects.filter(
                timetable_slot__course__in=[cs['course'] for cs in courses_with_stats],
                attendance_session__session_date__range=[week_start, week_end]
            ).count()
            
            attendance_rate = (week_attendance / week_total * 100) if week_total > 0 else 0
            
            weekly_attendance.append({
                'week': f"Week {week + 1}",
                'attendance_rate': round(attendance_rate, 1),
                'total_students': week_total
            })
    
    # Get enrollment trends (monthly data for current academic year)
    enrollment_trends = []
    if current_academic_year:
        for month in range(1, 13):
            month_enrollments = Enrollment.objects.filter(
                lecturer=lecturer,
                enrollment_date__year=current_academic_year.start_date.year,
                enrollment_date__month=month,
                is_active=True
            ).count()
            
            enrollment_trends.append({
                'month': datetime(2024, month, 1).strftime('%B'),
                'enrollments': month_enrollments
            })
    
    # Get grade distribution data
    grade_distribution = []
    if current_semester:
        grades = Grade.objects.filter(
            enrollment__lecturer=lecturer,
            enrollment__semester=current_semester,
            grade__isnull=False
        ).values('grade').annotate(count=Count('grade')).order_by('grade')
        
        for grade_data in grades:
            grade_distribution.append({
                'grade': grade_data['grade'],
                'count': grade_data['count']
            })
    
    # Get assignment submission statistics
    assignment_stats = []
    if current_semester:
        assignments = Assignment.objects.filter(
            lecturer_assignment__lecturer=lecturer,
            lecturer_assignment__semester=current_semester,
            is_published=True
        )
        
        for assignment in assignments[:5]:  # Latest 5 assignments
            total_submissions = assignment.submissions.count()
            submitted_count = assignment.submissions.filter(is_submitted=True).count()
            pending_count = total_submissions - submitted_count
            
            assignment_stats.append({
                'title': assignment.title,
                'submitted': submitted_count,
                'pending': pending_count,
                'total': total_submissions,
                'submission_rate': (submitted_count / total_submissions * 100) if total_submissions > 0 else 0
            })
    
    # Get daily schedule for current week
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_schedule = []
    
    for day in range(7):
        current_day = week_start + timedelta(days=day)
        day_sessions = AttendanceSession.objects.filter(
            lecturer=lecturer,
            session_date=current_day,
            is_active=True
        ).select_related('timetable_slot__course')
        
        week_schedule.append({
            'date': current_day,
            'day_name': current_day.strftime('%A'),
            'sessions': day_sessions,
            'is_today': current_day == today
        })
    
    # Calculate performance metrics
    performance_metrics = {
        'total_courses': len(courses_with_stats),
        'total_credit_hours': total_credit_hours,
        'avg_class_size': round(total_students / len(courses_with_stats), 1) if courses_with_stats else 0,
        'overall_attendance_rate': round(sum([cs['attendance_rate'] for cs in courses_with_stats]) / len(courses_with_stats), 1) if courses_with_stats else 0,
        'avg_grade_points': round(sum([cs['avg_grade_points'] for cs in courses_with_stats]) / len(courses_with_stats), 2) if courses_with_stats else 0
    }
    
    # Get upcoming deadlines
    upcoming_assignments = Assignment.objects.filter(
        lecturer_assignment__lecturer=lecturer,
        lecturer_assignment__semester=current_semester,
        due_date__gte=timezone.now(),
        is_published=True
    ).order_by('due_date')[:5]
    
    # Prepare chart data for JSON serialization
    chart_data = {
        'weekly_attendance': json.dumps(weekly_attendance),
        'enrollment_trends': json.dumps(enrollment_trends),
        'grade_distribution': json.dumps(grade_distribution),
        'assignment_stats': json.dumps(assignment_stats)
    }

    # Get lecturer's consultation hours and office info
    consultation_hours = lecturer.consultation_hours
    office_location = lecturer.office_location

    # Get academic rank and experience
    academic_rank = lecturer.get_academic_rank_display()
    teaching_experience = lecturer.teaching_experience_years
    
    context = {
        'lecturer': lecturer,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
        'total_students': total_students,
        'courses_with_stats': courses_with_stats,
        'recent_enrollments': recent_enrollments,
        'total_grades_pending': total_grades_pending,
        'total_grades_completed': total_grades_completed,
        'grading_progress': round(grading_progress, 1),
        'consultation_hours': lecturer.consultation_hours,
        'office_location': lecturer.office_location,
        'academic_rank': lecturer.get_academic_rank_display(),
        'teaching_experience': lecturer.teaching_experience_years,
        'performance_metrics': performance_metrics,
        'week_schedule': week_schedule,
        'upcoming_assignments': upcoming_assignments,
        'chart_data': chart_data,
        'today': today,
        'consultation_hours': consultation_hours,
        'office_location': office_location,
        'academic_rank': academic_rank,
        'teaching_experience': teaching_experience,
    }

    return render(request, 'lecturers/lecturer_dashboard.html', context)

# views.py - Add these views to your existing views file

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.forms import modelformset_factory
import json

from .models import (
    User, Lecturer, Course, AcademicYear, Semester, LecturerCourseAssignment,
    Assignment, CourseNotes, AssignmentSubmission, Enrollment, Student,
    Programme, Department, Faculty, AssignmentAnnouncement
)

def is_admin_or_hod(user):
    """Check if user is admin or head of department"""
    return user.user_type in ['admin', 'hod', 'dean']

def is_lecturer(user):
    """Check if user is a lecturer"""
    return user.user_type in ['lecturer', 'professor'] and hasattr(user, 'lecturer_profile')

@login_required
@user_passes_test(is_admin_or_hod)
def lecturer_allocation_dashboard(request):
    """Dashboard for admin to allocate units to lecturers"""
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_academic_year or not current_semester:
        messages.error(request, "Please set current academic year and semester first.")
        return redirect('admin_dashboard')
    
    # Get all active courses
    courses = Course.objects.filter(is_active=True).select_related('department', 'department__faculty')
    
    # Get all active lecturers
    lecturers = Lecturer.objects.filter(
        is_active=True,
        user__is_active=True
    ).select_related('user', 'department')
    
    # Get current allocations
    allocations = LecturerCourseAssignment.objects.filter(
        academic_year=current_academic_year,
        semester=current_semester,
        is_active=True
    ).select_related('lecturer__user', 'course')
    
    # Create a mapping of course_id to lecturer for quick lookup
    allocated_courses = {alloc.course_id: alloc for alloc in allocations}
    
    # Get unallocated courses
    allocated_course_ids = set(allocated_courses.keys())
    all_course_ids = set(courses.values_list('id', flat=True))
    unallocated_course_ids = all_course_ids - allocated_course_ids
    unallocated_courses = courses.filter(id__in=unallocated_course_ids)
    
    # Filter courses by department if user is HOD
    if request.user.user_type == 'hod':
        user_department = request.user.headed_departments.first()
        if user_department:
            courses = courses.filter(department=user_department)
            lecturers = lecturers.filter(department=user_department)
            unallocated_courses = unallocated_courses.filter(department=user_department)
    
    # Get statistics
    stats = {
        'total_courses': courses.count(),
        'allocated_courses': len(allocated_course_ids),
        'unallocated_courses': unallocated_courses.count(),
        'total_lecturers': lecturers.count(),
        'lecturers_with_assignments': allocations.values('lecturer').distinct().count()
    }
    
    # Get departments for filtering
    departments = Department.objects.filter(is_active=True)
    if request.user.user_type == 'hod':
        user_department = request.user.headed_departments.first()
        if user_department:
            departments = departments.filter(id=user_department.id)
    
    context = {
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'courses': courses,
        'lecturers': lecturers,
        'allocations': allocations,
        'allocated_courses': allocated_courses,
        'unallocated_courses': unallocated_courses,
        'stats': stats,
        'departments': departments,
    }
    
    return render(request, 'admin/lecturer_allocation_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_hod)
@require_http_methods(["POST"])
def allocate_course_to_lecturer(request):
    """AJAX endpoint to allocate a course to a lecturer"""
    
    try:
        course_id = request.POST.get('course_id')
        lecturer_id = request.POST.get('lecturer_id')
        lecture_venue = request.POST.get('lecture_venue', '')
        lecture_time = request.POST.get('lecture_time', '')
        remarks = request.POST.get('remarks', '')
        
        if not course_id or not lecturer_id:
            return JsonResponse({'success': False, 'message': 'Course and lecturer are required.'})
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_academic_year or not current_semester:
            return JsonResponse({'success': False, 'message': 'Current academic year and semester not set.'})
        
        course = get_object_or_404(Course, id=course_id, is_active=True)
        lecturer = get_object_or_404(Lecturer, id=lecturer_id, is_active=True)
        
        # Check if course is already allocated
        existing_allocation = LecturerCourseAssignment.objects.filter(
            course=course,
            academic_year=current_academic_year,
            semester=current_semester,
            is_active=True
        ).first()
        
        if existing_allocation:
            return JsonResponse({
                'success': False, 
                'message': f'Course {course.code} is already allocated to {existing_allocation.lecturer.user.get_full_name()}'
            })
        
        # Create allocation
        allocation = LecturerCourseAssignment.objects.create(
            lecturer=lecturer,
            course=course,
            academic_year=current_academic_year,
            semester=current_semester,
            assigned_by=request.user,
            lecture_venue=lecture_venue,
            lecture_time=lecture_time,
            remarks=remarks
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Course {course.code} successfully allocated to {lecturer.user.get_full_name()}',
            'allocation_id': allocation.id,
            'lecturer_name': lecturer.user.get_full_name(),
            'course_code': course.code,
            'course_name': course.name
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@user_passes_test(is_admin_or_hod)
@require_http_methods(["POST"])
def remove_course_allocation(request):
    """AJAX endpoint to remove a course allocation"""
    
    try:
        allocation_id = request.POST.get('allocation_id')
        
        if not allocation_id:
            return JsonResponse({'success': False, 'message': 'Allocation ID is required.'})
        
        allocation = get_object_or_404(LecturerCourseAssignment, id=allocation_id)
        
        # Check if user has permission to remove this allocation
        if request.user.user_type == 'hod':
            user_department = request.user.headed_departments.first()
            if user_department and allocation.course.department != user_department:
                return JsonResponse({'success': False, 'message': 'You can only manage allocations in your department.'})
        
        course_code = allocation.course.code
        lecturer_name = allocation.lecturer.user.get_full_name()
        
        allocation.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Allocation of {course_code} to {lecturer_name} has been removed.',
            'course_id': allocation.course.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@user_passes_test(is_lecturer)
def lecturer_unit_dashboard(request):
    """Dashboard for lecturers to view their allocated courses"""
    
    lecturer = request.user.lecturer_profile
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_academic_year or not current_semester:
        messages.error(request, "Current academic year and semester not set.")
        return render(request, 'lecturer/dashboard.html', {'lecturer': lecturer})
    
    # Get lecturer's course assignments for current semester
    assignments = LecturerCourseAssignment.objects.filter(
        lecturer=lecturer,
        academic_year=current_academic_year,
        semester=current_semester,
        is_active=True
    ).select_related('course', 'course__department').prefetch_related(
        'course__enrollments__student__user',
        'assignments',
        'course_notes'
    )
    
    # Calculate statistics for each assignment
    assignment_stats = []
    for assignment in assignments:
        # Get enrolled students for this course in current semester
        enrollments = Enrollment.objects.filter(
            course=assignment.course,
            semester=current_semester,
            is_active=True
        ).select_related('student__user')
        
        # Get assignment and notes counts
        assignment_count = Assignment.objects.filter(
            lecturer_assignment=assignment,
            is_active=True
        ).count()
        
        notes_count = CourseNotes.objects.filter(
            lecturer_assignment=assignment,
            is_active=True
        ).count()
        
        # Get pending submissions across all assignments
        pending_submissions = 0
        for assign in assignment.assignments.filter(is_active=True, is_published=True):
            pending_submissions += assign.pending_submissions
        
        assignment_stats.append({
            'assignment': assignment,
            'enrolled_students': enrollments,
            'student_count': enrollments.count(),
            'assignment_count': assignment_count,
            'notes_count': notes_count,
            'pending_submissions': pending_submissions
        })
    
    # Overall statistics
    stats = {
        'total_courses': assignments.count(),
        'total_students': sum([stat['student_count'] for stat in assignment_stats]),
        'total_assignments': sum([stat['assignment_count'] for stat in assignment_stats]),
        'total_notes': sum([stat['notes_count'] for stat in assignment_stats]),
        'pending_submissions': sum([stat['pending_submissions'] for stat in assignment_stats])
    }
    
    context = {
        'lecturer': lecturer,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'assignment_stats': assignment_stats,
        'stats': stats
    }
    
    return render(request, 'lecturers/unit_dashboard.html', context)

@login_required
@user_passes_test(is_lecturer)
def lecturer_course_detail(request, assignment_id):
    """Detailed view of a specific course assignment for lecturer"""
    
    lecturer = request.user.lecturer_profile
    assignment = get_object_or_404(
        LecturerCourseAssignment,
        id=assignment_id,
        lecturer=lecturer,
        is_active=True
    )
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(
        course=assignment.course,
        semester=assignment.semester,
        is_active=True
    ).select_related('student__user', 'student__programme').order_by('student__user__first_name')
    
    # Get course assignments
    course_assignments = Assignment.objects.filter(
        lecturer_assignment=assignment,
        is_active=True
    ).order_by('-posted_date')
    
    # Get course notes
    course_notes = CourseNotes.objects.filter(
        lecturer_assignment=assignment,
        is_active=True
    ).order_by('-posted_date')
    
    # Get recent announcements
    recent_announcements = AssignmentAnnouncement.objects.filter(
        assignment__lecturer_assignment=assignment,
        is_active=True
    ).order_by('-posted_date')[:5]
    
    # Statistics
    stats = {
        'enrolled_students': enrollments.count(),
        'total_assignments': course_assignments.count(),
        'published_assignments': course_assignments.filter(is_published=True).count(),
        'total_notes': course_notes.count(),
        'total_announcements': recent_announcements.count()
    }
    
    # Get submission statistics for each assignment
    assignment_submission_stats = []
    for assign in course_assignments.filter(is_published=True):
        submissions = AssignmentSubmission.objects.filter(assignment=assign)
        assignment_submission_stats.append({
            'assignment': assign,
            'total_submissions': submissions.count(),
            'submitted_count': submissions.filter(is_submitted=True).count(),
            'pending_grading': submissions.filter(is_submitted=True, grading_status='pending').count(),
            'graded_count': submissions.filter(grading_status='graded').count()
        })
    
    context = {
        'lecturer': lecturer,
        'assignment': assignment,
        'enrollments': enrollments,
        'course_assignments': course_assignments,
        'course_notes': course_notes,
        'recent_announcements': recent_announcements,
        'stats': stats,
        'assignment_submission_stats': assignment_submission_stats
    }
    
    return render(request, 'lecturers/course_detail.html', context)

@login_required
@user_passes_test(is_lecturer)
def create_assignment(request, assignment_id):
    """Create new assignment for a course"""
    
    lecturer = request.user.lecturer_profile
    course_assignment = get_object_or_404(
        LecturerCourseAssignment,
        id=assignment_id,
        lecturer=lecturer,
        is_active=True
    )
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            assignment_type = request.POST.get('assignment_type')
            description = request.POST.get('description')
            instructions = request.POST.get('instructions', '')
            due_date = request.POST.get('due_date')
            total_marks = request.POST.get('total_marks')
            weight_percentage = request.POST.get('weight_percentage')
            submission_format = request.POST.get('submission_format')
            max_file_size_mb = request.POST.get('max_file_size_mb', 10)
            late_submission_allowed = request.POST.get('late_submission_allowed') == 'on'
            late_submission_penalty = request.POST.get('late_submission_penalty', '')
            is_published = request.POST.get('is_published') == 'on'
            
            # Validate required fields
            if not all([title, assignment_type, description, due_date, total_marks, weight_percentage]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('create_assignment', assignment_id=assignment_id)
            
            # Create assignment
            assignment = Assignment.objects.create(
                lecturer_assignment=course_assignment,
                title=title,
                assignment_type=assignment_type,
                description=description,
                instructions=instructions,
                due_date=due_date,
                total_marks=int(total_marks),
                weight_percentage=float(weight_percentage),
                submission_format=submission_format,
                max_file_size_mb=int(max_file_size_mb),
                late_submission_allowed=late_submission_allowed,
                late_submission_penalty=late_submission_penalty,
                is_published=is_published
            )
            
            # Handle file upload
            if 'assignment_file' in request.FILES:
                assignment.assignment_file = request.FILES['assignment_file']
                assignment.save()
            
            messages.success(request, f'Assignment "{title}" created successfully.')
            return redirect('lecturer_course_detail', assignment_id=assignment_id)
            
        except Exception as e:
            messages.error(request, f'Error creating assignment: {str(e)}')
            return redirect('create_assignment', assignment_id=assignment_id)
    
    context = {
        'lecturer': lecturer,
        'course_assignment': course_assignment,
        'assignment_types': Assignment.ASSIGNMENT_TYPES,
        'submission_formats': Assignment.SUBMISSION_FORMATS
    }
    
    return render(request, 'lecturers/create_assignment.html', context)

@login_required
@user_passes_test(is_lecturer)
def create_course_notes(request, assignment_id):
    """Create new course notes"""
    
    lecturer = request.user.lecturer_profile
    course_assignment = get_object_or_404(
        LecturerCourseAssignment,
        id=assignment_id,
        lecturer=lecturer,
        is_active=True
    )
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            note_type = request.POST.get('note_type')
            description = request.POST.get('description', '')
            topic = request.POST.get('topic', '')
            week_number = request.POST.get('week_number')
            is_public = request.POST.get('is_public') == 'on'
            
            # Validate required fields
            if not all([title, note_type]) or 'notes_file' not in request.FILES:
                messages.error(request, 'Title, note type, and file are required.')
                return redirect('create_course_notes', assignment_id=assignment_id)
            
            # Create notes
            notes = CourseNotes.objects.create(
                lecturer_assignment=course_assignment,
                title=title,
                note_type=note_type,
                description=description,
                topic=topic,
                week_number=int(week_number) if week_number else None,
                is_public=is_public,
                notes_file=request.FILES['notes_file']
            )
            
            # Set file size
            if notes.notes_file:
                notes.file_size = notes.notes_file.size
                notes.save()
            
            messages.success(request, f'Notes "{title}" uploaded successfully.')
            return redirect('lecturer_course_detail', assignment_id=assignment_id)
            
        except Exception as e:
            messages.error(request, f'Error uploading notes: {str(e)}')
            return redirect('create_course_notes', assignment_id=assignment_id)
    
    context = {
        'lecturer': lecturer,
        'course_assignment': course_assignment,
        'note_types': CourseNotes.NOTE_TYPES
    }
    
    return render(request, 'lecturers/create_notes.html', context)

@login_required
@user_passes_test(is_lecturer)
def create_announcement(request, assignment_id):
    """Create announcement for an assignment"""
    
    lecturer = request.user.lecturer_profile
    
    if request.method == 'POST':
        try:
            assignment_pk = request.POST.get('assignment_pk')
            title = request.POST.get('title')
            message = request.POST.get('message')
            is_urgent = request.POST.get('is_urgent') == 'on'
            
            if not all([assignment_pk, title, message]):
                return JsonResponse({'success': False, 'message': 'All fields are required.'})
            
            # Verify assignment belongs to lecturer
            assignment = get_object_or_404(
                Assignment,
                id=assignment_pk,
                lecturer_assignment__lecturer=lecturer,
                is_active=True
            )
            
            # Create announcement
            announcement = AssignmentAnnouncement.objects.create(
                assignment=assignment,
                title=title,
                message=message,
                is_urgent=is_urgent
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Announcement created successfully.',
                'announcement': {
                    'id': announcement.id,
                    'title': announcement.title,
                    'message': announcement.message,
                    'is_urgent': announcement.is_urgent,
                    'posted_date': announcement.posted_date.strftime('%Y-%m-%d %H:%M')
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os

from .models import (
    Student, Enrollment, Course, Assignment, AssignmentSubmission, 
    CourseNotes, NotesDownload, Semester, AcademicYear,
    LecturerCourseAssignment, AssignmentAnnouncement
)
#used for cats and notes
@login_required
def student_unit_dashboard(request):
    """Main student dashboard showing enrolled courses and overview"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administrator.")
        return redirect('login')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get student's active enrollments for current semester
    enrollments = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).select_related(
        'course', 'course__department', 'course__department__faculty', 'lecturer'
    ).order_by('course__name')
    
    # Calculate statistics
    total_courses = enrollments.count()
    total_assignments = Assignment.objects.filter(
        lecturer_assignment__course__in=[e.course for e in enrollments],
        lecturer_assignment__semester=current_semester,
        is_published=True
    ).count()
    
    # Get pending assignments (not submitted)
    submitted_assignments = AssignmentSubmission.objects.filter(
        student=student,
        is_submitted=True
    ).values_list('assignment_id', flat=True)
    
    pending_assignments = Assignment.objects.filter(
        lecturer_assignment__course__in=[e.course for e in enrollments],
        lecturer_assignment__semester=current_semester,
        is_published=True
    ).exclude(id__in=submitted_assignments).count()
    
    # Get overdue assignments
    overdue_assignments = Assignment.objects.filter(
        lecturer_assignment__course__in=[e.course for e in enrollments],
        lecturer_assignment__semester=current_semester,
        is_published=True,
        due_date__lt=timezone.now()
    ).exclude(id__in=submitted_assignments).count()
    
    # Get recent announcements
    recent_announcements = AssignmentAnnouncement.objects.filter(
        assignment__lecturer_assignment__course__in=[e.course for e in enrollments],
        assignment__lecturer_assignment__semester=current_semester,
        is_active=True
    ).order_by('-posted_date')[:5]
    
    # Course statistics for each enrollment
    course_stats = []
    for enrollment in enrollments:
        course_assignments = Assignment.objects.filter(
            lecturer_assignment__course=enrollment.course,
            lecturer_assignment__semester=current_semester,
            is_published=True
        )
        
        submitted_count = AssignmentSubmission.objects.filter(
            student=student,
            assignment__in=course_assignments,
            is_submitted=True
        ).count()
        
        course_notes_count = CourseNotes.objects.filter(
            lecturer_assignment__course=enrollment.course,
            lecturer_assignment__semester=current_semester,
            is_active=True,
            is_public=True
        ).count()
        
        course_stats.append({
            'enrollment': enrollment,
            'total_assignments': course_assignments.count(),
            'submitted_assignments': submitted_count,
            'pending_assignments': course_assignments.count() - submitted_count,
            'notes_count': course_notes_count
        })
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'enrollments': enrollments,
        'course_stats': course_stats,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'pending_assignments': pending_assignments,
        'overdue_assignments': overdue_assignments,
        'recent_announcements': recent_announcements,
    }
    
    return render(request, 'student/unit_dashboard.html', context)


@login_required
def student_course_detail(request, enrollment_id):
    """Detailed view of a specific course with assignments and notes"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')
    
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            'course', 'course__department', 'course__department__faculty', 
            'lecturer', 'semester'
        ),
        id=enrollment_id,
        student=student,
        is_active=True
    )
    
    # Get lecturer assignment for this course
    lecturer_assignment = LecturerCourseAssignment.objects.filter(
        course=enrollment.course,
        semester=enrollment.semester,
        is_active=True
    ).first()
    
    # Get course assignments
    assignments = Assignment.objects.filter(
        lecturer_assignment=lecturer_assignment,
        is_published=True
    ).order_by('-posted_date')
    
    # Get student's submissions for these assignments
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__in=assignments
    )
    submission_dict = {sub.assignment_id: sub for sub in submissions}
    
    # Add submission status to assignments
    for assignment in assignments:
        assignment.student_submission = submission_dict.get(assignment.id)
        assignment.is_submitted = assignment.id in submission_dict and submission_dict[assignment.id].is_submitted
        assignment.is_late = assignment.due_date < timezone.now()
        assignment.can_submit = not assignment.is_late or assignment.late_submission_allowed
    
    # Get course notes
    course_notes = CourseNotes.objects.filter(
        lecturer_assignment=lecturer_assignment,
        is_active=True,
        is_public=True
    ).order_by('-posted_date')
    
    # Get recent announcements for this course
    announcements = AssignmentAnnouncement.objects.filter(
        assignment__lecturer_assignment=lecturer_assignment,
        is_active=True
    ).order_by('-posted_date')[:10]
    
    # Calculate statistics
    total_assignments = assignments.count()
    submitted_count = len([a for a in assignments if a.is_submitted])
    pending_count = total_assignments - submitted_count
    overdue_count = len([a for a in assignments if a.is_overdue and not a.is_submitted])
    
    # Get student's grades for this course
    try:
        from .models import Grade
        grade = Grade.objects.get(enrollment=enrollment)
    except Grade.DoesNotExist:
        grade = None
    
    context = {
        'student': student,
        'enrollment': enrollment,
        'lecturer_assignment': lecturer_assignment,
        'assignments': assignments,
        'course_notes': course_notes,
        'announcements': announcements,
        'grade': grade,
        'stats': {
            'total_assignments': total_assignments,
            'submitted_count': submitted_count,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
            'notes_count': course_notes.count(),
        }
    }
    
    return render(request, 'student/course_detail.html', context)


@login_required
def download_notes(request, notes_id):
    """Download course notes and track the download"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')
    
    notes = get_object_or_404(CourseNotes, id=notes_id, is_active=True, is_public=True)
    
    # Check if student is enrolled in this course
    enrollment_exists = Enrollment.objects.filter(
        student=student,
        course=notes.lecturer_assignment.course,
        semester=notes.lecturer_assignment.semester,
        is_active=True
    ).exists()
    
    if not enrollment_exists:
        messages.error(request, "You are not enrolled in this course.")
        return redirect('student_dashboard')
    
    # Track the download
    NotesDownload.objects.create(
        course_notes=notes,
        student=student,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Increment download count
    notes.download_count += 1
    notes.save(update_fields=['download_count'])
    
    # Serve the file
    try:
        if notes.notes_file:
            response = HttpResponse(notes.notes_file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(notes.notes_file.name)}"'
            return response
    except Exception as e:
        messages.error(request, "Error downloading file. Please try again.")
        return redirect('student_course_detail', enrollment_id=enrollment_exists.id if enrollment_exists else 0)
    
    messages.error(request, "File not found.")
    return redirect('student_dashboard')


@login_required
def assignment_detail(request, assignment_id):
    """Detailed view of an assignment with submission form"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')
    
    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'lecturer_assignment', 'lecturer_assignment__course',
            'lecturer_assignment__lecturer', 'lecturer_assignment__semester'
        ),
        id=assignment_id,
        is_published=True
    )
    
    # Check if student is enrolled in this course
    enrollment = get_object_or_404(
        Enrollment,
        student=student,
        course=assignment.lecturer_assignment.course,
        semester=assignment.lecturer_assignment.semester,
        is_active=True
    )
    
    # Get or create submission
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student,
        defaults={'submission_status': 'draft'}
    )
    
    # Check if assignment is overdue
    is_overdue = assignment.due_date < timezone.now()
    can_submit = not is_overdue or assignment.late_submission_allowed
    
    # Get assignment announcements
    announcements = AssignmentAnnouncement.objects.filter(
        assignment=assignment,
        is_active=True
    ).order_by('-posted_date')
    
    context = {
        'student': student,
        'assignment': assignment,
        'enrollment': enrollment,
        'submission': submission,
        'is_overdue': is_overdue,
        'can_submit': can_submit,
        'announcements': announcements,
    }
    
    return render(request, 'student/assignment_detail.html', context)


@login_required
@require_http_methods(["POST"])
def submit_assignment(request, assignment_id):
    """Handle assignment submission"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student profile not found.'})
    
    assignment = get_object_or_404(Assignment, id=assignment_id, is_published=True)
    
    # Check if student is enrolled
    enrollment = Enrollment.objects.filter(
        student=student,
        course=assignment.lecturer_assignment.course,
        semester=assignment.lecturer_assignment.semester,
        is_active=True
    ).first()
    
    if not enrollment:
        return JsonResponse({'success': False, 'message': 'You are not enrolled in this course.'})
    
    # Check if submission is allowed
    is_overdue = assignment.due_date < timezone.now()
    if is_overdue and not assignment.late_submission_allowed:
        return JsonResponse({'success': False, 'message': 'Assignment submission deadline has passed.'})
    
    # Get or create submission
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student
    )
    
    # Check if already submitted
    if submission.is_submitted:
        return JsonResponse({'success': False, 'message': 'Assignment has already been submitted.'})
    
    # Handle file upload
    if 'submission_file' not in request.FILES:
        return JsonResponse({'success': False, 'message': 'Please select a file to upload.'})
    
    uploaded_file = request.FILES['submission_file']
    
    # Validate file size
    max_size = assignment.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
    if uploaded_file.size > max_size:
        return JsonResponse({
            'success': False, 
            'message': f'File size exceeds maximum allowed size of {assignment.max_file_size_mb}MB.'
        })
    
    # Validate file format
    allowed_extensions = {
        'pdf': ['.pdf'],
        'doc': ['.doc', '.docx'],
        'any': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
        'code': ['.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.zip'],
        'presentation': ['.ppt', '.pptx', '.odp']
    }
    
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    if assignment.submission_format in allowed_extensions:
        if file_extension not in allowed_extensions[assignment.submission_format]:
            return JsonResponse({
                'success': False,
                'message': f'Invalid file format. Allowed formats: {", ".join(allowed_extensions[assignment.submission_format])}'
            })
    
    # Update submission
    submission.submission_file = uploaded_file
    submission.original_filename = uploaded_file.name
    submission.file_size = uploaded_file.size
    submission.student_comments = request.POST.get('student_comments', '')
    submission.is_submitted = True
    submission.submitted_date = timezone.now()
    
    if is_overdue:
        submission.is_late = True
        submission.submission_status = 'late'
    else:
        submission.submission_status = 'submitted'
    
    submission.save()
    
    messages.success(request, 'Assignment submitted successfully!')
    return JsonResponse({'success': True, 'message': 'Assignment submitted successfully!'})


@login_required
def student_assignments(request):
    """View all assignments for the student across all courses"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all enrollments for current semester
    enrollments = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).select_related('course')
    
    # Get all assignments for enrolled courses
    assignments = Assignment.objects.filter(
        lecturer_assignment__course__in=[e.course for e in enrollments],
        lecturer_assignment__semester=current_semester,
        is_published=True
    ).select_related(
        'lecturer_assignment', 'lecturer_assignment__course'
    ).order_by('-posted_date')
    
    # Get submission status for each assignment
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__in=assignments
    )
    submission_dict = {sub.assignment_id: sub for sub in submissions}
    
    # Add submission info to assignments
    for assignment in assignments:
        assignment.student_submission = submission_dict.get(assignment.id)
        assignment.is_submitted = assignment.id in submission_dict and submission_dict[assignment.id].is_submitted
        assignment.is_overdue = assignment.due_date < timezone.now()
    
    # Filter assignments based on status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'pending':
        assignments = [a for a in assignments if not a.is_submitted]
    elif status_filter == 'submitted':
        assignments = [a for a in assignments if a.is_submitted]
    elif status_filter == 'overdue':
        assignments = [a for a in assignments if a.is_overdue and not a.is_submitted]
    
    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'student': student,
        'assignments': page_obj,
        'current_semester': current_semester,
        'status_filter': status_filter,
    }
    
    return render(request, 'student/assignments.html', context)


@login_required
def student_grades(request):
    """View student's grades for all courses"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')
    
    # Get all enrollments with grades
    from .models import Grade
    grades = Grade.objects.filter(
        enrollment__student=student
    ).select_related(
        'enrollment', 'enrollment__course', 'enrollment__semester'
    ).order_by('-enrollment__semester__start_date', 'enrollment__course__name')
    
    # Calculate overall GPA
    total_quality_points = sum(g.quality_points or 0 for g in grades if g.quality_points)
    total_credit_hours = sum(g.enrollment.course.credit_hours for g in grades if g.quality_points)
    overall_gpa = total_quality_points / total_credit_hours if total_credit_hours > 0 else 0
    
    # Update student's cumulative GPA
    student.cumulative_gpa = overall_gpa
    student.total_credit_hours = total_credit_hours
    student.save(update_fields=['cumulative_gpa', 'total_credit_hours'])
    
    context = {
        'student': student,
        'grades': grades,
        'overall_gpa': overall_gpa,
        'total_credit_hours': total_credit_hours,
        'passed_courses_count': Grade.objects.filter(
            enrollment__student=student, 
            is_passed=True
        ).count(),
    }
    
    return render(request, 'student/grades_student.html', context)



# views.py - Add these views to your existing views.py file

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal

from .models import (
    LecturerCourseAssignment, Assignment, AssignmentSubmission, 
    Grade, Enrollment, Student, Lecturer
)

@login_required
def assignment_submissions_list(request, assignment_id):
    """View all submissions for a specific assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    lecturer_assignment = assignment.lecturer_assignment
    
    # Verify lecturer has access to this assignment
    if not hasattr(request.user, 'lecturer_profile'):
        messages.error(request, "Access denied. Only lecturers can view submissions.")
        return redirect('lecturer_unit_dashboard')
    
    lecturer = request.user.lecturer_profile
    if lecturer_assignment.lecturer != lecturer:
        messages.error(request, "You don't have permission to view these submissions.")
        return redirect('lecturer_unit_dashboard')
    
    # Get all enrolled students for this course and semester
    enrolled_students = Enrollment.objects.filter(
        course=lecturer_assignment.course,
        semester=lecturer_assignment.semester,
        is_active=True
    ).select_related('student__user', 'student__programme')
    
    # Get all submissions for this assignment
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).select_related('student__user', 'student__programme')
    
    # Create a comprehensive list combining enrolled students and their submissions
    submission_data = []
    submitted_student_ids = set(submissions.values_list('student_id', flat=True))
    
    for enrollment in enrolled_students:
        student = enrollment.student
        try:
            submission = submissions.get(student=student)
        except AssignmentSubmission.DoesNotExist:
            submission = None
        
        submission_data.append({
            'student': student,
            'enrollment': enrollment,
            'submission': submission,
            'has_submitted': submission is not None and submission.is_submitted,
            'is_late': submission.is_late if submission else False,
            'is_graded': submission and submission.grading_status == 'graded',
        })
    
    # Sort by submission status and student name
    submission_data.sort(key=lambda x: (
        not x['has_submitted'],  # Submitted first
        x['is_late'],  # On-time submissions before late ones
        x['student'].user.last_name
    ))
    
    # Pagination
    paginator = Paginator(submission_data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_enrolled = enrolled_students.count()
    total_submitted = submissions.filter(is_submitted=True).count()
    total_graded = submissions.filter(grading_status='graded').count()
    total_pending = total_submitted - total_graded
    late_submissions = submissions.filter(is_late=True, is_submitted=True).count()
    
    # Grade statistics
    graded_submissions = submissions.filter(grading_status='graded', marks_obtained__isnull=False)
    avg_score = graded_submissions.aggregate(avg_score=Avg('percentage_score'))['avg_score']
    
    context = {
        'assignment': assignment,
        'lecturer_assignment': lecturer_assignment,
        'submission_data': page_obj,
        'page_obj': page_obj,
        'stats': {
            'total_enrolled': total_enrolled,
            'total_submitted': total_submitted,
            'total_graded': total_graded,
            'total_pending': total_pending,
            'late_submissions': late_submissions,
            'submission_rate': round((total_submitted / total_enrolled * 100), 1) if total_enrolled > 0 else 0,
            'avg_score': round(avg_score, 1) if avg_score else 0,
        }
    }
    
    return render(request, 'assignment/assignment_submissions_list.html', context)


@login_required
def grade_submission(request, submission_id):
    """Grade a specific submission"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    lecturer_assignment = assignment.lecturer_assignment
    
    # Verify lecturer has access
    if not hasattr(request.user, 'lecturer_profile'):
        messages.error(request, "Access denied.")
        return redirect('lecturer_unit_dashboard')
    
    lecturer = request.user.lecturer_profile
    if lecturer_assignment.lecturer != lecturer:
        messages.error(request, "You don't have permission to grade this submission.")
        return redirect('lecturer_unit_dashboard')
    
    if request.method == 'POST':
        try:
            marks_obtained = Decimal(request.POST.get('marks_obtained', 0))
            lecturer_feedback = request.POST.get('lecturer_feedback', '')
            
            # Validate marks
            if marks_obtained < 0 or marks_obtained > assignment.total_marks:
                messages.error(request, f"Marks must be between 0 and {assignment.total_marks}")
                return redirect('grade_submission', submission_id=submission_id)
            
            # Update submission
            submission.marks_obtained = marks_obtained
            submission.lecturer_feedback = lecturer_feedback
            submission.grading_status = 'graded'
            submission.graded_date = timezone.now()
            submission.graded_by = request.user
            submission.save()
            
            messages.success(request, f"Submission graded successfully. Score: {submission.percentage_score}%")
            
            # Redirect to next ungraded submission or back to list
            next_submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                grading_status='pending',
                is_submitted=True
            ).exclude(id=submission_id).first()
            
            if next_submission and request.POST.get('grade_next'):
                return redirect('grade_submission', submission_id=next_submission.id)
            else:
                return redirect('assignment_submissions_list', assignment_id=assignment.id)
                
        except (ValueError, TypeError) as e:
            messages.error(request, "Invalid marks entered. Please enter a valid number.")
    
    # Get next and previous submissions for navigation
    all_submissions = AssignmentSubmission.objects.filter(
        assignment=assignment,
        is_submitted=True
    ).order_by('student__user__last_name')
    
    submission_ids = list(all_submissions.values_list('id', flat=True))
    current_index = submission_ids.index(submission.id) if submission.id in submission_ids else 0
    
    next_submission = None
    prev_submission = None
    if current_index < len(submission_ids) - 1:
        next_submission = AssignmentSubmission.objects.get(id=submission_ids[current_index + 1])
    if current_index > 0:
        prev_submission = AssignmentSubmission.objects.get(id=submission_ids[current_index - 1])
    
    context = {
        'submission': submission,
        'assignment': assignment,
        'lecturer_assignment': lecturer_assignment,
        'next_submission': next_submission,
        'prev_submission': prev_submission,
        'current_position': current_index + 1,
        'total_submissions': len(submission_ids),
    }
    
    return render(request, 'assignment/grade_submission.html', context)


@login_required
@require_http_methods(["POST"])
def quick_grade_submission(request, submission_id):
    """Quick grade submission via AJAX"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    lecturer_assignment = assignment.lecturer_assignment
    
    # Verify lecturer has access
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    lecturer = request.user.lecturer_profile
    if lecturer_assignment.lecturer != lecturer:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        marks_obtained = Decimal(str(data.get('marks_obtained', 0)))
        feedback = data.get('feedback', '')
        
        # Validate marks
        if marks_obtained < 0 or marks_obtained > assignment.total_marks:
            return JsonResponse({
                'success': False, 
                'message': f'Marks must be between 0 and {assignment.total_marks}'
            })
        
        # Update submission
        submission.marks_obtained = marks_obtained
        submission.lecturer_feedback = feedback
        submission.grading_status = 'graded'
        submission.graded_date = timezone.now()
        submission.graded_by = request.user
        submission.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Submission graded successfully',
            'percentage_score': float(submission.percentage_score),
            'graded_date': submission.graded_date.strftime('%Y-%m-%d %H:%M')
        })
        
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'message': 'Invalid data provided'})


@login_required
def bulk_grade_submissions(request, assignment_id):
    """Bulk grade multiple submissions"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    lecturer_assignment = assignment.lecturer_assignment
    
    # Verify lecturer has access
    if not hasattr(request.user, 'lecturer_profile'):
        messages.error(request, "Access denied.")
        return redirect('lecturer_unit_dashboard')
    
    lecturer = request.user.lecturer_profile
    if lecturer_assignment.lecturer != lecturer:
        messages.error(request, "Permission denied.")
        return redirect('lecturer_unit_dashboard')
    
    if request.method == 'POST':
        try:
            graded_count = 0
            errors = []
            
            for key, value in request.POST.items():
                if key.startswith('marks_'):
                    submission_id = key.replace('marks_', '')
                    try:
                        submission = AssignmentSubmission.objects.get(
                            id=submission_id, 
                            assignment=assignment
                        )
                        marks = Decimal(str(value)) if value else None
                        feedback = request.POST.get(f'feedback_{submission_id}', '')
                        
                        if marks is not None:
                            if marks < 0 or marks > assignment.total_marks:
                                errors.append(f"Invalid marks for {submission.student.user.get_full_name()}")
                                continue
                            
                            submission.marks_obtained = marks
                            submission.lecturer_feedback = feedback
                            submission.grading_status = 'graded'
                            submission.graded_date = timezone.now()
                            submission.graded_by = request.user
                            submission.save()
                            graded_count += 1
                            
                    except (AssignmentSubmission.DoesNotExist, ValueError, TypeError):
                        errors.append(f"Error grading submission {submission_id}")
            
            if graded_count > 0:
                messages.success(request, f"Successfully graded {graded_count} submissions.")
            
            if errors:
                messages.warning(request, f"Errors occurred: {'; '.join(errors)}")
            
            return redirect('assignment_submissions_list', assignment_id=assignment_id)
            
        except Exception as e:
            messages.error(request, "An error occurred during bulk grading.")
    
    # Get all submitted but ungraded submissions
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment,
        is_submitted=True
    ).select_related('student__user').order_by('student__user__last_name')
    
    context = {
        'assignment': assignment,
        'lecturer_assignment': lecturer_assignment,
        'submissions': submissions,
    }
    
    return render(request, 'assignment/bulk_grade_submissions.html', context)


@login_required
def submission_statistics(request, assignment_id):
    """View detailed statistics for assignment submissions"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    lecturer_assignment = assignment.lecturer_assignment
    
    # Verify lecturer has access
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'error': 'Access denied'})
    
    lecturer = request.user.lecturer_profile
    if lecturer_assignment.lecturer != lecturer:
        return JsonResponse({'error': 'Permission denied'})
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment, is_submitted=True)
    
    # Grade distribution
    grade_ranges = [
        {'name': 'A (80-100)', 'min': 80, 'max': 100, 'count': 0},
        {'name': 'B (70-79)', 'min': 70, 'max': 79, 'count': 0},
        {'name': 'C (60-69)', 'min': 60, 'max': 69, 'count': 0},
        {'name': 'D (50-59)', 'min': 50, 'max': 59, 'count': 0},
        {'name': 'F (0-49)', 'min': 0, 'max': 49, 'count': 0},
    ]
    
    for submission in submissions.filter(grading_status='graded'):
        score = submission.percentage_score or 0
        for grade_range in grade_ranges:
            if grade_range['min'] <= score <= grade_range['max']:
                grade_range['count'] += 1
                break
    
    stats = {
        'total_enrolled': Enrollment.objects.filter(
            course=lecturer_assignment.course,
            semester=lecturer_assignment.semester,
            is_active=True
        ).count(),
        'total_submitted': submissions.count(),
        'total_graded': submissions.filter(grading_status='graded').count(),
        'late_submissions': submissions.filter(is_late=True).count(),
        'avg_score': submissions.filter(
            grading_status='graded', 
            percentage_score__isnull=False
        ).aggregate(avg=Avg('percentage_score'))['avg'] or 0,
        'grade_distribution': grade_ranges,
    }
    
    return JsonResponse(stats)

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

@csrf_exempt
def handler404(request, exception=None):
    """ Custom 404 error handler """
    context = {
        'error_code': '404_NOT_FOUND',
        'timestamp': timezone.now().isoformat(),
    }
    return render(request, '404.html', context, status=404)

@csrf_exempt
def handler500(request):
    """ Custom 500 error handler """
    context = {
        'error_code': '500_SERVER_ERROR',
        'timestamp': timezone.now().isoformat(),
    }
    return render(request, '500.html', context, status=500)

def custom_permission_denied(request, exception=None):
    """ Custom 403 error handler """
    return render(request, '403.html', status=403)

def custom_bad_request(request, exception=None):
    """ Custom 400 error handler """
    return render(request, '400.html', status=400)


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime, time
import json

from .models import (
    Programme, Course, Lecturer, Semester, AcademicYear, 
    Timetable, ProgrammeCourse, User
)

@login_required
def timetable_management(request):
    """Main timetable management view"""
    if not request.user.user_type == 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all active programmes
    programmes = Programme.objects.filter(is_active=True).order_by('name')
    
    # Time slots - default university schedule
    time_slots = [
        {'start': '07:00', 'end': '10:00', 'label': '7:00 AM - 10:00 AM'},
        {'start': '10:00', 'end': '13:00', 'label': '10:00 AM - 1:00 PM'},
        {'start': '14:00', 'end': '17:00', 'label': '2:00 PM - 5:00 PM'},
        {'start': '17:00', 'end': '19:00', 'label': '5:00 PM - 7:00 PM'},
    ]
    
    days_of_week = [
        {'key': 'monday', 'label': 'Monday'},
        {'key': 'tuesday', 'label': 'Tuesday'},
        {'key': 'wednesday', 'label': 'Wednesday'},
        {'key': 'thursday', 'label': 'Thursday'},
        {'key': 'friday', 'label': 'Friday'},
    ]
    
    context = {
        'programmes': programmes,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'time_slots': time_slots,
        'days_of_week': days_of_week,
        'years_range': range(1, 5),  # Assuming max 4 years
    }
    
    return render(request, 'admin/timetable_management.html', context)

@login_required
def admin_get_programme_courses(request, programme_id):
    """Get courses for a specific programme and year"""
    if not request.user.user_type == 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        programme = get_object_or_404(Programme, id=programme_id, is_active=True)
        year = request.GET.get('year', 1)
        
        current_semester = Semester.objects.filter(is_current=True).first()
        if not current_semester:
            return JsonResponse({'error': 'No current semester found'}, status=400)
        
        # Get programme courses for the specified year and current semester
        programme_courses = ProgrammeCourse.objects.filter(
            programme=programme,
            year=year,
            semester=current_semester.semester_number,
            is_active=True
        ).select_related('course', 'course__department')
        
        courses = []
        for pc in programme_courses:
            # Get assigned lecturer (if any)
            lecturer = None
            timetable_entry = Timetable.objects.filter(
                course=pc.course,
                programme=programme,
                year=year,
                semester=current_semester,
                is_active=True
            ).first()
            
            if timetable_entry:
                lecturer = timetable_entry.lecturer
            
            courses.append({
                'id': pc.course.id,
                'code': pc.course.code,
                'name': pc.course.name,
                'credit_hours': pc.course.credit_hours,
                'course_type': pc.course.get_course_type_display(),
                'department': pc.course.department.name,
                'lecturer': {
                    'id': lecturer.id if lecturer else None,
                    'name': lecturer.user.get_full_name() if lecturer else 'Not Assigned',
                    'rank': lecturer.academic_rank if lecturer else ''
                }
            })
        
        return JsonResponse({
            'success': True,
            'courses': courses,
            'programme': {
                'id': programme.id,
                'name': programme.name,
                'code': programme.code
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_programme_timetable(request, programme_id):
    """Get existing timetable for a programme"""
    if not request.user.user_type == 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        programme = get_object_or_404(Programme, id=programme_id, is_active=True)
        year = request.GET.get('year', 1)
        
        current_semester = Semester.objects.filter(is_current=True).first()
        if not current_semester:
            return JsonResponse({'error': 'No current semester found'}, status=400)
        
        # Get timetable entries
        timetable_entries = Timetable.objects.filter(
            programme=programme,
            year=year,
            semester=current_semester,
            is_active=True
        ).select_related('course', 'lecturer', 'lecturer__user')
        
        timetable_data = []
        for entry in timetable_entries:
            timetable_data.append({
                'id': entry.id,
                'course_id': entry.course.id,
                'course_code': entry.course.code,
                'course_name': entry.course.name,
                'lecturer_name': entry.lecturer.user.get_full_name(),
                'day_of_week': entry.day_of_week,
                'start_time': entry.start_time.strftime('%H:%M'),
                'end_time': entry.end_time.strftime('%H:%M'),
                'venue': entry.venue,
                'class_type': entry.class_type,
            })
        
        return JsonResponse({
            'success': True,
            'timetable': timetable_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def save_timetable_entry(request):
    """Save a timetable entry via AJAX"""
    if not request.user.user_type == 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        course_id = data.get('course_id')
        programme_id = data.get('programme_id')
        year = data.get('year')
        day_of_week = data.get('day_of_week')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        venue = data.get('venue', 'TBA')
        class_type = data.get('class_type', 'lecture')
        
        # Validate required fields
        if not all([course_id, programme_id, year, day_of_week, start_time, end_time]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get objects
        course = get_object_or_404(Course, id=course_id)
        programme = get_object_or_404(Programme, id=programme_id)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            return JsonResponse({'error': 'No current semester found'}, status=400)
        
        # Get a lecturer for the course (preferably from the same department)
        lecturer = Lecturer.objects.filter(
            department=course.department,
            is_active=True
        ).first()
        
        if not lecturer:
            # Get any available lecturer
            lecturer = Lecturer.objects.filter(is_active=True).first()
        
        if not lecturer:
            return JsonResponse({'error': 'No lecturer available'}, status=400)
        
        # Parse time strings
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        
        with transaction.atomic():
            # Check for conflicts
            conflicts = Timetable.objects.filter(
                programme=programme,
                year=year,
                semester=current_semester,
                day_of_week=day_of_week,
                start_time__lt=end_time_obj,
                end_time__gt=start_time_obj,
                is_active=True
            ).exclude(course=course)
            
            if conflicts.exists():
                return JsonResponse({
                    'error': 'Time slot conflict detected',
                    'conflicts': list(conflicts.values('course__code', 'start_time', 'end_time'))
                }, status=400)
            
            # Check if entry already exists and update, otherwise create
            timetable_entry, created = Timetable.objects.update_or_create(
                course=course,
                programme=programme,
                year=year,
                semester=current_semester,
                defaults={
                    'lecturer': lecturer,
                    'day_of_week': day_of_week,
                    'start_time': start_time_obj,
                    'end_time': end_time_obj,
                    'venue': venue,
                    'class_type': class_type,
                    'semester_number': current_semester.semester_number,
                    'is_active': True
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Timetable entry saved successfully',
            'entry': {
                'id': timetable_entry.id,
                'course_code': course.code,
                'course_name': course.name,
                'lecturer_name': lecturer.user.get_full_name(),
                'day_of_week': day_of_week,
                'start_time': start_time,
                'end_time': end_time,
                'venue': venue,
                'class_type': class_type,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def delete_timetable_entry(request, entry_id):
    """Delete a timetable entry"""
    if not request.user.user_type == 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        entry = get_object_or_404(Timetable, id=entry_id)
        entry.is_active = False  # Soft delete
        entry.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Timetable entry deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_available_lecturers(request):
    """Get available lecturers for a course"""
    if not request.user.user_type == 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        course_id = request.GET.get('course_id')
        if not course_id:
            return JsonResponse({'error': 'Course ID required'}, status=400)
        
        course = get_object_or_404(Course, id=course_id)
        
        # Get lecturers from the same department first, then others
        department_lecturers = Lecturer.objects.filter(
            department=course.department,
            is_active=True
        ).select_related('user')
        
        other_lecturers = Lecturer.objects.filter(
            is_active=True
        ).exclude(
            department=course.department
        ).select_related('user')
        
        lecturers_data = []
        
        # Add department lecturers first
        for lecturer in department_lecturers:
            lecturers_data.append({
                'id': lecturer.id,
                'name': lecturer.user.get_full_name(),
                'rank': lecturer.academic_rank,
                'department': lecturer.department.name,
                'preferred': True
            })
        
        # Add other lecturers
        for lecturer in other_lecturers:
            lecturers_data.append({
                'id': lecturer.id,
                'name': lecturer.user.get_full_name(),
                'rank': lecturer.academic_rank,
                'department': lecturer.department.name,
                'preferred': False
            })
        
        return JsonResponse({
            'success': True,
            'lecturers': lecturers_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from collections import defaultdict
from datetime import time
from .models import (
    Student, Lecturer, Timetable, AcademicYear, Semester, 
    Enrollment, Course, Programme
)

@login_required
def student_timetable_view(request):
    """View for students to see their timetable"""
    try:
        # Get student profile
        student = get_object_or_404(Student, user=request.user)
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_academic_year or not current_semester:
            context = {
                'error': 'No active academic year or semester found.',
                'student': student,
            }
            return render(request, 'students/student_timetable.html', context)
        
        # Get student's enrolled courses for current semester
        enrollments = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('course', 'lecturer')
        
        if not enrollments.exists():
            context = {
                'error': 'No course enrollments found for current semester.',
                'student': student,
                'current_academic_year': current_academic_year,
                'current_semester': current_semester,
            }
            return render(request, 'students/student_timetable.html', context)
        
        # Get course codes for enrolled courses
        enrolled_courses = [enrollment.course for enrollment in enrollments]
        
        # Get timetable entries for enrolled courses
        timetable_entries = Timetable.objects.filter(
            course__in=enrolled_courses,
            semester=current_semester,
            programme=student.programme,
            year=student.current_year,
            is_active=True
        ).select_related('course', 'lecturer', 'lecturer__user').order_by('day_of_week', 'start_time')
        
        # Define time slots (you can customize these)
        time_slots = [
            {'start': time(7, 0), 'end': time(10, 0), 'label': '7:00 - 10:00 AM'},
            {'start': time(10, 0), 'end': time(13, 0), 'label': '10:00 - 1:00 PM'},
            {'start': time(14, 0), 'end': time(17, 0), 'label': '2:00 - 5:00 PM'},
            {'start': time(17, 0), 'end': time(19, 0), 'label': '5:00 - 7:00 PM'},
        ]
        
        # Days of the week
        days_of_week = [
            {'key': 'monday', 'label': 'Monday'},
            {'key': 'tuesday', 'label': 'Tuesday'},
            {'key': 'wednesday', 'label': 'Wednesday'},
            {'key': 'thursday', 'label': 'Thursday'},
            {'key': 'friday', 'label': 'Friday'},
            {'key': 'saturday', 'label': 'Saturday'},
        ]
        
        # Organize timetable data
        timetable_grid = defaultdict(lambda: defaultdict(list))
        
        for entry in timetable_entries:
            # Find matching time slot
            for slot in time_slots:
                if entry.start_time >= slot['start'] and entry.start_time < slot['end']:
                    timetable_grid[entry.day_of_week][slot['start']].append(entry)
                    break
        
        # Calculate statistics
        total_courses = len(enrolled_courses)
        total_classes = timetable_entries.count()
        total_credit_hours = sum(course.credit_hours for course in enrolled_courses)
        
        context = {
            'student': student,
            'programme': student.programme,
            'current_academic_year': current_academic_year,
            'current_semester': current_semester,
            'timetable_grid': dict(timetable_grid),
            'time_slots': time_slots,
            'days_of_week': days_of_week,
            'enrolled_courses': enrolled_courses,
            'enrollments': enrollments,
            'stats': {
                'total_courses': total_courses,
                'total_classes': total_classes,
                'total_credit_hours': total_credit_hours,
            }
        }
        
        return render(request, 'student/student_timetable.html', context)
        
    except Student.DoesNotExist:
        context = {
            'error': 'Student profile not found.',
        }
        return render(request, 'student/student_timetable.html', context)
    
    except Exception as e:
        context = {
            'error': f'An error occurred: {str(e)}',
        }
        return render(request, 'student/student_timetable.html', context)



@login_required
def lecturer_timetable_view(request):
    """View for lecturers to see their teaching schedule"""
    try:
        # Get lecturer profile
        lecturer = get_object_or_404(Lecturer, user=request.user)
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_academic_year or not current_semester:
            context = {
                'error': 'No active academic year or semester found.',
                'lecturer': lecturer,
            }
            return render(request, 'lecturers/lecturer_timetable.html', context)
        
        # Get lecturer's teaching assignments for current semester
        timetable_entries = Timetable.objects.filter(
            lecturer=lecturer,
            semester=current_semester,
            is_active=True
        ).select_related('course', 'programme').order_by('day_of_week', 'start_time')
        
        if not timetable_entries.exists():
            context = {
                'error': 'No teaching assignments found for current semester.',
                'lecturer': lecturer,
                'current_academic_year': current_academic_year,
                'current_semester': current_semester,
            }
            return render(request, 'lecturers/lecturer_timetable.html', context)
        
        # Define time slots
        time_slots = [
            {'start': time(7, 0), 'end': time(10, 0), 'label': '7:00 - 10:00 AM'},
            {'start': time(10, 0), 'end': time(13, 0), 'label': '10:00 - 1:00 PM'},
            {'start': time(14, 0), 'end': time(17, 0), 'label': '2:00 - 5:00 PM'},
            {'start': time(17, 0), 'end': time(19, 0), 'label': '5:00 - 7:00 PM'},
        ]
        
        # Days of the week
        days_of_week = [
            {'key': 'monday', 'label': 'Monday'},
            {'key': 'tuesday', 'label': 'Tuesday'},
            {'key': 'wednesday', 'label': 'Wednesday'},
            {'key': 'thursday', 'label': 'Thursday'},
            {'key': 'friday', 'label': 'Friday'},
            {'key': 'saturday', 'label': 'Saturday'},
        ]
        
        # Organize timetable data - group multiple courses in same time slot
        timetable_grid = defaultdict(lambda: defaultdict(list))
        
        for entry in timetable_entries:
            # Find matching time slot
            for slot in time_slots:
                if entry.start_time >= slot['start'] and entry.start_time < slot['end']:
                    timetable_grid[entry.day_of_week][slot['start']].append(entry)
                    break
        
        # Get unique courses and programmes
        unique_courses = timetable_entries.values_list('course__code', 'course__name').distinct()
        unique_programmes = timetable_entries.values_list('programme__code', 'programme__name').distinct()
        
        # Calculate statistics
        total_courses = len(unique_courses)
        total_classes = timetable_entries.count()
        total_programmes = len(unique_programmes)
        
        # Get weekly teaching hours
        weekly_hours = 0
        for entry in timetable_entries:
            # Calculate duration in hours
            start_datetime = entry.start_time
            end_datetime = entry.end_time
            duration = (end_datetime.hour - start_datetime.hour) + (end_datetime.minute - start_datetime.minute) / 60.0
            weekly_hours += duration
        
        context = {
            'lecturer': lecturer,
            'current_academic_year': current_academic_year,
            'current_semester': current_semester,
            'timetable_grid': dict(timetable_grid),
            'time_slots': time_slots,
            'days_of_week': days_of_week,
            'timetable_entries': timetable_entries,
            'unique_courses': unique_courses,
            'unique_programmes': unique_programmes,
            'stats': {
                'total_courses': total_courses,
                'total_classes': total_classes,
                'total_programmes': total_programmes,
                'weekly_hours': round(weekly_hours, 1),
            }
        }
        
        return render(request, 'lecturers/lecturer_timetable.html', context)
        
    except Lecturer.DoesNotExist:
        context = {
            'error': 'Lecturer profile not found.',
        }
        return render(request, 'lecturers/lecturer_timetable.html', context)
    
    except Exception as e:
        context = {
            'error': f'An error occurred: {str(e)}',
        }
        return render(request, 'lecturers/lecturer_timetable.html', context)
    

    # views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from .models import (
    AttendanceSession, Attendance, Timetable, Student, Lecturer, 
    Semester, AcademicYear, Enrollment
)

@login_required
def lecturer_generate_qr_attendance(request, timetable_id):
    """Lecturer view to generate QR code for attendance"""
    try:
        lecturer = get_object_or_404(Lecturer, user=request.user)
        timetable_slot = get_object_or_404(Timetable, id=timetable_id, lecturer=lecturer)
        
        # Get current semester
        current_semester = Semester.objects.filter(is_current=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return redirect('lecturer_dashboard')
        
        if request.method == 'POST':
            week_number = request.POST.get('week_number')
            session_date = request.POST.get('session_date')
            
            if not week_number or not session_date:
                messages.error(request, "Week number and session date are required.")
                return redirect(request.META.get('HTTP_REFERER', 'lecturer_dashboard'))
            
            try:
                # Check if session already exists for this week
                existing_session = AttendanceSession.objects.filter(
                    timetable_slot=timetable_slot,
                    week_number=week_number,
                    session_date=session_date
                ).first()
                
                if existing_session:
                    if existing_session.is_expired:
                        # Deactivate expired session and create new one
                        existing_session.is_active = False
                        existing_session.save()
                    else:
                        messages.info(request, f"Attendance session for Week {week_number} already exists and is still active.")
                        return redirect('lecturer_attendance_dashboard')
                
                # Create new attendance session
                attendance_session = AttendanceSession.objects.create(
                    timetable_slot=timetable_slot,
                    lecturer=lecturer,
                    semester=current_semester,
                    week_number=week_number,
                    session_date=session_date
                )
                
                messages.success(request, f"QR Code generated successfully for Week {week_number}!")
                return redirect('lecturer_attendance_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error creating attendance session: {str(e)}")
                return redirect('lecturer_attendance_dashboard')
        
        # Get enrolled students for this course
        enrolled_students = Student.objects.filter(
            enrollments__course=timetable_slot.course,
            enrollments__semester=current_semester,
            enrollments__is_active=True
        ).count()
        
        # Get existing sessions for this timetable slot
        existing_sessions = AttendanceSession.objects.filter(
            timetable_slot=timetable_slot,
            semester=current_semester
        ).order_by('-week_number')
        
        context = {
            'timetable_slot': timetable_slot,
            'lecturer': lecturer,
            'current_semester': current_semester,
            'enrolled_students': enrolled_students,
            'existing_sessions': existing_sessions,
            'week_choices': AttendanceSession.WEEK_CHOICES,
        }
        
        return render(request, 'lecturers/generate_qr_attendance.html', context)
        
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found.")
        return redirect('lecturer_dashboard')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('lecturer_dashboard')


@login_required
def lecturer_attendance_dashboard(request):
    """Lecturer dashboard to view all attendance sessions and statistics"""
    try:
        lecturer = get_object_or_404(Lecturer, user=request.user)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            messages.error(request, "No active semester found.")
            return redirect('lecturer_dashboard')
        
        # Get lecturer's timetable slots for current semester
        timetable_slots = Timetable.objects.filter(
            lecturer=lecturer,
            semester=current_semester,
            is_active=True
        ).select_related('course', 'programme').order_by('day_of_week', 'start_time')
        
        # Get attendance sessions with statistics
        attendance_sessions = AttendanceSession.objects.filter(
            lecturer=lecturer,
            semester=current_semester
        ).select_related('timetable_slot__course').annotate(
            total_attendance=Count('attendance_records'),
            present_count=Count('attendance_records', filter=Q(attendance_records__status='present')),
            absent_count=Count('attendance_records', filter=Q(attendance_records__status='absent')),
            late_count=Count('attendance_records', filter=Q(attendance_records__status='late'))
        ).order_by('-created_at')
        
        # Paginate sessions
        paginator = Paginator(attendance_sessions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get overall statistics
        total_sessions = attendance_sessions.count()
        active_sessions = attendance_sessions.filter(is_active=True, expires_at__gt=timezone.now()).count()
        total_courses = timetable_slots.values('course').distinct().count()
        
        # Get attendance summary by course
        course_attendance = []
        for slot in timetable_slots:
            sessions = AttendanceSession.objects.filter(
                timetable_slot=slot,
                semester=current_semester
            )
            total_possible_attendance = 0
            actual_attendance = 0
            
            for session in sessions:
                enrolled_count = Student.objects.filter(
                    enrollments__course=slot.course,
                    enrollments__semester=current_semester,
                    enrollments__is_active=True
                ).count()
                present_count = Attendance.objects.filter(
                    attendance_session=session,
                    status='present'
                ).count()
                
                total_possible_attendance += enrolled_count
                actual_attendance += present_count
            
            attendance_rate = (actual_attendance / total_possible_attendance * 100) if total_possible_attendance > 0 else 0
            
            course_attendance.append({
                'course': slot.course,
                'timetable_slot': slot,
                'sessions_count': sessions.count(),
                'attendance_rate': round(attendance_rate, 1),
                'total_possible': total_possible_attendance,
                'actual_attendance': actual_attendance
            })
        
        context = {
            'lecturer': lecturer,
            'current_semester': current_semester,
            'timetable_slots': timetable_slots,
            'attendance_sessions': page_obj,
            'course_attendance': course_attendance,
            'stats': {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_courses': total_courses,
            }
        }
        
        return render(request, 'lecturers/attendance_dashboard.html', context)
        
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found.")
        return redirect('lecturer_dashboard')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('lecturer_dashboard')


def mark_attendance_qr(request, token):
    """Student marks attendance via QR code"""
    try:
        # Get attendance session by token
        attendance_session = get_object_or_404(AttendanceSession, session_token=token)
        
        # Check if session is still active and not expired
        if not attendance_session.is_active or attendance_session.is_expired:
            return render(request, 'student/attendance_error.html', {
                'error': 'This attendance session has expired or is no longer active.',
                'session': attendance_session
            })
        
        if request.method == 'POST':
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'message': 'You must be logged in to mark attendance.'
                })
            
            try:
                student = get_object_or_404(Student, user=request.user)
                
                # Check if student is enrolled in this course
                enrollment = Enrollment.objects.filter(
                    student=student,
                    course=attendance_session.timetable_slot.course,
                    semester=attendance_session.semester,
                    is_active=True
                ).first()
                
                if not enrollment:
                    return JsonResponse({
                        'success': False,
                        'message': 'You are not enrolled in this course.'
                    })
                
                # Check if attendance already marked for this session
                existing_attendance = Attendance.objects.filter(
                    student=student,
                    attendance_session=attendance_session
                ).first()
                
                if existing_attendance:
                    return JsonResponse({
                        'success': False,
                        'message': 'You have already marked attendance for this session.'
                    })
                
                # Mark attendance
                attendance = Attendance.objects.create(
                    student=student,
                    attendance_session=attendance_session,
                    timetable_slot=attendance_session.timetable_slot,
                    week_number=attendance_session.week_number,
                    status='present',
                    marked_via_qr=True,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Attendance marked successfully!',
                    'attendance_id': attendance.id
                })
                
            except Student.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Student profile not found.'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error marking attendance: {str(e)}'
                })
        
        # GET request - show attendance form
        context = {
            'attendance_session': attendance_session,
            'course': attendance_session.timetable_slot.course,
            'lecturer': attendance_session.lecturer,
            'week_number': attendance_session.week_number,
            'expires_at': attendance_session.expires_at,
        }
        
        return render(request, 'student/mark_attendance_qr.html', context)
        
    except AttendanceSession.DoesNotExist:
        return render(request, 'student/attendance_error.html', {
            'error': 'Invalid attendance session. The QR code may be corrupted or expired.'
        })
    except Exception as e:
        return render(request, 'student/attendance_error.html', {
            'error': f'An error occurred: {str(e)}'
        })


@login_required
def lecturer_attendance_detail(request, session_id):
    """Detailed view of a specific attendance session"""
    try:
        lecturer = get_object_or_404(Lecturer, user=request.user)
        attendance_session = get_object_or_404(
            AttendanceSession, 
            id=session_id, 
            lecturer=lecturer
        )
        
        # Get all attendance records for this session
        attendance_records = Attendance.objects.filter(
            attendance_session=attendance_session
        ).select_related('student__user').order_by('student__user__first_name')
        
        # Get enrolled students who haven't marked attendance
        enrolled_students = Student.objects.filter(
            enrollments__course=attendance_session.timetable_slot.course,
            enrollments__semester=attendance_session.semester,
            enrollments__is_active=True
        ).exclude(
            id__in=attendance_records.values_list('student_id', flat=True)
        ).select_related('user')
        
        # Statistics
        total_enrolled = Student.objects.filter(
            enrollments__course=attendance_session.timetable_slot.course,
            enrollments__semester=attendance_session.semester,
            enrollments__is_active=True
        ).count()
        
        present_count = attendance_records.filter(status='present').count()
        absent_count = enrolled_students.count()  # Students who didn't mark attendance
        late_count = attendance_records.filter(status='late').count()
        
        attendance_rate = (present_count / total_enrolled * 100) if total_enrolled > 0 else 0
        
        context = {
            'attendance_session': attendance_session,
            'attendance_records': attendance_records,
            'absent_students': enrolled_students,
            'lecturer': lecturer,
            'stats': {
                'total_enrolled': total_enrolled,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'attendance_rate': round(attendance_rate, 1)
            }
        }
        
        return render(request, 'lecturers/attendance_detail.html', context)
        
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found.")
        return redirect('lecturer_dashboard')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('lecturer_attendance_dashboard')


@login_required
def student_attendance_history(request):
    """Student view of their attendance history"""
    try:
        student = get_object_or_404(Student, user=request.user)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            messages.error(request, "No active semester found.")
            return redirect('student_dashboard')
        
        # Get student's attendance records for current semester
        attendance_records = Attendance.objects.filter(
            student=student,
            attendance_session__semester=current_semester
        ).select_related(
            'timetable_slot__course',
            'attendance_session'
        ).order_by('-marked_at')
        
        # Get attendance summary by course
        course_attendance = {}
        enrolled_courses = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('course')
        
        for enrollment in enrolled_courses:
            course_records = attendance_records.filter(
                timetable_slot__course=enrollment.course
            )
            
            total_sessions = AttendanceSession.objects.filter(
                timetable_slot__course=enrollment.course,
                semester=current_semester
            ).count()
            
            present_count = course_records.filter(status='present').count()
            late_count = course_records.filter(status='late').count()
            absent_count = total_sessions - course_records.count()
            
            attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0
            
            course_attendance[enrollment.course.id] = {
                'course': enrollment.course,
                'total_sessions': total_sessions,
                'present_count': present_count,
                'late_count': late_count,
                'absent_count': absent_count,
                'attendance_rate': round(attendance_rate, 1),
                'records': course_records
            }
        
        context = {
            'student': student,
            'current_semester': current_semester,
            'attendance_records': attendance_records,
            'course_attendance': course_attendance,
        }
        
        return render(request, 'student/attendance_history.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('student_dashboard')

def scan_attendance_qr(request):
    """View to scan QR code for attendance"""
    context = {
        'page_title': 'Scan QR Code for Attendance',
    }
    return render(request, 'student/scan_attendance_qr.html', context)


def lecturer_support(request):
    return render( request, 'lecturers/support.html')

def lecturer_training(request):
    return render( request, 'lecturers/lecturer_training.html')

def curriculum(request):
    return render( request, 'lecturers/curriculum.html')



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
import json

from .models import (
    Student, Lecturer, AcademicYear, Semester, Enrollment, 
    Grade, LecturerCourseAssignment, Course
)

@login_required
def grade_entry(request):
    """Main grade entry page for lecturers"""
    # Ensure user is a lecturer
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, "Access denied. Only lecturers can access this page.")
        return redirect('lecturer_dashboard')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all academic years and semesters for the dropdown
    academic_years = AcademicYear.objects.all().order_by('-year')
    semesters = Semester.objects.all().order_by('-academic_year__year', '-semester_number')
    
    # Get lecturer's assigned courses for current semester
    lecturer_assignments = LecturerCourseAssignment.objects.filter(
        lecturer=lecturer,
        is_active=True
    ).select_related('course', 'academic_year', 'semester')
    
    context = {
        'lecturer': lecturer,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'academic_years': academic_years,
        'semesters': semesters,
        'lecturer_assignments': lecturer_assignments,
    }
    
    return render(request, 'lecturers/grade_entry.html', context)


@login_required
@require_http_methods(["POST"])
def get_student_enrollments(request):
    """AJAX view to get student enrollments for a specific academic year and semester"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        student_reg_number = data.get('student_reg_number', '').strip()
        academic_year_id = data.get('academic_year_id')
        semester_id = data.get('semester_id')
        
        if not all([student_reg_number, academic_year_id, semester_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get student
        try:
            student = Student.objects.get(student_id=student_reg_number)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        
        # Get academic year and semester
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        semester = get_object_or_404(Semester, id=semester_id)
        
        # Get lecturer's assigned courses for this semester
        lecturer_courses = LecturerCourseAssignment.objects.filter(
            lecturer=lecturer,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        ).values_list('course_id', flat=True)
        
        if not lecturer_courses:
            return JsonResponse({'error': 'You have no course assignments for this academic year and semester'}, status=403)
        
        # Get student enrollments for courses assigned to this lecturer
        enrollments = Enrollment.objects.filter(
            student=student,
            semester=semester,
            course_id__in=lecturer_courses,
            is_active=True
        ).select_related('course', 'lecturer').prefetch_related('grade')
        
        if not enrollments:
            return JsonResponse({'error': 'No enrollments found for this student in your assigned courses'}, status=404)
        
        # Prepare enrollment data with existing grades
        enrollment_data = []
        for enrollment in enrollments:
            # Get existing grade if any
            try:
                grade = enrollment.grade
                grade_data = {
                    'continuous_assessment': float(grade.continuous_assessment) if grade.continuous_assessment else '',
                    'final_exam': float(grade.final_exam) if grade.final_exam else '',
                    'practical_marks': float(grade.practical_marks) if grade.practical_marks else '',
                    'project_marks': float(grade.project_marks) if grade.project_marks else '',
                    'total_marks': float(grade.total_marks) if grade.total_marks else '',
                    'grade': grade.grade or '',
                    'grade_points': float(grade.grade_points) if grade.grade_points else '',
                    'is_passed': grade.is_passed,
                    'remarks': grade.remarks or ''
                }
            except Grade.DoesNotExist:
                grade_data = {
                    'continuous_assessment': '',
                    'final_exam': '',
                    'practical_marks': '',
                    'project_marks': '',
                    'total_marks': '',
                    'grade': '',
                    'grade_points': '',
                    'is_passed': False,
                    'remarks': ''
                }
            
            enrollment_data.append({
                'enrollment_id': enrollment.id,
                'course_code': enrollment.course.code,
                'course_name': enrollment.course.name,
                'credit_hours': enrollment.course.credit_hours,
                'course_type': enrollment.course.get_course_type_display(),
                'is_repeat': enrollment.is_repeat,
                'grade_data': grade_data
            })
        
        return JsonResponse({
            'success': True,
            'student': {
                'student_id': student.student_id,
                'name': student.user.get_full_name(),
                'programme': student.programme.name,
                'current_year': student.current_year,
                'current_semester': student.current_semester
            },
            'academic_year': academic_year.year,
            'semester': f"Semester {semester.semester_number}",
            'enrollments': enrollment_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_grades(request):
    """AJAX view to save/update student grades"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        grades_data = data.get('grades', [])
        
        if not grades_data:
            return JsonResponse({'error': 'No grade data provided'}, status=400)
        
        saved_grades = []
        errors = []
        
        with transaction.atomic():
            for grade_item in grades_data:
                try:
                    enrollment_id = grade_item.get('enrollment_id')
                    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
                    
                    # Verify lecturer has permission to grade this enrollment
                    lecturer_assignment = LecturerCourseAssignment.objects.filter(
                        lecturer=lecturer,
                        course=enrollment.course,
                        academic_year=enrollment.semester.academic_year,
                        semester=enrollment.semester,
                        is_active=True
                    ).first()
                    
                    if not lecturer_assignment:
                        errors.append(f"No permission to grade {enrollment.course.code}")
                        continue
                    
                    # Get or create grade object
                    grade, created = Grade.objects.get_or_create(
                        enrollment=enrollment,
                        defaults={'exam_date': enrollment.semester.end_date}
                    )
                    
                    # Update grade fields
                    continuous_assessment = grade_item.get('continuous_assessment')
                    final_exam = grade_item.get('final_exam')
                    practical_marks = grade_item.get('practical_marks')
                    project_marks = grade_item.get('project_marks')
                    remarks = grade_item.get('remarks', '')
                    
                    # Validate and set marks
                    if continuous_assessment is not None and continuous_assessment != '':
                        if 0 <= float(continuous_assessment) <= 40:
                            grade.continuous_assessment = float(continuous_assessment)
                        else:
                            errors.append(f"{enrollment.course.code}: CAT marks must be between 0-40")
                            continue
                    
                    if final_exam is not None and final_exam != '':
                        if 0 <= float(final_exam) <= 60:
                            grade.final_exam = float(final_exam)
                        else:
                            errors.append(f"{enrollment.course.code}: Final exam marks must be between 0-60")
                            continue
                    
                    if practical_marks is not None and practical_marks != '':
                        if 0 <= float(practical_marks) <= 100:
                            grade.practical_marks = float(practical_marks)
                        else:
                            errors.append(f"{enrollment.course.code}: Practical marks must be between 0-100")
                            continue
                    
                    if project_marks is not None and project_marks != '':
                        if 0 <= float(project_marks) <= 100:
                            grade.project_marks = float(project_marks)
                        else:
                            errors.append(f"{enrollment.course.code}: Project marks must be between 0-100")
                            continue
                    
                    grade.remarks = remarks
                    grade.save()  # This will trigger the grade calculation in the model
                    
                    saved_grades.append({
                        'course_code': enrollment.course.code,
                        'total_marks': float(grade.total_marks) if grade.total_marks else 0,
                        'grade': grade.grade,
                        'grade_points': float(grade.grade_points) if grade.grade_points else 0,
                        'is_passed': grade.is_passed
                    })
                    
                except ValueError as e:
                    errors.append(f"{enrollment.course.code}: Invalid numeric value")
                except Exception as e:
                    errors.append(f"{enrollment.course.code}: {str(e)}")
        
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors,
                'saved_grades': saved_grades
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully saved grades for {len(saved_grades)} courses',
            'saved_grades': saved_grades
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_semesters_by_year(request):
    """AJAX view to get semesters for a specific academic year"""
    academic_year_id = request.GET.get('academic_year_id')
    
    if not academic_year_id:
        return JsonResponse({'error': 'Academic year ID required'}, status=400)
    
    try:
        semesters = Semester.objects.filter(
            academic_year_id=academic_year_id
        ).order_by('semester_number').values('id', 'semester_number', 'start_date', 'end_date')
        
        return JsonResponse({
            'success': True,
            'semesters': list(semesters)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    Student, Lecturer, AcademicYear, Semester, Enrollment, 
    LecturerCourseAssignment, Course, Timetable, AttendanceSession, 
    Attendance
)

@login_required
def my_students(request):
    """Main view showing lecturer's assigned courses and students"""
    # Ensure user is a lecturer
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, "Access denied. Only lecturers can access this page.")
        return redirect('lecturer_dashboard')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all academic years and semesters for the dropdown
    academic_years = AcademicYear.objects.all().order_by('-year')
    semesters = Semester.objects.all().order_by('-academic_year__year', '-semester_number')
    
    # Get lecturer's course assignments for current semester
    lecturer_assignments = LecturerCourseAssignment.objects.filter(
        lecturer=lecturer,
        is_active=True
    ).select_related('course', 'academic_year', 'semester').prefetch_related(
        'course__enrollments__student__user'
    )
    
    # Get course statistics
    course_stats = []
    for assignment in lecturer_assignments:
        # Get enrolled students for this course in this semester
        enrolled_students = Enrollment.objects.filter(
            course=assignment.course,
            semester=assignment.semester,
            is_active=True
        ).select_related('student__user')
        
        # Get attendance sessions for this course
        attendance_sessions = AttendanceSession.objects.filter(
            timetable_slot__course=assignment.course,
            semester=assignment.semester,
            lecturer=lecturer
        ).count()
        
        # Calculate average attendance
        total_sessions = attendance_sessions
        if total_sessions > 0:
            total_possible_attendance = enrolled_students.count() * total_sessions
            present_count = Attendance.objects.filter(
                timetable_slot__course=assignment.course,
                attendance_session__semester=assignment.semester,
                status__in=['present', 'late']
            ).count()
            attendance_percentage = round((present_count / total_possible_attendance * 100), 1) if total_possible_attendance > 0 else 0
        else:
            attendance_percentage = 0
        
        course_stats.append({
            'assignment': assignment,
            'student_count': enrolled_students.count(),
            'attendance_sessions': total_sessions,
            'attendance_percentage': attendance_percentage,
            'students': enrolled_students
        })
    
    context = {
        'lecturer': lecturer,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'academic_years': academic_years,
        'semesters': semesters,
        'course_stats': course_stats,
        'total_courses': lecturer_assignments.count(),
        'total_students': sum(stat['student_count'] for stat in course_stats),
    }
    
    return render(request, 'lecturers/my_students.html', context)


@login_required
@require_http_methods(["POST"])
def get_course_students(request):
    """AJAX view to get students for a specific course and their attendance"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        academic_year_id = data.get('academic_year_id')
        semester_id = data.get('semester_id')
        
        if not all([course_id, academic_year_id, semester_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get course assignment
        try:
            assignment = LecturerCourseAssignment.objects.get(
                lecturer=lecturer,
                course_id=course_id,
                academic_year_id=academic_year_id,
                semester_id=semester_id,
                is_active=True
            )
        except LecturerCourseAssignment.DoesNotExist:
            return JsonResponse({'error': 'Course assignment not found'}, status=404)
        
        # Get enrolled students
        enrollments = Enrollment.objects.filter(
            course=assignment.course,
            semester=assignment.semester,
            is_active=True
        ).select_related('student__user', 'student__programme').order_by('student__student_id')
        
        # Get attendance sessions for this course
        attendance_sessions = AttendanceSession.objects.filter(
            timetable_slot__course=assignment.course,
            semester=assignment.semester,
            lecturer=lecturer
        ).order_by('week_number', 'session_date')
        
        # Prepare student data with attendance records
        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            
            # Get attendance records for this student
            attendance_records = Attendance.objects.filter(
                student=student,
                timetable_slot__course=assignment.course,
                attendance_session__semester=assignment.semester
            ).order_by('week_number')
            
            # Create attendance summary
            attendance_summary = {}
            total_sessions = attendance_sessions.count()
            present_count = 0
            
            for record in attendance_records:
                attendance_summary[record.week_number] = {
                    'status': record.status,
                    'marked_at': record.marked_at.strftime('%Y-%m-%d %H:%M'),
                    'marked_via_qr': record.marked_via_qr,
                    'remarks': record.remarks
                }
                if record.status in ['present', 'late']:
                    present_count += 1
            
            # Calculate attendance percentage
            attendance_percentage = round((present_count / total_sessions * 100), 1) if total_sessions > 0 else 0
            
            students_data.append({
                'student_id': student.student_id,
                'name': student.user.get_full_name(),
                'email': student.user.email,
                'phone': student.user.phone,
                'programme': student.programme.name,
                'year': student.current_year,
                'semester': student.current_semester,
                'attendance_summary': attendance_summary,
                'attendance_percentage': attendance_percentage,
                'total_present': present_count,
                'total_sessions': total_sessions
            })
        
        # Prepare attendance sessions data
        sessions_data = []
        for session in attendance_sessions:
            sessions_data.append({
                'week_number': session.week_number,
                'session_date': session.session_date.strftime('%Y-%m-%d'),
                'day_of_week': session.timetable_slot.day_of_week.title(),
                'start_time': session.timetable_slot.start_time.strftime('%H:%M'),
                'end_time': session.timetable_slot.end_time.strftime('%H:%M'),
                'venue': session.timetable_slot.venue,
                'is_active': session.is_active,
                'is_expired': session.is_expired
            })
        
        return JsonResponse({
            'success': True,
            'course': {
                'code': assignment.course.code,
                'name': assignment.course.name,
                'credit_hours': assignment.course.credit_hours,
                'course_type': assignment.course.get_course_type_display()
            },
            'academic_info': {
                'academic_year': assignment.academic_year.year,
                'semester': f"Semester {assignment.semester.semester_number}"
            },
            'students': students_data,
            'attendance_sessions': sessions_data,
            'summary': {
                'total_students': len(students_data),
                'total_sessions': len(sessions_data),
                'average_attendance': round(sum(s['attendance_percentage'] for s in students_data) / len(students_data), 1) if students_data else 0
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_attendance(request):
    """AJAX view to manually update student attendance"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        student_id_number = data.get('student_id')
        course_id = data.get('course_id')
        semester_id = data.get('semester_id')
        week_number = data.get('week_number')
        status = data.get('status')
        remarks = data.get('remarks', '')
        
        if not all([student_id_number, course_id, semester_id, week_number, status]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get student
        try:
            student = Student.objects.get(student_id=student_id_number)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        
        # Verify lecturer has permission
        assignment = LecturerCourseAssignment.objects.filter(
            lecturer=lecturer,
            course_id=course_id,
            semester_id=semester_id,
            is_active=True
        ).first()
        
        if not assignment:
            return JsonResponse({'error': 'No permission to update attendance for this course'}, status=403)
        
        # Get or create attendance session
        timetable_slot = Timetable.objects.filter(
            course_id=course_id,
            lecturer=lecturer,
            semester_id=semester_id
        ).first()
        
        if not timetable_slot:
            return JsonResponse({'error': 'No timetable slot found for this course'}, status=404)
        
        attendance_session, created = AttendanceSession.objects.get_or_create(
            timetable_slot=timetable_slot,
            lecturer=lecturer,
            semester_id=semester_id,
            week_number=week_number,
            defaults={
                'session_date': timezone.now().date(),
                'expires_at': timezone.now() + timedelta(hours=3)
            }
        )
        
        # Update or create attendance record
        attendance, created = Attendance.objects.update_or_create(
            student=student,
            attendance_session=attendance_session,
            timetable_slot=timetable_slot,
            week_number=week_number,
            defaults={
                'status': status,
                'remarks': remarks,
                'marked_via_qr': False,
                'ip_address': request.META.get('REMOTE_ADDR')
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance updated for {student.user.get_full_name()}',
            'attendance': {
                'status': attendance.status,
                'marked_at': attendance.marked_at.strftime('%Y-%m-%d %H:%M'),
                'remarks': attendance.remarks
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_attendance(request, course_id, semester_id):
    """Export attendance data for a course"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, "Access denied.")
        return redirect('my_students')
    
    # Verify lecturer has permission
    assignment = get_object_or_404(
        LecturerCourseAssignment,
        lecturer=lecturer,
        course_id=course_id,
        semester_id=semester_id,
        is_active=True
    )
    
    # Get enrolled students and attendance data
    enrollments = Enrollment.objects.filter(
        course=assignment.course,
        semester=assignment.semester,
        is_active=True
    ).select_related('student__user').order_by('student__student_id')
    
    attendance_sessions = AttendanceSession.objects.filter(
        timetable_slot__course=assignment.course,
        semester=assignment.semester,
        lecturer=lecturer
    ).order_by('week_number')
    
    # Create CSV response
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{assignment.course.code}_attendance.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    headers = ['Student ID', 'Student Name', 'Programme']
    for session in attendance_sessions:
        headers.append(f'Week {session.week_number} ({session.session_date})')
    headers.extend(['Total Present', 'Total Sessions', 'Attendance %'])
    
    writer.writerow(headers)
    
    # Write student data
    for enrollment in enrollments:
        student = enrollment.student
        row = [student.student_id, student.user.get_full_name(), student.programme.name]
        
        present_count = 0
        for session in attendance_sessions:
            attendance = Attendance.objects.filter(
                student=student,
                attendance_session=session
            ).first()
            
            if attendance:
                row.append(attendance.status.title())
                if attendance.status in ['present', 'late']:
                    present_count += 1
            else:
                row.append('Absent')
        
        total_sessions = attendance_sessions.count()
        attendance_percentage = round((present_count / total_sessions * 100), 1) if total_sessions > 0 else 0
        
        row.extend([present_count, total_sessions, f"{attendance_percentage}%"])
        writer.writerow(row)
    
    return response


@login_required
def generate_qr_attendance(request, course_id, semester_id):
    """Generate QR code for attendance"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Verify lecturer has permission
    assignment = LecturerCourseAssignment.objects.filter(
        lecturer=lecturer,
        course_id=course_id,
        semester_id=semester_id,
        is_active=True
    ).first()
    
    if not assignment:
        return JsonResponse({'error': 'Course assignment not found'}, status=404)
    
    # Get current week number (you may need to adjust this logic)
    from datetime import datetime
    current_date = datetime.now().date()
    semester_start = assignment.semester.start_date
    week_number = ((current_date - semester_start).days // 7) + 1
    week_number = max(1, min(week_number, 12))  # Ensure week is between 1-12
    
    # Get timetable slot
    timetable_slot = Timetable.objects.filter(
        course=assignment.course,
        lecturer=lecturer,
        semester=assignment.semester
    ).first()
    
    if not timetable_slot:
        return JsonResponse({'error': 'No timetable slot found'}, status=404)
    
    # Create or get attendance session
    attendance_session, created = AttendanceSession.objects.get_or_create(
        timetable_slot=timetable_slot,
        lecturer=lecturer,
        semester=assignment.semester,
        week_number=week_number,
        session_date=current_date,
        defaults={
            'expires_at': timezone.now() + timedelta(hours=3)
        }
    )
    
    return JsonResponse({
        'success': True,
        'session_id': attendance_session.id,
        'qr_code_url': attendance_session.qr_code_image_url,
        'session_token': attendance_session.session_token,
        'expires_at': attendance_session.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
        'week_number': week_number
    })


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import month_name
import json

from .models import (
    Hostel, Room, Bed, HostelBooking, HostelPayment, 
    HostelIncident, AcademicYear, Student
)

@login_required
def hostel_dashboard(request):
    """
    Hostel warden dashboard view with comprehensive statistics and charts
    """
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_date = timezone.now().date()
    
    # Get hostels managed by current user (warden)
    managed_hostels = Hostel.objects.filter(
        warden=request.user,
        is_active=True
    )
    
    if not managed_hostels.exists():
        # If user doesn't manage any hostels, show all (for admin)
        managed_hostels = Hostel.objects.filter(is_active=True)
    
    # Basic Statistics
    total_hostels = managed_hostels.count()
    total_rooms = Room.objects.filter(
        hostel__in=managed_hostels,
        is_active=True
    ).count()
    
    # Bed statistics
    total_beds = Bed.objects.filter(
        room__hostel__in=managed_hostels,
        academic_year=current_academic_year
    ).count()
    
    occupied_beds = Bed.objects.filter(
        room__hostel__in=managed_hostels,
        academic_year=current_academic_year,
        is_available=False
    ).count()
    
    available_beds = total_beds - occupied_beds
    occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    
    # Booking statistics
    total_bookings = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year
    ).count()
    
    active_bookings = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year,
        booking_status__in=['approved', 'checked_in']
    ).count()
    
    pending_bookings = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year,
        booking_status='pending'
    ).count()
    
    # Financial statistics
    total_revenue = HostelPayment.objects.filter(
        booking__bed__room__hostel__in=managed_hostels,
        booking__academic_year=current_academic_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    today_payments = HostelPayment.objects.filter(
        booking__bed__room__hostel__in=managed_hostels,
        payment_date=current_date
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_payments = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year,
        payment_status__in=['pending', 'partial']
    ).aggregate(balance=Sum('booking_fee') - Sum('amount_paid'))['balance'] or 0
    
    # Recent activities
    recent_bookings = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year
    ).select_related('student', 'bed__room__hostel').order_by('-booking_date')[:5]
    
    recent_payments = HostelPayment.objects.filter(
        booking__bed__room__hostel__in=managed_hostels
    ).select_related('booking__student').order_by('-payment_date')[:5]
    
    recent_incidents = HostelIncident.objects.filter(
        booking__bed__room__hostel__in=managed_hostels
    ).select_related('booking__student', 'booking__bed__room__hostel').order_by('-incident_date')[:5]
    
    # Chart Data Preparation
    
    # 1. Gender Distribution (Donut Chart)
    gender_data = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year,
        booking_status__in=['approved', 'checked_in']
    ).values('student__user__gender').annotate(
        count=Count('id')
    ).order_by('student__user__gender')
    
    gender_chart_data = {
        'labels': [item['student__user__gender'].title() if item['student__user__gender'] else 'Not Specified' for item in gender_data],
        'data': [item['count'] for item in gender_data],
        'colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    }
    
    # 2. Hostel Occupancy (Bar Chart)
    hostel_occupancy = []
    for hostel in managed_hostels:
        total_hostel_beds = Bed.objects.filter(
            room__hostel=hostel,
            academic_year=current_academic_year
        ).count()
        occupied_hostel_beds = Bed.objects.filter(
            room__hostel=hostel,
            academic_year=current_academic_year,
            is_available=False
        ).count()
        
        hostel_occupancy.append({
            'name': hostel.name,
            'total': total_hostel_beds,
            'occupied': occupied_hostel_beds,
            'rate': (occupied_hostel_beds / total_hostel_beds * 100) if total_hostel_beds > 0 else 0
        })
    
    hostel_chart_data = {
        'labels': [item['name'] for item in hostel_occupancy],
        'data': [item['rate'] for item in hostel_occupancy],
        'occupied': [item['occupied'] for item in hostel_occupancy],
        'total': [item['total'] for item in hostel_occupancy]
    }
    
    # 3. Monthly Payment Trend (Line Chart)
    monthly_payments = []
    for i in range(12):
        month_start = (current_date.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        month_total = HostelPayment.objects.filter(
            booking__bed__room__hostel__in=managed_hostels,
            payment_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_payments.append({
            'month': month_name[month_start.month][:3],
            'amount': float(month_total)
        })
    
    monthly_payments.reverse()
    payment_trend_data = {
        'labels': [item['month'] for item in monthly_payments],
        'data': [item['amount'] for item in monthly_payments]
    }
    
    # 4. Booking Status Distribution (Pie Chart)
    booking_status_data = HostelBooking.objects.filter(
        bed__room__hostel__in=managed_hostels,
        academic_year=current_academic_year
    ).values('booking_status').annotate(
        count=Count('id')
    ).order_by('booking_status')
    
    status_colors = {
        'pending': '#FFA726',
        'approved': '#66BB6A',
        'rejected': '#EF5350',
        'cancelled': '#BDBDBD',
        'checked_in': '#42A5F5',
        'checked_out': '#AB47BC'
    }
    
    booking_status_chart_data = {
        'labels': [item['booking_status'].replace('_', ' ').title() for item in booking_status_data],
        'data': [item['count'] for item in booking_status_data],
        'colors': [status_colors.get(item['booking_status'], '#78909C') for item in booking_status_data]
    }
    
    # 5. Incident Trends (Bar Chart)
    incident_monthly = []
    for i in range(6):
        month_start = (current_date.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        month_incidents = HostelIncident.objects.filter(
            booking__bed__room__hostel__in=managed_hostels,
            incident_date__range=[month_start, month_end]
        ).count()
        
        incident_monthly.append({
            'month': month_name[month_start.month][:3],
            'count': month_incidents
        })
    
    incident_monthly.reverse()
    incident_trend_data = {
        'labels': [item['month'] for item in incident_monthly],
        'data': [item['count'] for item in incident_monthly]
    }
    
    # 6. Room Utilization by Floor (Horizontal Bar)
    floor_utilization = Room.objects.filter(
        hostel__in=managed_hostels,
        is_active=True
    ).values('floor').annotate(
        total_beds=Count('beds', filter=Q(beds__academic_year=current_academic_year)),
        occupied_beds=Count('beds', filter=Q(
            beds__academic_year=current_academic_year,
            beds__is_available=False
        ))
    ).order_by('floor')
    
    floor_chart_data = {
        'labels': [f'Floor {item["floor"]}' for item in floor_utilization],
        'data': [(item['occupied_beds'] / item['total_beds'] * 100) if item['total_beds'] > 0 else 0 for item in floor_utilization]
    }
    
    # 7. Payment Method Distribution
    payment_methods = HostelPayment.objects.filter(
        booking__bed__room__hostel__in=managed_hostels,
        booking__academic_year=current_academic_year
    ).values('payment_method').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('-amount')
    
    payment_method_chart_data = {
        'labels': [item['payment_method'].replace('_', ' ').title() for item in payment_methods],
        'data': [float(item['amount']) for item in payment_methods],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    }
    
    context = {
        'current_academic_year': current_academic_year,
        'current_date': current_date,
        'managed_hostels': managed_hostels,
        
        # Basic stats
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'occupancy_rate': round(occupancy_rate, 1),
        
        # Booking stats
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'pending_bookings': pending_bookings,
        
        # Financial stats
        'total_revenue': total_revenue,
        'today_payments': today_payments,
        'pending_payments': pending_payments,
        
        # Recent activities
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
        'recent_incidents': recent_incidents,
        
        # Chart data (JSON serialized for JavaScript)
        'gender_chart_data': json.dumps(gender_chart_data),
        'hostel_chart_data': json.dumps(hostel_chart_data),
        'payment_trend_data': json.dumps(payment_trend_data),
        'booking_status_chart_data': json.dumps(booking_status_chart_data),
        'incident_trend_data': json.dumps(incident_trend_data),
        'floor_chart_data': json.dumps(floor_chart_data),
        'payment_method_chart_data': json.dumps(payment_method_chart_data),
    }
    
    return render(request, 'hostels/hostel_dashboard.html', context)

# views.py - Updated Student Fee Management
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import uuid
from datetime import datetime, date
#from dateutil.relativedelta import relativedelta

from .models import (
    Student, AcademicYear, Semester, FeeStructure, 
    FeePayment, User
)

@login_required
def student_fee_management(request):
    """
    View for students to manage and view their fee payments
    Only shows academic years and semesters relevant to the student's programme
    """
    try:
        student = request.user.student_profile
    except:
        messages.error(request, "You don't have a student profile.")
        return redirect('login')
    
    # Get student's programme details
    programme = student.programme
    programme_duration_years = programme.duration_years
    semesters_per_year = programme.semesters_per_year
    admission_year = student.admission_date.year
    
    # Calculate the academic years the student should be in
    # For example, if admitted in 2021/2022 and programme is 3 years:
    # Academic years: 2021/2022, 2022/2023, 2023/2024
    relevant_academic_years = []
    
    for year_offset in range(programme_duration_years):
        start_year = admission_year + year_offset
        end_year = start_year + 1
        academic_year_str = f"{start_year}/{end_year}"
        
        try:
            academic_year = AcademicYear.objects.get(year=academic_year_str)
            relevant_academic_years.append(academic_year)
        except AcademicYear.DoesNotExist:
            # Create the academic year if it doesn't exist (optional)
            # You might want to handle this differently based on your requirements
            continue
    
    # Calculate overall statistics
    total_fees_charged = Decimal('0.00')
    total_fees_paid = Decimal('0.00')
    overall_balance = Decimal('0.00')
    
    # Prepare data for each relevant academic year
    years_data = []
    
    for year_index, academic_year in enumerate(relevant_academic_years):
        # Calculate which programme year this academic year represents for the student
        student_programme_year = year_index + 1
        
        # Get only the semesters that exist for this programme
        # Most programmes have semester 1 and 2, some have 3
        semester_numbers = list(range(1, semesters_per_year + 1))
        
        year_data = {
            'academic_year': academic_year,
            'student_programme_year': student_programme_year,
            'semesters': [],
            'year_total_charged': Decimal('0.00'),
            'year_total_paid': Decimal('0.00'),
            'year_balance': Decimal('0.00')
        }
        
        for semester_number in semester_numbers:
            # Try to get the actual semester object
            try:
                semester = Semester.objects.get(
                    academic_year=academic_year,
                    semester_number=semester_number
                )
            except Semester.DoesNotExist:
                # Create a minimal semester object for display purposes
                semester = type('obj', (object,), {
                    'semester_number': semester_number,
                    'academic_year': academic_year,
                    'start_date': None,
                    'end_date': None
                })()
            
            # Get fee structure for this specific semester and programme year
            try:
                fee_structure = FeeStructure.objects.get(
                    programme=student.programme,
                    academic_year=academic_year,
                    year=student_programme_year,  # Use the calculated programme year
                    semester=semester_number
                )
                semester_fee = fee_structure.net_fee()
            except FeeStructure.DoesNotExist:
                fee_structure = None
                semester_fee = Decimal('0.00')
            
            # Get payments for this semester
            payments = FeePayment.objects.filter(
                student=student,
                fee_structure__academic_year=academic_year,
                fee_structure__year=student_programme_year,
                fee_structure__semester=semester_number,
                payment_status='completed'
            ).order_by('-payment_date')
            
            semester_paid = payments.aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal('0.00')
            
            semester_balance = semester_fee - semester_paid
            
            semester_data = {
                'semester': semester,
                'fee_structure': fee_structure,
                'semester_fee': semester_fee,
                'semester_paid': semester_paid,
                'semester_balance': semester_balance,
                'payments': payments,
                'student_programme_year': student_programme_year
            }
            
            year_data['semesters'].append(semester_data)
            year_data['year_total_charged'] += semester_fee
            year_data['year_total_paid'] += semester_paid
        
        year_data['year_balance'] = year_data['year_total_charged'] - year_data['year_total_paid']
        
        # Only add year data if there are semesters or if it's relevant to the student
        if year_data['semesters']:
            years_data.append(year_data)
            
            # Add to overall totals
            total_fees_charged += year_data['year_total_charged']
            total_fees_paid += year_data['year_total_paid']
    
    overall_balance = total_fees_charged - total_fees_paid
    
    # Get recent payments for quick overview (last 5 payments)
    recent_payments = FeePayment.objects.filter(
        student=student,
        payment_status='completed'
    ).order_by('-payment_date')[:5]
    
    # Calculate statistics
    stats = {
        'total_fees_charged': total_fees_charged,
        'total_fees_paid': total_fees_paid,
        'overall_balance': overall_balance,
        'total_payments': FeePayment.objects.filter(
            student=student, 
            payment_status='completed'
        ).count(),
        'payment_methods_used': FeePayment.objects.filter(
            student=student,
            payment_status='completed'
        ).values('payment_method').distinct().count()
    }
    
    # Calculate expected graduation year for context
    expected_graduation_year = admission_year + programme_duration_years
    expected_graduation_academic_year = f"{expected_graduation_year-1}/{expected_graduation_year}"
    
    context = {
        'student': student,
        'years_data': years_data,
        'recent_payments': recent_payments,
        'stats': stats,
        'current_year': timezone.now().year,
        'programme_info': {
            'duration_years': programme_duration_years,
            'semesters_per_year': semesters_per_year,
            'expected_graduation': expected_graduation_academic_year,
            'admission_year': f"{admission_year}/{admission_year + 1}",
        }
    }
    
    return render(request, 'student/fee_management.html', context)



@staff_member_required
def admin_fee_payment(request):
    """
    View for admin to process student fee payments with overpayment handling
    """
    receipt_data = None
    student = None
    fee_structure = None
    overpayment_details = None
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        academic_year_id = request.POST.get('academic_year_id')
        semester_number = request.POST.get('semester_number')
        student_year = request.POST.get('student_year', 1)
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        transaction_reference = request.POST.get('transaction_reference', '')
        mpesa_receipt = request.POST.get('mpesa_receipt', '')
        bank_slip_number = request.POST.get('bank_slip_number', '')
        remarks = request.POST.get('remarks', '')
        
        try:
            # Get student
            student = Student.objects.get(student_id=student_id)
            
            # Get academic year and fee structure
            academic_year = AcademicYear.objects.get(id=academic_year_id)
            fee_structure = FeeStructure.objects.get(
                programme=student.programme,
                academic_year=academic_year,
                year=int(student_year),
                semester=int(semester_number)
            )
            
            # Calculate current balance
            previous_payments = FeePayment.objects.filter(
                student=student,
                fee_structure=fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            
            current_balance = fee_structure.net_fee() - previous_payments
            amount_paid_decimal = Decimal(amount_paid)
            
            # Generate receipt number
            receipt_number = f"RCT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Create payment record for current semester
            current_payment_amount = min(amount_paid_decimal, current_balance)
            overpayment_amount = amount_paid_decimal - current_payment_amount
            
            # Main payment record
            payment = FeePayment.objects.create(
                student=student,
                fee_structure=fee_structure,
                receipt_number=receipt_number,
                amount_paid=current_payment_amount,
                payment_date=payment_date,
                payment_method=payment_method,
                payment_status='completed',
                transaction_reference=transaction_reference,
                mpesa_receipt=mpesa_receipt,
                bank_slip_number=bank_slip_number,
                remarks=remarks,
                processed_by=request.user
            )
            
            # Handle overpayment
            overpayment_details = []
            remaining_overpayment = overpayment_amount
            
            if remaining_overpayment > 0:
                overpayment_details = handle_overpayment(
                    student, academic_year, int(student_year), int(semester_number),
                    remaining_overpayment, payment_method, payment_date,
                    transaction_reference, mpesa_receipt, bank_slip_number,
                    f"Overpayment from {receipt_number}", request.user
                )
            
            # Calculate totals for receipt (including overpayment)
            total_payments_current = FeePayment.objects.filter(
                student=student,
                fee_structure=fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            
            balance = fee_structure.net_fee() - total_payments_current
            
            receipt_data = {
                'payment': payment,
                'student': student,
                'fee_structure': fee_structure,
                'academic_year': academic_year,
                'total_fee': fee_structure.net_fee(),
                'total_paid': total_payments_current,
                'balance': balance,
                'payment_date': payment_date,
                'total_amount_paid': amount_paid_decimal,
                'overpayment_amount': overpayment_amount,
                'overpayment_details': overpayment_details
            }
            
            success_message = f'Payment recorded successfully. Receipt: {receipt_number}'
            if overpayment_amount > 0:
                success_message += f'. Overpayment of KES {overpayment_amount} allocated to future semesters.'
            
            messages.success(request, success_message)
            
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        except FeeStructure.DoesNotExist:
            messages.error(request, 'Fee structure not found for the selected criteria.')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    # Get data for form with current defaults
    academic_years = AcademicYear.objects.all().order_by('-year')
    payment_methods = FeePayment.PAYMENT_METHODS
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    context = {
        'academic_years': academic_years,
        'payment_methods': payment_methods,
        'receipt_data': receipt_data,
        'student': student,
        'fee_structure': fee_structure,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester
    }
    
    return render(request, 'admin/fee_payment.html', context)


def handle_overpayment(student, current_academic_year, current_year, current_semester, 
                      overpayment_amount, payment_method, payment_date, 
                      transaction_reference, mpesa_receipt, bank_slip_number, 
                      remarks, processed_by):
    """
    Handle overpayment by allocating to future semesters/years
    """
    overpayment_details = []
    remaining_amount = overpayment_amount
    
    # Get programme details
    programme = student.programme
    max_years = programme.duration_years
    max_semesters = programme.semesters_per_year
    
    # Calculate next semester/year
    next_year = current_year
    next_semester = current_semester + 1
    next_academic_year = current_academic_year
    
    # Handle semester overflow
    if next_semester > max_semesters:
        next_semester = 1
        next_year += 1
        
        # Check if we need next academic year
        if next_year <= max_years:
            # Get next academic year
            next_academic_year_obj = AcademicYear.objects.filter(
                year__gt=current_academic_year.year
            ).order_by('year').first()
            
            if next_academic_year_obj:
                next_academic_year = next_academic_year_obj
    
    # Don't allocate if student is in final year and final semester
    is_final_year = current_year == max_years
    is_final_semester = current_semester == max_semesters
    
    if is_final_year and is_final_semester:
        # Create a credit balance record (you might want to create a separate model for this)
        overpayment_details.append({
            'type': 'credit_balance',
            'amount': remaining_amount,
            'description': f'Credit balance - Student completed programme'
        })
        return overpayment_details
    
    # Allocate overpayment to future periods
    while remaining_amount > 0 and next_year <= max_years:
        try:
            # Get fee structure for next period
            next_fee_structure = FeeStructure.objects.get(
                programme=programme,
                academic_year=next_academic_year,
                year=next_year,
                semester=next_semester
            )
            
            # Check existing payments for this period
            existing_payments = FeePayment.objects.filter(
                student=student,
                fee_structure=next_fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            
            # Calculate how much can be allocated
            balance_needed = next_fee_structure.net_fee() - existing_payments
            
            if balance_needed > 0:
                allocation_amount = min(remaining_amount, balance_needed)
                
                # Create payment record for future period
                receipt_number = f"ADV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                FeePayment.objects.create(
                    student=student,
                    fee_structure=next_fee_structure,
                    receipt_number=receipt_number,
                    amount_paid=allocation_amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    payment_status='completed',
                    transaction_reference=transaction_reference,
                    mpesa_receipt=mpesa_receipt,
                    bank_slip_number=bank_slip_number,
                    remarks=f"Advanced payment - {remarks}",
                    processed_by=processed_by
                )
                
                overpayment_details.append({
                    'type': 'advance_payment',
                    'academic_year': next_academic_year.year,
                    'year': next_year,
                    'semester': next_semester,
                    'amount': allocation_amount,
                    'receipt_number': receipt_number,
                    'description': f'Advanced payment for Year {next_year} Semester {next_semester} ({next_academic_year.year})'
                })
                
                remaining_amount -= allocation_amount
            
            # Move to next semester/year
            next_semester += 1
            if next_semester > max_semesters:
                next_semester = 1
                next_year += 1
                
                # Get next academic year if needed
                if next_year <= max_years:
                    next_academic_year_obj = AcademicYear.objects.filter(
                        year__gt=next_academic_year.year
                    ).order_by('year').first()
                    
                    if next_academic_year_obj:
                        next_academic_year = next_academic_year_obj
                    else:
                        break  # No more academic years available
                        
        except FeeStructure.DoesNotExist:
            # No fee structure for this period, move to next
            next_semester += 1
            if next_semester > max_semesters:
                next_semester = 1
                next_year += 1
                
                if next_year <= max_years:
                    next_academic_year_obj = AcademicYear.objects.filter(
                        year__gt=next_academic_year.year
                    ).order_by('year').first()
                    
                    if next_academic_year_obj:
                        next_academic_year = next_academic_year_obj
                    else:
                        break
    
    # If there's still remaining amount, create credit balance
    if remaining_amount > 0:
        overpayment_details.append({
            'type': 'credit_balance',
            'amount': remaining_amount,
            'description': f'Credit balance - Excess payment'
        })
    
    return overpayment_details


@staff_member_required
def get_student_data_info(request): #used in fee management
    """
    AJAX view to get student information with current academic period
    """
    student_id = request.GET.get('student_id')
    
    try:
        student = Student.objects.get(student_id=student_id)
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        data = {
            'success': True,
            'student': {
                'name': student.user.get_full_name(),
                'programme': student.programme.name,
                'current_year': student.current_year,
                'current_semester': student.current_semester,
                'status': student.status
            },
            'current_academic_year_id': current_academic_year.id if current_academic_year else None,
            'current_semester_number': current_semester.semester_number if current_semester else None
        }
    except Student.DoesNotExist:
        data = {
            'success': False,
            'message': 'Student not found'
        }
    
    from django.http import JsonResponse
    return JsonResponse(data)


@staff_member_required
def get_fee_structure(request):
    """
    AJAX view to get fee structure information
    """
    student_id = request.GET.get('student_id')
    academic_year_id = request.GET.get('academic_year_id')
    semester_number = request.GET.get('semester_number')
    student_year = request.GET.get('student_year', 1)
    
    try:
        student = Student.objects.get(student_id=student_id)
        academic_year = AcademicYear.objects.get(id=academic_year_id)
        
        fee_structure = FeeStructure.objects.get(
            programme=student.programme,
            academic_year=academic_year,
            year=int(student_year),
            semester=int(semester_number)
        )
        
        # Calculate payments and balance
        payments = FeePayment.objects.filter(
            student=student,
            fee_structure=fee_structure,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        balance = fee_structure.net_fee() - payments
        
        data = {
            'success': True,
            'fee_structure': {
                'total_fee': str(fee_structure.total_fee()),
                'net_fee': str(fee_structure.net_fee()),
                'total_paid': str(payments),
                'balance': str(balance),
                'tuition_fee': str(fee_structure.tuition_fee),
                'registration_fee': str(fee_structure.registration_fee),
                'examination_fee': str(fee_structure.examination_fee),
                'other_fees': str(fee_structure.other_fees),
                'government_subsidy': str(fee_structure.government_subsidy),
                'scholarship_amount': str(fee_structure.scholarship_amount)
            }
        }
    except (Student.DoesNotExist, AcademicYear.DoesNotExist, FeeStructure.DoesNotExist):
        data = {
            'success': False,
            'message': 'Required data not found'
        }
    
    from django.http import JsonResponse
    return JsonResponse(data)


from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import os
from decimal import Decimal
from django.conf import settings

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from decimal import Decimal
from django.db.models import Sum
import os
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from decimal import Decimal
from django.db.models import Sum
import os

@staff_member_required
def download_payment_receipt_pdf(request, payment_id):
    """
    Generate and download a professional PDF receipt for a fee payment using HTML to PDF
    """
    try:
        # Get the payment record
        payment = get_object_or_404(FeePayment, id=payment_id, payment_status='completed')
        
        # Get related data
        student = payment.student
        fee_structure = payment.fee_structure
        academic_year = fee_structure.academic_year
        
        # Calculate totals
        total_payments = FeePayment.objects.filter(
            student=student,
            fee_structure=fee_structure,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        balance = fee_structure.net_fee() - total_payments
        
        # Calculate previous payments (total payments minus current payment)
        previous_payments = total_payments - payment.amount_paid
        
        # Get overpayment details if any
        overpayment_details = []
        overpayment_total = Decimal('0.00')
        if hasattr(payment, 'overpayment_allocations'):
            overpayment_details = payment.overpayment_allocations.all()
            overpayment_total = sum(detail.amount for detail in overpayment_details)
        
        # Prepare context for template
        context = {
            'payment': payment,
            'student': student,
            'fee_structure': fee_structure,
            'academic_year': academic_year,
            'total_payments': total_payments,
            'previous_payments': previous_payments,
            'balance': balance,
            'overpayment_details': overpayment_details,
            'overpayment_total': overpayment_total,
            'university_name': getattr(settings, 'UNIVERSITY_NAME', 'MURANGA UNIVERSITY OF TECHNOLOGY '),
            'university_address': getattr(settings, 'UNIVERSITY_ADDRESS', 'Muranga Town 351, Kiambu, Kenya'),
            'university_contact': getattr(settings, 'UNIVERSITY_CONTACT', 'Tel: +254-763-7474893 | Email: finance@mutuniversity.edu'),
            'logo_url': getattr(settings, 'LOGO_URL', ''),
        }
        
        # Render HTML template
        html_string = render_to_string('receipt/receipt_template.html', context)
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        filename = f"Receipt-{payment.receipt_number}-{payment.payment_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Generate PDF using WeasyPrint
        font_config = FontConfiguration()
        css = CSS(string='''
            @page {
                size: A4;
                margin: 1cm;
                @top-center {
                    content: "OFFICIAL FEE PAYMENT RECEIPT";
                    font-size: 12px;
                    font-weight: bold;
                }
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10px;
                }
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
                border-bottom: 2px solid #000;
                padding-bottom: 10px;
            }
            .university-name {
                font-size: 18px;
                font-weight: bold;
                color: #003366;
            }
            .receipt-title {
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                margin: 15px 0;
                text-decoration: underline;
            }
            .section {
                margin-bottom: 15px;
            }
            .section-title {
                font-weight: bold;
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #ddd;
            }
            .two-columns {
                display: flex;
                justify-content: space-between;
            }
            .column {
                width: 48%;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .total-row {
                font-weight: bold;
                background-color: #e6f2ff;
            }
            .balance-row {
                font-weight: bold;
                background-color: #ffffcc;
            }
            .signature-area {
                margin-top: 50px;
                border-top: 1px solid #000;
                padding-top: 10px;
            }
            .footer {
                margin-top: 30px;
                font-size: 10px;
                text-align: center;
                color: #666;
            }
            .text-right {
                text-align: right;
            }
            .text-center {
                text-align: center;
            }
            .notes {
                font-size: 10px;
                margin-top: 20px;
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
            }
        ''', font_config=font_config)
        
        # Generate PDF
        HTML(string=html_string).write_pdf(
            response, 
            stylesheets=[css],
            font_config=font_config
        )
        
        return response
        
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating PDF receipt for payment {payment_id}: {str(e)}")
        
        # Return error response
        return HttpResponse(
            f"Error generating PDF receipt: {str(e)}", 
            status=500,
            content_type='text/plain'
        )


# Alternative view for generating receipt data (for use with frontend PDF generation)
@staff_member_required
def get_receipt_data_json(request, payment_id):
    """
    Return receipt data as JSON for frontend PDF generation
    """
    from django.http import JsonResponse
    
    try:
        payment = get_object_or_404(FeePayment, id=payment_id, payment_status='completed')
        student = payment.student
        fee_structure = payment.fee_structure
        academic_year = fee_structure.academic_year
        
        # Calculate totals
        total_payments = FeePayment.objects.filter(
            student=student,
            fee_structure=fee_structure,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        balance = fee_structure.net_fee() - total_payments
        
        receipt_data = {
            'payment': {
                'receipt_number': payment.receipt_number,
                'amount_paid': str(payment.amount_paid),
                'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
                'payment_method': payment.get_payment_method_display(),
                'transaction_reference': payment.transaction_reference or '',
                'mpesa_receipt': payment.mpesa_receipt or '',
                'bank_slip_number': payment.bank_slip_number or '',
                'remarks': payment.remarks or '',
                'processed_by': payment.processed_by.get_full_name(),
            },
            'student': {
                'student_id': student.student_id,
                'name': student.user.get_full_name(),
                'programme': student.programme.name,
                'year': fee_structure.year,
                'semester': fee_structure.semester,
            },
            'academic_year': {
                'year': academic_year.year,
            },
            'fee_structure': {
                'tuition_fee': str(fee_structure.tuition_fee),
                'registration_fee': str(fee_structure.registration_fee),
                'examination_fee': str(fee_structure.examination_fee),
                'other_fees': str(fee_structure.other_fees),
                'total_fee': str(fee_structure.total_fee()),
                'government_subsidy': str(fee_structure.government_subsidy),
                'scholarship_amount': str(fee_structure.scholarship_amount),
                'net_fee': str(fee_structure.net_fee()),
            },
            'totals': {
                'total_paid': str(total_payments),
                'previous_payments': str(total_payments - payment.amount_paid),
                'balance': str(balance),
            }
        }
        
        return JsonResponse({'success': True, 'data': receipt_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
# views.py - Student Services Views
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import FileResponse
from .models import *
from .forms import *  # You'll need to create these forms


# Exam Repository Views
@login_required
def exam_repository(request):
    """Display exam materials for student's programme"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    
    # Get materials for student's programme
    materials = ExamRepository.objects.filter(
        programme=student.programme,
        is_public=True
    ).select_related('course', 'academic_year')
    
    # Filter by course if specified
    course_id = request.GET.get('course')
    if course_id:
        materials = materials.filter(course_id=course_id)
    
    # Filter by material type if specified
    material_type = request.GET.get('type')
    if material_type:
        materials = materials.filter(material_type=material_type)
    
    # Get courses for filtering
    courses = Course.objects.filter(
        course_programmes__programme=student.programme
    ).distinct()
    
    # Pagination
    paginator = Paginator(materials, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'courses': courses,
        'selected_course': course_id,
        'selected_type': material_type,
        'material_types': ExamRepository.MATERIAL_TYPES,
    }
    return render(request, 'student/exam_repository.html', context)

@login_required
def download_exam_material(request, material_id):
    """Download exam material and track the download"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    material = get_object_or_404(ExamRepository, id=material_id, is_public=True)
    
    # Check if student's programme has access to this material
    if material.programme != student.programme:
        messages.error(request, "You don't have access to this material.")
        return redirect('exam_repository')
    
    # Track the download
    ExamMaterialDownload.objects.create(
        exam_material=material,
        student=student,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Increment download count
    material.download_count += 1
    material.save()
    
    # Serve the file
    try:
        return FileResponse(
            material.material_file.open(),
            as_attachment=True,
            filename=material.material_file.name
        )
    except Exception as e:
        messages.error(request, "Error downloading file.")
        return redirect('exam_repository')

# Special Exam Application Views
@login_required
def special_exam_applications(request):
    """List student's special exam applications"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    applications = SpecialExamApplication.objects.filter(
        student=student
    ).select_related('course', 'semester')
    
    context = {
        'applications': applications,
    }
    return render(request, 'student/special_exam_list.html', context)

@login_required
def apply_special_exam(request):
    """Apply for special exam"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        form = SpecialExamApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = student
            application.save()
            messages.success(request, "Special exam application submitted successfully!")
            return redirect('special_exam_applications')
    else:
        form = SpecialExamApplicationForm()
    
    # Get courses student is enrolled in current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    enrolled_courses = []
    if current_semester:
        enrolled_courses = Course.objects.filter(
            enrollments__student=student,
            enrollments__semester=current_semester
        )
    
    context = {
        'form': form,
        'enrolled_courses': enrolled_courses,
    }
    return render(request, 'student/apply_special_exam.html', context)

# Deferment Application Views
@login_required
def deferment_applications(request):
    """List student's deferment applications"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    applications = DefermentApplication.objects.filter(student=student)
    
    context = {
        'applications': applications,
    }
    return render(request, 'student/deferment_list.html', context)

@login_required
def apply_deferment(request):
    """Apply for academic deferment"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        form = DefermentApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = student
            application.save()
            messages.success(request, "Deferment application submitted successfully!")
            return redirect('deferment_applications')
    else:
        form = DefermentApplicationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'student/apply_deferment.html', context)

# Clearance Views
@login_required
def clearance_requests(request):
    """List student's clearance requests"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    requests = ClearanceRequest.objects.filter(student=student)
    
    context = {
        'clearance_requests': requests,
    }
    return render(request, 'student/clearance_list.html', context)

@login_required
def request_clearance(request):
    """Request clearance"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        form = ClearanceRequestForm(request.POST)
        if form.is_valid():
            clearance_request = form.save(commit=False)
            clearance_request.student = student
            clearance_request.save()
            messages.success(request, "Clearance request submitted successfully!")
            return redirect('clearance_requests')
    else:
        form = ClearanceRequestForm()
    
    context = {
        'form': form,
    }
    return render(request, 'student/request_clearance.html', context)

# Messaging Views
@login_required
def messages_inbox(request):
    """Student's message inbox"""
    messages_list = Message.objects.filter(
        recipient=request.user,
        is_deleted_by_recipient=False
    ).select_related('sender')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        messages_list = messages_list.filter(
            Q(subject__icontains=search) | 
            Q(message__icontains=search) |
            Q(sender__first_name__icontains=search) |
            Q(sender__last_name__icontains=search)
        )
    
    # Filter by read/unread
    filter_type = request.GET.get('filter')
    if filter_type == 'unread':
        messages_list = messages_list.filter(is_read=False)
    elif filter_type == 'starred':
        messages_list = messages_list.filter(is_starred=True)
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_type': filter_type,
    }
    return render(request, 'student/messages_inbox.html', context)

@login_required
def message_detail(request, message_id):
    """View message details"""
    message = get_object_or_404(
        Message, 
        id=message_id,
        recipient=request.user,
        is_deleted_by_recipient=False
    )
    
    # Mark as read
    message.mark_as_read()
    
    # Get replies
    replies = Message.objects.filter(
        parent_message=message,
        is_deleted_by_recipient=False
    ).select_related('sender')
    
    context = {
        'message': message,
        'replies': replies,
    }
    return render(request, 'student/message_detail.html', context)

@login_required
def compose_message(request):
    """Compose new message"""
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, "Message sent successfully!")
            return redirect('messages_inbox')
    else:
        form = MessageForm()
    
    # Get possible recipients (lecturers, staff, admins)
    recipients = User.objects.filter(
        Q(user_type__in=['lecturer', 'staff', 'admin', 'hod', 'dean']) |
        Q(is_staff=True)
    ).exclude(id=request.user.id)
    
    context = {
        'form': form,
        'recipients': recipients,
    }
    return render(request, 'student/compose_message.html', context)

@login_required
def reply_message(request, message_id):
    """Reply to a message"""
    parent_message = get_object_or_404(
        Message,
        id=message_id,
        recipient=request.user
    )
    
    if request.method == 'POST':
        form = MessageReplyForm(request.POST, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.recipient = parent_message.sender
            reply.parent_message = parent_message
            reply.subject = f"Re: {parent_message.subject}"
            reply.save()
            messages.success(request, "Reply sent successfully!")
            return redirect('message_detail', message_id=parent_message.id)
    else:
        form = MessageReplyForm()
    
    context = {
        'form': form,
        'parent_message': parent_message,
    }
    return render(request, 'student/reply_message.html', context)

@login_required
def sent_messages(request):
    """View sent messages"""
    messages_list = Message.objects.filter(
        sender=request.user,
        is_deleted_by_sender=False
    ).select_related('recipient')
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'student/sent_messages.html', context)

@login_required
def notifications(request):
    """View student notifications"""
    if not hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    notifications_list = StudentNotification.objects.filter(student=student)
    
    # Mark all as read when viewing
    unread_notifications = notifications_list.filter(is_read=False)
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_date = timezone.now()
    StudentNotification.objects.bulk_update(unread_notifications, ['is_read', 'read_date'])
    
    # Pagination
    paginator = Paginator(notifications_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'student/student_notifications.html', context)

def course_evaluation(request):
    return render (request , 'student/course_evaluation.html')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .models import User, Lecturer, Department


@login_required
@require_http_methods(["GET", "POST"])
def lecturer_profile(request):
    """
    Handle lecturer profile view and updates
    """
    # Check if user is a lecturer
    if request.user.user_type not in ['lecturer', 'professor']:
        messages.error(request, "Access denied. This page is for lecturers only.")
        return redirect('login')
    
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found. Please contact the administrator.")
        return redirect('lecturer_dashboard')
    
    if request.method == 'POST':
        return handle_lecturer_profile_update(request, lecturer)
    
    context = {
        'lecturer': lecturer,
        'departments': Department.objects.filter(is_active=True),
    }
    
    return render(request, 'lecturers/lecturer_profile.html', context)


def handle_lecturer_profile_update(request, lecturer):
    """
    Handle POST requests for lecturer profile updates
    """
    user = request.user
    
    # Handle profile picture upload
    if 'profile_picture' in request.FILES:
        profile_picture = request.FILES['profile_picture']
        
        # Validate file type
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        file_extension = profile_picture.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            messages.error(request, "Invalid file type. Please upload JPG, JPEG, PNG, or GIF files only.")
            return redirect('lecturer_profile')
        
        # Validate file size (5MB limit)
        if profile_picture.size > 5 * 1024 * 1024:
            messages.error(request, "File size too large. Please upload files smaller than 5MB.")
            return redirect('lecturer_profile')
        
        # Delete old profile picture if exists
        if user.profile_picture:
            if default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)
        
        user.profile_picture = profile_picture
        user.save()
        messages.success(request, "Profile picture updated successfully!")
        return redirect('lecturer_profile')
    
    # Handle personal details update
    if any(field in request.POST for field in ['first_name', 'last_name', 'phone', 'email', 'address']):
        try:
            # Update user fields
            if 'first_name' in request.POST:
                user.first_name = request.POST.get('first_name', '').strip()
            if 'last_name' in request.POST:
                user.last_name = request.POST.get('last_name', '').strip()
            if 'phone' in request.POST:
                user.phone = request.POST.get('phone', '').strip()
            if 'email' in request.POST:
                email = request.POST.get('email', '').strip()
                if email and User.objects.exclude(id=user.id).filter(email=email).exists():
                    messages.error(request, "This email address is already in use.")
                    return redirect('lecturer_profile')
                user.email = email
            if 'address' in request.POST:
                user.address = request.POST.get('address', '').strip()
            
            user.save()
            messages.success(request, "Personal details updated successfully!")
            
        except Exception as e:
            messages.error(request, f"Error updating personal details: {str(e)}")
    
    # Handle professional details update
    if any(field in request.POST for field in [
        'academic_rank', 'employment_type', 'highest_qualification', 'university_graduated',
        'graduation_year', 'research_interests', 'publications', 'professional_registration',
        'teaching_experience_years', 'research_experience_years', 'industry_experience_years',
        'office_location', 'office_phone', 'consultation_hours'
    ]):
        try:
            # Update lecturer fields
            if 'academic_rank' in request.POST:
                lecturer.academic_rank = request.POST.get('academic_rank', lecturer.academic_rank)
            if 'employment_type' in request.POST:
                lecturer.employment_type = request.POST.get('employment_type', lecturer.employment_type)
            if 'highest_qualification' in request.POST:
                lecturer.highest_qualification = request.POST.get('highest_qualification', '').strip()
            if 'university_graduated' in request.POST:
                lecturer.university_graduated = request.POST.get('university_graduated', '').strip()
            if 'graduation_year' in request.POST:
                graduation_year = request.POST.get('graduation_year', '').strip()
                lecturer.graduation_year = int(graduation_year) if graduation_year.isdigit() else lecturer.graduation_year
            if 'research_interests' in request.POST:
                lecturer.research_interests = request.POST.get('research_interests', '').strip()
            if 'publications' in request.POST:
                lecturer.publications = request.POST.get('publications', '').strip()
            if 'professional_registration' in request.POST:
                lecturer.professional_registration = request.POST.get('professional_registration', '').strip()
            if 'teaching_experience_years' in request.POST:
                teaching_exp = request.POST.get('teaching_experience_years', '0').strip()
                lecturer.teaching_experience_years = int(teaching_exp) if teaching_exp.isdigit() else lecturer.teaching_experience_years
            if 'research_experience_years' in request.POST:
                research_exp = request.POST.get('research_experience_years', '0').strip()
                lecturer.research_experience_years = int(research_exp) if research_exp.isdigit() else lecturer.research_experience_years
            if 'industry_experience_years' in request.POST:
                industry_exp = request.POST.get('industry_experience_years', '0').strip()
                lecturer.industry_experience_years = int(industry_exp) if industry_exp.isdigit() else lecturer.industry_experience_years
            if 'office_location' in request.POST:
                lecturer.office_location = request.POST.get('office_location', '').strip()
            if 'office_phone' in request.POST:
                lecturer.office_phone = request.POST.get('office_phone', '').strip()
            if 'consultation_hours' in request.POST:
                lecturer.consultation_hours = request.POST.get('consultation_hours', '').strip()
            
            lecturer.save()
            messages.success(request, "Professional details updated successfully!")
            
        except ValueError as e:
            messages.error(request, "Invalid input for numeric fields. Please check your entries.")
        except Exception as e:
            messages.error(request, f"Error updating professional details: {str(e)}")
    
    # Handle password change
    if all(field in request.POST for field in ['current_password', 'new_password1', 'new_password2']):
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate current password
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect('lecturer_profile')
        
        # Validate new passwords match
        if new_password1 != new_password2:
            messages.error(request, "New passwords do not match.")
            return redirect('lecturer_profile')
        
        # Validate password strength (basic validation)
        if len(new_password1) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
            return redirect('lecturer_profile')
        
        try:
            user.set_password(new_password1)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Password changed successfully!")
        except Exception as e:
            messages.error(request, f"Error changing password: {str(e)}")
    
    return redirect('lecturer_profile')


# Alternative AJAX view for profile picture upload (optional)
@login_required
@require_http_methods(["POST"])
def lecturer_profile_picture_upload(request):
    """
    Handle AJAX profile picture upload for lecturers
    """
    if request.user.user_type not in ['lecturer', 'professor']:
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    if 'profile_picture' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    
    profile_picture = request.FILES['profile_picture']
    
    # Validate file type
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
    file_extension = profile_picture.name.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid file type. Please upload JPG, JPEG, PNG, or GIF files only.'
        }, status=400)
    
    # Validate file size (5MB limit)
    if profile_picture.size > 5 * 1024 * 1024:
        return JsonResponse({
            'success': False, 
            'error': 'File size too large. Please upload files smaller than 5MB.'
        }, status=400)
    
    try:
        user = request.user
        
        # Delete old profile picture if exists
        if user.profile_picture:
            if default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)
        
        user.profile_picture = profile_picture
        user.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Profile picture updated successfully!',
            'profile_picture_url': user.profile_picture.url if user.profile_picture else None
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
import json

from .models import AcademicYear, Semester, Student, Programme, Enrollment


def is_admin(user):
    """Check if user is admin or has administrative privileges"""
    return user.is_authenticated and user.user_type in ['admin', 'registrar']


@login_required
@user_passes_test(is_admin)
def academic_management(request):
    """Main academic year and semester management dashboard"""
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    context = {
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'total_academic_years': AcademicYear.objects.count(),
        'total_semesters': Semester.objects.count(),
        'active_students': Student.objects.filter(status='active').count(),
    }
    return render(request, 'admin/academic_management.html', context)


@login_required
@user_passes_test(is_admin)
def get_academic_years(request):
    """AJAX endpoint to get all academic years with their semesters"""
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    years_data = []
    for year in academic_years:
        semesters = []
        for semester in year.semesters.all().order_by('semester_number'):
            semester_stats = {
                'total_students': Student.objects.filter(
                    current_year__lte=semester.academic_year.end_date.year - semester.academic_year.start_date.year + 1
                ).count(),
                'registrations': Enrollment.objects.filter(semester=semester).count() if hasattr(semester, 'courseenrollment_set') else 0
            }
            
            semesters.append({
                'id': semester.id,
                'semester_number': semester.semester_number,
                'start_date': semester.start_date.strftime('%Y-%m-%d'),
                'end_date': semester.end_date.strftime('%Y-%m-%d'),
                'registration_start_date': semester.registration_start_date.strftime('%Y-%m-%d'),
                'registration_end_date': semester.registration_end_date.strftime('%Y-%m-%d'),
                'is_current': semester.is_current,
                'stats': semester_stats
            })
        
        years_data.append({
            'id': year.id,
            'year': year.year,
            'start_date': year.start_date.strftime('%Y-%m-%d'),
            'end_date': year.end_date.strftime('%Y-%m-%d'),
            'is_current': year.is_current,
            'semesters': semesters
        })
    
    return JsonResponse({'academic_years': years_data})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_academic_year(request):
    """AJAX endpoint to create a new academic year"""
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            academic_year = AcademicYear.objects.create(
                year=data['year'],
                start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
                is_current=data.get('is_current', False)
            )
            
        return JsonResponse({
            'success': True,
            'message': f'Academic year {academic_year.year} created successfully!',
            'academic_year': {
                'id': academic_year.id,
                'year': academic_year.year,
                'start_date': academic_year.start_date.strftime('%Y-%m-%d'),
                'end_date': academic_year.end_date.strftime('%Y-%m-%d'),
                'is_current': academic_year.is_current
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating academic year: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_academic_year(request, year_id):
    """AJAX endpoint to update an academic year"""
    try:
        academic_year = get_object_or_404(AcademicYear, id=year_id)
        data = json.loads(request.body)
        
        with transaction.atomic():
            academic_year.year = data['year']
            academic_year.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            academic_year.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            academic_year.is_current = data.get('is_current', False)
            academic_year.save()
            
        return JsonResponse({
            'success': True,
            'message': f'Academic year {academic_year.year} updated successfully!',
            'academic_year': {
                'id': academic_year.id,
                'year': academic_year.year,
                'start_date': academic_year.start_date.strftime('%Y-%m-%d'),
                'end_date': academic_year.end_date.strftime('%Y-%m-%d'),
                'is_current': academic_year.is_current
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating academic year: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_academic_year(request, year_id):
    """AJAX endpoint to delete an academic year"""
    try:
        academic_year = get_object_or_404(AcademicYear, id=year_id)
        year_name = academic_year.year
        
        # Check if year has students or other dependencies
        if academic_year.semesters.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete academic year with existing semesters. Delete semesters first.'
            }, status=400)
        
        academic_year.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Academic year {year_name} deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting academic year: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_semester(request, year_id):
    """AJAX endpoint to create a new semester"""
    try:
        academic_year = get_object_or_404(AcademicYear, id=year_id)
        data = json.loads(request.body)
        
        with transaction.atomic():
            semester = Semester.objects.create(
                academic_year=academic_year,
                semester_number=data['semester_number'],
                start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
                registration_start_date=datetime.strptime(data['registration_start_date'], '%Y-%m-%d').date(),
                registration_end_date=datetime.strptime(data['registration_end_date'], '%Y-%m-%d').date(),
                is_current=data.get('is_current', False)
            )
            
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.semester_number} created successfully!',
            'semester': {
                'id': semester.id,
                'semester_number': semester.semester_number,
                'start_date': semester.start_date.strftime('%Y-%m-%d'),
                'end_date': semester.end_date.strftime('%Y-%m-%d'),
                'registration_start_date': semester.registration_start_date.strftime('%Y-%m-%d'),
                'registration_end_date': semester.registration_end_date.strftime('%Y-%m-%d'),
                'is_current': semester.is_current
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating semester: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_semester(request, semester_id):
    """AJAX endpoint to update a semester"""
    try:
        semester = get_object_or_404(Semester, id=semester_id)
        data = json.loads(request.body)
        
        with transaction.atomic():
            semester.semester_number = data['semester_number']
            semester.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            semester.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            semester.registration_start_date = datetime.strptime(data['registration_start_date'], '%Y-%m-%d').date()
            semester.registration_end_date = datetime.strptime(data['registration_end_date'], '%Y-%m-%d').date()
            semester.is_current = data.get('is_current', False)
            semester.save()
            
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.semester_number} updated successfully!',
            'semester': {
                'id': semester.id,
                'semester_number': semester.semester_number,
                'start_date': semester.start_date.strftime('%Y-%m-%d'),
                'end_date': semester.end_date.strftime('%Y-%m-%d'),
                'registration_start_date': semester.registration_start_date.strftime('%Y-%m-%d'),
                'registration_end_date': semester.registration_end_date.strftime('%Y-%m-%d'),
                'is_current': semester.is_current
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating semester: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_semester(request, semester_id):
    """AJAX endpoint to delete a semester"""
    try:
        semester = get_object_or_404(Semester, id=semester_id)
        semester_name = f"Semester {semester.semester_number}"
        
        # Check if semester has enrollments or other dependencies
        if hasattr(semester, 'courseenrollment_set') and semester.courseenrollment_set.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete semester with existing course enrollments.'
            }, status=400)
        
        semester.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{semester_name} deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting semester: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def set_current_academic_year(request, year_id):
    """AJAX endpoint to set current academic year"""
    try:
        with transaction.atomic():
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
            academic_year = get_object_or_404(AcademicYear, id=year_id)
            academic_year.is_current = True
            academic_year.save()
            
        return JsonResponse({
            'success': True,
            'message': f'Academic year {academic_year.year} set as current!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error setting current academic year: {str(e)}'
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def set_current_semester(request, semester_id):
    """AJAX endpoint to set current semester"""
    try:
        with transaction.atomic():
            Semester.objects.filter(is_current=True).update(is_current=False)
            semester = get_object_or_404(Semester, id=semester_id)
            semester.is_current = True
            semester.save()
            
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.semester_number} ({semester.academic_year.year}) set as current!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error setting current semester: {str(e)}'
        }, status=400)

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import Semester, Programme, Enrollment

@login_required
@user_passes_test(is_admin)
def get_semester_registrations(request, semester_id):
    """AJAX endpoint to get semester registration details"""
    try:
        semester = get_object_or_404(Semester, id=semester_id)
        
        # Get all programmes and count enrollments for this semester
        programmes = Programme.objects.filter(is_active=True).annotate(
            enrollment_count=Count(
                'students__enrollments',
                filter=Q(students__enrollments__semester=semester) & Q(students__enrollments__is_active=True),
                distinct=True
            )
        ).select_related('department', 'faculty')
        
        programmes_data = []
        total_registrations = 0
        
        for programme in programmes:
            enrollment_count = programme.enrollment_count
            total_registrations += enrollment_count
            
            programmes_data.append({
                'id': programme.id,
                'name': programme.name,
                'code': programme.code,
                'programme_type': programme.get_programme_type_display(),
                'department': programme.department.name if programme.department else 'N/A',
                'enrollment_count': enrollment_count
            })
        
        # Sort by enrollment count (highest first)
        programmes_data.sort(key=lambda x: x['enrollment_count'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'semester': {
                'id': semester.id,
                'name': f"Semester {semester.semester_number}",
                'academic_year': semester.academic_year.year,
                'registration_start': semester.registration_start_date.strftime('%Y-%m-%d') if semester.registration_start_date else 'N/A',
                'registration_end': semester.registration_end_date.strftime('%Y-%m-%d') if semester.registration_end_date else 'N/A',
            },
            'programmes': programmes_data,
            'total_registrations': total_registrations
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_semester_registrations: {str(e)}")
        print(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'message': f'Error fetching semester registrations: {str(e)}'
        }, status=400)



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from .models import (
    HostelBooking, Hostel, Room, Bed, AcademicYear, 
    Student, HostelPayment, HostelIncident
)

def is_admin_or_warden(user):
    """Check if user is admin or hostel warden"""
    return user.is_superuser or user.user_type in ['admin', 'hostel_warden']

@login_required
@user_passes_test(is_admin_or_warden)
def manage_hostel_bookings(request):
    """Main view for managing hostel bookings"""
    # Get all academic years
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get selected academic year from request or use current
    selected_year_id = request.GET.get('year', current_year.id if current_year else None)
    selected_year = get_object_or_404(AcademicYear, id=selected_year_id) if selected_year_id else academic_years.first()
    
    # Get all hostels
    hostels = Hostel.objects.filter(is_active=True).prefetch_related('rooms__beds')
    
    # Get booking statistics for selected year
    booking_stats = get_booking_statistics(selected_year)
    
    # Get hostels with availability data
    hostels_data = []
    for hostel in hostels:
        hostel_data = {
            'hostel': hostel,
            'total_beds': hostel.get_total_beds_count(selected_year),
            'occupied_beds': hostel.get_occupied_beds_count(selected_year),
            'available_beds': hostel.get_total_beds_count(selected_year) - hostel.get_occupied_beds_count(selected_year),
            'occupancy_rate': 0
        }
        if hostel_data['total_beds'] > 0:
            hostel_data['occupancy_rate'] = round(
                (hostel_data['occupied_beds'] / hostel_data['total_beds']) * 100, 1
            )
        hostels_data.append(hostel_data)
    
    context = {
        'academic_years': academic_years,
        'selected_year': selected_year,
        'hostels_data': hostels_data,
        'booking_stats': booking_stats,
    }
    
    return render(request, 'hostels/manage_bookings.html', context)

@login_required
@user_passes_test(is_admin_or_warden)
def get_booking_data(request):
    """AJAX endpoint to get booking data for specific academic year"""
    year_id = request.GET.get('year_id')
    hostel_id = request.GET.get('hostel_id')
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    if not year_id:
        return JsonResponse({'error': 'Academic year required'}, status=400)
    
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    # Build query
    bookings = HostelBooking.objects.filter(
        academic_year=academic_year
    ).select_related(
        'student__user', 'bed__room__hostel', 'approved_by'
    ).order_by('-booking_date')
    
    # Apply filters
    if hostel_id and hostel_id != 'all':
        bookings = bookings.filter(bed__room__hostel_id=hostel_id)
    
    if status and status != 'all':
        bookings = bookings.filter(booking_status=status)
    
    if search:
        bookings = bookings.filter(
            Q(student__student_id__icontains=search) |
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(bed__bed_number__icontains=search)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(bookings, 20)
    bookings_page = paginator.get_page(page)
    
    # Serialize data
    bookings_data = []
    for booking in bookings_page:
        bookings_data.append({
            'id': booking.id,
            'student_id': booking.student.student_id,
            'student_name': booking.student.user.get_full_name(),
            'hostel_name': booking.bed.room.hostel.name,
            'room_number': booking.bed.room.room_number,
            'bed_number': booking.bed.bed_number,
            'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M'),
            'check_in_date': booking.check_in_date.strftime('%Y-%m-%d') if booking.check_in_date else None,
            'check_out_date': booking.check_out_date.strftime('%Y-%m-%d') if booking.check_out_date else None,
            'booking_status': booking.booking_status,
            'booking_status_display': booking.get_booking_status_display(),
            'payment_status': booking.payment_status,
            'payment_status_display': booking.get_payment_status_display(),
            'booking_fee': str(booking.booking_fee),
            'amount_paid': str(booking.amount_paid),
            'balance_due': str(booking.balance_due),
            'approved_by': booking.approved_by.get_full_name() if booking.approved_by else None,
            'approval_date': booking.approval_date.strftime('%Y-%m-%d %H:%M') if booking.approval_date else None,
        })
    
    return JsonResponse({
        'bookings': bookings_data,
        'has_next': bookings_page.has_next(),
        'has_previous': bookings_page.has_previous(),
        'page_number': bookings_page.number,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
    })

@login_required
@user_passes_test(is_admin_or_warden)
def get_room_availability(request):
    """AJAX endpoint to get room availability for a hostel"""
    hostel_id = request.GET.get('hostel_id')
    year_id = request.GET.get('year_id')
    
    if not hostel_id or not year_id:
        return JsonResponse({'error': 'Hostel and academic year required'}, status=400)
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    academic_year = get_object_or_404(AcademicYear, id=year_id)
    
    rooms_data = []
    for room in hostel.rooms.filter(is_active=True).prefetch_related('beds'):
        # Get beds for this academic year
        beds = room.beds.filter(academic_year=academic_year)
        
        room_data = {
            'id': room.id,
            'room_number': room.room_number,
            'floor': room.floor,
            'capacity': room.capacity,
            'total_beds': beds.count(),
            'available_beds': beds.filter(is_available=True).count(),
            'occupied_beds': beds.filter(is_available=False).count(),
            'beds': []
        }
        
        # Get bed details
        for bed in beds:
            booking = HostelBooking.objects.filter(
                bed=bed, 
                academic_year=academic_year,
                booking_status__in=['approved', 'checked_in']
            ).select_related('student__user').first()
            
            bed_data = {
                'id': bed.id,
                'bed_number': bed.bed_number,
                'bed_position': bed.get_bed_position_display(),
                'is_available': bed.is_available,
                'maintenance_status': bed.maintenance_status,
                'maintenance_status_display': bed.get_maintenance_status_display(),
                'student': {
                    'id': booking.student.id,
                    'student_id': booking.student.student_id,
                    'name': booking.student.user.get_full_name(),
                    'booking_status': booking.booking_status,
                } if booking else None
            }
            room_data['beds'].append(bed_data)
        
        # Calculate occupancy rate
        if room_data['total_beds'] > 0:
            room_data['occupancy_rate'] = round(
                (room_data['occupied_beds'] / room_data['total_beds']) * 100, 1
            )
        else:
            room_data['occupancy_rate'] = 0
            
        rooms_data.append(room_data)
    
    return JsonResponse({
        'hostel_name': hostel.name,
        'rooms': rooms_data
    })

@login_required
@user_passes_test(is_admin_or_warden)
def update_booking_status(request):
    """AJAX endpoint to update booking status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    booking_id = request.POST.get('booking_id')
    new_status = request.POST.get('status')
    remarks = request.POST.get('remarks', '')
    
    if not booking_id or not new_status:
        return JsonResponse({'error': 'Booking ID and status required'}, status=400)
    
    booking = get_object_or_404(HostelBooking, id=booking_id)
    old_status = booking.booking_status
    
    # Update booking status
    booking.booking_status = new_status
    booking.approval_remarks = remarks
    
    if new_status in ['approved', 'rejected']:
        booking.approved_by = request.user
        booking.approval_date = timezone.now()
    
    if new_status == 'checked_in':
        booking.checked_in_by = request.user
        booking.check_in_date = timezone.now().date()
    
    if new_status == 'checked_out':
        booking.checked_out_by = request.user
        booking.check_out_date = timezone.now().date()
    
    booking.save()  # This will automatically update bed availability
    
    return JsonResponse({
        'success': True,
        'message': f'Booking status updated from {old_status} to {new_status}',
        'new_status': booking.get_booking_status_display()
    })

def get_booking_statistics(academic_year):
    """Helper function to get booking statistics"""
    bookings = HostelBooking.objects.filter(academic_year=academic_year)
    
    stats = {
        'total_bookings': bookings.count(),
        'pending': bookings.filter(booking_status='pending').count(),
        'approved': bookings.filter(booking_status='approved').count(),
        'rejected': bookings.filter(booking_status='rejected').count(),
        'checked_in': bookings.filter(booking_status='checked_in').count(),
        'checked_out': bookings.filter(booking_status='checked_out').count(),
        'cancelled': bookings.filter(booking_status='cancelled').count(),
        'total_revenue': bookings.aggregate(
            total=Sum('booking_fee')
        )['total'] or 0,
        'collected_revenue': bookings.aggregate(
            collected=Sum('amount_paid')
        )['collected'] or 0,
        'pending_payments': bookings.filter(
            payment_status__in=['pending', 'partial']
        ).count(),
    }
    
    # Calculate occupancy rates by hostel type
    boys_hostels = Hostel.objects.filter(hostel_type='boys', is_active=True)
    girls_hostels = Hostel.objects.filter(hostel_type='girls', is_active=True)
    
    boys_total = sum(h.get_total_beds_count(academic_year) for h in boys_hostels)
    boys_occupied = sum(h.get_occupied_beds_count(academic_year) for h in boys_hostels)
    
    girls_total = sum(h.get_total_beds_count(academic_year) for h in girls_hostels)
    girls_occupied = sum(h.get_occupied_beds_count(academic_year) for h in girls_hostels)
    
    stats['boys_occupancy'] = round((boys_occupied / boys_total * 100), 1) if boys_total > 0 else 0
    stats['girls_occupancy'] = round((girls_occupied / girls_total * 100), 1) if girls_total > 0 else 0
    stats['overall_occupancy'] = round(((boys_occupied + girls_occupied) / (boys_total + girls_total) * 100), 1) if (boys_total + girls_total) > 0 else 0
    
    return stats

# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse
import json
from .models import Hostel, Room, Bed, AcademicYear, Department

@login_required
@require_http_methods(["GET", "POST"])
def hostel_room_management(request, hostel_id):
    """Main view for managing rooms in a hostel"""
    hostel = get_object_or_404(Hostel, id=hostel_id)
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    academic_years = AcademicYear.objects.all().order_by('-year')
    
    # Get selected academic year from request
    selected_year_id = request.GET.get('academic_year', current_academic_year.id if current_academic_year else None)
    selected_academic_year = get_object_or_404(AcademicYear, id=selected_year_id) if selected_year_id else None
    
    # Get rooms for the hostel with pagination
    rooms = Room.objects.filter(hostel=hostel).order_by('floor', 'room_number')
    # Calculate bed counts for each room
    for room in rooms:
        if selected_academic_year:
            room.available_beds = room.get_available_beds_count(selected_academic_year)
            room.occupied_beds = room.get_occupied_beds_count(selected_academic_year)
        else:
            room.available_beds = 0
            room.occupied_beds = 0

    paginator = Paginator(rooms, 20)  # Show 20 rooms per page
    page_number = request.GET.get('page')
    page_rooms = paginator.get_page(page_number)
    
    # Get room statistics
    total_rooms = rooms.count()
    active_rooms = rooms.filter(is_active=True).count()
    inactive_rooms = total_rooms - active_rooms
    
    # Get bed statistics for selected academic year
    bed_stats = {}
    if selected_academic_year:
        bed_stats = {
            'total_beds': Bed.objects.filter(
                room__hostel=hostel,
                academic_year=selected_academic_year
            ).count(),
            'available_beds': Bed.objects.filter(
                room__hostel=hostel,
                academic_year=selected_academic_year,
                is_available=True
            ).count(),
            'occupied_beds': Bed.objects.filter(
                room__hostel=hostel,
                academic_year=selected_academic_year,
                is_available=False
            ).count(),
        }
    
    context = {
        'hostel': hostel,
        'rooms': page_rooms,
        'total_rooms': total_rooms,
        'active_rooms': active_rooms,
        'inactive_rooms': inactive_rooms,
        'academic_years': academic_years,
        'selected_academic_year': selected_academic_year,
        'bed_stats': bed_stats,
        'floors': sorted(set(room.floor for room in rooms)) if rooms else [],
    }
    
    return render(request, 'hostels/room_management.html', context)

@login_required
@require_http_methods(["POST"])
def create_single_room(request, hostel_id):
    """Create a single room via AJAX"""
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    try:
        data = json.loads(request.body)
        room_number = data.get('room_number', '').strip()
        floor = int(data.get('floor', 0))
        capacity = int(data.get('capacity', 4))
        description = data.get('description', '').strip()
        facilities = data.get('facilities', '').strip()
        
        # Validate room number
        if not room_number:
            return JsonResponse({'success': False, 'message': 'Room number is required'})
        
        # Check if room already exists
        if Room.objects.filter(hostel=hostel, room_number=room_number).exists():
            return JsonResponse({'success': False, 'message': f'Room {room_number} already exists'})
        
        # Create the room
        room = Room.objects.create(
            hostel=hostel,
            room_number=room_number,
            floor=floor,
            capacity=capacity,
            description=description,
            facilities=facilities
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Room {room_number} created successfully',
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'floor': room.floor,
                'capacity': room.capacity,
                'is_active': room.is_active,
                'created_at': room.created_at.strftime('%Y-%m-%d %H:%M:%S') if room.created_at else ''
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except ValueError as e:
        return JsonResponse({'success': False, 'message': 'Invalid number format'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error creating room: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def bulk_create_rooms(request, hostel_id):
    """Create multiple rooms with auto-generated numbers"""
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    try:
        data = json.loads(request.body)
        room_prefix = data.get('room_prefix', '').strip().upper()
        start_number = int(data.get('start_number', 1))
        room_count = int(data.get('room_count', 1))
        floor = int(data.get('floor', 0))
        capacity = int(data.get('capacity', 4))
        description = data.get('description', '').strip()
        facilities = data.get('facilities', '').strip()
        
        # Validation
        if not room_prefix:
            return JsonResponse({'success': False, 'message': 'Room prefix is required'})
        
        if room_count > 500:  # Prevent creating too many rooms at once
            return JsonResponse({'success': False, 'message': 'Cannot create more than 500 rooms at once'})
        
        if room_count < 1:
            return JsonResponse({'success': False, 'message': 'Room count must be at least 1'})
        
        created_rooms = []
        existing_rooms = []
        
        with transaction.atomic():
            for i in range(room_count):
                room_number = f"{room_prefix}{start_number + i:03d}"  # Format: KL001, KL002, etc.
                
                # Check if room already exists
                if Room.objects.filter(hostel=hostel, room_number=room_number).exists():
                    existing_rooms.append(room_number)
                    continue
                
                # Create the room
                room = Room.objects.create(
                    hostel=hostel,
                    room_number=room_number,
                    floor=floor,
                    capacity=capacity,
                    description=description,
                    facilities=facilities
                )
                
                created_rooms.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'floor': room.floor,
                    'capacity': room.capacity,
                    'is_active': room.is_active
                })
        
        message = f"Successfully created {len(created_rooms)} rooms"
        if existing_rooms:
            message += f". {len(existing_rooms)} rooms already existed: {', '.join(existing_rooms[:5])}"
            if len(existing_rooms) > 5:
                message += f" and {len(existing_rooms) - 5} more"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'created_count': len(created_rooms),
            'existing_count': len(existing_rooms),
            'rooms': created_rooms
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except ValueError as e:
        return JsonResponse({'success': False, 'message': 'Invalid number format'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error creating rooms: {str(e)}'})

@login_required
@require_http_methods(["DELETE"])
def delete_room(request, room_id):
    """Delete a single room via AJAX"""
    room = get_object_or_404(Room, id=room_id)
    
    try:
        # Check if room has any beds with students
        occupied_beds = Bed.objects.filter(room=room, is_available=False).exists()
        if occupied_beds:
            return JsonResponse({
                'success': False, 
                'message': 'Cannot delete room with occupied beds'
            })
        
        room_number = room.room_number
        room.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Room {room_number} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error deleting room: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def bulk_delete_rooms(request, hostel_id):
    """Delete multiple rooms via AJAX"""
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    try:
        data = json.loads(request.body)
        room_ids = data.get('room_ids', [])
        
        if not room_ids:
            return JsonResponse({'success': False, 'message': 'No rooms selected'})
        
        # Get rooms to delete
        rooms = Room.objects.filter(id__in=room_ids, hostel=hostel)
        
        # Check for rooms with occupied beds
        rooms_with_students = []
        for room in rooms:
            if Bed.objects.filter(room=room, is_available=False).exists():
                rooms_with_students.append(room.room_number)
        
        if rooms_with_students:
            return JsonResponse({
                'success': False,
                'message': f'Cannot delete rooms with occupied beds: {", ".join(rooms_with_students)}'
            })
        
        deleted_count = rooms.count()
        rooms.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} rooms'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error deleting rooms: {str(e)}'})

@login_required
@require_http_methods(["POST"])
def toggle_room_status(request, room_id):
    """Toggle room active/inactive status via AJAX"""
    room = get_object_or_404(Room, id=room_id)
    
    try:
        room.is_active = not room.is_active
        room.save()
        
        status = "activated" if room.is_active else "deactivated"
        
        return JsonResponse({
            'success': True,
            'message': f'Room {room.room_number} {status} successfully',
            'is_active': room.is_active
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating room status: {str(e)}'})

@login_required
def get_room_details(request, room_id):
    """Get detailed information about a room via AJAX"""
    room = get_object_or_404(Room, id=room_id)
    academic_year_id = request.GET.get('academic_year')
    
    try:
        academic_year = None
        bed_info = {}
        
        if academic_year_id:
            academic_year = AcademicYear.objects.get(id=academic_year_id)
            beds = Bed.objects.filter(room=room, academic_year=academic_year)
            bed_info = {
                'total_beds': beds.count(),
                'available_beds': beds.filter(is_available=True).count(),
                'occupied_beds': beds.filter(is_available=False).count(),
                'maintenance_beds': beds.filter(maintenance_status__in=['needs_repair', 'under_maintenance', 'out_of_order']).count()
            }
        
        return JsonResponse({
            'success': True,
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'floor': room.floor,
                'capacity': room.capacity,
                'description': room.description,
                'facilities': room.facilities,
                'is_active': room.is_active,
                'bed_info': bed_info
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error getting room details: {str(e)}'})

@login_required
def get_hostel_list(request):
    """Get list of hostels for room management"""
    # Check if user can manage hostels (customize based on your permissions)
    if request.user.user_type not in ['admin', 'hostel_warden', 'staff']:
        messages.error(request, 'You do not have permission to manage hostels')
        return redirect('student_dashboard')  # or appropriate redirect
    
    hostels = Hostel.objects.filter(is_active=True).order_by('hostel_type', 'name')
    
    context = {
        'hostels': hostels
    }
    
    return render(request, 'hostels/warden_hostel_list.html', context)



from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from .models import (
    Student, Enrollment, Course, AcademicYear, Semester, 
    Programme, Faculty, Department, ProgrammeCourse
)
import json

@staff_member_required
@login_required
def admin_student_enrollment_list(request):
    """Main view to display list of students for enrollment management"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    programme_filter = request.GET.get('programme', '')
    faculty_filter = request.GET.get('faculty', '')
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year', '')
    
    # Base queryset with related data
    students = Student.objects.select_related(
        'user', 'programme', 'programme__department', 'programme__faculty'
    ).annotate(
        total_enrollments=Count('enrollments')
    ).order_by('-admission_date')
    
    # Apply filters
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if programme_filter:
        students = students.filter(programme_id=programme_filter)
    
    if faculty_filter:
        students = students.filter(programme__faculty_id=faculty_filter)
    
    if status_filter:
        students = students.filter(status=status_filter)
    
    if year_filter:
        students = students.filter(current_year=year_filter)
    
    # Pagination
    paginator = Paginator(students, 12)  # 12 students per page
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)
    
    # Get filter options
    programmes = Programme.objects.filter(is_active=True).select_related('faculty')
    faculties = Faculty.objects.filter(is_active=True)
    
    context = {
        'students': students_page,
        'programmes': programmes,
        'faculties': faculties,
        'search_query': search_query,
        'programme_filter': programme_filter,
        'faculty_filter': faculty_filter,
        'status_filter': status_filter,
        'year_filter': year_filter,
        'student_statuses': Student.STATUS_CHOICES,
        'current_years': range(1, 9),  # 1-8 years
    }
    
    return render(request, 'admin/student_enrollment_list.html', context)

@staff_member_required
@login_required
def get_student_enrollments(request, student_id):
    """AJAX view to fetch student enrollments organized by academic year and semester"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        student = get_object_or_404(
            Student.objects.select_related('user', 'programme'), 
            id=student_id
        )
        
        # Get all enrollments with related data
        enrollments = Enrollment.objects.filter(
            student=student
        ).select_related(
            'course', 'semester', 'semester__academic_year', 'lecturer', 'lecturer__user'
        ).order_by(
            'semester__academic_year__start_date', 'semester__semester_number', 'course__name'
        )
        
        # Organize enrollments by academic year and semester
        enrollment_data = {}
        
        for enrollment in enrollments:
            academic_year = enrollment.semester.academic_year
            semester_num = enrollment.semester.semester_number
            
            year_key = academic_year.year
            semester_key = f"semester_{semester_num}"
            
            if year_key not in enrollment_data:
                enrollment_data[year_key] = {
                    'academic_year': {
                        'id': academic_year.id,
                        'year': academic_year.year,
                        'start_date': academic_year.start_date.strftime('%Y-%m-%d'),
                        'end_date': academic_year.end_date.strftime('%Y-%m-%d'),
                        'is_current': academic_year.is_current,
                    },
                    'semesters': {}
                }
            
            if semester_key not in enrollment_data[year_key]['semesters']:
                enrollment_data[year_key]['semesters'][semester_key] = {
                    'semester_info': {
                        'id': enrollment.semester.id,
                        'number': semester_num,
                        'start_date': enrollment.semester.start_date.strftime('%Y-%m-%d'),
                        'end_date': enrollment.semester.end_date.strftime('%Y-%m-%d'),
                        'is_current': enrollment.semester.is_current,
                    },
                    'enrollments': []
                }
            
            # Add enrollment data
            enrollment_info = {
                'id': enrollment.id,
                'course': {
                    'id': enrollment.course.id,
                    'name': enrollment.course.name,
                    'code': enrollment.course.code,
                    'credit_hours': enrollment.course.credit_hours,
                    'course_type': enrollment.course.course_type,
                    'course_type_display': enrollment.course.get_course_type_display(),
                    'level': enrollment.course.level,
                },
                'lecturer': {
                    'id': enrollment.lecturer.id if enrollment.lecturer else None,
                    'name': enrollment.lecturer.user.get_full_name() if enrollment.lecturer else 'Not Assigned',
                    'academic_rank': enrollment.lecturer.academic_rank if enrollment.lecturer else '',
                } if enrollment.lecturer else None,
                'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d'),
                'is_active': enrollment.is_active,
                'is_repeat': enrollment.is_repeat,
                'is_audit': enrollment.is_audit,
            }
            
            enrollment_data[year_key]['semesters'][semester_key]['enrollments'].append(enrollment_info)
        
        # Get available courses for adding new enrollments
        available_courses = get_available_courses_for_student(student)
        
        response_data = {
            'student': {
                'id': student.id,
                'student_id': student.student_id,
                'name': student.user.get_full_name(),
                'email': student.user.email,
                'programme': {
                    'name': student.programme.name,
                    'code': student.programme.code,
                },
                'current_year': student.current_year,
                'current_semester': student.current_semester,
                'status': student.status,
                'admission_date': student.admission_date.strftime('%Y-%m-%d'),
            },
            'enrollment_data': enrollment_data,
            'available_courses': available_courses,
            'success': True
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch enrollments: {str(e)}',
            'success': False
        }, status=500)

def get_available_courses_for_student(student):
    """Get courses available for the student based on their programme"""
    # Get programme courses for the student's current level
    programme_courses = ProgrammeCourse.objects.filter(
        programme=student.programme,
        is_active=True,
        year__lte=student.current_year
    ).select_related('course').order_by('year', 'semester', 'course__name')
    
    # Get already enrolled course IDs
    enrolled_course_ids = Enrollment.objects.filter(
        student=student
    ).values_list('course_id', flat=True)
    
    available_courses = []
    for pc in programme_courses:
        if pc.course.id not in enrolled_course_ids:
            available_courses.append({
                'id': pc.course.id,
                'name': pc.course.name,
                'code': pc.course.code,
                'credit_hours': pc.course.credit_hours,
                'course_type': pc.course.get_course_type_display(),
                'level': pc.course.level,
                'year': pc.year,
                'semester': pc.semester,
                'is_mandatory': pc.is_mandatory,
            })
    
    return available_courses

@staff_member_required
@login_required
@require_http_methods(["POST"])
def add_student_enrollment(request):
    """AJAX view to add new enrollment for a student"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        semester_id = data.get('semester_id')
        lecturer_id = data.get('lecturer_id')
        
        # Validate required fields
        if not all([student_id, course_id, semester_id]):
            return JsonResponse({
                'error': 'Student, course, and semester are required',
                'success': False
            }, status=400)
        
        # Get objects
        student = get_object_or_404(Student, id=student_id)
        course = get_object_or_404(Course, id=course_id)
        semester = get_object_or_404(Semester, id=semester_id)
        lecturer = None
        
        if lecturer_id:
            lecturer = get_object_or_404(Lecturer, id=lecturer_id)
        
        # Check if enrollment already exists
        existing_enrollment = Enrollment.objects.filter(
            student=student,
            course=course,
            semester=semester
        ).first()
        
        if existing_enrollment:
            return JsonResponse({
                'error': 'Student is already enrolled in this course for this semester',
                'success': False
            }, status=400)
        
        # Create enrollment
        with transaction.atomic():
            enrollment = Enrollment.objects.create(
                student=student,
                course=course,
                semester=semester,
                lecturer=lecturer,
                is_active=True
            )
        
        return JsonResponse({
            'message': f'Successfully enrolled {student.user.get_full_name()} in {course.name}',
            'enrollment_id': enrollment.id,
            'success': True
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'success': False
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to add enrollment: {str(e)}',
            'success': False
        }, status=500)

@staff_member_required
@login_required
@require_http_methods(["DELETE"])
def delete_student_enrollment(request, enrollment_id):
    """AJAX view to delete a student enrollment"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        enrollment = get_object_or_404(
            Enrollment.objects.select_related('student__user', 'course'),
            id=enrollment_id
        )
        
        student_name = enrollment.student.user.get_full_name()
        course_name = enrollment.course.name
        
        enrollment.delete()
        
        return JsonResponse({
            'message': f'Successfully removed {student_name} from {course_name}',
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to delete enrollment: {str(e)}',
            'success': False
        }, status=500)

@staff_member_required
@login_required
def get_semester_options(request):
    """AJAX view to get available semesters for enrollment"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        semesters = Semester.objects.select_related('academic_year').filter(
            academic_year__is_current=True
        ).order_by('semester_number')
        
        semester_options = []
        for semester in semesters:
            semester_options.append({
                'id': semester.id,
                'display_name': f"{semester.academic_year.year} - Semester {semester.semester_number}",
                'semester_number': semester.semester_number,
                'academic_year': semester.academic_year.year,
                'is_current': semester.is_current,
            })
        
        return JsonResponse({
            'semesters': semester_options,
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch semesters: {str(e)}',
            'success': False
        }, status=500)
    

# Add these views to your views.py file

@staff_member_required
@login_required
def get_programme_students(request, programme_id):
    """Get students for a specific programme (for bulk enrollment)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        programme = get_object_or_404(Programme, id=programme_id, is_active=True)
        
        # Get students enrolled in this programme
        students = Student.objects.filter(
            programme=programme,
            status__in=['active', 'deferred']  # Only active and deferred students
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        
        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'name': student.user.get_full_name(),
                'student_id': student.student_id,
                'current_year': student.current_year,
                'current_semester': student.current_semester,
                'status': student.status,
                'status_display': student.get_status_display(),
                'email': student.user.email,
            })
        
        return JsonResponse({
            'success': True,
            'students': student_data,
            'programme': {
                'id': programme.id,
                'name': programme.name,
                'code': programme.code,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch students: {str(e)}',
            'success': False
        }, status=500)


@staff_member_required
@login_required  
def get_programme_courses(request, programme_id):
    """Get courses for a specific programme/year/semester (for bulk enrollment)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        programme = get_object_or_404(Programme, id=programme_id, is_active=True)
        year = request.GET.get('year')
        semester = request.GET.get('semester')
        
        if not year or not semester:
            return JsonResponse({
                'error': 'Year and semester parameters are required',
                'success': False
            }, status=400)
        
        # Get programme courses for the specified year and semester
        programme_courses = ProgrammeCourse.objects.filter(
            programme=programme,
            year=year,
            semester=semester,
            is_active=True
        ).select_related('course').order_by('course__name')
        
        course_data = []
        for pc in programme_courses:
            course_data.append({
                'id': pc.course.id,
                'name': pc.course.name,
                'code': pc.course.code,
                'credit_hours': pc.course.credit_hours,
                'course_type': pc.course.get_course_type_display(),
                'course_type_raw': pc.course.course_type,
                'level': pc.course.level,
                'is_mandatory': pc.is_mandatory,
                'year': pc.year,
                'semester': pc.semester,
                'description': pc.course.description,
                'department': pc.course.department.name,
            })
        
        return JsonResponse({
            'success': True,
            'courses': course_data,
            'programme': {
                'id': programme.id,
                'name': programme.name,
                'code': programme.code,
            },
            'filters': {
                'year': year,
                'semester': semester,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch courses: {str(e)}',
            'success': False
        }, status=500)


@staff_member_required
@login_required
@require_http_methods(["POST"])
def bulk_add_enrollments(request):
    """Handle bulk enrollment creation"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
        course_ids = data.get('course_ids', [])
        semester_id = data.get('semester_id')
        
        # Validate required fields
        if not student_ids or not course_ids or not semester_id:
            return JsonResponse({
                'error': 'Student IDs, course IDs, and semester ID are required',
                'success': False
            }, status=400)
        
        # Get objects
        students = Student.objects.filter(id__in=student_ids)
        courses = Course.objects.filter(id__in=course_ids)
        semester = get_object_or_404(Semester, id=semester_id)
        
        if len(students) != len(student_ids):
            return JsonResponse({
                'error': 'Some students were not found',
                'success': False
            }, status=400)
        
        if len(courses) != len(course_ids):
            return JsonResponse({
                'error': 'Some courses were not found',
                'success': False
            }, status=400)
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        with transaction.atomic():
            for student in students:
                for course in courses:
                    # Check if enrollment already exists
                    existing_enrollment = Enrollment.objects.filter(
                        student=student,
                        course=course,
                        semester=semester
                    ).first()
                    
                    if existing_enrollment:
                        skipped_count += 1
                        continue
                    
                    try:
                        # Create enrollment
                        enrollment = Enrollment.objects.create(
                            student=student,
                            course=course,
                            semester=semester,
                            is_active=True,
                            is_repeat=False,
                            is_audit=False
                        )
                        created_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append({
                            'student': student.user.get_full_name(),
                            'course': course.name,
                            'error': str(e)
                        })
        
        # Prepare response
        response_data = {
            'success': True,
            'created_count': created_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'total_attempted': len(student_ids) * len(course_ids),
            'message': f'Bulk enrollment completed. Created: {created_count}, Skipped: {skipped_count}, Errors: {error_count}'
        }
        
        if errors:
            response_data['errors'] = errors[:10]  # Limit to first 10 errors
            if len(errors) > 10:
                response_data['additional_errors'] = len(errors) - 10
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'success': False
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to perform bulk enrollment: {str(e)}',
            'success': False
        }, status=500)


# Additional helper view for getting lecturers (optional - for lecturer assignment in enrollment modal)
@staff_member_required
@login_required
def get_course_lecturers(request, course_id):
    """Get lecturers who can teach a specific course"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        course = get_object_or_404(Course, id=course_id)
        
        # Get lecturers from the same department as the course
        lecturers = Lecturer.objects.filter(
            department=course.department,
            is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        
        lecturer_data = []
        for lecturer in lecturers:
            lecturer_data.append({
                'id': lecturer.id,
                'name': lecturer.user.get_full_name(),
                'academic_rank': lecturer.get_academic_rank_display(),
                'employee_number': lecturer.employee_number,
            })
        
        return JsonResponse({
            'success': True,
            'lecturers': lecturer_data,
            'course': {
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'department': course.department.name,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch lecturers: {str(e)}',
            'success': False
        }, status=500)

# departments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse
import json
import csv
from datetime import datetime

from .models import Department, Faculty, User
from .forms import DepartmentForm


def is_admin_or_staff(user):
    """Check if user is admin or staff member"""
    return user.is_authenticated and user.user_type in ['admin', 'registrar', 'dean']


@login_required
@user_passes_test(is_admin_or_staff)
def department_list(request):
    """List all departments with filtering and search"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    faculty_filter = request.GET.get('faculty', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset with related data
    departments = Department.objects.select_related(
        'faculty', 
        'head_of_department'
    ).annotate(
        total_programmes=Count('programmes', distinct=True),
        total_students=Count('programmes__students', distinct=True)
    )
    
    # Apply search filter
    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(faculty__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply faculty filter
    if faculty_filter:
        departments = departments.filter(faculty_id=faculty_filter)
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            departments = departments.filter(is_active=True)
        elif status_filter == 'inactive':
            departments = departments.filter(is_active=False)
    
    # Order by name
    departments = departments.order_by('faculty__name', 'name')
    
    # Pagination
    paginator = Paginator(departments, 25)
    page_number = request.GET.get('page')
    departments_page = paginator.get_page(page_number)
    
    # Get all faculties for filter dropdown
    faculties = Faculty.objects.filter(is_active=True).order_by('name')
    
    # Status choices for filter
    status_choices = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    # Calculate totals
    total_departments = Department.objects.count()
    active_departments = Department.objects.filter(is_active=True).count()
    inactive_departments = Department.objects.filter(is_active=False).count()
    
    context = {
        'departments': departments_page,
        'faculties': faculties,
        'status_choices': status_choices,
        'search_query': search_query,
        'faculty_filter': faculty_filter,
        'status_filter': status_filter,
        'total_departments': total_departments,
        'active_departments': active_departments,
        'inactive_departments': inactive_departments,
    }
    
    return render(request, 'departments/department_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def department_detail(request, code):
    """Get department details via AJAX"""
    department = get_object_or_404(Department, code=code)
    
    if request.method == 'GET':
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {
                'id': department.id,
                'name': department.name,
                'code': department.code,
                'faculty_name': department.faculty.name,
                'faculty_code': department.faculty.code,
                'head_of_department': {
                    'name': department.head_of_department.get_full_name() if department.head_of_department else None,
                    'email': department.head_of_department.email if department.head_of_department else None,
                    'phone': department.head_of_department.phone if department.head_of_department else None,
                } if department.head_of_department else None,
                'description': department.description,
                'established_date': department.established_date.strftime('%Y-%m-%d') if department.established_date else None,
                'is_active': department.is_active,
                'total_programmes': getattr(department, 'total_programmes', 0),
                'total_students': getattr(department, 'total_students', 0),
            }
            return JsonResponse(data)
        
        # Regular page view
        context = {
            'department': department,
        }
        return render(request, 'departments/department_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def department_create(request):
    """Create new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            
            # AJAX response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Department "{department.name}" created successfully!',
                    'department': {
                        'id': department.id,
                        'name': department.name,
                        'code': department.code,
                        'faculty_name': department.faculty.name,
                    }
                })
            
            messages.success(request, f'Department "{department.name}" created successfully!')
            return redirect('department_list')
        else:
            # AJAX error response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = DepartmentForm()
    
    # Get faculties for dropdown
    faculties = Faculty.objects.filter(is_active=True).order_by('name')
    
    # Get potential HODs (lecturers, professors, staff)
    potential_hods = User.objects.filter(
        user_type__in=['lecturer', 'professor', 'hod', 'staff'],
        is_active=True
    ).order_by('first_name', 'last_name')
    
    context = {
        'form': form,
        'faculties': faculties,
        'potential_hods': potential_hods,
        'action': 'Create',
    }
    
    return render(request, 'departments/department_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def department_update(request, code):
    """Update department via AJAX"""
    department = get_object_or_404(Department, code=code)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            
            # AJAX response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Department "{department.name}" updated successfully!',
                    'department': {
                        'id': department.id,
                        'name': department.name,
                        'code': department.code,
                        'faculty_name': department.faculty.name,
                        'head_of_department': department.head_of_department.get_full_name() if department.head_of_department else 'Not assigned',
                        'is_active': department.is_active,
                    }
                })
            
            messages.success(request, f'Department "{department.name}" updated successfully!')
            return redirect('department_list')
        else:
            # AJAX error response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = DepartmentForm(instance=department)
    
    # Get faculties for dropdown
    faculties = Faculty.objects.filter(is_active=True).order_by('name')
    
    # Get potential HODs
    potential_hods = User.objects.filter(
        user_type__in=['lecturer', 'professor', 'hod', 'staff'],
        is_active=True
    ).order_by('first_name', 'last_name')
    
    context = {
        'form': form,
        'department': department,
        'faculties': faculties,
        'potential_hods': potential_hods,
        'action': 'Update',
    }
    
    return render(request, 'departments/department_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["DELETE", "POST"])
def department_delete(request, code):
    """Delete department via AJAX"""
    department = get_object_or_404(Department, code=code)
    
    try:
        department_name = department.name
        department.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Department "{department_name}" deleted successfully!'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting department: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
def department_export(request):
    """Export departments to CSV"""
    
    # Get filter parameters (same as list view)
    search_query = request.GET.get('search', '').strip()
    faculty_filter = request.GET.get('faculty', '')
    status_filter = request.GET.get('status', '')
    
    # Apply same filters as list view
    departments = Department.objects.select_related('faculty', 'head_of_department')
    
    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(faculty__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if faculty_filter:
        departments = departments.filter(faculty_id=faculty_filter)
    
    if status_filter:
        if status_filter == 'active':
            departments = departments.filter(is_active=True)
        elif status_filter == 'inactive':
            departments = departments.filter(is_active=False)
    
    departments = departments.order_by('faculty__name', 'name')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="departments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Department Code',
        'Department Name',
        'Faculty',
        'Head of Department',
        'HOD Email',
        'HOD Phone',
        'Description',
        'Established Date',
        'Status',
        'Created Date',
    ])
    
    # Write data
    for dept in departments:
        writer.writerow([
            dept.code,
            dept.name,
            dept.faculty.name,
            dept.head_of_department.get_full_name() if dept.head_of_department else '',
            dept.head_of_department.email if dept.head_of_department else '',
            dept.head_of_department.phone if dept.head_of_department else '',
            dept.description,
            dept.established_date.strftime('%Y-%m-%d') if dept.established_date else '',
            'Active' if dept.is_active else 'Inactive',
            dept.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(dept, 'created_at') else '',
        ])
    
    return response


@login_required
def get_department_programmes(request, department_id):
    """Get programmes for a specific department (AJAX endpoint)"""
    try:
        department = get_object_or_404(Department, id=department_id)
        programmes = department.programmes.filter(is_active=True).values('id', 'name', 'code')
        
        return JsonResponse({
            'success': True,
            'programmes': list(programmes)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.core.files.storage import default_storage
import json
from .models import Staff, User, Department, Faculty

@login_required
def staff_list_view(request):
    """Main staff list page"""
    # Get filter choices for the template
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    # Get staff statistics
    total_staff = Staff.objects.count()
    active_staff = Staff.objects.filter(is_active=True).count()
    inactive_staff = Staff.objects.filter(is_active=False).count()
    
    context = {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
        'departments': departments,
    }
    
    return render(request, 'staff/staff_list.html', context)

@login_required
def staff_ajax_list(request):
    """AJAX endpoint for staff data"""
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        department_id = request.GET.get('department', '')
        category = request.GET.get('category', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
        # Base queryset
        staff_list = Staff.objects.select_related(
            'user', 'department'
        ).all()
        
        # Apply filters
        if search:
            staff_list = staff_list.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_number__icontains=search) |
                Q(designation__icontains=search)
            )
        
        if status:
            is_active = status == 'active'
            staff_list = staff_list.filter(is_active=is_active)
        
        if department_id:
            staff_list = staff_list.filter(department_id=department_id)
        
        if category:
            staff_list = staff_list.filter(staff_category=category)
        
        # Order by name
        staff_list = staff_list.order_by('user__first_name', 'user__last_name')
        
        # Pagination
        paginator = Paginator(staff_list, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        staff_data = []
        for staff in page_obj:
            profile_picture_url = ''
            if staff.user.profile_picture:
                try:
                    profile_picture_url = staff.user.profile_picture.url
                except:
                    profile_picture_url = ''
            
            staff_data.append({
                'id': staff.id,
                'employee_number': staff.employee_number,
                'first_name': staff.user.first_name,
                'last_name': staff.user.last_name,
                'full_name': staff.user.get_full_name(),
                'email': staff.user.email or 'No email',
                'designation': staff.designation,
                'staff_category': staff.get_staff_category_display(),
                'staff_category_code': staff.staff_category,
                'department': staff.department.name if staff.department else 'No Department',
                'department_id': staff.department.id if staff.department else None,
                'joining_date': staff.joining_date.strftime('%b %d, %Y'),
                'is_active': staff.is_active,
                'status_display': 'Active' if staff.is_active else 'Inactive',
                'profile_picture': profile_picture_url,
                'phone': staff.user.phone or '',
                'address': staff.user.address or '',
                'gender': staff.user.gender or '',
                'date_of_birth': staff.user.date_of_birth.strftime('%Y-%m-%d') if staff.user.date_of_birth else '',
                'national_id': staff.user.national_id or '',
                'office_location': staff.office_location or '',
                'job_description': staff.job_description or '',
            })
        
        return JsonResponse({
            'success': True,
            'data': staff_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                'total_items': paginator.count,
                'start_index': page_obj.start_index(),
                'end_index': page_obj.end_index(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching staff data: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def staff_create_ajax(request):
    """AJAX endpoint for creating staff"""
    try:
        # Create user first
        user_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'username': request.POST.get('email'),  # Use email as username
            'user_type': 'staff',
            'phone': request.POST.get('phone', ''),
            'address': request.POST.get('address', ''),
            'gender': request.POST.get('gender', ''),
            'national_id': request.POST.get('national_id', ''),
        }
        
        # Handle date of birth
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            user_data['date_of_birth'] = date_of_birth
        
        # Create user
        user = User.objects.create_user(
            username=user_data['email'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            user_type=user_data['user_type'],
            phone=user_data['phone'],
            address=user_data['address'],
            gender=user_data['gender'],
            national_id=user_data['national_id'] if user_data['national_id'] else None,
        )
        
        if date_of_birth:
            user.date_of_birth = date_of_birth
            user.save()
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
            user.save()
        
        # Create staff profile
        staff_data = {
            'employee_number': request.POST.get('employee_number'),
            'staff_category': request.POST.get('staff_category'),
            'designation': request.POST.get('designation'),
            'joining_date': request.POST.get('joining_date'),
            'office_location': request.POST.get('office_location', ''),
            'job_description': request.POST.get('job_description', ''),
        }
        
        # Handle department
        department_id = request.POST.get('department')
        if department_id:
            staff_data['department_id'] = department_id
        
        # Handle salary
        salary = request.POST.get('salary')
        if salary:
            staff_data['salary'] = salary
        
        staff = Staff.objects.create(
            user=user,
            **staff_data
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Staff member created successfully!',
            'staff_id': staff.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating staff: {str(e)}'
        }, status=500)

@login_required
def staff_detail_ajax(request, staff_id):
    """AJAX endpoint for staff details"""
    try:
        staff = get_object_or_404(Staff, id=staff_id)
        
        profile_picture_url = ''
        if staff.user.profile_picture:
            try:
                profile_picture_url = staff.user.profile_picture.url
            except:
                profile_picture_url = ''
        
        data = {
            'id': staff.id,
            'employee_number': staff.employee_number,
            'first_name': staff.user.first_name,
            'last_name': staff.user.last_name,
            'email': staff.user.email,
            'phone': staff.user.phone or '',
            'address': staff.user.address or '',
            'gender': staff.user.gender or '',
            'date_of_birth': staff.user.date_of_birth.strftime('%Y-%m-%d') if staff.user.date_of_birth else '',
            'national_id': staff.user.national_id or '',
            'profile_picture': profile_picture_url,
            'staff_category': staff.staff_category,
            'staff_category_display': staff.get_staff_category_display(),
            'department_id': staff.department.id if staff.department else '',
            'department_name': staff.department.name if staff.department else '',
            'designation': staff.designation,
            'joining_date': staff.joining_date.strftime('%Y-%m-%d'),
            'office_location': staff.office_location or '',
            'job_description': staff.job_description or '',
            'salary': str(staff.salary) if staff.salary else '',
            'is_active': staff.is_active,
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching staff details: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def staff_update_ajax(request, staff_id):
    """AJAX endpoint for updating staff"""
    try:
        staff = get_object_or_404(Staff, id=staff_id)
        user = staff.user
        
        # Update user data
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.gender = request.POST.get('gender', user.gender)
        
        # Handle national ID
        national_id = request.POST.get('national_id')
        if national_id:
            user.national_id = national_id
        
        # Handle date of birth
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            user.date_of_birth = date_of_birth
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Update staff data
        staff.employee_number = request.POST.get('employee_number', staff.employee_number)
        staff.staff_category = request.POST.get('staff_category', staff.staff_category)
        staff.designation = request.POST.get('designation', staff.designation)
        staff.joining_date = request.POST.get('joining_date', staff.joining_date)
        staff.office_location = request.POST.get('office_location', staff.office_location)
        staff.job_description = request.POST.get('job_description', staff.job_description)
        
        # Handle department
        department_id = request.POST.get('department')
        if department_id:
            staff.department_id = department_id
        else:
            staff.department = None
        
        # Handle salary
        salary = request.POST.get('salary')
        if salary:
            staff.salary = salary
        
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Staff updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating staff: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def staff_delete_ajax(request, staff_id):
    """AJAX endpoint for deleting staff"""
    try:
        staff = get_object_or_404(Staff, id=staff_id)
        user = staff.user
        
        # Delete staff and user
        staff.delete()
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Staff deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting staff: {str(e)}'
        }, status=500)

@login_required
def departments_ajax(request):
    """AJAX endpoint for departments list"""
    try:
        departments = Department.objects.filter(is_active=True).values('id', 'name').order_by('name')
        return JsonResponse({
            'success': True,
            'data': list(departments)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching departments: {str(e)}'
        }, status=500)



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from collections import defaultdict
import json

from .models import (
    Student, StudentReporting, AcademicYear, Semester, 
    Programme, Faculty, Department, User
)


def is_admin_or_staff(user):
    """Check if user is admin, registrar, dean, hod, or staff"""
    return user.is_authenticated and user.user_type in [
        'admin', 'registrar', 'dean', 'hod', 'staff'
    ]


@login_required
@user_passes_test(is_admin_or_staff)
def student_reporting_list(request):
    """List all students with their reporting status"""
    
    # Get filter parameters
    programme_id = request.GET.get('programme')
    faculty_id = request.GET.get('faculty')
    year = request.GET.get('year')
    status = request.GET.get('status')
    search = request.GET.get('search', '').strip()
    
    # Base queryset
    students = Student.objects.select_related(
        'user', 'programme', 'programme__department', 'programme__faculty'
    ).prefetch_related(
        Prefetch(
            'studentreporting_set',
            queryset=StudentReporting.objects.select_related('semester__academic_year')
        )
    )
    
    # Apply filters
    if programme_id:
        students = students.filter(programme_id=programme_id)
    
    if faculty_id:
        students = students.filter(programme__faculty_id=faculty_id)
    
    if year:
        students = students.filter(current_year=year)
    
    if status:
        students = students.filter(status=status)
    
    if search:
        students = students.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(student_id__icontains=search)
        )
    
    # Get current semester for reporting status
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Annotate with reporting counts
    students = students.annotate(
        total_reports=Count('studentreporting'),
        pending_reports=Count(
            'studentreporting',
            filter=Q(studentreporting__status='pending')
        )
    )
    
    # Calculate reporting statistics for each student
    students_data = []
    for student in students:
        # Get current semester reporting status
        current_report = None
        if current_semester:
            current_report = student.studentreporting_set.filter(
                semester=current_semester
            ).first()
        
        # Calculate total semesters the student should have reported for
        total_semesters = 0
        if student.admission_date:
            # Simple calculation - this can be made more sophisticated
            years_enrolled = student.current_year
            total_semesters = years_enrolled * student.programme.semesters_per_year
        
        students_data.append({
            'student': student,
            'current_report': current_report,
            'total_semesters': total_semesters,
            'reporting_percentage': (
                (student.total_reports / total_semesters * 100) 
                if total_semesters > 0 else 0
            ),
        })
    
    # Pagination
    paginator = Paginator(students_data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    programmes = Programme.objects.filter(is_active=True).select_related('department', 'faculty')
    faculties = Faculty.objects.filter(is_active=True)
    
    # Statistics
    stats = {
        'total_students': students.count(),
        'reported_current': StudentReporting.objects.filter(
            semester=current_semester,
            status='approved'
        ).count() if current_semester else 0,
        'pending_reports': StudentReporting.objects.filter(
            semester=current_semester,
            status='pending'
        ).count() if current_semester else 0,
        'active_students': students.filter(status='active').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'programmes': programmes,
        'faculties': faculties,
        'current_semester': current_semester,
        'stats': stats,
        'filters': {
            'programme_id': programme_id,
            'faculty_id': faculty_id,
            'year': year,
            'status': status,
            'search': search,
        },
        'year_choices': range(1, 9),
        'status_choices': Student.STATUS_CHOICES,
    }
    
    return render(request, 'admin/student_reporting_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def student_reporting_detail(request, student_id):
    """Detailed view of a student's reporting history"""
    
    student = get_object_or_404(
        Student.objects.select_related(
            'user', 'programme', 'programme__department', 'programme__faculty'
        ),
        id=student_id
    )
    
    # Get all student reports with semester and academic year info
    reports = StudentReporting.objects.filter(
        student=student
    ).select_related(
        'semester__academic_year', 'processed_by'
    ).order_by('-semester__academic_year__start_date', '-semester__semester_number')
    
    # Get all academic years and semesters for this student's tenure
    academic_years = AcademicYear.objects.filter(
        start_date__gte=student.admission_date
    ).prefetch_related('semesters').order_by('start_date')
    
    # Organize reports by academic year and semester
    reports_by_year = defaultdict(lambda: defaultdict(dict))
    for report in reports:
        year_key = report.semester.academic_year.year
        sem_key = report.semester.semester_number
        reports_by_year[year_key][sem_key] = report
    
    # Create complete structure including missing semesters
    years_structure = []
    for academic_year in academic_years:
        year_data = {
            'academic_year': academic_year,
            'semesters': []
        }
        
        for semester in academic_year.semesters.all():
            # Check if student should have been enrolled in this semester
            semester_data = {
                'semester': semester,
                'report': reports_by_year[academic_year.year].get(
                    semester.semester_number
                ),
                'should_report': True,  # Logic to determine if student should report
            }
            year_data['semesters'].append(semester_data)
        
        if year_data['semesters']:  # Only add years with semesters
            years_structure.append(year_data)
    
    # Calculate statistics
    total_semesters = sum(len(year['semesters']) for year in years_structure)
    reported_semesters = len(reports)
    pending_reports = reports.filter(status='pending').count()
    approved_reports = reports.filter(status='approved').count()
    rejected_reports = reports.filter(status='rejected').count()
    
    stats = {
        'total_semesters': total_semesters,
        'reported_semesters': reported_semesters,
        'pending_reports': pending_reports,
        'approved_reports': approved_reports,
        'rejected_reports': rejected_reports,
        'reporting_percentage': (
            (reported_semesters / total_semesters * 100) 
            if total_semesters > 0 else 0
        ),
    }
    
    context = {
        'student': student,
        'years_structure': years_structure,
        'reports': reports,
        'stats': stats,
        'current_semester': Semester.objects.filter(is_current=True).first(),
    }
    
    return render(request, 'admin/student_reporting_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def process_student_report(request):
    """AJAX endpoint to approve/reject student reports"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        action = data.get('action')  # 'approve' or 'reject'
        remarks = data.get('remarks', '')
        
        if not report_id or action not in ['approve', 'reject']:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid parameters'
            })
        
        report = get_object_or_404(StudentReporting, id=report_id)
        
        # Update report status
        if action == 'approve':
            report.status = 'approved'
            message = f'Report for {report.student.student_id} approved successfully'
        else:
            report.status = 'rejected'
            message = f'Report for {report.student.student_id} rejected'
        
        report.processed_by = request.user
        report.processed_date = timezone.now()
        if remarks:
            report.remarks = remarks
        
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'status': report.get_status_display(),
            'processed_by': report.processed_by.get_full_name(),
            'processed_date': report.processed_date.strftime('%Y-%m-%d %H:%M'),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
def bulk_approve_reports(request):
    """AJAX endpoint to bulk approve multiple reports"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        data = json.loads(request.body)
        report_ids = data.get('report_ids', [])
        
        if not report_ids:
            return JsonResponse({
                'success': False,
                'error': 'No reports selected'
            })
        
        # Update selected reports
        updated = StudentReporting.objects.filter(
            id__in=report_ids,
            status='pending'
        ).update(
            status='approved',
            processed_by=request.user,
            processed_date=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{updated} reports approved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
def export_reporting_data(request):
    """Export student reporting data as CSV"""
    
    import csv
    from django.http import HttpResponse
    
    # Get filter parameters
    programme_id = request.GET.get('programme')
    faculty_id = request.GET.get('faculty')
    
    # Build queryset
    reports = StudentReporting.objects.select_related(
        'student__user',
        'student__programme',
        'semester__academic_year'
    )
    
    if programme_id:
        reports = reports.filter(student__programme_id=programme_id)
    
    if faculty_id:
        reports = reports.filter(student__programme__faculty_id=faculty_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_reporting_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Student Name', 'Programme', 'Academic Year',
        'Semester', 'Reporting Date', 'Status', 'Processed By', 'Remarks'
    ])
    
    for report in reports:
        writer.writerow([
            report.student.student_id,
            report.student.user.get_full_name(),
            report.student.programme.name,
            report.semester.academic_year.year,
            f'Semester {report.semester.semester_number}',
            report.reporting_date.strftime('%Y-%m-%d %H:%M'),
            report.get_status_display(),
            report.processed_by.get_full_name() if report.processed_by else '',
            report.remarks or ''
        ])
    
    return response



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

from .models import (
    Hostel, Room, Bed, HostelBooking, AcademicYear, 
    Student, User, Department
)

@login_required
def admin_hostel_management(request):
    """Main hostel management dashboard"""
    # Get all hostels without conflicting annotation
    hostels = Hostel.objects.filter(is_active=True)
    
    # Get all academic years
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Overall statistics
    total_hostels = hostels.count()
    total_rooms = Room.objects.filter(is_active=True, hostel__is_active=True).count()
    
    if current_year:
        total_beds = Bed.objects.filter(
            academic_year=current_year,
            room__is_active=True,
            room__hostel__is_active=True
        ).count()
        occupied_beds = Bed.objects.filter(
            academic_year=current_year,
            is_available=False,
            room__is_active=True,
            room__hostel__is_active=True
        ).count()
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    else:
        total_beds = 0
        occupied_beds = 0
        occupancy_rate = 0
    
    # Prepare hostel data with year-specific information
    hostel_data = []
    for hostel in hostels:
        year_stats = {}
        for year in academic_years:
            # Calculate active rooms count here instead of using annotation
            rooms_count = hostel.rooms.filter(is_active=True).count()
            beds_count = Bed.objects.filter(
                room__hostel=hostel,
                academic_year=year,
                room__is_active=True
            ).count()
            occupied_count = Bed.objects.filter(
                room__hostel=hostel,
                academic_year=year,
                is_available=False,
                room__is_active=True
            ).count()
            
            year_stats[year.id] = {
                'year': year,
                'rooms_count': rooms_count,
                'beds_count': beds_count,
                'occupied_count': occupied_count,
                'available_count': beds_count - occupied_count,
                'occupancy_rate': (occupied_count / beds_count * 100) if beds_count > 0 else 0
            }
        
        hostel_data.append({
            'hostel': hostel,
            'year_stats': year_stats,
            'active_rooms_count': hostel.rooms.filter(is_active=True).count()  # Add this line
        })
    
    stats = {
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': total_beds - occupied_beds,
        'occupancy_rate': occupancy_rate
    }
    
    context = {
        'hostel_data': hostel_data,
        'academic_years': academic_years,
        'current_year': current_year,
        'stats': stats,
    }
    
    return render(request, 'admin/hostel_management.html', context)

@login_required
def hostel_detail_view(request, hostel_id):
    """Detailed view of a specific hostel"""
    hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Prepare year-wise data
    years_data = []
    for year in academic_years:
        rooms = hostel.rooms.filter(is_active=True).prefetch_related('beds')
        
        rooms_data = []
        for room in rooms:
            beds = room.beds.filter(academic_year=year)
            beds_info = []
            
            for bed in beds:
                booking = HostelBooking.objects.filter(
                    bed=bed,
                    academic_year=year,
                    booking_status__in=['approved', 'checked_in']
                ).first()
                
                beds_info.append({
                    'bed': bed,
                    'booking': booking,
                    'student': booking.student if booking else None
                })
            
            rooms_data.append({
                'room': room,
                'beds_info': beds_info,
                'total_beds': beds.count(),
                'occupied_beds': beds.filter(is_available=False).count(),
                'available_beds': beds.filter(is_available=True).count()
            })
        
        # Calculate year statistics
        total_beds_year = Bed.objects.filter(
            room__hostel=hostel,
            academic_year=year,
            room__is_active=True
        ).count()
        occupied_beds_year = Bed.objects.filter(
            room__hostel=hostel,
            academic_year=year,
            is_available=False,
            room__is_active=True
        ).count()
        
        years_data.append({
            'academic_year': year,
            'rooms_data': rooms_data,
            'stats': {
                'total_rooms': rooms.count(),
                'total_beds': total_beds_year,
                'occupied_beds': occupied_beds_year,
                'available_beds': total_beds_year - occupied_beds_year,
                'occupancy_rate': (occupied_beds_year / total_beds_year * 100) if total_beds_year > 0 else 0
            }
        })
    
    context = {
        'hostel': hostel,
        'years_data': years_data,
        'current_year': current_year,
        'academic_years': academic_years,
    }
    
    return render(request, 'admin/hostel_detail.html', context)

@login_required
@require_POST
def create_rooms_bulk(request):
    """Create rooms in bulk for a hostel"""
    try:
        data = json.loads(request.body)
        hostel_id = data.get('hostel_id')
        academic_year_id = data.get('academic_year_id')
        room_count = int(data.get('room_count', 0))
        beds_per_room = int(data.get('beds_per_room', 4))
        room_prefix = data.get('room_prefix', '').upper()
        start_number = int(data.get('start_number', 1))
        floor_number = int(data.get('floor_number', 0))
        
        if not hostel_id or not academic_year_id or room_count <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid data provided'
            })
        
        hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        
        created_rooms = []
        created_beds_count = 0
        
        with transaction.atomic():
            for i in range(room_count):
                room_number = f"{room_prefix}{start_number + i:03d}"
                
                # Check if room already exists
                if Room.objects.filter(hostel=hostel, room_number=room_number).exists():
                    continue
                
                # Create room
                room = Room.objects.create(
                    hostel=hostel,
                    room_number=room_number,
                    floor=floor_number,
                    capacity=beds_per_room,
                    description=f"Room {room_number} on floor {floor_number}"
                )
                
                # Create beds for this room
                bed_positions = ['bed_1', 'bed_2', 'bed_3', 'bed_4'][:beds_per_room]
                for bed_pos in bed_positions:
                    bed = Bed.objects.create(
                        room=room,
                        academic_year=academic_year,
                        bed_position=bed_pos,
                        is_available=True
                    )
                    created_beds_count += 1
                
                created_rooms.append(room.room_number)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {len(created_rooms)} rooms with {created_beds_count} beds',
            'created_rooms': created_rooms
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def toggle_bed_maintenance(request):
    """Toggle bed maintenance status"""
    try:
        data = json.loads(request.body)
        bed_id = data.get('bed_id')
        maintenance_status = data.get('maintenance_status', 'good')
        
        bed = get_object_or_404(Bed, id=bed_id)
        bed.maintenance_status = maintenance_status
        
        # If bed is under maintenance or out of order, make it unavailable
        if maintenance_status in ['under_maintenance', 'out_of_order']:
            bed.is_available = False
        elif maintenance_status == 'good' and not bed.bookings.filter(
            booking_status__in=['approved', 'checked_in']
        ).exists():
            bed.is_available = True
            
        bed.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Bed maintenance status updated to {bed.get_maintenance_status_display()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def checkout_student(request):
    """Check out a student from their bed"""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        checkout_remarks = data.get('remarks', '')
        
        booking = get_object_or_404(HostelBooking, id=booking_id)
        
        with transaction.atomic():
            # Update booking status
            booking.booking_status = 'checked_out'
            booking.check_out_date = timezone.now().date()
            booking.checked_out_by = request.user
            booking.remarks = checkout_remarks
            booking.save()
            
            # Make bed available
            bed = booking.bed
            bed.is_available = True
            bed.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Student {booking.student.student_id} checked out successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def search_students(request):
    """Search students for bed assignment"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'students': []})
    
    students = Student.objects.filter(
        Q(student_id__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query),
        status='active'
    ).select_related('user', 'programme').order_by('student_id')[:20]
    
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'student_id': student.student_id,
            'name': student.user.get_full_name(),
            'programme': student.programme.name,
            'year': student.current_year,
            'semester': student.current_semester
        })
    
    return JsonResponse({'students': students_data})

@login_required
@require_POST
def assign_bed_to_student(request):
    """Assign a bed to a student"""
    try:
        data = json.loads(request.body)
        bed_id = data.get('bed_id')
        student_id = data.get('student_id')
        academic_year_id = data.get('academic_year_id')
        booking_fee = float(data.get('booking_fee', 0))
        
        bed = get_object_or_404(Bed, id=bed_id)
        student = get_object_or_404(Student, id=student_id)
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        
        # Check if student already has a booking for this academic year
        existing_booking = HostelBooking.objects.filter(
            student=student,
            academic_year=academic_year,
            booking_status__in=['pending', 'approved', 'checked_in']
        ).first()
        
        if existing_booking:
            return JsonResponse({
                'success': False,
                'error': f'Student already has a booking for {academic_year.year}'
            })
        
        # Check if bed is available
        if not bed.is_available:
            return JsonResponse({
                'success': False,
                'error': 'Bed is not available'
            })
        
        with transaction.atomic():
            # Create booking
            booking = HostelBooking.objects.create(
                student=student,
                bed=bed,
                academic_year=academic_year,
                booking_status='approved',
                booking_fee=booking_fee,
                approved_by=request.user,
                approval_date=timezone.now(),
                approval_remarks=f'Direct assignment by {request.user.get_full_name()}'
            )
            
            # Update bed availability
            bed.is_available = False
            bed.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Bed assigned to {student.student_id} successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import HostelBooking, Hostel, Room, Bed, Student, AcademicYear

@login_required
def admin_hostel_bookings(request):
    """Admin hostel bookings list with search, filter and pagination"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    hostel_filter = request.GET.get('hostel', '')
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year', '')
    booking_type_filter = request.GET.get('booking_type', '')
    
    # Base queryset
    bookings = HostelBooking.objects.select_related(
        'student__user',
        'bed__room__hostel',
        'academic_year'
    ).order_by('-created_at')
    
    # Apply search filter
    if search_query:
        bookings = bookings.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(bed__room__room_number__icontains=search_query) |
            Q(bed__room__hostel__name__icontains=search_query)
        )
    
    # Apply filters
    if hostel_filter:
        bookings = bookings.filter(bed__room__hostel_id=hostel_filter)
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if year_filter:
        bookings = bookings.filter(academic_year_id=year_filter)
    
    if booking_type_filter:
        bookings = bookings.filter(booking_type=booking_type_filter)
    
    # Pagination
    paginator = Paginator(bookings, 20)  # 20 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for dropdowns
    hostels = Hostel.objects.filter(is_active=True).order_by('name')
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    # Status choices from model
    status_choices = HostelBooking.STATUS_CHOICES if hasattr(HostelBooking, 'STATUS_CHOICES') else [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    # Booking type choices
    booking_type_choices = [
        ('new', 'New Booking'),
        ('renewal', 'Renewal'),
        ('transfer', 'Transfer'),
    ]
    
    context = {
        'page_obj': page_obj,
        'hostels': hostels,
        'academic_years': academic_years,
        'status_choices': status_choices,
        'booking_type_choices': booking_type_choices,
        'search_query': search_query,
        'current_filters': {
            'hostel': hostel_filter,
            'status': status_filter,
            'year': year_filter,
            'booking_type': booking_type_filter,
        }
    }
    
    return render(request, 'admin/hostel_bookings.html', context)
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

@login_required
@require_http_methods(["GET"])
def booking_details_ajax(request, booking_id):
    """Get booking details via AJAX"""
    try:
        booking = get_object_or_404(
            HostelBooking.objects.select_related(
                'student__user',
                'bed__room__hostel',
                'academic_year'
            ),
            id=booking_id
        )
        
        data = {
            'success': True,
            'booking': {
                'id': booking.id,
                'student_name': f"{booking.student.user.first_name} {booking.student.user.last_name}",
                'student_id': booking.student.student_id,
                'student_email': booking.student.user.email,
                'student_phone': getattr(booking.student.user, 'phone', ''),
                'hostel_name': booking.bed.room.hostel.name,
                'room_number': booking.bed.room.room_number,
                'bed_number': booking.bed.bed_number,
                'academic_year': str(booking.academic_year),
                'status': booking.booking_status,  # Use booking_status from model
                'booking_type': getattr(booking, 'booking_type', 'regular'),
                'booking_date': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'check_in_date': booking.check_in_date.strftime('%Y-%m-%d') if booking.check_in_date else '',
                'check_out_date': booking.check_out_date.strftime('%Y-%m-%d') if booking.check_out_date else '',
                'amount': str(booking.booking_fee) if hasattr(booking, 'booking_fee') else '0.00',
                'payment_status': booking.payment_status,
                'notes': booking.remarks if hasattr(booking, 'remarks') else '',
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_booking_ajax(request, booking_id):
    """Update booking details via AJAX"""
    try:
        booking = get_object_or_404(HostelBooking, id=booking_id)
        
        # Parse JSON data
        data = json.loads(request.body)
        
        # Update allowed fields - use correct field names from model
        if 'status' in data:
            booking.booking_status = data['status']  # Map to booking_status
        
        if 'check_in_date' in data and data['check_in_date']:
            from datetime import datetime
            booking.check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        
        if 'check_out_date' in data and data['check_out_date']:
            from datetime import datetime
            booking.check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        
        if 'notes' in data:
            booking.remarks = data['notes']  # Map to remarks field
        
        if 'amount' in data:
            booking.booking_fee = float(data['amount'])  # Map to booking_fee
        
        if 'payment_status' in data:
            booking.payment_status = data['payment_status']
        
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def delete_booking_ajax(request, booking_id):
    """Delete booking via AJAX"""
    try:
        booking = get_object_or_404(HostelBooking, id=booking_id)
        
        # Make bed available again when booking is deleted
        if booking.bed:
            booking.bed.is_available = True
            booking.bed.save()
        
        # Hard delete
        booking.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def booking_stats_ajax(request):
    """Get booking statistics for dashboard"""
    try:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        
        if current_year:
            total_bookings = HostelBooking.objects.filter(academic_year=current_year).count()
            confirmed_bookings = HostelBooking.objects.filter(
                academic_year=current_year,
                booking_status='approved'  # Use booking_status
            ).count()
            pending_bookings = HostelBooking.objects.filter(
                academic_year=current_year,
                booking_status='pending'  # Use booking_status
            ).count()
            cancelled_bookings = HostelBooking.objects.filter(
                academic_year=current_year,
                booking_status__in=['cancelled', 'rejected']  # Use booking_status
            ).count()
        else:
            total_bookings = confirmed_bookings = pending_bookings = cancelled_bookings = 0
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_bookings': total_bookings,
                'confirmed_bookings': confirmed_bookings,
                'pending_bookings': pending_bookings,
                'cancelled_bookings': cancelled_bookings,
                'confirmation_rate': round((confirmed_bookings / total_bookings * 100), 2) if total_bookings > 0 else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def bulk_update_bookings_ajax(request):
    """Bulk update multiple bookings"""
    try:
        data = json.loads(request.body)
        booking_ids = data.get('booking_ids', [])
        action = data.get('action', '')
        
        if not booking_ids or not action:
            return JsonResponse({
                'success': False,
                'error': 'Missing booking IDs or action'
            })
        
        bookings = HostelBooking.objects.filter(id__in=booking_ids)
        
        if action == 'confirm':
            # Update beds availability and booking status
            for booking in bookings:
                booking.booking_status = 'approved'
                if booking.bed:
                    booking.bed.is_available = False
                    booking.bed.save()
                booking.save()
            message = f'{bookings.count()} bookings confirmed successfully'
            
        elif action == 'cancel':
            # Update beds availability and booking status
            for booking in bookings:
                booking.booking_status = 'cancelled'
                if booking.bed:
                    booking.bed.is_available = True
                    booking.bed.save()
                booking.save()
            message = f'{bookings.count()} bookings cancelled successfully'
            
        elif action == 'delete':
            count = bookings.count()
            # Make beds available before deleting
            for booking in bookings:
                if booking.bed:
                    booking.bed.is_available = True
                    booking.bed.save()
            bookings.delete()
            message = f'{count} bookings deleted successfully'
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action'
            })
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Prefetch
from django.utils import timezone
from django.template.loader import render_to_string
import csv
from io import StringIO
from .models import (
    Programme, AcademicYear, Semester, Student, Enrollment, 
    FeeStructure, FeePayment, LecturerCourseAssignment, Course
)

@login_required
def student_exam_programmes_list(request):
    """View to display all programmes for exam management"""
    programmes = Programme.objects.filter(is_active=True).select_related(
        'department', 'faculty'
    ).annotate(
        total_students=Count('students', distinct=True),
        active_students=Count('students', filter=Q(students__status='active'), distinct=True)
    ).order_by('faculty__name', 'name')
    
    context = {
        'programmes': programmes,
        'page_title': 'Student Exam Management - Programmes',
    }
    return render(request, 'exams/student_exam_programmes_list.html', context)

@login_required
def student_exam_programme_detail(request, programme_id):
    """Detailed view of a specific programme showing academic years and students"""
    programme = get_object_or_404(Programme, id=programme_id, is_active=True)
    
    # Get all academic years that have enrollments for this programme
    academic_years = AcademicYear.objects.filter(
        semesters__enrollments__student__programme=programme
    ).distinct().order_by('-year')
    
    # Get programme course structure to determine years and semesters
    programme_years = list(range(1, programme.duration_years + 1))
    programme_semesters = list(range(1, programme.semesters_per_year + 1))
    
    context = {
        'programme': programme,
        'academic_years': academic_years,
        'programme_years': programme_years,
        'programme_semesters': programme_semesters,
        'page_title': f'Exam Management - {programme.name}',
    }
    return render(request, 'exams/student_exam_programme_detail.html', context)

@login_required
def get_programme_year_data(request, programme_id, academic_year_id):
    """AJAX endpoint to get student data for a specific programme and academic year"""
    programme = get_object_or_404(Programme, id=programme_id)
    academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    
    # Get all semesters for this academic year
    semesters = Semester.objects.filter(academic_year=academic_year).order_by('semester_number')
    
    year_data = {}
    for year in range(1, programme.duration_years + 1):
        year_data[year] = {
            'year_number': year,
            'semesters': []
        }
        
        for semester in semesters:
            if semester.semester_number <= programme.semesters_per_year:
                # Get students for this year and semester
                students = Student.objects.filter(
                    programme=programme,
                    current_year=year,
                    status='active',
                    enrollments__semester=semester
                ).select_related('user').distinct()
                
                # Get courses for this year and semester
                courses = Course.objects.filter(
                    course_programmes__programme=programme,
                    course_programmes__year=year,
                    course_programmes__semester=semester.semester_number,
                    course_programmes__is_active=True
                ).select_related('department')
                
                semester_data = {
                    'semester': semester,
                    'student_count': students.count(),
                    'courses': []
                }
                
                for course in courses:
                    # Get lecturer assignment for this course
                    lecturer_assignment = LecturerCourseAssignment.objects.filter(
                        course=course,
                        academic_year=academic_year,
                        semester=semester,
                        is_active=True
                    ).select_related('lecturer__user').first()
                    
                    # Get enrolled students for this specific course
                    enrolled_students = students.filter(
                        enrollments__course=course,
                        enrollments__semester=semester,
                        enrollments__is_active=True
                    )
                    
                    course_data = {
                        'course': course,
                        'lecturer_assignment': lecturer_assignment,
                        'enrolled_count': enrolled_students.count(),
                        'course_id': course.id,
                        'semester_id': semester.id,
                    }
                    semester_data['courses'].append(course_data)
                
                year_data[year]['semesters'].append(semester_data)
    
    return JsonResponse({
        'year_data': year_data,
        'programme_name': programme.name,
        'academic_year': academic_year.year
    })

@login_required
def course_exam_students_list(request, programme_id, course_id, semester_id):
    """View to show all students enrolled in a specific course with exam eligibility"""
    programme = get_object_or_404(Programme, id=programme_id)
    course = get_object_or_404(Course, id=course_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Get lecturer assignment
    lecturer_assignment = LecturerCourseAssignment.objects.filter(
        course=course,
        academic_year=semester.academic_year,
        semester=semester,
        is_active=True
    ).select_related('lecturer__user').first()
    
    # Get all enrolled students for this course
    enrollments = Enrollment.objects.filter(
        course=course,
        semester=semester,
        is_active=True,
        student__programme=programme
    ).select_related(
        'student__user', 'student__programme'
    ).prefetch_related(
        'student__fee_payments'
    )
    
    # Get fee structure for the semester
    fee_structure = FeeStructure.objects.filter(
        programme=programme,
        academic_year=semester.academic_year,
        semester=semester.semester_number
    ).first()
    
    # Process student eligibility
    students_data = []
    eligible_count = 0
    ineligible_count = 0
    
    for enrollment in enrollments:
        student = enrollment.student
        
        # Calculate fee payment status
        total_paid = 0
        if fee_structure:
            payments = FeePayment.objects.filter(
                student=student,
                fee_structure=fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            total_paid = payments
            
            required_fee = fee_structure.net_fee()
            fee_balance = required_fee - total_paid
            is_eligible = fee_balance <= 0  # Eligible if no outstanding balance
        else:
            required_fee = 0
            fee_balance = 0
            is_eligible = True  # If no fee structure, assume eligible
        
        if is_eligible:
            eligible_count += 1
        else:
            ineligible_count += 1
        
        student_data = {
            'enrollment': enrollment,
            'student': student,
            'total_paid': total_paid,
            'required_fee': fee_structure.net_fee() if fee_structure else 0,
            'fee_balance': fee_balance,
            'is_eligible': is_eligible,
        }
        students_data.append(student_data)
    
    # Sort by eligibility first, then by student name
    students_data.sort(key=lambda x: (not x['is_eligible'], x['student'].user.get_full_name()))
    
    context = {
        'programme': programme,
        'course': course,
        'semester': semester,
        'lecturer_assignment': lecturer_assignment,
        'students_data': students_data,
        'fee_structure': fee_structure,
        'eligible_count': eligible_count,
        'ineligible_count': ineligible_count,
        'total_students': len(students_data),
        'page_title': f'Exam Eligibility - {course.name}',
    }
    
    return render(request, 'exams/course_exam_students_list.html', context)

@login_required
def download_eligible_students_csv(request, programme_id, course_id, semester_id):
    """Download CSV of eligible students for exams"""
    programme = get_object_or_404(Programme, id=programme_id)
    course = get_object_or_404(Course, id=course_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Get lecturer assignment
    lecturer_assignment = LecturerCourseAssignment.objects.filter(
        course=course,
        academic_year=semester.academic_year,
        semester=semester,
        is_active=True
    ).select_related('lecturer__user').first()
    
    # Get eligible students
    enrollments = Enrollment.objects.filter(
        course=course,
        semester=semester,
        is_active=True,
        student__programme=programme
    ).select_related('student__user', 'student__programme')
    
    # Get fee structure
    fee_structure = FeeStructure.objects.filter(
        programme=programme,
        academic_year=semester.academic_year,
        semester=semester.semester_number
    ).first()
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="exam_eligible_students_{course.code}_{semester.academic_year.year}_S{semester.semester_number}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID', 'Student Name', 'Programme', 'Year', 'Semester',
        'Course Code', 'Course Name', 'Lecturer', 'Phone', 'Email',
        'Required Fee', 'Amount Paid', 'Balance', 'Exam Eligible'
    ])
    
    # Write student data
    for enrollment in enrollments:
        student = enrollment.student
        
        # Calculate fee eligibility
        if fee_structure:
            payments = FeePayment.objects.filter(
                student=student,
                fee_structure=fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            required_fee = fee_structure.net_fee()
            fee_balance = required_fee - payments
            is_eligible = fee_balance <= 0
        else:
            required_fee = 0
            payments = 0
            fee_balance = 0
            is_eligible = True
        
        # Only include eligible students
        if is_eligible:
            writer.writerow([
                student.student_id,
                student.user.get_full_name(),
                student.programme.name,
                student.current_year,
                semester.semester_number,
                course.code,
                course.name,
                lecturer_assignment.lecturer.user.get_full_name() if lecturer_assignment else 'Not Assigned',
                student.user.phone or 'N/A',
                student.user.email,
                f"{required_fee:,.2f}",
                f"{payments:,.2f}",
                f"{fee_balance:,.2f}",
                'Yes' if is_eligible else 'No'
            ])
    
    return response

@login_required
def download_all_students_csv(request, programme_id, course_id, semester_id):
    """Download CSV of all students (both eligible and ineligible) for exams"""
    programme = get_object_or_404(Programme, id=programme_id)
    course = get_object_or_404(Course, id=course_id)
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Get lecturer assignment
    lecturer_assignment = LecturerCourseAssignment.objects.filter(
        course=course,
        academic_year=semester.academic_year,
        semester=semester,
        is_active=True
    ).select_related('lecturer__user').first()
    
    # Get all enrolled students
    enrollments = Enrollment.objects.filter(
        course=course,
        semester=semester,
        is_active=True,
        student__programme=programme
    ).select_related('student__user', 'student__programme')
    
    # Get fee structure
    fee_structure = FeeStructure.objects.filter(
        programme=programme,
        academic_year=semester.academic_year,
        semester=semester.semester_number
    ).first()
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="all_students_{course.code}_{semester.academic_year.year}_S{semester.semester_number}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID', 'Student Name', 'Programme', 'Year', 'Semester',
        'Course Code', 'Course Name', 'Lecturer', 'Phone', 'Email',
        'Required Fee', 'Amount Paid', 'Balance', 'Exam Eligible', 'Status'
    ])
    
    # Write student data
    for enrollment in enrollments:
        student = enrollment.student
        
        # Calculate fee eligibility
        if fee_structure:
            payments = FeePayment.objects.filter(
                student=student,
                fee_structure=fee_structure,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            required_fee = fee_structure.net_fee()
            fee_balance = required_fee - payments
            is_eligible = fee_balance <= 0
        else:
            required_fee = 0
            payments = 0
            fee_balance = 0
            is_eligible = True
        
        writer.writerow([
            student.student_id,
            student.user.get_full_name(),
            student.programme.name,
            student.current_year,
            semester.semester_number,
            course.code,
            course.name,
            lecturer_assignment.lecturer.user.get_full_name() if lecturer_assignment else 'Not Assigned',
            student.user.phone or 'N/A',
            student.user.email,
            f"{required_fee:,.2f}",
            f"{payments:,.2f}",
            f"{fee_balance:,.2f}",
            'Yes' if is_eligible else 'No',
            student.status.title()
        ])
    
    return response

@login_required
def get_academic_year_courses(request, programme_id, academic_year_id, year, semester_num):
    """AJAX endpoint to get courses for a specific year and semester"""
    programme = get_object_or_404(Programme, id=programme_id)
    academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    
    # Get semester
    semester = get_object_or_404(Semester, 
        academic_year=academic_year, 
        semester_number=semester_num
    )
    
    # Get courses for this programme, year, and semester
    courses = Course.objects.filter(
        course_programmes__programme=programme,
        course_programmes__year=year,
        course_programmes__semester=semester_num,
        course_programmes__is_active=True
    ).select_related('department').distinct()
    
    courses_data = []
    for course in courses:
        # Get lecturer assignment
        lecturer_assignment = LecturerCourseAssignment.objects.filter(
            course=course,
            academic_year=academic_year,
            semester=semester,
            is_active=True
        ).select_related('lecturer__user').first()
        
        # Get enrollment count
        enrollment_count = Enrollment.objects.filter(
            course=course,
            semester=semester,
            student__programme=programme,
            student__current_year=year,
            is_active=True
        ).count()
        
        # Calculate eligible students count
        enrollments = Enrollment.objects.filter(
            course=course,
            semester=semester,
            student__programme=programme,
            student__current_year=year,
            is_active=True
        ).select_related('student')
        
        eligible_count = 0
        fee_structure = FeeStructure.objects.filter(
            programme=programme,
            academic_year=academic_year,
            year=year,
            semester=semester_num
        ).first()
        
        if fee_structure:
            for enrollment in enrollments:
                payments = FeePayment.objects.filter(
                    student=enrollment.student,
                    fee_structure=fee_structure,
                    payment_status='completed'
                ).aggregate(total=Sum('amount_paid'))['total'] or 0
                
                fee_balance = fee_structure.net_fee() - payments
                if fee_balance <= 0:
                    eligible_count += 1
        else:
            eligible_count = enrollment_count  # If no fee structure, all are eligible
        
        course_data = {
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'credit_hours': course.credit_hours,
            'course_type': course.get_course_type_display(),
            'lecturer_name': lecturer_assignment.lecturer.user.get_full_name() if lecturer_assignment else 'Not Assigned',
            'lecturer_id': lecturer_assignment.lecturer.id if lecturer_assignment else None,
            'enrollment_count': enrollment_count,
            'eligible_count': eligible_count,
            'ineligible_count': enrollment_count - eligible_count,
        }
        courses_data.append(course_data)
    
    return JsonResponse({
        'courses': courses_data,
        'semester_id': semester.id,
        'year': year,
        'semester_number': semester_num
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg, Case, When, IntegerField
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import os

# PDF generation imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO

from .models import (
    Student, Enrollment, Grade, AcademicYear, Semester, 
    Course, Programme, Faculty, Department, User
)

def is_admin(user):
    """Check if user is admin or has administrative privileges"""
    return user.is_authenticated and (user.is_superuser or user.user_type in ['admin', 'registrar', 'dean'])

@login_required
@user_passes_test(is_admin)
def student_search(request):
    """Search for students by ID or name"""
    students = []
    search_query = ''
    
    if request.method == 'GET' and request.GET.get('q'):
        search_query = request.GET.get('q', '').strip()
        
        if search_query:
            students = Student.objects.select_related(
                'user', 'programme', 'programme__department', 'programme__faculty'
            ).filter(
                Q(student_id__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )[:20]  # Limit to 20 results
    
    context = {
        'students': students,
        'search_query': search_query,
    }
    return render(request, 'admin/student_search.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_transcript(request, student_id):
    """Display detailed student transcript"""
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get all enrollments grouped by academic year and semester
    enrollments = Enrollment.objects.filter(
        student=student
    ).select_related(
        'course', 'semester', 'semester__academic_year', 'lecturer', 'lecturer__user'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__start_date', 'semester__semester_number', 'course__name'
    )
    
    # Group enrollments by academic year and semester
    transcript_data = {}
    total_credit_hours = 0
    total_quality_points = Decimal('0.00')
    passed_units = 0
    failed_units = 0
    semester_gpas = []
    
    for enrollment in enrollments:
        year_key = enrollment.semester.academic_year.year
        semester_key = enrollment.semester.semester_number
        
        if year_key not in transcript_data:
            transcript_data[year_key] = {}
        if semester_key not in transcript_data[year_key]:
            transcript_data[year_key][semester_key] = {
                'enrollments': [],
                'semester_credits': 0,
                'semester_quality_points': Decimal('0.00'),
                'semester_gpa': Decimal('0.00')
            }
        
        # Add enrollment with grade info
        enrollment_data = {
            'enrollment': enrollment,
            'course': enrollment.course,
            'grade_obj': getattr(enrollment, 'grade', None),
            'grade': getattr(enrollment, 'grade', None).grade if hasattr(enrollment, 'grade') else 'N/A',
            'grade_points': getattr(enrollment, 'grade', None).grade_points if hasattr(enrollment, 'grade') else 0,
            'quality_points': getattr(enrollment, 'grade', None).quality_points if hasattr(enrollment, 'grade') else 0,
            'is_passed': getattr(enrollment, 'grade', None).is_passed if hasattr(enrollment, 'grade') else False,
        }
        
        transcript_data[year_key][semester_key]['enrollments'].append(enrollment_data)
        
        # Calculate semester totals
        if hasattr(enrollment, 'grade') and enrollment.grade.quality_points:
            transcript_data[year_key][semester_key]['semester_credits'] += enrollment.course.credit_hours
            transcript_data[year_key][semester_key]['semester_quality_points'] += enrollment.grade.quality_points
            
            total_credit_hours += enrollment.course.credit_hours
            total_quality_points += enrollment.grade.quality_points
            
            if enrollment.grade.is_passed:
                passed_units += 1
            else:
                failed_units += 1
    
    # Calculate semester GPAs
    for year in transcript_data:
        for semester in transcript_data[year]:
            semester_data = transcript_data[year][semester]
            if semester_data['semester_credits'] > 0:
                semester_gpa = semester_data['semester_quality_points'] / semester_data['semester_credits']
                semester_data['semester_gpa'] = semester_gpa.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                semester_gpas.append(semester_gpa)
    
    # Calculate overall GPA
    overall_gpa = Decimal('0.00')
    if total_credit_hours > 0:
        overall_gpa = (total_quality_points / total_credit_hours).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Determine class/honors based on GPA
    graduation_class = get_graduation_class(overall_gpa)
    
    # Check if student has completed programme
    programme_completed = check_programme_completion(student, total_credit_hours, passed_units)
    
    context = {
        'student': student,
        'transcript_data': transcript_data,
        'overall_gpa': overall_gpa,
        'total_credit_hours': total_credit_hours,
        'total_quality_points': total_quality_points,
        'passed_units': passed_units,
        'failed_units': failed_units,
        'total_units': passed_units + failed_units,
        'graduation_class': graduation_class,
        'programme_completed': programme_completed,
        'semester_gpas': semester_gpas,
    }
    
    return render(request, 'admin/admin_student_transcript.html', context)

import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from django.utils import timezone
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
import pdfkit
from io import BytesIO
import base64

# Import your models
from .models import (
    Student, Enrollment, AcademicYear, Semester, 
    Grade, Programme, Faculty, Department
)

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def download_transcript_pdf(request, student_id):
    """Generate and download beautiful HTML-based transcript PDF"""
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get transcript data
    enrollments = Enrollment.objects.filter(
        student=student
    ).select_related(
        'course', 'semester', 'semester__academic_year'
    ).prefetch_related('grade').order_by(
        'semester__academic_year__start_date', 'semester__semester_number', 'course__name'
    )
    
    # Calculate GPA and other metrics
    transcript_data, stats = calculate_transcript_data(enrollments, student)
    
    # Prepare context for template
    context = {
        'student': student,
        'programme': student.programme,
        'faculty': student.programme.faculty,
        'department': student.programme.department,
        'transcript_data': transcript_data,
        'stats': stats,
        'generated_date': timezone.now(),
        'university_name': 'MURANGA UNIVERSITY OF TECHNOLOGY',
        'grading_system': get_grading_system(),
    }
    
    # Render HTML template
    html_string = render_to_string('transcripts/transcript_template.html', context)
    
    # Generate PDF from HTML
    try:
        # Configure wkhtmltopdf options
        options = {
            'page-size': 'A4',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None,
        }
        
        # Generate PDF
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)
        pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
        
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="transcript_{student.student_id}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('admin_student_transcript', student_id=student_id)

@login_required
@user_passes_test(is_admin)
def download_certificate_pdf(request, student_id):
    """Generate completion certificate for graduated students"""
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get transcript data to check completion
    enrollments = Enrollment.objects.filter(student=student).prefetch_related('grade')
    transcript_data, stats = calculate_transcript_data(enrollments,  student)
    
    if not stats['programme_completed']:
        messages.error(request, 'Certificate can only be generated for students who have completed their programme.')
        return redirect('admin_student_transcript', student_id=student_id)
    
    # Prepare context for certificate template
    context = {
        'student': student,
        'programme': student.programme,
        'faculty': student.programme.faculty,
        'department': student.programme.department,
        'stats': stats,
        'completion_date': timezone.now().date(),
        'generated_date': timezone.now(),
        'university_name': 'MURANGA UNIVERSITY OF TECHNOLOGY',
        'university_motto': 'INNOVATING FOR DEVELOPMENT',
    }
    
    # Render HTML template
    html_string = render_to_string('certificates/certificate_template.html', context)
    
    # Generate PDF from HTML
    try:
        # Configure wkhtmltopdf options for certificate (landscape might be better)
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '0.3in',
            'margin-right': '0.3in',
            'margin-bottom': '0.3in',
            'margin-left': '0.3in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None,
        }
        
        # Generate PDF
       
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)
        pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{student.student_id}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating certificate PDF: {str(e)}')
        return redirect('admin_student_transcript', student_id=student_id)

def calculate_transcript_data(enrollments, student):
    """Helper function to calculate transcript data and statistics"""
    transcript_data = {}
    total_credit_hours = 0
    total_quality_points = Decimal('0.00')
    passed_units = 0
    failed_units = 0
    
    for enrollment in enrollments:
        year_key = enrollment.semester.academic_year.year
        semester_key = enrollment.semester.semester_number
        
        if year_key not in transcript_data:
            transcript_data[year_key] = {}
        if semester_key not in transcript_data[year_key]:
            transcript_data[year_key][semester_key] = {
                'enrollments': [],
                'semester_credits': 0,
                'semester_quality_points': Decimal('0.00'),
                'semester_gpa': Decimal('0.00')
            }
        
        # Add enrollment data
        grade_obj = getattr(enrollment, 'grade', None)
        enrollment_data = {
            'enrollment': enrollment,
            'course': enrollment.course,
            'grade_obj': grade_obj,
            'grade': grade_obj.grade if grade_obj else 'N/A',
            'grade_points': grade_obj.grade_points if grade_obj else 0,
            'quality_points': grade_obj.quality_points if grade_obj else 0,
            'is_passed': grade_obj.is_passed if grade_obj else False,
        }
        
        transcript_data[year_key][semester_key]['enrollments'].append(enrollment_data)
        
        # Calculate totals
        if grade_obj and grade_obj.quality_points:
            transcript_data[year_key][semester_key]['semester_credits'] += enrollment.course.credit_hours
            transcript_data[year_key][semester_key]['semester_quality_points'] += grade_obj.quality_points
            
            total_credit_hours += enrollment.course.credit_hours
            total_quality_points += grade_obj.quality_points
            
            if grade_obj.is_passed:
                passed_units += 1
            else:
                failed_units += 1
    
    # Calculate semester GPAs
    for year in transcript_data:
        for semester in transcript_data[year]:
            semester_data = transcript_data[year][semester]
            if semester_data['semester_credits'] > 0:
                semester_gpa = semester_data['semester_quality_points'] / semester_data['semester_credits']
                semester_data['semester_gpa'] = semester_gpa.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Calculate overall GPA
    overall_gpa = Decimal('0.00')
    if total_credit_hours > 0:
        overall_gpa = (total_quality_points / total_credit_hours).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Determine graduation class and programme completion
    graduation_class = get_graduation_class(overall_gpa)
    programme_completed = check_programme_completion(student, total_credit_hours, passed_units)
    
    stats = {
        'total_credit_hours': total_credit_hours,
        'total_quality_points': total_quality_points,
        'passed_units': passed_units,
        'failed_units': failed_units,
        'overall_gpa': overall_gpa,
        'graduation_class': graduation_class,
        'programme_completed': programme_completed
    }
    
    return transcript_data, stats

def get_graduation_class(gpa):
    """Determine graduation class based on GPA"""
    gpa = float(gpa)
    if gpa >= 3.7:
        return "First Class Honors"
    elif gpa >= 3.3:
        return "Second Class Honors (Upper Division)"
    elif gpa >= 2.7:
        return "Second Class Honors (Lower Division)"
    elif gpa >= 2.0:
        return "Third Class Honors"
    elif gpa >= 1.0:
        return "Pass"
    else:
        return "Fail"

def check_programme_completion(student, total_credit_hours, passed_units):
    """Check if student has completed their programme requirements"""
    programme = student.programme
    required_credits = programme.credit_hours_required
    
    # Simple check - can be enhanced with more complex logic
    return total_credit_hours >= required_credits and passed_units > 0



def get_grading_system():
    """Return grading system for display in transcript"""
    return [
        {'grade': 'A+', 'points': '4.0', 'percentage': '90-100'},
        {'grade': 'A', 'points': '4.0', 'percentage': '80-89'},
        {'grade': 'A-', 'points': '3.7', 'percentage': '75-79'},
        {'grade': 'B+', 'points': '3.3', 'percentage': '70-74'},
        {'grade': 'B', 'points': '3.0', 'percentage': '65-69'},
        {'grade': 'B-', 'points': '2.7', 'percentage': '60-64'},
        {'grade': 'C+', 'points': '2.3', 'percentage': '55-59'},
        {'grade': 'C', 'points': '2.0', 'percentage': '50-54'},
        {'grade': 'C-', 'points': '1.7', 'percentage': '45-49'},
        {'grade': 'D+', 'points': '1.3', 'percentage': '40-44'},
        {'grade': 'D', 'points': '1.0', 'percentage': '35-39'},
        {'grade': 'F', 'points': '0.0', 'percentage': 'Below 35'},
    ]

# views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import json

def is_librarian(user):
    """Check if user is a librarian (you can customize this logic)"""
    return user.is_staff or user.groups.filter(name='Librarians').exists()

@login_required
@user_passes_test(is_librarian)
def library_book_management(request):
    """Main library book management view"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    resource_type = request.GET.get('resource_type', '')
    availability = request.GET.get('availability', '')
    
    # Build queryset with filters
    books = Library.objects.all()
    
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(call_number__icontains=search_query)
        )
    
    if resource_type:
        books = books.filter(resource_type=resource_type)
    
    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'unavailable':
        books = books.filter(available_copies=0)
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_books': Library.objects.count(),
        'available_books': Library.objects.filter(available_copies__gt=0).count(),
        'total_copies': Library.objects.aggregate(total=Sum('total_copies'))['total'] or 0,
        'borrowed_books': LibraryTransaction.objects.filter(status='active').count(),
        'overdue_books': LibraryTransaction.objects.filter(
            status='active', due_date__lt=timezone.now().date()
        ).count(),
    }
    
    context = {
        'books': page_obj,
        'stats': stats,
        'resource_types': Library.RESOURCE_TYPES,
        'search_query': search_query,
        'resource_type': resource_type,
        'availability': availability,
    }
    
    return render(request, 'library/book_management.html', context)

@login_required
@user_passes_test(is_librarian)
def library_issuance(request):
    """Library book issuance and return management"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    transaction_type = request.GET.get('transaction_type', '')
    status = request.GET.get('status', '')
    
    # Build queryset with filters
    transactions = LibraryTransaction.objects.select_related('user', 'library_resource', 'librarian')
    
    if search_query:
        transactions = transactions.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(library_resource__title__icontains=search_query) |
            Q(library_resource__call_number__icontains=search_query)
        )
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status:
        transactions = transactions.filter(status=status)
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_transactions': LibraryTransaction.objects.count(),
        'active_borrowings': LibraryTransaction.objects.filter(status='active').count(),
        'overdue_transactions': LibraryTransaction.objects.filter(
            status='active', due_date__lt=timezone.now().date()
        ).count(),
        'total_fines': LibraryTransaction.objects.aggregate(total=Sum('fine_amount'))['total'] or 0,
        'returned_books': LibraryTransaction.objects.filter(status='returned').count(),
    }
    
    # Get all users for borrowing dropdown
    users = User.objects.filter(is_active=True).order_by('username')
    available_books = Library.objects.filter(available_copies__gt=0).order_by('title')
    
    context = {
        'transactions': page_obj,
        'stats': stats,
        'transaction_types': LibraryTransaction.TRANSACTION_TYPES,
        'status_choices': LibraryTransaction.STATUS_CHOICES,
        'users': users,
        'available_books': available_books,
        'search_query': search_query,
        'transaction_type': transaction_type,
        'status': status,
    }
    
    return render(request, 'library/issuance_management.html', context)

# AJAX Views for CRUD Operations

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_librarian)
def create_book(request):
    """Create a new library book"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'author', 'call_number', 'resource_type']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field} is required'})
        
        # Check if call_number already exists
        if Library.objects.filter(call_number=data['call_number']).exists():
            return JsonResponse({'success': False, 'message': 'Call number already exists'})
        
        book = Library.objects.create(
            title=data['title'],
            author=data['author'],
            isbn=data.get('isbn', ''),
            resource_type=data['resource_type'],
            publisher=data.get('publisher', ''),
            publication_year=data.get('publication_year') or None,
            edition=data.get('edition', ''),
            total_copies=int(data.get('total_copies', 1)),
            available_copies=int(data.get('total_copies', 1)),
            location=data.get('location', ''),
            call_number=data['call_number'],
            subject_area=data.get('subject_area', ''),
            description=data.get('description', ''),
            digital_copy_url=data.get('digital_copy_url', ''),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Book created successfully',
            'book': {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'call_number': book.call_number,
                'resource_type': book.get_resource_type_display(),
                'total_copies': book.total_copies,
                'available_copies': book.available_copies,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["PUT"])
@login_required
@user_passes_test(is_librarian)
def update_book(request, book_id):
    """Update an existing book"""
    try:
        book = get_object_or_404(Library, id=book_id)
        data = json.loads(request.body)
        
        # Update fields
        book.title = data.get('title', book.title)
        book.author = data.get('author', book.author)
        book.isbn = data.get('isbn', book.isbn)
        book.resource_type = data.get('resource_type', book.resource_type)
        book.publisher = data.get('publisher', book.publisher)
        book.publication_year = data.get('publication_year') or book.publication_year
        book.edition = data.get('edition', book.edition)
        book.location = data.get('location', book.location)
        book.subject_area = data.get('subject_area', book.subject_area)
        book.description = data.get('description', book.description)
        book.digital_copy_url = data.get('digital_copy_url', book.digital_copy_url)
        
        # Handle copy count updates
        if 'total_copies' in data:
            old_total = book.total_copies
            new_total = int(data['total_copies'])
            difference = new_total - old_total
            book.total_copies = new_total
            book.available_copies = max(0, book.available_copies + difference)
        
        book.update_availability()
        book.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Book updated successfully',
            'book': {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'total_copies': book.total_copies,
                'available_copies': book.available_copies,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
@user_passes_test(is_librarian)
def delete_book(request, book_id):
    """Delete a book"""
    try:
        book = get_object_or_404(Library, id=book_id)
        
        # Check if book has active transactions
        active_transactions = LibraryTransaction.objects.filter(
            library_resource=book, status='active'
        ).exists()
        
        if active_transactions:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete book with active borrowings'
            })
        
        book_title = book.title
        book.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Book "{book_title}" deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_librarian)
def create_transaction(request):
    """Create a new library transaction (borrow/return/etc)"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['user_id', 'library_resource_id', 'transaction_type', 'due_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field} is required'})
        
        user = get_object_or_404(User, id=data['user_id'])
        library_resource = get_object_or_404(Library, id=data['library_resource_id'])
        
        # Check availability for borrowing
        if data['transaction_type'] == 'borrow':
            if library_resource.available_copies <= 0:
                return JsonResponse({'success': False, 'message': 'Book not available'})
            
            # Check if user already has this book borrowed
            active_borrow = LibraryTransaction.objects.filter(
                user=user,
                library_resource=library_resource,
                transaction_type='borrow',
                status='active'
            ).exists()
            
            if active_borrow:
                return JsonResponse({
                    'success': False,
                    'message': 'User already has this book borrowed'
                })
        
        # Parse due_date
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        
        transaction = LibraryTransaction.objects.create(
            user=user,
            library_resource=library_resource,
            transaction_type=data['transaction_type'],
            due_date=due_date,
            librarian=request.user,
            remarks=data.get('remarks', '')
        )
        
        # Update book availability
        if data['transaction_type'] == 'borrow':
            library_resource.available_copies -= 1
            library_resource.update_availability()
        
        return JsonResponse({
            'success': True,
            'message': f'{data["transaction_type"].title()} transaction created successfully',
            'transaction': {
                'id': transaction.id,
                'user': user.get_full_name() or user.username,
                'book': library_resource.title,
                'transaction_type': transaction.get_transaction_type_display(),
                'due_date': transaction.due_date.strftime('%Y-%m-%d'),
                'status': transaction.get_status_display(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["PUT"])
@login_required
@user_passes_test(is_librarian)
def return_book(request, transaction_id):
    """Process book return"""
    try:
        transaction = get_object_or_404(LibraryTransaction, id=transaction_id)
        data = json.loads(request.body)
        
        if transaction.status != 'active':
            return JsonResponse({'success': False, 'message': 'Transaction is not active'})
        
        # Update transaction
        transaction.status = 'returned'
        transaction.return_date = timezone.now().date()
        transaction.remarks = data.get('remarks', transaction.remarks)
        
        # Calculate and update fine
        if transaction.is_overdue():
            fine_amount = transaction.calculate_fine()
            transaction.fine_amount = fine_amount
            transaction.status = 'returned' if fine_amount == 0 else 'returned'
        
        transaction.save()
        
        # Update book availability
        library_resource = transaction.library_resource
        library_resource.available_copies += 1
        library_resource.update_availability()
        
        return JsonResponse({
            'success': True,
            'message': 'Book returned successfully',
            'fine_amount': float(transaction.fine_amount),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
@login_required
@user_passes_test(is_librarian)
def get_book_details(request, book_id):
    """Get detailed information about a book"""
    try:
        book = get_object_or_404(Library, id=book_id)
        
        return JsonResponse({
            'success': True,
            'book': {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'resource_type': book.resource_type,
                'resource_type_display': book.get_resource_type_display(),
                'publisher': book.publisher,
                'publication_year': book.publication_year,
                'edition': book.edition,
                'total_copies': book.total_copies,
                'available_copies': book.available_copies,
                'location': book.location,
                'call_number': book.call_number,
                'subject_area': book.subject_area,
                'description': book.description,
                'digital_copy_url': book.digital_copy_url,
                'is_available': book.is_available,
                'added_date': book.added_date.strftime('%Y-%m-%d'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
@login_required
@user_passes_test(is_librarian)
def get_transaction_details(request, transaction_id):
    """Get detailed information about a transaction"""
    try:
        transaction = get_object_or_404(LibraryTransaction, id=transaction_id)
        
        return JsonResponse({
            'success': True,
            'transaction': {
                'id': transaction.id,
                'user_id': transaction.user.id,
                'user_name': transaction.user.get_full_name() or transaction.user.username,
                'user_email': transaction.user.email,
                'library_resource_id': transaction.library_resource.id,
                'book_title': transaction.library_resource.title,
                'call_number': transaction.library_resource.call_number,
                'transaction_type': transaction.transaction_type,
                'transaction_type_display': transaction.get_transaction_type_display(),
                'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d %H:%M'),
                'due_date': transaction.due_date.strftime('%Y-%m-%d'),
                'return_date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else None,
                'status': transaction.status,
                'status_display': transaction.get_status_display(),
                'fine_amount': float(transaction.fine_amount),
                'is_overdue': transaction.is_overdue(),
                'librarian': transaction.librarian.get_full_name() if transaction.librarian else None,
                'remarks': transaction.remarks,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Event
import json

@login_required
def event_list(request):
    """Event list view"""
    events = Event.objects.all().order_by('-start_date')
    
    # Filter by event type if provided
    event_type = request.GET.get('event_type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Calculate counts
    upcoming_count = events.filter(start_date__gte=timezone.now()).count()
    past_count = events.filter(start_date__lt=timezone.now()).count()
    my_events_count = events.filter(organizer=request.user).count()
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'events': page_obj,
        'event_types': Event.EVENT_TYPES,
        'selected_event_type': event_type,
        'upcoming_count': upcoming_count,
        'past_count': past_count,
        'my_events_count': my_events_count,
    }
    return render(request, 'events/event_list.html', context)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_event(request):
    """Create event via AJAX"""
    try:
        data = json.loads(request.body)
        
        event = Event(
            title=data['title'],
            description=data['description'],
            event_type=data['event_type'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            venue=data['venue'],
            organizer=request.user,
            is_public=data.get('is_public', True),
            max_participants=data.get('max_participants'),
            registration_required=data.get('registration_required', False)
        )
        event.save()
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'event_type': event.get_event_type_display(),
                'start_date': event.start_date.strftime('%Y-%m-%d %H:%M'),
                'end_date': event.end_date.strftime('%Y-%m-%d %H:%M'),
                'venue': event.venue,
                'organizer': event.organizer.get_full_name(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_event(request, event_id):
    """Update event via AJAX"""
    try:
        event = get_object_or_404(Event, id=event_id)
        
        # Check if user is the organizer
        if event.organizer != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        data = json.loads(request.body)
        
        event.title = data['title']
        event.description = data['description']
        event.event_type = data['event_type']
        event.start_date = data['start_date']
        event.end_date = data['end_date']
        event.venue = data['venue']
        event.is_public = data.get('is_public', True)
        event.max_participants = data.get('max_participants')
        event.registration_required = data.get('registration_required', False)
        
        event.save()
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'event_type': event.get_event_type_display(),
                'start_date': event.start_date.strftime('%Y-%m-%d %H:%M'),
                'end_date': event.end_date.strftime('%Y-%m-%d %H:%M'),
                'venue': event.venue,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_event(request, event_id):
    """Delete event via AJAX"""
    try:
        event = get_object_or_404(Event, id=event_id)
        
        # Check if user is the organizer
        if event.organizer != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        event.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_event_details(request, event_id):
    """Get event details for editing"""
    try:
        event = get_object_or_404(Event, id=event_id)
        
        # Check if user is the organizer
        if event.organizer != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'event_type': event.event_type,
                'start_date': event.start_date.strftime('%Y-%m-%dT%H:%M'),
                'end_date': event.end_date.strftime('%Y-%m-%dT%H:%M'),
                'venue': event.venue,
                'is_public': event.is_public,
                'max_participants': event.max_participants,
                'registration_required': event.registration_required,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.forms.models import model_to_dict
import json

from .models import StudentClub, ClubMembership, ClubEvent
from .forms import StudentClubForm, ClubEventForm


@login_required
def clubs_management(request):
    """Main clubs management view"""
    clubs = StudentClub.objects.annotate(
        members_count=Count('members', filter=Q(members__is_active=True)),
        events_count=Count('events')
    ).select_related('chairperson').order_by('-created_at')
    
    # Filtering
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        clubs = clubs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        clubs = clubs.filter(category=category_filter)
    
    if status_filter:
        clubs = clubs.filter(is_active=(status_filter == 'active'))
    
    # Pagination
    paginator = Paginator(clubs, 12)
    page = request.GET.get('page')
    clubs_page = paginator.get_page(page)
    
    # Statistics
    stats = {
        'total_clubs': StudentClub.objects.count(),
        'active_clubs': StudentClub.objects.filter(is_active=True).count(),
        'total_members': ClubMembership.objects.filter(is_active=True).count(),
        'categories_count': StudentClub.objects.values('category').distinct().count(),
    }
    
    context = {
        'clubs': clubs_page,
        'stats': stats,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': StudentClub.CATEGORY_CHOICES,
    }
    
    return render(request, 'clubs/clubs_management.html', context)


@login_required
@require_http_methods(["POST"])
def create_club(request):
    """AJAX endpoint to create a new club"""
    try:
        form = StudentClubForm(request.POST, request.FILES)
        if form.is_valid():
            club = form.save()
            
            # Create membership for chairperson if specified
            if club.chairperson:
                ClubMembership.objects.get_or_create(
                    student=club.chairperson,
                    club=club,
                    defaults={
                        'is_executive': True,
                        'position': 'Chairperson'
                    }
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Club created successfully!',
                'club': {
                    'id': club.id,
                    'name': club.name,
                    'category': club.get_category_display(),
                    'description': club.description,
                    'chairperson': club.chairperson.get_full_name() if club.chairperson else 'Not assigned',
                    'contact_phone': club.contact_phone,
                    'email': club.email,
                    'membership_fee': str(club.membership_fee),
                    'is_active': club.is_active,
                    'created_at': club.created_at.strftime('%B %d, %Y'),
                    'members_count': 0,
                    'events_count': 0,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating club: {str(e)}'
        })


@login_required
def get_club(request, club_id):
    """AJAX endpoint to get club details"""
    try:
        club = get_object_or_404(StudentClub, id=club_id)
        members_count = club.members.filter(is_active=True).count()
        events_count = club.events.count()
        
        data = {
            'id': club.id,
            'name': club.name,
            'category': club.category,
            'description': club.description,
            'chairperson_id': club.chairperson.id if club.chairperson else None,
            'chairperson_name': club.chairperson.get_full_name() if club.chairperson else 'Not assigned',
            'contact_phone': club.contact_phone,
            'email': club.email,
            'meeting_schedule': club.meeting_schedule,
            'membership_fee': str(club.membership_fee),
            'is_active': club.is_active,
            'created_at': club.created_at.strftime('%B %d, %Y'),
            'members_count': members_count,
            'events_count': events_count,
            'logo_url': club.logo.url if club.logo else None,
        }
        
        return JsonResponse({'success': True, 'club': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_club(request, club_id):
    """AJAX endpoint to update club"""
    try:
        club = get_object_or_404(StudentClub, id=club_id)
        form = StudentClubForm(request.POST, request.FILES, instance=club)
        
        if form.is_valid():
            updated_club = form.save()
            
            # Update chairperson membership
            if updated_club.chairperson:
                membership, created = ClubMembership.objects.get_or_create(
                    student=updated_club.chairperson,
                    club=updated_club,
                    defaults={
                        'is_executive': True,
                        'position': 'Chairperson'
                    }
                )
                if not created:
                    membership.is_executive = True
                    membership.position = 'Chairperson'
                    membership.is_active = True
                    membership.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Club updated successfully!',
                'club': {
                    'id': updated_club.id,
                    'name': updated_club.name,
                    'category': updated_club.get_category_display(),
                    'description': updated_club.description,
                    'chairperson': updated_club.chairperson.get_full_name() if updated_club.chairperson else 'Not assigned',
                    'contact_phone': updated_club.contact_phone,
                    'email': updated_club.email,
                    'membership_fee': str(updated_club.membership_fee),
                    'is_active': updated_club.is_active,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating club: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def delete_club(request, club_id):
    """AJAX endpoint to delete club"""
    try:
        club = get_object_or_404(StudentClub, id=club_id)
        club_name = club.name
        club.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Club "{club_name}" deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting club: {str(e)}'
        })


@login_required
def club_events_management(request):
    """Main club events management view"""
    events = ClubEvent.objects.select_related('club', 'organizer').order_by('-start_datetime')
    
    # Filtering
    search_query = request.GET.get('search', '')
    club_filter = request.GET.get('club', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if club_filter:
        events = events.filter(club_id=club_filter)
    
    if status_filter:
        events = events.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(events, 12)
    page = request.GET.get('page')
    events_page = paginator.get_page(page)
    
    # Statistics
    now = timezone.now()
    stats = {
        'total_events': ClubEvent.objects.count(),
        'upcoming_events': ClubEvent.objects.filter(start_datetime__gt=now).count(),
        'ongoing_events': ClubEvent.objects.filter(
            start_datetime__lte=now,
            end_datetime__gte=now
        ).count(),
        'completed_events': ClubEvent.objects.filter(end_datetime__lt=now).count(),
    }
    
    context = {
        'events': events_page,
        'stats': stats,
        'search_query': search_query,
        'club_filter': club_filter,
        'status_filter': status_filter,
        'clubs': StudentClub.objects.filter(is_active=True),
        'status_choices': ClubEvent.EVENT_STATUS_CHOICES,
    }
    
    return render(request, 'clubs/club_events_management.html', context)


@login_required
@require_http_methods(["POST"])
def create_club_event(request):
    """AJAX endpoint to create a new club event"""
    try:
        form = ClubEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            if not event.organizer:
                event.organizer = request.user
            event.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Event created successfully!',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'club_name': event.club.name,
                    'description': event.description,
                    'start_datetime': event.start_datetime.strftime('%B %d, %Y %I:%M %p'),
                    'end_datetime': event.end_datetime.strftime('%B %d, %Y %I:%M %p'),
                    'location': event.location,
                    'organizer': event.organizer.get_full_name() if event.organizer else 'Unknown',
                    'status': event.get_status_display(),
                    'registration_required': event.registration_required,
                    'max_participants': event.max_participants,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating event: {str(e)}'
        })


@login_required
def get_club_event(request, event_id):
    """AJAX endpoint to get club event details"""
    try:
        event = get_object_or_404(ClubEvent, id=event_id)
        
        data = {
            'id': event.id,
            'title': event.title,
            'club_id': event.club.id,
            'club_name': event.club.name,
            'description': event.description,
            'start_datetime': event.start_datetime.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': event.end_datetime.strftime('%Y-%m-%dT%H:%M'),
            'location': event.location,
            'organizer_id': event.organizer.id if event.organizer else None,
            'organizer_name': event.organizer.get_full_name() if event.organizer else 'Unknown',
            'status': event.status,
            'registration_required': event.registration_required,
            'max_participants': event.max_participants,
            'image_url': event.image.url if event.image else None,
        }
        
        return JsonResponse({'success': True, 'event': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_club_event(request, event_id):
    """AJAX endpoint to update club event"""
    try:
        event = get_object_or_404(ClubEvent, id=event_id)
        form = ClubEventForm(request.POST, request.FILES, instance=event)
        
        if form.is_valid():
            updated_event = form.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Event updated successfully!',
                'event': {
                    'id': updated_event.id,
                    'title': updated_event.title,
                    'club_name': updated_event.club.name,
                    'description': updated_event.description,
                    'start_datetime': updated_event.start_datetime.strftime('%B %d, %Y %I:%M %p'),
                    'end_datetime': updated_event.end_datetime.strftime('%B %d, %Y %I:%M %p'),
                    'location': updated_event.location,
                    'organizer': updated_event.organizer.get_full_name() if updated_event.organizer else 'Unknown',
                    'status': updated_event.get_status_display(),
                    'registration_required': updated_event.registration_required,
                    'max_participants': updated_event.max_participants,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating event: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def delete_club_event(request, event_id):
    """AJAX endpoint to delete club event"""
    try:
        event = get_object_or_404(ClubEvent, id=event_id)
        event_title = event.title
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Event "{event_title}" deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting event: {str(e)}'
        })


# views.py - Student Comments Management
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.forms.models import model_to_dict
import json
from django.db.models.functions import Concat
from .models import StudentComment, Student
from .forms import StudentCommentForm, AdminResponseForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, CharField, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.shortcuts import render
from django.db import models

def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin_or_staff)
def student_comments_management(request):
    """Main student comments management view"""
    comments = StudentComment.objects.select_related(
        'student__user', 'responded_by'
    ).annotate(
        student_name=Concat(
            'student__user__first_name',
            Value(' '),
            'student__user__last_name',
            output_field=CharField()
        )
    ).order_by('-created_at')
    
    # Filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    if search_query:
        comments = comments.filter(
            Q(comment__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(admin_response__icontains=search_query)
        )
    
    if status_filter:
        if status_filter == 'resolved':
            comments = comments.filter(is_resolved=True)
        elif status_filter == 'pending':
            comments = comments.filter(is_resolved=False)
        elif status_filter == 'responded':
            comments = comments.filter(admin_response__isnull=False)
        elif status_filter == 'unresponded':
            comments = comments.filter(admin_response__isnull=True)
    
    if date_filter:
        from datetime import datetime, timedelta
        today = timezone.now().date()
        
        if date_filter == 'today':
            comments = comments.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            comments = comments.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            comments = comments.filter(created_at__date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(comments, 15)
    page = request.GET.get('page')
    comments_page = paginator.get_page(page)
    
    # Statistics
    stats = {
        'total_comments': StudentComment.objects.count(),
        'pending_comments': StudentComment.objects.filter(is_resolved=False).count(),
        'resolved_comments': StudentComment.objects.filter(is_resolved=True).count(),
        'responded_comments': StudentComment.objects.filter(admin_response__isnull=False).count(),
        'unresponded_comments': StudentComment.objects.filter(admin_response__isnull=True).count(),
        'today_comments': StudentComment.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
    }
    
    context = {
        'comments': comments_page,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    
    return render(request, 'comments/student_comments_management.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def get_student_comment(request, comment_id):
    """AJAX endpoint to get comment details"""
    try:
        comment = get_object_or_404(StudentComment, id=comment_id)
        
        data = {
            'id': comment.id,
            'student_name': comment.student.user.get_full_name(),
            'student_id': comment.student.student_id,
            'student_email': comment.student.user.email,
            'comment': comment.comment,
            'created_at': comment.created_at.strftime('%B %d, %Y %I:%M %p'),
            'updated_at': comment.updated_at.strftime('%B %d, %Y %I:%M %p'),
            'is_resolved': comment.is_resolved,
            'admin_response': comment.admin_response,
            'responded_by': comment.responded_by.get_full_name() if comment.responded_by else None,
            'response_date': comment.updated_at.strftime('%B %d, %Y %I:%M %p') if comment.admin_response else None,
        }
        
        return JsonResponse({'success': True, 'comment': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def add_admin_response(request, comment_id):
    """AJAX endpoint to add admin response to comment"""
    try:
        comment = get_object_or_404(StudentComment, id=comment_id)
        
        admin_response = request.POST.get('admin_response', '').strip()
        is_resolved = request.POST.get('is_resolved') == 'on'
        
        if not admin_response:
            return JsonResponse({
                'success': False,
                'message': 'Admin response cannot be empty.'
            })
        
        comment.admin_response = admin_response
        comment.is_resolved = is_resolved
        comment.responded_by = request.user
        comment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Response added successfully!',
            'comment': {
                'id': comment.id,
                'admin_response': comment.admin_response,
                'is_resolved': comment.is_resolved,
                'responded_by': comment.responded_by.get_full_name(),
                'response_date': comment.updated_at.strftime('%B %d, %Y %I:%M %p'),
                'updated_at': comment.updated_at.strftime('%B %d, %Y %I:%M %p'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding response: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def update_admin_response(request, comment_id):
    """AJAX endpoint to update admin response"""
    try:
        comment = get_object_or_404(StudentComment, id=comment_id)
        
        admin_response = request.POST.get('admin_response', '').strip()
        is_resolved = request.POST.get('is_resolved') == 'on'
        
        if not admin_response:
            return JsonResponse({
                'success': False,
                'message': 'Admin response cannot be empty.'
            })
        
        comment.admin_response = admin_response
        comment.is_resolved = is_resolved
        comment.responded_by = request.user
        comment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Response updated successfully!',
            'comment': {
                'id': comment.id,
                'admin_response': comment.admin_response,
                'is_resolved': comment.is_resolved,
                'responded_by': comment.responded_by.get_full_name(),
                'response_date': comment.updated_at.strftime('%B %d, %Y %I:%M %p'),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating response: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def toggle_comment_status(request, comment_id):
    """AJAX endpoint to toggle comment resolved status"""
    try:
        comment = get_object_or_404(StudentComment, id=comment_id)
        comment.is_resolved = not comment.is_resolved
        comment.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Comment marked as {"resolved" if comment.is_resolved else "pending"}.',
            'is_resolved': comment.is_resolved
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating status: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def delete_student_comment(request, comment_id):
    """AJAX endpoint to delete comment"""
    try:
        comment = get_object_or_404(StudentComment, id=comment_id)
        student_name = comment.student.user.get_full_name()
        comment.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Comment by {student_name} deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting comment: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def bulk_action_comments(request):
    """AJAX endpoint for bulk actions on comments"""
    try:
        action = request.POST.get('action')
        comment_ids = request.POST.getlist('comment_ids')
        
        if not comment_ids:
            return JsonResponse({
                'success': False,
                'message': 'No comments selected.'
            })
        
        comments = StudentComment.objects.filter(id__in=comment_ids)
        
        if action == 'mark_resolved':
            comments.update(is_resolved=True)
            message = f'{comments.count()} comments marked as resolved.'
        elif action == 'mark_pending':
            comments.update(is_resolved=False)
            message = f'{comments.count()} comments marked as pending.'
        elif action == 'delete':
            count = comments.count()
            comments.delete()
            message = f'{count} comments deleted.'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action.'
            })
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error performing bulk action: {str(e)}'
        })


# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, CharField, Value, Count, Case, When, IntegerField
from django.db.models.functions import Concat
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import json
from datetime import datetime, timedelta

@login_required
@user_passes_test(is_admin_or_staff)
def notification_management(request):
    """Main notification management view"""
    # Get notification type from URL parameter
    notification_type = request.GET.get('type', 'student')  # 'student' or 'general'
    
    if notification_type == 'student':
        notifications = StudentNotification.objects.select_related(
            'student__user'
        ).annotate(
            student_name=Concat(
                'student__user__first_name',
                Value(' '),
                'student__user__last_name',
                output_field=CharField()
            )
        ).order_by('-created_date')
        
        # Student notification statistics
        stats = {
            'total_notifications': StudentNotification.objects.count(),
            'read_notifications': StudentNotification.objects.filter(is_read=True).count(),
            'unread_notifications': StudentNotification.objects.filter(is_read=False).count(),
            'today_notifications': StudentNotification.objects.filter(
                created_date__date=timezone.now().date()
            ).count(),
            'exam_notifications': StudentNotification.objects.filter(
                notification_type='exam_schedule'
            ).count(),
            'assignment_notifications': StudentNotification.objects.filter(
                notification_type='assignment_due'
            ).count(),
        }
        
    else:  # general notifications
        notifications = Notification.objects.select_related(
            'sender'
        ).prefetch_related('recipients').annotate(
            recipient_count=Count('recipients')
        ).order_by('-created_at')
        
        # General notification statistics
        stats = {
            'total_notifications': Notification.objects.count(),
            'active_notifications': Notification.objects.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).count(),
            'expired_notifications': Notification.objects.filter(
                expires_at__lte=timezone.now()
            ).count(),
            'today_notifications': Notification.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'high_priority': Notification.objects.filter(priority='high').count(),
            'urgent_priority': Notification.objects.filter(priority='urgent').count(),
        }
    
    # Common filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('filter_type', '')
    date_filter = request.GET.get('date', '')
    
    if search_query:
        if notification_type == 'student':
            notifications = notifications.filter(
                Q(title__icontains=search_query) |
                Q(message__icontains=search_query) |
                Q(student__user__first_name__icontains=search_query) |
                Q(student__user__last_name__icontains=search_query) |
                Q(student__student_id__icontains=search_query)
            )
        else:
            notifications = notifications.filter(
                Q(title__icontains=search_query) |
                Q(message__icontains=search_query) |
                Q(sender__first_name__icontains=search_query) |
                Q(sender__last_name__icontains=search_query)
            )
    
    if status_filter:
        if notification_type == 'student':
            if status_filter == 'read':
                notifications = notifications.filter(is_read=True)
            elif status_filter == 'unread':
                notifications = notifications.filter(is_read=False)
        else:
            if status_filter == 'active':
                notifications = notifications.filter(
                    Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
                )
            elif status_filter == 'expired':
                notifications = notifications.filter(expires_at__lte=timezone.now())
    
    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)
    
    if date_filter:
        today = timezone.now().date()
        date_field = 'created_date' if notification_type == 'student' else 'created_at'
        
        if date_filter == 'today':
            notifications = notifications.filter(**{f'{date_field}__date': today})
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            notifications = notifications.filter(**{f'{date_field}__date__gte': week_ago})
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            notifications = notifications.filter(**{f'{date_field}__date__gte': month_ago})
    
    # Pagination
    paginator = Paginator(notifications, 15)
    page = request.GET.get('page')
    notifications_page = paginator.get_page(page)
    
    context = {
        'notifications': notifications_page,
        'notification_type': notification_type,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'date_filter': date_filter,
        'student_notification_types': StudentNotification.NOTIFICATION_TYPES,
        'general_notification_types': Notification.NOTIFICATION_TYPES,
        'priority_levels': Notification.PRIORITY_LEVELS,
    }
    
    return render(request, 'admin/notification_management.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def notification_detail(request, notification_id):
    """Get notification details for viewing"""
    notification_type = request.GET.get('type', 'student')
    
    try:
        if notification_type == 'student':
            notification = get_object_or_404(
                StudentNotification.objects.select_related('student__user'),
                id=notification_id
            )
            data = {
                'success': True,
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.get_notification_type_display(),
                    'student_name': notification.student.user.get_full_name(),
                    'student_id': notification.student.student_id,
                    'student_email': notification.student.user.email,
                    'is_read': notification.is_read,
                    'created_date': notification.created_date.strftime('%B %d, %Y at %H:%M'),
                    'read_date': notification.read_date.strftime('%B %d, %Y at %H:%M') if notification.read_date else None,
                    'related_url': notification.related_url,
                }
            }
        else:
            notification = get_object_or_404(
                Notification.objects.select_related('sender').prefetch_related('recipients'),
                id=notification_id
            )
            recipients = [f"{user.get_full_name()} ({user.email})" for user in notification.recipients.all()]
            
            data = {
                'success': True,
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.get_notification_type_display(),
                    'priority': notification.get_priority_display(),
                    'sender_name': notification.sender.get_full_name(),
                    'sender_email': notification.sender.email,
                    'recipients': recipients,
                    'recipient_count': notification.recipients.count(),
                    'send_email': notification.send_email,
                    'send_sms': notification.send_sms,
                    'created_at': notification.created_at.strftime('%B %d, %Y at %H:%M'),
                    'scheduled_time': notification.scheduled_time.strftime('%B %d, %Y at %H:%M') if notification.scheduled_time else None,
                    'expires_at': notification.expires_at.strftime('%B %d, %Y at %H:%M') if notification.expires_at else None,
                }
            }
            
    except Exception as e:
        data = {
            'success': False,
            'message': f'Error loading notification: {str(e)}'
        }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def create_notification(request):
    """Create a new notification"""
    try:
        notification_type = request.POST.get('notification_type')
        
        if notification_type == 'student':
            student_id = request.POST.get('student_id')
            student = get_object_or_404(Student, id=student_id)
            
            notification = StudentNotification.objects.create(
                student=student,
                title=request.POST.get('title'),
                message=request.POST.get('message'),
                notification_type=request.POST.get('type'),
                related_url=request.POST.get('related_url', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Student notification created successfully!'
            })
            
        else:  # general notification
            recipient_ids = request.POST.getlist('recipients')
            
            notification = Notification.objects.create(
                title=request.POST.get('title'),
                message=request.POST.get('message'),
                notification_type=request.POST.get('type'),
                priority=request.POST.get('priority', 'medium'),
                sender=request.user,
                send_email=request.POST.get('send_email') == 'on',
                send_sms=request.POST.get('send_sms') == 'on',
                scheduled_time=request.POST.get('scheduled_time') or None,
                expires_at=request.POST.get('expires_at') or None,
            )
            
            # Add recipients
            if recipient_ids:
                recipients = User.objects.filter(id__in=recipient_ids)
                notification.recipients.set(recipients)
            
            return JsonResponse({
                'success': True,
                'message': 'General notification created successfully!'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating notification: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """Mark student notification as read"""
    try:
        notification = get_object_or_404(StudentNotification, id=notification_id)
        notification.is_read = True
        notification.read_date = timezone.now()
        notification.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating notification: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        notification_type = request.POST.get('type', 'student')
        
        if notification_type == 'student':
            notification = get_object_or_404(StudentNotification, id=notification_id)
        else:
            notification = get_object_or_404(Notification, id=notification_id)
        
        notification.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting notification: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def bulk_action(request):
    """Handle bulk actions on notifications"""
    try:
        action = request.POST.get('action')
        notification_ids = request.POST.getlist('notification_ids')
        notification_type = request.POST.get('type', 'student')
        
        if not notification_ids:
            return JsonResponse({
                'success': False,
                'message': 'No notifications selected.'
            })
        
        if notification_type == 'student':
            notifications = StudentNotification.objects.filter(id__in=notification_ids)
            
            if action == 'mark_read':
                notifications.update(is_read=True, read_date=timezone.now())
                message = f'{len(notification_ids)} notifications marked as read.'
            elif action == 'mark_unread':
                notifications.update(is_read=False, read_date=None)
                message = f'{len(notification_ids)} notifications marked as unread.'
            elif action == 'delete':
                notifications.delete()
                message = f'{len(notification_ids)} notifications deleted.'
        else:
            notifications = Notification.objects.filter(id__in=notification_ids)
            
            if action == 'delete':
                notifications.delete()
                message = f'{len(notification_ids)} notifications deleted.'
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action for general notifications.'
                })
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error performing bulk action: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
def get_students(request):
    """Get students for notification creation"""
    try:
        search = request.GET.get('search', '')
        students = Student.objects.select_related('user').all()
        
        if search:
            students = students.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(student_id__icontains=search)
            )
        
        student_data = []
        for student in students[:20]:  # Limit to 20 results
            student_data.append({
                'id': student.id,
                'name': student.user.get_full_name(),
                'student_id': student.student_id,
                'email': student.user.email
            })
        
        return JsonResponse({
            'success': True,
            'students': student_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading students: {str(e)}'
        })


# news_views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
from datetime import datetime, timedelta
from .models import NewsArticle

def is_admin_or_staff(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin_or_staff)
def news_management(request):
    """Main news management view"""
    
    # Get all news articles with author information
    news_articles = NewsArticle.objects.select_related('author').all()
    
    # Statistics
    stats = {
        'total_articles': NewsArticle.objects.count(),
        'published_articles': NewsArticle.objects.filter(is_published=True).count(),
        'draft_articles': NewsArticle.objects.filter(is_published=False).count(),
        'today_articles': NewsArticle.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
        'academic_articles': NewsArticle.objects.filter(category='academic').count(),
        'event_articles': NewsArticle.objects.filter(category='event').count(),
    }
    
    # Filtering
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    if search_query:
        news_articles = news_articles.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query)
        )
    
    if category_filter:
        news_articles = news_articles.filter(category=category_filter)
    
    if status_filter:
        if status_filter == 'published':
            news_articles = news_articles.filter(is_published=True)
        elif status_filter == 'draft':
            news_articles = news_articles.filter(is_published=False)
    
    if date_filter:
        today = timezone.now().date()
        
        if date_filter == 'today':
            news_articles = news_articles.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            news_articles = news_articles.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            news_articles = news_articles.filter(created_at__date__gte=month_ago)
    
    # Ordering
    news_articles = news_articles.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(news_articles, 15)
    page = request.GET.get('page')
    articles_page = paginator.get_page(page)
    
    context = {
        'articles': articles_page,
        'stats': stats,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'category_choices': NewsArticle.CATEGORY_CHOICES,
    }
    
    return render(request, 'admin/news_management.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def news_detail(request, article_id):
    """Get news article details for viewing"""
    try:
        article = get_object_or_404(
            NewsArticle.objects.select_related('author'),
            id=article_id
        )
        
        data = {
            'success': True,
            'article': {
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'content': article.content,
                'category': article.get_category_display(),
                'category_key': article.category,
                'image_url': article.image.url if article.image else None,
                'author_name': article.author.get_full_name() if article.author else 'Unknown',
                'author_email': article.author.email if article.author else '',
                'publish_date': article.publish_date.strftime('%B %d, %Y at %H:%M'),
                'is_published': article.is_published,
                'created_at': article.created_at.strftime('%B %d, %Y at %H:%M'),
                'updated_at': article.updated_at.strftime('%B %d, %Y at %H:%M'),
            }
        }
            
    except Exception as e:
        data = {
            'success': False,
            'message': f'Error loading article: {str(e)}'
        }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def create_news(request):
    """Create a new news article"""
    try:
        # Handle image upload
        image = request.FILES.get('image')
        
        article = NewsArticle.objects.create(
            title=request.POST.get('title'),
            summary=request.POST.get('summary'),
            content=request.POST.get('content'),
            category=request.POST.get('category'),
            image=image,
            author=request.user,
            is_published=request.POST.get('is_published') == 'on',
            publish_date=request.POST.get('publish_date') or timezone.now(),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'News article created successfully!',
            'article_id': article.id
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating article: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def update_news(request, article_id):
    """Update an existing news article"""
    try:
        article = get_object_or_404(NewsArticle, id=article_id)
        
        # Update fields
        article.title = request.POST.get('title')
        article.summary = request.POST.get('summary')
        article.content = request.POST.get('content')
        article.category = request.POST.get('category')
        article.is_published = request.POST.get('is_published') == 'on'
        
        # Handle publish date
        publish_date = request.POST.get('publish_date')
        if publish_date:
            article.publish_date = publish_date
        
        # Handle image upload
        if request.FILES.get('image'):
            # Delete old image if exists
            if article.image:
                default_storage.delete(article.image.name)
            article.image = request.FILES.get('image')
        
        article.save()
        
        return JsonResponse({
            'success': True,
            'message': 'News article updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating article: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def delete_news(request, article_id):
    """Delete a news article"""
    try:
        article = get_object_or_404(NewsArticle, id=article_id)
        
        # Delete associated image
        if article.image:
            default_storage.delete(article.image.name)
        
        article.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'News article deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting article: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def toggle_publish_status(request, article_id):
    """Toggle publish status of a news article"""
    try:
        article = get_object_or_404(NewsArticle, id=article_id)
        article.is_published = not article.is_published
        
        # If publishing for first time, set publish date to now
        if article.is_published and not article.publish_date:
            article.publish_date = timezone.now()
        
        article.save()
        
        status = 'published' if article.is_published else 'unpublished'
        return JsonResponse({
            'success': True,
            'message': f'Article {status} successfully!',
            'is_published': article.is_published
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating publish status: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def bulk_news_action(request):
    """Handle bulk actions on news articles"""
    try:
        action = request.POST.get('action')
        article_ids = request.POST.getlist('article_ids')
        
        if not article_ids:
            return JsonResponse({
                'success': False,
                'message': 'No articles selected.'
            })
        
        articles = NewsArticle.objects.filter(id__in=article_ids)
        
        if action == 'publish':
            articles.update(is_published=True, publish_date=timezone.now())
            message = f'{len(article_ids)} articles published.'
        elif action == 'unpublish':
            articles.update(is_published=False)
            message = f'{len(article_ids)} articles unpublished.'
        elif action == 'delete':
            # Delete associated images
            for article in articles:
                if article.image:
                    default_storage.delete(article.image.name)
            articles.delete()
            message = f'{len(article_ids)} articles deleted.'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action.'
            })
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error performing bulk action: {str(e)}'
        })


@login_required
@user_passes_test(is_admin_or_staff)
def get_authors(request):
    """Get authors for news article creation/editing"""
    try:
        search = request.GET.get('search', '')
        authors = User.objects.filter(is_staff=True)
        
        if search:
            authors = authors.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        author_data = []
        for author in authors[:20]:  # Limit to 20 results
            author_data.append({
                'id': author.id,
                'name': author.get_full_name() or author.username,
                'email': author.email
            })
        
        return JsonResponse({
            'success': True,
            'authors': author_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading authors: {str(e)}'
        })
    

# analytics/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    Student, Lecturer, Faculty, Department, Programme, Course, 
    Enrollment, Grade, AcademicYear, Semester, FeePayment, 
    HostelBooking, Hostel, Assignment, AssignmentSubmission,
    Library, LibraryTransaction, Attendance, AttendanceSession
)

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Basic statistics
    context = {
        'total_students': Student.objects.filter(status='active').count(),
        'total_lecturers': Lecturer.objects.filter(is_active=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_programmes': Programme.objects.filter(is_active=True).count(),
        'total_faculties': Faculty.objects.filter(is_active=True).count(),
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
def student_enrollment_data(request):
    """API endpoint for student enrollment trends"""
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get enrollment data by programme
    programme_data = Programme.objects.annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    ).values('name', 'student_count')
    
    # Get enrollment trends over semesters
    semester_data = []
    semesters = Semester.objects.filter(
        academic_year__year__gte='2023/2024'
    ).order_by('academic_year__start_date', 'semester_number')
    
    for semester in semesters:
        enrollments = Enrollment.objects.filter(
            semester=semester,
            is_active=True
        ).count()
        semester_data.append({
            'semester': f"{semester.academic_year.year} S{semester.semester_number}",
            'enrollments': enrollments
        })
    
    # Gender distribution
    gender_data = Student.objects.filter(status='active').values('user__gender').annotate(
        count=Count('id')
    ).order_by('user__gender')
    
    return JsonResponse({
        'programme_data': list(programme_data),
        'semester_trends': semester_data,
        'gender_distribution': list(gender_data)
    })

@login_required
def academic_performance_data(request):
    """API endpoint for academic performance metrics"""
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Grade distribution
    grade_distribution = Grade.objects.filter(
        enrollment__semester=current_semester,
        grade__isnull=False
    ).values('grade').annotate(
        count=Count('id')
    ).order_by('grade')
    
    # Programme performance averages
    programme_performance = Programme.objects.annotate(
        avg_gpa=Avg('students__enrollments__grade__grade_points',
                   filter=Q(students__enrollments__semester=current_semester))
    ).values('name', 'avg_gpa')
    
    # Assignment completion rates
    assignment_completion = AssignmentSubmission.objects.filter(
        assignment__lecturer_assignment__semester=current_semester,
        is_submitted=True
    ).count()
    
    total_assignments = Assignment.objects.filter(
        lecturer_assignment__semester=current_semester,
        is_published=True
    ).count()
    
    completion_rate = (assignment_completion / total_assignments * 100) if total_assignments > 0 else 0
    
    return JsonResponse({
        'grade_distribution': list(grade_distribution),
        'programme_performance': list(programme_performance),
        'assignment_completion_rate': completion_rate,
        'total_assignments': total_assignments,
        'submitted_assignments': assignment_completion
    })

@login_required
def financial_data(request):
    """API endpoint for financial analytics"""
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Fee collection by programme
    fee_by_programme = FeePayment.objects.filter(
        fee_structure__academic_year=current_year,
        payment_status='completed'
    ).values(
        'fee_structure__programme__name'
    ).annotate(
        total_fees=Sum('amount_paid')
    ).order_by('-total_fees')
    
    # Monthly fee collection trend
    months = []
    fee_collections = []
    
    for i in range(12):
        month_date = timezone.now().replace(day=1) - timedelta(days=30*i)
        monthly_fees = FeePayment.objects.filter(
            payment_date__year=month_date.year,
            payment_date__month=month_date.month,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        months.insert(0, month_date.strftime('%b %Y'))
        fee_collections.insert(0, float(monthly_fees))
    
    # Payment method distribution
    payment_methods = FeePayment.objects.filter(
        fee_structure__academic_year=current_year,
        payment_status='completed'
    ).values('payment_method').annotate(
        count=Count('id'),
        total_amount=Sum('amount_paid')
    )
    
    return JsonResponse({
        'fee_by_programme': list(fee_by_programme),
        'monthly_trends': {
            'months': months,
            'collections': fee_collections
        },
        'payment_methods': list(payment_methods)
    })

@login_required
def hostel_occupancy_data(request):
    """API endpoint for hostel occupancy analytics"""
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Occupancy by hostel
    hostel_occupancy = []
    for hostel in Hostel.objects.filter(is_active=True):
        total_beds = hostel.get_total_beds_count(current_year)
        occupied_beds = hostel.get_occupied_beds_count(current_year)
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        
        hostel_occupancy.append({
            'hostel_name': hostel.name,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'occupancy_rate': round(occupancy_rate, 2)
        })
    
    # Gender-wise accommodation
    gender_accommodation = HostelBooking.objects.filter(
        academic_year=current_year,
        booking_status='checked_in'
    ).values(
        'student__user__gender'
    ).annotate(count=Count('id'))
    
    # Booking status distribution
    booking_status = HostelBooking.objects.filter(
        academic_year=current_year
    ).values('booking_status').annotate(count=Count('id'))
    
    return JsonResponse({
        'hostel_occupancy': hostel_occupancy,
        'gender_accommodation': list(gender_accommodation),
        'booking_status': list(booking_status)
    })

@login_required
def library_usage_data(request):
    """API endpoint for library usage analytics"""
    # Most borrowed books
    popular_books = LibraryTransaction.objects.filter(
        transaction_type='borrow',
        transaction_date__gte=timezone.now() - timedelta(days=30)
    ).values(
        'library_resource__title',
        'library_resource__author'
    ).annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')[:10]
    
    # Daily library usage trend
    daily_usage = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        transactions = LibraryTransaction.objects.filter(
            transaction_date__date=date
        ).count()
        daily_usage.insert(0, {
            'date': date.strftime('%m/%d'),
            'transactions': transactions
        })
    
    # Resource type distribution
    resource_types = Library.objects.values('resource_type').annotate(
        count=Count('id')
    )
    
    return JsonResponse({
        'popular_books': list(popular_books),
        'daily_usage': daily_usage,
        'resource_types': list(resource_types)
    })

@login_required
def attendance_analytics_data(request):
    """API endpoint for attendance analytics"""
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Course-wise attendance rates
    course_attendance = []
    courses = Course.objects.filter(
        enrollments__semester=current_semester,
        is_active=True
    ).distinct()
    
    for course in courses:
        total_sessions = AttendanceSession.objects.filter(
            timetable_slot__course=course,
            semester=current_semester
        ).count()
        
        total_possible_attendance = Enrollment.objects.filter(
            course=course,
            semester=current_semester,
            is_active=True
        ).count() * total_sessions
        
        present_count = Attendance.objects.filter(
            timetable_slot__course=course,
            attendance_session__semester=current_semester,
            status='present'
        ).count()
        
        attendance_rate = (present_count / total_possible_attendance * 100) if total_possible_attendance > 0 else 0
        
        course_attendance.append({
            'course_code': course.code,
            'course_name': course.name,
            'attendance_rate': round(attendance_rate, 2)
        })
    
    # Weekly attendance trends
    weekly_attendance = []
    for week in range(1, 13):
        week_attendance = Attendance.objects.filter(
            week_number=week,
            attendance_session__semester=current_semester,
            status='present'
        ).count()
        weekly_attendance.append({
            'week': week,
            'attendance': week_attendance
        })
    
    return JsonResponse({
        'course_attendance': course_attendance,
        'weekly_trends': weekly_attendance
    })