# ADR-001: Frontend and Backend Technology Stack Selection

## Status
Accepted

## Date
2026-09-17

## Context
CampusPulse requires a modern, production-grade web application architecture that provides a responsive user experience for students, faculty, and administrators, alongside a high-performance, strictly typed backend capable of executing data normalization and analytics. The system must support long-term extensibility without architectural rewrites.

## Decision
We select:
- **Frontend**: Next.js (App Router), TypeScript, and Tailwind CSS.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, and SQLAlchemy 2.0.

## Alternatives Considered
- **Single Page Application (React + Vite)**: Simpler to configure initially, but lacks built-in server-side rendering, unified SEO/metadata capabilities, and App Router layout conventions needed for role-specific portals.
- **Django / Django REST Framework**: Offers rapid admin scaffolding, but introduces monolithic coupling, slower async API performance, and heavier ORM abstractions compared to FastAPI and SQLAlchemy 2.0.
- **Node.js (NestJS / Express)**: Excellent for I/O bound tasks, but Python is required for deep scientific data analysis, statistical trend computation, and future LLM/AI integration ecosystems.

## Consequences
- Fast API execution with automatic OpenAPI documentation (`/docs`).
- Strong typing end-to-end (TypeScript on frontend, Pydantic on backend).
- Shared component design using Tailwind CSS and reusable UI primitives.
- Requires maintaining two runtimes (Node.js and Python) in development and CI environments.
