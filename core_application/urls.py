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
    path('news/', views.student_news, name='student_news'),
    # Events
    path('events/', views.student_events, name='student_events'),
    path('events/register/<int:event_id>/', views.register_event, name='register_event'),
    path('comments/', views.student_comments, name='student_comments'),
    path('faqs/', views.faqs , name="faqs"),
    path('virtual_assistant', views.virtual_assistant , name="virtual_assistant"),
    path('process-query/', views.process_assistant_query, name='process_assistant_query'),
    
   

    path('news/', views.student_news, name='student_news'),
    path('clubs/', views.student_clubs, name='student_clubs'),
    path('clubs/join/<int:club_id>/', views.join_club, name='join_club'),
    path('clubs/leave/<int:club_id>/', views.leave_club, name='leave_club'),
    path('club-events/', views.club_events, name='club_events'),
    path('club-events/<int:club_id>/', views.club_events, name='club_events_detail'),

    # Main hostel booking flow
    path('hostel/check-eligibility/', views.hostel_booking_eligibility, name='hostel_booking_eligibility'),
    path('hostel/list/', views.hostel_list, name='hostel_list'),
    path('hostel/<int:hostel_id>/rooms/', views.room_list, name='room_list'),
    path('room/<int:room_id>/beds/', views.bed_list, name='bed_list'),
    path('bed/<int:bed_id>/book/', views.book_bed, name='book_bed'),
    
    # Booking management
    path('booking/<int:booking_id>/', views.hostel_booking_detail, name='hostel_booking_detail'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # AJAX endpoints
    path('ajax/rooms/', views.get_rooms_ajax, name='get_rooms_ajax'),
    path('ajax/beds/', views.get_beds_ajax, name='get_beds_ajax'),

    # Admin authentication URLs
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    path('students/<str:student_id>/update/', views.student_update, name='student_update'),
    path('students/<str:student_id>/delete/', views.student_delete, name='student_delete'),
    path('students/<str:student_id>/performance/', views.student_performance, name='student_performance'),
    path('api/programmes-by-school/', views.get_programmes_by_school, name='get_programmes_by_school'),
    # Marks entry URLs
    path('admin-marks-entry/', views.admin_marks_entry, name='admin_marks_entry'),
    path('admin-marks-entry/<str:student_id>/', views.admin_marks_entry, name='admin_marks_entry_student'),
    
    
    # AJAX endpoints
    path('admin-get-student-info/', views.get_student_info, name='get_student_info'),
    path('admin-calculate-gpa/<str:student_id>/', views.calculate_student_gpa, name='calculate_student_gpa'),
     #students transcript
    path('student/transcript/', views.student_transcript, name='student_transcript'),
    path('student-download-transcript', views.student_transcript_pdf , name='student_transcript_pdf'),

    # Lecturer management URLs
    path('lecturers/', views.lecturer_list, name='lecturer_list'),
    path('lecturers/create/', views.lecturer_create, name='lecturer_create'),
    path('lecturers/<str:employee_number>/', views.lecturer_detail, name='lecturer_detail'),
    path('lecturers/<str:employee_number>/edit/', views.lecturer_update, name='lecturer_update'),
    path('lecturers/<str:employee_number>/delete/', views.lecturer_delete, name='lecturer_delete'),
    
    # Bulk operations
    path('lecturers/bulk/action/', views.lecturer_bulk_action, name='lecturer_bulk_action'),
    
    # Export functionality
    path('lecturers/export/csv/', views.lecturer_export, name='lecturer_export'),
    # Programme URLs
    path('programmes/', views.programme_list, name='programme_list'),
    path('programmes/<int:programme_id>/', views.programme_detail, name='programme_detail'),
    path('programmes/<int:programme_id>/courses/<int:course_id>/enrollments/', 
         views.course_enrollments, name='course_enrollments'),
    path('students/<int:student_id>/courses/<int:course_id>/enrollment/', 
         views.student_enrollment_detail, name='student_enrollment_detail'),

     #Grades URLs
    path('grades/', views.grades_list, name='grades_list'),
    path('grades/download-pdf/', views.download_grades_pdf, name='download_grades_pdf'),
    path('api/semesters-by-year/', views.get_semesters_by_year, name='get_semesters_by_year'),
    
    # Additional grade-related URLs you might need
    #path('grades/student/<str:student_id>/', views.student_transcript, name='student_transcript'),
    path('grades/course/<int:course_id>/', views.course_grades, name='course_grades'),
    path('grades/analytics/', views.grades_analytics, name='grades_analytics'),

    # Fee Structure URLs
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('programme/<int:programme_id>/fees/', views.programme_fee_detail, name='programme_fee_detail'),
    path('fee-structures/comparison/', views.fee_structure_comparison, name='fee_structure_comparison'),

]