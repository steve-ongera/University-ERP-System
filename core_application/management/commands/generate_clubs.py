from django.core.management.base import BaseCommand
from core_application.models import StudentClub

class Command(BaseCommand):
    help = 'Generate sample Student Clubs'

    def handle(self, *args, **kwargs):
        club_names = [
            "Tech Innovators Club",
            "Drama & Arts Society",
            "Red Cross Chapter",
            "Environmental Conservation Club",
            "Poly Music Band",
            "Debate & Public Speaking Club",
            "Entrepreneurs Hub",
            "Gaming & eSports Club"
        ]

        for name in club_names:
            club, created = StudentClub.objects.get_or_create(
                name=name,
                defaults={
                    'description': f"{name} is a vibrant student club focused on {name.lower()} activities and events."
                }
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(self.style.SUCCESS(f'{status}: {club.name}'))
