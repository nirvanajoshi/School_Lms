from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet)
router.register(r'enrollments', views.EnrollmentViewSet)
router.register(r'materials', views.CourseMaterialViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'syllabi', views.SyllabusViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
