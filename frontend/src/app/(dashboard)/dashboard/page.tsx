"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { format, formatDistanceToNow, parseISO } from "date-fns";
import Link from "next/link";
import {
  HiOutlineAcademicCap,
  HiOutlineClipboard,
  HiOutlineCheckCircle,
  HiOutlineMegaphone,
  HiOutlineUsers,
  HiOutlineCalendarDays,
  HiOutlineClock,
  HiOutlineExclamationTriangle,
  HiOutlineArrowTrendingUp,
} from "react-icons/hi2";

export default function DashboardPage() {
  const { profile } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/").then((r) => setData(r.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center py-20"><div className="spinner" /></div>;
  if (!data) return <div className="empty-state py-20"><p className="text-[var(--color-gray-500)]">Could not load dashboard</p></div>;

  const role = profile?.role || "student";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="max-w-[1200px] mx-auto space-y-6">
      <div className="animate-fade-in">
        <h1 className="text-[22px] font-bold text-[var(--color-gray-900)] tracking-tight">
          {greeting}, {profile?.full_name?.split(" ")[0] || "there"}
        </h1>
        <p className="text-[13px] text-[var(--color-gray-500)] mt-0.5">
          Here&apos;s what&apos;s happening with your {role === "student" ? "studies" : role === "instructor" ? "courses" : "system"} today.
        </p>
      </div>

      {role === "student" && <StudentDashboard data={data} />}
      {role === "instructor" && <InstructorDashboard data={data} />}
      {role === "admin" && <AdminDashboard data={data} />}
    </div>
  );
}

function StatCard({ icon: Icon, value, label, color }: { icon: any; value: number; label: string; color: string }) {
  const bgMap: Record<string, string> = {
    primary: "var(--color-primary-50)",
    success: "var(--color-success-50)",
    warning: "var(--color-warning-50)",
    danger: "var(--color-danger-50)",
    info: "var(--color-info-50)",
  };
  const fgMap: Record<string, string> = {
    primary: "var(--color-primary-600)",
    success: "var(--color-success-600)",
    warning: "var(--color-warning-600)",
    danger: "var(--color-danger-600)",
    info: "var(--color-info-600)",
  };

  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: bgMap[color], color: fgMap[color] }}>
        <Icon />
      </div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

function CardHeader({ title, href, hrefLabel }: { title: string; href?: string; hrefLabel?: string }) {
  return (
    <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid var(--color-gray-100)" }}>
      <h2 className="text-[14px] font-semibold text-[var(--color-gray-900)]">{title}</h2>
      {href && (
        <Link href={href} className="text-[12px] font-semibold" style={{ color: "var(--color-primary-600)" }}>
          {hrefLabel || "View all"}
        </Link>
      )}
    </div>
  );
}

/* ──────── Student ──────── */
function StudentDashboard({ data }: { data: any }) {
  const courses = data.enrolled_courses || [];
  const assignments = data.upcoming_assignments || [];
  const attendance = data.attendance_summaries || [];
  const sessions = data.upcoming_sessions || [];

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in animate-fade-in-delay-1">
        <StatCard icon={HiOutlineAcademicCap} value={courses.length} label="Enrolled Courses" color="primary" />
        <StatCard icon={HiOutlineClipboard} value={assignments.length} label="Upcoming Assignments" color="warning" />
        <StatCard icon={HiOutlineCheckCircle} value={sessions.length} label="Upcoming Classes" color="success" />
        <StatCard icon={HiOutlineMegaphone} value={data.active_announcements} label="Announcements" color="info" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Courses */}
        <div className="lg:col-span-2 card animate-fade-in animate-fade-in-delay-2">
          <CardHeader title="My Courses" href="/courses" />
          <div className="p-4">
            {courses.length === 0 ? (
              <div className="empty-state py-8">
                <HiOutlineAcademicCap className="empty-state-icon" />
                <h3>No courses yet</h3><p>Browse courses to get started</p>
              </div>
            ) : (
              <div className="space-y-1">
                {courses.map((c: any) => (
                  <Link key={c.id} href={`/courses/${c.id}`} className="flex items-center gap-3 p-3 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-50)] transition-colors group">
                    <div className="w-9 h-9 rounded-[var(--radius-sm)] flex items-center justify-center text-white text-[12px] font-bold flex-shrink-0" style={{ background: "var(--color-gray-900)" }}>
                      {c.code.slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-[var(--color-gray-900)] truncate group-hover:text-[var(--color-primary-600)] transition-colors">{c.title}</p>
                      <p className="text-[11px] text-[var(--color-gray-500)]">{c.code} · {c.instructor}</p>
                    </div>
                    <span className="badge badge-gray text-[10px]">{c.semester} {c.year}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Assignments */}
        <div className="card animate-fade-in animate-fade-in-delay-3">
          <CardHeader title="Assignments" href="/assignments" />
          <div className="p-4">
            {assignments.length === 0 ? (
              <div className="empty-state py-8">
                <HiOutlineClipboard className="empty-state-icon" />
                <h3>No pending</h3><p>You&apos;re all caught up</p>
              </div>
            ) : (
              <div className="space-y-2">
                {assignments.map((a: any) => (
                  <div key={a.id} className="p-3 rounded-[var(--radius-sm)]" style={{ border: "1px solid var(--color-gray-100)" }}>
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-[13px] font-semibold text-[var(--color-gray-900)]">{a.title}</p>
                      {a.is_submitted && <span className="badge badge-success text-[10px]">Done</span>}
                    </div>
                    <p className="text-[11px] text-[var(--color-gray-500)] mt-1">
                      {a.course_code} · Due {format(parseISO(a.due_date), "MMM d, h:mm a")}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 animate-fade-in animate-fade-in-delay-4">
        {/* Attendance */}
        <div className="card">
          <CardHeader title="Attendance" href="/attendance" />
          <div className="p-4">
            {attendance.length === 0 ? (
              <div className="empty-state py-6"><HiOutlineCheckCircle className="empty-state-icon" /><h3>No data yet</h3></div>
            ) : (
              <div className="space-y-4">
                {attendance.map((a: any) => {
                  const pct = parseFloat(a.attendance_percentage);
                  return (
                    <div key={a.course_code}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div>
                          <p className="text-[13px] font-semibold text-[var(--color-gray-900)]">{a.course_title}</p>
                          <p className="text-[11px] text-[var(--color-gray-400)]">{a.course_code}</p>
                        </div>
                        <span className="text-[14px] font-bold text-[var(--color-gray-900)]">{a.attendance_percentage}%</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-bar-fill" style={{
                          width: `${Math.min(100, pct)}%`,
                          background: pct >= 75 ? "var(--color-success-500)" : pct >= 50 ? "var(--color-warning-500)" : "var(--color-danger-500)",
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Sessions */}
        <div className="card">
          <CardHeader title="Upcoming Classes" />
          <div className="p-4">
            {sessions.length === 0 ? (
              <div className="empty-state py-6"><HiOutlineCalendarDays className="empty-state-icon" /><h3>No upcoming classes</h3></div>
            ) : (
              <div className="space-y-2">
                {sessions.map((s: any) => (
                  <div key={s.id} className="flex items-center gap-3 p-3 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-50)] transition-colors">
                    <div className="w-11 h-11 rounded-[var(--radius-sm)] flex flex-col items-center justify-center flex-shrink-0" style={{ background: "var(--color-gray-50)", border: "1px solid var(--color-gray-200)" }}>
                      <span className="text-[9px] font-bold uppercase" style={{ color: "var(--color-primary-600)" }}>{format(parseISO(s.date), "EEE")}</span>
                      <span className="text-[15px] font-bold text-[var(--color-gray-900)] leading-none">{format(parseISO(s.date), "d")}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-[var(--color-gray-900)]">{s.title}</p>
                      <p className="text-[11px] text-[var(--color-gray-500)]">
                        {s.course_code} · {s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)}
                        {s.location ? ` · ${s.location}` : ""}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

/* ──────── Instructor ──────── */
function InstructorDashboard({ data }: { data: any }) {
  const courses = data.courses || [];
  const pending = data.pending_submissions || [];
  const stats = data.assignment_stats || [];

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in animate-fade-in-delay-1">
        <StatCard icon={HiOutlineAcademicCap} value={courses.length} label="Active Courses" color="primary" />
        <StatCard icon={HiOutlineClipboard} value={pending.length} label="Pending Submissions" color="warning" />
        <StatCard icon={HiOutlineArrowTrendingUp} value={courses.reduce((s: number, c: any) => s + c.enrolled_count, 0)} label="Total Students" color="success" />
        <StatCard icon={HiOutlineCalendarDays} value={(data.upcoming_sessions || []).length} label="Upcoming Sessions" color="info" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card animate-fade-in animate-fade-in-delay-2">
          <CardHeader title="My Courses" href="/courses" />
          <div className="p-4">
            {courses.length === 0 ? (
              <div className="empty-state py-8"><HiOutlineAcademicCap className="empty-state-icon" /><h3>No courses</h3></div>
            ) : (
              <div className="space-y-1">
                {courses.map((c: any) => (
                  <Link key={c.id} href={`/courses/${c.id}`} className="flex items-center gap-3 p-3 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-50)] transition-colors group">
                    <div className="w-9 h-9 rounded-[var(--radius-sm)] flex items-center justify-center text-white text-[12px] font-bold flex-shrink-0" style={{ background: "var(--color-gray-900)" }}>
                      {c.code.slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-[var(--color-gray-900)] truncate group-hover:text-[var(--color-primary-600)] transition-colors">{c.title}</p>
                      <p className="text-[11px] text-[var(--color-gray-500)]">{c.code}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[13px] font-bold text-[var(--color-gray-900)]">{c.enrolled_count}/{c.max_enrollment}</p>
                      <p className="text-[10px] text-[var(--color-gray-400)]">enrolled</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card animate-fade-in animate-fade-in-delay-3">
          <CardHeader title="To Grade" />
          <div className="p-4">
            {pending.length === 0 ? (
              <div className="empty-state py-8"><HiOutlineCheckCircle className="empty-state-icon" /><h3>All graded</h3></div>
            ) : (
              <div className="space-y-2">
                {pending.slice(0, 8).map((s: any) => (
                  <div key={s.id} className="p-3 rounded-[var(--radius-sm)]" style={{ border: "1px solid var(--color-gray-100)" }}>
                    <div className="flex items-center justify-between">
                      <p className="text-[13px] font-semibold text-[var(--color-gray-900)]">{s.student_name}</p>
                      {s.is_late && <span className="badge badge-warning text-[10px]">Late</span>}
                    </div>
                    <p className="text-[11px] text-[var(--color-gray-500)] mt-0.5">{s.assignment_title} · {s.course_code}</p>
                    <p className="text-[11px] text-[var(--color-gray-400)] mt-1 flex items-center gap-1">
                      <HiOutlineClock className="w-3 h-3" />
                      {formatDistanceToNow(parseISO(s.submitted_at), { addSuffix: true })}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {stats.length > 0 && (
        <div className="card animate-fade-in animate-fade-in-delay-4">
          <CardHeader title="Assignment Stats" />
          <div className="table-container" style={{ border: "none", borderRadius: 0 }}>
            <table className="table">
              <thead>
                <tr><th>Course</th><th>Assignments</th><th>Submissions</th><th>Graded</th><th>Pending</th></tr>
              </thead>
              <tbody>
                {stats.map((s: any) => (
                  <tr key={s.course_code}>
                    <td>
                      <p className="font-semibold text-[var(--color-gray-900)]">{s.course_title}</p>
                      <p className="text-[11px] text-[var(--color-gray-400)]">{s.course_code}</p>
                    </td>
                    <td>{s.total_assignments}</td>
                    <td>{s.total_submissions}</td>
                    <td><span className="badge badge-success">{s.graded_submissions}</span></td>
                    <td>{s.pending_grading > 0 ? <span className="badge badge-warning">{s.pending_grading}</span> : <span className="text-[var(--color-gray-300)]">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

/* ──────── Admin ──────── */
function AdminDashboard({ data }: { data: any }) {
  const t = data.totals || {};
  const items = [
    { label: "Total Users", value: t.users, icon: HiOutlineUsers, color: "primary" },
    { label: "Students", value: t.students, icon: HiOutlineUsers, color: "success" },
    { label: "Instructors", value: t.instructors, icon: HiOutlineUsers, color: "info" },
    { label: "Departments", value: t.departments, icon: HiOutlineAcademicCap, color: "primary" },
    { label: "Active Courses", value: t.active_courses, icon: HiOutlineAcademicCap, color: "success" },
    { label: "Enrollments", value: t.enrollments, icon: HiOutlineCheckCircle, color: "info" },
    { label: "Assignments", value: t.assignments, icon: HiOutlineClipboard, color: "warning" },
    { label: "Pending Grading", value: t.pending_grading, icon: HiOutlineExclamationTriangle, color: "danger" },
    { label: "Submissions", value: t.submissions, icon: HiOutlineClipboard, color: "primary" },
    { label: "Sessions", value: t.attendance_sessions, icon: HiOutlineCalendarDays, color: "success" },
    { label: "Announcements", value: t.announcements, icon: HiOutlineMegaphone, color: "info" },
    { label: "Total Courses", value: t.courses, icon: HiOutlineAcademicCap, color: "primary" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {items.map((s, i) => (
        <div key={s.label} className="animate-fade-in" style={{ animationDelay: `${i * 0.03}s`, opacity: 0 }}>
          <StatCard icon={s.icon} value={s.value ?? 0} label={s.label} color={s.color} />
        </div>
      ))}
    </div>
  );
}
