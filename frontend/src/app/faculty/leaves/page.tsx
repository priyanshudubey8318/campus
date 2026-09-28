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
import { LeaveRequest, LeaveStatus, LeaveReviewPayload } from "@/types/pulserecord";
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  AlertCircle,
  Paperclip,
  Download,
  Filter,
} from "lucide-react";

export default function FacultyLeavesPage() {
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filter
  const [statusFilter, setStatusFilter] = useState<string>("");

  // Review Modal
  const [selectedLeave, setSelectedLeave] = useState<LeaveRequest | null>(null);
  const [reviewForm, setReviewForm] = useState<LeaveReviewPayload>({
    status: "APPROVED",
    reviewer_notes: "",
  });
  const [reviewing, setReviewing] = useState(false);

  // Attachments Modal
  const [attachmentLeave, setAttachmentLeave] = useState<LeaveRequest | null>(null);

  const fetchLeaves = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAssignedLeaves(statusFilter || undefined);
      setLeaves(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load assigned student leave requests.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const handleReviewLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeave) return;

    try {
      setReviewing(true);
      setError(null);
      await api.reviewLeave(selectedLeave.id, reviewForm);
      setSuccessMsg(`Leave request marked as ${reviewForm.status}.`);
      setSelectedLeave(null);
      setReviewForm({ status: "APPROVED", reviewer_notes: "" });
      await fetchLeaves();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to review leave request.");
      }
    } finally {
      setReviewing(false);
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

  const pendingLeaves = leaves.filter((l) => l.status === "SUBMITTED" || l.status === "UNDER_REVIEW").length;
  const approvedLeaves = leaves.filter((l) => l.status === "APPROVED").length;
  const rejectedLeaves = leaves.filter((l) => l.status === "REJECTED").length;

  return (
    <ProtectedRoute requiredRoles={["FACULTY", "DEPARTMENT_HEAD", "ADMIN", "SUPER_ADMIN"]}>
      <div className="relative min-h-screen bg-[#07090D] overflow-hidden py-8 px-4">
        <RingBackground variant="hero" />
        <div className="relative z-10 container mx-auto max-w-6xl space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <Link
                href="/faculty"
                className="p-2 text-surface-400 hover:text-white hover:bg-white/5 rounded-lg border border-white/5 transition"
              >
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                  Student Leave Approvals
                </h1>
                <p className="text-sm text-surface-400">
                  Review and adjudicate absence requests for your enrolled and advisee students
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-surface-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
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

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Awaiting Decision</p>
                  <p className="text-2xl font-bold text-amber-400 mt-1 font-display">{pendingLeaves}</p>
                </div>
                <Clock className="h-8 w-8 text-amber-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Approved Requests</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1 font-display">{approvedLeaves}</p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </CardContent>
            </Card>
            <Card className="bg-[#0D1117] border-white/10 hover-lift">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-surface-400">Rejected Requests</p>
                  <p className="text-2xl font-bold text-rose-400 mt-1 font-display">{rejectedLeaves}</p>
                </div>
                <XCircle className="h-8 w-8 text-rose-400" />
              </CardContent>
            </Card>
          </div>

          {/* Table of Leaves */}
          <Card className="bg-[#0D1117] border-white/10 hover-lift">
            <CardHeader className="border-b border-white/5 pb-4">
              <CardTitle className="text-white font-display text-lg">Assigned Student Leave Requests</CardTitle>
              <CardDescription className="text-surface-400">
                Review supporting documentation and grant formal excused absence status
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {loading ? (
                <div className="py-12 flex justify-center items-center text-surface-400 space-x-2">
                  <Clock className="h-6 w-6 animate-spin text-[#FF9A3D]" />
                  <span>Loading assigned leaves...</span>
                </div>
              ) : leaves.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No leave requests found"
                  description="There are currently no student leave requests requiring your review."
                />
              ) : (
                <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#0D1117]">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-[#111722]/80 border-b border-white/10 text-xs font-mono uppercase text-surface-400 tracking-wider">
                      <tr>
                        <th className="py-3 px-4">Student</th>
                        <th className="py-3 px-4">Type</th>
                        <th className="py-3 px-4">Period</th>
                        <th className="py-3 px-4">Days</th>
                        <th className="py-3 px-4">Reason</th>
                        <th className="py-3 px-4">Evidence</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {leaves.map((item) => {
                        const canReview = item.status === "SUBMITTED" || item.status === "UNDER_REVIEW";

                        return (
                          <tr key={item.id} className="hover:bg-[#111722]/40 transition">
                            <td className="py-3 px-4">
                              <p className="font-semibold text-white">
                                {item.student_name || "Enrolled Student"}
                              </p>
                              <p className="text-xs text-[#FF9A3D] font-mono">
                                {item.enrollment_number || item.student_id.slice(0, 8)}
                              </p>
                            </td>
                            <td className="py-3 px-4 font-medium text-white">
                              <span className="capitalize">{item.leave_type.replace("_", " ")}</span>
                            </td>
                            <td className="py-3 px-4 text-surface-300">
                              <div>{item.start_date}</div>
                              <div className="text-xs text-surface-400">to {item.end_date}</div>
                            </td>
                            <td className="py-3 px-4 font-semibold text-white">
                              {item.days_count} {item.days_count === 1 ? "day" : "days"}
                            </td>
                            <td className="py-3 px-4 max-w-xs">
                              <p className="line-clamp-2 text-surface-300">{item.reason}</p>
                              {item.reviewer_notes && (
                                <p className="text-xs text-surface-400 italic mt-1 bg-[#111722] p-1.5 rounded border border-white/5">
                                  Note: {item.reviewer_notes}
                                </p>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              <button
                                onClick={() => setAttachmentLeave(item)}
                                className="flex items-center space-x-1 text-xs font-medium text-[#FF9A3D] hover:underline"
                              >
                                <Paperclip className="h-3.5 w-3.5" />
                                <span>{item.attachment_count} file(s)</span>
                              </button>
                            </td>
                            <td className="py-3 px-4">{getStatusBadge(item.status)}</td>
                            <td className="py-3 px-4 text-right">
                              {canReview ? (
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setSelectedLeave(item);
                                    setReviewForm({ status: "APPROVED", reviewer_notes: "" });
                                  }}
                                  className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold text-xs shadow-md shadow-[#FF7A18]/20"
                                >
                                  Review Request
                                </Button>
                              ) : (
                                <span className="text-xs text-surface-400 font-mono">Adjudicated</span>
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

          {/* Modal: Review Leave Request */}
          <Modal
            isOpen={!!selectedLeave}
            onClose={() => setSelectedLeave(null)}
            title="Adjudicate Leave Request"
          >
            <form onSubmit={handleReviewLeave} className="space-y-4">
              <div className="p-3 bg-[#111722] rounded-lg border border-white/10 space-y-1 text-xs text-surface-300">
                <p>
                  <span className="font-semibold text-white">Student:</span> {selectedLeave?.student_name || "Enrolled Student"} ({selectedLeave?.enrollment_number})
                </p>
                <p>
                  <span className="font-semibold text-white">Dates:</span> {selectedLeave?.start_date} to {selectedLeave?.end_date} ({selectedLeave?.days_count} days)
                </p>
                <p>
                  <span className="font-semibold text-white">Type:</span> {selectedLeave?.leave_type}
                </p>
                <p>
                  <span className="font-semibold text-white">Student Reason:</span> {selectedLeave?.reason}
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Adjudication Decision *
                </label>
                <div className="flex items-center space-x-6">
                  <label className="flex items-center space-x-2 text-sm cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      value="APPROVED"
                      checked={reviewForm.status === "APPROVED"}
                      onChange={() => setReviewForm({ ...reviewForm, status: "APPROVED" })}
                      className="text-emerald-500 focus:ring-emerald-500 bg-[#0D1117] border-white/10"
                    />
                    <span className="font-medium text-emerald-400">Approve Leave</span>
                  </label>
                  <label className="flex items-center space-x-2 text-sm cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      value="REJECTED"
                      checked={reviewForm.status === "REJECTED"}
                      onChange={() => setReviewForm({ ...reviewForm, status: "REJECTED" })}
                      className="text-rose-500 focus:ring-rose-500 bg-[#0D1117] border-white/10"
                    />
                    <span className="font-medium text-rose-400">Reject Leave</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">
                  Reviewer Comments &amp; Academic Instructions
                </label>
                <textarea
                  rows={3}
                  placeholder="Specify makeup exam dates, required assignments, or reason for rejection..."
                  value={reviewForm.reviewer_notes || ""}
                  onChange={(e) => setReviewForm({ ...reviewForm, reviewer_notes: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-[#111722] text-white px-3 py-2 text-sm focus:border-[#FF7A18] focus:outline-none focus:ring-1 focus:ring-[#FF7A18]/30 placeholder-surface-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedLeave(null)}
                  className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={reviewing}
                  className={
                    reviewForm.status === "APPROVED"
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
                      : "bg-rose-600 hover:bg-rose-500 text-white font-medium"
                  }
                >
                  {reviewing ? "Saving..." : `Confirm ${reviewForm.status}`}
                </Button>
              </div>
            </form>
          </Modal>

          {/* Modal: View Attachments */}
          <Modal
            isOpen={!!attachmentLeave}
            onClose={() => setAttachmentLeave(null)}
            title={`Supporting Evidence (${attachmentLeave?.attachment_count || 0})`}
          >
            <div className="space-y-4">
              {(!attachmentLeave?.attachments || attachmentLeave.attachments.length === 0) ? (
                <p className="text-sm text-surface-400 italic py-2">
                  No attachments uploaded by student for this leave request.
                </p>
              ) : (
                <ul className="divide-y divide-white/5">
                  {attachmentLeave.attachments.map((att) => (
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
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownloadAttachment(attachmentLeave.id, att.id, att.file_name)}
                        className="p-1.5 h-8 w-8 border-white/10 text-surface-300 hover:text-white hover:bg-white/5"
                        title="Download Document"
                      >
                        <Download className="h-4 w-4 text-surface-300" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex justify-end pt-2">
                <Button variant="outline" onClick={() => setAttachmentLeave(null)} className="border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
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
