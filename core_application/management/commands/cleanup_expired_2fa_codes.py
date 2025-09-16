# management/commands/cleanup_expired_2fa_codes.py
# Create this file in your_app/management/commands/

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core_application.models import AdminTwoFactorCode, AdminLoginAttempt

class Command(BaseCommand):
    help = 'Clean up expired 2FA codes and old login attempts'

    def handle(self, *args, **options):
        # Delete expired 2FA codes
        expired_codes = AdminTwoFactorCode.objects.filter(
            expires_at__lt=timezone.now()
        )
        expired_count = expired_codes.count()
        expired_codes.delete()
        
        # Delete old login attempts (older than 30 days)
        old_attempts = AdminLoginAttempt.objects.filter(
            attempt_time__lt=timezone.now() - timedelta(days=30)
        )
        attempt_count = old_attempts.count()
        old_attempts.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {expired_count} expired 2FA codes '
                f'and {attempt_count} old login attempts'
            )
        )
