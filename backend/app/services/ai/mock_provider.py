"""Deterministic mock AI provider for testing and offline development."""

import hashlib
import math
import re
from typing import List, Optional

from app.services.ai.protocols import AIProviderProtocol, AIResponse


class MockAIProvider(AIProviderProtocol):
    """Deterministic AI provider generating reproducible 768-dim embeddings and grounded responses."""

    def __init__(self, model_name: str = "mock-pulseassist-v1"):
        self.model_name = model_name
        self.provider_name = "mock"

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a deterministic 768-dimensional normalized float vector from text."""
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        vector: List[float] = []

        # Generate 768 dimensions using repeated hashing with offset
        for i in range(768):
            chunk_seed = seed_bytes[i % len(seed_bytes)]
            val = (float(chunk_seed) / 255.0) * 2.0 - 1.0 + math.sin(float(i + 1) * 0.1)
            vector.append(val)

        # L2-normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Generate a deterministic response adhering to grounding and citation rules."""
        # Check if the prompt has context chunks with document codes
        # Format usually: [Doc: CODE, Title: ..., Section: ...]
        doc_matches = re.findall(r"\[Doc:\s*([A-Za-z0-9_-]+)", prompt)
        cited_docs = sorted(list(set(doc_matches)))

        # Check for student metrics in prompt
        metric_matches = re.findall(r"(\w+):\s*([0-9.]+)", prompt)
        metrics_dict = dict(metric_matches) if metric_matches else {}

        response_parts = []
        if cited_docs:
            primary_doc = cited_docs[0]
            response_parts.append(
                f"Based on institutional policy [Doc: {primary_doc}], here is the verified guidance:"
            )
            # Synthesize answer text from prompt keywords
            if "attendance" in prompt.lower():
                response_parts.append(
                    f"Students are required to maintain a minimum attendance threshold. According to [Doc: {primary_doc}], "
                    "failure to meet mandatory attendance criteria will result in administrative review."
                )
                if "attendance_percentage" in metrics_dict:
                    att_val = metrics_dict["attendance_percentage"]
                    response_parts.append(
                        f"Your current recorded attendance is verified at {att_val}%."
                    )
            elif "grading" in prompt.lower() or "gpa" in prompt.lower() or "grade" in prompt.lower():
                response_parts.append(
                    f"Academic performance standards are defined under [Doc: {primary_doc}]. "
                    "Assessments and cumulative grade point averages follow standard institutional grading bands."
                )
            else:
                response_parts.append(
                    f"The official institutional policy in [Doc: {primary_doc}] provides the governing regulations for this inquiry."
                )

            # If there are additional docs, cite them too
            if len(cited_docs) > 1:
                response_parts.append(
                    f"Additional relevant provisions are documented in [Doc: {cited_docs[1]}]."
                )
        else:
            response_parts.append(
                "I could not locate an active institutional policy document covering this specific query. "
                "Please consult your academic advisor or department handbook."
            )

        response_text = " ".join(response_parts)

        # Estimate tokens
        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(1, len(response_text) // 4)

        return AIResponse(
            text=response_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=12,
            model_name=self.model_name,
            provider_name=self.provider_name,
        )
