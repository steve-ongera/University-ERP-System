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


