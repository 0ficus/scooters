-- =============================================
-- Metabase Dashboard SQL Queries
-- Pre-built queries for 6 business metrics
-- =============================================

-- Query 1: Total Revenue (Last 30 Days)
-- Use as: Number visualization
-- Format: Currency (divide by 100 for rubles)
SELECT 
    COALESCE(SUM(total_revenue) / 100.0, 0) as total_revenue_rubles
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================

-- Query 2: Total Orders Count (Last 30 Days)
-- Use as: Number visualization
-- Format: Integer with trend
SELECT 
    COALESCE(SUM(orders_count), 0) as total_orders
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================

-- Query 3: Average Conversion Rate (Last 30 Days)
-- Use as: Gauge visualization (0-100%)
-- Format: Percentage with suffix "%"
SELECT 
    COALESCE(AVG(conversion_rate), 0) as avg_conversion_rate
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================

-- Query 4: Average Ride Duration (Last 30 Days)
-- Use as: Number visualization
-- Format: Float with suffix " min"
SELECT 
    COALESCE(AVG(avg_ride_duration_minutes), 0) as avg_duration
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================

-- Query 5: Average Order Price (Last 30 Days)
-- Use as: Number visualization
-- Format: Currency (divide by 100)
SELECT 
    COALESCE(AVG(avg_order_price) / 100.0, 0) as avg_price_rubles
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================

-- Query 6: Active Users Count (Last 30 Days)
-- Use as: Number visualization
-- Format: Integer with user icon
SELECT 
    COALESCE(SUM(active_users_count), 0) as total_active_users
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================
-- BONUS: Trend Charts
-- =============================================

-- Query 7: Revenue Trend (Daily, Last 30 Days)
-- Use as: Line chart
-- X-axis: Date, Y-axis: Revenue
SELECT 
    metric_date as date,
    total_revenue / 100.0 as revenue_rubles
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date ASC;

-- =============================================

-- Query 8: Orders Trend (Daily, Last 30 Days)
-- Use as: Line chart
-- X-axis: Date, Y-axis: Orders
SELECT 
    metric_date as date,
    orders_count as orders
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date ASC;

-- =============================================

-- Query 9: Conversion Rate Trend (Daily, Last 30 Days)
-- Use as: Line chart with goal line at 75%
-- X-axis: Date, Y-axis: Conversion %
SELECT 
    metric_date as date,
    conversion_rate as conversion_pct
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date ASC;

-- =============================================

-- Query 10: Multi-Metric Overview Table
-- Use as: Table visualization
-- Shows all key metrics by date
SELECT 
    metric_date as "Date",
    total_revenue / 100.0 as "Revenue (₽)",
    orders_count as "Orders",
    offers_count as "Offers",
    conversion_rate as "Conv. %",
    active_users_count as "Users",
    avg_ride_duration_minutes as "Avg Duration (min)",
    completed_orders_count as "Completed",
    data_quality_score as "Data Quality"
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date DESC;

-- =============================================
-- Comparison Queries (Current vs Previous Period)
-- =============================================

-- Query 11: Revenue Comparison (Current 30d vs Previous 30d)
-- Use as: Bar chart or number with trend
WITH current_period AS (
    SELECT SUM(total_revenue) / 100.0 as revenue
    FROM dm.business_metrics
    WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
),
previous_period AS (
    SELECT SUM(total_revenue) / 100.0 as revenue
    FROM dm.business_metrics
    WHERE metric_date >= CURRENT_DATE - INTERVAL '60 days'
      AND metric_date < CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    c.revenue as current_revenue,
    p.revenue as previous_revenue,
    ((c.revenue - p.revenue) / NULLIF(p.revenue, 0) * 100) as growth_percent
FROM current_period c, previous_period p;

-- =============================================

-- Query 12: Week-over-Week Growth
-- Use as: Table showing weekly trends
SELECT 
    DATE_TRUNC('week', metric_date) as week_start,
    SUM(total_revenue) / 100.0 as weekly_revenue,
    SUM(orders_count) as weekly_orders,
    AVG(conversion_rate) as avg_conversion,
    SUM(active_users_count) as weekly_active_users
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', metric_date)
ORDER BY week_start DESC;

-- =============================================
-- Data Quality & Monitoring Queries
-- =============================================

-- Query 13: Data Freshness Check
-- Use as: Alert or status indicator
SELECT 
    MAX(metric_date) as last_metric_date,
    CURRENT_DATE - MAX(metric_date) as days_since_update,
    CASE 
        WHEN CURRENT_DATE - MAX(metric_date) = 0 THEN '✅ Fresh'
        WHEN CURRENT_DATE - MAX(metric_date) = 1 THEN '⚠️ 1 day old'
        ELSE '❌ Outdated'
    END as freshness_status
FROM dm.business_metrics;

-- =============================================

-- Query 14: Data Quality Score Trend
-- Use as: Line chart to monitor data quality
SELECT 
    metric_date as date,
    data_quality_score * 100 as quality_percent,
    CASE 
        WHEN data_quality_score >= 0.9 THEN '✅ Excellent'
        WHEN data_quality_score >= 0.7 THEN '⚠️ Good'
        ELSE '❌ Poor'
    END as quality_status
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date ASC;

-- =============================================

-- Query 15: ETL Run Status (Last 10 runs)
-- Use as: Table to monitor ETL health
SELECT 
    dag_id,
    task_id,
    execution_date,
    status,
    rows_processed,
    EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds,
    error_message
FROM dm.etl_runs
WHERE dag_id = 'scooter_rental_etl'
ORDER BY execution_date DESC
LIMIT 10;

-- =============================================
-- Advanced Analytics Queries
-- =============================================

-- Query 16: Cohort Analysis - Revenue by User Acquisition Date
-- Shows revenue breakdown by when users first appeared
WITH user_first_date AS (
    SELECT 
        user_id,
        MIN(DATE(time_offer_creation)) as first_seen_date
    FROM stg.offers
    GROUP BY user_id
),
order_revenue AS (
    SELECT 
        o.user_id,
        DATE(o.time_start) as order_date,
        dm.calculate_order_revenue(
            o.price_unlock, 
            o.price_per_minute, 
            o.time_start, 
            o.time_finish
        ) as revenue
    FROM stg.orders o
    WHERE o.time_finish IS NOT NULL
)
SELECT 
    DATE_TRUNC('week', ufd.first_seen_date) as cohort_week,
    COUNT(DISTINCT o.user_id) as users_count,
    SUM(o.revenue) / 100.0 as total_revenue,
    AVG(o.revenue) / 100.0 as avg_revenue_per_user
FROM user_first_date ufd
LEFT JOIN order_revenue o ON o.user_id = ufd.user_id
WHERE ufd.first_seen_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', ufd.first_seen_date)
ORDER BY cohort_week DESC;

-- =============================================

-- Query 17: Scooter Utilization Analysis
-- Shows which scooters are most used
SELECT 
    scooter_id,
    COUNT(*) as ride_count,
    SUM(EXTRACT(EPOCH FROM (time_finish - time_start)) / 60) as total_minutes,
    AVG(EXTRACT(EPOCH FROM (time_finish - time_start)) / 60) as avg_ride_duration,
    SUM(dm.calculate_order_revenue(
        price_unlock, price_per_minute, time_start, time_finish
    )) / 100.0 as total_revenue
FROM stg.orders
WHERE time_finish IS NOT NULL
  AND time_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY scooter_id
ORDER BY ride_count DESC
LIMIT 20;

-- =============================================

-- Query 18: Hourly Demand Pattern
-- Shows when users most frequently start rides
SELECT 
    EXTRACT(HOUR FROM time_start) as hour_of_day,
    COUNT(*) as orders_count,
    AVG(EXTRACT(EPOCH FROM (time_finish - time_start)) / 60) as avg_duration,
    SUM(dm.calculate_order_revenue(
        price_unlock, price_per_minute, time_start, time_finish
    )) / 100.0 as hourly_revenue
FROM stg.orders
WHERE time_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY EXTRACT(HOUR FROM time_start)
ORDER BY hour_of_day;

-- =============================================

-- Query 19: Conversion Funnel Detail
-- Shows drop-off at each stage
WITH funnel_data AS (
    SELECT 
        DATE(time_offer_creation) as date,
        COUNT(*) as offers_created
    FROM stg.offers
    WHERE time_offer_creation >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY DATE(time_offer_creation)
),
orders_data AS (
    SELECT 
        DATE(time_start) as date,
        COUNT(*) as orders_started,
        COUNT(CASE WHEN time_finish IS NOT NULL THEN 1 END) as orders_completed
    FROM stg.orders
    WHERE time_start >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY DATE(time_start)
)
SELECT 
    f.date,
    f.offers_created as "1. Offers Created",
    COALESCE(o.orders_started, 0) as "2. Orders Started",
    COALESCE(o.orders_completed, 0) as "3. Orders Completed",
    ROUND(COALESCE(o.orders_started::NUMERIC / NULLIF(f.offers_created, 0) * 100, 0), 2) as "Conv: Offer→Order %",
    ROUND(COALESCE(o.orders_completed::NUMERIC / NULLIF(o.orders_started, 0) * 100, 0), 2) as "Conv: Start→Complete %"
FROM funnel_data f
LEFT JOIN orders_data o ON f.date = o.date
ORDER BY f.date DESC;

-- =============================================

-- Query 20: Revenue Forecast (Simple Linear Trend)
-- Extrapolates revenue based on last 30 days
WITH daily_revenue AS (
    SELECT 
        metric_date,
        total_revenue / 100.0 as revenue,
        EXTRACT(EPOCH FROM (metric_date - MIN(metric_date) OVER ())) / 86400 as day_index
    FROM dm.business_metrics
    WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
),
stats AS (
    SELECT 
        AVG(day_index) as avg_x,
        AVG(revenue) as avg_y,
        SUM((day_index - AVG(day_index) OVER ()) * (revenue - AVG(revenue) OVER ())) as numerator,
        SUM(POWER(day_index - AVG(day_index) OVER (), 2)) as denominator
    FROM daily_revenue
),
trend AS (
    SELECT 
        numerator / NULLIF(denominator, 0) as slope,
        avg_y - (numerator / NULLIF(denominator, 0)) * avg_x as intercept
    FROM stats
)
SELECT 
    '30-Day Projected Revenue' as metric,
    ROUND((slope * 30 + intercept) * 30, 2) as projected_monthly_revenue
FROM trend;

-- =============================================
-- End of Dashboard Queries
-- =============================================

-- Usage Instructions:
-- 1. Copy desired query to Metabase "New Question" → "Native Query"
-- 2. Select database: "Scooters DWH"
-- 3. Run query and choose appropriate visualization
-- 4. Save and add to dashboard
-- 5. Customize visualization settings (colors, labels, formats)

