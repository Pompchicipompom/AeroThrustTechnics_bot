import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError, adminApiClient } from "./api";
import type {
  AdminProfile,
  AnalyticsDynamics,
  AnalyticsOverview,
  AuditLogItem,
  AuditLogListResponse,
  PageMeta,
  ReportDetail,
  ReportListResponse,
  ReportStatus,
  SubmitMode,
} from "./types";

const TOKEN_STORAGE_KEY = "aerotrust_admin_token";
const REPORT_STATUSES: ReportStatus[] = ["new", "in_progress", "closed"];

type TabKey = "reports" | "analytics" | "audit";
type CategoryCode = "safety" | "quality" | "process" | "ethics" | "improvements" | "general";
const CATEGORY_OPTIONS: CategoryCode[] = [
  "safety",
  "quality",
  "process",
  "ethics",
  "improvements",
  "general",
];

const STATUS_LABELS: Record<ReportStatus, string> = {
  new: "Новое",
  in_progress: "В работе",
  closed: "Закрыто",
};

const SUBMIT_MODE_LABELS: Record<SubmitMode, string> = {
  anonymous: "Анонимно",
  open: "Открыто",
};

const CATEGORY_LABELS: Record<string, string> = {
  safety: "Безопасность",
  quality: "Качество",
  process: "Процессы",
  ethics: "Поведение и этика",
  improvements: "Улучшения",
  general: "Другое",
};

const ZONE_LABELS: Record<string, string> = {
  safety: "Безопасность",
  quality: "Качество",
  process: "Процессы",
  ethics: "Поведение и этика",
  improvements: "Улучшения",
  general: "Другое",
};

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  resolver: "Ответственный",
};

const AUDIT_ACTION_LABELS: Record<string, string> = {
  login: "Вход администратора",
  report_viewed: "Просмотр обращения",
  status_changed: "Изменение статуса обращения",
};

const AUDIT_ENTITY_LABELS: Record<string, string> = {
  report: "Обращение",
  admin_user: "Администратор",
};

function formatDateTime(iso: string | null): string {
  if (!iso) {
    return "-";
  }

  return new Date(iso).toLocaleString("ru-RU");
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} Б`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} КБ`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} МБ`;
}

function toDisplayKey(value: string): string {
  return value.trim().toLowerCase();
}

function mapCategory(value: string): string {
  return CATEGORY_LABELS[toDisplayKey(value)] ?? value;
}

function mapZone(value: string): string {
  return ZONE_LABELS[toDisplayKey(value)] ?? value;
}

function mapStatus(value: ReportStatus): string {
  return STATUS_LABELS[value] ?? value;
}

function mapMode(value: SubmitMode): string {
  return SUBMIT_MODE_LABELS[value] ?? value;
}

function mapRole(value: string): string {
  return ROLE_LABELS[toDisplayKey(value)] ?? value;
}

function mapAuditAction(value: string): string {
  return AUDIT_ACTION_LABELS[toDisplayKey(value)] ?? value;
}

function mapAuditEntity(value: string): string {
  return AUDIT_ENTITY_LABELS[toDisplayKey(value)] ?? value;
}

function formatTelegramUsername(username: string | null): string | null {
  if (!username) {
    return null;
  }
  return username.startsWith("@") ? username : `@${username}`;
}

function formatAuthorLabel(author: { display_name: string | null; telegram_username: string | null }): string {
  const username = formatTelegramUsername(author.telegram_username);
  const displayName = author.display_name ?? "Без имени";

  if (!username) {
    return displayName;
  }
  if (displayName === username) {
    return displayName;
  }
  return `${displayName} (${username})`;
}

function extractErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = error.message;
    if (detail === "Attachment file not found.") {
      return "Файл вложения не найден в хранилище.";
    }
    if (detail === "Attachment not found.") {
      return "Вложение не найдено в обращении.";
    }
    if (detail === "Report not found.") {
      return "Обращение не найдено.";
    }
    if (detail === "Invalid credentials.") {
      return "Неверный email или пароль.";
    }
    if (detail === "Unauthorized.") {
      return "Сессия истекла. Выполните вход повторно.";
    }

    if (error.status === 401) {
      return "Сессия истекла. Выполните вход повторно.";
    }
    if (error.status === 403) {
      return "Недостаточно прав для выполнения операции.";
    }
    if (error.status === 404) {
      return "Данные не найдены.";
    }

    return detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Произошла непредвиденная ошибка.";
}

function emptyPageMeta(): PageMeta {
  return {
    page: 1,
    page_size: 20,
    total_items: 0,
    total_pages: 0,
  };
}

function formatAuditDescription(item: AuditLogItem): string {
  if (item.action === "status_changed") {
    const fromStatusRaw = item.payload_json?.from_status;
    const toStatusRaw = item.payload_json?.to_status;
    if (typeof fromStatusRaw === "string" && typeof toStatusRaw === "string") {
      const fromStatus = REPORT_STATUSES.includes(fromStatusRaw as ReportStatus)
        ? mapStatus(fromStatusRaw as ReportStatus)
        : fromStatusRaw;
      const toStatus = REPORT_STATUSES.includes(toStatusRaw as ReportStatus)
        ? mapStatus(toStatusRaw as ReportStatus)
        : toStatusRaw;
      return `Статус изменен: ${fromStatus} -> ${toStatus}`;
    }
  }

  if (item.action === "report_viewed") {
    return "Карточка обращения открыта";
  }

  if (item.action === "login") {
    return "Успешный вход в систему";
  }

  return mapAuditAction(item.action);
}

export function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("reports");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginPending, setLoginPending] = useState(false);
  const [sessionInfo, setSessionInfo] = useState<string | null>(null);

  const [profileError, setProfileError] = useState<string | null>(null);
  const [profilePending, setProfilePending] = useState(false);

  const [reportsError, setReportsError] = useState<string | null>(null);
  const [reportsPending, setReportsPending] = useState(false);
  const [reportsResponse, setReportsResponse] = useState<ReportListResponse>({
    items: [],
    page: emptyPageMeta(),
  });

  const [reportPage, setReportPage] = useState(1);
  const [reportPageSize, setReportPageSize] = useState(20);
  const [reportPublicNumber, setReportPublicNumber] = useState("");
  const [reportCategory, setReportCategory] = useState("");
  const [reportStatusFilter, setReportStatusFilter] = useState<ReportStatus | "">("");
  const [reportSubmitModeFilter, setReportSubmitModeFilter] = useState<"" | SubmitMode>("");

  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [reportDetail, setReportDetail] = useState<ReportDetail | null>(null);
  const [reportDetailPending, setReportDetailPending] = useState(false);
  const [reportDetailError, setReportDetailError] = useState<string | null>(null);
  const [statusDraft, setStatusDraft] = useState<ReportStatus>("new");
  const [statusUpdatePending, setStatusUpdatePending] = useState(false);
  const [statusUpdateError, setStatusUpdateError] = useState<string | null>(null);
  const [statusUpdateSuccess, setStatusUpdateSuccess] = useState<string | null>(null);
  const [attachmentActionError, setAttachmentActionError] = useState<string | null>(null);
  const [attachmentActionPendingId, setAttachmentActionPendingId] = useState<number | null>(null);

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [dynamics, setDynamics] = useState<AnalyticsDynamics | null>(null);
  const [dynamicsGranularity, setDynamicsGranularity] = useState<"day" | "week">("day");
  const [analyticsPending, setAnalyticsPending] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  const [auditResponse, setAuditResponse] = useState<AuditLogListResponse>({
    items: [],
    page: emptyPageMeta(),
  });
  const [auditPending, setAuditPending] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [auditPage, setAuditPage] = useState(1);
  const [auditPageSize, setAuditPageSize] = useState(20);
  const [auditActionFilter, setAuditActionFilter] = useState("");
  const [auditEntityTypeFilter, setAuditEntityTypeFilter] = useState("");

  const clearSession = (message: string): void => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setSessionInfo(message);
    setProfile(null);
  };

  useEffect(() => {
    adminApiClient.setToken(token);
  }, [token]);

  useEffect(() => {
    if (!token) {
      setProfile(null);
      return;
    }

    let cancelled = false;
    setProfilePending(true);
    setProfileError(null);

    adminApiClient
      .getMe()
      .then((data) => {
        if (cancelled) {
          return;
        }
        setProfile(data);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        const message = extractErrorMessage(error);
        if (error instanceof ApiError && error.status === 401) {
          clearSession("Сессия истекла. Войдите снова.");
          return;
        }
        setProfileError(message);
      })
      .finally(() => {
        if (!cancelled) {
          setProfilePending(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!profile || activeTab !== "reports") {
      return;
    }

    let cancelled = false;
    setReportsPending(true);
    setReportsError(null);

    adminApiClient
      .listReports({
        page: reportPage,
        pageSize: reportPageSize,
        publicNumber: reportPublicNumber,
        category: reportCategory,
        status: reportStatusFilter,
        submitMode: reportSubmitModeFilter,
      })
      .then((data) => {
        if (cancelled) {
          return;
        }
        setReportsResponse(data);

        if (data.items.length > 0) {
          setSelectedReportId((prevId) => {
            if (prevId && data.items.some((item) => item.id === prevId)) {
              return prevId;
            }
            return data.items[0].id;
          });
        } else {
          setSelectedReportId(null);
          setReportDetail(null);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          clearSession("Сессия истекла. Войдите снова.");
          return;
        }
        setReportsError(extractErrorMessage(error));
      })
      .finally(() => {
        if (!cancelled) {
          setReportsPending(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    profile,
    activeTab,
    reportPage,
    reportPageSize,
    reportPublicNumber,
    reportCategory,
    reportStatusFilter,
    reportSubmitModeFilter,
  ]);

  useEffect(() => {
    if (!profile || activeTab !== "reports" || selectedReportId === null) {
      return;
    }

    let cancelled = false;
    setReportDetailPending(true);
    setReportDetailError(null);

    adminApiClient
      .getReport(selectedReportId)
      .then((data) => {
        if (cancelled) {
          return;
        }
        setReportDetail(data);
        setStatusDraft(data.status);
        setStatusUpdateSuccess(null);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          clearSession("Сессия истекла. Войдите снова.");
          return;
        }
        setReportDetailError(extractErrorMessage(error));
      })
      .finally(() => {
        if (!cancelled) {
          setReportDetailPending(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [profile, activeTab, selectedReportId]);

  useEffect(() => {
    if (!profile || activeTab !== "analytics") {
      return;
    }

    let cancelled = false;
    setAnalyticsPending(true);
    setAnalyticsError(null);

    Promise.all([adminApiClient.getOverview(), adminApiClient.getDynamics(dynamicsGranularity)])
      .then(([overviewData, dynamicsData]) => {
        if (cancelled) {
          return;
        }
        setOverview(overviewData);
        setDynamics(dynamicsData);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          clearSession("Сессия истекла. Войдите снова.");
          return;
        }
        setAnalyticsError(extractErrorMessage(error));
      })
      .finally(() => {
        if (!cancelled) {
          setAnalyticsPending(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [profile, activeTab, dynamicsGranularity]);

  useEffect(() => {
    if (!profile || activeTab !== "audit") {
      return;
    }

    let cancelled = false;
    setAuditPending(true);
    setAuditError(null);

    adminApiClient
      .getAuditLogs({
        page: auditPage,
        pageSize: auditPageSize,
        action: auditActionFilter,
        entityType: auditEntityTypeFilter,
      })
      .then((data) => {
        if (!cancelled) {
          setAuditResponse(data);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          clearSession("Сессия истекла. Войдите снова.");
          return;
        }
        setAuditError(extractErrorMessage(error));
      })
      .finally(() => {
        if (!cancelled) {
          setAuditPending(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [profile, activeTab, auditPage, auditPageSize, auditActionFilter, auditEntityTypeFilter]);

  const reportPageInfo = useMemo(() => {
    const { page, total_pages: totalPages, total_items: totalItems } = reportsResponse.page;
    return `Страница ${page} из ${Math.max(totalPages, 1)} (всего ${totalItems})`;
  }, [reportsResponse.page]);

  const auditPageInfo = useMemo(() => {
    const { page, total_pages: totalPages, total_items: totalItems } = auditResponse.page;
    return `Страница ${page} из ${Math.max(totalPages, 1)} (всего ${totalItems})`;
  }, [auditResponse.page]);

  const handleLogin = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setLoginPending(true);
    setLoginError(null);
    setSessionInfo(null);

    try {
      const loginResult = await adminApiClient.login(loginEmail, loginPassword);
      localStorage.setItem(TOKEN_STORAGE_KEY, loginResult.access_token);
      setToken(loginResult.access_token);
    } catch (error: unknown) {
      setLoginError(extractErrorMessage(error));
    } finally {
      setLoginPending(false);
    }
  };

  const handleLogout = (): void => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setSelectedReportId(null);
    setReportDetail(null);
    setOverview(null);
    setDynamics(null);
    setAuditResponse({ items: [], page: emptyPageMeta() });
    setSessionInfo("Вы вышли из системы.");
  };

  const handleReportStatusUpdate = async (): Promise<void> => {
    if (!reportDetail) {
      return;
    }

    setStatusUpdatePending(true);
    setStatusUpdateError(null);
    setStatusUpdateSuccess(null);

    try {
      await adminApiClient.updateReportStatus(reportDetail.id, statusDraft);
      const [updatedDetail, refreshedList] = await Promise.all([
        adminApiClient.getReport(reportDetail.id),
        adminApiClient.listReports({
          page: reportPage,
          pageSize: reportPageSize,
          publicNumber: reportPublicNumber,
          category: reportCategory,
          status: reportStatusFilter,
          submitMode: reportSubmitModeFilter,
        }),
      ]);
      setReportDetail(updatedDetail);
      setReportsResponse(refreshedList);
      setStatusUpdateSuccess(`Статус обращения обновлен: ${mapStatus(statusDraft)}.`);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 401) {
        clearSession("Сессия истекла. Войдите снова.");
        return;
      }
      setStatusUpdateError(extractErrorMessage(error));
    } finally {
      setStatusUpdatePending(false);
    }
  };

  const handleAttachmentAction = async (
    attachmentId: number,
    options: { fileName: string; download: boolean },
  ): Promise<void> => {
    if (!reportDetail) {
      return;
    }

    setAttachmentActionError(null);
    setAttachmentActionPendingId(attachmentId);
    try {
      const fileResult = await adminApiClient.fetchAttachmentFile({
        reportId: reportDetail.id,
        attachmentId,
        download: options.download,
      });
      const blobUrl = URL.createObjectURL(fileResult.blob);
      const suggestedName = fileResult.suggestedFileName || options.fileName;

      if (options.download) {
        const link = document.createElement("a");
        link.href = blobUrl;
        link.download = suggestedName;
        link.click();
      } else {
        const openedWindow = window.open(blobUrl, "_blank", "noopener,noreferrer");
        if (!openedWindow) {
          const link = document.createElement("a");
          link.href = blobUrl;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.click();
        }
      }

      setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 401) {
        clearSession("Сессия истекла. Войдите снова.");
        return;
      }
      setAttachmentActionError(
        `Не удалось получить файл «${options.fileName}»: ${extractErrorMessage(error)}`,
      );
    } finally {
      setAttachmentActionPendingId(null);
    }
  };

  if (!token) {
    return (
      <main className="page page-center">
        <section className="card card-auth">
          <h1>Панель обработки обращений</h1>
          <p className="subtitle">Войдите, чтобы работать с обращениями, аналитикой и журналом действий.</p>
          <form onSubmit={handleLogin} className="form-grid">
            <label>
              Логин
              <input
                type="text"
                value={loginEmail}
                onChange={(event) => setLoginEmail(event.target.value)}
                required
                autoComplete="username"
              />
            </label>
            <label>
              Пароль
              <input
                type="password"
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
                required
                autoComplete="current-password"
              />
            </label>
            <button type="submit" disabled={loginPending}>
              {loginPending ? "Выполняем вход..." : "Войти"}
            </button>
            {sessionInfo ? <p className="info-box">{sessionInfo}</p> : null}
            {loginError ? <p className="error-box">{loginError}</p> : null}
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar card">
        <div>
          <h1>Панель обработки обращений</h1>
          {profile ? (
            <p className="subtitle">
              {profile.email} | роль: <b>{mapRole(profile.role)}</b>
              {profile.zone ? ` | зона: ${mapZone(profile.zone)}` : ""}
            </p>
          ) : null}
          {profilePending ? <p className="subtitle">Загружаем профиль...</p> : null}
          {profileError ? <p className="error-box">{profileError}</p> : null}
        </div>
        <button type="button" className="ghost-button" onClick={handleLogout}>
          Выйти
        </button>
      </header>

      <nav className="tabs card">
        <button
          type="button"
          className={activeTab === "reports" ? "tab-button active" : "tab-button"}
          onClick={() => setActiveTab("reports")}
        >
          Обращения
        </button>
        <button
          type="button"
          className={activeTab === "analytics" ? "tab-button active" : "tab-button"}
          onClick={() => setActiveTab("analytics")}
        >
          Аналитика
        </button>
        <button
          type="button"
          className={activeTab === "audit" ? "tab-button active" : "tab-button"}
          onClick={() => setActiveTab("audit")}
        >
          Журнал действий
        </button>
      </nav>

      {activeTab === "reports" ? (
        <section className="layout-columns">
          <article className="card">
            <h2>Обращения</h2>
            <div className="filters report-filters">
              <label>
                Номер обращения
                <input
                  value={reportPublicNumber}
                  onChange={(event) => {
                    setReportPublicNumber(event.target.value);
                    setReportPage(1);
                  }}
                  placeholder="AT-..."
                />
              </label>
              <label>
                Категория
                <select
                  value={reportCategory}
                  onChange={(event) => {
                    setReportCategory(event.target.value);
                    setReportPage(1);
                  }}
                >
                  <option value="">Все</option>
                  {CATEGORY_OPTIONS.map((categoryCode) => (
                    <option key={categoryCode} value={categoryCode}>
                      {mapCategory(categoryCode)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Статус
                <select
                  value={reportStatusFilter}
                  onChange={(event) => {
                    setReportStatusFilter(event.target.value as ReportStatus | "");
                    setReportPage(1);
                  }}
                >
                  <option value="">Все</option>
                  {REPORT_STATUSES.map((status) => (
                    <option value={status} key={status}>
                      {mapStatus(status)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Формат отправки
                <select
                  value={reportSubmitModeFilter}
                  onChange={(event) => {
                    setReportSubmitModeFilter(event.target.value as "" | SubmitMode);
                    setReportPage(1);
                  }}
                >
                  <option value="">Все</option>
                  <option value="anonymous">{mapMode("anonymous")}</option>
                  <option value="open">{mapMode("open")}</option>
                </select>
              </label>
              <label>
                Размер страницы
                <select
                  value={reportPageSize}
                  onChange={(event) => {
                    setReportPageSize(Number(event.target.value));
                    setReportPage(1);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </label>
            </div>

            <div className="toolbar">
              <p className="subtitle">{reportPageInfo}</p>
              <div className="toolbar-buttons">
                <button
                  type="button"
                  onClick={() => setReportPage((page) => Math.max(page - 1, 1))}
                  disabled={reportPage <= 1}
                >
                  Назад
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setReportPage((page) => Math.min(page + 1, Math.max(reportsResponse.page.total_pages, 1)))
                  }
                  disabled={reportPage >= reportsResponse.page.total_pages}
                >
                  Вперед
                </button>
              </div>
            </div>

            {reportsError ? <p className="error-box">Ошибка загрузки обращений: {reportsError}</p> : null}
            {reportsPending ? <p className="subtitle">Загружаем обращения...</p> : null}

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Номер</th>
                    <th>Статус</th>
                    <th>Зона</th>
                    <th>Формат отправки</th>
                    <th>Создано</th>
                  </tr>
                </thead>
                <tbody>
                  {reportsResponse.items.map((item) => (
                    <tr
                      key={item.id}
                      className={item.id === selectedReportId ? "row-active" : ""}
                      onClick={() => setSelectedReportId(item.id)}
                    >
                      <td>{item.id}</td>
                      <td>{item.public_number}</td>
                      <td>{mapStatus(item.status)}</td>
                      <td>{mapZone(item.zone)}</td>
                      <td>{mapMode(item.submit_mode)}</td>
                      <td>{formatDateTime(item.created_at)}</td>
                    </tr>
                  ))}
                  {reportsResponse.items.length === 0 ? (
                    <tr>
                      <td colSpan={6}>Обращения не найдены. Измените фильтры или проверьте период.</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </article>

          <article className="card">
            <h2>Карточка обращения</h2>
            {reportDetailPending ? <p className="subtitle">Загружаем карточку обращения...</p> : null}
            {reportDetailError ? <p className="error-box">Ошибка загрузки карточки: {reportDetailError}</p> : null}

            {reportDetail ? (
              <div className="detail-grid">
                <p>
                  <b>Номер обращения:</b> {reportDetail.public_number}
                </p>
                <p>
                  <b>Категория:</b> {mapCategory(reportDetail.category)}
                </p>
                <p>
                  <b>Формат отправки:</b> {mapMode(reportDetail.submit_mode)}
                </p>
                <p>
                  <b>Автор:</b>{" "}
                  {reportDetail.author ? formatAuthorLabel(reportDetail.author) : "Анонимно"}
                </p>
                {reportDetail.author ? (
                  <p>
                    <b>Технический ID автора:</b> {reportDetail.author.technical_id}
                  </p>
                ) : null}
                <p>
                  <b>Создано:</b> {formatDateTime(reportDetail.created_at)}
                </p>
                <p>
                  <b>Обновлено:</b> {formatDateTime(reportDetail.updated_at)}
                </p>
                <p>
                  <b>Закрыто:</b> {formatDateTime(reportDetail.closed_at)}
                </p>
                <p>
                  <b>Текст обращения:</b>
                </p>
                <pre className="text-box">{reportDetail.text}</pre>

                <div className="status-box">
                  <label>
                    Статус
                    <select value={statusDraft} onChange={(event) => setStatusDraft(event.target.value as ReportStatus)}>
                      {REPORT_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {mapStatus(status)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button type="button" onClick={handleReportStatusUpdate} disabled={statusUpdatePending}>
                    {statusUpdatePending ? "Обновляем..." : "Обновить статус"}
                  </button>
                </div>
                {statusUpdateError ? <p className="error-box">Ошибка обновления: {statusUpdateError}</p> : null}
                {statusUpdateSuccess ? <p className="success-box">{statusUpdateSuccess}</p> : null}

                <p>
                  <b>Вложения:</b>
                </p>
                {reportDetail.attachments.length === 0 ? (
                  <p className="subtitle">Вложений нет.</p>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Файл</th>
                          <th>Тип</th>
                          <th>Размер</th>
                          <th>Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportDetail.attachments.map((attachment) => (
                          <tr key={attachment.id}>
                            <td>{attachment.file_name}</td>
                            <td>{attachment.file_type}</td>
                            <td>{formatBytes(attachment.file_size)}</td>
                            <td>
                              <div className="toolbar-buttons">
                                <button
                                  type="button"
                                  className="secondary-button"
                                  onClick={() =>
                                    handleAttachmentAction(attachment.id, {
                                      fileName: attachment.file_name,
                                      download: false,
                                    })
                                  }
                                  disabled={attachmentActionPendingId === attachment.id}
                                >
                                  Открыть
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    handleAttachmentAction(attachment.id, {
                                      fileName: attachment.file_name,
                                      download: true,
                                    })
                                  }
                                  disabled={attachmentActionPendingId === attachment.id}
                                >
                                  Скачать
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {attachmentActionError ? <p className="error-box">{attachmentActionError}</p> : null}
              </div>
            ) : (
              <p className="subtitle">Выберите обращение в таблице слева.</p>
            )}
          </article>
        </section>
      ) : null}

      {activeTab === "analytics" ? (
        <section className="card">
          <h2>Аналитика</h2>
          <div className="toolbar">
            <label>
              Шаг динамики
              <select
                value={dynamicsGranularity}
                onChange={(event) => setDynamicsGranularity(event.target.value as "day" | "week")}
              >
                <option value="day">По дням</option>
                <option value="week">По неделям</option>
              </select>
            </label>
          </div>
          {analyticsPending ? <p className="subtitle">Загружаем аналитику...</p> : null}
          {analyticsError ? <p className="error-box">Ошибка загрузки аналитики: {analyticsError}</p> : null}

          {!analyticsPending && !overview && !analyticsError ? (
            <p className="subtitle">Нет данных для отображения аналитики.</p>
          ) : null}

          <div className="analytics-dashboard-grid">
            {overview ? (
              <>
                <article className="metric">
                  <span>Всего обращений</span>
                  <b>{overview.total_reports}</b>
                </article>
                <article className="metric">
                  <span>Доля анонимных</span>
                  <b>{formatPercent(overview.anonymous_share)}</b>
                </article>
                <article className="metric">
                  <span>Доля открытых</span>
                  <b>{formatPercent(overview.open_share)}</b>
                </article>
                <article className="metric">
                  <span>Среднее время до закрытия (ч)</span>
                  <b>{overview.avg_hours_to_close === null ? "-" : overview.avg_hours_to_close.toFixed(2)}</b>
                </article>
              </>
            ) : null}

            <article className="analytics-panel analytics-panel-categories">
              <h3>По категориям</h3>
              {overview ? (
                <ul className="simple-list">
                  {overview.by_category.map((item) => (
                    <li key={`category-${item.key}`}>
                      {mapCategory(item.key)}: {item.count}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>

            <article className="analytics-panel analytics-panel-statuses">
              <h3>По статусам</h3>
              {overview ? (
                <ul className="simple-list">
                  {overview.by_status.map((item) => (
                    <li key={`status-${item.key}`}>
                      {REPORT_STATUSES.includes(item.key as ReportStatus) ? mapStatus(item.key as ReportStatus) : item.key}:{" "}
                      {item.count}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>

            <article className="analytics-panel analytics-panel-dynamics">
              <h3>Динамика обращений</h3>
              {dynamics && dynamics.points.length > 0 ? (
                <ul className="simple-list">
                  {dynamics.points.map((point) => (
                    <li key={point.period_start}>
                      {point.period_start}: {point.count}
                    </li>
                  ))}
                </ul>
              ) : null}
              {dynamics && dynamics.points.length === 0 ? <p className="subtitle">Нет данных по выбранному шагу динамики.</p> : null}
            </article>
          </div>
        </section>
      ) : null}

      {activeTab === "audit" ? (
        <section className="card">
          <h2>Журнал действий</h2>
          <div className="filters">
            <label>
              Действие (код)
              <input
                value={auditActionFilter}
                onChange={(event) => {
                  setAuditActionFilter(event.target.value);
                  setAuditPage(1);
                }}
                placeholder="например: изменение статуса (код: status_changed)"
              />
            </label>
            <label>
              Тип сущности
              <input
                value={auditEntityTypeFilter}
                onChange={(event) => {
                  setAuditEntityTypeFilter(event.target.value);
                  setAuditPage(1);
                }}
                placeholder="например: обращение (код: report)"
              />
            </label>
            <label>
              Размер страницы
              <select
                value={auditPageSize}
                onChange={(event) => {
                  setAuditPageSize(Number(event.target.value));
                  setAuditPage(1);
                }}
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </label>
          </div>

          <div className="toolbar">
            <p className="subtitle">{auditPageInfo}</p>
            <div className="toolbar-buttons">
              <button
                type="button"
                onClick={() => setAuditPage((page) => Math.max(page - 1, 1))}
                disabled={auditPage <= 1}
              >
                Назад
              </button>
              <button
                type="button"
                onClick={() => setAuditPage((page) => Math.min(page + 1, Math.max(auditResponse.page.total_pages, 1)))}
                disabled={auditPage >= auditResponse.page.total_pages}
              >
                Вперед
              </button>
            </div>
          </div>

          {auditPending ? <p className="subtitle">Загружаем журнал действий...</p> : null}
          {auditError ? <p className="error-box">Ошибка загрузки журнала: {auditError}</p> : null}

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Когда</th>
                  <th>Действие</th>
                  <th>Описание</th>
                  <th>Сущность</th>
                  <th>ID сущности</th>
                  <th>ID администратора</th>
                </tr>
              </thead>
              <tbody>
                {auditResponse.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td>{mapAuditAction(item.action)}</td>
                    <td>{formatAuditDescription(item)}</td>
                    <td>{mapAuditEntity(item.entity_type)}</td>
                    <td>{item.entity_id}</td>
                    <td>{item.admin_user_id ?? "-"}</td>
                  </tr>
                ))}
                {auditResponse.items.length === 0 ? (
                  <tr>
                    <td colSpan={7}>Записей журнала не найдено.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </main>
  );
}
