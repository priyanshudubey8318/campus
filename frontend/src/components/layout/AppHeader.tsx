"use client";

import React from "react";
import Link from "next/link";
import { Activity, LogIn, LogOut, User } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/lib/auth/auth-context";

export function AppHeader() {
  const { user, isAuthenticated, logout } = useAuth();

  const primaryRole = user?.roles[0] || "USER";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-[#0D1117]/95 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center space-x-3">
          <Link href="/" className="flex items-center space-x-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#FF7A18] text-[#07090D] shadow-[0_0_16px_rgba(255,122,24,0.35)] group-hover:bg-[#FF9A3D] transition-colors">
              <Activity className="h-5 w-5 stroke-[2.5]" />
            </div>
            <div className="flex flex-col">
              <span className="font-display text-lg font-bold tracking-tight text-[#F5F7FA]">
                CampusPulse
              </span>
              <span className="hidden sm:inline-block font-mono text-[10px] text-[#A7AFBD] uppercase tracking-wider">
                Student Success Platform
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center space-x-2 sm:space-x-4">
          {user?.roles?.includes("SUPER_ADMIN") && (
            <>
              <Link
                href="/system-status"
                className="hidden sm:inline-flex items-center space-x-1.5 text-xs text-[#A7AFBD] hover:text-[#F5F7FA] transition-colors"
              >
                <Activity className="h-3.5 w-3.5 text-[#FF7A18]" />
                <span className="font-mono">Platform Status</span>
              </Link>
              <div className="hidden sm:block h-4 w-px bg-white/[0.08]" />
            </>
          )}

          <ThemeToggle />
          <div className="h-4 w-px bg-white/[0.08]" />

          {isAuthenticated && user ? (
            <div className="flex items-center space-x-3" data-testid="user-profile-menu">
              <div className="flex items-center space-x-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#151B24] border border-white/10 text-[#FF9A3D] font-mono font-bold text-xs">
                  {user.full_name
                    ? user.full_name
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join("")
                        .toUpperCase()
                    : <User className="h-4 w-4" />}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-semibold text-[#F5F7FA]">
                    {user.full_name}
                  </span>
                  <div className="flex items-center space-x-1">
                    <Badge
                      variant="primary"
                      className="text-[9px] py-0 px-1 font-mono uppercase bg-[#FF7A18]/12 text-[#FF9A3D] border border-[#FF7A18]/30"
                    >
                      {primaryRole}
                    </Badge>
                  </div>
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  await logout();
                }}
                className="text-xs text-[#A7AFBD] hover:text-[#FF4D4D] hover:bg-[#FF4D4D]/10"
                data-testid="sign-out-button"
              >
                <LogOut className="h-3.5 w-3.5 mr-1" />
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2" data-testid="auth-action-buttons">
              <Link href="/login">
                <Button variant="ghost" size="sm" className="text-xs text-[#A7AFBD] hover:text-[#F5F7FA]" data-testid="nav-login-button">
                  <LogIn className="h-3.5 w-3.5 mr-1" />
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="text-xs bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold" data-testid="nav-register-button">
                  Register
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
