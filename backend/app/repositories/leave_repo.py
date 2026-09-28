"""Repository for Leave Requests and Attachments."""

from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.pulserecord import LeaveAttachment, LeaveRequest


class LeaveRepository:
    """Data access repository for Leave Requests and Attachments."""

    @staticmethod
    def create(db: Session, leave: LeaveRequest) -> LeaveRequest:
        db.add(leave)
        db.commit()
        db.refresh(leave)
        return leave

    @staticmethod
    def get_by_id(db: Session, leave_id: str) -> Optional[LeaveRequest]:
        return (
            db.query(LeaveRequest)
            .options(
                joinedload(LeaveRequest.student),
                joinedload(LeaveRequest.reviewer),
                joinedload(LeaveRequest.attachments),
            )
            .filter(LeaveRequest.id == leave_id)
            .first()
        )

    @staticmethod
    def list_for_student(
        db: Session,
        student_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[LeaveRequest]:
        query = (
            db.query(LeaveRequest)
            .options(joinedload(LeaveRequest.reviewer), joinedload(LeaveRequest.attachments))
            .filter(LeaveRequest.student_id == student_id)
        )
        if status:
            query = query.filter(LeaveRequest.status == status)
        return query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_for_institution(
        db: Session,
        institution_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LeaveRequest]:
        query = (
            db.query(LeaveRequest)
            .options(
                joinedload(LeaveRequest.student),
                joinedload(LeaveRequest.reviewer),
                joinedload(LeaveRequest.attachments),
            )
            .filter(LeaveRequest.institution_id == institution_id)
        )
        if status:
            query = query.filter(LeaveRequest.status == status)
        return query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_for_assigned_students(
        db: Session,
        student_ids: List[str],
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[LeaveRequest]:
        if not student_ids:
            return []
        query = (
            db.query(LeaveRequest)
            .options(
                joinedload(LeaveRequest.student),
                joinedload(LeaveRequest.reviewer),
                joinedload(LeaveRequest.attachments),
            )
            .filter(LeaveRequest.student_id.in_(student_ids))
        )
        if status:
            query = query.filter(LeaveRequest.status == status)
        return query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_approved_in_range(
        db: Session,
        student_id: str,
        start_date: date,
        end_date: date,
    ) -> List[LeaveRequest]:
        """Query approved leave requests overlapping with [start_date, end_date]."""
        return (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.student_id == student_id,
                LeaveRequest.status == "APPROVED",
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            )
            .order_by(LeaveRequest.start_date.asc())
            .all()
        )

    @staticmethod
    def create_attachment(db: Session, attachment: LeaveAttachment) -> LeaveAttachment:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    @staticmethod
    def get_attachment_by_id(db: Session, attachment_id: str) -> Optional[LeaveAttachment]:
        return db.query(LeaveAttachment).filter(LeaveAttachment.id == attachment_id).first()

    @staticmethod
    def delete_attachment(db: Session, attachment: LeaveAttachment) -> None:
        db.delete(attachment)
        db.commit()
