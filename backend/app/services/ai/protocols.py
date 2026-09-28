"""AI provider and vector store protocols for Phase 5 PulseAssist."""

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, runtime_checkable


@dataclass
class AIResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    model_name: str = ""
    provider_name: str = ""


@dataclass
class VectorSearchResult:
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    section_title: Optional[str]
    page_number: Optional[int]
    score: float
    metadata_json: dict = field(default_factory=dict)


@runtime_checkable
class AIProviderProtocol(Protocol):
    """Protocol for AI completion and embedding providers."""

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Generate response text with token usage telemetry."""
        ...

    def generate_embedding(self, text: str) -> List[float]:
        """Generate 768-dimensional normalized dense embedding vector."""
        ...


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Protocol for vector similarity search."""

    def similarity_search(
        self,
        query_embedding: List[float],
        institution_id: str,
        active_doc_ids: List[str],
        audience: str = "ALL",
        limit: int = 10,
    ) -> List[VectorSearchResult]:
        """Retrieve top dense vector search matches scoped to tenant and active documents."""
        ...
