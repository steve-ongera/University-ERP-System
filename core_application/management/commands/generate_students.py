from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from core_application.models import User, Student, Programme
from faker import Faker
import random
import datetime

class Command(BaseCommand):
    help = 'Generate 300 student users for each year from 2021 to 2025 with realistic data'

    def handle(self, *args, **options):
        fake = Faker()
        created = 0

        programmes = list(Programme.objects.all())

        if not programmes:
            self.stdout.write(self.style.ERROR("No programmes available. Please create some programmes first."))
            return

        years = range(2021, 2026)  # 2021 to 2025
        total_to_create = 300 * len(years)

        for year in years:
            count_for_year = 0
            while count_for_year < 300:
                try:
                    number = random.randint(1000, 9999)
                    prefix = random.choice(['EC211', 'CT211'])

                    username = f"{prefix}/{number:04d}/{year}"
                    student_id = f"{prefix}-{number:04d}-{year}"

                    if User.objects.filter(username=username).exists():
                        continue

                    gender = random.choice(['male', 'female'])
                    first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
                    last_name = fake.last_name()

                    user = User.objects.create(
                        username=username,
                        password=make_password('cp7kvt'),
                        first_name=first_name,
                        last_name=last_name,
                        email=fake.unique.email(),
                        user_type='student',
                        gender=gender,
                        phone=fake.phone_number(),
                        address=fake.address(),
                        national_id=fake.unique.ssn(),
                        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=25),
                        is_active=True
                    )

                    programme = random.choice(programmes)
                    admission_date = fake.date_between(
                        start_date=datetime.date(year, 1, 1),
                        end_date=datetime.date(year, 12, 31)
                    )
                    expected_graduation = timezone.datetime(year + programme.duration_years, 6, 30).date()

                    Student.objects.create(
                        user=user,
                        student_id=student_id,
                        programme=programme,
                        current_year=min(4, (timezone.now().year - year) + 1),
                        current_semester=random.choice([1, 2]),
                        admission_date=admission_date,
                        admission_type=random.choice([choice[0] for choice in Student.ADMISSION_TYPES]),
                        sponsor_type=random.choice([choice[0] for choice in Student.SPONSOR_TYPES]),
                        status='active',
                        entry_qualification=random.choice(['KCSE', 'Diploma', 'A-Level']),
                        entry_points=round(random.uniform(50.0, 84.0), 2),
                        expected_graduation_date=expected_graduation,
                        cumulative_gpa=round(random.uniform(2.0, 4.0), 2),
                        total_credit_hours=random.randint(30, 120),
                        guardian_name=fake.name(),
                        guardian_phone=fake.phone_number(),
                        guardian_relationship=random.choice(['Father', 'Mother', 'Uncle', 'Aunt', 'Guardian']),
                        guardian_address=fake.address(),
                        emergency_contact=fake.phone_number(),
                        blood_group=random.choice(['A+', 'B+', 'AB+', 'O+', 'O-', 'B-', 'A-']),
                        medical_conditions=fake.sentence(nb_words=4),
                        accommodation_type=random.choice(['On-campus', 'Off-campus']),
                    )

                    created += 1
                    count_for_year += 1
                    self.stdout.write(self.style.SUCCESS(f"[{created}/{total_to_create}] Created: {username}"))

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created} student accounts."))
