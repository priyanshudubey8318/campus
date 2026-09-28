"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api/client";
import { CasePriority, FacultyReferralCreatePayload } from "@/types/pulsecase";
import {
  Compass,
  ArrowLeft,
  Send,
  AlertTriangle,
  Info,
  CheckCircle2,
} from "lucide-react";

export default function NewFacultyReferralPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successReceipt, setSuccessReceipt] = useState<{
    case_number: string;
    student_id: string;
  } | null>(null);

  const [formData, setFormData] = useState<FacultyReferralCreatePayload>({
    student_id: "",
    reason: "",
    course_id: "",
    priority: "MEDIUM",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.student_id.trim()) {
      setError("Student ID or enrollment reference is required.");
      return;
    }
    if (formData.reason.trim().length < 5) {
      setError("Initial concern reason must be at least 5 characters.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const receipt = await api.submitFacultyReferral({
        student_id: formData.student_id.trim(),
        reason: formData.reason.trim(),
        course_id: formData.course_id?.trim() || undefined,
        priority: formData.priority,
      });

      setSuccessReceipt({
        case_number: receipt.case_number,
        student_id: receipt.student_id,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to submit faculty referral.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ProtectedRoute requiredRoles={["FACULTY", "ADMIN", "SUPER_ADMIN"]}>
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/academic/referrals/my">
            <Button variant="outline" size="sm" className="h-9 px-2.5 border-white/10 hover:border-[#FF7A18]/40 hover:text-white">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold font-display tracking-tight text-white flex items-center gap-2">
              <Compass className="h-6 w-6 text-[#FF7A18]" />
              Submit Academic Advising Referral
            </h1>
            <p className="text-sm text-surface-400 mt-0.5">
              Refer a student to academic advising or early intervention support services.
            </p>
          </div>
        </div>

        {/* Guidance Notice */}
        <div className="rounded-xl border border-[#FF7A18]/20 bg-[#FF7A18]/5 p-4 text-xs text-surface-300 flex items-start gap-3">
          <Info className="h-5 w-5 shrink-0 text-[#FF9A3D] mt-0.5" />
          <div className="space-y-1 leading-relaxed">
            <p className="font-semibold text-white">Professional Discretion Notice</p>
            <p>
              Faculty referrals trigger immediate intake in the Academic Advising triage queue.
              Please document observed academic indicators, missed coursework patterns, or engagement
              changes clearly. Note that any subsequent clinical or counseling notes remain strictly
              confidential.
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-950/30 p-4 text-xs text-red-400 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successReceipt ? (
          <Card className="border-emerald-500/20 bg-emerald-950/20 text-center p-8 space-y-4">
            <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-400" />
            <h3 className="text-lg font-bold text-white font-display">
              Referral Successfully Submitted
            </h3>
            <p className="text-sm text-surface-300">
              Advising intake case <span className="font-mono font-semibold text-[#FF9A3D]">{successReceipt.case_number}</span>{" "}
              has been opened and routed to the academic support team.
            </p>
            <div className="pt-2 flex justify-center gap-3">
              <Link href="/academic/referrals/my">
                <Button variant="primary" size="sm">
                  View My Referrals
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSuccessReceipt(null);
                  setFormData({
                    student_id: "",
                    reason: "",
                    course_id: "",
                    priority: "MEDIUM",
                  });
                }}
                className="border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white"
              >
                Submit Another Referral
              </Button>
            </div>
          </Card>
        ) : (
          <Card className="border-white/10 bg-[#0D1117]">
            <CardHeader className="border-b border-white/10 pb-3">
              <CardTitle className="text-base text-white font-display">Student &amp; Concern Details</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Provide accurate student information and clear descriptive observations.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                    Student UUID or Enrollment ID <span className="text-[#FF4D4D]">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Enter student ID..."
                    value={formData.student_id}
                    onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                      Associated Course ID (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Course UUID..."
                      value={formData.course_id || ""}
                      onChange={(e) => setFormData({ ...formData, course_id: e.target.value })}
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                      Urgency / Priority Level <span className="text-[#FF4D4D]">*</span>
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) =>
                        setFormData({ ...formData, priority: e.target.value as CasePriority })
                      }
                      className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                    >
                      <option value="LOW">Low (Routine Check-in)</option>
                      <option value="MEDIUM">Medium (Academic Concern)</option>
                      <option value="HIGH">High (Substantial Grade/Attendance Drop)</option>
                      <option value="URGENT">Urgent (Immediate Intervention Needed)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-surface-300 mb-1.5">
                    Observed Concerns &amp; Referral Reason <span className="text-[#FF4D4D]">*</span>
                  </label>
                  <textarea
                    rows={5}
                    required
                    placeholder="Describe specific observations, missed assignments, attendance patterns, or communications..."
                    value={formData.reason}
                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-[#111722] p-2.5 text-sm text-white placeholder:text-surface-500 focus:outline-none focus:border-[#FF7A18] focus:ring-1 focus:ring-[#FF7A18]"
                  />
                  <span className="text-[11px] text-surface-500 mt-1 block">Minimum 5 characters.</span>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
                  <Link href="/academic/referrals/my">
                    <Button type="button" variant="outline" className="border-white/10 hover:border-white/20 text-surface-300 hover:text-white">
                      Cancel
                    </Button>
                  </Link>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={submitting}
                    className="flex items-center gap-1.5"
                  >
                    <Send className="h-4 w-4" />
                    {submitting ? "Submitting Referral..." : "Submit Referral"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedRoute>
  );
}
