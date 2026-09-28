"use client";

import React, { useCallback, useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import { StudentSupportSummary } from "@/types/pulsecase";
import {
  HeartHandshake,
  UserCheck,
  CheckSquare,
  Calendar,
  RefreshCw,
  AlertTriangle,
  Clock,
  Sparkles,
  BookOpen,
} from "lucide-react";

export default function StudentSupportPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [supportData, setSupportData] = useState<StudentSupportSummary | null>(null);

  const loadSupportData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getStudentSupportSummary();
      setSupportData(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load student support items.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSupportData();
  }, [loadSupportData]);

  return (
    <ProtectedRoute requiredRoles={["STUDENT", "ADMIN", "SUPER_ADMIN"]}>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header Hero */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 shadow-2xl">
          <RingBackground variant="hero" className="opacity-40" />
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#FF7A18]/10 border border-[#FF7A18]/20 text-[#FF9A3D] text-xs font-mono mb-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF7A18] animate-pulse" />
                ACADEMIC SUCCESS &amp; WELLBEING
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white flex items-center gap-2.5">
                <HeartHandshake className="h-7 w-7 text-[#FF7A18]" />
                Student Support &amp; Academic Success
              </h1>
              <p className="text-sm text-surface-400 mt-1">
                Your personalized academic action plan, advising support, and upcoming appointments.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadSupportData()}
              disabled={loading}
              className="flex items-center gap-1.5 self-start sm:self-auto border-white/10 hover:border-[#FF7A18]/40 hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#FF7A18]" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Supportive Banner */}
        <div className="rounded-xl border border-white/10 bg-[#0D1117] p-5 text-sm text-surface-200 flex items-start gap-4">
          <div className="rounded-lg bg-[#FF7A18]/10 p-2.5 text-[#FF9A3D]">
            <Sparkles className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-base text-white font-display">
              We&apos;re Here to Help You Succeed
            </h3>
            <p className="text-xs text-surface-400 leading-relaxed">
              Every student faces academic challenges from time to time. This support center connects you
              directly with designated advisors, peer tutors, and resources designed to help you stay on track
              and reach your educational goals.
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-950/30 p-4 text-xs text-red-400 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Assigned Advisor Card */}
        <Card className="border-white/10 bg-[#0D1117]">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="rounded-full bg-[#111722] border border-white/10 p-3 text-[#FF9A3D]">
              <UserCheck className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xs uppercase font-semibold text-surface-400 font-mono tracking-wider">
                Your Academic Advisor
              </span>
              <h3 className="text-base font-semibold text-white font-display mt-0.5">
                {supportData?.assigned_advisor_name || "Academic Advising Center"}
              </h3>
              <p className="text-xs text-surface-400 mt-0.5">
                {supportData?.assigned_advisor_name
                  ? "Assigned personal advisor for academic progression and graduation support."
                  : "Your department advising committee will assign a dedicated advisor upon intake."}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Action Items List */}
        <Card className="border-white/10 bg-[#0D1117]">
          <CardHeader className="border-b border-white/10 pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-white font-display flex items-center gap-2">
                  <CheckSquare className="h-5 w-5 text-emerald-400" />
                  Your Academic Action Items
                </CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Active milestones and tasks agreed upon with your advising team
                </CardDescription>
              </div>
              <Badge variant="neutral" className="font-mono text-xs">
                {supportData?.support_action_items.length || 0} Items
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            {!supportData || supportData.support_action_items.length === 0 ? (
              <EmptyState
                title="No Pending Action Items"
                description="You are all caught up! When you and your advisor agree on specific goals or tutoring plans, they will appear here."
                icon={BookOpen}
              />
            ) : (
              <div className="space-y-3">
                {supportData.support_action_items.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-lg border border-white/10 bg-[#111722] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-white">
                          {item.title}
                        </span>
                        <Badge variant="neutral" className="text-[10px]">
                          {item.intervention_type.replace(/_/g, " ")}
                        </Badge>
                        <Badge
                          variant={item.status === "COMPLETED" ? "success" : "primary"}
                          className="text-[10px]"
                        >
                          {item.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-surface-400 mt-1">
                        {item.description}
                      </p>
                      {item.target_date && (
                        <span className="text-[11px] text-surface-400 mt-1 block font-mono">
                          Target Completion: {item.target_date}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Check-in Appointments */}
        <Card className="border-white/10 bg-[#0D1117]">
          <CardHeader className="border-b border-white/10 pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-white font-display flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-[#FF7A18]" />
                  Scheduled Check-in Appointments
                </CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Upcoming advising meetings and progress reviews
                </CardDescription>
              </div>
              <Badge variant="neutral" className="font-mono text-xs">
                {supportData?.upcoming_follow_ups.length || 0} Scheduled
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            {!supportData || supportData.upcoming_follow_ups.length === 0 ? (
              <EmptyState
                title="No Upcoming Appointments"
                description="You have no check-in appointments currently scheduled."
                icon={Calendar}
              />
            ) : (
              <div className="space-y-3">
                {supportData.upcoming_follow_ups.map((f) => (
                  <div
                    key={f.id}
                    className="p-4 rounded-lg border border-white/10 bg-[#111722] flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-[#FF7A18]/10 p-2 text-[#FF9A3D]">
                        <Clock className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-white font-mono">
                            {f.scheduled_date} {f.scheduled_time && `at ${f.scheduled_time}`}
                          </span>
                          <Badge variant="neutral" className="text-[10px]">
                            {f.follow_up_type.replace(/_/g, " ")}
                          </Badge>
                        </div>
                        <span className="text-xs text-surface-400 mt-0.5 block font-mono">
                          Status: {f.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
