"""Authentication and authorization endpoints for CampusPulse."""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.auth_deps import (
    get_current_user,
    require_active_user,
    require_role,
    require_permission,
)
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    MessageResponse,
    UserRoleUpdateRequest,
)
from app.services.auth_service import AuthService


router = APIRouter()
settings = get_settings()


def get_client_ip(request: Request) -> str:
    """Extract true client IP address taking proxies into account."""
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Register a new user account with Argon2id password hashing and audit logging."""
    client_ip = get_client_ip(request)
    user = AuthService.register(db=db, payload=payload, client_ip=client_ip)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and establish session",
)
def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user, set secure HTTP-only session cookies, and return access token."""
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    user, access_token, refresh_token = AuthService.authenticate(
        db=db,
        payload=payload,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    # Set HTTP-only cookies
    access_cookie_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    response.set_cookie(
        key="campuspulse_access_token",
        value=access_token,
        max_age=access_cookie_max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="campuspulse_refresh_token",
        value=refresh_token,
        max_age=refresh_cookie_max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_cookie_max_age,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate session refresh token",
)
def refresh_session(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Exchange valid refresh token for fresh access token and rotated refresh token."""
    raw_refresh = None
    if payload and payload.refresh_token:
        raw_refresh = payload.refresh_token
    elif "campuspulse_refresh_token" in request.cookies:
        raw_refresh = request.cookies.get("campuspulse_refresh_token")

    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies or request payload",
        )

    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    user, access_token, new_refresh = AuthService.refresh_session(
        db=db,
        raw_refresh_token=raw_refresh,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    access_cookie_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    response.set_cookie(
        key="campuspulse_access_token",
        value=access_token,
        max_age=access_cookie_max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="campuspulse_refresh_token",
        value=new_refresh,
        max_age=refresh_cookie_max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_cookie_max_age,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Terminate session and invalidate tokens",
)
def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Revoke refresh token, clear session cookies, and record security audit log."""
    raw_refresh = None
    if payload and payload.refresh_token:
        raw_refresh = payload.refresh_token
    elif "campuspulse_refresh_token" in request.cookies:
        raw_refresh = request.cookies.get("campuspulse_refresh_token")

    # Attempt to resolve current user for audit logging if token present
    current_user: Optional[User] = None
    try:
        current_user = get_current_user(request=request, bearer_auth=None, db=db)
    except HTTPException:
        pass

    client_ip = get_client_ip(request)
    AuthService.logout(
        db=db,
        raw_refresh_token=raw_refresh,
        current_user=current_user,
        client_ip=client_ip,
    )

    # Clear cookies with matching attributes
    response.delete_cookie(
        "campuspulse_access_token",
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        "campuspulse_refresh_token",
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: User = Depends(require_active_user),
) -> UserResponse:
    """Retrieve profile, roles, and permissions for the currently authenticated active user."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/role-check/admin",
    response_model=MessageResponse,
    summary="RBAC verification endpoint requiring ADMIN or SUPER_ADMIN role",
)
def check_admin_access(
    current_user: User = Depends(require_role("ADMIN")),
) -> MessageResponse:
    """Verify caller has ADMIN or SUPER_ADMIN role."""
    return MessageResponse(message=f"Admin access granted to {current_user.email}")


@router.get(
    "/role-check/student",
    response_model=MessageResponse,
    summary="RBAC verification endpoint requiring STUDENT or SUPER_ADMIN role",
)
def check_student_access(
    current_user: User = Depends(require_role("STUDENT")),
) -> MessageResponse:
    """Verify caller has STUDENT or SUPER_ADMIN role."""
    return MessageResponse(message=f"Student access granted to {current_user.email}")


@router.get(
    "/permission-check/user-manage",
    response_model=MessageResponse,
    summary="Permission verification endpoint requiring users:write permission",
)
def check_user_create_permission(
    current_user: User = Depends(require_permission("users:write")),
) -> MessageResponse:
    """Verify caller has users:write permission."""
    return MessageResponse(message=f"Permission granted to {current_user.email}")


@router.get(
    "/role-check/external-reporter",
    response_model=MessageResponse,
    summary="RBAC verification endpoint requiring EXTERNAL_REPORTER or SUPER_ADMIN role",
)
def check_external_reporter_access(
    current_user: User = Depends(require_role("EXTERNAL_REPORTER")),
) -> MessageResponse:
    """Verify caller has EXTERNAL_REPORTER or SUPER_ADMIN role."""
    return MessageResponse(message=f"External reporter access granted to {current_user.email}")


@router.put(
    "/users/{user_id}/roles",
    response_model=UserResponse,
    summary="Administrative endpoint to update user roles (requires roles:write permission)",
)
def update_roles(
    user_id: str,
    payload: UserRoleUpdateRequest,
    request: Request,
    current_user: User = Depends(require_permission("roles:write")),
    db: Session = Depends(get_db),
) -> User:
    """Update roles for target user. Guarded by roles:write permission."""
    client_ip = get_client_ip(request)
    updated_user = AuthService.update_user_roles(
        db=db,
        target_user_id=user_id,
        new_roles=payload.roles,
        actor=current_user,
        client_ip=client_ip,
    )
    return updated_user


