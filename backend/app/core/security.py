"""Cryptographic security utilities for CampusPulse.

Implements:
- Argon2id password hashing and constant-time verification.
- Signed JWT access token creation and decoding.
- Cryptographic refresh token generation with SHA-256 storage hashing.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.core.config import get_settings

settings = get_settings()

# Argon2id hasher configured per RFC 9106 recommended parameters
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

# Pre-computed dummy hash to guarantee constant-time verification when a user does not exist
_DUMMY_PASSWORD_HASH = _hasher.hash("CampusPulseDummyHashForTimingMitigation!123")


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash.
    
    Returns True if valid, False otherwise. Never leaks internal exceptions.
    """
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception:
        return False


def dummy_verify_password(plain_password: str) -> None:
    """Execute dummy Argon2id verification to prevent user enumeration timing channels."""
    try:
        _hasher.verify(_DUMMY_PASSWORD_HASH, plain_password)
    except Exception:
        pass



def create_access_token(
    subject: str,
    email: str,
    roles: List[str],
    permissions: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT access token containing subject, roles, and permissions."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "email": email,
        "roles": roles,
        "permissions": permissions,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT access token.
    
    Raises:
        jwt.ExpiredSignatureError: If token has expired.
        jwt.PyJWTError: If token signature or structure is invalid.
    """
    return jwt.decode(
        token,
        settings.AUTH_SECRET,
        algorithms=["HS256"],
        options={"require": ["exp", "sub", "type"]},
    )


def generate_refresh_token() -> Tuple[str, str]:
    """Generate a high-entropy refresh token and its SHA-256 storage hash.
    
    Returns:
        Tuple of (raw_secret_token, sha256_hash_for_db_storage)
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash


def hash_token(raw_token: str) -> str:
    """Hash a raw token with SHA-256 for secure database lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
