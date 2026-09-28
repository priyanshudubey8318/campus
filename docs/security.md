# CampusPulse — Security Architecture & Baseline Controls

This document details the security controls, authentication mechanisms, session management, and authorization model for CampusPulse.

---

## 1. Authentication & Password Security (Phase 1)

### 1.1 Password Storage
* **Algorithm**: Argon2id via `argon2-cffi` following RFC 9106 recommended parameters:
  - Memory cost ($m$): 65,536 KiB (64 MiB)
  - Time cost ($t$): 3 iterations
  - Parallelism ($p$): 4 parallel lanes
  - Hash length: 32 bytes
* Verification is strictly constant-time, preventing timing side-channel attacks.
* Plaintext passwords and hashes are never returned in API responses, serialized in Pydantic schemas, or logged.

### 1.2 Password Complexity Policy
All user registrations enforce strict complexity validation:
* Minimum 8 characters, maximum 128 characters
* At least one uppercase Latin letter (`[A-Z]`)
* At least one lowercase Latin letter (`[a-z]`)
* At least one numeric digit (`[0-9]`)
* At least one special or punctuation character (`[\W_]`)

### 1.3 Account Enumeration & Timing Defense
* Failed login attempts return a uniform `401 Unauthorized` status with generic detail `"Invalid email or password"`.
* Timing behavior between existing and non-existing email lookups is normalized using pre-computed dummy Argon2id verification (`dummy_verify_password`), ensuring indistinguishable cryptographic execution time.
* Public self-registration is restricted to self-service roles (`STUDENT`, `EXTERNAL_REPORTER`), rejecting privileged role requests with `400 Bad Request`.

### 1.4 Rate Limiting & Brute-Force Defense
* Authentication endpoints implement an in-memory thread-safe sliding-window rate limiter implementing the `BaseRateLimiter` abstract contract.
* Threshold: 5 failed attempts per 300-second window tracked per IP address and normalized email.
* Excess failed attempts are rejected with `429 Too Many Requests` including a standard `Retry-After` header.
* Successful login immediately resets the failure counter for that IP and email.
* **Architecture Limitation**: The current rate limiter operates in single-process memory. It protects single-node deployments and developer workflows. Horizontally scaled multi-worker deployments behind load balancers must supply a distributed backend (such as Redis) adhering to `BaseRateLimiter`.

---

## 2. Session Management & Token Architecture

### 2.1 Dual Token Architecture
* **Access Tokens**: Short-lived JWT (15 minutes) signed with HMAC-SHA256 (`AUTH_SECRET`). Payload includes `sub` (User UUID), `email`, `roles`, and `permissions`.
* **Refresh Tokens**: Cryptographically secure random 256-bit URL-safe tokens (7 days expiry).
  - Raw tokens are never persisted in the database; only their cryptographic SHA-256 hash is stored in `refresh_tokens`.
  - **Token Rotation**: Every refresh exchanges the active token for a fresh pair and invalidates the previous refresh token (`revoked_at` timestamp).
  - **Token Replay Defense**: Presenting an already-revoked refresh token triggers an immediate `TOKEN_REPLAY_ATTEMPT` security audit alert and returns `401 Unauthorized`.
  - Immediate revocation upon explicit user logout.

### 2.2 Dual Delivery Mechanism & Browser Storage Policy
* **Browser Clients**: Delivered via HTTP-only, SameSite=Lax, Secure cookies (`campuspulse_access_token`, `campuspulse_refresh_token`). Protects against Cross-Site Scripting (XSS) credential theft.
  - The refresh token is **never exposed to browser JavaScript** and is strictly managed via `HttpOnly` cookies.
  - Frontend JavaScript state keeps only short-lived session identity in memory; tokens and credentials are **never written to `localStorage` or `sessionStorage`**.
* **API / Programmatic Clients**: Access tokens and user profiles are returned in JSON response bodies for non-browser clients (e.g. mobile apps, automated services). Handled via `Authorization: Bearer <token>` headers.
* Server-side authorization dependencies inspect the `Authorization` header first, falling back transparently to session cookies.

---

## 3. Centralized Role-Based Access Control (RBAC)

### 3.1 Role & Permission Model
* Identity is strictly decoupled from academic domain profiles (`Role != Person Type`).
* Users hold one or more institutional roles (`User` -> `UserRole` -> `Role`).
* Roles map to granular permissions (`Role` -> `RolePermission` -> `Permission`).

### 3.2 Authorization Claims & Database Resolution Model
CampusPulse utilizes a **hybrid claims and authoritative database resolution model**:
* **Cryptographic Bound**: The access token carries signed identity, roles, and permissions with a strict 15-minute expiration window for stateless inspection.
* **Authoritative Enforcement**: Every server-side authorization check in FastAPI (`get_current_user`, `require_active_user`, `require_role`, `require_permission`) loads the current `User` and their assigned roles from the PostgreSQL database within the request transaction.
* **Revocation Latency**:
  - **Account Deactivation**: Immediate on the very next HTTP request (returns `403 Forbidden`).
  - **Role Revocation**: Immediate on the very next HTTP request (returns `403 Forbidden`).
  - **Session Invalidation**: Immediate on logout / refresh token revocation.

### 3.3 Active Role Matrix

| Role | System Scope | Granular Permissions Assigned |
|---|---|---|
| `SUPER_ADMIN` | Root system administration and audit oversight | All 20 system permissions |
| `ADMIN` | User account administration, role assignment, governance | `users:read`, `users:write`, `roles:read`, `roles:write`, `audit:read`, `profile:read_all`, `academic:read_all`, `pulsewatch:read_all`, `cases:read_all`, `complaints:read_all` |
| `FACULTY` | Course rosters, attendance marking, internal marks | `profile:read_own`, `profile:read_assigned`, `academic:read_own`, `academic:write_assigned`, `pulsewatch:read_assigned` |
| `ADVISOR` | Advising, retention monitoring, intervention cases | `profile:read_own`, `profile:read_assigned`, `academic:read_own`, `pulsewatch:read_assigned`, `cases:read_assigned`, `cases:write_assigned` |
| `COUNSELOR` | Confidential student wellbeing and supportive interventions | `profile:read_own`, `profile:read_assigned`, `cases:read_assigned`, `cases:write_assigned` |
| `STUDENT` | Self-service portal, check-ins, grievance submission | `profile:read_own`, `academic:read_own`, `pulsewatch:read_own`, `complaints:create`, `complaints:read_own` |
| `EXTERNAL_REPORTER` | Formal complaint reporting | `complaints:create`, `complaints:read_own` |

### 3.4 Privilege Escalation Defense
* Self-registration through `POST /api/v1/auth/register` strictly rejects requests for administrative or academic roles (`ADMIN`, `SUPER_ADMIN`, `FACULTY`, `ADVISOR`, `COUNSELOR`).
* Administrative role modification (`PUT /api/v1/auth/users/{id}/roles`) strictly requires the `roles:write` permission held only by `ADMIN` and `SUPER_ADMIN`.
* Normal authenticated users cannot alter their own roles or elevate permissions through any API endpoint.

---

## 4. Security Audit Logging

* Security events are captured in the append-only `audit_logs` table:
  - `ACCOUNT_CREATED`: New user registration with assigned initial role.
  - `LOGIN_SUCCESS`: Authenticated session established.
  - `LOGIN_FAILURE`: Invalid credential attempt (email masked for privacy).
  - `TOKEN_REFRESHED`: Refresh token rotated.
  - `TOKEN_REPLAY_ATTEMPT`: Attempted reuse of an already-revoked refresh token.
  - `LOGOUT`: Session terminated and refresh token revoked.
  - `ROLES_UPDATED`: User roles modified by an authorized administrator.
* Plaintext passwords, password hashes, JWT access tokens, and raw token secrets are strictly omitted from all log entries (verified via automated tests).

---

## 5. Academic Domain Authorization & Data Isolation (Phase 2)

Phase 2 establishes strict relational boundaries and access controls across academic operations:

### 5.1 Identity vs Domain Profile Separation
* `User` models strictly handle authentication principals (email, password hash, active status, system roles).
* `StudentProfile` and `FacultyProfile` hold domain metadata linked 1:1 on `users.id` with `ondelete="RESTRICT"`.
* **Zero Credentials on Profiles**: Passwords, tokens, or security hashes are never stored in profile tables.
* **Transcript & Record Protection**: The `RESTRICT` foreign key rule ensures user records cannot be deleted while active academic transcripts, enrollment histories, or teaching records exist.

### 5.2 Resource Scoping & Authorization Boundaries
* **Student Privacy Isolation**:
  - Students can only view their own student profile, course enrollments, attendance records, coursework submissions, and evaluated results.
  - Cross-student access attempts are caught by `verify_student_record_access` dependency and rejected with `403 Forbidden`.
  - Public/unauthenticated access to academic records is rejected with `401 Unauthorized`.
* **Faculty Course Scoping**:
  - Faculty members are only authorized to record attendance (`POST /academic/attendance`), create assignments, and evaluate assessment results (`POST /academic/assessments/{id}/results`) for courses and sections to which they hold an active `faculty_course_assignments` record.
  - Attempting to modify unassigned courses or sections is rejected by `verify_faculty_course_access` with `403 Forbidden`.
* **Administrative Oversight**:
  - Users with `ADMIN` or `SUPER_ADMIN` roles retain read and configuration capabilities across all institutional departments, programs, courses, and offerings.

### 5.3 Business Logic & Data Integrity Defense
* **No Cross-Table CHECK Constraints**: Relational boundaries requiring cross-table comparison (e.g. `marks_obtained <= assessment.max_marks`) are enforced deterministically in the Python service layer. The database enforces `marks_obtained >= 0`.
* **Attendance Integrity**: Attendance percentage is never stored as a raw mutable float; it is strictly derived on demand from atomic event records (`PRESENT`, `ABSENT`, `LATE`, `EXCUSED`). Non-enrolled students are rejected from attendance recording.
* **Submission Lateness & Attempt Numbering**: Attempt counts are deterministically incremented starting at 1 (`UNIQUE(assignment_id, student_id, attempt_number)`), and lateness is derived on the server by comparing current server UTC timestamp with the assignment's due date.

---

## 6. Infrastructure & Database Safeguards

* **CORS**: `CORSMiddleware` restricted to explicit institutional origins (`ALLOWED_ORIGINS`). Wildcards (`*`) prohibited when credentials are enabled.
* **Test Database Guard**: `validate_test_database_safety()` ensures test suites cannot run against development or production databases.
* **Error Sanitization**: Global exception handler strips internal stack traces and database schemas in production mode (`DEBUG=False`).


