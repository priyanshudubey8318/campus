# CampusPulse — API Contract Specification

This document specifies the authoritative HTTP API contracts for CampusPulse Phase 0.

> **Status**: v1.0 (Phase 0 Foundation)  
> **Base URL**: `/api/v1`  
> **API Versioning Strategy**: Explicit URI versioning (`/api/v1/...`). Breaking contract alterations will require a new major version prefix (`/api/v2/...`).

---

## 1. Root Information

### `GET /`
Returns service metadata and navigation links for discovery.

* **Method**: `GET`
* **Path**: `/`
* **Authentication**: None
* **Status Code**: `200 OK`
* **Response Content-Type**: `application/json`

#### Response Payload
```json
{
  "name": "CampusPulse",
  "version": "0.1.0",
  "environment": "development",
  "docs_url": "/docs",
  "health_url": "/api/v1/health"
}
```

---

## 2. Health & Diagnostics

### `GET /api/v1/health`
Performs an end-to-end check of application liveness, uptime, and database connectivity.

* **Method**: `GET`
* **Path**: `/api/v1/health`
* **Authentication**: None
* **Status Code**: `200 OK`
* **Response Content-Type**: `application/json`

#### Response Fields
| Field | Type | Description |
|---|---|---|
| `status` | string | `"healthy"` (when DB connected) or `"degraded"` (when DB unreachable) |
| `app_name` | string | Configured application name |
| `version` | string | Application semantic version |
| `environment` | string | Active runtime environment (`development`, `staging`, `production`, `test`) |
| `timestamp` | string (ISO-8601) | Current server UTC timestamp |
| `uptime_seconds` | number | Server process uptime in seconds |
| `database.connected` | boolean | Database reachability indicator |
| `database.dialect` | string | SQLAlchemy database dialect name (`postgresql`, `sqlite`) |
| `database.message` | string | Diagnostic connection message |

#### Success Response Example (`200 OK`)
```json
{
  "status": "healthy",
  "app_name": "CampusPulse",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-17T17:06:24.708291Z",
  "uptime_seconds": 80.35,
  "database": {
    "connected": true,
    "dialect": "postgresql",
    "message": "Database is operational"
  }
}
```

#### Degraded Response Example (`200 OK`)
```json
{
  "status": "degraded",
  "app_name": "CampusPulse",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-17T17:05:12.783901Z",
  "uptime_seconds": 8.43,
  "database": {
    "connected": false,
    "dialect": "postgresql",
    "message": "(psycopg2.OperationalError) connection to server at \"localhost\" failed..."
  }
}
```

---

### `GET /api/v1/health/db`
Dedicated database engine health probe.

* **Method**: `GET`
* **Path**: `/api/v1/health/db`
* **Authentication**: None
* **Status Code**: `200 OK`
* **Response Content-Type**: `application/json`

#### Success Response Example (`200 OK`)
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "dialect": "postgresql",
    "message": "Database is operational"
  },
  "timestamp": "2026-09-17T17:06:25.125455Z"
}
```

---

## 3. Identity, Authentication & RBAC (Phase 1)

All Phase 1 authentication endpoints reside under `/api/v1/auth`. Authentication tokens are dual-delivered via HTTP-Only SameSite cookies (`campuspulse_access_token`, `campuspulse_refresh_token`) and Bearer Authorization headers (`Authorization: Bearer <token>`).

### `POST /api/v1/auth/register`
Registers a new user account with Argon2id password hashing and assigns an initial role.

* **Method**: `POST`
* **Path**: `/api/v1/auth/register`
* **Authentication**: None
* **Status Code**: `201 Created`
* **Request Payload**:
  ```json
  {
    "email": "student@university.edu",
    "password": "SecurePassword123!",
    "full_name": "Jane Doe",
    "phone": "+15550199",
    "role": "STUDENT"
  }
  ```
* **Response Payload (`201 Created`)**:
  ```json
  {
    "id": "c1f73bca-9014-4e3a-9694-811c793ff018",
    "email": "student@university.edu",
    "full_name": "Jane Doe",
    "phone": "+15550199",
    "is_active": true,
    "is_verified": false,
    "roles": ["STUDENT"],
    "permissions": ["academic:read_own", "complaints:create", "complaints:read_own", "profile:read_own", "pulsewatch:read_own"],
    "created_at": "2026-09-18T06:20:00Z",
    "last_login_at": null
  }
  ```
* **Error Responses**:
  - `400 Bad Request`: Email already registered.
  - `422 Unprocessable Entity`: Password fails complexity rules (minimum 8 chars, uppercase, lowercase, digit, special character).

---

### `POST /api/v1/auth/login`
Authenticates credentials, updates rate-limiting counters, writes security audit trail, and issues session tokens.

* **Method**: `POST`
* **Path**: `/api/v1/auth/login`
* **Authentication**: None
* **Status Code**: `200 OK`
* **Cookies Set**:
  - `campuspulse_access_token` (HttpOnly, SameSite=Lax, Path=/, Max-Age=900s)
  - `campuspulse_refresh_token` (HttpOnly, SameSite=Lax, Path=/, Max-Age=604800s)
* **Request Payload**:
  ```json
  {
    "email": "student@university.edu",
    "password": "SecurePassword123!"
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": "c1f73bca-9014-4e3a-9694-811c793ff018",
      "email": "student@university.edu",
      "full_name": "Jane Doe",
      "is_active": true,
      "is_verified": false,
      "roles": ["STUDENT"],
      "permissions": ["academic:read_own", "complaints:create", "complaints:read_own", "profile:read_own", "pulsewatch:read_own"],
      "created_at": "2026-09-18T06:20:00Z",
      "last_login_at": "2026-09-18T06:25:00Z"
    }
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`: `"Invalid email or password"` (generic message prevents account enumeration).
  - `403 Forbidden`: `"Account is inactive"`.
  - `429 Too Many Requests`: Triggered when sliding-window threshold is exceeded (5 failed attempts per 300 seconds). Returns `Retry-After` header.

---

### `POST /api/v1/auth/refresh`
Rotates refresh tokens and issues fresh access token. Reads refresh token from HTTP-only cookie or optional JSON body.

* **Method**: `POST`
* **Path**: `/api/v1/auth/refresh`
* **Authentication**: Refresh token in cookie or body
* **Status Code**: `200 OK`
* **Response Payload**: Same schema as `/login` (`TokenResponse`).
* **Error Responses**:
  - `401 Unauthorized`: Invalid, expired, or already-revoked refresh token.

---

### `POST /api/v1/auth/logout`
Revokes active refresh token in database, deletes browser session cookies, and emits audit event.

* **Method**: `POST`
* **Path**: `/api/v1/auth/logout`
* **Authentication**: Optional Bearer token or cookie
* **Status Code**: `200 OK`
* **Response Payload**:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```

---

### `GET /api/v1/auth/me`
Retrieves public profile, assigned roles, and granted permission codes for the authenticated user.

* **Method**: `GET`
* **Path**: `/api/v1/auth/me`
* **Authentication**: Bearer token or `campuspulse_access_token` cookie
* **Status Code**: `200 OK`
* **Response Payload**: `UserResponse` object.
* **Error Responses**:
  - `401 Unauthorized`: Not authenticated or token expired.
  - `403 Forbidden`: Account is inactive.

---

### RBAC Verification Endpoints
- `GET /api/v1/auth/role-check/admin`: Enforces `require_role("ADMIN")` (or `SUPER_ADMIN`). Returns 403 Forbidden if not authorized.
- `GET /api/v1/auth/role-check/student`: Enforces `require_role("STUDENT")` (or `SUPER_ADMIN`).
- `GET /api/v1/auth/permission-check/user-manage`: Enforces `require_permission("users:write")` (or `SUPER_ADMIN`).

---

## 4. Phase 2 Academic Domain & Profiles Contracts

Base Path: `/api/v1/academic`

### 4.1 Profile Endpoints

#### `GET /api/v1/academic/student-profiles/me`
* **Auth**: Active user with `STUDENT` role (or `SUPER_ADMIN`).
* **Response**: `StudentProfileResponse` containing student's enrollment record, batch, program, section, and semester.

#### `GET /api/v1/academic/student-profiles/{id}`
* **Auth**: Active user. Students may only access their own profile; faculty/advisors/admins may inspect institutional records. Returns `403 Forbidden` on cross-student violations.
* **Response**: `StudentProfileResponse`.

#### `GET /api/v1/academic/faculty-profiles/me`
* **Auth**: Active user with `FACULTY` role (or `SUPER_ADMIN`).
* **Response**: `FacultyProfileResponse` containing employee ID, department, designation, and appointment status.

#### `GET /api/v1/academic/faculty-profiles/{id}`
* **Auth**: Active user with administrative or faculty access.

### 4.2 Hierarchy & Course Catalog

#### `GET /api/v1/academic/courses`
* **Auth**: Authenticated user.
* **Query Params**: `department_id` (optional).
* **Response**: `List[CourseResponse]`.

#### `GET /api/v1/academic/enrollments`
* **Auth**: Authenticated user. Students receive their own enrollments; faculty/admins receive scoped or all enrollments.
* **Query Params**: `student_id`, `course_id`, `term_id`.
* **Response**: `List[EnrollmentResponse]`.

#### `POST /api/v1/academic/enrollments`
* **Auth**: `ADMIN`, `SUPER_ADMIN`.
* **Payload**: `EnrollmentCreate` (`student_id`, `course_id`, `term_id`, `section_id`, `enrollment_date`, `status`).
* **Validations**:
  - Student `academic_status` must be `ENROLLED`.
  - Course must be active (`course.is_active == True`); inactive courses rejected with `422 Unprocessable Entity` (`"Cannot enroll in an inactive course"`).
  - Course and term must belong to the same institution (`course.institution_id == term.institution_id`); mismatches rejected with `422 Unprocessable Entity` (`"Course and academic term must belong to the same institution"`).
  - Enforces `(student_id, course_id, term_id)` composite uniqueness (returns `409 Conflict` on duplicates).
* **Response**: `EnrollmentResponse` (`201 Created`).

#### `GET /api/v1/academic/faculty-assignments`
* **Auth**: Authenticated user. Faculty members receive their own assignments; admins receive all assignments.
* **Query Params**: `faculty_id`, `course_id`, `term_id`.
* **Response**: `List[FacultyCourseAssignmentResponse]`.

### 4.3 Attendance Operations

#### `GET /api/v1/academic/attendance`
* **Auth**: Authenticated user. Students can only view their own attendance records.
* **Query Params**: `student_id`, `course_id`, `term_id`.
* **Response**: `List[AttendanceRecordResponse]`.

#### `GET /api/v1/academic/attendance/summary`
* **Auth**: Authenticated user. Returns derived attendance metrics calculated on demand.
* **Query Params**: `student_id`, `course_id`, `term_id`.
* **Response**: `AttendanceSummaryResponse` (`total_sessions`, `present_count`, `absent_count`, `late_count`, `excused_count`, `attendance_percentage`).

#### `POST /api/v1/academic/attendance`
* **Auth**: `FACULTY` assigned to course/section, or `ADMIN`/`SUPER_ADMIN`.
* **Payload**: `AttendanceRecordCreate` (`student_id`, `course_id`, `term_id`, `session_date`, `session_slot`, `status`, `source`, `remarks`).
* **Strict Enum Constraints**:
  - `status`: `Literal["PRESENT", "ABSENT", "LATE", "EXCUSED"]` (invalid values rejected with `422 Unprocessable Entity`).
  - `source`: `Literal["MANUAL", "IMPORT", "LMS", "BIOMETRIC", "API"]` (default `"MANUAL"`, invalid values rejected with `422 Unprocessable Entity`).
* **Validations**: Student must be actively enrolled in course/term. Rejects unassigned faculty with `403 Forbidden`. Enforces session uniqueness `(student_id, course_id, session_date, session_slot)` (returns `409 Conflict` on duplicates).
* **Response**: `AttendanceRecordResponse` (`201 Created`).

### 4.4 Coursework & Assessments

#### `GET /api/v1/academic/assignments`
* **Auth**: Authenticated user.
* **Query Params**: `course_id`, `term_id`.
* **Response**: `List[AssignmentResponse]`.

#### `POST /api/v1/academic/assignments`
* **Auth**: `FACULTY` assigned to course, or `ADMIN`.
* **Payload**: `AssignmentCreate` (`course_id`, `term_id`, `section_id`, `title`, `description`, `max_marks`, `weightage_percentage`, `release_date`, `due_date`, `cutoff_date`, `allow_late_submission`).
* **Response**: `AssignmentResponse` (`201 Created`).

#### `POST /api/v1/academic/assignments/{id}/submissions`
* **Auth**: Enrolled `STUDENT`.
* **Payload**: `AssignmentSubmissionCreate` (`submission_text`, `file_url`).
* **Behavior**: Automatically determines `attempt_number` and sets `is_late` based on current server timestamp vs assignment due date. Rejects after cutoff date.
* **Response**: `AssignmentSubmissionResponse` (`201 Created`).

#### `GET /api/v1/academic/assessments`
* **Auth**: Authenticated user.
* **Query Params**: `course_id`, `term_id`.
* **Response**: `List[AssessmentResponse]`.

#### `POST /api/v1/academic/assessments/{id}/results`
* **Auth**: `FACULTY` assigned to course, or `ADMIN`.
* **Payload**: `AssessmentResultCreate` (`student_id`, `marks_obtained`, `is_absent`, `remarks`).
* **Validations**: `marks_obtained >= 0`, `marks_obtained <= assessment.max_marks`, positive marks rejected if `is_absent=True`.
* **Response**: `AssessmentResultResponse` (`201 Created`).

---

## 5. Phase 3: PulseWatch Behavioral Monitoring Endpoints

All endpoints require authentication and enforce strict student-scoping (`verify_student_record_access`):
- `STUDENT`: Permitted to inspect only their own behavioral records. Cross-student requests return `403 Forbidden`.
- `FACULTY`: Permitted only for students actively enrolled in an assigned course offering.
- `ADMIN` / `SUPER_ADMIN`: Permitted with institutional oversight.

### `GET /api/v1/pulsewatch/student/{student_id}/summary`
Computes live academic behavioral engagement summary. Strictly read-only with zero database write side-effects.
* **Query Params**: `window_days` (integer, default `14`, min `7`, max `60`).
* **Response**: `PulseWatchSummaryResponse` (`200 OK`)
  - `student_id`: UUID
  - `observation_window_days`: integer
  - `window_start_date`, `window_end_date`: ISO date
  - `baseline_start_date`, `baseline_end_date`: ISO date (strictly precedes observation window)
  - `data_quality`: `"NO_DATA"` | `"INSUFFICIENT_DATA"` | `"VALID_DATA"`
  - `overall_status`: `"NORMAL"` | `"MILD_CHANGE"` | `"MODERATE_CHANGE"` | `"SIGNIFICANT_CHANGE"`
  - `summary_text`: string
  - `signals`: `List[SignalEvidenceSchema]`
  - `cohort_context`: `CohortContextSchema`
  - `academic_context`: `AcademicContextSchema`
  - `explainability`: `ExplainabilitySchema`
  - `algorithm_version`: `"pulsewatch-v1.0"`
  - `calculated_at`: ISO datetime

### `GET /api/v1/pulsewatch/student/{student_id}/timeline`
Retrieves persisted historical behavior events for an authorized student.
* **Query Params**: `limit` (integer, default `50`, min `1`, max `100`).
* **Response**: `List[BehaviorEventResponse]` (`200 OK`).

### `GET /api/v1/pulsewatch/student/{student_id}/signals`
Retrieves granular calculated signal evidence for the observation window.
* **Query Params**: `window_days` (integer, default `14`).
* **Response**: `List[SignalEvidenceSchema]` (`200 OK`).

### `GET /api/v1/pulsewatch/student/{student_id}/baseline`
Retrieves persisted personal behavioral baselines for an authorized student.
* **Response**: `List[StudentBehaviorBaselineResponse]` (`200 OK`).

### `POST /api/v1/pulsewatch/student/{student_id}/evaluate`
Explicitly computes and idempotently persists PulseWatch events and rolling baselines.
* **Query Params**: `window_days` (integer, default `14`).
* **Idempotency Guarantee**: Repeated calls with the same student, window, dates, and algorithm version update the existing record without generating duplicate events.
* **Response**: `BehaviorEventResponse` (`200 OK`).

---

## 6. PulseAssist API Contract (Phase 5)

### `POST /api/v1/pulseassist/query`
Main student & user policy inquiry endpoint executing RAG hybrid retrieval, grounded generation, and verification.
* **Method**: `POST`
* **Path**: `/api/v1/pulseassist/query`
* **Authentication**: Bearer Token (Any authenticated user)
* **Request Body**:
  ```json
  {
    "question": "What is the minimum attendance requirement to write final exams?",
    "conversation_id": "optional-uuid",
    "institution_id": "optional-uuid-super-admin-override"
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "answer": "Under the Attendance Policy [Doc: POL-ATT-001], students must maintain at least 75% attendance...",
    "conversation_id": "99999999-9999-4999-8999-999999999999",
    "citations": [
      {
        "citation_id": "88888888-8888-4888-8888-888888888888",
        "document_code": "POL-ATT-001",
        "document_title": "Attendance and Minimum Floor Policy",
        "chunk_index": 0,
        "content_snippet": "Students must maintain at least 75% overall course attendance...",
        "verified": true,
        "effective_from": "2026-01-01",
        "effective_to": null
      }
    ],
    "metrics": {
      "attendance_pct": 74.5,
      "cgpa": 3.42,
      "spi_tier": "TIER_0",
      "as_of_date": "2026-09-23",
      "disclaimer": "Verified ground-truth data from registrar/attendance systems. Not an AI estimate."
    },
    "disclaimer": "PulseAssist provides institutional policy guidance based on approved campus documents. It does not provide medical, mental health, or academic intervention determinations."
  }
  ```

### `GET /api/v1/pulseassist/conversations`
Lists the user's active conversations.
* **Response**: `List[PulseAssistConversationSummary]` (`200 OK`).

### `GET /api/v1/pulseassist/conversations/{conversation_id}`
Retrieves complete conversation thread with messages and citations.
* **Response**: `PulseAssistConversationDetail` (`200 OK`).

### `GET /api/v1/pulseassist/documents`
Lists institutional knowledge documents (Admins & Super Admins).
* **Query Params**: `institution_id` (optional for SUPER_ADMIN).
* **Response**: `List[KnowledgeDocumentResponse]` (`200 OK`).

### `POST /api/v1/pulseassist/documents`
Uploads and parses a new draft knowledge document.
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "document_code": "POL-ATT-001",
    "title": "Institutional Attendance Regulations",
    "category": "ATTENDANCE",
    "target_audience": "STUDENTS",
    "content_text": "# SECTION 1: Minimum Attendance Floor\nStudents must maintain..."
  }
  ```
* **Response**: `KnowledgeDocumentResponse` (`201 Created`).

### `POST /api/v1/pulseassist/documents/{document_id}/publish`
Publishes a draft document, makes it immutable, vectors semantic chunks, and creates an active version schedule.
* **Request Body**:
  ```json
  {
    "effective_from": "2026-09-01",
    "effective_to": null
  }
  ```
* **Response**: `KnowledgeDocumentResponse` (`200 OK`).

### `POST /api/v1/pulseassist/documents/{document_id}/archive`
Archives an active or published document, setting its schedule to inactive and removing it from future RAG retrieval.
* **Response**: `KnowledgeDocumentResponse` (`200 OK`).

---

## 7. Error Contract

Unhandled exceptions return standardized JSON error responses with sanitized messaging:

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An internal server error occurred.",
    "path": "/api/v1/example"
  }
}
```

* Stack traces and internal database connection parameters are stripped in non-debug environments.

---

## 8. Planned Future Phase Endpoints

The following endpoint modules are planned for subsequent phases:
- `/api/v1/leaves/...` (Phase 6: Leave Management)
- `/api/v1/complaints/...` (Phase 6: Complaint & Appeal Workflows)
- `/api/v1/cases/...` (Phase 7: Advisor Intervention Case Management)
- `/api/v1/analytics/...` (Phase 8: Institutional & Fairness Reporting)


