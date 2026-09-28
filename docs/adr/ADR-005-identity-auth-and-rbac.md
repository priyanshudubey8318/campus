# ADR-005: Decoupled Identity, Token-Based Authentication, and Centralized RBAC

## Status
Accepted

## Date
2026-09-18

## Context
CampusPulse serves multiple institutional personas (Students, Faculty, Academic Advisors, Counselors, Administrators, Super Administrators, External Reporters). In conventional academic systems, the person type is often directly conflated with user credentials or modeled as single inheritance tables, leading to brittle database schemas, difficult role transitions, and lack of fine-grained access control. Furthermore, secure credential storage, prevention of account enumeration, session management across browsers and API clients, and security event auditing are mandatory architectural requirements.

## Decision
1. **Decoupled User Identity**:
   - `User` represents the core authentication principal (`email`, `password_hash`, `is_active`, `is_verified`).
   - Domain profiles (`StudentProfile`, `FacultyProfile`, etc.) are decoupled and reference `user_id` as foreign keys in future phases.
   - Roles are many-to-many (`User` -> `UserRole` -> `Role`), supporting multi-role institutional users.
2. **Cryptographic Password Hashing**:
   - Argon2id (`argon2-cffi`) using RFC 9106 recommended parameters (memory cost: 65,536 KiB, time cost: 3 iterations, parallelism: 4 lanes).
   - Strict password complexity: minimum 8 characters, uppercase, lowercase, digit, and special character.
   - Timing-attack safe verification.
3. **Session Management & Dual Token Delivery**:
   - Short-lived JWT Access Tokens (15 minutes expiry) signed with `HS256` secret containing `sub`, `email`, `roles`, and `permissions`.
   - Long-lived cryptographically random Refresh Tokens (7 days expiry). Raw tokens are never stored in plaintext in the database; only SHA-256 hashes are persisted in `refresh_tokens`.
   - Token Rotation: Every refresh revokes the prior refresh token and issues a new pair.
   - Dual delivery: Delivered via HTTP-only, SameSite=lax, Secure cookies for browser security against XSS, while also accepting `Authorization: Bearer <token>` for programmatic API clients and automated tests.
4. **Centralized RBAC Dependencies**:
   - Granular permissions mapped to roles (`Role` -> `RolePermission` -> `Permission`).
   - Declarative FastAPI dependencies: `get_current_user`, `require_active_user`, `require_role(*roles)`, `require_permission(*permissions)`.
   - `SUPER_ADMIN` acts as root system authority with bypass capability.
5. **Security Audit Trails & Privacy**:
   - Key authentication events (`ACCOUNT_CREATED`, `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `TOKEN_REFRESHED`, `LOGOUT`) are written to `audit_logs`.
   - Passwords and token secrets are strictly omitted from log details, database columns, and Pydantic response schemas.
   - Failed authentication returns generic 401 messages to prevent account enumeration.
   - Sliding-window in-memory rate limiting throttles excessive login failures.

## Alternatives Considered
- **Conflating Role with Person Type (`users.type = 'STUDENT'`)**: Prevents faculty members from acting as advisors or taking courses, requiring multiple accounts. Decoupled many-to-many RBAC prevents this limitation.
- **Stateless-Only Refresh Tokens (JWT Refresh Tokens)**: Cannot be revoked immediately upon logout or credential compromise. Database-backed refresh tokens with hash storage enable instant revocation and rotation detection.
- **OAuth2 / Social Sign-In Only**: Institutional environments require direct directory or credential management; third-party SSO can be layered on top of this internal identity foundation in future phases.

## Consequences
- Clean separation of identity concerns from academic domain models.
- Robust protection against credential stuffing, brute-force attacks, and session hijacking.
- Extensible authorization layer easily applied to all future phase endpoints.
