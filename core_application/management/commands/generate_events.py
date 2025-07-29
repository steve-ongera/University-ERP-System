import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core_application.models import ClubEvent, StudentClub

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample Club Events'

    def handle(self, *args, **kwargs):
        titles = [
            "Tech Talk: AI in Education",
            "Cultural Night 2025",
            "Charity Walk for Health",
            "Coding Bootcamp: Web Dev Basics",
            "Music & Poetry Jam Session"
        ]

        descriptions = [
            "A deep dive into how artificial intelligence is transforming the education sector.",
            "Showcase of diverse cultures through food, dance, and storytelling.",
            "Join us as we raise funds for community health initiatives.",
            "A weekend of hands-on web development with experienced mentors.",
            "An evening of creativity through music, spoken word, and poetry."
        ]

        locations = ["Main Hall", "Auditorium", "Library Grounds", "ICT Lab", "Sports Field"]
        statuses = ['upcoming', 'ongoing', 'completed']

        organizer = User.objects.filter(is_staff=True).first()
        if not organizer:
            self.stdout.write(self.style.ERROR('No staff user found. Please create one first.'))
            return

        clubs = StudentClub.objects.all()
        if not clubs.exists():
            self.stdout.write(self.style.ERROR('No Student Clubs found. Please create some clubs first.'))
            return

        for i in range(10):
            title = random.choice(titles)
            description = random.choice(descriptions)
            location = random.choice(locations)
            club = random.choice(clubs)

            days_offset = random.randint(-10, 10)
            start = timezone.now() + timedelta(days=days_offset, hours=random.randint(1, 4))
            end = start + timedelta(hours=random.randint(1, 4))

            event = ClubEvent.objects.create(
                club=club,
                title=f"{title} #{i+1}",
                description=description,
                start_datetime=start,
                end_datetime=end,
                location=location,
                organizer=organizer,
                registration_required=random.choice([True, False]),
                max_participants=random.choice([None, random.randint(20, 100)]),
            )
            self.stdout.write(self.style.SUCCESS(f'Created event: {event.title} for club {club.name}'))
