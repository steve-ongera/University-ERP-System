from django.core.management.base import BaseCommand
from core_application.models import Student, Semester, StudentReporting
from django.utils import timezone
from datetime import date


class Command(BaseCommand):
    help = "Report students to all applicable semesters based on programme duration and admission year."

    def handle(self, *args, **options):
        today = timezone.now().date()
        count = 0

        students = Student.objects.select_related('programme').all()
        total_students = students.count()
        self.stdout.write(f"🎓 Found {total_students} students to process...\n")

        for student in students:
            programme = student.programme
            admission_year = student.admission_date.year
            duration_years = programme.duration_years
            semesters_per_year = programme.semesters_per_year
            total_semesters = duration_years * semesters_per_year

            # Get valid semesters within the student's academic period
            valid_semesters = Semester.objects.filter(
                start_date__year__gte=admission_year,
                start_date__lte=date(admission_year + duration_years, 12, 31)
            ).order_by('start_date')[:total_semesters]

            for semester in valid_semesters:
                # Avoid duplicate reporting
                if not StudentReporting.objects.filter(student=student, semester=semester).exists():
                    StudentReporting.objects.create(
                        student=student,
                        semester=semester,
                        reporting_type='online',  # default type
                        status='approved',       # or 'pending' if approval is required
                    )
                    count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Reported {student.student_id} to {semester}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Finished: Created {count} reporting records for {total_students} students."
        ))
