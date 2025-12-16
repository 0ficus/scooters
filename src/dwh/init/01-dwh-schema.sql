-- =============================================
-- DWH Schema Initialization
-- Database: dwh_db
-- Architecture: STG -> DM (simplified, no DDS)
-- =============================================

-- Create schemas for different layers
CREATE SCHEMA IF NOT EXISTS stg;  -- Staging layer
CREATE SCHEMA IF NOT EXISTS dm;   -- Data Marts layer

-- =============================================
-- STG Layer: Staging tables (replicas from OLTP)
-- =============================================

-- STG: Offers table (replica from orders_db.offers)
CREATE TABLE IF NOT EXISTS stg.offers (
    offer_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    scooter_id INTEGER NOT NULL,
    time_offer_creation TIMESTAMPTZ NOT NULL,
    price_per_minute INTEGER NOT NULL,
    price_unlock INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    ttl INTEGER NOT NULL,
    loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stg_offers_user ON stg.offers (user_id);
CREATE INDEX IF NOT EXISTS idx_stg_offers_created ON stg.offers (time_offer_creation);

COMMENT ON TABLE stg.offers IS 'Staging table: replica of OLTP offers table';
COMMENT ON COLUMN stg.offers.loaded_at IS 'Timestamp when record was loaded into DWH';

-- STG: Orders table (replica from orders_db.orders)
CREATE TABLE IF NOT EXISTS stg.orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    scooter_id INTEGER NOT NULL,
    time_start TIMESTAMPTZ NOT NULL,
    time_finish TIMESTAMPTZ NULL,
    price_per_minute INTEGER NOT NULL,
    price_unlock INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    ttl INTEGER NOT NULL,
    loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stg_orders_user ON stg.orders (user_id);
CREATE INDEX IF NOT EXISTS idx_stg_orders_start ON stg.orders (time_start);
CREATE INDEX IF NOT EXISTS idx_stg_orders_finish ON stg.orders (time_finish);

COMMENT ON TABLE stg.orders IS 'Staging table: replica of OLTP orders table';
COMMENT ON COLUMN stg.orders.loaded_at IS 'Timestamp when record was loaded into DWH';

-- =============================================
-- DM Layer: Data Mart for Business Dashboard
-- =============================================

-- DM: Business Metrics Mart (aggregated daily metrics)
CREATE TABLE IF NOT EXISTS dm.business_metrics (
    metric_date DATE PRIMARY KEY,
    
    -- Revenue metrics
    total_revenue INTEGER NOT NULL DEFAULT 0,
    avg_order_price NUMERIC(10, 2) DEFAULT 0,
    
    -- Operational metrics
    orders_count INTEGER NOT NULL DEFAULT 0,
    offers_count INTEGER NOT NULL DEFAULT 0,
    conversion_rate NUMERIC(5, 2) DEFAULT 0,  -- percentage
    
    -- User metrics
    active_users_count INTEGER NOT NULL DEFAULT 0,
    
    -- Ride metrics
    avg_ride_duration_minutes NUMERIC(10, 2) DEFAULT 0,
    total_ride_minutes INTEGER DEFAULT 0,
    completed_orders_count INTEGER DEFAULT 0,
    
    -- Metadata
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    data_quality_score NUMERIC(3, 2) DEFAULT 1.0  -- 0.0 to 1.0
);

CREATE INDEX IF NOT EXISTS idx_dm_metrics_date ON dm.business_metrics (metric_date DESC);

COMMENT ON TABLE dm.business_metrics IS 'Data Mart: Daily aggregated business metrics for dashboard';
COMMENT ON COLUMN dm.business_metrics.total_revenue IS 'Total revenue from completed orders (price_unlock + price_per_minute * duration)';
COMMENT ON COLUMN dm.business_metrics.avg_order_price IS 'Average revenue per completed order';
COMMENT ON COLUMN dm.business_metrics.orders_count IS 'Total number of orders started';
COMMENT ON COLUMN dm.business_metrics.offers_count IS 'Total number of offers created';
COMMENT ON COLUMN dm.business_metrics.conversion_rate IS 'Percentage of offers converted to orders';
COMMENT ON COLUMN dm.business_metrics.active_users_count IS 'Number of unique users who created offers or orders';
COMMENT ON COLUMN dm.business_metrics.avg_ride_duration_minutes IS 'Average duration of completed rides in minutes';
COMMENT ON COLUMN dm.business_metrics.total_ride_minutes IS 'Total minutes of all completed rides';
COMMENT ON COLUMN dm.business_metrics.completed_orders_count IS 'Number of orders with time_finish set';
COMMENT ON COLUMN dm.business_metrics.calculated_at IS 'Timestamp when metrics were calculated';
COMMENT ON COLUMN dm.business_metrics.data_quality_score IS 'Quality score based on data completeness';

-- =============================================
-- Helper: ETL metadata table
-- =============================================

CREATE TABLE IF NOT EXISTS dm.etl_runs (
    run_id SERIAL PRIMARY KEY,
    dag_id VARCHAR(100) NOT NULL,
    task_id VARCHAR(100),
    execution_date TIMESTAMPTZ NOT NULL,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    status VARCHAR(20),  -- success, failed, running
    rows_processed INTEGER,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_etl_runs_date ON dm.etl_runs (execution_date DESC);

COMMENT ON TABLE dm.etl_runs IS 'Metadata about ETL process executions';

-- =============================================
-- Functions for metric calculations
-- =============================================

-- Function to calculate revenue from an order
CREATE OR REPLACE FUNCTION dm.calculate_order_revenue(
    p_price_unlock INTEGER,
    p_price_per_minute INTEGER,
    p_time_start TIMESTAMPTZ,
    p_time_finish TIMESTAMPTZ
) RETURNS INTEGER AS $$
BEGIN
    IF p_time_finish IS NULL THEN
        RETURN 0;
    END IF;
    
    RETURN p_price_unlock + 
           (p_price_per_minute * EXTRACT(EPOCH FROM (p_time_finish - p_time_start)) / 60)::INTEGER;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION dm.calculate_order_revenue IS 'Calculate total revenue for a completed order';

-- =============================================
-- Initial data quality check
-- =============================================

CREATE OR REPLACE VIEW dm.data_quality_summary AS
SELECT
    'stg.offers' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE user_id IS NULL) as null_user_ids,
    COUNT(*) FILTER (WHERE scooter_id IS NULL) as null_scooter_ids,
    MAX(loaded_at) as last_load_time
FROM stg.offers
UNION ALL
SELECT
    'stg.orders' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE user_id IS NULL) as null_user_ids,
    COUNT(*) FILTER (WHERE scooter_id IS NULL) as null_scooter_ids,
    MAX(loaded_at) as last_load_time
FROM stg.orders;

COMMENT ON VIEW dm.data_quality_summary IS 'Summary of data quality metrics for STG tables';

-- =============================================
-- Grant permissions
-- =============================================

GRANT USAGE ON SCHEMA stg TO dwh_user;
GRANT USAGE ON SCHEMA dm TO dwh_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA stg TO dwh_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dm TO dwh_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dm TO dwh_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA dm TO dwh_user;

-- =============================================
-- Initialization complete
-- =============================================

INSERT INTO dm.etl_runs (dag_id, task_id, execution_date, end_time, status, rows_processed, error_message)
VALUES ('init', 'schema_creation', NOW(), NOW(), 'success', 0, 'DWH schema initialized successfully');

