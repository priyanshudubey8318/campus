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
import { FacultyProfile, FacultyCourseAssignment } from "@/types/academic";
import {
  BookOpenCheck,
  BookOpen,
  CalendarCheck2,
  Users,
  Award,
  ArrowRight,
  Briefcase,
  AlertCircle,
  PlusCircle,
  Clock,
  Building,
} from "lucide-react";

export default function FacultyDashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<FacultyProfile | null>(null);
  const [assignments, setAssignments] = useState<FacultyCourseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadFacultyDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [profData, asgData] = await Promise.all([
          api.getMyFacultyProfile().catch(() => null),
          api.getFacultyAssignments().catch(() => []),
        ]);

        setProfile(profData);
        setAssignments(asgData);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load faculty records");
        }
      } finally {
        setLoading(false);
      }
    }
    loadFacultyDashboard();
  }, []);

  const distinctCourses = new Set(assignments.map((a) => a.course_id)).size;
  const primaryRoles = assignments.filter((a) => a.role === "PRIMARY_INSTRUCTOR").length;

  return (
    <ProtectedRoute requiredRoles={["FACULTY"]}>
      <div className="space-y-8" data-testid="faculty-portal">
        {/* Faculty Profile & Appointment Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0D1117] p-6 md:p-8 shadow-xl">
          <RingBackground variant="hero" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="primary">FACULTY CONSOLE</Badge>
                <Badge variant={profile?.is_active ? "success" : "neutral"}>
                  {profile?.is_active ? "ACTIVE APPOINTMENT" : "INACTIVE"}
                </Badge>
                {profile?.employee_id && (
                  <span className="text-xs font-mono text-zinc-400 font-semibold" data-testid="faculty-emp-badge">
                    {profile.employee_id}
                  </span>
                )}
              </div>
              <h1 className="font-display text-2xl md:text-3xl font-bold tracking-tight text-white">
                Welcome back, {user?.full_name || "Faculty Member"}
              </h1>
              <p className="text-xs md:text-sm text-zinc-400 max-w-2xl">
                {profile?.designation || "Associate Professor"} &bull;{" "}
                {profile?.department_name || "Computer Science & Engineering"} &bull;{" "}
                Specialization: {profile?.specialization || "Distributed Systems"}
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Link href="/faculty/profile">
                <Button variant="outline" size="sm" className="text-xs" data-testid="faculty-profile-btn">
                  <span>View Appointment</span>
                </Button>
              </Link>
              <Link href="/faculty/courses">
                <Button size="sm" className="text-xs space-x-1.5" data-testid="faculty-workspace-btn">
                  <span>Course Management</span>
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

        {/* 4 KPIs */}
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
              title="Assigned Offerings"
              value={assignments.length}
              subtitle="Current semester teaching load"
              icon={BookOpenCheck}
              iconColor="text-[#FF9A3D]"
              testId="kpi-faculty-offerings"
            />
            <StatsCard
              title="Distinct Courses"
              value={distinctCourses}
              subtitle="Subject curriculum coverage"
              icon={BookOpen}
              iconColor="text-blue-400"
              testId="kpi-faculty-subjects"
            />
            <StatsCard
              title="Primary Roles"
              value={primaryRoles}
              subtitle="Head course coordinator"
              icon={Award}
              iconColor="text-purple-400"
              testId="kpi-faculty-primary"
            />
            <StatsCard
              title="Authorization Scope"
              value="Enforced"
              subtitle="Strict course & section access"
              icon={Users}
              iconColor="text-emerald-400"
              badge={{ text: "Least-Privilege RBAC", variant: "success" }}
              testId="kpi-faculty-rbac"
            />
          </div>
        )}

        {/* Assigned Courses Roster Preview */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-lg font-bold tracking-tight text-white">
                Assigned Teaching Load &amp; Offerings
              </h2>
              <p className="text-xs text-zinc-400">
                You have authorized instruction, attendance logging, and grading scopes for these courses.
              </p>
            </div>
            <Link href="/faculty/courses">
              <Button size="sm" variant="outline" className="text-xs space-x-1">
                <span>Manage All Courses</span>
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <p className="text-xs text-zinc-400 py-6 text-center">Loading assigned teaching courses...</p>
          ) : assignments.length === 0 ? (
            <EmptyState
              icon={BookOpenCheck}
              title="No Teaching Assignments Found"
              description="You currently have no course offerings assigned by the academic dean."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="faculty-courses-summary">
              {assignments.map((asg) => (
                <Card key={asg.id} className="border-white/[0.08] bg-[#0D1117] hover-lift transition">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <span className="font-mono text-xs font-bold text-[#FF9A3D]">
                          {asg.course_code || "COURSE"}
                        </span>
                        <CardTitle className="text-base font-display font-bold text-white">
                          {asg.course_title || "Course Offering"}
                        </CardTitle>
                      </div>
                      <Badge variant={asg.role === "PRIMARY_INSTRUCTOR" ? "success" : "neutral"}>
                        {asg.role.replace("_", " ")}
                      </Badge>
                    </div>
                    <CardDescription className="text-xs text-zinc-400">
                      Term: {asg.term_name || "Fall 2026"} &bull; Section: {asg.section_name || "All Sections"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0 space-y-3">
                    <div className="p-3 rounded-xl bg-[#111722] text-xs border border-white/[0.06] flex items-center justify-between">
                      <span className="text-zinc-400">Authorized Scopes:</span>
                      <span className="font-semibold text-white">
                        Attendance, Assignments, Marks
                      </span>
                    </div>
                    <div className="flex justify-end pt-1">
                      <Link href="/faculty/courses">
                        <Button size="sm" className="text-xs space-x-1.5">
                          <span>Open Course Workspace</span>
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
