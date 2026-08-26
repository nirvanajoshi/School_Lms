from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Department, Profile, Student, Instructor


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'role', 'phone_number', 'date_of_birth',
            'address', 'profile_picture', 'department', 'department_name',
            'is_active', 'full_name', 'email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    email = serializers.CharField(source='profile.email', read_only=True)
    department_name = serializers.CharField(source='profile.department.name', read_only=True, default=None)
    advisor_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'profile', 'student_id', 'enrollment_date',
            'year_level', 'gpa', 'advisor', 'full_name', 'email',
            'department_name', 'advisor_name'
        ]

    def get_advisor_name(self, obj):
        if obj.advisor:
            return obj.advisor.profile.full_name
        return None


class InstructorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    email = serializers.CharField(source='profile.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Instructor
        fields = [
            'id', 'profile', 'employee_id', 'hire_date', 'rank',
            'department', 'department_name', 'office_location',
            'office_hours', 'full_name', 'email'
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']
        read_only_fields = ['id']
