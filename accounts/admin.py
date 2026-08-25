from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Department, Profile, Student, Instructor


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Student Details'


class InstructorInline(admin.StackedInline):
    model = Instructor
    can_delete = False
    verbose_name_plural = 'Instructor Details'


# Extend the default User admin
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'role', 'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    ordering = ['-created_at']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'year_level', 'gpa', 'enrollment_date']
    list_filter = ['year_level', 'enrollment_date']
    search_fields = ['student_id', 'profile__user__first_name', 'profile__user__last_name']
    ordering = ['student_id']

    @admin.display(description='Student Name')
    def full_name(self, obj):
        return obj.profile.full_name


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'rank', 'department', 'office_location']
    list_filter = ['rank', 'department']
    search_fields = ['employee_id', 'profile__user__first_name', 'profile__user__last_name']
    ordering = ['employee_id']

    @admin.display(description='Instructor Name')
    def full_name(self, obj):
        return obj.profile.full_name


# Re-register User admin with Profile inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
