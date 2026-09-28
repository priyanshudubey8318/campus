"""RiskPolicyService managing the governed lifecycle of institutional risk policies.

Lifecycle: DRAFT -> VALIDATED -> ACTIVE -> RETIRED.
Enforces weight integrity, monotonicity, immutability of ACTIVE/RETIRED policies,
and atomic single-active uniqueness per institution scope.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pulserisk import RiskPolicy
from app.models.user import User
from app.repositories.pulserisk_repo import PulseRiskRepository
from app.schemas.pulserisk import RiskPolicyCreate, RiskPolicyUpdate


class RiskPolicyService:
    """Business logic and lifecycle management for institutional risk policies."""

    @staticmethod
    def validate_policy_parameters(
        weight_att: Decimal,
        weight_asg: Decimal,
        weight_assess: Decimal,
        weight_persist: Decimal,
        thresh_mod: Decimal,
        thresh_elev: Decimal,
        thresh_urg: Decimal,
        half_life_days: int,
    ) -> None:
        """Validate mathematical and policy constraints."""
        total_weight = weight_att + weight_asg + weight_assess + weight_persist
        if total_weight != Decimal("1.000"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Policy weights must sum exactly to 1.000 (currently {total_weight})",
            )

        if not (Decimal("0.0") < thresh_mod < thresh_elev < thresh_urg < Decimal("100.0")):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Thresholds must be strictly monotonic in range (0, 100): "
                    f"moderate ({thresh_mod}) < elevated ({thresh_elev}) < urgent ({thresh_urg})"
                ),
            )

        if not (1 <= half_life_days <= 90):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Persistence half-life must be between 1 and 90 days (currently {half_life_days})",
            )

    @staticmethod
    def create_policy(db: Session, data: RiskPolicyCreate, current_user: User) -> RiskPolicy:
        """Create a new risk policy in DRAFT status."""
        role_names = set(current_user.role_names)
        if not ("SUPER_ADMIN" in role_names or "ADMIN" in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators may configure institutional risk policies",
            )

        # Check for unique code + version in institution
        existing = (
            db.query(RiskPolicy)
            .filter(
                RiskPolicy.institution_id == data.institution_id,
                RiskPolicy.code == data.code,
                RiskPolicy.policy_version == data.policy_version,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Policy with code '{data.code}' and version '{data.policy_version}' already exists",
            )

        policy = RiskPolicy(
            id=str(uuid.uuid4()),
            institution_id=data.institution_id,
            code=data.code,
            name=data.name,
            description=data.description,
            weight_attendance=data.weight_attendance,
            weight_coursework=data.weight_coursework,
            weight_assessment=data.weight_assessment,
            weight_persistence=data.weight_persistence,
            threshold_moderate=data.threshold_moderate,
            threshold_elevated=data.threshold_elevated,
            threshold_urgent=data.threshold_urgent,
            persistence_half_life_days=data.persistence_half_life_days,
            status="DRAFT",
            policy_version=data.policy_version,
        )
        return PulseRiskRepository.create_policy(db, policy)

    @staticmethod
    def update_draft_policy(
        db: Session,
        policy_id: str,
        data: RiskPolicyUpdate,
        current_user: User,
    ) -> RiskPolicy:
        """Update an existing DRAFT policy. ACTIVE and RETIRED policies are immutable."""
        role_names = set(current_user.role_names)
        if not ("SUPER_ADMIN" in role_names or "ADMIN" in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators may update risk policies",
            )

        policy = PulseRiskRepository.get_policy_by_id(db, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk policy not found")

        if policy.status in ["ACTIVE", "RETIRED"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot edit policy in '{policy.status}' state. Active and retired policies are immutable.",
            )

        if data.name is not None:
            policy.name = data.name
        if data.description is not None:
            policy.description = data.description
        if data.weight_attendance is not None:
            policy.weight_attendance = data.weight_attendance
        if data.weight_coursework is not None:
            policy.weight_coursework = data.weight_coursework
        if data.weight_assessment is not None:
            policy.weight_assessment = data.weight_assessment
        if data.weight_persistence is not None:
            policy.weight_persistence = data.weight_persistence
        if data.threshold_moderate is not None:
            policy.threshold_moderate = data.threshold_moderate
        if data.threshold_elevated is not None:
            policy.threshold_elevated = data.threshold_elevated
        if data.threshold_urgent is not None:
            policy.threshold_urgent = data.threshold_urgent
        if data.persistence_half_life_days is not None:
            policy.persistence_half_life_days = data.persistence_half_life_days

        return PulseRiskRepository.update_policy(db, policy)

    @staticmethod
    def validate_policy(db: Session, policy_id: str, current_user: User) -> RiskPolicy:
        """Advance DRAFT policy to VALIDATED status after verifying parameter integrity."""
        role_names = set(current_user.role_names)
        if not ("SUPER_ADMIN" in role_names or "ADMIN" in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators may validate risk policies",
            )

        policy = PulseRiskRepository.get_policy_by_id(db, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk policy not found")

        if policy.status in ["ACTIVE", "RETIRED"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Policy is already in '{policy.status}' status",
            )

        RiskPolicyService.validate_policy_parameters(
            weight_att=policy.weight_attendance,
            weight_asg=policy.weight_coursework,
            weight_assess=policy.weight_assessment,
            weight_persist=policy.weight_persistence,
            thresh_mod=policy.threshold_moderate,
            thresh_elev=policy.threshold_elevated,
            thresh_urg=policy.threshold_urgent,
            half_life_days=policy.persistence_half_life_days,
        )

        policy.status = "VALIDATED"
        return PulseRiskRepository.update_policy(db, policy)

    @staticmethod
    def activate_policy(db: Session, policy_id: str, current_user: User) -> RiskPolicy:
        """Activate a VALIDATED (or DRAFT that passes validation) policy. Atomically retires previous ACTIVE policy."""
        role_names = set(current_user.role_names)
        if not ("SUPER_ADMIN" in role_names or "ADMIN" in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators may activate risk policies",
            )

        policy = PulseRiskRepository.get_policy_by_id(db, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk policy not found")

        if policy.status == "RETIRED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot activate a retired policy. Create a new policy version instead.",
            )

        # Ensure parameters are valid before activating
        RiskPolicyService.validate_policy_parameters(
            weight_att=policy.weight_attendance,
            weight_asg=policy.weight_coursework,
            weight_assess=policy.weight_assessment,
            weight_persist=policy.weight_persistence,
            thresh_mod=policy.threshold_moderate,
            thresh_elev=policy.threshold_elevated,
            thresh_urg=policy.threshold_urgent,
            half_life_days=policy.persistence_half_life_days,
        )

        return PulseRiskRepository.activate_policy(db, policy_id)
