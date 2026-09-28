"use client";

import React from "react";
import Link from "next/link";
import {
  CalendarCheck,
  Activity,
  AlertTriangle,
  Compass,
  Briefcase,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RingBackground } from "@/components/ui/RingBackground";

export default function HowItWorksPage() {
  const steps = [
    {
      step: "01",
      title: "Academic Operations & Evidence Recording",
      icon: CalendarCheck,
      description: "Instructors record official roll-call attendance per teaching section. Students submit coursework assignments, and instructors enter verified evaluation results. All events are recorded immutably in PostgreSQL.",
      details: ["Real-time session roll call", "Coursework submission timestamps", "Deterministic evaluation scoring"],
    },
    {
      step: "02",
      title: "Behavioral Monitoring & Trend Calculation",
      icon: Activity,
      description: "Engagement signals are derived from attendance trends and submission pacing relative to each student's personal baseline. Changes are classified deterministically without invasive tracking or surveillance.",
      details: ["Personal historical baseline comparison", "Trend classification: Normal, Mild, Moderate, Shift", "Secondary cohort context for advisors"],
    },
    {
      step: "03",
      title: "Deterministic Support Prioritization",
      icon: AlertTriangle,
      description: "The Support Priority Index (0–100) aggregates weighted attendance, coursework, and persistence signals. Transparent safety floors override scores when critical drops occur, ensuring high-risk needs are immediately flagged.",
      details: ["Fully explainable math: no black-box models", "Configurable institutional risk policies", "Instant 'Why am I seeing this?' decomposition"],
    },
    {
      step: "04",
      title: "Faculty Referrals & Advisor Triage",
      icon: Compass,
      description: "Instructors submit proactive referrals for students exhibiting academic friction. Advisors inspect the prioritized roster, review decomposed factors, and initiate targeted intervention cases.",
      details: ["Scoped faculty referral submission form", "Multi-filter cohort prioritization roster", "One-click case creation from roster view"],
    },
    {
      step: "05",
      title: "Holistic Casework & Student Action Plans",
      icon: Briefcase,
      description: "Advisors establish measurable action plans (tutoring contracts, advising check-ins). Students track their assigned action items directly in their self-service portal with zero exposure of internal staff notes.",
      details: ["Checkable action items in student portal", "Scheduled follow-up appointment tracking", "Mandatory resolution outcome summaries"],
    },
    {
      step: "06",
      title: "Confidential Care & Governance Auditing",
      icon: ShieldCheck,
      description: "When personal or mental health needs arise, cases are routed to licensed counselors. Case notes marked as confidential are restricted exclusively to counselors and root admins, protected by strict boundaries.",
      details: ["Cryptographic confidentiality boundaries", "Full audit trail for compliance verification", "Tenant-scoped database isolation"],
    },
  ];

  return (
    <div className="space-y-16 pb-16 relative">
      {/* Header */}
      <section className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 text-center space-y-4 shadow-[0_8px_30px_rgba(0,0,0,0.6)]">
        <RingBackground variant="subtle" glowPosition="top" />
        <div className="relative z-10 max-w-3xl mx-auto space-y-4">
          <Badge variant="primary" className="font-mono text-xs">
            PLATFORM ARCHITECTURE &amp; WORKFLOW
          </Badge>
          <h1 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tight text-[#F5F7FA]">
            How CampusPulse Connects Early Signals to Measurable Support
          </h1>
          <p className="text-sm sm:text-base text-[#A7AFBD] leading-relaxed">
            From the first lecture roll call to graduation, CampusPulse provides an auditable, transparent lifecycle connecting academic signals, faculty observations, and student interventions.
          </p>
        </div>
      </section>

      {/* Steps Timeline */}
      <section className="max-w-4xl mx-auto space-y-6">
        {steps.map((s) => {
          const Icon = s.icon;
          return (
            <div
              key={s.step}
              className="relative flex flex-col md:flex-row items-start gap-6 p-6 sm:p-8 rounded-2xl border border-white/[0.08] bg-[#0D1117] shadow-sm hover-lift-card hover:border-[#FF7A18]/30 transition-all duration-200"
            >
              <div className="flex items-center gap-4 md:flex-col md:items-center">
                <span className="text-2xl sm:text-3xl font-extrabold text-[#FF7A18] font-mono">
                  {s.step}
                </span>
                <div className="p-3 rounded-2xl bg-[#151B24] border border-white/10 text-[#FF7A18]">
                  <Icon className="h-6 w-6" />
                </div>
              </div>

              <div className="flex-1 space-y-3">
                <h3 className="text-lg sm:text-xl font-display font-bold text-[#F5F7FA]">
                  {s.title}
                </h3>
                <p className="text-xs sm:text-sm text-[#A7AFBD] leading-relaxed">
                  {s.description}
                </p>
                <div className="pt-2 border-t border-white/[0.06] flex flex-wrap gap-4 text-xs text-[#A7AFBD]">
                  {s.details.map((d, i) => (
                    <div key={i} className="flex items-center space-x-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-[#FF7A18] shrink-0" />
                      <span>{d}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0D1117] p-8 sm:p-12 text-center space-y-4 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
        <RingBackground variant="subtle" glowPosition="center" />
        <div className="relative z-10 space-y-3 max-w-xl mx-auto">
          <h2 className="text-2xl font-display font-bold text-[#F5F7FA]">
            Explore the Platform First-Hand
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD]">
            Sign in to experience role workstations with pre-loaded mock demonstration data.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link href="/login">
              <Button size="lg" className="bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold space-x-1.5 shadow-[0_4px_20px_rgba(255,122,24,0.3)]">
                <span>Sign In to Workstations</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/security">
              <Button size="lg" variant="secondary" className="border-white/10 text-[#F5F7FA]">
                <span>Security Architecture &rarr;</span>
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
