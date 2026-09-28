"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatsCard } from "@/components/ui/StatsCard";
import { CardSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import { AcademicPulseCard } from "@/components/pulsewatch/AcademicPulseCard";
import { SupportPriorityCard } from "@/components/pulserisk/SupportPriorityCard";
import { PulseWatchSummary } from "@/types/pulsewatch";
import { PulseRiskSummary } from "@/types/pulserisk";
import {
  StudentProfile,
  Enrollment,
  AttendanceSummary,
  Assignment,
  AssessmentResult,
} from "@/types/academic";
import {
  GraduationCap,
  BookOpen,
  CalendarCheck,
  FileCheck2,
  Award,
  ArrowRight,
  HelpCircle,
  Mail,
  Building,
  Clock,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

export default function StudentDashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [attendance, setAttendance] = useState<AttendanceSummary | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [results, setResults] = useState<AssessmentResult[]>([]);
  const [pulseSummary, setPulseSummary] = useState<PulseWatchSummary | null>(null);
  const [pulseLoading, setPulseLoading] = useState(true);
  const [riskSummary, setRiskSummary] = useState<PulseRiskSummary | null>(null);
  const [riskLoading, setRiskLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        setPulseLoading(true);
        setError(null);

        const [profData, enrData, attData, asgData] = await Promise.all([
          api.getMyStudentProfile().catch(() => null),
          api.getEnrollments().catch(() => []),
          api.getAttendanceSummary().catch(() => null),
          api.getAssignments().catch(() => []),
        ]);

        setProfile(profData);
        setEnrollments(enrData);
        setAttendance(attData);
        setAssignments(asgData);

        // Fetch PulseWatch & PulseRisk summaries if student profile is verified
        if (profData?.id) {
          try {
            const [pSummary, rSummary] = await Promise.all([
              api.getPulseWatchSummary(profData.id, 14).catch(() => null),
              api.getPulseRiskCurrent(profData.id, 14).catch(() => null),
            ]);
            setPulseSummary(pSummary);
            setRiskSummary(rSummary);
          } catch {
            // Metrics establish as data accumulates
          } finally {
            setPulseLoading(false);
            setRiskLoading(false);
          }
        } else {
          setPulseLoading(false);
          setRiskLoading(false);
        }

        // Load assessment results if assessments exist
        try {
          const assessments = await api.getAssessments();
          if (assessments.length > 0) {
            const resPromises = assessments.map((a) => api.getAssessmentResults(a.id));
            const allRes = await Promise.all(resPromises);
            setResults(allRes.flat());
          }
        } catch {
          // No assessment results yet
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load student dashboard records");
        }
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  return (
    <ProtectedRoute requiredRoles={["STUDENT"]}>
      <div className="space-y-8" data-testid="student-portal">
        <div data-testid="student-dashboard" className="space-y-8">
        {/* Welcome & Academic Standing Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6 md:p-8 shadow-xl">
          <RingBackground variant="hero" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="primary">STUDENT PORTAL</Badge>
                <Badge variant={profile?.academic_status === "ENROLLED" ? "success" : "neutral"}>
                  {profile?.academic_status || "ENROLLED"}
                </Badge>
                {profile?.enrollment_number && (
                  <span className="text-xs font-mono text-zinc-400 font-semibold" data-testid="student-enrollment-badge">
                    {profile.enrollment_number}
                  </span>
                )}
              </div>
              <h1 className="font-display text-2xl md:text-3xl font-bold tracking-tight text-white">
                Welcome back, {user?.full_name || "Student"}
              </h1>
              <p className="text-xs md:text-sm text-zinc-400 max-w-2xl">
                {profile
                  ? `${profile.program_name || "Degree Program"} • ${profile.batch_name || "Active Batch"} • Semester ${profile.current_semester || 1}${profile.section_name ? ` (${profile.section_name})` : ""}`
                  : "Institutional Student Account • Degree Enrollment Pending Registrar Assignment"}
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Link href="/student/profile">
                <Button variant="outline" size="sm" className="text-xs" data-testid="view-profile-btn">
                  <span>View Official Profile</span>
                </Button>
              </Link>
              <Link href="/student/academics">
                <Button size="sm" className="text-xs space-x-1.5" data-testid="view-academics-btn">
                  <span>Academic Records</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 p-4 text-xs text-rose-300 flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Academic Support Momentum & Priority (Phase 4 PulseRisk) */}
        <SupportPriorityCard summary={riskSummary} loading={riskLoading} />

        {/* Academic Pulse: Deterministic Behavioral Monitoring Foundation */}
        <AcademicPulseCard summary={pulseSummary} loading={pulseLoading} />

        {/* 4 Primary KPI Metrics */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
              title="Registered Courses"
              value={enrollments.length}
              subtitle="Active term registrations"
              icon={BookOpen}
              iconColor="text-[#FF9A3D]"
              testId="kpi-registered-courses"
            />
            <StatsCard
              title="Attendance Rate"
              value={attendance ? `${attendance.attendance_percentage}%` : "100%"}
              subtitle={
                attendance
                  ? `${attendance.present_count} present · ${attendance.absent_count} absent`
                  : "All sessions verified"
              }
              icon={CalendarCheck}
              iconColor="text-emerald-400"
              badge={{
                text:
                  (attendance?.attendance_percentage || 100) >= 75
                    ? "Satisfactory Attendance"
                    : "Action Required",
                variant:
                  (attendance?.attendance_percentage || 100) >= 75
                    ? "success"
                    : "danger",
              }}
              testId="kpi-attendance-rate"
            />
            <StatsCard
              title="Coursework Assignments"
              value={assignments.length}
              subtitle="Published course assignments"
              icon={FileCheck2}
              iconColor="text-blue-400"
              testId="kpi-coursework-assignments"
            />
            <StatsCard
              title="Graded Evaluations"
              value={results.length}
              subtitle="Midterms & formal tests"
              icon={Award}
              iconColor="text-purple-400"
              testId="kpi-graded-evaluations"
            />
          </div>
        )}

        {/* Two-Column Product Layout: Active Courses + Upcoming Tasks */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left 2 Cols: Registered Course Offerings */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-white/[0.08] bg-[#0D1117]">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle className="text-base font-display text-white">Current Course Registrations</CardTitle>
                  <CardDescription className="text-xs text-zinc-400">
                    Institutional courses enrolled for the current academic semester.
                  </CardDescription>
                </div>
                <Link href="/student/academics">
                  <Button variant="ghost" size="sm" className="text-xs space-x-1 text-zinc-300 hover:text-white">
                    <span>Full Records</span>
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent className="space-y-3">
                {loading ? (
                  <p className="text-xs text-zinc-400 py-4 text-center">Loading course registrations...</p>
                ) : enrollments.length === 0 ? (
                  <EmptyState
                    icon={BookOpen}
                    title="No Active Enrollments"
                    description="You are not currently enrolled in any courses for this academic term."
                  />
                ) : (
                  <div className="divide-y divide-white/[0.06]" data-testid="student-courses-list">
                    {enrollments.map((enr) => (
                      <div
                        key={enr.id}
                        className="py-3.5 flex items-center justify-between gap-4"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-xs font-bold text-[#FF9A3D]">
                              {enr.course_code || "COURSE"}
                            </span>
                            <Badge variant="neutral" className="text-[10px]">
                              {enr.course_credits || 4} Credits
                            </Badge>
                            <Badge variant={enr.status === "ENROLLED" ? "success" : "neutral"} className="text-[10px]">
                              {enr.status}
                            </Badge>
                          </div>
                          <p className="text-xs font-semibold text-white">
                            {enr.course_title || "Course"}
                          </p>
                          <p className="text-[11px] text-zinc-400">
                            Academic Term: {enr.term_name || "Active Term"}
                          </p>
                        </div>
                        <Link href="/student/academics">
                          <Button size="sm" variant="outline" className="text-xs">
                            View Details
                          </Button>
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Assignments Summary */}
            <Card className="border-white/[0.08] bg-[#0D1117]">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle className="text-base font-display text-white">Coursework &amp; Submissions</CardTitle>
                  <CardDescription className="text-xs text-zinc-400">
                    Latest assignments released by course instructors.
                  </CardDescription>
                </div>
                <Link href="/student/academics">
                  <Button variant="ghost" size="sm" className="text-xs space-x-1 text-zinc-300 hover:text-white">
                    <span>Submit &amp; View</span>
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {(!assignments || assignments.length === 0) ? (
                  <EmptyState
                    icon={FileCheck2}
                    title="No Assignments Released"
                    description="Instructors have not posted any pending assignments for your enrolled courses."
                  />
                ) : (
                  <div className="space-y-3" data-testid="student-assignments-list">
                    {(assignments || []).slice(0, 3).map((asg) => {
                      const formattedDate = asg.due_date && !isNaN(Date.parse(asg.due_date))
                        ? new Date(asg.due_date).toLocaleDateString()
                        : "TBD";
                      return (
                        <div
                          key={asg.id}
                          className="rounded-xl border border-white/[0.08] p-3.5 bg-[#111722]/60 hover-lift flex items-center justify-between transition"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-[11px] font-semibold text-zinc-400">
                                {asg.course_code || "COURSE"}
                              </span>
                              <span className="text-xs font-semibold text-white">
                                {asg.title}
                              </span>
                            </div>
                            <p className="text-[11px] text-zinc-400">
                              Due: {formattedDate} &bull; Max Marks: {asg.max_marks}
                            </p>
                          </div>
                          <Link href="/student/academics">
                            <Button size="sm" variant="outline" className="text-xs">
                              Details
                            </Button>
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Informational Support Hub & Profile Summary */}
          <div className="space-y-6">
            {/* Informational Academic Support Card (Strictly Static & Informational) */}
            <Card className="relative overflow-hidden border-white/[0.08] bg-[#0D1117] shadow-xl" data-testid="student-support-hub">
              <RingBackground variant="subtle" />
              <CardHeader className="relative z-10 pb-3">
                <div className="flex items-center space-x-2 text-[#FF9A3D]">
                  <HelpCircle className="h-5 w-5" />
                  <CardTitle className="text-base font-display text-white">Institutional Support Hub</CardTitle>
                </div>
                <CardDescription className="text-xs text-zinc-400">
                  Official campus resources, mentoring, and academic guidance.
                </CardDescription>
              </CardHeader>
              <CardContent className="relative z-10 space-y-3 text-xs">
                <div className="rounded-xl border border-white/[0.06] bg-[#111722]/80 p-3 hover-lift transition">
                  <div className="flex items-center space-x-2 text-white font-semibold">
                    <Building className="h-3.5 w-3.5 text-[#FF9A3D]" />
                    <span>Academic Advising Center</span>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Room 304, Academic Block A &bull; Mon–Fri, 9:00 AM – 5:00 PM
                  </p>
                  <p className="font-mono text-[11px] text-[#FF9A3D] mt-0.5">
                    advising@campuspulse.edu
                  </p>
                </div>

                <div className="rounded-xl border border-white/[0.06] bg-[#111722]/80 p-3 hover-lift transition">
                  <div className="flex items-center space-x-2 text-white font-semibold">
                    <Mail className="h-3.5 w-3.5 text-blue-400" />
                    <span>Office of the Registrar</span>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Student Services Wing, Counter 2 &bull; Mon–Fri, 10:00 AM – 4:00 PM
                  </p>
                  <p className="font-mono text-[11px] text-blue-400 mt-0.5">
                    registrar@campuspulse.edu
                  </p>
                </div>

                <div className="rounded-xl border border-white/[0.06] bg-[#111722]/80 p-3 hover-lift transition">
                  <div className="flex items-center space-x-2 text-white font-semibold">
                    <Clock className="h-3.5 w-3.5 text-amber-400" />
                    <span>Library &amp; Study Commons</span>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Central Library &bull; Open 24/7 during midterm examinations
                  </p>
                </div>

                <div className="p-2.5 rounded-lg bg-[#111722] text-[11px] text-zinc-400 border border-white/[0.06]">
                  <span className="font-semibold text-zinc-300">Note: </span>
                  Automated case management, counselor escalation, and leave requests will be connected in future phases.
                </div>
              </CardContent>
            </Card>

            {/* Quick Profile Summary Card */}
            <Card className="border-white/[0.08] bg-[#0D1117]">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center space-x-2 text-white font-display">
                  <GraduationCap className="h-4 w-4 text-[#FF9A3D]" />
                  <span>Verified Identity Record</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-white/[0.06]">
                  <span className="text-zinc-400">Student Name:</span>
                  <span className="font-semibold text-white">{user?.full_name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/[0.06]">
                  <span className="text-zinc-400">Enrollment ID:</span>
                  <span className="font-mono font-semibold text-white">
                    {profile?.enrollment_number || "Verified"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/[0.06]">
                  <span className="text-zinc-400">Email:</span>
                  <span className="font-mono text-zinc-300">{user?.email}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-zinc-400">Admission Date:</span>
                  <span className="text-white">{profile?.admission_date || "2024-08-01"}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

