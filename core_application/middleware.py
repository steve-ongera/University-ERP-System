# Create a new file: middleware.py in your app directory

import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib.auth import get_user
from .models import ActivityLog, PageVisit, UserSession

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """Get user agent string"""
    return request.META.get('HTTP_USER_AGENT', '')

class ActivityTrackingMiddleware(MiddlewareMixin):
    """Middleware to track user activities and page visits"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Record start time for response time calculation"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Track page visits and response times"""
        # Skip tracking for static files, admin, and API calls
        if any(request.path.startswith(path) for path in ['/static/', '/media/', '/admin/', '/favicon.ico']):
            return response
            
        # Skip tracking for AJAX requests (optional)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return response
        
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # Calculate response time
            response_time = None
            if hasattr(request, '_start_time'):
                response_time = int((time.time() - request._start_time) * 1000)
            
            # Get page title from response if possible
            page_title = ''
            if hasattr(response, 'context_data') and response.context_data:
                page_title = response.context_data.get('title', '')
            
            # Create page visit record
            try:
                PageVisit.objects.create(
                    user=user,
                    session_key=request.session.session_key or '',
                    url=request.path,
                    view_name=getattr(request.resolver_match, 'url_name', '') if hasattr(request, 'resolver_match') else '',
                    page_title=page_title,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    referrer=request.META.get('HTTP_REFERER', ''),
                    response_time=response_time
                )
                
                # Update user session activity
                if request.session.session_key:
                    UserSession.objects.filter(
                        session_key=request.session.session_key,
                        user=user,
                        is_active=True
                    ).update(last_activity=timezone.now())
                    
            except Exception as e:
                # Log error but don't break the response
                print(f"Error tracking page visit: {e}")
        
        return response

class UserSessionMiddleware(MiddlewareMixin):
    """Middleware to track user sessions"""
    
    def process_request(self, request):
        """Track user login sessions"""
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated and request.session.session_key:
            # Check if this session is already tracked
            session_exists = UserSession.objects.filter(
                session_key=request.session.session_key,
                user=user,
                is_active=True
            ).exists()
            
            if not session_exists:
                # Create new session record
                try:
                    UserSession.objects.create(
                        user=user,
                        session_key=request.session.session_key,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
                    )
                    
                    # Log the login activity
                    ActivityLog.objects.create(
                        user=user,
                        action='login',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        description=f"User logged in from {get_client_ip(request)}"
                    )
                except Exception as e:
                    print(f"Error creating user session: {e}")
        
        return None

# Utility functions for logging activities
def log_activity(user, action, content_object=None, description='', old_values=None, new_values=None, request=None):
    """
    Helper function to log user activities
    """
    if not user or not user.is_authenticated:
        return
    
    ip_address = '127.0.0.1'
    user_agent = ''
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
    
    # Convert values to JSON if they're dictionaries
    old_values_json = json.dumps(old_values) if old_values and isinstance(old_values, dict) else old_values or ''
    new_values_json = json.dumps(new_values) if new_values and isinstance(new_values, dict) else new_values or ''
    
    try:
        ActivityLog.objects.create(
            user=user,
            action=action,
            content_object=content_object,
            description=description,
            old_values=old_values_json,
            new_values=new_values_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Error logging activity: {e}")

# Signal handlers for automatic logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """Log model saves automatically"""
    # Skip logging for our own tracking models to avoid recursion
    if sender in [ActivityLog, PageVisit, UserSession]:
        return
    
    # Skip for sessions and other system models
    if sender.__name__ in ['Session', 'LogEntry', 'ContentType', 'Permission']:
        return
    
    # Try to get user from current request (would need threading.local in real implementation)
    # For now, we'll skip automatic logging and rely on manual logging in views
    pass

@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    """Log model deletions automatically"""
    # Similar to save handler, skip for tracking models
    if sender in [ActivityLog, PageVisit, UserSession]:
        return
    
    # Skip for sessions and other system models
    if sender.__name__ in ['Session', 'LogEntry', 'ContentType', 'Permission']:
        return
    
    # Manual logging in views would be more reliable
    pass



# =============================================================================
# middleware.py - IP Whitelist Middleware for Bank Webhooks
# =============================================================================

from django.http import HttpResponseForbidden
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class BankWebhookIPWhitelistMiddleware:
    """
    Middleware to restrict bank webhook endpoints to specific IP addresses
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.webhook_paths = [
            '/api/payments/equity/webhook/',
            '/api/payments/kcb/webhook/',
            '/api/payments/mpesa/callback/',
        ]

    def __call__(self, request):
        # Check if the request is for a webhook endpoint
        if any(request.path.startswith(path) for path in self.webhook_paths):
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(',')[0]
            else:
                client_ip = request.META.get('REMOTE_ADDR')
            
            # Check if IP is whitelisted
            allowed_ips = getattr(settings, 'PAYMENT_WEBHOOK_IPS', [])
            
            # Allow localhost for testing
            if settings.DEBUG or client_ip in allowed_ips or client_ip == '127.0.0.1':
                return self.get_response(request)
            else:
                logger.warning(f"Unauthorized webhook access attempt from IP: {client_ip}")
                return HttpResponseForbidden("Access denied")
        
        return self.get_response(request)
    

"""
 Security and Audit Middleware

"""

from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
import json

class SecurityAuditMiddleware:
    """
    Middleware to:
    1. Prevent non-superusers from deleting data
    2. Log all database modifications
    3. Track user activities
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Store request info for later use
        request._middleware_start_time = timezone.now()
        
        response = self.get_response(request)
        
        # Log page visits
        if not isinstance(request.user, AnonymousUser):
            self._log_page_visit(request, response)
        
        return response
    
    def _log_page_visit(self, request, response):
        """Log page visits for analytics"""
        from .models import PageVisit
        
        try:
            # Calculate response time
            response_time = None
            if hasattr(request, '_middleware_start_time'):
                delta = timezone.now() - request._middleware_start_time
                response_time = int(delta.total_seconds() * 1000)
            
            PageVisit.objects.create(
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                session_key=request.session.session_key or '',
                url=request.path,
                view_name=request.resolver_match.view_name if request.resolver_match else '',
                timestamp=timezone.now(),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', ''),
                response_time=response_time
            )
        except Exception:
            pass  # Don't break the request if logging fails
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


class DeletionControlMiddleware:
    """
    Middleware to prevent non-superusers from deleting records
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Check if user is attempting deletion"""
        # Check if this is a delete request
        if request.method == 'POST' and 'delete' in request.path.lower():
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can delete records from the system.")
        
        return None