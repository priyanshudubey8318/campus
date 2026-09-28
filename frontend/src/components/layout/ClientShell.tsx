"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { PublicNavbar } from "./PublicNavbar";
import { PublicFooter } from "./PublicFooter";
import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";
import { AppFooter } from "./AppFooter";
import { PulseAssistDrawer } from "@/components/pulseassist/PulseAssistDrawer";

interface ClientShellProps {
  children: React.ReactNode;
}

const PUBLIC_ROUTES = [
  "/",
  "/features",
  "/how-it-works",
  "/security",
  "/login",
  "/register",
];

export function ClientShell({ children }: ClientShellProps) {
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  if (isPublic) {
    return (
      <div className="min-h-screen flex flex-col bg-[#07090D] text-[#F5F7FA]">
        <PublicNavbar />
        <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
          {children}
        </main>
        <PublicFooter />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col min-h-screen bg-[#07090D] text-[#F5F7FA]">
      <AppHeader />
      <div className="flex flex-1 overflow-hidden">
        <AppSidebar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
      <AppFooter />
      <PulseAssistDrawer />
    </div>
  );
}
