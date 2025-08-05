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
        if user is not None:
            login(request, user)
            
            # Redirect based on user_type
            if user.user_type == 'student':
                return redirect('student_dashboard')
            elif user.user_type == 'lecturer':
                return redirect('lecturer_dashboard')
            else:
                messages.error(request, 'Unauthorized user type.')
        else:
            messages.error(request, 'Invalid username or password.')
    
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
    }
    
    return render(request, 'student/student_transcript.html', context)


# Alternative view for generating transcript PDF
@login_required
def student_transcript_pdf(request, student_id=None):
    """Generate PDF version of student transcript"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # Get the same data as the regular transcript view
    if student_id:
        if not (request.user.user_type in ['admin', 'instructor', 'staff', 'registrar']):
            return HttpResponseForbidden("Access denied.")
        student = get_object_or_404(Student, id=student_id)
    else:
        if not hasattr(request.user, 'student_profile'):
            return HttpResponseForbidden("Access denied. Students only.")
        student = request.user.student_profile
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transcript_{student.registration_number}.pdf"'
    
    # Create the PDF object using BytesIO as a file-like buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#3639A4'),
        alignment=1  # Center alignment
    )
    
    # Title
    title = Paragraph("ACADEMIC TRANSCRIPT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Student Information
    student_info = [
        ['Student Name:', student.user.get_full_name()],
        ['Registration Number:', student.registration_number],
        ['Programme:', student.programme.name],
        ['School:', student.programme.school.name],
        ['Current Year/Semester:', f"{student.current_year}/{student.current_semester}"],
        ['Status:', student.get_status_display()],
    ]
    
    student_table = Table(student_info, colWidths=[2*inch, 4*inch])
    student_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(student_table)
    elements.append(Spacer(1, 20))
    
    # Add transcript data (simplified version for PDF)
    # This would need to be expanded based on your specific requirements
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
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
def get_programme_courses(request, programme_id):
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