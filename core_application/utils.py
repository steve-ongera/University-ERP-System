
# utils.py - Additional utility functions

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def send_security_alert_html_email(alert_type, username, ip_address, details, user_agent=''):
    """Send HTML security alert email to administrators"""
    try:
        from core_application.models import User, AdminSecurityAlert
        
        # Get all superusers to notify
        admin_emails = User.objects.filter(
            is_superuser=True, 
            is_active=True,
            email__isnull=False
        ).exclude(email='').values_list('email', flat=True)
        
        if not admin_emails:
            logger.warning("No admin emails found for security alert")
            return False
        
        subject = f'🚨 SECURITY ALERT - {alert_type.upper()}'
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc3545, #c82333); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; }}
                .alert-box {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .details {{ background: white; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0; }}
                .footer {{ background: #6c757d; color: white; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; }}
                .timestamp {{ color: #6c757d; font-size: 14px; }}
                .critical {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ SECURITY ALERT</h1>
                    <p>Unauthorized Admin Access Attempt Detected</p>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h3 class="critical">⚠️ {alert_type}</h3>
                        <p><strong>Immediate attention required!</strong></p>
                    </div>
                    
                    <div class="details">
                        <h4>Incident Details:</h4>
                        <ul>
                            <li><strong>Target Username:</strong> {username}</li>
                            <li><strong>Source IP Address:</strong> {ip_address}</li>
                            <li><strong>Timestamp:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                            <li><strong>User Agent:</strong> {user_agent or 'Unknown'}</li>
                        </ul>
                        
                        <h4>Additional Information:</h4>
                        <p>{details}</p>
                    </div>
                    
                    <div class="alert-box">
                        <h4>Recommended Actions:</h4>
                        <ul>
                            <li>Review admin access logs immediately</li>
                            <li>Verify the legitimacy of this access attempt</li>
                            <li>Consider temporarily disabling the affected account if suspicious</li>
                            <li>Monitor for additional attempts from this IP address</li>
                            <li>Update security policies if necessary</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated security notification from your University Management System.</p>
                    <p class="timestamp">System Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_content = f"""
SECURITY ALERT: {alert_type.upper()}

Target Username: {username}
IP Address: {ip_address}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
User Agent: {user_agent or 'Unknown'}

Details: {details}

Please review admin access logs and take appropriate security measures.

This is an automated security notification from your University Management System.
        """
        
        # Send email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(admin_emails)
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        # Log the alert
        AdminSecurityAlert.objects.create(
            alert_type=alert_type.lower().replace(' ', '_'),
            username=username,
            ip_address=ip_address,
            details=f"{details}\nUser Agent: {user_agent}",
            email_sent=True
        )
        
        logger.info(f"Security alert sent for {alert_type}: {username}@{ip_address}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send security alert email: {str(e)}")
        return False

def get_geolocation_info(ip_address):
    """Get basic geolocation info for IP address (optional enhancement)"""
    try:
        import requests
        
        # Using a free IP geolocation service (you can use others)
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country', 'Unknown'),
                'region': data.get('regionName', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'isp': data.get('isp', 'Unknown')
            }
    except Exception:
        pass
    
    return {
        'country': 'Unknown',
        'region': 'Unknown', 
        'city': 'Unknown',
        'isp': 'Unknown'
    }
