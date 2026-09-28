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
import { api, ApiError } from "@/lib/api/client";
import {
  Enrollment,
  AttendanceSummary,
  AttendanceRecord,
  Assignment,
  AssessmentResult,
} from "@/types/academic";
import {
  ArrowLeft,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  Award,
  HelpCircle,
  Building,
  Mail,
  Send,
  Activity,
} from "lucide-react";
import { PulseTimelineView } from "@/components/pulsewatch/PulseTimelineView";
import { PulseWatchSummary, BehaviorEvent } from "@/types/pulsewatch";

export default function StudentAcademicsPage() {
  const [activeTab, setActiveTab] = useState<string>("courses");
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [attendanceSummary, setAttendanceSummary] = useState<AttendanceSummary | null>(null);
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [results, setResults] = useState<AssessmentResult[]>([]);
  const [pulseSummary, setPulseSummary] = useState<PulseWatchSummary | null>(null);
  const [pulseEvents, setPulseEvents] = useState<BehaviorEvent[]>([]);
  const [pulseLoading, setPulseLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sync tab from URL query if provided (e.g. ?tab=pulse)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get("tab");
      if (tab && ["courses", "attendance", "assignments", "assessments", "pulse", "support"].includes(tab)) {
        setActiveTab(tab);
      }
    }
  }, []);

  // Assignment Submission State
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [submissionContent, setSubmissionContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAcademicData() {
      try {
        setLoading(true);
        setPulseLoading(true);
        setError(null);

        const [enrList, attSummary, attRecords, asgList, prof] = await Promise.all([
          api.getEnrollments().catch(() => []),
          api.getAttendanceSummary().catch(() => null),
          api.getAttendanceRecords().catch(() => []),
          api.getAssignments().catch(() => []),
          api.getMyStudentProfile().catch(() => null),
        ]);

        setEnrollments(enrList);
        setAttendanceSummary(attSummary);
        setAttendanceRecords(attRecords);
        setAssignments(asgList);

        // Fetch PulseWatch summary & timeline if student profile exists
        if (prof?.id) {
          try {
            const [pSummary, pEvents] = await Promise.all([
              api.getPulseWatchSummary(prof.id, 14).catch(() => null),
              api.getPulseWatchTimeline(prof.id).catch(() => []),
            ]);
            setPulseSummary(pSummary);
            setPulseEvents(pEvents);
          } catch {
            // PulseWatch establishes as data accumulates
          } finally {
            setPulseLoading(false);
          }
        } else {
          setPulseLoading(false);
        }

        // Fetch results for any assessments
        try {
          const assessments = await api.getAssessments();
          if (assessments.length > 0) {
            const resPromises = assessments.map((a) => api.getAssessmentResults(a.id));
            const allResults = await Promise.all(resPromises);
            setResults(allResults.flat());
          }
        } catch {
          // If no assessments yet, proceed
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load academic records");
        }
      } finally {
        setLoading(false);
      }
    }
    loadAcademicData();
  }, []);

  const handleSubmitAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignment) return;
    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      await api.submitAssignment(selectedAssignment.id, {
        submission_content: submissionContent,
      });
      setSubmitSuccess("Assignment submitted successfully!");
      setSubmissionContent("");
      setTimeout(() => {
        setSelectedAssignment(null);
        setSubmitSuccess(null);
      }, 1500);
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.message);
      } else {
        setSubmitError("Failed to submit assignment");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const tabs = [
    { id: "courses", label: "Enrolled Courses", count: enrollments.length, icon: BookOpen },
    { id: "attendance", label: "Attendance Record", count: attendanceRecords.length, icon: Calendar },
    { id: "assignments", label: "Coursework Assignments", count: assignments.length, icon: FileText },
    { id: "assessments", label: "Assessment Results", count: results.length, icon: Award },
    { id: "pulse", label: "Academic Pulse", count: pulseEvents.length, icon: Activity },
    { id: "support", label: "Academic Support", icon: HelpCircle },
  ];

  return (
    <ProtectedRoute requiredRoles={["STUDENT"]}>
      <div className="space-y-6" data-testid="student-academics-page">
        {/* Header with back link */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/student"
              className="p-2 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] transition"
              aria-label="Back to student dashboard"
            >
              <ArrowLeft className="h-4 w-4 text-zinc-400" />
            </Link>
            <div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                Academic Dashboard &amp; Performance
              </h1>
              <p className="text-xs sm:text-sm text-zinc-400">
                Enrolled courses, derived session attendance, coursework submissions, and verified marks.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="primary">ACADEMIC FOUNDATION</Badge>
          </div>
        </div>

        {/* Top Summary Metrics Row (Always Visible for E2E Tests) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase text-zinc-400">Courses Enrolled</CardTitle>
              <BookOpen className="h-4 w-4 text-[#FF9A3D]" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-white" data-testid="enrolled-courses-count">
                {enrollments.length}
              </div>
              <p className="text-xs text-zinc-400">Active semester registrations</p>
            </CardContent>
          </Card>

          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase text-zinc-400">Overall Attendance</CardTitle>
              <Calendar className="h-4 w-4 text-emerald-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-emerald-400" data-testid="attendance-rate">
                {attendanceSummary ? `${attendanceSummary.attendance_percentage}%` : "100%"}
              </div>
              <p className="text-xs text-zinc-400">
                {attendanceSummary?.present_count || 0} present, {attendanceSummary?.late_count || 0} late, {attendanceSummary?.absent_count || 0} absent
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase text-zinc-400">Assignments</CardTitle>
              <FileText className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-white">
                {assignments.length}
              </div>
              <p className="text-xs text-zinc-400">Coursework requirements</p>
            </CardContent>
          </Card>

          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase text-zinc-400">Evaluations</CardTitle>
              <Award className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono text-white">
                {results.length}
              </div>
              <p className="text-xs text-zinc-400">Evaluated test results</p>
            </CardContent>
          </Card>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Tab Navigation */}
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {/* Tab 1: Enrolled Courses */}
        {activeTab === "courses" && (
          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-base font-display text-white">
                <BookOpen className="h-5 w-5 text-[#FF9A3D]" />
                <span>Enrolled Course Offerings</span>
              </CardTitle>
              <CardDescription className="text-xs text-zinc-400">
                Official courses registered for current term with credit allocation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {enrollments.length === 0 ? (
                <EmptyState
                  icon={BookOpen}
                  title="No Course Registrations"
                  description="You are not enrolled in any courses for the current academic term."
                />
              ) : (
                <div className="space-y-3" data-testid="courses-list">
                  {enrollments.map((enr) => (
                    <div
                      key={enr.id}
                      className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 rounded-xl border border-white/[0.08] bg-[#111722]/60 hover-lift gap-3 transition"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-xs text-[#FF9A3D]">
                            {enr.course_code}
                          </span>
                          <Badge variant="neutral" className="text-[10px]">
                            {enr.course_credits || 4} Credits
                          </Badge>
                          <Badge variant={enr.status === "ENROLLED" ? "success" : "neutral"} className="text-[10px]">
                            {enr.status}
                          </Badge>
                        </div>
                        <p className="text-sm font-semibold text-white">
                          {enr.course_title}
                        </p>
                        <p className="text-xs text-zinc-400">
                          Term: {enr.term_name || "Fall 2026"} &bull; Enrolled on: {enr.enrollment_date}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs"
                          onClick={() => setActiveTab("attendance")}
                        >
                          View Attendance
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab 2: Attendance Tracking */}
        {activeTab === "attendance" && (
          <div className="space-y-6">
            <Card className="border-white/[0.08] bg-[#0D1117]">
              <CardHeader>
                <CardTitle className="text-base font-display text-white flex items-center space-x-2">
                  <Calendar className="h-5 w-5 text-emerald-400" />
                  <span>Derived Attendance Standing</span>
                </CardTitle>
                <CardDescription className="text-xs text-zinc-400">
                  Calculated dynamically on demand from raw session records.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-zinc-300">
                    Cumulative Attendance Rate
                  </span>
                  <span className="font-bold font-mono text-emerald-400">
                    {attendanceSummary?.attendance_percentage || 100}%
                  </span>
                </div>
                <div className="w-full bg-white/[0.08] rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2.5 rounded-full transition-all"
                    style={{ width: `${attendanceSummary?.attendance_percentage || 100}%` }}
                  />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 rounded-lg bg-[#111722] border border-white/[0.06] text-center">
                    <p className="text-[10px] uppercase font-semibold text-zinc-400">Total Sessions</p>
                    <p className="text-lg font-bold font-mono text-white mt-0.5">
                      {attendanceSummary?.total_sessions || 0}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[#111722] border border-white/[0.06] text-center">
                    <p className="text-[10px] uppercase font-semibold text-emerald-400">Present</p>
                    <p className="text-lg font-bold font-mono text-emerald-400 mt-0.5">
                      {attendanceSummary?.present_count || 0}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[#111722] border border-white/[0.06] text-center">
                    <p className="text-[10px] uppercase font-semibold text-[#FFB020]">Late</p>
                    <p className="text-lg font-bold font-mono text-[#FFB020] mt-0.5">
                      {attendanceSummary?.late_count || 0}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[#111722] border border-white/[0.06] text-center">
                    <p className="text-[10px] uppercase font-semibold text-rose-400">Absent</p>
                    <p className="text-lg font-bold font-mono text-rose-400 mt-0.5">
                      {attendanceSummary?.absent_count || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-white/[0.08] bg-[#0D1117]">
              <CardHeader>
                <CardTitle className="text-base font-display text-white">Granular Session Logs</CardTitle>
                <CardDescription className="text-xs text-zinc-400">
                  Event log with date, slot, and source verification.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {attendanceRecords.length === 0 ? (
                  <EmptyState
                    icon={Calendar}
                    title="No Session Records"
                    description="No classroom attendance has been entered for your profile yet."
                  />
                ) : (
                  <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1" data-testid="attendance-records-list">
                    {attendanceRecords.map((att) => (
                      <div
                        key={att.id}
                        className="flex items-center justify-between p-3 rounded-xl border border-white/[0.08] bg-[#111722]/50 text-xs hover:bg-[#111722] transition"
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono font-bold text-white">
                              {att.session_date}
                            </span>
                            <span className="text-zinc-400 font-mono">({att.session_slot})</span>
                            <Badge variant="neutral" className="text-[10px]">
                              {att.course_code || "CS101"}
                            </Badge>
                          </div>
                          {att.remarks && (
                            <p className="text-[11px] text-zinc-400 italic">“{att.remarks}”</p>
                          )}
                        </div>
                        <Badge
                          variant={
                            att.status === "PRESENT"
                              ? "success"
                              : att.status === "LATE"
                              ? "warning"
                              : "danger"
                          }
                        >
                          {att.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 3: Assignments & Submissions */}
        {activeTab === "assignments" && (
          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader>
              <CardTitle className="text-base font-display text-white flex items-center space-x-2">
                <FileText className="h-5 w-5 text-blue-400" />
                <span>Coursework Assignments Desk</span>
              </CardTitle>
              <CardDescription className="text-xs text-zinc-400">
                Submit course assignments and inspect evaluation remarks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {assignments.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No Assignments Released"
                  description="Your instructors have not published any coursework assignments yet."
                />
              ) : (
                <div className="space-y-4">
                  {assignments.map((asg) => (
                    <div
                      key={asg.id}
                      className="p-4 rounded-xl border border-white/[0.08] bg-[#111722]/60 hover-lift flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 transition"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-bold text-blue-400">
                            {asg.course_code || "COURSE"}
                          </span>
                          <span className="text-sm font-semibold text-white">
                            {asg.title}
                          </span>
                        </div>
                        {asg.description && (
                          <p className="text-xs text-zinc-300 max-w-xl">
                            {asg.description}
                          </p>
                        )}
                        <p className="text-[11px] text-zinc-400">
                          Due Date: {new Date(asg.due_date).toLocaleDateString()} &bull; Max Marks: {asg.max_marks} &bull; Weightage: {asg.weightage_percentage}%
                        </p>
                      </div>
                      <Button
                        size="sm"
                        className="text-xs space-x-1.5"
                        onClick={() => {
                          setSelectedAssignment(asg);
                          setSubmitSuccess(null);
                          setSubmitError(null);
                        }}
                        data-testid={`submit-asg-${asg.id}`}
                      >
                        <Send className="h-3.5 w-3.5" />
                        <span>Submit Work</span>
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab 4: Assessments & Marks */}
        {activeTab === "assessments" && (
          <Card className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader>
              <CardTitle className="text-base font-display text-white flex items-center space-x-2">
                <Award className="h-5 w-5 text-purple-400" />
                <span>Formal Evaluation Results</span>
              </CardTitle>
              <CardDescription className="text-xs text-zinc-400">
                Marks officially recorded and verified by faculty instructors.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {results.length === 0 ? (
                <EmptyState
                  icon={Award}
                  title="No Evaluations Recorded"
                  description="No examination or quiz scores have been recorded for your profile."
                />
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4" data-testid="assessment-results-list">
                  {results.map((res) => (
                    <div
                      key={res.id}
                      className="p-4 rounded-xl border border-white/[0.08] bg-[#111722]/60 hover-lift space-y-2 transition"
                    >
                      <div className="flex items-center justify-between">
                        <Badge variant="neutral" className="text-[10px] font-mono">
                          {res.assessment_type || "TEST"}
                        </Badge>
                        {res.is_absent ? (
                          <Badge variant="danger">ABSENT</Badge>
                        ) : (
                          <Badge variant="success">GRADED</Badge>
                        )}
                      </div>
                      <p className="font-semibold text-sm text-white pt-1">
                        {res.assessment_title || "Midterm Assessment"}
                      </p>
                      <div className="flex items-baseline space-x-1 pt-1">
                        <span className="text-2xl font-bold font-mono text-white">
                          {res.is_absent ? "0" : res.marks_obtained}
                        </span>
                        <span className="text-xs text-zinc-400">/ {res.max_marks || 50}</span>
                      </div>
                      {res.remarks && (
                        <p className="text-xs text-zinc-400 italic pt-1">“{res.remarks}”</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab 5: Academic Pulse (PulseWatch Deterministic Monitoring) */}
        {activeTab === "pulse" && (
          <PulseTimelineView
            summary={pulseSummary}
            events={pulseEvents}
            loading={pulseLoading}
          />
        )}

        {/* Tab 6: Academic Support (Strictly Informational) */}
        {activeTab === "support" && (
          <div className="space-y-6">
            <Card className="border-white/[0.08] bg-[#0D1117]">
              <CardHeader>
                <div className="flex items-center space-x-2 text-[#FF9A3D]">
                  <HelpCircle className="h-5 w-5" />
                  <CardTitle className="text-base font-display text-white">Institutional Academic Support Directory</CardTitle>
                </div>
                <CardDescription className="text-xs text-zinc-400">
                  Official contact channels for academic advising, mentor consultations, and institutional records.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded-xl border border-white/[0.08] p-4 bg-[#111722]/60 hover-lift transition">
                    <div className="flex items-center space-x-2 font-semibold text-white">
                      <Building className="h-4 w-4 text-[#FF9A3D]" />
                      <span>Academic Advising &amp; Mentorship</span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-2">
                      Guidance on credit requirements, course selection, and academic progression.
                    </p>
                    <div className="mt-3 pt-3 border-t border-white/[0.06] space-y-1">
                      <p className="text-zinc-300">Location: Faculty Office Block B, Room 210</p>
                      <p className="font-mono text-[#FF9A3D]">advising-team@campuspulse.edu</p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/[0.08] p-4 bg-[#111722]/60 hover-lift transition">
                    <div className="flex items-center space-x-2 font-semibold text-white">
                      <Mail className="h-4 w-4 text-blue-400" />
                      <span>Office of the Registrar</span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-2">
                      Official transcripts, enrollment certificates, and registration queries.
                    </p>
                    <div className="mt-3 pt-3 border-t border-white/[0.06] space-y-1">
                      <p className="text-zinc-300">Location: Administrative Building, Window 3</p>
                      <p className="font-mono text-blue-400">registrar@campuspulse.edu</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#111722] border border-white/[0.08]">
                  <p className="font-semibold text-white text-xs">
                    Integrated CampusPulse Services Active
                  </p>
                  <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                    Interactive policy document exploration (PulseAssist), leave requests (PulseRecord), formal grievances, and individualized academic support action plans (PulseCase) are fully integrated into your student workspace.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Modal: Submit Assignment */}
        <Modal
          isOpen={!!selectedAssignment}
          onClose={() => setSelectedAssignment(null)}
          title={`Submit: ${selectedAssignment?.title || "Assignment"}`}
          description={`Course: ${selectedAssignment?.course_code || "CS101"} · Max Marks: ${selectedAssignment?.max_marks}`}
        >
          <form onSubmit={handleSubmitAssignment} className="space-y-4">
            {submitError && (
              <div className="p-3 rounded-lg bg-rose-950/40 text-rose-300 text-xs border border-rose-500/30">
                {submitError}
              </div>
            )}
            {submitSuccess && (
              <div className="p-3 rounded-lg bg-emerald-950/40 text-emerald-300 text-xs border border-emerald-500/30">
                {submitSuccess}
              </div>
            )}
            <div>
              <label htmlFor="submission-content" className="block text-xs font-semibold text-zinc-300 mb-1">
                Submission Text / Repository Link / Solution
              </label>
              <textarea
                id="submission-content"
                rows={4}
                required
                placeholder="Enter solution summary, repository link, or coursework response..."
                value={submissionContent}
                onChange={(e) => setSubmissionContent(e.target.value)}
                className="w-full p-3 rounded-lg border border-white/[0.08] bg-[#111722] text-white text-xs focus:ring-2 focus:ring-[#FF7A18] focus:outline-none"
                data-testid="assignment-submission-input"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setSelectedAssignment(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={submitting || !submissionContent.trim()}
                data-testid="confirm-submit-assignment-btn"
              >
                {submitting ? "Submitting..." : "Submit Assignment"}
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
