"""add seller performance standards columns

Revision ID: 20260409_02_seller_performance_standards
Revises: 20260409_01_seller_ipi
Create Date: 2026-04-09
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260409_02_seller_performance_standards"
down_revision = "20260409_01_seller_ipi"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
ALTER TABLE seller_svc.sellers
  ADD COLUMN IF NOT EXISTS valid_tracking_rate NUMERIC(5,4) NOT NULL DEFAULT 0.9900,
  ADD COLUMN IF NOT EXISTS seller_response_rate NUMERIC(5,4) NOT NULL DEFAULT 0.9500,
  ADD COLUMN IF NOT EXISTS item_not_received_rate NUMERIC(5,4) NOT NULL DEFAULT 0.0100,
  ADD COLUMN IF NOT EXISTS negative_feedback_rate NUMERIC(5,4) NOT NULL DEFAULT 0.0100,
  ADD COLUMN IF NOT EXISTS uses_wfs BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS performance_updated_at TIMESTAMPTZ;
"""
    )


def downgrade() -> None:
    op.execute(
        """
ALTER TABLE seller_svc.sellers
  DROP COLUMN IF EXISTS performance_updated_at,
  DROP COLUMN IF EXISTS uses_wfs,
  DROP COLUMN IF EXISTS negative_feedback_rate,
  DROP COLUMN IF EXISTS item_not_received_rate,
  DROP COLUMN IF EXISTS seller_response_rate,
  DROP COLUMN IF EXISTS valid_tracking_rate;
"""
    )
