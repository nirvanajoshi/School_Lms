"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { format, parseISO } from "date-fns";
import toast from "react-hot-toast";
import type { Assignment, PaginatedResponse } from "@/lib/types";
import { HiOutlineClipboard, HiOutlineClock, HiOutlineCheckCircle, HiOutlineExclamationTriangle, HiOutlineDocumentArrowUp } from "react-icons/hi2";

export default function AssignmentsPage() {
  const { profile } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submittingId, setSubmittingId] = useState<number | null>(null);
  const [showSubmitModal, setShowSubmitModal] = useState<number | null>(null);
  const [textContent, setTextContent] = useState("");

  useEffect(() => {
    api.get<PaginatedResponse<Assignment>>("/assignments/assignments/").then((r) => setAssignments(r.data.results)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (assignmentId: number) => {
    setSubmittingId(assignmentId);
    try {
      await api.post("/assignments/submissions/", { assignment: assignmentId, text_content: textContent });
      toast.success("Submitted!");
      setShowSubmitModal(null);
      setTextContent("");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.response?.data?.text_content?.[0] || "Failed");
    } finally { setSubmittingId(null); }
  };

  const statusCfg: Record<string, { badge: string; icon: any; label: string }> = {
    draft: { badge: "badge-gray", icon: HiOutlineClock, label: "Draft" },
    published: { badge: "badge-success", icon: HiOutlineCheckCircle, label: "Published" },
    closed: { badge: "badge-danger", icon: HiOutlineExclamationTriangle, label: "Closed" },
    archived: { badge: "badge-warning", icon: HiOutlineClipboard, label: "Archived" },
  };

  return (
    <div className="max-w-[900px] mx-auto space-y-5">
      <div className="page-header"><h1>Assignments</h1><p>View and submit your assignments</p></div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : assignments.length === 0 ? (
        <div className="empty-state py-20"><HiOutlineClipboard className="empty-state-icon" /><h3>No assignments</h3><p>Assignments will appear here</p></div>
      ) : (
        <div className="space-y-2.5">
          {assignments.map((a) => {
            const sc = statusCfg[a.status] || statusCfg.draft;
            const Icon = sc.icon;
            const overdue = a.is_overdue && a.status === "published";
            return (
              <div key={a.id} className={`card p-5 transition-all hover:shadow-[var(--shadow-sm)] ${overdue ? "border-l-[3px] border-l-[var(--color-danger-500)]" : ""}`}>
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-[14px] font-semibold text-[var(--color-gray-900)]">{a.title}</h3>
                      <span className={`badge ${sc.badge}`}><Icon className="w-3 h-3" />{sc.label}</span>
                      <span className="badge badge-gray">{a.submission_type}</span>
                    </div>
                    <p className="text-[13px] text-[var(--color-gray-600)] mt-1.5 line-clamp-2">{a.description}</p>
                    <div className="flex flex-wrap items-center gap-3 mt-2.5 text-[11px] text-[var(--color-gray-500)]">
                      <span>📚 {a.course_name || `Course ${a.course}`}</span>
                      <span>📊 {a.max_points} pts</span>
                      <span>📅 Due {format(parseISO(a.due_date), "MMM d, yyyy 'at' h:mm a")}</span>
                      {overdue && <span className="font-semibold" style={{ color: "var(--color-danger-600)" }}>⚠️ Overdue</span>}
                      {a.allow_late_submissions && <span style={{ color: "var(--color-warning-600)" }}>Late OK (-{a.late_penalty_per_day}%/day)</span>}
                    </div>
                  </div>
                  {profile?.role === "student" && a.status === "published" && (
                    <button onClick={() => setShowSubmitModal(a.id)} className="btn btn-primary btn-sm flex-shrink-0">
                      <HiOutlineDocumentArrowUp className="w-4 h-4" />Submit
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showSubmitModal && (
        <div className="fixed inset-0 flex items-center justify-center p-4 z-50" style={{ background: "rgba(0,0,0,0.4)", backdropFilter: "blur(4px)" }}>
          <div className="bg-white rounded-[var(--radius-xl)] w-full max-w-lg animate-fade-in" style={{ boxShadow: "var(--shadow-xl)" }}>
            <div className="px-6 pt-6 pb-4" style={{ borderBottom: "1px solid var(--color-gray-100)" }}>
              <h2 className="text-[16px] font-bold text-[var(--color-gray-900)]">Submit Assignment</h2>
              <p className="text-[13px] text-[var(--color-gray-500)] mt-0.5">{assignments.find((a) => a.id === showSubmitModal)?.title}</p>
            </div>
            <div className="px-6 pt-5 pb-4">
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-2">Your Answer</label>
              <textarea className="input min-h-[180px] resize-y" style={{ fontFamily: "var(--font-mono)", fontSize: "13px" }} placeholder="Type your submission here..." value={textContent} onChange={(e) => setTextContent(e.target.value)} />
            </div>
            <div className="flex gap-3 px-6 pb-6">
              <button onClick={() => { setShowSubmitModal(null); setTextContent(""); }} className="btn btn-secondary flex-1">Cancel</button>
              <button onClick={() => handleSubmit(showSubmitModal)} disabled={submittingId === showSubmitModal || !textContent.trim()} className="btn btn-primary flex-1">
                {submittingId === showSubmitModal ? <div className="spinner" style={{ borderTopColor: "white" }} /> : "Submit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
