# CampusPulse — AI Agent Architecture & Subsystem Contracts

This document specifies the planned AI Agent boundaries, interfaces, and safety constraints for CampusPulse.

> [!IMPORTANT]
> **Phase 0 Status**: AI agents are **NOT implemented in Phase 0**. This document defines the architectural boundaries and contracts that future agent implementations must strictly adhere to.

---

## 1. The Cardinal Rule of AI in CampusPulse

**AI/LLM models must NEVER be the source of truth for deterministic calculations.**

All quantitative evaluations must be performed by deterministic Python application logic:
* Attendance percentages and consecutive absence counts
* Moving averages, slopes, and trend calculations
* Baseline deviations and statistical metrics
* Risk scores and weight adjustments
* Cooldown windows and deduplication timestamps
* Role-based permissions and access gates

The AI layer is strictly confined to:
* Grounded natural language explanations of observed facts
* Summarization of case histories
* Policy document question answering with verbatim citations (RAG)
* Drafting supportive check-in messages for student outreach

---

## 2. Planned Agent Contracts (Phase 3+)

### 2.1 Data Agent
* **Role**: Ingests, normalizes, and validates institutional academic telemetry.
* **Input**: LMS events, attendance records, assignment logs.
* **Output**: Validated metric summaries and time-series vectors.
* **Constraint**: Pure deterministic normalization; no unsupported data inferences.

### 2.2 Behavior Subsystem (PulseWatch Core — Implemented in Phase 3)
* **Status**: Implemented in Phase 3 as pure deterministic Python domain services (`PulseWatchCalculationService`, `PulseWatchEventService`).
* **Role**: Identifies meaningful engagement shifts relative to a student's personal historical baseline and cohort context.
* **Input**: Historical personal baselines (attendance, coursework on-time rate, assessment scores), current observation window records, cohort context.
* **Output**: Deterministic engagement summary (`NORMAL`, `MILD_CHANGE`, `MODERATE_CHANGE`, `SIGNIFICANT_CHANGE`), granular `SignalEvidence`, transparent `Explainability` breakdown.
* **Core Principles Enforced**:
  - Pure deterministic calculations (no black-box scoring or LLM decision-making).
  - Strict baseline leakage prevention: $T_{\text{baseline\_end}} < T_{\text{observation\_start}}$.
  - Read-only summary endpoint (`GET /summary` has zero database writes).
  - Strict event persistence idempotency on `(student_id, observation_window_days, window_start_date, window_end_date, algorithm_version)`.
  - Non-punitive transparency: "Why am I seeing this?" explainability modal accessible to students.
* **Constraint**: Pure factual arithmetic; zero dropout prediction, mental-health inference, or disciplinary scoring.

### 2.3 Risk Agent (PulseRisk Core)
* **Role**: Evaluates multi-signal support priority for institutional advisors.
* **Input**: Aggregated academic trends, verified leave records, student responses.
* **Output**: Explainable support priority indicator and component weights.
* **Constraint**: Configurable weights and deterministic scoring. Approved leave periods explain rather than erase signals.

### 2.4 Knowledge Agent (PulseAssist / RAG)
* **Role**: Answers student institutional inquiries grounded in official documents.
* **Input**: Student query + retrieved chunks from verified institutional policies.
* **Output**: Factual answer with document title and page/section citations.
* **Constraint**: Zero hallucination policy. If no matching policy chunk is found, return standard fallback referral message. Never access unauthorized student data.

### 2.5 Coordinator Agent
* **Role**: Orchestrates workflow handoffs between subsystems (e.g. anomaly -> check-in -> case escalation).
* **Input**: Anomaly event state, cooldown records, student response.
* **Output**: Next authorized workflow step (e.g. Schedule check-in, Alert advisor).
* **Constraint**: Must enforce server-side permissions and human-in-the-loop review boundaries for any disciplinary action.

### 2.6 Root Cause Agent
* **Role**: Correlates behavioral anomalies with broader institutional context.
* **Input**: Anomaly evidence + institutional calendar (exam schedules, deadline clusters, university outages).
* **Output**: Identified context categories labeled as "Confirmed Context", "Possible Context", or "No Known Context".
* **Constraint**: Never diagnose medical, psychological, or disciplinary conditions.
