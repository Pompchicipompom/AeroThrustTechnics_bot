"""Add indexes for admin API filters and analytics

Revision ID: 20260421_0002
Revises: 20260421_0001
Create Date: 2026-04-21 18:40:00
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260421_0002"
down_revision: str | None = "20260421_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_reports_zone", "reports", ["zone"], unique=False)
    op.create_index("ix_reports_status", "reports", ["status"], unique=False)
    op.create_index("ix_reports_category", "reports", ["category"], unique=False)
    op.create_index("ix_reports_submit_mode", "reports", ["submit_mode"], unique=False)
    op.create_index("ix_reports_created_at", "reports", ["created_at"], unique=False)
    op.create_index("ix_reports_zone_status_created_at", "reports", ["zone", "status", "created_at"], unique=False)
    op.create_index("ix_audit_logs_admin_user_id", "audit_logs", ["admin_user_id"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_admin_user_id", table_name="audit_logs")
    op.drop_index("ix_reports_zone_status_created_at", table_name="reports")
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_index("ix_reports_submit_mode", table_name="reports")
    op.drop_index("ix_reports_category", table_name="reports")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_zone", table_name="reports")
