"use client";

import React from "react";
import { CitationDetail } from "@/types/pulseassist";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { FileText, Calendar, CheckCircle2, ShieldCheck, Database, Layers } from "lucide-react";

interface WhySeeingModalProps {
  citation: CitationDetail | null;
  isOpen: boolean;
  onClose: () => void;
}

export function WhySeeingModal({ citation, isOpen, onClose }: WhySeeingModalProps) {
  if (!citation) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Why am I seeing this policy citation?"
      description="Explainability and grounding verification for institutional knowledge retrieval."
      maxWidth="lg"
    >
      <div className="space-y-4 text-xs" data-testid="why-seeing-modal">
        {/* Source Document Metadata Header */}
        <div className="p-3.5 rounded-xl border border-white/10 bg-[#111722] space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-[#FF7A18]" />
              <span className="font-mono text-xs font-bold text-[#FF9A3D]" data-testid="why-document-code">
                {citation.document_code}
              </span>
            </div>
            <Badge
              variant={citation.verified ? "success" : "neutral"}
              className="text-[10px] font-mono"
              data-testid="why-verification-badge"
            >
              {citation.verified ? "Ground-Truth Grounded" : "Extracted Citation"}
            </Badge>
          </div>

          <h4 className="text-sm font-display font-semibold text-[#F5F7FA]" data-testid="why-document-title">
            {citation.document_title}
          </h4>

          {/* Effective Date Range */}
          <div className="flex items-center space-x-1.5 text-[11px] text-[#A7AFBD] font-mono" data-testid="why-effective-date">
            <Calendar className="h-3.5 w-3.5 text-[#6F7785]" />
            <span>Effective Policy Window:</span>
            <span className="font-medium text-[#F5F7FA]">
              {citation.effective_from ? citation.effective_from : "Current Active Policy"}
              {" — "}
              {citation.effective_to ? citation.effective_to : "Ongoing"}
            </span>
          </div>
        </div>

        {/* Exact Source Knowledge Chunk */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono font-medium text-[#A7AFBD] text-[11px] uppercase tracking-wide">
              Exact Source Knowledge Chunk (Index #{citation.chunk_index})
            </span>
            <span className="text-[10px] text-[#6F7785] font-mono">
              Citation ID: {citation.citation_id.substring(0, 8)}...
            </span>
          </div>
          <div
            className="p-3 rounded-lg border border-[#FF7A18]/30 bg-[#FF7A18]/10 text-[#F5F7FA] leading-relaxed font-sans text-xs italic"
            data-testid="why-chunk-snippet"
          >
            &ldquo;{citation.content_snippet}&rdquo;
          </div>
        </div>

        {/* Explainability & Retrieval Process */}
        <div className="p-3 rounded-lg border border-white/10 bg-[#111722] space-y-2">
          <span className="font-mono font-semibold text-[#F5F7FA] text-[11px] flex items-center space-x-1.5">
            <Layers className="h-3.5 w-3.5 text-[#FF7A18]" />
            <span>Deterministic RAG Retrieval &amp; Grounding Architecture</span>
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px] text-[#A7AFBD]">
            <div className="p-2 rounded bg-[#151B24] border border-white/10">
              <span className="font-semibold text-[#F5F7FA] block mb-0.5">1. Hybrid Retrieval</span>
              Dense semantic similarity (top 10) + Full-text BM25 sparse search (top 10).
            </div>
            <div className="p-2 rounded bg-[#151B24] border border-white/10">
              <span className="font-semibold text-[#F5F7FA] block mb-0.5">2. Weighted RRF</span>
              Merged via Reciprocal Rank Fusion: 0.7/(60 + dense) + 0.3/(60 + sparse).
            </div>
            <div className="p-2 rounded bg-[#151B24] border border-white/10">
              <span className="font-semibold text-[#F5F7FA] block mb-0.5">3. Grounding Gate</span>
              AI claims verified against institutional chunks. Unverified claims dropped.
            </div>
          </div>
        </div>

        {/* Institutional Safeguards Note */}
        <div className="p-2.5 rounded-lg bg-[#151B24] border border-white/10 text-[10px] text-[#A7AFBD] flex items-start space-x-2">
          <ShieldCheck className="h-4 w-4 text-[#FF7A18] flex-shrink-0 mt-0.5" />
          <span>
            CampusPulse PulseAssist enforces strict deterministic grounding. Assistant responses only cite approved, currently effective institutional documents and verified academic databases.
          </span>
        </div>

        <div className="flex justify-end pt-2">
          <Button variant="outline" size="sm" onClick={onClose} data-testid="why-close-btn">
            Close Explainability
          </Button>
        </div>
      </div>
    </Modal>
  );
}
