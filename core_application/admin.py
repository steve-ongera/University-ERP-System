from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Faculty, Department, Programme, Course, ProgrammeCourse,
    Lecturer, Student, Staff, AcademicYear, Semester, StudentReporting,
    Enrollment, Grade, FeeStructure, FeePayment, Research, Library,
    LibraryTransaction, Hostel, Room, Bed, HostelBooking, HostelPayment,
    HostelIncident, Examination, Timetable, Attendance, Notification
)

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'gender', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'national_id')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'address', 'gender', 'date_of_birth', 
                      'profile_picture', 'national_id')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'address', 'gender', 'date_of_birth', 
                      'profile_picture', 'national_id')
        }),
    )

# Academic Structure Admin
class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 0
    fields = ('name', 'code', 'head_of_department', 'is_active')

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'dean', 'department_count', 'is_active', 'established_date')
    list_filter = ('is_active', 'established_date')
    search_fields = ('name', 'code', 'description')
    inlines = [DepartmentInline]
    
    def department_count(self, obj):
        return obj.departments.count()
    department_count.short_description = 'Departments'

class ProgrammeInline(admin.TabularInline):
    model = Programme
    extra = 0
    fields = ('name', 'code', 'programme_type', 'study_mode', 'is_active')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty', 'head_of_department', 'programme_count', 'is_active')
    list_filter = ('faculty', 'is_active', 'established_date')
    search_fields = ('name', 'code', 'description')
    inlines = [ProgrammeInline]
    
    def programme_count(self, obj):
        return obj.programmes.count()
    programme_count.short_description = 'Programmes'

class ProgrammeCourseInline(admin.TabularInline):
    model = ProgrammeCourse
    extra = 0
    fields = ('course', 'year', 'semester', 'is_mandatory', 'is_active')

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'programme_type', 'study_mode', 'department', 
                   'duration_years', 'total_semesters', 'student_count', 'is_active')
    list_filter = ('programme_type', 'study_mode', 'department__faculty', 'department', 'is_active')
    search_fields = ('name', 'code', 'description')
    inlines = [ProgrammeCourseInline]
    
    def student_count(self, obj):
        return obj.students.filter(status='active').count()
    student_count.short_description = 'Active Students'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'course_type', 'level', 'credit_hours', 
                   'department', 'total_contact_hours', 'enrollment_count', 'is_active')
    list_filter = ('course_type', 'level', 'department__faculty', 'department', 'is_active')
    search_fields = ('name', 'code', 'description')
    filter_horizontal = ('prerequisites',)
    
    def enrollment_count(self, obj):
        return obj.enrollments.filter(is_active=True).count()
    enrollment_count.short_description = 'Current Enrollments'

@admin.register(ProgrammeCourse)
class ProgrammeCourseAdmin(admin.ModelAdmin):
    list_display = ('programme', 'course', 'year', 'semester', 'is_mandatory', 'is_active')
    list_filter = ('programme__programme_type', 'year', 'semester', 'is_mandatory', 'is_active')
    search_fields = ('programme__name', 'course__name', 'programme__code', 'course__code')

# People Admin
@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'employee_number', 'department', 'academic_rank', 
                   'employment_type', 'teaching_experience_years', 'is_active')
    list_filter = ('academic_rank', 'employment_type', 'department__faculty', 'department', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'employee_number')
    readonly_fields = ('user',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_number', 'department', 'academic_rank', 'employment_type')
        }),
        ('Academic Qualifications', {
            'fields': ('highest_qualification', 'university_graduated', 'graduation_year', 
                      'research_interests', 'publications')
        }),
        ('Professional Information', {
            'fields': ('professional_registration', 'teaching_experience_years', 
                      'research_experience_years', 'industry_experience_years')
        }),
        ('Employment Details', {
            'fields': ('salary', 'joining_date', 'contract_end_date', 'office_location', 
                      'office_phone', 'consultation_hours', 'is_active')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'student_id', 'programme', 'current_year', 
                   'current_semester', 'status', 'cumulative_gpa', 'sponsor_type')
    list_filter = ('status', 'programme__programme_type', 'programme', 'current_year', 
                   'current_semester', 'sponsor_type', 'admission_type')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'student_id')
    readonly_fields = ('user',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'student_id', 'programme', 'current_year', 'current_semester', 'status')
        }),
        ('Admission Information', {
            'fields': ('admission_date', 'admission_type', 'sponsor_type', 'entry_qualification', 
                      'entry_points', 'expected_graduation_date')
        }),
        ('Academic Progress', {
            'fields': ('cumulative_gpa', 'total_credit_hours')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_relationship', 
                      'guardian_address', 'emergency_contact')
        }),
        ('Additional Information', {
            'fields': ('blood_group', 'medical_conditions', 'accommodation_type')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'employee_number', 'staff_category', 'designation', 
                   'department', 'joining_date', 'is_active')
    list_filter = ('staff_category', 'department', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'employee_number')
    readonly_fields = ('user',)
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'

# Academic Records Admin
class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 0
    fields = ('semester_number', 'start_date', 'end_date', 'is_current')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_current', 'semester_count')
    list_filter = ('is_current',)
    inlines = [SemesterInline]
    
    def semester_count(self, obj):
        return obj.semesters.count()
    semester_count.short_description = 'Semesters'

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester_number', 'start_date', 'end_date', 
                   'registration_start_date', 'registration_end_date', 'is_current')
    list_filter = ('academic_year', 'semester_number', 'is_current')

@admin.register(StudentReporting)
class StudentReportingAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'reporting_type', 'reporting_date', 'status', 'processed_by')
    list_filter = ('reporting_type', 'status', 'semester__academic_year', 'semester')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('reporting_date',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'lecturer', 'is_active', 'is_repeat', 'enrollment_date')
    list_filter = ('semester__academic_year', 'semester', 'course__department', 'is_active', 'is_repeat', 'is_audit')
    search_fields = ('student__student_id', 'course__code', 'course__name')
    readonly_fields = ('enrollment_date',)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_course', 'get_semester', 'continuous_assessment', 
                   'final_exam', 'total_marks', 'grade', 'grade_points', 'is_passed')
    list_filter = ('grade', 'is_passed', 'enrollment__semester__academic_year', 
                   'enrollment__course__department')
    search_fields = ('enrollment__student__student_id', 'enrollment__course__code')
    readonly_fields = ('total_marks', 'grade', 'grade_points', 'quality_points', 'is_passed')
    
    def get_student(self, obj):
        return obj.enrollment.student.student_id
    get_student.short_description = 'Student ID'
    
    def get_course(self, obj):
        return obj.enrollment.course.code
    get_course.short_description = 'Course'
    
    def get_semester(self, obj):
        return str(obj.enrollment.semester)
    get_semester.short_description = 'Semester'

# Fee Management Admin
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('programme', 'academic_year', 'year', 'semester', 'tuition_fee', 
                   'total_fee', 'net_fee', 'payment_count')
    list_filter = ('academic_year', 'programme__programme_type', 'programme', 'year', 'semester')
    search_fields = ('programme__name', 'programme__code')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('programme', 'academic_year', 'year', 'semester')
        }),
        ('Fee Components', {
            'fields': ('tuition_fee', 'registration_fee', 'examination_fee', 'library_fee', 
                      'laboratory_fee', 'fieldwork_fee', 'technology_fee', 'accommodation_fee', 
                      'meals_fee', 'medical_fee', 'insurance_fee', 'student_union_fee', 
                      'sports_fee', 'graduation_fee', 'other_fees')
        }),
        ('Financial Aid', {
            'fields': ('government_subsidy', 'scholarship_amount')
        }),
    )
    
    def payment_count(self, obj):
        return obj.payments.count()
    payment_count.short_description = 'Payments Made'

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'receipt_number', 'amount_paid', 'payment_date', 
                   'payment_method', 'payment_status', 'processed_by')
    list_filter = ('payment_method', 'payment_status', 'payment_date', 
                   'fee_structure__academic_year')
    search_fields = ('student__student_id', 'receipt_number', 'transaction_reference', 'mpesa_receipt')
    readonly_fields = ('receipt_number',)

# Research and Library Admin
@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('title', 'research_type', 'principal_investigator', 'department', 
                   'status', 'start_date', 'funding_amount')
    list_filter = ('research_type', 'status', 'department__faculty', 'department', 
                   'ethics_approval', 'start_date')
    search_fields = ('title', 'abstract', 'keywords', 'principal_investigator__user__first_name')
    filter_horizontal = ('co_investigators', 'students')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'research_type', 'principal_investigator', 'department', 'status')
        }),
        ('Collaborators', {
            'fields': ('co_investigators', 'students')
        }),
        ('Timeline', {
            'fields': ('start_date', 'expected_end_date', 'actual_end_date')
        }),
        ('Content', {
            'fields': ('abstract', 'keywords')
        }),
        ('Funding', {
            'fields': ('funding_amount', 'funding_source')
        }),
        ('Approval', {
            'fields': ('ethics_approval',)
        }),
    )

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'resource_type', 'total_copies', 'available_copies', 
                   'call_number', 'is_available', 'publication_year')
    list_filter = ('resource_type', 'is_available', 'publication_year', 'subject_area')
    search_fields = ('title', 'author', 'isbn', 'call_number', 'subject_area')
    
    def get_availability_status(self, obj):
        if obj.available_copies > 0:
            return format_html('<span style="color: green;">Available ({})</span>', obj.available_copies)
        else:
            return format_html('<span style="color: red;">Not Available</span>')
    get_availability_status.short_description = 'Availability'

@admin.register(LibraryTransaction)
class LibraryTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'library_resource', 'transaction_type', 'transaction_date', 
                   'due_date', 'return_date', 'status', 'fine_amount')
    list_filter = ('transaction_type', 'status', 'transaction_date', 'due_date')
    search_fields = ('user__username', 'library_resource__title', 'library_resource__call_number')
    readonly_fields = ('transaction_date',)
    
    def get_overdue_status(self, obj):
        if obj.status == 'overdue':
            return format_html('<span style="color: red;">OVERDUE</span>')
        return obj.status
    get_overdue_status.short_description = 'Status'

# Custom Admin Site Configuration
admin.site.site_header = "University Management System"
admin.site.site_title = "UMS Admin"
admin.site.index_title = "Welcome to University Management System Administration"

# Hostel/Accommodation Admin
class RoomInline(admin.TabularInline):
    model = Room
    extra = 0
    fields = ('room_number', 'floor', 'capacity', 'is_active')

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostel_type', 'school', 'warden', 'total_rooms', 
                   'get_available_rooms', 'is_active')
    list_filter = ('hostel_type', 'school', 'is_active')
    search_fields = ('name', 'description')
    inlines = [RoomInline]
    
    def get_available_rooms(self, obj):
        # Get current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            return obj.get_available_rooms_count(current_year)
        return "N/A"
    get_available_rooms.short_description = 'Available Rooms'

class BedInline(admin.TabularInline):
    model = Bed
    extra = 0
    fields = ('bed_position', 'bed_number', 'academic_year', 'is_available', 'maintenance_status')
    readonly_fields = ('bed_number',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'room_number', 'floor', 'capacity', 'get_available_beds', 'is_active')
    list_filter = ('hostel__hostel_type', 'hostel', 'floor', 'is_active')
    search_fields = ('room_number', 'hostel__name')
    inlines = [BedInline]
    
    def get_available_beds(self, obj):
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            return obj.get_available_beds_count(current_year)
        return "N/A"
    get_available_beds.short_description = 'Available Beds'

@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room', 'academic_year', 'bed_position', 
                   'is_available', 'maintenance_status')
    list_filter = ('academic_year', 'is_available', 'maintenance_status', 
                   'room__hostel__hostel_type', 'room__hostel')
    search_fields = ('bed_number', 'room__room_number', 'room__hostel__name')
    readonly_fields = ('bed_number',)

class HostelPaymentInline(admin.TabularInline):
    model = HostelPayment
    extra = 0
    fields = ('amount', 'payment_date', 'payment_method', 'receipt_number')
    readonly_fields = ('receipt_number',)

@admin.register(HostelBooking)
class HostelBookingAdmin(admin.ModelAdmin):
    list_display = ('student', 'bed', 'academic_year', 'booking_status', 'payment_status', 
                   'booking_fee', 'amount_paid', 'balance_due', 'booking_date')
    list_filter = ('booking_status', 'payment_status', 'academic_year', 
                   'bed__room__hostel__hostel_type', 'bed__room__hostel')
    search_fields = ('student__student_id', 'student__user__first_name', 
                    'student__user__last_name', 'bed__bed_number')
    readonly_fields = ('booking_date', 'balance_due', 'is_fully_paid')
    inlines = [HostelPaymentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'bed', 'academic_year', 'booking_fee')
        }),
        ('Booking Status', {
            'fields': ('booking_status', 'payment_status', 'amount_paid', 'balance_due', 'is_fully_paid')
        }),
        ('Dates', {
            'fields': ('booking_date', 'check_in_date', 'check_out_date', 'expected_checkout_date')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_date', 'approval_remarks')
        }),
        ('Check-in/out', {
            'fields': ('checked_in_by', 'checked_out_by')
        }),
        ('Additional Info', {
            'fields': ('remarks',)
        }),
    )

@admin.register(HostelPayment)
class HostelPaymentAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'booking', 'amount', 'payment_date', 
                   'payment_method', 'receipt_number', 'received_by')
    list_filter = ('payment_method', 'payment_date', 'booking__academic_year')
    search_fields = ('booking__student__student_id', 'receipt_number', 'reference_number')
    readonly_fields = ('receipt_number',)
    
    def get_student(self, obj):
        return obj.booking.student.student_id
    get_student.short_description = 'Student ID'

@admin.register(HostelIncident)
class HostelIncidentAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'incident_type', 'severity', 'status', 'incident_date', 
                   'fine_amount', 'fine_paid', 'reported_by')
    list_filter = ('incident_type', 'severity', 'status', 'fine_paid', 'incident_date')
    search_fields = ('booking__student__student_id', 'description')
    
    fieldsets = (
        ('Incident Details', {
            'fields': ('booking', 'incident_type', 'severity', 'status', 'incident_date', 'description')
        }),
        ('Action & Resolution', {
            'fields': ('action_taken', 'reported_by', 'handled_by')
        }),
        ('Financial', {
            'fields': ('fine_amount', 'fine_paid')
        }),
    )
    
    def get_student(self, obj):
        return obj.booking.student.student_id
    get_student.short_description = 'Student ID'

# Examination Admin
@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ('course', 'exam_type', 'exam_date', 'start_time', 'duration_minutes', 
                   'venue', 'max_marks', 'is_published', 'created_by')
    list_filter = ('exam_type', 'is_published', 'exam_date', 'semester__academic_year', 
                   'course__department')
    search_fields = ('course__name', 'course__code', 'venue')
    filter_horizontal = ('invigilators',)
    readonly_fields = ('end_time',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'semester', 'exam_type', 'max_marks')
        }),
        ('Schedule', {
            'fields': ('exam_date', 'start_time', 'duration_minutes', 'end_time', 'venue')
        }),
        ('Supervision', {
            'fields': ('invigilators', 'created_by')
        }),
        ('Content', {
            'fields': ('instructions', 'is_published')
        }),
    )

# Timetable Admin
@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('course', 'programme', 'year', 'semester_number', 'day_of_week', 
                   'start_time', 'end_time', 'venue', 'lecturer', 'class_type', 'is_active')
    list_filter = ('semester__academic_year', 'programme', 'year', 'semester_number', 
                   'day_of_week', 'class_type', 'is_active')
    search_fields = ('course__name', 'course__code', 'venue', 'lecturer__user__first_name')
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'lecturer', 'programme', 'class_type')
        }),
        ('Academic Period', {
            'fields': ('semester', 'year', 'semester_number')
        }),
        ('Schedule', {
            'fields': ('day_of_week', 'start_time', 'end_time', 'venue')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_course', 'date', 'status', 'marked_by', 'marked_at')
    list_filter = ('status', 'date', 'timetable_slot__course__department', 
                   'timetable_slot__semester__academic_year')
    search_fields = ('student__student_id', 'student__user__first_name', 
                    'timetable_slot__course__code')
    readonly_fields = ('marked_at',)
    
    def get_course(self, obj):
        return obj.timetable_slot.course.code
    get_course.short_description = 'Course'

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'priority', 'sender', 'recipient_count', 
                   'is_read', 'send_email', 'send_sms', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'send_email', 'send_sms', 'created_at')
    search_fields = ('title', 'message', 'sender__username')
    filter_horizontal = ('recipients',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Message Content', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Sender & Recipients', {
            'fields': ('sender', 'recipients')
        }),
        ('Delivery Options', {
            'fields': ('send_email', 'send_sms', 'scheduled_time', 'expires_at')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def recipient_count(self, obj):
        return obj.recipients.count()
    recipient_count.short_description = 'Recipients'

# Custom admin actions
def mark_as_read(modeladmin, request, queryset):
    queryset.update(is_read=True)
mark_as_read.short_description = "Mark selected notifications as read"

def approve_bookings(modeladmin, request, queryset):
    for booking in queryset:
        if booking.booking_status == 'pending':
            booking.booking_status = 'approved'
            booking.approved_by = request.user
            booking.approval_date = timezone.now()
            booking.save()
approve_bookings.short_description = "Approve selected hostel bookings"

def reject_bookings(modeladmin, request, queryset):
    for booking in queryset:
        if booking.booking_status == 'pending':
            booking.booking_status = 'rejected'
            booking.approved_by = request.user
            booking.approval_date = timezone.now()
            booking.save()
reject_bookings.short_description = "Reject selected hostel bookings"

# Add actions to admin classes
NotificationAdmin.actions = [mark_as_read]
HostelBookingAdmin.actions = [approve_bookings, reject_bookings]

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    NewsArticle, StudentComment, CommonQuestion, QuickLink,
    StudentClub, ClubMembership, ClubEvent, Event, EventRegistration
)


# ----------------- NEWS ARTICLE -----------------
@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'publish_date', 'is_published')
    list_filter = ('category', 'is_published', 'publish_date')
    search_fields = ('title', 'summary', 'content', 'author__username')
    date_hierarchy = 'publish_date'
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-publish_date',)


# ----------------- STUDENT COMMENT -----------------
@admin.register(StudentComment)
class StudentCommentAdmin(admin.ModelAdmin):
    list_display = ('student', 'comment_snippet', 'is_resolved', 'created_at', 'responded_by')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('student__student_id', 'comment', 'admin_response')
    readonly_fields = ('created_at', 'updated_at')

    def comment_snippet(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_snippet.short_description = "Comment"


# ----------------- COMMON QUESTIONS -----------------
class CommonQuestionAdmin(admin.ModelAdmin):
    list_display = ('order', 'question', 'is_active')
    list_display_links = ('question',)
    list_editable = ('order',)


# ----------------- QUICK LINKS -----------------
class QuickLinkAdmin(admin.ModelAdmin):
    list_display = ('order', 'title', 'url')
    list_display_links = ('title',)
    list_editable = ('order',)


# ----------------- CLUB MEMBERSHIP INLINE -----------------
class ClubMembershipInline(admin.TabularInline):
    model = ClubMembership
    extra = 1


# ----------------- STUDENT CLUB -----------------
@admin.register(StudentClub)
class StudentClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'chairperson', 'contact_phone', 'email', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'chairperson__username', 'email')
    inlines = [ClubMembershipInline]


# ----------------- CLUB EVENTS -----------------
@admin.register(ClubEvent)
class ClubEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'start_datetime', 'end_datetime', 'status')
    list_filter = ('status', 'club', 'start_datetime')
    search_fields = ('title', 'description', 'club__name')
    date_hierarchy = 'start_datetime'
    readonly_fields = ('created_at', 'updated_at')


# ----------------- EVENTS -----------------
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'venue', 'is_public')
    list_filter = ('event_type', 'is_public', 'start_date')
    search_fields = ('title', 'description', 'venue')
    date_hierarchy = 'start_date'


# ----------------- EVENT REGISTRATIONS -----------------
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registration_date', 'is_attended')
    list_filter = ('is_attended', 'registration_date')
    search_fields = ('event__title', 'user__username')
    date_hierarchy = 'registration_date'

# Update admin site header for additional models
admin.site.site_header = "University Management System - Complete"
admin.site.site_title = "UMS Admin Portal"
admin.site.index_title = "Welcome to University Management System Administration"