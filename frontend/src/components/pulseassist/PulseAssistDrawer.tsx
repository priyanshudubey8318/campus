"use client";

import React, { useState, useEffect, useRef } from "react";
import { api, ApiError } from "@/lib/api/client";
import {
  PulseAssistQueryResponse,
  CitationDetail,
  StudentMetricsCardData,
} from "@/types/pulseassist";
import { CitationPill } from "./CitationPill";
import { GroundTruthCard } from "./GroundTruthCard";
import { WhySeeingModal } from "./WhySeeingModal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  Bot,
  X,
  Send,
  Sparkles,
  HelpCircle,
  RotateCcw,
  AlertCircle,
  ShieldCheck,
  ChevronDown,
  Loader2,
  Clock,
} from "lucide-react";

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationDetail[];
  metrics?: StudentMetricsCardData | null;
  disclaimer?: string;
  timestamp: string;
}

const SUGGESTED_QUERIES = [
  "What is the minimum attendance required to write final exams?",
  "What are the rules regarding academic probation and advisory?",
  "How do I submit an assignment for evaluation?",
  "What is my current attendance percentage and academic standing?",
];

export function PulseAssistDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [rateLimitTimer, setRateLimitTimer] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<CitationDetail | null>(null);
  const [isWhyModalOpen, setIsWhyModalOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto scroll to latest message
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  // Support opening via global custom event (e.g. from sidebar or buttons)
  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener("open-pulseassist", handleOpen);
    return () => window.removeEventListener("open-pulseassist", handleOpen);
  }, []);

  // Rate limit countdown effect
  useEffect(() => {
    if (rateLimitTimer === null || rateLimitTimer <= 0) return;
    const interval = setInterval(() => {
      setRateLimitTimer((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval);
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [rateLimitTimer]);

  const handleOpenWhySeeing = (citation: CitationDetail) => {
    setActiveCitation(citation);
    setIsWhyModalOpen(true);
  };

  const handleResetConversation = () => {
    setConversationId(null);
    setMessages([]);
    setError(null);
  };

  const handleSubmit = async (e?: React.FormEvent, customQuestion?: string) => {
    if (e) e.preventDefault();
    const questionText = (customQuestion || query).trim();
    if (!questionText || isLoading || rateLimitTimer !== null) return;

    setError(null);
    const userMsg: MessageItem = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: questionText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setIsLoading(true);

    try {
      const response: PulseAssistQueryResponse = await api.pulseAssistQuery({
        query: questionText,
        include_student_metrics: true,
      });

      const mappedCitations: CitationDetail[] = (response.citations || []).map((c, idx) => ({
        citation_id: c.chunk_id || `cit_${idx}`,
        document_code: c.document_code,
        document_title: c.document_title,
        chunk_index: idx,
        content_snippet: c.snippet,
        verified: true,
        section_title: c.section_title,
      }));

      let mappedMetrics: StudentMetricsCardData | null = response.metrics || null;
      if (!mappedMetrics && response.ground_truth_metrics && response.ground_truth_metrics.length > 0) {
        let attendance_pct: number | undefined;
        let cgpa: number | undefined;
        let spi_tier: string | undefined;
        let as_of_date = new Date().toISOString().split("T")[0];

        for (const m of response.ground_truth_metrics) {
          const name = m.metric_name.toLowerCase();
          if (name.includes("attendance")) {
            const val = parseFloat(m.observed_value.replace("%", ""));
            if (!isNaN(val)) attendance_pct = val;
          } else if (name.includes("cgpa") || name.includes("gpa")) {
            const val = parseFloat(m.observed_value);
            if (!isNaN(val)) cgpa = val;
          } else if (name.includes("tier") || name.includes("spi")) {
            spi_tier = m.observed_value;
          }
          if (m.timestamp) {
            as_of_date = new Date(m.timestamp).toISOString().split("T")[0];
          }
        }

        mappedMetrics = {
          attendance_pct,
          cgpa,
          spi_tier,
          as_of_date,
          disclaimer: "Verified ground-truth data from registrar/attendance systems. Not an AI estimate.",
        };
      }

      const answerText = response.response || response.answer || "No response received.";
      const assistantMsg: MessageItem = {
        id: `asst_${Date.now()}`,
        role: "assistant",
        content: answerText,
        citations: mappedCitations,
        metrics: mappedMetrics,
        disclaimer: response.disclaimer || "Verified institutional policy answer grounded in official university documents.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setRateLimitTimer(60);
          setError("Rate limit reached. Please wait before submitting another question.");
        } else {
          setError(err.message || "PulseAssist could not process your query.");
        }
      } else {
        setError("Network error connecting to PulseAssist. Please retry.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="flex items-center space-x-2 px-4 py-3 rounded-full bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold shadow-[0_4px_24px_rgba(255,122,24,0.35)] hover:-translate-y-0.5 transition-all duration-180 focus:outline-none focus:ring-2 focus:ring-[#FF7A18] focus:ring-offset-2 focus:ring-offset-[#07090D]"
          data-testid="pulseassist-trigger-btn"
          aria-label="Ask PulseAssist Institutional Policy Assistant"
        >
          <Bot className="h-5 w-5 stroke-[2.5]" />
          <span className="text-xs font-bold tracking-wide">
            Ask CampusPulse <span className="opacity-80 font-normal text-[11px] font-mono">(Ask PulseAssist)</span>
          </span>
          <span className="flex h-2 w-2 rounded-full bg-[#07090D] animate-pulse" />
        </button>
      </div>

      {/* Slide-out Drawer Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-[#07090D]/80 backdrop-blur-sm transition-opacity"
          onClick={() => setIsOpen(false)}
          data-testid="pulseassist-overlay"
        />
      )}

      {/* Slide-out Drawer Container */}
      <aside
        className={`fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] lg:w-[520px] bg-[#0D1117] shadow-2xl flex flex-col transform transition-transform duration-260 ease-in-out border-l border-white/[0.08] ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
        data-testid="pulseassist-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="PulseAssist Policy Inquiries"
      >
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between bg-[#111722]">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-[#151B24] border border-white/10 text-[#FF7A18]">
              <Bot className="h-5 w-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-display text-sm font-bold text-[#F5F7FA]">
                  PulseAssist
                </h3>
                <Badge variant="primary" className="text-[10px] px-1.5 py-0 font-mono">
                  RAG Subsystem
                </Badge>
              </div>
              <p className="text-[11px] font-mono text-[#A7AFBD]">
                Institutional Policy &amp; Academic Inquiries
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetConversation}
                title="New Policy Conversation"
                className="text-xs text-[#A7AFBD] hover:text-[#F5F7FA]"
                data-testid="pulseassist-new-chat-btn"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="text-[#A7AFBD] hover:text-[#F5F7FA]"
              data-testid="pulseassist-close-btn"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Informational Subheader */}
        <div className="px-5 py-2 bg-[#151B24] border-b border-white/[0.06] flex items-center justify-between text-[11px] text-[#A7AFBD]">
          <div className="flex items-center space-x-1.5 font-mono">
            <ShieldCheck className="h-3.5 w-3.5 text-[#FF7A18]" />
            <span>Strictly grounded in approved institutional policy documents</span>
          </div>
        </div>

        {/* Message Thread Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4" data-testid="pulseassist-messages">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center space-y-4 px-4 my-auto">
              <div className="p-3.5 rounded-full bg-[#151B24] border border-white/10 text-[#FF7A18]">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h4 className="font-display text-sm font-semibold text-[#F5F7FA]">
                  Campus Knowledge Assistant
                </h4>
                <p className="text-xs text-[#A7AFBD] max-w-sm">
                  Inquire about campus academic rules, minimum attendance requirements, examination policies, or view your official verified records.
                </p>
              </div>

              {/* Quick suggestions */}
              <div className="w-full space-y-2 pt-2">
                <span className="text-[11px] font-mono font-medium uppercase tracking-wider text-[#6F7785] block text-left">
                  Suggested Policy Questions
                </span>
                <div className="space-y-1.5 text-left">
                  {SUGGESTED_QUERIES.map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSubmit(undefined, q)}
                      className="w-full text-left p-2.5 rounded-xl border border-white/[0.08] hover:border-[#FF7A18]/40 bg-[#111722] hover:bg-[#151B24] text-xs text-[#F5F7FA] hover:text-[#FF9A3D] transition shadow-sm flex items-center justify-between group"
                      data-testid={`suggested-query-${idx}`}
                    >
                      <span className="line-clamp-1">{q}</span>
                      <Send className="h-3 w-3 text-[#6F7785] group-hover:text-[#FF7A18] opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
                data-testid={`message-${msg.role}`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl p-4 text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[#FF7A18] text-[#07090D] font-medium rounded-br-none"
                      : "bg-[#111722] text-[#F5F7FA] rounded-bl-none border border-white/[0.08]"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Ground Truth Personal Academic Metrics Card */}
                  {msg.metrics && <GroundTruthCard metrics={msg.metrics} />}

                  {/* Grounded Citation Badges */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-white/[0.08]" data-testid="citations-container">
                      <span className="text-[10px] uppercase font-mono tracking-wide font-medium text-[#A7AFBD] block mb-1">
                        Verified Policy Citations
                      </span>
                      <div className="flex flex-wrap items-center">
                        {msg.citations.map((c) => (
                          <CitationPill
                            key={c.citation_id}
                            citation={c}
                            onOpenWhySeeing={handleOpenWhySeeing}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Message Disclaimer */}
                  {msg.disclaimer && (
                    <p className="mt-2 text-[9px] text-[#6F7785] italic">
                      {msg.disclaimer}
                    </p>
                  )}
                </div>
                <span className="text-[9px] text-[#6F7785] font-mono mt-1 px-1">{msg.timestamp}</span>
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex items-center space-x-2 text-xs text-[#A7AFBD] p-3 rounded-xl bg-[#111722] border border-white/10 w-fit">
              <Loader2 className="h-4 w-4 animate-spin text-[#FF7A18]" />
              <span className="font-mono">Retrieving institutional policies &amp; verifying citations...</span>
            </div>
          )}

          {/* Rate limit banner */}
          {rateLimitTimer !== null && (
            <div
              className="p-3 rounded-xl border border-[#FFB020]/30 bg-[#FFB020]/10 text-[#FFB020] text-xs flex items-center space-x-2"
              data-testid="rate-limit-banner"
            >
              <Clock className="h-4 w-4 flex-shrink-0 text-[#FFB020]" />
              <span>
                Rate limit active. Please wait{" "}
                <strong className="font-mono">{rateLimitTimer}s</strong> before submitting your next question.
              </span>
            </div>
          )}

          {/* Error banner */}
          {error && !rateLimitTimer && (
            <div className="p-3 rounded-xl border border-[#FF4D4D]/30 bg-[#FF4D4D]/10 text-[#FF4D4D] text-xs flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-white/[0.08] bg-[#0D1117]">
          <form onSubmit={(e) => handleSubmit(e)} className="flex items-center space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                rateLimitTimer !== null
                  ? `Please wait ${rateLimitTimer}s...`
                  : "Ask a question about campus policies or records..."
              }
              disabled={isLoading || rateLimitTimer !== null}
              className="flex-1 text-xs px-3.5 py-2.5 rounded-lg border border-white/10 bg-[#151B24] text-[#F5F7FA] placeholder-[#6F7785] focus:outline-none focus:ring-1 focus:ring-[#FF7A18] focus:border-[#FF7A18] disabled:opacity-50"
              data-testid="pulseassist-query-input"
            />
            <Button
              type="submit"
              size="sm"
              disabled={!query.trim() || isLoading || rateLimitTimer !== null}
              className="px-3.5 py-2.5 bg-[#FF7A18] hover:bg-[#FF9A3D] text-[#07090D] font-semibold"
              data-testid="pulseassist-send-btn"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>

          {/* Institutional Compliance Disclaimer Footer */}
          <div className="mt-2.5 text-center text-[10px] text-[#6F7785] font-mono">
            PulseAssist answers are grounded in official institutional documents. Not an academic intervention or clinical tool.
          </div>
        </div>
      </aside>

      {/* "Why am I seeing this?" Explainability Modal */}
      <WhySeeingModal
        citation={activeCitation}
        isOpen={isWhyModalOpen}
        onClose={() => setIsWhyModalOpen(false)}
      />
    </>
  );
}
