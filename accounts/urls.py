from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'profiles', views.ProfileViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'instructors', views.InstructorViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
