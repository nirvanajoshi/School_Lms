"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { format, parseISO } from "date-fns";
import type { AttendanceSession, AttendanceSummary, PaginatedResponse } from "@/lib/types";
import { HiOutlineCheckCircle, HiOutlineCalendarDays } from "react-icons/hi2";

export default function AttendancePage() {
  const { profile } = useAuth();
  const [tab, setTab] = useState<"sessions" | "summaries">("sessions");
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [summaries, setSummaries] = useState<AttendanceSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<PaginatedResponse<AttendanceSession>>("/attendance/sessions/"),
      api.get<PaginatedResponse<AttendanceSummary>>("/attendance/summaries/"),
    ]).then(([s, m]) => { setSessions(s.data.results); setSummaries(m.data.results); })
      .catch(console.error).finally(() => setLoading(false));
  }, []);

  const sessStatus: Record<string, { badge: string; label: string }> = {
    scheduled: { badge: "badge-info", label: "Scheduled" },
    in_progress: { badge: "badge-warning", label: "In Progress" },
    completed: { badge: "badge-success", label: "Completed" },
    cancelled: { badge: "badge-gray", label: "Cancelled" },
  };

  const recStatus: Record<string, { badge: string; emoji: string }> = {
    present: { badge: "badge-success", emoji: "✓" },
    absent: { badge: "badge-danger", emoji: "✗" },
    late: { badge: "badge-warning", emoji: "⏰" },
    excused: { badge: "badge-info", emoji: "N" },
  };

  return (
    <div className="max-w-[900px] mx-auto space-y-5">
      <div className="page-header"><h1>Attendance</h1><p>Track your class attendance</p></div>

      <div className="tabs" style={{ width: "fit-content" }}>
        <button onClick={() => setTab("sessions")} className={`tab-btn ${tab === "sessions" ? "active" : ""}`}>
          <HiOutlineCalendarDays className="w-4 h-4" />Sessions
        </button>
        <button onClick={() => setTab("summaries")} className={`tab-btn ${tab === "summaries" ? "active" : ""}`}>
          <HiOutlineCheckCircle className="w-4 h-4" />Summary
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : tab === "sessions" ? (
        sessions.length === 0 ? (
          <div className="empty-state py-20"><HiOutlineCalendarDays className="empty-state-icon" /><h3>No sessions yet</h3></div>
        ) : (
          <div className="space-y-2.5">
            {sessions.map((s) => {
              const sc = sessStatus[s.status] || sessStatus.scheduled;
              return (
                <div key={s.id} className="card p-5">
                  <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                    <div className="w-12 h-12 rounded-[var(--radius-sm)] flex flex-col items-center justify-center flex-shrink-0" style={{ background: "var(--color-gray-50)", border: "1px solid var(--color-gray-200)" }}>
                      <span className="text-[9px] font-bold uppercase" style={{ color: "var(--color-primary-600)" }}>{format(parseISO(s.date), "EEE")}</span>
                      <span className="text-[16px] font-bold text-[var(--color-gray-900)] leading-none">{format(parseISO(s.date), "d")}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-[14px] font-semibold text-[var(--color-gray-900)]">{s.title}</h3>
                        <span className={`badge ${sc.badge}`}>{sc.label}</span>
                      </div>
                      <p className="text-[12px] text-[var(--color-gray-500)] mt-1">
                        {s.course_code} · {s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)}
                        {s.location ? ` · ${s.location}` : ""}
                      </p>
                      {(profile?.role === "instructor" || profile?.role === "admin") && s.records?.length > 0 && (
                        <div className="mt-2.5 flex flex-wrap gap-1.5">
                          {s.records.map((r) => {
                            const rc = recStatus[r.status] || recStatus.absent;
                            return <span key={r.id} className={`badge ${rc.badge}`}>{r.student_name}</span>;
                          })}
                        </div>
                      )}
                      {s.status === "completed" && (
                        <div className="mt-2 flex items-center gap-4 text-[11px] text-[var(--color-gray-500)]">
                          <span>👥 {s.total_present}/{s.total_expected} present</span>
                          <span>📊 {s.attendance_rate}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : summaries.length === 0 ? (
        <div className="empty-state py-20"><HiOutlineCheckCircle className="empty-state-icon" /><h3>No summary</h3></div>
      ) : (
        <div className="space-y-3">
          {summaries.map((sum) => {
            const pct = parseFloat(sum.attendance_percentage);
            return (
              <div key={sum.id} className="card p-5">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="text-[14px] font-semibold text-[var(--color-gray-900)]">{sum.course_name}</h3>
                    <p className="text-[11px] text-[var(--color-gray-400)]">{sum.course_code}</p>
                  </div>
                  <span className="text-[22px] font-bold" style={{ color: pct >= 75 ? "var(--color-success-600)" : pct >= 50 ? "var(--color-warning-600)" : "var(--color-danger-600)" }}>
                    {sum.attendance_percentage}%
                  </span>
                </div>
                <div className="progress-bar mb-3">
                  <div className="progress-bar-fill" style={{
                    width: `${Math.min(100, pct)}%`,
                    background: pct >= 75 ? "var(--color-success-500)" : pct >= 50 ? "var(--color-warning-500)" : "var(--color-danger-500)",
                  }} />
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { label: "Present", value: sum.present_count, color: "var(--color-success-600)" },
                    { label: "Absent", value: sum.absent_count, color: "var(--color-danger-600)" },
                    { label: "Late", value: sum.late_count, color: "var(--color-warning-600)" },
                    { label: "Excused", value: sum.excused_count, color: "var(--color-info-600)" },
                  ].map((s) => (
                    <div key={s.label} className="text-center py-2 rounded-[var(--radius-sm)]" style={{ background: "var(--color-gray-50)" }}>
                      <p className="text-[18px] font-bold" style={{ color: s.color }}>{s.value}</p>
                      <p className="text-[10px] font-medium uppercase" style={{ color: "var(--color-gray-400)" }}>{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
