from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset all user passwords to password123'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-type',
            type=str,
            help='Reset passwords for a specific user type only (e.g. student, lecturer)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        new_password = 'password123'
        user_type = options.get('user_type')

        # Filter users
        users = User.objects.all()
        if user_type:
            users = users.filter(user_type=user_type)

        total = users.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No users found matching the criteria.'))
            return

        # Confirm
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                f'This will reset passwords for {total} user(s)'
                + (f' of type "{user_type}"' if user_type else '')
                + f' to "{new_password}".'
            ))
            confirm = input('Are you sure? Type "yes" to continue: ')
            if confirm.strip().lower() != 'yes':
                self.stdout.write(self.style.ERROR('Aborted.'))
                return

        # Reset passwords
        updated = 0
        for user in users:
            user.set_password(new_password)
            user.save(update_fields=['password'])
            updated += 1
            self.stdout.write(f'  Reset: {user.username} ({user.user_type})')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {updated} password(s) reset to "{new_password}".'
        ))