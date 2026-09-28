import { HealthResponse } from "@/types/health";
import {
  User,
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  MessageResponse,
} from "@/types/auth";

const RAW_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE_URL = RAW_BASE.endsWith("/api/v1")
  ? RAW_BASE
  : `${RAW_BASE.replace(/\/+$/, "")}/api/v1`;

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let inMemoryToken: string | null = null;

export function setClientAuthToken(token: string | null): void {
  inMemoryToken = token;
}

export function getClientAuthToken(): string | null {
  return inMemoryToken;
}

export async function fetchFromApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    ...(typeof FormData !== "undefined" && options?.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    ...(options?.headers as Record<string, string> | undefined),
  };

  if (inMemoryToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${inMemoryToken}`;
  }

  try {
    const res = await fetch(url, {
      credentials: "include",
      headers,
      ...options,
    });

    if (!res.ok) {
      let errorBody: any;
      try {
        errorBody = await res.json();
      } catch {
        errorBody = { message: res.statusText };
      }

      const errorMessage =
        errorBody?.detail ||
        errorBody?.error?.message ||
        errorBody?.message ||
        "An API error occurred";

      throw new ApiError(res.status, errorMessage, errorBody);
    }

    return (await res.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      0,
      error instanceof Error ? error.message : "Network request failed"
    );
  }
}

export const api = {
  // Diagnostics & Health
  getHealth: () => fetchFromApi<HealthResponse>("/health"),
  getDatabaseHealth: () =>
    fetchFromApi<{ status: string; database: any }>("/health/db"),

  // Authentication & Identity
  register: (payload: RegisterPayload) =>
    fetchFromApi<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const data = await fetchFromApi<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (data.access_token) {
      setClientAuthToken(data.access_token);
    }
    return data;
  },

  logout: async (): Promise<MessageResponse> => {
    try {
      return await fetchFromApi<MessageResponse>("/auth/logout", {
        method: "POST",
      });
    } finally {
      setClientAuthToken(null);
    }
  },

  refreshSession: async (): Promise<TokenResponse> => {
    const data = await fetchFromApi<TokenResponse>("/auth/refresh", {
      method: "POST",
    });
    if (data.access_token) {
      setClientAuthToken(data.access_token);
    }
    return data;
  },

  getMe: () => fetchFromApi<User>("/auth/me"),

  // Academic Foundation
  getMyStudentProfile: () =>
    fetchFromApi<import("@/types/academic").StudentProfile>("/academic/student-profiles/me"),
  getStudentProfile: (id: string) =>
    fetchFromApi<import("@/types/academic").StudentProfile>(`/academic/student-profiles/${id}`),
  getMyFacultyProfile: () =>
    fetchFromApi<import("@/types/academic").FacultyProfile>("/academic/faculty-profiles/me"),
  getFacultyProfile: (id: string) =>
    fetchFromApi<import("@/types/academic").FacultyProfile>(`/academic/faculty-profiles/${id}`),
  getEnrollments: (params?: { student_id?: string; course_id?: string; term_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.student_id) q.set("student_id", params.student_id);
    if (params?.course_id) q.set("course_id", params.course_id);
    if (params?.term_id) q.set("term_id", params.term_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").Enrollment[]>(`/academic/enrollments${qs}`);
  },
  getFacultyAssignments: (params?: { faculty_id?: string; course_id?: string; term_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.faculty_id) q.set("faculty_id", params.faculty_id);
    if (params?.course_id) q.set("course_id", params.course_id);
    if (params?.term_id) q.set("term_id", params.term_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").FacultyCourseAssignment[]>(`/academic/faculty-assignments${qs}`);
  },
  getAttendanceRecords: (params?: { student_id?: string; course_id?: string; term_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.student_id) q.set("student_id", params.student_id);
    if (params?.course_id) q.set("course_id", params.course_id);
    if (params?.term_id) q.set("term_id", params.term_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").AttendanceRecord[]>(`/academic/attendance${qs}`);
  },
  getAttendanceSummary: (params?: { student_id?: string; course_id?: string; term_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.student_id) q.set("student_id", params.student_id);
    if (params?.course_id) q.set("course_id", params.course_id);
    if (params?.term_id) q.set("term_id", params.term_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").AttendanceSummary>(`/academic/attendance/summary${qs}`);
  },
  getAssignments: (params?: { course_id?: string; term_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.course_id) q.set("course_id", params.course_id);
    if (params?.term_id) q.set("term_id", params.term_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").Assignment[]>(`/academic/assignments${qs}`);
  },
  getAssignmentSubmissions: (assignmentId: string, studentId?: string) => {
    const q = new URLSearchParams();
    if (studentId) q.set("student_id", studentId);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").AssignmentSubmission[]>(`/academic/assignments/${assignmentId}/submissions${qs}`);
  },
  getAssessments: (params?: { course_id?: string; term_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.course_id) q.set("course_id", params.course_id);
    if (params?.term_id) q.set("term_id", params.term_id);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").Assessment[]>(`/academic/assessments${qs}`);
  },
  getAssessmentResults: (assessmentId: string, studentId?: string) => {
    const q = new URLSearchParams();
    if (studentId) q.set("student_id", studentId);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/academic").AssessmentResult[]>(`/academic/assessments/${assessmentId}/results${qs}`);
  },
  getCourses: () => fetchFromApi<import("@/types/academic").Course[]>("/academic/courses"),
  getDepartments: (institutionId?: string) => {
    const qs = institutionId ? `?institution_id=${institutionId}` : "";
    return fetchFromApi<import("@/types/academic").Department[]>(`/academic/departments${qs}`);
  },
  getTerms: (institutionId?: string) => {
    const qs = institutionId ? `?institution_id=${institutionId}` : "";
    return fetchFromApi<import("@/types/academic").AcademicTerm[]>(`/academic/terms${qs}`);
  },
  recordAttendance: (payload: import("@/types/academic").AttendanceRecordCreate) =>
    fetchFromApi<import("@/types/academic").AttendanceRecord>("/academic/attendance", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createAssignment: (payload: import("@/types/academic").AssignmentCreate) =>
    fetchFromApi<import("@/types/academic").Assignment>("/academic/assignments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitAssignment: (
    assignmentId: string,
    payload: import("@/types/academic").AssignmentSubmissionCreate
  ) =>
    fetchFromApi<import("@/types/academic").AssignmentSubmission>(
      `/academic/assignments/${assignmentId}/submit`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),
  gradeSubmission: (
    submissionId: string,
    payload: import("@/types/academic").SubmissionGradeRequest
  ) =>
    fetchFromApi<import("@/types/academic").AssignmentSubmission>(
      `/academic/submissions/${submissionId}/grade`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),
  createAssessment: (payload: import("@/types/academic").AssessmentCreate) =>
    fetchFromApi<import("@/types/academic").Assessment>("/academic/assessments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recordAssessmentResult: (
    assessmentId: string,
    payload: import("@/types/academic").AssessmentResultCreate
  ) =>
    fetchFromApi<import("@/types/academic").AssessmentResult>(
      `/academic/assessments/${assessmentId}/results`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),

  // PulseWatch Behavioral Monitoring Foundation (Deterministic)
  getPulseWatchSummary: (studentId: string, windowDays?: number) => {
    const qs = windowDays ? `?window_days=${windowDays}` : "";
    return fetchFromApi<import("@/types/pulsewatch").PulseWatchSummary>(
      `/pulsewatch/student/${studentId}/summary${qs}`
    );
  },
  getPulseWatchTimeline: (studentId: string, limit?: number) => {
    const qs = limit ? `?limit=${limit}` : "";
    return fetchFromApi<import("@/types/pulsewatch").BehaviorEvent[]>(
      `/pulsewatch/student/${studentId}/timeline${qs}`
    );
  },
  getPulseWatchSignals: (studentId: string, windowDays?: number) => {
    const qs = windowDays ? `?window_days=${windowDays}` : "";
    return fetchFromApi<import("@/types/pulsewatch").SignalEvidence[]>(
      `/pulsewatch/student/${studentId}/signals${qs}`
    );
  },
  getPulseWatchBaseline: (studentId: string) =>
    fetchFromApi<any[]>(`/pulsewatch/student/${studentId}/baseline`),
  evaluatePulseWatch: (studentId: string, windowDays?: number) => {
    const qs = windowDays ? `?window_days=${windowDays}` : "";
    return fetchFromApi<import("@/types/pulsewatch").BehaviorEvent>(
      `/pulsewatch/student/${studentId}/evaluate${qs}`,
      { method: "POST" }
    );
  },

  // PulseRisk Support Prioritization Subsystem (Deterministic)
  getPulseRiskCurrent: (studentId: string, windowDays?: number) => {
    const qs = windowDays ? `?window_days=${windowDays}` : "";
    return fetchFromApi<import("@/types/pulserisk").PulseRiskSummary>(
      `/pulserisk/student/${studentId}/current${qs}`
    );
  },
  getPulseRiskHistory: (studentId: string, limit?: number) => {
    const qs = limit ? `?limit=${limit}` : "";
    return fetchFromApi<import("@/types/pulserisk").StudentRiskSnapshot[]>(
      `/pulserisk/student/${studentId}/history${qs}`
    );
  },
  evaluatePulseRisk: (studentId: string, windowDays?: number) => {
    const qs = windowDays ? `?window_days=${windowDays}` : "";
    return fetchFromApi<import("@/types/pulserisk").StudentRiskSnapshot>(
      `/pulserisk/student/${studentId}/evaluate${qs}`,
      { method: "POST" }
    );
  },
  getCohortPriorities: (params?: {
    priorityTier?: string;
    primaryDriver?: string;
    page?: number;
    limit?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.priorityTier) query.set("priority_tier", params.priorityTier);
    if (params?.primaryDriver) query.set("primary_driver", params.primaryDriver);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.limit) query.set("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchFromApi<import("@/types/pulserisk").CohortPrioritiesPage>(
      `/pulserisk/cohort/priorities${qs}`
    );
  },
  getActiveRiskPolicy: () =>
    fetchFromApi<import("@/types/pulserisk").RiskPolicy>("/pulserisk/policies/active"),
  createRiskPolicy: (payload: Partial<import("@/types/pulserisk").RiskPolicy>) =>
    fetchFromApi<import("@/types/pulserisk").RiskPolicy>("/pulserisk/policies", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  activateRiskPolicy: (policyId: string) =>
    fetchFromApi<import("@/types/pulserisk").RiskPolicy>(
      `/pulserisk/policies/${policyId}/activate`,
      { method: "POST" }
    ),

  // PulseAssist Institutional RAG Subsystem
  pulseAssistQuery: (payload: import("@/types/pulseassist").PulseAssistQueryRequest) => {
    const bodyPayload = {
      query: payload.query || payload.question || "",
      student_id: payload.student_id ?? null,
      include_student_metrics: payload.include_student_metrics ?? true,
      institution_id: payload.institution_id ?? null,
    };
    return fetchFromApi<import("@/types/pulseassist").PulseAssistQueryResponse>(
      "/pulseassist/query",
      {
        method: "POST",
        body: JSON.stringify(bodyPayload),
      }
    );
  },
  getPulseAssistConversations: () =>
    fetchFromApi<import("@/types/pulseassist").PulseAssistConversationSummary[]>(
      "/pulseassist/conversations"
    ),
  getPulseAssistConversation: (conversationId: string) =>
    fetchFromApi<import("@/types/pulseassist").PulseAssistConversationDetail>(
      `/pulseassist/conversations/${conversationId}`
    ),
  getPulseAssistAuditLogs: (params?: { institutionId?: string; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.institutionId) q.append("institution_id", params.institutionId);
    if (params?.skip !== undefined) q.append("skip", String(params.skip));
    if (params?.limit !== undefined) q.append("limit", String(params.limit));
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchFromApi<import("@/types/pulseassist").AIInteractionLog[]>(
      `/pulseassist/audit-logs${qs}`
    );
  },
  getKnowledgeDocuments: (institutionId?: string) => {
    const qs = institutionId ? `?institution_id=${institutionId}` : "";
    return fetchFromApi<import("@/types/pulseassist").KnowledgeDocument[]>(
      `/pulseassist/documents${qs}`
    );
  },
  getKnowledgeDocument: (docId: string) =>
    fetchFromApi<import("@/types/pulseassist").KnowledgeDocument>(
      `/pulseassist/documents/${docId}`
    ),
  createKnowledgeDocument: (
    payload: import("@/types/pulseassist").KnowledgeDocumentCreate | FormData,
    institutionId?: string
  ) => {
    const qs = institutionId ? `?institution_id=${institutionId}` : "";
    let body: BodyInit;
    if (payload instanceof FormData) {
      body = payload;
    } else {
      const fd = new FormData();
      fd.append("title", payload.title);
      fd.append("document_code", payload.document_code);
      fd.append("category", payload.category);
      fd.append("version", "v1.0");
      fd.append("audience", payload.target_audience || "ALL");
      const fileBlob = new Blob([payload.content_text], { type: "text/plain" });
      fd.append("file", fileBlob, `${payload.document_code}.txt`);
      body = fd;
    }
    return fetchFromApi<import("@/types/pulseassist").KnowledgeDocument>(
      `/pulseassist/documents${qs}`,
      {
        method: "POST",
        body,
      }
    );
  },
  publishKnowledgeDocument: (
    docId: string,
    payload: import("@/types/pulseassist").DocumentPublishRequest
  ) =>
    fetchFromApi<import("@/types/pulseassist").KnowledgeDocument>(
      `/pulseassist/documents/${docId}/publish`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),
  archiveKnowledgeDocument: (docId: string) =>
    fetchFromApi<import("@/types/pulseassist").KnowledgeDocument>(
      `/pulseassist/documents/${docId}/archive`,
      { method: "POST" }
    ),

  // Phase 6: PulseRecord - Leaves
  getOwnLeaves: (status?: string) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchFromApi<import("@/types/pulserecord").LeaveRequest[]>(`/leaves/mine${qs}`);
  },
  getAssignedLeaves: (status?: string) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchFromApi<import("@/types/pulserecord").LeaveRequest[]>(`/leaves/assigned${qs}`);
  },
  getAllLeaves: (institutionId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (institutionId) params.append("institution_id", institutionId);
    if (status) params.append("status", status);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return fetchFromApi<import("@/types/pulserecord").LeaveRequest[]>(`/leaves${qs}`);
  },
  getLeave: (id: string) =>
    fetchFromApi<import("@/types/pulserecord").LeaveRequest>(`/leaves/${id}`),
  createLeave: (payload: import("@/types/pulserecord").LeaveRequestPayload) =>
    fetchFromApi<import("@/types/pulserecord").LeaveRequest>("/leaves", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reviewLeave: (id: string, payload: import("@/types/pulserecord").LeaveReviewPayload) =>
    fetchFromApi<import("@/types/pulserecord").LeaveRequest>(`/leaves/${id}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cancelLeave: (id: string, payload: import("@/types/pulserecord").LeaveCancelPayload) =>
    fetchFromApi<import("@/types/pulserecord").LeaveRequest>(`/leaves/${id}/cancel`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadLeaveAttachment: async (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return fetchFromApi<import("@/types/pulserecord").LeaveAttachment>(
      `/leaves/${id}/attachments`,
      {
        method: "POST",
        body: formData,
      }
    );
  },
  deleteLeaveAttachment: (id: string, attachmentId: string) =>
    fetchFromApi<{ message: string }>(`/leaves/${id}/attachments/${attachmentId}`, {
      method: "DELETE",
    }),

  // Phase 6: PulseRecord - Complaints
  getOwnComplaints: () =>
    fetchFromApi<import("@/types/pulserecord").Complaint[]>("/complaints/mine"),
  getAssignedComplaints: (status?: string) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchFromApi<import("@/types/pulserecord").Complaint[]>(`/complaints/assigned${qs}`);
  },
  getAllComplaints: (params?: { institutionId?: string; status?: string; category?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.institutionId) searchParams.append("institution_id", params.institutionId);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.category) searchParams.append("category", params.category);
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return fetchFromApi<import("@/types/pulserecord").Complaint[]>(`/complaints${qs}`);
  },
  getComplaint: (id: string) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>(`/complaints/${id}`),
  createComplaint: (payload: import("@/types/pulserecord").ComplaintCreatePayload) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>("/complaints", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignComplaintReviewer: (id: string, reviewerUserId: string) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>(`/complaints/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ reviewer_user_id: reviewerUserId }),
    }),
  requestComplaintInfo: (id: string, details: string) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>(`/complaints/${id}/request-information`, {
      method: "POST",
      body: JSON.stringify({ details }),
    }),
  provideComplaintInfo: (id: string, response: string) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>(`/complaints/${id}/respond`, {
      method: "POST",
      body: JSON.stringify({ response }),
    }),
  adjudicateComplaint: (
    id: string,
    payload: {
      status: string;
      adjudication_outcome: string;
      adjudication_summary: string;
      internal_reviewer_notes?: string;
    }
  ) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>(`/complaints/${id}/adjudicate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  appealComplaint: (id: string, reason: string) =>
    fetchFromApi<import("@/types/pulserecord").ComplaintAppeal>(`/complaints/${id}/appeal`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  resolveComplaintAppeal: (
    id: string,
    appealId: string,
    payload: { status: string; disposition_summary: string; reviewer_notes?: string }
  ) =>
    fetchFromApi<import("@/types/pulserecord").ComplaintAppeal>(
      `/complaints/${id}/resolve-appeal?appeal_id=${encodeURIComponent(appealId)}`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),
  closeComplaint: (id: string) =>
    fetchFromApi<import("@/types/pulserecord").Complaint>(`/complaints/${id}/close`, {
      method: "POST",
    }),
  uploadComplaintEvidence: async (id: string, file: File, description?: string, isConfidential?: boolean) => {
    const formData = new FormData();
    formData.append("file", file);
    if (description) formData.append("description", description);
    if (isConfidential !== undefined) formData.append("is_confidential", String(isConfidential));
    return fetchFromApi<import("@/types/pulserecord").ComplaintEvidence>(
      `/complaints/${id}/evidence`,
      {
        method: "POST",
        body: formData,
      }
    );
  },
  deleteComplaintEvidence: (id: string, evidenceId: string) =>
    fetchFromApi<{ message: string }>(`/complaints/${id}/evidence/${evidenceId}`, {
      method: "DELETE",
    }),
  downloadLeaveAttachmentUrl: (id: string, attachmentId: string) =>
    `${API_BASE_URL}/leaves/${id}/attachments/${attachmentId}/download`,
  downloadComplaintEvidenceUrl: (id: string, evidenceId: string) =>
    `${API_BASE_URL}/complaints/${id}/evidence/${evidenceId}/download`,
  downloadFileBlob: async (url: string): Promise<Blob> => {
    const fullUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url.startsWith("/") ? url : `/${url}`}`;
    const headers: Record<string, string> = {};
    if (inMemoryToken) headers["Authorization"] = `Bearer ${inMemoryToken}`;
    const res = await fetch(fullUrl, {
      credentials: "include",
      headers,
    });
    if (!res.ok) throw new ApiError(res.status, "Failed to download file");
    return res.blob();
  },

  // Phase 7 — PulseCase Client Methods
  getCases: (params?: {
    studentId?: string;
    status?: string;
    caseType?: string;
    priority?: string;
    assignedStaffId?: string;
    skip?: number;
    limit?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.studentId) searchParams.append("student_id", params.studentId);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.caseType) searchParams.append("case_type", params.caseType);
    if (params?.priority) searchParams.append("priority", params.priority);
    if (params?.assignedStaffId) searchParams.append("assigned_staff_id", params.assignedStaffId);
    if (params?.skip !== undefined) searchParams.append("skip", String(params.skip));
    if (params?.limit !== undefined) searchParams.append("limit", String(params.limit));
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return fetchFromApi<import("@/types/pulsecase").SupportCase[]>(`/cases${qs}`);
  },

  getCaseDetail: (caseId: string) =>
    fetchFromApi<import("@/types/pulsecase").SupportCaseDetail>(`/cases/${caseId}`),

  createCase: (payload: import("@/types/pulsecase").CaseCreatePayload) =>
    fetchFromApi<import("@/types/pulsecase").SupportCase>("/cases", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  assignCase: (caseId: string, assignedStaffId: string) =>
    fetchFromApi<import("@/types/pulsecase").SupportCase>(`/cases/${caseId}/assign`, {
      method: "PATCH",
      body: JSON.stringify({ assigned_staff_id: assignedStaffId }),
    }),

  updateCaseStatus: (caseId: string, payload: import("@/types/pulsecase").CaseStatusUpdatePayload) =>
    fetchFromApi<import("@/types/pulsecase").SupportCase>(`/cases/${caseId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  resolveCase: (caseId: string, payload: import("@/types/pulsecase").CaseResolvePayload) =>
    fetchFromApi<import("@/types/pulsecase").SupportCase>(`/cases/${caseId}/resolve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  closeCase: (caseId: string, payload?: import("@/types/pulsecase").CaseClosePayload) =>
    fetchFromApi<import("@/types/pulsecase").SupportCase>(`/cases/${caseId}/close`, {
      method: "POST",
      body: JSON.stringify(payload || {}),
    }),

  addCaseNote: (caseId: string, payload: import("@/types/pulsecase").CaseNoteCreatePayload) =>
    fetchFromApi<import("@/types/pulsecase").CaseNote>(`/cases/${caseId}/notes`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getCaseNotes: (caseId: string) =>
    fetchFromApi<import("@/types/pulsecase").CaseNote[]>(`/cases/${caseId}/notes`),

  addCaseIntervention: (caseId: string, payload: import("@/types/pulsecase").CaseInterventionCreatePayload) =>
    fetchFromApi<import("@/types/pulsecase").CaseIntervention>(`/cases/${caseId}/interventions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateCaseIntervention: (
    caseId: string,
    interventionId: string,
    payload: import("@/types/pulsecase").CaseInterventionUpdatePayload
  ) =>
    fetchFromApi<import("@/types/pulsecase").CaseIntervention>(
      `/cases/${caseId}/interventions/${interventionId}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      }
    ),

  scheduleCaseFollowUp: (caseId: string, payload: import("@/types/pulsecase").CaseFollowUpCreatePayload) =>
    fetchFromApi<import("@/types/pulsecase").CaseFollowUp>(`/cases/${caseId}/follow-ups`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateCaseFollowUp: (
    caseId: string,
    followUpId: string,
    payload: import("@/types/pulsecase").CaseFollowUpUpdatePayload
  ) =>
    fetchFromApi<import("@/types/pulsecase").CaseFollowUp>(
      `/cases/${caseId}/follow-ups/${followUpId}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      }
    ),

  submitFacultyReferral: (payload: import("@/types/pulsecase").FacultyReferralCreatePayload) =>
    fetchFromApi<import("@/types/pulsecase").FacultyReferralReceipt>("/cases/referrals", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getFacultyReferrals: (params?: { skip?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.append("skip", String(params.skip));
    if (params?.limit !== undefined) searchParams.append("limit", String(params.limit));
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return fetchFromApi<import("@/types/pulsecase").FacultyReferralReceipt[]>(`/cases/referrals/my${qs}`);
  },

  getStudentSupportSummary: () =>
    fetchFromApi<import("@/types/pulsecase").StudentSupportSummary>("/cases/student/my-support"),

  getStudentCaseHistory: (studentId: string) =>
    fetchFromApi<import("@/types/pulsecase").SupportCase[]>(`/cases/students/${studentId}/history`),
};


