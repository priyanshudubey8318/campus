"use client";

import React, { useEffect } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to monitoring infrastructure
    console.error("CampusPulse frontend error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 text-center p-6">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-950/40 border border-rose-500/20 text-rose-400">
        <AlertCircle className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h2 className="text-xl font-bold tracking-tight text-white font-display">
          Application Error Encountered
        </h2>
        <p className="max-w-md text-sm text-surface-400">
          An unexpected error occurred while rendering this interface. Details have been captured.
        </p>
      </div>
      <Button variant="primary" size="sm" onClick={() => reset()} className="space-x-1.5">
        <RotateCcw className="h-3.5 w-3.5" />
        <span>Try Again</span>
      </Button>
    </div>
  );
}
