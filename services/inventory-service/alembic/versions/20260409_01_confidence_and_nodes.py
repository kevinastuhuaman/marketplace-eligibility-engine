"""Add inventory confidence and fulfillment nodes."""

from alembic import op


revision = "20260409_01_confidence_and_nodes"
down_revision = None
branch_labels = None
depends_on = None


UPGRADE_SQL = """
ALTER TABLE inventory_svc.inventory_positions
  ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(4,3) NOT NULL DEFAULT 1.000,
  ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS verification_source VARCHAR(32) NOT NULL DEFAULT 'seed',
  ADD COLUMN IF NOT EXISTS oos_30d_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS node_type VARCHAR(32) NOT NULL DEFAULT 'fc';

CREATE INDEX IF NOT EXISTS idx_inventory_positions_confidence
  ON inventory_svc.inventory_positions (path_id, confidence_score);

CREATE INDEX IF NOT EXISTS idx_inventory_positions_last_verified_at
  ON inventory_svc.inventory_positions (last_verified_at DESC);

CREATE TABLE IF NOT EXISTS inventory_svc.fulfillment_nodes (
  node_id VARCHAR(64) PRIMARY KEY,
  market_code VARCHAR(16) NOT NULL,
  node_name VARCHAR(128) NOT NULL,
  node_type VARCHAR(32) NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fulfillment_nodes_market_type
  ON inventory_svc.fulfillment_nodes (market_code, node_type, enabled);
"""


DOWNGRADE_SQL = """
DROP INDEX IF EXISTS idx_fulfillment_nodes_market_type;
DROP TABLE IF EXISTS inventory_svc.fulfillment_nodes;
DROP INDEX IF EXISTS idx_inventory_positions_last_verified_at;
DROP INDEX IF EXISTS idx_inventory_positions_confidence;
ALTER TABLE inventory_svc.inventory_positions
  DROP COLUMN IF EXISTS node_type,
  DROP COLUMN IF EXISTS oos_30d_count,
  DROP COLUMN IF EXISTS verification_source,
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS confidence_score;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
