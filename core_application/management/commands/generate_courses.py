import random
from django.core.management.base import BaseCommand
from core_application.models import Course, Department


class Command(BaseCommand):
    help = 'Generate 200 real university course units'

    def handle(self, *args, **kwargs):
        departments = list(Department.objects.all())
        if not departments:
            self.stdout.write(self.style.ERROR('❌ No departments found. Please create departments first.'))
            return

        course_types = [ct[0] for ct in Course.COURSE_TYPES]
        course_levels = [cl[0] for cl in Course.COURSE_LEVELS]

        # Expanded list of real-sounding courses
        course_data = [
            # Computer Science
            ('CSC', 'Introduction to Programming'),
            ('CSC', 'Data Structures and Algorithms'),
            ('CSC', 'Database Systems'),
            ('CSC', 'Operating Systems'),
            ('CSC', 'Computer Networks'),
            ('CSC', 'Software Engineering'),
            ('CSC', 'Web Development'),
            ('CSC', 'Mobile Application Development'),
            ('CSC', 'Machine Learning'),
            ('CSC', 'Artificial Intelligence'),
            ('CSC', 'Cloud Computing'),
            ('CSC', 'Cyber Security'),
            ('CSC', 'Digital Logic Design'),
            ('CSC', 'Human-Computer Interaction'),

            # Mathematics
            ('MAT', 'Calculus I'),
            ('MAT', 'Calculus II'),
            ('MAT', 'Linear Algebra'),
            ('MAT', 'Differential Equations'),
            ('MAT', 'Statistics and Probability'),
            ('MAT', 'Numerical Methods'),

            # Physics
            ('PHY', 'Classical Mechanics'),
            ('PHY', 'Electricity and Magnetism'),
            ('PHY', 'Modern Physics'),
            ('PHY', 'Quantum Physics'),
            ('PHY', 'Thermodynamics'),

            # Chemistry
            ('CHE', 'Organic Chemistry I'),
            ('CHE', 'Inorganic Chemistry I'),
            ('CHE', 'Physical Chemistry'),
            ('CHE', 'Analytical Chemistry'),
            ('CHE', 'Industrial Chemistry'),

            # Biology
            ('BIO', 'Cell Biology'),
            ('BIO', 'Genetics'),
            ('BIO', 'Microbiology'),
            ('BIO', 'Biotechnology'),

            # Business
            ('BUS', 'Principles of Management'),
            ('BUS', 'Organizational Behavior'),
            ('BUS', 'Financial Accounting'),
            ('BUS', 'Business Law'),
            ('BUS', 'Marketing Management'),
            ('BUS', 'Human Resource Management'),
            ('BUS', 'Entrepreneurship Development'),
            ('BUS', 'Business Ethics'),

            # Economics
            ('ECO', 'Principles of Microeconomics'),
            ('ECO', 'Principles of Macroeconomics'),
            ('ECO', 'Econometrics'),
            ('ECO', 'International Trade'),

            # Education
            ('EDU', 'Philosophy of Education'),
            ('EDU', 'Educational Psychology'),
            ('EDU', 'Curriculum Development'),
            ('EDU', 'Instructional Methods'),
            ('EDU', 'Educational Technology'),

            # Engineering
            ('CIV', 'Structural Analysis'),
            ('CIV', 'Construction Materials'),
            ('CIV', 'Geotechnical Engineering'),
            ('CIV', 'Transportation Engineering'),
            ('ELE', 'Circuit Theory'),
            ('ELE', 'Control Systems'),
            ('ELE', 'Power Electronics'),
            ('ELE', 'Electrical Machines'),
            ('MEC', 'Fluid Mechanics'),
            ('MEC', 'Thermodynamics'),
            ('MEC', 'Mechanical Design'),

            # Law
            ('LAW', 'Introduction to Law'),
            ('LAW', 'Constitutional Law'),
            ('LAW', 'Criminal Law'),
            ('LAW', 'Law of Torts'),
            ('LAW', 'Human Rights Law'),
            ('LAW', 'International Law'),

            # Medicine
            ('MED', 'Human Anatomy'),
            ('MED', 'Medical Biochemistry'),
            ('MED', 'Pathology'),
            ('MED', 'Pharmacology'),
            ('MED', 'Clinical Medicine'),

            # Nursing
            ('NUR', 'Foundations of Nursing'),
            ('NUR', 'Community Health Nursing'),
            ('NUR', 'Medical-Surgical Nursing'),
            ('NUR', 'Clinical Pharmacology'),

            # Agriculture
            ('AGR', 'Soil Science'),
            ('AGR', 'Agricultural Economics'),
            ('AGR', 'Crop Production'),
            ('AGR', 'Animal Science'),

            # Environmental Science
            ('ENV', 'Environmental Impact Assessment'),
            ('ENV', 'Waste Management'),
            ('ENV', 'Climate Change and Adaptation'),

            # Communication & Arts
            ('COM', 'Mass Communication'),
            ('COM', 'Media Ethics'),
            ('ART', 'Introduction to Drawing'),
            ('ART', 'Graphic Design'),

            # Theology & Religion
            ('THE', 'Introduction to Theology'),
            ('THE', 'Comparative Religion'),

            # Others
            ('GEN', 'Research Methods'),
            ('GEN', 'Project Management'),
            ('GEN', 'Development Studies'),
        ]

        created_codes = set()
        total_courses = 0
        course_index = 1

        while total_courses < 200:
            prefix, title = random.choice(course_data)
            level = random.choice(course_levels)
            course_code = f"{prefix}{level}{course_index:02d}"

            if course_code in created_codes or Course.objects.filter(code=course_code).exists():
                course_index += 1
                continue

            created_codes.add(course_code)
            department = random.choice(departments)
            course_type = random.choice(course_types)

            Course.objects.create(
                name=title,
                code=course_code,
                course_type=course_type,
                level=level,
                credit_hours=random.randint(2, 5),
                lecture_hours=random.randint(1, 3),
                tutorial_hours=random.randint(0, 2),
                practical_hours=random.randint(0, 3),
                field_work_hours=random.randint(0, 1),
                department=department,
                description=f"{title} covers fundamental and applied concepts.",
                learning_outcomes="1. Demonstrate understanding\n2. Apply knowledge in context\n3. Solve problems",
                assessment_methods="Continuous Assessment Tests (CATs), Assignments, Final Exams",
                recommended_textbooks="Author A. (Year). Book Title. Publisher.",
                is_active=True,
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Created: {title} [{course_code}]"))
            total_courses += 1
            course_index += 1

        self.stdout.write(self.style.SUCCESS(f"\n🎓 Successfully created {total_courses} real university courses."))
