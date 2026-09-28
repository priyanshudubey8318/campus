/**
 * PulseWatch behavioral monitoring types.
 */

export type BehaviorSeverity = "NORMAL" | "MILD_CHANGE" | "MODERATE_CHANGE" | "SIGNIFICANT_CHANGE";

export interface SignalEvidence {
  signal_type: string;
  severity: BehaviorSeverity;
  metric_name: string;
  current_value: number | null;
  baseline_value: number | null;
  delta_value: number | null;
  evidence_payload?: Record<string, any> | null;
}

export interface CohortContext {
  program_code?: string | null;
  batch_name?: string | null;
  section_name?: string | null;
  cohort_attendance_rate?: number | null;
  cohort_submission_rate?: number | null;
  cohort_assessment_average?: number | null;
  context_note: string;
}

export interface AcademicContext {
  term_name?: string | null;
  upcoming_assessments_count: number;
  assignment_deadline_clustering: boolean;
  untracked_contexts: string[];
}

export interface Explainability {
  what_changed: string;
  compared_with: string;
  observation_period: string;
  data_sufficiency: string;
  disclaimer: string;
}

export interface PulseWatchSummary {
  student_id: string;
  observation_window_days: number;
  window_start_date: string;
  window_end_date: string;
  baseline_start_date: string;
  baseline_end_date: string;
  data_quality: string;
  overall_status: BehaviorSeverity;
  summary_text: string;
  signals: SignalEvidence[];
  cohort_context: CohortContext;
  academic_context: AcademicContext;
  explainability: Explainability;
  algorithm_version: string;
  calculated_at: string;
}

export interface BehaviorEvent {
  id: string;
  student_id: string;
  event_type: string;
  severity: BehaviorSeverity;
  observation_window_days: number;
  window_start_date: string;
  window_end_date: string;
  summary_text: string;
  status: string;
  algorithm_version: string;
  detected_at: string;
  evidence: SignalEvidence[];
}
