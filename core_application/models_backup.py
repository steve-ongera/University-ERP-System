# Add these models to your existing models.py file

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class Timetable(models.Model):
    """Class timetable management"""
    DAYS_OF_WEEK = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    CLASS_TYPES = (
        ('lecture', 'Lecture'),
        ('tutorial', 'Tutorial'),
        ('practical', 'Practical'),
        ('seminar', 'Seminar'),
        ('fieldwork', 'Field Work'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetable_slots')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='teaching_slots')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=100)
    class_type = models.CharField(max_length=15, choices=CLASS_TYPES, default='lecture')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='timetable_slots')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    semester_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'programme', 'semester', 'year']
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['programme', 'year', 'semester']),
            models.Index(fields=['lecturer', 'day_of_week', 'start_time']),
            models.Index(fields=['day_of_week', 'start_time']),
        ]
    
    def clean(self):
        """Validate timetable entry"""
        super().clean()
        
        # Validate time range
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time.')
        
        # Check for lecturer conflicts
        lecturer_conflicts = Timetable.objects.filter(
            lecturer=self.lecturer,
            day_of_week=self.day_of_week,
            semester=self.semester,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            is_active=True
        ).exclude(pk=self.pk if self.pk else None)
        
        if lecturer_conflicts.exists():
            raise ValidationError(f'Lecturer {self.lecturer} has a conflicting class at this time.')
        
        # Check for venue conflicts
        venue_conflicts = Timetable.objects.filter(
            venue=self.venue,
            day_of_week=self.day_of_week,
            semester=self.semester,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            is_active=True
        ).exclude(pk=self.pk if self.pk else None)
        
        if venue_conflicts.exists():
            raise ValidationError(f'Venue {self.venue} is already booked at this time.')
        
        # Check for programme year conflicts (students can't be in two places at once)
        programme_conflicts = Timetable.objects.filter(
            programme=self.programme,
            year=self.year,
            day_of_week=self.day_of_week,
            semester=self.semester,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            is_active=True
        ).exclude(pk=self.pk if self.pk else None)
        
        if programme_conflicts.exists():
            raise ValidationError(f'Students in {self.programme} Year {self.year} have a conflicting class.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes"""
        if self.start_time and self.end_time:
            start_datetime = timezone.datetime.combine(timezone.datetime.today(), self.start_time)
            end_datetime = timezone.datetime.combine(timezone.datetime.today(), self.end_time)
            return int((end_datetime - start_datetime).total_seconds() / 60)
        return 0
    
    @property
    def time_display(self):
        """Format time for display"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def get_enrolled_students(self):
        """Get students enrolled in this course for this programme and year"""
        return Student.objects.filter(
            programme=self.programme,
            current_year=self.year,
            status='active',
            enrollments__course=self.course,
            enrollments__semester=self.semester,
            enrollments__is_active=True
        ).distinct()
    
    def __str__(self):
        return f"{self.course.code} - {self.get_day_of_week_display()} {self.time_display} - {self.venue}"

class Attendance(models.Model):
    """Student attendance tracking"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absence'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='marked_attendance')
    remarks = models.CharField(max_length=200, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'timetable_slot', 'date']
        ordering = ['-date', 'student__student_id']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['timetable_slot', 'date']),
            models.Index(fields=['date', 'status']),
        ]
    
    def clean(self):
        """Validate attendance record"""
        super().clean()
        
        # Ensure student is enrolled in the course
        if not Enrollment.objects.filter(
            student=self.student,
            course=self.timetable_slot.course,
            semester=self.timetable_slot.semester,
            is_active=True
        ).exists():
            raise ValidationError('Student is not enrolled in this course.')
        
        # Ensure attendance date is not in the future
        if self.date > timezone.now().date():
            raise ValidationError('Cannot mark attendance for future dates.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_late_marked(self):
        """Check if attendance was marked late (after class end time)"""
        if self.marked_at and self.timetable_slot.end_time:
            class_end = timezone.datetime.combine(self.date, self.timetable_slot.end_time)
            # Make it timezone-aware
            if timezone.is_naive(class_end):
                class_end = timezone.make_aware(class_end)
            return self.marked_at > class_end
        return False
    
    def __str__(self):
        return f"{self.student.student_id} - {self.timetable_slot.course.code} - {self.date} - {self.status}"

# Additional helper model for timetable statistics
class TimetableStats(models.Model):
    """Model to cache timetable statistics for performance"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    year = models.IntegerField()
    total_classes = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    courses_count = models.IntegerField(default=0)
    lecturers_count = models.IntegerField(default=0)
    venues_used = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['programme', 'semester', 'year']
    
    @classmethod
    def update_stats(cls, programme, semester, year):
        """Update statistics for a programme/semester/year combination"""
        timetable_entries = Timetable.objects.filter(
            programme=programme,
            semester=semester,
            year=year,
            is_active=True
        )
        
        total_classes = timetable_entries.count()
        total_hours = sum(entry.duration