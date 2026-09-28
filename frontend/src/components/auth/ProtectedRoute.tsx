"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { ShieldAlert, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  fallbackUrl?: string;
}

export function ProtectedRoute({
  children,
  requiredRoles,
  requiredPermissions,
  fallbackUrl = "/login",
}: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading, hasRole, hasPermission } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const returnUrl = encodeURIComponent(pathname);
      router.push(`${fallbackUrl}?returnUrl=${returnUrl}`);
    }
  }, [isLoading, isAuthenticated, router, pathname, fallbackUrl]);

  if (isLoading) {
    return (
      <div
        className="flex min-h-[50vh] flex-col items-center justify-center space-y-4"
        role="status"
        aria-label="Verifying authentication credentials"
      >
        <Loader2 className="h-8 w-8 animate-spin text-[#FF7A18]" />
        <p className="text-sm font-medium text-surface-400">
          Verifying security credentials...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-md py-12">
        <Card className="border-amber-500/20 bg-[#0D1117]">
          <CardHeader>
            <div className="flex items-center space-x-2 text-amber-400">
              <AlertCircle className="h-5 w-5" />
              <CardTitle className="text-white font-display">Authentication Required</CardTitle>
            </div>
            <CardDescription className="text-surface-400">
              You must be signed in to access this resource.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              className="w-full bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20"
              onClick={() => {
                const returnUrl = encodeURIComponent(pathname);
                router.push(`${fallbackUrl}?returnUrl=${returnUrl}`);
              }}
            >
              Sign In to Continue
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check Role requirements
  if (requiredRoles && requiredRoles.length > 0 && !hasRole(requiredRoles)) {
    const isStudent = user?.roles.includes("STUDENT");
    const dashboardHref = isStudent ? "/student" : "/dashboard";

    return (
      <div className="mx-auto max-w-xl py-12" data-testid="forbidden-state">
        <Card className="border-rose-500/20 bg-[#0D1117] shadow-sm">
          <CardHeader>
            <div className="flex items-center space-x-3 text-rose-400">
              <ShieldAlert className="h-7 w-7 flex-shrink-0" />
              <div>
                <CardTitle className="text-xl text-white font-display">403 — Access Forbidden</CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Access Restricted &bull; Your account does not hold the required role for this portal. Staff access is required for this area.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-lg bg-[#111722] p-4 space-y-2 border border-white/10">
              <div className="text-xs font-semibold uppercase text-surface-400 font-mono">
                Your Assigned Roles
              </div>
              <div className="flex flex-wrap gap-2">
                {user?.roles.map((role) => (
                  <Badge key={role} variant="neutral">
                    {role}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Link href={dashboardHref} className="flex-1">
                <Button className="w-full bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] hover:from-[#FF8A2E] hover:to-[#FFA751] text-black font-semibold shadow-lg shadow-[#FF7A18]/20" data-testid="return-to-dashboard-btn">
                  Return to My Dashboard
                </Button>
              </Link>
              <Link href="/" className="sm:w-auto">
                <Button variant="outline" className="w-full border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
                  Home
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check Permission requirements
  if (
    requiredPermissions &&
    requiredPermissions.length > 0 &&
    !hasPermission(requiredPermissions)
  ) {
    return (
      <div className="mx-auto max-w-xl py-12" data-testid="forbidden-state">
        <Card className="border-rose-500/20 bg-[#0D1117]">
          <CardHeader>
            <div className="flex items-center space-x-3 text-rose-400">
              <ShieldAlert className="h-7 w-7 flex-shrink-0" />
              <div>
                <CardTitle className="text-xl text-white font-display">403 — Missing Permission</CardTitle>
                <CardDescription className="text-surface-400">
                  Your account lacks the specific permissions required to execute this operation.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-lg bg-[#111722] p-4 space-y-2 border border-white/10">
              <div className="text-xs font-semibold uppercase text-surface-400 font-mono">
                Required Permissions
              </div>
              <div className="flex flex-wrap gap-2">
                {requiredPermissions.map((perm) => (
                  <Badge key={perm} variant="primary">
                    {perm}
                  </Badge>
                ))}
              </div>
            </div>

            <Link href="/">
              <Button variant="outline" className="w-full border-white/10 text-surface-300 hover:text-white hover:bg-white/5">
                Return to Home
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
