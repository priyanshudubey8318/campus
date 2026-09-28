# CampusPulse — Database Architecture & Schema

This document details the database configuration, schema, and migration workflows for CampusPulse Phase 0.

---

## 1. Canonical Database Engine

* **Database**: PostgreSQL 16
* **Python ORM**: SQLAlchemy 2.0 (Declarative Base, Mapped column types)
* **Migration Framework**: Alembic 1.13+
* **Driver**: `psycopg2-binary`

Manual schema modifications in production or development databases are strictly forbidden. Every schema modification must be tracked by an Alembic migration script.

---

## 2. Session Management & Scoping

Database sessions are managed via FastAPI dependency injection:

* Engine: Configured with `pool_pre_ping=True` to detect and refresh stale connections.
* Session Factory: `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
* Request-Scoped Lifecycle:
  ```python
  def get_db() -> Generator[Session, None, None]:
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```
  Every HTTP request receives its own isolated session and automatically closes it when the request cycle completes.

---

## 3. Current Phase 0 Schema

Phase 0 intentionally avoids creating premature business-domain tables (which are scheduled for Phases 1–7). It establishes a minimal foundational schema to verify Alembic migrations bidirectionally and support security audit trails.

### Table: `audit_logs`

Tracks administrative, system, and critical lifecycle actions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `action` | `VARCHAR(100)` | NOT NULL, INDEXED | Event action code (e.g. `SYSTEM_INITIALIZE`) |
| `entity_type` | `VARCHAR(100)` | NULLABLE, INDEXED | Target entity category (e.g. `SYSTEM`, `USER`) |
| `entity_id` | `VARCHAR(100)` | NULLABLE | Target record UUID or identifier |
| `actor_id` | `VARCHAR(100)` | NULLABLE, INDEXED | User or system actor ID |
| `actor_role` | `VARCHAR(50)` | NULLABLE | Actor role at time of event |
| `details` | `TEXT` | NULLABLE | Contextual details or event payload |
| `ip_address` | `VARCHAR(45)` | NULLABLE | Client IPv4 or IPv6 address |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC update timestamp |

### Table: `alembic_version`
Maintained automatically by Alembic to record the current applied migration revision.

---

## 4. Phase 1 Schema: Identity, Authentication & RBAC

Migration `0002_identity_and_access.py` establishes the decoupled identity foundation, token-based session management, and many-to-many role-based access control.

### Table: `users`
Core authentication principal. Stripped of domain profiles, which reference `user_id` in subsequent phases.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEXED | Normalized institutional/personal email |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Argon2id cryptographic hash (RFC 9106) |
| `full_name` | `VARCHAR(255)` | NOT NULL | User's full preferred name |
| `phone` | `VARCHAR(30)` | NULLABLE | Contact telephone |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT true, INDEXED | Account active status indicator |
| `is_verified` | `BOOLEAN` | NOT NULL, DEFAULT false | Email/identity verification status |
| `last_login_at` | `TIMESTAMP WITH TIME ZONE` | NULLABLE | Timestamp of most recent authentication |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC update timestamp |

### Table: `roles`
Institutional system and administrative roles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `name` | `VARCHAR(50)` | UNIQUE, NOT NULL, INDEXED | Canonical role name (`STUDENT`, `FACULTY`, `ADMIN`, etc.) |
| `description` | `VARCHAR(255)` | NULLABLE | Description of responsibilities and scope |
| `is_system_role` | `BOOLEAN` | NOT NULL, DEFAULT true | System-defined immutable role flag |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC update timestamp |

### Table: `permissions`
Granular operation and capability codes.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `code` | `VARCHAR(100)` | UNIQUE, NOT NULL, INDEXED | Canonical permission code (`users:read`, `cases:write_assigned`) |
| `name` | `VARCHAR(100)` | NOT NULL | Human-readable permission name |
| `description` | `VARCHAR(255)` | NULLABLE | Scope of operations authorized |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC update timestamp |

### Table: `user_roles`
Many-to-many junction linking users to assigned institutional roles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `user_id` | `VARCHAR(36)` | NOT NULL, FK(`users.id` CASCADE) | Reference to user |
| `role_id` | `VARCHAR(36)` | NOT NULL, FK(`roles.id` CASCADE) | Reference to assigned role |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |

*Unique Index*: `(user_id, role_id)` prevents duplicate role assignments.

### Table: `role_permissions`
Many-to-many junction mapping granular permissions to roles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `role_id` | `VARCHAR(36)` | NOT NULL, FK(`roles.id` CASCADE) | Reference to role |
| `permission_id` | `VARCHAR(36)` | NOT NULL, FK(`permissions.id` CASCADE) | Reference to permission |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |

*Unique Index*: `(role_id, permission_id)`.

### Table: `refresh_tokens`
Opaque session refresh tokens with cryptographic hash storage.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID identifier |
| `user_id` | `VARCHAR(36)` | NOT NULL, FK(`users.id` CASCADE) | Owning user account |
| `token_hash` | `VARCHAR(64)` | UNIQUE, NOT NULL, INDEXED | SHA-256 hash of plaintext refresh token |
| `expires_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, INDEXED | Session expiration timestamp (7 days) |
| `revoked_at` | `TIMESTAMP WITH TIME ZONE` | NULLABLE | Timestamp token was explicitly revoked |
| `replaced_by_token_id` | `VARCHAR(36)` | NULLABLE | Pointer to successor token (rotation tracking) |
| `ip_address` | `VARCHAR(45)` | NULLABLE | Client IP at token issuance |
| `user_agent` | `TEXT` | NULLABLE | Client browser User-Agent header |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | UTC update timestamp |

---

## 5. Test Database Isolation & Safety Guards

To guarantee tests never mutate or destroy development or production data:

1. **Explicit Separation**:
   - `DATABASE_URL`: Primary development database (e.g. `postgresql://.../campuspulse`)
   - `TEST_DATABASE_URL`: Dedicated isolated test database (e.g. `postgresql://.../campuspulse_test`)

2. **Automated Safety Guard**:
   In `app.core.config.Settings.validate_test_database_safety()`:
   - Fails immediately if `TEST_DATABASE_URL == DATABASE_URL`.
   - Fails immediately if `TEST_DATABASE_URL` does not explicitly contain `"test"` in its name.

3. **Transaction Isolation**:
   Integration tests run inside database transactions that are rolled back upon test completion, ensuring a clean state across tests.

---

## 6. Phase 2 Schema: Academic Domain, Profiles & Coursework Foundation

Migration `0003_academic_foundation.py` establishes the foundational academic relational schema, separating domain profiles from identity principals and enforcing relational constraints across the educational hierarchy.

### 6.1 Institutional Hierarchy Models

#### Table: `institutions`
Top-level accredited entity.
* Columns: `id` (PK, UUID), `name` (VARCHAR 255), `code` (VARCHAR 50, UNIQUE), `address` (TEXT), `contact_email` (VARCHAR 255), `is_active` (BOOLEAN, default true), `created_at`, `updated_at`.

#### Table: `departments`
Academic departments belonging to an institution.
* Columns: `id` (PK, UUID), `institution_id` (FK `institutions.id`), `name` (VARCHAR 255), `code` (VARCHAR 50), `is_active` (BOOLEAN), `created_at`, `updated_at`.
* *Composite Unique*: `(institution_id, code)`.

#### Table: `programs`
Degree programs offered by departments.
* Columns: `id` (PK, UUID), `department_id` (FK `departments.id`), `name` (VARCHAR 255), `code` (VARCHAR 50), `degree_level` (VARCHAR 50), `duration_years` (INT), `is_active` (BOOLEAN), `created_at`, `updated_at`.
* *Composite Unique*: `(department_id, code)`.

#### Table: `batches`
Student cohort year groups within a program.
* Columns: `id` (PK, UUID), `program_id` (FK `programs.id`), `name` (VARCHAR 100), `start_year` (INT), `end_year` (INT), `current_semester` (INT), `is_active` (BOOLEAN), `created_at`, `updated_at`.
* *Composite Unique*: `(program_id, name)`.
* *CHECK Constraint*: `start_year <= end_year`.

#### Table: `sections`
Lecture/lab cohort subdivisions within a batch.
* Columns: `id` (PK, UUID), `batch_id` (FK `batches.id`), `name` (VARCHAR 50), `capacity` (INT), `is_active` (BOOLEAN), `created_at`, `updated_at`.
* *Composite Unique*: `(batch_id, name)`.

#### Table: `academic_terms`
Semesters, trimesters, or academic calendars.
* Columns: `id` (PK, UUID), `institution_id` (FK `institutions.id`), `name` (VARCHAR 100), `term_type` (VARCHAR 50), `start_date` (DATE), `end_date` (DATE), `is_current` (BOOLEAN), `created_at`, `updated_at`.
* *Composite Unique*: `(institution_id, name)`.
* *CHECK Constraint*: `start_date <= end_date`.

### 6.2 Domain Profiles (Identity Decoupling)

#### Table: `student_profiles`
Student academic records linked 1:1 with `users.id` with zero authentication credentials.
* Columns: `id` (PK, UUID), `user_id` (VARCHAR 36, FK `users.id` RESTRICT), `enrollment_number` (VARCHAR 100), `program_id` (FK `programs.id`), `batch_id` (FK `batches.id`), `section_id` (NULLABLE, FK `sections.id`), `current_semester` (INT), `admission_date` (DATE), `academic_status` (VARCHAR 50, default 'ENROLLED'), `created_at`, `updated_at`.
* *Named Unique Constraints*: `uq_student_profiles_enrollment_number` on `enrollment_number`, `uq_student_profiles_user_id` on `user_id`.
* *Unique Indexes*: `ix_student_profiles_enrollment_number`, `ix_student_profiles_user_id`.

#### Table: `faculty_profiles`
Faculty appointments linked 1:1 with `users.id` with zero authentication credentials.
* Columns: `id` (PK, UUID), `user_id` (VARCHAR 36, FK `users.id` RESTRICT), `employee_id` (VARCHAR 100), `department_id` (FK `departments.id`), `designation` (VARCHAR 100), `qualification` (VARCHAR 255), `specialization` (VARCHAR 255), `joining_date` (DATE), `is_active` (BOOLEAN, default true), `created_at`, `updated_at`.
* *Named Unique Constraints*: `uq_faculty_profiles_employee_id` on `employee_id`, `uq_faculty_profiles_user_id` on `user_id`.
* *Unique Indexes*: `ix_faculty_profiles_employee_id`, `ix_faculty_profiles_user_id`.

### 6.3 Courses & Teaching Assignments

#### Table: `courses`
Accredited courses offered by departments.
* Columns: `id` (PK, UUID), `institution_id` (FK `institutions.id`), `department_id` (FK `departments.id`), `code` (VARCHAR 50), `title` (VARCHAR 255), `credits` (INT), `course_type` (VARCHAR 50), `syllabus_summary` (TEXT), `is_active` (BOOLEAN), `created_at`, `updated_at`.
* *Composite Unique*: `(institution_id, code)`.

#### Table: `faculty_course_assignments`
Teaching allocations scoped to courses, terms, and optional sections.
* Columns: `id` (PK, UUID), `faculty_id` (FK `faculty_profiles.id`), `course_id` (FK `courses.id`), `term_id` (FK `academic_terms.id`), `section_id` (NULLABLE, FK `sections.id`), `role` (VARCHAR 50), `created_at`, `updated_at`.
* *Partial Unique Indexes*:
  - `uq_faculty_assignment_course`: `(faculty_id, course_id, term_id) WHERE section_id IS NULL`
  - `uq_faculty_assignment_section`: `(faculty_id, course_id, term_id, section_id) WHERE section_id IS NOT NULL`

### 6.4 Enrollments & Attendance

#### Table: `enrollments`
Course registrations for a term.
* Columns: `id` (PK, UUID), `student_id` (FK `student_profiles.id`), `course_id` (FK `courses.id`), `term_id` (FK `academic_terms.id`), `section_id` (NULLABLE, FK `sections.id`), `enrollment_date` (DATE), `status` (VARCHAR 50), `created_at`, `updated_at`.
* *Composite Unique*: `(student_id, course_id, term_id)`.
* *Service Validation*: `course.is_active == True` and `course.institution_id == term.institution_id`.

#### Table: `attendance_records`
Raw session events (attendance percentage is strictly derived on demand).
* Columns: `id` (PK, UUID), `student_id` (FK `student_profiles.id`), `course_id` (FK `courses.id`), `term_id` (FK `academic_terms.id`), `session_date` (DATE), `session_slot` (VARCHAR 50), `status` (VARCHAR 50), `source` (VARCHAR 50), `recorded_by_faculty_id` (NULLABLE, FK `faculty_profiles.id`), `remarks` (TEXT), `created_at`, `updated_at`.
* *Composite Unique*: `(student_id, course_id, session_date, session_slot)`.
* *Composite Time-Series Index*: `ix_attendance_records_student_id_session_date` on `(student_id, session_date)` (PulseWatch rolling-window and streak analysis).
* *Strict Enums*:
  - `status`: `PRESENT`, `ABSENT`, `LATE`, `EXCUSED`
  - `source`: `MANUAL`, `IMPORT`, `LMS`, `BIOMETRIC`, `API` (default `MANUAL`)

### 6.5 Coursework & Evaluations

#### Table: `assignments`
Tasks issued by faculty.
* Columns: `id` (PK, UUID), `course_id` (FK `courses.id`), `term_id` (FK `academic_terms.id`), `section_id` (NULLABLE, FK `sections.id`), `created_by_faculty_id` (FK `faculty_profiles.id`), `title` (VARCHAR 255), `description` (TEXT), `max_marks` (NUMERIC 6,2), `weightage_percentage` (NUMERIC 5,2), `release_date` (TIMESTAMPTZ), `due_date` (TIMESTAMPTZ), `cutoff_date` (NULLABLE, TIMESTAMPTZ), `allow_late_submission` (BOOLEAN), `created_at`, `updated_at`.
* *CHECK Constraints*:
  - `chk_assignments_release_due`: `release_date <= due_date`
  - `chk_assignments_due_cutoff`: `cutoff_date IS NULL OR due_date <= cutoff_date`

#### Table: `assignment_submissions`
Student submission attempts with full attempt tracking.
* Columns: `id` (PK, UUID), `assignment_id` (FK `assignments.id`), `student_id` (FK `student_profiles.id`), `attempt_number` (INT, >= 1), `submitted_at` (TIMESTAMPTZ), `submission_content` (TEXT), `attachment_path` (VARCHAR 500), `is_late` (BOOLEAN), `status` (VARCHAR 50), `marks_obtained` (NUMERIC 6,2), `remarks` (VARCHAR 255), `created_at`, `updated_at`.
* *Composite Unique*: `(assignment_id, student_id, attempt_number)`.
* *Composite Time-Series Index*: `ix_assignment_submissions_student_id_submitted_at` on `(student_id, submitted_at)` (PulseWatch submission velocity and lead-time analysis).

#### Table: `assessments`
Examinations and formal tests.
* Columns: `id` (PK, UUID), `course_id` (FK `courses.id`), `term_id` (FK `academic_terms.id`), `title` (VARCHAR 255), `assessment_type` (VARCHAR 50), `max_marks` (NUMERIC 6,2), `weightage_percentage` (NUMERIC 5,2), `conducted_date` (DATE), `created_at`, `updated_at`.

#### Table: `assessment_results`
Student scores evaluated against assessments.
* Columns: `id` (PK, UUID), `assessment_id` (FK `assessments.id`), `student_id` (FK `student_profiles.id`), `marks_obtained` (NUMERIC 6,2), `is_absent` (BOOLEAN, default false), `remarks` (TEXT), `evaluated_by_faculty_id` (NULLABLE, FK `faculty_profiles.id`), `created_at`, `updated_at`.
* *Composite Unique*: `(assessment_id, student_id)`.
* *Database CHECK Constraint*: `marks_obtained >= 0`.
* *Deterministic Service Validation*: `marks_obtained <= assessment.max_marks` and marks must be 0 if `is_absent=True`.

---

## 7. Phase 3 Schema: PulseWatch Deterministic Behavioral Monitoring

Migration `0005_pulsewatch_behavioral_monitoring.py` establishes the persistent foundation for student baselines, behavioral shift events, and granular deterministic signal evidence.

### Table: `student_behavior_baselines`
Persisted personal rolling engagement baselines.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `student_id` (`VARCHAR(36)`, FK `student_profiles.id`, ondelete `CASCADE`)
  - `metric_type` (`VARCHAR(50)`, NOT NULL)
  - `baseline_value` (`NUMERIC(6,2)`, NULLABLE)
  - `observation_count` (`INTEGER`, NOT NULL, DEFAULT 0)
  - `data_quality` (`VARCHAR(30)`, NOT NULL, DEFAULT `'INSUFFICIENT_DATA'`)
  - `window_days` (`INTEGER`, NOT NULL, DEFAULT 30)
  - `algorithm_version` (`VARCHAR(50)`, NOT NULL, DEFAULT `'pulsewatch-v1.0'`)
  - `calculated_at` (`TIMESTAMPTZ`, NOT NULL)
  - `created_at`, `updated_at` (`TIMESTAMPTZ`, NOT NULL)
* *Composite Unique Constraint*: `uq_student_baselines_metric_window_algo` on `(student_id, metric_type, window_days, algorithm_version)`
* *Performance Index*: `ix_student_baselines_student_metric` on `(student_id, metric_type)`

### Table: `behavior_events`
Persisted academic engagement shifts evaluated over an observation window.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `student_id` (`VARCHAR(36)`, FK `student_profiles.id`, ondelete `CASCADE`)
  - `event_type` (`VARCHAR(50)`, NOT NULL) — `ACADEMIC_ENGAGEMENT_CHANGE`, `ATTENDANCE_DROP`, etc.
  - `severity` (`VARCHAR(30)`, NOT NULL) — `NORMAL`, `MILD_CHANGE`, `MODERATE_CHANGE`, `SIGNIFICANT_CHANGE`
  - `observation_window_days` (`INTEGER`, NOT NULL, DEFAULT 14)
  - `window_start_date` (`DATE`, NOT NULL)
  - `window_end_date` (`DATE`, NOT NULL)
  - `summary_text` (`TEXT`, NOT NULL)
  - `status` (`VARCHAR(30)`, NOT NULL, DEFAULT `'ACTIVE'`)
  - `algorithm_version` (`VARCHAR(50)`, NOT NULL, DEFAULT `'pulsewatch-v1.0'`)
  - `detected_at` (`TIMESTAMPTZ`, NOT NULL)
  - `created_at`, `updated_at` (`TIMESTAMPTZ`, NOT NULL)
* *Composite Unique Constraint (Idempotency)*: `uq_behavior_events_student_window_algo` on `(student_id, observation_window_days, window_start_date, window_end_date, algorithm_version)`
* *Time-Series Index*: `ix_behavior_events_student_detected` on `(student_id, detected_at)`

### Table: `behavior_signal_evidence`
Granular metric indicators explaining each detected behavioral shift event.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `event_id` (`VARCHAR(36)`, FK `behavior_events.id`, ondelete `CASCADE`)
  - `signal_type` (`VARCHAR(50)`, NOT NULL) — `ATTENDANCE_CHANGE`, `SUBMISSION_LATENESS`, `MISSED_ASSIGNMENT`, `ASSESSMENT_PERFORMANCE`
  - `severity` (`VARCHAR(30)`, NOT NULL)
  - `metric_name` (`VARCHAR(100)`, NOT NULL)
  - `current_value` (`NUMERIC(6,2)`, NULLABLE)
  - `baseline_value` (`NUMERIC(6,2)`, NULLABLE)
  - `delta_value` (`NUMERIC(6,2)`, NULLABLE)
  - `evidence_payload` (`JSONB`, NULLABLE)
  - `created_at` (`TIMESTAMPTZ`, NOT NULL)
* *Index*: `ix_signal_evidence_event_signal` on `(event_id, signal_type)`

---

## 8. Phase 4 Schema: PulseRisk Support Prioritization Subsystem

Migration `0006_pulserisk_support_prioritization.py` adds institutional support priority scoring models:
* `risk_policies`: Governed policy configuration with partial unique index `uq_risk_policies_active_scope` ensuring at most one active policy per institution.
* `student_risk_snapshots`: Immutable prioritization evaluations with composite uniqueness on `(student_id, evaluation_date, window_days, algorithm_version, policy_version)`.
* `risk_signal_contributions`: Granular dimension contributions with full factor scores, weights, and observed values.

---

## 9. Phase 5 Schema: PulseAssist Institutional Knowledge Subsystem

Migration `0007_pulseassist_rag_knowledge.py` establishes the knowledge repository, vector chunk store, decoupled version scheduling, and grounded conversation system.

### Table: `knowledge_documents`
Authoritative institutional documents ingested for RAG.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `institution_id` (`VARCHAR(36)`, NOT NULL, FK `institutions.id`, ondelete `CASCADE`)
  - `document_code` (`VARCHAR(50)`, NOT NULL)
  - `title` (`VARCHAR(255)`, NOT NULL)
  - `version` (`INTEGER`, NOT NULL, DEFAULT 1)
  - `category` (`VARCHAR(50)`, NOT NULL, DEFAULT `'GENERAL'`)
  - `status` (`VARCHAR(30)`, NOT NULL, DEFAULT `'DRAFT'`) — `DRAFT`, `PUBLISHED`, `ARCHIVED`
  - `target_audience` (`VARCHAR(50)`, NOT NULL, DEFAULT `'ALL'`)
  - `content_hash` (`VARCHAR(64)`, NOT NULL)
  - `file_metadata` (`JSONB`, NOT NULL, DEFAULT `{}`)
  - `created_by` (`VARCHAR(36)`, NULLABLE, FK `users.id`, ondelete `SET NULL`)
  - `published_at` (`TIMESTAMPTZ`, NULLABLE) — Set strictly by database trigger on publication
  - `archived_at` (`TIMESTAMPTZ`, NULLABLE) — Set strictly by database trigger on archive
  - `created_at`, `updated_at` (`TIMESTAMPTZ`, NOT NULL)
* *Composite Uniqueness*: `uq_knowledge_documents_tenant_code_version` on `(institution_id, document_code, version)`
* *Unique Key for Composite FK Reference*: `uq_knowledge_documents_tenant_code_id` on `(institution_id, document_code, id)`

### Table: `document_chunks`
Semantic chunks derived from knowledge documents with dual dense/sparse representations.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `document_id` (`VARCHAR(36)`, NOT NULL, FK `knowledge_documents.id`, ondelete `CASCADE`)
  - `chunk_index` (`INTEGER`, NOT NULL)
  - `content` (`TEXT`, NOT NULL)
  - `chunk_hash` (`VARCHAR(64)`, NOT NULL)
  - `embedding` (`vector(768)`, NULLABLE) — Dense semantic vector representation (pgvector)
  - `tsv_content` (`tsvector`, NULLABLE) — Sparse full-text search index
  - `created_at`, `updated_at` (`TIMESTAMPTZ`, NOT NULL)
* *Composite Uniqueness*: `uq_document_chunks_document_chunk_index` on `(document_id, chunk_index)`
* *Indexes*:
  - `ix_document_chunks_tsv` using GIN on `tsv_content`
  - `ix_document_chunks_embedding_cosine` using HNSW on `embedding vector_cosine_ops` (or fallback IVFFlat)

### Table: `document_version_schedules`
Decoupled timeline schedules preserving document content immutability.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `institution_id` (`VARCHAR(36)`, NOT NULL)
  - `document_code` (`VARCHAR(50)`, NOT NULL)
  - `document_id` (`VARCHAR(36)`, NOT NULL)
  - `effective_from` (`DATE`, NOT NULL)
  - `effective_to` (`DATE`, NULLABLE)
  - `effective_range` (`daterange`, GENERATED ALWAYS AS `daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]')` STORED)
  - `is_active` (`BOOLEAN`, NOT NULL, DEFAULT TRUE)
  - `created_at`, `updated_at` (`TIMESTAMPTZ`, NOT NULL)
* *Composite Foreign Key*: `fk_doc_version_schedules_tenant_code_doc` references `knowledge_documents (institution_id, document_code, id)`
* *PostgreSQL Exclusion Constraint*: `ex_document_version_schedules_non_overlapping`
  `EXCLUDE USING gist (institution_id WITH =, document_code WITH =, effective_range WITH &&) WHERE (is_active = TRUE)`

### Table: `pulseassist_conversations`
Tenant-isolated chat sessions.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `institution_id` (`VARCHAR(36)`, NOT NULL, FK `institutions.id`, ondelete `CASCADE`)
  - `user_id` (`VARCHAR(36)`, NOT NULL, FK `users.id`, ondelete `CASCADE`)
  - `title` (`VARCHAR(255)`, NOT NULL, DEFAULT `'Policy Inquiry'`)
  - `created_at`, `updated_at` (`TIMESTAMPTZ`, NOT NULL)

### Table: `pulseassist_messages`
Individual message turns with latency telemetry.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `conversation_id` (`VARCHAR(36)`, NOT NULL, FK `pulseassist_conversations.id`, ondelete `CASCADE`)
  - `role` (`VARCHAR(20)`, NOT NULL) — `user`, `assistant`, `system`
  - `content` (`TEXT`, NOT NULL)
  - `prompt_tokens`, `completion_tokens` (`INTEGER`, NULLABLE)
  - `latency_ms` (`INTEGER`, NULLABLE)
  - `created_at` (`TIMESTAMPTZ`, NOT NULL)

### Table: `pulseassist_citations`
Grounded citation relationships linking answers to source chunks.
* Columns:
  - `id` (`VARCHAR(36)`, PK, UUID)
  - `message_id` (`VARCHAR(36)`, NOT NULL, FK `pulseassist_messages.id`, ondelete `CASCADE`)
  - `chunk_id` (`VARCHAR(36)`, NOT NULL, FK `document_chunks.id`, ondelete `CASCADE`)
  - `document_code` (`VARCHAR(50)`, NOT NULL)
  - `document_title` (`VARCHAR(255)`, NOT NULL)
  - `chunk_index` (`INTEGER`, NOT NULL)
  - `content_snippet` (`TEXT`, NOT NULL)
  - `verified` (`BOOLEAN`, NOT NULL, DEFAULT TRUE)
  - `created_at` (`TIMESTAMPTZ`, NOT NULL)

### Database-Level Triggers & Security Invariants
1. **`trg_protect_document_immutability`**: Prohibits UPDATE of document content or core metadata once status is `PUBLISHED` or `ARCHIVED`.
2. **`trg_protect_knowledge_document_delete`**: Raises exception on direct DELETE of `PUBLISHED` or `ARCHIVED` documents.
3. **`trg_server_control_document_timestamps`**: Automatically stamps `published_at = CURRENT_TIMESTAMP` and `archived_at = CURRENT_TIMESTAMP` at the database level.
4. **`trg_validate_schedule_document_published`**: Requires referenced document to be `PUBLISHED` when adding or updating active schedule records.
5. **`trg_protect_document_version_schedule_delete`**: Rejects direct DELETE on active version schedules.

---

## 10. Migration Workflow


### Applying Migrations
```bash
cd backend
alembic upgrade head
```

### Reverting Last Migration
```bash
cd backend
alembic downgrade -1
```

### Reverting All Migrations
```bash
cd backend
alembic downgrade base
```

### Generating a New Migration
```bash
cd backend
alembic revision --autogenerate -m "describe_change"
```
*Always inspect the auto-generated migration file in `backend/alembic/versions/` before committing.*

