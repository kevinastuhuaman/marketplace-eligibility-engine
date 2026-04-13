"""Add market regulations, geo restriction zones, and audit extensions."""

from alembic import op


revision = "20260409_01_regulations_geo_audit"
down_revision = None
branch_labels = None
depends_on = None


UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS eligibility_svc.market_regulations (
  market_code VARCHAR(16) PRIMARY KEY,
  display_name VARCHAR(128) NOT NULL,
  country_code VARCHAR(2) NOT NULL,
  region_code VARCHAR(16) NOT NULL,
  currency_code VARCHAR(3) NOT NULL DEFAULT 'USD',
  language_codes JSONB NOT NULL DEFAULT '["en"]'::jsonb,
  default_timezone VARCHAR(64) NOT NULL,
  regulatory_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_regulations_country_region
  ON eligibility_svc.market_regulations (country_code, region_code);

CREATE TABLE IF NOT EXISTS eligibility_svc.geo_restriction_zones (
  zone_id BIGSERIAL PRIMARY KEY,
  zone_code VARCHAR(64) NOT NULL UNIQUE,
  market_code VARCHAR(16) NOT NULL REFERENCES eligibility_svc.market_regulations (market_code),
  zone_name VARCHAR(128) NOT NULL,
  zone_type VARCHAR(32) NOT NULL,
  geometry_type VARCHAR(16) NOT NULL DEFAULT 'polygon',
  center_latitude DOUBLE PRECISION,
  center_longitude DOUBLE PRECISION,
  radius_meters INTEGER,
  polygon_coordinates JSONB NOT NULL DEFAULT '[]'::jsonb,
  hex_cells JSONB NOT NULL DEFAULT '[]'::jsonb,
  blocked_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_geo_restriction_zones_market_active
  ON eligibility_svc.geo_restriction_zones (market_code, active);

CREATE INDEX IF NOT EXISTS idx_geo_restriction_zones_hex_cells
  ON eligibility_svc.geo_restriction_zones USING GIN (hex_cells);

ALTER TABLE eligibility_svc.compliance_rules
  ADD COLUMN IF NOT EXISTS regulation_type VARCHAR(32) NOT NULL DEFAULT 'GENERAL';

CREATE INDEX IF NOT EXISTS idx_compliance_rules_regulation_type
  ON eligibility_svc.compliance_rules (regulation_type, enabled);

ALTER TABLE eligibility_svc.eligibility_audit_log
  ADD COLUMN IF NOT EXISTS blocking_rule_names TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS gating_rule_names TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS warning_rule_names TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS path_statuses JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS diagnosis_source_service VARCHAR(64),
  ADD COLUMN IF NOT EXISTS diagnosis_root_cause_code VARCHAR(128);

CREATE INDEX IF NOT EXISTS idx_eligibility_audit_log_market_time
  ON eligibility_svc.eligibility_audit_log (market_code, evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_eligibility_audit_log_item_market_time
  ON eligibility_svc.eligibility_audit_log (item_id, market_code, evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_eligibility_audit_log_blocking_rule_names
  ON eligibility_svc.eligibility_audit_log USING GIN (blocking_rule_names);

CREATE INDEX IF NOT EXISTS idx_eligibility_audit_log_path_statuses
  ON eligibility_svc.eligibility_audit_log USING GIN (path_statuses);
"""


DOWNGRADE_SQL = """
DROP INDEX IF EXISTS idx_eligibility_audit_log_path_statuses;
DROP INDEX IF EXISTS idx_eligibility_audit_log_blocking_rule_names;
DROP INDEX IF EXISTS idx_eligibility_audit_log_item_market_time;
DROP INDEX IF EXISTS idx_eligibility_audit_log_market_time;

ALTER TABLE eligibility_svc.eligibility_audit_log
  DROP COLUMN IF EXISTS diagnosis_root_cause_code,
  DROP COLUMN IF EXISTS diagnosis_source_service,
  DROP COLUMN IF EXISTS path_statuses,
  DROP COLUMN IF EXISTS warning_rule_names,
  DROP COLUMN IF EXISTS gating_rule_names,
  DROP COLUMN IF EXISTS blocking_rule_names;

DROP INDEX IF EXISTS idx_compliance_rules_regulation_type;
ALTER TABLE eligibility_svc.compliance_rules
  DROP COLUMN IF EXISTS regulation_type;

DROP INDEX IF EXISTS idx_geo_restriction_zones_hex_cells;
DROP INDEX IF EXISTS idx_geo_restriction_zones_market_active;
DROP TABLE IF EXISTS eligibility_svc.geo_restriction_zones;

DROP INDEX IF EXISTS idx_market_regulations_country_region;
DROP TABLE IF EXISTS eligibility_svc.market_regulations;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
