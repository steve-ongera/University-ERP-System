import random
from django.core.management.base import BaseCommand
from core_application.models import Programme, Course, ProgrammeCourse

class Command(BaseCommand):
    help = 'Allocates 5 unique units to each semester in all programmes and across all years'

    def handle(self, *args, **kwargs):
        courses = list(Course.objects.filter(is_active=True))
        total_courses = len(courses)

        if total_courses < 5:
            self.stdout.write(self.style.ERROR("❌ Not enough courses available to allocate (minimum required: 5)."))
            return

        programmes = Programme.objects.filter(is_active=True)
        if not programmes.exists():
            self.stdout.write(self.style.ERROR("❌ No active programmes found."))
            return

        allocated_count = 0

        for programme in programmes:
            duration = programme.duration_years
            semesters = programme.semesters_per_year
            required_semesters = duration * semesters

            used_courses = set()

            for year in range(1, duration + 1):
                for semester in range(1, semesters + 1):
                    # Filter out already allocated courses for this programme-year-semester
                    existing_allocations = ProgrammeCourse.objects.filter(
                        programme=programme, year=year, semester=semester
                    ).values_list('course_id', flat=True)

                    available_courses = [course for course in courses if course.id not in used_courses and course.id not in existing_allocations]

                    if len(available_courses) < 5:
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Not enough available courses for {programme.code} Y{year}S{semester}. Skipping."
                        ))
                        continue

                    selected_courses = random.sample(available_courses, 5)

                    for course in selected_courses:
                        ProgrammeCourse.objects.create(
                            programme=programme,
                            course=course,
                            year=year,
                            semester=semester,
                            is_mandatory=True,
                            is_active=True
                        )
                        used_courses.add(course.id)
                        allocated_count += 1

                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Allocated 5 courses to {programme.code} Year {year} Semester {semester}"
                    ))

        self.stdout.write(self.style.SUCCESS(f"\n🎓 Total courses allocated: {allocated_count}"))
