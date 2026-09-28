"use client";

import React, { useState } from "react";
import { PulseWatchSummary, BehaviorEvent } from "@/types/pulsewatch";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { PulseExplainModal } from "./PulseExplainModal";
import {
  Activity,
  Calendar,
  Users,
  AlertCircle,
  HelpCircle,
  Layers,
  FileCheck2,
  Clock,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  Award,
} from "lucide-react";

interface PulseTimelineViewProps {
  summary: PulseWatchSummary | null;
  events: BehaviorEvent[];
  loading?: boolean;
}

export function PulseTimelineView({
  summary,
  events,
  loading = false,
}: PulseTimelineViewProps) {
  const [explainModalOpen, setExplainModalOpen] = useState(false);

  if (loading) {
    return (
      <div className="space-y-6" data-testid="pulse-timeline-loading">
        <div className="p-8 rounded-2xl bg-[#0D1117] border border-white/[0.08] animate-pulse space-y-4">
          <div className="h-6 bg-white/[0.06] rounded w-1/3" />
          <div className="h-4 bg-white/[0.04] rounded w-2/3" />
        </div>
      </div>
    );
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "NORMAL":
        return <Badge variant="success">NORMAL</Badge>;
      case "MILD_CHANGE":
        return <Badge variant="warning">MILD CHANGE</Badge>;
      case "MODERATE_CHANGE":
        return <Badge variant="warning">MODERATE CHANGE</Badge>;
      case "SIGNIFICANT_CHANGE":
        return <Badge variant="danger">SIGNIFICANT CHANGE</Badge>;
      default:
        return <Badge variant="neutral">{severity}</Badge>;
    }
  };

  const formatDelta = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined) return "0.0%";
    if (delta > 0) return `+${delta.toFixed(1)}%`;
    if (delta < 0) return `${delta.toFixed(1)}%`;
    return "0.0%";
  };

  return (
    <div className="space-y-6" data-testid="academic-pulse-tab-content">
      {/* 1. Header Card with Explainability Trigger */}
      <Card className="relative overflow-hidden border-white/[0.08] bg-[#0D1117] shadow-xl">
        <RingBackground variant="card" />
        <CardHeader className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-[#FF9A3D]" />
              <CardTitle className="text-base font-display text-white">PulseWatch Behavioral Monitoring</CardTitle>
              {summary && getSeverityBadge(summary.overall_status)}
            </div>
            <CardDescription className="text-xs mt-1 text-zinc-400">
              Deterministic, transparent indicators tracking academic engagement relative to your historical baseline.
            </CardDescription>
          </div>
          {summary && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs space-x-1.5"
              onClick={() => setExplainModalOpen(true)}
              data-testid="timeline-explain-btn"
            >
              <HelpCircle className="h-3.5 w-3.5 text-zinc-400" />
              <span>Explain Calculation</span>
            </Button>
          )}
        </CardHeader>

        {summary && (
          <CardContent className="relative z-10 space-y-3 pt-0">
            <div className="p-3.5 rounded-xl bg-[#111722]/80 border border-white/[0.06] text-xs text-zinc-300">
              <p className="font-medium">{summary.summary_text}</p>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-400">
              <span>
                <strong className="text-zinc-300">Observation Window:</strong> {summary.observation_window_days} days ({summary.window_start_date} → {summary.window_end_date})
              </span>
              <span>
                <strong className="text-zinc-300">Baseline Window:</strong> {summary.baseline_start_date} → {summary.baseline_end_date}
              </span>
              <span>
                <strong className="text-zinc-300">Algorithm:</strong> {summary.algorithm_version}
              </span>
            </div>
          </CardContent>
        )}
      </Card>

      {/* 2. Context Cards Grid: Secondary Cohort Context & Academic Context */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cohort Context Card */}
          <Card className="border-white/[0.08] bg-[#0D1117]" data-testid="cohort-context-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center space-x-2 text-white font-display">
                <Users className="h-4 w-4 text-blue-400" />
                <span>Secondary Cohort Context</span>
              </CardTitle>
              <CardDescription className="text-xs text-zinc-400">
                Population reference values for context. Never overrides personal baseline.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2.5 rounded-lg bg-[#111722] border border-white/[0.06]">
                  <div className="text-[10px] text-zinc-400 font-medium">Cohort Attendance</div>
                  <div className="text-sm font-bold font-mono text-white mt-0.5">
                    {summary.cohort_context.cohort_attendance_rate !== null && summary.cohort_context.cohort_attendance_rate !== undefined
                      ? `${Number(summary.cohort_context.cohort_attendance_rate).toFixed(1)}%`
                      : "N/A"}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-[#111722] border border-white/[0.06]">
                  <div className="text-[10px] text-zinc-400 font-medium">Cohort Submission</div>
                  <div className="text-sm font-bold font-mono text-white mt-0.5">
                    {summary.cohort_context.cohort_submission_rate !== null && summary.cohort_context.cohort_submission_rate !== undefined
                      ? `${Number(summary.cohort_context.cohort_submission_rate).toFixed(1)}%`
                      : "N/A"}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-[#111722] border border-white/[0.06]">
                  <div className="text-[10px] text-zinc-400 font-medium">Cohort Marks Avg</div>
                  <div className="text-sm font-bold font-mono text-white mt-0.5">
                    {summary.cohort_context.cohort_assessment_average !== null && summary.cohort_context.cohort_assessment_average !== undefined
                      ? `${Number(summary.cohort_context.cohort_assessment_average).toFixed(1)}%`
                      : "N/A"}
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-zinc-400 italic">
                {summary.cohort_context.context_note}
              </p>
            </CardContent>
          </Card>

          {/* Academic Context Card */}
          <Card className="border-white/[0.08] bg-[#0D1117]" data-testid="academic-context-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center space-x-2 text-white font-display">
                <Calendar className="h-4 w-4 text-purple-400" />
                <span>Academic Environmental Context</span>
              </CardTitle>
              <CardDescription className="text-xs text-zinc-400">
                Term pacing factors and scheduled academic milestones.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="space-y-2">
                <div className="flex justify-between py-1 border-b border-white/[0.06]">
                  <span className="text-zinc-400">Upcoming Assessments:</span>
                  <span className="font-semibold text-white">
                    {summary.academic_context.upcoming_assessments_count} scheduled
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/[0.06]">
                  <span className="text-zinc-400">Deadline Clustering:</span>
                  <span className="font-semibold text-white">
                    {summary.academic_context.assignment_deadline_clustering ? "Detected (3+ tasks in window)" : "Normal Distribution"}
                  </span>
                </div>
                <div className="pt-1">
                  <span className="text-[11px] text-zinc-400 block mb-1 font-medium">Deferred Context Modules:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {summary.academic_context.untracked_contexts.map((ctx) => (
                      <Badge key={ctx} variant="neutral" className="text-[10px]">
                        {ctx.replace(/_/g, " ")}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 3. Historical Behavior Events Timeline */}
      <Card className="border-white/[0.08] bg-[#0D1117]">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-[#FF9A3D]" />
            <CardTitle className="text-base font-display text-white">Behavioral Shift Timeline</CardTitle>
          </div>
          <CardDescription className="text-xs text-zinc-400">
            Persisted engagement shift evaluations recorded during periodic or explicit monitoring runs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div data-testid="empty-behavior-timeline">
              <EmptyState
                icon={Activity}
                title="No Behavioral Shifts Recorded"
                description="Your academic engagement has remained consistent with your personal historical baseline. No shift events are currently registered."
              />
            </div>
          ) : (
            <div className="space-y-4" data-testid="behavior-timeline-list">
              {events.map((ev) => (
                <div
                  key={ev.id}
                  className="p-4 rounded-xl border border-white/[0.08] bg-[#111722]/60 space-y-3 hover-lift transition"
                  data-testid="behavior-event-item"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-xs text-white">
                        {ev.event_type.replace(/_/g, " ")}
                      </span>
                      {getSeverityBadge(ev.severity)}
                    </div>
                    <div className="text-[11px] text-zinc-400 font-mono">
                      Detected: {new Date(ev.detected_at).toLocaleDateString()}
                    </div>
                  </div>

                  <p className="text-xs text-zinc-300">
                    {ev.summary_text}
                  </p>

                  <div className="text-[11px] text-zinc-400 flex items-center space-x-2">
                    <span>
                      Window: {ev.observation_window_days}d ({ev.window_start_date} → {ev.window_end_date})
                    </span>
                    <span>&bull;</span>
                    <span>Algorithm: {ev.algorithm_version}</span>
                  </div>

                  {/* Evidence Pills */}
                  {ev.evidence && ev.evidence.length > 0 && (
                    <div className="pt-2 border-t border-white/[0.06] flex flex-wrap gap-2">
                      {ev.evidence.map((sig, idx) => (
                        <div
                          key={idx}
                          className="px-2.5 py-1 rounded-lg bg-[#0D1117] border border-white/[0.08] text-[11px] flex items-center space-x-2"
                        >
                          <span className="font-semibold text-zinc-300">
                            {sig.metric_name}:
                          </span>
                          <span className="font-mono text-white">
                            {sig.current_value !== null ? `${Number(sig.current_value).toFixed(1)}%` : "N/A"}
                          </span>
                          <span className="text-[10px] text-zinc-400">
                            (Δ {formatDelta(sig.delta_value)})
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Institutional Non-Punitive Assurance Card */}
      <div className="p-4 rounded-xl bg-[#111722]/60 border border-white/[0.08] flex items-start space-x-3 text-xs text-zinc-400">
        <ShieldCheck className="h-5 w-5 text-[#FF9A3D] flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-white">
            Ethical AI &amp; Engagement Policy Assurance
          </span>
          <p className="leading-relaxed text-zinc-300">
            PulseWatch indicators are deterministic tools engineered strictly for academic engagement continuity. The platform does not score dropout probability, perform psychological profiling, or recommend disciplinary sanctions.
          </p>
        </div>
      </div>

      <PulseExplainModal
        isOpen={explainModalOpen}
        onClose={() => setExplainModalOpen(false)}
        summary={summary}
      />
    </div>
  );
}
