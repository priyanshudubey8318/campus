import React from "react";
import { RefreshCw } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4">
      <RefreshCw className="h-8 w-8 animate-spin text-[#FF7A18]" />
      <p className="text-sm text-surface-400 font-medium">Loading CampusPulse interface...</p>
    </div>
  );
}
