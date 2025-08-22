# Fee Structure Creation for Medical Programmes (2021/2022 to 2025/2026)
# This management command creates fee structures for all three medical programmes

from django.core.management.base import BaseCommand
from core_application.models import Programme, AcademicYear, FeeStructure
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create fee structures for medical programmes from 2021/2022 to 2025/2026'

    def handle(self, *args, **options):
        # Get the programmes
        try:
            medicine_surgery = Programme.objects.get(code="MBCHB")
            medical_lab = Programme.objects.get(code="DMLT")
            community_health = Programme.objects.get(code="BCH")
        except Programme.DoesNotExist:
            self.stdout.write(self.style.ERROR('Programmes not found. Please create them first.'))
            return

        # Academic years to process
        academic_years = ['2021/2022', '2022/2023', '2023/2024', '2024/2025', '2025/2026']
        
        # Fee structures for each programme
        medicine_fees = {
            # Medicine & Surgery fees (higher due to clinical training)
            'tuition_fee': Decimal('180000.00'),
            'registration_fee': Decimal('5000.00'),
            'examination_fee': Decimal('8000.00'),
            'library_fee': Decimal('3000.00'),
            'laboratory_fee': Decimal('15000.00'),  # High lab costs for medical training
            'fieldwork_fee': Decimal('12000.00'),   # Clinical attachments
            'technology_fee': Decimal('4000.00'),
            'accommodation_fee': Decimal('45000.00'),
            'meals_fee': Decimal('36000.00'),
            'medical_fee': Decimal('2500.00'),
            'insurance_fee': Decimal('1500.00'),
            'student_union_fee': Decimal('1000.00'),
            'sports_fee': Decimal('1000.00'),
            'graduation_fee': Decimal('0.00'),  # Only final semester
            'other_fees': Decimal('5000.00'),
            'government_subsidy': Decimal('120000.00'),  # High government support for medicine
            'scholarship_amount': Decimal('0.00'),
        }

        lab_tech_fees = {
            # Medical Lab Technology fees (moderate, diploma level)
            'tuition_fee': Decimal('85000.00'),
            'registration_fee': Decimal('4000.00'),
            'examination_fee': Decimal('5000.00'),
            'library_fee': Decimal('2500.00'),
            'laboratory_fee': Decimal('12000.00'),  # High lab component
            'fieldwork_fee': Decimal('8000.00'),    # Clinical placements
            'technology_fee': Decimal('3000.00'),
            'accommodation_fee': Decimal('40000.00'),
            'meals_fee': Decimal('32000.00'),
            'medical_fee': Decimal('2000.00'),
            'insurance_fee': Decimal('1200.00'),
            'student_union_fee': Decimal('800.00'),
            'sports_fee': Decimal('800.00'),
            'graduation_fee': Decimal('0.00'),  # Only final semester
            'other_fees': Decimal('3500.00'),
            'government_subsidy': Decimal('55000.00'),
            'scholarship_amount': Decimal('0.00'),
        }

        community_health_fees = {
            # Community Health fees (bachelor level, field-oriented)
            'tuition_fee': Decimal('120000.00'),
            'registration_fee': Decimal('4500.00'),
            'examination_fee': Decimal('6000.00'),
            'library_fee': Decimal('2800.00'),
            'laboratory_fee': Decimal('6000.00'),
            'fieldwork_fee': Decimal('10000.00'),   # Community fieldwork
            'technology_fee': Decimal('3500.00'),
            'accommodation_fee': Decimal('42000.00'),
            'meals_fee': Decimal('34000.00'),
            'medical_fee': Decimal('2200.00'),
            'insurance_fee': Decimal('1300.00'),
            'student_union_fee': Decimal('900.00'),
            'sports_fee': Decimal('900.00'),
            'graduation_fee': Decimal('0.00'),  # Only final semester
            'other_fees': Decimal('4000.00'),
            'government_subsidy': Decimal('75000.00'),
            'scholarship_amount': Decimal('0.00'),
        }

        def create_fee_structure(programme, year_str, year_num, semester_num, fee_data):
            try:
                academic_year = AcademicYear.objects.get(year=year_str)
                
                # Add graduation fee for final semester
                final_fee_data = fee_data.copy()
                is_final_semester = False
                
                if programme.code == "MBCHB" and year_num == 3 and semester_num == 3:  # Final semester
                    final_fee_data['graduation_fee'] = Decimal('15000.00')
                    is_final_semester = True
                elif programme.code == "DMLT" and year_num == 2 and semester_num == 3:  # Final semester
                    final_fee_data['graduation_fee'] = Decimal('12000.00')
                    is_final_semester = True
                elif programme.code == "BCH" and year_num == 4 and semester_num == 2:  # Final semester
                    final_fee_data['graduation_fee'] = Decimal('15000.00')
                    is_final_semester = True

                fee_structure, created = FeeStructure.objects.get_or_create(
                    programme=programme,
                    academic_year=academic_year,
                    year=year_num,
                    semester=semester_num,
                    defaults=final_fee_data
                )
                
                if created:
                    status = "CREATED"
                    if is_final_semester:
                        status += " (with graduation fee)"
                else:
                    status = "EXISTS"
                
                return f"  Y{year_num}S{semester_num}: {status}"
                
            except AcademicYear.DoesNotExist:
                return f"  Y{year_num}S{semester_num}: ERROR - Academic year {year_str} not found"

        # Process each academic year
        for year_str in academic_years:
            self.stdout.write(f"\nProcessing Academic Year: {year_str}")
            self.stdout.write("=" * 50)
            
            # MEDICINE & SURGERY (3 years, 3 semesters each)
            self.stdout.write(f"\n{medicine_surgery.name} ({medicine_surgery.code}):")
            for year in range(1, 4):  # Years 1-3
                for semester in range(1, 4):  # Semesters 1-3
                    result = create_fee_structure(medicine_surgery, year_str, year, semester, medicine_fees)
                    self.stdout.write(result)
            
            # MEDICAL LAB TECHNOLOGY (2 years, 3 semesters each)
            self.stdout.write(f"\n{medical_lab.name} ({medical_lab.code}):")
            for year in range(1, 3):  # Years 1-2
                for semester in range(1, 4):  # Semesters 1-3
                    result = create_fee_structure(medical_lab, year_str, year, semester, lab_tech_fees)
                    self.stdout.write(result)
            
            # COMMUNITY HEALTH (4 years, 2 semesters each)
            self.stdout.write(f"\n{community_health.name} ({community_health.code}):")
            for year in range(1, 5):  # Years 1-4
                for semester in range(1, 3):  # Semesters 1-2
                    result = create_fee_structure(community_health, year_str, year, semester, community_health_fees)
                    self.stdout.write(result)

        # Summary report
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("FEE STRUCTURE CREATION SUMMARY"))
        self.stdout.write("=" * 70)
        
        total_structures = 0
        for programme in [medicine_surgery, medical_lab, community_health]:
            count = FeeStructure.objects.filter(programme=programme).count()
            total_structures += count
            
            # Calculate expected structures
            if programme.code == "MBCHB":
                expected = 3 * 3 * 5  # 3 years * 3 semesters * 5 academic years = 45
            elif programme.code == "DMLT":
                expected = 2 * 3 * 5  # 2 years * 3 semesters * 5 academic years = 30
            else:  # BCH
                expected = 4 * 2 * 5  # 4 years * 2 semesters * 5 academic years = 40
            
            self.stdout.write(f"{programme.name}: {count}/{expected} fee structures")
        
        self.stdout.write(f"\nTotal fee structures in database: {total_structures}")
        
        # Fee breakdown sample for verification
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("SAMPLE FEE BREAKDOWN (Academic Year 2024/2025, Year 1, Semester 1)")
        self.stdout.write("=" * 70)
        
        try:
            sample_year = AcademicYear.objects.get(year='2024/2025')
            
            for programme in [medicine_surgery, medical_lab, community_health]:
                try:
                    fee_structure = FeeStructure.objects.get(
                        programme=programme,
                        academic_year=sample_year,
                        year=1,
                        semester=1
                    )
                    
                    self.stdout.write(f"\n{programme.name}:")
                    self.stdout.write(f"  Total Fee: KES {fee_structure.total_fee():,.2f}")
                    self.stdout.write(f"  Government Subsidy: KES {fee_structure.government_subsidy:,.2f}")
                    self.stdout.write(f"  Net Fee (Student Pays): KES {fee_structure.net_fee():,.2f}")
                    
                except FeeStructure.DoesNotExist:
                    self.stdout.write(f"\n{programme.name}: Sample fee structure not found")
                    
        except AcademicYear.DoesNotExist:
            self.stdout.write("Sample academic year 2024/2025 not found for fee breakdown")

        self.stdout.write(f"\n{self.style.SUCCESS('Fee structure creation completed successfully!')}")

# Additional utility command to update fees for inflation/cost adjustments
class InflationAdjustmentCommand(BaseCommand):
    help = 'Adjust fees for inflation across academic years'
    
    def add_arguments(self, parser):
        parser.add_argument('--inflation-rate', type=float, default=0.05, 
                          help='Inflation rate as decimal (e.g., 0.05 for 5%)')
        parser.add_argument('--start-year', type=str, default='2022/2023',
                          help='Academic year to start applying inflation')
    
    def handle(self, *args, **options):
        inflation_rate = options['inflation_rate']
        start_year = options['start_year']
        
        self.stdout.write(f"Applying {inflation_rate*100:.1f}% inflation adjustment from {start_year}")
        
        # Get academic years from start year onwards
        academic_years = AcademicYear.objects.filter(
            year__gte=start_year
        ).order_by('year')
        
        base_year = None
        for year in academic_years:
            if base_year is None:
                base_year = year
                continue
            
            # Calculate years difference
            base_year_int = int(base_year.year.split('/')[0])
            current_year_int = int(year.year.split('/')[0])
            years_diff = current_year_int - base_year_int
            
            # Apply compound inflation
            inflation_multiplier = (1 + inflation_rate) ** years_diff
            
            fee_structures = FeeStructure.objects.filter(academic_year=year)
            
            for fee_structure in fee_structures:
                # Get base year fee structure for comparison
                try:
                    base_fee_structure = FeeStructure.objects.get(
                        programme=fee_structure.programme,
                        academic_year=base_year,
                        year=fee_structure.year,
                        semester=fee_structure.semester
                    )
                    
                    # Apply inflation to main fee components
                    fee_structure.tuition_fee = base_fee_structure.tuition_fee * inflation_multiplier
                    fee_structure.accommodation_fee = base_fee_structure.accommodation_fee * inflation_multiplier
                    fee_structure.meals_fee = base_fee_structure.meals_fee * inflation_multiplier
                    fee_structure.laboratory_fee = base_fee_structure.laboratory_fee * inflation_multiplier
                    fee_structure.fieldwork_fee = base_fee_structure.fieldwork_fee * inflation_multiplier
                    
                    fee_structure.save()
                    
                except FeeStructure.DoesNotExist:
                    continue
            
            self.stdout.write(f"Applied {inflation_multiplier:.2f}x multiplier to {year.year}")
        
        self.stdout.write(self.style.SUCCESS(f'Inflation adjustment completed!'))