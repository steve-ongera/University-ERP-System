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

            if not self.is_update and len(password) < 8:
                raise ValidationError("Password must be at least 8 characters.")

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