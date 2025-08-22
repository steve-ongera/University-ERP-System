# Medical Programmes Course Data for Django Models
# This data can be used to populate your database via fixtures or management commands

from django.core.management.base import BaseCommand
from core_application.models import Programme, Course, ProgrammeCourse, Department, Faculty

class Command(BaseCommand):
    help = 'Create medical programmes with allocated courses'

    def handle(self, *args, **options):
        # Assume Faculty and Department already exist
        # You'll need to replace these with actual IDs from your database
        faculty = Faculty.objects.get(name="Faculty of Medicine")
        dept_medicine = Department.objects.get(name="Medicine & Surgery Department")
        dept_lab = Department.objects.get(name="Medical Laboratory Department") 
        dept_community = Department.objects.get(name="Community Health Department")

        # Create Programmes
        medicine_surgery = Programme.objects.create(
            name="Bachelor of Medicine and Surgery",
            code="MBCHB",
            programme_type="bachelor",
            department=dept_medicine,
            faculty=faculty,
            duration_years=3,
            semesters_per_year=3,
            total_semesters=9,
            credit_hours_required=180,
            entry_requirements="A-level with Biology, Chemistry, Physics/Mathematics"
        )

        medical_lab = Programme.objects.create(
            name="Diploma in Medical Laboratory Technology",
            code="DMLT",
            programme_type="diploma",
            department=dept_lab,
            faculty=faculty,
            duration_years=2,
            semesters_per_year=3,
            total_semesters=6,
            credit_hours_required=120,
            entry_requirements="O-level with Biology, Chemistry, Mathematics"
        )

        community_health = Programme.objects.create(
            name="Bachelor of Community Health",
            code="BCH",
            programme_type="bachelor",
            department=dept_community,
            faculty=faculty,
            duration_years=4,
            semesters_per_year=2,
            total_semesters=8,
            credit_hours_required=160,
            entry_requirements="A-level with Biology, Chemistry, Mathematics"
        )

        # MEDICINE AND SURGERY COURSES (3 Years, 3 Semesters per year)
        medicine_courses = [
            # YEAR 1
            # Semester 1
            {"name": "Human Anatomy I", "code": "MED101", "level": "100", "credits": 6, "year": 1, "semester": 1},
            {"name": "Human Physiology I", "code": "MED102", "level": "100", "credits": 5, "year": 1, "semester": 1},
            {"name": "Medical Biochemistry I", "code": "MED103", "level": "100", "credits": 4, "year": 1, "semester": 1},
            {"name": "Medical Ethics & Communication", "code": "MED104", "level": "100", "credits": 3, "year": 1, "semester": 1},
            {"name": "Medical Statistics", "code": "MED105", "level": "100", "credits": 2, "year": 1, "semester": 1},
            
            # Semester 2
            {"name": "Human Anatomy II", "code": "MED106", "level": "100", "credits": 6, "year": 1, "semester": 2},
            {"name": "Human Physiology II", "code": "MED107", "level": "100", "credits": 5, "year": 1, "semester": 2},
            {"name": "Medical Biochemistry II", "code": "MED108", "level": "100", "credits": 4, "year": 1, "semester": 2},
            {"name": "Histology & Embryology", "code": "MED109", "level": "100", "credits": 4, "year": 1, "semester": 2},
            {"name": "Medical Microbiology I", "code": "MED110", "level": "100", "credits": 3, "year": 1, "semester": 2},
            
            # Semester 3
            {"name": "Pathology I", "code": "MED111", "level": "100", "credits": 5, "year": 1, "semester": 3},
            {"name": "Pharmacology I", "code": "MED112", "level": "100", "credits": 4, "year": 1, "semester": 3},
            {"name": "Medical Microbiology II", "code": "MED113", "level": "100", "credits": 4, "year": 1, "semester": 3},
            {"name": "Immunology", "code": "MED114", "level": "100", "credits": 3, "year": 1, "semester": 3},
            {"name": "Research Methodology", "code": "MED115", "level": "100", "credits": 2, "year": 1, "semester": 3},

            # YEAR 2
            # Semester 1
            {"name": "Internal Medicine I", "code": "MED201", "level": "200", "credits": 6, "year": 2, "semester": 1},
            {"name": "Surgery I", "code": "MED202", "level": "200", "credits": 6, "year": 2, "semester": 1},
            {"name": "Pathology II", "code": "MED203", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Pharmacology II", "code": "MED204", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Clinical Skills I", "code": "MED205", "level": "200", "credits": 2, "year": 2, "semester": 1},
            
            # Semester 2
            {"name": "Internal Medicine II", "code": "MED206", "level": "200", "credits": 6, "year": 2, "semester": 2},
            {"name": "Surgery II", "code": "MED207", "level": "200", "credits": 6, "year": 2, "semester": 2},
            {"name": "Obstetrics & Gynecology I", "code": "MED208", "level": "200", "credits": 4, "year": 2, "semester": 2},
            {"name": "Pediatrics I", "code": "MED209", "level": "200", "credits": 4, "year": 2, "semester": 2},
            {"name": "Clinical Skills II", "code": "MED210", "level": "200", "credits": 2, "year": 2, "semester": 2},
            
            # Semester 3
            {"name": "Psychiatry", "code": "MED211", "level": "200", "credits": 4, "year": 2, "semester": 3},
            {"name": "Radiology", "code": "MED212", "level": "200", "credits": 3, "year": 2, "semester": 3},
            {"name": "Anesthesiology", "code": "MED213", "level": "200", "credits": 3, "year": 2, "semester": 3},
            {"name": "Emergency Medicine", "code": "MED214", "level": "200", "credits": 4, "year": 2, "semester": 3},
            {"name": "Medical Imaging", "code": "MED215", "level": "200", "credits": 3, "year": 2, "semester": 3},

            # YEAR 3
            # Semester 1
            {"name": "Clinical Medicine I", "code": "MED301", "level": "300", "credits": 8, "year": 3, "semester": 1},
            {"name": "Advanced Surgery I", "code": "MED302", "level": "300", "credits": 6, "year": 3, "semester": 1},
            {"name": "Obstetrics & Gynecology II", "code": "MED303", "level": "300", "credits": 4, "year": 3, "semester": 1},
            {"name": "Pediatrics II", "code": "MED304", "level": "300", "credits": 4, "year": 3, "semester": 1},
            
            # Semester 2
            {"name": "Clinical Medicine II", "code": "MED305", "level": "300", "credits": 8, "year": 3, "semester": 2},
            {"name": "Advanced Surgery II", "code": "MED306", "level": "300", "credits": 6, "year": 3, "semester": 2},
            {"name": "Orthopedics", "code": "MED307", "level": "300", "credits": 4, "year": 3, "semester": 2},
            {"name": "Ophthalmology", "code": "MED308", "level": "300", "credits": 3, "year": 3, "semester": 2},
            {"name": "ENT (Otolaryngology)", "code": "MED309", "level": "300", "credits": 3, "year": 3, "semester": 2},
            
            # Semester 3
            {"name": "Clinical Internship", "code": "MED310", "level": "300", "credits": 10, "year": 3, "semester": 3, "type": "internship"},
            {"name": "Medical Research Project", "code": "MED311", "level": "300", "credits": 6, "year": 3, "semester": 3, "type": "capstone"},
            {"name": "Medical Law & Ethics", "code": "MED312", "level": "300", "credits": 2, "year": 3, "semester": 3},
        ]

        # MEDICAL LABORATORY TECHNOLOGY COURSES (2 Years, 3 Semesters per year)
        lab_courses = [
            # YEAR 1
            # Semester 1
            {"name": "Basic Medical Laboratory Science", "code": "MLT101", "level": "100", "credits": 4, "year": 1, "semester": 1},
            {"name": "Human Anatomy & Physiology", "code": "MLT102", "level": "100", "credits": 4, "year": 1, "semester": 1},
            {"name": "General Chemistry", "code": "MLT103", "level": "100", "credits": 3, "year": 1, "semester": 1},
            {"name": "Medical Microbiology", "code": "MLT104", "level": "100", "credits": 4, "year": 1, "semester": 1},
            {"name": "Laboratory Safety & Quality Control", "code": "MLT105", "level": "100", "credits": 3, "year": 1, "semester": 1},
            
            # Semester 2
            {"name": "Clinical Hematology", "code": "MLT106", "level": "100", "credits": 5, "year": 1, "semester": 2},
            {"name": "Clinical Chemistry", "code": "MLT107", "level": "100", "credits": 5, "year": 1, "semester": 2},
            {"name": "Pathology", "code": "MLT108", "level": "100", "credits": 4, "year": 1, "semester": 2},
            {"name": "Immunology & Serology", "code": "MLT109", "level": "100", "credits": 4, "year": 1, "semester": 2},
            {"name": "Laboratory Equipment & Maintenance", "code": "MLT110", "level": "100", "credits": 2, "year": 1, "semester": 2},
            
            # Semester 3
            {"name": "Clinical Parasitology", "code": "MLT111", "level": "100", "credits": 4, "year": 1, "semester": 3},
            {"name": "Histopathology Techniques", "code": "MLT112", "level": "100", "credits": 4, "year": 1, "semester": 3},
            {"name": "Blood Banking", "code": "MLT113", "level": "100", "credits": 4, "year": 1, "semester": 3},
            {"name": "Laboratory Information Systems", "code": "MLT114", "level": "100", "credits": 3, "year": 1, "semester": 3},
            {"name": "Biostatistics", "code": "MLT115", "level": "100", "credits": 2, "year": 1, "semester": 3},

            # YEAR 2
            # Semester 1
            {"name": "Advanced Hematology", "code": "MLT201", "level": "200", "credits": 5, "year": 2, "semester": 1},
            {"name": "Advanced Clinical Chemistry", "code": "MLT202", "level": "200", "credits": 5, "year": 2, "semester": 1},
            {"name": "Advanced Microbiology", "code": "MLT203", "level": "200", "credits": 5, "year": 2, "semester": 1},
            {"name": "Molecular Diagnostics", "code": "MLT204", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Laboratory Management", "code": "MLT205", "level": "200", "credits": 3, "year": 2, "semester": 1},
            
            # Semester 2
            {"name": "Cytology & Cytogenetics", "code": "MLT206", "level": "200", "credits": 4, "year": 2, "semester": 2},
            {"name": "Clinical Biochemistry", "code": "MLT207", "level": "200", "credits": 4, "year": 2, "semester": 2},
            {"name": "Medical Laboratory Ethics", "code": "MLT208", "level": "200", "credits": 2, "year": 2, "semester": 2},
            {"name": "Research Methods in Laboratory Science", "code": "MLT209", "level": "200", "credits": 3, "year": 2, "semester": 2},
            {"name": "Clinical Placement I", "code": "MLT210", "level": "200", "credits": 6, "year": 2, "semester": 2, "type": "practicum"},
            
            # Semester 3
            {"name": "Clinical Placement II", "code": "MLT211", "level": "200", "credits": 8, "year": 2, "semester": 3, "type": "practicum"},
            {"name": "Laboratory Research Project", "code": "MLT212", "level": "200", "credits": 6, "year": 2, "semester": 3, "type": "capstone"},
            {"name": "Professional Development", "code": "MLT213", "level": "200", "credits": 2, "year": 2, "semester": 3},
            {"name": "Quality Assurance in Laboratory", "code": "MLT214", "level": "200", "credits": 4, "year": 2, "semester": 3},
        ]

        # COMMUNITY HEALTH COURSES (4 Years, 2 Semesters per year)
        community_health_courses = [
            # YEAR 1
            # Semester 1
            {"name": "Introduction to Community Health", "code": "CHE101", "level": "100", "credits": 3, "year": 1, "semester": 1},
            {"name": "Human Anatomy & Physiology", "code": "CHE102", "level": "100", "credits": 4, "year": 1, "semester": 1},
            {"name": "Public Health Principles", "code": "CHE103", "level": "100", "credits": 3, "year": 1, "semester": 1},
            {"name": "Health Education Methods", "code": "CHE104", "level": "100", "credits": 3, "year": 1, "semester": 1},
            {"name": "Basic Medical Sciences", "code": "CHE105", "level": "100", "credits": 4, "year": 1, "semester": 1},
            {"name": "Communication Skills", "code": "CHE106", "level": "100", "credits": 2, "year": 1, "semester": 1},
            
            # Semester 2
            {"name": "Epidemiology I", "code": "CHE107", "level": "100", "credits": 4, "year": 1, "semester": 2},
            {"name": "Biostatistics", "code": "CHE108", "level": "100", "credits": 3, "year": 1, "semester": 2},
            {"name": "Environmental Health", "code": "CHE109", "level": "100", "credits": 4, "year": 1, "semester": 2},
            {"name": "Nutrition & Dietetics", "code": "CHE110", "level": "100", "credits": 3, "year": 1, "semester": 2},
            {"name": "Community Development", "code": "CHE111", "level": "100", "credits": 3, "year": 1, "semester": 2},
            {"name": "First Aid & Basic Life Support", "code": "CHE112", "level": "100", "credits": 2, "year": 1, "semester": 2},

            # YEAR 2
            # Semester 1
            {"name": "Epidemiology II", "code": "CHE201", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Health Promotion & Disease Prevention", "code": "CHE202", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Maternal & Child Health", "code": "CHE203", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Infectious Disease Control", "code": "CHE204", "level": "200", "credits": 4, "year": 2, "semester": 1},
            {"name": "Health Systems & Policy", "code": "CHE205", "level": "200", "credits": 3, "year": 2, "semester": 1},
            {"name": "Community Health Assessment", "code": "CHE206", "level": "200", "credits": 3, "year": 2, "semester": 1},
            
            # Semester 2
            {"name": "Non-Communicable Diseases", "code": "CHE207", "level": "200", "credits": 4, "year": 2, "semester": 2},
            {"name": "Mental Health in Community", "code": "CHE208", "level": "200", "credits": 3, "year": 2, "semester": 2},
            {"name": "Occupational Health & Safety", "code": "CHE209", "level": "200", "credits": 3, "year": 2, "semester": 2},
            {"name": "Health Economics", "code": "CHE210", "level": "200", "credits": 3, "year": 2, "semester": 2},
            {"name": "Research Methods I", "code": "CHE211", "level": "200", "credits": 3, "year": 2, "semester": 2},
            {"name": "Community Fieldwork I", "code": "CHE212", "level": "200", "credits": 4, "year": 2, "semester": 2, "type": "practicum"},

            # YEAR 3
            # Semester 1
            {"name": "Global Health", "code": "CHE301", "level": "300", "credits": 3, "year": 3, "semester": 1},
            {"name": "Health Program Planning & Evaluation", "code": "CHE302", "level": "300", "credits": 4, "year": 3, "semester": 1},
            {"name": "Disaster Management & Emergency Preparedness", "code": "CHE303", "level": "300", "credits": 3, "year": 3, "semester": 1},
            {"name": "Health Communication", "code": "CHE304", "level": "300", "credits": 3, "year": 3, "semester": 1},
            {"name": "Community Health Nursing", "code": "CHE305", "level": "300", "credits": 4, "year": 3, "semester": 1},
            {"name": "Research Methods II", "code": "CHE306", "level": "300", "credits": 3, "year": 3, "semester": 1},
            
            # Semester 2
            {"name": "Health Informatics", "code": "CHE307", "level": "300", "credits": 3, "year": 3, "semester": 2},
            {"name": "Community Health Leadership", "code": "CHE308", "level": "300", "credits": 3, "year": 3, "semester": 2},
            {"name": "Health Behavior Change", "code": "CHE309", "level": "300", "credits": 3, "year": 3, "semester": 2},
            {"name": "Reproductive Health", "code": "CHE310", "level": "300", "credits": 3, "year": 3, "semester": 2},
            {"name": "Community Fieldwork II", "code": "CHE311", "level": "300", "credits": 6, "year": 3, "semester": 2, "type": "practicum"},
            {"name": "Health Ethics & Law", "code": "CHE312", "level": "300", "credits": 2, "year": 3, "semester": 2},

            # YEAR 4
            # Semester 1
            {"name": "Advanced Community Health Practice", "code": "CHE401", "level": "400", "credits": 5, "year": 4, "semester": 1},
            {"name": "Health Quality Improvement", "code": "CHE402", "level": "400", "credits": 3, "year": 4, "semester": 1},
            {"name": "Community Health Internship I", "code": "CHE403", "level": "400", "credits": 8, "year": 4, "semester": 1, "type": "internship"},
            {"name": "Research Project I", "code": "CHE404", "level": "400", "credits": 4, "year": 4, "semester": 1, "type": "capstone"},
            
            # Semester 2
            {"name": "Community Health Management", "code": "CHE405", "level": "400", "credits": 4, "year": 4, "semester": 2},
            {"name": "Health Policy Analysis", "code": "CHE406", "level": "400", "credits": 3, "year": 4, "semester": 2},
            {"name": "Community Health Internship II", "code": "CHE407", "level": "400", "credits": 8, "year": 4, "semester": 2, "type": "internship"},
            {"name": "Research Project II", "code": "CHE408", "level": "400", "credits": 5, "year": 4, "semester": 2, "type": "capstone"},
        ]

        # Create courses and allocate to programmes
        def create_and_allocate_courses(programme, courses_data):
            for course_data in courses_data:
                # Create course
                course, created = Course.objects.get_or_create(
                    code=course_data['code'],
                    defaults={
                        'name': course_data['name'],
                        'level': course_data['level'],
                        'credit_hours': course_data['credits'],
                        'course_type': course_data.get('type', 'core'),
                        'department': programme.department,
                        'lecture_hours': 30,
                        'practical_hours': 20 if 'practical' in course_data['name'].lower() else 10,
                        'tutorial_hours': 10,
                    }
                )
                
                # Allocate course to programme
                ProgrammeCourse.objects.get_or_create(
                    programme=programme,
                    course=course,
                    year=course_data['year'],
                    semester=course_data['semester'],
                    defaults={'is_mandatory': True}
                )

        # Execute course creation and allocation
        create_and_allocate_courses(medicine_surgery, medicine_courses)
        create_and_allocate_courses(medical_lab, lab_courses)
        create_and_allocate_courses(community_health, community_health_courses)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created medical programmes with allocated courses:\n'
                f'- {medicine_surgery.name}: {len(medicine_courses)} courses\n'
                f'- {medical_lab.name}: {len(lab_courses)} courses\n'
                f'- {community_health.name}: {len(community_health_courses)} courses'
            )
        )