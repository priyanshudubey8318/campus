"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import {
  Complaint,
  ComplaintCategory,
  ComplaintTargetType,
  ComplaintStatus,
  ComplaintCreatePayload,
} from "@/types/pulserecord";
import {
  ShieldAlert,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  Paperclip,
  Download,
  Lock,
  EyeOff,
  Scale,
  Send,
  Upload,
} from "lucide-react";

export default function StudentComplaintsPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New Complaint Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState<ComplaintCreatePayload>({
    category: "ACADEMIC_INTEGRITY",
    target_type: "FACULTY",
    title: "",
    description: "",
    is_anonymous: false,
  });

  // Provide Info Modal
  const [activeComplaintForInfo, setActiveComplaintForInfo] = useState<Complaint | null>(null);
  const [infoResponseText, setInfoResponseText] = useState("");
  const [respondingInfo, setRespondingInfo] = useState(false);

  // Appeal Modal
  const [activeComplaintForAppeal, setActiveComplaintForAppeal] = useState<Complaint | null>(null);
  const [appealReasonText, setAppealReasonText] = useState("");
  const [submittingAppeal, setSubmittingAppeal] = useState(false);

  // Evidence Modal
  const [activeEvidenceComplaint, setActiveEvidenceComplaint] = useState<Complaint | null>(null);
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [evidenceDesc, setEvidenceDesc] = useState("");
  const [evidenceConfidential, setEvidenceConfidential] = useState(false);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getOwnComplaints();
      setComplaints(data);
      if (activeEvidenceComplaint) {
        const updated = data.find((c) => c.id === activeEvidenceComplaint.id);
        if (updated) setActiveEvidenceComplaint(updated);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load complaints");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.title.trim() || !createForm.description.trim()) {
      setError("Please provide a complete title and description.");
      return;
    }

    try {
      setCreating(true);
      setError(null);
      const created = await api.createComplaint(createForm);
      setSuccessMsg(`Grievance record filed successfully with tracking code: ${created.complaint_code}`);
      setIsCreateOpen(false);
      setCreateForm({
        category: "ACADEMIC_INTEGRITY",
        target_type: "FACULTY",
        title: "",
        description: "",
        is_anonymous: false,
      });
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to file grievance.");
      }
    } finally {
      setCreating(false);
    }
  };

  const handleProvideInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeComplaintForInfo || !infoResponseText.trim()) return;

    try {
      setRespondingInfo(true);
      setError(null);
      await api.provideComplaintInfo(activeComplaintForInfo.id, infoResponseText);
      setSuccessMsg(`Information submitted for ${activeComplaintForInfo.complaint_code}. Status returned to Under Review.`);
      setActiveComplaintForInfo(null);
      setInfoResponseText("");
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to submit information response.");
      }
    } finally {
      setRespondingInfo(false);
    }
  };

  const handleAppeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeComplaintForAppeal || !appealReasonText.trim()) return;

    try {
      setSubmittingAppeal(true);
      setError(null);
      await api.appealComplaint(activeComplaintForAppeal.id, appealReasonText);
      setSuccessMsg(`Appeal filed successfully for ${activeComplaintForAppeal.complaint_code}.`);
      setActiveComplaintForAppeal(null);
      setAppealReasonText("");
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to submit appeal.");
      }
    } finally {
      setSubmittingAppeal(false);
    }
  };

  const handleUploadEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeEvidenceComplaint || !evidenceFile) return;

    try {
      setUploadingEvidence(true);
      setError(null);
      await api.uploadComplaintEvidence(
        activeEvidenceComplaint.id,
        evidenceFile,
        evidenceDesc.trim() || undefined,
        evidenceConfidential
      );
      setSuccessMsg(`Evidence "${evidenceFile.name}" securely attached.`);
      setEvidenceFile(null);
      setEvidenceDesc("");
      setEvidenceConfidential(false);
      await fetchComplaints();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to upload evidence.");
      }
    } finally {
      setUploadingEvidence(false);
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
      setError("Failed to download evidence file.");
    }
  };

  const getStatusBadge = (status: ComplaintStatus) => {
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

  const totalComplaints = complaints.length;
  const inReviewComplaints = complaints.filter(
    (c) => c.status === "SUBMITTED" || c.status === "UNDER_REVIEW" || c.status === "NEEDS_INFORMATION"
  ).length;
  const appealableComplaints = complaints.filter(
    (c) => ["VERIFIED", "DISMISSED", "OTHER_AUTHORIZED_OUTCOME"].includes(c.status)
  ).length;
  const resolvedComplaints = complaints.filter(
    (c) => c.status === "RESOLVED" || c.status === "CLOSED"
  ).length;

  return (
    <ProtectedRoute requiredRoles={["STUDENT"]}>
      <div className="relative min-h-screen bg-[#07090D] overflow-hidden py-8 px-4">
        <RingBackground variant="hero" />
        <div className="relative z-10 container mx-auto max-w-6xl space-y-6">
          {/* Top Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <Link
                href="/student"
                className="p-2 text-surface-400 hover:text-white hover:bg-white/5 rounded-lg border border-white/5 transition"
              >
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                  Grievances &amp; Complaints
                </h1>
                <p className="text-sm text-surface-400">
                  Confidential grievance reporting, tracking, and appellate review
                </p>
              </div>
            </div>
            <Button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center space-x-2 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20"
            >
              <Plus className="h-4 w-4" />
              <span>File Grievance</span>
            </Button>
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

          {/* Stats Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Total Filed</p>
                  <p className="text-2xl font-bold text-white mt-1 font-display">{totalComplaints}</p>
                </div>
                <ShieldAlert className="h-8 w-8 text-surface-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Active In Review</p>
                  <p className="text-2xl font-bold text-amber-400 mt-1 font-display">{inReviewComplaints}</p>
                </div>
                <Clock className="h-8 w-8 text-amber-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Adjudicated</p>
                  <p className="text-2xl font-bold text-purple-400 mt-1 font-display">{appealableComplaints}</p>
                </div>
                <Scale className="h-8 w-8 text-purple-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Resolved / Closed</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1 font-display">{resolvedComplaints}</p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </CardContent>
            </Card>
          </div>

          {/* Grievance List */}
          <Card className="bg-[#0D1117] border-white/10 hover-lift">
            <CardHeader className="border-b border-white/5 pb-4">
              <CardTitle className="text-white font-display text-lg">My Grievance Filings</CardTitle>
              <CardDescription className="text-surface-400">
                Protected records of official complaints, investigator correspondence, and appeals
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {loading ? (
                <div className="py-12 flex justify-center items-center text-surface-400 space-x-2">
                  <Clock className="h-6 w-6 animate-spin text-[#FF9A3D]" />
                  <span>Loading grievance records...</span>
                </div>
              ) : complaints.length === 0 ? (
                <EmptyState
                  icon={ShieldAlert}
                  title="No grievances on record"
                  description="You have not filed any formal complaints. If you experience academic or facility issues, click the button to submit a protected grievance."
                  actionText="File Grievance"
                  onAction={() => setIsCreateOpen(true)}
                />
              ) : (
                <div className="space-y-4">
                  {complaints.map((item) => {
                    const needsInfo = item.status === "NEEDS_INFORMATION";
                    const canAppeal =
                      ["VERIFIED", "DISMISSED", "OTHER_AUTHORIZED_OUTCOME"].includes(item.status) &&
                      item.status !== "APPEALED" &&
                      item.status !== "CLOSED";

                    return (
                      <div
                        key={item.id}
                        className="border border-white/10 bg-[#0D1117] rounded-xl p-5 space-y-4 hover:border-white/20 transition hover-lift"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-3">
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-[#111722] rounded text-[#FF9A3D] border border-white/10">
                              {item.complaint_code}
                            </span>
                            <span className="text-xs uppercase font-medium text-surface-400 font-mono">
                              {item.category.replace("_", " ")} • Target: {item.target_type}
                            </span>
                            {item.is_anonymous ? (
                              <span className="inline-flex items-center space-x-1 text-[11px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                                <EyeOff className="h-3 w-3" />
                                <span>Anonymous Filing</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center space-x-1 text-[11px] text-surface-400 bg-[#111722] px-2 py-0.5 rounded-full border border-white/5 font-mono">
                                <span>Direct Filing</span>
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            {getStatusBadge(item.status)}
                            {item.adjudication_outcome && (
                              <Badge variant="outline" className="text-xs font-mono border-white/10 text-surface-300">
                                {item.adjudication_outcome}
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Content */}
                        <div>
                          <h3 className="font-semibold text-white text-base font-display">
                            {item.title}
                          </h3>
                          <p className="mt-1 text-sm text-surface-300 whitespace-pre-wrap">
                            {item.description}
                          </p>
                        </div>

                        {/* Adjudication summary */}
                        {item.adjudication_summary && (
                          <div className="p-3.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-sm text-purple-200">
                            <p className="font-semibold text-xs uppercase tracking-wider text-purple-300 mb-1 font-mono">
                              Adjudication Disposition:
                            </p>
                            <p>{item.adjudication_summary}</p>
                          </div>
                        )}

                        {/* Needs Information Alert Box */}
                        {needsInfo && (
                          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg space-y-3">
                            <div className="flex items-start space-x-2">
                              <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="text-xs font-bold uppercase tracking-wider text-amber-300 font-mono">
                                  Additional Information Requested by Reviewer
                                </p>
                                <p className="text-sm text-amber-200 mt-1">
                                  {item.info_request_details || "The reviewer has requested additional clarification to process this grievance."}
                                </p>
                              </div>
                            </div>
                            <Button
                              size="sm"
                              onClick={() => {
                                setActiveComplaintForInfo(item);
                                setInfoResponseText("");
                              }}
                              className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20 flex items-center space-x-1"
                            >
                              <Send className="h-3.5 w-3.5" />
                              <span>Respond to Information Request</span>
                            </Button>
                          </div>
                        )}

                        {/* Info Response Details if already answered */}
                        {!needsInfo && item.info_response_details && (
                          <div className="text-xs text-surface-400 italic bg-[#111722] border border-white/5 p-2 rounded-lg">
                            Your response: &ldquo;{item.info_response_details}&rdquo;
                          </div>
                        )}

                        {/* Footer Actions & Metadata */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-white/5 text-xs text-surface-400 font-mono">
                          <div className="flex items-center space-x-4">
                            <span>Filed: {new Date(item.created_at).toLocaleDateString()}</span>
                            <button
                              onClick={() => setActiveEvidenceComplaint(item)}
                              className="flex items-center space-x-1 font-medium text-[#FF9A3D] hover:underline"
                            >
                              <Paperclip className="h-3.5 w-3.5" />
                              <span>{item.evidence_count} evidence item(s)</span>
                            </button>
                            {item.appeal_count > 0 && (
                              <span className="font-semibold text-rose-400">
                                {item.appeal_count} appeal(s) filed
                              </span>
                            )}
                          </div>

                          <div className="flex items-center space-x-2">
                            {canAppeal && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setActiveComplaintForAppeal(item);
                                  setAppealReasonText("");
                                }}
                                className="text-rose-400 border-rose-500/20 hover:bg-rose-500/10 flex items-center space-x-1 text-xs"
                              >
                                <Scale className="h-3.5 w-3.5" />
                                <span>Appeal Adjudication</span>
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

          {/* Modal: File Complaint */}
          <Modal
            isOpen={isCreateOpen}
            onClose={() => setIsCreateOpen(false)}
            title="File Protected Grievance"
          >
            <form onSubmit={handleCreateComplaint} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-surface-300 mb-1">
                    Category *
                  </label>
                  <select
                    value={createForm.category}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, category: e.target.value as ComplaintCategory })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                  >
                    <option value="ACADEMIC_INTEGRITY">Academic Integrity</option>
                    <option value="GRADING_DISPUTE">Grading Dispute</option>
                    <option value="FACILITY_HARASSMENT">Facility / Bullying</option>
                    <option value="DISCRIMINATION">Discrimination</option>
                    <option value="SAFETY_CONCERN">Safety / Security Concern</option>
                    <option value="OTHER">Other Institutional Grievance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-surface-300 mb-1">
                    Target Entity *
                  </label>
                  <select
                    value={createForm.target_type}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, target_type: e.target.value as ComplaintTargetType })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                  >
                    <option value="FACULTY">Faculty Member</option>
                    <option value="STUDENT">Student</option>
                    <option value="DEPARTMENT">Academic Department</option>
                    <option value="FACILITY">Campus Facility</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Grievance Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Brief summary of the incident or dispute..."
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Detailed Incident Description *
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Provide dates, locations, involved individuals, and factual description..."
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="p-3 bg-[#111722] rounded-lg border border-white/10 flex items-start space-x-3">
                <input
                  id="is_anonymous"
                  type="checkbox"
                  checked={createForm.is_anonymous}
                  onChange={(e) => setCreateForm({ ...createForm, is_anonymous: e.target.checked })}
                  className="h-4 w-4 mt-0.5 rounded border-white/10 bg-[#0D1117] text-[#FF7A18] focus:ring-[#FF7A18]"
                />
                <label htmlFor="is_anonymous" className="text-xs text-surface-300 cursor-pointer">
                  <span className="font-semibold text-white">Anonymous Reporting</span>:
                  Your identity will be redacted from the accused subject or department. Institutional leadership
                  maintains internal accountability to protect against fraudulent claims while safeguarding your privacy.
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCreateOpen(false)}
                  className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={creating}
                  className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20"
                >
                  {creating ? "Filing..." : "Submit Grievance"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Respond to Information Request */}
          <Modal
            isOpen={!!activeComplaintForInfo}
            onClose={() => setActiveComplaintForInfo(null)}
            title={`Provide Information (${activeComplaintForInfo?.complaint_code})`}
          >
            <form onSubmit={handleProvideInfo} className="space-y-4">
              <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20 text-xs text-amber-200">
                <p className="font-semibold text-amber-300 font-mono">Reviewer Request:</p>
                <p className="mt-1">{activeComplaintForInfo?.info_request_details}</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Your Clarification / Response *
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Provide the requested details or answers here..."
                  value={infoResponseText}
                  onChange={(e) => setInfoResponseText(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setActiveComplaintForInfo(null)}
                  className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={respondingInfo}
                  className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20"
                >
                  {respondingInfo ? "Submitting..." : "Send Clarification"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Appeal Adjudication */}
          <Modal
            isOpen={!!activeComplaintForAppeal}
            onClose={() => setActiveComplaintForAppeal(null)}
            title={`File Formal Appeal (${activeComplaintForAppeal?.complaint_code})`}
          >
            <form onSubmit={handleAppeal} className="space-y-4">
              <div className="p-3 bg-[#111722] rounded-lg border border-white/10 text-xs">
                <p className="font-semibold text-white">Adjudicated Outcome:</p>
                <p className="mt-0.5 text-surface-300">
                  {activeComplaintForAppeal?.adjudication_outcome}: {activeComplaintForAppeal?.adjudication_summary}
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Appellate Grounds &amp; Justification *
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Explain why the adjudication was in error or what new evidence exists..."
                  value={appealReasonText}
                  onChange={(e) => setAppealReasonText(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setActiveComplaintForAppeal(null)}
                  className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={submittingAppeal}
                  className="bg-rose-600 hover:bg-rose-500 text-white font-medium"
                >
                  {submittingAppeal ? "Submitting..." : "Submit Appeal"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Evidence Files */}
          <Modal
            isOpen={!!activeEvidenceComplaint}
            onClose={() => {
              setActiveEvidenceComplaint(null);
              setEvidenceFile(null);
            }}
            title={`Evidence Repository (${activeEvidenceComplaint?.complaint_code})`}
          >
            <div className="space-y-5">
              {(!activeEvidenceComplaint?.evidence || activeEvidenceComplaint.evidence.length === 0) ? (
                <p className="text-sm text-surface-400 italic py-2">
                  No evidence items attached to this grievance.
                </p>
              ) : (
                <ul className="divide-y divide-white/5">
                  {activeEvidenceComplaint.evidence.map((ev) => (
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
                          </div>
                          <p className="text-xs text-surface-400 font-mono">
                            {(ev.file_size_bytes / 1024).toFixed(1)} KB • Role: {ev.uploader_role}
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownloadEvidence(activeEvidenceComplaint.id, ev.id, ev.file_name)}
                        className="p-1.5 h-8 w-8 border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                        title="Download Evidence"
                      >
                        <Download className="h-4 w-4 text-surface-300" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}

              {/* Upload form if not closed */}
              {activeEvidenceComplaint?.status !== "CLOSED" ? (
                <form onSubmit={handleUploadEvidence} className="border-t border-white/10 pt-4 space-y-3">
                  <h4 className="text-xs font-semibold text-surface-300 uppercase tracking-wider font-mono">
                    Add Supporting Evidence
                  </h4>
                  <div className="space-y-2">
                    <input
                      type="file"
                      required
                      onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                      className="text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border file:border-white/10 file:text-xs file:font-medium file:bg-[#111722] file:text-surface-300 hover:file:bg-white/10 text-surface-300 w-full"
                    />
                    <input
                      type="text"
                      placeholder="Short description of this document..."
                      value={evidenceDesc}
                      onChange={(e) => setEvidenceDesc(e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-1.5 text-xs focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                    />
                    <div className="flex items-center space-x-2">
                      <input
                        id="confidential_chk"
                        type="checkbox"
                        checked={evidenceConfidential}
                        onChange={(e) => setEvidenceConfidential(e.target.checked)}
                        className="h-3.5 w-3.5 rounded border-white/10 bg-[#0D1117] text-[#FF7A18] focus:ring-[#FF7A18]"
                      />
                      <label htmlFor="confidential_chk" className="text-xs text-surface-300 cursor-pointer">
                        Mark as confidential (accessible only to authorized investigators)
                      </label>
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      size="sm"
                      disabled={uploadingEvidence || !evidenceFile}
                      className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20 flex items-center space-x-1"
                    >
                      <Upload className="h-3.5 w-3.5" />
                      <span>{uploadingEvidence ? "Uploading..." : "Upload Evidence"}</span>
                    </Button>
                  </div>
                </form>
              ) : (
                <p className="text-xs text-surface-400 italic border-t border-white/10 pt-3">
                  This grievance is closed. Evidence is sealed and immutable.
                </p>
              )}
            </div>
          </Modal>
        </div>
      </div>
    </ProtectedRoute>
  );
}
