"""Central API v1 router mounting all domain routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, academic, pulsewatch, pulserisk, pulseassist, leaves, complaints, cases

api_v1_router = APIRouter()

# Foundational health & diagnostics routes
api_v1_router.include_router(health.router, tags=["Health & Diagnostics"])

# Phase 1: Identity & Access Management
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Identity & Access"])

# Phase 2: Academic Domain, Profiles & Academic Data
api_v1_router.include_router(academic.router, prefix="/academic", tags=["Academic Foundation"])

# Phase 3: PulseWatch Behavioral Monitoring
api_v1_router.include_router(pulsewatch.router, prefix="/pulsewatch", tags=["PulseWatch"])

# Phase 4: PulseRisk Support Prioritization Subsystem
api_v1_router.include_router(pulserisk.router, prefix="/pulserisk", tags=["PulseRisk"])

# Phase 5: PulseAssist RAG & Knowledge Subsystem
api_v1_router.include_router(pulseassist.router, prefix="/pulseassist", tags=["PulseAssist"])

# Phase 6: PulseRecord - Leaves & Complaints
api_v1_router.include_router(leaves.router, prefix="/leaves", tags=["PulseRecord - Leaves"])
api_v1_router.include_router(complaints.router, prefix="/complaints", tags=["PulseRecord - Complaints"])

# Phase 7: PulseCase - Support Cases & Interventions
api_v1_router.include_router(cases.router, prefix="/cases", tags=["PulseCase"])

# Phase 8:
# api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Reporting"])
# ============================================================================
