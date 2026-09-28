export interface PulseAssistMetricEvidence {
  metric_name: string;
  observed_value: string;
  source_entity: string;
  timestamp?: string | null;
}

export interface PulseAssistCitation {
  chunk_id: string;
  document_code: string;
  document_title: string;
  section_title?: string | null;
  page_number?: number | null;
  snippet: string;
  relevance_score: number;
}

export interface CitationDetail {
  citation_id: string;
  document_code: string;
  document_title: string;
  chunk_index: number;
  content_snippet: string;
  verified: boolean;
  section_title?: string | null;
  effective_from?: string | null;
  effective_to?: string | null;
}

export interface StudentMetricsCardData {
  attendance_pct?: number | null;
  cgpa?: number | null;
  spi_tier?: string | null;
  as_of_date: string;
  disclaimer: string;
}

export interface PulseAssistQueryRequest {
  query: string;
  student_id?: string | null;
  include_student_metrics?: boolean;
  institution_id?: string | null;
  // Backward compatibility alias:
  question?: string;
  conversation_id?: string | null;
}

export interface PulseAssistQueryResponse {
  query: string;
  response: string;
  citations: PulseAssistCitation[];
  ground_truth_metrics?: PulseAssistMetricEvidence[];
  verified_data_included?: boolean;
  tokens_used?: number;
  latency_ms?: number;
  ai_provider?: string;
  model_name?: string;
  // Convenience client fields:
  answer?: string;
  conversation_id?: string;
  metrics?: StudentMetricsCardData | null;
  disclaimer?: string;
}

export interface PulseAssistMessageDetail {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  citations: CitationDetail[];
}

export interface PulseAssistConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface PulseAssistConversationDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: PulseAssistMessageDetail[];
}

export interface KnowledgeDocument {
  id: string;
  institution_id: string;
  document_code: string;
  title: string;
  version: number;
  category: string;
  status: "DRAFT" | "PUBLISHED" | "ARCHIVED";
  target_audience: string;
  effective_from?: string | null;
  effective_to?: string | null;
  created_at: string;
  published_at?: string | null;
  archived_at?: string | null;
}

export interface KnowledgeDocumentCreate {
  document_code: string;
  title: string;
  category: string;
  target_audience?: string;
  content_text: string;
}

export interface DocumentPublishRequest {
  effective_from: string;
  effective_to?: string | null;
}

export interface AIInteractionLog {
  id: string;
  user_id: string;
  student_context_id?: string | null;
  interaction_type: string;
  query_text: string;
  response_text: string;
  chunks_cited_ids?: string[] | null;
  verified_data_included?: boolean;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  latency_ms?: number | null;
  ai_provider?: string;
  model_name?: string;
  created_at: string;
}
