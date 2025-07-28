from django.core.management.base import BaseCommand
from core_application.models import Faculty, Department, User
from datetime import date
import random

class Command(BaseCommand):
    help = 'Generate sample faculties and departments with dummy data'

    def handle(self, *args, **kwargs):
        sample_faculties = [
            {
                "name": "Faculty of Engineering",
                "code": "ENG",
                "description": "Engineering and Technology",
                "departments": [
                    ("Mechanical Engineering", "MECH"),
                    ("Electrical Engineering", "ELEC"),
                    ("Civil Engineering", "CIV"),
                    ("Computer Engineering", "COMP")
                ]
            },
            {
                "name": "Faculty of Medicine",
                "code": "MED",
                "description": "Health and Clinical Sciences",
                "departments": [
                    ("Pharmacy", "PHAR"),
                    ("Clinical Medicine", "CLIN"),
                    ("Public Health", "PUBH"),
                    ("Nursing", "NURS")
                ]
            },
            {
                "name": "Faculty of Business",
                "code": "BUS",
                "description": "Business, Finance and Management",
                "departments": [
                    ("Accounting", "ACC"),
                    ("Marketing", "MKT"),
                    ("Finance", "FIN"),
                    ("Business Administration", "BADM")
                ]
            },
            {
                "name": "Faculty of Education",
                "code": "EDU",
                "description": "Teacher training and pedagogy",
                "departments": [
                    ("Early Childhood Education", "ECE"),
                    ("Curriculum Studies", "CST"),
                    ("Educational Psychology", "EDPSY")
                ]
            },
            {
                "name": "Faculty of Agriculture",
                "code": "AGR",
                "description": "Agriculture and Food Sciences",
                "departments": [
                    ("Agronomy", "AGRO"),
                    ("Animal Science", "ANSC"),
                    ("Soil Science", "SOIL"),
                    ("Agricultural Economics", "AGEC")
                ]
            },
        ]

        deans_and_heads = list(User.objects.all())
        if not deans_and_heads:
            self.stdout.write(self.style.WARNING("No users found. Please create at least one user."))
            return

        for faculty_data in sample_faculties:
            faculty, created = Faculty.objects.get_or_create(
                code=faculty_data['code'],
                defaults={
                    'name': faculty_data['name'],
                    'description': faculty_data['description'],
                    'dean': random.choice(deans_and_heads),
                    'established_date': date(2000 + random.randint(0, 20), 1, 1),
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created faculty: {faculty.name}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Faculty already exists: {faculty.name}"))

            for dept_name, dept_code in faculty_data["departments"]:
                if Department.objects.filter(code=dept_code).exists():
                    self.stdout.write(self.style.NOTICE(f"Department {dept_code} exists. Skipping..."))
                    continue

                dept = Department.objects.create(
                    name=dept_name,
                    code=dept_code,
                    faculty=faculty,
                    head_of_department=random.choice(deans_and_heads),
                    description=f"{dept_name} under {faculty.name}",
                    established_date=date(2000 + random.randint(0, 20), 1, 1),
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"  ↳ Created department: {dept.name} ({dept.code})"))
