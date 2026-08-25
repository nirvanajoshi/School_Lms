from django.contrib import admin
from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'department', 'instructor', 'semester', 'year', 'is_active']
    list_filter = ['semester', 'year', 'department', 'is_active']
    search_fields = ['code', 'title', 'description']
    ordering = ['-year', 'semester', 'code']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'grade', 'enrolled_at']
    list_filter = ['status', 'course', 'enrolled_at']
    search_fields = ['student__student_id', 'course__code', 'course__title']
    ordering = ['-enrolled_at']
