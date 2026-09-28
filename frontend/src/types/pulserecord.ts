/**
 * TypeScript definitions for Phase 6 PulseRecord subsystem.
 */

export type LeaveType = "MEDICAL" | "ACADEMIC_DUTY" | "PERSONAL" | "EMERGENCY" | "BEREAVEMENT";
export type LeaveStatus = "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED" | "CANCELLED";

export interface LeaveRequestPayload {
  leave_type: LeaveType;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  reason: string;
}

export interface LeaveReviewPayload {
  status: "APPROVED" | "REJECTED";
  reviewer_notes?: string;
}

export interface LeaveCancelPayload {
  cancellation_reason: string;
}

export interface LeaveAttachment {
  id: string;
  leave_request_id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  created_at: string;
}

export interface LeaveRequest {
  id: string;
  institution_id: string;
  student_id: string;
  student_name?: string | null;
  enrollment_number?: string | null;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  days_count: number;
  reason: string;
  status: LeaveStatus;
  reviewed_by_user_id?: string | null;
  reviewer_name?: string | null;
  reviewed_at?: string | null;
  reviewer_notes?: string | null;
  cancellation_reason?: string | null;
  cancelled_at?: string | null;
  attachment_count: number;
  attachments?: LeaveAttachment[];
  created_at: string;
  updated_at: string;
}

export type ComplaintCategory =
  | "ACADEMIC_INTEGRITY"
  | "FACILITY_HARASSMENT"
  | "DISCRIMINATION"
  | "GRADING_DISPUTE"
  | "SAFETY_CONCERN"
  | "OTHER";

export type ComplaintTargetType = "STUDENT" | "FACULTY" | "DEPARTMENT" | "FACILITY" | "OTHER";

export type ComplaintStatus =
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "NEEDS_INFORMATION"
  | "VERIFIED"
  | "DISMISSED"
  | "OTHER_AUTHORIZED_OUTCOME"
  | "APPEALED"
  | "RESOLVED"
  | "CLOSED";

export interface ComplaintCreatePayload {
  category: ComplaintCategory;
  target_type: ComplaintTargetType;
  target_student_id?: string;
  target_department_id?: string;
  title: string;
  description: string;
  is_anonymous: boolean;
}

export interface ComplaintEvidence {
  id: string;
  complaint_id: string;
  uploader_user_id?: string | null;
  uploader_role: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  description?: string | null;
  is_confidential: boolean;
  is_sealed: boolean;
  created_at: string;
}

export interface ComplaintAppeal {
  id: string;
  complaint_id: string;
  appellant_user_id?: string | null;
  appeal_number: number;
  reason: string;
  status: "SUBMITTED" | "UNDER_REVIEW" | "UPHELD" | "OVERTURNED" | "MODIFIED" | "DISMISSED";
  reviewer_user_id?: string | null;
  reviewer_notes?: string | null;
  disposition_summary?: string | null;
  decided_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Complaint {
  id: string;
  institution_id: string;
  complaint_code: string;
  complainant_user_id?: string | null;
  complainant_role?: string | null;
  is_anonymous: boolean;
  category: ComplaintCategory;
  target_type: ComplaintTargetType;
  target_student_id?: string | null;
  target_department_id?: string | null;
  title: string;
  description: string;
  status: ComplaintStatus;
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  assigned_at?: string | null;
  adjudication_outcome?: string | null;
  adjudication_summary?: string | null;
  internal_reviewer_notes?: string | null;
  info_request_details?: string | null;
  info_response_details?: string | null;
  evidence_count: number;
  appeal_count: number;
  evidence?: ComplaintEvidence[];
  appeals?: ComplaintAppeal[];
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
}
