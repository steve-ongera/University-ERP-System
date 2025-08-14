from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Student authentication
    path('', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    
    # Student dashboard and main views
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('units/', views.student_units_view, name='student_units'),
    path('check-prerequisites/', views.check_prerequisites_ajax, name='check_prerequisites'),
    path('course-details/<int:course_id>/', views.course_details_ajax, name='course_details'),
    path('reporting/', views.student_reporting, name='student_reporting'),
    path('news/', views.student_news, name='student_news'),
    path('course_evaluation/', views.course_evaluation , name='course_evaluation'),
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

    #warden hostel views
    # Hostel Management URLs
    path('hostels/', views.get_hostel_list, name='warden_hostel_list'),
    path('warden/hostel/<int:hostel_id>/rooms/', views.hostel_room_management, name='hostel_room_management'),
    
    # Room Creation URLs
    path('hostel/<int:hostel_id>/rooms/create/', views.create_single_room, name='create_single_room'),
    path('hostel/<int:hostel_id>/rooms/bulk-create/', views.bulk_create_rooms, name='bulk_create_rooms'),
    
    # Room Management URLs
    path('rooms/<int:room_id>/delete/', views.delete_room, name='delete_room'),
    path('rooms/<int:room_id>/toggle-status/', views.toggle_room_status, name='toggle_room_status'),
    path('rooms/<int:room_id>/details/', views.get_room_details, name='get_room_details'),
    
    # Bulk Operations URLs
    path('hostel/<int:hostel_id>/rooms/bulk-delete/', views.bulk_delete_rooms, name='bulk_delete_rooms'),

    #end of warden views 

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
    path('hostel-dashboard/', views.hostel_dashboard, name='hostel_dashboard'),

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
    # Complete transcript (all years)
    path('transcript/pdf/', views.student_transcript_pdf, name='transcript_pdf'),
    
    # Academic year transcript
    path('transcript/pdf/year/<int:academic_year_id>/', views.student_transcript_pdf, name='transcript_pdf_year'),
    
    # Semester transcript
    path('transcript/pdf/semester/<int:semester_id>/', views.student_transcript_pdf, name='transcript_pdf_semester'),


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

    # Admin or HOD views
    path('dashboard/lecturer-allocation/', views.lecturer_allocation_dashboard, name='lecturer_allocation_dashboard'),
    path('dashboard/allocate-course/', views.allocate_course_to_lecturer, name='allocate_course_to_lecturer'),
    path('dashboard/remove-allocation/', views.remove_course_allocation, name='remove_course_allocation'),

    # Lecturer views
    path('lecturer/unit/dashboard/', views.lecturer_unit_dashboard, name='lecturer_unit_dashboard'),
    # Lecturer Profile URLs
    path('lecturer/profile/', views.lecturer_profile, name='lecturer_profile'),
    path('lecturer/profile/upload-picture/', views.lecturer_profile_picture_upload, name='lecturer_profile_picture_upload'),
    path('lecturer/course/<int:assignment_id>/', views.lecturer_course_detail, name='lecturer_course_detail'),
    path('lecturer/course/<int:assignment_id>/create-assignment/', views.create_assignment, name='create_assignment'),
    path('lecturer/course/<int:assignment_id>/create-notes/', views.create_course_notes, name='create_course_notes'),
    path('lecturer/course/<int:assignment_id>/create-announcement/', views.create_announcement, name='create_announcement'),

    # Student Dashboard URLs
    path('student/unit/dashboard/', views.student_unit_dashboard, name='student_unit_dashboard'),
    path('student/course/<int:enrollment_id>/', views.student_course_detail, name='student_course_detail'),
    
    # Assignment URLs
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('student/assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    
    # Notes and Downloads
    path('student/notes/<int:notes_id>/download/', views.download_notes, name='download_notes'),
    path('student/grades/', views.student_grades, name='student_grades'),

    # Assignment Submission URLs
    path('assignment/<int:assignment_id>/submissions/', views.assignment_submissions_list, name='assignment_submissions_list'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),   
    path('submission/<int:submission_id>/quick-grade/', views.quick_grade_submission, name='quick_grade_submission'), 
    path('assignment/<int:assignment_id>/bulk-grade/', views.bulk_grade_submissions, name='bulk_grade_submissions'),
    path('assignment/<int:assignment_id>/statistics/', views.submission_statistics, name='submission_statistics'),

    # Main timetable management page
    path('admin-timetable-management/', views.timetable_management, name='timetable_management'),
    # AJAX endpoints
    path('admin-get-programme-courses/<int:programme_id>/', views.get_programme_courses, name='get_programme_courses'),
    path('admin-get-programme-timetable/<int:programme_id>/', views.get_programme_timetable, name='get_programme_timetable'),
    path('admin-save-timetable-entry/', views.save_timetable_entry, name='save_timetable_entry'),
    path('admin-delete-timetable-entry/<int:entry_id>/', views.delete_timetable_entry, name='delete_timetable_entry'),
    path('admin-get-available-lecturers/', views.get_available_lecturers, name='get_available_lecturers'),

    #timetable URL
    path('student/timetable/', views.student_timetable_view, name='student_timetable'),
    path('lecturer/timetable/', views.lecturer_timetable_view, name='lecturer_timetable'),

    # Lecturer Attendance URLs
    path('lecturer/attendance/', views.lecturer_attendance_dashboard, name='lecturer_attendance_dashboard'),
    path('lecturer/attendance/generate/<int:timetable_id>/', views.lecturer_generate_qr_attendance, name='lecturer_generate_qr_attendance'),
    path('lecturer/attendance/detail/<int:session_id>/', views.lecturer_attendance_detail, name='lecturer_attendance_detail'),
    
    # Student Attendance URLS  curriculum
    path('attendance/scan/', views.scan_attendance_qr, name='scan_attendance_qr'),
    path('attendance/mark/<str:token>/', views.mark_attendance_qr, name='mark_attendance_qr'),
    path('student/attendance/history/', views.student_attendance_history, name='student_attendance_history'),
    path('lecturer_support/', views.lecturer_support, name='lecturer_support'),
    path('lecturer_training/', views.lecturer_training, name='lecturer_training'),
    path('curriculum/', views.curriculum, name='curriculum'),

    # Lecturer Grade Entry URLs
    path('grade-entry/', views.grade_entry, name='grade_entry'),
    path('lecturer/get-student-enrollments/', views.get_student_enrollments, name='get_student_enrollments'),
    path('lecturer/save-grades/', views.save_grades, name='save_grades'),
    path('lecturer/get-semesters-by-year/', views.get_semesters_by_year, name='get_semesters_by_year'),

    # Students and Attendance Management
    path('my-students/', views.my_students, name='my_students'),
    path('lecturer/get-course-students/', views.get_course_students, name='get_course_students'),
    path('lecturer/update-attendance/', views.update_attendance, name='update_attendance'),
    path('export-attendance/<int:course_id>/<int:semester_id>/', views.export_attendance, name='export_attendance'),
    # QR Code Attendance
    path('lecturer/generate-qr-attendance/<int:course_id>/<int:semester_id>/', views.generate_qr_attendance, name='generate_qr_attendance'),

    #  Fee Management
    path('student/fees/', views.student_fee_management, name='student_fee_management'),
    path('admin-fee-payment/', views.admin_fee_payment, name='admin_fee_payment'),
    path('admin-ajax/student-info/', views.get_student_info, name='get_student_info'),
    path('admin-ajax/fee-structure/', views.get_fee_structure, name='get_fee_structure'),

    # Exam Repository URLs
    path('exam-repository/', views.exam_repository, name='exam_repository'),
    path('exam-material/<int:material_id>/download/', views.download_exam_material, name='download_exam_material'),

    # Special Exam Application URLs
    path('special-exams/', views.special_exam_applications, name='special_exam_applications'),
    path('special-exams/apply/', views.apply_special_exam, name='apply_special_exam'),
    
    # Deferment Application URLs
    path('deferments/', views.deferment_applications, name='deferment_applications'),
    path('deferments/apply/', views.apply_deferment, name='apply_deferment'),
    
    # Clearance URLs
    path('clearances/', views.clearance_requests, name='clearance_requests'),
    path('clearances/request/', views.request_clearance, name='request_clearance'),
    
    # Messaging URLs
    path('messages/', views.messages_inbox, name='messages_inbox'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    path('messages/<int:message_id>/reply/', views.reply_message, name='reply_message'),
    path('messages/sent/', views.sent_messages, name='sent_messages'),
    
    # Notifications URL
    path('notifications/', views.notifications, name='student_notifications'),

    # Main academic management dashboard
    path('management/', views.academic_management, name='academic_management'),
    
    # Academic Year AJAX endpoints
    path('academics/api/academic-years/', views.get_academic_years, name='get_academic_years'),
    path('academics/api/academic-years/create/', views.create_academic_year, name='create_academic_year'),
    path('academics/api/academic-years/<int:year_id>/update/', views.update_academic_year, name='update_academic_year'),
    path('academics/api/academic-years/<int:year_id>/delete/', views.delete_academic_year, name='delete_academic_year'),
    path('academics/api/academic-years/<int:year_id>/set-current/', views.set_current_academic_year, name='set_current_academic_year'),
    
    # Semester AJAX endpoints
    path('academics/api/academic-years/<int:year_id>/semesters/create/', views.create_semester, name='create_semester'),
    path('academics/api/semesters/<int:semester_id>/update/', views.update_semester, name='update_semester'),
    path('academics/api/semesters/<int:semester_id>/delete/', views.delete_semester, name='delete_semester'),
    path('academics/api/semesters/<int:semester_id>/set-current/', views.set_current_semester, name='set_current_semester'),
    path('academics/api/semesters/<int:semester_id>/registrations/', views.get_semester_registrations, name='get_semester_registrations'),

    #Main hostel booking management view
    path('manage-bookings/', views.manage_hostel_bookings, name='manage_hostel_bookings'),
    
    # AJAX endpoints
    path('hostel/get-booking-data/', views.get_booking_data, name='get_booking_data'),
    path('hostel/get-room-availability/', views.get_room_availability, name='get_room_availability'),
    path('update-booking-status/', views.update_booking_status, name='update_booking_status'),

    # Admin Student Enrollment Management
    path('admin-students/enrollments/', views.admin_student_enrollment_list,   name='admin_student_enrollment_list'),
    # AJAX endpoints
    path('ajax/student/<int:student_id>/enrollments/',  views.get_student_enrollments,  name='get_student_enrollments'),
    path('ajax/enrollment/add/', views.add_student_enrollment, name='add_student_enrollment'),
    path('ajax/enrollment/<int:enrollment_id>/delete/',  views.delete_student_enrollment,  name='delete_student_enrollment'),
    path('ajax/semesters/options/', views.get_semester_options,  name='get_semester_options'),

    # Bulk enrollment AJAX endpoints
    path('ajax/programme/<int:programme_id>/students/', views.get_programme_students, name='get_programme_students'),
    path('ajax/programme/<int:programme_id>/courses/', views.get_programme_courses, name='get_programme_courses'),
    path('ajax/enrollment/bulk-add/', views.bulk_add_enrollments, name='bulk_add_enrollments'),

    # Optional: Lecturer assignment endpoint
    path('ajax/course/<int:course_id>/lecturers/', views.get_course_lecturers, name='get_course_lecturers'),

    path('department-list/', views.department_list, name='department_list'),
    path('department/create/', views.department_create, name='department_create'),
    path('department/<str:code>/', views.department_detail, name='department_detail'),
    path('department/<str:code>/update/', views.department_update, name='department_update'),
    path('department/<str:code>/delete/', views.department_delete, name='department_delete'),
    path('department/export/', views.department_export, name='department_export'),
    
    # AJAX endpoints
    path('department/api/<int:department_id>/programmes/', views.get_department_programmes, name='get_department_programmes'),


]