"use client";

import React, { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AlertCircle, Eye, EyeOff, Loader2, Lock, Mail } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export function LoginForm() {
  const { login, isLoading, error, clearError } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = searchParams.get("returnUrl") || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setClientError(null);

    if (!email.trim()) {
      setClientError("Please enter your email address.");
      return;
    }
    if (!password) {
      setClientError("Please enter your password.");
      return;
    }

    try {
      const user = await login({ email: email.trim(), password });
      // Redirect to returnUrl or user role portal
      if (returnUrl && returnUrl !== "/") {
        router.push(returnUrl);
      } else if (user.roles.includes("SUPER_ADMIN")) {
        router.push("/super-admin");
      } else if (user.roles.includes("ADMIN")) {
        router.push("/admin");
      } else if (user.roles.includes("FACULTY")) {
        router.push("/faculty");
      } else if (user.roles.includes("ADVISOR")) {
        router.push("/advisor");
      } else if (user.roles.includes("COUNSELOR")) {
        router.push("/counselor");
      } else {
        router.push("/student");
      }
    } catch {
      // Error handled by AuthContext
    }
  };

  const handleQuickLogin = async (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("CampusPulse@2026!");
    setClientError(null);
    clearError();
    try {
      const u = await login({ email: demoEmail, password: "CampusPulse@2026!" });
      if (returnUrl && returnUrl !== "/") {
        router.push(returnUrl);
      } else if (u.roles.includes("SUPER_ADMIN")) {
        router.push("/super-admin");
      } else if (u.roles.includes("ADMIN")) {
        router.push("/admin");
      } else if (u.roles.includes("FACULTY")) {
        router.push("/faculty");
      } else if (u.roles.includes("ADVISOR")) {
        router.push("/advisor");
      } else if (u.roles.includes("COUNSELOR")) {
        router.push("/counselor");
      } else {
        router.push("/student");
      }
    } catch {
      // Error handled by AuthContext
    }
  };

  const displayError = clientError || error;

  return (
    <Card className="w-full max-w-md shadow-[0_16px_50px_rgba(0,0,0,0.8)] border-white/[0.08] bg-[#0D1117]">
      <CardHeader className="space-y-1 text-center pb-4">
        <CardTitle className="text-2xl font-display font-bold tracking-tight text-[#F5F7FA]">
          Sign in to CampusPulse
        </CardTitle>
        <CardDescription className="text-xs text-[#A7AFBD]">
          Enter your institutional credentials to access your account
        </CardDescription>
      </CardHeader>

      <CardContent>
        {displayError && (
          <div
            className="mb-4 flex items-center space-x-2 rounded-lg bg-[#FF4D4D]/10 p-3 text-sm text-[#FF4D4D] border border-[#FF4D4D]/25"
            role="alert"
            data-testid="login-error-alert"
          >
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="font-medium">{displayError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]"
            >
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-[#6F7785]" />
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                disabled={isLoading}
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (clientError) setClientError(null);
                }}
                placeholder="name@university.edu"
                className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-3 py-2 text-sm text-[#F5F7FA] placeholder-[#6F7785] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]"
            >
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-[#6F7785]" />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                disabled={isLoading}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (clientError) setClientError(null);
                }}
                placeholder="••••••••"
                className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-10 py-2 text-sm text-[#F5F7FA] placeholder-[#6F7785] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-[#6F7785] hover:text-[#F5F7FA] transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full font-semibold py-2.5 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] shadow-[0_2px_14px_rgba(255,122,24,0.3)] mt-2"
            data-testid="login-submit-button"
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Signing in...</span>
              </div>
            ) : (
              "Sign In"
            )}
          </Button>
        </form>

        {/* Demo Quick Accounts */}
        <div className="mt-6 pt-5 border-t border-white/[0.08]">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-[11px] font-mono font-medium uppercase tracking-wider text-[#A7AFBD]">
              Demo Instant Login
            </span>
            <span className="text-[10px] text-[#FF7A18] font-mono">1-Click Fill</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { role: "Student", email: "student@campuspulse.edu", label: "Student" },
              { role: "Faculty", email: "faculty@campuspulse.edu", label: "Faculty" },
              { role: "Advisor", email: "advisor@campuspulse.edu", label: "Advisor" },
              { role: "Counselor", email: "counselor@campuspulse.edu", label: "Counselor" },
              { role: "Admin", email: "admin@campuspulse.edu", label: "Admin" },
              { role: "Super Admin", email: "superadmin@campuspulse.edu", label: "Super Admin" },
            ].map((acc) => (
              <button
                key={acc.role}
                type="button"
                onClick={() => handleQuickLogin(acc.email)}
                className="p-2 rounded-lg border border-white/[0.08] hover:border-[#FF7A18]/40 bg-[#111722] hover:bg-[#151B24] text-left transition-colors"
              >
                <div className="font-semibold text-[#F5F7FA] text-[11px]">
                  {acc.label}
                </div>
                <div className="text-[10px] text-[#6F7785] truncate font-mono">
                  {acc.email.split("@")[0]}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-[#A7AFBD]">
          Do not have an account?{" "}
          <Link
            href="/register"
            className="font-semibold text-[#FF9A3D] hover:underline"
          >
            Create an institutional account
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
