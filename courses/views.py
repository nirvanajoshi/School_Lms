from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response

from .models import Course, Enrollment, CourseMaterial, Schedule, Syllabus
from .serializers import (
    CourseSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    EnrollmentListSerializer,
    CourseMaterialSerializer,
    ScheduleSerializer,
    SyllabusSerializer,
)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class IsAdminOrInstructor(IsAuthenticated):
    """Allow admin and instructor roles."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role in ("admin", "instructor")


class IsCourseInstructorOrAdmin(IsAuthenticated):
    """Object-level: must be the instructor of the course or an admin."""

    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return False
        if profile.role == "admin":
            return True
        if profile.role == "instructor":
            # For Course objects
            if hasattr(obj, "instructor"):
                return obj.instructor.profile.user == request.user
            # For objects with a course FK
            if hasattr(obj, "course"):
                return obj.course.instructor.profile.user == request.user
        return False


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class CourseViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for courses.

    **Queryset logic:**
    * Students see active courses
    * Instructors see their own courses + active ones
    * Admins see everything

    **Query params:**
    * `semester` – filter by semester
    * `year` – filter by year
    * `department` – filter by department id
    * `instructor` – filter by instructor id
    * `is_active` – boolean filter
    * `search` – searches title, code, description

    **Custom actions:**
    * `enrollments/` – list enrollments for this course
    * `materials/` – list materials for this course
    * `schedules/` – list schedules for this course
    * `syllabus/` – get/update syllabus for this course
    """

    queryset = Course.objects.select_related(
        "department", "instructor", "instructor__profile"
    ).all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ["semester", "year", "department", "instructor", "is_active"]
    search_fields = ["title", "code", "description"]
    ordering_fields = ["title", "code", "year", "semester", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            return qs.filter(
                models.Q(instructor__profile__user=user) | models.Q(is_active=True)
            )

        # Students see active courses
        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    # -- Nested resources ----------------------------------------------------

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def enrollments(self, request, pk=None):
        """List all enrollments for this course."""
        course = self.get_object()
        user = request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        qs = course.enrollments.select_related(
            "student", "student__profile", "student__profile__user"
        ).all()

        # Students only see their own enrollment
        if role == "student":
            qs = qs.filter(student__profile__user=user)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = EnrollmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EnrollmentListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def materials(self, request, pk=None):
        """List published materials for this course."""
        course = self.get_object()
        user = request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        qs = course.materials.all()

        # Students only see published materials
        if role == "student":
            qs = qs.filter(is_published=True)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = CourseMaterialSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CourseMaterialSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def schedules(self, request, pk=None):
        """List schedules for this course."""
        course = self.get_object()
        qs = course.schedules.all()

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ScheduleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ScheduleSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "put", "patch"], permission_classes=[IsAuthenticated])
    def syllabus(self, request, pk=None):
        """Get or update the syllabus for this course."""
        course = self.get_object()

        if request.method == "GET":
            syllabus = getattr(course, "syllabus", None)
            if syllabus is None:
                return Response(
                    {"detail": "No syllabus found for this course."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = SyllabusSerializer(syllabus)
            return Response(serializer.data)

        # PUT / PATCH – must be instructor or admin
        profile = getattr(request.user, "profile", None)
        if profile is None or profile.role not in ("admin", "instructor"):
            return Response(
                {"detail": "Only instructors or admins can update the syllabus."},
                status=status.HTTP_403_FORBIDDEN,
            )

        syllabus, _ = Syllabus.objects.get_or_create(
            course=course, defaults={"created_by": request.user}
        )
        serializer = SyllabusSerializer(syllabus, data=request.data, partial=(request.method == "PATCH"))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def stats(self, request, pk=None):
        """Return enrollment stats for this course."""
        course = self.get_object()
        enrollments = course.enrollments.all()
        total = enrollments.count()
        enrolled = enrollments.filter(status=Enrollment.Status.ENROLLED).count()
        dropped = enrollments.filter(status=Enrollment.Status.DROPPED).count()
        completed = enrollments.filter(status=Enrollment.Status.COMPLETED).count()

        from django.db.models import Avg
        avg_grade = enrollments.filter(
            status=Enrollment.Status.COMPLETED, grade__isnull=False
        ).aggregate(avg=Avg("grade"))["avg"]

        return Response({
            "total_enrollments": total,
            "currently_enrolled": enrolled,
            "dropped": dropped,
            "completed": completed,
            "available_spots": max(0, course.max_enrollment - enrolled),
            "average_grade": str(avg_grade) if avg_grade else None,
        })


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    Manage student enrollments.

    **Logic:**
    * Students can **enroll** themselves in a course (via `enroll/` action).
    * Students can **drop** their enrollment (via `drop/` action).
    * Students only see their own enrollments.
    * Instructors see enrollments for their courses.
    * Admins see all.

    **Custom actions:**
    * `enroll/` – POST to enroll in a course
    * `drop/` – POST to drop a course
    * `complete/` – POST to mark enrollment as completed (instructor/admin)
    """

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "course"]
    ordering_fields = ["enrolled_at", "status"]

    def get_serializer_class(self):
        if self.action == "list":
            return EnrollmentListSerializer
        return EnrollmentSerializer

    def get_queryset(self):
        qs = Enrollment.objects.select_related(
            "course", "student", "student__profile", "student__profile__user"
        ).all()

        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            return qs.filter(course__instructor__profile__user=user)

        # Students only see their own
        return qs.filter(student__profile__user=user)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    # -- Custom actions ------------------------------------------------------

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request):
        """Enroll the current student in a course."""
        from accounts.models import Student

        student = Student.objects.filter(profile__user=request.user).first()
        if student is None:
            return Response(
                {"detail": "You do not have a student record."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course_id = request.data.get("course")
        if not course_id:
            return Response(
                {"detail": "'course' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check course is active
        if not course.is_active:
            return Response(
                {"detail": "This course is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check not already enrolled
        if Enrollment.objects.filter(course=course, student=student, status=Enrollment.Status.ENROLLED).exists():
            return Response(
                {"detail": "You are already enrolled in this course."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check capacity
        current_enrolled = course.enrollments.filter(status=Enrollment.Status.ENROLLED).count()
        if current_enrolled >= course.max_enrollment:
            return Response(
                {"detail": "This course is full."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment = Enrollment.objects.create(
            course=course, student=student, status=Enrollment.Status.ENROLLED
        )
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def drop(self, request, pk=None):
        """Drop an enrollment."""
        enrollment = self.get_object()

        # Students can only drop their own
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "student":
            if enrollment.student.profile.user != request.user:
                return Response(
                    {"detail": "You can only drop your own enrollments."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if enrollment.status != Enrollment.Status.ENROLLED:
            return Response(
                {"detail": f"Cannot drop: current status is '{enrollment.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment.status = Enrollment.Status.DROPPED
        enrollment.save(update_fields=["status"])
        return Response(EnrollmentSerializer(enrollment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def complete(self, request, pk=None):
        """Mark an enrollment as completed, optionally with a grade."""
        enrollment = self.get_object()

        if enrollment.status != Enrollment.Status.ENROLLED:
            return Response(
                {"detail": f"Cannot complete: current status is '{enrollment.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grade = request.data.get("grade")
        enrollment.status = Enrollment.Status.COMPLETED
        if grade is not None:
            enrollment.grade = grade
        enrollment.save(update_fields=["status", "grade"])
        return Response(EnrollmentSerializer(enrollment).data)


# ---------------------------------------------------------------------------
# Course Material
# ---------------------------------------------------------------------------

class CourseMaterialViewSet(viewsets.ModelViewSet):
    """
    Manage course materials (lecture notes, slides, videos, etc.).

    **Logic:**
    * Instructors/admin can CRUD materials for their courses.
    * Students only see published materials.
    * Custom `publish/` and `unpublish/` actions.

    **Query params:**
    * `course` – filter by course id
    * `material_type` – filter by type
    * `week_number` – filter by week
    * `is_published` – boolean filter
    """

    queryset = CourseMaterial.objects.select_related(
        "course", "uploaded_by"
    ).all()
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["course", "material_type", "week_number", "is_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["week_number", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role in ("admin", "instructor"):
            return qs

        # Students only see published materials
        return qs.filter(is_published=True)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsCourseInstructorOrAdmin])
    def publish(self, request, pk=None):
        """Publish a course material."""
        material = self.get_object()
        if material.is_published:
            return Response(
                {"detail": "Material is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        material.is_published = True
        material.save(update_fields=["is_published", "updated_at"])
        return Response(CourseMaterialSerializer(material).data)

    @action(detail=True, methods=["post"], permission_classes=[IsCourseInstructorOrAdmin])
    def unpublish(self, request, pk=None):
        """Unpublish a course material."""
        material = self.get_object()
        if not material.is_published:
            return Response(
                {"detail": "Material is not published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        material.is_published = False
        material.save(update_fields=["is_published", "updated_at"])
        return Response(CourseMaterialSerializer(material).data)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

class ScheduleViewSet(viewsets.ModelViewSet):
    """
    Manage weekly course schedules.

    **Logic:**
    * Students see all schedules for active courses.
    * Instructors manage schedules for their courses.
    * Admins manage all.

    **Query params:**
    * `course` – filter by course id
    * `day_of_week` – filter by day
    * `is_active` – boolean filter
    """

    queryset = Schedule.objects.select_related("course").all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "day_of_week", "is_active"]
    ordering_fields = ["day_of_week", "start_time"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsCourseInstructorOrAdmin()]


# ---------------------------------------------------------------------------
# Syllabus
# ---------------------------------------------------------------------------

class SyllabusViewSet(viewsets.ModelViewSet):
    """
    Manage course syllabi.

    **Logic:**
    * Students see syllabi for courses they're enrolled in + any published course.
    * Instructors manage syllabi for their courses.
    * Admins manage all.

    **Query params:**
    * `course` – filter by course id
    * `search` – searches objectives, prerequisites, textbooks
    """

    queryset = Syllabus.objects.select_related(
        "course", "course__instructor", "course__instructor__profile", "created_by"
    ).all()
    serializer_class = SyllabusSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course"]
    search_fields = ["objectives", "prerequisites", "textbooks"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role in ("admin", "instructor"):
            return qs

        # Students see syllabi for courses they're enrolled in
        from .models import Enrollment
        enrolled_course_ids = Enrollment.objects.filter(
            student__profile__user=user,
            status=Enrollment.Status.ENROLLED
        ).values_list("course_id", flat=True)
        return qs.filter(course_id__in=enrolled_course_ids)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsCourseInstructorOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
