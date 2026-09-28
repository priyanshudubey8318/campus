"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { Loader2 } from "lucide-react";

export default function DashboardRouterPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated || !user) {
      router.replace("/login?returnUrl=/dashboard");
      return;
    }

    const roles = user.roles || [];

    if (roles.includes("SUPER_ADMIN")) {
      router.replace("/super-admin");
    } else if (roles.includes("ADMIN")) {
      router.replace("/admin");
    } else if (roles.includes("ADVISOR")) {
      router.replace("/advisor");
    } else if (roles.includes("COUNSELOR")) {
      router.replace("/counselor");
    } else if (roles.includes("FACULTY")) {
      router.replace("/faculty");
    } else {
      router.replace("/student");
    }
  }, [isLoading, isAuthenticated, user, router]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center space-y-4">
      <Loader2 className="h-8 w-8 animate-spin text-[#FF7A18]" />
      <p className="text-sm font-medium text-surface-400">
        Navigating to your authorized workstation...
      </p>
    </div>
  );
}
