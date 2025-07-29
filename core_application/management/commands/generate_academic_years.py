from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from core_application.models import AcademicYear, Semester  # Adjust to your app name
from django.db import transaction

class Command(BaseCommand):
    help = "Generate academic years from 2021/2022 to 2025/2026 with 3 semesters each"

    def handle(self, *args, **kwargs):
        start_year = 2021
        end_year = 2025

        with transaction.atomic():
            for year in range(start_year, end_year + 1):
                next_year = year + 1
                year_str = f"{year}/{next_year}"

                start_date = date(year, 9, 1)
                end_date = date(next_year, 8, 31)

                academic_year, created = AcademicYear.objects.get_or_create(
                    year=year_str,
                    defaults={
                        'start_date': start_date,
                        'end_date': end_date,
                        'is_current': False
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created Academic Year: {year_str}"))

                    # Create 3 semesters
                    sem1_start = start_date
                    sem1_end = sem1_start + timedelta(days=100)

                    sem2_start = sem1_end + timedelta(days=7)
                    sem2_end = sem2_start + timedelta(days=100)

                    sem3_start = sem2_end + timedelta(days=7)
                    sem3_end = sem3_start + timedelta(days=100)

                    semesters = [
                        (1, sem1_start, sem1_end),
                        (2, sem2_start, sem2_end),
                        (3, sem3_start, sem3_end),
                    ]

                    for sem_number, s_start, s_end in semesters:
                        Semester.objects.create(
                            academic_year=academic_year,
                            semester_number=sem_number,
                            start_date=s_start,
                            end_date=s_end,
                            registration_start_date=s_start - timedelta(days=14),
                            registration_end_date=s_start + timedelta(days=14),
                            is_current=False
                        )

                    self.stdout.write(self.style.SUCCESS(f"  - 3 Semesters added for {year_str}"))

                else:
                    self.stdout.write(self.style.WARNING(f"Academic Year {year_str} already exists"))
