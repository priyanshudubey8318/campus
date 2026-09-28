"""Pydantic schemas for Phase 5 PulseAssist knowledge subsystem."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    content: str
    token_count: int
    metadata_json: dict = Field(default_factory=dict)
    created_at: datetime


class DocumentScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    document_code: str
    document_id: str
    version: str
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool
    created_at: datetime


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    title: str
    document_code: str
    category: str
    version: str
    status: str
    audience: str
    summary: Optional[str] = None
    file_name: str
    file_hash: str
    file_size_bytes: int
    created_by_user_id: str
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    chunks_count: Optional[int] = None
    schedules: Optional[List[DocumentScheduleResponse]] = None


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    document_code: str = Field(..., min_length=2, max_length=64)
    category: str = Field(..., min_length=2, max_length=64)
    version: str = Field(default="v1.0", max_length=32)
    audience: str = Field(default="ALL", max_length=32)
    summary: Optional[str] = Field(default=None, max_length=2000)


class KnowledgeDocumentPublish(BaseModel):
    effective_from: date
    effective_to: Optional[date] = None


class PulseAssistCitation(BaseModel):
    chunk_id: str
    document_code: str
    document_title: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    snippet: str
    relevance_score: float


class PulseAssistMetricEvidence(BaseModel):
    metric_name: str
    observed_value: str
    source_entity: str
    timestamp: Optional[datetime] = None


class PulseAssistQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    student_id: Optional[str] = None
    include_student_metrics: bool = False
    institution_id: Optional[str] = None


class PulseAssistQueryResponse(BaseModel):
    query: str
    response: str
    citations: List[PulseAssistCitation] = Field(default_factory=list)
    ground_truth_metrics: List[PulseAssistMetricEvidence] = Field(default_factory=list)
    verified_data_included: bool = False
    tokens_used: int = 0
    latency_ms: int = 0
    ai_provider: str = "mock"
    model_name: str = ""
