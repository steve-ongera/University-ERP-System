from django import forms
from .models import *


class StudentCommentForm(forms.ModelForm):
    class Meta:
        model = StudentComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter your comment or question here...'
            })
        }

# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, Student, Programme, Department

# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        required=False,
        help_text="Leave blank to keep current password on update."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        required=False,
        help_text="Re-enter password to confirm."
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'address', 'gender', 'date_of_birth', 
            'profile_picture', 'national_id'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_update = kwargs.pop('is_update', False)
        self.user_type = kwargs.pop('user_type', 'instructor')  # Default to instructor
        super().__init__(*args, **kwargs)

        # Password fields required only on create
        if not self.is_update:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

        # Add gender placeholder
        self.fields['gender'].choices = [('', 'Select Gender')] + list(User.GENDER_CHOICES)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = User.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            qs = User.objects.filter(username=username)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A user with this username already exists.")
        return username

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = timezone.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise ValidationError("User must be at least 16 years old.")
            if age > 80:
                raise ValidationError("Please check the date of birth.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match.")

            if not self.is_update and len(password) < 6:
                raise ValidationError("Password must be at least 6 characters.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        # Automatically set user type only on creation
        if not user.pk or not user.user_type:
            user.user_type = self.user_type

        if commit:
            user.save()
        return user



class StudentForm(forms.ModelForm):
    # Remove the duplicate course field - we'll use programme directly
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'programme', 'current_year', 'current_semester',
            'admission_date', 'admission_type', 'sponsor_type', 'status',
            'guardian_name', 'guardian_phone', 'guardian_relationship', 'guardian_address',
            'emergency_contact', 'blood_group', 'medical_conditions',
            'expected_graduation_date', 'cumulative_gpa'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter student registration number',
                'required': True
            }),
            'programme': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'current_year': forms.NumberInput(attrs={
                'class': 'form-select',
                'required': True
            }),
            'current_semester': forms.NumberInput(attrs={
                'class': 'form-select',
                'required': True
            }),
            'admission_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'admission_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sponsor_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter guardian full name',
                'required': True
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter guardian phone number',
                'required': True
            }),
            'guardian_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter relationship (e.g., Father, Mother, Guardian)',
                'required': True
            }),
            'guardian_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter guardian address'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact number',
                'required': True
            }),
            'blood_group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blood group (e.g., A+, B-, O+)'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any medical conditions or allergies (optional)'
            }),
            'expected_graduation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cumulative_gpa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '4',
                'placeholder': 'Enter GPA (0.00 - 4.00)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up programme choices
        self.fields['programme'].queryset = Programme.objects.filter(is_active=True).order_by('name')
        self.fields['programme'].empty_label = "Select Programme"
        
        # Set up year choices - dynamic based on selected programme
        # Default to max 4 years, but will be updated via JavaScript based on programme selection
        year_choices = [('', 'Select Year')]
        for i in range(1, 5):  # 1 to 4 years
            year_choices.append((i, f'Year {i}'))
        self.fields['current_year'].choices = year_choices
        
        # Set up semester choices - dynamic based on programme's semesters_per_year
        semester_choices = [('', 'Select Semester')]
        for i in range(1, 4):  # 1 to 3 semesters (covers most cases)
            semester_choices.append((i, f'Semester {i}'))
        self.fields['current_semester'].choices = semester_choices
        
        # Set up other choice fields
        self.fields['admission_type'].choices = [('', 'Select Admission Type')] + list(Student.ADMISSION_TYPES)
        self.fields['sponsor_type'].choices = [('', 'Select Sponsor Type')] + list(Student.SPONSOR_TYPES)
        self.fields['status'].choices = [('', 'Select Status')] + list(Student.STATUS_CHOICES)
        
        # Make required fields
        required_fields = ['student_id', 'programme', 'current_year', 'current_semester', 
                          'admission_date', 'guardian_name', 'guardian_phone', 'guardian_relationship', 
                          'emergency_contact']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

        # If editing existing student, limit year/semester choices to programme's constraints
        if self.instance.pk and self.instance.programme:
            programme = self.instance.programme
            
            # Update year choices based on programme duration
            year_choices = [('', 'Select Year')]
            for i in range(1, programme.duration_years + 1):
                year_choices.append((i, f'Year {i}'))
            self.fields['current_year'].choices = year_choices
            
            # Update semester choices based on programme's semesters per year
            semester_choices = [('', 'Select Semester')]
            for i in range(1, programme.semesters_per_year + 1):
                semester_choices.append((i, f'Semester {i}'))
            self.fields['current_semester'].choices = semester_choices

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            qs = Student.objects.filter(student_id=student_id)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A student with this registration number already exists.")
        return student_id

    def clean_gpa(self):
        gpa = self.cleaned_data.get('cumulative_gpa')
        if gpa is not None and (gpa < 0 or gpa > 4):
            raise ValidationError("GPA must be between 0.00 and 4.00")
        return gpa

    def clean_admission_date(self):
        admission_date = self.cleaned_data.get('admission_date')
        if admission_date:
            today = timezone.now().date()
            
            # Check if admission date is not too old (e.g., more than 10 years ago)
            years_ago = today.year - admission_date.year
            if years_ago > 10:
                raise ValidationError("Admission date seems too old. Please verify.")
        return admission_date

    def clean_expected_graduation_date(self):
        expected_graduation_date = self.cleaned_data.get('expected_graduation_date')
        admission_date = self.cleaned_data.get('admission_date')
        programme = self.cleaned_data.get('programme')
        
        if expected_graduation_date and admission_date and programme:
            # Calculate expected graduation based on programme duration
            expected_years = programme.duration_years
            calculated_graduation = admission_date.replace(year=admission_date.year + expected_years)
            
            # Allow some flexibility (6 months before to 2 years after calculated date)
            min_date = calculated_graduation.replace(month=max(1, calculated_graduation.month - 6))
            max_date = calculated_graduation.replace(year=calculated_graduation.year + 2)
            
            if expected_graduation_date < min_date or expected_graduation_date > max_date:
                raise ValidationError(
                    f"Expected graduation date should be around {calculated_graduation.strftime('%Y-%m-%d')} "
                    f"based on the programme duration of {expected_years} years."
                )
        
        return expected_graduation_date

    def clean(self):
        cleaned_data = super().clean()
        programme = cleaned_data.get('programme')
        current_year = cleaned_data.get('current_year')
        current_semester = cleaned_data.get('current_semester')
        
        if programme and current_year and current_semester:
            # Validate year against programme duration
            if current_year > programme.duration_years:
                raise ValidationError(
                    f"Current year cannot exceed programme duration of {programme.duration_years} years."
                )
            
            # Validate semester against programme's semesters per year
            if current_semester > programme.semesters_per_year:
                raise ValidationError(
                    f"Current semester cannot exceed {programme.semesters_per_year} semesters per year "
                    f"for this programme."
                )
        
        return cleaned_data
    





class LecturerForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = [
            'employee_number', 'department', 'academic_rank', 'employment_type',
            'highest_qualification', 'university_graduated', 'graduation_year',
            'research_interests', 'publications', 'professional_registration',
            'teaching_experience_years', 'research_experience_years', 
            'industry_experience_years', 'salary', 'joining_date',
            'contract_end_date', 'office_location', 'office_phone',
            'consultation_hours', 'is_active'
        ]
        widgets = {
            'employee_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'academic_rank': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'highest_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'university_graduated': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'professional_registration': forms.TextInput(attrs={'class': 'form-control'}),
            'teaching_experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'research_experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'industry_experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'office_location': forms.TextInput(attrs={'class': 'form-control'}),
            'office_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'consultation_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# forms.py - Student Services Forms
from django import forms
from django.contrib.auth.models import User
from .models import *

class SpecialExamApplicationForm(forms.ModelForm):
    class Meta:
        model = SpecialExamApplication
        fields = [
            'course', 'application_type', 'reason', 'original_exam_date',
            'supporting_document'
        ]
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Provide detailed reason for your special exam application...'
            }),
            'original_exam_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'application_type': forms.Select(attrs={'class': 'form-control'}),
            'supporting_document': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'supporting_document': 'Supporting Document (Medical certificate, etc.)'
        }

class DefermentApplicationForm(forms.ModelForm):
    class Meta:
        model = DefermentApplication
        fields = [
            'deferment_type', 'reason', 'requested_start_date',
            'requested_duration_months', 'supporting_document'
        ]
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Provide detailed reason for your deferment request...'
            }),
            'requested_start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'deferment_type': forms.Select(attrs={'class': 'form-control'}),
            'requested_duration_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '24'
            }),
            'supporting_document': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'supporting_document': 'Supporting Document (Medical certificate, financial documents, etc.)'
        }

class ClearanceRequestForm(forms.ModelForm):
    class Meta:
        model = ClearanceRequest
        fields = ['clearance_type', 'reason']
        widgets = {
            'clearance_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Explain why you need this clearance...',
                'class': 'form-control'
            })
        }

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'message', 'message_type', 'priority', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter message subject...'
            }),
            'message': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Type your message here...'
            }),
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set recipients to staff, lecturers, admins
        from django.db.models import Q
        self.fields['recipient'].queryset = User.objects.filter(
            Q(user_type__in=['lecturer', 'staff', 'admin', 'hod', 'dean']) |
            Q(is_staff=True)
        )

class MessageReplyForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message', 'attachment']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Type your reply here...'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'})
            
        }



# departments/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from .models import Department, Faculty, User


class DepartmentForm(forms.ModelForm):
    """Form for creating/updating departments"""
    
    class Meta:
        model = Department
        fields = [
            'name', 
            'code', 
            'faculty', 
            'head_of_department', 
            'description', 
            'established_date', 
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department code (e.g., CS, ENG)',
                'maxlength': 10
            }),
            'faculty': forms.Select(attrs={
                'class': 'form-select',
            }),
            'head_of_department': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter department description'
            }),
            'established_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Department Name',
            'code': 'Department Code',
            'faculty': 'Faculty',
            'head_of_department': 'Head of Department',
            'description': 'Description',
            'established_date': 'Established Date',
            'is_active': 'Active Status',
        }
        help_texts = {
            'code': 'Unique code for the department (max 10 characters)',
            'established_date': 'Date when the department was established',
            'head_of_department': 'Optional: Assign a head of department',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter faculties to only active ones
        self.fields['faculty'].queryset = Faculty.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Filter head_of_department to eligible users
        self.fields['head_of_department'].queryset = User.objects.filter(
            user_type__in=['lecturer', 'professor', 'hod', 'staff'],
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Make head_of_department optional
        self.fields['head_of_department'].required = False
        self.fields['head_of_department'].empty_label = "Select Head of Department (Optional)"
        
        # Set default established_date to today
        if not self.instance.pk:
            self.fields['established_date'].initial = timezone.now().date()

    def clean_code(self):
        """Validate department code"""
        code = self.cleaned_data.get('code', '').upper().strip()
        
        if not code:
            raise ValidationError("Department code is required.")
        
        if len(code) < 2:
            raise ValidationError("Department code must be at least 2 characters long.")
        
        # Check for uniqueness (excluding current instance)
        existing = Department.objects.filter(code=code)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError(f"A department with code '{code}' already exists.")
        
        return code

    def clean_name(self):
        """Validate department name"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError("Department name is required.")
        
        if len(name) < 3:
            raise ValidationError("Department name must be at least 3 characters long.")
        
        # Check for uniqueness within the same faculty
        faculty = self.cleaned_data.get('faculty')
        if faculty:
            existing = Department.objects.filter(
                name__iexact=name,
                faculty=faculty
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f"A department named '{name}' already exists in {faculty.name}.")
        
        return name

    def clean_established_date(self):
        """Validate established date"""
        established_date = self.cleaned_data.get('established_date')
        
        if established_date:
            # Can't be in the future
            if established_date > date.today():
                raise ValidationError("Established date cannot be in the future.")
            
            # Can't be too far in the past (before 1800)
            if established_date.year < 1800:
                raise ValidationError("Please enter a valid established date.")
        
        return established_date

    def clean_head_of_department(self):
        """Validate head of department"""
        hod = self.cleaned_data.get('head_of_department')
        
        if hod:
            # Check if user is already HOD of another department
            existing_hod = Department.objects.filter(
                head_of_department=hod
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_hod.exists():
                dept_name = existing_hod.first().name
                raise ValidationError(f"{hod.get_full_name()} is already Head of Department for {dept_name}.")
        
        return hod

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        faculty = cleaned_data.get('faculty')
        hod = cleaned_data.get('head_of_department')
        
        # Additional validations can be added here
        
        return cleaned_data

    def save(self, commit=True):
        """Save the department"""
        department = super().save(commit=False)
        
        # Ensure code is uppercase
        department.code = department.code.upper()
        
        if commit:
            department.save()
            
        return department


class DepartmentFilterForm(forms.Form):
    """Form for filtering departments"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search departments...'
        })
    )
    
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.filter(is_active=True),
        required=False,
        empty_label="All Faculties",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


# forms.py
from django import forms
from .models import StudentClub, ClubEvent


class StudentClubForm(forms.ModelForm):
    chairperson = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Select Chairperson",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = StudentClub
        fields = [
            'name', 'category', 'description', 'chairperson', 
            'contact_phone', 'email', 'meeting_schedule', 
            'membership_fee', 'logo', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter club name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe the club...'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+254 xxx xxx xxx'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'club@university.edu'
            }),
            'meeting_schedule': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'When does the club meet?'
            }),
            'membership_fee': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is already taken by another club
            existing_club = StudentClub.objects.filter(email=email)
            if self.instance.pk:
                existing_club = existing_club.exclude(pk=self.instance.pk)
            if existing_club.exists():
                raise forms.ValidationError("A club with this email already exists.")
        return email


class ClubEventForm(forms.ModelForm):
    club = forms.ModelChoiceField(
        queryset=StudentClub.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    organizer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Select Organizer",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = ClubEvent
        fields = [
            'club', 'title', 'description', 'start_datetime', 
            'end_datetime', 'location', 'organizer', 'status',
            'image', 'registration_required', 'max_participants'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe the event...'
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Event location'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'registration_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise forms.ValidationError("Start date/time must be before end date/time.")
                
        return cleaned_data
    

class AdminResponseForm(forms.ModelForm):
    class Meta:
        model = StudentComment
        fields = ['admin_response', 'is_resolved']
        widgets = {
            'admin_response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter your response to the student...',
                'required': True
            }),
            'is_resolved': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def clean_admin_response(self):
        admin_response = self.cleaned_data.get('admin_response')
        if admin_response and len(admin_response.strip()) < 5:
            raise forms.ValidationError("Response must be at least 5 characters long.")
        return admin_response


class CommentFilterForm(forms.Form):
    SEARCH_CHOICES = [
        ('', 'All Comments'),
        ('resolved', 'Resolved'),
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('unresponded', 'Not Responded'),
    ]
    
    DATE_CHOICES = [
        ('', 'All Time'),
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
    ]
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search comments, student names, or responses...'
        })
    )
    
    status = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date = forms.ChoiceField(
        choices=DATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )