from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'assignments', views.AssignmentViewSet)
router.register(r'submissions', views.SubmissionViewSet)
router.register(r'grades', views.GradeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(
        'submissions/<int:submission_pk>/attachments/',
        views.SubmissionAttachmentViewSet.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='submission-attachments-list',
    ),
    path(
        'submissions/<int:submission_pk>/attachments/<int:pk>/',
        views.SubmissionAttachmentViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='submission-attachments-detail',
    ),
]
