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
