"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import Link from "next/link";
import toast from "react-hot-toast";
import type { Course, PaginatedResponse } from "@/lib/types";
import { HiOutlineMagnifyingGlass, HiOutlineAcademicCap } from "react-icons/hi2";

export default function CoursesPage() {
  const { profile } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [semester, setSemester] = useState("");
  const [enrolling, setEnrolling] = useState<number | null>(null);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (search) params.search = search;
      if (semester) params.semester = semester;
      const { data } = await api.get<PaginatedResponse<Course>>("/courses/courses/", { params });
      setCourses(data.results);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  useEffect(() => { fetchCourses(); }, [semester]);

  const handleEnroll = async (courseId: number) => {
    setEnrolling(courseId);
    try {
      await api.post("/courses/enrollments/enroll/", { course: courseId });
      toast.success("Enrolled successfully!");
      fetchCourses();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Could not enroll");
    } finally { setEnrolling(null); }
  };

  return (
    <div className="max-w-[1200px] mx-auto space-y-5">
      <div className="page-header">
        <h1>Courses</h1>
        <p>Browse and enroll in available courses</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <form onSubmit={(e) => { e.preventDefault(); fetchCourses(); }} className="flex gap-2 flex-1">
          <div className="relative flex-1">
            <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-gray-400)]" />
            <input type="text" placeholder="Search by title or code..." className="input pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary">Search</button>
        </form>
        <select className="input select w-auto" style={{ width: "auto", minWidth: "160px" }} value={semester} onChange={(e) => setSemester(e.target.value)}>
          <option value="">All Semesters</option>
          <option value="fall">Fall</option>
          <option value="spring">Spring</option>
          <option value="summer">Summer</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : courses.length === 0 ? (
        <div className="empty-state py-20"><HiOutlineAcademicCap className="empty-state-icon" /><h3>No courses found</h3><p>Try adjusting your search or filters</p></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {courses.map((course) => (
            <div key={course.id} className="card card-interactive p-5 flex flex-col">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-[var(--radius-sm)] flex items-center justify-center text-white text-[12px] font-bold flex-shrink-0" style={{ background: "var(--color-gray-900)" }}>
                  {course.code.slice(0, 3)}
                </div>
                <div className="flex-1 min-w-0">
                  <Link href={`/courses/${course.id}`}>
                    <h3 className="text-[14px] font-semibold text-[var(--color-gray-900)] hover:text-[var(--color-primary-600)] transition-colors">{course.title}</h3>
                  </Link>
                  <p className="text-[11px] text-[var(--color-gray-500)]">{course.code}</p>
                </div>
              </div>
              <p className="text-[13px] text-[var(--color-gray-600)] line-clamp-2 mb-3 flex-1">{course.description || "No description available"}</p>
              <div className="space-y-1.5 text-[12px] text-[var(--color-gray-500)] mb-3">
                <div className="flex justify-between"><span>Instructor</span><span className="font-medium text-[var(--color-gray-700)]">{course.instructor_name}</span></div>
                <div className="flex justify-between"><span>Schedule</span><span className="font-medium text-[var(--color-gray-700)]">{course.semester} {course.year}</span></div>
                <div className="flex justify-between"><span>Enrollment</span><span className="font-medium text-[var(--color-gray-700)]">{course.enrollment_count}/{course.max_enrollment}</span></div>
              </div>
              <div className="progress-bar mb-3">
                <div className="progress-bar-fill" style={{ width: `${(course.enrollment_count / course.max_enrollment) * 100}%`, background: "var(--color-primary-500)" }} />
              </div>
              <div className="flex gap-2">
                <Link href={`/courses/${course.id}`} className="btn btn-secondary btn-sm flex-1">Details</Link>
                {profile?.role === "student" && (
                  <button onClick={() => handleEnroll(course.id)} disabled={enrolling === course.id || course.available_spots === 0} className="btn btn-primary btn-sm flex-1">
                    {enrolling === course.id ? "Enrolling..." : course.available_spots === 0 ? "Full" : "Enroll"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
