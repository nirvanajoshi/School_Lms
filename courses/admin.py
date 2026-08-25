from django.contrib import admin
from .models import Course, Enrollment, CourseMaterial, Schedule, Syllabus


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


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'material_type', 'week_number', 'is_published', 'created_at']
    list_filter = ['material_type', 'is_published', 'course', 'week_number']
    search_fields = ['title', 'description', 'course__code']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['course', 'week_number', '-created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['course', 'day_of_week', 'start_time', 'end_time', 'location', 'room', 'is_active']
    list_filter = ['day_of_week', 'course', 'is_active']
    search_fields = ['course__code', 'location', 'room']
    ordering = ['day_of_week', 'start_time']


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ['course', 'created_at', 'updated_at']
    search_fields = ['course__code', 'course__title', 'objectives']
    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
