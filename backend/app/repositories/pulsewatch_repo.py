"""PulseWatch repository layer.

Provides optimized, bounded date-window queries against attendance records,
assignment submissions, and assessment evaluations, as well as idempotent persistence
for behavioral baselines and auditable events.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.academic import (
    AcademicTerm,
    Assessment,
    AssessmentResult,
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
    Enrollment,
    StudentProfile,
)
from app.models.pulsewatch import (
    BehaviorEvent,
    BehaviorSignalEvidence,
    StudentBehaviorBaseline,
)


class PulseWatchRepository:
    """Data access methods for PulseWatch behavioral features and persistence."""

    # -------------------------------------------------------------------------
    # Academic Data Access (Date-Bounded Window Queries)
    # -------------------------------------------------------------------------

    @staticmethod
    def get_attendance_in_window(
        db: Session,
        student_id: str,
        start_date: date,
        end_date: date,
    ) -> List[AttendanceRecord]:
        """Fetch attendance records for a student strictly bounded within [start_date, end_date]."""
        return (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.session_date >= start_date,
                AttendanceRecord.session_date <= end_date,
            )
            .order_by(AttendanceRecord.session_date.asc())
            .all()
        )

    @staticmethod
    def get_eligible_assignments_in_window(
        db: Session,
        student_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Assignment]:
        """Fetch assignments eligible for a student whose due_date falls within [start_date, end_date].
        
        Rules:
        - Student has an active enrollment in the course offering.
        - Section matches student enrollment section or is course-wide (section_id IS NULL).
        - release_date <= end_date.
        - due_date >= start_date AND due_date <= end_date.
        """
        enrollments = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status.in_(["ENROLLED", "AUDITING"]),
            )
            .all()
        )
        if not enrollments:
            return []

        enrolled_course_ids = [e.course_id for e in enrollments]
        enrolled_section_ids = [e.section_id for e in enrollments if e.section_id is not None]

        query = (
            db.query(Assignment)
            .filter(
                Assignment.course_id.in_(enrolled_course_ids),
                Assignment.release_date <= end_date,
                Assignment.due_date >= start_date,
                Assignment.due_date <= end_date,
            )
        )

        if enrolled_section_ids:
            query = query.filter(
                (Assignment.section_id.is_(None)) | (Assignment.section_id.in_(enrolled_section_ids))
            )
        else:
            query = query.filter(Assignment.section_id.is_(None))

        return query.order_by(Assignment.due_date.asc()).all()

    @staticmethod
    def get_submissions_for_assignment_and_student(
        db: Session,
        assignment_id: str,
        student_id: str,
    ) -> List[AssignmentSubmission]:
        """Fetch all eligible submissions for an assignment and student, ordered by earliest submitted_at."""
        return (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
                AssignmentSubmission.status.in_(["SUBMITTED", "LATE", "EVALUATED", "RESUBMITTED"]),
            )
            .order_by(AssignmentSubmission.submitted_at.asc())
            .all()
        )

    @staticmethod
    def get_assessments_and_results_in_window(
        db: Session,
        student_id: str,
        start_date: date,
        end_date: date,
    ) -> List[Tuple[Assessment, Optional[AssessmentResult]]]:
        """Fetch formal assessments due within [start_date, end_date] and student's outcome if any."""
        enrollments = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status.in_(["ENROLLED", "AUDITING"]),
            )
            .all()
        )
        if not enrollments:
            return []

        enrolled_course_ids = [e.course_id for e in enrollments]
        assessments = (
            db.query(Assessment)
            .filter(
                Assessment.course_id.in_(enrolled_course_ids),
                Assessment.assessment_date >= start_date,
                Assessment.assessment_date <= end_date,
            )
            .order_by(Assessment.assessment_date.asc())
            .all()
        )

        results = (
            db.query(AssessmentResult)
            .filter(
                AssessmentResult.student_id == student_id,
                AssessmentResult.assessment_id.in_([a.id for a in assessments]) if assessments else False,
            )
            .all()
        )
        result_map = {r.assessment_id: r for r in results}

        return [(a, result_map.get(a.id)) for a in assessments]

    # -------------------------------------------------------------------------
    # Cohort Context Queries
    # -------------------------------------------------------------------------

    @staticmethod
    def get_cohort_attendance_rate(
        db: Session,
        student_id: str,
        start_date: date,
        end_date: date,
    ) -> Optional[Decimal]:
        """Derive secondary cohort (section or batch) average attendance rate over the window."""
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            return None

        peer_query = db.query(StudentProfile.id)
        if student.section_id:
            peer_query = peer_query.filter(StudentProfile.section_id == student.section_id)
        elif student.batch_id:
            peer_query = peer_query.filter(StudentProfile.batch_id == student.batch_id)
        elif student.program_id:
            peer_query = peer_query.filter(StudentProfile.program_id == student.program_id)
        else:
            return None

        peer_ids = [row[0] for row in peer_query.all()]
        if not peer_ids:
            return None

        records = (
            db.query(AttendanceRecord.status)
            .filter(
                AttendanceRecord.student_id.in_(peer_ids),
                AttendanceRecord.session_date >= start_date,
                AttendanceRecord.session_date <= end_date,
            )
            .all()
        )
        if not records:
            return None

        present_or_late = sum(1 for (st,) in records if st in ["PRESENT", "LATE"])
        return Decimal(str(round((present_or_late / len(records)) * 100.0, 2)))

    @staticmethod
    def get_cohort_assessment_average(
        db: Session,
        student_id: str,
        start_date: date,
        end_date: date,
    ) -> Optional[Decimal]:
        """Derive secondary cohort average assessment percentage over the window."""
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            return None

        peer_query = db.query(StudentProfile.id)
        if student.section_id:
            peer_query = peer_query.filter(StudentProfile.section_id == student.section_id)
        elif student.batch_id:
            peer_query = peer_query.filter(StudentProfile.batch_id == student.batch_id)
        else:
            return None

        peer_ids = [row[0] for row in peer_query.all()]
        if not peer_ids:
            return None

        results = (
            db.query(AssessmentResult.marks_obtained, Assessment.max_marks)
            .join(Assessment, Assessment.id == AssessmentResult.assessment_id)
            .filter(
                AssessmentResult.student_id.in_(peer_ids),
                AssessmentResult.is_absent == False,
                AssessmentResult.marks_obtained.is_not(None),
                Assessment.assessment_date >= start_date,
                Assessment.assessment_date <= end_date,
            )
            .all()
        )
        if not results:
            return None

        percentages = [float(marks) / float(max_m) * 100.0 for marks, max_m in results if max_m > 0]
        if not percentages:
            return None

        return Decimal(str(round(sum(percentages) / len(percentages), 2)))

    # -------------------------------------------------------------------------
    # Baseline Persistence & Idempotency
    # -------------------------------------------------------------------------

    @staticmethod
    def get_student_baselines(
        db: Session,
        student_id: str,
        algorithm_version: str = "pulsewatch-v1.0",
    ) -> List[StudentBehaviorBaseline]:
        return (
            db.query(StudentBehaviorBaseline)
            .filter(
                StudentBehaviorBaseline.student_id == student_id,
                StudentBehaviorBaseline.algorithm_version == algorithm_version,
            )
            .all()
        )

    @staticmethod
    def upsert_student_baseline(
        db: Session,
        student_id: str,
        metric_type: str,
        window_days: int,
        algorithm_version: str,
        baseline_value: Optional[Decimal],
        observation_count: int,
        data_quality: str,
        calculated_at: datetime,
    ) -> StudentBehaviorBaseline:
        """Idempotently create or update a student behavior baseline record."""
        existing = (
            db.query(StudentBehaviorBaseline)
            .filter(
                StudentBehaviorBaseline.student_id == student_id,
                StudentBehaviorBaseline.metric_type == metric_type,
                StudentBehaviorBaseline.window_days == window_days,
                StudentBehaviorBaseline.algorithm_version == algorithm_version,
            )
            .first()
        )
        if existing:
            existing.baseline_value = baseline_value
            existing.observation_count = observation_count
            existing.data_quality = data_quality
            existing.calculated_at = calculated_at
            db.commit()
            db.refresh(existing)
            return existing

        baseline = StudentBehaviorBaseline(
            id=str(uuid.uuid4()),
            student_id=student_id,
            metric_type=metric_type,
            baseline_value=baseline_value,
            observation_count=observation_count,
            data_quality=data_quality,
            window_days=window_days,
            algorithm_version=algorithm_version,
            calculated_at=calculated_at,
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        return baseline

    # -------------------------------------------------------------------------
    # Behavior Event Persistence & Idempotency
    # -------------------------------------------------------------------------

    @staticmethod
    def get_behavior_events(
        db: Session,
        student_id: str,
        limit: int = 50,
    ) -> List[BehaviorEvent]:
        return (
            db.query(BehaviorEvent)
            .options(joinedload(BehaviorEvent.evidence_records))
            .filter(BehaviorEvent.student_id == student_id)
            .order_by(BehaviorEvent.detected_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_behavior_event_by_window(
        db: Session,
        student_id: str,
        observation_window_days: int,
        window_start_date: date,
        window_end_date: date,
        algorithm_version: str = "pulsewatch-v1.0",
    ) -> Optional[BehaviorEvent]:
        return (
            db.query(BehaviorEvent)
            .options(joinedload(BehaviorEvent.evidence_records))
            .filter(
                BehaviorEvent.student_id == student_id,
                BehaviorEvent.observation_window_days == observation_window_days,
                BehaviorEvent.window_start_date == window_start_date,
                BehaviorEvent.window_end_date == window_end_date,
                BehaviorEvent.algorithm_version == algorithm_version,
            )
            .first()
        )

    @staticmethod
    def upsert_behavior_event(
        db: Session,
        student_id: str,
        event_type: str,
        severity: str,
        observation_window_days: int,
        window_start_date: date,
        window_end_date: date,
        summary_text: str,
        algorithm_version: str,
        detected_at: datetime,
        evidence_list: List[Dict[str, Any]],
    ) -> BehaviorEvent:
        """Idempotently insert or update a behavior event matching the unique constraint."""
        event = PulseWatchRepository.get_behavior_event_by_window(
            db,
            student_id=student_id,
            observation_window_days=observation_window_days,
            window_start_date=window_start_date,
            window_end_date=window_end_date,
            algorithm_version=algorithm_version,
        )

        if event:
            event.event_type = event_type
            event.severity = severity
            event.summary_text = summary_text
            event.detected_at = detected_at

            # Replace child evidence records
            db.query(BehaviorSignalEvidence).filter(BehaviorSignalEvidence.event_id == event.id).delete()
            for ev in evidence_list:
                evidence_row = BehaviorSignalEvidence(
                    id=str(uuid.uuid4()),
                    event_id=event.id,
                    signal_type=ev["signal_type"],
                    severity=ev["severity"],
                    metric_name=ev["metric_name"],
                    current_value=ev.get("current_value"),
                    baseline_value=ev.get("baseline_value"),
                    delta_value=ev.get("delta_value"),
                    evidence_payload=json.dumps(ev.get("evidence_payload")) if ev.get("evidence_payload") else None,
                    created_at=detected_at,
                )
                db.add(evidence_row)

            db.commit()
            db.refresh(event)
            return event

        event = BehaviorEvent(
            id=str(uuid.uuid4()),
            student_id=student_id,
            event_type=event_type,
            severity=severity,
            observation_window_days=observation_window_days,
            window_start_date=window_start_date,
            window_end_date=window_end_date,
            summary_text=summary_text,
            status="DETECTED",
            algorithm_version=algorithm_version,
            detected_at=detected_at,
        )
        db.add(event)
        db.flush()

        for ev in evidence_list:
            evidence_row = BehaviorSignalEvidence(
                id=str(uuid.uuid4()),
                event_id=event.id,
                signal_type=ev["signal_type"],
                severity=ev["severity"],
                metric_name=ev["metric_name"],
                current_value=ev.get("current_value"),
                baseline_value=ev.get("baseline_value"),
                delta_value=ev.get("delta_value"),
                evidence_payload=json.dumps(ev.get("evidence_payload")) if ev.get("evidence_payload") else None,
                created_at=detected_at,
            )
            db.add(evidence_row)

        db.commit()
        db.refresh(event)
        return event
