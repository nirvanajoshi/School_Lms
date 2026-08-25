from django.db import models
from django.conf import settings


class AttendanceSession(models.Model):
    """A class session where attendance is taken."""

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    title = models.CharField(max_length=255, help_text='e.g., Week 1 - Introduction')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_sessions_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.date})"

    @property
    def total_expected(self):
        return self.course.enrollments.filter(status='enrolled').count()

    @property
    def total_present(self):
        return self.records.filter(status=AttendanceRecord.Status.PRESENT).count()

    @property
    def attendance_rate(self):
        expected = self.total_expected
        if expected == 0:
            return 0
        return round((self.total_present / expected) * 100, 1)


class AttendanceRecord(models.Model):
    """Individual student attendance for a session."""

    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        EXCUSED = 'excused', 'Excused'

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABSENT)
    check_in_time = models.TimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_recorded'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_at']
        unique_together = ['session', 'student']

    def __str__(self):
        return f"{self.student} - {self.session.title} ({self.get_status_display()})"


class AttendanceSummary(models.Model):
    """Aggregated attendance statistics per student per course."""

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    total_sessions = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-attendance_percentage']
        unique_together = ['student', 'course']
        verbose_name_plural = 'attendance summaries'

    def __str__(self):
        return f"{self.student} - {self.course} ({self.attendance_percentage}%)"

    def recalculate(self):
        """Recalculate attendance statistics from records."""
        records = AttendanceRecord.objects.filter(
            session__course=self.course,
            student=self.student
        )
        self.total_sessions = records.count()
        self.present_count = records.filter(status=AttendanceRecord.Status.PRESENT).count()
        self.absent_count = records.filter(status=AttendanceRecord.Status.ABSENT).count()
        self.late_count = records.filter(status=AttendanceRecord.Status.LATE).count()
        self.excused_count = records.filter(status=AttendanceRecord.Status.EXCUSED).count()

        # Count present + late + excused as "attended"
        attended = self.present_count + self.late_count + self.excused_count
        self.attendance_percentage = round(
            (attended / self.total_sessions * 100) if self.total_sessions > 0 else 0, 2
        )
        self.save()
