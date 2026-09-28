"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { api, ApiError } from "@/lib/api/client";
import { FacultyReferralReceipt } from "@/types/pulsecase";
import {
  Compass,
  PlusCircle,
  RefreshCw,
  AlertTriangle,
  Info,
  Clock,
  CheckCircle2,
} from "lucide-react";

export default function MyFacultyReferralsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [referrals, setReferrals] = useState<FacultyReferralReceipt[]>([]);

  const loadReferrals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getFacultyReferrals();
      setReferrals(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load academic referrals.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReferrals();
  }, [loadReferrals]);

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

  return (
    <ProtectedRoute requiredRoles={["FACULTY", "ADMIN", "SUPER_ADMIN"]}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold font-display tracking-tight text-white flex items-center gap-2">
              <Compass className="h-7 w-7 text-[#FF7A18]" />
              My Academic Support Referrals
            </h1>
            <p className="text-sm text-surface-400 mt-1">
              Track advising intake status and resolution outcomes for your student referrals.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadReferrals()}
              disabled={loading}
              className="flex items-center gap-1.5 border-white/10 hover:border-[#FF7A18]/40 hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#FF7A18]" : ""}`} />
              Refresh
            </Button>
            <Link href="/academic/referrals/new">
              <Button variant="primary" size="sm" className="flex items-center gap-1.5">
                <PlusCircle className="h-4 w-4" />
                Submit New Referral
              </Button>
            </Link>
          </div>
        </div>

        {/* Privacy & Confidentiality Notice */}
        <div className="rounded-xl border border-white/10 bg-[#0D1117] p-4 text-xs text-surface-400 flex items-start gap-3">
          <Info className="h-5 w-5 shrink-0 text-[#FF9A3D] mt-0.5" />
          <div className="space-y-1 leading-relaxed">
            <p className="font-semibold text-white">
              Student Privacy Invariant
            </p>
            <p>
              To protect student privacy and clinical boundaries under institutional policy, faculty tracking
              is limited to lifecycle status and high-level outcomes. Internal case worker notes and
              counseling logs remain strictly confidential.
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-950/30 p-4 text-xs text-red-400 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Referrals Table */}
        <Card className="border-white/10 bg-[#0D1117] overflow-hidden">
          <CardHeader className="pb-3 border-b border-white/10">
            <CardTitle className="text-base font-semibold text-white font-display">Submitted Referrals</CardTitle>
            <CardDescription className="text-xs text-surface-400">
              Showing {referrals.length} referrals submitted by you
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {referrals.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  title="No Referrals Submitted"
                  description="You have not submitted any student advising referrals yet. Click 'Submit New Referral' to refer a student."
                  icon={Compass}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[#111722] text-xs uppercase text-surface-400 border-b border-white/10 font-mono">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Case Number</th>
                      <th className="px-4 py-3 font-semibold">Student</th>
                      <th className="px-4 py-3 font-semibold">Priority</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold">Submitted</th>
                      <th className="px-4 py-3 font-semibold">Resolution Outcome</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {referrals.map((r) => (
                      <tr
                        key={r.id}
                        className="hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="px-4 py-3.5 font-mono font-medium text-[#FF9A3D]">
                          {r.case_number}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-medium text-white">
                            {r.student_name || "Enrolled Student"}
                          </div>
                          <div className="text-xs text-surface-400 font-mono">
                            {r.student_id.slice(0, 8)}...
                          </div>
                        </td>
                        <td className="px-4 py-3.5">{getPriorityBadge(r.priority)}</td>
                        <td className="px-4 py-3.5">{getStatusBadge(r.status)}</td>
                        <td className="px-4 py-3.5 text-xs text-surface-400 whitespace-nowrap font-mono">
                          {new Date(r.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3.5 text-xs text-surface-300">
                          {r.resolution_outcome
                            ? r.resolution_outcome.replace(/_/g, " ")
                            : r.status === "CLOSED" || r.status === "RESOLVED"
                            ? "Completed"
                            : "In Triage"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
