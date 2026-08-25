from django.contrib import admin
from .models import Assignment, Submission, SubmissionAttachment, Grade


class SubmissionAttachmentInline(admin.TabularInline):
    model = SubmissionAttachment
    extra = 0
    readonly_fields = ['uploaded_at', 'file_size']


class GradeInline(admin.StackedInline):
    model = Grade
    extra = 0
    can_delete = False


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'status', 'submission_type', 'max_points', 'due_date', 'created_by']
    list_filter = ['status', 'submission_type', 'course', 'due_date']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'status', 'is_late', 'submitted_at']
    list_filter = ['status', 'is_late', 'assignment']
    search_fields = ['assignment__title', 'student__student_id', 'text_content']
    readonly_fields = ['submitted_at', 'updated_at', 'is_late']
    inlines = [SubmissionAttachmentInline, GradeInline]
    ordering = ['-submitted_at']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'points', 'graded_by', 'graded_at']
    list_filter = ['graded_by', 'graded_at']
    search_fields = ['submission__assignment__title', 'submission__student__student_id']
    readonly_fields = ['graded_at']
    ordering = ['-graded_at']
