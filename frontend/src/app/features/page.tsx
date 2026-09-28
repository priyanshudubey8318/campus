"use client";

import React from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Bot,
  FileText,
  Briefcase,
  HeartHandshake,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { RingBackground } from "@/components/ui/RingBackground";

export default function FeaturesPage() {
  const features = [
    {
      title: "Academic Engagement Monitoring",
      description: "Continuous, privacy-respecting behavioral monitoring measuring attendance stability, submission timeliness, and evaluation performance against a student's personal baseline.",
      icon: Activity,
      badge: "Behavioral Analytics",
      highlights: [
        "Session-by-session roll-call verification",
        "Deterministic trend classification (Stable, Mild, Moderate, Shift)",
        "Secondary cohort context without student ranking or shaming",
      ],
    },
    {
      title: "Explainable Support Priority",
      description: "Deterministic algorithm calculating a 0–100 Support Priority Index (SPI) across attendance, coursework, and persistence signals to guide advisor intervention rosters.",
      icon: AlertTriangle,
      badge: "Early Warning",
      highlights: [
        "Zero black-box machine learning decisions",
        "Deterministic safety-floor overrides for acute drops",
        "Full transparent decomposition: 'Why am I seeing this?'",
      ],
    },
    {
      title: "Campus Knowledge Assistant",
      description: "Retrieval-Augmented Generation (RAG) assistant answering questions about institutional academic regulations, leave policies, and exam criteria with exact citations.",
      icon: Bot,
      badge: "Grounded AI",
      highlights: [
        "Answers grounded strictly in verified institutional documents",
        "Interactive citation drawer with exact excerpt highlights",
        "Comprehensive query logging and token latency auditing",
      ],
    },
    {
      title: "Student Records & Grievance Governance",
      description: "Auditable workflows for student leave requests, medical certificates, and confidential grievance reporting with anonymous whistleblower protections.",
      icon: FileText,
      badge: "Records & Leaves",
      highlights: [
        "Multi-step leave review: Faculty recommendation to Admin approval",
        "Anonymous complaint submission protecting student identity",
        "Audit logging for every status change and review action",
      ],
    },
    {
      title: "Multi-Disciplinary Support Cases",
      description: "Holistic student case management connecting early warning flags and faculty referrals to structured advising action plans and scheduled progress check-ins.",
      icon: Briefcase,
      badge: "Interventions",
      highlights: [
        "Lifecycle state machine: Open to Resolved with mandatory summaries",
        "Action plans with checkboxes visible directly in student portal",
        "Scheduled check-ins and follow-up appointment tracking",
      ],
    },
    {
      title: "Confidential Wellbeing & Counseling Services",
      description: "Dedicated mental health and personal counseling intake with cryptographically and logically isolated case notes protected from general staff view.",
      icon: HeartHandshake,
      badge: "Wellbeing Care",
      highlights: [
        "Strict confidentiality boundaries preventing non-clinical access",
        "Urgent care prioritization and intake scheduling",
        "Sanitized student-facing views that never leak diagnostic codes",
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
            PLATFORM CAPABILITIES
          </Badge>
          <h1 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tight text-[#F5F7FA]">
            Engineered for Academic Rigor and Student Care
          </h1>
          <p className="text-sm sm:text-base text-[#A7AFBD] leading-relaxed">
            CampusPulse unifies deterministic academic intelligence, early support intervention, policy retrieval, and confidential student support into a single reliable platform.
          </p>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feat) => {
          const Icon = feat.icon;
          return (
            <Card key={feat.title} interactive className="flex flex-col justify-between border-white/[0.08] bg-[#0D1117] shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="p-2.5 rounded-xl bg-[#151B24] border border-white/10 text-[#FF7A18]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <Badge variant="outline" className="text-xs font-mono">
                    {feat.badge}
                  </Badge>
                </div>
                <CardTitle className="text-base pt-3 font-display">{feat.title}</CardTitle>
                <CardDescription className="text-xs leading-relaxed text-[#A7AFBD]">
                  {feat.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="border-t border-white/[0.06] pt-3">
                  <h4 className="text-[11px] font-mono font-medium uppercase tracking-wider text-[#A7AFBD] mb-2">
                    Key Features
                  </h4>
                  <ul className="text-xs text-[#A7AFBD] space-y-1.5">
                    {feat.highlights.map((h, i) => (
                      <li key={i} className="flex items-start space-x-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#FF7A18] shrink-0 mt-0.5" />
                        <span>{h}</span>
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
            Ready to inspect the platform?
          </h2>
          <p className="text-xs sm:text-sm text-[#A7AFBD]">
            Explore the live interactive environment across all role workstations.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link href="/login">
              <Button size="lg" className="bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold space-x-1.5 shadow-[0_4px_20px_rgba(255,122,24,0.3)]">
                <span>Sign In to Workstations</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/how-it-works">
              <Button size="lg" variant="secondary" className="border-white/10 text-[#F5F7FA]">
                <span>How It Works &rarr;</span>
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
