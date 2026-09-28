"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api, ApiError } from "@/lib/api/client";
import { Course, Enrollment } from "@/types/academic";
import {
  ArrowLeft,
  BookOpen,
  GraduationCap,
  Layers,
  Search,
  AlertCircle,
  Building2,
  Users,
} from "lucide-react";

export default function AdminAcademicPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [departments, setDepartments] = useState<import("@/types/academic").Department[]>([]);
  const [terms, setTerms] = useState<import("@/types/academic").AcademicTerm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    async function loadAdminAcademicData() {
      try {
        setLoading(true);
        setError(null);
        const [courseList, enrList, deptList, termList] = await Promise.all([
          api.getCourses(),
          api.getEnrollments(),
          api.getDepartments().catch(() => []),
          api.getTerms().catch(() => []),
        ]);
        setCourses(courseList);
        setEnrollments(enrList);
        setDepartments(deptList);
        setTerms(termList);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load academic catalog data");
        }
      } finally {
        setLoading(false);
      }
    }
    loadAdminAcademicData();
  }, []);

  const filteredCourses = courses.filter((c) => {
    const s = searchTerm.toLowerCase();
    return (
      c.code.toLowerCase().includes(s) ||
      c.title.toLowerCase().includes(s) ||
      c.course_type.toLowerCase().includes(s)
    );
  });

  return (
    <ProtectedRoute requiredRoles={["ADMIN"]}>
      <div className="space-y-6" data-testid="admin-academic-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/admin"
              className="p-2 rounded-lg border border-white/10 hover:bg-white/5 text-surface-400 hover:text-white transition"
              aria-label="Back to admin portal"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white font-display">
                Academic Management &amp; Catalog
              </h1>
              <p className="text-sm text-surface-400">
                Institutional course directory, active offerings, and student enrollment records.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="primary">ADMIN PORTAL</Badge>
            <Badge variant="success">ACADEMIC OPERATIONS</Badge>
          </div>
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-surface-400 uppercase font-semibold font-mono">Courses in Catalog</p>
                <p className="text-2xl font-bold text-white mt-0.5">
                  {courses.length}
                </p>
              </div>
              <BookOpen className="h-7 w-7 text-[#FF9A3D]/40" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-surface-400 uppercase font-semibold font-mono">Total Enrollments</p>
                <p className="text-2xl font-bold text-white mt-0.5">
                  {enrollments.length}
                </p>
              </div>
              <Users className="h-7 w-7 text-[#FF7A18]/40" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-surface-400 uppercase font-semibold font-mono">Active Enrollments</p>
                <p className="text-2xl font-bold text-white mt-0.5">
                  {enrollments.filter((e) => e.status === "ENROLLED").length}
                </p>
              </div>
              <GraduationCap className="h-7 w-7 text-blue-400/40" />
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-surface-500" />
          <input
            type="text"
            placeholder="Search courses by code, title, or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-white/10 bg-[#0D1117] text-white placeholder-surface-500 text-sm focus:outline-none focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30 transition"
            data-testid="admin-courses-search"
          />
        </div>

        {loading && (
          <Card>
            <CardContent className="py-12 text-center text-surface-400 text-xs">
              Loading academic catalog and records...
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="border-rose-500/30 bg-rose-500/10">
            <CardContent className="py-4 flex items-center space-x-3 text-rose-400 text-sm">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{error}</span>
            </CardContent>
          </Card>
        )}

        {/* Courses Table */}
        {!loading && !error && (
          <Card>
            <CardHeader className="pb-3 border-b border-white/10">
              <div className="flex items-center space-x-2">
                <Building2 className="h-5 w-5 text-[#FF9A3D]" />
                <CardTitle className="text-base text-white font-display">Institutional Course Catalog</CardTitle>
              </div>
              <CardDescription className="text-xs text-surface-400">
                Accredited academic courses scoped to departments and institutions.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse" data-testid="admin-courses-table">
                <thead>
                  <tr className="border-y border-white/10 bg-[#111722] text-surface-400 font-mono uppercase text-[11px] tracking-wider">
                    <th className="py-3 px-4 font-semibold">Course Code</th>
                    <th className="py-3 px-4 font-semibold">Title</th>
                    <th className="py-3 px-4 font-semibold">Type</th>
                    <th className="py-3 px-4 font-semibold">Credits</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredCourses.map((c) => (
                    <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-[#FF9A3D]">
                        {c.code}
                      </td>
                      <td className="py-3 px-4 font-medium text-white">
                        {c.title}
                        {c.syllabus_summary && (
                          <p className="text-[11px] text-surface-400 font-normal truncate max-w-xs mt-0.5">
                            {c.syllabus_summary}
                          </p>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="neutral">{c.course_type}</Badge>
                      </td>
                      <td className="py-3 px-4 font-semibold text-surface-200">
                        {c.credits} Cr
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={c.is_active ? "success" : "neutral"}>
                          {c.is_active ? "ACTIVE" : "INACTIVE"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                  {filteredCourses.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-surface-500">
                        No courses found matching filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {/* Enrollments Sample */}
        {!loading && !error && enrollments.length > 0 && (
          <Card>
            <CardHeader className="pb-3 border-b border-white/10">
              <div className="flex items-center space-x-2">
                <Layers className="h-5 w-5 text-[#FF7A18]" />
                <CardTitle className="text-base text-white font-display">Active Course Enrollments</CardTitle>
              </div>
              <CardDescription className="text-xs text-surface-400">
                Composite unique enrollments mapped to students and academic terms.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse" data-testid="admin-enrollments-table">
                <thead>
                  <tr className="border-y border-white/10 bg-[#111722] text-surface-400 font-mono uppercase text-[11px] tracking-wider">
                    <th className="py-3 px-4 font-semibold">Enrollment ID</th>
                    <th className="py-3 px-4 font-semibold">Course Code</th>
                    <th className="py-3 px-4 font-semibold">Term</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold">Enrolled On</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {enrollments.slice(0, 10).map((e) => (
                    <tr key={e.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4 font-mono text-surface-400">
                        {e.id.slice(0, 8)}...
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-white">
                        {e.course_code || e.course_id.slice(0, 8)}
                      </td>
                      <td className="py-3 px-4 text-surface-300">
                        {e.term_name || "Fall 2026"}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={e.status === "ENROLLED" ? "success" : "neutral"}>
                          {e.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-surface-400">
                        {e.enrollment_date}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {/* Institutional Departments & Academic Terms */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-3 border-b border-white/10">
                <div className="flex items-center space-x-2">
                  <Building2 className="h-5 w-5 text-blue-400" />
                  <CardTitle className="text-base text-white font-display">Configured Departments</CardTitle>
                </div>
                <CardDescription className="text-xs text-surface-400">
                  Academic divisions mapped to institutional degree programs.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 pt-4">
                {departments.length === 0 ? (
                  <p className="text-xs text-surface-500 py-4 text-center">No departments loaded.</p>
                ) : (
                  departments.map((d) => (
                    <div
                      key={d.id}
                      className="flex items-center justify-between p-3 rounded-lg border border-white/10 bg-[#111722]/60 text-xs"
                    >
                      <div>
                        <span className="font-mono font-bold text-white">
                          {d.code}
                        </span>
                        <p className="text-surface-400 mt-0.5">{d.name}</p>
                      </div>
                      <Badge variant="neutral" className="text-[10px]">ACTIVE</Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3 border-b border-white/10">
                <div className="flex items-center space-x-2">
                  <Layers className="h-5 w-5 text-purple-400" />
                  <CardTitle className="text-base text-white font-display">Academic Terms</CardTitle>
                </div>
                <CardDescription className="text-xs text-surface-400">
                  Institutional calendar terms and semester enrollment windows.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 pt-4">
                {terms.length === 0 ? (
                  <p className="text-xs text-surface-500 py-4 text-center">No terms loaded.</p>
                ) : (
                  terms.map((t) => (
                    <div
                      key={t.id}
                      className="flex items-center justify-between p-3 rounded-lg border border-white/10 bg-[#111722]/60 text-xs"
                    >
                      <div>
                        <span className="font-semibold text-white">
                          {t.name}
                        </span>
                        <p className="text-[11px] text-surface-400 mt-0.5">
                          {t.start_date} to {t.end_date}
                        </p>
                      </div>
                      <Badge variant={t.is_active ? "success" : "neutral"}>
                        {t.is_active ? "CURRENT TERM" : "ARCHIVED"}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}

