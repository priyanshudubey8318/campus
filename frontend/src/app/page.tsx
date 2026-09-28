"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  GraduationCap,
  BookOpenCheck,
  Building2,
  ShieldCheck,
  ArrowRight,
  Activity,
  HeartHandshake,
  Compass,
  AlertTriangle,
  Bot,
  FileText,
  Briefcase,
  CheckCircle2,
  Lock,
  Database,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { RingBackground } from "@/components/ui/RingBackground";
import { useAuth } from "@/lib/auth/auth-context";
import { api } from "@/lib/api/client";
import { HealthResponse } from "@/types/health";

export default function ProductLandingPage() {
  const { user, isAuthenticated } = useAuth();
  const [, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const primaryRole = user?.roles[0];

  const getPortalHref = () => {
    if (!isAuthenticated || !primaryRole) return "/login";
    switch (primaryRole) {
      case "SUPER_ADMIN":
        return "/super-admin";
      case "ADMIN":
        return "/admin";
      case "ADVISOR":
        return "/advisor";
      case "COUNSELOR":
        return "/counselor";
      case "FACULTY":
        return "/faculty";
      default:
        return "/student";
    }
  };

  return (
    <div className="space-y-16 pb-16 relative" data-testid="product-landing-page">
      {/* 1. Hero Section */}
      <section className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 lg:p-16 shadow-[0_12px_40px_rgba(0,0,0,0.6)]">
        {/* Orbital Ring Background */}
        <RingBackground variant="hero" glowPosition="top" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-xs tracking-wider uppercase text-[#FF7A18] font-semibold flex items-center gap-2">
              <span className="inline-block w-4 h-0.5 bg-[#FF7A18]" />
              STUDENT SUCCESS PLATFORM
            </span>
            <span className="flex items-center space-x-1.5 text-xs text-[#A7AFBD] font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-[#28C76F] animate-pulse" />
              <span>Higher Education Operating System</span>
            </span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#F5F7FA] leading-[1.12] font-display">
            Helping students succeed <br />
            <span className="text-[#FF7A18]">
              before challenges become barriers.
            </span>
          </h1>

          <p className="text-sm sm:text-base lg:text-lg text-[#A7AFBD] leading-relaxed max-w-2xl font-sans">
            A unified, role-governed platform connecting students, faculty, advisors, and administrators.
            Real-time academic tracking, explainable support priorities, and collaborative institutional care.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-4">
            {isAuthenticated ? (
              <Link href={getPortalHref()}>
                <Button size="lg" className="space-x-2 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold shadow-[0_4px_20px_rgba(255,122,24,0.3)]" data-testid="hero-primary-portal-btn">
                  <span>Enter My Workstation ({primaryRole})</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/register">
                  <Button size="lg" className="space-x-2 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold shadow-[0_4px_20px_rgba(255,122,24,0.3)]" data-testid="hero-signin-btn">
                    <span>Get Started</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/features">
                  <Button size="lg" variant="secondary" className="border-white/10 text-[#F5F7FA]" data-testid="hero-explore-btn">
                    <span>Explore Platform</span>
                  </Button>
                </Link>
              </>
            )}
            <Link href="/system-status">
              <Button variant="ghost" size="lg" className="text-xs space-x-1.5 text-[#A7AFBD] hover:text-[#F5F7FA]" data-testid="view-system-status-btn">
                <Activity className="h-4 w-4 text-[#FF7A18]" />
                <span className="font-mono">Live System Telemetry</span>
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* 2. Role-Based Workstations Showcase */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <Badge variant="primary" className="font-mono text-xs">
            DEDICATED WORKSPACES
          </Badge>
          <h2 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-[#F5F7FA]">
            Role-Based Workstations
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD]">
            Purpose-built consoles designed around the daily operational needs of campus stakeholders.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* 1. Student Portal */}
          <Card interactive className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#FF7A18]">
                  <GraduationCap className="h-5 w-5" />
                </div>
                <Badge variant="primary">STUDENT</Badge>
              </div>
              <CardTitle className="text-base pt-2">Student Learning Center</CardTitle>
              <CardDescription className="text-xs">
                Active term courses, attendance tracking, coursework submissions, and personal support action plans.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <ul className="text-xs text-[#A7AFBD] space-y-1.5 list-disc list-inside">
                <li>Coursework &amp; attendance records</li>
                <li>Academic engagement trends</li>
                <li>Verified support action plans &amp; check-ins</li>
              </ul>
              <Link href={isAuthenticated ? "/student" : "/login"} className="block pt-2">
                <Button size="sm" variant="outline" className="w-full text-xs space-x-1" data-testid="goto-student-portal">
                  <span>Open Student Portal</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* 2. Faculty Workstation */}
          <Card interactive className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#FF9A3D]">
                  <BookOpenCheck className="h-5 w-5" />
                </div>
                <Badge variant="primary">FACULTY</Badge>
              </div>
              <CardTitle className="text-base pt-2">Faculty Academic Workstation</CardTitle>
              <CardDescription className="text-xs">
                Teaching section management, verified roll-call attendance, coursework grading, and proactive student referrals.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <ul className="text-xs text-[#A7AFBD] space-y-1.5 list-disc list-inside">
                <li>Class rosters &amp; session attendance</li>
                <li>Assignment releases &amp; evaluation</li>
                <li>One-click academic support referrals</li>
              </ul>
              <Link href={isAuthenticated ? "/faculty" : "/login"} className="block pt-2">
                <Button size="sm" variant="outline" className="w-full text-xs space-x-1" data-testid="goto-faculty-portal">
                  <span>Open Faculty Portal</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* 3. Advisor Roster */}
          <Card interactive className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#FFB020]">
                  <Compass className="h-5 w-5" />
                </div>
                <Badge variant="warning">ADVISOR</Badge>
              </div>
              <CardTitle className="text-base pt-2">Advisor Support &amp; Triage Roster</CardTitle>
              <CardDescription className="text-xs">
                Cohort prioritization, explainable support priority indexes, and integrated intervention cases.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <ul className="text-xs text-[#A7AFBD] space-y-1.5 list-disc list-inside">
                <li>Deterministic cohort triage roster</li>
                <li>Explainable metric decomposition</li>
                <li>Integrated intervention case creation</li>
              </ul>
              <Link href={isAuthenticated ? "/advisor" : "/login"} className="block pt-2">
                <Button size="sm" variant="outline" className="w-full text-xs space-x-1">
                  <span>Open Advisor Portal</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* 4. Counselor Wellbeing Services */}
          <Card interactive className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#FF4D4D]">
                  <HeartHandshake className="h-5 w-5" />
                </div>
                <Badge variant="danger">COUNSELOR</Badge>
              </div>
              <CardTitle className="text-base pt-2">Student Wellbeing Services</CardTitle>
              <CardDescription className="text-xs">
                Mental health intake, urgent consultation caseloads, and strictly confidential progress tracking.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <ul className="text-xs text-[#A7AFBD] space-y-1.5 list-disc list-inside">
                <li>Confidential wellbeing intakes</li>
                <li>Cryptographically isolated case notes</li>
                <li>Scheduled student progress check-ins</li>
              </ul>
              <Link href={isAuthenticated ? "/counselor" : "/login"} className="block pt-2">
                <Button size="sm" variant="outline" className="w-full text-xs space-x-1">
                  <span>Open Counselor Portal</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* 5. Institutional Administration */}
          <Card interactive className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#F5F7FA]">
                  <Building2 className="h-5 w-5" />
                </div>
                <Badge variant="outline">ADMIN</Badge>
              </div>
              <CardTitle className="text-base pt-2">Institutional Administration</CardTitle>
              <CardDescription className="text-xs">
                Academic programs, terms, course catalog, official student records, and grievance investigations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <ul className="text-xs text-[#A7AFBD] space-y-1.5 list-disc list-inside">
                <li>Degree catalogs, terms, and sections</li>
                <li>Official leave request approvals</li>
                <li>Formal complaint resolution workflows</li>
              </ul>
              <Link href={isAuthenticated ? "/admin" : "/login"} className="block pt-2">
                <Button size="sm" variant="outline" className="w-full text-xs space-x-1" data-testid="goto-admin-portal">
                  <span>Open Admin Portal</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* 6. Root Governance & Audit */}
          <Card interactive className="border-white/[0.08] bg-[#0D1117]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#FF4D4D]">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <Badge variant="danger">SUPER_ADMIN</Badge>
              </div>
              <CardTitle className="text-base pt-2">Root Governance &amp; Audit</CardTitle>
              <CardDescription className="text-xs">
                System telemetry, database integrity oversight, and immutable AI interaction audit trails.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <ul className="text-xs text-[#A7AFBD] space-y-1.5 list-disc list-inside">
                <li>Global platform engine telemetry</li>
                <li>AI assistant query &amp; citation audits</li>
                <li>Multi-tenant compliance oversight</li>
              </ul>
              <Link href={isAuthenticated ? "/super-admin" : "/login"} className="block pt-2">
                <Button size="sm" variant="outline" className="w-full text-xs space-x-1">
                  <span>Open Governance Console</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 3. Core Subsystems Overview */}
      <section className="rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 shadow-[0_8px_30px_rgba(0,0,0,0.5)] space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <Badge variant="primary" className="font-mono text-xs">
            ARCHITECTURE CORE
          </Badge>
          <h2 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-[#F5F7FA]">
            Built for Deterministic Academic Support
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD]">
            Engineered with strict service isolation, verifiable algorithms, and multi-tenant security invariants.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="p-5 rounded-2xl border border-white/[0.06] bg-[#111722] space-y-3 hover-lift-card">
            <div className="p-2 w-fit rounded-lg bg-[#151B24] border border-white/10 text-[#FF7A18]">
              <Activity className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-bold text-[#F5F7FA]">
              Academic Engagement
            </h3>
            <p className="text-xs text-[#A7AFBD] leading-relaxed">
              Continuous monitoring of session attendance, submission timeliness, and evaluation scores relative to each student&apos;s baseline.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.06] bg-[#111722] space-y-3 hover-lift-card">
            <div className="p-2 w-fit rounded-lg bg-[#151B24] border border-white/10 text-[#FFB020]">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-bold text-[#F5F7FA]">
              Support Priority Index
            </h3>
            <p className="text-xs text-[#A7AFBD] leading-relaxed">
              Transparent, deterministic score (0–100) combining attendance, coursework, and persistence signals into prioritized triage tiers.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.06] bg-[#111722] space-y-3 hover-lift-card">
            <div className="p-2 w-fit rounded-lg bg-[#151B24] border border-white/10 text-[#FF9A3D]">
              <Bot className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-bold text-[#F5F7FA]">
              Campus Knowledge Assistant
            </h3>
            <p className="text-xs text-[#A7AFBD] leading-relaxed">
              Grounded AI assistant answering student and staff policy queries strictly from verified institutional handbooks with citation trails.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.06] bg-[#111722] space-y-3 hover-lift-card">
            <div className="p-2 w-fit rounded-lg bg-[#151B24] border border-white/10 text-[#F5F7FA]">
              <FileText className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-bold text-[#F5F7FA]">
              Student Records &amp; Leaves
            </h3>
            <p className="text-xs text-[#A7AFBD] leading-relaxed">
              Official medical and academic leave submission, faculty recommendation reviews, and confidential grievance reporting.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.06] bg-[#111722] space-y-3 hover-lift-card">
            <div className="p-2 w-fit rounded-lg bg-[#151B24] border border-white/10 text-[#FF7A18]">
              <Briefcase className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-bold text-[#F5F7FA]">
              Support Cases &amp; Interventions
            </h3>
            <p className="text-xs text-[#A7AFBD] leading-relaxed">
              Integrated casework connecting advisor check-ins, tutoring contracts, counseling intakes, and student-facing action plans.
            </p>
          </div>

          <div className="p-5 rounded-2xl border border-white/[0.06] bg-[#111722] space-y-3 hover-lift-card">
            <div className="p-2 w-fit rounded-lg bg-[#151B24] border border-white/10 text-[#FF4D4D]">
              <Lock className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-bold text-[#F5F7FA]">
              Confidentiality Boundaries
            </h3>
            <p className="text-xs text-[#A7AFBD] leading-relaxed">
              Strict compartmentalization preventing non-clinical staff or student views from accessing sensitive mental health notes.
            </p>
          </div>
        </div>
      </section>

      {/* 4. Security & Privacy Architecture */}
      <section className="rounded-3xl border border-white/[0.08] bg-[#0D1117] text-[#F5F7FA] p-8 sm:p-12 shadow-[0_8px_30px_rgba(0,0,0,0.5)] space-y-6">
        <div className="max-w-3xl space-y-2">
          <div className="flex items-center space-x-2 text-[#FF7A18] text-xs font-mono font-semibold">
            <ShieldCheck className="h-4 w-4" />
            <span>INSTITUTIONAL GOVERNANCE</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-display font-bold tracking-tight">
            Security, Isolation &amp; Privacy by Design
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD] leading-relaxed">
            CampusPulse enforces strict architectural controls to protect sensitive student records, prevent cross-tenant data leakage, and maintain immutable audit records.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
          <div className="p-4 rounded-xl bg-[#111722] border border-white/[0.06] space-y-1.5">
            <h4 className="text-sm font-semibold text-[#F5F7FA] flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-[#FF7A18]" />
              Role-Based Access Control
            </h4>
            <p className="text-xs text-[#A7AFBD]">
              Fine-grained permissions strictly enforce authorization on every API endpoint and prevent privilege escalation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#111722] border border-white/[0.06] space-y-1.5">
            <h4 className="text-sm font-semibold text-[#F5F7FA] flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-[#FF7A18]" />
              Counselor Confidentiality
            </h4>
            <p className="text-xs text-[#A7AFBD]">
              Wellbeing case notes are cryptographically and logically isolated from general academic records and non-counselor roles.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#111722] border border-white/[0.06] space-y-1.5">
            <h4 className="text-sm font-semibold text-[#F5F7FA] flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-[#FF7A18]" />
              Immutable Audit Trails
            </h4>
            <p className="text-xs text-[#A7AFBD]">
              Every status change, case assignment, policy publication, and AI interaction is permanently logged for compliance auditing.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Call to Action */}
      <section className="relative overflow-hidden text-center rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 space-y-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
        <RingBackground variant="subtle" glowPosition="center" />
        <div className="relative z-10 space-y-4">
          <h2 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-[#F5F7FA]">
            Experience the CampusPulse Platform
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD] max-w-xl mx-auto">
            Explore the live interactive environment across all academic roles using pre-configured demonstration accounts.
          </p>
          <div className="pt-2 flex flex-wrap justify-center gap-3">
            <Link href="/login">
              <Button size="lg" className="bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold space-x-1.5 shadow-[0_4px_20px_rgba(255,122,24,0.3)]">
                <span>Sign In to Workstations</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/system-status">
              <Button size="lg" variant="secondary" className="border-white/10 text-[#F5F7FA]">
                <span className="font-mono">System Telemetry</span>
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
