export interface StudentProfile {
  id: string;
  user_id: string;
  enrollment_number: string;
  program_id: string;
  batch_id: string;
  section_id?: string | null;
  current_semester: number;
  admission_date: string;
  academic_status: string;
  created_at: string;
  program_name?: string | null;
  batch_name?: string | null;
  section_name?: string | null;
  full_name?: string | null;
  email?: string | null;
}

export interface FacultyProfile {
  id: string;
  user_id: string;
  employee_id: string;
  department_id: string;
  designation: string;
  qualification?: string | null;
  specialization?: string | null;
  joining_date: string;
  is_active: boolean;
  created_at: string;
  department_name?: string | null;
  full_name?: string | null;
  email?: string | null;
}

export interface Course {
  id: string;
  institution_id: string;
  department_id: string;
  code: string;
  title: string;
  credits: number;
  course_type: string;
  syllabus_summary?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Enrollment {
  id: string;
  student_id: string;
  course_id: string;
  term_id: string;
  section_id?: string | null;
  enrollment_date: string;
  status: string;
  created_at: string;
  course_code?: string | null;
  course_title?: string | null;
  course_credits?: number | null;
  term_name?: string | null;
}

export interface FacultyCourseAssignment {
  id: string;
  faculty_id: string;
  course_id: string;
  term_id: string;
  section_id?: string | null;
  role: string;
  created_at: string;
  course_code?: string | null;
  course_title?: string | null;
  term_name?: string | null;
  section_name?: string | null;
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  course_id: string;
  term_id: string;
  session_date: string;
  session_slot: string;
  status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED" | string;
  source: string;
  recorded_by_faculty_id?: string | null;
  remarks?: string | null;
  created_at: string;
  course_code?: string | null;
  course_title?: string | null;
}

export interface AttendanceSummary {
  total_sessions: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  attendance_percentage: number;
}

export interface Assignment {
  id: string;
  course_id: string;
  term_id: string;
  section_id?: string | null;
  created_by_faculty_id: string;
  title: string;
  description?: string | null;
  max_marks: number;
  weightage_percentage: number;
  release_date: string;
  due_date: string;
  cutoff_date?: string | null;
  allow_late_submission: boolean;
  created_at: string;
  course_code?: string | null;
  course_title?: string | null;
}

export interface AssignmentSubmission {
  id: string;
  assignment_id: string;
  student_id: string;
  attempt_number: number;
  submission_content?: string | null;
  attachment_path?: string | null;
  submitted_at: string;
  status: "DRAFT" | "SUBMITTED" | "LATE" | "EVALUATED" | "RESUBMITTED" | string;
  marks_obtained?: number | null;
  feedback?: string | null;
  evaluated_by_faculty_id?: string | null;
  evaluated_at?: string | null;
  created_at: string;
  assignment_title?: string | null;
  max_marks?: number | null;
}

export interface Assessment {
  id: string;
  course_id: string;
  term_id: string;
  section_id?: string | null;
  created_by_faculty_id: string;
  title: string;
  assessment_type: "QUIZ" | "MIDTERM" | "FINAL" | "PRACTICAL" | "PROJECT" | string;
  max_marks: number;
  weightage_percentage: number;
  assessment_date: string;
  created_at: string;
  course_code?: string | null;
  course_title?: string | null;
}

export interface AssessmentResult {
  id: string;
  assessment_id: string;
  student_id: string;
  marks_obtained?: number | null;
  is_absent: boolean;
  remarks?: string | null;
  evaluated_by_faculty_id?: string | null;
  evaluated_at?: string | null;
  created_at: string;
  assessment_title?: string | null;
  assessment_type?: string | null;
  max_marks?: number | null;
  student_enrollment_number?: string | null;
  student_name?: string | null;
}

export interface Department {
  id: string;
  institution_id: string;
  name: string;
  code: string;
  created_at: string;
}

export interface AcademicTerm {
  id: string;
  institution_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at: string;
}

export interface AttendanceRecordCreate {
  student_id: string;
  course_id: string;
  term_id: string;
  session_date: string;
  session_slot: string;
  status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED";
  source?: "MANUAL" | "IMPORT" | "LMS" | "BIOMETRIC" | "API";
  remarks?: string;
}

export interface AssignmentCreate {
  course_id: string;
  term_id: string;
  section_id?: string | null;
  title: string;
  description?: string;
  max_marks: number;
  weightage_percentage?: number;
  release_date: string;
  due_date: string;
  cutoff_date?: string | null;
  allow_late_submission?: boolean;
}

export interface AssignmentSubmissionCreate {
  submission_content?: string;
  attachment_path?: string;
}

export interface SubmissionGradeRequest {
  marks_obtained: number;
  feedback?: string;
}

export interface AssessmentCreate {
  course_id: string;
  term_id: string;
  section_id?: string | null;
  title: string;
  assessment_type?: string;
  max_marks: number;
  weightage_percentage?: number;
  assessment_date: string;
}

export interface AssessmentResultCreate {
  student_id: string;
  marks_obtained?: number | null;
  is_absent?: boolean;
  remarks?: string;
}

