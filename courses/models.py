from django.db import models
from django.conf import settings


class Course(models.Model):
    """A course offered by the institution."""

    class Semester(models.TextChoices):
        FALL = 'fall', 'Fall'
        SPRING = 'spring', 'Spring'
        SUMMER = 'summer', 'Summer'

    title = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.CASCADE,
        related_name='courses'
    )
    instructor = models.ForeignKey(
        'accounts.Instructor',
        on_delete=models.CASCADE,
        related_name='courses_teaching'
    )
    semester = models.CharField(max_length=10, choices=Semester.choices, default=Semester.FALL)
    year = models.PositiveIntegerField()
    max_enrollment = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'semester', 'code']
        unique_together = ['code', 'semester', 'year']

    def __str__(self):
        return f"{self.code} - {self.title}"


class Enrollment(models.Model):
    """Student enrollment in a course."""

    class Status(models.TextChoices):
        ENROLLED = 'enrolled', 'Enrolled'
        DROPPED = 'dropped', 'Dropped'
        COMPLETED = 'completed', 'Completed'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Final grade for the course'
    )

    class Meta:
        ordering = ['-enrolled_at']
        unique_together = ['course', 'student']

    def __str__(self):
        return f"{self.student} - {self.course}"


class CourseMaterial(models.Model):
    """Lecture notes, slides, and other course resources."""

    class MaterialType(models.TextChoices):
        LECTURE_NOTE = 'lecture_note', 'Lecture Note'
        SLIDE = 'slide', 'Slide'
        VIDEO = 'video', 'Video'
        DOCUMENT = 'document', 'Document'
        LINK = 'link', 'External Link'
        OTHER = 'other', 'Other'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices, default=MaterialType.DOCUMENT)
    file = models.FileField(upload_to='courses/materials/', blank=True, null=True)
    external_url = models.URLField(blank=True, help_text='URL for external resources')
    week_number = models.PositiveIntegerField(null=True, blank=True, help_text='Week this material belongs to')
    is_published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_materials_uploaded'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['week_number', '-created_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Schedule(models.Model):
    """Weekly class schedule/timetable for a course."""

    class DayOfWeek(models.TextChoices):
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        SUNDAY = 'sunday', 'Sunday'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    room = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name_plural = 'schedules'

    def __str__(self):
        return f"{self.course.code} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Syllabus(models.Model):
    """Course syllabus with detailed academic information."""

    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='syllabus')
    objectives = models.TextField(help_text='Course objectives and learning outcomes')
    prerequisites = models.TextField(blank=True, help_text='Required prior knowledge or courses')
    textbooks = models.TextField(blank=True, help_text='Required and recommended textbooks')
    grading_policy = models.TextField(blank=True, help_text='How grades are calculated')
    course_policies = models.TextField(blank=True, help_text='Attendance, late work, academic integrity policies')
    weekly_outline = models.TextField(blank=True, help_text='Week-by-week topic breakdown')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='syllabi_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'syllabi'

    def __str__(self):
        return f"Syllabus - {self.course.code}"
