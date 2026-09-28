"""Authentication and identity business logic service."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    hash_password,
    verify_password,
    dummy_verify_password,
    create_access_token,
    generate_refresh_token,
    hash_token,
)
from app.core.rate_limit import login_rate_limiter
from app.models.user import User
from app.models.audit_log import AuditLog
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserRegisterRequest, UserLoginRequest

settings = get_settings()

ALLOWED_REGISTRATION_ROLES = {"STUDENT", "EXTERNAL_REPORTER"}



class AuthService:
    """Orchestrates registration, authentication, session tokens, and security audits."""

    @staticmethod
    def _record_audit(
        db: Session,
        action: str,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Helper to write sanitized security audit events."""
        try:
            entry = AuditLog(
                action=action,
                actor_id=actor_id,
                actor_role=actor_role,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
            )
            db.add(entry)
            db.commit()
        except Exception:
            db.rollback()

    @classmethod
    def register(cls, db: Session, payload: UserRegisterRequest, client_ip: Optional[str] = None) -> User:
        """Register a new user account with secure Argon2id password hashing."""
        existing = UserRepository.get_by_email(db, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered",
            )

        hashed_pw = hash_password(payload.password)
        user = UserRepository.create_user(
            db=db,
            email=payload.email,
            password_hash=hashed_pw,
            full_name=payload.full_name,
            phone=payload.phone,
            is_active=True,
            is_verified=False,
        )

        # Assign initial role - self-service registration restricted to allowed roles
        role_name = (payload.role or "STUDENT").upper().strip()
        if role_name not in ALLOWED_REGISTRATION_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Self-registration for role '{role_name}' is not permitted. Contact an administrator.",
            )
        role = UserRepository.get_role_by_name(db, role_name)
        if not role:
            # Fallback to STUDENT if specified role does not exist
            role = UserRepository.get_role_by_name(db, "STUDENT")
        if role:
            UserRepository.assign_role(db, user.id, role.id)

        # Refresh user to load roles
        user = UserRepository.get_by_id(db, user.id)

        cls._record_audit(
            db=db,
            action="ACCOUNT_CREATED",
            actor_id=user.id,
            actor_role=user.role_names[0] if user.role_names else None,
            entity_type="USER",
            entity_id=user.id,
            details=f"User account created for {user.email}",
            ip_address=client_ip,
        )

        return user

    @classmethod
    def authenticate(
        cls,
        db: Session,
        payload: UserLoginRequest,
        client_ip: str,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Verify user credentials with rate limiting and issue access + refresh tokens.
        
        Returns:
            Tuple of (user: User, access_token: str, raw_refresh_token: str)
        """
        ip_key = f"ip:{client_ip}"
        email_key = f"email:{payload.email}"

        # 1. Rate limit inspection
        ip_limited, ip_retry = login_rate_limiter.check(ip_key)
        email_limited, email_retry = login_rate_limiter.check(email_key)
        if ip_limited or email_limited:
            retry_after = max(ip_retry, email_retry)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        # 2. Credential verification with constant-time non-existent user protection
        user = UserRepository.get_by_email(db, payload.email)
        if not user:
            dummy_verify_password(payload.password)
            login_rate_limiter.record_failure(ip_key)
            login_rate_limiter.record_failure(email_key)

            masked_email = f"{payload.email[:2]}***@{payload.email.split('@')[-1]}" if "@" in payload.email else "***"
            cls._record_audit(
                db=db,
                action="LOGIN_FAILURE",
                entity_type="USER",
                details=f"Failed authentication attempt for {masked_email}",
                ip_address=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(payload.password, user.password_hash):
            login_rate_limiter.record_failure(ip_key)
            login_rate_limiter.record_failure(email_key)

            masked_email = f"{payload.email[:2]}***@{payload.email.split('@')[-1]}" if "@" in payload.email else "***"
            cls._record_audit(
                db=db,
                action="LOGIN_FAILURE",
                entity_type="USER",
                details=f"Failed authentication attempt for {masked_email}",
                ip_address=client_ip,
            )
            # Safe generic error message prevents account enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )


        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive. Please contact an institutional administrator.",
            )

        # 3. Successful authentication: reset rate limiter
        login_rate_limiter.reset(ip_key)
        login_rate_limiter.reset(email_key)

        # 4. Generate tokens
        access_token = create_access_token(
            subject=user.id,
            email=user.email,
            roles=user.role_names,
            permissions=list(user.permission_codes),
        )

        raw_refresh, token_hash = generate_refresh_token()
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        UserRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=refresh_expires,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        UserRepository.update_last_login(db, user.id)

        cls._record_audit(
            db=db,
            action="LOGIN_SUCCESS",
            actor_id=user.id,
            actor_role=user.role_names[0] if user.role_names else None,
            entity_type="USER",
            entity_id=user.id,
            details="User logged in successfully",
            ip_address=client_ip,
        )

        return user, access_token, raw_refresh

    @classmethod
    def refresh_session(
        cls,
        db: Session,
        raw_refresh_token: str,
        client_ip: str,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Rotate refresh token and issue a fresh access token."""
        token_hash = hash_token(raw_refresh_token)
        token_entry = UserRepository.get_refresh_token_by_hash(db, token_hash)

        if token_entry and token_entry.revoked_at is not None:
            # Replay attack detection: token was previously revoked
            cls._record_audit(
                db=db,
                action="TOKEN_REPLAY_ATTEMPT",
                actor_id=token_entry.user_id,
                actor_role=token_entry.user.role_names[0] if token_entry.user and token_entry.user.role_names else None,
                entity_type="REFRESH_TOKEN",
                entity_id=str(token_entry.id),
                details="Attempted reuse of an already-revoked refresh token",
                ip_address=client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session token has been revoked",
            )

        if not token_entry or not token_entry.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session refresh token",
            )

        user = token_entry.user
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found",
            )

        # Revoke old refresh token (Token Rotation)
        UserRepository.revoke_refresh_token(db, token_entry)

        # Issue new pair
        new_access_token = create_access_token(
            subject=user.id,
            email=user.email,
            roles=user.role_names,
            permissions=list(user.permission_codes),
        )

        new_raw_refresh, new_token_hash = generate_refresh_token()
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        UserRepository.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=refresh_expires,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        cls._record_audit(
            db=db,
            action="TOKEN_REFRESHED",
            actor_id=user.id,
            actor_role=user.role_names[0] if user.role_names else None,
            entity_type="USER",
            entity_id=user.id,
            details="Session token refreshed",
            ip_address=client_ip,
        )

        return user, new_access_token, new_raw_refresh

    @classmethod
    def logout(
        cls,
        db: Session,
        raw_refresh_token: Optional[str] = None,
        current_user: Optional[User] = None,
        client_ip: Optional[str] = None,
    ) -> None:
        """Revoke active refresh token and record logout audit event."""
        if raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            token_entry = UserRepository.get_refresh_token_by_hash(db, token_hash)
            if token_entry and token_entry.revoked_at is None:
                UserRepository.revoke_refresh_token(db, token_entry)

        if current_user:
            cls._record_audit(
                db=db,
                action="LOGOUT",
                actor_id=current_user.id,
                actor_role=current_user.role_names[0] if current_user.role_names else None,
                entity_type="USER",
                entity_id=current_user.id,
                details="User logged out",
                ip_address=client_ip,
            )

    @classmethod
    def update_user_roles(
        cls,
        db: Session,
        target_user_id: str,
        new_roles: List[str],
        actor: User,
        client_ip: Optional[str] = None,
    ) -> User:
        """Administratively update roles assigned to a user."""
        target_user = UserRepository.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )

        # Validate that all requested roles exist in database
        for rname in new_roles:
            role = UserRepository.get_role_by_name(db, rname)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown role '{rname}'",
                )

        assigned_roles = UserRepository.set_user_roles(db, target_user_id, new_roles)
        updated_user = UserRepository.get_by_id(db, target_user_id)

        cls._record_audit(
            db=db,
            action="ROLES_UPDATED",
            actor_id=actor.id,
            actor_role=actor.role_names[0] if actor.role_names else None,
            entity_type="USER",
            entity_id=target_user_id,
            details=f"Roles updated to [{', '.join(assigned_roles)}] for {target_user.email}",
            ip_address=client_ip,
        )

        return updated_user

