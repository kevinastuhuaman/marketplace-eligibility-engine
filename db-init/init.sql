-- Walmart Transactability Engine — Database Initialization
-- Creates the ltree extension and per-service schemas

CREATE EXTENSION IF NOT EXISTS ltree;

CREATE SCHEMA IF NOT EXISTS item_svc;
CREATE SCHEMA IF NOT EXISTS eligibility_svc;
CREATE SCHEMA IF NOT EXISTS inventory_svc;
CREATE SCHEMA IF NOT EXISTS seller_svc;
