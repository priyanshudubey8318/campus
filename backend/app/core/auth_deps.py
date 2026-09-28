"""Centralized FastAPI authentication and authorization dependencies.

Provides token extraction from Bearer headers and HTTP-only cookies,
user resolution, active account validation, and role/permission enforcement.
"""

from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    bearer_auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT access token from Bearer header or HTTP-only cookie.
    
    Bearer header is checked first (useful for programmatic API clients and automated tests),
    falling back to `campuspulse_access_token` cookie (standard browser sessions).
    """
    token: Optional[str] = None

    if bearer_auth and bearer_auth.credentials:
        token = bearer_auth.credentials
    elif "authorization" in request.headers:
        raw_auth = request.headers.get("authorization", "")
        if raw_auth.lower().startswith("bearer "):
            token = raw_auth[7:].strip()
    elif "campuspulse_access_token" in request.cookies:
        token = request.cookies.get("campuspulse_access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token was not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Validate that the authenticated user's account is currently active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Contact an administrator.",
        )
    return current_user


def require_role(*allowed_roles: str) -> Callable[..., User]:
    """Dependency factory enforcing that the authenticated user possesses at least one of the specified roles.
    
    SUPER_ADMIN always satisfies role requirements.
    """
    def _role_guard(current_user: User = Depends(require_active_user)) -> User:
        user_roles = set(current_user.role_names)
        if "SUPER_ADMIN" in user_roles:
            return current_user

        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: [{', '.join(allowed_roles)}]",
            )
        return current_user

    return _role_guard


def require_permission(*required_permissions: str) -> Callable[..., User]:
    """Dependency factory enforcing that the authenticated user possesses all specified permissions.
    
    SUPER_ADMIN always satisfies permission requirements.
    """
    def _permission_guard(current_user: User = Depends(require_active_user)) -> User:
        user_roles = set(current_user.role_names)
        if "SUPER_ADMIN" in user_roles:
            return current_user

        user_perms = current_user.permission_codes
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires permissions: [{', '.join(missing)}]",
            )
        return current_user

    return _permission_guard


def check_resource_ownership(user: User, resource_owner_id: str) -> bool:
    """Verify resource ownership. Allows owner, SUPER_ADMIN, or ADMIN; raises HTTP 403 otherwise."""
    user_roles = set(user.role_names)
    if "SUPER_ADMIN" in user_roles or "ADMIN" in user_roles:
        return True
    if str(user.id) == str(resource_owner_id):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this resource",
    )
