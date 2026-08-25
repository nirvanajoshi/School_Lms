from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord, AttendanceSummary


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ['recorded_at', 'updated_at']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'date', 'start_time', 'end_time', 'status', 'attendance_rate']
    list_filter = ['status', 'course', 'date']
    search_fields = ['title', 'course__code', 'course__title', 'location']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AttendanceRecordInline]
    ordering = ['-date', '-start_time']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Attendance %')
    def attendance_rate(self, obj):
        return f"{obj.attendance_rate}%"


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'check_in_time', 'recorded_at']
    list_filter = ['status', 'session__course', 'session__date']
    search_fields = ['student__student_id', 'session__title', 'notes']
    readonly_fields = ['recorded_at', 'updated_at']
    ordering = ['-recorded_at']


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'total_sessions', 'present_count', 'absent_count', 'attendance_percentage']
    list_filter = ['course', 'attendance_percentage']
    search_fields = ['student__student_id', 'course__code']
    readonly_fields = ['last_updated']
    ordering = ['-attendance_percentage']
