from rest_framework import serializers
from .models import Assignment, Submission, SubmissionAttachment, Grade


class AssignmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'course', 'course_name',
            'created_by', 'created_by_name', 'status', 'submission_type',
            'max_points', 'weight', 'due_date', 'allow_late_submissions',
            'late_penalty_per_day', 'is_overdue', 'submission_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_submission_count(self, obj):
        return obj.submissions.count()


class SubmissionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAttachment
        fields = ['id', 'submission', 'file', 'filename', 'file_size', 'uploaded_at']
        read_only_fields = ['uploaded_at', 'file_size']


class GradeSerializer(serializers.ModelSerializer):
    graded_by_name = serializers.CharField(source='graded_by.get_full_name', read_only=True)
    max_points = serializers.IntegerField(source='submission.assignment.max_points', read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id', 'submission', 'graded_by', 'graded_by_name',
            'points', 'max_points', 'graded_at', 'comments'
        ]
        read_only_fields = ['graded_at']


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    student_name = serializers.CharField(source='student.profile.full_name', read_only=True)
    attachments = SubmissionAttachmentSerializer(many=True, read_only=True)
    grade = GradeSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_name',
            'text_content', 'submitted_at', 'updated_at', 'status',
            'is_late', 'feedback', 'attachments', 'grade'
        ]
        read_only_fields = ['submitted_at', 'updated_at', 'is_late']


class SubmissionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    student_name = serializers.CharField(source='student.profile.full_name', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_name',
            'status', 'is_late', 'submitted_at'
        ]
