# ADR-003: Deterministic Computing Core with AI-Assisted Presentation

## Status
Accepted

## Date
2026-09-17

## Context
Educational platforms face strict regulatory, ethical, and fairness requirements. If an AI or LLM is permitted to determine quantitative metrics (attendance percentage, baseline deviation, risk scores, disciplinary thresholds), the system becomes non-deterministic, untestable, unexplainable, and prone to hallucinations.

## Decision
We enforce a strict separation of concerns:
1. **Deterministic Core**: All metrics, statistics, moving averages, baseline comparisons, risk calculations, cooldown windows, and permissions are computed exclusively by deterministic Python code.
2. **AI Presentation & RAG Layer**: AI models (e.g. Gemini) are used strictly for natural-language explanations of observed facts, case summaries, supportive student drafting, and grounded retrieval-augmented generation (RAG) referencing official institutional policy documents.
3. **Provider Decoupling**: AI integrations are isolated behind abstract service protocols so underlying LLMs or vector stores can be replaced without rewriting core application logic.

## Alternatives Considered
- **Prompt-Based Risk Scoring**: Passing student records to an LLM to "predict risk score from 1-100". Rejected as unreliable, non-reproducible, unexplainable, and ethically impermissible for academic interventions.
- **Purely Rule-Based Platform (No AI)**: Misses the capability to synthesize complex policy documentation for students (RAG) and provide clear, empathetic explanations for why support is recommended.

## Consequences
- Guaranteed auditability and mathematical reproducibility.
- Clear legal and compliance posture for higher education institutions.
- AI service latency or provider outages cannot break core tracking or reporting features.
