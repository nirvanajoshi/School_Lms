"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import api from "@/lib/api";
import Link from "next/link";
import toast from "react-hot-toast";
import { format, parseISO } from "date-fns";
import type { Course, CourseMaterial, Schedule, Syllabus } from "@/lib/types";
import {
  HiOutlineArrowLeft,
  HiOutlineDocumentText,
  HiOutlineCalendarDays,
  HiOutlineBookOpen,
  HiOutlineUsers,
  HiOutlineLink,
  HiOutlineDocumentDuplicate,
} from "react-icons/hi2";

type Tab = "materials" | "schedule" | "syllabus";

export default function CourseDetailPage() {
  const params = useParams();
  const id = params.id;
  const [course, setCourse] = useState<Course | null>(null);
  const [materials, setMaterials] = useState<CourseMaterial[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("materials");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.get(`/courses/courses/${id}/`),
      api.get(`/courses/courses/${id}/materials/`).catch(() => ({ data: [] })),
      api.get(`/courses/courses/${id}/schedules/`).catch(() => ({ data: [] })),
      api.get(`/courses/courses/${id}/syllabus/`).catch(() => ({ data: null })),
    ])
      .then(([courseRes, matRes, schedRes, syllRes]) => {
        setCourse(courseRes.data);
        setMaterials(Array.isArray(matRes.data) ? matRes.data : matRes.data.results || []);
        setSchedules(Array.isArray(schedRes.data) ? schedRes.data : schedRes.data.results || []);
        setSyllabus(syllRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="spinner" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="empty-state py-20">
        <h3>Course not found</h3>
      </div>
    );
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: "materials", label: "Materials", icon: HiOutlineDocumentText },
    { key: "schedule", label: "Schedule", icon: HiOutlineCalendarDays },
    { key: "syllabus", label: "Syllabus", icon: HiOutlineBookOpen },
  ];

  const materialTypeColors: Record<string, string> = {
    lecture_note: "badge-primary",
    slide: "badge-info",
    video: "badge-danger",
    document: "badge-gray",
    link: "badge-success",
    other: "badge-warning",
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back */}
      <Link
        href="/courses"
        className="inline-flex items-center gap-2 text-sm font-medium text-[var(--gray-500)] hover:text-[var(--gray-900)] transition-colors"
      >
        <HiOutlineArrowLeft className="w-4 h-4" />
        Back to courses
      </Link>

      {/* Course header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--primary-400)] to-[var(--primary-600)] flex items-center justify-center text-white text-lg font-bold flex-shrink-0">
            {course.code.slice(0, 3)}
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-[var(--gray-900)]">{course.title}</h1>
            <p className="text-[var(--gray-500)] mt-0.5">
              {course.code} · {course.department_name}
            </p>
            {course.description && (
              <p className="text-sm text-[var(--gray-600)] mt-3 leading-relaxed">
                {course.description}
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="badge badge-primary">{course.semester} {course.year}</span>
            <span className="badge badge-success">
              {course.enrollment_count}/{course.max_enrollment} enrolled
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-5 pt-5 border-t border-[var(--gray-100)]">
          <div>
            <p className="text-xs text-[var(--gray-500)]">Instructor</p>
            <p className="text-sm font-semibold text-[var(--gray-900)]">{course.instructor_name}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--gray-500)]">Available Spots</p>
            <p className="text-sm font-semibold text-[var(--gray-900)]">{course.available_spots}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--gray-500)]">Status</p>
            <span className={`badge ${course.is_active ? "badge-success" : "badge-gray"}`}>
              {course.is_active ? "Active" : "Inactive"}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-[var(--gray-100)] rounded-xl">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                activeTab === tab.key
                  ? "bg-white text-[var(--gray-900)] shadow-sm"
                  : "text-[var(--gray-500)] hover:text-[var(--gray-700)]"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {activeTab === "materials" && (
        <div className="card">
          <div className="p-5 border-b border-[var(--gray-100)]">
            <h2 className="font-bold text-[var(--gray-900)]">Course Materials</h2>
          </div>
          <div className="p-5">
            {materials.length === 0 ? (
              <div className="empty-state py-8">
                <HiOutlineDocumentText className="empty-state-icon" />
                <h3>No materials yet</h3>
                <p>Materials will appear here once uploaded</p>
              </div>
            ) : (
              <div className="space-y-3">
                {materials.map((mat) => (
                  <div
                    key={mat.id}
                    className="flex items-center gap-4 p-4 rounded-xl border border-[var(--gray-100)] hover:border-[var(--primary-200)] hover:bg-[var(--gray-50)] transition-all"
                  >
                    <div className="w-10 h-10 rounded-lg bg-[var(--gray-100)] flex items-center justify-center flex-shrink-0">
                      {mat.material_type === "video" ? (
                        <span className="text-lg">🎥</span>
                      ) : mat.material_type === "slide" ? (
                        <span className="text-lg">📊</span>
                      ) : mat.material_type === "link" ? (
                        <HiOutlineLink className="w-5 h-5 text-[var(--gray-500)]" />
                      ) : (
                        <HiOutlineDocumentDuplicate className="w-5 h-5 text-[var(--gray-500)]" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-[var(--gray-900)]">{mat.title}</p>
                      {mat.description && (
                        <p className="text-xs text-[var(--gray-500)] truncate">{mat.description}</p>
                      )}
                      <p className="text-xs text-[var(--gray-400)] mt-0.5">
                        {mat.week_number ? `Week ${mat.week_number} · ` : ""}
                        Uploaded by {mat.uploaded_by_name}
                      </p>
                    </div>
                    <span className={`badge ${materialTypeColors[mat.material_type] || "badge-gray"}`}>
                      {mat.material_type.replace("_", " ")}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "schedule" && (
        <div className="card">
          <div className="p-5 border-b border-[var(--gray-100)]">
            <h2 className="font-bold text-[var(--gray-900)]">Class Schedule</h2>
          </div>
          <div className="p-5">
            {schedules.length === 0 ? (
              <div className="empty-state py-8">
                <HiOutlineCalendarDays className="empty-state-icon" />
                <h3>No schedule set</h3>
                <p>Schedule will appear here once configured</p>
              </div>
            ) : (
              <div className="space-y-3">
                {schedules.map((sched) => (
                  <div
                    key={sched.id}
                    className="flex items-center gap-4 p-4 rounded-xl border border-[var(--gray-100)]"
                  >
                    <div className="w-12 h-12 rounded-xl bg-[var(--primary-50)] flex flex-col items-center justify-center flex-shrink-0">
                      <span className="text-[10px] font-bold text-[var(--primary-600)] uppercase">
                        {sched.day_of_week.slice(0, 3)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-[var(--gray-900)]">
                        {sched.start_time.slice(0, 5)} – {sched.end_time.slice(0, 5)}
                      </p>
                      <p className="text-xs text-[var(--gray-500)]">
                        {sched.location || "No location set"}
                        {sched.room ? ` · Room ${sched.room}` : ""}
                      </p>
                    </div>
                    <span className={`badge ${sched.is_active ? "badge-success" : "badge-gray"}`}>
                      {sched.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "syllabus" && (
        <div className="card">
          <div className="p-5 border-b border-[var(--gray-100)]">
            <h2 className="font-bold text-[var(--gray-900)]">Syllabus</h2>
          </div>
          <div className="p-5">
            {!syllabus ? (
              <div className="empty-state py-8">
                <HiOutlineBookOpen className="empty-state-icon" />
                <h3>No syllabus available</h3>
                <p>The instructor hasn&apos;t uploaded a syllabus yet</p>
              </div>
            ) : (
              <div className="space-y-6">
                {[
                  { label: "Course Objectives", content: syllabus.objectives },
                  { label: "Prerequisites", content: syllabus.prerequisites },
                  { label: "Textbooks", content: syllabus.textbooks },
                  { label: "Grading Policy", content: syllabus.grading_policy },
                  { label: "Course Policies", content: syllabus.course_policies },
                  { label: "Weekly Outline", content: syllabus.weekly_outline },
                ]
                  .filter((s) => s.content)
                  .map((section) => (
                    <div key={section.label}>
                      <h3 className="text-sm font-bold text-[var(--gray-900)] uppercase tracking-wide mb-2">
                        {section.label}
                      </h3>
                      <div className="text-sm text-[var(--gray-600)] leading-relaxed whitespace-pre-wrap bg-[var(--gray-50)] rounded-xl p-4">
                        {section.content}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
