-- JUMO Data Warehouse schema
-- Mounted at /docker-entrypoint-initdb.d/init.sql (auto-runs on first start)

CREATE TABLE IF NOT EXISTS revenue_by_ambassador (
    id             SERIAL PRIMARY KEY,
    ambassador_email VARCHAR(255)   NOT NULL,
    total_revenue  NUMERIC(14, 2)  NOT NULL DEFAULT 0,
    order_count    INTEGER         NOT NULL DEFAULT 0,
    window_date    DATE            NOT NULL,
    created_at     TIMESTAMP       NOT NULL DEFAULT NOW(),
    UNIQUE (ambassador_email, window_date)
);
CREATE INDEX IF NOT EXISTS idx_rba_window ON revenue_by_ambassador(window_date);

CREATE TABLE IF NOT EXISTS revenue_by_product (
    id             SERIAL PRIMARY KEY,
    product_title  VARCHAR(255)    NOT NULL,
    total_revenue  NUMERIC(14, 2)  NOT NULL DEFAULT 0,
    units_sold     INTEGER         NOT NULL DEFAULT 0,
    window_date    DATE            NOT NULL,
    created_at     TIMESTAMP       NOT NULL DEFAULT NOW(),
    UNIQUE (product_title, window_date)
);
CREATE INDEX IF NOT EXISTS idx_rbp_window ON revenue_by_product(window_date);

CREATE TABLE IF NOT EXISTS daily_order_summary (
    id                      SERIAL PRIMARY KEY,
    window_date             DATE           NOT NULL UNIQUE,
    total_orders            INTEGER        NOT NULL DEFAULT 0,
    total_admin_revenue     NUMERIC(14, 2) NOT NULL DEFAULT 0,
    total_ambassador_revenue NUMERIC(14, 2) NOT NULL DEFAULT 0,
    created_at              TIMESTAMP      NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dos_window ON daily_order_summary(window_date);

-- Used by Grafana/postgres_exporter to surface last Spark run time
CREATE TABLE IF NOT EXISTS pipeline_metadata (
    key        VARCHAR(100) PRIMARY KEY,
    value      TEXT         NOT NULL,
    updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

INSERT INTO pipeline_metadata (key, value, updated_at)
VALUES ('last_spark_run', 'never', NOW())
ON CONFLICT (key) DO NOTHING;
