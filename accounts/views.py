from django.contrib.auth.models import User
from django.db import models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response

from .models import Department, Profile, Student, Instructor
from .serializers import (
    DepartmentSerializer,
    ProfileSerializer,
    StudentSerializer,
    InstructorSerializer,
    UserSerializer,
)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class IsAdminOrReadOnly(IsAuthenticated):
    """Admin can write; everyone else can only read."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return super().has_permission(request, view)
        return super().has_permission(request, view) and request.user.is_staff


class IsAdminOrInstructor(IsAuthenticated):
    """Allow admin and instructor roles."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role in ("admin", "instructor")


class IsOwnerOrAdmin(IsAuthenticated):
    """Object-level: owner of the profile or admin can mutate."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Admin can edit anyone
        if request.user.is_staff:
            return True
        # For Profile objects, check the user field
        if hasattr(obj, "user"):
            return obj.user == request.user
        # For other objects, check created_by or profile.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        return False


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    CRUD for departments.

    * **list / retrieve** – any authenticated user
    * **create / update / destroy** – admin only
    """

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["code"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["name", "code", "created_at"]

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def instructors(self, request, pk=None):
        """List all instructors in this department."""
        department = self.get_object()
        instructors = Instructor.objects.filter(department=department).select_related(
            "profile", "profile__user"
        )
        page = self.paginate_queryset(instructors)
        if page is not None:
            serializer = InstructorSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InstructorSerializer(instructors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def students(self, request, pk=None):
        """List all students whose profile is in this department."""
        department = self.get_object()
        students = Student.objects.filter(
            profile__department=department
        ).select_related("profile", "profile__user", "profile__department")
        page = self.paginate_queryset(students)
        if page is not None:
            serializer = StudentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileViewSet(viewsets.ModelViewSet):
    """
    Manage user profiles.

    * **list** – admin only
    * **retrieve** – admin or own profile
    * **update / partial_update** – admin or own profile (limited fields for non-admin)
    * **destroy** – admin only
    * **`/me/`** – returns the current user's profile
    """

    queryset = Profile.objects.select_related("user", "department").all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["role", "is_active", "department"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "phone_number"]
    ordering_fields = ["role", "created_at"]
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ("list",):
            return [IsAdminUser()]
        if self.action in ("destroy",):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Non-admin users can only see their own profile via detail views
        if not user.is_staff:
            return qs.filter(user=user)
        return qs

    def get_object(self):
        # Allow /me/ to resolve to current user's profile
        if self.kwargs.get("pk") == "me":
            profile = getattr(self.request.user, "profile", None)
            if profile is None:
                from rest_framework.exceptions import NotFound
                raise NotFound("No profile found for the current user.")
            self.check_object_permissions(self.request, profile)
            return profile
        return super().get_object()

    def partial_update(self, request, *args, **kwargs):
        """Non-admin users can only update limited fields."""
        profile = self.get_object()
        if not request.user.is_staff:
            allowed_fields = {"phone_number", "date_of_birth", "address", "profile_picture"}
            disallowed = set(request.data.keys()) - allowed_fields
            if disallowed:
                return Response(
                    {"detail": f"You cannot update these fields: {', '.join(disallowed)}"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update the current user's profile."""
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return Response(
                {"detail": "No profile found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "PATCH":
            if not request.user.is_staff:
                allowed_fields = {"phone_number", "date_of_birth", "address", "profile_picture"}
                disallowed = set(request.data.keys()) - allowed_fields
                if disallowed:
                    return Response(
                        {"detail": f"You cannot update these fields: {', '.join(disallowed)}"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        serializer = self.get_serializer(profile, data=request.data, partial=(request.method == "PATCH"))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------

class StudentViewSet(viewsets.ModelViewSet):
    """
    CRUD for students.

    * **list** – admin & instructor see all; students see only themselves
    * **retrieve** – admin & instructor see any; students see only themselves
    * **create / update / destroy** – admin only
    * **`/me/`** – current student's record
    * **`/{id}/gpa/`** – GET current GPA
    """

    queryset = Student.objects.select_related(
        "profile", "profile__user", "profile__department", "advisor", "advisor__profile"
    ).all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["year_level", "advisor"]
    search_fields = ["student_id", "profile__user__first_name", "profile__user__last_name"]
    ordering_fields = ["student_id", "gpa", "enrollment_date", "year_level"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            # Instructors see students in their department + their advisees
            dept = profile.department
            return qs.filter(
                models.Q(profile__department=dept) | models.Q(advisor__profile__user=user)
            ).distinct()

        # Students only see themselves
        return qs.filter(profile__user=user)

    def get_object(self):
        if self.kwargs.get("pk") == "me":
            student = Student.objects.filter(profile__user=self.request.user).first()
            if student is None:
                from rest_framework.exceptions import NotFound
                raise NotFound("No student record found for the current user.")
            self.check_object_permissions(self.request, student)
            return student
        return super().get_object()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Return the current user's student record."""
        student = Student.objects.filter(profile__user=request.user).select_related(
            "profile", "profile__user", "profile__department", "advisor", "advisor__profile"
        ).first()
        if student is None:
            return Response(
                {"detail": "No student record found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(student)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def gpa(self, request, pk=None):
        """Return the student's current GPA."""
        student = self.get_object()
        return Response({
            "student_id": student.student_id,
            "gpa": str(student.gpa),
        })


# ---------------------------------------------------------------------------
# Instructor
# ---------------------------------------------------------------------------

class InstructorViewSet(viewsets.ModelViewSet):
    """
    CRUD for instructors.

    * **list / retrieve** – any authenticated user
    * **create / update / destroy** – admin only
    * **`/me/`** – current instructor's record
    * **`/{id}/advisees/`** – GET list of advisees
    """

    queryset = Instructor.objects.select_related(
        "profile", "profile__user", "department"
    ).all()
    serializer_class = InstructorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["rank", "department"]
    search_fields = ["employee_id", "profile__user__first_name", "profile__user__last_name", "office_location"]
    ordering_fields = ["employee_id", "rank", "hire_date"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "advisees"):
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            # Instructors see themselves + colleagues in same department
            dept = profile.department
            return qs.filter(
                models.Q(profile__user=user) | models.Q(department=dept)
            ).distinct()

        # Students see all instructors (useful for course pages, etc.)
        return qs

    def get_object(self):
        if self.kwargs.get("pk") == "me":
            instructor = Instructor.objects.filter(profile__user=self.request.user).first()
            if instructor is None:
                from rest_framework.exceptions import NotFound
                raise NotFound("No instructor record found for the current user.")
            self.check_object_permissions(self.request, instructor)
            return instructor
        return super().get_object()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Return the current user's instructor record."""
        instructor = Instructor.objects.filter(profile__user=request.user).select_related(
            "profile", "profile__user", "department"
        ).first()
        if instructor is None:
            return Response(
                {"detail": "No instructor record found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instructor)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def advisees(self, request, pk=None):
        """List all students advised by this instructor."""
        instructor = self.get_object()
        advisees = Student.objects.filter(advisor=instructor).select_related(
            "profile", "profile__user", "profile__department"
        )
        page = self.paginate_queryset(advisees)
        if page is not None:
            serializer = StudentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StudentSerializer(advisees, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserViewSet(viewsets.ModelViewSet):
    """
    User management.

    * **list / retrieve** – admin only
    * **`/me/`** – current user's info (any authenticated user)
    * **create / update / destroy** – admin only
    """

    queryset = User.objects.select_related("profile").all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_active", "is_staff"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["username", "date_joined"]

    def get_permissions(self):
        if self.action in ("me",):
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update the current user's basic info (not profile)."""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Only allow updating name fields for non-staff
        if not request.user.is_staff:
            allowed = {"first_name", "last_name", "email"}
            disallowed = set(request.data.keys()) - allowed
            if disallowed:
                return Response(
                    {"detail": f"You cannot update these fields: {', '.join(disallowed)}"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        serializer.save()
        return Response(serializer.data)
