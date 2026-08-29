from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from . import auth_views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'profiles', views.ProfileViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'instructors', views.InstructorViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', auth_views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', auth_views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='auth-logout'),
    path('auth/change-password/', auth_views.ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/password-reset/', auth_views.PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('auth/password-reset/confirm/', auth_views.PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    # JWT token refresh (simplejwt built-in)
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # Router endpoints
    path('', include(router.urls)),
]
