"use client";

import React, { useCallback, useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import {
  SupportCaseDetail,
  CaseStatus,
  CasePriority,
  CaseType,
  InterventionType,
  InterventionStatus,
  FollowUpType,
  FollowUpStatus,
  ResolutionOutcome,
  NoteType,
  ConfidentialityLevel,
} from "@/types/pulsecase";
import {
  Briefcase,
  ArrowLeft,
  Clock,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  User,
  ShieldCheck,
  Lock,
  PlusCircle,
  X,
  FileText,
  UserCheck,
  Send,
  MessageSquare,
  CheckSquare,
  RefreshCw,
  Archive,
} from "lucide-react";

export default function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = resolvedParams.id;
  const router = useRouter();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [caseData, setCaseData] = useState<SupportCaseDetail | null>(null);

  // Active Tab
  const [activeTab, setActiveTab] = useState<"overview" | "interventions" | "followups" | "notes">("overview");

  // Reassign Modal
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [newAssigneeId, setNewAssigneeId] = useState("");
  const [assignLoading, setAssignLoading] = useState(false);

  // Status Change Modal
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<CaseStatus>("IN_PROGRESS");
  const [statusNotes, setStatusNotes] = useState("");
  const [statusLoading, setStatusLoading] = useState(false);

  // Resolve Modal
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [resolveOutcome, setResolveOutcome] = useState<ResolutionOutcome>("IMPROVED_ENGAGEMENT");
  const [resolveSummary, setResolveSummary] = useState("");
  const [resolveLoading, setResolveLoading] = useState(false);

  // Close Modal
  const [closeModalOpen, setCloseModalOpen] = useState(false);
  const [closingNotes, setClosingNotes] = useState("");
  const [closeLoading, setCloseLoading] = useState(false);

  // Add Intervention Modal
  const [interventionModalOpen, setInterventionModalOpen] = useState(false);
  const [newIntervention, setNewIntervention] = useState<{
    intervention_type: InterventionType;
    title: string;
    description: string;
    target_completion_date: string;
  }>({
    intervention_type: "ONE_ON_ONE_ADVISING",
    title: "",
    description: "",
    target_completion_date: "",
  });
  const [interventionLoading, setInterventionLoading] = useState(false);

  // Schedule Follow-Up Modal
  const [followUpModalOpen, setFollowUpModalOpen] = useState(false);
  const [newFollowUp, setNewFollowUp] = useState<{
    scheduled_date: string;
    scheduled_time: string;
    follow_up_type: FollowUpType;
    notes: string;
  }>({
    scheduled_date: "",
    scheduled_time: "",
    follow_up_type: "CHECK_IN_MEETING",
    notes: "",
  });
  const [followUpLoading, setFollowUpLoading] = useState(false);

  // Add Note Form
  const [newNoteContent, setNewNoteContent] = useState("");
  const [newNoteType, setNewNoteType] = useState<NoteType>("ADVISING_NOTE");
  const [isCounselorConfidential, setIsCounselorConfidential] = useState(false);
  const [noteLoading, setNoteLoading] = useState(false);

  const loadCaseDetail = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCaseDetail(caseId);
      setCaseData(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load case details.");
      }
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    loadCaseDetail();
  }, [loadCaseDetail]);

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAssigneeId.trim()) return;
    try {
      setAssignLoading(true);
      await api.assignCase(caseId, newAssigneeId.trim());
      setAssignModalOpen(false);
      setNewAssigneeId("");
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to assign staff handler");
    } finally {
      setAssignLoading(false);
    }
  };

  const handleStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setStatusLoading(true);
      await api.updateCaseStatus(caseId, {
        status: selectedStatus,
        notes: statusNotes.trim() || undefined,
      });
      setStatusModalOpen(false);
      setStatusNotes("");
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to update case status");
    } finally {
      setStatusLoading(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (resolveSummary.trim().length < 5) {
      alert("Resolution summary must be at least 5 characters.");
      return;
    }
    try {
      setResolveLoading(true);
      await api.resolveCase(caseId, {
        resolution_outcome: resolveOutcome,
        resolution_summary: resolveSummary.trim(),
      });
      setResolveModalOpen(false);
      setResolveSummary("");
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to resolve case");
    } finally {
      setResolveLoading(false);
    }
  };

  const handleClose = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCloseLoading(true);
      await api.closeCase(caseId, {
        closing_notes: closingNotes.trim() || undefined,
      });
      setCloseModalOpen(false);
      setClosingNotes("");
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to close case");
    } finally {
      setCloseLoading(false);
    }
  };

  const handleAddIntervention = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIntervention.title.trim() || newIntervention.description.trim().length < 5) {
      alert("Title and description (min 5 chars) are required.");
      return;
    }
    try {
      setInterventionLoading(true);
      await api.addCaseIntervention(caseId, {
        ...newIntervention,
        target_completion_date: newIntervention.target_completion_date || undefined,
      });
      setInterventionModalOpen(false);
      setNewIntervention({
        intervention_type: "ONE_ON_ONE_ADVISING",
        title: "",
        description: "",
        target_completion_date: "",
      });
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to add intervention");
    } finally {
      setInterventionLoading(false);
    }
  };

  const handleUpdateInterventionStatus = async (
    interventionId: string,
    status: InterventionStatus
  ) => {
    try {
      await api.updateCaseIntervention(caseId, interventionId, { status });
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to update intervention status");
    }
  };

  const handleScheduleFollowUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFollowUp.scheduled_date) {
      alert("Scheduled date is required.");
      return;
    }
    try {
      setFollowUpLoading(true);
      await api.scheduleCaseFollowUp(caseId, {
        scheduled_date: newFollowUp.scheduled_date,
        scheduled_time: newFollowUp.scheduled_time || undefined,
        follow_up_type: newFollowUp.follow_up_type,
        notes: newFollowUp.notes.trim() || undefined,
      });
      setFollowUpModalOpen(false);
      setNewFollowUp({
        scheduled_date: "",
        scheduled_time: "",
        follow_up_type: "CHECK_IN_MEETING",
        notes: "",
      });
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to schedule follow-up");
    } finally {
      setFollowUpLoading(false);
    }
  };

  const handleUpdateFollowUpStatus = async (
    followUpId: string,
    status: FollowUpStatus
  ) => {
    try {
      await api.updateCaseFollowUp(caseId, followUpId, { status });
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to update follow-up");
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteContent.trim()) return;
    try {
      setNoteLoading(true);
      const confLevel: ConfidentialityLevel = isCounselorConfidential
        ? "COUNSELOR_CONFIDENTIAL"
        : "STANDARD";
      const nType: NoteType = isCounselorConfidential
        ? "COUNSELOR_CONFIDENTIAL"
        : newNoteType;

      await api.addCaseNote(caseId, {
        note_type: nType,
        confidentiality_level: confLevel,
        content: newNoteContent.trim(),
      });
      setNewNoteContent("");
      setIsCounselorConfidential(false);
      await loadCaseDetail();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to record case note");
    } finally {
      setNoteLoading(false);
    }
  };

  const isCounselorOrAdmin =
    user?.roles?.includes("COUNSELOR") ||
    user?.roles?.includes("ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");

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

  if (loading) {
    return (
      <ProtectedRoute requiredRoles={["ADVISOR", "COUNSELOR", "ADMIN", "SUPER_ADMIN"]}>
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-[#FF7A18]" />
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !caseData) {
    return (
      <ProtectedRoute requiredRoles={["ADVISOR", "COUNSELOR", "ADMIN", "SUPER_ADMIN"]}>
        <div className="space-y-4">
          <Link href="/cases">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5 border-white/10 hover:border-[#FF7A18]/40 hover:text-white">
              <ArrowLeft className="h-4 w-4" />
              Back to Cases
            </Button>
          </Link>
          <div className="rounded-xl border border-red-500/20 bg-red-950/30 p-6 text-center text-red-400">
            <AlertTriangle className="mx-auto h-8 w-8 mb-2" />
            <h3 className="text-base font-semibold font-display text-white">Error Loading Case</h3>
            <p className="text-sm mt-1 text-surface-400">{error || "Case record could not be found."}</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute requiredRoles={["ADVISOR", "COUNSELOR", "ADMIN", "SUPER_ADMIN"]}>
      <div className="space-y-6">
        {/* Navigation & Header Hero */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 shadow-2xl">
          <RingBackground variant="hero" className="opacity-40" />
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link href="/cases">
                <Button variant="outline" size="sm" className="h-9 px-2.5 border-white/10 hover:border-[#FF7A18]/40 hover:text-white">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <div>
                <div className="flex items-center gap-2.5">
                  <h1 className="text-2xl font-bold font-mono text-white">
                    {caseData.case_number}
                  </h1>
                  {getPriorityBadge(caseData.priority)}
                  {getStatusBadge(caseData.status)}
                </div>
                <p className="text-sm text-surface-400 mt-0.5">
                  {caseData.case_type.replace(/_/g, " ")} &bull; Trigger: {caseData.trigger_source}
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-2">
              {caseData.status !== "RESOLVED" && caseData.status !== "CLOSED" && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setStatusModalOpen(true)}
                    className="flex items-center gap-1.5 text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white"
                  >
                    <Clock className="h-3.5 w-3.5" />
                    Update Status
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAssignModalOpen(true)}
                    className="flex items-center gap-1.5 text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    Assign Handler
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setResolveModalOpen(true)}
                    className="flex items-center gap-1.5 text-xs"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Resolve Case
                  </Button>
                </>
              )}

              {caseData.status === "RESOLVED" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCloseModalOpen(true)}
                  className="flex items-center gap-1.5 text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white"
                >
                  <Archive className="h-3.5 w-3.5" />
                  Close &amp; Archive
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Case Info Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-white/10 bg-[#0D1117]">
            <CardContent className="p-4">
              <span className="text-xs font-semibold text-surface-400 uppercase tracking-wider font-mono">Student Subject</span>
              <div className="mt-1 font-medium text-white flex items-center gap-2">
                <User className="h-4 w-4 text-[#FF7A18]" />
                {caseData.student_name || "Enrolled Student"}
              </div>
              <div className="text-xs text-surface-400 font-mono mt-0.5">
                ID: {caseData.student_enrollment_number || caseData.student_id}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-[#0D1117]">
            <CardContent className="p-4">
              <span className="text-xs font-semibold text-surface-400 uppercase tracking-wider font-mono">Assigned Staff</span>
              <div className="mt-1 font-medium text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                {caseData.assigned_staff_name || "Unassigned"}
              </div>
              <div className="text-xs text-surface-400 mt-0.5">
                Role: {caseData.assigned_staff_role || "None"}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-[#0D1117]">
            <CardContent className="p-4">
              <span className="text-xs font-semibold text-surface-400 uppercase tracking-wider font-mono">Referred By</span>
              <div className="mt-1 font-medium text-white">
                {caseData.referred_by_name || "Self / Institutional System"}
              </div>
              <div className="text-xs text-surface-400 mt-0.5 font-mono">
                Created: {new Date(caseData.created_at).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-[#0D1117]">
            <CardContent className="p-4">
              <span className="text-xs font-semibold text-surface-400 uppercase tracking-wider font-mono">Resolution State</span>
              <div className="mt-1 font-medium text-white">
                {caseData.resolution_outcome ? caseData.resolution_outcome.replace(/_/g, " ") : "Pending Outcome"}
              </div>
              <div className="text-xs text-surface-400 mt-0.5">
                {caseData.closed_at
                  ? `Closed on ${new Date(caseData.closed_at).toLocaleDateString()}`
                  : "Active Support Lifecycle"}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-white/10">
          <nav className="flex space-x-6">
            <button
              onClick={() => setActiveTab("overview")}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "overview"
                  ? "border-[#FF7A18] text-[#FF9A3D]"
                  : "border-transparent text-surface-400 hover:text-white"
              }`}
            >
              <FileText className="h-4 w-4" />
              Overview &amp; Context
            </button>
            <button
              onClick={() => setActiveTab("interventions")}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "interventions"
                  ? "border-[#FF7A18] text-[#FF9A3D]"
                  : "border-transparent text-surface-400 hover:text-white"
              }`}
            >
              <CheckSquare className="h-4 w-4" />
              Action Plan ({caseData.interventions.length})
            </button>
            <button
              onClick={() => setActiveTab("followups")}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "followups"
                  ? "border-[#FF7A18] text-[#FF9A3D]"
                  : "border-transparent text-surface-400 hover:text-white"
              }`}
            >
              <Calendar className="h-4 w-4" />
              Follow-ups ({caseData.follow_ups.length})
            </button>
            <button
              onClick={() => setActiveTab("notes")}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "notes"
                  ? "border-[#FF7A18] text-[#FF9A3D]"
                  : "border-transparent text-surface-400 hover:text-white"
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              Case Notes ({caseData.notes.length})
            </button>
          </nav>
        </div>

        {/* TAB 1: Overview */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <Card className="border-white/10 bg-[#0D1117]">
              <CardHeader className="border-b border-white/10 pb-3">
                <CardTitle className="text-base text-white font-display">Initial Concern &amp; Trigger Reason</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <div className="rounded-lg bg-[#111722] p-4 border border-white/10 text-sm leading-relaxed text-surface-200">
                  {caseData.reason}
                </div>

                {caseData.evidence_references && Object.keys(caseData.evidence_references).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider font-mono mb-2">
                      Evidence References &amp; Recurrence Metadata
                    </h4>
                    <pre className="p-3 bg-[#07090D] text-[#FF9A3D] border border-white/10 rounded-lg text-xs font-mono overflow-x-auto">
                      {JSON.stringify(caseData.evidence_references, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>

            {caseData.resolution_summary && (
              <Card className="border-emerald-500/20 bg-emerald-950/20">
                <CardHeader className="border-b border-emerald-500/20 pb-3">
                  <CardTitle className="text-base text-emerald-400 font-display flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5" />
                    Documented Resolution
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-surface-200 pt-4">
                  <p>
                    <span className="font-semibold text-white">Outcome: </span>
                    {caseData.resolution_outcome?.replace(/_/g, " ")}
                  </p>
                  <p className="leading-relaxed text-surface-300">{caseData.resolution_summary}</p>
                  {caseData.resolved_at && (
                    <span className="text-xs text-surface-500 block font-mono">
                      Resolved on {new Date(caseData.resolved_at).toLocaleString()}
                    </span>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* TAB 2: Interventions & Action Plan */}
        {activeTab === "interventions" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white font-display">
                Student Action Plan &amp; Interventions
              </h3>
              {caseData.status !== "CLOSED" && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setInterventionModalOpen(true)}
                  className="flex items-center gap-1.5 text-xs"
                >
                  <PlusCircle className="h-4 w-4" />
                  Add Action Item
                </Button>
              )}
            </div>

            {caseData.interventions.length === 0 ? (
              <EmptyState
                title="No Action Items Added"
                description="Create measurable intervention items such as tutoring referrals, attendance contracts, or advising sessions."
                icon={CheckSquare}
              />
            ) : (
              <div className="space-y-3">
                {caseData.interventions.map((item) => (
                  <Card key={item.id} className="p-4 border-white/10 bg-[#0D1117]">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2.5">
                          <span className="font-medium text-white">
                            {item.title}
                          </span>
                          <Badge variant="neutral" className="text-[10px]">
                            {item.intervention_type.replace(/_/g, " ")}
                          </Badge>
                          <Badge
                            variant={
                              item.status === "COMPLETED"
                                ? "success"
                                : item.status === "CANCELLED"
                                ? "danger"
                                : "primary"
                            }
                            className="text-[10px]"
                          >
                            {item.status}
                          </Badge>
                        </div>
                        <p className="text-xs text-surface-400 mt-1">
                          {item.description}
                        </p>
                        {item.target_completion_date && (
                          <span className="text-[11px] text-surface-400 mt-1 block font-mono">
                            Target Date: {item.target_completion_date}
                          </span>
                        )}
                      </div>

                      {caseData.status !== "CLOSED" && item.status !== "COMPLETED" && (
                        <div className="flex items-center gap-2 self-end sm:self-auto">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUpdateInterventionStatus(item.id, "IN_PROGRESS")}
                            className="text-xs h-7 px-2 border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white"
                          >
                            In Progress
                          </Button>
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleUpdateInterventionStatus(item.id, "COMPLETED")}
                            className="text-xs h-7 px-2"
                          >
                            Complete
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUpdateInterventionStatus(item.id, "CANCELLED")}
                            className="text-xs h-7 px-2 text-red-400 border-red-500/20 hover:bg-red-950/30"
                          >
                            Cancel
                          </Button>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Follow-ups */}
        {activeTab === "followups" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-white font-display">
                Scheduled Follow-up Check-ins
              </h3>
              {caseData.status !== "CLOSED" && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setFollowUpModalOpen(true)}
                  className="flex items-center gap-1.5 text-xs"
                >
                  <PlusCircle className="h-4 w-4" />
                  Schedule Follow-Up
                </Button>
              )}
            </div>

            {caseData.follow_ups.length === 0 ? (
              <EmptyState
                title="No Follow-ups Scheduled"
                description="Schedule a check-in appointment to review student progress and attendance trajectory."
                icon={Calendar}
              />
            ) : (
              <div className="space-y-3">
                {caseData.follow_ups.map((f) => (
                  <Card key={f.id} className="p-4 border-white/10 bg-[#0D1117]">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2.5">
                          <Calendar className="h-4 w-4 text-[#FF7A18]" />
                          <span className="font-semibold text-white text-sm font-mono">
                            {f.scheduled_date} {f.scheduled_time && `at ${f.scheduled_time}`}
                          </span>
                          <Badge variant="neutral" className="text-[10px]">
                            {f.follow_up_type.replace(/_/g, " ")}
                          </Badge>
                          <Badge
                            variant={
                              f.status === "COMPLETED"
                                ? "success"
                                : f.status === "CANCELLED" || f.status === "MISSED"
                                ? "danger"
                                : "primary"
                            }
                            className="text-[10px]"
                          >
                            {f.status}
                          </Badge>
                        </div>
                        {f.notes && (
                          <p className="text-xs text-surface-400 mt-1.5">
                            {f.notes}
                          </p>
                        )}
                        <span className="text-[11px] text-surface-400 mt-1 block font-mono">
                          Assigned Staff: {f.assigned_staff_name || f.assigned_staff_id}
                        </span>
                      </div>

                      {caseData.status !== "CLOSED" && f.status === "SCHEDULED" && (
                        <div className="flex items-center gap-2 self-end sm:self-auto">
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleUpdateFollowUpStatus(f.id, "COMPLETED")}
                            className="text-xs h-7 px-2"
                          >
                            Complete
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUpdateFollowUpStatus(f.id, "MISSED")}
                            className="text-xs h-7 px-2 text-[#FFB020] border-amber-500/20 hover:bg-amber-950/30"
                          >
                            Missed
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUpdateFollowUpStatus(f.id, "CANCELLED")}
                            className="text-xs h-7 px-2 text-red-400 border-red-500/20 hover:bg-red-950/30"
                          >
                            Cancel
                          </Button>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: Case Notes */}
        {activeTab === "notes" && (
          <div className="space-y-6">
            {caseData.status !== "CLOSED" && (
              <Card className="border-white/10 bg-[#0D1117]">
                <CardHeader className="border-b border-white/10 pb-3">
                  <CardTitle className="text-sm font-semibold text-white font-display">Record Case Note</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 pt-4">
                  <form onSubmit={handleAddNote} className="space-y-3">
                    <textarea
                      rows={3}
                      required
                      placeholder="Add case observation, interaction summary, or meeting notes..."
                      value={newNoteContent}
                      onChange={(e) => setNewNoteContent(e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    />

                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex items-center gap-4">
                        <select
                          value={newNoteType}
                          onChange={(e) => setNewNoteType(e.target.value as NoteType)}
                          className="py-1.5 px-2.5 text-xs rounded-lg border border-white/10 bg-[#111722] text-white focus:outline-none focus:border-[#FF7A18]"
                        >
                          <option value="ADVISING_NOTE">Advising Note</option>
                          <option value="STUDENT_INTERACTION">Student Interaction</option>
                          <option value="ACTION_PLAN">Action Plan Note</option>
                        </select>

                        {isCounselorOrAdmin && (
                          <label className="flex items-center gap-2 cursor-pointer text-xs text-[#FFB020] font-medium">
                            <input
                              type="checkbox"
                              checked={isCounselorConfidential}
                              onChange={(e) => setIsCounselorConfidential(e.target.checked)}
                              className="rounded border-amber-500/40 text-[#FF7A18] focus:ring-[#FF7A18] bg-[#111722] h-4 w-4"
                            />
                            <Lock className="h-3.5 w-3.5" />
                            Counselor Confidential (Restricted)
                          </label>
                        )}
                      </div>

                      <Button
                        type="submit"
                        size="sm"
                        variant="primary"
                        disabled={noteLoading || !newNoteContent.trim()}
                        className="flex items-center gap-1.5"
                      >
                        <Send className="h-3.5 w-3.5" />
                        {noteLoading ? "Saving..." : "Add Note"}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {caseData.notes.length === 0 ? (
              <EmptyState
                title="No Case Notes Recorded"
                description="Staff notes and interaction logs will appear here in chronological order."
                icon={MessageSquare}
              />
            ) : (
              <div className="space-y-3">
                {caseData.notes.map((note) => {
                  const isConfidential = note.confidentiality_level === "COUNSELOR_CONFIDENTIAL";
                  return (
                    <Card
                      key={note.id}
                      className={
                        isConfidential
                          ? "border-[#FF7A18]/30 bg-[#FF7A18]/5"
                          : "border-white/10 bg-[#0D1117]"
                      }
                    >
                      <CardContent className="p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-white">
                              {note.author_name || "Case Worker"}
                            </span>
                            <Badge variant="neutral" className="text-[10px]">
                              {note.note_type.replace(/_/g, " ")}
                            </Badge>
                            {isConfidential && (
                              <Badge variant="warning" className="text-[10px] flex items-center gap-1">
                                <Lock className="h-2.5 w-2.5" />
                                COUNSELOR CONFIDENTIAL
                              </Badge>
                            )}
                          </div>
                          <span className="text-[11px] text-surface-400 font-mono">
                            {new Date(note.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-surface-200 leading-relaxed whitespace-pre-wrap">
                          {note.content}
                        </p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Modal: Assign Staff */}
        {assignModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-xl bg-[#0D1117] border border-white/10 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-base font-semibold text-white font-display">Assign Staff Handler</h3>
                <button onClick={() => setAssignModalOpen(false)} className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <form onSubmit={handleAssign} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Staff User ID</label>
                  <input
                    type="text"
                    required
                    placeholder="Enter user UUID of Advisor or Counselor..."
                    value={newAssigneeId}
                    onChange={(e) => setNewAssigneeId(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                  <Button type="button" variant="outline" onClick={() => setAssignModalOpen(false)} className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white">
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={assignLoading}>
                    {assignLoading ? "Assigning..." : "Assign"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Update Status */}
        {statusModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-xl bg-[#0D1117] border border-white/10 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-base font-semibold text-white font-display">Update Case Status</h3>
                <button onClick={() => setStatusModalOpen(false)} className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <form onSubmit={handleStatusChange} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">New Status</label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value as CaseStatus)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  >
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="WAITING_FOR_STUDENT">Waiting for Student</option>
                    <option value="FOLLOW_UP_SCHEDULED">Follow-Up Scheduled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Status Transition Notes</label>
                  <textarea
                    rows={2}
                    placeholder="Optional transition reason..."
                    value={statusNotes}
                    onChange={(e) => setStatusNotes(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                  <Button type="button" variant="outline" onClick={() => setStatusModalOpen(false)} className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white">
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={statusLoading}>
                    {statusLoading ? "Updating..." : "Update Status"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Resolve Case */}
        {resolveModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-xl bg-[#0D1117] border border-white/10 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-base font-semibold flex items-center gap-2 text-white font-display">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  Resolve Support Case
                </h3>
                <button onClick={() => setResolveModalOpen(false)} className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <form onSubmit={handleResolve} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Resolution Outcome</label>
                  <select
                    value={resolveOutcome}
                    onChange={(e) => setResolveOutcome(e.target.value as ResolutionOutcome)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  >
                    <option value="IMPROVED_ENGAGEMENT">Improved Engagement</option>
                    <option value="ACADEMIC_PLAN_ESTABLISHED">Academic Plan Established</option>
                    <option value="REFERRED_TO_EXTERNAL_RESOURCE">Referred to External Resource</option>
                    <option value="STUDENT_UNRESPONSIVE">Student Unresponsive</option>
                    <option value="NO_FURTHER_ACTION">No Further Action</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                    Resolution Summary <span className="text-[#FF4D4D]">*</span>
                  </label>
                  <textarea
                    rows={4}
                    required
                    placeholder="Document student outcome, academic plan agreed upon, or closing assessment..."
                    value={resolveSummary}
                    onChange={(e) => setResolveSummary(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                  <span className="text-[11px] text-surface-500 mt-1 block">Minimum 5 characters.</span>
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                  <Button type="button" variant="outline" onClick={() => setResolveModalOpen(false)} className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white">
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={resolveLoading}
                  >
                    {resolveLoading ? "Resolving..." : "Confirm Resolution"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Close Case */}
        {closeModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-xl bg-[#0D1117] border border-white/10 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-base font-semibold flex items-center gap-2 text-white font-display">
                  <Archive className="h-5 w-5 text-[#FF7A18]" />
                  Close &amp; Archive Case
                </h3>
                <button onClick={() => setCloseModalOpen(false)} className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-xs text-surface-400">
                Closing this case marks the complete institutional lifecycle as archived. Once closed, no
                further modifications can be made without reopening.
              </p>
              <form onSubmit={handleClose} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Closing Notes (Optional)</label>
                  <textarea
                    rows={3}
                    placeholder="Final archive remarks..."
                    value={closingNotes}
                    onChange={(e) => setClosingNotes(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                  <Button type="button" variant="outline" onClick={() => setCloseModalOpen(false)} className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white">
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={closeLoading}>
                    {closeLoading ? "Closing..." : "Close Case"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Add Intervention */}
        {interventionModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-xl bg-[#0D1117] border border-white/10 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-base font-semibold text-white font-display">Add Action Item / Intervention</h3>
                <button onClick={() => setInterventionModalOpen(false)} className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <form onSubmit={handleAddIntervention} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Intervention Type</label>
                  <select
                    value={newIntervention.intervention_type}
                    onChange={(e) =>
                      setNewIntervention({
                        ...newIntervention,
                        intervention_type: e.target.value as InterventionType,
                      })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  >
                    <option value="ONE_ON_ONE_ADVISING">One-on-One Advising</option>
                    <option value="PEER_TUTORING_REFERRAL">Peer Tutoring Referral</option>
                    <option value="ACADEMIC_SKILLS_WORKSHOP">Academic Skills Workshop</option>
                    <option value="ATTENDANCE_CONTRACT">Attendance Contract</option>
                    <option value="WELLBEING_SUPPORT">Wellbeing Support</option>
                    <option value="COURSE_LOAD_ADJUSTMENT">Course Load Adjustment</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Schedule Peer Tutoring for Calculus I"
                    value={newIntervention.title}
                    onChange={(e) =>
                      setNewIntervention({ ...newIntervention, title: e.target.value })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Description</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Specific actionable expectations..."
                    value={newIntervention.description}
                    onChange={(e) =>
                      setNewIntervention({ ...newIntervention, description: e.target.value })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Target Completion Date</label>
                  <input
                    type="date"
                    value={newIntervention.target_completion_date}
                    onChange={(e) =>
                      setNewIntervention({
                        ...newIntervention,
                        target_completion_date: e.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setInterventionModalOpen(false)}
                    className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={interventionLoading}>
                    {interventionLoading ? "Adding..." : "Add Item"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Schedule Follow-up */}
        {followUpModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-xl bg-[#0D1117] border border-white/10 p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-base font-semibold text-white font-display">Schedule Follow-up Meeting</h3>
                <button onClick={() => setFollowUpModalOpen(false)} className="rounded p-1 text-surface-400 hover:bg-white/10 hover:text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <form onSubmit={handleScheduleFollowUp} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Date</label>
                    <input
                      type="date"
                      required
                      value={newFollowUp.scheduled_date}
                      onChange={(e) =>
                        setNewFollowUp({ ...newFollowUp, scheduled_date: e.target.value })
                      }
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Time (Optional)</label>
                    <input
                      type="time"
                      value={newFollowUp.scheduled_time}
                      onChange={(e) =>
                        setNewFollowUp({ ...newFollowUp, scheduled_time: e.target.value })
                      }
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Meeting Type</label>
                  <select
                    value={newFollowUp.follow_up_type}
                    onChange={(e) =>
                      setNewFollowUp({
                        ...newFollowUp,
                        follow_up_type: e.target.value as FollowUpType,
                      })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  >
                    <option value="CHECK_IN_MEETING">Check-In Meeting</option>
                    <option value="ACADEMIC_PROGRESS_REVIEW">Academic Progress Review</option>
                    <option value="ATTENDANCE_CHECK">Attendance Check</option>
                    <option value="WELLBEING_FOLLOW_UP">Wellbeing Follow-Up</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">Meeting Notes / Agenda</label>
                  <textarea
                    rows={3}
                    placeholder="Objectives for the check-in..."
                    value={newFollowUp.notes}
                    onChange={(e) =>
                      setNewFollowUp({ ...newFollowUp, notes: e.target.value })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setFollowUpModalOpen(false)}
                    className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={followUpLoading}>
                    {followUpLoading ? "Scheduling..." : "Schedule"}
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
