from enum import StrEnum


class SubmitMode(StrEnum):
    ANONYMOUS = "anonymous"
    OPEN = "open"


class ReportStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class AdminRole(StrEnum):
    ADMIN = "admin"
    RESOLVER = "resolver"
