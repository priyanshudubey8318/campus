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
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import { Course, Enrollment, Department } from "@/types/academic";
import { HealthResponse } from "@/types/health";
import {
  ShieldCheck,
  Building2,
  BookOpen,
  Users,
  Layers,
  ArrowRight,
  Activity,
  AlertCircle,
  Database,
  Lock,
} from "lucide-react";

export default function AdminPortalPage() {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAdminData() {
      try {
        setLoading(true);
        setError(null);

        const [courseList, enrList, deptList, healthData] = await Promise.all([
          api.getCourses().catch(() => []),
          api.getEnrollments().catch(() => []),
          api.getDepartments().catch(() => []),
          api.getHealth().catch(() => null),
        ]);

        setCourses(courseList);
        setEnrollments(enrList);
        setDepartments(deptList);
        setHealth(healthData);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load institutional administration metrics");
        }
      } finally {
        setLoading(false);
      }
    }

    loadAdminData();
  }, []);

  const activeEnrollments = enrollments.filter((e) => e.status === "ENROLLED").length;

  return (
    <ProtectedRoute requiredRoles={["ADMIN"]}>
      <div className="space-y-8" data-testid="admin-portal">
        {/* Admin Header Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 md:p-8 shadow-sm">
          <RingBackground variant="hero" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Badge variant="primary">ADMINISTRATION</Badge>
                <Badge variant="success">INSTITUTIONAL GOVERNANCE</Badge>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white font-display">
                Institutional Academic Governance
              </h1>
              <p className="text-xs md:text-sm text-surface-400 max-w-2xl">
                Master course catalog, department structure, and student enrollment registers across campus departments.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Link href="/system-status">
                <Button variant="outline" size="sm" className="text-xs space-x-1.5 border-white/10 hover:bg-white/5 text-surface-200" data-testid="admin-system-status-btn">
                  <Activity className="h-3.5 w-3.5 text-[#FF9A3D]" />
                  <span>Architecture Status</span>
                </Button>
              </Link>
              <Link href="/admin/academic">
                <Button size="sm" className="text-xs space-x-1.5 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0" data-testid="admin-academic-btn">
                  <span>Academic Catalog</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-400 flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
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
              title="Courses in Catalog"
              value={courses.length}
              subtitle="Accredited degree courses"
              icon={BookOpen}
              iconColor="text-[#FF9A3D]"
              testId="kpi-admin-courses"
            />
            <StatsCard
              title="Active Enrollments"
              value={activeEnrollments}
              subtitle={`${enrollments.length} total registrations`}
              icon={Users}
              iconColor="text-[#FF7A18]"
              testId="kpi-admin-enrollments"
            />
            <StatsCard
              title="Academic Departments"
              value={departments.length}
              subtitle="Faculty divisions"
              icon={Building2}
              iconColor="text-blue-400"
              testId="kpi-admin-departments"
            />
            <StatsCard
              title="Database Status"
              value={health?.database?.connected ? "Operational" : "Connecting"}
              subtitle={health ? `${health.database.dialect} dialect` : "Health check active"}
              icon={Database}
              iconColor="text-purple-400"
              badge={{
                text: health?.status === "healthy" ? "Healthy Engine" : "Connecting",
                variant: health?.status === "healthy" ? "success" : "neutral",
              }}
              testId="kpi-admin-system-health"
            />
          </div>
        )}

        {/* Governance Workstation Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Academic Catalog Management */}
          <Card className="flex flex-col justify-between hover:shadow-md transition">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="rounded-xl bg-[#FF7A18]/10 p-2.5 text-[#FF9A3D] border border-[#FF7A18]/20">
                  <BookOpen className="h-6 w-6" />
                </div>
                <Badge variant="success">AVAILABLE</Badge>
              </div>
              <CardTitle className="mt-4 text-base text-white font-display">Academic Catalog &amp; Offerings</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Inspect institutional degree courses, course types, credit allocations, and syllabus descriptions.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              <div className="p-3 bg-[#111722] rounded-lg border border-white/10 text-xs">
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-surface-400">Active Offerings:</span>
                  <span className="font-semibold text-white">
                    {courses.filter((c) => c.is_active).length} Courses
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-surface-400">Departments Configured:</span>
                  <span className="font-semibold text-white">
                    {departments.length}
                  </span>
                </div>
              </div>
              <Link href="/admin/academic" className="block pt-1">
                <Button size="sm" className="w-full justify-between text-xs bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0" data-testid="goto-academic-catalog-btn">
                  <span>Open Academic Records</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Card 2: User Directory & RBAC Notice (User instruction #2 compliant) */}
          <Card className="flex flex-col justify-between border-white/10">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="rounded-xl bg-white/5 p-2.5 text-surface-400 border border-white/10">
                  <Lock className="h-6 w-6" />
                </div>
                <Badge variant="neutral">ROLE GOVERNED</Badge>
              </div>
              <CardTitle className="mt-4 text-base text-white font-display">User Directory &amp; RBAC Control</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Least-privilege role-based access control and secure Argon2id password authentication.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 space-y-3 text-xs text-surface-400">
              <p className="leading-relaxed">
                Enterprise identity authentication and authorization are securely enforcing least-privilege role boundaries across all campus operations.
              </p>
              <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                <span className="font-semibold text-white">Active Governance: </span>
                Identity decoupled from academic student/faculty profiles via immutable 1-to-1 relations.
              </div>
            </CardContent>
          </Card>

          {/* Card 3: Institutional Knowledge & Policy Management */}
          <Card className="flex flex-col justify-between hover:shadow-md transition md:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="rounded-xl bg-[#FF7A18]/10 p-2.5 text-[#FF9A3D] border border-[#FF7A18]/20">
                  <Layers className="h-6 w-6" />
                </div>
                <Badge variant="success">KNOWLEDGE ACTIVE</Badge>
              </div>
              <CardTitle className="mt-4 text-base text-white font-display">Institutional Knowledge &amp; Policies</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Authoritative campus document repository. Manage document versioning, publication schedules, and vector embeddings for AI policy retrieval.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              <div className="p-3 bg-[#111722] rounded-lg border border-white/10 text-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <span className="text-surface-400">
                  Strictly grounded policy retrieval with Reciprocal Rank Fusion &amp; non-overlapping version constraints.
                </span>
                <Link href="/admin/knowledge">
                  <Button size="sm" className="text-xs space-x-1.5 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0 flex-shrink-0" data-testid="goto-knowledge-mgmt-btn">
                    <span>Manage Policies</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ProtectedRoute>
  );
}

