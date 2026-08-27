from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response

from .models import Category, Announcement, AnnouncementAttachment
from .serializers import (
    CategorySerializer,
    AnnouncementSerializer,
    AnnouncementListSerializer,
    AnnouncementAttachmentSerializer,
)


# ---------------------------------------------------------------------------
# Helpers / Permissions
# ---------------------------------------------------------------------------

class IsAdminOrInstructor(IsAuthenticated):
    """Allow access to admin-role users and instructors."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return False
        return profile.role in ("admin", "instructor")


class IsOwnerOrReadOnly(IsAuthenticated):
    """Object-level: only the creator (or admin) may mutate."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.created_by == request.user or self._is_admin(request)

    @staticmethod
    def _is_admin(request):
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role == "admin"


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for announcement categories.

    * **list / retrieve** – any authenticated user
    * **create / update / destroy** – admin & instructor only
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = ["type", "is_active"]
    search_fields = ["name", "description"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminOrInstructor()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Non-admin users only see active categories
        profile = getattr(self.request.user, "profile", None)
        if profile is None or profile.role != "admin":
            qs = qs.filter(is_active=True)
        return qs


# ---------------------------------------------------------------------------
# Announcement
# ---------------------------------------------------------------------------

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    Full lifecycle for announcements.

    **Key logic:**
    * Students only see *published & non-expired* announcements targeted to
      them (or to *everyone*).
    * Instructors/admins see everything they created + all published ones.
    * `target_audience` filtering is automatic based on the caller's role.
    * Custom actions: `publish`, `unpublish`, `active`.

    **Query params (list):**
    * `priority` – filter by priority level (1-4)
    * `category` – filter by category id
    * `target_audience` – filter by audience key
    * `is_published` – boolean filter
    * `search` – searches title & content
    """

    queryset = Announcement.objects.select_related("category", "created_by").prefetch_related("attachments")
    permission_classes = [IsAuthenticated]
    filterset_fields = ["priority", "category", "target_audience", "is_published"]
    search_fields = ["title", "content"]
    ordering_fields = ["priority", "created_at", "published_at"]
    parser_classes = [MultiPartParser, FormParser]

    # -- Serializers --------------------------------------------------------

    def get_serializer_class(self):
        if self.action == "list":
            return AnnouncementListSerializer
        return AnnouncementSerializer

    # -- Queryset -----------------------------------------------------------

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        role = profile.role if profile else None

        if role == "admin":
            # Admins see everything
            return qs

        if role == "instructor":
            # Instructors see their own + all published
            return qs.filter(models.Q(created_by=user) | models.Q(is_published=True))

        # Students / unauthenticated (shouldn't reach here due to perms)
        now = timezone.now()
        return qs.filter(
            is_published=True,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now),
        ).filter(
            models.Q(target_audience="all") | models.Q(target_audience="students"),
        )

    # -- Create -------------------------------------------------------------

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # -- Custom actions -----------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def publish(self, request, pk=None):
        """Mark an announcement as published and set published_at."""
        announcement = self.get_object()
        if announcement.is_published:
            return Response(
                {"detail": "Announcement is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.save(update_fields=["is_published", "published_at", "updated_at"])
        serializer = self.get_serializer(announcement)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrInstructor])
    def unpublish(self, request, pk=None):
        """Revoke publication status."""
        announcement = self.get_object()
        if not announcement.is_published:
            return Response(
                {"detail": "Announcement is not published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        announcement.is_published = False
        announcement.save(update_fields=["is_published", "updated_at"])
        serializer = self.get_serializer(announcement)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def active(self, request):
        """Return only published, non-expired announcements visible to the caller."""
        now = timezone.now()
        qs = self.get_queryset().filter(
            is_published=True,
            published_at__lte=now,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now),
        )

        # Apply standard filtering
        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def expired(self, request):
        """Admin-only: list announcements past their expiry date."""
        now = timezone.now()
        qs = self.get_queryset().filter(
            expires_at__isnull=False,
            expires_at__lte=now,
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Announcement Attachments
# ---------------------------------------------------------------------------

class AnnouncementAttachmentViewSet(viewsets.ModelViewSet):
    """
    Manage file attachments for an announcement.

    Accessed as a nested resource: `/announcements/{id}/attachments/`
    """

    serializer_class = AnnouncementAttachmentSerializer
    permission_classes = [IsAdminOrInstructor]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return AnnouncementAttachment.objects.filter(
            announcement_id=self.kwargs["announcement_pk"]
        )

    def perform_create(self, serializer):
        serializer.save(announcement_id=self.kwargs["announcement_pk"])
