from rest_framework import serializers
from .models import AttendanceSession, AttendanceRecord, AttendanceSummary


class AttendanceSessionSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    total_expected = serializers.ReadOnlyField()
    total_present = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()
    records = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course', 'course_code', 'course_name', 'title', 'date',
            'start_time', 'end_time', 'location', 'status', 'notes',
            'created_by', 'created_by_name', 'total_expected', 'total_present',
            'attendance_rate', 'records', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_records(self, obj):
        records = obj.records.all()
        return AttendanceRecordSerializer(records, many=True).data


class AttendanceSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    course_code = serializers.CharField(source='course.code', read_only=True)
    total_expected = serializers.ReadOnlyField()
    total_present = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course', 'course_code', 'title', 'date',
            'start_time', 'end_time', 'status', 'total_expected',
            'total_present', 'attendance_rate', 'created_at'
        ]


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.profile.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'session', 'student', 'student_name', 'student_id',
            'status', 'check_in_time', 'notes', 'recorded_by',
            'recorded_by_name', 'recorded_at', 'updated_at'
        ]
        read_only_fields = ['recorded_at', 'updated_at']


class AttendanceSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.profile.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = AttendanceSummary
        fields = [
            'id', 'student', 'student_name', 'student_id',
            'course', 'course_code', 'course_name',
            'total_sessions', 'present_count', 'absent_count',
            'late_count', 'excused_count', 'attendance_percentage',
            'last_updated'
        ]
        read_only_fields = ['last_updated']
