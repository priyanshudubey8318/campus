"""Repository for Complaints, Evidence, and Appeals."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.pulserecord import Complaint, ComplaintAppeal, ComplaintEvidence


class ComplaintRepository:
    """Data access repository for Complaints, Evidence, and Appeals."""

    @staticmethod
    def generate_next_code(db: Session, institution_id: str) -> str:
        """Generate next monotonic complaint tracking code per institution."""
        year = datetime.now(timezone.utc).year
        count = (
            db.query(func.count(Complaint.id))
            .filter(
                Complaint.institution_id == institution_id,
                Complaint.complaint_code.like(f"CMP-{year}-%"),
            )
            .scalar()
            or 0
        )
        return f"CMP-{year}-{count + 1:04d}"

    @staticmethod
    def create(db: Session, complaint: Complaint) -> Complaint:
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def get_by_id(db: Session, complaint_id: str) -> Optional[Complaint]:
        return (
            db.query(Complaint)
            .options(
                joinedload(Complaint.complainant),
                joinedload(Complaint.assigned_reviewer),
                joinedload(Complaint.closed_by),
                joinedload(Complaint.evidence),
                joinedload(Complaint.appeals),
            )
            .filter(Complaint.id == complaint_id)
            .first()
        )

    @staticmethod
    def list_for_complainant(
        db: Session,
        complainant_user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Complaint]:
        return (
            db.query(Complaint)
            .options(
                joinedload(Complaint.assigned_reviewer),
                joinedload(Complaint.evidence),
                joinedload(Complaint.appeals),
            )
            .filter(Complaint.complainant_user_id == complainant_user_id)
            .order_by(Complaint.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_for_assigned_reviewer(
        db: Session,
        reviewer_user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Complaint]:
        query = (
            db.query(Complaint)
            .options(
                joinedload(Complaint.complainant),
                joinedload(Complaint.evidence),
                joinedload(Complaint.appeals),
            )
            .filter(Complaint.assigned_reviewer_id == reviewer_user_id)
        )
        if status:
            query = query.filter(Complaint.status == status)
        return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_for_institution(
        db: Session,
        institution_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Complaint]:
        query = (
            db.query(Complaint)
            .options(
                joinedload(Complaint.complainant),
                joinedload(Complaint.assigned_reviewer),
                joinedload(Complaint.closed_by),
                joinedload(Complaint.evidence),
                joinedload(Complaint.appeals),
            )
            .filter(Complaint.institution_id == institution_id)
        )
        if status:
            query = query.filter(Complaint.status == status)
        if category:
            query = query.filter(Complaint.category == category)
        return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def create_evidence(db: Session, evidence: ComplaintEvidence) -> ComplaintEvidence:
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    @staticmethod
    def get_evidence_by_id(db: Session, evidence_id: str) -> Optional[ComplaintEvidence]:
        return db.query(ComplaintEvidence).filter(ComplaintEvidence.id == evidence_id).first()

    @staticmethod
    def get_next_appeal_number(db: Session, complaint_id: str) -> int:
        count = (
            db.query(func.count(ComplaintAppeal.id))
            .filter(ComplaintAppeal.complaint_id == complaint_id)
            .scalar()
            or 0
        )
        return count + 1

    @staticmethod
    def create_appeal(db: Session, appeal: ComplaintAppeal) -> ComplaintAppeal:
        db.add(appeal)
        db.commit()
        db.refresh(appeal)
        return appeal

    @staticmethod
    def get_appeal_by_id(db: Session, appeal_id: str) -> Optional[ComplaintAppeal]:
        return db.query(ComplaintAppeal).filter(ComplaintAppeal.id == appeal_id).first()
