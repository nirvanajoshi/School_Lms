from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response

from .models import Assignment, Submission, SubmissionAttachment, Grade
from .serializers import (
    AssignmentSerializer,
    SubmissionSerializer,
    SubmissionListSerializer,
    SubmissionAttachmentSerializer,
    GradeSerializer,
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


class IsInstructorForCourse(IsAuthenticated):
    """Object-level: must be the instructor of the assignment's course."""

    def has_object_permission(self, request, view, obj):
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return False
        if profile.role == "admin":
            return True
        if profile.role == "instructor":
            # For Assignment objects, check course.instructor
            if hasattr(obj, "course"):
                return obj.course.instructor.profile.user == request.user
            # For Submission objects, check the parent assignment's course
            if hasattr(obj, "assignment"):
                return obj.assignment.course.instructor.profile.user == request.user
        return False


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------

class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Full lifecycle for assignments.

    **Status transitions (via custom actions):**
    * draft → **publish** → published
    * published → **close** → closed
    * closed / published → **archive** → archived

    **Queryset logic:**
    * Students see only **published** assignments
    * Instructors see their own assignments + published ones
    * Admins see everything

    **Query params (list):**
    * `course` – filter by course id
    * `status` – filter by status
    * `search` – searches title & description
    """

    queryset = Assignment.objects.select_related("course", "created_by").all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "status", "submission_type"]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at", "max_points", "weight"]

    def get_serializer_class(self):
        if self.action == "list":
            return AssignmentSerializer  # Could use a list serializer if needed
        return AssignmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            # Instructors see their own + all published
            return qs.filter(
                models.Q(created_by=user) | models.Q(status=Assignment.Status.PUBLISHED)
            )

        # Students see only published assignments
        return qs.filter(status=Assignment.Status.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # -- Status transitions --------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def publish(self, request, pk=None):
        """Transition draft → published."""
        assignment = self.get_object()
        if assignment.status != Assignment.Status.DRAFT:
            return Response(
                {"detail": f"Cannot publish: current status is '{assignment.status}'. Only drafts can be published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.status = Assignment.Status.PUBLISHED
        assignment.save(update_fields=["status", "updated_at"])
        return Response(AssignmentSerializer(assignment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def close(self, request, pk=None):
        """Transition published → closed (no new submissions accepted)."""
        assignment = self.get_object()
        if assignment.status != Assignment.Status.PUBLISHED:
            return Response(
                {"detail": f"Cannot close: current status is '{assignment.status}'. Only published assignments can be closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.status = Assignment.Status.CLOSED
        assignment.save(update_fields=["status", "updated_at"])
        return Response(AssignmentSerializer(assignment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def archive(self, request, pk=None):
        """Transition published/closed → archived."""
        assignment = self.get_object()
        if assignment.status not in (Assignment.Status.PUBLISHED, Assignment.Status.CLOSED):
            return Response(
                {"detail": f"Cannot archive: current status is '{assignment.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.status = Assignment.Status.ARCHIVED
        assignment.save(update_fields=["status", "updated_at"])
        return Response(AssignmentSerializer(assignment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def reopen(self, request, pk=None):
        """Transition closed → published (re-open submissions)."""
        assignment = self.get_object()
        if assignment.status != Assignment.Status.CLOSED:
            return Response(
                {"detail": f"Cannot reopen: current status is '{assignment.status}'. Only closed assignments can be reopened."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.status = Assignment.Status.PUBLISHED
        assignment.save(update_fields=["status", "updated_at"])
        return Response(AssignmentSerializer(assignment).data)

    # -- Nested: submissions -------------------------------------------------

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def submissions(self, request, pk=None):
        """List all submissions for this assignment."""
        assignment = self.get_object()
        user = request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        qs = assignment.submissions.select_related(
            "student", "student__profile", "student__profile__user"
        ).prefetch_related("attachments", "grade")

        # Students only see their own submission
        if role == "student":
            qs = qs.filter(student__profile__user=user)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = SubmissionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SubmissionListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def stats(self, request, pk=None):
        """Return submission stats for this assignment (instructor/admin only)."""
        assignment = self.get_object()
        submissions = assignment.submissions.all()
        total = submissions.count()
        graded = submissions.filter(status=Submission.Status.GRADED).count()
        late = submissions.filter(is_late=True).count()

        avg_grade = None
        if graded > 0:
            from django.db.models import Avg
            avg = submissions.filter(
                status=Submission.Status.GRADED
            ).aggregate(avg=Avg("grade__points"))
            avg_grade = str(avg["avg"]) if avg["avg"] else None

        return Response({
            "total_submissions": total,
            "graded": graded,
            "pending": total - graded,
            "late_submissions": late,
            "average_grade": avg_grade,
        })


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Manage student submissions.

    **Logic:**
    * Students can **create** a submission (auto-sets student to self).
    * Students can only see/edit their own submissions.
    * Instructors/admin see all submissions.
    * Students cannot submit after due date unless `allow_late_submissions`.
    * **`/grade/`** action for instructors to grade a submission.
    """

    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["status", "is_late"]
    search_fields = ["student__student_id", "student__profile__user__first_name"]
    ordering_fields = ["submitted_at", "status"]

    def get_serializer_class(self):
        if self.action == "list":
            return SubmissionListSerializer
        return SubmissionSerializer

    def get_queryset(self):
        qs = Submission.objects.select_related(
            "assignment", "student", "student__profile", "student__profile__user"
        ).prefetch_related("attachments", "grade").all()

        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role in ("admin", "instructor"):
            return qs

        # Students only see their own
        return qs.filter(student__profile__user=user)

    def perform_create(self, serializer):
        from accounts.models import Student
        student = Student.objects.filter(profile__user=self.request.user).first()
        if student is None:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You do not have a student record.")

        assignment = serializer.validated_data["assignment"]

        # Check assignment is published
        if assignment.status != Assignment.Status.PUBLISHED:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot submit to an assignment that is not published.")

        # Check due date / late policy
        now = timezone.now()
        is_late = now > assignment.due_date
        if is_late and not assignment.allow_late_submissions:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("This assignment does not accept late submissions.")

        serializer.save(student=student, is_late=is_late)

    # -- Grade action --------------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[IsInstructorForCourse])
    def grade(self, request, pk=None):
        """Grade a submission. Creates or updates the Grade object."""
        submission = self.get_object()

        points = request.data.get("points")
        comments = request.data.get("comments", "")

        if points is None:
            return Response(
                {"detail": "'points' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_points = submission.assignment.max_points
        if float(points) < 0 or float(points) > max_points:
            return Response(
                {"detail": f"Points must be between 0 and {max_points}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grade, created = Grade.objects.update_or_create(
            submission=submission,
            defaults={
                "graded_by": request.user,
                "points": points,
                "comments": comments,
            },
        )

        return Response(
            GradeSerializer(grade).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsInstructorForCourse])
    def return_for_revision(self, request, pk=None):
        """Mark a submission as returned for revision."""
        submission = self.get_object()
        if submission.status not in (Submission.Status.SUBMITTED, Submission.Status.GRADED):
            return Response(
                {"detail": f"Cannot return: current status is '{submission.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission.status = Submission.Status.RETURNED
        submission.feedback = request.data.get("feedback", submission.feedback)
        submission.save(update_fields=["status", "feedback", "updated_at"])
        return Response(SubmissionSerializer(submission).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInstructorForCourse])
    def resubmit_allowed(self, request, pk=None):
        """Allow a student to resubmit by resetting status to submitted."""
        submission = self.get_object()
        if submission.status != Submission.Status.RETURNED:
            return Response(
                {"detail": "Only returned submissions can be reset for resubmission."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission.status = Submission.Status.SUBMITTED
        submission.save(update_fields=["status", "updated_at"])
        return Response(SubmissionSerializer(submission).data)


# ---------------------------------------------------------------------------
# Submission Attachments
# ---------------------------------------------------------------------------

class SubmissionAttachmentViewSet(viewsets.ModelViewSet):
    """
    Manage file attachments for a submission.

    Nested resource: `/submissions/{id}/attachments/`
    """

    serializer_class = SubmissionAttachmentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return SubmissionAttachment.objects.filter(
            submission_id=self.kwargs["submission_pk"]
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve", "create"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    def perform_create(self, serializer):
        serializer.save(submission_id=self.kwargs["submission_pk"])


# ---------------------------------------------------------------------------
# Grade
# ---------------------------------------------------------------------------

class GradeViewSet(viewsets.ModelViewSet):
    """
    CRUD for grades.

    * **list / retrieve** – admin, instructor, or the graded student
    * **create / update** – admin & instructor only
    * **destroy** – admin only
    """

    queryset = Grade.objects.select_related(
        "submission", "submission__assignment", "graded_by"
    ).all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["graded_by"]
    ordering_fields = ["points", "graded_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            return qs

        if role == "instructor":
            # Instructors see grades they gave + grades for their course submissions
            return qs.filter(
                models.Q(graded_by=user)
                | models.Q(submission__assignment__course__instructor__profile__user=user)
            ).distinct()

        # Students only see their own grades
        return qs.filter(submission__student__profile__user=user)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        if self.action == "destroy":
            return [IsAdminUser()]
        return [IsAdminOrInstructor()]

    def perform_create(self, serializer):
        serializer.save(graded_by=self.request.user)
