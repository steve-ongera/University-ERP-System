from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Student, Enrollment,  Semester, Grade
from decimal import Decimal

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

