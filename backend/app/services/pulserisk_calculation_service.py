"""PulseRisk Calculation Service.

Deterministic Support Priority Index (SPI) calculation, dynamic weight renormalization,
safety-floor precedence, and canonical temporal deduplication.
Strictly zero ML, zero LLM, and zero direct queries against raw academic tables.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.pulserisk import RiskPolicy
from app.models.pulsewatch import BehaviorEvent
from app.repositories.academic_repo import AcademicRepository
from app.repositories.pulserisk_repo import PulseRiskRepository
from app.schemas.pulsewatch import PulseWatchSummaryResponse
from app.schemas.pulserisk import (
    ExplainabilitySummarySchema,
    PulseRiskSummaryResponse,
    RiskSignalContributionSchema,
    SafetyFloorTriggerSchema,
)
from app.services.pulsewatch_calculation_service import PulseWatchCalculationService

ALGORITHM_VERSION = "pulserisk-v1.0"


class PulseRiskCalculationService:
    """Core mathematical engine for deterministic support prioritization."""

    # -------------------------------------------------------------------------
    # 1. Canonical Temporal Window Deduplication for Persistence
    # -------------------------------------------------------------------------

    @staticmethod
    def cluster_and_deduplicate_events(
        events: List[BehaviorEvent],
    ) -> List[Tuple[BehaviorEvent, int]]:
        """Cluster overlapping historical PulseWatch events and return canonical representatives.
        
        Rule: Two events belong to the same cluster if their observation date intervals
        overlap by >= 50% relative to the shorter duration:
            Overlap / min(Duration_a, Duration_b) >= 0.50
            
        Canonical Selection within cluster:
            1. Highest severity (SIGNIFICANT_CHANGE > MODERATE_CHANGE)
            2. Longest observation window_days
            3. Most recent detected_at
            
        Returns list of tuples: (canonical_event, total_cluster_event_count)
        """
        if not events:
            return []

        # Filter only moderate and significant events for persistence
        filtered_events = [e for e in events if e.severity in ["MODERATE_CHANGE", "SIGNIFICANT_CHANGE"]]
        if not filtered_events:
            return []

        # Sort chronologically by start date
        sorted_events = sorted(filtered_events, key=lambda e: (e.window_start_date, e.window_end_date))

        clusters: List[List[BehaviorEvent]] = []
        for ev in sorted_events:
            ev_start = ev.window_start_date
            ev_end = ev.window_end_date
            ev_dur = max(1, (ev_end - ev_start).days + 1)

            placed = False
            for cluster in clusters:
                # Check overlap with any event in this cluster
                for member in cluster:
                    m_start = member.window_start_date
                    m_end = member.window_end_date
                    m_dur = max(1, (m_end - m_start).days + 1)

                    # Compute intersection
                    overlap_start = max(ev_start, m_start)
                    overlap_end = min(ev_end, m_end)
                    if overlap_end >= overlap_start:
                        overlap_days = (overlap_end - overlap_start).days + 1
                        overlap_ratio = overlap_days / min(ev_dur, m_dur)
                        if overlap_ratio >= 0.50:
                            cluster.append(ev)
                            placed = True
                            break
                if placed:
                    break

            if not placed:
                clusters.append([ev])

        canonical_results = []
        severity_rank = {"SIGNIFICANT_CHANGE": 2, "MODERATE_CHANGE": 1}

        for cluster in clusters:
            # Sort cluster members by tie-breakers
            sorted_cluster = sorted(
                cluster,
                key=lambda e: (
                    severity_rank.get(e.severity, 0),
                    e.observation_window_days,
                    e.detected_at,
                ),
                reverse=True,
            )
            canonical_results.append((sorted_cluster[0], len(cluster)))

        return canonical_results

    # -------------------------------------------------------------------------
    # 2. Main Deterministic Evaluation Engine
    # -------------------------------------------------------------------------

    @classmethod
    def compute_student_priority(
        cls,
        db: Session,
        student_id: str,
        pulsewatch_summary: Optional[PulseWatchSummaryResponse] = None,
        observation_window_days: int = 14,
        reference_date: Optional[date] = None,
        policy: Optional[RiskPolicy] = None,
    ) -> PulseRiskSummaryResponse:
        """Compute the deterministic Support Priority Index (SPI) and full explainability decomposition."""
        ref_date = reference_date or date.today()

        # Resolve student profile to get institution_id
        student = AcademicRepository.get_student_profile_by_id(db, student_id)
        if not student:
            raise ValueError(f"StudentProfile not found for ID: {student_id}")

        # Resolve institution_id safely from student hierarchy
        institution_id = getattr(student, "institution_id", None)
        if not institution_id and student.program and getattr(student.program, "department_id", None):
            dept = AcademicRepository.get_department_by_id(db, student.program.department_id)
            if dept:
                institution_id = dept.institution_id
        if not institution_id:
            institutions = AcademicRepository.get_institutions(db)
            institution_id = institutions[0].id if institutions else "default_inst"

        active_policy = policy or PulseRiskRepository.get_active_policy(db, institution_id)

        # ---------------------------------------------------------------------
        # Step 1: Ingest PulseWatch Summary (Zero raw academic queries)
        # ---------------------------------------------------------------------
        pw_summary = pulsewatch_summary or PulseWatchCalculationService.compute_student_summary(
            db=db,
            student_id=student_id,
            reference_date=ref_date,
            observation_window_days=observation_window_days,
        )

        signals_map = {s.signal_type: s for s in pw_summary.signals}
        att_sig = signals_map.get("ATTENDANCE_CHANGE")
        asg_sig = signals_map.get("SUBMISSION_LATENESS") or signals_map.get("MISSED_ASSIGNMENT")
        assess_sig = signals_map.get("ASSESSMENT_PERFORMANCE")

        # ---------------------------------------------------------------------
        # Dimension 1: Attendance Factor (F_att)
        # ---------------------------------------------------------------------
        att_status = "NO_DATA"
        f_att = Decimal("0.00")
        obs_att_rate_str = None
        base_att_rate_str = None
        att_delta_str = None
        consecutive_absences = 0
        observation_sessions = 0

        if att_sig and att_sig.evidence_payload:
            att_data_quality = att_sig.evidence_payload.get("data_quality", "NO_DATA")
            consecutive_absences = int(att_sig.evidence_payload.get("consecutive_absences", 0))
            observation_sessions = int(att_sig.evidence_payload.get("observation_sessions", 0))

            if att_sig.current_value is not None:
                obs_att_rate_str = f"{att_sig.current_value:.1f}%"
            if att_sig.baseline_value is not None:
                base_att_rate_str = f"{att_sig.baseline_value:.1f}%"
            if att_sig.delta_value is not None:
                att_delta_str = f"{att_sig.delta_value:+.1f}%"

            if att_data_quality == "VALID_DATA" and att_sig.delta_value is not None:
                att_status = "VALID_DATA"
                d = float(att_sig.delta_value)
                if d >= 0.0:
                    base_f = 0.0
                elif -5.0 <= d < 0.0:
                    base_f = 10.0 * (abs(d) / 5.0)
                elif -15.0 <= d < -5.0:
                    base_f = 10.0 + 30.0 * ((abs(d) - 5.0) / 10.0)
                elif -25.0 <= d < -15.0:
                    base_f = 40.0 + 35.0 * ((abs(d) - 15.0) / 10.0)
                else:
                    base_f = min(100.0, 75.0 + 25.0 * ((abs(d) - 25.0) / 25.0))

                # Streak escalation
                if consecutive_absences == 1:
                    base_f = max(base_f, 15.0)
                elif consecutive_absences == 2:
                    base_f = max(base_f, 35.0)
                elif consecutive_absences >= 5:
                    base_f = 100.0
                elif consecutive_absences >= 3:
                    base_f = max(base_f, 75.0)

                f_att = Decimal(str(round(base_f, 2)))
            elif att_data_quality == "INSUFFICIENT_DATA":
                att_status = "INSUFFICIENT_DATA"
                # If there's an absence streak even during insufficient data window, streak applies
                if consecutive_absences >= 5:
                    f_att = Decimal("100.00")
                elif consecutive_absences >= 3:
                    f_att = Decimal("75.00")
                elif consecutive_absences == 2:
                    f_att = Decimal("35.00")
                elif consecutive_absences == 1:
                    f_att = Decimal("15.00")
            else:
                att_status = "NO_DATA"

        # ---------------------------------------------------------------------
        # Dimension 2: Coursework & Submission Factor (F_asg)
        # ---------------------------------------------------------------------
        asg_status = "NO_DATA"
        f_asg = Decimal("0.00")
        obs_asg_str = None
        base_asg_str = None
        asg_delta_str = None
        eligible_assignments = 0
        missed_assignments = 0
        late_assignments = 0

        if asg_sig and asg_sig.evidence_payload:
            asg_data_quality = asg_sig.evidence_payload.get("data_quality", "NO_DATA")
            eligible_assignments = int(asg_sig.evidence_payload.get("eligible_assignments", 0))
            missed_assignments = int(asg_sig.evidence_payload.get("missed_assignments", 0))
            late_assignments = int(asg_sig.evidence_payload.get("late_assignments", 0))

            if asg_sig.current_value is not None:
                obs_asg_str = f"{asg_sig.current_value:.1f}%"
            if asg_sig.baseline_value is not None:
                base_asg_str = f"{asg_sig.baseline_value:.1f}%"
            if asg_sig.delta_value is not None:
                asg_delta_str = f"{asg_sig.delta_value:+.1f}%"

            if asg_data_quality == "VALID_DATA" and eligible_assignments > 0:
                asg_status = "VALID_DATA"
                r_missed = missed_assignments / eligible_assignments
                r_late = late_assignments / eligible_assignments
                penalty = 20.0 if missed_assignments >= 2 else 0.0
                score_f = min(100.0, (r_missed * 80.0) + (r_late * 30.0) + penalty)
                if missed_assignments >= 3:
                    score_f = max(score_f, 80.0)
                f_asg = Decimal(str(round(score_f, 2)))
            elif asg_data_quality == "INSUFFICIENT_DATA":
                asg_status = "INSUFFICIENT_DATA"
                if missed_assignments >= 3:
                    f_asg = Decimal("80.00")
            else:
                asg_status = "NO_DATA"

        # ---------------------------------------------------------------------
        # Dimension 3: Assessment Performance Factor (F_assess)
        # ---------------------------------------------------------------------
        assess_status = "NO_DATA"
        f_assess = Decimal("0.00")
        obs_assess_str = None
        base_assess_str = None
        assess_delta_str = None
        has_assessment_absence = False
        assessments_evaluated = 0

        if assess_sig and assess_sig.evidence_payload:
            assess_data_quality = assess_sig.evidence_payload.get("data_quality", "NO_DATA")
            has_assessment_absence = bool(assess_sig.evidence_payload.get("has_assessment_absence", False))
            assessments_evaluated = int(assess_sig.evidence_payload.get("assessments_evaluated", 0))

            if has_assessment_absence:
                obs_assess_str = "Formal Assessment Absence"
            elif assess_sig.current_value is not None:
                obs_assess_str = f"{assess_sig.current_value:.1f}%"

            if assess_sig.baseline_value is not None:
                base_assess_str = f"{assess_sig.baseline_value:.1f}%"
            if assess_sig.delta_value is not None:
                assess_delta_str = f"{assess_sig.delta_value:+.1f} pts"

            if has_assessment_absence:
                # Critical formal assessment absence overrides to 100
                f_assess = Decimal("100.00")
                assess_status = "VALID_DATA"
            elif assess_data_quality == "VALID_DATA" and assess_sig.delta_value is not None:
                assess_status = "VALID_DATA"
                ad = float(assess_sig.delta_value)
                if ad >= 0.0:
                    score_a = 0.0
                elif -5.0 <= ad < 0.0:
                    score_a = 10.0 * (abs(ad) / 5.0)
                elif -15.0 <= ad < -5.0:
                    score_a = 10.0 + 30.0 * ((abs(ad) - 5.0) / 10.0)
                elif -25.0 <= ad < -15.0:
                    score_a = 40.0 + 35.0 * ((abs(ad) - 15.0) / 10.0)
                else:
                    score_a = min(100.0, 75.0 + 25.0 * ((abs(ad) - 25.0) / 25.0))
                f_assess = Decimal(str(round(score_a, 2)))
            elif assess_data_quality == "INSUFFICIENT_DATA":
                assess_status = "INSUFFICIENT_DATA"
            else:
                assess_status = "NO_DATA"

        # ---------------------------------------------------------------------
        # Dimension 4: Longitudinal Persistence Factor (F_persist)
        # ---------------------------------------------------------------------
        history_events = PulseRiskRepository.get_student_historical_behavior_events(
            db, student_id, lookback_days=60, reference_date=ref_date
        )
        canonical_clusters = cls.cluster_and_deduplicate_events(history_events)

        decay_half_life = active_policy.persistence_half_life_days or 14
        decay_sum = 0.0

        for canon_event, cluster_size in canonical_clusters:
            # Days elapsed
            t_days = max(0, (ref_date - canon_event.window_end_date).days)
            # lambda(t) = exp(- ln(2) * t / half_life)
            decay_factor = math.exp(-0.693147 * t_days / decay_half_life)
            weight_severity = 1.0 if canon_event.severity == "SIGNIFICANT_CHANGE" else 0.5
            decay_sum += weight_severity * decay_factor

        f_persist = Decimal(str(round(min(100.0, decay_sum * 40.0), 2)))
        persist_status = "VALID_DATA"

        # ---------------------------------------------------------------------
        # Step 2: Critical Safety-Floor Trigger Evaluation
        # ---------------------------------------------------------------------
        safety_triggers: List[SafetyFloorTriggerSchema] = []

        # T1: Formal assessment absence
        if has_assessment_absence:
            safety_triggers.append(
                SafetyFloorTriggerSchema(
                    trigger_name="FORMAL_ASSESSMENT_ABSENCE",
                    mandated_tier="URGENT_PRIORITY",
                    mandated_floor=Decimal("75.00"),
                    reason="Absence recorded for a formal scheduled examination or assessment in observation window.",
                )
            )

        # T2: Severe consecutive absences (>= 5)
        if consecutive_absences >= 5:
            safety_triggers.append(
                SafetyFloorTriggerSchema(
                    trigger_name="SEVERE_ABSENCE_STREAK",
                    mandated_tier="URGENT_PRIORITY",
                    mandated_floor=Decimal("75.00"),
                    reason=f"Severe attendance disruption with {consecutive_absences} consecutive recorded absences.",
                )
            )
        # T3: Moderate consecutive absences (>= 3)
        elif consecutive_absences >= 3:
            safety_triggers.append(
                SafetyFloorTriggerSchema(
                    trigger_name="MODERATE_ABSENCE_STREAK",
                    mandated_tier="ELEVATED_PRIORITY",
                    mandated_floor=Decimal("50.00"),
                    reason=f"Attendance streak disruption with {consecutive_absences} consecutive recorded absences.",
                )
            )

        # T4: Multiple missed assignments (>= 3)
        if missed_assignments >= 3:
            safety_triggers.append(
                SafetyFloorTriggerSchema(
                    trigger_name="MULTIPLE_MISSED_COURSEWORK",
                    mandated_tier="ELEVATED_PRIORITY",
                    mandated_floor=Decimal("50.00"),
                    reason=f"Pacing disruption with {missed_assignments} missed coursework assignments.",
                )
            )

        # T5: Dual significant shift in PulseWatch
        significant_pulse_count = sum(1 for s in pw_summary.signals if s.severity == "SIGNIFICANT_CHANGE")
        if significant_pulse_count >= 2:
            safety_triggers.append(
                SafetyFloorTriggerSchema(
                    trigger_name="DUAL_SIGNIFICANT_PULSE_SHIFT",
                    mandated_tier="URGENT_PRIORITY",
                    mandated_floor=Decimal("80.00"),
                    reason="Multiple concurrent significant behavioral shifts detected across academic dimensions.",
                )
            )

        active_floor = Decimal("0.00")
        if safety_triggers:
            active_floor = max(t.mandated_floor for t in safety_triggers)

        # ---------------------------------------------------------------------
        # Step 3: Confidence Score & Dimension Renormalization
        # ---------------------------------------------------------------------
        dimension_validity = {
            "ATTENDANCE": att_status == "VALID_DATA",
            "COURSEWORK": asg_status == "VALID_DATA",
            "ASSESSMENTS": assess_status == "VALID_DATA",
            "LONGITUDINAL_PERSISTENCE": True,  # Persistence is always valid if checked
        }

        base_weights = {
            "ATTENDANCE": active_policy.weight_attendance,
            "COURSEWORK": active_policy.weight_coursework,
            "ASSESSMENTS": active_policy.weight_assessment,
            "LONGITUDINAL_PERSISTENCE": active_policy.weight_persistence,
        }

        # Calculate aggregate confidence C = sum of base weights for valid dimensions
        # Note: If no academic metrics are available, longitudinal persistence alone does not grant high confidence
        academic_valid_weights = sum(
            base_weights[d] for d in ["ATTENDANCE", "COURSEWORK", "ASSESSMENTS"] if dimension_validity[d]
        )
        total_valid_weights = sum(base_weights[d] for d in base_weights if dimension_validity[d])

        confidence_score = Decimal(str(round(total_valid_weights, 2)))

        # ---------------------------------------------------------------------
        # Step 4 & 5 & 6: Mathematical Precedence Resolution
        # ---------------------------------------------------------------------
        assigned_weights: Dict[str, Decimal] = {}
        weighted_contributions: Dict[str, Decimal] = {}

        if active_floor > Decimal("0.00"):
            # CASE A: Verified Safety Trigger Exists -> Overrides Confidence unconditionally!
            data_quality = "VALID_DATA" if confidence_score >= Decimal("0.35") else "VERIFIED_TRIGGER_SPARSE_CONTEXT"

            # Renormalize among valid dimensions to compute raw SPI
            if total_valid_weights > Decimal("0.00"):
                for d in base_weights:
                    if dimension_validity[d]:
                        assigned_weights[d] = Decimal(str(round(base_weights[d] / total_valid_weights, 3)))
                    else:
                        assigned_weights[d] = Decimal("0.000")
            else:
                for d in base_weights:
                    assigned_weights[d] = Decimal("0.000")

            weighted_contributions["ATTENDANCE"] = Decimal(str(round(f_att * assigned_weights["ATTENDANCE"], 2)))
            weighted_contributions["COURSEWORK"] = Decimal(str(round(f_asg * assigned_weights["COURSEWORK"], 2)))
            weighted_contributions["ASSESSMENTS"] = Decimal(str(round(f_assess * assigned_weights["ASSESSMENTS"], 2)))
            weighted_contributions["LONGITUDINAL_PERSISTENCE"] = Decimal(
                str(round(f_persist * assigned_weights["LONGITUDINAL_PERSISTENCE"], 2))
            )

            raw_spi = sum(weighted_contributions.values())
            final_spi = max(raw_spi, active_floor)

        elif confidence_score < Decimal("0.35") or academic_valid_weights == Decimal("0.00"):
            # CASE B: No safety floor AND confidence < 0.35 -> INSUFFICIENT_DATA / SPI = 0
            data_quality = "INSUFFICIENT_DATA"
            final_spi = Decimal("0.00")
            for d in base_weights:
                assigned_weights[d] = Decimal("0.000")
                weighted_contributions[d] = Decimal("0.00")

        else:
            # CASE C: No safety floor AND confidence >= 0.35 -> Standard Weighted Renormalization
            data_quality = "VALID_DATA"
            for d in base_weights:
                if dimension_validity[d]:
                    assigned_weights[d] = Decimal(str(round(base_weights[d] / total_valid_weights, 3)))
                else:
                    assigned_weights[d] = Decimal("0.000")

            weighted_contributions["ATTENDANCE"] = Decimal(str(round(f_att * assigned_weights["ATTENDANCE"], 2)))
            weighted_contributions["COURSEWORK"] = Decimal(str(round(f_asg * assigned_weights["COURSEWORK"], 2)))
            weighted_contributions["ASSESSMENTS"] = Decimal(str(round(f_assess * assigned_weights["ASSESSMENTS"], 2)))
            weighted_contributions["LONGITUDINAL_PERSISTENCE"] = Decimal(
                str(round(f_persist * assigned_weights["LONGITUDINAL_PERSISTENCE"], 2))
            )

            final_spi = min(Decimal("100.00"), sum(weighted_contributions.values()))

        # Determine Priority Tier
        if data_quality == "INSUFFICIENT_DATA" and active_floor == Decimal("0.00"):
            priority_tier = "LOW_PRIORITY"
        elif final_spi >= active_policy.threshold_urgent:
            priority_tier = "URGENT_PRIORITY"
        elif final_spi >= active_policy.threshold_elevated:
            priority_tier = "ELEVATED_PRIORITY"
        elif final_spi >= active_policy.threshold_moderate:
            priority_tier = "MODERATE_PRIORITY"
        else:
            priority_tier = "LOW_PRIORITY"

        # Determine Primary Driver
        primary_driver: Optional[str] = None
        if safety_triggers:
            # Primary driver maps directly to the active safety floor
            trigger_driver_map = {
                "FORMAL_ASSESSMENT_ABSENCE": "ASSESSMENTS",
                "SEVERE_ABSENCE_STREAK": "ATTENDANCE",
                "MODERATE_ABSENCE_STREAK": "ATTENDANCE",
                "MULTIPLE_MISSED_COURSEWORK": "COURSEWORK",
                "DUAL_SIGNIFICANT_PULSE_SHIFT": "MULTIPLE_DRIVERS",
            }
            primary_driver = trigger_driver_map.get(safety_triggers[0].trigger_name, "ATTENDANCE")
        else:
            non_zero_contribs = {k: v for k, v in weighted_contributions.items() if v > Decimal("0.00")}
            if non_zero_contribs:
                primary_driver = max(non_zero_contribs, key=non_zero_contribs.get)

        # ---------------------------------------------------------------------
        # Step 7: Build Contributions Schema and Structured Narrative
        # ---------------------------------------------------------------------
        contributions_schema = [
            RiskSignalContributionSchema(
                dimension="ATTENDANCE",
                metric_label="Attendance Shift & Streaks",
                observed_value=obs_att_rate_str,
                baseline_value=base_att_rate_str,
                delta_value=att_delta_str,
                factor_score=f_att,
                assigned_weight=assigned_weights["ATTENDANCE"],
                weighted_contribution=weighted_contributions["ATTENDANCE"],
                data_quality=att_status,
                source_signal="ATTENDANCE_CHANGE",
                context_details={
                    "consecutive_absences": consecutive_absences,
                    "observation_sessions": observation_sessions,
                },
            ),
            RiskSignalContributionSchema(
                dimension="COURSEWORK",
                metric_label="Submission Velocity & Completion",
                observed_value=obs_asg_str,
                baseline_value=base_asg_str,
                delta_value=asg_delta_str,
                factor_score=f_asg,
                assigned_weight=assigned_weights["COURSEWORK"],
                weighted_contribution=weighted_contributions["COURSEWORK"],
                data_quality=asg_status,
                source_signal="SUBMISSION_LATENESS",
                context_details={
                    "eligible_assignments": eligible_assignments,
                    "missed_assignments": missed_assignments,
                    "late_assignments": late_assignments,
                },
            ),
            RiskSignalContributionSchema(
                dimension="ASSESSMENTS",
                metric_label="Assessment Performance & Formal Presence",
                observed_value=obs_assess_str,
                baseline_value=base_assess_str,
                delta_value=assess_delta_str,
                factor_score=f_assess,
                assigned_weight=assigned_weights["ASSESSMENTS"],
                weighted_contribution=weighted_contributions["ASSESSMENTS"],
                data_quality=assess_status,
                source_signal="ASSESSMENT_PERFORMANCE",
                context_details={
                    "has_assessment_absence": has_assessment_absence,
                    "assessments_evaluated": assessments_evaluated,
                },
            ),
            RiskSignalContributionSchema(
                dimension="LONGITUDINAL_PERSISTENCE",
                metric_label="Recurrent Shifts (Past 60 Days)",
                observed_value=f"{len(canonical_clusters)} canonical shift(s)",
                baseline_value="0",
                delta_value=None,
                factor_score=f_persist,
                assigned_weight=assigned_weights["LONGITUDINAL_PERSISTENCE"],
                weighted_contribution=weighted_contributions["LONGITUDINAL_PERSISTENCE"],
                data_quality=persist_status,
                source_signal="BEHAVIOR_EVENT_HISTORY",
                context_details={
                    "canonical_incidents_count": len(canonical_clusters),
                    "raw_events_evaluated": len(history_events),
                },
            ),
        ]

        # Formulate structured explanation summary
        summary_narratives = []
        if priority_tier == "LOW_PRIORITY":
            if data_quality == "INSUFFICIENT_DATA":
                summary_narratives.append(
                    "Academic activity is currently sparse; baseline data is being established."
                )
            else:
                summary_narratives.append(
                    "Academic engagement across attendance, coursework, and evaluations is stable."
                )
        else:
            if safety_triggers:
                for st in safety_triggers:
                    summary_narratives.append(st.reason)
            else:
                if f_att >= Decimal("30.00") and att_delta_str:
                    summary_narratives.append(f"Attendance declined by {att_delta_str} from historical baseline.")
                if f_asg >= Decimal("30.00"):
                    summary_narratives.append(
                        f"Coursework pacing friction: {missed_assignments} missed, {late_assignments} late submissions."
                    )
                if f_assess >= Decimal("30.00") and assess_delta_str:
                    summary_narratives.append(f"Assessment performance shifted by {assess_delta_str}.")
                if f_persist >= Decimal("30.00"):
                    summary_narratives.append(
                        f"Compounding persistence detected: {len(canonical_clusters)} recurring shift(s) in past 60 days."
                    )

        summary_text = (
            " ".join(summary_narratives)
            if summary_narratives
            else f"Student is prioritized at {priority_tier.replace('_', ' ').title()}."
        )

        now = datetime.now(timezone.utc)
        return PulseRiskSummaryResponse(
            student_id=student_id,
            evaluation_date=ref_date,
            observation_window_days=observation_window_days,
            support_priority_index=final_spi,
            priority_tier=priority_tier,
            confidence_score=confidence_score,
            data_quality=data_quality,
            primary_driver=primary_driver,
            algorithm_version=ALGORITHM_VERSION,
            policy_version=active_policy.policy_version,
            policy_name=active_policy.name,
            calculated_at=now,
            contributions=contributions_schema,
            safety_floors_triggered=safety_triggers,
            explainability=ExplainabilitySummarySchema(
                summary=summary_text,
                primary_driver=primary_driver,
            ),
        )
