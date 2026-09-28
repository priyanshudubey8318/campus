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
  FacultyCourseAssignment,
  Enrollment,
  AttendanceRecord,
  Assignment,
  AssignmentSubmission,
  Assessment,
  AssessmentResult,
} from "@/types/academic";
import {
  ArrowLeft,
  BookOpen,
  Calendar,
  Layers,
  Users,
  AlertCircle,
  Search,
  Award,
  PlusCircle,
  FileCheck2,
  CheckCircle2,
  Check,
  UserCheck,
} from "lucide-react";

export default function FacultyCoursesPage() {
  const [assignments, setAssignments] = useState<FacultyCourseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  // Selected Course Workspace State
  const [selectedCourse, setSelectedCourse] = useState<FacultyCourseAssignment | null>(null);
  const [courseTab, setCourseTab] = useState("roster");
  const [roster, setRoster] = useState<Enrollment[]>([]);
  const [courseAssignments, setCourseAssignments] = useState<Assignment[]>([]);
  const [courseAssessments, setCourseAssessments] = useState<Assessment[]>([]);
  const [loadingWorkspace, setLoadingWorkspace] = useState(false);

  // Modals & Action Forms
  // 1. Attendance Modal
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);
  const [attStudentId, setAttStudentId] = useState("");
  const [attDate, setAttDate] = useState(new Date().toISOString().split("T")[0]);
  const [attSlot, setAttSlot] = useState("SLOT_09_00");
  const [attStatus, setAttStatus] = useState<"PRESENT" | "ABSENT" | "LATE" | "EXCUSED">("PRESENT");
  const [attRemarks, setAttRemarks] = useState("");
  const [submittingAtt, setSubmittingAtt] = useState(false);
  const [attFeedback, setAttFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // 2. Create Assignment Modal
  const [showCreateAssignmentModal, setShowCreateAssignmentModal] = useState(false);
  const [asgTitle, setAsgTitle] = useState("");
  const [asgDesc, setAsgDesc] = useState("");
  const [asgMaxMarks, setAsgMaxMarks] = useState(50);
  const [asgWeightage, setAsgWeightage] = useState(10);
  const [asgDueDate, setAsgDueDate] = useState(
    new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16)
  );
  const [submittingAsg, setSubmittingAsg] = useState(false);
  const [asgFeedback, setAsgFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // 3. Submissions & Grading Modal
  const [activeGradingAssignment, setActiveGradingAssignment] = useState<Assignment | null>(null);
  const [submissions, setSubmissions] = useState<AssignmentSubmission[]>([]);
  const [selectedSubmission, setSelectedSubmission] = useState<AssignmentSubmission | null>(null);
  const [gradeMarks, setGradeMarks] = useState(0);
  const [gradeFeedback, setGradeFeedback] = useState("");
  const [submittingGrade, setSubmittingGrade] = useState(false);

  useEffect(() => {
    async function loadAssignments() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getFacultyAssignments();
        setAssignments(data);
        if (data.length > 0) {
          setSelectedCourse(data[0]);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load faculty assignments");
        }
      } finally {
        setLoading(false);
      }
    }
    loadAssignments();
  }, []);

  // Load course details when a course is selected
  useEffect(() => {
    if (!selectedCourse) return;
    const currentCourse = selectedCourse;

    async function loadCourseWorkspace() {
      setLoadingWorkspace(true);
      try {
        const [rosterData, asgData, assessData] = await Promise.all([
          api.getEnrollments({ course_id: currentCourse.course_id }).catch(() => []),
          api.getAssignments({ course_id: currentCourse.course_id }).catch(() => []),
          api.getAssessments({ course_id: currentCourse.course_id }).catch(() => []),
        ]);
        setRoster(rosterData);
        setCourseAssignments(asgData);
        setCourseAssessments(assessData);
        if (rosterData.length > 0) {
          setAttStudentId(rosterData[0].student_id);
        }
      } catch {
        // Continue gracefully
      } finally {
        setLoadingWorkspace(false);
      }
    }

    loadCourseWorkspace();
  }, [selectedCourse]);

  const handleRecordAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse || !attStudentId) return;
    setSubmittingAtt(true);
    setAttFeedback(null);

    try {
      await api.recordAttendance({
        student_id: attStudentId,
        course_id: selectedCourse.course_id,
        term_id: selectedCourse.term_id,
        session_date: attDate,
        session_slot: attSlot,
        status: attStatus,
        source: "MANUAL",
        remarks: attRemarks || undefined,
      });
      setAttFeedback({ type: "success", msg: "Attendance record saved successfully!" });
      setTimeout(() => {
        setShowAttendanceModal(false);
        setAttFeedback(null);
        setAttRemarks("");
      }, 1200);
    } catch (err: any) {
      setAttFeedback({ type: "error", msg: err?.message || "Failed to record attendance" });
    } finally {
      setSubmittingAtt(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse) return;
    setSubmittingAsg(true);
    setAsgFeedback(null);

    try {
      const created = await api.createAssignment({
        course_id: selectedCourse.course_id,
        term_id: selectedCourse.term_id,
        title: asgTitle,
        description: asgDesc || undefined,
        max_marks: asgMaxMarks,
        weightage_percentage: asgWeightage,
        release_date: new Date().toISOString(),
        due_date: new Date(asgDueDate).toISOString(),
        allow_late_submission: true,
      });
      setCourseAssignments((prev) => [created, ...prev]);
      setAsgFeedback({ type: "success", msg: "Assignment created successfully!" });
      setTimeout(() => {
        setShowCreateAssignmentModal(false);
        setAsgFeedback(null);
        setAsgTitle("");
        setAsgDesc("");
      }, 1200);
    } catch (err: any) {
      setAsgFeedback({ type: "error", msg: err?.message || "Failed to create assignment" });
    } finally {
      setSubmittingAsg(false);
    }
  };

  const openGradingDesk = async (asg: Assignment) => {
    setActiveGradingAssignment(asg);
    try {
      const subs = await api.getAssignmentSubmissions(asg.id);
      setSubmissions(subs);
    } catch {
      setSubmissions([]);
    }
  };

  const handleGradeSubmission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubmission) return;
    setSubmittingGrade(true);

    try {
      const updated = await api.gradeSubmission(selectedSubmission.id, {
        marks_obtained: gradeMarks,
        feedback: gradeFeedback,
      });
      setSubmissions((prev) =>
        prev.map((s) => (s.id === updated.id ? updated : s))
      );
      setSelectedSubmission(null);
      setGradeFeedback("");
    } catch (err: any) {
      alert(err?.message || "Grading failed");
    } finally {
      setSubmittingGrade(false);
    }
  };

  const filteredAssignments = assignments.filter((a) => {
    const code = a.course_code?.toLowerCase() || "";
    const title = a.course_title?.toLowerCase() || "";
    const term = a.term_name?.toLowerCase() || "";
    const s = searchTerm.toLowerCase();
    return code.includes(s) || title.includes(s) || term.includes(s);
  });

  return (
    <ProtectedRoute requiredRoles={["FACULTY"]}>
      <div className="space-y-6" data-testid="faculty-courses-page">
        {/* Header with back button */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/faculty"
              className="p-2 rounded-lg border border-white/10 hover:bg-white/5 transition text-surface-400 hover:text-white"
              aria-label="Back to faculty portal"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                Assigned Teaching Courses &amp; Workspace
              </h1>
              <p className="text-xs sm:text-sm text-surface-400">
                Course administration, authorized student rosters, attendance entry, and grading.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="primary">FACULTY PORTAL</Badge>
            <Badge variant="success">INSTRUCTION ROSTER</Badge>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-surface-400" />
          <input
            type="text"
            placeholder="Filter courses by code, title, or academic term..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-white/10 bg-[#0D1117] text-xs sm:text-sm text-white placeholder-surface-500 focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30 transition"
            data-testid="faculty-courses-search"
          />
        </div>

        {loading && (
          <Card>
            <CardContent className="py-12 text-center text-xs text-surface-400">
              Loading faculty assignments...
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="border-red-500/30 bg-red-500/10">
            <CardContent className="py-4 flex items-center space-x-3 text-red-400 text-xs">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{error}</span>
            </CardContent>
          </Card>
        )}

        {/* Assigned Courses Grid (Always Present for E2E Tests) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="faculty-assignments-grid">
          {filteredAssignments.map((assignment) => {
            const isSelected = selectedCourse?.id === assignment.id;
            return (
              <Card
                key={assignment.id}
                className={`transition-all cursor-pointer ${
                  isSelected
                    ? "border-[#FF7A18] ring-2 ring-[#FF7A18]/20 shadow-[0_0_25px_rgba(255,122,24,0.1)] bg-[#FF7A18]/[0.03]"
                    : "border-white/10 hover:border-white/20 bg-[#0D1117]"
                }`}
                onClick={() => setSelectedCourse(assignment)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#FF7A18]/10 text-[#FF9A3D] border border-[#FF7A18]/20">
                        {assignment.course_code || "COURSE"}
                      </span>
                      <CardTitle className="text-base font-bold mt-2 text-white font-display">
                        {assignment.course_title || "Course Assignment"}
                      </CardTitle>
                    </div>
                    <Badge
                      variant={assignment.role === "PRIMARY_INSTRUCTOR" ? "success" : "neutral"}
                    >
                      {assignment.role.replace("_", " ")}
                    </Badge>
                  </div>
                  <CardDescription className="text-xs text-surface-400">
                    Academic Term: {assignment.term_name || "Active Term"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="p-2.5 bg-[#111722] rounded-lg border border-white/10 flex items-center justify-between text-xs">
                    <span className="text-surface-400 font-medium">Assigned Section:</span>
                    <span className="font-semibold text-white">
                      {assignment.section_name || "All Sections (Course-wide)"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-surface-400 pt-1">
                    <span>Click to manage course workspace</span>
                    {isSelected && (
                      <span className="text-[#FF9A3D] font-semibold flex items-center space-x-1">
                        <Check className="h-3.5 w-3.5" />
                        <span>Active Workspace</span>
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Active Course Management Workspace */}
        {selectedCourse && (
          <div className="mt-8 pt-6 border-t border-white/10 space-y-6" data-testid="course-workspace">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold text-[#FF9A3D]">
                    {selectedCourse.course_code}
                  </span>
                  <Badge variant="primary">COURSE CONSOLE</Badge>
                </div>
                <h2 className="text-xl font-bold tracking-tight text-white font-display mt-1">
                  {selectedCourse.course_title} Workspace
                </h2>
                <p className="text-xs text-surface-400">
                  Authorized Scope: {selectedCourse.section_name || "All Sections"} &bull; {selectedCourse.term_name}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowAttendanceModal(true)}
                  className="text-xs space-x-1.5 border-white/10 hover:bg-white/5 text-surface-200"
                  data-testid="open-attendance-modal-btn"
                >
                  <Calendar className="h-3.5 w-3.5 text-[#FF9A3D]" />
                  <span>Log Attendance</span>
                </Button>
                <Button
                  size="sm"
                  onClick={() => setShowCreateAssignmentModal(true)}
                  className="text-xs space-x-1.5 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                  data-testid="open-create-assignment-btn"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  <span>New Assignment</span>
                </Button>
              </div>
            </div>

            {/* Workspace Tabs */}
            <Tabs
              tabs={[
                { id: "roster", label: "Enrolled Students", count: roster.length, icon: Users },
                { id: "assignments", label: "Coursework Desk", count: courseAssignments.length, icon: FileCheck2 },
                { id: "assessments", label: "Assessments & Marks", count: courseAssessments.length, icon: Award },
              ]}
              activeTab={courseTab}
              onChange={setCourseTab}
            />

            {/* Tab 1: Authorized Student Roster */}
            {courseTab === "roster" && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center space-x-2 text-white font-display">
                    <Users className="h-5 w-5 text-[#FF9A3D]" />
                    <span>Authorized Student Roster</span>
                  </CardTitle>
                  <CardDescription className="text-xs text-surface-400">
                    Students formally enrolled in this course offering within instructor authorization scope.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  {roster.length === 0 ? (
                    <div className="p-8">
                      <EmptyState
                        icon={Users}
                        title="No Enrolled Students"
                        description="No students are enrolled in this course section."
                      />
                    </div>
                  ) : (
                    <table className="w-full text-left text-xs border-collapse" data-testid="course-roster-table">
                      <thead>
                        <tr className="border-y border-white/10 bg-[#111722] text-surface-400 font-semibold uppercase text-[11px] font-mono tracking-wider">
                          <th className="py-3 px-4">Student ID</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4">Enrolled On</th>
                          <th className="py-3 px-4 text-right">Quick Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {roster.map((stu) => (
                          <tr key={stu.id} className="hover:bg-white/[0.02] transition-colors">
                            <td className="py-3 px-4 font-mono font-semibold text-white">
                              {stu.student_id}
                            </td>
                            <td className="py-3 px-4">
                              <Badge variant={stu.status === "ENROLLED" ? "success" : "neutral"}>
                                {stu.status}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-surface-400">
                              {stu.enrollment_date}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-xs hover:bg-white/5 text-surface-300 hover:text-white"
                                onClick={() => {
                                  setAttStudentId(stu.student_id);
                                  setShowAttendanceModal(true);
                                }}
                              >
                                Log Attendance
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Tab 2: Assignments Desk */}
            {courseTab === "assignments" && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <div>
                    <CardTitle className="text-base flex items-center space-x-2 text-white font-display">
                      <FileCheck2 className="h-5 w-5 text-[#FF9A3D]" />
                      <span>Assignments &amp; Submissions Desk</span>
                    </CardTitle>
                    <CardDescription className="text-xs text-surface-400">
                      Manage course assignments, inspect student solutions, and enter marks.
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => setShowCreateAssignmentModal(true)}
                    className="text-xs space-x-1 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                  >
                    <PlusCircle className="h-3.5 w-3.5" />
                    <span>Create Assignment</span>
                  </Button>
                </CardHeader>
                <CardContent>
                  {courseAssignments.length === 0 ? (
                    <EmptyState
                      icon={FileCheck2}
                      title="No Assignments Published"
                      description="Click Create Assignment to release coursework to students."
                    />
                  ) : (
                    <div className="space-y-4">
                      {courseAssignments.map((asg) => (
                        <div
                          key={asg.id}
                          className="p-4 rounded-xl border border-white/10 bg-[#111722]/60 hover:border-white/20 transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                        >
                          <div className="space-y-1">
                            <span className="font-semibold text-sm text-white">
                              {asg.title}
                            </span>
                            {asg.description && (
                              <p className="text-xs text-surface-400 max-w-xl">{asg.description}</p>
                            )}
                            <p className="text-[11px] text-surface-400">
                              Due: {new Date(asg.due_date).toLocaleDateString()} &bull; Max Marks: {asg.max_marks} &bull; Weightage: {asg.weightage_percentage}%
                            </p>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs space-x-1 border-white/10 hover:bg-white/5 text-surface-200"
                            onClick={() => openGradingDesk(asg)}
                            data-testid={`grade-asg-${asg.id}`}
                          >
                            <span>Submissions Desk</span>
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Tab 3: Assessments & Marks */}
            {courseTab === "assessments" && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center space-x-2 text-white font-display">
                    <Award className="h-5 w-5 text-[#FF9A3D]" />
                    <span>Course Assessments &amp; Examinations</span>
                  </CardTitle>
                  <CardDescription className="text-xs text-surface-400">
                    Institutional exams, midterms, and formal evaluated marks.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {courseAssessments.length === 0 ? (
                    <EmptyState
                      icon={Award}
                      title="No Assessments Created"
                      description="No formal examinations or tests are currently scheduled for this course."
                    />
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {courseAssessments.map((assess) => (
                        <div
                          key={assess.id}
                          className="p-4 rounded-xl border border-white/10 bg-[#111722]/60 space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <Badge variant="neutral">{assess.assessment_type}</Badge>
                            <span className="text-xs text-surface-400">{assess.assessment_date}</span>
                          </div>
                          <p className="text-sm font-semibold text-white">
                            {assess.title}
                          </p>
                          <p className="text-xs text-surface-400">
                            Max Marks: {assess.max_marks} &bull; Weightage: {assess.weightage_percentage}%
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Modal: Record Attendance */}
        <Modal
          isOpen={showAttendanceModal}
          onClose={() => setShowAttendanceModal(false)}
          title="Record Classroom Attendance"
          description={`Course: ${selectedCourse?.course_code || "Course"} · Section: ${selectedCourse?.section_name || "All"}`}
        >
          <form onSubmit={handleRecordAttendance} className="space-y-4">
            {attFeedback && (
              <div
                className={`p-3 rounded-lg text-xs border ${
                  attFeedback.type === "success"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                }`}
              >
                {attFeedback.msg}
              </div>
            )}

            <div>
              <label htmlFor="student-id-select" className="block text-xs font-semibold text-surface-300 mb-1">
                Student ID
              </label>
              {roster.length > 0 ? (
                <select
                  id="student-id-select"
                  value={attStudentId}
                  onChange={(e) => setAttStudentId(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                  data-testid="attendance-student-select"
                >
                  {roster.map((stu) => (
                    <option key={stu.student_id} value={stu.student_id} className="bg-[#111722] text-white">
                      {stu.student_id} (Enrolled: {stu.enrollment_date})
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  id="student-id-select"
                  type="text"
                  required
                  placeholder="Enter Student Profile ID"
                  value={attStudentId}
                  onChange={(e) => setAttStudentId(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-white/10 bg-[#111722] text-white placeholder-surface-500 text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                />
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="session-date-input" className="block text-xs font-semibold text-surface-300 mb-1">
                  Session Date
                </label>
                <input
                  id="session-date-input"
                  type="date"
                  required
                  value={attDate}
                  onChange={(e) => setAttDate(e.target.value)}
                  className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                />
              </div>
              <div>
                <label htmlFor="session-slot-input" className="block text-xs font-semibold text-surface-300 mb-1">
                  Session Slot
                </label>
                <input
                  id="session-slot-input"
                  type="text"
                  required
                  value={attSlot}
                  onChange={(e) => setAttSlot(e.target.value)}
                  className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                />
              </div>
            </div>

            <div>
              <label htmlFor="attendance-status-select" className="block text-xs font-semibold text-surface-300 mb-1">
                Attendance Status
              </label>
              <select
                id="attendance-status-select"
                value={attStatus}
                onChange={(e) => setAttStatus(e.target.value as any)}
                className="w-full p-2.5 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                data-testid="attendance-status-select"
              >
                <option value="PRESENT" className="bg-[#111722] text-white">PRESENT</option>
                <option value="ABSENT" className="bg-[#111722] text-white">ABSENT</option>
                <option value="LATE" className="bg-[#111722] text-white">LATE</option>
                <option value="EXCUSED" className="bg-[#111722] text-white">EXCUSED</option>
              </select>
            </div>

            <div>
              <label htmlFor="attendance-remarks-input" className="block text-xs font-semibold text-surface-300 mb-1">
                Remarks (Optional)
              </label>
              <input
                id="attendance-remarks-input"
                type="text"
                placeholder="Lecture notes or reason"
                value={attRemarks}
                onChange={(e) => setAttRemarks(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-white/10 bg-[#111722] text-white placeholder-surface-500 text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowAttendanceModal(false)}
                className="border-white/10 hover:bg-white/5 text-surface-300 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={submittingAtt}
                className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                data-testid="confirm-record-attendance-btn"
              >
                {submittingAtt ? "Recording..." : "Save Attendance"}
              </Button>
            </div>
          </form>
        </Modal>

        {/* Modal: Create Assignment */}
        <Modal
          isOpen={showCreateAssignmentModal}
          onClose={() => setShowCreateAssignmentModal(false)}
          title="Create New Assignment"
          description={`For Course: ${selectedCourse?.course_code || "Course"}`}
        >
          <form onSubmit={handleCreateAssignment} className="space-y-4">
            {asgFeedback && (
              <div
                className={`p-3 rounded-lg text-xs border ${
                  asgFeedback.type === "success"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                }`}
              >
                {asgFeedback.msg}
              </div>
            )}

            <div>
              <label htmlFor="assignment-title-input" className="block text-xs font-semibold text-surface-300 mb-1">
                Assignment Title
              </label>
              <input
                id="assignment-title-input"
                type="text"
                required
                placeholder="e.g. Lab Exercise 1: Relational Schemas"
                value={asgTitle}
                onChange={(e) => setAsgTitle(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-white/10 bg-[#111722] text-white placeholder-surface-500 text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                data-testid="assignment-title-input"
              />
            </div>

            <div>
              <label htmlFor="assignment-desc-input" className="block text-xs font-semibold text-surface-300 mb-1">
                Description / Problem Statement
              </label>
              <textarea
                id="assignment-desc-input"
                rows={3}
                placeholder="Brief requirements and grading rubric..."
                value={asgDesc}
                onChange={(e) => setAsgDesc(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-white/10 bg-[#111722] text-white placeholder-surface-500 text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label htmlFor="assignment-maxmarks-input" className="block text-xs font-semibold text-surface-300 mb-1">
                  Max Marks
                </label>
                <input
                  id="assignment-maxmarks-input"
                  type="number"
                  min="1"
                  required
                  value={asgMaxMarks}
                  onChange={(e) => setAsgMaxMarks(Number(e.target.value))}
                  className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                />
              </div>
              <div>
                <label htmlFor="assignment-weightage-input" className="block text-xs font-semibold text-surface-300 mb-1">
                  Weightage (%)
                </label>
                <input
                  id="assignment-weightage-input"
                  type="number"
                  min="0"
                  max="100"
                  required
                  value={asgWeightage}
                  onChange={(e) => setAsgWeightage(Number(e.target.value))}
                  className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                />
              </div>
              <div>
                <label htmlFor="assignment-duedate-input" className="block text-xs font-semibold text-surface-300 mb-1">
                  Due Date
                </label>
                <input
                  id="assignment-duedate-input"
                  type="datetime-local"
                  required
                  value={asgDueDate}
                  onChange={(e) => setAsgDueDate(e.target.value)}
                  className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowCreateAssignmentModal(false)}
                className="border-white/10 hover:bg-white/5 text-surface-300 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={submittingAsg || !asgTitle.trim()}
                className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                data-testid="confirm-create-assignment-btn"
              >
                {submittingAsg ? "Creating..." : "Publish Assignment"}
              </Button>
            </div>
          </form>
        </Modal>

        {/* Modal: Submissions & Grading Desk */}
        <Modal
          isOpen={!!activeGradingAssignment}
          onClose={() => {
            setActiveGradingAssignment(null);
            setSelectedSubmission(null);
          }}
          title={`Submissions: ${activeGradingAssignment?.title || "Assignment"}`}
          description={`Max Marks: ${activeGradingAssignment?.max_marks} · Weightage: ${activeGradingAssignment?.weightage_percentage}%`}
          maxWidth="xl"
        >
          <div className="space-y-4">
            {submissions.length === 0 ? (
              <EmptyState
                icon={FileCheck2}
                title="No Submissions Received"
                description="Students have not uploaded submissions for this assignment yet."
              />
            ) : (
              <div className="divide-y divide-white/5 max-h-[350px] overflow-y-auto">
                {submissions.map((sub) => (
                  <div key={sub.id} className="py-3 flex items-center justify-between gap-4 text-xs">
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-white">
                          {sub.student_id}
                        </span>
                        <Badge variant={sub.status === "EVALUATED" ? "success" : "neutral"}>
                          {sub.status}
                        </Badge>
                      </div>
                      {sub.submission_content && (
                        <p className="text-surface-300 truncate max-w-sm">
                          “{sub.submission_content}”
                        </p>
                      )}
                      <p className="text-[11px] text-surface-400">
                        Submitted: {new Date(sub.submitted_at).toLocaleString()}
                        {sub.marks_obtained !== null && sub.marks_obtained !== undefined && (
                          <span className="ml-2 font-semibold text-[#FF9A3D]">
                            Marks: {sub.marks_obtained} / {sub.max_marks || activeGradingAssignment?.max_marks}
                          </span>
                        )}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs border-white/10 hover:bg-white/5 text-surface-200"
                      onClick={() => {
                        setSelectedSubmission(sub);
                        setGradeMarks(sub.marks_obtained || 0);
                        setGradeFeedback(sub.feedback || "");
                      }}
                    >
                      {sub.status === "EVALUATED" ? "Edit Grade" : "Enter Grade"}
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Grading Inline Form */}
            {selectedSubmission && (
              <form onSubmit={handleGradeSubmission} className="pt-4 border-t border-white/10 space-y-3">
                <h4 className="text-xs font-bold text-white font-display">
                  Grade Submission for Student {selectedSubmission.student_id}
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="grading-marks-input" className="block text-[11px] font-semibold text-surface-300 mb-1">
                      Marks Obtained (Max: {activeGradingAssignment?.max_marks})
                    </label>
                    <input
                      id="grading-marks-input"
                      type="number"
                      min="0"
                      max={activeGradingAssignment?.max_marks || 100}
                      step="0.5"
                      required
                      value={gradeMarks}
                      onChange={(e) => setGradeMarks(Number(e.target.value))}
                      className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                      data-testid="grading-marks-input"
                    />
                  </div>
                  <div>
                    <label htmlFor="grading-feedback-input" className="block text-[11px] font-semibold text-surface-300 mb-1">
                      Instructor Feedback
                    </label>
                    <input
                      id="grading-feedback-input"
                      type="text"
                      placeholder="Feedback comments..."
                      value={gradeFeedback}
                      onChange={(e) => setGradeFeedback(e.target.value)}
                      className="w-full p-2 rounded-lg border border-white/10 bg-[#111722] text-white placeholder-surface-500 text-xs focus:ring-1 focus:ring-[#FF7A18]/50 focus:border-[#FF7A18]/50"
                      data-testid="grading-feedback-input"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedSubmission(null)}
                    className="border-white/10 hover:bg-white/5 text-surface-300 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={submittingGrade}
                    className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                    data-testid="confirm-grade-submission-btn"
                  >
                    {submittingGrade ? "Saving..." : "Save Grade"}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
