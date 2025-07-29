import os
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from core_application.models import NewsArticle  # Replace with your actual app and model

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed up to 10 real-like university news articles into the database.'

    def handle(self, *args, **kwargs):
        author = User.objects.first()

        if not author:
            self.stdout.write(self.style.ERROR("❌ No users found. Please create a user first."))
            return

        news_data = [
            {
                "title": "Murang’a University Hosts 2025 Engineering Innovation Expo",
                "summary": "The university welcomed over 50 institutions for a showcase of engineering breakthroughs.",
                "content": "The 2025 Engineering Expo brought together students, innovators, and industry experts to demonstrate cutting-edge projects, including renewable energy solutions and smart farming tech.",
                "category": "event",
                "publish_date": datetime(2025, 6, 10, tzinfo=dt_timezone.utc),
            },
            {
                "title": "Vice Chancellor Addresses 2024 Graduating Class",
                "summary": "The VC encouraged graduates to remain ethical and innovative.",
                "content": "In a moving ceremony, the Vice Chancellor urged students to be ambassadors of positive change and to uphold integrity in their careers.",
                "category": "academic",
                "publish_date": datetime(2024, 12, 15, tzinfo=dt_timezone.utc),
            },
            {
                "title": "University Ranked Among Top 10 in East Africa",
                "summary": "Murang’a University has climbed regional rankings due to research and innovation.",
                "content": "Thanks to faculty-led research and international collaborations, the university is now among the most reputable institutions in East Africa.",
                "category": "general",
                "publish_date": datetime(2024, 5, 8, tzinfo=dt_timezone.utc),
            },
            {
                "title": "Students Win National Hackathon Challenge",
                "summary": "Computer Science students developed a health-monitoring app.",
                "content": "The winning app, which tracks vital signs remotely, impressed judges with its practicality and user interface.",
                "category": "academic",
                "publish_date": datetime(2023, 11, 2, tzinfo=dt_timezone.utc),
            },
            {
                "title": "Annual Sports Day Held With Record Participation",
                "summary": "Over 1,000 students participated in athletics, football, and volleyball competitions.",
                "content": "The event, themed 'One Team, One Dream', promoted unity and physical fitness across faculties.",
                "category": "sports",
                "publish_date": datetime(2024, 3, 20, tzinfo=dt_timezone.utc),
            },
            {
                "title": "Call for Papers: International Science Conference 2025",
                "summary": "Academics invited to submit research papers by January 30, 2025.",
                "content": "The upcoming conference will focus on sustainable development, AI in education, and biotechnology breakthroughs.",
                "category": "announcement",
                "publish_date": datetime(2024, 9, 1, tzinfo=dt_timezone.utc),
            },
            {
                "title": "University Launches Mental Health Support Center",
                "summary": "New center to offer counseling, peer mentorship, and wellness programs.",
                "content": "The Vice Dean of Students emphasized the importance of mental wellness, especially during exam seasons.",
                "category": "general",
                "publish_date": datetime(2023, 10, 5, tzinfo=dt_timezone.utc),
            },
            {
                "title": "Faculty Member Awarded Global Research Grant",
                "summary": "Dr. Jane Muthoni received a $100,000 grant for climate change research.",
                "content": "Her project explores how rural communities in Kenya can adapt to shifting weather patterns using traditional knowledge.",
                "category": "academic",
                "publish_date": datetime(2023, 8, 18, tzinfo=dt_timezone.utc),
            },
            {
                "title": "Upcoming Career Fair to Feature Top Employers",
                "summary": "Google, Safaricom, and Equity Bank confirmed to attend the 2025 Career Day.",
                "content": "Students are encouraged to bring updated CVs and dress professionally to maximize internship and job opportunities.",
                "category": "event",
                "publish_date": datetime(2025, 2, 25, tzinfo=dt_timezone.utc),
            },
            {
                "title": "University Launches Smart Library System",
                "summary": "New RFID-powered library management reduces queues and improves book tracking.",
                "content": "Students can now borrow and return books using their student cards, with auto-notifications for due dates.",
                "category": "academic",
                "publish_date": datetime(2024, 1, 14, tzinfo=dt_timezone.utc),
            },
        ]

        created_count = 0
        for news in news_data:
            obj, created = NewsArticle.objects.get_or_create(
                title=news["title"],
                defaults={
                    "summary": news["summary"],
                    "content": news["content"],
                    "category": news["category"],
                    "publish_date": news["publish_date"],
                    "author": author,
                    "is_published": True,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {created_count} news articles added."))
