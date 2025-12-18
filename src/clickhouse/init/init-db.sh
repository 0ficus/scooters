#!/bin/bash
set -e

CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-clickhouse}"

until clickhouse-client --host "$CLICKHOUSE_HOST" --query "SELECT 1" > /dev/null 2>&1; do
    echo "Waiting for ClickHouse to be ready..."
    sleep 2
done

echo "ClickHouse is ready. Creating schema..."

clickhouse-client --host "$CLICKHOUSE_HOST" --query "
CREATE TABLE IF NOT EXISTS orders (
    order_id UInt64,
    user_id UInt64,
    scooter_id UInt64,
    total_price UInt32,
    started_at DateTime,
    finished_at DateTime,
    ttl UInt32
) ENGINE = MergeTree()
ORDER BY (order_id)
PRIMARY KEY (order_id)
"

echo "Orders table created."

clickhouse-client --host "$CLICKHOUSE_HOST" --query "
CREATE MATERIALIZED VIEW IF NOT EXISTS aggregated_metrics
ENGINE = MergeTree()
ORDER BY (metric_date, metric_tenmin)
POPULATE
AS
SELECT
    toDate(started_at) as metric_date,
    toStartOfTenMinutes(started_at) as metric_tenmin,
    sum(total_price) as total_revenue,
    avg(total_price) as avg_order_price,
    count(*) as orders_count,
    count(DISTINCT user_id) as users_count,
    avg(toUnixTimestamp(finished_at) - toUnixTimestamp(started_at)) / 60 as avg_ride_duration_minutes,
    now() as calculated_at
FROM orders
WHERE finished_at > toDateTime('1970-01-01 00:00:00')
GROUP BY metric_date, metric_tenmin
"

echo "Aggregated metrics materialized view created."
echo "ClickHouse schema initialization complete!"
