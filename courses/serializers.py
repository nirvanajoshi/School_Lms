from rest_framework import serializers
from .models import Course, Enrollment, CourseMaterial, Schedule, Syllabus


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = [
            'id', 'course', 'day_of_week', 'start_time', 'end_time',
            'location', 'room', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class CourseMaterialSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = CourseMaterial
        fields = [
            'id', 'course', 'title', 'description', 'material_type',
            'file', 'external_url', 'week_number', 'is_published',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SyllabusSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Syllabus
        fields = [
            'id', 'course', 'course_code', 'course_title', 'objectives',
            'prerequisites', 'textbooks', 'grading_policy', 'course_policies',
            'weekly_outline', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.profile.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_code', 'course_name', 'student',
            'student_name', 'student_id', 'status', 'enrolled_at', 'grade'
        ]
        read_only_fields = ['enrolled_at']


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    student_name = serializers.CharField(source='student.profile.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'student', 'student_name', 'student_id',
            'status', 'enrolled_at', 'grade'
        ]


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.profile.full_name', read_only=True)
    enrollment_count = serializers.SerializerMethodField()
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'code', 'description', 'department', 'department_name',
            'instructor', 'instructor_name', 'semester', 'year', 'max_enrollment',
            'is_active', 'enrollment_count', 'available_spots', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_enrollment_count(self, obj):
        return obj.enrollments.filter(status=Enrollment.Status.ENROLLED).count()

    def get_available_spots(self, obj):
        enrolled = obj.enrollments.filter(status=Enrollment.Status.ENROLLED).count()
        return max(0, obj.max_enrollment - enrolled)


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.profile.full_name', read_only=True)
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'code', 'department', 'department_name',
            'instructor', 'instructor_name', 'semester', 'year',
            'is_active', 'enrollment_count', 'created_at'
        ]

    def get_enrollment_count(self, obj):
        return obj.enrollments.filter(status=Enrollment.Status.ENROLLED).count()
