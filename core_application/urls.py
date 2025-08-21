from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Student authentication
    path('', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
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

    path('ajax/add-programme-year/', views.add_programme_year, name='ajax_add_programme_year'),
    path('ajax/add-programme-semester/', views.add_programme_semester, name='ajax_add_programme_semester'),
    path('ajax/add-programme-course/', views.add_programme_course, name='ajax_add_programme_course'),
    path('ajax/get-available-courses/', views.get_available_courses, name='ajax_get_available_courses'),
    path('ajax/remove-programme-course/', views.remove_programme_course, name='ajax_remove_programme_course'),

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
    path('admin-get-programme-courses/<int:programme_id>/', views.admin_get_programme_courses, name='admin_get_programme_courses'),
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
    path('departments/<str:code>/', views.department_detail, name='department_detail'),
    path('departments/<str:code>/update/', views.department_update, name='department_update'),
    path('departments/<str:code>/delete/', views.department_delete, name='department_delete'),
    path('departments/export/', views.department_export, name='department_export'),
    
    # AJAX endpoints
    path('departments/api/<int:department_id>/programmes/', views.get_department_programmes, name='get_department_programmes'),

    path('staff/', views.staff_list_view, name='staff_list'),
    
    # AJAX endpoints
    path('ajax/staff/list/', views.staff_ajax_list, name='staff_ajax_list'),
    path('ajax/staff/create/', views.staff_create_ajax, name='staff_create_ajax'),
    path('ajax/staff/<int:staff_id>/detail/', views.staff_detail_ajax, name='staff_detail_ajax'),
    path('ajax/staff/<int:staff_id>/update/', views.staff_update_ajax, name='staff_update_ajax'),
    path('ajax/staff/<int:staff_id>/delete/', views.staff_delete_ajax, name='staff_delete_ajax'),
    path('ajax/departments/', views.departments_ajax, name='departments_ajax'),


    # Student Reporting Management URLs
    path('admin-student-reporting/',  views.student_reporting_list,  name='student_reporting_list'),
    path('admin-student-reporting/<int:student_id>/', views.student_reporting_detail, name='student_reporting_detail'),
    path('admin-student-reporting/export/', views.export_reporting_data, name='export_reporting_data'),
    
    # AJAX endpoints
    path('ajax/process-student-report/', views.process_student_report, name='process_student_report'),  
    path('ajax/bulk-approve-reports/', views.bulk_approve_reports,  name='bulk_approve_reports'),

   # Main hostel management dashboard
    path('admin-hostel-management/', views.admin_hostel_management, name='admin_hostel_management'),                    
    path('admin-hostel-management/<int:hostel_id>/', views.hostel_detail_view, name='hostel_detail_view'),
    
    # AJAX endpoints for hostel management
    path('ajax/create-rooms-bulk/', views.create_rooms_bulk, name='create_rooms_bulk'),
    path('ajax/toggle-bed-maintenance/', views.toggle_bed_maintenance, name='toggle_bed_maintenance'),
    path('ajax/checkout-student/', views.checkout_student, name='checkout_student'),
    path('ajax/search-students/', views.search_students, name='search_students'),
    path('ajax/assign-bed-to-student/', views.assign_bed_to_student, name='assign_bed_to_student'),

    # Main booking management page
    path('bookings/', views.admin_hostel_bookings, name='admin_hostel_bookings'),
    
    # AJAX endpoints - Fixed URL patterns
     path('admin-hostel/bookings/details/<int:booking_id>/', views.booking_details_ajax, name='booking_details_ajax'),
     path('admin-hostel/bookings/update/<int:booking_id>/', views.update_booking_ajax, name='update_booking_ajax'),
     path('admin-hostel/bookings/delete/<int:booking_id>/', views.delete_booking_ajax, name='delete_booking_ajax'),  # Fixed: removed duplicate admin-hostel
     path('admin-hostel/bookings/stats/', views.booking_stats_ajax, name='booking_stats_ajax'),
     path('admin-hostel/bookings/bulk-update/', views.bulk_update_bookings_ajax, name='bulk_update_bookings_ajax'),

     # Student Exam Management URLs
    path('student-exams/', views.student_exam_programmes_list, name='student_exam_programmes_list'),
    path('student-exams/programme/<int:programme_id>/', views.student_exam_programme_detail, name='student_exam_programme_detail'),
    path('exams/course-students/<int:programme_id>/<int:course_id>/<int:semester_id>/', 
         views.course_exam_students_list, name='course_exam_students_list'),
    
    # AJAX endpoints
    path('api/programme/<int:programme_id>/academic-year/<int:academic_year_id>/year-data/', 
         views.get_programme_year_data, name='get_programme_year_data'),
    path('exams/ajax/academic-year-courses/<int:programme_id>/<int:academic_year_id>/<int:year>/<int:semester_num>/', 
     views.get_academic_year_courses, name='get_academic_year_courses'),
    
    # Download URLs
    path('exams/download-eligible-students/<int:programme_id>/<int:course_id>/<int:semester_id>/', 
         views.download_eligible_students_csv, name='download_eligible_students_csv'),
    path('exams/download-all-students/<int:programme_id>/<int:course_id>/<int:semester_id>/', 
         views.download_all_students_csv, name='download_all_students_csv'),

     # Student transcript management URLs
    path('admin-students/search/', views.student_search, name='student_search'),
    path('admin-students/<str:student_id>/transcript/', views.admin_student_transcript, name='admin_student_transcript'),
    path('admin-students/<str:student_id>/transcript/download/', views.download_transcript_pdf, name='download_transcript_pdf'),
    path('admin-students/<str:student_id>/certificate/download/', views.download_certificate_pdf, name='download_certificate_pdf'),


    path('books/', views.library_book_management, name='book_management'),
    path('issuance/', views.library_issuance, name='issuance_management'),
    path('library/api/books/create/', views.create_book, name='create_book'),
    path('library/api/books/<int:book_id>/update/', views.update_book, name='update_book'),
    path('library/api/books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path('library/api/books/<int:book_id>/details/', views.get_book_details, name='get_book_details'),
    path('library/api/transactions/create/', views.create_transaction, name='create_transaction'),
    path('library/api/transactions/<int:transaction_id>/return/', views.return_book, name='return_book'),
    path('library/api/transactions/<int:transaction_id>/details/', views.get_transaction_details, name='get_transaction_details'),

    path('admin-events/', views.event_list, name='event_list'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/<int:event_id>/update/', views.update_event, name='update_event'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('events/<int:event_id>/details/', views.get_event_details, name='get_event_details'),

    # Club Management URLs
    path('admin-clubs/', views.clubs_management, name='clubs_management'),
    path('admin-clubs/create/', views.create_club, name='create_club'),
    path('admin-clubs/<int:club_id>/', views.get_club, name='get_club'),
    path('admin-clubs/<int:club_id>/update/', views.update_club, name='update_club'),
    path('admin-clubs/<int:club_id>/delete/', views.delete_club, name='delete_club'),
    
    # Club Events Management URLs
    path('admin-club-events/', views.club_events_management, name='club_events_management'),
    path('admin-club-events/create/', views.create_club_event, name='create_club_event'),
    path('admin-club-events/<int:event_id>/', views.get_club_event, name='get_club_event'),
    path('admin-club-events/<int:event_id>/update/', views.update_club_event, name='update_club_event'),
    path('admin-club-events/<int:event_id>/delete/', views.delete_club_event, name='delete_club_event'),

     # Admin/Staff Comment Management URLs
    path('admin-student-comments/', views.student_comments_management, name='student_comments_management'),
    path('admin-student-comments/<int:comment_id>/', views.get_student_comment, name='get_student_comment'),
    path('admin-student-comments/<int:comment_id>/respond/', views.add_admin_response, name='add_admin_response'),
    path('admin-student-comments/<int:comment_id>/update-response/', views.update_admin_response, name='update_admin_response'),
    path('admin-student-comments/<int:comment_id>/toggle-status/', views.toggle_comment_status, name='toggle_comment_status'),
    path('admin-student-comments/<int:comment_id>/delete/', views.delete_student_comment, name='delete_student_comment'),
    path('admin-student-comments/bulk-action/', views.bulk_action_comments, name='bulk_action_comments'),


]