# core_application/management/commands/generate_staff.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from core_application.models import User, Staff, Department

class Command(BaseCommand):
    help = "Generate 20 random staff members with real-like data."

    def handle(self, *args, **kwargs):
        fake = Faker()
        password = "cp7kvt"
        staff_categories = [choice[0] for choice in Staff.STAFF_CATEGORIES]

        departments = list(Department.objects.all())
        if not departments:
            self.stdout.write(self.style.ERROR(
                "No departments found! Please add departments before generating staff."
            ))
            return

        for i in range(20):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}"

            # Create user
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=fake.email(),
                phone=fake.phone_number(),
                address=fake.address(),
                gender=random.choice(['male', 'female', 'other']),
                date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=60),
                national_id=str(fake.random_number(digits=8, fix_len=True)),
                user_type="staff",
                password=password
            )

            # Create staff profile
            Staff.objects.create(
                user=user,
                employee_number=f"EMP{random.randint(1000, 9999)}",
                staff_category=random.choice(staff_categories),
                department=random.choice(departments),
                designation=fake.job(),
                job_description=fake.text(max_nb_chars=200),
                salary=round(random.uniform(30000, 150000), 2),
                joining_date=fake.date_between(start_date='-10y', end_date='today'),
                office_location=fake.street_name(),
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS("Successfully generated 20 staff members!"))
