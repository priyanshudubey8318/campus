/**
 * PulseRisk Support Prioritization types.
 *
 * Deterministic Support Priority Index (SPI) models, priority tiers,
 * explainability decompositions, risk policies, and cohort rosters.
 */

export type PriorityTier =
  | "LOW_PRIORITY"
  | "MODERATE_PRIORITY"
  | "ELEVATED_PRIORITY"
  | "URGENT_PRIORITY";

export type RiskPolicyStatus = "DRAFT" | "VALIDATED" | "ACTIVE" | "RETIRED";

export type RiskDimension =
  | "ATTENDANCE"
  | "COURSEWORK"
  | "ASSESSMENTS"
  | "LONGITUDINAL_PERSISTENCE";

export interface RiskPolicy {
  id: string;
  institution_id: string;
  code: string;
  name: string;
  description?: string | null;
  weight_attendance: number;
  weight_coursework: number;
  weight_assessment: number;
  weight_persistence: number;
  threshold_moderate: number;
  threshold_elevated: number;
  threshold_urgent: number;
  persistence_half_life_days: number;
  status: RiskPolicyStatus;
  policy_version: string;
  activated_at?: string | null;
  retired_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskSignalContribution {
  dimension: string;
  metric_label: string;
  observed_value?: string | null;
  baseline_value?: string | null;
  delta_value?: string | null;
  factor_score: number;
  assigned_weight: number;
  weighted_contribution: number;
  data_quality: string;
  source_signal?: string | null;
  context_details?: Record<string, any> | null;
}

export interface SafetyFloorTrigger {
  trigger_name: string;
  mandated_tier: string;
  mandated_floor: number;
  reason: string;
}

export interface ExplainabilitySummary {
  summary: string;
  primary_driver?: string | null;
  institutional_notice: string;
}

export interface PulseRiskSummary {
  student_id: string;
  evaluation_date: string;
  observation_window_days: number;
  support_priority_index: number;
  priority_tier: PriorityTier;
  confidence_score: number;
  data_quality: string;
  primary_driver?: string | null;
  algorithm_version: string;
  policy_version: string;
  policy_name: string;
  calculated_at: string;
  contributions: RiskSignalContribution[];
  safety_floors_triggered: SafetyFloorTrigger[];
  explainability: ExplainabilitySummary;
}

export interface StudentRiskSnapshot {
  id: string;
  student_id: string;
  policy_id: string;
  evaluation_date: string;
  window_days: number;
  support_priority_index: number;
  priority_tier: PriorityTier;
  confidence_score: number;
  data_quality: string;
  primary_driver?: string | null;
  summary_text: string;
  status: string;
  algorithm_version: string;
  policy_version: string;
  calculated_at: string;
  contributions: RiskSignalContribution[];
}

export interface CohortPriorityItem {
  student_id: string;
  student_name: string;
  roll_number: string;
  program_code?: string | null;
  section_name?: string | null;
  support_priority_index: number;
  priority_tier: PriorityTier;
  primary_driver?: string | null;
  confidence_score: number;
  data_quality: string;
  evaluation_date: string;
  calculated_at: string;
}

export interface CohortPrioritiesPage {
  items: CohortPriorityItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
