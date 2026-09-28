"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api/client";
import { StudentProfile } from "@/types/academic";
import { GraduationCap, ArrowLeft, BookOpen, Calendar, ShieldCheck, UserCheck, AlertCircle } from "lucide-react";

export default function StudentProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError(null);
        setNotFound(false);
        const data = await api.getMyStudentProfile();
        setProfile(data);
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 404 || err.message?.toLowerCase().includes("not found")) {
            setNotFound(true);
          } else {
            setError(err.message);
          }
        } else {
          setError("Failed to load student profile");
        }
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  return (
    <ProtectedRoute requiredRoles={["STUDENT"]}>
      <div className="space-y-6" data-testid="student-profile-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/student"
              className="p-2 rounded-lg border border-white/10 hover:border-[#FF7A18]/40 hover:text-white transition"
              aria-label="Back to student portal"
            >
              <ArrowLeft className="h-4 w-4 text-surface-400" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold font-display tracking-tight text-white">
                Academic Student Profile
              </h1>
              <p className="text-sm text-surface-400">
                Official institutional student enrollment records and cohort details.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="primary">STUDENT DOMAIN</Badge>
            <Badge variant={profile?.academic_status === "ENROLLED" ? "success" : "neutral"}>
              {profile?.academic_status || "PENDING"}
            </Badge>
          </div>
        </div>

        {loading && (
          <Card className="border-white/10 bg-[#0D1117]">
            <CardContent className="py-12 text-center text-surface-400">
              Loading verified academic profile...
            </CardContent>
          </Card>
        )}

        {notFound && (
          <Card className="border-white/10 bg-[#0D1117] shadow-2xl" data-testid="profile-not-available">
            <CardContent className="py-12 px-6 flex flex-col items-center justify-center text-center space-y-4">
              <div className="rounded-full bg-[#111722] border border-white/10 p-4 text-[#FF9A3D]">
                <GraduationCap className="h-8 w-8" />
              </div>
              <div className="space-y-1 max-w-md">
                <h3 className="text-lg font-bold font-display text-white">
                  Academic Profile Not Available Yet
                </h3>
                <p className="text-xs sm:text-sm text-surface-400 leading-relaxed">
                  Your official student record has not been linked to an active degree program yet. Please contact the Office of the Registrar to verify your enrollment.
                </p>
              </div>
              <Link href="/student">
                <Button size="sm" variant="primary" className="space-x-1.5">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Return to Dashboard</span>
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {error && !notFound && (
          <Card className="border-red-500/20 bg-red-950/30">
            <CardContent className="py-6 flex items-center space-x-3 text-red-400">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-sm">System Connection Issue</p>
                <p className="text-xs text-surface-400">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {profile && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2 border-white/10 bg-[#0D1117]">
              <CardHeader className="border-b border-white/10 pb-3">
                <CardTitle className="flex items-center space-x-2 text-white font-display">
                  <GraduationCap className="h-5 w-5 text-[#FF7A18]" />
                  <span>Cohort &amp; Registration Details</span>
                </CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Immutable academic identifiers assigned by registrar.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Enrollment Number</span>
                    <p className="text-base font-bold text-white font-mono mt-0.5" data-testid="student-enrollment-number">
                      {profile.enrollment_number}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Academic Program</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.program_name || "B.Tech Computer Science"}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Batch Cohort</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.batch_name || "2024-2028"}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Assigned Section</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.section_name || "Section A"}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Current Semester</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      Semester {profile.current_semester}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Admission Date</span>
                    <p className="text-base font-semibold text-white mt-0.5 font-mono">
                      {profile.admission_date}
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/10 flex justify-end">
                  <Link
                    href="/student/academics"
                    className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:opacity-90 text-white rounded-lg transition"
                  >
                    <BookOpen className="h-4 w-4" />
                    <span>View Coursework &amp; Attendance</span>
                  </Link>
                </div>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-[#0D1117]">
              <CardHeader className="border-b border-white/10 pb-3">
                <CardTitle className="flex items-center space-x-2 text-sm font-semibold text-white font-display">
                  <UserCheck className="h-4 w-4 text-emerald-400" />
                  <span>Identity Association</span>
                </CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Institutional Identity Principal.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm pt-4">
                <div>
                  <span className="text-xs text-surface-400">Student Name</span>
                  <p className="font-semibold text-white">{user?.full_name}</p>
                </div>
                <div>
                  <span className="text-xs text-surface-400">Institutional Email</span>
                  <p className="font-mono text-xs text-surface-300">{user?.email}</p>
                </div>
                <div>
                  <span className="text-xs text-surface-400">Security Architecture</span>
                  <p className="text-xs text-surface-500 mt-1 leading-relaxed">
                    Zero credentials or passwords exist in academic profile. Strict 1-to-1 RESTRICT relation protects transcripts.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
