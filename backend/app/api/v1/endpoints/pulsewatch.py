"""PulseWatch API endpoints.

Provides scoped endpoints for academic engagement summaries, timelines, signal metrics,
baselines, and idempotent evaluation runs.
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.academic_deps import verify_student_record_access
from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.repositories.pulsewatch_repo import PulseWatchRepository
from app.schemas.pulsewatch import (
    BehaviorEventResponse,
    PulseWatchSummaryResponse,
    SignalEvidenceSchema,
    StudentBehaviorBaselineResponse,
)
from app.services.pulsewatch_calculation_service import (
    ALGORITHM_VERSION,
    PulseWatchCalculationService,
)
from app.services.pulsewatch_event_service import PulseWatchEventService

router = APIRouter()


@router.get(
    "/student/{student_id}/summary",
    response_model=PulseWatchSummaryResponse,
    summary="Get live academic engagement summary (Read-Only)",
)
def get_student_pulsewatch_summary(
    student_id: str,
    window_days: int = Query(14, ge=7, le=60, description="Observation window duration in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PulseWatchSummaryResponse:
    """Compute current academic behavioral engagement summary for an authorized student.
    
    Strictly read-only with zero database write side-effects.
    """
    verify_student_record_access(current_user, student_id, db)

    # Verify student exists
    student = AcademicRepository.get_student_profile_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    return PulseWatchCalculationService.compute_student_summary(
        db=db,
        student_id=student_id,
        observation_window_days=window_days,
    )


@router.get(
    "/student/{student_id}/timeline",
    response_model=List[BehaviorEventResponse],
    summary="Get historical behavior events timeline",
)
def get_student_behavior_timeline(
    student_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BehaviorEventResponse]:
    """Retrieve persisted historical behavior events for an authorized student."""
    verify_student_record_access(current_user, student_id, db)

    events = PulseWatchRepository.get_behavior_events(db, student_id=student_id, limit=limit)
    response_list = []
    for ev in events:
        evidence_schemas = [
            SignalEvidenceSchema(
                signal_type=ev_row.signal_type,
                severity=ev_row.severity,
                metric_name=ev_row.metric_name,
                current_value=ev_row.current_value,
                baseline_value=ev_row.baseline_value,
                delta_value=ev_row.delta_value,
                evidence_payload=None,
            )
            for ev_row in ev.evidence_records
        ]
        response_list.append(
            BehaviorEventResponse(
                id=ev.id,
                student_id=ev.student_id,
                event_type=ev.event_type,
                severity=ev.severity,
                observation_window_days=ev.observation_window_days,
                window_start_date=ev.window_start_date,
                window_end_date=ev.window_end_date,
                summary_text=ev.summary_text,
                status=ev.status,
                algorithm_version=ev.algorithm_version,
                detected_at=ev.detected_at,
                evidence=evidence_schemas,
            )
        )
    return response_list


@router.get(
    "/student/{student_id}/signals",
    response_model=List[SignalEvidenceSchema],
    summary="Get detailed engagement signals",
)
def get_student_signals(
    student_id: str,
    window_days: int = Query(14, ge=7, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SignalEvidenceSchema]:
    """Retrieve granular calculated signal evidence for the observation window."""
    verify_student_record_access(current_user, student_id, db)

    summary = PulseWatchCalculationService.compute_student_summary(
        db=db,
        student_id=student_id,
        observation_window_days=window_days,
    )
    return summary.signals


@router.get(
    "/student/{student_id}/baseline",
    response_model=List[StudentBehaviorBaselineResponse],
    summary="Get stored student behavioral baselines",
)
def get_student_baselines(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StudentBehaviorBaselineResponse]:
    """Retrieve persisted personal behavioral baselines for an authorized student."""
    verify_student_record_access(current_user, student_id, db)

    baselines = PulseWatchRepository.get_student_baselines(db, student_id=student_id)
    return [
        StudentBehaviorBaselineResponse(
            metric_type=b.metric_type,
            baseline_value=b.baseline_value,
            observation_count=b.observation_count,
            data_quality=b.data_quality,
            window_days=b.window_days,
            algorithm_version=b.algorithm_version,
            calculated_at=b.calculated_at,
        )
        for b in baselines
    ]


@router.post(
    "/student/{student_id}/evaluate",
    response_model=BehaviorEventResponse,
    summary="Evaluate and idempotently persist behavioral event",
)
def evaluate_and_persist_student(
    student_id: str,
    window_days: int = Query(14, ge=7, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BehaviorEventResponse:
    """Explicitly compute and idempotently persist PulseWatch event and baselines."""
    verify_student_record_access(current_user, student_id, db)

    event = PulseWatchEventService.evaluate_and_persist_student(
        db=db,
        student_id=student_id,
        observation_window_days=window_days,
    )

    evidence_schemas = [
        SignalEvidenceSchema(
            signal_type=ev_row.signal_type,
            severity=ev_row.severity,
            metric_name=ev_row.metric_name,
            current_value=ev_row.current_value,
            baseline_value=ev_row.baseline_value,
            delta_value=ev_row.delta_value,
            evidence_payload=None,
        )
        for ev_row in event.evidence_records
    ]

    return BehaviorEventResponse(
        id=event.id,
        student_id=event.student_id,
        event_type=event.event_type,
        severity=event.severity,
        observation_window_days=event.observation_window_days,
        window_start_date=event.window_start_date,
        window_end_date=event.window_end_date,
        summary_text=event.summary_text,
        status=event.status,
        algorithm_version=event.algorithm_version,
        detected_at=event.detected_at,
        evidence=evidence_schemas,
    )
