"use client";

import React from "react";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { PulseRiskSummary } from "@/types/pulserisk";
import {
  ShieldAlert,
  HelpCircle,
  BarChart3,
  Layers,
  Scale,
  Calendar,
  AlertTriangle,
  Info,
} from "lucide-react";

interface PulseRiskExplainModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: PulseRiskSummary | null;
}

export function PulseRiskExplainModal({
  isOpen,
  onClose,
  summary,
}: PulseRiskExplainModalProps) {
  if (!summary) return null;

  const {
    support_priority_index,
    priority_tier,
    confidence_score,
    data_quality,
    primary_driver,
    policy_name,
    policy_version,
    algorithm_version,
    contributions,
    safety_floors_triggered,
    explainability,
  } = summary;

  const getTierBadge = () => {
    switch (priority_tier) {
      case "LOW_PRIORITY":
        return <Badge variant="success">Standard Support Pacing</Badge>;
      case "MODERATE_PRIORITY":
        return <Badge variant="primary">Emerging Support Opportunity</Badge>;
      case "ELEVATED_PRIORITY":
        return <Badge variant="warning">Active Support Prioritized</Badge>;
      case "URGENT_PRIORITY":
        return <Badge variant="danger">Immediate Proactive Support</Badge>;
      default:
        return <Badge variant="neutral">{priority_tier}</Badge>;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Academic Momentum & Support Prioritization Decomposition"
      description="Transparent, deterministic breakdown of your Support Priority Index (SPI)."
      maxWidth="xl"
    >
      <div
        className="space-y-4 text-xs text-zinc-300"
        data-testid="pulserisk-explain-modal"
      >
        {/* Header KPI Card */}
        <div className="flex flex-wrap items-center justify-between p-4 rounded-xl bg-[#111722] border border-white/[0.08] gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-[#FF7A18]/10 text-[#FF9A3D]">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                Support Priority Index (SPI)
              </div>
              <div className="text-xl font-bold font-mono text-white flex items-center space-x-2">
                <span data-testid="modal-spi-value">{Number(support_priority_index).toFixed(1)}</span>
                <span className="text-xs font-normal text-zinc-400">/ 100</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div data-testid="modal-priority-tier">{getTierBadge()}</div>
            <div className="text-[11px] text-zinc-400 flex items-center space-x-2">
              <span>Confidence: {(Number(confidence_score) * 100).toFixed(0)}%</span>
              <span>•</span>
              <span className="uppercase text-zinc-300">{data_quality.replace(/_/g, " ")}</span>
            </div>
          </div>
        </div>

        {/* Safety Floor Alert if triggered */}
        {safety_floors_triggered.length > 0 && (
          <div
            className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-950/40 text-rose-200 space-y-1.5"
            data-testid="modal-safety-floor-alert"
          >
            <div className="flex items-center space-x-2 font-semibold text-rose-300">
              <AlertTriangle className="h-4 w-4 text-rose-400" />
              <span>Safety Floor Protection Triggered</span>
            </div>
            {safety_floors_triggered.map((st, idx) => (
              <p key={idx} className="text-xs text-rose-300 leading-relaxed">
                <strong>{st.trigger_name.replace(/_/g, " ")}:</strong> {st.reason} Mandated minimum floor: {st.mandated_floor} pts.
              </p>
            ))}
          </div>
        )}

        {/* Dimension Decomposition Table */}
        <div className="p-3.5 rounded-xl bg-[#111722]/60 border border-white/[0.08] space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 font-semibold text-white">
              <BarChart3 className="h-4 w-4 text-[#FF9A3D]" />
              <span>Multi-Signal Dimension Breakdown</span>
            </div>
            <span className="text-[11px] font-mono text-zinc-400">
              SPI = min(100, Σ (Factor × Weight))
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" data-testid="modal-contributions-table">
              <thead>
                <tr className="border-b border-white/[0.08] text-[11px] text-zinc-400 uppercase tracking-wider">
                  <th className="py-2 pr-2 font-medium">Dimension</th>
                  <th className="py-2 px-2 font-medium">Observed</th>
                  <th className="py-2 px-2 font-medium">Baseline</th>
                  <th className="py-2 px-2 font-medium">Shift</th>
                  <th className="py-2 px-2 font-medium text-right">Factor</th>
                  <th className="py-2 px-2 font-medium text-right">Weight</th>
                  <th className="py-2 pl-2 font-medium text-right">Contribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06]">
                {contributions.map((c, i) => (
                  <tr key={i} className="hover:bg-white/[0.02]">
                    <td className="py-2 pr-2 font-medium text-white">
                      {c.dimension.replace(/_/g, " ")}
                    </td>
                    <td className="py-2 px-2 text-zinc-300 font-mono">
                      {c.observed_value || "—"}
                    </td>
                    <td className="py-2 px-2 text-zinc-400 font-mono">
                      {c.baseline_value || "—"}
                    </td>
                    <td className="py-2 px-2 font-medium text-zinc-200 font-mono">
                      {c.delta_value || "—"}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-zinc-300">
                      {Number(c.factor_score).toFixed(1)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-zinc-400">
                      {(Number(c.assigned_weight) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 pl-2 text-right font-mono font-semibold text-white">
                      {Number(c.weighted_contribution).toFixed(1)} pts
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Primary Driver & Narrative */}
        <div className="p-3.5 rounded-xl bg-[#111722]/60 border border-white/[0.08] space-y-1.5">
          <div className="flex items-center space-x-2 font-semibold text-white">
            <Info className="h-4 w-4 text-[#FF9A3D]" />
            <span>Support Context Summary</span>
          </div>
          {primary_driver && (
            <div className="text-xs text-zinc-300">
              <strong className="text-zinc-400">Primary Pacing Driver:</strong>{" "}
              <span className="font-semibold text-white uppercase font-mono">
                {primary_driver.replace(/_/g, " ")}
              </span>
            </div>
          )}
          <p className="text-xs text-zinc-300 leading-relaxed" data-testid="modal-explain-summary">
            {explainability.summary}
          </p>
        </div>

        {/* Policy & Governance Metadata */}
        <div className="p-3 rounded-xl bg-[#111722] border border-white/[0.08] flex flex-wrap items-center justify-between text-[11px] text-zinc-400 font-mono">
          <div>
            <strong className="text-zinc-300">Governing Policy:</strong> {policy_name} ({policy_version})
          </div>
          <div>
            <strong className="text-zinc-300">Algorithm:</strong> {algorithm_version}
          </div>
        </div>

        {/* Institutional Non-Punitive Notice */}
        <p className="text-[11px] text-zinc-400 italic leading-relaxed pt-1">
          {explainability.institutional_notice}
        </p>
      </div>
    </Modal>
  );
}
