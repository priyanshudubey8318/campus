"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatsCard } from "@/components/ui/StatsCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { PulseRiskExplainModal } from "@/components/pulserisk/PulseRiskExplainModal";
import { api, ApiError } from "@/lib/api/client";
import {
  CohortPriorityItem,
  CohortPrioritiesPage,
  PriorityTier,
  PulseRiskSummary,
  RiskPolicy,
} from "@/types/pulserisk";
import {
  Compass,
  Users,
  Search,
  Filter,
  RefreshCw,
  AlertTriangle,
  Scale,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Eye,
  Layers,
  FileCheck2,
  CalendarCheck,
  Award,
  Clock,
  Briefcase,
  PlusCircle,
} from "lucide-react";

export default function AdvisorPortalPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Roster data & pagination
  const [rosterPage, setRosterPage] = useState<CohortPrioritiesPage | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [activePolicy, setActivePolicy] = useState<RiskPolicy | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTier, setSelectedTier] = useState<string>("ALL");
  const [selectedDriver, setSelectedDriver] = useState<string>("ALL");

  // Decomposition Modal State
  const [selectedStudentSummary, setSelectedStudentSummary] = useState<PulseRiskSummary | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);

  // Load cohort priorities and policy
  const loadRosterData = useCallback(async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);

      const [policyRes, prioritiesRes] = await Promise.all([
        api.getActiveRiskPolicy().catch(() => null),
        api.getCohortPriorities({
          priorityTier: selectedTier !== "ALL" ? selectedTier : undefined,
          primaryDriver: selectedDriver !== "ALL" ? selectedDriver : undefined,
          page,
          limit: 25,
        }),
      ]);

      setActivePolicy(policyRes);
      setRosterPage(prioritiesRes);
      setCurrentPage(page);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to retrieve cohort support priority records");
      }
    } finally {
      setLoading(false);
    }
  }, [selectedTier, selectedDriver]);

  useEffect(() => {
    loadRosterData(1);
  }, [loadRosterData]);

  // Open decomposition audit modal
  const handleOpenDecomposition = async (studentId: string) => {
    try {
      setModalLoading(true);
      const summary = await api.getPulseRiskCurrent(studentId, 14);
      setSelectedStudentSummary(summary);
      setModalOpen(true);
    } catch (err) {
      console.error("Failed to load student decomposition:", err);
    } finally {
      setModalLoading(false);
    }
  };

  // Filtered items based on client-side search query
  const displayItems = (rosterPage?.items || []).filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.student_name.toLowerCase().includes(q) ||
      item.roll_number.toLowerCase().includes(q) ||
      (item.program_code && item.program_code.toLowerCase().includes(q))
    );
  });

  const getTierBadge = (tier: PriorityTier) => {
    switch (tier) {
      case "URGENT_PRIORITY":
        return <Badge variant="danger">Urgent Priority</Badge>;
      case "ELEVATED_PRIORITY":
        return <Badge variant="warning">Elevated Priority</Badge>;
      case "MODERATE_PRIORITY":
        return <Badge variant="primary">Moderate Priority</Badge>;
      case "LOW_PRIORITY":
        return <Badge variant="success">Standard Pacing</Badge>;
      default:
        return <Badge variant="neutral">{tier}</Badge>;
    }
  };

  // Tally tiers for KPI metrics
  const urgentCount = (rosterPage?.items || []).filter((i) => i.priority_tier === "URGENT_PRIORITY").length;
  const elevatedCount = (rosterPage?.items || []).filter((i) => i.priority_tier === "ELEVATED_PRIORITY").length;
  const moderateCount = (rosterPage?.items || []).filter((i) => i.priority_tier === "MODERATE_PRIORITY").length;
  const lowCount = (rosterPage?.items || []).filter((i) => i.priority_tier === "LOW_PRIORITY").length;

  return (
    <ProtectedRoute requiredRoles={["ADVISOR", "FACULTY", "ADMIN", "SUPER_ADMIN"]}>
      <div className="space-y-6" data-testid="advisor-portal">
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                Academic Support Priority &amp; Advising Roster
              </h1>
              <Badge variant="primary">SUPPORT ROSTER</Badge>
            </div>
            <p className="text-sm text-surface-400 mt-1">
              Deterministic, explainable multi-signal support prioritization for student cohorts.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {activePolicy && (
              <div className="px-3 py-1.5 rounded-lg border border-white/10 bg-[#111722] text-xs text-surface-300">
                <span className="font-semibold text-white">Active Policy:</span>{" "}
                <span className="text-[#FF9A3D]">{activePolicy.name}</span> ({activePolicy.policy_version})
              </div>
            )}
            <Link href="/cases">
              <Button size="sm" className="text-xs space-x-1.5 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0">
                <Briefcase className="h-3.5 w-3.5" />
                <span>Support Cases</span>
              </Button>
            </Link>
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadRosterData(currentPage)}
              disabled={loading}
              className="border-white/10 hover:bg-white/5 text-surface-200 text-xs"
              data-testid="refresh-roster-btn"
            >
              <RefreshCw className={`h-4 w-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-400 text-xs flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Urgent Priority"
            value={urgentCount}
            subtitle="Immediate advising intervention"
            icon={AlertTriangle}
            iconColor="text-rose-500"
            badge={{ text: "High Priority", variant: "danger" }}
            testId="kpi-urgent-count"
          />
          <StatsCard
            title="Elevated Priority"
            value={elevatedCount}
            subtitle="Pacing support recommended"
            icon={Scale}
            iconColor="text-amber-500"
            badge={{ text: "Active Friction", variant: "warning" }}
            testId="kpi-elevated-count"
          />
          <StatsCard
            title="Moderate Opportunity"
            value={moderateCount}
            subtitle="Emerging engagement shifts"
            icon={Layers}
            iconColor="text-blue-500"
            badge={{ text: "Monitored", variant: "primary" }}
            testId="kpi-moderate-count"
          />
          <StatsCard
            title="Standard Pacing"
            value={lowCount}
            subtitle="Consistent engagement"
            icon={ShieldCheck}
            iconColor="text-emerald-500"
            badge={{ text: "Stable", variant: "success" }}
            testId="kpi-stable-count"
          />
        </div>

        {/* Filter and Search Controls */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Search */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
                <input
                  type="text"
                  placeholder="Search students by name, roll number, or program..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-white/10 bg-[#0D1117] text-white placeholder-surface-500 focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                  data-testid="roster-search-input"
                />
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center space-x-1.5 text-xs text-surface-400">
                  <Filter className="h-3.5 w-3.5" />
                  <span>Tier:</span>
                  <select
                    value={selectedTier}
                    onChange={(e) => setSelectedTier(e.target.value)}
                    className="px-2.5 py-1.5 text-xs rounded-lg border border-white/10 bg-[#0D1117] text-white focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                    data-testid="filter-tier-select"
                  >
                    <option value="ALL">All Tiers</option>
                    <option value="URGENT_PRIORITY">Urgent Priority</option>
                    <option value="ELEVATED_PRIORITY">Elevated Priority</option>
                    <option value="MODERATE_PRIORITY">Moderate Priority</option>
                    <option value="LOW_PRIORITY">Standard Pacing</option>
                  </select>
                </div>

                <div className="flex items-center space-x-1.5 text-xs text-surface-400">
                  <span>Driver:</span>
                  <select
                    value={selectedDriver}
                    onChange={(e) => setSelectedDriver(e.target.value)}
                    className="px-2.5 py-1.5 text-xs rounded-lg border border-white/10 bg-[#0D1117] text-white focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                    data-testid="filter-driver-select"
                  >
                    <option value="ALL">All Drivers</option>
                    <option value="ATTENDANCE">Attendance</option>
                    <option value="COURSEWORK">Coursework</option>
                    <option value="ASSESSMENTS">Assessments</option>
                    <option value="LONGITUDINAL_PERSISTENCE">Persistence</option>
                  </select>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Triage Roster Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base flex items-center space-x-2 text-white font-display">
                <Users className="h-5 w-5 text-[#FF9A3D]" />
                <span>Cohort Prioritization Roster</span>
              </CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Students ordered by Support Priority Index (SPI) score and safety floor status.
              </CardDescription>
            </div>
            <span className="text-xs text-surface-400">
              Showing {displayItems.length} of {rosterPage?.total || 0} students
            </span>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-xs text-surface-400" data-testid="roster-loading">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#FF9A3D]" />
                Calculating deterministic cohort prioritizations...
              </div>
            ) : displayItems.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={Compass}
                  title="No Cohort Prioritizations Found"
                  description="No evaluated student priority snapshots matched the active filter criteria."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse" data-testid="advisor-roster-table">
                  <thead>
                    <tr className="border-b border-white/10 bg-[#111722] text-[11px] text-surface-400 uppercase tracking-wider font-mono">
                      <th className="py-3 px-4 font-semibold">Student</th>
                      <th className="py-3 px-4 font-semibold">Program / Section</th>
                      <th className="py-3 px-4 font-semibold">Support Priority (SPI)</th>
                      <th className="py-3 px-4 font-semibold">Priority Tier</th>
                      <th className="py-3 px-4 font-semibold">Primary Driver</th>
                      <th className="py-3 px-4 font-semibold">Data Quality</th>
                      <th className="py-3 px-4 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-xs">
                    {displayItems.map((item) => {
                      const spi = Number(item.support_priority_index) || 0;
                      return (
                        <tr
                          key={item.student_id}
                          className="hover:bg-white/[0.02] transition-colors"
                          data-testid={`roster-row-${item.student_id}`}
                        >
                          {/* Student Info */}
                          <td className="py-3.5 px-4 font-medium text-white">
                            <div>{item.student_name}</div>
                            <div className="text-[11px] text-surface-400 font-mono">
                              {item.roll_number}
                            </div>
                          </td>

                          {/* Program & Section */}
                          <td className="py-3.5 px-4 text-surface-300">
                            <div>{item.program_code || "General"}</div>
                            <div className="text-[11px] text-surface-400">
                              Section {item.section_name || "A"}
                            </div>
                          </td>

                          {/* SPI Meter */}
                          <td className="py-3.5 px-4">
                            <div className="space-y-1 max-w-[140px]">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-bold font-mono text-white">
                                  {spi.toFixed(1)}
                                </span>
                                <span className="text-[10px] text-surface-500">/ 100</span>
                              </div>
                              <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    item.priority_tier === "URGENT_PRIORITY"
                                      ? "bg-[#FF4D4D]"
                                      : item.priority_tier === "ELEVATED_PRIORITY"
                                      ? "bg-[#FF9A3D]"
                                      : item.priority_tier === "MODERATE_PRIORITY"
                                      ? "bg-blue-400"
                                      : "bg-[#28C76F]"
                                  }`}
                                  style={{ width: `${Math.max(4, Math.min(100, spi))}%` }}
                                />
                              </div>
                            </div>
                          </td>

                          {/* Tier Badge */}
                          <td className="py-3.5 px-4">
                            {getTierBadge(item.priority_tier)}
                          </td>

                          {/* Primary Driver */}
                          <td className="py-3.5 px-4 font-medium text-surface-200">
                            {item.primary_driver ? (
                              <span className="uppercase text-[11px] px-2 py-0.5 rounded bg-[#111722] border border-white/10 text-surface-300 font-mono">
                                {item.primary_driver.replace(/_/g, " ")}
                              </span>
                            ) : (
                              <span className="text-surface-500">—</span>
                            )}
                          </td>

                          {/* Data Quality & Confidence */}
                          <td className="py-3.5 px-4 text-surface-400 text-[11px]">
                            <div className="uppercase font-semibold text-surface-200">
                              {item.data_quality.replace(/_/g, " ")}
                            </div>
                            <div>{(Number(item.confidence_score) * 100).toFixed(0)}% confidence</div>
                          </td>

                          {/* Action Button */}
                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleOpenDecomposition(item.student_id)}
                                className="text-xs border-white/10 hover:bg-white/5 text-surface-200"
                                data-testid={`view-decomp-${item.student_id}`}
                              >
                                <Eye className="h-3.5 w-3.5 mr-1 text-[#FF9A3D]" />
                                Decomposition
                              </Button>
                              <Link href={`/cases?createForStudent=${item.student_id}&name=${encodeURIComponent(item.student_name)}`}>
                                <Button size="sm" className="text-xs space-x-1 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0">
                                  <PlusCircle className="h-3.5 w-3.5" />
                                  <span>Open Case</span>
                                </Button>
                              </Link>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Controls */}
            {rosterPage && rosterPage.pages > 1 && (
              <div className="p-4 border-t border-white/10 flex items-center justify-between text-xs text-surface-400">
                <div>
                  Page {rosterPage.page} of {rosterPage.pages} ({rosterPage.total} students)
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadRosterData(currentPage - 1)}
                    disabled={currentPage <= 1 || loading}
                    className="border-white/10 hover:bg-white/5 text-surface-200"
                  >
                    <ChevronLeft className="h-3.5 w-3.5 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadRosterData(currentPage + 1)}
                    disabled={currentPage >= rosterPage.pages || loading}
                    className="border-white/10 hover:bg-white/5 text-surface-200"
                  >
                    Next
                    <ChevronRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Explainability Audit Modal */}
        <PulseRiskExplainModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          summary={selectedStudentSummary}
        />
      </div>
    </ProtectedRoute>
  );
}
