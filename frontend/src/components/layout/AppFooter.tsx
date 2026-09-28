"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/auth-context";

export function AppFooter() {
  const { user } = useAuth();

  return (
    <footer className="border-t border-white/[0.08] bg-[#07090D] py-3.5 px-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[#A7AFBD]">
        <div>
          <span className="font-mono text-[11px]">CampusPulse &copy; 2026. Unified Student Success Platform.</span>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/security" className="hover:text-[#FF9A3D] transition-colors">
            Security &amp; Privacy
          </Link>
          {user?.roles?.includes("SUPER_ADMIN") && (
            <>
              <span>&bull;</span>
              <Link href="/system-status" className="hover:text-[#FF9A3D] transition-colors">
                Platform Status
              </Link>
            </>
          )}
          <span>&bull;</span>
          <span className="font-mono text-[11px] text-[#28C76F]">
            RBAC Enforced
          </span>
        </div>
      </div>
    </footer>
  );
}
