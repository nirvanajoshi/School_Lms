from django.db import models
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_root(request):
    """
    GET /api/

    API root — lists all available endpoints grouped by app.
    """
    user = request.user
    profile = getattr(user, "profile", None)
    role = profile.role if profile else None

    endpoints = {
        "auth": {
            "register": "/accounts/auth/register/",
            "login": "/accounts/auth/login/",
            "logout": "/accounts/auth/logout/",
            "change_password": "/accounts/auth/change-password/",
            "password_reset": "/accounts/auth/password-reset/",
            "password_reset_confirm": "/accounts/auth/password-reset/confirm/",
            "token_refresh": "/accounts/auth/token/refresh/",
        },
        "accounts": {
            "users": "/accounts/users/",
            "profiles": "/accounts/profiles/",
            "students": "/accounts/students/",
            "instructors": "/accounts/instructors/",
            "departments": "/accounts/departments/",
            "my_profile": "/accounts/profiles/me/",
            "my_user": "/accounts/users/me/",
        },
        "courses": {
            "courses": "/courses/courses/",
            "enrollments": "/courses/enrollments/",
            "materials": "/courses/materials/",
            "schedules": "/courses/schedules/",
            "syllabi": "/courses/syllabi/",
        },
        "assignments": {
            "assignments": "/assignments/assignments/",
            "submissions": "/assignments/submissions/",
            "grades": "/assignments/grades/",
        },
        "announcements": {
            "announcements": "/announcements/announcements/",
            "categories": "/announcements/categories/",
            "active_announcements": "/announcements/announcements/active/",
        },
        "attendance": {
            "sessions": "/attendance/sessions/",
            "records": "/attendance/records/",
            "summaries": "/attendance/summaries/",
        },
        "dashboard": {
            "my_dashboard": "/api/dashboard/",
        },
    }

    return Response({
        "message": "Welcome to the School LMS API",
        "version": "1.0",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": role,
        },
        "endpoints": endpoints,
    })


def _student_dashboard(request):
    """
    GET /api/dashboard/student/

    Aggregated dashboard for students:
    - Enrolled courses
    - Upcoming assignments
    - Recent attendance
    - Announcement count
    """
    from courses.models import Enrollment, Course
    from assignments.models import Assignment, Submission
    from attendance.models import AttendanceSession, AttendanceSummary
    from announcements.models import Announcement

    user = request.user
    now = timezone.now()

    # Enrolled courses
    enrollments = Enrollment.objects.filter(
        student__profile__user=user,
        status=Enrollment.Status.ENROLLED,
    ).select_related("course", "course__instructor", "course__instructor__profile")

    enrolled_courses = []
    for enrollment in enrollments:
        course = enrollment.course
        enrolled_courses.append({
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "instructor": course.instructor.profile.full_name,
            "semester": course.semester,
            "year": course.year,
        })

    # Upcoming assignments (published, not yet due)
    upcoming_assignments = Assignment.objects.filter(
        course__enrollments__student__profile__user=user,
        course__enrollments__status=Enrollment.Status.ENROLLED,
        status=Assignment.Status.PUBLISHED,
        due_date__gte=now,
    ).select_related("course").order_by("due_date")[:10]

    assignments_list = []
    for assignment in upcoming_assignments:
        submitted = Submission.objects.filter(
            assignment=assignment,
            student__profile__user=user,
        ).exists()
        assignments_list.append({
            "id": assignment.id,
            "title": assignment.title,
            "course_code": assignment.course.code,
            "due_date": assignment.due_date.isoformat(),
            "max_points": assignment.max_points,
            "is_submitted": submitted,
        })

    # Attendance summaries
    attendance_summaries = AttendanceSummary.objects.filter(
        student__profile__user=user,
    ).select_related("course")

    attendance_list = []
    for summary in attendance_summaries:
        attendance_list.append({
            "course_code": summary.course.code,
            "course_title": summary.course.title,
            "attendance_percentage": str(summary.attendance_percentage),
            "total_sessions": summary.total_sessions,
            "present_count": summary.present_count,
        })

    # Upcoming attendance sessions
    upcoming_sessions = AttendanceSession.objects.filter(
        course__enrollments__student__profile__user=user,
        course__enrollments__status=Enrollment.Status.ENROLLED,
        status=AttendanceSession.Status.SCHEDULED,
        date__gte=now.date(),
    ).select_related("course").order_by("date", "start_time")[:5]

    sessions_list = []
    for session in upcoming_sessions:
        sessions_list.append({
            "id": session.id,
            "course_code": session.course.code,
            "title": session.title,
            "date": session.date.isoformat(),
            "start_time": session.start_time.strftime("%H:%M"),
            "end_time": session.end_time.strftime("%H:%M"),
            "location": session.location,
        })

    # Active announcements
    active_announcements = Announcement.objects.filter(
        is_published=True,
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now),
    ).filter(
        models.Q(target_audience="all") | models.Q(target_audience="students"),
    ).count()

    return Response({
        "role": "student",
        "enrolled_courses": enrolled_courses,
        "upcoming_assignments": assignments_list,
        "attendance_summaries": attendance_list,
        "upcoming_sessions": sessions_list,
        "active_announcements": active_announcements,
    })


def _instructor_dashboard(request):
    """
    GET /api/dashboard/instructor/

    Aggregated dashboard for instructors:
    - Courses teaching
    - Pending submissions to grade
    - Recent attendance stats
    """
    from django.db.models import Count, Q
    from courses.models import Course, Enrollment
    from assignments.models import Assignment, Submission
    from attendance.models import AttendanceSession

    user = request.user
    now = timezone.now()

    # Courses teaching
    courses = Course.objects.filter(
        instructor__profile__user=user,
        is_active=True,
    ).annotate(
        enrolled_count=Count(
            "enrollments",
            filter=Q(enrollments__status=Enrollment.Status.ENROLLED),
        )
    )

    courses_list = []
    for course in courses:
        courses_list.append({
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "semester": course.semester,
            "year": course.year,
            "enrolled_count": course.enrolled_count,
            "max_enrollment": course.max_enrollment,
        })

    # Pending submissions to grade
    pending_submissions = Submission.objects.filter(
        assignment__course__instructor__profile__user=user,
        status=Submission.Status.SUBMITTED,
    ).select_related(
        "assignment", "assignment__course", "student", "student__profile"
    ).order_by("-submitted_at")[:10]

    submissions_list = []
    for sub in pending_submissions:
        submissions_list.append({
            "id": sub.id,
            "assignment_title": sub.assignment.title,
            "course_code": sub.assignment.course.code,
            "student_name": sub.student.profile.full_name,
            "student_id": sub.student.student_id,
            "submitted_at": sub.submitted_at.isoformat(),
            "is_late": sub.is_late,
        })

    # Assignment stats per course
    assignment_stats = []
    for course in courses:
        total_assignments = Assignment.objects.filter(course=course).count()
        published = Assignment.objects.filter(
            course=course, status=Assignment.Status.PUBLISHED
        ).count()
        total_submissions = Submission.objects.filter(
            assignment__course=course
        ).count()
        graded = Submission.objects.filter(
            assignment__course=course, status=Submission.Status.GRADED
        ).count()

        assignment_stats.append({
            "course_code": course.code,
            "course_title": course.title,
            "total_assignments": total_assignments,
            "published_assignments": published,
            "total_submissions": total_submissions,
            "graded_submissions": graded,
            "pending_grading": total_submissions - graded,
        })

    # Upcoming attendance sessions
    upcoming_sessions = AttendanceSession.objects.filter(
        course__instructor__profile__user=user,
        status__in=[AttendanceSession.Status.SCHEDULED, AttendanceSession.Status.IN_PROGRESS],
        date__gte=now.date(),
    ).select_related("course").order_by("date", "start_time")[:5]

    sessions_list = []
    for session in upcoming_sessions:
        sessions_list.append({
            "id": session.id,
            "course_code": session.course.code,
            "title": session.title,
            "date": session.date.isoformat(),
            "start_time": session.start_time.strftime("%H:%M"),
            "end_time": session.end_time.strftime("%H:%M"),
            "status": session.status,
            "location": session.location,
        })

    return Response({
        "role": "instructor",
        "courses": courses_list,
        "pending_submissions": submissions_list,
        "assignment_stats": assignment_stats,
        "upcoming_sessions": sessions_list,
    })


def _admin_dashboard(request):
    """
    GET /api/dashboard/admin/

    Aggregated dashboard for admins:
    - Total counts
    - Recent activity
    """
    from django.contrib.auth.models import User
    from accounts.models import Student, Instructor, Department
    from courses.models import Course, Enrollment
    from assignments.models import Assignment, Submission
    from attendance.models import AttendanceSession
    from announcements.models import Announcement

    return Response({
        "role": "admin",
        "totals": {
            "users": User.objects.count(),
            "students": Student.objects.count(),
            "instructors": Instructor.objects.count(),
            "departments": Department.objects.count(),
            "courses": Course.objects.count(),
            "active_courses": Course.objects.filter(is_active=True).count(),
            "enrollments": Enrollment.objects.filter(status=Enrollment.Status.ENROLLED).count(),
            "assignments": Assignment.objects.count(),
            "submissions": Submission.objects.count(),
            "pending_grading": Submission.objects.filter(status=Submission.Status.SUBMITTED).count(),
            "attendance_sessions": AttendanceSession.objects.count(),
            "announcements": Announcement.objects.filter(is_published=True).count(),
        },
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """
    GET /api/dashboard/

    Routes to the correct dashboard based on user role.
    """
    profile = getattr(request.user, "profile", None)
    role = profile.role if profile else None

    if role == "student":
        return _student_dashboard(request)
    elif role == "instructor":
        return _instructor_dashboard(request)
    elif role == "admin":
        return _admin_dashboard(request)
    else:
        return Response({
            "detail": "No dashboard available for your role.",
            "role": role,
        })
