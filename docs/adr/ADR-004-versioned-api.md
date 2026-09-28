# ADR-004: Explicit API Versioning Strategy

## Status
Accepted

## Date
2026-09-17

## Context
CampusPulse will evolve over multiple development phases, integrating new client applications (web portals, mobile apps, LMS webhooks, and institutional notification endpoints). Unversioned endpoints lead to breaking changes that disrupt active clients.

## Decision
All backend API routes must be explicitly versioned from the initial foundation:
- Prefix: `/api/v1/`
- Future breaking changes will introduce a new prefix (`/api/v2/`) while maintaining backward-compatible support for previous clients during a formal deprecation window.
- Additive, non-breaking changes (new optional fields, new endpoints) will remain on the active version.

## Alternatives Considered
- **Header Versioning (`Accept: application/vnd.campuspulse.v1+json`)**: More standard in some REST purist architectures, but harder to inspect in browser bars, harder to cache via CDNs, and more complex to configure in standard frontend client generators.
- **Unversioned URLs (`/api/...`)**: Causes silent regressions as request and response schemas change across development phases.

## Consequences
- Clean, predictable API routing for frontend clients.
- Prevents breaking changes during iterative product rollouts.
