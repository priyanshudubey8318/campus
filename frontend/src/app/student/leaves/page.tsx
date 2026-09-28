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
  LeaveRequest,
  LeaveType,
  LeaveStatus,
  LeaveRequestPayload,
  LeaveCancelPayload,
} from "@/types/pulserecord";
import {
  FileText,
  Plus,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Ban,
  ArrowLeft,
  AlertCircle,
  Paperclip,
  Download,
  Trash2,
  Upload,
} from "lucide-react";

export default function StudentLeavesPage() {
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New Leave Request Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState<LeaveRequestPayload>({
    leave_type: "PERSONAL",
    start_date: new Date().toISOString().split("T")[0],
    end_date: new Date().toISOString().split("T")[0],
    reason: "",
  });

  // Cancel Leave Modal
  const [selectedLeaveForCancel, setSelectedLeaveForCancel] = useState<LeaveRequest | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [cancelForm, setCancelForm] = useState<LeaveCancelPayload>({
    cancellation_reason: "",
  });

  // Attachments Modal
  const [activeAttachmentLeave, setActiveAttachmentLeave] = useState<LeaveRequest | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fetchLeaves = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getOwnLeaves();
      setLeaves(data);
      if (activeAttachmentLeave) {
        const updated = data.find((l) => l.id === activeAttachmentLeave.id);
        if (updated) setActiveAttachmentLeave(updated);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load leave requests");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.reason.trim()) {
      setError("Please provide a reason for the leave request.");
      return;
    }
    if (new Date(createForm.end_date) < new Date(createForm.start_date)) {
      setError("End date cannot be prior to start date.");
      return;
    }

    try {
      setCreating(true);
      setError(null);
      const created = await api.createLeave(createForm);
      setSuccessMsg(`Leave request submitted successfully (${created.days_count} day(s)).`);
      setIsCreateOpen(false);
      setCreateForm({
        leave_type: "PERSONAL",
        start_date: new Date().toISOString().split("T")[0],
        end_date: new Date().toISOString().split("T")[0],
        reason: "",
      });
      await fetchLeaves();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to submit leave request.");
      }
    } finally {
      setCreating(false);
    }
  };

  const handleCancelLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeaveForCancel) return;
    if (!cancelForm.cancellation_reason.trim()) {
      setError("Please provide a reason for cancellation.");
      return;
    }

    try {
      setCancelling(true);
      setError(null);
      await api.cancelLeave(selectedLeaveForCancel.id, cancelForm);
      setSuccessMsg("Leave request cancelled successfully.");
      setSelectedLeaveForCancel(null);
      setCancelForm({ cancellation_reason: "" });
      await fetchLeaves();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to cancel leave request.");
      }
    } finally {
      setCancelling(false);
    }
  };

  const handleUploadAttachment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAttachmentLeave || !selectedFile) return;

    try {
      setUploadingFile(true);
      setError(null);
      await api.uploadLeaveAttachment(activeAttachmentLeave.id, selectedFile);
      setSuccessMsg(`Attachment "${selectedFile.name}" uploaded successfully.`);
      setSelectedFile(null);
      await fetchLeaves();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to upload attachment.");
      }
    } finally {
      setUploadingFile(false);
    }
  };

  const handleDeleteAttachment = async (leaveId: string, attachmentId: string) => {
    if (!confirm("Are you sure you want to remove this attachment?")) return;
    try {
      setError(null);
      await api.deleteLeaveAttachment(leaveId, attachmentId);
      setSuccessMsg("Attachment removed.");
      await fetchLeaves();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to delete attachment.");
      }
    }
  };

  const handleDownloadAttachment = async (leaveId: string, attachmentId: string, fileName: string) => {
    try {
      const url = api.downloadLeaveAttachmentUrl(leaveId, attachmentId);
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
      setError("Failed to download attachment.");
    }
  };

  const getStatusBadge = (status: LeaveStatus) => {
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

  // Stats calculation
  const totalLeaves = leaves.length;
  const pendingLeaves = leaves.filter((l) => l.status === "SUBMITTED" || l.status === "UNDER_REVIEW").length;
  const approvedLeaves = leaves.filter((l) => l.status === "APPROVED").length;
  const totalApprovedDays = leaves
    .filter((l) => l.status === "APPROVED")
    .reduce((acc, curr) => acc + curr.days_count, 0);

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
                  Leave Management
                </h1>
                <p className="text-sm text-surface-400">
                  Request, track, and manage official student leave of absence
                </p>
              </div>
            </div>
            <Button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center space-x-2 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20"
            >
              <Plus className="h-4 w-4" />
              <span>New Leave Request</span>
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
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Total Requests</p>
                  <p className="text-2xl font-bold text-white mt-1 font-display">{totalLeaves}</p>
                </div>
                <FileText className="h-8 w-8 text-surface-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">In Review</p>
                  <p className="text-2xl font-bold text-amber-400 mt-1 font-display">{pendingLeaves}</p>
                </div>
                <Clock className="h-8 w-8 text-amber-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Approved Leaves</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1 font-display">{approvedLeaves}</p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Approved Days</p>
                  <p className="text-2xl font-bold text-white mt-1 font-display">{totalApprovedDays}</p>
                </div>
                <Calendar className="h-8 w-8 text-[#FF9A3D]" />
              </CardContent>
            </Card>
          </div>

          {/* Main Leave Records List */}
          <Card className="bg-[#0D1117] border-white/10 hover-lift">
            <CardHeader className="border-b border-white/5 pb-4">
              <CardTitle className="text-white font-display text-lg">Leave History &amp; Applications</CardTitle>
              <CardDescription className="text-surface-400">
                All formal leave requests and institutional review status
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {loading ? (
                <div className="py-12 flex justify-center items-center text-surface-400 space-x-2">
                  <Clock className="h-6 w-6 animate-spin text-[#FF9A3D]" />
                  <span>Loading leave records...</span>
                </div>
              ) : leaves.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No leave requests filed"
                  description="You have not submitted any leave of absence requests yet. Click the button above to request a new leave."
                  actionText="New Leave Request"
                  onAction={() => setIsCreateOpen(true)}
                />
              ) : (
                <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#0D1117]">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-[#111722]/80 border-b border-white/10 text-xs font-mono uppercase text-surface-400 tracking-wider">
                      <tr>
                        <th className="py-3 px-4">Type</th>
                        <th className="py-3 px-4">Period</th>
                        <th className="py-3 px-4">Days</th>
                        <th className="py-3 px-4">Reason &amp; Feedback</th>
                        <th className="py-3 px-4">Attachments</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {leaves.map((leave) => {
                        const canCancel = leave.status === "SUBMITTED" || leave.status === "UNDER_REVIEW";

                        return (
                          <tr key={leave.id} className="hover:bg-[#111722]/40 transition">
                            <td className="py-3 px-4 font-medium text-white">
                              <span className="capitalize">{leave.leave_type.replace("_", " ")}</span>
                            </td>
                            <td className="py-3 px-4 text-surface-300">
                              <div>{leave.start_date}</div>
                              <div className="text-xs text-surface-400">to {leave.end_date}</div>
                            </td>
                            <td className="py-3 px-4 font-semibold text-white">
                              {leave.days_count} {leave.days_count === 1 ? "day" : "days"}
                            </td>
                            <td className="py-3 px-4 max-w-xs">
                              <p className="line-clamp-2 text-surface-300">{leave.reason}</p>
                              {leave.reviewer_notes && (
                                <div className="mt-1 text-xs text-surface-400 italic bg-[#111722] border border-white/5 p-1.5 rounded">
                                  Reviewer note: &ldquo;{leave.reviewer_notes}&rdquo;
                                </div>
                              )}
                              {leave.cancellation_reason && (
                                <div className="mt-1 text-xs text-rose-400 italic">
                                  Cancelled: &ldquo;{leave.cancellation_reason}&rdquo;
                                </div>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              <button
                                onClick={() => setActiveAttachmentLeave(leave)}
                                className="flex items-center space-x-1 text-xs font-medium text-[#FF9A3D] hover:underline"
                              >
                                <Paperclip className="h-3.5 w-3.5" />
                                <span>{leave.attachment_count} file(s)</span>
                              </button>
                            </td>
                            <td className="py-3 px-4">{getStatusBadge(leave.status)}</td>
                            <td className="py-3 px-4 text-right space-x-2">
                              {canCancel && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedLeaveForCancel(leave);
                                    setCancelForm({ cancellation_reason: "" });
                                  }}
                                  className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border-rose-500/20 text-xs"
                                >
                                  Cancel
                                </Button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Modal: New Leave Request */}
          <Modal
            isOpen={isCreateOpen}
            onClose={() => setIsCreateOpen(false)}
            title="Submit Leave Request"
          >
            <form onSubmit={handleCreateLeave} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Leave Category *
                </label>
                <select
                  value={createForm.leave_type}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, leave_type: e.target.value as LeaveType })
                  }
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                >
                  <option value="PERSONAL">Personal Leave</option>
                  <option value="MEDICAL">Medical / Health Absence</option>
                  <option value="ACADEMIC_DUTY">Academic Duty / Conference</option>
                  <option value="EMERGENCY">Family / Personal Emergency</option>
                  <option value="BEREAVEMENT">Bereavement</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-surface-300 mb-1">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={createForm.start_date}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, start_date: e.target.value })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-surface-300 mb-1">
                    End Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={createForm.end_date}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, end_date: e.target.value })
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Reason &amp; Context *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Explain the necessity of leave and academic makeup arrangements..."
                  value={createForm.reason}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, reason: e.target.value })
                  }
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
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
                  {creating ? "Submitting..." : "Submit Leave Request"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: Cancel Leave Request */}
          <Modal
            isOpen={!!selectedLeaveForCancel}
            onClose={() => setSelectedLeaveForCancel(null)}
            title="Cancel Leave Request"
          >
            <form onSubmit={handleCancelLeave} className="space-y-4">
              <p className="text-sm text-surface-300">
                Are you sure you want to cancel this leave request? This action cannot be undone.
              </p>
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Cancellation Reason *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Schedule changed, emergency resolved..."
                  value={cancelForm.cancellation_reason}
                  onChange={(e) =>
                    setCancelForm({ cancellation_reason: e.target.value })
                  }
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedLeaveForCancel(null)}
                  className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                >
                  Keep Request
                </Button>
                <Button
                  type="submit"
                  disabled={cancelling}
                  className="bg-rose-600 hover:bg-rose-500 text-white font-medium"
                >
                  {cancelling ? "Cancelling..." : "Confirm Cancellation"}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: View & Manage Attachments */}
          <Modal
            isOpen={!!activeAttachmentLeave}
            onClose={() => {
              setActiveAttachmentLeave(null);
              setSelectedFile(null);
            }}
            title={`Supporting Documents (${activeAttachmentLeave?.attachment_count || 0})`}
          >
            <div className="space-y-5">
              {/* Existing attachments */}
              {(!activeAttachmentLeave?.attachments || activeAttachmentLeave.attachments.length === 0) ? (
                <p className="text-sm text-surface-400 italic py-2">
                  No attachments uploaded for this leave request.
                </p>
              ) : (
                <ul className="divide-y divide-white/5">
                  {activeAttachmentLeave.attachments.map((att) => (
                    <li key={att.id} className="py-2.5 flex items-center justify-between hover:bg-white/5 px-2 rounded-lg transition">
                      <div className="flex items-center space-x-2.5 truncate max-w-sm">
                        <Paperclip className="h-4 w-4 text-surface-400 flex-shrink-0" />
                        <div className="truncate">
                          <p className="text-sm font-medium text-white truncate">
                            {att.file_name}
                          </p>
                          <p className="text-xs text-surface-400 font-mono">
                            {(att.file_size_bytes / 1024).toFixed(1)} KB • SHA256: {att.sha256_hash.slice(0, 8)}...
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadAttachment(activeAttachmentLeave.id, att.id, att.file_name)}
                          className="p-1.5 h-8 w-8 border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                          title="Download Document"
                        >
                          <Download className="h-4 w-4 text-surface-300" />
                        </Button>
                        {activeAttachmentLeave.status === "SUBMITTED" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteAttachment(activeAttachmentLeave.id, att.id)}
                            className="p-1.5 h-8 w-8 text-rose-400 border-rose-500/20 hover:bg-rose-500/10"
                            title="Delete Attachment"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              {/* Upload new attachment - only if SUBMITTED */}
              {activeAttachmentLeave?.status === "SUBMITTED" ? (
                <form onSubmit={handleUploadAttachment} className="border-t border-white/10 pt-4 space-y-3">
                  <h4 className="text-xs font-semibold text-surface-300 uppercase tracking-wider font-mono">
                    Upload Supporting Document
                  </h4>
                  <div className="flex items-center space-x-3">
                    <input
                      type="file"
                      required
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      className="text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border file:border-white/10 file:text-xs file:font-medium file:bg-[#111722] file:text-surface-300 hover:file:bg-white/10 text-surface-300"
                    />
                    <Button
                      type="submit"
                      size="sm"
                      disabled={uploadingFile || !selectedFile}
                      className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20 flex items-center space-x-1"
                    >
                      <Upload className="h-3.5 w-3.5" />
                      <span>{uploadingFile ? "Uploading..." : "Upload"}</span>
                    </Button>
                  </div>
                  <p className="text-[11px] text-surface-400">
                    Allowed file types: PDF, PNG, JPEG, WEBP. Maximum 10MB per file.
                  </p>
                </form>
              ) : (
                <p className="text-xs text-surface-400 italic border-t border-white/10 pt-3">
                  Attachments cannot be modified once the request moves beyond Submitted state.
                </p>
              )}
            </div>
          </Modal>
        </div>
      </div>
    </ProtectedRoute>
  );
}
