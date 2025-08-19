#!/usr/bin/env python
"""
Django Management Command for University Student Enrollment, Fee Payment & Grade Assignment
Usage: 
  python manage.py seed_university_data
  python manage.py seed_university_data --enroll-student STUDENT123
  python manage.py seed_university_data --reset-student STUDENT123
  python manage.py seed_university_data --reset-all
  python manage.py seed_university_data --create-mappings
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

from core_application.models import (
    User, Student, Programme, Course, AcademicYear, Semester, 
    Enrollment, Grade, FeeStructure, FeePayment, ProgrammeCourse,
    Lecturer, LecturerCourseAssignment
)


class Command(BaseCommand):
    help = 'Seed university data with student enrollments, grades, and fee payments'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_date = date.today()
        self.current_year = self.current_date.year
        
        # Grade mapping for random grade generation
        self.grade_options = [
            ('A+', 4.0, 95), ('A', 4.0, 85), ('A-', 3.7, 77),
            ('B+', 3.3, 72), ('B', 3.0, 67), ('B-', 2.7, 62),
            ('C+', 2.3, 57), ('C', 2.0, 52), ('C-', 1.7, 47),
            ('D+', 1.3, 42), ('D', 1.0, 37), ('F', 0.0, 25)
        ]
        
        # Payment methods for fee payments
        self.payment_methods = ['mpesa', 'bank_transfer', 'online', 'card']

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--enroll-student',
            type=str,
            help='Enroll a specific student by student ID',
        )
        
        parser.add_argument(
            '--reset-student',
            type=str,
            help='Reset enrollment and payment data for a specific student',
        )
        
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Reset ALL student enrollment and payment data (use with caution)',
        )
        
        parser.add_argument(
            '--create-mappings',
            action='store_true',
            help='Create sample programme-course mappings',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        try:
            if options['enroll_student']:
                self.enroll_specific_student(options['enroll_student'], options['dry_run'])
            elif options['reset_student']:
                self.reset_student_data(options['reset_student'], options['dry_run'])
            elif options['reset_all']:
                self.reset_all_data(options['dry_run'])
            elif options['create_mappings']:
                self.create_sample_programme_courses(options['dry_run'])
            else:
                self.run_full_seeding(options['dry_run'])
                
        except Exception as e:
            raise CommandError(f'Seeding failed: {str(e)}')

    def log(self, message, level='INFO'):
        """Enhanced logging with different levels"""
        timestamp = timezone.now().strftime('%H:%M:%S')
        if level == 'ERROR':
            self.stdout.write(
                self.style.ERROR(f"[{timestamp}] ERROR: {message}")
            )
        elif level == 'WARNING':
            self.stdout.write(
                self.style.WARNING(f"[{timestamp}] WARNING: {message}")
            )
        elif level == 'SUCCESS':
            self.stdout.write(
                self.style.SUCCESS(f"[{timestamp}] SUCCESS: {message}")
            )
        else:
            self.stdout.write(f"[{timestamp}] {message}")

    def get_tuition_fee(self, programme):
        """Calculate tuition fee based on programme type"""
        base_fees = {
            'bachelor': Decimal('60000'),
            'master': Decimal('80000'),
            'phd': Decimal('100000'),
            'diploma': Decimal('45000'),
            'certificate': Decimal('30000'),
            'postgraduate_diploma': Decimal('70000'),
        }
        return base_fees.get(programme.programme_type, Decimal('60000'))
    
    def get_government_subsidy(self, programme):
        """Calculate government subsidy"""
        if programme.programme_type == 'bachelor':
            return Decimal('30000')
        elif programme.programme_type == 'diploma':
            return Decimal('20000')
        return Decimal('0')

    @transaction.atomic
    def enroll_students_to_courses(self, dry_run=False):
        """Enroll students to courses based on their programme and current academic status"""
        students = Student.objects.filter(status='active')
        enrollment_count = 0
        
        for student in students:
            self.log(f"Processing enrollments for student: {student.student_id}")
            
            # Calculate academic years student should be enrolled
            admission_year = student.admission_date.year
            programme_duration = student.programme.duration_years
            
            # Get all academic years student should be part of
            for year_offset in range(programme_duration):
                target_year = admission_year + year_offset
                target_academic_year_str = f"{target_year}/{target_year+1}"
                
                try:
                    academic_year = AcademicYear.objects.get(year=target_academic_year_str)
                except AcademicYear.DoesNotExist:
                    continue
                
                student_year = year_offset + 1
                
                # Skip if student hasn't reached this year yet
                if target_year > self.current_year:
                    continue
                
                # Get programme courses for this year
                programme_courses = ProgrammeCourse.objects.filter(
                    programme=student.programme,
                    year=student_year,
                    is_active=True
                )
                
                for semester_num in range(1, student.programme.semesters_per_year + 1):
                    # Skip future semesters in current year
                    if (target_year == self.current_year and 
                        semester_num > student.current_semester):
                        continue
                    
                    try:
                        semester = Semester.objects.get(
                            academic_year=academic_year,
                            semester_number=semester_num
                        )
                    except Semester.DoesNotExist:
                        continue
                    
                    # Get courses for this semester
                    semester_courses = programme_courses.filter(semester=semester_num)
                    
                    for programme_course in semester_courses:
                        # Check if already enrolled
                        existing_enrollment = Enrollment.objects.filter(
                            student=student,
                            course=programme_course.course,
                            semester=semester
                        ).first()
                        
                        if not existing_enrollment:
                            # Get a lecturer assignment for this course
                            lecturer_assignment = LecturerCourseAssignment.objects.filter(
                                course=programme_course.course,
                                academic_year=academic_year,
                                semester=semester,
                                is_active=True
                            ).first()
                            
                            if not dry_run:
                                # Create enrollment
                                enrollment = Enrollment.objects.create(
                                    student=student,
                                    course=programme_course.course,
                                    semester=semester,
                                    lecturer=lecturer_assignment.lecturer if lecturer_assignment else None,
                                    is_active=True
                                )
                                
                                # Create grade if semester is completed (not current or future)
                                if (target_year < self.current_year or 
                                    (target_year == self.current_year and semester_num < student.current_semester)):
                                    self.create_grade_for_enrollment(enrollment, dry_run)
                                
                                enrollment_count += 1
                            
                            self.log(f"{'[DRY RUN] Would enroll' if dry_run else 'Enrolled'} {student.student_id} to {programme_course.course.code} for {semester}")
                            
                        # Handle fee payment for this semester
                        self.process_fee_payment(student, academic_year, student_year, semester_num, dry_run)
        
        return enrollment_count

    def create_grade_for_enrollment(self, enrollment, dry_run=False):
        """Create a grade for an enrollment if it doesn't exist"""
        existing_grade = Grade.objects.filter(enrollment=enrollment).first()
        
        if not existing_grade:
            # Generate random but realistic grades
            grade_choice = random.choices(
                self.grade_options,
                weights=[5, 10, 15, 20, 20, 15, 10, 3, 1, 0.5, 0.3, 0.2]  # Weighted towards better grades
            )[0]
            
            grade_letter, grade_points, avg_marks = grade_choice
            
            # Generate marks with some variation
            variation = random.uniform(-5, 5)
            total_marks = max(0, min(100, avg_marks + variation))
            
            # Calculate CAT and Final exam marks
            cat_marks = total_marks * 0.4
            final_marks = total_marks * 0.6
            
            if not dry_run:
                Grade.objects.create(
                    enrollment=enrollment,
                    continuous_assessment=round(cat_marks, 2),
                    final_exam=round(final_marks, 2),
                    total_marks=round(total_marks, 2),
                    grade=grade_letter,
                    grade_points=grade_points,
                    is_passed=grade_points >= 2.0,
                    exam_date=enrollment.semester.end_date
                )
            
            self.log(f"{'[DRY RUN] Would create' if dry_run else 'Created'} grade {grade_letter} for {enrollment.student.student_id} - {enrollment.course.code}")

    def process_fee_payment(self, student, academic_year, year, semester, dry_run=False):
        """Process fee payment for a student's semester"""
        # Get existing fee structure
        fee_structure = FeeStructure.objects.filter(
            programme=student.programme,
            academic_year=academic_year,
            year=year,
            semester=semester
        ).first()
        
        if not fee_structure:
            self.log(f"No fee structure found for {student.programme.code} {academic_year.year} Y{year}S{semester}", 'WARNING')
            return
        
        # Check if payment already exists
        existing_payment = FeePayment.objects.filter(
            student=student,
            fee_structure=fee_structure
        ).first()
        
        if not existing_payment:
            # Calculate payment amount (usually net fee)
            amount_to_pay = fee_structure.net_fee()
            
            # Generate receipt number
            receipt_number = self.generate_receipt_number(student, academic_year, semester)
            
            # Create payment record
            payment_date = self.calculate_payment_date(academic_year, semester)
            
            if not dry_run:
                FeePayment.objects.create(
                    student=student,
                    fee_structure=fee_structure,
                    receipt_number=receipt_number,
                    amount_paid=amount_to_pay,
                    payment_date=payment_date,
                    payment_method=random.choice(self.payment_methods),
                    payment_status='completed',
                    transaction_reference=f"TXN{receipt_number}",
                    mpesa_receipt=f"M{random.randint(100000000, 999999999)}" if random.choice([True, False]) else "",
                    remarks=f"Full semester fee payment for {academic_year.year} semester {semester}"
                )
            
            self.log(f"{'[DRY RUN] Would create' if dry_run else 'Created'} fee payment for {student.student_id} - {receipt_number} - KES {amount_to_pay}")

    def generate_receipt_number(self, student, academic_year, semester):
        """Generate unique receipt number"""
        year_code = academic_year.year.split('/')[0][-2:]  # Last 2 digits of year
        student_code = student.student_id[-4:]  # Last 4 digits of student ID
        semester_code = f"S{semester}"
        
        # Generate unique receipt number
        max_attempts = 100
        for attempt in range(max_attempts):
            random_code = random.randint(1000, 9999)  # Use 4 digits for better uniqueness
            receipt_number = f"FEE{year_code}{student_code}{semester_code}{random_code}"
            
            # Check if this receipt number already exists
            if not FeePayment.objects.filter(receipt_number=receipt_number).exists():
                return receipt_number
        
        # Fallback: use timestamp if all attempts fail
        timestamp = int(timezone.now().timestamp())
        return f"FEE{year_code}{student_code}{semester_code}{timestamp}"

    def calculate_payment_date(self, academic_year, semester_num):
        """Calculate realistic payment date for semester"""
        try:
            semester = Semester.objects.get(
                academic_year=academic_year,
                semester_number=semester_num
            )
            # Payment usually happens before or at start of semester
            base_date = semester.start_date
            # Add some random days before/after start
            days_offset = random.randint(-15, 30)
            return base_date + timedelta(days=days_offset)
        except Semester.DoesNotExist:
            # Fallback to academic year dates
            if semester_num == 1:
                return academic_year.start_date + timedelta(days=random.randint(0, 30))
            else:
                return date(int(academic_year.year.split('/')[1]), 1, 1) + timedelta(days=random.randint(0, 30))

    @transaction.atomic
    def assign_lecturers_to_courses(self, dry_run=False):
        """Assign lecturers to courses for current academic year"""
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_academic_year or not current_semester:
            self.log("No current academic year or semester found", 'WARNING')
            return 0
        
        # Get all courses that need lecturer assignments
        courses = Course.objects.filter(is_active=True)
        lecturers = Lecturer.objects.filter(is_active=True)
        assignment_count = 0
        
        for course in courses:
            # Check if lecturer assignment exists for current academic year
            existing_assignment = LecturerCourseAssignment.objects.filter(
                course=course,
                academic_year=current_academic_year,
                semester=current_semester
            ).first()
            
            if not existing_assignment:
                # Find suitable lecturer from same department
                suitable_lecturers = lecturers.filter(department=course.department)
                
                if suitable_lecturers:
                    lecturer = random.choice(suitable_lecturers)
                    
                    if not dry_run:
                        LecturerCourseAssignment.objects.create(
                            lecturer=lecturer,
                            course=course,
                            academic_year=current_academic_year,
                            semester=current_semester,
                            lecture_venue=f"LH-{random.randint(1, 20)}",
                            lecture_time=self.generate_lecture_time(),
                            is_active=True
                        )
                    
                    assignment_count += 1
                    self.log(f"{'[DRY RUN] Would assign' if dry_run else 'Assigned'} {lecturer.user.get_full_name()} to {course.code}")
        
        return assignment_count

    def generate_lecture_time(self):
        """Generate random lecture time"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        times = ['8:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00', '16:00-18:00']
        
        day = random.choice(days)
        time = random.choice(times)
        return f"{day} {time}"

    @transaction.atomic
    def update_student_academic_progress(self, dry_run=False):
        """Update students' current year and semester based on their enrollments"""
        students = Student.objects.filter(status='active')
        updated_count = 0
        
        for student in students:
            # Find the highest year and semester the student is enrolled in
            latest_enrollment = Enrollment.objects.filter(
                student=student,
                is_active=True
            ).order_by('-semester__academic_year__start_date', '-semester__semester_number').first()
            
            if latest_enrollment:
                # Get the programme course to determine year
                programme_course = ProgrammeCourse.objects.filter(
                    programme=student.programme,
                    course=latest_enrollment.course
                ).first()
                
                if programme_course:
                    if not dry_run:
                        student.current_year = programme_course.year
                        student.current_semester = latest_enrollment.semester.semester_number
                        student.save()
                    
                    updated_count += 1
                    self.log(f"{'[DRY RUN] Would update' if dry_run else 'Updated'} {student.student_id} to Year {programme_course.year}, Semester {latest_enrollment.semester.semester_number}")
        
        return updated_count

    @transaction.atomic
    def calculate_student_gpa(self, dry_run=False):
        """Calculate cumulative GPA for all students"""
        students = Student.objects.filter(status='active')
        gpa_count = 0
        
        for student in students:
            # Get all completed grades
            grades = Grade.objects.filter(
                enrollment__student=student,
                grade_points__isnull=False,
                enrollment__is_active=True
            )
            
            if grades:
                total_quality_points = sum(grade.quality_points or 0 for grade in grades)
                total_credit_hours = sum(grade.enrollment.course.credit_hours for grade in grades)
                
                if total_credit_hours > 0:
                    cumulative_gpa = total_quality_points / total_credit_hours
                    
                    if not dry_run:
                        student.cumulative_gpa = round(cumulative_gpa, 2)
                        student.total_credit_hours = total_credit_hours
                        student.save()
                    
                    gpa_count += 1
                    self.log(f"{'[DRY RUN] Would update' if dry_run else 'Updated'} GPA for {student.student_id}: {round(cumulative_gpa, 2)}")
        
        return gpa_count

    def enroll_specific_student(self, student_id, dry_run=False):
        """Enroll a specific student (useful for testing)"""
        try:
            student = Student.objects.get(student_id=student_id)
            self.log(f"Processing specific student: {student_id}")
            
            # Temporarily filter to only this student
            original_filter = Student.objects.filter(student_id=student_id, status='active')
            
            if original_filter.exists():
                # Process enrollments for this student only
                with transaction.atomic():
                    # First assign lecturers if needed
                    self.assign_lecturers_to_courses(dry_run)
                    
                    # Then enroll student
                    enrollments = self.enroll_students_to_courses(dry_run)
                    self.update_student_academic_progress(dry_run)
                    self.calculate_student_gpa(dry_run)
                
                self.log(f"Successfully processed student {student_id}", 'SUCCESS')
            else:
                self.log(f"Student {student_id} not found or not active", 'ERROR')
                
        except Student.DoesNotExist:
            raise CommandError(f"Student with ID {student_id} not found")

    @transaction.atomic
    def create_sample_programme_courses(self, dry_run=False):
        """Create sample programme-course mappings if none exist"""
        programmes = Programme.objects.filter(is_active=True)
        mapping_count = 0
        
        for programme in programmes:
            self.log(f"Creating course mappings for programme: {programme.code}")
            
            # Get courses from the same department/faculty
            department_courses = Course.objects.filter(
                department=programme.department,
                is_active=True
            )
            
            if not department_courses:
                # Get courses from faculty
                department_courses = Course.objects.filter(
                    department__faculty=programme.faculty,
                    is_active=True
                )
            
            if department_courses:
                courses_per_semester = min(6, len(department_courses) // (programme.duration_years * programme.semesters_per_year))
                course_index = 0
                
                for year in range(1, programme.duration_years + 1):
                    for semester in range(1, programme.semesters_per_year + 1):
                        for _ in range(courses_per_semester):
                            if course_index < len(department_courses):
                                course = department_courses[course_index]
                                
                                # Check if mapping already exists
                                existing = ProgrammeCourse.objects.filter(
                                    programme=programme,
                                    course=course,
                                    year=year,
                                    semester=semester
                                ).first()
                                
                                if not existing:
                                    if not dry_run:
                                        ProgrammeCourse.objects.create(
                                            programme=programme,
                                            course=course,
                                            year=year,
                                            semester=semester,
                                            is_mandatory=True,
                                            is_active=True
                                        )
                                    
                                    mapping_count += 1
                                    self.log(f"{'[DRY RUN] Would create' if dry_run else 'Created'} programme-course mapping: {programme.code} - {course.code} Y{year}S{semester}")
                                
                                course_index += 1
        
        return mapping_count

    @transaction.atomic
    def reset_student_data(self, student_id, dry_run=False):
        """Reset enrollment and grade data for a specific student"""
        try:
            student = Student.objects.get(student_id=student_id)
            
            if not dry_run:
                enrollment_count = Enrollment.objects.filter(student=student).count()
                payment_count = FeePayment.objects.filter(student=student).count()
                
                Enrollment.objects.filter(student=student).delete()
                FeePayment.objects.filter(student=student).delete()
                
                self.log(f"Reset data for student {student_id}: {enrollment_count} enrollments, {payment_count} payments deleted", 'SUCCESS')
            else:
                enrollment_count = Enrollment.objects.filter(student=student).count()
                payment_count = FeePayment.objects.filter(student=student).count()
                self.log(f"[DRY RUN] Would reset data for student {student_id}: {enrollment_count} enrollments, {payment_count} payments")
                
        except Student.DoesNotExist:
            raise CommandError(f"Student with ID {student_id} not found")

    @transaction.atomic
    def reset_all_data(self, dry_run=False):
        """Reset ALL student enrollment and payment data"""
        if not dry_run:
            # Ask for confirmation in non-dry-run mode
            confirm = input("Are you sure you want to reset ALL student enrollment and payment data? (yes/no): ")
            if confirm.lower() != 'yes':
                self.log("Operation cancelled by user", 'WARNING')
                return
        
        enrollment_count = Enrollment.objects.count()
        grade_count = Grade.objects.count()
        payment_count = FeePayment.objects.count()
        
        if not dry_run:
            Enrollment.objects.all().delete()
            Grade.objects.all().delete()
            FeePayment.objects.all().delete()
            self.log(f"Reset ALL data: {enrollment_count} enrollments, {grade_count} grades, {payment_count} payments deleted", 'SUCCESS')
        else:
            self.log(f"[DRY RUN] Would reset ALL data: {enrollment_count} enrollments, {grade_count} grades, {payment_count} payments")

    def run_full_seeding(self, dry_run=False):
        """Main function to run all seeding operations"""
        self.log("Starting university data seeding..." + (" (DRY RUN)" if dry_run else ""))
        
        # Check if we have programme-course mappings
        if not ProgrammeCourse.objects.exists():
            self.log("No programme-course mappings found. Creating sample mappings...")
            self.create_sample_programme_courses(dry_run)
        
        # Step 1: Assign lecturers to courses
        self.log("Assigning lecturers to courses...")
        assignments = self.assign_lecturers_to_courses(dry_run)
        
        # Step 2: Enroll students to courses
        self.log("Enrolling students to courses...")
        enrollments = self.enroll_students_to_courses(dry_run)
        
        # Step 3: Update student academic progress
        self.log("Updating student academic progress...")
        progress_updates = self.update_student_academic_progress(dry_run)
        
        # Step 4: Calculate GPAs
        self.log("Calculating student GPAs...")
        gpa_updates = self.calculate_student_gpa(dry_run)
        
        self.log("Seeding completed successfully!" + (" (DRY RUN)" if dry_run else ""), 'SUCCESS')
        
        # Print summary statistics
        self.print_summary(dry_run)

    def print_summary(self, dry_run=False):
        """Print summary of created data"""
        self.log("\n" + "="*50)
        self.log("SEEDING SUMMARY" + (" (DRY RUN)" if dry_run else ""))
        self.log("="*50)
        
        total_students = Student.objects.filter(status='active').count()
        total_enrollments = Enrollment.objects.filter(is_active=True).count()
        total_grades = Grade.objects.count()
        total_payments = FeePayment.objects.filter(payment_status='completed').count()
        total_fee_structures = FeeStructure.objects.count()
        total_lecturers = Lecturer.objects.filter(is_active=True).count()
        total_assignments = LecturerCourseAssignment.objects.filter(is_active=True).count()
        
        self.log(f"Active Students: {total_students}")
        self.log(f"Total Enrollments: {total_enrollments}")
        self.log(f"Total Grades: {total_grades}")
        self.log(f"Completed Payments: {total_payments}")
        self.log(f"Fee Structures: {total_fee_structures}")
        self.log(f"Active Lecturers: {total_lecturers}")
        self.log(f"Lecturer Assignments: {total_assignments}")
        
        # Payment summary
        total_fees_collected = FeePayment.objects.filter(
            payment_status='completed'
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        
        self.log(f"Total Fees Collected: KES {total_fees_collected:,.2f}")
        
        # Student distribution by year
        self.log("\nStudent Distribution by Academic Year:")
        for year in range(1, 9):
            count = Student.objects.filter(current_year=year, status='active').count()
            if count > 0:
                self.log(f"  Year {year}: {count} students")
        
        # Programme distribution
        self.log("\nStudent Distribution by Programme:")
        programmes = Programme.objects.filter(is_active=True)
        for programme in programmes:
            count = Student.objects.filter(programme=programme, status='active').count()
            if count > 0:
                self.log(f"  {programme.code}: {count} students")
        
        # Grade distribution
        self.log("\nGrade Distribution:")
        for grade_letter, _, _ in self.grade_options:
            count = Grade.objects.filter(grade=grade_letter).count()
            if count > 0:
                self.log(f"  {grade_letter}: {count} grades")
        
        self.log("="*50)