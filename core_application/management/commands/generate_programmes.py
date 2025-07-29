import random
from django.core.management.base import BaseCommand
from core_application.models import Programme, Department, Faculty
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Generate sample academic programmes for each department'

    def handle(self, *args, **kwargs):
        programme_types = [
            ('bachelor', 'Bachelor Degree'),
            ('master', 'Master Degree'),
            ('phd', 'PhD'),
            ('diploma', 'Diploma'),
            ('certificate', 'Certificate'),
            ('postgraduate_diploma', 'Postgraduate Diploma'),
        ]

        programme_modes = [
            'full_time',
            'part_time',
            'distance_learning',
            'online',
            'evening',
            'weekend',
        ]

        sample_names = {
            'Engineering': ['Civil Engineering', 'Mechanical Engineering', 'Electrical Engineering', 'Mechatronics'],
            'Medicine': ['General Medicine', 'Pharmacy', 'Nursing Science', 'Medical Lab Science'],
            'Business': ['Business Administration', 'Marketing', 'Human Resource', 'Accounting'],
            'Education': ['Education Arts', 'Education Science', 'Early Childhood Education', 'Special Needs Education'],
            'ICT': ['Computer Science', 'Information Technology', 'Data Science', 'Cybersecurity'],
        }

        departments = Department.objects.select_related('faculty').all()

        if not departments:
            self.stdout.write(self.style.ERROR("No departments found. Please run department generation first."))
            return

        counter = 0

        for dept in departments:
            faculty = dept.faculty
            sample_key = next((key for key in sample_names if key.lower() in dept.name.lower()), 'ICT')
            base_names = sample_names.get(sample_key, sample_names['ICT'])

            for name in base_names[:random.randint(2, 4)]:
                code = f"{dept.code.upper()[:3]}-{random.randint(100, 999)}"
                if Programme.objects.filter(code=code).exists():
                    continue

                programme = Programme.objects.create(
                    name=name,
                    code=code,
                    programme_type=random.choice(programme_types)[0],
                    study_mode=random.choice(programme_modes),
                    department=dept,
                    faculty=faculty,
                    duration_years=random.randint(3, 6),
                    semesters_per_year=2,
                    total_semesters=random.randint(6, 12),
                    credit_hours_required=random.randint(120, 180),
                    description=f"A comprehensive {name} programme.",
                    entry_requirements="Minimum KCSE C+ or its equivalent.",
                    career_prospects=f"Graduates can work in various sectors related to {name}.",
                    is_active=True,
                )
                counter += 1
                self.stdout.write(self.style.SUCCESS(f"Created programme: {programme}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully created {counter} programmes."))
