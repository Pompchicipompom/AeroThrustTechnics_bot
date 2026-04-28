import type {
  AdminProfile,
  AdminTokenResponse,
  AnalyticsDynamics,
  AnalyticsOverview,
  AuditLogListResponse,
  ReportDetail,
  ReportListResponse,
  ReportStatus,
  ReportStatusUpdateResponse,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").trim();

function buildUrl(path: string): string {
  if (!API_BASE_URL) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

function buildQuery(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}

export class ApiError extends Error {
  public readonly status: number;

  public constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export class AdminApiClient {
  private token: string | null = null;

  public setToken(token: string | null): void {
    this.token = token;
  }

  private async request<T>(
    path: string,
    options: {
      method?: string;
      body?: unknown;
      withAuth?: boolean;
    } = {},
  ): Promise<T> {
    const { method = "GET", body, withAuth = true } = options;
    const headers = new Headers({
      "Content-Type": "application/json",
    });

    if (withAuth) {
      if (!this.token) {
        throw new ApiError("Unauthorized.", 401);
      }
      headers.set("Authorization", `Bearer ${this.token}`);
    }

    const response = await fetch(buildUrl(path), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const payload = (await response.json()) as { detail?: string };
        if (payload.detail) {
          detail = payload.detail;
        }
      } catch {
        // Ignore JSON parse failures and use generic error.
      }
      throw new ApiError(detail, response.status);
    }

    return (await response.json()) as T;
  }

  public login(email: string, password: string): Promise<AdminTokenResponse> {
    return this.request<AdminTokenResponse>("/admin/auth/login", {
      method: "POST",
      body: { email, password },
      withAuth: false,
    });
  }

  public getMe(): Promise<AdminProfile> {
    return this.request<AdminProfile>("/admin/auth/me");
  }

  public listReports(params: {
    page: number;
    pageSize: number;
    publicNumber?: string;
    category?: string;
    zone?: string;
    status?: ReportStatus | "";
    submitMode?: "anonymous" | "open" | "";
  }): Promise<ReportListResponse> {
    const query = buildQuery({
      page: params.page,
      page_size: params.pageSize,
      public_number: params.publicNumber,
      category: params.category,
      zone: params.zone,
      status: params.status,
      submit_mode: params.submitMode,
    });
    return this.request<ReportListResponse>(`/admin/reports${query}`);
  }

  public getReport(reportId: number): Promise<ReportDetail> {
    return this.request<ReportDetail>(`/admin/reports/${reportId}`);
  }

  public updateReportStatus(reportId: number, status: ReportStatus): Promise<ReportStatusUpdateResponse> {
    return this.request<ReportStatusUpdateResponse>(`/admin/reports/${reportId}/status`, {
      method: "PATCH",
      body: { status },
    });
  }

  public getOverview(): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>("/admin/analytics/overview");
  }

  public getDynamics(granularity: "day" | "week"): Promise<AnalyticsDynamics> {
    const query = buildQuery({ granularity });
    return this.request<AnalyticsDynamics>(`/admin/analytics/dynamics${query}`);
  }

  public getAuditLogs(params: {
    page: number;
    pageSize: number;
    action?: string;
    entityType?: string;
  }): Promise<AuditLogListResponse> {
    const query = buildQuery({
      page: params.page,
      page_size: params.pageSize,
      action: params.action,
      entity_type: params.entityType,
    });
    return this.request<AuditLogListResponse>(`/admin/audit-logs${query}`);
  }

  public async fetchAttachmentFile(params: {
    reportId: number;
    attachmentId: number;
    download: boolean;
  }): Promise<{ blob: Blob; suggestedFileName: string | null }> {
    if (!this.token) {
      throw new ApiError("Unauthorized.", 401);
    }

    const query = buildQuery({ download: params.download ? "true" : undefined });
    const url = buildUrl(
      `/admin/reports/${params.reportId}/attachments/${params.attachmentId}/file${query}`,
    );
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const payload = (await response.json()) as { detail?: string };
        if (payload.detail) {
          detail = payload.detail;
        }
      } catch {
        // Ignore non-json responses for error details.
      }
      throw new ApiError(detail, response.status);
    }

    const contentDisposition = response.headers.get("content-disposition");
    const fileNameMatch = contentDisposition?.match(/filename\\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?/i);
    const encodedName = fileNameMatch?.[1];
    const plainName = fileNameMatch?.[2];
    const suggestedFileName = encodedName
      ? decodeURIComponent(encodedName)
      : plainName
        ? plainName
        : null;

    return {
      blob: await response.blob(),
      suggestedFileName,
    };
  }
}

export const adminApiClient = new AdminApiClient();
