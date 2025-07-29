from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
import uuid

# Custom User Model
class User(AbstractUser):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    USER_TYPES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('professor', 'Professor'),
        ('staff', 'Staff'),
        ('registrar', 'Registrar'),
        ('dean', 'Dean'),
        ('hod', 'Head of Department'),
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+\-/]+$',
                message="Username can contain letters, numbers, @, ., +, -, _, and / characters only."
            )
        ],
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_/ allowed."
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_student(self):
        return self.user_type == 'student' and hasattr(self, 'student_profile')

    def __str__(self):
        return f"{self.username} ({self.user_type})"

# Academic Structure Models
class Faculty(models.Model):
    """University Faculties like Faculty of Engineering, Faculty of Medicine, etc."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_faculties')
    established_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Faculties"
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Department(models.Model):
    """Academic departments within faculties"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    head_of_department = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    description = models.TextField(blank=True)
    established_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Programme(models.Model):
    """Academic programmes offered by the university"""
    PROGRAMME_TYPES = (
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('phd', 'PhD'),
        ('diploma', 'Diploma'),
        ('certificate', 'Certificate'),
        ('postgraduate_diploma', 'Postgraduate Diploma'),
    )
    
    PROGRAMME_MODES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('distance_learning', 'Distance Learning'),
        ('online', 'Online'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
    )
    
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    programme_type = models.CharField(max_length=25, choices=PROGRAMME_TYPES)
    study_mode = models.CharField(max_length=20, choices=PROGRAMME_MODES, default='full_time')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='programmes')
    duration_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    semesters_per_year = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(3)], default=2)
    total_semesters = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(24)])
    credit_hours_required = models.IntegerField(validators=[MinValueValidator(60), MaxValueValidator(300)])
    description = models.TextField(blank=True)
    entry_requirements = models.TextField()
    career_prospects = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Course(models.Model):
    """Academic courses/units - can be shared across programmes"""
    COURSE_TYPES = (
        ('core', 'Core Course'),
        ('elective', 'Elective Course'),
        ('major', 'Major Course'),
        ('minor', 'Minor Course'),
        ('general_education', 'General Education'),
        ('capstone', 'Capstone Project'),
        ('thesis', 'Thesis'),
        ('practicum', 'Practicum'),
        ('internship', 'Internship'),
    )
    
    COURSE_LEVELS = (
        ('100', '100 Level (First Year)'),
        ('200', '200 Level (Second Year)'),
        ('300', '300 Level (Third Year)'),
        ('400', '400 Level (Fourth Year)'),
        ('500', '500 Level (Master)'),
        ('600', '600 Level (PhD)'),
    )
    
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='core')
    level = models.CharField(max_length=3, choices=COURSE_LEVELS)
    credit_hours = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(15)])
    lecture_hours = models.IntegerField(default=0)
    tutorial_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    field_work_hours = models.IntegerField(default=0)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField(blank=True)
    learning_outcomes = models.TextField(blank=True)
    assessment_methods = models.TextField(blank=True)
    recommended_textbooks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='prerequisite_for')
    
    def total_contact_hours(self):
        return self.lecture_hours + self.tutorial_hours + self.practical_hours + self.field_work_hours
    
    def __str__(self):
        return f"{self.name} ({self.code})"

#allocated units to programmes 
class ProgrammeCourse(models.Model):
    """Junction table for Programme-Course relationship with semester and year info"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='programme_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_programmes')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['programme', 'course', 'year', 'semester']
        ordering = ['year', 'semester', 'course__name']
    
    def __str__(self):
        return f"{self.programme.code} - {self.course.code} (Y{self.year}S{self.semester})"

# People Models
class Lecturer(models.Model):
    """Academic staff including professors and lecturers"""
    ACADEMIC_RANKS = (
        ('professor', 'Professor'),
        ('associate_professor', 'Associate Professor'),
        ('senior_lecturer', 'Senior Lecturer'),
        ('lecturer', 'Lecturer'),
        ('assistant_lecturer', 'Assistant Lecturer'),
        ('tutorial_fellow', 'Tutorial Fellow'),
        ('graduate_assistant', 'Graduate Assistant'),
        ('visiting_lecturer', 'Visiting Lecturer'),
    )
    
    EMPLOYMENT_TYPES = (
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('part_time', 'Part Time'),
        ('visiting', 'Visiting'),
        ('adjunct', 'Adjunct'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    employee_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='lecturers')
    academic_rank = models.CharField(max_length=30, choices=ACADEMIC_RANKS)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='permanent')
    
    # Academic Qualifications
    highest_qualification = models.CharField(max_length=100)
    university_graduated = models.CharField(max_length=200, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    research_interests = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    
    # Professional Information
    professional_registration = models.CharField(max_length=100, blank=True)
    teaching_experience_years = models.IntegerField(default=0)
    research_experience_years = models.IntegerField(default=0)
    industry_experience_years = models.IntegerField(default=0)
    
    # Employment Details
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    office_location = models.CharField(max_length=100, blank=True)
    office_phone = models.CharField(max_length=15, blank=True)
    consultation_hours = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_number}"

class Student(models.Model):
    ADMISSION_TYPES = (
        ('direct', 'Direct Entry'),
        ('mature', 'Mature Entry'),
        ('transfer', 'Transfer'),
        ('international', 'International'),
        ('exchange', 'Exchange Student'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('deferred', 'Deferred'),
        ('suspended', 'Suspended'),
        ('discontinued', 'Discontinued'),
        ('expelled', 'Expelled'),
        ('on_leave', 'On Academic Leave'),
    )
    
    SPONSOR_TYPES = (
        ('government', 'Government Sponsored'),
        ('self', 'Self Sponsored'),
        ('employer', 'Employer Sponsored'),
        ('scholarship', 'Scholarship'),
        ('bursary', 'Bursary'),
        ('loan', 'Student Loan'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, help_text="University student ID number")
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='students')
    current_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    current_semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    admission_date = models.DateField()
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPES, default='direct')
    sponsor_type = models.CharField(max_length=20, choices=SPONSOR_TYPES, default='government')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Academic Information
    entry_qualification = models.CharField(max_length=100, help_text="e.g., KCSE, A-Level, Diploma")
    entry_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    expected_graduation_date = models.DateField(null=True, blank=True)
    cumulative_gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    total_credit_hours = models.IntegerField(default=0)
    
    # Guardian/Next of Kin Information
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_relationship = models.CharField(max_length=50)
    guardian_address = models.TextField()
    emergency_contact = models.CharField(max_length=15)
    
    # Additional Information
    blood_group = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True)
    accommodation_type = models.CharField(max_length=50, blank=True, help_text="On-campus/Off-campus")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"

class Staff(models.Model):
    STAFF_CATEGORIES = (
        ('administrative', 'Administrative'),
        ('technical', 'Technical Support'),
        ('library', 'Library Staff'),
        ('laboratory', 'Laboratory Technician'),
        ('it_support', 'IT Support'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('catering', 'Catering'),
        ('transport', 'Transport'),
        ('medical', 'Medical Staff'),
        ('counselling', 'Counselling'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_number = models.CharField(max_length=20, unique=True)
    staff_category = models.CharField(max_length=20, choices=STAFF_CATEGORIES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100)
    job_description = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    office_location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_number}"

# Academic Records Models
class AcademicYear(models.Model):
    year = models.CharField(max_length=10, unique=True)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.year

class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start_date = models.DateField()
    registration_end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['academic_year', 'semester_number']
        ordering = ['academic_year', 'semester_number']
    
    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.academic_year.year} - Semester {self.semester_number}"

class StudentReporting(models.Model):
    REPORTING_TYPES = (
        ('online', 'Online Reporting'),
        ('physical', 'Physical Reporting'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    reporting_type = models.CharField(max_length=10, choices=REPORTING_TYPES, default='online')
    reporting_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['-reporting_date']
        
    def __str__(self):
        return f"{self.student.student_id} - {self.semester}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True, blank=True)
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_repeat = models.BooleanField(default=False)
    is_audit = models.BooleanField(default=False, help_text="Audit course (no grade)")
    
    class Meta:
        unique_together = ['student', 'course', 'semester']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} - {self.semester}"

# Updated Grading System for University
class Grade(models.Model):
    GRADE_CHOICES = (
        ('A+', 'A+ (90-100)'),
        ('A', 'A (80-89)'),
        ('A-', 'A- (75-79)'),
        ('B+', 'B+ (70-74)'),
        ('B', 'B (65-69)'),
        ('B-', 'B- (60-64)'),
        ('C+', 'C+ (55-59)'),
        ('C', 'C (50-54)'),
        ('C-', 'C- (45-49)'),
        ('D+', 'D+ (40-44)'),
        ('D', 'D (35-39)'),
        ('F', 'F (Below 35)'),
        ('I', 'Incomplete'),
        ('W', 'Withdrawn'),
        ('P', 'Pass'),
        ('NP', 'No Pass'),
    )
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    continuous_assessment = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="CAT marks (40%)")
    final_exam = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Final exam marks (60%)")
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    project_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    quality_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    exam_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate total marks and determine grade
        if self.continuous_assessment is not None and self.final_exam is not None:
            self.total_marks = (self.continuous_assessment * 0.4) + (self.final_exam * 0.6)
            
            # Add practical and project marks if applicable
            if self.practical_marks:
                self.total_marks += self.practical_marks * 0.1
            if self.project_marks:
                self.total_marks += self.project_marks * 0.1
            
            # Determine grade based on total marks
            if self.total_marks >= 90:
                self.grade = 'A+'
                self.grade_points = 4.0
                self.is_passed = True
            elif self.total_marks >= 80:
                self.grade = 'A'
                self.grade_points = 4.0
                self.is_passed = True
            elif self.total_marks >= 75:
                self.grade = 'A-'
                self.grade_points = 3.7
                self.is_passed = True
            elif self.total_marks >= 70:
                self.grade = 'B+'
                self.grade_points = 3.3
                self.is_passed = True
            elif self.total_marks >= 65:
                self.grade = 'B'
                self.grade_points = 3.0
                self.is_passed = True
            elif self.total_marks >= 60:
                self.grade = 'B-'
                self.grade_points = 2.7
                self.is_passed = True
            elif self.total_marks >= 55:
                self.grade = 'C+'
                self.grade_points = 2.3
                self.is_passed = True
            elif self.total_marks >= 50:
                self.grade = 'C'
                self.grade_points = 2.0
                self.is_passed = True
            elif self.total_marks >= 45:
                self.grade = 'C-'
                self.grade_points = 1.7
                self.is_passed = True
            elif self.total_marks >= 40:
                self.grade = 'D+'
                self.grade_points = 1.3
                self.is_passed = False
            elif self.total_marks >= 35:
                self.grade = 'D'
                self.grade_points = 1.0
                self.is_passed = False
            else:
                self.grade = 'F'
                self.grade_points = 0.0
                self.is_passed = False
            
            # Calculate quality points (grade points * credit hours)
            if self.enrollment.course.credit_hours:
                self.quality_points = self.grade_points * self.enrollment.course.credit_hours
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.enrollment.student.student_id} - {self.enrollment.course.code} - {self.grade}"

# Fee Management Models (Updated for University)
class FeeStructure(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    
    # Different fee components
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    examination_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    laboratory_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fieldwork_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    technology_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    accommodation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    meals_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    medical_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    insurance_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    student_union_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sports_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    graduation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Financial aid
    government_subsidy = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scholarship_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['programme', 'academic_year', 'year', 'semester']
    
    def total_fee(self):
        return (self.tuition_fee + self.registration_fee + self.examination_fee + 
                self.library_fee + self.laboratory_fee + self.fieldwork_fee + 
                self.technology_fee + self.accommodation_fee + self.meals_fee + 
                self.medical_fee + self.insurance_fee + self.student_union_fee + 
                self.sports_fee + self.graduation_fee + self.other_fees)
    
    def net_fee(self):
        """Fee after subsidies and scholarships"""
        return self.total_fee() - self.government_subsidy - self.scholarship_amount
    
    def __str__(self):
        return f"{self.programme.code} - {self.academic_year.year} - Y{self.year}S{self.semester}"

class FeePayment(models.Model):
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bankers_cheque', 'Bankers Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Credit/Debit Card'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
        ('refunded', 'Refunded'),
        ('partial', 'Partial Payment'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    receipt_number = models.CharField(max_length=50, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_reference = models.CharField(max_length=100, blank=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    bank_slip_number = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.receipt_number} - KES {self.amount_paid}"

# Additional University-specific Models
class Research(models.Model):
    """Research projects and publications"""
    RESEARCH_TYPES = (
        ('undergraduate', 'Undergraduate Research'),
        ('masters', 'Masters Thesis'),
        ('phd', 'PhD Dissertation'),
        ('faculty', 'Faculty Research'),
        ('collaborative', 'Collaborative Research'),
        ('funded', 'Funded Research Project'),
    )
    
    STATUS_CHOICES = (
        ('proposal', 'Proposal Stage'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('published', 'Published'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=300)
    research_type = models.CharField(max_length=20, choices=RESEARCH_TYPES)
    principal_investigator = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='led_research')
    co_investigators = models.ManyToManyField(Lecturer, blank=True, related_name='collaborated_research')
    students = models.ManyToManyField(Student, blank=True, related_name='research_projects')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='research_projects')
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposal')
    abstract = models.TextField()
    keywords = models.CharField(max_length=500, blank=True)
    funding_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    funding_source = models.CharField(max_length=200, blank=True)
    ethics_approval = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.principal_investigator.user.get_full_name()}"

class Library(models.Model):
    """Library resources and management"""
    RESOURCE_TYPES = (
        ('book', 'Book'),
        ('journal', 'Journal'),
        ('ebook', 'E-Book'),
        ('thesis', 'Thesis/Dissertation'),
        ('reference', 'Reference Material'),
        ('multimedia', 'Multimedia'),
        ('database', 'Online Database'),
    )
    
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    publisher = models.CharField(max_length=200, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    location = models.CharField(max_length=100, blank=True)
    call_number = models.CharField(max_length=50, unique=True)
    subject_area = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    digital_copy_url = models.URLField(blank=True)
    is_available = models.BooleanField(default=True)
    added_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.author}"

class LibraryTransaction(models.Model):
    """Library book borrowing and returning"""
    TRANSACTION_TYPES = (
        ('borrow', 'Borrow'),
        ('return', 'Return'),
        ('renew', 'Renew'),
        ('reserve', 'Reserve'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_transactions')
    library_resource = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    librarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_transactions')
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.library_resource.title} - {self.transaction_type}"

# Hostel/Accommodation Models
class Hostel(models.Model):
    """Hostel buildings for accommodation"""
    HOSTEL_TYPES = (
        ('boys', 'Boys Hostel'),
        ('girls', 'Girls Hostel'),
    )
    
    name = models.CharField(max_length=100)
    hostel_type = models.CharField(max_length=10, choices=HOSTEL_TYPES)
    school = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='hostels')
    warden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_hostels')
    total_rooms = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    facilities = models.TextField(blank=True, help_text="Available facilities like WiFi, laundry, etc.")
    rules_and_regulations = models.TextField( null=True, blank=True,)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True,)
    
    class Meta:
        ordering = ['hostel_type', 'name']

    
    
    def __str__(self):
        return f"{self.name} ({self.get_hostel_type_display()})"
    
    def get_available_rooms_count(self, academic_year):
        """Get count of rooms with available beds for the academic year"""
        return self.rooms.filter(
            beds__academic_year=academic_year,
            beds__is_available=True,
            is_active=True
        ).distinct().count()
    
    def get_total_beds_count(self, academic_year):
        """Get total beds in hostel for academic year"""
        return self.rooms.filter(
            beds__academic_year=academic_year,
            is_active=True
        ).aggregate(
            total=models.Count('beds')
        )['total'] or 0
    
    def get_occupied_beds_count(self, academic_year):
        """Get count of occupied beds for academic year"""
        return self.rooms.filter(
            beds__academic_year=academic_year,
            beds__is_available=False,
            is_active=True
        ).aggregate(
            occupied=models.Count('beds')
        )['occupied'] or 0


class Room(models.Model):
    """Individual rooms in hostels"""
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    floor = models.IntegerField(validators=[MinValueValidator(0)], help_text="Floor number (0 for ground floor)")
    capacity = models.IntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(8)])
    description = models.TextField(blank=True)
    facilities = models.TextField(blank=True, help_text="Room-specific facilities")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True , blank=True , null=True)
    
    class Meta:
        unique_together = ['hostel', 'room_number']
        ordering = ['hostel', 'floor', 'room_number']
    
    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"
    
    def get_available_beds_count(self, academic_year):
        """Get count of available beds in this room for academic year"""
        return self.beds.filter(
            academic_year=academic_year,
            is_available=True
        ).count()
    
    def get_occupied_beds_count(self, academic_year):
        """Get count of occupied beds in this room for academic year"""
        return self.beds.filter(
            academic_year=academic_year,
            is_available=False
        ).count()
    
    def is_full(self, academic_year):
        """Check if room is fully occupied for academic year"""
        return self.get_available_beds_count(academic_year) == 0

class Bed(models.Model):
    """Individual beds in rooms for each academic year"""
    BED_POSITIONS = (
        ('bed_1', 'Bed 1'),
        ('bed_2', 'Bed 2'),
        ('bed_3', 'Bed 3'),
        ('bed_4', 'Bed 4'),
    )
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_beds')
    bed_position = models.CharField(max_length=10, choices=BED_POSITIONS)
    bed_number = models.CharField(max_length=20, help_text="Unique bed identifier")
    is_available = models.BooleanField(default=True)
    maintenance_status = models.CharField(
        max_length=20,
        choices=(
            ('good', 'Good Condition'),
            ('needs_repair', 'Needs Repair'),
            ('under_maintenance', 'Under Maintenance'),
            ('out_of_order', 'Out of Order'),
        ),
        default='good'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['room', 'academic_year', 'bed_position']
        ordering = ['room', 'bed_position']
    
    def __str__(self):
        return f"{self.room} - {self.bed_number} ({self.academic_year})"
    
    def save(self, *args, **kwargs):
        if not self.bed_number:
            # Auto-generate bed number: HOSTEL_ROOM_BED_YEAR
            hostel_code = self.room.hostel.name[:3].upper()
            year_code = self.academic_year.year.split('/')[0][-2:]  # Last 2 digits of start year
            self.bed_number = f"{hostel_code}{self.room.room_number}{self.bed_position[-1]}{year_code}"
        super().save(*args, **kwargs)


class HostelBooking(models.Model):
    """Student hostel booking records"""
    BOOKING_STATUS = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Payment Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hostel_bookings')
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='bookings')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_bookings')
    
    booking_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    expected_checkout_date = models.DateField(null=True, blank=True)
    
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Approval workflow
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True)
    
    # Check-in/out details
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_students')
    checked_out_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_out_students')
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'academic_year']  # One booking per student per academic year
        ordering = ['-booking_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.bed} ({self.academic_year})"
    
    def save(self, *args, **kwargs):
        # Update bed availability based on booking status
        if self.pk:  # If updating existing booking
            old_booking = HostelBooking.objects.get(pk=self.pk)
            if old_booking.booking_status != self.booking_status:
                if self.booking_status in ['approved', 'checked_in']:
                    self.bed.is_available = False
                    self.bed.save()
                elif self.booking_status in ['rejected', 'cancelled', 'checked_out']:
                    self.bed.is_available = True
                    self.bed.save()
        else:  # New booking
            if self.booking_status in ['approved', 'checked_in']:
                self.bed.is_available = False
                self.bed.save()
        
        super().save(*args, **kwargs)
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.booking_fee - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if booking is fully paid"""
        return self.amount_paid >= self.booking_fee

class HostelPayment(models.Model):
    """Track hostel fee payments"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('card', 'Credit/Debit Card'),
    )
    
    booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.booking.student.registration_number} - {self.amount} ({self.payment_date})"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Auto-generate receipt number
            year = timezone.now().year
            count = HostelPayment.objects.filter(
                created_at__year=year
            ).count() + 1
            self.receipt_number = f"HPR{year}{count:05d}"
        
        super().save(*args, **kwargs)
        
        # Update booking payment status
        booking = self.booking
        total_paid = booking.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        booking.amount_paid = total_paid
        
        if total_paid >= booking.booking_fee:
            booking.payment_status = 'paid'
        elif total_paid > 0:
            booking.payment_status = 'partial'
        else:
            booking.payment_status = 'pending'
        
        booking.save()

class HostelIncident(models.Model):
    """Track incidents and disciplinary issues in hostels"""
    INCIDENT_TYPES = (
        ('damage', 'Property Damage'),
        ('noise', 'Noise Complaint'),
        ('theft', 'Theft'),
        ('violence', 'Violence/Fighting'),
        ('drugs', 'Drug/Alcohol Related'),
        ('curfew', 'Curfew Violation'),
        ('cleanliness', 'Cleanliness Issue'),
        ('other', 'Other'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('reported', 'Reported'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
    )
    
    booking = models.ForeignKey(HostelBooking, on_delete=models.CASCADE, related_name='incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
    incident_date = models.DateTimeField()
    description = models.TextField()
    action_taken = models.TextField(blank=True)
    
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_incidents')
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_incidents')
    
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incident_date']
    
    def __str__(self):
        return f"{self.booking.student.registration_number} - {self.get_incident_type_display()} ({self.incident_date.date()})"


class Examination(models.Model):
    """Examination scheduling and management"""
    EXAM_TYPES = (
        ('cat', 'Continuous Assessment Test'),
        ('mid_semester', 'Mid-Semester Exam'),
        ('final', 'Final Examination'),
        ('supplementary', 'Supplementary Exam'),
        ('special', 'Special Examination'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='examinations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='examinations')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    exam_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.IntegerField()
    venue = models.CharField(max_length=100)
    max_marks = models.IntegerField(default=100)
    instructions = models.TextField(blank=True)
    invigilators = models.ManyToManyField(Lecturer, blank=True, related_name='invigilated_exams')
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def end_time(self):
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.exam_date, self.start_time)
        end_datetime = start_datetime + timedelta(minutes=self.duration_minutes)
        return end_datetime.time()
    
    def __str__(self):
        return f"{self.course.code} - {self.exam_type} - {self.exam_date}"

class Timetable(models.Model):
    """Class timetable management"""
    DAYS_OF_WEEK = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    CLASS_TYPES = (
        ('lecture', 'Lecture'),
        ('tutorial', 'Tutorial'),
        ('practical', 'Practical'),
        ('seminar', 'Seminar'),
        ('fieldwork', 'Field Work'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetable_slots')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='teaching_slots')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=100)
    class_type = models.CharField(max_length=15, choices=CLASS_TYPES, default='lecture')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='timetable_slots')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    semester_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['course', 'lecturer', 'semester', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.course.code} - {self.day_of_week} {self.start_time}-{self.end_time}"

class Attendance(models.Model):
    """Student attendance tracking"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absence'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='marked_attendance')
    remarks = models.CharField(max_length=200, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'timetable_slot', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.timetable_slot.course.code} - {self.date} - {self.status}"

class Notification(models.Model):
    """System notifications"""
    NOTIFICATION_TYPES = (
        ('academic', 'Academic'),
        ('fee', 'Fee Related'),
        ('exam', 'Examination'),
        ('general', 'General'),
        ('emergency', 'Emergency'),
        ('event', 'Event'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    recipients = models.ManyToManyField(User, related_name='received_notifications')
    is_read = models.BooleanField(default=False)
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.notification_type}"