from django.db import models
from django.conf import settings


class Category(models.Model):
    """Category for organizing announcements."""

    class Type(models.TextChoices):
        GENERAL = 'general', 'General'
        ACADEMIC = 'academic', 'Academic'
        EVENT = 'event', 'Event'
        URGENT = 'urgent', 'Urgent'
        ADMINISTRATIVE = 'administrative', 'Administrative'

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.GENERAL)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Announcement(models.Model):
    """System-wide or targeted announcements."""

    class Priority(models.IntegerChoices):
        LOW = 1, 'Low'
        NORMAL = 2, 'Normal'
        HIGH = 3, 'High'
        URGENT = 4, 'Urgent'

    class TargetAudience(models.TextChoices):
        ALL = 'all', 'Everyone'
        STUDENTS = 'students', 'Students'
        INSTRUCTORS = 'instructors', 'Instructors'
        ADMINS = 'admins', 'Administrators'

    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements'
    )
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL)
    target_audience = models.CharField(
        max_length=20,
        choices=TargetAudience.choices,
        default=TargetAudience.ALL
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_published:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True


class AnnouncementAttachment(models.Model):
    """File attachments for announcements."""

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='announcements/attachments/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        super().save(*args, **kwargs)
