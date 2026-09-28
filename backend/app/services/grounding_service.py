"""Citation verification and numerical grounding engine for PulseAssist."""

import re
from typing import Dict, List, Optional, Set, Tuple
from app.schemas.knowledge import PulseAssistCitation, PulseAssistMetricEvidence
from app.services.retrieval_service import RetrievedChunk


class GroundingViolation(Exception):
    """Raised when an AI response contains ungrounded claims or hallucinated citations."""
    pass


class CitationVerificationService:
    """Verifies that all citations in the generated response correspond to retrieved chunks."""

    # Matches citations like:
    # [Doc: POL-ATT-2026]
    # [Doc: POL-ATT, Sec: Minimum Attendance]
    # [Doc: POL-ATT, Page: 4]
    CITATION_REGEX = re.compile(
        r"\[Doc:\s*([A-Za-z0-9_-]+)(?:,\s*(?:Sec|Section):\s*([^,\]]+))?(?:,\s*(?:Page|p\.?):\s*([^,\]]+))?\]",
        re.IGNORECASE,
    )

    def extract_citations(self, response_text: str) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """Extract all (document_code, section, page) tuples cited in the response text."""
        matches = self.CITATION_REGEX.findall(response_text)
        return [(m[0].strip(), m[1].strip() if m[1] else None, m[2].strip() if m[2] else None) for m in matches]

    def verify_and_align_citations(
        self,
        response_text: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> Tuple[str, List[PulseAssistCitation], bool]:
        """Verify citations against retrieved chunks.
        
        If a citation references a document code not present in retrieved chunks,
        it is identified as hallucinated and sanitized from the response text.
        Returns (sanitized_text, verified_citations, has_hallucination).
        """
        valid_doc_codes: Set[str] = {c.document_code.upper() for c in retrieved_chunks}
        chunk_by_code: Dict[str, RetrievedChunk] = {c.document_code.upper(): c for c in retrieved_chunks}

        extracted = self.extract_citations(response_text)
        verified_citations: List[PulseAssistCitation] = []
        has_hallucination = False
        sanitized_text = response_text

        for doc_code, sec, page in extracted:
            code_upper = doc_code.upper()
            if code_upper in valid_doc_codes:
                chunk = chunk_by_code[code_upper]
                # Avoid duplicate citation objects for the same chunk
                if not any(vc.chunk_id == chunk.chunk_id for vc in verified_citations):
                    verified_citations.append(
                        PulseAssistCitation(
                            chunk_id=chunk.chunk_id,
                            document_code=chunk.document_code,
                            document_title=chunk.document_title,
                            section_title=sec or chunk.section_title,
                            page_number=int(page) if page and page.isdigit() else chunk.page_number,
                            snippet=chunk.content[:200] + ("..." if len(chunk.content) > 200 else ""),
                            relevance_score=chunk.rrf_score,
                        )
                    )
            else:
                # Hallucinated citation detected!
                has_hallucination = True
                # Remove or sanitize the hallucinated citation pattern
                pattern = rf"\[Doc:\s*{re.escape(doc_code)}[^\]]*\]"
                sanitized_text = re.sub(pattern, "[Citation Unverified]", sanitized_text)

        # If no explicit inline citation was written by the LLM but valid chunks were used,
        # attach the top retrieved chunk as the grounding reference
        if not verified_citations and retrieved_chunks:
            top_c = retrieved_chunks[0]
            verified_citations.append(
                PulseAssistCitation(
                    chunk_id=top_c.chunk_id,
                    document_code=top_c.document_code,
                    document_title=top_c.document_title,
                    section_title=top_c.section_title,
                    page_number=top_c.page_number,
                    snippet=top_c.content[:200] + ("..." if len(top_c.content) > 200 else ""),
                    relevance_score=top_c.rrf_score,
                )
            )

        return sanitized_text, verified_citations, has_hallucination


class NumericalGroundingValidator:
    """Validates that numerical values in responses are grounded in chunks or verified student data."""

    # Matches numbers, percentages, decimals, e.g. 75%, 3.42, 80, 100%
    NUMERICAL_REGEX = re.compile(r"\b(\d+(?:\.\d+)?%?)\b")

    def extract_numbers(self, text: str) -> Set[str]:
        """Extract normalized numbers from text."""
        raw_matches = self.NUMERICAL_REGEX.findall(text)
        return {m.strip() for m in raw_matches}

    def validate_grounding(
        self,
        response_text: str,
        retrieved_chunks: List[RetrievedChunk],
        ground_truth_metrics: List[PulseAssistMetricEvidence],
    ) -> Tuple[bool, List[str]]:
        """Verify that every number in response_text exists in either chunks or metrics.
        
        Returns (is_valid, ungrounded_numbers).
        """
        response_numbers = self.extract_numbers(response_text)
        if not response_numbers:
            return True, []

        # Gather all allowed numbers from chunks
        allowed_numbers: Set[str] = set()
        for c in retrieved_chunks:
            allowed_numbers.update(self.extract_numbers(c.content))

        # Gather all allowed numbers from ground truth student evidence
        for m in ground_truth_metrics:
            allowed_numbers.update(self.extract_numbers(m.observed_value))
            allowed_numbers.add(m.observed_value.strip())

        # Also allow trivial numbers (0, 1, 2) that may be grammatical or ordinal
        allowed_numbers.update({"0", "1", "2", "3", "4", "5", "10"})

        ungrounded: List[str] = []
        for num in response_numbers:
            # Check direct match or match without % sign
            clean_num = num.rstrip("%")
            matched = (
                num in allowed_numbers
                or clean_num in allowed_numbers
                or any(clean_num in allowed.rstrip("%") for allowed in allowed_numbers)
            )
            if not matched:
                ungrounded.append(num)

        return len(ungrounded) == 0, ungrounded
