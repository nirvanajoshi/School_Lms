"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format, parseISO, formatDistanceToNow } from "date-fns";
import type { Announcement, PaginatedResponse } from "@/lib/types";
import { HiOutlineMegaphone, HiOutlineExclamationTriangle } from "react-icons/hi2";

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    api.get<PaginatedResponse<Announcement>>("/announcements/announcements/")
      .then((r) => setAnnouncements(r.data.results)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const pCfg: Record<number, { badge: string; label: string; border?: string }> = {
    1: { badge: "badge-gray", label: "Low" },
    2: { badge: "badge-info", label: "Normal" },
    3: { badge: "badge-warning", label: "High", border: "border-l-[3px] border-l-[var(--color-warning-500)]" },
    4: { badge: "badge-danger", label: "Urgent", border: "border-l-[3px] border-l-[var(--color-danger-500)]" },
  };

  const audience: Record<string, string> = { all: "Everyone", students: "Students", instructors: "Instructors", admins: "Admins" };

  return (
    <div className="max-w-[800px] mx-auto space-y-5">
      <div className="page-header"><h1>Announcements</h1><p>Stay updated with the latest news</p></div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : announcements.length === 0 ? (
        <div className="empty-state py-20"><HiOutlineMegaphone className="empty-state-icon" /><h3>No announcements</h3></div>
      ) : (
        <div className="space-y-2.5">
          {announcements.map((a) => {
            const pc = pCfg[a.priority] || pCfg[2];
            const open = expandedId === a.id;
            return (
              <div key={a.id} className={`card overflow-hidden transition-all hover:shadow-[var(--shadow-sm)] ${pc.border || ""}`}>
                <button onClick={() => setExpandedId(open ? null : a.id)} className="w-full text-left p-5">
                  <div className="flex items-start gap-3">
                    {a.priority >= 3 && (
                      <HiOutlineExclamationTriangle className={`w-4 h-4 flex-shrink-0 mt-0.5`} style={{ color: a.priority === 4 ? "var(--color-danger-500)" : "var(--color-warning-500)" }} />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-[14px] font-semibold text-[var(--color-gray-900)]">{a.title}</h3>
                        <span className={`badge ${pc.badge}`}>{pc.label}</span>
                        {a.category_name && <span className="badge badge-gray">{a.category_name}</span>}
                      </div>
                      <div className="flex items-center gap-2.5 mt-1.5 text-[11px] text-[var(--color-gray-400)]">
                        <span>{formatDistanceToNow(parseISO(a.created_at), { addSuffix: true })}</span>
                        <span>·</span>
                        <span>{audience[a.target_audience]}</span>
                        <span>·</span>
                        <span>{a.created_by_name}</span>
                      </div>
                      {!open && <p className="text-[13px] text-[var(--color-gray-600)] mt-2 line-clamp-2">{a.content}</p>}
                    </div>
                    <svg className={`w-4 h-4 text-[var(--color-gray-400)] flex-shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </button>
                {open && (
                  <div className="px-5 pb-5">
                    <div className="text-[13px] text-[var(--color-gray-700)] leading-relaxed whitespace-pre-wrap rounded-[var(--radius-sm)] p-4" style={{ background: "var(--color-gray-50)" }}>
                      {a.content}
                    </div>
                    {a.published_at && <p className="text-[11px] text-[var(--color-gray-400)] mt-3">Published {format(parseISO(a.published_at), "MMM d, yyyy 'at' h:mm a")}</p>}
                    {a.expires_at && <p className="text-[11px] text-[var(--color-gray-400)]">Expires {format(parseISO(a.expires_at), "MMM d, yyyy")}</p>}
                    {a.attachments?.length > 0 && (
                      <div className="mt-3">
                        <p className="text-[11px] font-semibold uppercase" style={{ color: "var(--color-gray-400)" }}>Attachments</p>
                        <div className="space-y-1 mt-1.5">
                          {a.attachments.map((att) => (
                            <a key={att.id} href={att.file} target="_blank" rel="noopener noreferrer" className="text-[13px] hover:underline" style={{ color: "var(--color-primary-600)" }}>
                              📎 {att.filename}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
