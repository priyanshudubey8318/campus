"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api, ApiError } from "@/lib/api/client";
import { FacultyProfile } from "@/types/academic";
import { ArrowLeft, BookOpen, Briefcase, Calendar, ShieldCheck, UserCheck, AlertCircle } from "lucide-react";

export default function FacultyProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<FacultyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getMyFacultyProfile();
        setProfile(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load faculty profile");
        }
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  return (
    <ProtectedRoute requiredRoles={["FACULTY"]}>
      <div className="space-y-6" data-testid="faculty-profile-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/faculty"
              className="p-2 rounded-lg border border-white/10 hover:border-[#FF7A18]/40 hover:text-white transition"
              aria-label="Back to faculty portal"
            >
              <ArrowLeft className="h-4 w-4 text-surface-400" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold font-display tracking-tight text-white">
                Faculty Academic Profile
              </h1>
              <p className="text-sm text-surface-400">
                Institutional department appointments and verified teaching credentials.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="primary">FACULTY DOMAIN</Badge>
            <Badge variant={profile?.is_active ? "success" : "neutral"}>
              {profile?.is_active ? "ACTIVE FACULTY" : "INACTIVE"}
            </Badge>
          </div>
        </div>

        {loading && (
          <Card className="border-white/10 bg-[#0D1117]">
            <CardContent className="py-12 text-center text-surface-400">
              Loading verified faculty profile...
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="border-red-500/20 bg-red-950/30">
            <CardContent className="py-4 text-sm text-red-400">
              {error}
            </CardContent>
          </Card>
        )}

        {profile && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2 border-white/10 bg-[#0D1117]">
              <CardHeader className="border-b border-white/10 pb-3">
                <CardTitle className="flex items-center space-x-2 text-white font-display">
                  <Briefcase className="h-5 w-5 text-[#FF7A18]" />
                  <span>Appointment &amp; Designation</span>
                </CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Academic appointment records maintained by the university dean.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Employee ID</span>
                    <p className="text-base font-bold text-white font-mono mt-0.5" data-testid="faculty-employee-id">
                      {profile.employee_id}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Department</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.department_name || "Computer Science & Engineering"}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Designation</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.designation}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Joining Date</span>
                    <p className="text-base font-semibold text-white mt-0.5 font-mono">
                      {profile.joining_date}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Specialization</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.specialization || "General Computer Science"}
                    </p>
                  </div>
                  <div className="p-3 bg-[#111722] rounded-lg border border-white/10">
                    <span className="text-xs text-surface-400 uppercase font-semibold font-mono tracking-wider">Highest Qualification</span>
                    <p className="text-base font-semibold text-white mt-0.5">
                      {profile.qualification || "Doctorate / Masters"}
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/10 flex justify-end">
                  <Link
                    href="/faculty/courses"
                    className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:opacity-90 text-white rounded-lg transition"
                  >
                    <BookOpen className="h-4 w-4" />
                    <span>View Assigned Teaching Offerings</span>
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
                  <span className="text-xs text-surface-400">Faculty Full Name</span>
                  <p className="font-semibold text-white">{user?.full_name}</p>
                </div>
                <div>
                  <span className="text-xs text-surface-400">Institutional Email</span>
                  <p className="font-mono text-xs text-surface-300">{user?.email}</p>
                </div>
                <div>
                  <span className="text-xs text-surface-400">Scoped Authorization</span>
                  <p className="text-xs text-surface-500 mt-1 leading-relaxed">
                    Grading, assessment, and attendance operations are strictly scoped to assigned courses and sections.
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
