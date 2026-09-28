"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Database,
  Layers,
  Server,
  ShieldCheck,
  Cpu,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { api } from "@/lib/api/client";
import { HealthResponse } from "@/types/health";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

function SystemStatusContent() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err?.message || "Failed to connect to backend service");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8" data-testid="system-status-page">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0D1117] p-4 sm:p-6 md:p-8 shadow-[0_8px_30px_rgba(0,0,0,0.6)]">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="success">Phase 0 Foundation</Badge>
              <Badge variant="neutral">Platform Production v1.0</Badge>
              <span className="text-xs text-[#A7AFBD] font-mono">MVP Operational</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-display font-bold tracking-tight text-[#F5F7FA]">
              CampusPulse Architecture Shell
            </h1>
            <p className="max-w-2xl text-sm text-[#A7AFBD]">
              AI-assisted student success and institutional support platform. Deterministic computing core with modular service isolation, built strictly according to the Master Engineering Specification.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchHealth}
              disabled={loading}
              className="space-x-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Status</span>
            </Button>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              <Button size="sm" variant="primary" className="space-x-1.5 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold">
                <span>API Docs</span>
              </Button>
            </a>
          </div>
        </div>
      </div>

      {/* Real-time System Connectivity Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Backend Service
              </span>
              <StatusIndicator
                status={loading ? "loading" : health ? "healthy" : "offline"}
                label={loading ? "Checking..." : health ? "Healthy" : "Offline"}
              />
            </div>
            <CardTitle className="mt-2 text-base flex items-center space-x-2">
              <Server className="h-4 w-4 text-emerald-600" />
              <span>FastAPI Runtime</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-surface-400">
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Backend Status:</span>
              <span data-testid="backend-status" className="font-mono text-white font-medium capitalize">
                {loading ? "Checking..." : (health?.status || "offline")}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>API Version:</span>
              <span data-testid="backend-version" className="font-mono text-white font-medium">
                {loading ? "Checking..." : (health?.version || "Unavailable")}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Uptime:</span>
              <span data-testid="backend-uptime" className="font-mono text-white font-medium">
                {loading ? "Checking..." : (health ? `${health.uptime_seconds}s` : "Unavailable")}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Environment:</span>
              <span className="font-mono text-white font-medium">
                {loading ? "Checking..." : (health?.environment || "Unavailable")}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span>Endpoint:</span>
              <span className="font-mono text-surface-400">/api/v1/health</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-400">
                Data Storage
              </span>
              <StatusIndicator
                status={
                  loading
                    ? "loading"
                    : health?.database?.connected
                    ? "healthy"
                    : "degraded"
                }
                label={
                  loading
                    ? "Checking..."
                    : health?.database?.connected
                    ? "Connected"
                    : "Standby"
                }
              />
            </div>
            <CardTitle className="mt-2 text-base flex items-center space-x-2">
              <Database className="h-4 w-4 text-emerald-500" />
              <span>PostgreSQL & Alembic</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-surface-400">
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Dialect / Engine:</span>
              <span data-testid="db-dialect" className="font-mono text-white font-medium">
                {loading ? "Checking..." : (health?.database?.dialect || "Unavailable")}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Database Connectivity:</span>
              <span data-testid="db-status" className="font-mono text-white font-medium">
                {loading ? "Checking..." : (health?.database?.connected ? "Connected" : "Disconnected")}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Migration Tool:</span>
              <span className="font-mono text-white font-medium">
                Alembic v1.13+
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span>Initial Revision:</span>
              <span className="font-mono text-surface-400">0001_initial_foundation</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-400">
                Frontend App
              </span>
              <StatusIndicator status="healthy" label="Ready" />
            </div>
            <CardTitle className="mt-2 text-base flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-emerald-500" />
              <span>Next.js App Shell</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-surface-400">
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Router:</span>
              <span className="font-mono text-white font-medium">
                App Router (TypeScript)
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5">
              <span>Styling:</span>
              <span className="font-mono text-white font-medium">
                Tailwind CSS
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span>Client Layer:</span>
              <span className="font-mono text-surface-400">Typed ApiClient</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Architecture Domain Matrix */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg">Domain Subsystems Roadmap</CardTitle>
              <CardDescription>
                Architectural boundaries established in accordance with Master Engineering Specification.
              </CardDescription>
            </div>
            <Badge variant="outline">11 Domains</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                title: "Core Infrastructure",
                phase: "Phase 0",
                status: "Ready",
                variant: "success" as const,
                desc: "Database engine, Alembic migrations, configuration, structured logging, health endpoints.",
              },
              {
                title: "Identity & Access",
                phase: "Phase 1",
                status: "Planned",
                variant: "default" as const,
                desc: "Least-privilege RBAC, JWT session management, audit trail logging, user administration.",
              },
              {
                title: "Student Profiles",
                phase: "Phase 1",
                status: "Planned",
                variant: "default" as const,
                desc: "Academic identity, cohorts, program records, timeline representation.",
              },
              {
                title: "Academic Data",
                phase: "Phase 2",
                status: "Planned",
                variant: "default" as const,
                desc: "Attendance tracking, assessments, assignments, submission timestamps, LMS activity.",
              },
              {
                title: "PulseWatch Subsystem",
                phase: "Phase 3",
                status: "Planned",
                variant: "default" as const,
                desc: "Deterministic baselines, trend detection, behavioral anomaly engine, cooldowns.",
              },
              {
                title: "PulseRisk Subsystem",
                phase: "Phase 4",
                status: "Planned",
                variant: "default" as const,
                desc: "Multi-signal explainable support priority, context weighting, historical scoring.",
              },
              {
                title: "PulseAssist (RAG)",
                phase: "Phase 5",
                status: "Planned",
                variant: "default" as const,
                desc: "Institution-grounded document search, source citations, student self-service assistant.",
              },
              {
                title: "PulseRecord (Leaves & Claims)",
                phase: "Phase 6",
                status: "Planned",
                variant: "default" as const,
                desc: "Leave requests, evidence uploads, authorized complaint and appeal workflows.",
              },
              {
                title: "PulseCase (Interventions)",
                phase: "Phase 7",
                status: "Planned",
                variant: "default" as const,
                desc: "Advisor intervention cases, case notes, follow-up schedules, outcome tracking.",
              },
            ].map((module) => (
              <div
                key={module.title}
                className="rounded-lg border border-white/10 p-4 bg-[#111722] space-y-2 hover:border-white/20 transition"
              >
                <div className="flex flex-wrap items-center justify-between gap-1.5">
                  <span className="text-xs font-bold text-white">
                    {module.title}
                  </span>
                  <Badge variant={module.variant} className="text-[10px]">
                    {module.phase} &bull; {module.status}
                  </Badge>
                </div>
                <p className="text-xs text-surface-400">
                  {module.desc}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SystemStatusPage() {
  return (
    <ProtectedRoute requiredRoles={["SUPER_ADMIN"]}>
      <SystemStatusContent />
    </ProtectedRoute>
  );
}
