"""Repository for PulseCase support cases, notes, interventions, and follow-ups."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.pulsecase import (
    CaseFollowUp,
    CaseIntervention,
    CaseNote,
    SupportCase,
)


class PulseCaseRepository:
    """Data access repository for PulseCase entities."""

    @staticmethod
    def generate_next_case_number(db: Session, institution_id: str) -> str:
        """Generate next monotonic case tracking number (CASE-YYYY-XXXX)."""
        year = datetime.now(timezone.utc).year
        last_case = (
            db.query(SupportCase.case_number)
            .filter(SupportCase.case_number.like(f"CASE-{year}-%"))
            .order_by(SupportCase.case_number.desc())
            .first()
        )
        if last_case and last_case[0]:
            try:
                last_seq = int(last_case[0].split("-")[-1])
                return f"CASE-{year}-{last_seq + 1:04d}"
            except (ValueError, IndexError):
                pass

        count = (
            db.query(func.count(SupportCase.id))
            .filter(SupportCase.case_number.like(f"CASE-{year}-%"))
            .scalar()
            or 0
        )
        return f"CASE-{year}-{count + 1:04d}"

    @staticmethod
    def create_case(db: Session, case: SupportCase) -> SupportCase:
        db.add(case)
        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def get_case_by_id(db: Session, case_id: str) -> Optional[SupportCase]:
        return (
            db.query(SupportCase)
            .options(
                joinedload(SupportCase.student),
                joinedload(SupportCase.assigned_staff),
                joinedload(SupportCase.referred_by),
                joinedload(SupportCase.closed_by),
                joinedload(SupportCase.notes),
                joinedload(SupportCase.interventions),
                joinedload(SupportCase.follow_ups),
            )
            .filter(SupportCase.id == case_id)
            .first()
        )

    @staticmethod
    def get_case_by_number(db: Session, case_number: str) -> Optional[SupportCase]:
        return db.query(SupportCase).filter(SupportCase.case_number == case_number).first()

    @staticmethod
    def list_cases(
        db: Session,
        institution_id: str,
        student_id: Optional[str] = None,
        assigned_staff_id: Optional[str] = None,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SupportCase]:
        query = (
            db.query(SupportCase)
            .options(
                joinedload(SupportCase.student),
                joinedload(SupportCase.assigned_staff),
                joinedload(SupportCase.referred_by),
            )
            .filter(SupportCase.institution_id == institution_id)
        )

        if student_id:
            query = query.filter(SupportCase.student_id == student_id)
        if assigned_staff_id:
            query = query.filter(SupportCase.assigned_staff_id == assigned_staff_id)
        if status:
            query = query.filter(SupportCase.status == status)
        if case_type:
            query = query.filter(SupportCase.case_type == case_type)
        if priority:
            query = query.filter(SupportCase.priority == priority)

        return query.order_by(SupportCase.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def count_cases(
        db: Session,
        institution_id: str,
        student_id: Optional[str] = None,
        assigned_staff_id: Optional[str] = None,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> int:
        query = db.query(func.count(SupportCase.id)).filter(SupportCase.institution_id == institution_id)

        if student_id:
            query = query.filter(SupportCase.student_id == student_id)
        if assigned_staff_id:
            query = query.filter(SupportCase.assigned_staff_id == assigned_staff_id)
        if status:
            query = query.filter(SupportCase.status == status)
        if case_type:
            query = query.filter(SupportCase.case_type == case_type)
        if priority:
            query = query.filter(SupportCase.priority == priority)

        return query.scalar() or 0

    @staticmethod
    def list_referrals_by_referrer(
        db: Session,
        referred_by_user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SupportCase]:
        return (
            db.query(SupportCase)
            .options(joinedload(SupportCase.student))
            .filter(SupportCase.referred_by_user_id == referred_by_user_id)
            .order_by(SupportCase.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_student_history(db: Session, student_id: str) -> List[SupportCase]:
        """Fetch all historical cases for a student ordered by creation date."""
        return (
            db.query(SupportCase)
            .options(
                joinedload(SupportCase.assigned_staff),
                joinedload(SupportCase.interventions),
                joinedload(SupportCase.follow_ups),
            )
            .filter(SupportCase.student_id == student_id)
            .order_by(SupportCase.created_at.desc())
            .all()
        )

    @staticmethod
    def has_active_intervention(db: Session, student_id: str) -> bool:
        """Read-only check if a student currently has an active intervention case."""
        active_statuses = ("OPEN", "IN_PROGRESS", "WAITING_FOR_STUDENT", "FOLLOW_UP_SCHEDULED")
        count = (
            db.query(func.count(SupportCase.id))
            .filter(
                SupportCase.student_id == student_id,
                SupportCase.status.in_(active_statuses),
            )
            .scalar()
            or 0
        )
        return count > 0

    # Notes
    @staticmethod
    def create_note(db: Session, note: CaseNote) -> CaseNote:
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def get_notes_by_case(db: Session, case_id: str) -> List[CaseNote]:
        return (
            db.query(CaseNote)
            .options(joinedload(CaseNote.author))
            .filter(CaseNote.case_id == case_id)
            .order_by(CaseNote.created_at.asc())
            .all()
        )

    # Interventions
    @staticmethod
    def create_intervention(db: Session, intervention: CaseIntervention) -> CaseIntervention:
        db.add(intervention)
        db.commit()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def get_intervention_by_id(db: Session, intervention_id: str) -> Optional[CaseIntervention]:
        return (
            db.query(CaseIntervention)
            .options(joinedload(CaseIntervention.assigned_to))
            .filter(CaseIntervention.id == intervention_id)
            .first()
        )

    # Follow-Ups
    @staticmethod
    def create_follow_up(db: Session, follow_up: CaseFollowUp) -> CaseFollowUp:
        db.add(follow_up)
        db.commit()
        db.refresh(follow_up)
        return follow_up

    @staticmethod
    def get_follow_up_by_id(db: Session, follow_up_id: str) -> Optional[CaseFollowUp]:
        return (
            db.query(CaseFollowUp)
            .options(joinedload(CaseFollowUp.assigned_staff))
            .filter(CaseFollowUp.id == follow_up_id)
            .first()
        )
