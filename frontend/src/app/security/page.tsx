"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  Database,
  FileCheck2,
  EyeOff,
  KeyRound,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { RingBackground } from "@/components/ui/RingBackground";

export default function SecurityPage() {
  const pillars = [
    {
      title: "Multi-Tenant Data & Schema Isolation",
      icon: Database,
      description: "All academic tables, records, and casework enforce mandatory institutional tenant scoping at the database level. Foreign keys utilize ON DELETE RESTRICT constraints to prevent cascading accidental data destruction.",
      items: [
        "Strict institution_id scoping on every database query",
        "Deterministic tenant boundaries preventing cross-institutional leakage",
        "Referential integrity constraints guarding historical academic records",
      ],
    },
    {
      title: "Fine-Grained Role-Based Access Control (RBAC)",
      icon: KeyRound,
      description: "Every API endpoint enforces strict permission checks matching verified user roles: STUDENT, FACULTY, ADVISOR, COUNSELOR, ADMIN, and SUPER_ADMIN. Privilege escalation attempts result in instant HTTP 403 blocks.",
      items: [
        "Endpoint-level permission guards across all subsystems",
        "Role-tailored projections ensuring users only receive permitted fields",
        "Complete separation of student self-service and staff administrative tools",
      ],
    },
    {
      title: "Counselor Confidentiality Boundaries",
      icon: Lock,
      description: "Mental health and wellbeing case notes marked COUNSELOR_CONFIDENTIAL are partitioned from academic systems. Academic advisors, faculty, and students receive clean sanitized views with zero note leakage.",
      items: [
        "Access strictly limited to assigned counselors and root authorities",
        "Endpoint redaction: unauthorized requests receive clean 404 responses",
        "Diagnostic codes and clinical notes never exposed to student views",
      ],
    },
    {
      title: "Anonymous Grievance & Whistleblower Protection",
      icon: EyeOff,
      description: "Students can submit complaints anonymously. Submitter identities are cryptographically segregated, allowing administrators to investigate grievances without exposing student identities to retaliation.",
      items: [
        "Anonymous submitter flag removing user foreign key references",
        "Redacted complaint records in staff inspection listings",
        "Protected review status transitions and resolution timelines",
      ],
    },
    {
      title: "Immutable Event Auditing",
      icon: FileCheck2,
      description: "All critical platform events—including case status changes, note creations, leave reviews, policy publications, and AI query sessions—are recorded in immutable audit logs with timestamps and actor IDs.",
      items: [
        "CASE_CREATED, CASE_ASSIGNED, CASE_RESOLVED lifecycle audit events",
        "AI query and cited document chunk audit logging",
        "Tamper-resistant append-only logging tables",
      ],
    },
    {
      title: "AI Knowledge Isolation & Non-Leakage",
      icon: ShieldCheck,
      description: "The PulseAssist Retrieval-Augmented Generation (RAG) vector index is strictly restricted to approved, published institutional handbooks. Private student casework, leaves, and grievances are never indexed or embedded.",
      items: [
        "Zero vector leakage: student records strictly excluded from embeddings",
        "Grounded generation with verifiable citations only",
        "Immediate hallucination suppression for ungrounded queries",
      ],
    },
  ];

  return (
    <div className="space-y-16 pb-16 relative">
      {/* Header */}
      <section className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 text-center space-y-4 shadow-[0_8px_30px_rgba(0,0,0,0.6)]">
        <RingBackground variant="subtle" glowPosition="top" />
        <div className="relative z-10 max-w-3xl mx-auto space-y-4">
          <Badge variant="primary" className="font-mono text-xs">
            SECURITY &amp; PRIVACY ARCHITECTURE
          </Badge>
          <h1 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tight text-[#F5F7FA]">
            Factual Security Controls Built for Higher Education
          </h1>
          <p className="text-sm sm:text-base text-[#A7AFBD] leading-relaxed">
            CampusPulse is engineered around deterministic security invariants: multi-tenant isolation, fine-grained RBAC, counselor confidentiality boundaries, and immutable audit trails.
          </p>
        </div>
      </section>

      {/* Security Pillars Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pillars.map((p) => {
          const Icon = p.icon;
          return (
            <Card key={p.title} interactive className="flex flex-col justify-between border-white/[0.08] bg-[#0D1117] shadow-sm">
              <CardHeader className="pb-3">
                <div className="p-2.5 w-fit rounded-xl bg-[#151B24] border border-white/10 text-[#FF7A18]">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-base pt-3 font-display">{p.title}</CardTitle>
                <CardDescription className="text-xs leading-relaxed text-[#A7AFBD]">
                  {p.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="border-t border-white/[0.06] pt-3">
                  <h4 className="text-[11px] font-mono font-medium uppercase tracking-wider text-[#A7AFBD] mb-2">
                    Architectural Enforcement
                  </h4>
                  <ul className="text-xs text-[#A7AFBD] space-y-1.5">
                    {p.items.map((item, i) => (
                      <li key={i} className="flex items-start space-x-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#FF7A18] shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 text-center space-y-4 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
        <RingBackground variant="subtle" glowPosition="center" />
        <div className="relative z-10 space-y-3 max-w-xl mx-auto">
          <h2 className="text-2xl font-display font-bold text-[#F5F7FA]">
            Inspect the Platform First-Hand
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD]">
            Access our demo environment to verify role boundaries and security safeguards.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link href="/login">
              <Button size="lg" className="bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold space-x-1.5 shadow-[0_4px_20px_rgba(255,122,24,0.3)]">
                <span>Sign In to Workstations</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/system-status">
              <Button size="lg" variant="secondary" className="border-white/10 text-[#F5F7FA]">
                <span className="font-mono">System Telemetry &rarr;</span>
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
