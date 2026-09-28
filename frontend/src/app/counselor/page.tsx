"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatsCard } from "@/components/ui/StatsCard";
import { CardSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import { SupportCase, CaseType, CasePriority, CaseStatus } from "@/types/pulsecase";
import {
  HeartHandshake,
  ShieldCheck,
  Lock,
  PlusCircle,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar,
  UserCheck,
  Eye,
} from "lucide-react";

export default function CounselorPortalPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cases, setCases] = useState<SupportCase[]>([]);

  // Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");

  // Create Case Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState({
    student_id: "",
    priority: "MEDIUM" as CasePriority,
    reason: "",
  });

  const loadCounselorCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch cases accessible to counselor
      const data = await api.getCases({ limit: 100 });
      setCases(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to retrieve counselor intervention cases.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCounselorCases();
  }, [loadCounselorCases]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.student_id.trim()) {
      setCreateError("Student ID or enrollment reference is required.");
      return;
    }
    if (createForm.reason.trim().length < 5) {
      setCreateError("Reason must be at least 5 characters.");
      return;
    }

    try {
      setCreateSubmitting(true);
      setCreateError(null);
      await api.createCase({
        student_id: createForm.student_id.trim(),
        case_type: "WELLBEING_REFERRAL",
        priority: createForm.priority,
        reason: createForm.reason.trim(),
      });
      setIsCreateModalOpen(false);
      setCreateForm({
        student_id: "",
        priority: "MEDIUM",
        reason: "",
      });
      await loadCounselorCases();
    } catch (err) {
      if (err instanceof ApiError) {
        setCreateError(err.message);
      } else {
        setCreateError("Failed to initiate wellbeing support case.");
      }
    } finally {
      setCreateSubmitting(false);
    }
  };

  // Filtered cases
  const filteredCases = cases.filter((c) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      c.case_number.toLowerCase().includes(q) ||
      (c.student_name && c.student_name.toLowerCase().includes(q)) ||
      (c.student_enrollment_number && c.student_enrollment_number.toLowerCase().includes(q)) ||
      c.reason.toLowerCase().includes(q);

    const matchesStatus = statusFilter === "ALL" || c.status === statusFilter;
    const matchesPriority = priorityFilter === "ALL" || c.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  // KPI Calculations
  const urgentCount = cases.filter((c) => c.priority === "URGENT" || c.priority === "HIGH").length;
  const activeCount = cases.filter((c) => c.status === "OPEN" || c.status === "IN_PROGRESS").length;
  const resolvedCount = cases.filter((c) => c.status === "RESOLVED" || c.status === "CLOSED").length;

  const getPriorityBadge = (p: CasePriority | string) => {
    switch (p) {
      case "URGENT":
        return <Badge variant="danger">URGENT</Badge>;
      case "HIGH":
        return <Badge variant="warning">HIGH</Badge>;
      case "MEDIUM":
        return <Badge variant="primary">MEDIUM</Badge>;
      case "LOW":
        return <Badge variant="success">LOW</Badge>;
      default:
        return <Badge variant="neutral">{p}</Badge>;
    }
  };

  const getStatusBadge = (s: CaseStatus | string) => {
    switch (s) {
      case "OPEN":
        return <Badge variant="primary">OPEN</Badge>;
      case "IN_PROGRESS":
        return <Badge variant="warning">IN PROGRESS</Badge>;
      case "WAITING_FOR_STUDENT":
        return <Badge variant="neutral">WAITING FOR STUDENT</Badge>;
      case "FOLLOW_UP_SCHEDULED":
        return <Badge variant="neutral">FOLLOW UP</Badge>;
      case "RESOLVED":
        return <Badge variant="success">RESOLVED</Badge>;
      case "CLOSED":
        return <Badge variant="neutral">CLOSED</Badge>;
      default:
        return <Badge variant="neutral">{s}</Badge>;
    }
  };

  return (
    <ProtectedRoute requiredRoles={["COUNSELOR", "SUPER_ADMIN"]}>
      <div className="space-y-6" data-testid="counselor-portal">
        {/* Header Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 md:p-8 shadow-sm">
          <RingBackground variant="hero" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="primary">
                  COUNSELOR WORKSPACE
                </Badge>
                <div className="flex items-center space-x-1 text-xs text-[#FF9A3D] font-medium bg-[#FF7A18]/10 px-2 py-0.5 rounded border border-[#FF7A18]/20">
                  <Lock className="h-3.5 w-3.5" />
                  <span>Strict Confidentiality Boundaries Enforced</span>
                </div>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white font-display">
                Student Wellbeing &amp; Counseling Services
              </h1>
              <p className="text-xs md:text-sm text-surface-400 max-w-2xl">
                Welcome, {user?.full_name}. Oversee student wellness intakes, schedule confidential check-in
                appointments, and document supportive intervention plans.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadCounselorCases()}
                disabled={loading}
                className="border-white/10 hover:bg-white/5 text-surface-200 text-xs"
                data-testid="refresh-counselor-btn"
              >
                <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
              <Button
                size="sm"
                onClick={() => setIsCreateModalOpen(true)}
                className="text-xs space-x-1.5 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                data-testid="new-wellbeing-intake-btn"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>New Wellbeing Intake</span>
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-400 flex items-center space-x-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 4 Stats Cards */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              title="Active Wellbeing Cases"
              value={activeCount}
              subtitle="Open or in-progress care"
              icon={HeartHandshake}
              iconColor="text-rose-500"
              badge={{ text: "Active Care", variant: "primary" }}
              testId="kpi-active-cases"
            />
            <StatsCard
              title="Immediate Attention"
              value={urgentCount}
              subtitle="High/Urgent priority"
              icon={AlertTriangle}
              iconColor="text-amber-500"
              badge={{ text: "Priority", variant: "danger" }}
              testId="kpi-urgent-cases"
            />
            <StatsCard
              title="Total Assigned Cases"
              value={cases.length}
              subtitle="All registered cases"
              icon={UserCheck}
              iconColor="text-blue-500"
              badge={{ text: "Roster", variant: "neutral" }}
              testId="kpi-total-cases"
            />
            <StatsCard
              title="Successfully Resolved"
              value={resolvedCount}
              subtitle="Completed action plans"
              icon={CheckCircle2}
              iconColor="text-emerald-500"
              badge={{ text: "Resolved", variant: "success" }}
              testId="kpi-resolved-cases"
            />
          </div>
        )}

        {/* Filters and Cases Table */}
        <Card>
          <CardHeader className="pb-3 border-b border-white/10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-base text-white font-display">Counseling &amp; Wellbeing Cases Roster</CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Confidential notes and clinical disclosures are restricted to designated counselors and super-admins.
                </CardDescription>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-surface-500" />
                  <input
                    type="text"
                    placeholder="Search by student, case #..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-white/10 bg-[#0D1117] text-white placeholder-surface-500 focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30 w-48 sm:w-60"
                  />
                </div>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-2.5 py-1.5 text-xs rounded-lg border border-white/10 bg-[#0D1117] text-white focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="PENDING_REVIEW">Pending Review</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                </select>

                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="px-2.5 py-1.5 text-xs rounded-lg border border-white/10 bg-[#0D1117] text-white focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                >
                  <option value="ALL">All Priorities</option>
                  <option value="URGENT">Urgent</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-3">
                <div className="h-10 bg-white/5 rounded animate-pulse" />
                <div className="h-10 bg-white/5 rounded animate-pulse" />
                <div className="h-10 bg-white/5 rounded animate-pulse" />
              </div>
            ) : filteredCases.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={HeartHandshake}
                  title="No Wellbeing Cases Found"
                  description={
                    searchQuery || statusFilter !== "ALL" || priorityFilter !== "ALL"
                      ? "No cases match your active search or filter criteria."
                      : "No wellbeing cases have been registered yet. Initiate a new intake using the button above."
                  }
                  actionText="New Wellbeing Intake"
                  onAction={() => setIsCreateModalOpen(true)}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#111722] text-surface-400 border-b border-white/10 font-mono text-[11px] uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Case Number</th>
                      <th className="py-3 px-4 font-semibold">Student</th>
                      <th className="py-3 px-4 font-semibold">Type</th>
                      <th className="py-3 px-4 font-semibold">Priority</th>
                      <th className="py-3 px-4 font-semibold">Status</th>
                      <th className="py-3 px-4 font-semibold">Reason / Concern</th>
                      <th className="py-3 px-4 font-semibold">Created</th>
                      <th className="py-3 px-4 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {filteredCases.map((c) => (
                      <tr
                        key={c.id}
                        className="hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="py-3 px-4 font-mono font-bold text-[#FF9A3D]">
                          {c.case_number}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-white">
                            {c.student_name || "Enrolled Student"}
                          </div>
                          {c.student_enrollment_number && (
                            <span className="text-[10px] text-surface-400 font-mono">
                              {c.student_enrollment_number}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className="text-[10px]">
                            {c.case_type.replace("_", " ")}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">{getPriorityBadge(c.priority)}</td>
                        <td className="py-3 px-4">{getStatusBadge(c.status)}</td>
                        <td className="py-3 px-4 max-w-xs truncate text-surface-300">
                          {c.reason}
                        </td>
                        <td className="py-3 px-4 text-surface-400 text-[11px]">
                          {new Date(c.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link href={`/cases/${c.id}`}>
                            <Button size="sm" variant="outline" className="h-7 text-xs space-x-1 border-white/10 hover:bg-white/5 text-surface-200">
                              <Eye className="h-3 w-3 text-[#FF9A3D]" />
                              <span>Open Case</span>
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* New Wellbeing Intake Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="New Student Wellbeing Intake"
        >
          <form onSubmit={handleCreateCase} className="space-y-4 text-xs">
            {createError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{createError}</span>
              </div>
            )}

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Student ID or Enrollment Number *
              </label>
              <input
                type="text"
                placeholder="e.g. STU-2024-001 or student UUID"
                value={createForm.student_id}
                onChange={(e) => setCreateForm({ ...createForm, student_id: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg border-white/10 bg-[#111722] text-white placeholder-surface-500 focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                required
              />
            </div>

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Case Priority *
              </label>
              <select
                value={createForm.priority}
                onChange={(e) =>
                  setCreateForm({ ...createForm, priority: e.target.value as CasePriority })
                }
                className="w-full px-3 py-2 border rounded-lg border-white/10 bg-[#111722] text-white focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
              >
                <option value="LOW" className="bg-[#111722] text-white">Low - Routine wellness check</option>
                <option value="MEDIUM" className="bg-[#111722] text-white">Medium - Pacing or stress management support</option>
                <option value="HIGH" className="bg-[#111722] text-white">High - Significant distress or sustained absence</option>
                <option value="URGENT" className="bg-[#111722] text-white">Urgent - Immediate crisis or acute intervention</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Intake Reason &amp; Clinical Summary *
              </label>
              <textarea
                rows={4}
                placeholder="Document observed indicators, reason for consultation, or self-reported challenges..."
                value={createForm.reason}
                onChange={(e) => setCreateForm({ ...createForm, reason: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg border-white/10 bg-[#111722] text-white placeholder-surface-500 focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                required
              />
            </div>

            <div className="p-3 bg-[#111722] border border-amber-500/20 rounded-lg text-amber-300/90 text-[11px] leading-relaxed flex items-start gap-2">
              <Lock className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
              <span>
                <strong>Confidentiality Notice:</strong> Subsequent case notes flagged as
                COUNSELOR_CONFIDENTIAL will be protected under strict RBAC controls and accessible only
                to counseling staff and Super Administrators.
              </span>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateModalOpen(false)}
                disabled={createSubmitting}
                className="border-white/10 text-surface-300 hover:bg-white/5 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createSubmitting}
                className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
              >
                {createSubmitting ? "Creating Case..." : "Create Intake Case"}
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
