from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response

from .models import AttendanceSession, AttendanceRecord, AttendanceSummary
from .serializers import (
    AttendanceSessionSerializer,
    AttendanceSessionListSerializer,
    AttendanceRecordSerializer,
    AttendanceSummarySerializer,
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


class IsSessionInstructorOrAdmin(IsAuthenticated):
    """Object-level: must be the instructor of the session's course or admin."""

    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return False
        if profile.role == "admin":
            return True
        if profile.role == "instructor":
            course = obj.course if hasattr(obj, "course") else obj.session.course
            return course.instructor.profile.user == request.user
        return False


# ---------------------------------------------------------------------------
# Attendance Session
# ---------------------------------------------------------------------------

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    Manage attendance sessions.

    **Status lifecycle:**
    * scheduled → **start** → in_progress
    * in_progress → **complete** → completed
    * scheduled / in_progress → **cancel** → cancelled

    **Queryset logic:**
    * Students see sessions for courses they're enrolled in
    * Instructors see sessions for their courses
    * Admins see everything

    **Query params:**
    * `course` – filter by course id
    * `status` – filter by status
    * `date` – filter by date (exact)
    * `date_after` / `date_before` – date range filter
    * `search` – searches title, notes
    """

    queryset = AttendanceSession.objects.select_related(
        "course", "course__instructor", "course__instructor__profile", "created_by"
    ).prefetch_related("records", "records__student", "records__student__profile").all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "status", "date"]
    search_fields = ["title", "notes"]
    ordering_fields = ["date", "start_time", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return AttendanceSessionListSerializer
        return AttendanceSessionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            return qs.filter(course__instructor__profile__user=user)

        # Students see sessions for courses they're enrolled in
        from courses.models import Enrollment
        enrolled_course_ids = Enrollment.objects.filter(
            student__profile__user=user,
            status=Enrollment.Status.ENROLLED,
        ).values_list("course_id", flat=True)
        return qs.filter(course_id__in=enrolled_course_ids)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # -- Status transitions --------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[IsSessionInstructorOrAdmin])
    def start(self, request, pk=None):
        """Transition scheduled → in_progress."""
        session = self.get_object()
        if session.status != AttendanceSession.Status.SCHEDULED:
            return Response(
                {"detail": f"Cannot start: current status is '{session.status}'. Only scheduled sessions can be started."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = AttendanceSession.Status.IN_PROGRESS
        session.save(update_fields=["status", "updated_at"])
        return Response(AttendanceSessionSerializer(session).data)

    @action(detail=True, methods=["post"], permission_classes=[IsSessionInstructorOrAdmin])
    def complete(self, request, pk=None):
        """Transition in_progress → completed."""
        session = self.get_object()
        if session.status != AttendanceSession.Status.IN_PROGRESS:
            return Response(
                {"detail": f"Cannot complete: current status is '{session.status}'. Only in-progress sessions can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = AttendanceSession.Status.COMPLETED
        session.save(update_fields=["status", "updated_at"])

        # Auto-recalculate summary for all students in this course
        self._update_summaries(session)

        return Response(AttendanceSessionSerializer(session).data)

    @action(detail=True, methods=["post"], permission_classes=[IsSessionInstructorOrAdmin])
    def cancel(self, request, pk=None):
        """Transition scheduled/in_progress → cancelled."""
        session = self.get_object()
        if session.status not in (AttendanceSession.Status.SCHEDULED, AttendanceSession.Status.IN_PROGRESS):
            return Response(
                {"detail": f"Cannot cancel: current status is '{session.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = AttendanceSession.Status.CANCELLED
        session.save(update_fields=["status", "updated_at"])
        return Response(AttendanceSessionSerializer(session).data)

    # -- Records (nested) ---------------------------------------------------

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticated])
    def records(self, request, pk=None):
        """
        GET: List all records for this session.
        POST: Create a record for this session (bulk or single).
        """
        session = self.get_object()

        if request.method == "GET":
            records = session.records.select_related(
                "student", "student__profile", "student__profile__user", "recorded_by"
            ).all()

            # Students only see their own record
            profile = getattr(request.user, "profile", None)
            if profile and profile.role == "student":
                records = records.filter(student__profile__user=request.user)

            serializer = AttendanceRecordSerializer(records, many=True)
            return Response(serializer.data)

        # POST – create record(s)
        profile = getattr(request.user, "profile", None)
        if profile is None or profile.role not in ("admin", "instructor"):
            return Response(
                {"detail": "Only instructors or admins can record attendance."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if session.status == AttendanceSession.Status.CANCELLED:
            return Response(
                {"detail": "Cannot record attendance for a cancelled session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Support bulk create: list of records
        data = request.data
        if isinstance(data, list):
            serializer = AttendanceRecordSerializer(data=data, many=True)
        else:
            serializer = AttendanceRecordSerializer(data=data)

        serializer.is_valid(raise_exception=True)

        if isinstance(serializer.validated_data, list):
            records = []
            for item in serializer.validated_data:
                record, _ = AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=item["student"],
                    defaults={
                        "status": item.get("status", AttendanceRecord.Status.ABSENT),
                        "check_in_time": item.get("check_in_time"),
                        "notes": item.get("notes", ""),
                        "recorded_by": request.user,
                    },
                )
                records.append(record)
            return Response(
                AttendanceRecordSerializer(records, many=True).data,
                status=status.HTTP_201_CREATED,
            )
        else:
            record, _ = AttendanceRecord.objects.update_or_create(
                session=session,
                student=serializer.validated_data["student"],
                defaults={
                    "status": serializer.validated_data.get("status", AttendanceRecord.Status.ABSENT),
                    "check_in_time": serializer.validated_data.get("check_in_time"),
                    "notes": serializer.validated_data.get("notes", ""),
                    "recorded_by": request.user,
                },
            )
            return Response(
                AttendanceRecordSerializer(record).data,
                status=status.HTTP_201_CREATED,
            )

    @action(detail=True, methods=["get"], permission_classes=[IsSessionInstructorOrAdmin])
    def stats(self, request, pk=None):
        """Return attendance stats for this session."""
        session = self.get_object()
        records = session.records.all()
        total_expected = session.total_expected
        total_present = records.filter(status=AttendanceRecord.Status.PRESENT).count()
        total_late = records.filter(status=AttendanceRecord.Status.LATE).count()
        total_absent = records.filter(status=AttendanceRecord.Status.ABSENT).count()
        total_excused = records.filter(status=AttendanceRecord.Status.EXCUSED).count()

        return Response({
            "session_id": session.id,
            "total_expected": total_expected,
            "total_present": total_present,
            "total_late": total_late,
            "total_absent": total_absent,
            "total_excused": total_excused,
            "attendance_rate": session.attendance_rate,
        })

    # -- Helpers -------------------------------------------------------------

    @staticmethod
    def _update_summaries(session):
        """Recalculate AttendanceSummary for all enrolled students after session completion."""
        from courses.models import Enrollment
        enrolled_students = Enrollment.objects.filter(
            course=session.course,
            status=Enrollment.Status.ENROLLED,
        ).values_list("student_id", flat=True)

        for student_id in enrolled_students:
            summary, _ = AttendanceSummary.objects.get_or_create(
                student_id=student_id,
                course=session.course,
            )
            summary.recalculate()


# ---------------------------------------------------------------------------
# Attendance Record
# ---------------------------------------------------------------------------

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    Manage individual attendance records.

    **Logic:**
    * Students only see their own records.
    * Instructors see records for their course sessions.
    * Admins see all.
    * Only instructors/admins can create/update records.
    """

    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["session", "status"]
    search_fields = ["student__student_id", "student__profile__user__first_name", "notes"]
    ordering_fields = ["recorded_at", "status"]

    def get_queryset(self):
        qs = AttendanceRecord.objects.select_related(
            "session", "session__course",
            "student", "student__profile", "student__profile__user",
            "recorded_by",
        ).all()

        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            return qs.filter(session__course__instructor__profile__user=user)

        # Students only see their own
        return qs.filter(student__profile__user=user)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


# ---------------------------------------------------------------------------
# Attendance Summary
# ---------------------------------------------------------------------------

class AttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for attendance summaries.

    **Logic:**
    * Students see only their own summaries.
    * Instructors see summaries for their courses.
    * Admins see all.
    * **`recalculate/`** action to force recalculation.
    """

    queryset = AttendanceSummary.objects.select_related(
        "student", "student__profile", "student__profile__user",
        "course", "course__instructor",
    ).all()
    serializer_class = AttendanceSummarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "student"]
    search_fields = ["student__student_id", "student__profile__user__first_name", "course__code"]
    ordering_fields = ["attendance_percentage", "last_updated"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            return qs.filter(course__instructor__profile__user=user)

        # Students only see their own
        return qs.filter(student__profile__user=user)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def recalculate(self, request, pk=None):
        """Force recalculation of this attendance summary."""
        summary = self.get_object()
        summary.recalculate()
        return Response(AttendanceSummarySerializer(summary).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def recalculate_all(self, request):
        """Recalculate all summaries for a given course."""
        course_id = request.data.get("course")
        if not course_id:
            return Response(
                {"detail": "'course' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summaries = AttendanceSummary.objects.filter(course_id=course_id)
        for summary in summaries:
            summary.recalculate()

        return Response({
            "detail": f"Recalculated {summaries.count()} summaries.",
        })
