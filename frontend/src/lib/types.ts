// Auth
export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

// Profile
export interface Department {
  id: number;
  name: string;
  code: string;
  description: string;
}

export interface Profile {
  id: number;
  user: number;
  role: "student" | "instructor" | "admin";
  phone_number: string;
  date_of_birth: string | null;
  address: string;
  profile_picture: string | null;
  department: number | null;
  department_name: string | null;
  is_active: boolean;
  full_name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Student {
  id: number;
  profile: number;
  student_id: string;
  enrollment_date: string;
  year_level: number;
  gpa: string;
  advisor: number | null;
  full_name: string;
  email: string;
  department_name: string | null;
  advisor_name: string | null;
}

export interface Instructor {
  id: number;
  profile: number;
  employee_id: string;
  hire_date: string;
  rank: string;
  department: number;
  department_name: string;
  office_location: string;
  office_hours: string;
  full_name: string;
  email: string;
}

// Courses
export interface Course {
  id: number;
  title: string;
  code: string;
  description: string;
  department: number;
  department_name: string;
  instructor: number;
  instructor_name: string;
  semester: string;
  year: number;
  max_enrollment: number;
  is_active: boolean;
  enrollment_count: number;
  available_spots: number;
  created_at: string;
  updated_at: string;
}

export interface Enrollment {
  id: number;
  course: number;
  course_code: string;
  course_name: string;
  student: number;
  student_name: string;
  student_id: string;
  status: "enrolled" | "dropped" | "completed";
  enrolled_at: string;
  grade: string | null;
}

export interface CourseMaterial {
  id: number;
  course: number;
  title: string;
  description: string;
  material_type: string;
  file: string | null;
  external_url: string;
  week_number: number | null;
  is_published: boolean;
  uploaded_by: number;
  uploaded_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface Schedule {
  id: number;
  course: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  location: string;
  room: string;
  is_active: boolean;
  created_at: string;
}

export interface Syllabus {
  id: number;
  course: number;
  course_code: string;
  course_title: string;
  objectives: string;
  prerequisites: string;
  textbooks: string;
  grading_policy: string;
  course_policies: string;
  weekly_outline: string;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

// Assignments
export interface Assignment {
  id: number;
  title: string;
  description: string;
  course: number;
  course_name: string;
  created_by: number;
  created_by_name: string;
  status: "draft" | "published" | "closed" | "archived";
  submission_type: "file" | "text" | "both";
  max_points: number;
  weight: string;
  due_date: string;
  allow_late_submissions: boolean;
  late_penalty_per_day: string;
  is_overdue: boolean;
  submission_count: number;
  created_at: string;
  updated_at: string;
}

export interface Submission {
  id: number;
  assignment: number;
  assignment_title: string;
  student: number;
  student_name: string;
  text_content: string;
  submitted_at: string;
  updated_at: string;
  status: "submitted" | "graded" | "returned";
  is_late: boolean;
  feedback: string;
  attachments: SubmissionAttachment[];
  grade: Grade | null;
}

export interface SubmissionAttachment {
  id: number;
  submission: number;
  file: string;
  filename: string;
  file_size: number;
  uploaded_at: string;
}

export interface Grade {
  id: number;
  submission: number;
  graded_by: number;
  graded_by_name: string;
  points: string;
  max_points: number;
  graded_at: string;
  comments: string;
}

// Attendance
export interface AttendanceSession {
  id: number;
  course: number;
  course_code: string;
  course_name: string;
  title: string;
  date: string;
  start_time: string;
  end_time: string;
  location: string;
  status: "scheduled" | "in_progress" | "completed" | "cancelled";
  notes: string;
  created_by: number;
  created_by_name: string;
  total_expected: number;
  total_present: number;
  attendance_rate: number;
  records: AttendanceRecord[];
  created_at: string;
  updated_at: string;
}

export interface AttendanceRecord {
  id: number;
  session: number;
  student: number;
  student_name: string;
  student_id: string;
  status: "present" | "absent" | "late" | "excused";
  check_in_time: string | null;
  notes: string;
  recorded_by: number;
  recorded_by_name: string;
  recorded_at: string;
  updated_at: string;
}

export interface AttendanceSummary {
  id: number;
  student: number;
  student_name: string;
  student_id: string;
  course: number;
  course_code: string;
  course_name: string;
  total_sessions: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  attendance_percentage: string;
  last_updated: string;
}

// Announcements
export interface AnnouncementCategory {
  id: number;
  name: string;
  type: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface Announcement {
  id: number;
  title: string;
  content: string;
  category: number | null;
  category_name: string | null;
  priority: number;
  target_audience: string;
  is_published: boolean;
  published_at: string | null;
  expires_at: string | null;
  created_by: number;
  created_by_name: string;
  attachments: AnnouncementAttachment[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnnouncementAttachment {
  id: number;
  announcement: number;
  file: string;
  filename: string;
  uploaded_at: string;
}

// Dashboard
export interface StudentDashboard {
  role: "student";
  enrolled_courses: {
    id: number;
    code: string;
    title: string;
    instructor: string;
    semester: string;
    year: number;
  }[];
  upcoming_assignments: {
    id: number;
    title: string;
    course_code: string;
    due_date: string;
    max_points: number;
    is_submitted: boolean;
  }[];
  attendance_summaries: {
    course_code: string;
    course_title: string;
    attendance_percentage: string;
    total_sessions: number;
    present_count: number;
  }[];
  upcoming_sessions: {
    id: number;
    course_code: string;
    title: string;
    date: string;
    start_time: string;
    end_time: string;
    location: string;
  }[];
  active_announcements: number;
}

export interface InstructorDashboard {
  role: "instructor";
  courses: {
    id: number;
    code: string;
    title: string;
    semester: string;
    year: number;
    enrolled_count: number;
    max_enrollment: number;
  }[];
  pending_submissions: {
    id: number;
    assignment_title: string;
    course_code: string;
    student_name: string;
    student_id: string;
    submitted_at: string;
    is_late: boolean;
  }[];
  assignment_stats: {
    course_code: string;
    course_title: string;
    total_assignments: number;
    published_assignments: number;
    total_submissions: number;
    graded_submissions: number;
    pending_grading: number;
  }[];
  upcoming_sessions: {
    id: number;
    course_code: string;
    title: string;
    date: string;
    start_time: string;
    end_time: string;
    status: string;
    location: string;
  }[];
}

export interface AdminDashboard {
  role: "admin";
  totals: {
    users: number;
    students: number;
    instructors: number;
    departments: number;
    courses: number;
    active_courses: number;
    enrollments: number;
    assignments: number;
    submissions: number;
    pending_grading: number;
    attendance_sessions: number;
    announcements: number;
  };
}

// Pagination
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
