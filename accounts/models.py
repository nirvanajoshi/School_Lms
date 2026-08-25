from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Department(models.Model):
    """Academic department within the institution."""

    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Profile(models.Model):
    """Extended user profile linked to Django's built-in User model."""

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        INSTRUCTOR = 'instructor', 'Instructor'
        ADMIN = 'admin', 'Admin'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email


class Student(models.Model):
    """Student-specific data linked to a Profile."""

    class YearLevel(models.IntegerChoices):
        FRESHMAN = 1, 'Freshman'
        SOPHOMORE = 2, 'Sophomore'
        JUNIOR = 3, 'Junior'
        SENIOR = 4, 'Senior'

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='student_detail')
    student_id = models.CharField(max_length=20, unique=True)
    enrollment_date = models.DateField()
    year_level = models.IntegerField(choices=YearLevel.choices, default=YearLevel.FRESHMAN)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    advisor = models.ForeignKey(
        'Instructor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advisees'
    )

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f"{self.student_id} - {self.profile.full_name}"


class Instructor(models.Model):
    """Instructor-specific data linked to a Profile."""

    class Rank(models.TextChoices):
        LECTURER = 'lecturer', 'Lecturer'
        ASSISTANT_PROFESSOR = 'assistant_professor', 'Assistant Professor'
        ASSOCIATE_PROFESSOR = 'associate_professor', 'Associate Professor'
        PROFESSOR = 'professor', 'Professor'

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='instructor_detail')
    employee_id = models.CharField(max_length=20, unique=True)
    hire_date = models.DateField()
    rank = models.CharField(max_length=30, choices=Rank.choices, default=Rank.LECTURER)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='instructors'
    )
    office_location = models.CharField(max_length=100, blank=True)
    office_hours = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.profile.full_name}"


# Signals to auto-create Profile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
