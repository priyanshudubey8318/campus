/**
 * TypeScript definitions for Phase 7 PulseCase subsystem.
 */

export type CaseType =
  | "ACADEMIC_SUPPORT"
  | "ATTENDANCE_INTERVENTION"
  | "EARLY_WARNING_TRIAGE"
  | "WELLBEING_REFERRAL";

export type CaseStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "WAITING_FOR_STUDENT"
  | "FOLLOW_UP_SCHEDULED"
  | "RESOLVED"
  | "CLOSED";

export type CasePriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export type CaseTriggerSource =
  | "PULSERISK_SPI"
  | "PULSEWATCH_SHIFT"
  | "FACULTY_REFERRAL"
  | "STUDENT_REQUEST"
  | "MANUAL_ADVISOR";

export type ResolutionOutcome =
  | "IMPROVED_ENGAGEMENT"
  | "ACADEMIC_PLAN_ESTABLISHED"
  | "REFERRED_TO_EXTERNAL_RESOURCE"
  | "STUDENT_UNRESPONSIVE"
  | "NO_FURTHER_ACTION";

export type NoteType =
  | "ADVISING_NOTE"
  | "STUDENT_INTERACTION"
  | "COUNSELOR_CONFIDENTIAL"
  | "ACTION_PLAN"
  | "SYSTEM_EVENT";

export type ConfidentialityLevel =
  | "STANDARD"
  | "RESTRICTED_ADVISING"
  | "COUNSELOR_CONFIDENTIAL";

export type InterventionType =
  | "ONE_ON_ONE_ADVISING"
  | "PEER_TUTORING_REFERRAL"
  | "ACADEMIC_SKILLS_WORKSHOP"
  | "ATTENDANCE_CONTRACT"
  | "WELLBEING_SUPPORT"
  | "COURSE_LOAD_ADJUSTMENT";

export type InterventionStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED";

export type FollowUpType =
  | "CHECK_IN_MEETING"
  | "ACADEMIC_PROGRESS_REVIEW"
  | "ATTENDANCE_CHECK"
  | "WELLBEING_FOLLOW_UP";

export type FollowUpStatus =
  | "SCHEDULED"
  | "COMPLETED"
  | "MISSED"
  | "RESCHEDULED"
  | "CANCELLED";

// Payloads
export interface CaseCreatePayload {
  student_id: string;
  case_type: CaseType;
  priority?: CasePriority;
  trigger_source?: CaseTriggerSource;
  reason: string;
  evidence_references?: Record<string, any>;
  assigned_staff_id?: string;
}

export interface FacultyReferralCreatePayload {
  student_id: string;
  reason: string;
  course_id?: string;
  priority?: CasePriority;
}

export interface CaseAssignPayload {
  assigned_staff_id: string;
}

export interface CaseStatusUpdatePayload {
  status: CaseStatus;
  notes?: string;
}

export interface CaseResolvePayload {
  resolution_outcome: ResolutionOutcome;
  resolution_summary: string;
}

export interface CaseClosePayload {
  closing_notes?: string;
}

export interface CaseNoteCreatePayload {
  note_type?: NoteType;
  confidentiality_level?: ConfidentialityLevel;
  content: string;
}

export interface CaseInterventionCreatePayload {
  intervention_type: InterventionType;
  title: string;
  description: string;
  assigned_to_user_id?: string;
  target_completion_date?: string; // YYYY-MM-DD
}

export interface CaseInterventionUpdatePayload {
  status: InterventionStatus;
  outcome_notes?: string;
}

export interface CaseFollowUpCreatePayload {
  scheduled_date: string; // YYYY-MM-DD
  scheduled_time?: string;
  follow_up_type?: FollowUpType;
  assigned_staff_id?: string;
  notes?: string;
}

export interface CaseFollowUpUpdatePayload {
  status: FollowUpStatus;
  notes?: string;
}

// Data Entities
export interface CaseNote {
  id: string;
  case_id: string;
  author_user_id: string;
  author_name?: string | null;
  note_type: NoteType | string;
  confidentiality_level: ConfidentialityLevel | string;
  content: string;
  created_at: string;
}

export interface CaseIntervention {
  id: string;
  case_id: string;
  intervention_type: InterventionType | string;
  title: string;
  description: string;
  assigned_to_user_id?: string | null;
  target_completion_date?: string | null;
  status: InterventionStatus | string;
  completed_at?: string | null;
  outcome_notes?: string | null;
  created_at: string;
}

export interface CaseFollowUp {
  id: string;
  case_id: string;
  scheduled_date: string;
  scheduled_time?: string | null;
  follow_up_type: FollowUpType | string;
  assigned_staff_id: string;
  assigned_staff_name?: string | null;
  status: FollowUpStatus | string;
  notes?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface SupportCase {
  id: string;
  institution_id: string;
  case_number: string;
  student_id: string;
  student_name?: string | null;
  student_enrollment_number?: string | null;
  case_type: CaseType | string;
  status: CaseStatus | string;
  priority: CasePriority | string;
  trigger_source: CaseTriggerSource | string;
  reason: string;
  evidence_references?: Record<string, any> | null;
  assigned_staff_id?: string | null;
  assigned_advisor_id?: string | null;
  assigned_staff_name?: string | null;
  assigned_staff_role?: string | null;
  referred_by_user_id?: string | null;
  referred_by_name?: string | null;
  resolution_outcome?: ResolutionOutcome | string | null;
  resolution_summary?: string | null;
  resolved_at?: string | null;
  closed_by_user_id?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
  interventions_count: number;
  follow_ups_count: number;
  notes_count: number;
}

export interface SupportCaseDetail extends SupportCase {
  notes: CaseNote[];
  interventions: CaseIntervention[];
  follow_ups: CaseFollowUp[];
}

export interface FacultyReferralReceipt {
  id: string;
  case_number: string;
  student_id: string;
  student_name?: string | null;
  case_type: string;
  status: string;
  priority: string;
  created_at: string;
  closed_at?: string | null;
  resolution_outcome?: string | null;
}

export interface StudentSupportItem {
  id: string;
  title: string;
  description: string;
  intervention_type: string;
  target_date?: string | null;
  status: string;
}

export interface StudentUpcomingFollowUp {
  id: string;
  scheduled_date: string;
  scheduled_time?: string | null;
  follow_up_type: string;
  status: string;
}

export interface StudentSupportSummary {
  active_cases_count: number;
  assigned_advisor_name?: string | null;
  support_action_items: StudentSupportItem[];
  upcoming_follow_ups: StudentUpcomingFollowUp[];
}
