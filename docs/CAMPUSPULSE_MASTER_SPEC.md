# CampusPulse — Master Engineering Specification

## Version
v1.0 — Foundation Specification

## Purpose of this document

This document is the authoritative engineering specification for building CampusPulse from scratch with AI coding agents such as OpenAI Codex or Google Antigravity.

It is intentionally written as a **living architecture contract** rather than a one-time coding prompt. The project must be developed in small, verifiable increments so future features can be added without breaking existing functionality.

This document must remain in the repository at:

`/docs/CAMPUSPULSE_MASTER_SPEC.md`

When a design decision changes, update the document, changelog, architecture decision record, tests, and implementation as appropriate. Do not silently diverge from the specification.

---

# 1. Product definition

## Project name

**CampusPulse**

## Product concept

CampusPulse is an AI-assisted student success and institutional support platform. It combines academic activity monitoring, behavioral change detection, explainable support indicators, institution-grounded assistance, student self-service, leave management, complaint/case workflows, and human-reviewed intervention.

The system is designed to move from **reactive reporting** to **proactive, explainable support**.

### Core product loop

```text
Academic / LMS / institutional data
                |
                v
        Data normalization
                |
                v
 Personal baseline + recent trends
                |
                v
       PulseWatch detection
                |
                v
     Context / cause analysis
                |
                v
      Student notification
                |
                v
 Student response / self-report
                |
                v
       Support / intervention
                |
                v
      Re-evaluation over time
                |
       +--------+--------+
       |                 |
       v                 v
    Improved       Persistent pattern
                         |
                         v
                 Human review/case
```

The existing concept specifically calls for trend-based rather than snapshot-based risk analysis, multi-signal fusion, RAG-grounded resources, and tiered actions. CampusPulse extends that design by making proactive behavioral monitoring a first-class subsystem. [Source: prior CampusPulse handoff, trend/risk/RAG/action requirements.]

---

# 2. Primary goals

1. Detect meaningful changes in a student's academic engagement early.
2. Explain what was observed using actual evidence.
3. Search for relevant contextual explanations before escalating.
4. Notify the student first when appropriate.
5. Allow the student to provide context rather than making unsupported assumptions.
6. Provide institution-approved resources through grounded RAG.
7. Escalate persistent or significant cases to authorized humans.
8. Maintain complete auditability.
9. Preserve privacy and role-based access.
10. Make every subsystem replaceable and extensible.
11. Make new features additive whenever possible.
12. Ensure existing functionality is regression-tested before and after changes.

---

# 3. Non-goals and safety boundaries

CampusPulse must not:

- Diagnose mental-health conditions.
- Infer a medical or psychological condition from passive behavioral data.
- Automatically declare a student guilty of misconduct.
- Automatically punish a student.
- Automatically make high-impact disciplinary decisions.
- Treat an unverified complaint as an established fact.
- Reveal another student's private information.
- Invent institutional policies, resources, procedures, or student records.
- Treat missing data as evidence of bad behavior.
- Use an LLM as the authoritative calculator for quantitative scores when deterministic code can calculate them.
- Send repeated notifications for the same event without cooldown/deduplication controls.

The system can detect **academic engagement irregularities** and **support indicators**. It must distinguish observed facts, possible context, student-provided context, and authorized human decisions.

---

# 4. Product modules

CampusPulse must be organized into modular bounded areas.

## 4.1 Identity & Access

- Authentication
- Authorization
- RBAC
- User profiles
- Session management
- Audit logging

## 4.2 Student Profile

- Academic identity
- Program/section/semester
- Contact information subject to access policy
- Relevant institutional records
- Profile timeline

## 4.3 Academic Data

- Attendance
- Marks/assessments
- Assignments
- Submission timestamps
- LMS activity
- Academic calendar

## 4.4 PulseWatch

The proactive behavioral monitoring subsystem.

Responsibilities:

- Personal baseline calculation
- Baseline refresh
- Recent-window trend calculation
- Behavioral event generation
- Anomaly/irregularity detection
- Context lookup
- Cause-analysis evidence collection
- Notification eligibility
- Cooldown/deduplication
- Student response collection
- Re-evaluation

## 4.5 PulseRisk

The broader multi-signal support/risk analysis subsystem.

Responsibilities:

- Combine authorized signals
- Produce explainable scores
- Consider approved leave/context
- Generate support-priority information
- Maintain historical assessments

PulseWatch detects changes; PulseRisk evaluates broader support priority. They must remain separate services/modules.

## 4.6 PulseAssist

- Student-facing chatbot
- Institution-policy RAG
- Resource discovery
- Source citations
- Student self-service
- Resource/appointment workflows where enabled

## 4.7 PulseRecord

- Leave requests/history
- Complaint records
- Evidence metadata
- Review workflow
- Appeals
- Authorized institutional records

Unverified complaints must not automatically become risk signals.

## 4.8 PulseCase

- Advisor cases
- Interventions
- Case notes
- Follow-ups
- Outcomes
- Case closure

## 4.9 Notifications

- In-app notifications
- Email integration
- Optional automation integration
- Templates
- Preferences
- Cooldowns
- Delivery tracking

## 4.10 Analytics & Reporting

- Student trends
- Cohort/section aggregates
- Intervention outcomes
- Model evaluation
- Fairness evaluation
- System health

## 4.11 Administration

- User management
- Roles/permissions
- Policy/resource documents
- Academic configuration
- Notification configuration
- Threshold/configuration management
- Audit review

---

# 5. Roles and access model

Initial roles:

- `SUPER_ADMIN`
- `ADMIN`
- `FACULTY`
- `ADVISOR`
- `COUNSELOR`
- `STUDENT`
- `AUTHORIZED_REPORTER`

Access must be based on **least privilege**.

Frontend restrictions are not sufficient. Every sensitive backend endpoint must enforce authorization server-side.

Every sensitive read/write should answer:

1. Who is requesting the action?
2. What role do they have?
3. What permission is required?
4. Is the requested record within their authorized scope?
5. Should the action be audited?

---

# 6. Core architectural principles

## 6.1 Modular architecture

Do not build the whole application as one giant module.

Each major domain must have its own:

- models
- schemas/types
- service layer
- API/router layer
- validation
- tests
- documentation where needed

## 6.2 Stable contracts

Frontend and backend communicate through explicit typed API contracts.

Do not allow UI components to depend on database internals.

Prefer:

```text
UI -> API client -> API -> service -> repository -> database
```

rather than:

```text
UI -> database directly
```

## 6.3 Domain isolation

A change to complaints must not require rewriting academic analytics.

A change to the chatbot must not modify authentication.

A change to notification templates must not modify risk calculations.

## 6.4 Configuration over hard-coding

Thresholds, cooldowns, weights, notification channels, academic periods, and feature availability should be configurable.

Keep defaults in configuration, not scattered across code.

## 6.5 Additive change by default

When adding a feature:

- add a new module/service when appropriate
- add database migrations instead of editing production schema manually
- add new API endpoints instead of unexpectedly changing old contracts
- preserve existing request/response behavior unless a versioned change is required
- preserve existing routes
- preserve existing database data
- preserve existing UI behavior

## 6.6 Reversible changes

Where practical, new functionality should be protected behind a feature flag/configuration switch until verified.

## 6.7 Deterministic core, AI-assisted presentation

Use deterministic application code for:

- calculations
- thresholds
- comparisons
- timestamps
- permissions
- workflow state transitions
- duplicate prevention
- database writes

Use AI/LLMs for:

- natural-language explanations
- summarization
- grounded question answering
- message drafting
- structured interpretation of supplied evidence

The LLM must not become the hidden source of truth for business rules.

---

# 7. Recommended technology stack

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Component library such as shadcn/ui
- Recharts or equivalent charting library
- React Hook Form
- Zod

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

## Database

- PostgreSQL

## AI/RAG

- Gemini API or another configured LLM provider
- LangChain where it materially helps orchestration/retrieval
- ChromaDB or another vector store appropriate for the scale
- PyPDF and document loaders as required

## Testing

- Pytest for backend
- Playwright for end-to-end flows
- Vitest/Jest where appropriate for frontend logic

## Infrastructure

- Docker Compose for local development
- Environment-based configuration

## Automation

- UiPath may be integrated later as an external action/automation layer.

The architecture must not make UiPath mandatory for normal local development or core application operation.

---

# 8. High-level repository structure

```text
campuspulse/
|
+-- frontend/
|   +-- app/
|   +-- components/
|   +-- features/
|   +-- hooks/
|   +-- lib/
|   +-- types/
|   +-- tests/
|
+-- backend/
|   +-- app/
|       +-- api/
|       +-- core/
|       +-- models/
|       +-- schemas/
|       +-- repositories/
|       +-- services/
|       +-- workflows/
|       +-- agents/
|       |   +-- data_agent/
|       |   +-- behavior_agent/
|       |   +-- risk_agent/
|       |   +-- knowledge_agent/
|       |   +-- coordinator_agent/
|       |   +-- root_cause_agent/
|       +-- rag/
|       +-- notifications/
|       +-- tasks/
|       +-- tests/
|
+-- data/
|   +-- seed/
|   +-- mock/
|   +-- knowledge_base/
|
+-- scripts/
|   +-- generate_mock_data.py
|   +-- seed_database.py
|   +-- evaluate_models.py
|   +-- validate_environment.py
|
+-- docs/
|   +-- CAMPUSPULSE_MASTER_SPEC.md
|   +-- architecture.md
|   +-- api-contracts.md
|   +-- database.md
|   +-- security.md
|   +-- agent-contracts.md
|   +-- adr/
|   +-- changelog.md
|
+-- tests/
|   +-- integration/
|   +-- e2e/
|
+-- docker-compose.yml
+-- .env.example
+-- README.md
+-- CHANGELOG.md
+-- Makefile / task runner configuration
```

The exact framework-specific structure can evolve, but domain boundaries must remain.

---

# 9. PulseWatch behavioral monitoring specification

## 9.1 Supported signals

Initial signals:

- attendance frequency
- consecutive absences
- attendance trend
- LMS login/activity frequency
- incomplete LMS activities
- assignment completion
- assignment lateness
- assessment/marks trend
- approved leave periods
- academic-calendar context
- student self-reported context
- previous intervention state

Future adapters may add other institution-approved signals without changing the PulseWatch interface.

## 9.2 Personal baseline

Baseline must be calculated from the student's historical data over a configurable window.

Store baseline metadata including:

- metric name
- baseline value
- calculation window
- number of observations
- last calculated time
- calculation version

Never assume that a baseline exists when insufficient data is available.

## 9.3 Baseline comparison

Calculate deviations such as:

```text
current_value - baseline_value
```

and, where meaningful:

```text
(current_value - baseline_value) / baseline_value
```

Guard against division by zero and insufficient history.

## 9.4 Trend detection

Use deterministic code for trend analysis.

Initial methods may include:

- rolling average
- rolling difference
- consecutive decline count
- slope over a recent window
- comparison of recent window vs historical window

The implementation should expose a strategy interface so another method can be added later.

## 9.5 Irregularity event

An irregularity is a meaningful deviation from expected behavior based on configured rules and available data.

An event must contain:

```text
id
student_id
event_type
severity
score
detected_at
evidence[]
algorithm_version
status
```

## 9.6 Evidence requirements

Every irregularity must be traceable to raw or normalized data.

Example:

```text
Attendance changed from 91% baseline to 68% current.
LMS activity changed from 6 weekly activities to 1.
Three assignments became overdue.
```

Do not create an anomaly with an unexplained opaque score.

---

# 10. Context and cause analysis

Cause analysis must be evidence-based.

Potential context sources:

- approved leave
- academic calendar
- exam periods
- deadline clusters
- data outage/system outage
- student-provided context
- previous support/intervention record where authorized
- timetable changes

The system may produce:

- confirmed context
- possible context
- no known context
- insufficient data

It must not produce unsupported diagnoses.

### Example output

```json
{
  "observations": [
    "Attendance declined 21 percentage points from baseline",
    "LMS activity declined 75 percent",
    "Three assignments are overdue"
  ],
  "context": [
    {
      "type": "ACADEMIC_DEADLINE_CLUSTER",
      "evidence": "Three deadlines occurred within five days",
      "confidence": "SUPPORTED"
    }
  ],
  "unknowns": [
    "No student self-report available"
  ]
}
```

---

# 11. Student notification engine

Notifications are an intervention system, not simply alerts.

## Levels

### Level 0 — Informational

Example: pending LMS tasks.

### Level 1 — Gentle check-in

Used for small or early changes.

### Level 2 — Support suggestion

Used for persistent multi-signal changes.

### Level 3 — Human review

Used only after configured conditions and human-review rules are satisfied.

## Notification requirements

Every notification must have:

- trigger event
- evidence summary
- template version
- timestamp
- delivery channel
- delivery status
- cooldown key
- optional student response

## Cooldowns

A student must not receive repetitive alerts for the same issue every time a scheduled job runs.

Use a deterministic deduplication key such as:

```text
student_id + anomaly_type + rule_version + time_window
```

---

# 12. Student response / check-in

When a notification permits explanation, the UI should offer structured options and an optional free-text response.

Example:

```text
Is anything affecting your studies?

- I'm doing fine
- Academic workload
- Medical/personal issue
- LMS/technical problem
- Attendance issue
- I need academic support
- Prefer not to say
```

The student must be allowed to skip the check-in unless an institutional policy explicitly says otherwise.

Student-provided context becomes a data point, not an absolute truth for every future decision.

---

# 13. PulseRisk specification

PulseRisk evaluates broader support priority using multiple authorized signals.

Possible components:

- attendance trend
- academic trend
- assignment trend
- LMS activity
- intervention persistence
- context-adjusted observations

Approved leave can explain part of attendance variation. It should not automatically erase unrelated evidence.

Scores must include:

- score
- components
- weights
- version
- evidence
- generated_at

Weights and thresholds must be configurable.

---

# 14. Explainability

Every AI-assisted assessment must be explainable at the evidence level.

The UI should provide a "Why am I seeing this?" flow.

Example:

```text
Why you received this notification

Attendance
91% -> 68%

LMS activity
6 activities/week -> 1

Assignments
95% on-time -> 50%

Context checked
- Approved leave: none found
- Academic deadline cluster: found
- Student check-in: not provided

These observations triggered a support check-in.
```

Do not expose restricted internal data in student explanations.

---

# 15. RAG / PulseAssist specification (Phase 5 Implemented & Verified)

The PulseAssist subsystem provides institution-grounded policy advisory, explainable document retrieval, and verified academic record presentation for campus students and faculty.

## 15.1 Core Subsystem Boundaries & Non-Goals

PulseAssist operates strictly as an institutional policy and informational assistant:
- **Zero Diagnosis**: PulseAssist must NEVER diagnose mental health, offer medical opinions, or interpret psychological well-being.
- **Zero Calculation**: PulseAssist must NEVER calculate or alter SPI scores, behavioral trend metrics, or PulseWatch signals.
- **Zero Direct Intervention**: PulseAssist must NEVER make disciplinary determinations or assign risk tiers.
- **Zero Phase 6/7 Leakage**: PulseAssist must NEVER access unapproved leave applications, active complaint/appeal records (Phase 6), or confidential counselor/advisor intervention case notes (Phase 7).

## 15.2 Hybrid Retrieval & Reciprocal Rank Fusion (RRF)

PulseAssist implements deterministic hybrid search combining dense semantic vector retrieval (pgvector cosine distance) and sparse lexical search (PostgreSQL `tsvector` with `ts_rank_cd`):

### 1. Dual Retrieval Lists
- **Dense Retrieval**: Retrieves top 10 candidates by cosine distance ($1 - \text{cosine\_similarity}$) using embedding dimension 768.
- **Sparse Retrieval**: Retrieves top 10 candidates by full-text search rank using English stemming and document dictionary.

### 2. Relevance Gate
Candidates are filtered against a relevance threshold before final selection:
- Dense candidates: $\text{cosine\_similarity} \ge 0.65$.
- Sparse candidates: $\text{sparse\_score} > 0.0$.
- *Invariant*: The relevance gate removes candidates but preserves their original 1-based ranks. Missing dense or sparse candidates contribute $0.0$ to the rank component.

### 3. Canonical RRF Formula
$$RRF(c) = \left(\frac{0.7}{60 + \text{dense\_rank}(c)} \text{ if dense\_rank } \neq \text{None else } 0.0\right) + \left(\frac{0.3}{60 + \text{sparse\_rank}(c)} \text{ if sparse\_rank } \neq \text{None else } 0.0\right)$$

- Top 3 to 5 chunks by $RRF(c)$ score are passed into the AI generation and citation verification pipeline.

## 15.3 Database Architecture & Immutability Triggers

Migration `0007_pulseassist_rag_knowledge.py` establishes the knowledge repository schema:

### 1. Relational Entities
- `knowledge_documents`: Authoritative policy documents with status (`DRAFT`, `PUBLISHED`, `ARCHIVED`), composite tenant key `(institution_id, document_code)`, and version tracking.
- `document_chunks`: Semantic chunks (~1800 character target with section header preservation) with `embedding vector(768)` and full-text `tsv_content tsvector`.
- `document_version_schedules`: Decoupled timeline scheduling with `effective_from`, `effective_to`, `effective_range daterange`, and `is_active boolean`.
- `pulseassist_conversations`: Student and institutional chat threads with tenant isolation.
- `pulseassist_messages`: Individual dialogue turns with role (`user`, `assistant`, `system`) and latency telemetry.
- `pulseassist_citations`: Grounded citation links binding assistant responses to exact source chunks.

### 2. Database-Level Triggers & Guarantees
- **`trg_protect_document_immutability`**: Prohibits any SQL update to content, title, document_code, category, or audience once status is `PUBLISHED` or `ARCHIVED`.
- **`trg_protect_knowledge_document_delete`**: Rejects direct SQL delete operations on `PUBLISHED` or `ARCHIVED` documents.
- **`trg_server_control_document_timestamps`**: Server-controlled `published_at` and `archived_at` timestamps using `CURRENT_TIMESTAMP`.
- **`ex_document_version_schedules_non_overlapping`**: PostgreSQL GIST exclusion constraint enforcing non-overlapping active date ranges:
  `EXCLUDE USING gist (institution_id WITH =, document_code WITH =, effective_range WITH &&) WHERE (is_active = TRUE)`

## 15.4 Grounding & Ground Truth Verification

1. **Citation Verification**: Every citation emitted in an AI response is verified against the retrieved chunk IDs. Citations referencing non-retrieved or non-existent chunks are stripped.
2. **Ground Truth Academic Metrics Card**: When students ask about personal attendance, CGPA, or standing, verified metrics are queried directly from registrar tables and rendered with the mandatory disclaimer:
   > *"Verified ground-truth data from registrar/attendance systems. Not an AI estimate."*
3. **No-Match Fallback**: If no relevant documents exceed the retrieval threshold, PulseAssist responds safely with an institutional disclaimer without hallucinating policies.


---

# 16. Complaint module

Complaint workflow:

```text
SUBMITTED
   -> UNDER_REVIEW
   -> NEEDS_INFORMATION (optional)
   -> VERIFIED / DISMISSED / OTHER AUTHORIZED OUTCOME
   -> CONTESTED / APPEALED where applicable
   -> RESOLVED
   -> CLOSED
```

Required capabilities:

- authorized reporter submission
- evidence upload
- reviewer assignment
- review notes
- student response where policy permits
- appeal workflow
- access control
- audit trail

Unverified complaints must not be treated as proven facts.

Evidence storage must be private and access-controlled.

---

# 17. Leave management

Support:

- leave application
- document upload
- status tracking
- approval/rejection
- leave history
- reviewer audit trail

Leave data can be consumed by PulseWatch/PulseRisk only through a defined service contract.

Avoid direct database coupling between analytics and leave tables.

---

# 18. Case management

Case lifecycle:

```text
OPEN
 -> IN_PROGRESS
 -> WAITING_FOR_STUDENT / FOLLOW_UP_SCHEDULED
 -> RESOLVED
 -> CLOSED
```

Cases contain:

- reason
- evidence references
- assigned advisor
- interventions
- notes
- follow-ups
- outcome
- audit information

---

# 19. Database design principles

Use PostgreSQL and migrations.

Every schema change must have an Alembic migration.

Never instruct the coding agent to "just modify the database manually" for a tracked project.

Important entities include:

```text
users
roles
permissions
students
faculty
academic_terms
courses
enrollments
attendance
assessments
marks
assignments
submissions
lms_events
behavior_baselines
behavior_events
behavior_anomalies
cause_analyses
student_checkins
notifications
notification_deliveries
risk_assessments
leave_requests
leave_documents
complaints
complaint_evidence
complaint_reviews
appeals
support_cases
case_notes
interventions
followups
knowledge_documents
document_chunks
audit_logs
feature_flags
configuration_versions
```

The exact relational structure can evolve during implementation after an explicit architecture review.

---

# 20. API design rules

API endpoints must be versioned from the beginning.

Example:

```text
/api/v1/auth/...
/api/v1/students/...
/api/v1/attendance/...
/api/v1/pulsewatch/...
/api/v1/pulserisk/...
/api/v1/pulseassist/...
/api/v1/complaints/...
/api/v1/leaves/...
/api/v1/cases/...
/api/v1/notifications/...
```

Do not break an existing API contract silently.

For breaking changes:

1. Introduce a new endpoint/version.
2. Preserve the previous endpoint during migration.
3. Add migration notes.
4. Update tests.
5. Deprecate deliberately.

---

# 21. Background processing

Long-running work should not block normal API requests.

Suitable background tasks:

- baseline refresh
- behavior scans
- notification generation
- email delivery
- document indexing
- report generation
- scheduled follow-ups

Every job must be:

- idempotent where possible
- retry-safe
- observable
- logged

A repeated job must not generate duplicate notifications or duplicate database records.

---

# 22. Scheduled PulseWatch scan

The initial scheduled workflow should look like:

```text
Scheduler
   |
   v
Load active students
   |
   v
Load latest normalized data
   |
   v
Update baseline if due
   |
   v
Calculate recent trends
   |
   v
Run anomaly rules
   |
   v
Deduplicate/cooldown
   |
   v
Collect context
   |
   v
Create anomaly record
   |
   v
Generate student notification if eligible
   |
   v
Log everything
```

The scan must be safe to run repeatedly.

---

# 23. AI agent contracts

Each AI agent must have a defined contract.

## Data Agent

Input: normalized institutional records.

Output: validated metrics/trends.

Constraint: no unsupported inference.

## Behavior Agent

Input: metrics + baselines + configuration.

Output: anomaly candidates + evidence.

Constraint: deterministic rules/algorithms should perform quantitative detection.

## Risk Agent

Input: authorized signals + context.

Output: explainable support-priority assessment.

Constraint: configurable weights, evidence, versioning.

## Knowledge Agent

Input: student question + authorized retrieved chunks.

Output: grounded answer + citations.

Constraint: no unsupported institutional claims.

## Coordinator Agent

Input: validated events and workflow state.

Output: authorized next workflow action.

Constraint: must respect permissions and human-review boundaries.

## Root Cause Agent

Input: anomaly evidence + institutional context.

Output: possible context categories with evidence.

Constraint: never convert possibilities into diagnosis/certainty without evidence.

---

# 24. Observability and auditability

The system must make it possible to answer:

- What happened?
- When did it happen?
- Which rule/version detected it?
- What data supported it?
- Which AI model/prompt version was used, if any?
- What notification was generated?
- Was it delivered?
- What did the student respond?
- Who reviewed the case?
- What changed afterward?

Important logs:

- authentication events
- authorization failures
- data imports
- anomaly detections
- risk assessments
- notification generation/delivery
- complaint access
- evidence access
- case changes
- configuration changes
- AI request metadata where appropriate and privacy-safe

Never log passwords, API keys, access tokens, or sensitive document contents unnecessarily.

---

# 25. Testing strategy

Testing is a release requirement, not an optional cleanup step.

## Unit tests

Test:

- baseline calculations
- trend algorithms
- score calculations
- leave-aware adjustments
- cooldown logic
- deduplication
- permission checks
- validation

## Integration tests

Test:

- database interactions
- API contracts
- authentication/authorization
- notification pipeline
- RAG retrieval
- file uploads

## End-to-end tests

At minimum:

1. Student login -> dashboard.
2. Faculty updates attendance -> student data changes.
3. PulseWatch detects a configured anomaly.
4. Notification is generated once.
5. Student opens notification.
6. Student submits context.
7. Case/escalation occurs only when configured.
8. Admin can review authorized complaint.
9. Student can submit leave.
10. RAG chatbot answers from an indexed policy and cites the source.

## Regression testing

Before every feature merge:

- run previous tests
- run new tests
- run type checks/lint
- run migration validation
- verify API contracts
- verify critical user journeys

---

# 26. Acceptance criteria

A feature is not "complete" merely because the page exists.

A feature is complete only when:

1. Backend logic exists.
2. Database schema/migration exists where required.
3. API exists and is authorized.
4. Frontend is connected to the real API.
5. Loading/error/empty states work.
6. Validation exists.
7. Tests exist.
8. Existing tests still pass.
9. Audit logging is implemented where needed.
10. Documentation is updated.
11. Manual verification has been performed.
12. No known regression remains unresolved.

---

# 27. Mandatory AI coding-agent operating contract

This section is to be given directly to Codex or Antigravity at the start of the project.

## MASTER AGENT INSTRUCTION

You are the primary engineering agent for CampusPulse.

You are not authorized to treat each user request as an isolated coding task.
You must preserve the existing architecture, functionality, security model, API contracts, migrations, tests, and documentation.

### Before changing code

Always inspect the current repository state first.

At minimum inspect:

- README
- project specification
- git status
- recent git history
- package/dependency manifests
- environment/configuration
- frontend structure
- backend structure
- database migrations
- relevant tests
- relevant existing implementation

If a requested feature may interact with existing functionality, inspect that functionality before modifying it.

### Before implementing a requested feature

Produce a concise "change impact report" internally or in the task response containing:

```text
Current implementation found:
Files/modules affected:
Existing contracts affected:
Database impact:
API impact:
Frontend impact:
Tests currently covering this area:
Potential regression risks:
Implementation approach:
```

If the user says to skip checking previous work, do NOT skip it when doing so could cause regression.

### Never do these things

- Do not delete functioning code just to simplify implementation.
- Do not rewrite an entire module when a targeted extension is sufficient.
- Do not replace the database schema without a migration plan.
- Do not change authentication behavior without reviewing every dependent flow.
- Do not remove tests because they fail after a change.
- Do not hide errors by disabling validation.
- Do not silently change API response shapes.
- Do not commit secrets.
- Do not invent unimplemented features in documentation and present them as complete.
- Do not mark a feature complete merely because the UI renders.
- Do not make destructive changes without explicit justification.

### When a previous implementation is unclear

Ask the existing coding agent/tooling to inspect and report what is already implemented before modifying it.

If necessary, use commands/searches to determine:

- existing routes
- existing components
- existing services
- existing migrations
- existing environment variables
- existing tests
- existing feature flags

### When implementing a new feature

Prefer this sequence:

```text
1. Understand current architecture
2. Identify extension points
3. Add/modify domain model
4. Add migration
5. Add backend service
6. Add API contract
7. Add tests
8. Add frontend integration
9. Add UI tests where appropriate
10. Update docs
11. Run complete verification
12. Report exactly what changed
```

### Backward compatibility rule

Every new feature must be designed so existing features continue to work.

Use:

- additive database changes
- feature flags
- versioned APIs
- adapter interfaces
- dependency inversion
- service boundaries
- migration scripts
- regression tests

where appropriate.

### Verification rule

Never say "done" without verification.

At the end of every substantial task, report:

```text
IMPLEMENTED
- ...

VERIFIED
- Tests run: ...
- Build/typecheck: ...
- Database migration: ...
- Critical manual checks: ...

CHANGED
- file/path
- file/path

NOT CHANGED
- important unaffected areas

KNOWN LIMITATIONS
- ...

NEXT SAFE EXTENSION POINT
- ...
```

If something could not be verified, explicitly say so.

### Dependency rule

Before adding a package:

1. Check whether an existing dependency already solves the need.
2. Check compatibility with the current versions.
3. Add the smallest necessary dependency.
4. Update lockfiles correctly.
5. Verify the build/tests afterward.

### Database rule

Never alter tracked schema manually without recording the migration.

Every schema change requires:

- migration
- model/schema update
- tests where appropriate
- migration verification

### API rule

Preserve existing API contracts.

If a breaking change is genuinely required:

- explain why
- version the endpoint/contract
- preserve old behavior during migration where feasible
- update consumers and tests

### UI rule

Do not break existing routes or responsive behavior.

Every significant UI feature must handle:

- loading
- success
- empty
- error
- unauthorized
- mobile/responsive states

### AI rule

AI-generated outputs must be grounded in available evidence.

Never allow an LLM to bypass:

- authorization
- database constraints
- business rules
- validation
- audit requirements

### Security rule

Treat all uploaded evidence and student records as sensitive.

Validate:

- authentication
- authorization
- file types
- file sizes
- input validation
- access scope

Do not expose private storage through public URLs unless explicitly intended and secured.

---

# 28. Feature request protocol for future development

When the user asks for a future feature, do not immediately start coding.

First perform:

### Step 1 — Existing-state inspection

Identify the current implementation related to the feature.

### Step 2 — Impact analysis

Determine whether it affects:

- database
- API
- frontend
- background jobs
- AI agents
- notifications
- authentication
- permissions
- existing workflows

### Step 3 — Compatibility design

Decide how to add the feature without breaking existing functionality.

### Step 4 — Implementation

Implement the smallest coherent change.

### Step 5 — Verification

Run targeted tests plus regression checks.

### Step 6 — Documentation

Update:

- master specification if architecture changed
- API docs if API changed
- database docs if schema changed
- changelog
- README when setup changes
- ADR for meaningful architecture decisions

---

# 29. Architecture Decision Records

Create an ADR when a decision significantly affects future development.

Examples:

- PostgreSQL vs another database
- RAG vector store selection
- event-driven architecture
- baseline algorithm
- authentication architecture
- notification queue architecture
- multi-agent orchestration framework

ADR format:

```text
Title
Status
Date
Context
Decision
Alternatives considered
Consequences
Migration/rollback plan
```

This prevents future agents from accidentally undoing important architectural decisions.

---

# 30. Changelog policy

Maintain `/docs/changelog.md` and root `CHANGELOG.md` where useful.

Every meaningful feature should record:

- date
- feature
- affected modules
- migration
- verification
- compatibility notes

Example:

```text
2026-09-17
Added PulseWatch baseline monitoring.
Added behavior_anomalies migration.
Added notification cooldown.
Regression suite: PASS.
Existing authentication and dashboard flows unchanged.
```

---

# 31. Feature flags

Features that are incomplete, experimental, expensive, or risky should be controlled through feature flags.

Example:

```text
FEATURE_PULSEWATCH=true
FEATURE_STUDENT_CHECKIN=true
FEATURE_ADVANCED_ROOT_CAUSE=false
FEATURE_UIPATH_AUTOMATION=false
```

A feature flag must not become a permanent substitute for proper architecture. Remove obsolete flags after stabilization.

---

# 32. Mock-data strategy

Mock data must be deterministic when running tests.

Use a seed.

Required scenarios:

1. stable student
2. gradual attendance decline
3. sudden LMS inactivity
4. missed assignments
5. multi-signal decline
6. leave-explained attendance dip
7. missing/incomplete data
8. student recovery after intervention
9. complaint pending review
10. complaint resolved/appealed according to workflow

The mock generator must allow generating a reproducible dataset for demos and tests.

---

# 33. Demo scenario

The primary end-to-end demonstration should be:

```text
Student begins semester normally
        |
        v
Behavior baseline established
        |
        v
Attendance starts dropping
        |
        v
LMS activity decreases
        |
        v
Assignments become overdue
        |
        v
PulseWatch detects deviation
        |
        v
Context checked
        |
        v
Student receives supportive notification
        |
        v
Student explains situation
        |
        v
CampusPulse recommends relevant resources
        |
        v
Pattern continues OR improves
       / \
      /   \
 improved  persistent
    /          \
resolve       advisor case
```

This should be reproducible from seeded demo data.

---

# 34. Development phases

## Phase 0 — Repository and architecture foundation

- repository setup
- documentation
- environment setup
- CI/basic checks
- frontend shell
- backend shell
- database connection
- migration system
- health endpoint
- baseline test setup

## Phase 1 — Identity and student foundation

- auth
- roles
- users
- student profiles
- authorization middleware

## Phase 2 — Academic data

- courses
- enrollment
- attendance
- assessments
- assignments
- LMS events
- calendar

## Phase 3 — PulseWatch

- baseline service
- event normalization
- trend engine
- anomaly engine
- context engine
- notification engine
- cooldown/deduplication
- student check-in

## Phase 4 — PulseRisk

- multi-signal score
- explainability
- history
- evaluation

## Phase 5 — PulseAssist

- document management
- indexing
- retrieval
- chatbot
- citations
- access control

## Phase 6 — PulseRecord

- leave
- complaints
- evidence
- review
- appeals

## Phase 7 — PulseCase

- advisor cases
- interventions
- follow-up
- outcomes

## Phase 8 — Advanced capabilities

- root-cause analysis
- cohort comparisons
- fairness evaluation
- UiPath
- additional integrations

Never skip foundational verification to jump directly to advanced AI features.

---

# 35. Definition of Done for the entire project

CampusPulse is ready for a serious college demonstration only when:

- application starts reliably
- environment setup is documented
- authentication works
- role access works
- student profile works
- academic data works
- PulseWatch detects seeded patterns
- student notifications work
- duplicate notifications are controlled
- student response works
- PulseRisk produces explainable output
- chatbot answers from institutional documents
- complaint workflow is protected by authorization
- leave workflow works
- case workflow works
- audit logging works
- tests pass
- migrations are reproducible
- the demo dataset is reproducible
- no known critical regression remains

---

# 36. First instruction to Codex / Antigravity

Paste the following as the first project instruction:

```text
You are the lead software engineer for a new project called CampusPulse.

Read /docs/CAMPUSPULSE_MASTER_SPEC.md completely before writing code.

Do not implement the entire project in one pass.

First inspect the current repository. If the repository is empty, confirm that it is empty and start from the architecture described in the specification. If files already exist, do not overwrite or restructure them blindly.

Before making changes, report:
- repository state
- current tech stack detected
- existing modules
- existing database/migrations
- existing API routes
- existing frontend routes/components
- existing tests
- environment/configuration
- anything inconsistent with the master specification

Then create a Phase 0 implementation plan.

For Phase 0, build only the development foundation:
- repository structure
- frontend shell
- backend shell
- PostgreSQL connection
- Alembic migrations
- environment configuration
- health endpoint
- basic logging
- basic automated test setup
- lint/typecheck/build commands
- documentation placeholders

Do not build PulseWatch, complaints, chatbot, risk scoring, or advanced features yet.

After implementation, run the available verification commands and report exact results.

Do not claim completion if verification fails.

Do not delete functioning code merely to simplify the implementation.

Do not add unnecessary dependencies.

Do not commit secrets.

Do not create fake implementations hidden behind successful-looking UI.

The architecture must allow future modules to be added without breaking existing functionality.

At the end, provide:
IMPLEMENTED
VERIFIED
CHANGED
NOT CHANGED
KNOWN LIMITATIONS
NEXT SAFE EXTENSION POINT
```

---

# 37. How future instructions from the project owner should be handled

The project owner may later say things like:

> Add a student chatbot.

or:

> Add WhatsApp notifications.

or:

> Add biometric attendance.

The agent must not immediately modify unrelated code.

It must first inspect the current implementation and identify extension points.

For every request, preserve the existing working system unless a change is explicitly required by the new feature.

If the feature conflicts with the architecture, propose the smallest safe architectural adjustment and document it before implementation.

---

# 38. Project-owner communication contract

The project owner will use this specification as the source of truth.

Future instructions may be given conversationally. The agent must translate them into engineering tasks without losing the constraints in this document.

When requirements are ambiguous but implementation can proceed safely, use conservative assumptions and document them.

When requirements would cause destructive changes, security problems, data loss, or breaking API changes, stop the change and explain the impact before proceeding.

When a future feature can be implemented through an adapter, service, interface, or feature flag instead of modifying a stable core, prefer that architecture.

---

# 39. Final engineering principle

CampusPulse must grow like a real software product, not like a sequence of disconnected AI-generated demos.

The desired evolution is:

```text
Stable foundation
      -> modular feature
      -> tests
      -> verified integration
      -> documented contract
      -> next feature
```

not:

```text
feature request
      -> rewrite existing code
      -> broken feature
      -> patch
      -> another rewrite
```

Every future implementation decision should optimize for:

**correctness + maintainability + security + explainability + backward compatibility + extensibility.**
