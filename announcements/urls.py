from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'announcements', views.AnnouncementViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(
        'announcements/<int:announcement_pk>/attachments/',
        views.AnnouncementAttachmentViewSet.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='announcement-attachments-list',
    ),
    path(
        'announcements/<int:announcement_pk>/attachments/<int:pk>/',
        views.AnnouncementAttachmentViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='announcement-attachments-detail',
    ),
]
