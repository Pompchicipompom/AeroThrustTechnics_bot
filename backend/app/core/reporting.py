from app.models.enums import ReportStatus, SubmitMode

CATEGORY_TO_ZONE: dict[str, str] = {
    "safety": "safety",
    "quality": "quality",
    "process": "process",
    "ethics": "ethics",
    "improvements": "improvements",
    "general": "general",
}

CATEGORY_LABELS_RU: dict[str, str] = {
    "safety": "Безопасность",
    "quality": "Качество",
    "process": "Процессы",
    "ethics": "Поведение и этика",
    "improvements": "Улучшения",
    "general": "Другое",
}

SUBMIT_MODE_LABELS_RU: dict[SubmitMode, str] = {
    SubmitMode.ANONYMOUS: "Анонимно",
    SubmitMode.OPEN: "Открыто",
}

REPORT_STATUS_LABELS_RU: dict[ReportStatus, str] = {
    ReportStatus.NEW: "Новое",
    ReportStatus.IN_PROGRESS: "В работе",
    ReportStatus.CLOSED: "Закрыто",
}
