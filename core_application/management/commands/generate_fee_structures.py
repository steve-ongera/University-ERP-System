from django.core.management.base import BaseCommand
from core_application.models import Programme, AcademicYear, FeeStructure
from django.db import IntegrityError

from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Generate Fee Structures for all Programmes and Academic Years'

    def handle(self, *args, **kwargs):
        programmes = Programme.objects.all()
        academic_years = AcademicYear.objects.all()

        if not programmes.exists() or not academic_years.exists():
            self.stdout.write(self.style.ERROR("No programmes or academic years found."))
            return

        count_created = 0
        count_skipped = 0

        for programme in programmes:
            for academic_year in academic_years:
                for year in range(1, programme.duration_years + 1):
                    for semester in range(1, programme.semesters_per_year + 1):
                        try:
                            fs, created = FeeStructure.objects.get_or_create(
                                programme=programme,
                                academic_year=academic_year,
                                year=year,
                                semester=semester,
                                defaults={
                                    'tuition_fee': Decimal(random.randint(30000, 70000)),
                                    'registration_fee': Decimal(1500),
                                    'examination_fee': Decimal(2000),
                                    'library_fee': Decimal(1000),
                                    'laboratory_fee': Decimal(2500),
                                    'fieldwork_fee': Decimal(3000),
                                    'technology_fee': Decimal(1000),
                                    'accommodation_fee': Decimal(6000),
                                    'meals_fee': Decimal(4000),
                                    'medical_fee': Decimal(1200),
                                    'insurance_fee': Decimal(800),
                                    'student_union_fee': Decimal(500),
                                    'sports_fee': Decimal(600),
                                    'graduation_fee': Decimal(0 if year < programme.duration_years else 5000),
                                    'other_fees': Decimal(0),
                                    'government_subsidy': Decimal(0),
                                    'scholarship_amount': Decimal(0)
                                }
                            )
                            if created:
                                count_created += 1
                            else:
                                count_skipped += 1
                        except IntegrityError:
                            count_skipped += 1
                            continue

        self.stdout.write(self.style.SUCCESS(f"✅ Fee structures generated: {count_created}"))
        self.stdout.write(self.style.WARNING(f"⏭️ Fee structures skipped (already existed): {count_skipped}"))
