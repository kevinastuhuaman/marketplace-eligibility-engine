"""Add seller IPI fields."""

from alembic import op


revision = "20260409_01_seller_ipi"
down_revision = None
branch_labels = None
depends_on = None


UPGRADE_SQL = """
ALTER TABLE seller_svc.sellers
  ADD COLUMN IF NOT EXISTS in_stock_rate NUMERIC(5,4) NOT NULL DEFAULT 0.9800,
  ADD COLUMN IF NOT EXISTS cancellation_rate NUMERIC(5,4) NOT NULL DEFAULT 0.0100,
  ADD COLUMN IF NOT EXISTS vat_registered BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS ipi_score INTEGER NOT NULL DEFAULT 850,
  ADD COLUMN IF NOT EXISTS ipi_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS ipi_updated_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_sellers_ipi_score
  ON seller_svc.sellers (ipi_score DESC);
"""


DOWNGRADE_SQL = """
DROP INDEX IF EXISTS idx_sellers_ipi_score;
ALTER TABLE seller_svc.sellers
  DROP COLUMN IF EXISTS ipi_updated_at,
  DROP COLUMN IF EXISTS ipi_breakdown,
  DROP COLUMN IF EXISTS ipi_score,
  DROP COLUMN IF EXISTS vat_registered,
  DROP COLUMN IF EXISTS cancellation_rate,
  DROP COLUMN IF EXISTS in_stock_rate;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
