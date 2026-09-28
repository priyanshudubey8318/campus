"use client";

import React from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { PulseWatchSummary } from "@/types/pulsewatch";
import {
  Layers,
  Calendar,
  CheckCircle2,
  ShieldCheck,
  FileText,
} from "lucide-react";

interface PulseExplainModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: PulseWatchSummary | null;
}

export function PulseExplainModal({
  isOpen,
  onClose,
  summary,
}: PulseExplainModalProps) {
  if (!summary) return null;

  const { explainability, overall_status, data_quality } = summary;

  const getStatusBadge = () => {
    switch (overall_status) {
      case "NORMAL":
        return <Badge variant="success">Normal Stability</Badge>;
      case "MILD_CHANGE":
        return <Badge variant="warning">Mild Change Detected</Badge>;
      case "MODERATE_CHANGE":
        return <Badge variant="warning">Moderate Change Detected</Badge>;
      case "SIGNIFICANT_CHANGE":
        return <Badge variant="danger">Significant Change Detected</Badge>;
      default:
        return <Badge variant="neutral">{overall_status}</Badge>;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Academic Pulse Engagement Breakdown"
      description="Deterministic transparency on how your academic engagement indicators are calculated."
      maxWidth="lg"
    >
      <div className="space-y-4 text-xs text-zinc-300" data-testid="academic-pulse-explain-modal">
        {/* Status Header */}
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#111722] border border-white/[0.08]">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-white">Current Indicator:</span>
            <span data-testid="modal-status-badge">{getStatusBadge()}</span>
          </div>
          <span className="font-mono text-[11px] text-zinc-400">
            {summary.algorithm_version}
          </span>
        </div>

        {/* 1. What Changed */}
        <div className="p-3.5 rounded-xl bg-[#111722]/60 border border-white/[0.08] space-y-1">
          <div className="flex items-center space-x-2 text-white font-semibold">
            <Layers className="h-4 w-4 text-[#FF9A3D]" />
            <span>What Changed?</span>
          </div>
          <p className="text-zinc-300 leading-relaxed pt-1" data-testid="explain-what-changed">
            {explainability.what_changed}
          </p>
        </div>

        {/* 2. Compared With */}
        <div className="p-3.5 rounded-xl bg-[#111722]/60 border border-white/[0.08] space-y-1">
          <div className="flex items-center space-x-2 text-white font-semibold">
            <FileText className="h-4 w-4 text-blue-400" />
            <span>Baseline Comparison</span>
          </div>
          <p className="text-zinc-300 leading-relaxed pt-1" data-testid="explain-compared-with">
            {explainability.compared_with}
          </p>
          <div className="pt-2 text-[11px] text-zinc-400 flex flex-wrap gap-x-4 gap-y-1">
            <span>
              <strong className="text-zinc-300">Baseline Window:</strong> {summary.baseline_start_date} → {summary.baseline_end_date}
            </span>
          </div>
        </div>

        {/* 3. Observation Period */}
        <div className="p-3.5 rounded-xl bg-[#111722]/60 border border-white/[0.08] space-y-1">
          <div className="flex items-center space-x-2 text-white font-semibold">
            <Calendar className="h-4 w-4 text-purple-400" />
            <span>Observation Window</span>
          </div>
          <p className="text-zinc-300 leading-relaxed pt-1" data-testid="explain-observation-period">
            {explainability.observation_period}
          </p>
          <div className="pt-2 text-[11px] text-zinc-400 flex flex-wrap gap-x-4 gap-y-1">
            <span>
              <strong className="text-zinc-300">Window Duration:</strong> {summary.observation_window_days} days ({summary.window_start_date} → {summary.window_end_date})
            </span>
          </div>
        </div>

        {/* 4. Data Sufficiency */}
        <div className="p-3.5 rounded-xl bg-[#111722]/60 border border-white/[0.08] space-y-1">
          <div className="flex items-center space-x-2 text-white font-semibold">
            <CheckCircle2 className="h-4 w-4 text-[#28C76F]" />
            <span>Data Sufficiency Status</span>
          </div>
          <p className="text-zinc-300 leading-relaxed pt-1" data-testid="explain-data-sufficiency">
            {explainability.data_sufficiency}
          </p>
          <div className="pt-1">
            <Badge variant={data_quality === "VALID_DATA" ? "success" : "neutral"} className="text-[10px]">
              {data_quality}
            </Badge>
          </div>
        </div>

        {/* Institutional Non-Punitive Disclaimer */}
        <div className="p-3.5 rounded-xl bg-[#FF7A18]/5 border border-[#FF7A18]/20 text-[#FF9A3D] space-y-1">
          <div className="flex items-center space-x-2 font-semibold text-xs">
            <ShieldCheck className="h-4 w-4 text-[#FF7A18] flex-shrink-0" />
            <span>Institutional Engagement Notice</span>
          </div>
          <p className="text-[11px] text-zinc-300 leading-relaxed pt-1" data-testid="explain-disclaimer">
            {explainability.disclaimer}
          </p>
        </div>

        <div className="flex justify-end pt-2">
          <Button size="sm" variant="outline" onClick={onClose} data-testid="close-explain-modal-btn">
            Close Explanation
          </Button>
        </div>
      </div>
    </Modal>
  );
}
