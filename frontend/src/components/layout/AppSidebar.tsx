"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GraduationCap,
  BookOpen,
  CalendarCheck,
  FileText,
  Briefcase,
  HeartHandshake,
  Compass,
  Building2,
  ShieldCheck,
  ShieldAlert,
  Bot,
  Activity,
  Server,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth/auth-context";

interface NavItem {
  name: string;
  href?: string;
  icon: React.ComponentType<{ className?: string }>;
  isAction?: boolean;
  action?: () => void;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();
  const roles = user?.roles || [];

  const isSuperAdmin = roles.includes("SUPER_ADMIN");
  const isAdmin = roles.includes("ADMIN") || isSuperAdmin;
  const isCounselor = roles.includes("COUNSELOR");
  const isAdvisor = roles.includes("ADVISOR");
  const isFaculty = roles.includes("FACULTY");
  const isStudent = roles.includes("STUDENT");

  const openPulseAssist = () => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("open-pulseassist"));
    }
  };

  // Determine sections based on primary active role
  const sections: NavSection[] = [];

  if (isAdmin) {
    sections.push({
      title: "Overview",
      items: [
        { name: "Executive Dashboard", href: "/admin", icon: LayoutDashboard },
      ],
    });
    sections.push({
      title: "Institution",
      items: [
        { name: "Academic Management", href: "/admin/academic", icon: Building2 },
        { name: "Knowledge & Policies", href: "/admin/knowledge", icon: BookOpen },
        { name: "Support Cases", href: "/admin/cases", icon: Briefcase },
        { name: "Records & Grievances", href: "/admin/records", icon: FileText },
      ],
    });
    sections.push({
      title: "Student Success",
      items: [
        { name: "Engagement & Priority (SPI)", href: "/advisor", icon: Activity },
      ],
    });
    sections.push({
      title: "Assistance & Governance",
      items: [
        {
          name: "Knowledge Assistant",
          icon: Bot,
          isAction: true,
          action: openPulseAssist,
        },
        ...(isSuperAdmin
          ? [{ name: "Root Audit & System", href: "/super-admin", icon: ShieldAlert }]
          : []),
      ],
    });
  } else if (isCounselor) {
    sections.push({
      title: "Overview",
      items: [
        { name: "Counselor Dashboard", href: "/counselor", icon: LayoutDashboard },
      ],
    });
    sections.push({
      title: "Caseload Management",
      items: [
        { name: "Assigned Cases", href: "/counselor", icon: Briefcase },
        { name: "Urgent Care Queue", href: "/counselor?priority=URGENT", icon: AlertTriangle },
        { name: "Confidential Notes", href: "/counselor", icon: HeartHandshake },
      ],
    });
    sections.push({
      title: "Assistance & Account",
      items: [
        {
          name: "Knowledge Assistant",
          icon: Bot,
          isAction: true,
          action: openPulseAssist,
        },
        { name: "Staff Profile", href: "/faculty/profile", icon: GraduationCap },
      ],
    });
  } else if (isAdvisor) {
    sections.push({
      title: "Overview",
      items: [
        { name: "Advisor Dashboard", href: "/advisor", icon: LayoutDashboard },
      ],
    });
    sections.push({
      title: "Student Success",
      items: [
        { name: "Student Roster & Priority", href: "/advisor", icon: Compass },
        { name: "Academic Engagement", href: "/advisor", icon: Activity },
      ],
    });
    sections.push({
      title: "Interventions",
      items: [
        { name: "Support Cases", href: "/advisor/cases", icon: Briefcase },
        { name: "Open Referrals", href: "/cases?status=OPEN", icon: HeartHandshake },
      ],
    });
    sections.push({
      title: "Assistance & Account",
      items: [
        {
          name: "Knowledge Assistant",
          icon: Bot,
          isAction: true,
          action: openPulseAssist,
        },
        { name: "Staff Profile", href: "/faculty/profile", icon: GraduationCap },
      ],
    });
  } else if (isFaculty) {
    sections.push({
      title: "Overview",
      items: [
        { name: "Faculty Dashboard", href: "/faculty", icon: LayoutDashboard },
      ],
    });
    sections.push({
      title: "Academics",
      items: [
        { name: "Courses & Roster", href: "/faculty/courses", icon: CalendarCheck },
      ],
    });
    sections.push({
      title: "Support & Actions",
      items: [
        { name: "Submit Referral", href: "/academic/referrals/new", icon: Compass },
        { name: "My Referrals", href: "/academic/referrals/my", icon: Briefcase },
        { name: "Leave Requests", href: "/faculty/leaves", icon: FileText },
      ],
    });
    sections.push({
      title: "Assistance & Account",
      items: [
        {
          name: "Knowledge Assistant",
          icon: Bot,
          isAction: true,
          action: openPulseAssist,
        },
        { name: "Faculty Profile", href: "/faculty/profile", icon: GraduationCap },
      ],
    });
  } else if (isStudent) {
    sections.push({
      title: "Overview",
      items: [
        { name: "Student Dashboard", href: "/student", icon: LayoutDashboard },
      ],
    });
    sections.push({
      title: "Academics",
      items: [
        { name: "My Academics", href: "/student/academics", icon: BookOpen },
        { name: "Attendance & Records", href: "/student/academics?tab=attendance", icon: CalendarCheck },
      ],
    });
    sections.push({
      title: "Support & Wellbeing",
      items: [
        { name: "Support Center", href: "/student/support", icon: HeartHandshake },
        { name: "Leave Requests", href: "/student/leaves", icon: FileText },
        { name: "Grievances & Appeals", href: "/student/complaints", icon: ShieldAlert },
      ],
    });
    sections.push({
      title: "Assistance & Account",
      items: [
        {
          name: "Knowledge Assistant",
          icon: Bot,
          isAction: true,
          action: openPulseAssist,
        },
        { name: "Academic Profile", href: "/student/profile", icon: GraduationCap },
      ],
    });
  } else {
    // Unauthenticated or general fallback
    sections.push({
      title: "Workstations",
      items: [
        { name: "Student Portal", href: "/student", icon: GraduationCap },
        { name: "Faculty Portal", href: "/faculty", icon: CalendarCheck },
        { name: "Advisor Hub", href: "/advisor", icon: Compass },
        { name: "Counselor Hub", href: "/counselor", icon: HeartHandshake },
        { name: "Admin Console", href: "/admin", icon: ShieldCheck },
      ],
    });
  }

  return (
    <aside className="w-64 flex-shrink-0 border-r border-white/[0.08] bg-[#07090D] hidden md:block">
      <div className="flex h-full flex-col justify-between p-4 overflow-y-auto">
        <div className="space-y-6">
          {sections.map((section, idx) => (
            <div key={idx}>
              <span className="px-3 text-[10px] font-mono font-medium uppercase tracking-wider text-[#6F7785]">
                {section.title}
              </span>
              <nav className="mt-2 space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;

                  if (item.isAction) {
                    return (
                      <button
                        key={item.name}
                        type="button"
                        onClick={item.action}
                        className="w-full text-left group flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-[#A7AFBD] hover:bg-[#FF7A18]/10 hover:text-[#FF9A3D] transition-colors"
                      >
                        <div className="flex items-center space-x-2.5">
                          <Icon className="h-4 w-4 text-[#FF7A18]" />
                          <span>{item.name}</span>
                        </div>
                        <span className="text-[10px] font-mono font-semibold text-[#FF9A3D] bg-[#FF7A18]/15 px-1.5 py-0.5 rounded">Ask</span>
                      </button>
                    );
                  }

                  const isActive =
                    item.href === pathname ||
                    (item.href && item.href !== "/" && pathname.startsWith(item.href) && !item.href.includes("?"));

                  return (
                    <Link
                      key={item.name}
                      href={item.href || "#"}
                      className={cn(
                        "group flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-all duration-180",
                        isActive
                          ? "bg-[#FF7A18]/12 text-[#FF9A3D] font-semibold border-l-2 border-[#FF7A18] shadow-sm"
                          : "text-[#A7AFBD] hover:text-[#F5F7FA] hover:bg-white/[0.04]"
                      )}
                    >
                      <div className="flex items-center space-x-2.5">
                        <Icon
                          className={cn(
                            "h-4 w-4 transition-colors",
                            isActive
                              ? "text-[#FF7A18]"
                              : "text-[#6F7785] group-hover:text-[#A7AFBD]"
                          )}
                        />
                        <span>{item.name}</span>
                      </div>
                      {isActive && (
                        <span className="h-1.5 w-1.5 rounded-full bg-[#FF7A18]" />
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        {/* Operational Status Link - SUPER_ADMIN only */}
        {user?.roles?.includes("SUPER_ADMIN") && (
          <Link href="/system-status" className="block mt-6">
            <div className="rounded-lg border border-white/[0.08] bg-[#0D1117] p-3 hover:border-[#FF7A18]/30 transition shadow-sm">
              <div className="flex items-center justify-between text-xs text-[#F5F7FA] font-medium">
                <div className="flex items-center space-x-2">
                  <Server className="h-3.5 w-3.5 text-[#FF7A18]" />
                  <span className="font-mono">System Status</span>
                </div>
                <span className="h-2 w-2 rounded-full bg-[#28C76F] animate-pulse" />
              </div>
              <p className="mt-1 text-[11px] text-[#A7AFBD] font-mono">
                Live Diagnostics &amp; Telemetry
              </p>
            </div>
          </Link>
        )}
      </div>
    </aside>
  );
}
