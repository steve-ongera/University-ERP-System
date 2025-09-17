from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler400, handler403, handler404, handler500
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("core_application.urls")),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# This allows media files to be served even when DEBUG = False (for dev/testing)
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]

# Error handlers
handler400 = 'core_application.views.custom_bad_request'
handler403 = 'core_application.views.custom_permission_denied'
handler404 = 'core_application.views.handler404'
handler500 = 'core_application.views.handler500'
