"""Repository layer for User, Role, and Session data access."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.models.role import Role, UserRole
from app.models.refresh_token import RefreshToken


class UserRepository:
    """Encapsulates database operations for users, roles, and sessions."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch active or inactive user by exact normalized email with roles loaded."""
        return (
            db.query(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .filter(User.email == email.strip().lower())
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        """Fetch user by primary key with roles and permissions loaded."""
        return (
            db.query(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password_hash: str,
        full_name: str,
        phone: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
    ) -> User:
        """Create and persist a new user record."""
        user = User(
            email=email.strip().lower(),
            password_hash=password_hash,
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            is_active=is_active,
            is_verified=is_verified,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        """Lookup role entity by unique name."""
        return db.query(Role).filter(Role.name == name.upper().strip()).first()

    @staticmethod
    def assign_role(db: Session, user_id: str, role_id: str) -> UserRole:
        """Assign a role to a user if not already assigned."""
        existing = (
            db.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
            .first()
        )
        if existing:
            return existing

        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
        return user_role

    @staticmethod
    def set_user_roles(db: Session, user_id: str, role_names: List[str]) -> List[str]:
        """Replace all existing roles of a user with specified role names."""
        # 1. Clear existing user_roles
        db.query(UserRole).filter(UserRole.user_id == user_id).delete(synchronize_session=False)
        db.commit()

        # 2. Assign new roles
        assigned = []
        for rname in role_names:
            role = db.query(Role).filter(Role.name == rname.upper().strip()).first()
            if role:
                ur = UserRole(user_id=user_id, role_id=role.id)
                db.add(ur)
                assigned.append(role.name)
        db.commit()
        return assigned


    @staticmethod
    def update_last_login(db: Session, user_id: str) -> None:
        """Update last_login_at timestamp for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            db.commit()

    @staticmethod
    def create_refresh_token(
        db: Session,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RefreshToken:
        """Persist a newly issued refresh token hash."""
        token_entry = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(token_entry)
        db.commit()
        db.refresh(token_entry)
        return token_entry

    @staticmethod
    def get_refresh_token_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve a refresh token by its SHA-256 hash."""
        return (
            db.query(RefreshToken)
            .options(selectinload(RefreshToken.user).selectinload(User.roles).selectinload(Role.permissions))
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    @staticmethod
    def revoke_refresh_token(db: Session, token_entry: RefreshToken) -> None:
        """Mark a refresh token as revoked."""
        token_entry.revoked_at = datetime.now(timezone.utc)
        db.commit()
