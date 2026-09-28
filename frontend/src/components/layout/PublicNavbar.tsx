"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Menu, X, ArrowRight, ShieldCheck, LogIn } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/components/ui/Button";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function PublicNavbar() {
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const baseNavLinks = [
    { name: "Features", href: "/features" },
    { name: "How It Works", href: "/how-it-works" },
    { name: "Security & Privacy", href: "/security" },
  ];
  const navLinks = user?.roles?.includes("SUPER_ADMIN")
    ? [...baseNavLinks, { name: "System Status", href: "/system-status" }]
    : baseNavLinks;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#07090D]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#FF7A18] text-[#07090D] shadow-[0_0_16px_rgba(255,122,24,0.35)] group-hover:bg-[#FF9A3D] transition-colors">
            <Activity className="h-5 w-5 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <span className="font-display text-lg font-bold tracking-tight text-[#F5F7FA] leading-none">
              CampusPulse
            </span>
            <span className="text-[10px] text-[#A7AFBD] font-mono tracking-wide mt-0.5">
              STUDENT SUCCESS PLATFORM
            </span>
          </div>
        </Link>

        {/* Desktop Nav Links */}
        <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-180 ${
                  isActive
                    ? "text-[#FF9A3D] bg-[#FF7A18]/12 border border-[#FF7A18]/25"
                    : "text-[#A7AFBD] hover:text-[#F5F7FA] hover:bg-white/[0.05]"
                }`}
              >
                {link.name}
              </Link>
            );
          })}
        </nav>

        {/* Desktop Auth Actions */}
        <div className="hidden md:flex items-center space-x-3" data-testid="auth-action-buttons">
          <ThemeToggle />
          <div className="h-4 w-px bg-white/[0.08]" />
          {isAuthenticated && user ? (
            <Link href="/dashboard">
              <Button size="sm" className="text-xs space-x-1.5 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold">
                <span>Go to Workstation</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          ) : (
            <>
              <Link href="/login">
                <Button size="sm" variant="ghost" className="text-xs space-x-1.5 text-[#A7AFBD] hover:text-[#F5F7FA]" data-testid="nav-login-button">
                  <LogIn className="h-3.5 w-3.5" />
                  <span>Sign In</span>
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="text-xs bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold" data-testid="nav-register-button">
                  Register
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden items-center space-x-2">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-[#A7AFBD] hover:bg-white/[0.08] hover:text-[#F5F7FA] transition-colors"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-white/[0.08] bg-[#0D1117] px-4 py-4 space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <span className="text-xs font-mono uppercase tracking-wider text-[#A7AFBD]">Appearance</span>
            <ThemeToggle showLabel />
          </div>
          <nav className="flex flex-col space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-lg text-sm font-medium text-[#A7AFBD] hover:bg-white/[0.05] hover:text-[#F5F7FA]"
              >
                {link.name}
              </Link>
            ))}
          </nav>
          <div className="pt-2 border-t border-white/[0.08] flex flex-col gap-2">
            {isAuthenticated ? (
              <Link href="/dashboard" onClick={() => setMobileMenuOpen(false)}>
                <Button size="sm" className="w-full bg-[#FF7A18] text-[#07090D]">
                  Go to Workstation
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button size="sm" variant="outline" className="w-full">
                    Sign In
                  </Button>
                </Link>
                <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                  <Button size="sm" className="w-full bg-[#FF7A18] text-[#07090D]">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
