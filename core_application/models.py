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
        ('hostel_warden' , 'Hostel Warden')
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
    
#security models 



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

# Additional models for lecturer unit assignment and course management
# Add these to your existing models.py file

class LecturerCourseAssignment(models.Model):
    """Assigns courses/units to lecturers for specific academic years and semesters"""
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='course_assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lecturer_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='lecturer_assignments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='lecturer_assignments')
    
    # Assignment details
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='assigned_courses', 
                                  help_text="Admin/HOD who assigned the course")
    is_active = models.BooleanField(default=True)
    
    # Optional additional information
    lecture_venue = models.CharField(max_length=100, blank=True, help_text="Default lecture hall/venue")
    lecture_time = models.CharField(max_length=100, blank=True, help_text="e.g., Mon 8-10am, Wed 2-4pm")
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['lecturer', 'course', 'academic_year', 'semester']
        ordering = ['academic_year', 'semester', 'course__name']
    
    def __str__(self):
        return f"{self.lecturer.user.get_full_name()} - {self.course.code} ({self.academic_year.year} S{self.semester.semester_number})"


class CourseNotes(models.Model):
    """Notes posted by lecturers for their assigned courses"""
    NOTE_TYPES = (
        ('lecture', 'Lecture Notes'),
        ('tutorial', 'Tutorial Notes'),
        ('handout', 'Handout'),
        ('reference', 'Reference Material'),
        ('supplementary', 'Supplementary Material'),
        ('revision', 'Revision Notes'),
    )
    
    lecturer_assignment = models.ForeignKey(LecturerCourseAssignment, on_delete=models.CASCADE, 
                                          related_name='course_notes')
    title = models.CharField(max_length=200)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='lecture')
    description = models.TextField(blank=True)
    
    # File upload
    notes_file = models.FileField(upload_to='course_notes/', 
                                help_text="Upload PDF, DOC, PPTX or other document formats")
    file_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Metadata
    week_number = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(20)])
    topic = models.CharField(max_length=200, blank=True)
    posted_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Access control
    is_public = models.BooleanField(default=True, help_text="Visible to all enrolled students")
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-posted_date']
    
    def __str__(self):
        return f"{self.lecturer_assignment.course.code} - {self.title}"


class Assignment(models.Model):
    """Assignments posted by lecturers for their courses"""
    ASSIGNMENT_TYPES = (
        ('individual', 'Individual Assignment'),
        ('group', 'Group Assignment'),
        ('project', 'Project'),
        ('essay', 'Essay'),
        ('report', 'Report'),
        ('case_study', 'Case Study'),
        ('presentation', 'Presentation'),
        ('practical', 'Practical Work'),
    )
    
    SUBMISSION_FORMATS = (
        ('pdf', 'PDF Only'),
        ('doc', 'Word Document'),
        ('any', 'Any Format'),
        ('code', 'Code Files'),
        ('presentation', 'Presentation File'),
    )
    
    lecturer_assignment = models.ForeignKey(LecturerCourseAssignment, on_delete=models.CASCADE, 
                                          related_name='assignments')
    title = models.CharField(max_length=200)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='individual')
    description = models.TextField()
    instructions = models.TextField(blank=True, help_text="Detailed instructions for students")
    
    # Assignment files (optional)
    assignment_file = models.FileField(upload_to='assignments/', null=True, blank=True,
                                     help_text="Assignment question paper or additional materials")
    
    # Timing
    posted_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    late_submission_allowed = models.BooleanField(default=False)
    late_submission_penalty = models.CharField(max_length=200, blank=True, 
                                             help_text="e.g., 10% deduction per day")
    
    # Submission requirements
    max_file_size_mb = models.IntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(100)])
    submission_format = models.CharField(max_length=20, choices=SUBMISSION_FORMATS, default='pdf')
    max_pages = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    min_words = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    max_words = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    
    # Grading
    total_marks = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2, 
                                          validators=[MinValueValidator(0), MaxValueValidator(100)],
                                          help_text="Weight towards final grade (e.g., 15.00 for 15%)")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False, help_text="Make visible to students")
    
    class Meta:
        ordering = ['-posted_date']
    
    def __str__(self):
        return f"{self.lecturer_assignment.course.code} - {self.title}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    @property
    def total_submissions(self):
        return self.submissions.count()
    
    @property
    def submitted_count(self):
        return self.submissions.filter(is_submitted=True).count()
    
    @property
    def pending_submissions(self):
        """Count of enrolled students who haven't submitted"""
        enrolled_students = Enrollment.objects.filter(
            course=self.lecturer_assignment.course,
            semester=self.lecturer_assignment.semester,
            is_active=True
        ).count()
        return enrolled_students - self.submitted_count


class AssignmentSubmission(models.Model):
    """Student submissions for assignments"""
    SUBMISSION_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('late', 'Late Submission'),
        ('resubmitted', 'Resubmitted'),
    )
    
    GRADING_STATUS = (
        ('pending', 'Pending Grading'),
        ('graded', 'Graded'),
        ('returned', 'Returned with Feedback'),
    )
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    
    # Submission details
    submission_file = models.FileField(upload_to='assignment_submissions/')
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Submission metadata
    submitted_date = models.DateTimeField(null=True, blank=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    submission_status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='draft')
    is_submitted = models.BooleanField(default=False)
    is_late = models.BooleanField(default=False)
    
    # Student notes
    student_comments = models.TextField(blank=True, help_text="Optional comments from student")
    
    # Grading
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grading_status = models.CharField(max_length=20, choices=GRADING_STATUS, default='pending')
    graded_date = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='graded_submissions')
    
    # Feedback
    lecturer_feedback = models.TextField(blank=True)
    feedback_file = models.FileField(upload_to='assignment_feedback/', null=True, blank=True,
                                   help_text="Optional feedback file from lecturer")
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_date']
    
    def save(self, *args, **kwargs):
        # Set submission status and check if late
        if self.is_submitted and not self.submitted_date:
            self.submitted_date = timezone.now()
            if self.submitted_date > self.assignment.due_date:
                self.is_late = True
                self.submission_status = 'late'
            else:
                self.submission_status = 'submitted'
        
        # Calculate percentage score
        if self.marks_obtained is not None and self.assignment.total_marks:
            self.percentage_score = (self.marks_obtained / self.assignment.total_marks) * 100
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.student_id} - {self.assignment.title}"


class NotesDownload(models.Model):
    """Track downloads of course notes by students"""
    course_notes = models.ForeignKey(CourseNotes, on_delete=models.CASCADE, related_name='downloads')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notes_downloads')
    downloaded_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-downloaded_date']
    
    def __str__(self):
        return f"{self.student.student_id} downloaded {self.course_notes.title}"


class AssignmentAnnouncement(models.Model):
    """Announcements related to specific assignments"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    message = models.TextField()
    posted_date = models.DateTimeField(auto_now_add=True)
    is_urgent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-posted_date']
    
    def __str__(self):
        return f"{self.assignment.title} - {self.title}"
    
# Add these models to your existing models.py file

class ExamRepository(models.Model):
    """Repository for past papers and revision materials"""
    MATERIAL_TYPES = (
        ('past_paper', 'Past Paper'),
        ('revision_notes', 'Revision Notes'),
        ('marking_scheme', 'Marking Scheme'),
        ('sample_questions', 'Sample Questions'),
        ('study_guide', 'Study Guide'),
        ('reference_material', 'Reference Material'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_materials')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='exam_materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    description = models.TextField(blank=True)
    
    # File details
    material_file = models.FileField(upload_to='exam_repository/')
    file_size = models.IntegerField(null=True, blank=True)
    
    # Academic details
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    exam_date = models.DateField(null=True, blank=True)
    
    # Access control
    is_public = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_date = models.DateTimeField(auto_now_add=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_date']
    
    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.material_type})"


class SpecialExamApplication(models.Model):
    """Applications for special exams (missed or failed exams)"""
    APPLICATION_TYPES = (
        ('missed_exam', 'Missed Exam'),
        ('failed_exam', 'Failed Exam Retake'),
        ('sick_exam', 'Sick During Exam'),
        ('technical_issue', 'Technical Issues'),
        ('other', 'Other Reasons'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('scheduled', 'Exam Scheduled'),
        ('completed', 'Completed'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='special_exam_applications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='special_exam_applications')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    
    # Application details
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)
    reason = models.TextField(help_text="Detailed reason for special exam application")
    original_exam_date = models.DateField(help_text="Date of the original exam")
    
    # Supporting documents
    supporting_document = models.FileField(upload_to='special_exam_docs/', null=True, blank=True,
                                         help_text="Medical certificate, etc.")
    
    # Application processing
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='processed_special_exams')
    processed_date = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)
    
    # Exam scheduling (if approved)
    scheduled_exam_date = models.DateTimeField(null=True, blank=True)
    exam_venue = models.CharField(max_length=100, blank=True)
    exam_duration = models.IntegerField(null=True, blank=True, help_text="Duration in minutes")
    
    # Fee payment
    application_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fee_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} Special Exam"


class DefermentApplication(models.Model):
    """Online applications for academic deferment"""
    DEFERMENT_TYPES = (
        ('medical', 'Medical Reasons'),
        ('financial', 'Financial Difficulties'),
        ('family', 'Family Emergency'),
        ('work', 'Work Commitments'),
        ('personal', 'Personal Reasons'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='deferment_applications')
    
    # Deferment details
    deferment_type = models.CharField(max_length=20, choices=DEFERMENT_TYPES)
    reason = models.TextField(help_text="Detailed reason for deferment")
    requested_start_date = models.DateField(help_text="When you want deferment to start")
    requested_duration_months = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(24)],
                                                   help_text="Duration in months")
    
    # Supporting documents
    supporting_document = models.FileField(upload_to='deferment_docs/', null=True, blank=True,
                                         help_text="Medical certificate, financial documents, etc.")
    
    # Application processing
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='processed_deferments')
    processed_date = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)
    
    # If approved
    approved_start_date = models.DateField(null=True, blank=True)
    approved_end_date = models.DateField(null=True, blank=True)
    conditions = models.TextField(blank=True, help_text="Any conditions for the deferment")
    
    class Meta:
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.student.student_id} - Deferment Application ({self.deferment_type})"


class ClearanceRequest(models.Model):
    """Student clearance requests for various departments"""
    CLEARANCE_TYPES = (
        ('library', 'Library Clearance'),
        ('finance', 'Finance Clearance'),
        ('accommodation', 'Accommodation Clearance'),
        ('department', 'Department Clearance'),
        ('registry', 'Registry Clearance'),
        ('student_affairs', 'Student Affairs Clearance'),
        ('graduation', 'Graduation Clearance'),
        ('transfer', 'Transfer Clearance'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_action', 'Requires Action'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='clearance_requests')
    clearance_type = models.CharField(max_length=20, choices=CLEARANCE_TYPES)
    reason = models.TextField(help_text="Reason for clearance request")
    
    # Request details
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='processed_clearances')
    processed_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    # Requirements check
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    items_to_return = models.TextField(blank=True, help_text="Books, equipment, etc.")
    additional_requirements = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.clearance_type} Clearance"


class Message(models.Model):
    """Messaging system between users"""
    MESSAGE_TYPES = (
        ('personal', 'Personal Message'),
        ('academic', 'Academic Query'),
        ('administrative', 'Administrative'),
        ('announcement', 'Announcement'),
        ('complaint', 'Complaint'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    
    # Message content
    subject = models.CharField(max_length=200)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='personal')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Attachments
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    
    # Message tracking
    sent_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True, blank=True)
    is_starred = models.BooleanField(default=False)
    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_recipient = models.BooleanField(default=False)
    
    # Reply tracking
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='replies')
    
    class Meta:
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.subject}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_date = timezone.now()
            self.save()


class MessageThread(models.Model):
    """Group related messages into threads"""
    subject = models.CharField(max_length=200)
    participants = models.ManyToManyField(User, related_name='message_threads')
    created_date = models.DateTimeField(auto_now_add=True)
    last_message_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_message_date']
    
    def __str__(self):
        return f"Thread: {self.subject}"


class ExamMaterialDownload(models.Model):
    """Track downloads of exam materials"""
    exam_material = models.ForeignKey(ExamRepository, on_delete=models.CASCADE, related_name='downloads')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_downloads')
    downloaded_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-downloaded_date']
    
    def __str__(self):
        return f"{self.student.student_id} downloaded {self.exam_material.title}"


class StudentNotification(models.Model):
    """Notifications for students"""
    NOTIFICATION_TYPES = (
        ('exam_schedule', 'Exam Schedule'),
        ('assignment_due', 'Assignment Due'),
        ('grade_posted', 'Grade Posted'),
        ('message_received', 'Message Received'),
        ('application_status', 'Application Status Update'),
        ('clearance_update', 'Clearance Update'),
        ('general', 'General Notification'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    
    # Tracking
    created_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True, blank=True)
    
    # Optional links
    related_url = models.URLField(blank=True, help_text="Link to related page")
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"Notification for {self.student.student_id}: {self.title}"
    
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
        return f"{self.student.student_id} - {self.bed} ({self.academic_year})"
    
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
        return f"{self.booking.student.student_id } - {self.amount} ({self.payment_date})"
    
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
        return f"{self.booking.student.student_id} - {self.get_incident_type_display()} ({self.incident_date.date()})"


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

import qrcode
import io
import base64
from datetime import datetime, timedelta
from django.utils import timezone

class AttendanceSession(models.Model):
    """QR Code attendance session for each class"""
    WEEK_CHOICES = [(i, f'Week {i}') for i in range(1, 13)]  # Week 1 to 12
    
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='attendance_sessions')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='attendance_sessions')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='attendance_sessions')
    week_number = models.IntegerField(choices=WEEK_CHOICES)
    session_date = models.DateField()
    session_token = models.CharField(max_length=100, unique=True)  # Unique token for QR code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 3 hours after creation
    is_active = models.BooleanField(default=True)
    qr_code_data = models.TextField(blank=True)  # Base64 encoded QR code image
    
    class Meta:
        unique_together = ['timetable_slot', 'week_number', 'session_date']
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.session_token:
            # Generate unique token
            import uuid
            self.session_token = str(uuid.uuid4())
        
        if not self.expires_at:
            # Set expiry to 3 hours from creation
            self.expires_at = timezone.now() + timedelta(hours=3)
        
        super().save(*args, **kwargs)
        
        # Generate QR code after saving
        if not self.qr_code_data:
            self.generate_qr_code()
    
    def generate_qr_code(self):
        """Generate QR code for attendance session"""
        from django.urls import reverse
        from django.contrib.sites.models import Site
        
        # Create attendance URL
        current_site = Site.objects.get_current()
        attendance_url = f"http://{current_site.domain}{reverse('mark_attendance_qr', kwargs={'token': self.session_token})}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(attendance_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Save to model
        self.qr_code_data = qr_code_base64
        AttendanceSession.objects.filter(id=self.id).update(qr_code_data=qr_code_base64)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def qr_code_image_url(self):
        if self.qr_code_data:
            return f"data:image/png;base64,{self.qr_code_data}"
        return None
    
    def __str__(self):
        return f"{self.timetable_slot.course.code} - Week {self.week_number} - {self.session_date}"


class Attendance(models.Model):
    """Student attendance tracking - simplified version"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absence'),
    )
    
    WEEK_CHOICES = [(i, f'Week {i}') for i in range(1, 13)]  # Week 1 to 12
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendance_records')
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='attendance_records')
    week_number = models.IntegerField(choices=WEEK_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_at = models.DateTimeField(auto_now_add=True)
    remarks = models.CharField(max_length=200, blank=True)
    
    # Track how attendance was marked
    marked_via_qr = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'attendance_session', 'week_number']
        ordering = ['-marked_at']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.timetable_slot.course.code} - Week {self.week_number} - {self.status}"

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
    

class NewsArticle(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('event', 'Events'),
        ('announcement', 'Announcements'),
        ('sports', 'Sports'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-publish_date']
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'

class StudentComment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_comments')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Comment'
        verbose_name_plural = 'Student Comments'
    
    def __str__(self):
        return f"Comment by {self.student.student_id} on {self.created_at.date()}"
    


class CommonQuestion(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'question']
    
    def __str__(self):
        return self.question

class QuickLink(models.Model):
    title = models.CharField(max_length=100)
    url = models.URLField()
    icon = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title
    





class StudentClub(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('religious', 'Religious'),
        ('social', 'Social'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    chairperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chaired_clubs')
    contact_phone = models.CharField(max_length=15)
    email = models.EmailField()
    meeting_schedule = models.TextField()
    membership_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ClubMembership(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='club_memberships')
    club = models.ForeignKey(StudentClub, on_delete=models.CASCADE, related_name='members')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_executive = models.BooleanField(default=False)
    position = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        unique_together = ('student', 'club')
    
    def __str__(self):
        return f"{self.student.username} in {self.club.name}"





class ClubEvent(models.Model):
    EVENT_STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    club = models.ForeignKey(StudentClub, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=100)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='club_organized_events')
    status = models.CharField(max_length=20, choices=EVENT_STATUS_CHOICES, default='upcoming')
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    registration_required = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']
        
    def __str__(self):
        return f"{self.title} - {self.club.name}"
    
    def save(self, *args, **kwargs):
        # Automatically update status based on current time
        now = timezone.now()
        if self.start_datetime > now:
            self.status = 'upcoming'
        elif self.start_datetime <= now <= self.end_datetime:
            self.status = 'ongoing'
        elif self.end_datetime < now:
            self.status = 'completed'
        super().save(*args, **kwargs)


class Event(models.Model):
    EVENT_TYPES = (
        ('academic', 'Academic'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('holiday', 'Holiday'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    is_public = models.BooleanField(default=True)
    max_participants = models.IntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    is_attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['event', 'user']


# Add these models to your existing models.py file

from django.contrib.sessions.models import Session
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

class UserSession(models.Model):
    """Track user sessions and online status"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
    
    @property
    def duration(self):
        """Calculate session duration"""
        end_time = self.logout_time if self.logout_time else timezone.now()
        return end_time - self.login_time

class ActivityLog(models.Model):
    """Track all system activities and changes"""
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('download', 'Download'),
        ('upload', 'Upload'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('assign', 'Assign'),
        ('unassign', 'Unassign'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Generic foreign key to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional details
    description = models.TextField(blank=True)
    old_values = models.TextField(blank=True, help_text="JSON of old values for updates")
    new_values = models.TextField(blank=True, help_text="JSON of new values for updates")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.content_object or 'system'}"
    
    def get_old_values_dict(self):
        """Convert old_values JSON string to dict"""
        try:
            return json.loads(self.old_values) if self.old_values else {}
        except json.JSONDecodeError:
            return {}
    
    def get_new_values_dict(self):
        """Convert new_values JSON string to dict"""
        try:
            return json.loads(self.new_values) if self.new_values else {}
        except json.JSONDecodeError:
            return {}

class PageVisit(models.Model):
    """Track page visits for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='page_visits', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    url = models.CharField(max_length=500)
    view_name = models.CharField(max_length=100, blank=True)
    page_title = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.CharField(max_length=500, blank=True)
    response_time = models.IntegerField(null=True, blank=True, help_text="Response time in milliseconds")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['url', 'timestamp']),
            models.Index(fields=['view_name', 'timestamp']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} visited {self.url}"

class SystemMetrics(models.Model):
    """Store daily system metrics"""
    date = models.DateField(unique=True)
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_registrations = models.IntegerField(default=0)
    total_logins = models.IntegerField(default=0)
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    # Student metrics
    students_online = models.IntegerField(default=0)
    assignments_submitted = models.IntegerField(default=0)
    notes_downloaded = models.IntegerField(default=0)
    
    # System performance
    avg_response_time = models.FloatField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}"



# Add these models to your existing models.py

from django.utils import timezone
from datetime import timedelta
import random
import string

class AdminLoginAttempt(models.Model):
    """Track admin login attempts for security monitoring"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    attempt_time = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-attempt_time']
        indexes = [
            models.Index(fields=['username', 'attempt_time']),
            models.Index(fields=['ip_address', 'attempt_time']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.attempt_time} - {'Success' if self.success else 'Failed'}"

class AdminTwoFactorCode(models.Model):
    """Store 2FA codes for admin authentication"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_2fa_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'expires_at']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=3)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    @classmethod
    def generate_code(cls):
        """Generate a 6-digit random code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def __str__(self):
        return f"{self.user.username} - {self.code} - {'Used' if self.is_used else 'Valid' if self.is_valid else 'Expired'}"

class AdminSecurityAlert(models.Model):
    """Track security alerts for suspicious admin login activities"""
    ALERT_TYPES = (
        ('multiple_failures', 'Multiple Login Failures'),
        ('suspicious_ip', 'Suspicious IP Address'),
        ('brute_force', 'Brute Force Attack'),
        ('invalid_2fa', 'Invalid 2FA Attempts'),
    )
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} - {self.username} - {self.created_at}"