from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Student authentication
    path('', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    
    # Student dashboard and main views
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('units/', views.student_units_view, name='student_units'),
    path('check-prerequisites/', views.check_prerequisites_ajax, name='check_prerequisites'),
    path('course-details/<int:course_id>/', views.course_details_ajax, name='course_details'),
    path('reporting/', views.student_reporting, name='student_reporting'),
]