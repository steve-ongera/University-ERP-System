# =============================================================================
# tasks.py - Celery Tasks for Async Processing (Optional but Recommended)
# =============================================================================

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_payment_confirmation_email(student_id, payment_id):
    """
    Send payment confirmation email asynchronously
    """
    try:
        from .models import Student, FeePayment
        
        student = Student.objects.get(student_id=student_id)
        payment = FeePayment.objects.get(id=payment_id)
        
        subject = f"Fee Payment Confirmation - {payment.receipt_number}"
        message = f"""
Dear {student.user.get_full_name()},

Your fee payment has been successfully received.

Payment Details:
Receipt Number: {payment.receipt_number}
Amount: KES {payment.amount_paid:,.2f}
Date: {payment.payment_date}
Method: {payment.get_payment_method_display()}

Thank you.

Finance Office
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student.user.email],
            fail_silently=False
        )
        
        logger.info(f"Payment confirmation email sent to {student.user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send payment email: {str(e)}")


@shared_task
def reconcile_bank_payments():
    """
    Daily task to reconcile payments with bank statements
    """
    from .models import FeePayment
    from datetime import timedelta
    from django.utils import timezone
    
    # Get pending payments from last 24 hours
    yesterday = timezone.now() - timedelta(days=1)
    pending_payments = FeePayment.objects.filter(
        payment_status='pending',
        payment_date__gte=yesterday
    )
    
    for payment in pending_payments:
        # Call bank API to verify payment status
        # Update payment status accordingly
        pass
    
    logger.info(f"Reconciled {pending_payments.count()} pending payments")
