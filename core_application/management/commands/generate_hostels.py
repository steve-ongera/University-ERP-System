from django.core.management.base import BaseCommand
from django.db import transaction
from core_application.models import Hostel, Room, Bed, AcademicYear, Department


class Command(BaseCommand):
    help = "Generate hostel data with 200 rooms each"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write("🏠 Starting Hostel Data Generation")

                # Academic year setup
                current_year = "2024/2025"
                academic_year, created = AcademicYear.objects.get_or_create(
                    year=current_year,
                    defaults={
                        'start_date': '2024-09-01',
                        'end_date': '2025-06-30',
                        'is_current': True
                    }
                )

                department = Department.objects.first()
                if not department:
                    self.stdout.write("❌ No departments found. Create one first.")
                    return

                hostel_data = [
                    {"name": "MT KENYA HOSTEL", "code": "MTK", "type": "boys"},
                    {"name": "MT KILIMANJARO HOSTEL", "code": "MKL", "type": "boys"},
                    {"name": "MT ELGON HOSTEL", "code": "MEL", "type": "girls"},
                    {"name": "MT LONGONOT HOSTEL", "code": "MLG", "type": "girls"},
                ]

                rules = """HOSTEL RULES AND REGULATIONS
1. Maintain discipline and cleanliness.
2. No noise after 10:00 PM.
3. Visitors allowed 2–6 PM only.
4. Cooking in rooms is prohibited."""

                for hostel_info in hostel_data:
                    hostel, created = Hostel.objects.get_or_create(
                        name=hostel_info['name'],
                        defaults={
                            'hostel_type': hostel_info['type'],
                            'school': department,
                            'total_rooms': 200,
                            'description': "Auto-generated hostel",
                            'facilities': 'WiFi, Laundry, Common Room',
                            'rules_and_regulations': rules,
                            'is_active': True
                        }
                    )

                    self.stdout.write(f"\n🔧 Creating rooms for {hostel.name}")

                    # Create 200 rooms
                    for i in range(1, 201):
                        room_number = f"{hostel_info['code']}{i:03d}"
                        room, room_created = Room.objects.get_or_create(
                            hostel=hostel,
                            room_number=room_number,
                            defaults={
                                'floor': ((i - 1) // 40) + 1,
                                'capacity': 4,
                                'description': f"Room {room_number}",
                                'facilities': "Bed, Table, Chair",
                                'is_active': True
                            }
                        )

                        if room_created:
                            for bed_num in range(1, 5):
                                bed_pos = f"bed_{bed_num}"
                                Bed.objects.get_or_create(
                                    room=room,
                                    academic_year=academic_year,
                                    bed_position=bed_pos,
                                    defaults={
                                        'is_available': True,
                                        'maintenance_status': 'good'
                                    }
                                )

                    self.stdout.write(f"✅ {hostel.name} has 200 rooms created.")

                total_rooms = Room.objects.count()
                total_beds = Bed.objects.filter(academic_year=academic_year).count()
                self.stdout.write("\n🎉 Hostel Data Generation Complete!")
                self.stdout.write(f"🏨 Total Rooms: {total_rooms}")
                self.stdout.write(f"🛏️ Total Beds (for {academic_year.year}): {total_beds}")

        except Exception as e:
            self.stderr.write(f"❌ Error: {e}")
