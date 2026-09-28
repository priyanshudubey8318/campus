# CampusPulse — Changelog & Migration History

All meaningful architectural enhancements, database migrations, and contract updates must be recorded in this document.

---

## [Phase 0 Foundation] — 2026-09-17

### Implemented
- **Repository Setup**: Initialized Git repository, standard `.gitignore`, `.env.example`, `docker-compose.yml`, and root `README.md`.
- **Master Specification**: Relocated master specification to canonical location `docs/CAMPUSPULSE_MASTER_SPEC.md`.
- **Backend Architecture (`backend/`)**:
  - FastAPI application factory in `backend/app/main.py` with lifespan hooks, CORS middleware, and global exception handling.
  - Pydantic v2 configuration management in `backend/app/core/config.py` with `TEST_DATABASE_URL` and database safety guards.
  - SQLAlchemy 2.0 database engine in `backend/app/core/database.py` with request-scoped session dependency `get_db()`.
  - Authoritative dependency declaration in `backend/pyproject.toml` with synchronized `backend/requirements.txt`.
  - Versioned API router under `/api/v1/` with endpoints `GET /`, `GET /api/v1/health`, and `GET /api/v1/health/db`.
- **Database Migrations (`backend/alembic/`)**:
  - Configured Alembic migration engine with path-resilient script location.
  - Created initial migration `0001_initial_foundation.py` creating the `audit_logs` table.
- **Frontend Architecture (`frontend/`)**:
  - Next.js (App Router) with TypeScript and Tailwind CSS.
  - Responsive application shell with `AppHeader`, `AppSidebar`, `AppFooter`, and UI primitives.
  - Typed API client in `frontend/src/lib/api/client.ts` connecting to live `/api/v1/health`.
  - Error boundaries (`error.tsx`), loading state (`loading.tsx`), and 404 recovery (`not-found.tsx`).
  - Playwright browser smoke test suite in `frontend/tests/smoke.spec.ts`.
- **CI Pipeline**:
  - Created `.github/workflows/ci.yml` running backend migration/pytest with a real PostgreSQL 16 service container and frontend typecheck, lint, and build.
- **Documentation**:
  - `docs/architecture.md`, `docs/api-contracts.md`, `docs/database.md`, `docs/security.md`, `docs/agent-contracts.md`, `docs/changelog.md`, and Architecture Decision Records under `docs/adr/`.

### Verified
- Backend automated tests: 9 passed, 1 skipped (isolated PostgreSQL integration test cleanly skips when local PostgreSQL daemon is absent).
- Configuration safety guards: Rejects identical test/development URLs and test URLs without "test".
- Alembic migration lifecycle: Bidirectional upgrade/downgrade/upgrade verified against real PostgreSQL 16 and SQLite.
- Frontend: TypeScript typecheck passed (0 errors), ESLint passed (0 errors), Next.js production build passed.
- Live API health endpoints: Verified returning HTTP 200 with dynamic uptime and database status.

### Planned (NOT Implemented in Phase 0)
- Phase 1: Identity, RBAC, JWT authentication, and student profiles.
- Phase 2: Academic data models (attendance, marks, assignments, LMS logs).
- Phase 3: PulseWatch proactive behavioral monitoring subsystem.
- Phase 4: PulseRisk multi-signal support priority scoring.
- Phase 5: PulseAssist policy document RAG chatbot.
- Phase 6: PulseRecord leave and complaint review workflows.
- Phase 7: PulseCase advisor intervention case management.
- Phase 8: Advanced institutional analytics, fairness auditing, and integrations.

---

## [Phase 1 Identity, Authentication, Authorization & RBAC] — 2026-09-18

### Implemented
- **Cryptography & Security Core (`backend/app/core/security.py`)**:
  - Argon2id password hashing (`argon2-cffi`, RFC 9106) with timing-attack mitigation and complexity validation (min 8 chars, uppercase, lowercase, digit, special character).
  - Dual token architecture: 15-minute JWT access tokens signed with HMAC-SHA256 and 7-day cryptographically random refresh tokens (secrets.token_urlsafe).
  - Refresh tokens stored strictly as SHA-256 hashes (`backend/app/models/refresh_token.py`) with rotation, revocation, and device context tracking.
  - In-memory sliding-window rate limiting (`backend/app/core/rate_limit.py`) applied to authentication endpoints (`/auth/login`, `/auth/register`).
  - Strict HTTP-only, SameSite cookies with matching flags on deletion to ensure reliable browser cookie purging.
- **Database Models & Schema Migration (`backend/alembic/versions/0002_identity_and_access.py`)**:
  - `users`: User identity decoupled from domain profiles; email index, active/verified state, failed login counter, lockout timestamp.
  - `roles`: Approved Phase 1 system roles (`SUPER_ADMIN`, `ADMIN`, `FACULTY`, `ADVISOR`, `COUNSELOR`, `STUDENT`, `EXTERNAL_REPORTER`).
  - `permissions`: Granular capability tokens (`auth:read`, `profile:manage`, `audit:read`, etc.).
  - `user_roles` & `role_permissions`: Association tables enforcing many-to-many relationships.
  - `refresh_tokens`: Secure hashed refresh token store with cascade deletion on user removal.
  - Idempotent database seeder (`backend/app/core/seed.py`) populating 7 roles, 20 permissions, and 52 permission bindings.
- **Access Control & API Layer (`backend/app/core/auth_deps.py`, `backend/app/api/v1/endpoints/auth.py`)**:
  - Centralized FastAPI dependencies: `get_current_user`, `require_active_user`, `require_role`, `require_permission`.
  - Auth endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `GET /auth/verify-student`, `GET /auth/verify-faculty`, `GET /auth/verify-advisor`, `GET /auth/verify-counselor`, `GET /auth/verify-admin`, `GET /auth/verify-super-admin`.
  - Structured immutable audit logging for all authentication attempts (LOGIN_SUCCESS, LOGIN_FAILED, REGISTER, LOGOUT, TOKEN_REFRESH).
- **Frontend Authentication & State (`frontend/src/`)**:
  - Context & hooks (`AuthProvider`, `useAuth`) managing session bootstrapping via `/auth/me`, reactive user state, role checking (`hasRole`), and permission checking (`hasPermission`).
  - Typed API client (`frontend/src/lib/api/client.ts`) supporting credentials inclusion and Bearer token fallback.
  - Route protection (`ProtectedRoute.tsx`) supporting unauthenticated redirects (`/login?returnUrl=...`) and accessible 403 Forbidden state with role-badge diagnostic.
  - Semantic forms with live password complexity feedback: `LoginForm.tsx`, `RegisterForm.tsx`.
  - Role portal placeholders: `/student`, `/faculty`, `/advisor`, `/counselor`, `/admin`, `/super-admin`.
  - Application shell navigation updated with authenticated user badge, dynamic role indicator, sign out action, and portal navigation links.
- **Documentation & Decisions**:
  - `docs/adr/ADR-005-identity-auth-and-rbac.md` documenting Argon2id, dual-token strategy, and RBAC design.
  - Updated `docs/security.md`, `docs/database.md`, and `docs/api-contracts.md`.

### Verified
- **Backend Test Suite (`pytest backend/tests`)**: 26 passed, 0 failed, 0 skipped against isolated PostgreSQL 16 test database.
  - 10 Phase 0 baseline regression tests pass (config, health, database, audit log CRUD).
  - 9 authentication tests pass (Argon2id hashing, registration, login, JWT issuance, refresh rotation, logout, audit trails).
  - 7 RBAC tests pass (role & permission guards, active user check, token tampering rejection, unauthorized denial).
- **Database Migration Lifecycle**: Bidirectional Alembic migration (`0002_identity_and_access`) verified (`downgrade base` -> `upgrade head`) against live PostgreSQL.
- **Frontend Code Quality**:
  - `npm run typecheck`: 0 errors.
  - `npm run lint`: 0 errors, 0 warnings.
  - `npm run build`: 12/12 routes statically compiled without errors.
- **End-to-End Playwright Tests (`npx playwright test`)**: 8 passed, 0 failed in 20.1s against headless Chromium:
  - Phase 0 smoke test verified.
  - Auth: Unauthenticated redirect from protected route (`/student` -> `/login?returnUrl=%2Fstudent`).
  - Auth: Invalid credentials rejection with user-facing error message.
  - Auth: Registration, automatic session establishment, and portal entry.
  - Auth: 403 Forbidden enforcement (student attempting to access `/admin` receives access denied UI).
  - Auth: Logout revokes session cookies, clears local state, and blocks protected portal access.

---

## [Phase 2 Academic Domain, Profiles & Academic Data Foundation] — 2026-09-18

### Implemented
- **Relational Domain Models & Migration (`backend/alembic/versions/0003_academic_foundation.py`)**:
  - Implemented 16 relational models across 5 domain areas in `backend/app/models/academic.py`:
    - Institutional Hierarchy: `Institution`, `Department`, `Program`, `Batch`, `Section`, `AcademicTerm`.
    - Domain Profiles: `StudentProfile` and `FacultyProfile` linked 1:1 on `users.id` with `ondelete="RESTRICT"` and zero credentials.
    - Offerings & Teaching: `Course` and `FacultyCourseAssignment` with PostgreSQL partial unique indexes (`WHERE section_id IS NULL` and `WHERE section_id IS NOT NULL`).
    - Registration & Tracking: `Enrollment` (composite unique per student, course, term) and `AttendanceRecord` (atomic session events with composite uniqueness).
    - Coursework & Assessments: `Assignment` (release/due/cutoff date ordering checks), `AssignmentSubmission` (composite unique attempt numbering, server-derived lateness), `Assessment`, and `AssessmentResult` (`marks_obtained >= 0` DB CHECK + deterministic `marks_obtained <= max_marks` service validation).
- **Deterministic Data Seeder (`backend/app/core/seed_academic.py`)**:
  - Idempotent seed utility populating Apex Institute of Technology, CSE & IT departments, B.Tech & MCA programs, 2024-2028 batch, Sections A & B, Fall 2026 term, 4 accredited courses (`CS101`, `CS201`, `CS301`, `IT202`), student and faculty users with profiles, teaching assignments, active enrollments, attendance history, assignments, submissions, and evaluated assessment marks.
- **Repository & Service Layer (`backend/app/repositories/academic_repo.py`, `backend/app/services/academic_service.py`)**:
  - Encapsulated CRUD, query scoping, transaction management, attempt calculation, on-demand attendance percentage derivation, and validation logic.
- **API & Authorization Layer (`backend/app/api/v1/endpoints/academic.py`, `backend/app/core/academic_deps.py`)**:
  - 17 RESTful endpoints under `/api/v1/academic/` with Pydantic v2 schemas (`backend/app/schemas/academic.py`).
  - Scoped dependency guards: `verify_student_record_access` (enforcing privacy and cross-student isolation) and `verify_faculty_course_access` (ensuring faculty only modify assigned courses/sections).
- **Frontend Academic Experience (`frontend/src/`)**:
  - Strongly-typed models (`frontend/src/types/academic.ts`) and API client methods (`frontend/src/lib/api/client.ts`).
  - Student Academic Profile (`/student/profile`) displaying registrar enrollment details, cohort, and status.
  - Student Academics Dashboard (`/student/academics`) with derived overall attendance percentage, enrolled courses list, and assessment results.
  - Faculty Academic Profile (`/faculty/profile`) displaying employee ID, department appointment, and rank.
  - Faculty Teaching Courses (`/faculty/courses`) with assigned courses grid, roles, and section scopes.
  - Admin Academic Management (`/admin/academic`) with institutional catalog search and enrollment records.
  - Sidebar navigation updated with Phase 2 Academic Domain portal links.

### Verified
- **Backend Test Suite (`pytest backend/tests -v`)**: 46 passed, 0 failed, 0 skipped in 11.4s against isolated PostgreSQL test database:
  - 9 academic data tests in `backend/tests/test_academic.py` (marks validation, course code uniqueness, scoped composite uniqueness, submission attempts and lateness, student profile hierarchy consistency, faculty partial indexes, date checks, attendance integrity and derived summary, RESTRICT delete integrity).
  - 5 academic security tests in `backend/tests/test_academic_security.py` (401 unauthenticated, cross-student profile 403, student coursework creation 403, unassigned faculty 403, admin access 200).
  - 32 Phase 0 & Phase 1 regression tests all green.
- **Database Migration Lifecycle**: Bidirectional Alembic migration (`0003_academic_foundation.py`) verified (`downgrade 0002` -> `upgrade head`) cleanly against live PostgreSQL.
- **Frontend Quality Assurance**:
  - `npm run typecheck`: 0 errors.
  - `npm run lint`: 0 errors, 0 warnings.
  - `npm run build`: 17/17 routes statically prerendered without errors.
- **Playwright End-to-End Suite (`npx playwright test`)**: 16 passed, 0 failed in 29.7s:
  - 7 Phase 2 Academic tests pass (student profile, academics dashboard with attendance, faculty profile, faculty teaching courses, admin catalog, cross-role 403 protection).
  - 6 Phase 1 Auth & RBAC tests pass.
  - 3 Phase 0 Smoke tests pass.

### Planned (NOT Implemented in Phase 2)
- Phase 3: PulseWatch proactive behavioral monitoring subsystem.
- Phase 4: PulseRisk multi-signal support priority scoring.
- Phase 5: PulseAssist policy document RAG chatbot.
- Phase 6: PulseRecord leave and complaint review workflows.
- Phase 7: PulseCase advisor intervention case management.
- Phase 8: Advanced institutional analytics, fairness auditing, and integrations.

---

## [Phase 2 Final Fixes Closure] — 2026-09-18

### Implemented
- **Strict Attendance Enum Validation (`backend/app/schemas/academic.py`)**:
  - Replaced permissive string types in `AttendanceRecordCreate` with strict `Literal["PRESENT", "ABSENT", "LATE", "EXCUSED"]` and `Literal["MANUAL", "IMPORT", "LMS", "BIOMETRIC", "API"]`.
  - Rejects invalid values deterministically with HTTP 422 Unprocessable Entity.
- **Enrollment Domain Invariants (`backend/app/services/academic_service.py`)**:
  - Enforced active course check (`course.is_active == True`); rejects inactive courses with HTTP 422 (`"Cannot enroll in an inactive course"`).
  - Enforced institutional consistency (`course.institution_id == term.institution_id`); rejects cross-institutional mismatch with HTTP 422 (`"Course and academic term must belong to the same institution"`).
- **Model / Migration Constraint Harmonization (`backend/app/models/academic.py`)**:
  - Declared explicit named `UniqueConstraint` objects in `__table_args__` for `StudentProfile` (`uq_student_profiles_enrollment_number`, `uq_student_profiles_user_id`) and `FacultyProfile` (`uq_faculty_profiles_employee_id`, `uq_faculty_profiles_user_id`).
  - Completely eliminated false-positive schema drift warnings in `alembic check` ("No new upgrade operations detected").
- **Composite Time-Series Indexes & Migration 0004 (`backend/alembic/versions/0004_academic_time_series_indexes.py`)**:
  - Added composite index `ix_attendance_records_student_id_session_date` on `attendance_records(student_id, session_date)` for rolling-window attendance and consecutive absence queries.
  - Added composite index `ix_assignment_submissions_student_id_submitted_at` on `assignment_submissions(student_id, submitted_at)` for assignment submission velocity and timeliness analysis.
  - Created migration `0004_academic_time_series_indexes` with bidirectional `upgrade()` and `downgrade()` verified.
- **Automated Tests (`backend/tests/test_academic.py`)**:
  - Added `test_strict_attendance_enum_validation` verifying all 4 valid statuses accepted and invalid status/source rejected with validation errors.
  - Added `test_enrollment_course_state_and_cross_institution_guards` verifying active course enrollment accepted, inactive course rejected (422), and mismatched institution rejected (422).

### Verified
- **Backend Test Suite (`pytest backend/tests -v`)**: 48 passed, 0 failed, 0 skipped in 12.5s against isolated PostgreSQL test database (`campuspulse_test`).
- **Alembic Check & Migrations**:
  - `alembic check` verified on both `campuspulse_test` and `campuspulse_dev`: `No new upgrade operations detected` (0 drift).
  - Migration cycle verified: `upgrade head` -> `downgrade 0003_academic_foundation` -> `upgrade head` (both composite indexes cleanly drop and restore).
- **Frontend QA**:
  - `npm run typecheck`: 0 errors.
  - `npm run lint`: 0 errors, 0 warnings.
  - `npm run build`: 17/17 routes compiled successfully.
- **Playwright E2E Suite (`npx playwright test`)**: 16 passed, 0 failed in 26.2s.

### Phase Boundary Confirmation
- PulseWatch: NOT IMPLEMENTED
- PulseRisk: NOT IMPLEMENTED
- LMS ingestion: NOT IMPLEMENTED
- Notifications: NOT IMPLEMENTED
- RAG: NOT IMPLEMENTED
- AI agents: NOT IMPLEMENTED
- Complaints: NOT IMPLEMENTED
- Leave: NOT IMPLEMENTED
- Case management: NOT IMPLEMENTED

---

## [Phase 3 PulseWatch — Deterministic Behavioral Monitoring Foundation] — 2026-09-22

### Implemented
- **Database Models & Schema (`backend/app/models/pulsewatch.py`, `backend/alembic/versions/0005_pulsewatch_behavioral_monitoring.py`)**:
  - `student_behavior_baselines`: Rolling personal baselines for attendance, submission rate, and assessment average with composite unique constraint `uq_student_baselines_metric_window_algo` on `(student_id, metric_type, window_days, algorithm_version)` and performance index `ix_student_baselines_student_metric`.
  - `behavior_events`: Persisted academic engagement shift events with composite unique constraint for idempotency `uq_behavior_events_student_window_algo` on `(student_id, observation_window_days, window_start_date, window_end_date, algorithm_version)` and time-series index `ix_behavior_events_student_detected`.
  - `behavior_signal_evidence`: Granular quantitative metric breakdown supporting each event with foreign key cascade deletion and index `ix_signal_evidence_event_signal`.
- **Pure Deterministic Calculation Engine (`backend/app/services/pulsewatch_calculation_service.py`)**:
  - Zero database writes during summary computation (`GET /summary` is strictly read-only).
  - Strict Baseline Leakage Prevention: Personal baseline window $[T-M-N, T-N)$ strictly ends before the observation window $[T-N, T]$ ($T_{\text{baseline\_end}} < T_{\text{observation\_start}}$).
  - Exact Threshold Boundaries:
    - $\Delta \ge -5.0\% \rightarrow \text{NORMAL}$
    - $-15.0\% \le \Delta < -5.0\% \rightarrow \text{MILD\_CHANGE}$
    - $-25.0\% \le \Delta < -15.0\% \rightarrow \text{MODERATE\_CHANGE}$
    - $\Delta < -25.0\% \rightarrow \text{SIGNIFICANT\_CHANGE}$
  - Earliest Valid Submission Attempt: Computes assignment lateness using $\min(\text{submitted\_at}) \le \text{due\_date}$ across eligible submissions (`SUBMITTED`, `LATE`, `EVALUATED`, `RESUBMITTED`).
  - Zero Denominator Guard: When eligible assignment count is zero, returns `NO_DATA` / `null`, never `0.0%`.
  - Data Sufficiency Rules: If observations $< 3$, labels `INSUFFICIENT_DATA` and assigns `NORMAL` stability.
  - Multi-Signal Combination & Escalation: Two moderate signals escalate to `SIGNIFICANT_CHANGE`; consecutive absences ($\ge 3$) escalate to `SIGNIFICANT_CHANGE` (regardless of percentage delta); formal assessment absences (`is_absent == True`) escalate to `SIGNIFICANT_CHANGE`.
- **Idempotent Persistence Service (`backend/app/services/pulsewatch_event_service.py`, `backend/app/repositories/pulsewatch_repo.py`)**:
  - Bounded date-window queries preventing full-table scans.
  - Idempotent upsert logic ensuring repeated evaluation runs update records without creating duplicate events or baselines.
- **API & Access Control Layer (`backend/app/api/v1/endpoints/pulsewatch.py`)**:
  - `GET /api/v1/pulsewatch/student/{id}/summary`
  - `GET /api/v1/pulsewatch/student/{id}/timeline`
  - `GET /api/v1/pulsewatch/student/{id}/signals`
  - `GET /api/v1/pulsewatch/student/{id}/baseline`
  - `POST /api/v1/pulsewatch/student/{id}/evaluate`
  - Scoped RBAC enforcement via `verify_student_record_access`: Students strictly restricted to their own record (cross-student access blocked with HTTP 403); faculty restricted to assigned students; admin institutional oversight.
- **Frontend Academic Pulse Experience (`frontend/`)**:
  - `AcademicPulseCard.tsx`: Displays engagement status badge, summary text, 3 metric pills (Attendance, Coursework Pacing, Evaluation Marks), and triggers the explainability drawer.
  - `PulseExplainModal.tsx`: Transparent "Why am I seeing this?" dialog breaking down what changed, baseline comparison, observation window, data sufficiency, and institutional non-punitive notice.
  - `PulseTimelineView.tsx`: Full Academic Pulse view with historical behavior events, evidence breakdown, secondary cohort context card, and academic environmental context card.
  - Integrated into `/student` (Student Dashboard) and `/student/academics` (Academic Records Tab 5).
  - Typed client methods added in `frontend/src/lib/api/client.ts`.
- **Automated Tests**:
  - Backend: 17 PulseWatch tests in `backend/tests/test_pulsewatch.py` covering leakage prevention, exact boundaries, earliest-attempt lateness, zero denominator, idempotency, versioning, escalation overrides (consecutive absences $\ge 3 \rightarrow$ SIGNIFICANT_CHANGE and formal assessment absence $\rightarrow$ SIGNIFICANT_CHANGE), and 403 authorization scoping.
  - Frontend E2E: Playwright tests in `frontend/tests/pulsewatch.spec.ts` covering dashboard Academic Pulse card, metric pills, explainability modal, tab switching, cohort context, and cross-student 403 security enforcement.

### Verified
- **Backend Test Suite**: 64 passed, 0 failed in 40.85s (`pytest backend/tests -v`).
- **Alembic Drift Check**: `alembic check` returned `No new upgrade operations detected` (0 drift).
- **Frontend QA**:
  - TypeScript: `npm run typecheck` returned 0 errors.
  - ESLint: `npm run lint` returned 0 warnings, 0 errors.
  - Next.js Build: `npm run build` compiled 18/18 routes statically without errors.
  - Playwright E2E: 12/12 tests passed in 13.7s across all suites.

### Strict Phase Boundaries Preserved
- Prohibited and NOT IMPLEMENTED:
  - No PulseRisk scoring models
  - No dropout prediction or mental-health inference
  - No LLM / AI decision-making
  - No LMS ingestion (deferred)
  - No complaints, leave, or case management
  - No counselor intervention workflows

---

## [Phase 4 PulseRisk — Deterministic Support Prioritization Subsystem] — 2026-09-22

### Implemented
- **Database Models & Schema Migration (`backend/alembic/versions/0006_pulserisk_support_prioritization.py`)**:
  - `risk_policies`: Institutional prioritization policy configuration with versioning, dimension weights, safety trigger thresholds, and lifecycle states (`DRAFT`, `VALIDATED`, `ACTIVE`, `RETIRED`). Enforced at most one active policy per institution scope via PostgreSQL partial unique index `uq_risk_policies_active_scope`.
  - `student_risk_snapshots`: Historical and evaluated SPI prioritization snapshots with composite uniqueness `uq_student_risk_snapshots_student_window_algo_policy` on `(student_id, evaluation_date, window_days, algorithm_version, policy_version)`, time-series index `ix_risk_snapshots_student_eval`, and full auditable `decomposition_json`.
  - `risk_signal_contributions`: Granular dimension contribution rows (`snapshot_id`, `dimension`, `metric_label`, `observed_value`, `baseline_value`, `delta_value`, `factor_score`, `assigned_weight`, `weighted_contribution`, `data_quality`, `source_signal`, `evidence_payload_json`) with cascade deletion on snapshot removal.
  - Idempotent default policy seeder (`backend/app/core/seed_pulserisk.py` and `RiskPolicyService.ensure_active_policy`).
- **Pure Deterministic Calculation Engine (`backend/app/services/pulserisk_calculation_service.py`)**:
  - **Zero Metric Duplication**: Never queries raw attendance or assignment tables; consumes strictly structured outputs from PulseWatch (`PulseWatchSummaryResponse`, `BehaviorEvent`).
  - **Dynamic Weight Renormalization**: Evaluates 4 core dimensions: Attendance ($w_1 = 0.35$), Coursework ($w_2 = 0.30$), Assessments ($w_3 = 0.25$), and Longitudinal Persistence ($w_4 = 0.10$). Valid dimensions $\mathcal{V}$ are dynamically renormalized: $w'_i = \frac{w_i}{\sum_{j \in \mathcal{V}} w_j}$.
  - **Data Confidence & Insufficient Data Guard**: Aggregate confidence $\mathcal{C} = \sum_{j \in \mathcal{V}} w_j$. When $\mathcal{C} < 0.35$ and no safety trigger applies, yields `INSUFFICIENT_DATA`, $\text{SPI} = 0.0$, `LOW_PRIORITY`.
  - **Safety Floor Precedence Over Low Confidence**: Critical safety triggers ($T_1$: Formal assessment absence floor = 75.0 $\rightarrow$ `URGENT_PRIORITY`; $T_2$: Consecutive absences $\ge 5$ floor = 75.0 $\rightarrow$ `URGENT_PRIORITY`; $T_3$: Consecutive absences $\ge 3$ floor = 50.0 $\rightarrow$ `ELEVATED_PRIORITY`; $T_4$: Missed assignments $\ge 3$ floor = 50.0 $\rightarrow$ `ELEVATED_PRIORITY`; $T_5$: Dual significant PulseWatch shifts floor = 80.0 $\rightarrow$ `URGENT_PRIORITY`) unconditionally override low confidence ($\mathcal{C} < 0.35$) and prevent critical acute needs from being masked as insufficient data. Note: an attendance percentage delta by itself does not activate T2 without the approved trigger.
  - **Temporal Deduplication & Half-Life Decay**: Event clustering on $\ge 50\%$ date overlap; canonical events weighted with exponential decay $\lambda = \frac{\ln(2)}{14} \approx 0.04951\text{ day}^{-1}$.
  - **Non-Punitive Priority Tiers**: `LOW_PRIORITY` ($[0, 30)$), `MODERATE_PRIORITY` ($[30, 50)$), `ELEVATED_PRIORITY` ($[50, 75)$), `URGENT_PRIORITY` ($[75, 100]$).
  - **Complete Explainability Decomposition**: Full decomposition detailing every dimension's observed delta, factor score, weight, contribution, safety floors, and primary driver.
- **Repository & Policy Management (`backend/app/repositories/pulserisk_repo.py`, `backend/app/services/risk_policy_service.py`)**:
  - Policy lifecycle state transitions: `DRAFT` $\rightarrow$ `VALIDATED` $\rightarrow$ `ACTIVE` $\rightarrow$ `RETIRED`.
  - Cohort support priority triage queries with sorting by SPI descending and calculated_at descending.
  - Idempotent snapshot evaluation and upsert with full contribution mapping.
- **API & Authorization Layer (`backend/app/api/v1/endpoints/pulserisk.py`)**:
  - `GET /api/v1/pulserisk/student/{id}/current`: Compute current student priority decomposition (strictly read-only, zero DB side effects).
  - `GET /api/v1/pulserisk/student/{id}/history`: Retrieve historical SPI trajectory.
  - `POST /api/v1/pulserisk/student/{id}/evaluate`: Evaluate and idempotently persist snapshot (Advisors, Admins, Faculty).
  - `GET /api/v1/pulserisk/cohort/priorities`: Paginated advisor triage roster (403 for Students; scoped for Faculty).
  - `GET /api/v1/pulserisk/policies/active`: Retrieve active institutional policy.
  - `POST /api/v1/pulserisk/policies`: Create draft policy (Admins only).
  - `POST /api/v1/pulserisk/policies/{id}/activate`: Governed policy activation retiring existing active policy (Admins only).
- **Frontend Academic Support Experience (`frontend/`)**:
  - `SupportPriorityCard.tsx`: Displays student support status, SPI score, non-punitive tier badge, and "Why am I seeing this?" modal trigger. Integrated in `/student` dashboard.
  - `PulseRiskExplainModal.tsx`: Transparent explainability dialog breaking down SPI score, confidence score, primary driver, safety triggers, dimension factor scores, weights, and weighted contributions table.
  - `Advisor Triage Roster (`/advisor`)`: Complete advisor workstation with KPI summary metrics (Urgent, Elevated, Moderate, Standard), active policy banner, tier & primary driver filters, search input, paginated roster table, and instant student decomposition modal inspection.
  - Typed client methods added in `frontend/src/lib/api/client.ts` and models in `frontend/src/types/pulserisk.ts`.
- **Automated Tests**:
  - Backend: 21 PulseRisk tests in `backend/tests/test_pulserisk.py` covering all 7 mandatory design scenarios (including Test 3 safety floor precedence over $\mathcal{C} = 0.00$ and Test 4 $\mathcal{C} < 0.35$ insufficient data), approved T2 rule and delta isolation, Scenario 5 exact deterministic assessment calculation, exact boundary tests, temporal deduplication & half-life decay, policy lifecycle transitions, partial index active policy uniqueness, zero-write GET verification, evaluation idempotency, and RBAC security enforcement.
  - Frontend E2E: Playwright test suite in `frontend/tests/pulserisk.spec.ts` covering student Support Priority card and explainability modal, student 403 access restriction to advisor portal, advisor triage roster KPIs, filters, search, and decomposition modal, and admin institutional scope.

### Verified
- **Backend Test Suite**: 86 passed, 0 failed, 0 skipped in 47.98s (`pytest backend/tests -v`).
- **Alembic Drift Check**: `alembic check` returned `No new upgrade operations detected` (0 drift).
- **Frontend QA**:
  - TypeScript: `npm run typecheck` returned 0 errors.
  - ESLint: `npm run lint` returned 0 warnings, 0 errors.
  - Next.js Build: `npm run build` compiled 18/18 routes statically without errors.
  - Playwright E2E: 30/30 tests passed in 29.4s across all test suites.

### Strict Phase Boundaries Preserved
- Prohibited and NOT IMPLEMENTED:
  - No Leave management or complaints (Phase 6)
  - No Case management or intervention notes (Phase 7)
  - No LLM-generated risk scores or dropout predictions
  - No automated student warning notifications or punitive flags

---

## [Phase 5 PulseAssist — Institutional Knowledge & RAG Subsystem] — 2026-09-23

### Implemented
- **Database Models & Schema Migration (`backend/alembic/versions/0007_pulseassist_rag_knowledge.py`)**:
  - `knowledge_documents`: Authoritative policy documents with status (`DRAFT`, `PUBLISHED`, `ARCHIVED`), composite tenant key `(institution_id, document_code)`, and version tracking.
  - `document_chunks`: Semantic chunks (~1800 character target with section header preservation) with `embedding vector(768)` and full-text `tsv_content tsvector`.
  - `document_version_schedules`: Decoupled timeline scheduling with `effective_from`, `effective_to`, `effective_range daterange`, and `is_active boolean`.
  - `pulseassist_conversations`: Student and institutional chat threads with tenant isolation.
  - `pulseassist_messages`: Individual dialogue turns with role (`user`, `assistant`, `system`) and latency telemetry.
  - `pulseassist_citations`: Grounded citation links binding assistant responses to exact source chunks.
  - **Database Triggers & Invariants**:
    - `trg_protect_document_immutability`: Prohibits UPDATE of document content or core metadata once status is `PUBLISHED` or `ARCHIVED`.
    - `trg_protect_knowledge_document_delete`: Raises exception on direct DELETE of `PUBLISHED` or `ARCHIVED` documents.
    - `trg_server_control_document_timestamps`: Automatically stamps `published_at = CURRENT_TIMESTAMP` and `archived_at = CURRENT_TIMESTAMP` at the database level.
    - `trg_validate_schedule_document_published`: Requires referenced document to be `PUBLISHED` when adding or updating active schedule records.
    - `trg_protect_document_version_schedule_delete`: Rejects direct DELETE on active version schedules.
    - `ex_document_version_schedules_non_overlapping`: PostgreSQL GIST exclusion constraint enforcing non-overlapping active date ranges:
      `EXCLUDE USING gist (institution_id WITH =, document_code WITH =, effective_range WITH &&) WHERE (is_active = TRUE)`.
- **AI Provider & Vector Store (`backend/app/services/ai/`)**:
  - `protocols.py`: Clean interfaces `LLMProviderProtocol` and `VectorStoreProtocol`.
  - `mock_provider.py`: Deterministic mock provider supporting grounding tests, keyword extraction, and predictable responses.
  - `gemini_provider.py`: Google Gemini API provider integration (`google-genai` / `@google/genai`) with structured prompt framing and citation extraction.
  - `vector_store.py`: `PostgresPgVectorStore` executing hybrid semantic cosine distance and full-text BM25-style sparse search.
- **Hybrid Retrieval & RRF Engine (`backend/app/services/retrieval_service.py`)**:
  - Dense top 10 candidates ($d=768$) + Sparse top 10 candidates (`tsvector`).
  - Relevance Gate: Dense cosine similarity $\ge 0.65$, Sparse score $> 0.0$.
  - Canonical RRF Fusion:
    $$RRF(c) = \left(\frac{0.7}{60 + \text{dense\_rank}(c)} \text{ if dense else } 0.0\right) + \left(\frac{0.3}{60 + \text{sparse\_rank}(c)} \text{ if sparse else } 0.0\right)$$
  - Selects top 3 to 5 chunks for LLM context.
- **Citation Verification & Numerical Grounding (`backend/app/services/grounding_service.py`)**:
  - Validates all generated citation tags against retrieved chunk IDs. Ungrounded citations stripped.
  - Injects verified student academic metrics (Attendance %, CGPA, Support Priority Tier) directly from database with mandatory ground truth label:
    `"Verified ground-truth data from registrar/attendance systems. Not an AI estimate."`
- **Orchestration & API Layer (`backend/app/services/chat_service.py`, `backend/app/api/v1/endpoints/pulseassist.py`)**:
  - Endpoints: `POST /api/v1/pulseassist/query`, `GET /api/v1/pulseassist/conversations`, `GET /api/v1/pulseassist/conversations/{id}`, `GET /api/v1/pulseassist/documents`, `POST /api/v1/pulseassist/documents`, `POST /api/v1/pulseassist/documents/{id}/publish`, `POST /api/v1/pulseassist/documents/{id}/archive`.
  - Strict tenant scoping with super-admin override capability.
- **Frontend Experience (`frontend/`)**:
  - `PulseAssistDrawer.tsx`: Floating action trigger and slide-out chat interface for students with suggested policy questions, message history, rate limit countdown timer, and compliance disclaimers.
  - `CitationPill.tsx`: Interactive citation pill with chunk hover preview and click-to-explain trigger.
  - `GroundTruthCard.tsx`: Dedicated verified metrics card with attendance, CGPA, support tier, and mandatory registrar label.
  - `WhySeeingModal.tsx`: Transparent explainability dialog displaying exact source chunk, effective date range, document metadata, and hybrid RAG architecture breakdown.
  - `AdminKnowledgePage (`/admin/knowledge`)`: Institutional document repository for uploading, publishing, scheduling, and archiving policy documents.
- **Automated Tests**:
  - Backend: 43 PulseAssist test scenarios in `backend/tests/test_pulseassist.py` covering hybrid retrieval, RRF ranking, relevance gates, citation verification, ground-truth metrics, prompt injection guards, document lifecycle, database delete triggers, server-controlled timestamps, and exclusion constraints.
  - Regression Suite: Full 129 tests passed across Phase 0 through Phase 5 (`pytest backend/tests -v`).

### Verified
- **Backend Test Suite**: 129 passed, 0 failed in 56.37s.
- **Alembic Drift Check**: 0 schema drift (`alembic check` clean).
- **Bidirectional Migration**: Upgrade/downgrade/upgrade verified on live PostgreSQL 16.
- **Frontend Code Quality**:
  - `npm.cmd run typecheck`: 0 errors.
  - `npm.cmd run lint`: 0 errors, 0 warnings.
  - `npm.cmd run build`: 19/19 routes compiled successfully.

### Strict Phase Boundaries Preserved
- Prohibited and NOT IMPLEMENTED:
  - No Leave management or complaints (Phase 6)
  - No Case management or intervention notes (Phase 7)
  - No LLM-generated risk scores or dropout predictions
  - No mental health diagnosis or clinical interpretation
  - No direct disciplinary intervention or academic standing modification





