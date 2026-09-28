"""PulseRisk Repository for institutional policies, snapshots, and cohort triage queries.

IMPORTANT: This repository strictly does NOT query attendance_records,
assignment_submissions, or assessment_results for behavioral metrics.
All behavioral metrics are consumed from PulseWatch.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.academic import StudentProfile
from app.models.pulserisk import RiskPolicy, RiskSignalContribution, StudentRiskSnapshot
from app.models.pulsewatch import BehaviorEvent
from app.models.user import User


class PulseRiskRepository:
    """Data access layer for PulseRisk support prioritization subsystem."""

    # -------------------------------------------------------------------------
    # Policy Management
    # -------------------------------------------------------------------------

    @staticmethod
    def get_active_policy(db: Session, institution_id: str) -> RiskPolicy:
        """Fetch the single ACTIVE risk policy for an institution.
        
        If no policy exists yet, provisions and activates the default v1.0 institutional policy.
        """
        policy = (
            db.query(RiskPolicy)
            .filter(
                RiskPolicy.institution_id == institution_id,
                RiskPolicy.status == "ACTIVE",
            )
            .first()
        )
        if not policy:
            now = datetime.now(timezone.utc)
            policy = RiskPolicy(
                id=str(uuid.uuid4()),
                institution_id=institution_id,
                code="STANDARD_ACADEMIC_POLICY",
                name="Standard Institutional Academic Support Policy",
                description="Default deterministic support priority policy configured for standard semester pacing.",
                weight_attendance=Decimal("0.350"),
                weight_coursework=Decimal("0.300"),
                weight_assessment=Decimal("0.250"),
                weight_persistence=Decimal("0.100"),
                threshold_moderate=Decimal("25.00"),
                threshold_elevated=Decimal("50.00"),
                threshold_urgent=Decimal("75.00"),
                persistence_half_life_days=14,
                status="ACTIVE",
                policy_version="v1.0",
                activated_at=now,
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
        return policy

    @staticmethod
    def get_policy_by_id(db: Session, policy_id: str) -> Optional[RiskPolicy]:
        """Fetch risk policy by primary key ID."""
        return db.query(RiskPolicy).filter(RiskPolicy.id == policy_id).first()

    @staticmethod
    def get_policies_for_institution(db: Session, institution_id: str) -> List[RiskPolicy]:
        """List all risk policies (DRAFT, VALIDATED, ACTIVE, RETIRED) for an institution."""
        return (
            db.query(RiskPolicy)
            .filter(RiskPolicy.institution_id == institution_id)
            .order_by(desc(RiskPolicy.created_at))
            .all()
        )

    @staticmethod
    def create_policy(db: Session, policy: RiskPolicy) -> RiskPolicy:
        """Persist a new policy in DRAFT status."""
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def update_policy(db: Session, policy: RiskPolicy) -> RiskPolicy:
        """Update an existing DRAFT policy."""
        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def activate_policy(db: Session, policy_id: str) -> RiskPolicy:
        """Atomically transition target policy to ACTIVE and retire any previously ACTIVE policy."""
        now = datetime.now(timezone.utc)
        target = db.query(RiskPolicy).filter(RiskPolicy.id == policy_id).first()
        if not target:
            raise ValueError("Policy not found")

        # Retire existing active policies for this institution
        active_policies = (
            db.query(RiskPolicy)
            .filter(
                RiskPolicy.institution_id == target.institution_id,
                RiskPolicy.status == "ACTIVE",
                RiskPolicy.id != target.id,
            )
            .all()
        )
        for p in active_policies:
            p.status = "RETIRED"
            p.retired_at = now
        db.flush()

        target.status = "ACTIVE"
        target.activated_at = now
        db.commit()
        db.refresh(target)
        return target

    # -------------------------------------------------------------------------
    # PulseWatch Behavioral Events Ingestion (Zero Raw Academic Table Reads)
    # -------------------------------------------------------------------------

    @staticmethod
    def get_student_historical_behavior_events(
        db: Session,
        student_id: str,
        lookback_days: int = 60,
        reference_date: Optional[date] = None,
    ) -> List[BehaviorEvent]:
        """Retrieve historical detected behavior events from PulseWatch within the lookback window.
        
        Strictly queries behavior_events (Phase 3 PulseWatch output), NOT raw academic tables.
        """
        ref = reference_date or date.today()
        start_date = ref - timedelta(days=lookback_days)

        return (
            db.query(BehaviorEvent)
            .filter(
                BehaviorEvent.student_id == student_id,
                BehaviorEvent.window_end_date >= start_date,
                BehaviorEvent.window_end_date <= ref,
            )
            .order_by(desc(BehaviorEvent.detected_at))
            .all()
        )

    # -------------------------------------------------------------------------
    # Snapshot Persistence & Idempotency
    # -------------------------------------------------------------------------

    @staticmethod
    def get_latest_snapshot(
        db: Session,
        student_id: str,
        window_days: int = 14,
        policy_version: Optional[str] = None,
    ) -> Optional[StudentRiskSnapshot]:
        """Get the most recent snapshot for a student, optionally scoped by policy version."""
        q = (
            db.query(StudentRiskSnapshot)
            .options(joinedload(StudentRiskSnapshot.contributions), joinedload(StudentRiskSnapshot.policy))
            .filter(
                StudentRiskSnapshot.student_id == student_id,
                StudentRiskSnapshot.window_days == window_days,
            )
        )
        if policy_version:
            q = q.filter(StudentRiskSnapshot.policy_version == policy_version)
        return q.order_by(desc(StudentRiskSnapshot.evaluation_date), desc(StudentRiskSnapshot.calculated_at)).first()

    @staticmethod
    def get_snapshots_history(
        db: Session,
        student_id: str,
        limit: int = 10,
    ) -> List[StudentRiskSnapshot]:
        """Get chronological history of snapshots for trajectory analysis."""
        return (
            db.query(StudentRiskSnapshot)
            .options(joinedload(StudentRiskSnapshot.contributions), joinedload(StudentRiskSnapshot.policy))
            .filter(StudentRiskSnapshot.student_id == student_id)
            .order_by(desc(StudentRiskSnapshot.evaluation_date), desc(StudentRiskSnapshot.calculated_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def save_snapshot_and_contributions(
        db: Session,
        student_id: str,
        policy_id: str,
        evaluation_date: date,
        window_days: int,
        support_priority_index: Decimal,
        priority_tier: str,
        confidence_score: Decimal,
        data_quality: str,
        primary_driver: Optional[str],
        summary_text: str,
        algorithm_version: str,
        policy_version: str,
        calculated_at: datetime,
        decomposition_dict: dict,
        contributions_list: list,
        input_snapshot_dict: Optional[dict] = None,
    ) -> StudentRiskSnapshot:
        """Idempotently persist or update an SPI snapshot and its child contributions."""
        snapshot = (
            db.query(StudentRiskSnapshot)
            .filter(
                StudentRiskSnapshot.student_id == student_id,
                StudentRiskSnapshot.evaluation_date == evaluation_date,
                StudentRiskSnapshot.window_days == window_days,
                StudentRiskSnapshot.algorithm_version == algorithm_version,
                StudentRiskSnapshot.policy_version == policy_version,
            )
            .first()
        )

        decomposition_str = json.dumps(decomposition_dict)
        input_snapshot_str = json.dumps(input_snapshot_dict) if input_snapshot_dict else None

        if snapshot:
            snapshot.policy_id = policy_id
            snapshot.support_priority_index = support_priority_index
            snapshot.priority_tier = priority_tier
            snapshot.confidence_score = confidence_score
            snapshot.data_quality = data_quality
            snapshot.primary_driver = primary_driver
            snapshot.summary_text = summary_text
            snapshot.decomposition_json = decomposition_str
            snapshot.input_snapshot_json = input_snapshot_str
            snapshot.calculated_at = calculated_at

            # Replace child contributions
            db.query(RiskSignalContribution).filter(RiskSignalContribution.snapshot_id == snapshot.id).delete()
        else:
            snapshot = StudentRiskSnapshot(
                id=str(uuid.uuid4()),
                student_id=student_id,
                policy_id=policy_id,
                evaluation_date=evaluation_date,
                window_days=window_days,
                support_priority_index=support_priority_index,
                priority_tier=priority_tier,
                confidence_score=confidence_score,
                data_quality=data_quality,
                primary_driver=primary_driver,
                summary_text=summary_text,
                decomposition_json=decomposition_str,
                input_snapshot_json=input_snapshot_str,
                algorithm_version=algorithm_version,
                policy_version=policy_version,
                calculated_at=calculated_at,
            )
            db.add(snapshot)
            db.flush()

        # Add contributions
        for c in contributions_list:
            contrib_row = RiskSignalContribution(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot.id,
                dimension=c["dimension"],
                metric_label=c["metric_label"],
                observed_value=c.get("observed_value"),
                baseline_value=c.get("baseline_value"),
                delta_value=c.get("delta_value"),
                factor_score=c["factor_score"],
                assigned_weight=c["assigned_weight"],
                weighted_contribution=c["weighted_contribution"],
                data_quality=c["data_quality"],
                source_signal=c.get("source_signal"),
                evidence_payload_json=json.dumps(c.get("context_details")) if c.get("context_details") else None,
            )
            db.add(contrib_row)

        db.commit()
        db.refresh(snapshot)
        return snapshot

    # -------------------------------------------------------------------------
    # Advisor Support Priority Triage Roster
    # -------------------------------------------------------------------------

    @staticmethod
    def get_cohort_priorities(
        db: Session,
        student_ids: Optional[List[str]] = None,
        priority_tier: Optional[str] = None,
        primary_driver: Optional[str] = None,
        page: int = 1,
        limit: int = 25,
    ) -> Tuple[List[dict], int]:
        """Query latest snapshot per student for the advisor triage roster."""
        # Subquery to find the most recent snapshot per student
        latest_subq = (
            db.query(
                StudentRiskSnapshot.student_id,
                func.max(StudentRiskSnapshot.calculated_at).label("max_calc"),
            )
            .group_by(StudentRiskSnapshot.student_id)
            .subquery()
        )

        q = (
            db.query(
                StudentRiskSnapshot,
                StudentProfile,
                User,
            )
            .join(latest_subq, (StudentRiskSnapshot.student_id == latest_subq.c.student_id) & (StudentRiskSnapshot.calculated_at == latest_subq.c.max_calc))
            .join(StudentProfile, StudentRiskSnapshot.student_id == StudentProfile.id)
            .join(User, StudentProfile.user_id == User.id)
        )

        if student_ids is not None:
            q = q.filter(StudentRiskSnapshot.student_id.in_(student_ids))
        if priority_tier:
            q = q.filter(StudentRiskSnapshot.priority_tier == priority_tier)
        if primary_driver:
            q = q.filter(StudentRiskSnapshot.primary_driver == primary_driver)

        total = q.count()
        offset = (page - 1) * limit
        rows = (
            q.order_by(desc(StudentRiskSnapshot.support_priority_index), desc(StudentRiskSnapshot.calculated_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for snap, prof, usr in rows:
            results.append({
                "student_id": prof.id,
                "student_name": usr.full_name,
                "roll_number": getattr(prof, "enrollment_number", "N/A"),
                "program_code": prof.program.code if prof.program else None,
                "section_name": prof.section.name if prof.section else None,
                "support_priority_index": snap.support_priority_index,
                "priority_tier": snap.priority_tier,
                "primary_driver": snap.primary_driver,
                "confidence_score": snap.confidence_score,
                "data_quality": snap.data_quality,
                "evaluation_date": snap.evaluation_date,
                "calculated_at": snap.calculated_at,
            })

        return results, total
