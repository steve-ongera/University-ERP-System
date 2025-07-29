from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from core_application.models import User, Lecturer, Department
from faker import Faker
import random
import datetime

class Command(BaseCommand):
    help = 'Generate 100 fake lecturers with realistic data'

    def handle(self, *args, **options):
        fake = Faker()
        created = 0
        total = 100

        departments = list(Department.objects.all())
        if not departments:
            self.stdout.write(self.style.ERROR("No departments available. Please create some departments first."))
            return

        academic_ranks = [rank[0] for rank in Lecturer.ACADEMIC_RANKS]
        employment_types = [etype[0] for etype in Lecturer.EMPLOYMENT_TYPES]

        while created < total:
            try:
                gender = random.choice(['male', 'female'])
                first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
                last_name = fake.last_name()
                username = fake.unique.user_name()
                national_id = fake.unique.ssn()

                if User.objects.filter(username=username).exists():
                    continue

                user = User.objects.create(
                    username=username,
                    password=make_password('cp7kvt'),
                    first_name=first_name,
                    last_name=last_name,
                    email=fake.unique.email(),
                    user_type='lecturer',
                    gender=gender,
                    phone=fake.phone_number(),
                    address=fake.address(),
                    national_id=national_id,
                    date_of_birth=fake.date_of_birth(minimum_age=28, maximum_age=65),
                    is_active=True
                )

                department = random.choice(departments)
                employee_number = f"EMP{random.randint(10000, 99999)}"

                if Lecturer.objects.filter(employee_number=employee_number).exists():
                    continue

                joining_date = fake.date_between(start_date='-15y', end_date='today')
                contract_end_date = None
                employment_type = random.choice(employment_types)

                if employment_type in ['contract', 'visiting', 'adjunct']:
                    contract_end_date = joining_date + datetime.timedelta(days=random.randint(365, 1095))

                Lecturer.objects.create(
                    user=user,
                    employee_number=employee_number,
                    department=department,
                    academic_rank=random.choice(academic_ranks),
                    employment_type=employment_type,
                    highest_qualification=random.choice(['PhD', 'Masters', 'Bachelors']),
                    university_graduated=fake.company() + " University",
                    graduation_year=random.randint(1995, timezone.now().year - 3),
                    research_interests=fake.text(max_nb_chars=100),
                    publications=fake.text(max_nb_chars=200),
                    professional_registration=fake.bs().title(),
                    teaching_experience_years=random.randint(1, 35),
                    research_experience_years=random.randint(0, 30),
                    industry_experience_years=random.randint(0, 25),
                    salary=round(random.uniform(80000, 250000), 2),
                    joining_date=joining_date,
                    contract_end_date=contract_end_date,
                    office_location=fake.building_number() + " " + fake.street_name(),
                    office_phone=fake.phone_number(),
                    consultation_hours="Mon-Fri: 10am - 12pm",
                    is_active=True
                )

                created += 1
                self.stdout.write(self.style.SUCCESS(f"[{created}/{total}] Created lecturer: {username}"))

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created} lecturer accounts."))
