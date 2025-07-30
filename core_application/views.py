from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Student, Enrollment,  Semester, Grade
from decimal import Decimal
from .models import *
def student_login(request):
    """Custom login view for students"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.user_type == 'student':
            login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not a student account')
    
    return render(request, 'student/auth/login.html')

from django.contrib.auth import logout
from django.shortcuts import redirect

def student_logout(request):
    logout(request)
    return redirect('student_login')  # This should match your login URL name


@login_required
def student_dashboard(request):
    """Main dashboard for logged-in students"""
    if request.user.user_type != 'student':
        return redirect('student_login')
    
    student = get_object_or_404(Student, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get current semester enrollments
    current_enrollments = Enrollment.objects.filter(
        student=student,
        semester=current_semester,
        is_active=True
    ).select_related('course')
    
    # Calculate semester progress
    total_semesters = student.programme.total_semesters
    completed_semesters = (student.current_year - 1) * student.programme.semesters_per_year + (student.current_semester - 1)
    progress_percentage = (completed_semesters / total_semesters) * 100 if total_semesters > 0 else 0
    
    # Calculate GPA (mock fee balance for now)
    fee_balance = Decimal('45000.00')  # This should come from a Fee model
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'current_enrollments': current_enrollments,
        'progress_percentage': round(progress_percentage, 1),
        'completed_semesters': completed_semesters,
        'total_semesters': total_semesters,
        'fee_balance': fee_balance,
    }
    
    return render(request, 'student/dashboard.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from django.http import JsonResponse
import json

@login_required
def student_profile(request):
    try:
        student = request.user.student_profile
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')  # or wherever you want to redirect
    
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


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
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
        enrolled_course_ids = Enrollment.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).values_list('course_id', flat=True)
        
        # Filter out already enrolled courses
        available_programme_courses = programme_courses.exclude(
            course_id__in=enrolled_course_ids
        )
        
        for programme_course in available_programme_courses:
            available_courses.append(programme_course.course)
    
    # Get enrollment history
    enrollments = Enrollment.objects.select_related(
        'course', 'semester', 'semester__academic_year', 'lecturer'
    ).filter(
        student=student,
        is_active=True
    ).order_by('-semester__academic_year__year', '-semester__semester_number')
    
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
            
        curriculum_data[year_key][sem_key].append(programme_course.course)
    
    # Handle POST request for course enrollment
    if request.method == 'POST':
        return handle_course_enrollment(request, student, current_semester, available_courses)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'show_registration': show_registration,
        'available_units': available_courses,  # Keep 'available_units' for template compatibility
        'enrollment_history': enrollment_history,
        'curriculum_data': curriculum_data,
    }
    
    return render(request, 'student/units.html', context)


def handle_course_enrollment(request, student, current_semester, available_courses):
    """
    Handle course enrollment logic
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
    selected_course_ids = request.POST.getlist('units')  # Keep 'units' for template compatibility
    
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
            
            for course_id in selected_course_ids:
                try:
                    course = Course.objects.get(id=course_id)
                    
                    # Check if already enrolled (double-check)
                    existing_enrollment = Enrollment.objects.filter(
                        student=student,
                        course=course,
                        semester=current_semester
                    ).first()
                    
                    if existing_enrollment:
                        if existing_enrollment.is_active:
                            failed_enrollments.append(f"{course.code} - Already enrolled")
                        else:
                            # Reactivate inactive enrollment
                            existing_enrollment.is_active = True
                            existing_enrollment.enrollment_date = timezone.now().date()
                            existing_enrollment.save()
                            enrolled_count += 1
                    else:
                        # Create new enrollment
                        enrollment = Enrollment.objects.create(
                            student=student,
                            course=course,
                            semester=current_semester,
                            enrollment_date=timezone.now().date(),
                            is_active=True
                        )
                        enrolled_count += 1
                        
                except Course.DoesNotExist:
                    failed_enrollments.append(f"Course ID {course_id} - Not found")
                except Exception as e:
                    failed_enrollments.append(f"Course ID {course_id} - {str(e)}")
            
            # Provide feedback
            if enrolled_count > 0:
                messages.success(
                    request, 
                    f'Successfully enrolled in {enrolled_count} course{"s" if enrolled_count != 1 else ""}.'
                )
            
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
    
    if request.method == 'POST':
        if not current_semester:
            messages.error(request, "No active semester found for reporting.")
            return redirect('student_dashboard')
        
        if has_reported:
            messages.error(request, f"You have already reported for {current_semester}.")
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
    }
    return render(request, 'student/student_reporting.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
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
from django.contrib.auth.models import User
from django.http import JsonResponse
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
from django.http import JsonResponse
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
from django.http import JsonResponse
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
                'theory_marks': grade.theory_marks,
                'practical_marks': grade.practical_marks,
                'clinical_marks': grade.clinical_marks,
                'continuous_assessment': grade.continuous_assessment,
                'final_exam_marks': grade.final_exam_marks,
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
