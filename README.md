# CampusPulse

CampusPulse is an enterprise-grade, AI-assisted student success and institutional support platform built for higher education institutions. It provides academic engagement monitoring, behavioral change detection, explainable support indicators, student self-service, case management, and human-reviewed intervention.

> **Master Specification**: The complete architectural and engineering contract is defined in [`docs/CAMPUSPULSE_MASTER_SPEC.md`](docs/CAMPUSPULSE_MASTER_SPEC.md).

---

## Architectural Principles

1. **Modular Domain Boundaries**: Domain modules (`identity`, `students`, `academic`, `pulsewatch`, `pulserisk`, `pulseassist`, `pulsetrecord`, `pulsecase`, `notifications`) are isolated with explicit service and repository layers.
2. **Deterministic Core**: All quantitative calculations, attendance metrics, trends, baseline deviations, and risk indicators are executed by deterministic Python backend code. AI/LLM layers are strictly reserved for grounded explanations, summaries, and conversational assistance.
3. **Migration-Driven Database**: Schema changes are managed via Alembic migrations. Manual database mutations are prohibited.
4. **Versioned API**: REST APIs are explicitly versioned (e.g. `/api/v1/...`).
5. **Provider Agnostic**: External AI and vector store providers (e.g. Gemini, ChromaDB) are decoupled behind replaceable service interfaces.

---

## Repository Structure

```text
CampusPulse/
├── docs/
│   ├── CAMPUSPULSE_MASTER_SPEC.md   # Authoritative architectural specification
│   └── architecture.md              # Domain and subsystem documentation
├── backend/
│   ├── app/
│   │   ├── api/                     # Versioned routers & endpoints
│   │   ├── core/                    # Configuration, DB session, logging
│   │   ├── models/                  # SQLAlchemy declarative models
│   │   ├── repositories/            # Data access layer
│   │   ├── schemas/                 # Pydantic validation models
│   │   └── services/                # Business logic services
│   ├── alembic/                     # Database migrations
│   ├── tests/                       # Automated Pytest suite
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router
│   │   ├── components/              # UI primitives & layout shell
│   │   ├── lib/                     # Typed API client & utilities
│   │   └── types/                   # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   └── validate_environment.py      # Runtime and config verification
├── docker-compose.yml               # Multi-container orchestration
├── .env.example                     # Environment template
└── README.md
```

---

## Getting Started

### Prerequisites
- **Python**: 3.11+ (Python 3.14 compatible)
- **Node.js**: 20+ (Node.js 24 compatible) with `npm`
- **Docker & Docker Compose**: Optional for containerized workflow
- **PostgreSQL**: 15+ (or Docker)

### 1. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# Authoritative installation from pyproject.toml:
pip install -e ".[dev]"
# Or using the generated requirements.txt fallback:
# pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run tests (runs unit tests, safety guard checks, and integration tests against TEST_DATABASE_URL)
pytest tests/ -v

# Start development server
uvicorn app.main:app --reload --port 8000
```

The backend will be accessible at `http://localhost:8000`. API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend
npm install

# Run typecheck
npm run typecheck

# Run development server
npm run dev
```

The frontend application will be accessible at `http://localhost:3000`.

### 4. Running with Docker Compose

```bash
docker compose up -d --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Health: `http://localhost:8000/api/v1/health`
- PostgreSQL: `localhost:5432`

---

## Documentation Index

- [`docs/CAMPUSPULSE_MASTER_SPEC.md`](docs/CAMPUSPULSE_MASTER_SPEC.md) — Authoritative Master Engineering Specification
- [`docs/architecture.md`](docs/architecture.md) — System Architecture Overview
- [`docs/api-contracts.md`](docs/api-contracts.md) — API Contract Specifications (v1)
- [`docs/database.md`](docs/database.md) — Database Configuration, Models & Migration Guide
- [`docs/security.md`](docs/security.md) — Security Architecture & Baseline Controls
- [`docs/agent-contracts.md`](docs/agent-contracts.md) — AI Agent Subsystem Contracts & Constraints
- [`docs/changelog.md`](docs/changelog.md) — Project Changelog & Migration History
- [`docs/adr/`](docs/adr/) — Architecture Decision Records (ADR-001 through ADR-004)

---

## Verification & Quality Commands

| Task | Command |
|---|---|
| Environment Validation | `python scripts/validate_environment.py` |
| Backend Tests | `cd backend && pytest tests/ -v` |
| Database Migration (Upgrade) | `cd backend && alembic upgrade head` |
| Database Migration (Downgrade) | `cd backend && alembic downgrade -1` |
| Frontend Typecheck | `cd frontend && npm run typecheck` |
| Frontend Lint | `cd frontend && npm run lint` |
| Frontend Build | `cd frontend && npm run build` |
| Frontend Smoke Tests | `cd frontend && npm run test:smoke` |

---

## Roadmap

- [x] **Phase 0**: Architecture & Foundation (Repository, Next.js shell, FastAPI shell, PostgreSQL/Alembic, automated tests)
- [ ] **Phase 1**: Identity & Student Foundation (RBAC, JWT, profiles)
- [ ] **Phase 2**: Academic Data Subsystem (Attendance, marks, assignments, LMS events)
- [ ] **Phase 3**: PulseWatch Subsystem (Baselines, trend analysis, anomaly detection, cooldowns)
- [ ] **Phase 4**: PulseRisk Subsystem (Multi-signal scoring, explainability)
- [ ] **Phase 5**: PulseAssist Subsystem (Institution policy RAG, chatbot)
- [ ] **Phase 6**: PulseRecord Subsystem (Leave & complaint workflows)
- [ ] **Phase 7**: PulseCase Subsystem (Advisor interventions, case management)
- [ ] **Phase 8**: Advanced Analytics & Automation
