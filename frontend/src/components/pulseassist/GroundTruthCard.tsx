"use client";

import React from "react";
import { StudentMetricsCardData } from "@/types/pulseassist";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ShieldCheck, CalendarCheck, Award, AlertTriangle } from "lucide-react";

interface GroundTruthCardProps {
  metrics: StudentMetricsCardData;
}

export function GroundTruthCard({ metrics }: GroundTruthCardProps) {
  const getTierVariant = (tier?: string | null) => {
    switch (tier) {
      case "TIER_0":
        return "success";
      case "TIER_1":
        return "primary";
      case "TIER_2":
        return "warning";
      case "TIER_3":
        return "danger";
      default:
        return "neutral";
    }
  };

  const formatTierLabel = (tier?: string | null) => {
    switch (tier) {
      case "TIER_0":
        return "Tier 0 (Standard Standing)";
      case "TIER_1":
        return "Tier 1 (Mild Academic Monitoring)";
      case "TIER_2":
        return "Tier 2 (Targeted Academic Advisory)";
      case "TIER_3":
        return "Tier 3 (Intensive Academic Support)";
      default:
        return tier || "Not Evaluated";
    }
  };

  return (
    <Card
      className="my-3 border-white/[0.08] bg-[#0D1117] shadow-sm"
      data-testid="ground-truth-card"
    >
      <CardHeader className="py-2.5 px-4 border-b border-white/[0.06] bg-[#111722]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="h-4 w-4 text-[#FF7A18]" />
            <CardTitle className="text-xs font-mono font-bold text-[#F5F7FA] uppercase tracking-wide">
              Official Academic Records (Ground Truth)
            </CardTitle>
          </div>
          <span className="text-[10px] text-[#A7AFBD] font-mono">
            As of: {metrics.as_of_date}
          </span>
        </div>
      </CardHeader>
      <CardContent className="p-4 space-y-3">
        {/* Metric Badges Grid */}
        <div className="grid grid-cols-3 gap-3">
          {/* Attendance */}
          <div className="p-2.5 rounded-lg bg-[#151B24] border border-white/10">
            <div className="flex items-center space-x-1.5 text-[#A7AFBD] mb-1 font-mono">
              <CalendarCheck className="h-3.5 w-3.5 text-[#FF7A18]" />
              <span className="text-[11px] font-medium">Attendance</span>
            </div>
            <div className="text-base font-bold text-[#F5F7FA] font-mono" data-testid="metric-attendance">
              {metrics.attendance_pct !== null && metrics.attendance_pct !== undefined
                ? `${metrics.attendance_pct}%`
                : "N/A"}
            </div>
            <span className="text-[9px] text-[#6F7785]">Institutional records</span>
          </div>

          {/* CGPA */}
          <div className="p-2.5 rounded-lg bg-[#151B24] border border-white/10">
            <div className="flex items-center space-x-1.5 text-[#A7AFBD] mb-1 font-mono">
              <Award className="h-3.5 w-3.5 text-[#FF9A3D]" />
              <span className="text-[11px] font-medium">CGPA</span>
            </div>
            <div className="text-base font-bold text-[#F5F7FA] font-mono" data-testid="metric-cgpa">
              {metrics.cgpa !== null && metrics.cgpa !== undefined
                ? metrics.cgpa.toFixed(2)
                : "N/A"}
            </div>
            <span className="text-[9px] text-[#6F7785]">Registrar cumulative</span>
          </div>

          {/* Support Priority Tier */}
          <div className="p-2.5 rounded-lg bg-[#151B24] border border-white/10">
            <div className="flex items-center space-x-1.5 text-[#A7AFBD] mb-1 font-mono">
              <AlertTriangle className="h-3.5 w-3.5 text-[#FFB020]" />
              <span className="text-[11px] font-medium">Support Tier</span>
            </div>
            <div className="mt-0.5">
              <Badge variant={getTierVariant(metrics.spi_tier)} className="text-[10px] px-1.5 py-0.5 font-mono" data-testid="metric-spi-tier">
                {metrics.spi_tier ? metrics.spi_tier.replace("_", " ") : "Active"}
              </Badge>
            </div>
            <span className="text-[9px] text-[#6F7785] block mt-1">Deterministic policy</span>
          </div>
        </div>

        {/* Mandatory Ground Truth Label */}
        <div
          className="rounded-md border border-[#FF7A18]/30 bg-[#FF7A18]/10 p-2 text-center"
          data-testid="ground-truth-label"
        >
          <p className="text-[10px] font-semibold text-[#FF9A3D]">
            {metrics.disclaimer ||
              "Verified ground-truth data from registrar/attendance systems. Not an AI estimate."}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
