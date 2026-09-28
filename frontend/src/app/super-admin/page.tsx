"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/auth-context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatsCard } from "@/components/ui/StatsCard";
import { CardSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import { HealthResponse } from "@/types/health";
import { AIInteractionLog } from "@/types/pulseassist";
import {
  ShieldAlert,
  ShieldCheck,
  Database,
  Server,
  FileText,
  Activity,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  Lock,
  Clock,
  Terminal,
  Layers,
  BookOpen,
  Briefcase,
  Users,
} from "lucide-react";

export default function SuperAdminPortalPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AIInteractionLog[]>([]);
  const [casesCount, setCasesCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSuperAdminData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [healthData, logsData, casesData] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getPulseAssistAuditLogs({ limit: 50 }).catch(() => []),
        api.getCases({ limit: 100 }).catch(() => []),
      ]);

      setHealth(healthData);
      setAuditLogs(logsData);
      setCasesCount(casesData.length);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load root governance telemetry");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSuperAdminData();
  }, [loadSuperAdminData]);

  return (
    <ProtectedRoute requiredRoles={["SUPER_ADMIN"]}>
      <div className="space-y-8" data-testid="super-admin-portal">
        {/* Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 md:p-8 shadow-2xl">
          <RingBackground variant="hero" className="opacity-40" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="danger">ROOT AUTHORITY</Badge>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono border border-[#FF7A18]/20 bg-[#FF7A18]/10 text-[#FF9A3D]">
                  SUPER_ADMIN
                </span>
                <div className="flex items-center space-x-1 text-xs text-[#FF9A3D] font-medium font-mono">
                  <Lock className="h-3.5 w-3.5" />
                  <span>Unrestricted Institutional Oversight</span>
                </div>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold font-display tracking-tight text-white">
                Institutional Root Governance &amp; Security Audit
              </h1>
              <p className="text-xs md:text-sm text-surface-400 max-w-2xl leading-relaxed">
                Welcome, {user?.full_name}. Oversee multi-tenant academic telemetry, inspect AI interaction audit trails,
                and enforce strict compliance policies across all campus departments.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadSuperAdminData()}
                disabled={loading}
                className="text-xs border-white/10 hover:border-[#FF7A18]/40 hover:text-white"
                data-testid="refresh-superadmin-btn"
              >
                <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin text-[#FF7A18]" : ""}`} />
                Refresh
              </Button>
              <Link href="/system-status">
                <Button size="sm" variant="outline" className="text-xs space-x-1.5 border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white">
                  <Activity className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Live Telemetry</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-950/30 p-4 text-xs text-red-400 flex items-center space-x-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 4 KPIs */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              title="System Engine Health"
              value={health?.status === "healthy" ? "100% Operational" : "Connecting"}
              subtitle={`Uptime: ${health ? Math.round(health.uptime_seconds) : 0}s`}
              icon={Server}
              iconColor="text-emerald-400"
              badge={{
                text: health?.status === "healthy" ? "Healthy Engine" : "Connecting",
                variant: health?.status === "healthy" ? "success" : "neutral",
              }}
              testId="kpi-superadmin-health"
            />
            <StatsCard
              title="Database Authority"
              value={health?.database?.connected ? "Connected" : "Reconnecting"}
              subtitle={health ? `${health.database.dialect} 17.9` : "PostgreSQL"}
              icon={Database}
              iconColor="text-[#FF9A3D]"
              badge={{ text: "ACID Safe", variant: "primary" }}
              testId="kpi-superadmin-db"
            />
            <StatsCard
              title="Support Cases"
              value={casesCount}
              subtitle="Institutional total"
              icon={Briefcase}
              iconColor="text-blue-400"
              badge={{ text: "Active", variant: "neutral" }}
              testId="kpi-superadmin-cases"
            />
            <StatsCard
              title="Security Audit Records"
              value={auditLogs.length}
              subtitle="AI queries tracked"
              icon={FileText}
              iconColor="text-[#FFB020]"
              badge={{ text: "Audit Active", variant: "warning" }}
              testId="kpi-superadmin-logs"
            />
          </div>
        )}

        {/* Governance Quick Action Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-white/10 bg-[#0D1117] hover-lift-card transition-all">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-[#FF7A18]/10 p-2 text-[#FF9A3D]">
                  <BookOpen className="h-5 w-5" />
                </div>
                <Badge variant="success">ACADEMICS</Badge>
              </div>
              <CardTitle className="text-sm font-semibold text-white font-display mt-3">Catalog &amp; Offerings</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Inspect courses, degree programs, departments, and enrollment registries.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/admin/academic">
                <Button size="sm" variant="outline" className="w-full justify-between text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white">
                  <span>Open Academic Management</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-[#0D1117] hover-lift-card transition-all">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-teal-500/10 p-2 text-teal-400">
                  <Layers className="h-5 w-5" />
                </div>
                <Badge variant="primary">KNOWLEDGE</Badge>
              </div>
              <CardTitle className="text-sm font-semibold text-white font-display mt-3">PulseAssist RAG Documents</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Manage policy document drafts, schedule publication, and inspect vector chunks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/admin/knowledge">
                <Button size="sm" variant="outline" className="w-full justify-between text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white">
                  <span>Manage Knowledge Base</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-[#0D1117] hover-lift-card transition-all">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400">
                  <ShieldAlert className="h-5 w-5" />
                </div>
                <Badge variant="danger">GRIEVANCES</Badge>
              </div>
              <CardTitle className="text-sm font-semibold text-white font-display mt-3">PulseRecord Grievances &amp; Leaves</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Adjudicate institutional complaints, resolve appeals, and review leave records.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/admin/records">
                <Button size="sm" variant="outline" className="w-full justify-between text-xs border-white/10 hover:border-[#FF7A18]/40 text-surface-200 hover:text-white">
                  <span>Open Records Console</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* AI Interaction Audit Trail */}
        <Card className="border-white/10 bg-[#0D1117] overflow-hidden">
          <CardHeader className="pb-3 border-b border-white/10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-base text-white font-display flex items-center gap-2">
                  <FileText className="h-4 w-4 text-[#FF7A18]" />
                  <span>PulseAssist Interaction &amp; RAG Audit Trail</span>
                </CardTitle>
                <CardDescription className="text-xs text-surface-400">
                  Immutable audit records tracking user queries, cited document chunks, latency, and verified data.
                </CardDescription>
              </div>
              <Badge variant="neutral" className="text-[10px] font-mono">
                {auditLogs.length} LOGGED SESSIONS
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-3">
                <div className="h-10 bg-[#111722] rounded animate-pulse" />
                <div className="h-10 bg-[#111722] rounded animate-pulse" />
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={Clock}
                  title="No Audit Records Yet"
                  description="Interactive questions submitted through PulseAssist will appear here with token metrics and cited policy chunks."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#111722] text-surface-400 border-b border-white/10 font-mono uppercase text-xs">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Timestamp</th>
                      <th className="py-3 px-4 font-semibold">User</th>
                      <th className="py-3 px-4 font-semibold">Query</th>
                      <th className="py-3 px-4 font-semibold">AI Model</th>
                      <th className="py-3 px-4 font-semibold">Latency</th>
                      <th className="py-3 px-4 font-semibold">Citations</th>
                      <th className="py-3 px-4 font-semibold">Grounding</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {auditLogs.map((log) => (
                      <tr
                        key={log.id}
                        className="hover:bg-white/[0.02] transition"
                      >
                        <td className="py-3 px-4 text-surface-400 text-[11px] whitespace-nowrap font-mono">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-surface-300">
                          {log.user_id.slice(0, 8)}...
                        </td>
                        <td className="py-3 px-4 max-w-xs truncate text-white font-medium">
                          {log.query_text}
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className="text-[10px] font-mono border-white/10 text-surface-300">
                            {log.model_name || log.ai_provider || "mock"}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-surface-300 font-mono text-[11px]">
                          {log.latency_ms !== null && log.latency_ms !== undefined ? `${log.latency_ms}ms` : "-"}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-semibold text-emerald-400 font-mono">
                            {log.chunks_cited_ids?.length || 0} chunks
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {log.verified_data_included ? (
                            <Badge variant="success" className="text-[10px]">VERIFIED</Badge>
                          ) : (
                            <Badge variant="neutral" className="text-[10px]">POLICY ONLY</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
