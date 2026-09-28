"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import {
  LeaveRequest,
  LeaveStatus,
  Complaint,
  ComplaintStatus,
  ComplaintCategory,
  ComplaintAppeal,
} from "@/types/pulserecord";
import {
  ShieldAlert,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  AlertCircle,
  Paperclip,
  Download,
  Filter,
  UserCheck,
  Scale,
  Lock,
  EyeOff,
  Send,
  Archive,
} from "lucide-react";

export default function AdminRecordsPage() {
  const [activeTab, setActiveTab] = useState<string>("leaves");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // --- Leaves State ---
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [leaveStatusFilter, setLeaveStatusFilter] = useState<string>("");

  // --- Complaints State ---
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [complaintStatusFilter, setComplaintStatusFilter] = useState<string>("");
  const [complaintCategoryFilter, setComplaintCategoryFilter] = useState<string>("");

  // Modals
  // 1. Assign Reviewer Modal
  const [assignComplaint, setAssignComplaint] = useState<Complaint | null>(null);
  const [reviewerUserId, setReviewerUserId] = useState("");
  const [assigning, setAssigning] = useState(false);

  // 2. Request Info Modal
  const [requestInfoComplaint, setRequestInfoComplaint] = useState<Complaint | null>(null);
  const [infoRequestText, setInfoRequestText] = useState("");
  const [requestingInfo, setRequestingInfo] = useState(false);

  // 3. Adjudicate Modal
  const [adjudicateComplaint, setAdjudicateComplaint] = useState<Complaint | null>(null);
  const [adjudicateStatus, setAdjudicateStatus] = useState<string>("VERIFIED");
  const [adjudicateOutcome, setAdjudicateOutcome] = useState<string>("POLICY_VIOLATION_SUBSTANTIATED");
  const [adjudicateSummary, setAdjudicateSummary] = useState("");
  const [internalNotes, setInternalNotes] = useState("");
  const [adjudicating, setAdjudicating] = useState(false);

  // 4. Resolve Appeal Modal
  const [appealComplaint, setAppealComplaint] = useState<Complaint | null>(null);
  const [selectedAppeal, setSelectedAppeal] = useState<ComplaintAppeal | null>(null);
  const [appealStatus, setAppealStatus] = useState<string>("UPHELD");
  const [dispositionSummary, setDispositionSummary] = useState("");
  const [appealNotes, setAppealNotes] = useState("");
  const [resolvingAppeal, setResolvingAppeal] = useState(false);

  // 5. Evidence Modal
  const [evidenceComplaint, setEvidenceComplaint] = useState<Complaint | null>(null);

  const fetchLeaves = async () => {
    try {
      const data = await api.getAllLeaves(undefined, leaveStatusFilter || undefined);
      setLeaves(data);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
    }
  };

  const fetchComplaints = async () => {
    try {
      const data = await api.getAllComplaints({
        status: complaintStatusFilter || undefined,
        category: complaintCategoryFilter || undefined,
      });
      setComplaints(data);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
    }
  };

  const loadAll = async () => {
    setLoading(true);
    setError(null);
    await Promise.all([fetchLeaves(), fetchComplaints()]);
    setLoading(false);
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchLeaves();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leaveStatusFilter]);

  useEffect(() => {
    fetchComplaints();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [complaintStatusFilter, complaintCategoryFilter]);

  // Handlers
  const handleAssignReviewer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignComplaint || !reviewerUserId.trim()) return;

    try {
      setAssigning(true);
      setError(null);
      await api.assignComplaintReviewer(assignComplaint.id, reviewerUserId.trim());
      setSuccessMsg(`Investigator assigned to grievance ${assignComplaint.complaint_code}.`);
      setAssignComplaint(null);
      setReviewerUserId("");
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to assign reviewer.");
    } finally {
      setAssigning(false);
    }
  };

  const handleRequestInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestInfoComplaint || !infoRequestText.trim()) return;

    try {
      setRequestingInfo(true);
      setError(null);
      await api.requestComplaintInfo(requestInfoComplaint.id, infoRequestText.trim());
      setSuccessMsg(`Information request sent for ${requestInfoComplaint.complaint_code}.`);
      setRequestInfoComplaint(null);
      setInfoRequestText("");
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to request information.");
    } finally {
      setRequestingInfo(false);
    }
  };

  const handleAdjudicate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjudicateComplaint || !adjudicateSummary.trim()) return;

    try {
      setAdjudicating(true);
      setError(null);
      await api.adjudicateComplaint(adjudicateComplaint.id, {
        status: adjudicateStatus,
        adjudication_outcome: adjudicateOutcome,
        adjudication_summary: adjudicateSummary.trim(),
        internal_reviewer_notes: internalNotes.trim() || undefined,
      });
      setSuccessMsg(`Grievance ${adjudicateComplaint.complaint_code} formally adjudicated as ${adjudicateStatus}.`);
      setAdjudicateComplaint(null);
      setAdjudicateSummary("");
      setInternalNotes("");
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to adjudicate grievance.");
    } finally {
      setAdjudicating(false);
    }
  };

  const handleResolveAppeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!appealComplaint || !selectedAppeal || !dispositionSummary.trim()) return;

    try {
      setResolvingAppeal(true);
      setError(null);
      await api.resolveComplaintAppeal(appealComplaint.id, selectedAppeal.id, {
        status: appealStatus,
        disposition_summary: dispositionSummary.trim(),
        reviewer_notes: appealNotes.trim() || undefined,
      });
      setSuccessMsg(`Appeal resolved for ${appealComplaint.complaint_code}. Final status: ${appealStatus}.`);
      setAppealComplaint(null);
      setSelectedAppeal(null);
      setDispositionSummary("");
      setAppealNotes("");
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to resolve appeal.");
    } finally {
      setResolvingAppeal(false);
    }
  };

  const handleCloseComplaint = async (id: string, code: string) => {
    if (!confirm(`Are you sure you want to close and seal grievance record ${code}?`)) return;

    try {
      setError(null);
      await api.closeComplaint(id);
      setSuccessMsg(`Record ${code} officially closed and sealed.`);
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to close grievance.");
    }
  };

  const handleDownloadEvidence = async (complaintId: string, evidenceId: string, fileName: string) => {
    try {
      const url = api.downloadComplaintEvidenceUrl(complaintId, evidenceId);
      const blob = await api.downloadFileBlob(url);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError("Failed to download evidence.");
    }
  };

  const getLeaveStatusBadge = (status: LeaveStatus) => {
    switch (status) {
      case "SUBMITTED":
        return <Badge variant="warning">Submitted</Badge>;
      case "UNDER_REVIEW":
        return <Badge variant="primary">Under Review</Badge>;
      case "APPROVED":
        return <Badge variant="success">Approved</Badge>;
      case "REJECTED":
        return <Badge variant="danger">Rejected</Badge>;
      case "CANCELLED":
        return <Badge variant="outline">Cancelled</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getComplaintStatusBadge = (status: ComplaintStatus) => {
    switch (status) {
      case "SUBMITTED":
        return <Badge variant="warning">Submitted</Badge>;
      case "UNDER_REVIEW":
        return <Badge variant="primary">Under Review</Badge>;
      case "NEEDS_INFORMATION":
        return <Badge variant="warning">Needs Info</Badge>;
      case "VERIFIED":
        return <Badge variant="success">Verified</Badge>;
      case "DISMISSED":
        return <Badge variant="outline">Dismissed</Badge>;
      case "OTHER_AUTHORIZED_OUTCOME":
        return <Badge variant="neutral">Other Outcome</Badge>;
      case "APPEALED":
        return <Badge variant="danger">Appealed</Badge>;
      case "RESOLVED":
        return <Badge variant="success">Resolved</Badge>;
      case "CLOSED":
        return <Badge variant="outline">Closed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const tabItems = [
    { id: "leaves", label: `Institutional Leaves (${leaves.length})` },
    { id: "complaints", label: `Grievance Records (${complaints.length})` },
  ];

  return (
    <ProtectedRoute requiredRoles={["ADMIN", "SUPER_ADMIN"]}>
      <div className="relative min-h-screen bg-[#07090D] overflow-hidden py-8 px-4">
        <RingBackground variant="hero" />
        <div className="relative z-10 container mx-auto max-w-6xl space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <Link
                href="/admin"
                className="p-2 text-surface-400 hover:text-white hover:bg-white/5 rounded-lg border border-white/5 transition"
              >
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                  Institutional Records &amp; Grievance Oversight
                </h1>
                <p className="text-sm text-surface-400">
                  PulseRecord institutional management: official leaves of absence and protected grievances
                </p>
              </div>
            </div>
          </div>

          {/* Alerts */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-between text-rose-300 text-sm">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
              <button onClick={() => setError(null)} className="text-rose-400 hover:underline">
                Dismiss
              </button>
            </div>
          )}

          {successMsg && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-emerald-300 text-sm">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-emerald-400" />
                <span>{successMsg}</span>
              </div>
              <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:underline">
                Dismiss
              </button>
            </div>
          )}

          {/* Navigation Tabs */}
          <Tabs tabs={tabItems} activeTab={activeTab} onChange={setActiveTab} />

          {/* ===================== TAB 1: LEAVES ===================== */}
          {activeTab === "leaves" && (
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardHeader className="flex flex-row items-center justify-between border-b border-white/5 pb-4">
                <div>
                  <CardTitle className="text-white font-display text-lg">All Institutional Leave Requests</CardTitle>
                  <CardDescription className="text-surface-400">
                    Cross-departmental tracking of student absence requests and approvals
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Filter className="h-4 w-4 text-surface-400" />
                  <select
                    value={leaveStatusFilter}
                    onChange={(e) => setLeaveStatusFilter(e.target.value)}
                    className="rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-1.5 text-xs focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                  >
                    <option value="">All Statuses</option>
                    <option value="SUBMITTED">Submitted</option>
                    <option value="UNDER_REVIEW">Under Review</option>
                    <option value="APPROVED">Approved</option>
                    <option value="REJECTED">Rejected</option>
                    <option value="CANCELLED">Cancelled</option>
                  </select>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <div className="py-12 flex justify-center items-center text-surface-400 space-x-2">
                    <Clock className="h-6 w-6 animate-spin text-[#FF9A3D]" />
                    <span>Loading leaves...</span>
                  </div>
                ) : leaves.length === 0 ? (
                  <EmptyState
                    icon={FileText}
                    title="No leave records"
                    description="No leave requests match the current criteria."
                  />
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#0D1117]">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-[#111722]/80 border-b border-white/10 text-xs font-mono uppercase text-surface-400 tracking-wider">
                        <tr>
                          <th className="py-3 px-4">Student ID / Enrollment</th>
                          <th className="py-3 px-4">Type</th>
                          <th className="py-3 px-4">Dates</th>
                          <th className="py-3 px-4">Days</th>
                          <th className="py-3 px-4">Reason</th>
                          <th className="py-3 px-4">Reviewer</th>
                          <th className="py-3 px-4">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {leaves.map((l) => (
                          <tr key={l.id} className="hover:bg-[#111722]/40 transition">
                            <td className="py-3 px-4 font-mono text-xs text-[#FF9A3D]">
                              {l.enrollment_number || l.student_id.slice(0, 8)}
                            </td>
                            <td className="py-3 px-4 font-medium text-white capitalize">
                              {l.leave_type.replace("_", " ")}
                            </td>
                            <td className="py-3 px-4 text-surface-300 text-xs">
                              {l.start_date} to {l.end_date}
                            </td>
                            <td className="py-3 px-4 font-semibold text-white">
                              {l.days_count}
                            </td>
                            <td className="py-3 px-4 max-w-xs truncate text-surface-300">
                              {l.reason}
                            </td>
                            <td className="py-3 px-4 text-xs text-surface-400">
                              {l.reviewer_name || l.reviewed_by_user_id?.slice(0, 8) || "—"}
                            </td>
                            <td className="py-3 px-4">{getLeaveStatusBadge(l.status)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* ===================== TAB 2: COMPLAINTS ===================== */}
          {activeTab === "complaints" && (
            <div className="space-y-6">
              <Card className="bg-[#0D1117] border-white/10 hover-lift">
                <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
                  <div>
                    <CardTitle className="text-white font-display text-lg">Institutional Grievance Case Registry</CardTitle>
                    <CardDescription className="text-surface-400">
                      End-to-end management of official grievance cases, reviewer assignment, adjudication, and appeals
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      value={complaintCategoryFilter}
                      onChange={(e) => setComplaintCategoryFilter(e.target.value)}
                      className="rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-1.5 text-xs focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                    >
                      <option value="">All Categories</option>
                      <option value="ACADEMIC_INTEGRITY">Academic Integrity</option>
                      <option value="GRADING_DISPUTE">Grading Dispute</option>
                      <option value="FACILITY_HARASSMENT">Facility / Bullying</option>
                      <option value="DISCRIMINATION">Discrimination</option>
                      <option value="SAFETY_CONCERN">Safety Concern</option>
                      <option value="OTHER">Other</option>
                    </select>

                    <select
                      value={complaintStatusFilter}
                      onChange={(e) => setComplaintStatusFilter(e.target.value)}
                      className="rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-1.5 text-xs focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                    >
                      <option value="">All Statuses</option>
                      <option value="SUBMITTED">Submitted</option>
                      <option value="UNDER_REVIEW">Under Review</option>
                      <option value="NEEDS_INFORMATION">Needs Information</option>
                      <option value="VERIFIED">Verified</option>
                      <option value="DISMISSED">Dismissed</option>
                      <option value="OTHER_AUTHORIZED_OUTCOME">Other Outcome</option>
                      <option value="APPEALED">Appealed</option>
                      <option value="RESOLVED">Resolved</option>
                      <option value="CLOSED">Closed</option>
                    </select>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {loading ? (
                    <div className="py-12 flex justify-center items-center text-surface-400 space-x-2">
                      <Clock className="h-6 w-6 animate-spin text-[#FF9A3D]" />
                      <span>Loading grievances...</span>
                    </div>
                  ) : complaints.length === 0 ? (
                    <EmptyState
                      icon={ShieldAlert}
                      title="No grievances on record"
                      description="No complaint records found matching the specified filters."
                    />
                  ) : (
                    <div className="space-y-4">
                      {complaints.map((item) => {
                        const canAssign = item.status === "SUBMITTED" || item.status === "UNDER_REVIEW";
                        const canAdjudicate = item.status === "UNDER_REVIEW";
                        const canRequestInfo = item.status === "UNDER_REVIEW";
                        const hasActiveAppeal = item.status === "APPEALED" && item.appeals && item.appeals.length > 0;
                        const canClose = item.status === "RESOLVED" || (item.status !== "CLOSED" && ["VERIFIED", "DISMISSED", "OTHER_AUTHORIZED_OUTCOME"].includes(item.status));

                        return (
                          <div
                            key={item.id}
                            className="border border-white/10 bg-[#0D1117] rounded-xl p-5 space-y-4 hover:border-white/20 transition hover-lift"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-3">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-[#111722] rounded text-[#FF9A3D] border border-white/10">
                                  {item.complaint_code}
                                </span>
                                <span className="text-xs uppercase font-medium text-surface-400 font-mono">
                                  {item.category.replace("_", " ")} • Target: {item.target_type}
                                </span>
                                {item.is_anonymous ? (
                                  <div className="inline-flex items-center space-x-1.5">
                                    <span className="inline-flex items-center space-x-1 text-[11px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                                      <EyeOff className="h-3 w-3" />
                                      <span>Anonymous Complainant</span>
                                    </span>
                                    {item.complainant_user_id && (
                                      <span className="text-[11px] font-mono text-surface-400 bg-[#111722] px-2 py-0.5 rounded-full border border-white/5">
                                        Accountable ID: {item.complainant_user_id.slice(0, 8)} ({item.complainant_role || "Reporter"})
                                      </span>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-[11px] text-surface-400 bg-[#111722] px-2 py-0.5 rounded-full border border-white/5 font-mono">
                                    User: {item.complainant_user_id?.slice(0, 8)} ({item.complainant_role || "User"})
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                {getComplaintStatusBadge(item.status)}
                                {item.adjudication_outcome && (
                                  <Badge variant="outline" className="text-xs font-mono border-white/10 text-surface-300">
                                    {item.adjudication_outcome}
                                  </Badge>
                                )}
                              </div>
                            </div>

                            <div>
                              <h3 className="font-semibold text-white text-base font-display">
                                {item.title}
                              </h3>
                              <p className="mt-1 text-sm text-surface-300 whitespace-pre-wrap">
                                {item.description}
                              </p>
                            </div>

                            {/* Adjudication summary & internal notes */}
                            {item.adjudication_summary && (
                              <div className="p-3.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-sm text-purple-200 space-y-1">
                                <p className="font-semibold text-xs uppercase tracking-wider text-purple-300 font-mono">
                                  Adjudication Disposition ({item.adjudication_outcome}):
                                </p>
                                <p>{item.adjudication_summary}</p>
                                {item.internal_reviewer_notes && (
                                  <p className="text-xs text-purple-300/80 italic pt-1 border-t border-purple-500/20">
                                    Internal Notes: {item.internal_reviewer_notes}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Appeals Display */}
                            {item.appeals && item.appeals.length > 0 && (
                              <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-sm text-rose-200 space-y-2">
                                <p className="font-semibold text-xs uppercase tracking-wider text-rose-300 font-mono">
                                  Appellate History ({item.appeals.length} Appeal(s)):
                                </p>
                                {item.appeals.map((app) => (
                                  <div key={app.id} className="text-xs border-b border-rose-500/20 pb-2 last:border-b-0 last:pb-0">
                                    <div className="flex items-center justify-between font-medium">
                                      <span>Appeal #{app.appeal_number} — Status: {app.status}</span>
                                      <span className="font-mono text-surface-400">{new Date(app.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <p className="mt-1 text-surface-300">&ldquo;{app.reason}&rdquo;</p>
                                    {app.disposition_summary && (
                                      <p className="mt-1 font-semibold text-emerald-400">
                                        Disposition: {app.disposition_summary}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Footer / Actions Bar */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-white/5 text-xs">
                              <div className="flex items-center space-x-3 text-surface-400 font-mono">
                                <span>
                                  Reviewer: {item.assigned_reviewer_name || (item.assigned_reviewer_id ? item.assigned_reviewer_id.slice(0, 8) : "Unassigned")}
                                </span>
                                <button
                                  onClick={() => setEvidenceComplaint(item)}
                                  className="flex items-center space-x-1 font-medium text-[#FF9A3D] hover:underline"
                                >
                                  <Paperclip className="h-3.5 w-3.5" />
                                  <span>{item.evidence_count} evidence item(s)</span>
                                </button>
                              </div>

                              <div className="flex flex-wrap items-center gap-2">
                                {canAssign && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setAssignComplaint(item);
                                      setReviewerUserId(item.assigned_reviewer_id || "");
                                    }}
                                    className="text-xs flex items-center space-x-1 border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                                  >
                                    <UserCheck className="h-3.5 w-3.5" />
                                    <span>Assign</span>
                                  </Button>
                                )}

                                {canRequestInfo && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setRequestInfoComplaint(item);
                                      setInfoRequestText("");
                                    }}
                                    className="text-xs text-[#FF9A3D] border-[#FF7A18]/30 hover:bg-[#FF7A18]/10 flex items-center space-x-1"
                                  >
                                    <Send className="h-3.5 w-3.5" />
                                    <span>Request Info</span>
                                  </Button>
                                )}

                                {canAdjudicate && (
                                  <Button
                                    size="sm"
                                    onClick={() => {
                                      setAdjudicateComplaint(item);
                                      setAdjudicateStatus("VERIFIED");
                                      setAdjudicateOutcome("POLICY_VIOLATION_SUBSTANTIATED");
                                      setAdjudicateSummary("");
                                      setInternalNotes("");
                                    }}
                                    className="text-xs bg-purple-600 hover:bg-purple-500 text-white flex items-center space-x-1"
                                  >
                                    <Scale className="h-3.5 w-3.5" />
                                    <span>Adjudicate</span>
                                  </Button>
                                )}

                                {hasActiveAppeal && (
                                  <Button
                                    size="sm"
                                    onClick={() => {
                                      setAppealComplaint(item);
                                      setSelectedAppeal(item.appeals?.[item.appeals.length - 1] || null);
                                      setAppealStatus("UPHELD");
                                      setDispositionSummary("");
                                      setAppealNotes("");
                                    }}
                                    className="text-xs bg-rose-600 hover:bg-rose-500 text-white flex items-center space-x-1"
                                  >
                                    <Scale className="h-3.5 w-3.5" />
                                    <span>Resolve Appeal</span>
                                  </Button>
                                )}

                                {canClose && item.status !== "CLOSED" && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleCloseComplaint(item.id, item.complaint_code)}
                                    className="text-xs text-surface-400 hover:text-white border-white/10 hover:bg-white/5 flex items-center space-x-1"
                                  >
                                    <Archive className="h-3.5 w-3.5" />
                                    <span>Close Record</span>
                                  </Button>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Modal: Assign Reviewer */}
          <Modal
            isOpen={!!assignComplaint}
            onClose={() => setAssignComplaint(null)}
            title={`Assign Reviewer (${assignComplaint?.complaint_code})`}
          >
            <form onSubmit={handleAssignReviewer} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Reviewer / Investigator User ID (UUID) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  value={reviewerUserId}
                  onChange={(e) => setReviewerUserId(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 font-mono text-xs placeholder-surface-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setAssignComplaint(null)} className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
                  Cancel
                </Button>
                <Button type="submit" disabled={assigning} className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20">
                  {assigning ? "Assigning..." : "Confirm Assignment"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Request Information */}
          <Modal
            isOpen={!!requestInfoComplaint}
            onClose={() => setRequestInfoComplaint(null)}
            title={`Request Clarification (${requestInfoComplaint?.complaint_code})`}
          >
            <form onSubmit={handleRequestInfo} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Specific Clarifications Required *
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Specify the documentation, witness accounts, or details needed from the complainant..."
                  value={infoRequestText}
                  onChange={(e) => setInfoRequestText(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setRequestInfoComplaint(null)} className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
                  Cancel
                </Button>
                <Button type="submit" disabled={requestingInfo} className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20">
                  {requestingInfo ? "Sending..." : "Issue Request"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Adjudicate Complaint */}
          <Modal
            isOpen={!!adjudicateComplaint}
            onClose={() => setAdjudicateComplaint(null)}
            title={`Adjudicate Grievance (${adjudicateComplaint?.complaint_code})`}
          >
            <form onSubmit={handleAdjudicate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-surface-300 mb-1">
                    Adjudication Verdict *
                  </label>
                  <select
                    value={adjudicateStatus}
                    onChange={(e) => setAdjudicateStatus(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                  >
                    <option value="VERIFIED">VERIFIED (Substantiated)</option>
                    <option value="DISMISSED">DISMISSED (Unfounded / Lack of Evidence)</option>
                    <option value="OTHER_AUTHORIZED_OUTCOME">OTHER_AUTHORIZED_OUTCOME (Administrative)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-surface-300 mb-1">
                    Specific Outcome Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. POLICY_VIOLATION_SUBSTANTIATED"
                    value={adjudicateOutcome}
                    onChange={(e) => setAdjudicateOutcome(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 font-mono text-xs placeholder-surface-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Official Adjudication Summary (Visible to Parties) *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Findings of fact, rationale, and policy references..."
                  value={adjudicateSummary}
                  onChange={(e) => setAdjudicateSummary(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Internal Reviewer Notes (Privileged / Institutional Only)
                </label>
                <textarea
                  rows={2}
                  placeholder="Confidential notes, sanction recommendations, or advisor observations..."
                  value={internalNotes}
                  onChange={(e) => setInternalNotes(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setAdjudicateComplaint(null)} className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
                  Cancel
                </Button>
                <Button type="submit" disabled={adjudicating} className="bg-purple-600 hover:bg-purple-500 text-white font-medium">
                  {adjudicating ? "Recording..." : "Record Adjudication"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Resolve Appeal */}
          <Modal
            isOpen={!!appealComplaint && !!selectedAppeal}
            onClose={() => {
              setAppealComplaint(null);
              setSelectedAppeal(null);
            }}
            title={`Appellate Review (${appealComplaint?.complaint_code})`}
          >
            <form onSubmit={handleResolveAppeal} className="space-y-4">
              <div className="p-3 bg-[#111722] rounded-lg border border-white/10 text-xs space-y-1">
                <p className="font-semibold text-white">
                  Appeal #{selectedAppeal?.appeal_number} Grounds:
                </p>
                <p className="text-surface-300 italic">
                  &ldquo;{selectedAppeal?.reason}&rdquo;
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Appellate Decision *
                </label>
                <select
                  value={appealStatus}
                  onChange={(e) => setAppealStatus(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                >
                  <option value="UPHELD">UPHELD (Original Decision Stands)</option>
                  <option value="OVERTURNED">OVERTURNED (Adjudication Reversed)</option>
                  <option value="MODIFIED">MODIFIED (Corrected Remedy / Disposition)</option>
                  <option value="DISMISSED">DISMISSED (Lack of Appellate Merit)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Appellate Disposition Summary *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Formal decision of the appellate authority..."
                  value={dispositionSummary}
                  onChange={(e) => setDispositionSummary(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Internal Appellate Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Institutional records regarding appeal evaluation..."
                  value={appealNotes}
                  onChange={(e) => setAppealNotes(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setAppealComplaint(null);
                    setSelectedAppeal(null);
                  }}
                  className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={resolvingAppeal} className="bg-rose-600 hover:bg-rose-500 text-white font-medium">
                  {resolvingAppeal ? "Resolving..." : "Issue Appellate Ruling"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: View Evidence */}
          <Modal
            isOpen={!!evidenceComplaint}
            onClose={() => setEvidenceComplaint(null)}
            title={`Evidence Repository (${evidenceComplaint?.complaint_code})`}
          >
            <div className="space-y-4">
              {(!evidenceComplaint?.evidence || evidenceComplaint.evidence.length === 0) ? (
                <p className="text-sm text-surface-400 italic py-2">
                  No evidence items attached to this case.
                </p>
              ) : (
                <ul className="divide-y divide-white/5">
                  {evidenceComplaint.evidence.map((ev) => (
                    <li key={ev.id} className="py-2.5 flex items-center justify-between hover:bg-white/5 px-2 rounded-lg transition">
                      <div className="flex items-center space-x-2.5 truncate max-w-sm">
                        <Paperclip className="h-4 w-4 text-surface-400 flex-shrink-0" />
                        <div className="truncate">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium text-white truncate">
                              {ev.file_name}
                            </p>
                            {ev.is_confidential && (
                              <span className="inline-flex items-center space-x-0.5 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">
                                <Lock className="h-2.5 w-2.5" />
                                <span>Confidential</span>
                              </span>
                            )}
                            {ev.is_sealed && (
                              <span className="inline-flex items-center space-x-0.5 text-[10px] text-surface-400 bg-[#111722] px-1.5 py-0.2 rounded border border-white/5">
                                <Archive className="h-2.5 w-2.5" />
                                <span>Sealed</span>
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-surface-400 font-mono">
                            {(ev.file_size_bytes / 1024).toFixed(1)} KB • Role: {ev.uploader_role} • SHA256: {ev.sha256_hash.slice(0, 8)}...
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownloadEvidence(evidenceComplaint.id, ev.id, ev.file_name)}
                        className="p-1.5 h-8 w-8 border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                        title="Download Evidence"
                      >
                        <Download className="h-4 w-4 text-surface-300" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex justify-end pt-2">
                <Button variant="outline" onClick={() => setEvidenceComplaint(null)} className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
                  Close
                </Button>
              </div>
            </div>
          </Modal>
        </div>
      </div>
    </ProtectedRoute>
  );
}
