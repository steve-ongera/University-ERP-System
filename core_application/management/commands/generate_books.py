import random
from django.core.management.base import BaseCommand
from core_application.models import Library

class Command(BaseCommand):
    help = "Generate 40 real university library books"

    def handle(self, *args, **kwargs):
        books = [
            {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "publisher": "MIT Press", "year": 2009, "subject": "Computer Science"},
            {"title": "Database System Concepts", "author": "Abraham Silberschatz", "publisher": "McGraw-Hill", "year": 2019, "subject": "Information Technology"},
            {"title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell, Peter Norvig", "publisher": "Pearson", "year": 2021, "subject": "Computer Science"},
            {"title": "Linear Algebra and Its Applications", "author": "Gilbert Strang", "publisher": "Cengage Learning", "year": 2016, "subject": "Mathematics"},
            {"title": "Principles of Economics", "author": "N. Gregory Mankiw", "publisher": "Cengage Learning", "year": 2020, "subject": "Economics"},
            {"title": "Psychology", "author": "David G. Myers", "publisher": "Worth Publishers", "year": 2018, "subject": "Psychology"},
            {"title": "Business Management", "author": "Stephen P. Robbins", "publisher": "Pearson Education", "year": 2017, "subject": "Business Studies"},
            {"title": "Modern Physics", "author": "Kenneth Krane", "publisher": "Wiley", "year": 2019, "subject": "Physics"},
            {"title": "Organic Chemistry", "author": "Paula Yurkanis Bruice", "publisher": "Pearson", "year": 2016, "subject": "Chemistry"},
            {"title": "Molecular Biology of the Cell", "author": "Bruce Alberts", "publisher": "Garland Science", "year": 2015, "subject": "Biology"},
            {"title": "Constitutional Law", "author": "Erwin Chemerinsky", "publisher": "Aspen Publishers", "year": 2019, "subject": "Law"},
            {"title": "Political Science: An Introduction", "author": "Michael G. Roskin", "publisher": "Pearson", "year": 2017, "subject": "Political Science"},
            {"title": "Educational Psychology", "author": "John W. Santrock", "publisher": "McGraw-Hill", "year": 2018, "subject": "Education"},
            {"title": "Philosophy: The Basics", "author": "Nigel Warburton", "publisher": "Routledge", "year": 2020, "subject": "Philosophy"},
            {"title": "World History", "author": "William J. Duiker", "publisher": "Cengage Learning", "year": 2016, "subject": "History"},
        ]

        resource_types = ["book", "ebook", "reference", "journal", "thesis"]

        for i in range(40):
            book = random.choice(books)
            total_copies = random.randint(1, 10)
            edition = f"{random.randint(1, 5)}th Edition"

            Library.objects.create(
                title=book["title"],
                author=book["author"],
                isbn=f"978-{random.randint(1000000000, 9999999999)}",
                resource_type=random.choice(resource_types),
                publisher=book["publisher"],
                publication_year=book["year"],
                edition=edition,
                total_copies=total_copies,
                available_copies=total_copies,
                location=f"Shelf {random.randint(1,20)}",
                call_number=f"LB-{random.randint(1000,9999)}-{i}",
                subject_area=book["subject"],
                description=f"A comprehensive resource on {book['subject'].lower()}",
                is_available=True
            )

        self.stdout.write(self.style.SUCCESS("✅ Successfully generated 40 real-like library books"))
