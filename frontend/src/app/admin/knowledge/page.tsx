"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { RingBackground } from "@/components/ui/RingBackground";
import { api, ApiError } from "@/lib/api/client";
import { KnowledgeDocument, KnowledgeDocumentCreate, DocumentPublishRequest } from "@/types/pulseassist";
import {
  BookOpen,
  Plus,
  Calendar,
  CheckCircle2,
  Archive,
  ArrowLeft,
  AlertCircle,
  FileText,
  Clock,
  ShieldCheck,
  Layers,
  Lock,
} from "lucide-react";

export default function AdminKnowledgePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Create doc modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<KnowledgeDocumentCreate>({
    document_code: "",
    title: "",
    category: "ACADEMIC",
    target_audience: "ALL",
    content_text: "",
  });
  const [creating, setCreating] = useState(false);

  // Publish modal state
  const [isPublishOpen, setIsPublishOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);
  const [publishForm, setPublishForm] = useState<DocumentPublishRequest>({
    effective_from: new Date().toISOString().split("T")[0],
    effective_to: "",
  });
  const [publishing, setPublishing] = useState(false);

  // Archive modal state
  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [archiving, setArchiving] = useState(false);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const docs = await api.getKnowledgeDocuments();
      setDocuments(docs);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load knowledge documents");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleCreateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.document_code.trim() || !createForm.title.trim() || !createForm.content_text.trim()) {
      return;
    }

    try {
      setCreating(true);
      setError(null);
      await api.createKnowledgeDocument(createForm);
      setSuccessMsg(`Document ${createForm.document_code} created successfully as DRAFT.`);
      setIsCreateOpen(false);
      setCreateForm({
        document_code: "",
        title: "",
        category: "ACADEMIC",
        target_audience: "ALL",
        content_text: "",
      });
      await fetchDocuments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to create document.");
      }
    } finally {
      setCreating(false);
    }
  };

  const handlePublishDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc || !publishForm.effective_from) return;

    try {
      setPublishing(true);
      setError(null);
      await api.publishKnowledgeDocument(selectedDoc.id, {
        effective_from: publishForm.effective_from,
        effective_to: publishForm.effective_to?.trim() || null,
      });
      setSuccessMsg(`Document ${selectedDoc.document_code} (v${selectedDoc.version}) published successfully.`);
      setIsPublishOpen(false);
      setSelectedDoc(null);
      await fetchDocuments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to publish document.");
      }
    } finally {
      setPublishing(false);
    }
  };

  const handleArchiveDocument = async () => {
    if (!selectedDoc) return;

    try {
      setArchiving(true);
      setError(null);
      await api.archiveKnowledgeDocument(selectedDoc.id);
      setSuccessMsg(`Document ${selectedDoc.document_code} archived.`);
      setIsArchiveOpen(false);
      setSelectedDoc(null);
      await fetchDocuments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to archive document.");
      }
    } finally {
      setArchiving(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PUBLISHED":
        return <Badge variant="success">PUBLISHED</Badge>;
      case "DRAFT":
        return <Badge variant="warning">DRAFT</Badge>;
      case "ARCHIVED":
        return <Badge variant="neutral">ARCHIVED</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <ProtectedRoute requiredRoles={["ADMIN", "SUPER_ADMIN"]}>
      <div className="space-y-6" data-testid="admin-knowledge-page">
        {/* Navigation & Header */}
        <div className="flex items-center justify-between">
          <Link href="/admin">
            <Button variant="ghost" size="sm" className="text-xs space-x-1.5 text-surface-400 hover:text-white hover:bg-white/5">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Administration</span>
            </Button>
          </Link>

          <Button
            size="sm"
            onClick={() => setIsCreateOpen(true)}
            className="text-xs space-x-1.5 bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
            data-testid="create-document-btn"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Knowledge Document</span>
          </Button>
        </div>

        {/* Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0D1117] p-6 shadow-sm">
          <RingBackground variant="card" />
          <div className="relative z-10 space-y-1">
            <div className="flex items-center space-x-2">
              <Badge variant="primary">POLICY REGISTRY</Badge>
              <Badge variant="success">INSTITUTIONAL KNOWLEDGE</Badge>
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-display">
              Institutional Policy &amp; Knowledge Repository
            </h1>
            <p className="text-xs md:text-sm text-surface-400 max-w-3xl">
              Manage authoritative campus policy documents, versioning, and effective timelines. Ingested documents are chunked and vectorized for grounded retrieval in PulseAssist.
            </p>
          </div>
        </div>

        {/* Notifications */}
        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-400 flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-400 flex items-center space-x-3">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Documents Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-white/10">
            <div>
              <CardTitle className="text-base text-white font-display">Institutional Knowledge Documents</CardTitle>
              <CardDescription className="text-xs text-surface-400">
                Authoritative policies ingested for PulseAssist RAG grounding.
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2 text-xs text-surface-400">
              <ShieldCheck className="h-4 w-4 text-[#FF9A3D]" />
              <span>Immutable once published</span>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <p className="text-xs text-surface-400 py-8 text-center">Loading knowledge documents...</p>
            ) : documents.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={BookOpen}
                  title="No Knowledge Documents Ingested"
                  description="Create and publish your first institutional policy document to empower PulseAssist."
                  actionText="Ingest Document"
                  onAction={() => setIsCreateOpen(true)}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse" data-testid="documents-table">
                  <thead>
                    <tr className="border-b border-white/10 bg-[#111722] text-surface-400 font-mono text-[11px] uppercase tracking-wider">
                      <th className="py-2.5 px-3 font-semibold">Code / Version</th>
                      <th className="py-2.5 px-3 font-semibold">Title</th>
                      <th className="py-2.5 px-3 font-semibold">Category</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                      <th className="py-2.5 px-3 font-semibold">Effective Window</th>
                      <th className="py-2.5 px-3 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-white/[0.02] transition-colors" data-testid={`doc-row-${doc.document_code}`}>
                        <td className="py-3 px-3">
                          <div className="font-mono font-bold text-[#FF9A3D]">
                            {doc.document_code}
                          </div>
                          <span className="text-[10px] text-surface-400">Version {doc.version}</span>
                        </td>
                        <td className="py-3 px-3 font-medium text-white max-w-xs truncate">
                          {doc.title}
                        </td>
                        <td className="py-3 px-3">
                          <Badge variant="neutral" className="text-[10px]">
                            {doc.category}
                          </Badge>
                        </td>
                        <td className="py-3 px-3">{getStatusBadge(doc.status)}</td>
                        <td className="py-3 px-3 text-surface-400 text-[11px]">
                          {doc.effective_from ? (
                            <div className="flex items-center space-x-1">
                              <Calendar className="h-3 w-3 text-surface-500" />
                              <span>
                                {doc.effective_from} → {doc.effective_to || "Ongoing"}
                              </span>
                            </div>
                          ) : (
                            <span className="text-surface-500 italic">Not scheduled</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-right space-x-1.5">
                          {doc.status === "DRAFT" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedDoc(doc);
                                setIsPublishOpen(true);
                              }}
                              className="text-[11px] text-[#FF9A3D] border-[#FF7A18]/30 hover:bg-[#FF7A18]/10"
                              data-testid={`publish-btn-${doc.document_code}`}
                            >
                              Publish
                            </Button>
                          )}
                          {doc.status === "PUBLISHED" && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setSelectedDoc(doc);
                                setIsArchiveOpen(true);
                              }}
                              className="text-[11px] text-rose-400 hover:bg-rose-500/10"
                              data-testid={`archive-btn-${doc.document_code}`}
                            >
                              Archive
                            </Button>
                          )}
                          {doc.status === "ARCHIVED" && (
                            <span className="text-[11px] text-surface-500 italic">Archived</span>
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

        {/* Modal: Create Knowledge Document */}
        <Modal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          title="Ingest Institutional Knowledge Document"
          description="Create a draft policy document. Text will be chunked and indexed automatically upon publication."
          maxWidth="lg"
        >
          <form onSubmit={handleCreateDocument} className="space-y-4 text-xs" data-testid="create-document-form">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-medium text-surface-300 mb-1">
                  Document Code (Unique)
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. POL-ATT-001"
                  value={createForm.document_code}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, document_code: e.target.value.toUpperCase() })
                  }
                  className="w-full px-3 py-2 border rounded-lg bg-[#111722] border-white/10 text-white placeholder-surface-500 text-xs font-mono focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                  data-testid="doc-code-input"
                />
              </div>

              <div>
                <label className="block font-medium text-surface-300 mb-1">
                  Category
                </label>
                <select
                  value={createForm.category}
                  onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg bg-[#111722] border-white/10 text-white text-xs focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                  data-testid="doc-category-select"
                >
                  <option value="ACADEMIC" className="bg-[#111722] text-white">ACADEMIC</option>
                  <option value="ATTENDANCE" className="bg-[#111722] text-white">ATTENDANCE</option>
                  <option value="EXAMINATION" className="bg-[#111722] text-white">EXAMINATION</option>
                  <option value="CONDUCT" className="bg-[#111722] text-white">CONDUCT</option>
                  <option value="FINANCIAL" className="bg-[#111722] text-white">FINANCIAL</option>
                  <option value="GENERAL" className="bg-[#111722] text-white">GENERAL</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Document Title
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Standard Institutional Attendance & Minimum Floor Policy"
                value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg bg-[#111722] border-white/10 text-white placeholder-surface-500 text-xs focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                data-testid="doc-title-input"
              />
            </div>

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Document Content (Markdown / Text)
              </label>
              <textarea
                required
                rows={8}
                placeholder="Paste the official policy text here. Use headers (# Section) to ensure optimal semantic chunking..."
                value={createForm.content_text}
                onChange={(e) => setCreateForm({ ...createForm, content_text: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg bg-[#111722] border-white/10 text-white placeholder-surface-500 text-xs font-mono focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                data-testid="doc-content-textarea"
              />
              <p className="text-[10px] text-surface-400 mt-1">
                PulseAssist will parse semantic chunks (target ~1800 characters, respecting section boundaries) and generate dense embeddings.
              </p>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)} className="border-white/10 text-surface-300 hover:bg-white/5 hover:text-white">
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={creating}
                className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                data-testid="submit-create-doc-btn"
              >
                {creating ? "Creating..." : "Save Draft"}
              </Button>
            </div>
          </form>
        </Modal>

        {/* Modal: Publish Document */}
        <Modal
          isOpen={isPublishOpen}
          onClose={() => setIsPublishOpen(false)}
          title={`Publish Document: ${selectedDoc?.document_code}`}
          description="Publishing makes the document immutable and activates it for RAG retrieval during the specified effective window."
          maxWidth="md"
        >
          <form onSubmit={handlePublishDocument} className="space-y-4 text-xs" data-testid="publish-form">
            <div className="p-3 rounded-lg bg-[#111722] border border-white/10">
              <p className="font-semibold text-white">{selectedDoc?.title}</p>
              <p className="text-[11px] text-surface-400 mt-0.5">Version {selectedDoc?.version}</p>
            </div>

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Effective From Date (Mandatory)
              </label>
              <input
                type="date"
                required
                value={publishForm.effective_from}
                onChange={(e) =>
                  setPublishForm({ ...publishForm, effective_from: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg bg-[#111722] border-white/10 text-white text-xs focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                data-testid="publish-from-input"
              />
            </div>

            <div>
              <label className="block font-medium text-surface-300 mb-1">
                Effective To Date (Optional, leave blank for ongoing)
              </label>
              <input
                type="date"
                value={publishForm.effective_to || ""}
                onChange={(e) =>
                  setPublishForm({ ...publishForm, effective_to: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg bg-[#111722] border-white/10 text-white text-xs focus:border-[#FF7A18]/50 focus:ring-1 focus:ring-[#FF7A18]/30"
                data-testid="publish-to-input"
              />
            </div>

            <div className="p-2.5 rounded-lg bg-[#111722] border border-amber-500/20 text-[10px] text-amber-300/90 flex items-start space-x-2">
              <Lock className="h-3.5 w-3.5 flex-shrink-0 mt-0.5 text-amber-400" />
              <span>
                Once published, document text and metadata become strictly immutable. Overlapping effective date ranges for the same document code are prevented by database constraints.
              </span>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsPublishOpen(false)} className="border-white/10 text-surface-300 hover:bg-white/5 hover:text-white">
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={publishing}
                className="bg-gradient-to-r from-[#FF7A18] to-[#FF9A3D] text-white hover:opacity-90 border-0"
                data-testid="confirm-publish-btn"
              >
                {publishing ? "Publishing & Vectorizing..." : "Confirm Publication"}
              </Button>
            </div>
          </form>
        </Modal>

        {/* Modal: Archive Document */}
        <Modal
          isOpen={isArchiveOpen}
          onClose={() => setIsArchiveOpen(false)}
          title={`Archive Document: ${selectedDoc?.document_code}`}
          description="Archiving marks the document inactive and excludes its chunks from future RAG retrieval."
          maxWidth="sm"
        >
          <div className="space-y-4 text-xs" data-testid="archive-dialog">
            <p className="text-surface-300">
              Are you sure you want to archive <strong className="text-white">{selectedDoc?.document_code}</strong> ({selectedDoc?.title})?
            </p>

            <div className="flex justify-end space-x-2 pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsArchiveOpen(false)} className="border-white/10 text-surface-300 hover:bg-white/5 hover:text-white">
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={handleArchiveDocument}
                disabled={archiving}
                className="bg-rose-600 hover:bg-rose-700 text-white"
                data-testid="confirm-archive-btn"
              >
                {archiving ? "Archiving..." : "Archive Document"}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
