from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Assignment(models.Model):
    """An assignment given to students in a course."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

    class SubmissionType(models.TextChoices):
        FILE = 'file', 'File Upload'
        TEXT = 'text', 'Text Entry'
        BOTH = 'both', 'File & Text'

    title = models.CharField(max_length=255)
    description = models.TextField()
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignments_created'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submission_type = models.CharField(
        max_length=20,
        choices=SubmissionType.choices,
        default=SubmissionType.BOTH
    )
    max_points = models.PositiveIntegerField(default=100)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Percentage weight of this assignment in final grade'
    )
    due_date = models.DateTimeField()
    allow_late_submissions = models.BooleanField(default=False)
    late_penalty_per_day = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Percentage deducted per day late'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        from django.utils import timezone
        return timezone.now() > self.due_date


class Submission(models.Model):
    """A student's submission for an assignment."""

    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
        RETURNED = 'returned', 'Returned for Revision'

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    text_content = models.TextField(blank=True, help_text='Text-based submission content')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    is_late = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, help_text='Instructor feedback')

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student} - {self.assignment.title}"

    def save(self, *args, **kwargs):
        if not self.pk:
            from django.utils import timezone
            self.is_late = timezone.now() > self.assignment.due_date
        super().save(*args, **kwargs)


class SubmissionAttachment(models.Model):
    """File attachments for a submission."""

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='assignments/submissions/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        if not self.file_size and self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class Grade(models.Model):
    """Grade for a submission."""

    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name='grade'
    )
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grades_given'
    )
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    graded_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['-graded_at']

    def __str__(self):
        return f"{self.submission} - {self.points}/{self.submission.assignment.max_points}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-update submission status
        self.submission.status = Submission.Status.GRADED
        self.submission.save(update_fields=['status'])
