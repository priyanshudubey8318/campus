"""PulseWatch deterministic calculation service.

Pure domain service that computes academic behavioral engagement features,
personal historical baselines, deltas, and multi-signal classifications.
Zero database writes.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.academic import AcademicTerm, StudentProfile
from app.repositories.academic_repo import AcademicRepository
from app.repositories.pulsewatch_repo import PulseWatchRepository
from app.schemas.pulsewatch import (
    AcademicContextSchema,
    CohortContextSchema,
    ExplainabilitySchema,
    PulseWatchSummaryResponse,
    SignalEvidenceSchema,
)

ALGORITHM_VERSION = "pulsewatch-v1.0"


class PulseWatchCalculationService:
    """Pure domain calculation engine for PulseWatch."""

    @staticmethod
    def compute_student_summary(
        db: Session,
        student_id: str,
        reference_date: Optional[date] = None,
        observation_window_days: int = 14,
        baseline_window_days: int = 30,
    ) -> PulseWatchSummaryResponse:
        """Compute full PulseWatch engagement summary deterministically with zero database writes."""
        t_ref = reference_date or date.today()

        # ---------------------------------------------------------------------
        # 1. Leakage Prevention: Non-overlapping window date arithmetic
        # ---------------------------------------------------------------------
        t_obs_end = t_ref
        t_obs_start = t_ref - timedelta(days=observation_window_days - 1)

        t_base_end = t_obs_start - timedelta(days=1)
        t_base_start = t_base_end - timedelta(days=baseline_window_days - 1)

        # Assertion: T_base_end strictly precedes T_obs_start
        assert t_base_end < t_obs_start, "Baseline window must strictly end before observation window begins"

        eval_datetime = datetime.combine(t_ref, time.max, tzinfo=timezone.utc)
        obs_start_dt = datetime.combine(t_obs_start, time.min, tzinfo=timezone.utc)
        obs_end_dt = datetime.combine(t_obs_end, time.max, tzinfo=timezone.utc)
        base_start_dt = datetime.combine(t_base_start, time.min, tzinfo=timezone.utc)
        base_end_dt = datetime.combine(t_base_end, time.max, tzinfo=timezone.utc)

        signals: List[SignalEvidenceSchema] = []
        data_quality_flags: List[str] = []

        # ---------------------------------------------------------------------
        # 2. Attendance Signal
        # ---------------------------------------------------------------------
        obs_att_records = PulseWatchRepository.get_attendance_in_window(db, student_id, t_obs_start, t_obs_end)
        base_att_records = PulseWatchRepository.get_attendance_in_window(db, student_id, t_base_start, t_base_end)

        # Baseline attendance rate
        base_att_valid = [r for r in base_att_records if r.status != "EXCUSED"]
        base_att_count = len(base_att_valid)
        base_att_rate: Optional[Decimal] = None
        att_data_quality = "VALID_DATA"

        if base_att_count == 0:
            att_data_quality = "NO_DATA"
        elif base_att_count < 3:
            att_data_quality = "INSUFFICIENT_DATA"
        else:
            base_present = sum(1 for r in base_att_valid if r.status in ["PRESENT", "LATE"])
            base_att_rate = Decimal(str(round((base_present / base_att_count) * 100.0, 2)))

        data_quality_flags.append(att_data_quality)

        # Observation attendance rate
        obs_att_valid = [r for r in obs_att_records if r.status != "EXCUSED"]
        obs_att_count = len(obs_att_valid)
        obs_att_rate: Optional[Decimal] = None

        if obs_att_count > 0:
            obs_present = sum(1 for r in obs_att_valid if r.status in ["PRESENT", "LATE"])
            obs_att_rate = Decimal(str(round((obs_present / obs_att_count) * 100.0, 2)))

        # Consecutive absence count in observation window
        consecutive_absences = 0
        max_consecutive_absences = 0
        for r in obs_att_records:
            if r.status == "ABSENT":
                consecutive_absences += 1
                if consecutive_absences > max_consecutive_absences:
                    max_consecutive_absences = consecutive_absences
            elif r.status in ["PRESENT", "LATE"]:
                consecutive_absences = 0

        # Attendance classification
        att_severity = "NORMAL"
        att_delta: Optional[Decimal] = None

        if att_data_quality == "VALID_DATA" and obs_att_rate is not None and base_att_rate is not None:
            att_delta = obs_att_rate - base_att_rate
            delta_float = float(att_delta)

            if delta_float >= -5.0:
                att_severity = "NORMAL"
            elif -15.0 <= delta_float < -5.0:
                att_severity = "MILD_CHANGE"
            elif -25.0 <= delta_float < -15.0:
                att_severity = "MODERATE_CHANGE"
            else:  # delta_float < -25.0
                att_severity = "SIGNIFICANT_CHANGE"

        # Deterministic Override: consecutive_absences >= 3 -> SIGNIFICANT_CHANGE regardless of percentage delta
        if max_consecutive_absences >= 3:
            att_severity = "SIGNIFICANT_CHANGE"

        signals.append(
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity=att_severity if (att_data_quality == "VALID_DATA" or max_consecutive_absences >= 3) else "NORMAL",
                metric_name="Attendance Rate",
                current_value=obs_att_rate,
                baseline_value=base_att_rate,
                delta_value=att_delta,
                evidence_payload={
                    "observation_sessions": obs_att_count,
                    "baseline_sessions": base_att_count,
                    "consecutive_absences": max_consecutive_absences,
                    "absent_count": sum(1 for r in obs_att_records if r.status == "ABSENT"),
                    "late_count": sum(1 for r in obs_att_records if r.status == "LATE"),
                    "data_quality": att_data_quality,
                },
            )
        )

        # ---------------------------------------------------------------------
        # 3. Coursework & Assignment Submissions
        # ---------------------------------------------------------------------
        obs_asgs = PulseWatchRepository.get_eligible_assignments_in_window(db, student_id, obs_start_dt, obs_end_dt)
        base_asgs = PulseWatchRepository.get_eligible_assignments_in_window(db, student_id, base_start_dt, base_end_dt)

        base_asg_count = len(base_asgs)
        asg_data_quality = "VALID_DATA"
        if base_asg_count == 0:
            asg_data_quality = "NO_DATA"
        elif base_asg_count < 2:
            asg_data_quality = "INSUFFICIENT_DATA"

        data_quality_flags.append(asg_data_quality)

        # Analyze observation assignments
        missed_asg_count = 0
        late_asg_count = 0
        submitted_asg_count = 0
        on_time_asg_count = 0

        for asg in obs_asgs:
            subs = PulseWatchRepository.get_submissions_for_assignment_and_student(db, asg.id, student_id)
            if subs:
                submitted_asg_count += 1
                # Earliest valid submission rule
                earliest_sub = subs[0]  # Already ordered asc by submitted_at
                if earliest_sub.submitted_at <= asg.due_date:
                    on_time_asg_count += 1
                else:
                    late_asg_count += 1
            else:
                # If deadline passed, it's missed
                if asg.due_date < eval_datetime:
                    missed_asg_count += 1

        obs_asg_count = len(obs_asgs)
        obs_submission_rate: Optional[Decimal] = None
        obs_on_time_rate: Optional[Decimal] = None

        if obs_asg_count > 0:
            obs_submission_rate = Decimal(str(round((submitted_asg_count / obs_asg_count) * 100.0, 2)))
        if submitted_asg_count > 0:
            obs_on_time_rate = Decimal(str(round((on_time_asg_count / submitted_asg_count) * 100.0, 2)))

        # Coursework severity classification
        asg_severity = "NORMAL"
        if asg_data_quality == "VALID_DATA":
            if missed_asg_count >= 2:
                asg_severity = "SIGNIFICANT_CHANGE"
            elif missed_asg_count == 1 or late_asg_count >= 2:
                asg_severity = "MODERATE_CHANGE"
            elif missed_asg_count == 0 and late_asg_count == 1:
                asg_severity = "MILD_CHANGE"
            else:
                asg_severity = "NORMAL"

        signals.append(
            SignalEvidenceSchema(
                signal_type="SUBMISSION_LATENESS",
                severity=asg_severity if asg_data_quality == "VALID_DATA" else "NORMAL",
                metric_name="Coursework Submissions",
                current_value=obs_submission_rate,
                baseline_value=Decimal("100.00") if asg_data_quality == "VALID_DATA" else None,
                delta_value=(obs_submission_rate - Decimal("100.00")) if obs_submission_rate is not None else None,
                evidence_payload={
                    "eligible_assignments": obs_asg_count,
                    "submitted_assignments": submitted_asg_count,
                    "late_assignments": late_asg_count,
                    "missed_assignments": missed_asg_count,
                    "on_time_rate": float(obs_on_time_rate) if obs_on_time_rate is not None else None,
                    "data_quality": asg_data_quality,
                },
            )
        )

        # ---------------------------------------------------------------------
        # 4. Assessment Performance Signal
        # ---------------------------------------------------------------------
        obs_assess_pairs = PulseWatchRepository.get_assessments_and_results_in_window(db, student_id, t_obs_start, t_obs_end)
        base_assess_pairs = PulseWatchRepository.get_assessments_and_results_in_window(db, student_id, t_base_start, t_base_end)

        base_assess_count = len(base_assess_pairs)
        assess_data_quality = "VALID_DATA"
        base_assess_avg: Optional[Decimal] = None

        if base_assess_count == 0:
            assess_data_quality = "NO_DATA"
        else:
            base_pcts = []
            for a, r in base_assess_pairs:
                if r and not r.is_absent and r.marks_obtained is not None and a.max_marks > 0:
                    base_pcts.append(float(r.marks_obtained) / float(a.max_marks) * 100.0)
            if base_pcts:
                base_assess_avg = Decimal(str(round(sum(base_pcts) / len(base_pcts), 2)))
            else:
                assess_data_quality = "INSUFFICIENT_DATA"

        data_quality_flags.append(assess_data_quality)

        obs_assess_avg: Optional[Decimal] = None
        has_assessment_absence = False
        obs_pcts = []
        for a, r in obs_assess_pairs:
            if r and r.is_absent:
                has_assessment_absence = True
            elif r and r.marks_obtained is not None and a.max_marks > 0:
                obs_pcts.append(float(r.marks_obtained) / float(a.max_marks) * 100.0)

        if obs_pcts:
            obs_assess_avg = Decimal(str(round(sum(obs_pcts) / len(obs_pcts), 2)))

        assess_severity = "NORMAL"
        assess_delta: Optional[Decimal] = None

        if assess_data_quality == "VALID_DATA" and obs_assess_avg is not None and base_assess_avg is not None:
            assess_delta = obs_assess_avg - base_assess_avg
            delta_float = float(assess_delta)

            if delta_float >= -5.0:
                assess_severity = "NORMAL"
            elif -15.0 <= delta_float < -5.0:
                assess_severity = "MILD_CHANGE"
            elif -25.0 <= delta_float < -15.0:
                assess_severity = "MODERATE_CHANGE"
            else:
                assess_severity = "SIGNIFICANT_CHANGE"

            # Assessment absence escalation rule
            if has_assessment_absence:
                assess_severity = "SIGNIFICANT_CHANGE"
        elif has_assessment_absence:
            assess_severity = "SIGNIFICANT_CHANGE"

        signals.append(
            SignalEvidenceSchema(
                signal_type="ASSESSMENT_PERFORMANCE",
                severity=assess_severity if (assess_data_quality == "VALID_DATA" or has_assessment_absence) else "NORMAL",
                metric_name="Assessment Performance",
                current_value=obs_assess_avg,
                baseline_value=base_assess_avg,
                delta_value=assess_delta,
                evidence_payload={
                    "assessments_evaluated": len(obs_pcts),
                    "has_assessment_absence": has_assessment_absence,
                    "data_quality": assess_data_quality,
                },
            )
        )

        # ---------------------------------------------------------------------
        # 5. Overall Multi-Signal Combination (No Risk Scoring)
        # ---------------------------------------------------------------------
        active_severities = [s.severity for s in signals]
        sig_count = sum(1 for s in active_severities if s == "SIGNIFICANT_CHANGE")
        mod_count = sum(1 for s in active_severities if s == "MODERATE_CHANGE")
        mild_count = sum(1 for s in active_severities if s == "MILD_CHANGE")

        if sig_count >= 1 or mod_count >= 2:
            overall_status = "SIGNIFICANT_CHANGE"
        elif mod_count == 1:
            overall_status = "MODERATE_CHANGE"
        elif mild_count >= 1:
            overall_status = "MILD_CHANGE"
        else:
            overall_status = "NORMAL"

        # Overall data quality determination
        if all(q == "NO_DATA" for q in data_quality_flags):
            overall_data_quality = "NO_DATA"
            if not (max_consecutive_absences >= 3 or has_assessment_absence):
                overall_status = "NORMAL"
        elif any(q == "VALID_DATA" for q in data_quality_flags):
            overall_data_quality = "VALID_DATA"
        else:
            overall_data_quality = "INSUFFICIENT_DATA"
            if not (max_consecutive_absences >= 3 or has_assessment_absence):
                overall_status = "NORMAL"

        # ---------------------------------------------------------------------
        # 6. Structured Explainability & Summary Template
        # ---------------------------------------------------------------------
        summary_parts = []
        if overall_status == "NORMAL":
            summary_parts.append("Academic engagement is consistent with historical baseline patterns.")
        else:
            if att_severity in ["MILD_CHANGE", "MODERATE_CHANGE", "SIGNIFICANT_CHANGE"]:
                summary_parts.append(
                    f"Observed {att_severity.lower().replace('_', ' ')} in attendance ({obs_att_rate}% vs {base_att_rate}% baseline)."
                )
            if asg_severity in ["MILD_CHANGE", "MODERATE_CHANGE", "SIGNIFICANT_CHANGE"]:
                summary_parts.append(
                    f"Coursework changes detected: {missed_asg_count} missed, {late_asg_count} late submissions."
                )
            if assess_severity in ["MILD_CHANGE", "MODERATE_CHANGE", "SIGNIFICANT_CHANGE"]:
                if has_assessment_absence:
                    summary_parts.append("Absence recorded for a formal assessment.")
                elif assess_delta is not None:
                    summary_parts.append(f"Assessment performance changed by {assess_delta} percentage points.")

        summary_text = " ".join(summary_parts) if summary_parts else "Academic activity logged within expected variance."

        what_changed = summary_text
        compared_with = f"Personal historical baseline evaluated over preceding {baseline_window_days} days ({t_base_start} to {t_base_end})."
        observation_period = f"Past {observation_window_days} days ({t_obs_start} to {t_obs_end})"
        data_sufficiency = f"Baseline coverage: {att_data_quality} for attendance, {asg_data_quality} for coursework, {assess_data_quality} for assessments."

        # ---------------------------------------------------------------------
        # 7. Cohort & Academic Context (Secondary Information Only)
        # ---------------------------------------------------------------------
        student = AcademicRepository.get_student_profile_by_id(db, student_id)
        current_term = AcademicRepository.get_current_term(db)

        cohort_att = PulseWatchRepository.get_cohort_attendance_rate(db, student_id, t_obs_start, t_obs_end)
        cohort_assess = PulseWatchRepository.get_cohort_assessment_average(db, student_id, t_obs_start, t_obs_end)

        cohort_context = CohortContextSchema(
            program_code=student.program.code if student and student.program else None,
            batch_name=student.batch.name if student and student.batch else None,
            section_name=student.section.name if student and student.section else None,
            cohort_attendance_rate=cohort_att,
            cohort_assessment_average=cohort_assess,
        )

        academic_context = AcademicContextSchema(
            term_name=current_term.name if current_term else "Current Term",
            upcoming_assessments_count=len(obs_assess_pairs),
            assignment_deadline_clustering=(obs_asg_count >= 3),
        )

        return PulseWatchSummaryResponse(
            student_id=student_id,
            observation_window_days=observation_window_days,
            window_start_date=t_obs_start,
            window_end_date=t_obs_end,
            baseline_start_date=t_base_start,
            baseline_end_date=t_base_end,
            data_quality=overall_data_quality,
            overall_status=overall_status,
            summary_text=summary_text,
            signals=signals,
            cohort_context=cohort_context,
            academic_context=academic_context,
            explainability=ExplainabilitySchema(
                what_changed=what_changed,
                compared_with=compared_with,
                observation_period=observation_period,
                data_sufficiency=data_sufficiency,
            ),
            algorithm_version=ALGORITHM_VERSION,
            calculated_at=datetime.now(timezone.utc),
        )
