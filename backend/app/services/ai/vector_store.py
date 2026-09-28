"""PostgreSQL vector store using pgvector HNSW indexing."""

from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ai.protocols import VectorSearchResult, VectorStoreProtocol


class PostgresVectorStore(VectorStoreProtocol):
    """PostgreSQL pgvector storage adapter for dense retrieval."""

    def __init__(self, db: Session):
        self.db = db

    def similarity_search(
        self,
        query_embedding: List[float],
        institution_id: str,
        active_doc_ids: List[str],
        audience: str = "ALL",
        limit: int = 10,
    ) -> List[VectorSearchResult]:
        """Perform dense cosine similarity search over knowledge chunks."""
        if not active_doc_ids:
            return []

        # Format embedding as pgvector literal string '[v1, v2, ...]'
        vec_literal = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"

        # Audience filter logic:
        # If audience is ALL or SUPER_ADMIN, include ALL, STUDENT, FACULTY, ADVISOR
        # If audience is STUDENT, include ALL and STUDENT
        # If audience is FACULTY, include ALL and FACULTY
        # If audience is ADVISOR, include ALL, STUDENT, ADVISOR
        allowed_audiences = ["ALL"]
        if audience in ("STUDENT", "FACULTY", "ADVISOR"):
            allowed_audiences.append(audience)
        elif audience in ("SUPER_ADMIN", "ADMIN"):
            allowed_audiences.extend(["STUDENT", "FACULTY", "ADVISOR"])

        sql = text("""
        SELECT 
            c.id AS chunk_id,
            c.document_id,
            c.chunk_index,
            c.content,
            c.section_title,
            c.page_number,
            c.metadata_json,
            (1.0 - (c.embedding <=> CAST(:query_vec AS vector))) AS score
        FROM knowledge_chunks c
        JOIN knowledge_documents d ON c.document_id = d.id AND c.institution_id = d.institution_id
        WHERE c.institution_id = :institution_id
          AND c.document_id = ANY(:active_doc_ids)
          AND c.embedding IS NOT NULL
          AND d.audience = ANY(:allowed_audiences)
        ORDER BY c.embedding <=> CAST(:query_vec AS vector) ASC
        LIMIT :limit
        """)

        rows = self.db.execute(
            sql,
            {
                "query_vec": vec_literal,
                "institution_id": institution_id,
                "active_doc_ids": active_doc_ids,
                "allowed_audiences": allowed_audiences,
                "limit": limit,
            },
        ).fetchall()

        results = []
        for r in rows:
            results.append(
                VectorSearchResult(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    chunk_index=r.chunk_index,
                    content=r.content,
                    section_title=r.section_title,
                    page_number=r.page_number,
                    score=float(r.score) if r.score is not None else 0.0,
                    metadata_json=r.metadata_json or {},
                )
            )

        return results
