"use client";

import React, { useState } from "react";
import { PulseRiskSummary } from "@/types/pulserisk";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RingBackground } from "@/components/ui/RingBackground";
import { PulseRiskExplainModal } from "./PulseRiskExplainModal";
import {
  Scale,
  HelpCircle,
  TrendingUp,
  AlertTriangle,
  CalendarCheck,
  FileCheck2,
  Award,
  Clock,
  ShieldCheck,
} from "lucide-react";

interface SupportPriorityCardProps {
  summary: PulseRiskSummary | null;
  loading?: boolean;
}

export function SupportPriorityCard({
  summary,
  loading = false,
}: SupportPriorityCardProps) {
  const [explainModalOpen, setExplainModalOpen] = useState(false);

  if (loading) {
    return (
      <div
        className="rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6 shadow-sm animate-pulse"
        data-testid="pulserisk-card-loading"
      >
        <div className="h-6 bg-white/[0.06] rounded w-1/3 mb-4" />
        <div className="h-4 bg-white/[0.04] rounded w-2/3 mb-6" />
        <div className="h-24 bg-white/[0.03] rounded-xl" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div
        className="rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6"
        data-testid="pulserisk-card-empty"
      >
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#FF7A18]/10 text-[#FF9A3D]">
            <Scale className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white font-display">
              Support Momentum Establishing
            </h3>
            <p className="text-xs text-zinc-400">
              Your support prioritization metrics will establish as academic coursework and attendance accrue.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const support_priority_index = summary?.support_priority_index ?? 0;
  const priority_tier = summary?.priority_tier || "LOW_PRIORITY";
  const data_quality = summary?.data_quality || "ESTABLISHING";
  const contributions = Array.isArray(summary?.contributions) ? summary.contributions : [];
  const safety_floors_triggered = Array.isArray(summary?.safety_floors_triggered) ? summary.safety_floors_triggered : [];

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

  const getDimensionIcon = (dim: string) => {
    switch (dim) {
      case "ATTENDANCE":
        return <CalendarCheck className="h-3.5 w-3.5 text-[#FF9A3D]" />;
      case "COURSEWORK":
        return <FileCheck2 className="h-3.5 w-3.5 text-blue-400" />;
      case "ASSESSMENTS":
        return <Award className="h-3.5 w-3.5 text-purple-400" />;
      case "LONGITUDINAL_PERSISTENCE":
        return <Clock className="h-3.5 w-3.5 text-emerald-400" />;
      default:
        return <TrendingUp className="h-3.5 w-3.5 text-zinc-400" />;
    }
  };

  const spiValue = Number(support_priority_index) || 0;

  return (
    <>
      <div
        className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6 shadow-xl space-y-5"
        data-testid="pulserisk-support-card"
      >
        <RingBackground variant="card" />

        {/* Header */}
        <div className="relative z-10 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-[#FF7A18]/10 text-[#FF9A3D]">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-display text-base font-bold text-white">
                  Academic Momentum &amp; Support Priority
                </h3>
                <span data-testid="pulserisk-tier-badge">{getTierBadge()}</span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Deterministic support friction index calculated across academic dimensions.
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExplainModalOpen(true)}
            className="text-xs text-zinc-400 hover:text-white"
            data-testid="pulserisk-explain-btn"
          >
            <HelpCircle className="h-3.5 w-3.5 mr-1" />
            Why am I seeing this?
          </Button>
        </div>

        {/* SPI Meter & Dimension Bars */}
        <div className="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-6 items-center p-4 rounded-xl bg-[#111722]/70 border border-white/[0.08]">
          {/* Main SPI Value */}
          <div className="md:col-span-4 flex flex-col justify-center space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-400">
              Support Priority Index
            </span>
            <div className="flex items-baseline space-x-1.5">
              <span
                className="text-3xl font-extrabold tracking-tight font-mono text-white"
                data-testid="pulserisk-spi-score"
              >
                {spiValue.toFixed(1)}
              </span>
              <span className="text-xs font-semibold text-zinc-400">/ 100</span>
            </div>
            {safety_floors_triggered.length > 0 ? (
              <span className="text-[11px] text-rose-400 flex items-center gap-1 font-medium pt-1">
                <AlertTriangle className="h-3 w-3" /> Safety Floor Override
              </span>
            ) : (
              <span className="text-[11px] text-zinc-400 flex items-center gap-1 pt-1">
                <ShieldCheck className="h-3 w-3 text-emerald-400" /> Normal Algorithm Flow
              </span>
            )}
          </div>

          {/* Dimension Mini Contribution Bars */}
          <div className="md:col-span-8 space-y-2.5">
            {contributions.map((c) => {
              const weightPct = (Number(c.assigned_weight) * 100).toFixed(0);
              const contribPts = Number(c.weighted_contribution) || 0;
              const barWidth = Math.min(100, (contribPts / 40) * 100);

              return (
                <div key={c.dimension} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center space-x-1.5 font-medium text-zinc-300">
                      {getDimensionIcon(c.dimension)}
                      <span>{c.dimension.replace(/_/g, " ")}</span>
                      <span className="text-[10px] text-zinc-500 font-normal">
                        ({weightPct}% wt)
                      </span>
                    </span>
                    <span className="font-mono text-[11px] font-semibold text-white">
                      +{contribPts.toFixed(1)} pts
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/[0.08] overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] transition-all duration-300"
                      style={{ width: `${Math.max(2, barWidth)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Narrative & Institutional Transparency */}
        <div className="relative z-10 text-xs text-zinc-400 flex items-start space-x-2 pt-1 border-t border-white/[0.06]">
          <p className="leading-relaxed">
            {summary.explainability.summary}
          </p>
        </div>
      </div>

      {/* Explanation Modal */}
      <PulseRiskExplainModal
        isOpen={explainModalOpen}
        onClose={() => setExplainModalOpen(false)}
        summary={summary}
      />
    </>
  );
}
