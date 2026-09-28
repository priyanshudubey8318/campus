"""Hybrid dense/sparse retrieval and Reciprocal Rank Fusion (RRF) service for PulseAssist."""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ai.protocols import AIProviderProtocol, VectorSearchResult, VectorStoreProtocol
from app.services.ai.vector_store import PostgresVectorStore


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_code: str
    document_title: str
    chunk_index: int
    content: str
    section_title: Optional[str]
    page_number: Optional[int]
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    rrf_score: float = 0.0
    metadata_json: dict = field(default_factory=dict)


class PulseAssistRetrievalService:
    """Orchestrates multi-step hybrid retrieval with RRF and timeline resolution."""

    def __init__(
        self,
        ai_provider: AIProviderProtocol,
        vector_store: Optional[VectorStoreProtocol] = None,
    ):
        self.ai_provider = ai_provider
        self.vector_store = vector_store

    def resolve_active_documents(
        self,
        db: Session,
        institution_id: str,
        query_date: Optional[date] = None,
    ) -> Dict[str, dict]:
        """Step 1 (A): Resolve single currently-effective published version per (institution_id, document_code).
        
        Uses DISTINCT ON (s.institution_id, s.document_code) to deterministically select the active head.
        Returns a mapping from document_id to metadata dict.
        """
        target_date = query_date or date.today()

        sql = text("""
        SELECT DISTINCT ON (s.institution_id, s.document_code)
            s.document_id,
            s.document_code,
            s.version,
            d.title,
            d.audience,
            d.category
        FROM document_version_schedules s
        JOIN knowledge_documents d 
          ON s.document_id = d.id 
         AND s.institution_id = d.institution_id 
         AND s.document_code = d.document_code 
         AND s.version = d.version
        WHERE s.institution_id = :institution_id
          AND s.is_active = TRUE
          AND d.status = 'PUBLISHED'
          AND s.effective_from <= :query_date
          AND (s.effective_to IS NULL OR s.effective_to >= :query_date)
        ORDER BY s.institution_id, s.document_code, s.effective_from DESC, d.version DESC;
        """)

        rows = db.execute(sql, {"institution_id": institution_id, "query_date": target_date}).fetchall()

        active_docs: Dict[str, dict] = {}
        for r in rows:
            active_docs[r.document_id] = {
                "document_id": r.document_id,
                "document_code": r.document_code,
                "version": r.version,
                "title": r.title,
                "audience": r.audience,
                "category": r.category,
            }
        return active_docs

    def retrieve_sparse_candidates(
        self,
        db: Session,
        query_text: str,
        institution_id: str,
        active_doc_ids: List[str],
        allowed_audiences: List[str],
        limit: int = 10,
    ) -> List[dict]:
        """Step 2 (B): Sparse BM25-style lexical search using PostgreSQL plainto_tsquery."""
        if not active_doc_ids:
            return []

        sql = text("""
        SELECT 
            c.id AS chunk_id,
            c.document_id,
            c.chunk_index,
            c.content,
            c.section_title,
            c.page_number,
            c.metadata_json,
            ts_rank(c.tsv, plainto_tsquery('english', :query_text)) AS sparse_score
        FROM knowledge_chunks c
        JOIN knowledge_documents d ON c.document_id = d.id AND c.institution_id = d.institution_id
        WHERE c.institution_id = :institution_id
          AND c.document_id = ANY(:active_doc_ids)
          AND d.audience = ANY(:allowed_audiences)
          AND c.tsv @@ plainto_tsquery('english', :query_text)
        ORDER BY sparse_score DESC
        LIMIT :limit;
        """)

        rows = db.execute(
            sql,
            {
                "query_text": query_text,
                "institution_id": institution_id,
                "active_doc_ids": active_doc_ids,
                "allowed_audiences": allowed_audiences,
                "limit": limit,
            },
        ).fetchall()

        return [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "chunk_index": r.chunk_index,
                "content": r.content,
                "section_title": r.section_title,
                "page_number": r.page_number,
                "sparse_score": float(r.sparse_score) if r.sparse_score is not None else 0.0,
                "metadata_json": r.metadata_json or {},
            }
            for r in rows
        ]

    def hybrid_search(
        self,
        db: Session,
        query_text: str,
        institution_id: str,
        audience: str = "ALL",
        query_date: Optional[date] = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Execute full hybrid RAG retrieval pipeline:
        1. Resolve active documents for query_date.
        2. Execute dense top 10 + sparse top 10.
        3. Apply relevance gate (dense >= 0.65 OR sparse present).
        4. Fuse ranks using canonical RRF formula.
        5. Return top K ranked context chunks.
        """
        # 1. Resolve active documents
        active_docs = self.resolve_active_documents(db, institution_id, query_date)
        if not active_docs:
            return []

        active_doc_ids = list(active_docs.keys())

        # Determine audience scopes
        allowed_audiences = ["ALL"]
        if audience in ("STUDENT", "FACULTY", "ADVISOR"):
            allowed_audiences.append(audience)
        elif audience in ("SUPER_ADMIN", "ADMIN"):
            allowed_audiences.extend(["STUDENT", "FACULTY", "ADVISOR"])

        # 2. Dense retrieval Top-10
        vector_store = self.vector_store or PostgresVectorStore(db)
        query_embedding = self.ai_provider.generate_embedding(query_text)
        dense_results = vector_store.similarity_search(
            query_embedding=query_embedding,
            institution_id=institution_id,
            active_doc_ids=active_doc_ids,
            audience=audience,
            limit=10,
        )

        # 3. Sparse retrieval Top-10
        sparse_results = self.retrieve_sparse_candidates(
            db=db,
            query_text=query_text,
            institution_id=institution_id,
            active_doc_ids=active_doc_ids,
            allowed_audiences=allowed_audiences,
            limit=10,
        )

        # Build candidate map with original 1-based ranks
        candidates: Dict[str, RetrievedChunk] = {}

        for rank_idx, dr in enumerate(dense_results, start=1):
            doc_meta = active_docs.get(dr.document_id, {})
            candidates[dr.chunk_id] = RetrievedChunk(
                chunk_id=dr.chunk_id,
                document_id=dr.document_id,
                document_code=doc_meta.get("document_code", dr.metadata_json.get("document_code", "DOC")),
                document_title=doc_meta.get("title", dr.metadata_json.get("title", "Document")),
                chunk_index=dr.chunk_index,
                content=dr.content,
                section_title=dr.section_title,
                page_number=dr.page_number,
                dense_score=dr.score,
                dense_rank=rank_idx,
                metadata_json=dr.metadata_json,
            )

        for rank_idx, sr in enumerate(sparse_results, start=1):
            chunk_id = sr["chunk_id"]
            if chunk_id in candidates:
                candidates[chunk_id].sparse_score = sr["sparse_score"]
                candidates[chunk_id].sparse_rank = rank_idx
            else:
                doc_meta = active_docs.get(sr["document_id"], {})
                candidates[chunk_id] = RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=sr["document_id"],
                    document_code=doc_meta.get("document_code", sr["metadata_json"].get("document_code", "DOC")),
                    document_title=doc_meta.get("title", sr["metadata_json"].get("title", "Document")),
                    chunk_index=sr["chunk_index"],
                    content=sr["content"],
                    section_title=sr["section_title"],
                    page_number=sr["page_number"],
                    sparse_score=sr["sparse_score"],
                    sparse_rank=rank_idx,
                    metadata_json=sr["metadata_json"],
                )

        # 4. Relevance gate & RRF Scoring
        # Canonical formula:
        # RRF(c) = (0.7 / (60 + dense_rank(c)) if dense_rank is not None else 0.0) +
        #          (0.3 / (60 + sparse_rank(c)) if sparse_rank is not None else 0.0)
        qualified_chunks: List[RetrievedChunk] = []

        for c in candidates.values():
            # Relevance Gate: must have dense_score >= 0.65 OR sparse_score > 0
            dense_passed = c.dense_score is not None and c.dense_score >= 0.65
            sparse_passed = c.sparse_score is not None and c.sparse_score > 0.0

            if not (dense_passed or sparse_passed):
                continue

            dense_term = (0.7 / (60 + c.dense_rank)) if c.dense_rank is not None else 0.0
            sparse_term = (0.3 / (60 + c.sparse_rank)) if c.sparse_rank is not None else 0.0
            c.rrf_score = round(dense_term + sparse_term, 6)

            qualified_chunks.append(c)

        # 5. Sort by RRF score descending, take top K
        qualified_chunks.sort(key=lambda x: x.rrf_score, reverse=True)
        return qualified_chunks[:top_k]
