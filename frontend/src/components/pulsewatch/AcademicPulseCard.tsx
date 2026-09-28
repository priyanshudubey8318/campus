"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PulseWatchSummary } from "@/types/pulsewatch";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RingBackground } from "@/components/ui/RingBackground";
import { PulseExplainModal } from "./PulseExplainModal";
import {
  Activity,
  CalendarCheck,
  FileCheck2,
  Award,
  HelpCircle,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Minus,
  AlertCircle,
} from "lucide-react";

interface AcademicPulseCardProps {
  summary: PulseWatchSummary | null;
  loading?: boolean;
}

export function AcademicPulseCard({
  summary,
  loading = false,
}: AcademicPulseCardProps) {
  const [explainModalOpen, setExplainModalOpen] = useState(false);

  if (loading) {
    return (
      <div
        className="rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6 shadow-sm animate-pulse"
        data-testid="academic-pulse-loading"
      >
        <div className="h-6 bg-white/[0.06] rounded w-1/4 mb-4" />
        <div className="h-4 bg-white/[0.04] rounded w-3/4 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-20 bg-white/[0.03] rounded-xl" />
          <div className="h-20 bg-white/[0.03] rounded-xl" />
          <div className="h-20 bg-white/[0.03] rounded-xl" />
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div
        className="rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6"
        data-testid="academic-pulse-empty"
      >
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#FF7A18]/10 text-[#FF9A3D]">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white font-display">
              Academic Pulse Initializing
            </h3>
            <p className="text-xs text-zinc-400">
              Deterministic behavioral monitoring establishes your engagement baseline as academic records accumulate.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const overall_status = summary?.overall_status || "NORMAL";
  const summary_text = summary?.summary_text || "Establishing longitudinal engagement baseline.";
  const signals = Array.isArray(summary?.signals) ? summary.signals : [];

  // Find granular signals
  const attendanceSignal = signals.find((s) => s.signal_type === "ATTENDANCE_CHANGE");
  const latenessSignal = signals.find((s) => s.signal_type === "SUBMISSION_LATENESS");
  const missedSignal = signals.find((s) => s.signal_type === "MISSED_ASSIGNMENT");
  const assessmentSignal = signals.find((s) => s.signal_type === "ASSESSMENT_PERFORMANCE");

  const getStatusBadge = () => {
    switch (overall_status) {
      case "NORMAL":
        return <Badge variant="success">STABLE ENGAGEMENT</Badge>;
      case "MILD_CHANGE":
        return <Badge variant="warning">MILD ENGAGEMENT CHANGE</Badge>;
      case "MODERATE_CHANGE":
        return <Badge variant="warning">MODERATE ENGAGEMENT CHANGE</Badge>;
      case "SIGNIFICANT_CHANGE":
        return <Badge variant="danger">SIGNIFICANT ENGAGEMENT SHIFT</Badge>;
      default:
        return <Badge variant="neutral">{overall_status}</Badge>;
    }
  };

  const formatDelta = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined) return "No Change";
    if (delta > 0) return `+${delta.toFixed(1)}%`;
    if (delta < 0) return `${delta.toFixed(1)}%`;
    return "0.0%";
  };

  return (
    <>
      <div
        className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6 shadow-xl space-y-5"
        data-testid="academic-pulse-section"
      >
        <RingBackground variant="card" />

        {/* Header Row */}
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-[#FF7A18]/10 text-[#FF9A3D]">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-display text-base font-bold text-white">
                  Academic Pulse
                </h3>
                <span data-testid="academic-pulse-status">{getStatusBadge()}</span>
              </div>
              <p className="text-xs text-zinc-400">
                Deterministic behavioral monitoring relative to your verified historical baseline.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              className="text-xs space-x-1.5"
              onClick={() => setExplainModalOpen(true)}
              data-testid="academic-pulse-explain-btn"
            >
              <HelpCircle className="h-3.5 w-3.5 text-zinc-400" />
              <span>Why am I seeing this?</span>
            </Button>
            <Link href="/student/academics?tab=pulse">
              <Button size="sm" variant="ghost" className="text-xs space-x-1 text-zinc-300 hover:text-white">
                <span>View Details</span>
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Descriptive Summary Box */}
        <div className="relative z-10 p-3.5 rounded-xl bg-[#111722]/80 border border-white/[0.06] text-xs text-zinc-300">
          <p data-testid="academic-pulse-summary-text">{summary_text}</p>
        </div>

        {/* 3 Metric Pills Grid */}
        <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 1. Attendance Signal */}
          <div
            className="p-3.5 rounded-xl border border-white/[0.08] bg-[#111722]/60 space-y-1.5 hover-lift transition"
            data-testid="pulse-metric-attendance"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-zinc-300">
              <span className="flex items-center space-x-1.5">
                <CalendarCheck className="h-4 w-4 text-[#FF9A3D]" />
                <span>Attendance Stability</span>
              </span>
              <span className="font-mono text-[11px] text-zinc-400">
                Δ {formatDelta(attendanceSignal?.delta_value)}
              </span>
            </div>
            <div className="flex items-baseline justify-between pt-1">
              <div className="text-lg font-bold font-mono text-white">
                {attendanceSignal?.current_value !== null && attendanceSignal?.current_value !== undefined
                  ? `${Number(attendanceSignal.current_value).toFixed(1)}%`
                  : "N/A"}
              </div>
              <div className="text-[11px] text-zinc-400">
                Baseline:{" "}
                {attendanceSignal?.baseline_value !== null && attendanceSignal?.baseline_value !== undefined
                  ? `${Number(attendanceSignal.baseline_value).toFixed(1)}%`
                  : "Establishing"}
              </div>
            </div>
            <div className="text-[10px] text-zinc-500">
              Consecutive absences: {attendanceSignal?.evidence_payload?.consecutive_absences_count ?? 0}
            </div>
          </div>

          {/* 2. Coursework Lateness / Submissions */}
          <div
            className="p-3.5 rounded-xl border border-white/[0.08] bg-[#111722]/60 space-y-1.5 hover-lift transition"
            data-testid="pulse-metric-coursework"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-zinc-300">
              <span className="flex items-center space-x-1.5">
                <FileCheck2 className="h-4 w-4 text-blue-400" />
                <span>Coursework Pacing</span>
              </span>
              <span className="font-mono text-[11px] text-zinc-400">
                {missedSignal?.evidence_payload?.missed_assignments_count ?? 0} Missed
              </span>
            </div>
            <div className="flex items-baseline justify-between pt-1">
              <div className="text-lg font-bold font-mono text-white">
                {latenessSignal?.current_value !== null && latenessSignal?.current_value !== undefined
                  ? `${Number(latenessSignal.current_value).toFixed(1)}% On-time`
                  : "100.0% On-time"}
              </div>
              <div className="text-[11px] text-zinc-400">
                Late: {latenessSignal?.evidence_payload?.late_submissions_count ?? 0}
              </div>
            </div>
            <div className="text-[10px] text-zinc-500">
              Eligible tasks: {latenessSignal?.evidence_payload?.eligible_assignments_count ?? 0}
            </div>
          </div>

          {/* 3. Assessment Performance */}
          <div
            className="p-3.5 rounded-xl border border-white/[0.08] bg-[#111722]/60 space-y-1.5 hover-lift transition"
            data-testid="pulse-metric-assessment"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-zinc-300">
              <span className="flex items-center space-x-1.5">
                <Award className="h-4 w-4 text-purple-400" />
                <span>Evaluation Marks</span>
              </span>
              <span className="font-mono text-[11px] text-zinc-400">
                Δ {formatDelta(assessmentSignal?.delta_value)}
              </span>
            </div>
            <div className="flex items-baseline justify-between pt-1">
              <div className="text-lg font-bold font-mono text-white">
                {assessmentSignal?.current_value !== null && assessmentSignal?.current_value !== undefined
                  ? `${Number(assessmentSignal.current_value).toFixed(1)}%`
                  : "No Evaluations"}
              </div>
              <div className="text-[11px] text-zinc-400">
                Baseline:{" "}
                {assessmentSignal?.baseline_value !== null && assessmentSignal?.baseline_value !== undefined
                  ? `${Number(assessmentSignal.baseline_value).toFixed(1)}%`
                  : "Establishing"}
              </div>
            </div>
            <div className="text-[10px] text-zinc-500">
              Assessment absences: {assessmentSignal?.evidence_payload?.has_assessment_absence ? 1 : 0}
            </div>
          </div>
        </div>

        {/* Institutional Non-punitive Micro-notice */}
        <div className="relative z-10 text-[11px] text-zinc-500 flex items-center justify-between pt-1 border-t border-white/[0.06]">
          <span>
            Window: {summary.observation_window_days} days &bull; Observation: {summary.window_start_date} → {summary.window_end_date}
          </span>
          <span className="font-mono text-[10px] text-zinc-500">Deterministic Monitoring Foundation</span>
        </div>
      </div>

      <PulseExplainModal
        isOpen={explainModalOpen}
        onClose={() => setExplainModalOpen(false)}
        summary={summary}
      />
    </>
  );
}
