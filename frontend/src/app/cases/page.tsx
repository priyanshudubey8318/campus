"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatsCard } from "@/components/ui/StatsCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import {
  SupportCase,
  CaseType,
  CasePriority,
  CaseStatus,
  CaseCreatePayload,
} from "@/types/pulsecase";
import {
  Briefcase,
  Users,
  Search,
  Filter,
  RefreshCw,
  AlertTriangle,
  PlusCircle,
  Clock,
  CheckCircle2,
  Calendar,
  Eye,
  XCircle,
  HelpCircle,
  X,
} from "lucide-react";

export default function CasesDashboardPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cases list state
  const [cases, setCases] = useState<SupportCase[]>([]);
  const [filteredCases, setFilteredCases] = useState<SupportCase[]>([]);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Case Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [newCase, setNewCase] = useState<CaseCreatePayload>({
    student_id: "",
    case_type: "ACADEMIC_SUPPORT",
    priority: "MEDIUM",
    reason: "",
  });

  useEffect(() => {
    const studentIdParam = searchParams.get("createForStudent");
    if (studentIdParam) {
      const studentName = searchParams.get("name");
      setNewCase((prev) => ({
        ...prev,
        student_id: studentIdParam,
        reason: studentName
          ? `Advising intervention opened for ${studentName} following cohort priority triage.`
          : prev.reason,
      }));
      setModalOpen(true);
    }
  }, [searchParams]);

  const loadCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCases({ limit: 100 });
      setCases(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load intervention cases.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  // Apply filters
  useEffect(() => {
    let result = [...cases];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          c.case_number.toLowerCase().includes(q) ||
          c.student_name?.toLowerCase().includes(q) ||
          c.student_enrollment_number?.toLowerCase().includes(q) ||
          c.student_id.toLowerCase().includes(q) ||
          c.reason.toLowerCase().includes(q)
      );
    }

    if (typeFilter !== "ALL") {
      result = result.filter((c) => c.case_type === typeFilter);
    }

    if (priorityFilter !== "ALL") {
      result = result.filter((c) => c.priority === priorityFilter);
    }

    if (statusFilter !== "ALL") {
      result = result.filter((c) => c.status === statusFilter);
    }

    setFilteredCases(result);
  }, [cases, searchQuery, typeFilter, priorityFilter, statusFilter]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCase.student_id.trim() || !newCase.reason.trim()) {
      setModalError("Student ID and Reason are required.");
      return;
    }
    try {
      setSubmitting(true);
      setModalError(null);
      await api.createCase(newCase);
      setModalOpen(false);
      setNewCase({
        student_id: "",
        case_type: "ACADEMIC_SUPPORT",
        priority: "MEDIUM",
        reason: "",
      });
      await loadCases();
    } catch (err) {
      if (err instanceof ApiError) {
        setModalError(err.message);
      } else {
        setModalError("Failed to create intervention case.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "URGENT":
        return <Badge variant="danger">URGENT</Badge>;
      case "HIGH":
        return <Badge variant="warning">HIGH</Badge>;
      case "MEDIUM":
        return <Badge variant="neutral">MEDIUM</Badge>;
      case "LOW":
      default:
        return <Badge variant="neutral">LOW</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "OPEN":
        return <Badge variant="neutral">OPEN</Badge>;
      case "IN_PROGRESS":
        return <Badge variant="primary">IN PROGRESS</Badge>;
      case "WAITING_FOR_STUDENT":
        return <Badge variant="warning">WAITING STUDENT</Badge>;
      case "FOLLOW_UP_SCHEDULED":
        return <Badge variant="primary">FOLLOW-UP SET</Badge>;
      case "RESOLVED":
        return <Badge variant="success">RESOLVED</Badge>;
      case "CLOSED":
        return <Badge variant="neutral">CLOSED</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const urgentCount = cases.filter((c) => c.priority === "URGENT" || c.priority === "HIGH").length;
  const openCount = cases.filter((c) => c.status === "OPEN").length;
  const inProgressCount = cases.filter(
    (c) => c.status === "IN_PROGRESS" || c.status === "WAITING_FOR_STUDENT" || c.status === "FOLLOW_UP_SCHEDULED"
  ).length;
  const resolvedCount = cases.filter((c) => c.status === "RESOLVED" || c.status === "CLOSED").length;

  return (
    <ProtectedRoute requiredRoles={["ADVISOR", "COUNSELOR", "ADMIN", "SUPER_ADMIN"]}>
      <div className="space-y-6">
        {/* Header Hero */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 shadow-2xl">
          <RingBackground variant="hero" className="opacity-40" />
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#FF7A18]/10 border border-[#FF7A18]/20 text-[#FF9A3D] text-xs font-mono mb-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF7A18] animate-pulse" />
                MULTI-DISCIPLINARY TRIAGE WORKSPACE
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white flex items-center gap-3">
                <Briefcase className="h-7 w-7 text-[#FF7A18]" />
                PulseCase: Support &amp; Intervention Hub
              </h1>
              <p className="text-sm text-surface-400 mt-1 max-w-2xl">
                Holistic student case management, multi-disciplinary triage, and targeted support interventions.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadCases()}
                disabled={loading}
                className="flex items-center gap-1.5 border-white/10 hover:border-[#FF7A18]/40 hover:text-white"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#FF7A18]" : ""}`} />
                Refresh
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setModalOpen(true)}
                className="flex items-center gap-1.5"
              >
                <PlusCircle className="h-4 w-4" />
                Open New Case
              </Button>
            </div>
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-950/30 p-4 text-red-400 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Stats Metrics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Total Active"
            value={openCount + inProgressCount}
            icon={Briefcase}
            subtitle="Active caseload in triage or intervention"
          />
          <StatsCard
            title="Urgent & High Priority"
            value={urgentCount}
            icon={AlertTriangle}
            subtitle="Cases requiring expedited attention"
          />
          <StatsCard
            title="In Progress"
            value={inProgressCount}
            icon={Clock}
            subtitle="Ongoing interventions and action plans"
          />
          <StatsCard
            title="Resolved & Closed"
            value={resolvedCount}
            icon={CheckCircle2}
            subtitle="Successfully completed student support cycles"
          />
        </div>

        {/* Filter Toolbar */}
        <Card className="border-white/10 bg-[#0D1117]">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="relative md:col-span-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-surface-500" />
                <input
                  type="text"
                  placeholder="Search student, case #, reason..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-white/10 bg-[#111722] text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                />
              </div>

              <div>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full py-2 px-3 text-sm rounded-lg border border-white/10 bg-[#111722] text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                >
                  <option value="ALL">All Types</option>
                  <option value="ACADEMIC_SUPPORT">Academic Support</option>
                  <option value="ATTENDANCE_INTERVENTION">Attendance Intervention</option>
                  <option value="EARLY_WARNING_TRIAGE">Early Warning Triage</option>
                  <option value="WELLBEING_REFERRAL">Wellbeing Referral</option>
                </select>
              </div>

              <div>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="w-full py-2 px-3 text-sm rounded-lg border border-white/10 bg-[#111722] text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                >
                  <option value="ALL">All Priorities</option>
                  <option value="URGENT">Urgent</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full py-2 px-3 text-sm rounded-lg border border-white/10 bg-[#111722] text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="WAITING_FOR_STUDENT">Waiting Student</option>
                  <option value="FOLLOW_UP_SCHEDULED">Follow-Up Scheduled</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Case Worklist Table */}
        <Card className="border-white/10 bg-[#0D1117] overflow-hidden">
          <CardHeader className="pb-3 border-b border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-white font-display">Triage &amp; Caseload Worklist</CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Showing {filteredCases.length} of {cases.length} assigned or authorized cases
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {filteredCases.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  title="No Support Cases Found"
                  description={
                    searchQuery || typeFilter !== "ALL" || priorityFilter !== "ALL" || statusFilter !== "ALL"
                      ? "No cases matched your filter criteria. Try adjusting your query."
                      : "There are currently no active support or intervention cases in your caseload queue."
                  }
                  icon={Briefcase}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[#111722] text-xs uppercase text-surface-400 border-b border-white/10 font-mono">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Case Number</th>
                      <th className="px-4 py-3 font-semibold">Student</th>
                      <th className="px-4 py-3 font-semibold">Type</th>
                      <th className="px-4 py-3 font-semibold">Priority</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold">Assigned Staff</th>
                      <th className="px-4 py-3 font-semibold text-center">Items</th>
                      <th className="px-4 py-3 font-semibold">Created</th>
                      <th className="px-4 py-3 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {filteredCases.map((c) => (
                      <tr
                        key={c.id}
                        className="hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="px-4 py-3.5 font-mono font-medium text-[#FF9A3D]">
                          <Link href={`/cases/${c.id}`} className="hover:underline">
                            {c.case_number}
                          </Link>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-medium text-white">
                            {c.student_name || "Enrolled Student"}
                          </div>
                          <div className="text-xs text-surface-400 font-mono">
                            {c.student_enrollment_number || c.student_id.slice(0, 8)}
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-xs text-surface-300">
                          {c.case_type.replace(/_/g, " ")}
                        </td>
                        <td className="px-4 py-3.5">{getPriorityBadge(c.priority)}</td>
                        <td className="px-4 py-3.5">{getStatusBadge(c.status)}</td>
                        <td className="px-4 py-3.5 text-xs text-surface-400">
                          {c.assigned_staff_name || "Unassigned"}
                        </td>
                        <td className="px-4 py-3.5 text-center text-xs text-surface-400 font-mono">
                          <span title={`${c.interventions_count} interventions, ${c.follow_ups_count} follow-ups`}>
                            {c.interventions_count} int / {c.follow_ups_count} fol
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-xs text-surface-400 whitespace-nowrap font-mono">
                          {new Date(c.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <Link href={`/cases/${c.id}`}>
                            <Button variant="outline" size="sm" className="h-8 px-2.5 text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white">
                              <Eye className="h-3.5 w-3.5 mr-1" />
                              View
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

        {/* Modal: Open New Case */}
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-xl bg-[#0D1117] border border-white/10 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
                <h3 className="text-base font-semibold text-white font-display flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-[#FF7A18]" />
                  Open Support / Intervention Case
                </h3>
                <button
                  onClick={() => setModalOpen(false)}
                  className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateCase} className="p-6 space-y-4">
                {modalError && (
                  <div className="rounded-lg bg-red-950/40 border border-red-500/20 p-3 text-xs text-red-400">
                    {modalError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                    Student ID or Enrollment UUID <span className="text-[#FF4D4D]">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Enter student ID..."
                    value={newCase.student_id}
                    onChange={(e) => setNewCase({ ...newCase, student_id: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                      Case Type <span className="text-[#FF4D4D]">*</span>
                    </label>
                    <select
                      value={newCase.case_type}
                      onChange={(e) => setNewCase({ ...newCase, case_type: e.target.value as CaseType })}
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    >
                      <option value="ACADEMIC_SUPPORT">Academic Support</option>
                      <option value="ATTENDANCE_INTERVENTION">Attendance Intervention</option>
                      <option value="EARLY_WARNING_TRIAGE">Early Warning Triage</option>
                      <option value="WELLBEING_REFERRAL">Wellbeing Referral</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                      Priority <span className="text-[#FF4D4D]">*</span>
                    </label>
                    <select
                      value={newCase.priority}
                      onChange={(e) => setNewCase({ ...newCase, priority: e.target.value as CasePriority })}
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    >
                      <option value="LOW">Low</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="HIGH">High</option>
                      <option value="URGENT">Urgent</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                    Initial Concern &amp; Intervention Trigger Reason <span className="text-[#FF4D4D]">*</span>
                  </label>
                  <textarea
                    rows={4}
                    required
                    placeholder="Document student engagement signals, academic indicators, or counseling triage reason..."
                    value={newCase.reason}
                    onChange={(e) => setNewCase({ ...newCase, reason: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                  <span className="text-[11px] text-surface-500 mt-1 block">Minimum 5 characters.</span>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setModalOpen(false)}
                    disabled={submitting}
                    className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={submitting}>
                    {submitting ? "Opening Case..." : "Create Case"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
