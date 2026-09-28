import React from "react";
import Link from "next/link";
import { Compass, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 text-center p-6">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#111722] border border-white/10 text-[#FF9A3D]">
        <Compass className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h2 className="text-xl font-bold tracking-tight text-white font-display">
          Resource Not Found
        </h2>
        <p className="max-w-md text-sm text-surface-400">
          The requested CampusPulse portal page or resource does not exist or has been relocated.
        </p>
      </div>
      <Link href="/">
        <Button variant="outline" size="sm" className="space-x-1.5 border-white/10 hover:border-[#FF7A18]/40 hover:text-white">
          <Home className="h-3.5 w-3.5" />
          <span>Return to Dashboard</span>
        </Button>
      </Link>
    </div>
  );
}
