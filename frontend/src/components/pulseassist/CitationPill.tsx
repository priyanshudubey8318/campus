"use client";

import React, { useState } from "react";
import { CitationDetail } from "@/types/pulseassist";
import { Badge } from "@/components/ui/Badge";
import { FileText, CheckCircle2, AlertCircle, Info } from "lucide-react";

interface CitationPillProps {
  citation: CitationDetail;
  onOpenWhySeeing?: (citation: CitationDetail) => void;
}

export function CitationPill({ citation, onOpenWhySeeing }: CitationPillProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative inline-block my-1 mr-1.5 align-middle">
      <button
        type="button"
        onClick={() => onOpenWhySeeing?.(citation)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium font-mono transition-all border shadow-sm
          bg-[#FF7A18]/12 text-[#FF9A3D] border-[#FF7A18]/30 hover:bg-[#FF7A18]/20 hover:border-[#FF7A18]/50"
        title="Click to view policy citation source"
        data-testid={`citation-pill-${citation.document_code}`}
      >
        <FileText className="h-3 w-3 text-[#FF7A18] flex-shrink-0" />
        <span className="font-semibold">{citation.document_code}</span>
        {citation.verified ? (
          <CheckCircle2
            className="h-3 w-3 text-[#28C76F] flex-shrink-0"
            aria-label="Verified citation"
          />
        ) : (
          <AlertCircle
            className="h-3 w-3 text-[#FFB020] flex-shrink-0"
            aria-label="Unverified citation"
          />
        )}
      </button>

      {/* Hover preview tooltip */}
      {showTooltip && (
        <div className="absolute z-50 bottom-full left-0 mb-2 w-72 p-3 bg-[#151B24] border border-white/10 rounded-lg shadow-2xl text-left pointer-events-none animate-in fade-in-0 duration-150">
          <div className="flex items-center justify-between pb-1 border-b border-white/[0.08]">
            <span className="font-mono text-[10px] font-bold text-[#FF9A3D]">
              {citation.document_code}
            </span>
            <Badge
              variant={citation.verified ? "success" : "neutral"}
              className="text-[9px] px-1 py-0 font-mono"
            >
              {citation.verified ? "Ground-Truth Verified" : "Extracted"}
            </Badge>
          </div>
          <p className="text-xs font-semibold text-[#F5F7FA] mt-1 line-clamp-1">
            {citation.document_title}
          </p>
          <p className="text-[11px] text-[#A7AFBD] mt-1 line-clamp-3 italic">
            &ldquo;{citation.content_snippet}&rdquo;
          </p>
          <div className="mt-2 pt-1 border-t border-white/[0.08] text-[9px] text-[#6F7785] flex items-center justify-between font-mono">
            <span>Chunk #{citation.chunk_index + 1}</span>
            <span>Click for full explainability</span>
          </div>
        </div>
      )}
    </div>
  );
}
