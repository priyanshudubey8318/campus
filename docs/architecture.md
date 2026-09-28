# CampusPulse Architecture Overview

This document outlines the architectural foundation of CampusPulse, establishing domain boundaries, data flow patterns, and subsystem contracts.

## 1. Architectural Philosophy

CampusPulse is designed as a **long-lived modular monolith with service-oriented boundaries**, capable of transitioning into isolated microservices if organizational scale demands it in the future.

### Core Tenets:
1. **Layered Separation of Concerns**:
   - `Presentation Layer`: Next.js App Router, modular UI primitives, typed API clients.
   - `API & Contract Layer`: FastAPI versioned routing (`/api/v1/...`), Pydantic request/response schemas.
   - `Service Layer`: Pure Python business logic; independent of HTTP transport.
   - `Repository Layer`: Data access abstraction over SQLAlchemy ORM.
   - `Data Storage Layer`: PostgreSQL relational database with Alembic migration versioning.
2. **Deterministic Computing Priority**:
   - Quantitative evaluation (percentages, slopes, moving averages, standard deviations, risk metrics, cooldown windows) is executed strictly by deterministic Python algorithms.
   - AI/LLM models are invoked only for natural language summarization, evidence-grounded policy Q&A (RAG), and student draft messaging.
3. **Auditability & Traceability**:
   - Every sensitive institutional event (academic adjustments, complaints, behavioral anomalies, notifications) maintains an append-only audit trail with timestamps, acting users, and contextual evidence.

---

## 2. Planned Domain Modules

The backend architecture is partitioned into explicit bounded contexts under `backend/app/`:

| Domain | Responsibility | Planned Phase |
|---|---|---|
| `core` | Database sessions, settings, structured logging, base models | Phase 0 (Implemented) |
| `identity` | RBAC authentication, JWT sessions, user management | Phase 1 (Implemented) |
| `students` | Student academic profiles, cohorts, demographics | Phase 1/2 (Implemented) |
| `academic` | Attendance, marks, assignment submissions, course management | Phase 2 (Implemented) |
| `pulsewatch` | Deterministic behavioral monitoring, baselines, signals, explainability | Phase 3 (Implemented & Verified) |
| `pulserisk` | Multi-signal support priority scoring, explainability | Phase 4 (Implemented & Verified) |
| `pulseassist` | Policy document RAG retrieval, student Q&A assistant | Phase 5 (Implemented & Verified) |
| `pulsetrecord` | Leave management, authorized complaint & appeal tracking | Phase 6 |
| `pulsecase` | Advisor intervention cases, notes, follow-up workflows | Phase 7 |
| `notifications` | In-app, email, and external delivery pipeline with cooldowns | Phase 3+ |
| `analytics` | Cohort-level aggregates, model fairness, institutional metrics | Phase 8 |

### 2.1 PulseWatch Architecture (Phase 3)
PulseWatch is a deterministic behavioral monitoring subsystem that measures changes in academic engagement relative to each student's personal baseline and available cohort context:
* **Zero Black-Box / Zero LLM**: Strictly deterministic arithmetic in Python; no ML/LLM decision engines.
* **Leakage Prevention**: Baseline window $T_{\text{baseline}} \in [T-M-N, T-N)$ strictly ends before observation window $T_{\text{obs}} \in [T-N, T]$.
* **Exact Thresholds**: $\Delta \ge -5.0\%$ (NORMAL), $[-15.0\%, -5.0\%)$ (MILD_CHANGE), $[-25.0\%, -15.0\%)$ (MODERATE_CHANGE), $<-25.0\%$ (SIGNIFICANT_CHANGE).
* **Earliest Valid Submission**: Evaluates lateness on the earliest eligible attempt ($\min(\text{submitted\_at}) \le \text{due\_date}$).
* **Data Sufficiency & Zero Denominator Guard**: If denominator is 0, returns `NO_DATA` / `null`, never `0.0%`. If records $< 3$, labels `INSUFFICIENT_DATA` with `NORMAL` stability.
* **Deterministic Overrides**: Consecutive absences ($\ge 3 \rightarrow \text{SIGNIFICANT\_CHANGE}$ regardless of percentage delta); formal assessment absence ($\text{is\_absent} == \text{True} \rightarrow \text{SIGNIFICANT\_CHANGE}$).
* **Idempotency**: Repeated evaluations on the same window and algorithm version update the existing record without duplicate events.
* **Non-Punitive Transparency**: Interactive "Why am I seeing this?" explainability drawer providing clear factual context and institutional disclaimers.

### 2.2 PulseRisk Architecture (Phase 4)
PulseRisk is a deterministic multi-signal support prioritization subsystem that computes an actionable, transparent Support Priority Index ($\text{SPI} \in [0, 100]$) and priority tiers to guide timely, compassionate academic advising:
* **Zero Opaque ML / Zero Dropout Predictions**: No black-box ML models, logistic regression dropout scores, or mental health inferences. Prioritization is strictly deterministic and auditable.
* **Zero Metric Duplication**: Never queries raw attendance or assignment tables directly; consumes strictly structured outputs from PulseWatch (`PulseWatchSummaryResponse`, `BehaviorEvent`).
* **Non-Punitive Priority Tiers**:
  - `LOW_PRIORITY`: $\text{SPI} < 30.0$ (Standard pacing; routine advising touchpoints).
  - `MODERATE_PRIORITY`: $30.0 \le \text{SPI} < 50.0$ (Gentle pacing check-in).
  - `ELEVATED_PRIORITY`: $50.0 \le \text{SPI} < 75.0$ (Targeted academic assistance / tutoring coordination).
  - `URGENT_PRIORITY`: $\text{SPI} \ge 75.0$ (Immediate personal advising outreach).
* **Dynamic Weight Renormalization**: Evaluates 4 core dimensions: Attendance ($w_1 = 0.35$), Coursework ($w_2 = 0.30$), Assessments ($w_3 = 0.25$), and Longitudinal Persistence ($w_4 = 0.10$). Valid dimensions $\mathcal{V}$ are dynamically renormalized: $w'_i = \frac{w_i}{\sum_{j \in \mathcal{V}} w_j}$.
* **Data Confidence & Insufficient Data Guard**: Aggregate confidence $\mathcal{C} = \sum_{j \in \mathcal{V}} w_j$. When $\mathcal{C} < 0.35$ and no safety trigger applies, yields `INSUFFICIENT_DATA`, $\text{SPI} = 0.0$, `LOW_PRIORITY`.
* **Safety Floor Precedence Over Low Confidence**: Critical safety triggers ($T_1$: Formal assessment absence floor = 75.0 $\rightarrow$ `URGENT_PRIORITY`; $T_2$: Consecutive absences $\ge 5$ floor = 75.0 $\rightarrow$ `URGENT_PRIORITY`; $T_3$: Consecutive absences $\ge 3$ floor = 50.0 $\rightarrow$ `ELEVATED_PRIORITY`; $T_4$: Missed assignments $\ge 3$ floor = 50.0 $\rightarrow$ `ELEVATED_PRIORITY`; $T_5$: Dual significant PulseWatch shifts floor = 80.0 $\rightarrow$ `URGENT_PRIORITY`) unconditionally override low confidence ($\mathcal{C} < 0.35$) and prevent critical acute needs from being masked as insufficient data. Note: an attendance percentage delta by itself does not activate T2 without the approved trigger.
* **Temporal Deduplication & Half-Life Decay**: Event clustering on $\ge 50\%$ date overlap; canonical events weighted with exponential decay $\lambda = \frac{\ln(2)}{14} \approx 0.04951\text{ day}^{-1}$.
* **Governed Policy Lifecycle**: `DRAFT` $\rightarrow$ `VALIDATED` $\rightarrow$ `ACTIVE` $\rightarrow$ `RETIRED`. At most one active policy per institution scope enforced via PostgreSQL partial unique index.
* **Immutable Snapshot Identity**: `(student_id, evaluation_date, window_days, algorithm_version, policy_version)`.
* **Complete Explainability Decomposition**: Full JSON decomposition detailing every dimension's observed delta, factor score, weight, contribution, safety floors, and primary driver.

### 2.3 PulseAssist Architecture (Phase 5)
PulseAssist is an institution-grounded Retrieval-Augmented Generation (RAG) subsystem providing authoritative policy answers, explainable document retrieval, and verified academic record presentation:
* **Strict Non-Goals**: Zero clinical/mental-health diagnosis; zero calculation of SPI or PulseWatch metrics; zero disciplinary intervention; zero access to Phase 6 leaves/complaints or Phase 7 case notes.
* **Deterministic Hybrid Retrieval**:
  - Dense semantic retrieval: pgvector cosine distance, Top 10 candidates ($d=768$).
  - Sparse lexical retrieval: PostgreSQL `tsvector` with `ts_rank_cd`, Top 10 candidates.
  - Relevance Gate: Dense cosine similarity $\ge 0.65$, Sparse score $> 0.0$.
  - Canonical RRF Fusion: $RRF(c) = (0.7 / (60 + \text{dense\_rank}(c)) \text{ if dense else } 0.0) + (0.3 / (60 + \text{sparse\_rank}(c)) \text{ if sparse else } 0.0)$. Preserves original ranks; missing ranks contribute 0.0. Top 3–5 chunks selected.
* **Database-Enforced Invariants**:
  - Content and metadata immutability on `PUBLISHED` and `ARCHIVED` documents via PostgreSQL trigger `trg_protect_document_immutability`.
  - Database-level delete rejection on `PUBLISHED` and `ARCHIVED` documents via `trg_protect_knowledge_document_delete`.
  - Server-controlled publication and archival timestamps (`CURRENT_TIMESTAMP`).
  - Non-overlapping active versions enforced via PostgreSQL GIST exclusion constraint `ex_document_version_schedules_non_overlapping`.
  - Composite tenant foreign keys `(institution_id, document_code)`.
* **Citation & Numerical Grounding**:
  - Every emitted citation verified against retrieved chunk IDs. Ungrounded citations stripped.
  - Verified personal academic metrics (Attendance %, CGPA, Support Priority Tier) with the mandatory label: `"Verified ground-truth data from registrar/attendance systems. Not an AI estimate."`
  - Safe fallback messaging when no documents match or confidence is below threshold.



---

## 3. Database & Migration Strategy

- **Engine**: PostgreSQL 16 (production and containerized development), SQLite in-memory supported for rapid test suites.
- **ORM**: SQLAlchemy 2.0 with DeclarativeBase and typed column mappings.
- **Schema Management**: Alembic migrations under `backend/alembic/`.
- **Golden Rule**: No manual schema manipulation. Every change must be represented by an auto-generated or reviewed Alembic revision script and verified bidirectionally (`upgrade head` and `downgrade`).

---

## 4. External Integration Contracts

All third-party systems are encapsulated behind abstract Python protocols:
- **LLM Provider**: `LLMClientProtocol` (defaulting to Gemini, configurable to local or alternative providers).
- **Vector Store**: `VectorStoreProtocol` (defaulting to ChromaDB, extensible to pgvector or cloud vector stores).
- **Notification Provider**: `NotificationChannelProtocol` (In-App, SMTP Email, future webhook/SMS).

---

## 5. Security & Access Boundaries

- Least-privilege role-based access control (RBAC): `SUPER_ADMIN`, `ADMIN`, `FACULTY`, `ADVISOR`, `COUNSELOR`, `STUDENT`, `AUTHORIZED_REPORTER`.
- Server-side authorization verification on every data modification.
- Uploaded evidence documents stored in private, signed-access storage, never public URLs.
