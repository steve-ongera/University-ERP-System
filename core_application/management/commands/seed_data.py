#!/usr/bin/env python
"""
University Student Enrollment, Fee Payment & Grade Assignment Seed Data Script
Usage: python manage.py shell < seed_data.py
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')  # Update with your project name
django.setup()

from core_application.models import (
    User, Student, Programme, Course, AcademicYear, Semester, 
    Enrollment, Grade, FeeStructure, FeePayment, ProgrammeCourse,
    Lecturer, LecturerCourseAssignment
)

class UniversityDataSeeder:
    def __init__(self):
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
        
    def log(self, message):
        """Simple logging function"""
        print(f"[{timezone.now().strftime('%H:%M:%S')}] {message}")
    

    
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
    
    def enroll_students_to_courses(self):
        """Enroll students to courses based on their programme and current academic status"""
        students = Student.objects.filter(status='active')
        
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
                            
                            # Create enrollment
                            enrollment = Enrollment.objects.create(
                                student=student,
                                course=programme_course.course,
                                semester=semester,
                                lecturer=lecturer_assignment.lecturer if lecturer_assignment else None,
                                is_active=True
                            )
                            
                            self.log(f"Enrolled {student.student_id} to {programme_course.course.code} for {semester}")
                            
                            # Create grade if semester is completed (not current or future)
                            if (target_year < self.current_year or 
                                (target_year == self.current_year and semester_num < student.current_semester)):
                                self.create_grade_for_enrollment(enrollment)
                    
                    # Handle fee payment for this semester
                    self.process_fee_payment(student, academic_year, student_year, semester_num)
    
    def create_grade_for_enrollment(self, enrollment):
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
            
            self.log(f"Created grade {grade_letter} for {enrollment.student.student_id} - {enrollment.course.code}")
    
    def process_fee_payment(self, student, academic_year, year, semester):
        """Process fee payment for a student's semester"""
        # Get existing fee structure
        fee_structure = FeeStructure.objects.filter(
            programme=student.programme,
            academic_year=academic_year,
            year=year,
            semester=semester
        ).first()
        
        if not fee_structure:
            self.log(f"No fee structure found for {student.programme.code} {academic_year.year} Y{year}S{semester}")
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
            
            self.log(f"Created fee payment for {student.student_id} - {receipt_number} - KES {amount_to_pay}")
    
    def generate_receipt_number(self, student, academic_year, semester):
        """Generate unique receipt number"""
        year_code = academic_year.year.split('/')[0][-2:]  # Last 2 digits of year
        student_code = student.student_id[-4:]  # Last 4 digits of student ID
        semester_code = f"S{semester}"
        random_code = random.randint(100, 999)
        
        return f"FEE{year_code}{student_code}{semester_code}{random_code}"
    
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
    
    def assign_lecturers_to_courses(self):
        """Assign lecturers to courses for current academic year"""
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_academic_year or not current_semester:
            self.log("No current academic year or semester found")
            return
        
        # Get all courses that need lecturer assignments
        courses = Course.objects.filter(is_active=True)
        lecturers = Lecturer.objects.filter(is_active=True)
        
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
                    
                    LecturerCourseAssignment.objects.create(
                        lecturer=lecturer,
                        course=course,
                        academic_year=current_academic_year,
                        semester=current_semester,
                        lecture_venue=f"LH-{random.randint(1, 20)}",
                        lecture_time=self.generate_lecture_time(),
                        is_active=True
                    )
                    
                    self.log(f"Assigned {lecturer.user.get_full_name()} to {course.code}")
    
    def generate_lecture_time(self):
        """Generate random lecture time"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        times = ['8:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00', '16:00-18:00']
        
        day = random.choice(days)
        time = random.choice(times)
        return f"{day} {time}"
    
    def update_student_academic_progress(self):
        """Update students' current year and semester based on their enrollments"""
        students = Student.objects.filter(status='active')
        
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
                    student.current_year = programme_course.year
                    student.current_semester = latest_enrollment.semester.semester_number
                    student.save()
                    
                    self.log(f"Updated {student.student_id} to Year {student.current_year}, Semester {student.current_semester}")
    
    def calculate_student_gpa(self):
        """Calculate cumulative GPA for all students"""
        students = Student.objects.filter(status='active')
        
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
                    student.cumulative_gpa = round(cumulative_gpa, 2)
                    student.total_credit_hours = total_credit_hours
                    student.save()
                    
                    self.log(f"Updated GPA for {student.student_id}: {student.cumulative_gpa}")
    
    def run_seeding(self):
        """Main function to run all seeding operations"""
        self.log("Starting university data seeding...")
        
        # Step 1: Assign lecturers to courses
        self.log("Assigning lecturers to courses...")
        self.assign_lecturers_to_courses()
        
        # Step 2: Enroll students to courses
        self.log("Enrolling students to courses...")
        self.enroll_students_to_courses()
        
        # Step 3: Update student academic progress
        self.log("Updating student academic progress...")
        self.update_student_academic_progress()
        
        # Step 4: Calculate GPAs
        self.log("Calculating student GPAs...")
        self.calculate_student_gpa()
        
        self.log("Seeding completed successfully!")
        
        # Print summary statistics
        self.print_summary()
    
    def print_summary(self):
        """Print summary of created data"""
        self.log("\n" + "="*50)
        self.log("SEEDING SUMMARY")
        self.log("="*50)
        
        total_students = Student.objects.filter(status='active').count()
        total_enrollments = Enrollment.objects.filter(is_active=True).count()
        total_grades = Grade.objects.count()
        total_payments = FeePayment.objects.filter(payment_status='completed').count()
        total_fee_structures = FeeStructure.objects.count()
        
        self.log(f"Active Students: {total_students}")
        self.log(f"Total Enrollments: {total_enrollments}")
        self.log(f"Total Grades: {total_grades}")
        self.log(f"Completed Payments: {total_payments}")
        self.log(f"Fee Structures: {total_fee_structures}")
        
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
        
        self.log("="*50)

# Additional utility functions for specific operations

def enroll_specific_student(student_id, programme_code=None):
    """Enroll a specific student (useful for testing)"""
    try:
        student = Student.objects.get(student_id=student_id)
        seeder = UniversityDataSeeder()
        
        # Process only this student
        students_backup = Student.objects.all()
        Student.objects.filter(student_id=student_id).update(status='active')
        
        seeder.enroll_students_to_courses()
        seeder.update_student_academic_progress()
        seeder.calculate_student_gpa()
        
        print(f"Successfully processed enrollments for student {student_id}")
        
    except Student.DoesNotExist:
        print(f"Student with ID {student_id} not found")

def create_sample_programme_courses():
    """Create sample programme-course mappings if none exist"""
    programmes = Programme.objects.filter(is_active=True)
    
    for programme in programmes:
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
                                ProgrammeCourse.objects.create(
                                    programme=programme,
                                    course=course,
                                    year=year,
                                    semester=semester,
                                    is_mandatory=True,
                                    is_active=True
                                )
                                print(f"Created programme-course mapping: {programme.code} - {course.code} Y{year}S{semester}")
                            
                            course_index += 1

def reset_student_data(student_id=None):
    """Reset enrollment and grade data for testing"""
    if student_id:
        student = Student.objects.get(student_id=student_id)
        Enrollment.objects.filter(student=student).delete()
        FeePayment.objects.filter(student=student).delete()
        print(f"Reset data for student {student_id}")
    else:
        response = input("Are you sure you want to reset ALL student enrollment and payment data? (yes/no): ")
        if response.lower() == 'yes':
            Enrollment.objects.all().delete()
            Grade.objects.all().delete()
            FeePayment.objects.all().delete()
            print("Reset all student data")

# Main execution
if __name__ == "__main__":
    import sys
    
    # Check if we have programme-course mappings
    if not ProgrammeCourse.objects.exists():
        print("No programme-course mappings found. Creating sample mappings...")
        create_sample_programme_courses()
    
    # Run the main seeding
    seeder = UniversityDataSeeder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "enroll_student" and len(sys.argv) > 2:
            student_id = sys.argv[2]
            enroll_specific_student(student_id)
        elif command == "reset" and len(sys.argv) > 2:
            student_id = sys.argv[2] if sys.argv[2] != "all" else None
            reset_student_data(student_id)
        elif command == "create_mappings":
            create_sample_programme_courses()
        else:
            print("Available commands:")
            print("  python seed_data.py enroll_student <student_id>")
            print("  python seed_data.py reset <student_id|all>")
            print("  python seed_data.py create_mappings")
    else:
        # Run full seeding
        seeder.run_seeding()

# Django imports fix
from django.db import models