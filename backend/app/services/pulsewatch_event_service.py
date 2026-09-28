"""PulseWatch event and baseline persistence service.

Provides idempotent persistence for calculated baselines and behavioral events.
"""

from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.pulsewatch import BehaviorEvent
from app.repositories.pulsewatch_repo import PulseWatchRepository
from app.services.pulsewatch_calculation_service import (
    ALGORITHM_VERSION,
    PulseWatchCalculationService,
)


class PulseWatchEventService:
    """Service responsible for persisting PulseWatch baselines and events idempotently."""

    @staticmethod
    def evaluate_and_persist_student(
        db: Session,
        student_id: str,
        reference_date: Optional[date] = None,
        observation_window_days: int = 14,
        baseline_window_days: int = 30,
    ) -> BehaviorEvent:
        """Compute student engagement and idempotently persist baseline and event records."""
        summary = PulseWatchCalculationService.compute_student_summary(
            db=db,
            student_id=student_id,
            reference_date=reference_date,
            observation_window_days=observation_window_days,
            baseline_window_days=baseline_window_days,
        )

        now = datetime.now(timezone.utc)

        # 1. Idempotently persist baselines
        for sig in summary.signals:
            metric_type = sig.signal_type
            data_quality = sig.evidence_payload.get("data_quality", "NO_DATA") if sig.evidence_payload else "NO_DATA"
            obs_count = 0
            if metric_type == "ATTENDANCE_CHANGE":
                obs_count = sig.evidence_payload.get("baseline_sessions", 0) if sig.evidence_payload else 0
            elif metric_type == "SUBMISSION_LATENESS":
                obs_count = sig.evidence_payload.get("eligible_assignments", 0) if sig.evidence_payload else 0

            PulseWatchRepository.upsert_student_baseline(
                db=db,
                student_id=student_id,
                metric_type=metric_type,
                window_days=baseline_window_days,
                algorithm_version=ALGORITHM_VERSION,
                baseline_value=sig.baseline_value,
                observation_count=obs_count,
                data_quality=data_quality,
                calculated_at=now,
            )

        # 2. Determine primary event type
        active_signals = [s for s in summary.signals if s.severity != "NORMAL"]
        if len(active_signals) > 1:
            event_type = "MULTI_SIGNAL_CHANGE"
        elif len(active_signals) == 1:
            sig = active_signals[0]
            if sig.signal_type == "ATTENDANCE_CHANGE":
                event_type = "ATTENDANCE_DROP"
            elif sig.signal_type == "SUBMISSION_LATENESS":
                event_type = "COURSEWORK_IRREGULARITY"
            elif sig.signal_type == "ASSESSMENT_PERFORMANCE":
                event_type = "ASSESSMENT_DECLINE"
            else:
                event_type = "ACADEMIC_ENGAGEMENT_CHANGE"
        else:
            event_type = "ACADEMIC_ENGAGEMENT_CHANGE"

        evidence_payload_list = [
            {
                "signal_type": s.signal_type,
                "severity": s.severity,
                "metric_name": s.metric_name,
                "current_value": s.current_value,
                "baseline_value": s.baseline_value,
                "delta_value": s.delta_value,
                "evidence_payload": s.evidence_payload,
            }
            for s in summary.signals
        ]

        # 3. Idempotently persist BehaviorEvent and BehaviorSignalEvidence
        event = PulseWatchRepository.upsert_behavior_event(
            db=db,
            student_id=student_id,
            event_type=event_type,
            severity=summary.overall_status,
            observation_window_days=summary.observation_window_days,
            window_start_date=summary.window_start_date,
            window_end_date=summary.window_end_date,
            summary_text=summary.summary_text,
            algorithm_version=ALGORITHM_VERSION,
            detected_at=now,
            evidence_list=evidence_payload_list,
        )

        return event
