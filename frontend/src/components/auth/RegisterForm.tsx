"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Lock,
  Mail,
  User as UserIcon,
  Phone,
  Shield,
  Circle,
} from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export function RegisterForm() {
  const { register, isLoading, error, clearError } = useAuth();
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState("STUDENT");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  // Password rules validation
  const hasMinLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigit = /[0-9]/.test(password);
  const hasSpecial = /[\W_]/.test(password);
  const passwordsMatch = password.length > 0 && password === confirmPassword;

  const isPasswordValid =
    hasMinLength && hasUpper && hasLower && hasDigit && hasSpecial;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setClientError(null);

    if (!fullName.trim() || fullName.trim().length < 2) {
      setClientError("Please enter your full name (minimum 2 characters).");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setClientError("Please provide a valid institutional email address.");
      return;
    }
    if (!isPasswordValid) {
      setClientError("Password does not meet the institutional complexity requirements.");
      return;
    }
    if (!passwordsMatch) {
      setClientError("Passwords do not match.");
      return;
    }

    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        phone: phone.trim() || undefined,
        role: role,
        password,
      });

      // Redirect to appropriate dashboard
      if (role === "STUDENT") router.push("/student");
      else if (role === "FACULTY") router.push("/faculty");
      else if (role === "ADVISOR") router.push("/advisor");
      else if (role === "COUNSELOR") router.push("/counselor");
      else router.push("/admin");
    } catch {
      // Error handled by AuthContext
    }
  };

  const displayError = clientError || error;

  return (
    <Card className="w-full max-w-lg shadow-[0_16px_50px_rgba(0,0,0,0.8)] border-white/[0.08] bg-[#0D1117]">
      <CardHeader className="space-y-1 text-center pb-4">
        <CardTitle className="text-2xl font-display font-bold tracking-tight text-[#F5F7FA]">
          Create Account
        </CardTitle>
        <CardDescription className="text-xs text-[#A7AFBD]">
          Register for the CampusPulse institutional intelligence platform
        </CardDescription>
      </CardHeader>

      <CardContent>
        {displayError && (
          <div
            className="mb-4 flex items-center space-x-2 rounded-lg bg-[#FF4D4D]/10 p-3 text-sm text-[#FF4D4D] border border-[#FF4D4D]/25"
            role="alert"
            data-testid="register-error-alert"
          >
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="font-medium">{displayError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <label
              htmlFor="fullName"
              className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]"
            >
              Full Name
            </label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-3 h-4 w-4 text-[#6F7785]" />
              <input
                id="fullName"
                type="text"
                required
                autoComplete="name"
                disabled={isLoading}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-3 py-2 text-sm text-[#F5F7FA] placeholder-[#6F7785] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
              />
            </div>
          </div>

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
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane.doe@university.edu"
                className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-3 py-2 text-sm text-[#F5F7FA] placeholder-[#6F7785] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label
                htmlFor="phone"
                className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]"
              >
                Phone (Optional)
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-3 h-4 w-4 text-[#6F7785]" />
                <input
                  id="phone"
                  type="tel"
                  autoComplete="tel"
                  disabled={isLoading}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 555-0199"
                  className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-3 py-2 text-sm text-[#F5F7FA] placeholder-[#6F7785] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="role"
                className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]"
              >
                Initial Role
              </label>
              <div className="relative">
                <Shield className="absolute left-3 top-3 h-4 w-4 text-[#6F7785] pointer-events-none" />
                <select
                  id="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  disabled={isLoading}
                  className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-3 py-2 text-sm text-[#F5F7FA] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
                >
                  <option value="STUDENT">Student</option>
                  <option value="FACULTY">Faculty</option>
                  <option value="ADVISOR">Advisor</option>
                  <option value="COUNSELOR">Counselor</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </div>
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
                autoComplete="new-password"
                disabled={isLoading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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

          <div className="space-y-1.5">
            <label
              htmlFor="confirmPassword"
              className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]"
            >
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-[#6F7785]" />
              <input
                id="confirmPassword"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="new-password"
                disabled={isLoading}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-white/10 bg-[#151B24] pl-10 pr-3 py-2 text-sm text-[#F5F7FA] placeholder-[#6F7785] focus:border-[#FF7A18] focus:bg-[#151B24] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] transition-colors"
              />
            </div>
          </div>

          {/* Password complexity checklist */}
          <div className="rounded-xl bg-[#111722] p-3.5 text-xs border border-white/[0.08] space-y-1.5">
            <div className="font-mono font-medium text-[#F5F7FA] mb-1">
              Institutional Security Requirements:
            </div>
            <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              <div className={`flex items-center space-x-1.5 ${hasMinLength ? "text-[#28C76F]" : "text-[#6F7785]"}`}>
                {hasMinLength ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                <span>At least 8 characters</span>
              </div>
              <div className={`flex items-center space-x-1.5 ${hasUpper ? "text-[#28C76F]" : "text-[#6F7785]"}`}>
                {hasUpper ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                <span>One uppercase letter</span>
              </div>
              <div className={`flex items-center space-x-1.5 ${hasLower ? "text-[#28C76F]" : "text-[#6F7785]"}`}>
                {hasLower ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                <span>One lowercase letter</span>
              </div>
              <div className={`flex items-center space-x-1.5 ${hasDigit ? "text-[#28C76F]" : "text-[#6F7785]"}`}>
                {hasDigit ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                <span>One number</span>
              </div>
              <div className={`flex items-center space-x-1.5 ${hasSpecial ? "text-[#28C76F]" : "text-[#6F7785]"}`}>
                {hasSpecial ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                <span>One special character</span>
              </div>
              <div className={`flex items-center space-x-1.5 ${passwordsMatch ? "text-[#28C76F]" : "text-[#6F7785]"}`}>
                {passwordsMatch ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                <span>Passwords match</span>
              </div>
            </div>
          </div>

          <Button
            type="submit"
            disabled={isLoading || !isPasswordValid || !passwordsMatch}
            className="w-full font-semibold py-2.5 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] shadow-[0_2px_14px_rgba(255,122,24,0.3)] mt-2"
            data-testid="register-submit-button"
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Creating Account...</span>
              </div>
            ) : (
              "Register Account"
            )}
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-[#A7AFBD]">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold text-[#FF9A3D] hover:underline"
          >
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
