from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'sessions', views.AttendanceSessionViewSet)
router.register(r'records', views.AttendanceRecordViewSet)
router.register(r'summaries', views.AttendanceSummaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
