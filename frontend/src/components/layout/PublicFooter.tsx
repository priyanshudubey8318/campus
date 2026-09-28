"use client";

import React from "react";
import Link from "next/link";
import { Activity, ShieldCheck, Lock, Database } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";

export function PublicFooter() {
  const { user } = useAuth();
  return (
    <footer className="border-t border-white/[0.08] bg-[#07090D] text-[#A7AFBD] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        {/* Brand Column */}
        <div className="space-y-3 md:col-span-1">
          <div className="flex items-center space-x-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#FF7A18] text-[#07090D]">
              <Activity className="h-4 w-4 stroke-[2.5]" />
            </div>
            <span className="font-display text-lg font-bold text-[#F5F7FA] tracking-tight">CampusPulse</span>
          </div>
          <p className="text-xs text-[#A7AFBD] leading-relaxed">
            Unified student success, explainable early interventions, and institutional coordination engineered for higher education.
          </p>
          <div className="flex items-center space-x-2 text-[11px] text-[#28C76F] font-mono">
            <span className="h-2 w-2 rounded-full bg-[#28C76F] animate-pulse" />
            <span>Platform Operational</span>
          </div>
        </div>

        {/* Platform Workspaces */}
        <div>
          <h4 className="text-xs font-mono font-medium uppercase tracking-wider text-[#F5F7FA] mb-3">
            Role Workstations
          </h4>
          <ul className="space-y-2 text-xs">
            <li>
              <Link href="/login" className="hover:text-[#FF9A3D] transition-colors">
                Student Learning Center
              </Link>
            </li>
            <li>
              <Link href="/login" className="hover:text-[#FF9A3D] transition-colors">
                Faculty Academic Workstation
              </Link>
            </li>
            <li>
              <Link href="/login" className="hover:text-[#FF9A3D] transition-colors">
                Advisor Support &amp; Triage Roster
              </Link>
            </li>
            <li>
              <Link href="/login" className="hover:text-[#FF9A3D] transition-colors">
                Counselor Wellbeing Services
              </Link>
            </li>
            <li>
              <Link href="/login" className="hover:text-[#FF9A3D] transition-colors">
                Institutional Administration
              </Link>
            </li>
          </ul>
        </div>

        {/* Core Capabilities */}
        <div>
          <h4 className="text-xs font-mono font-medium uppercase tracking-wider text-[#F5F7FA] mb-3">
            Platform Capabilities
          </h4>
          <ul className="space-y-2 text-xs">
            <li>
              <Link href="/features" className="hover:text-[#FF9A3D] transition-colors">
                Academic Engagement Monitoring
              </Link>
            </li>
            <li>
              <Link href="/features" className="hover:text-[#FF9A3D] transition-colors">
                Explainable Support Priority
              </Link>
            </li>
            <li>
              <Link href="/features" className="hover:text-[#FF9A3D] transition-colors">
                Campus Knowledge Assistant
              </Link>
            </li>
            <li>
              <Link href="/features" className="hover:text-[#FF9A3D] transition-colors">
                Official Student Records &amp; Leaves
              </Link>
            </li>
            <li>
              <Link href="/features" className="hover:text-[#FF9A3D] transition-colors">
                Holistic Support Cases &amp; Action Plans
              </Link>
            </li>
          </ul>
        </div>

        {/* Architecture & Governance */}
        <div>
          <h4 className="text-xs font-mono font-medium uppercase tracking-wider text-[#F5F7FA] mb-3">
            Security &amp; Architecture
          </h4>
          <ul className="space-y-2 text-xs text-[#A7AFBD]">
            <li className="flex items-center space-x-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-[#FF7A18] shrink-0" />
              <span>Role-Based Access Control (RBAC)</span>
            </li>
            <li className="flex items-center space-x-1.5">
              <Lock className="h-3.5 w-3.5 text-[#FF7A18] shrink-0" />
              <span>Strict Counselor Confidentiality</span>
            </li>
            <li className="flex items-center space-x-1.5">
              <Database className="h-3.5 w-3.5 text-[#FF7A18] shrink-0" />
              <span>Multi-Tenant Schema Isolation</span>
            </li>
            <li className="pt-2">
              {user?.roles?.includes("SUPER_ADMIN") ? (
                <Link href="/system-status" className="text-[#FF9A3D] hover:underline font-mono text-xs">
                  View System Telemetry &rarr;
                </Link>
              ) : (
                <Link href="/security" className="text-[#FF9A3D] hover:underline font-mono text-xs">
                  Security Framework &rarr;
                </Link>
              )}
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto pt-6 border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#6F7785]">
        <p className="font-mono">&copy; {new Date().getFullYear()} CampusPulse. All rights reserved.</p>
        <div className="flex items-center space-x-4">
          <Link href="/security" className="hover:text-[#A7AFBD] transition-colors">
            Privacy Architecture
          </Link>
          <Link href="/how-it-works" className="hover:text-[#A7AFBD] transition-colors">
            How It Works
          </Link>
          {user?.roles?.includes("SUPER_ADMIN") ? (
            <Link href="/system-status" className="hover:text-[#A7AFBD] transition-colors">
              Live Telemetry
            </Link>
          ) : (
            <Link href="/features" className="hover:text-[#A7AFBD] transition-colors">
              Platform Features
            </Link>
          )}
        </div>
      </div>
    </footer>
  );
}
