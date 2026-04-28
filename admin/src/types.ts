export type SubmitMode = "anonymous" | "open";
export type ReportStatus = "new" | "in_progress" | "closed";

export interface AdminTokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface AdminProfile {
  id: number;
  email: string;
  role: string;
  zone: string | null;
}

export interface ReportAuthor {
  technical_id: number;
  display_name: string | null;
  telegram_username: string | null;
}

export interface ReportListItem {
  id: number;
  public_number: string;
  submit_mode: SubmitMode;
  category: string;
  zone: string;
  status: ReportStatus;
  text_preview: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  author: ReportAuthor | null;
}

export interface PageMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface ReportListResponse {
  items: ReportListItem[];
  page: PageMeta;
}

export interface ReportAttachment {
  id: number;
  file_name: string;
  file_type: string;
  file_path: string;
  file_size: number;
  created_at: string;
}

export interface ReportDetail {
  id: number;
  public_number: string;
  submit_mode: SubmitMode;
  category: string;
  zone: string;
  status: ReportStatus;
  text: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  author: ReportAuthor | null;
  attachments: ReportAttachment[];
}

export interface ReportStatusUpdateResponse {
  id: number;
  public_number: string;
  status: ReportStatus;
  updated_at: string;
  closed_at: string | null;
}

export interface CountByKey {
  key: string;
  count: number;
}

export interface AnalyticsOverview {
  total_reports: number;
  anonymous_reports: number;
  open_reports: number;
  anonymous_share: number;
  open_share: number;
  avg_hours_to_close: number | null;
  by_category: CountByKey[];
  by_zone: CountByKey[];
  by_status: CountByKey[];
}

export interface AnalyticsDynamicsPoint {
  period_start: string;
  count: number;
}

export interface AnalyticsDynamics {
  granularity: "day" | "week";
  points: AnalyticsDynamicsPoint[];
}

export interface AuditLogItem {
  id: number;
  admin_user_id: number | null;
  entity_type: string;
  entity_id: number;
  action: string;
  payload_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  page: PageMeta;
}
