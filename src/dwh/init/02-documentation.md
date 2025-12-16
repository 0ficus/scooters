# DWH Documentation: Scooter Rental Service

## Overview

This document describes the Data Warehouse (DWH) structure for the Scooter Rental Service. The DWH follows a simplified 2-layer architecture:

- **STG (Staging)**: Raw data replicas from OLTP sources
- **DM (Data Marts)**: Aggregated business metrics for dashboards and analytics

**Database**: `dwh_db`  
**DBMS**: PostgreSQL 15  
**ETL Tool**: Apache Airflow 2.8.1  
**BI Tool**: Metabase v0.48.3

---

## Architecture Layers

### Layer 1: STG (Staging)

Purpose: Store raw replicas of operational data from the OLTP database.

**Refresh Strategy**: Full refresh (TRUNCATE + INSERT)  
**Refresh Frequency**: Daily (via Airflow DAG)  
**Data Retention**: Last 7 days

### Layer 2: DM (Data Marts)

Purpose: Store aggregated business metrics for dashboard visualization.

**Refresh Strategy**: Incremental (DELETE period + INSERT)  
**Refresh Frequency**: Daily (via Airflow DAG)  
**Data Retention**: 1 year

---

## STG Layer Tables

### stg.offers

Replica of the `orders_db.offers` table from OLTP.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `offer_id` | INTEGER | NOT NULL | Primary key, unique identifier for offer |
| `user_id` | INTEGER | NOT NULL | Foreign key reference to user |
| `scooter_id` | INTEGER | NOT NULL | Foreign key reference to scooter |
| `time_offer_creation` | TIMESTAMPTZ | NOT NULL | Timestamp when offer was created |
| `price_per_minute` | INTEGER | NOT NULL | Price per minute in kopecks |
| `price_unlock` | INTEGER | NOT NULL | Unlock fee in kopecks |
| `deposit` | INTEGER | NOT NULL | Deposit amount in kopecks |
| `ttl` | INTEGER | NOT NULL | Time-to-live for offer in seconds |
| `loaded_at` | TIMESTAMPTZ | NOT NULL | Timestamp when record was loaded into DWH |

**Indexes**:
- `idx_stg_offers_user` on `user_id`
- `idx_stg_offers_created` on `time_offer_creation`

**Business Logic**:
- Offers are valid for TTL duration (typically 5 minutes)
- Users receive offers before starting a rental order
- Not all offers convert to orders

**Data Volume Estimate**: ~30,000 active offers at any time

---

### stg.orders

Replica of the `orders_db.orders` table from OLTP.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `order_id` | INTEGER | NOT NULL | Primary key, unique identifier for order |
| `user_id` | INTEGER | NOT NULL | Foreign key reference to user |
| `scooter_id` | INTEGER | NOT NULL | Foreign key reference to scooter |
| `time_start` | TIMESTAMPTZ | NOT NULL | Timestamp when rental started |
| `time_finish` | TIMESTAMPTZ | NULL | Timestamp when rental finished (NULL if ongoing) |
| `price_per_minute` | INTEGER | NOT NULL | Price per minute in kopecks |
| `price_unlock` | INTEGER | NOT NULL | Unlock fee in kopecks |
| `deposit` | INTEGER | NOT NULL | Deposit amount in kopecks |
| `ttl` | INTEGER | NOT NULL | Time-to-live for order record in seconds |
| `loaded_at` | TIMESTAMPTZ | NOT NULL | Timestamp when record was loaded into DWH |

**Indexes**:
- `idx_stg_orders_user` on `user_id`
- `idx_stg_orders_start` on `time_start`
- `idx_stg_orders_finish` on `time_finish`

**Business Logic**:
- Orders represent actual scooter rentals
- `time_finish` is NULL for active (ongoing) orders
- Completed orders have both `time_start` and `time_finish` set
- Revenue is calculated as: `price_unlock + (price_per_minute * duration_in_minutes)`

**Data Volume Estimate**: ~720,000 active orders at any time, ~100 RPS for new orders

---

## DM Layer Tables

### dm.business_metrics

Daily aggregated business metrics for the main dashboard.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `metric_date` | DATE | NOT NULL | Date of the metrics (primary key) |
| `total_revenue` | INTEGER | NOT NULL | Total revenue in kopecks from completed orders |
| `avg_order_price` | NUMERIC(10, 2) | NULL | Average revenue per completed order in kopecks |
| `orders_count` | INTEGER | NOT NULL | Total number of orders started |
| `offers_count` | INTEGER | NOT NULL | Total number of offers created |
| `conversion_rate` | NUMERIC(5, 2) | NULL | Percentage of offers converted to orders (0-100) |
| `active_users_count` | INTEGER | NOT NULL | Number of unique users who created offers or orders |
| `avg_ride_duration_minutes` | NUMERIC(10, 2) | NULL | Average duration of completed rides in minutes |
| `total_ride_minutes` | INTEGER | NULL | Total minutes of all completed rides |
| `completed_orders_count` | INTEGER | NULL | Number of orders with `time_finish` set |
| `calculated_at` | TIMESTAMPTZ | NOT NULL | Timestamp when metrics were calculated |
| `data_quality_score` | NUMERIC(3, 2) | NULL | Data quality score (0.0 - 1.0) |

**Indexes**:
- `idx_dm_metrics_date` on `metric_date DESC`

**Business Logic**:
- Metrics are calculated daily based on STG data
- Revenue is only counted for completed orders (`time_finish IS NOT NULL`)
- Conversion rate = (orders_count / offers_count) * 100
- Data quality score: 1.0 = both offers and orders present, 0.5 = only one, 0.0 = none

**Calculation Formula**:

```sql
total_revenue = SUM(price_unlock + (price_per_minute * duration_in_minutes))
avg_order_price = AVG(total_revenue) for completed orders
conversion_rate = (COUNT(DISTINCT order_id) / COUNT(DISTINCT offer_id)) * 100
avg_ride_duration = AVG(EXTRACT(EPOCH FROM (time_finish - time_start)) / 60)
```

**Dashboard Metrics** (6 required):
1. **Total Revenue** (`total_revenue`)
2. **Orders Count** (`orders_count`)
3. **Conversion Rate** (`conversion_rate`)
4. **Average Ride Duration** (`avg_ride_duration_minutes`)
5. **Average Order Price** (`avg_order_price`)
6. **Active Users Count** (`active_users_count`)

---

### dm.etl_runs

Metadata table for ETL process monitoring and debugging.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `run_id` | SERIAL | NOT NULL | Primary key, auto-incrementing ID |
| `dag_id` | VARCHAR(100) | NOT NULL | Airflow DAG identifier |
| `task_id` | VARCHAR(100) | NULL | Airflow task identifier |
| `execution_date` | TIMESTAMPTZ | NOT NULL | Execution timestamp |
| `start_time` | TIMESTAMPTZ | NOT NULL | Task start time |
| `end_time` | TIMESTAMPTZ | NULL | Task end time |
| `status` | VARCHAR(20) | NULL | Execution status (success, failed, running) |
| `rows_processed` | INTEGER | NULL | Number of rows processed |
| `error_message` | TEXT | NULL | Error message if failed |

**Indexes**:
- `idx_etl_runs_date` on `execution_date DESC`

**Business Logic**:
- Each ETL task logs its execution to this table
- Used for monitoring, debugging, and auditing
- Helps identify data freshness and ETL issues

---

## Helper Functions

### dm.calculate_order_revenue

Calculates total revenue for a completed order.

**Signature**:
```sql
dm.calculate_order_revenue(
    p_price_unlock INTEGER,
    p_price_per_minute INTEGER,
    p_time_start TIMESTAMPTZ,
    p_time_finish TIMESTAMPTZ
) RETURNS INTEGER
```

**Formula**:
```
revenue = price_unlock + (price_per_minute * duration_in_minutes)
```

**Returns**: `0` if order is not finished (`time_finish IS NULL`)

---

## Helper Views

### dm.data_quality_summary

Real-time view of data quality metrics for STG tables.

**Columns**:
- `table_name`: Name of the STG table
- `total_rows`: Total number of rows
- `null_user_ids`: Count of NULL user_id values
- `null_scooter_ids`: Count of NULL scooter_id values
- `last_load_time`: Timestamp of last data load

**Usage**:
```sql
SELECT * FROM dm.data_quality_summary;
```

---

## ER Diagram

```
┌─────────────────┐         ┌─────────────────┐
│   stg.offers    │         │   stg.orders    │
├─────────────────┤         ├─────────────────┤
│ offer_id (PK)   │         │ order_id (PK)   │
│ user_id         │         │ user_id         │
│ scooter_id      │         │ scooter_id      │
│ time_offer_...  │         │ time_start      │
│ price_per_min   │         │ time_finish     │
│ price_unlock    │         │ price_per_min   │
│ deposit         │         │ price_unlock    │
│ ttl             │         │ deposit         │
│ loaded_at       │         │ ttl             │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │    ┌──────────────────────┘
         │    │
         └────┼────────────────────┐
              │                    │
              ▼                    ▼
      ┌────────────────────────────────┐
      │  dm.business_metrics           │
      ├────────────────────────────────┤
      │ metric_date (PK)               │
      │ total_revenue                  │
      │ avg_order_price                │
      │ orders_count                   │
      │ offers_count                   │
      │ conversion_rate                │
      │ active_users_count             │
      │ avg_ride_duration_minutes      │
      │ total_ride_minutes             │
      │ completed_orders_count         │
      │ calculated_at                  │
      │ data_quality_score             │
      └────────────────────────────────┘
```

---

## ETL Process

### DAG: `scooter_rental_etl`

**Schedule**: Daily at midnight (`@daily`)  
**File**: `src/dwh/dags/etl_main_dag.py`

**Tasks**:

1. **load_stg_offers**: Load data from OLTP `offers` to `stg.offers`
   - Strategy: TRUNCATE + INSERT (full refresh)
   - Duration: ~1-2 minutes

2. **load_stg_orders**: Load data from OLTP `orders` to `stg.orders`
   - Strategy: TRUNCATE + INSERT (full refresh)
   - Duration: ~2-3 minutes

3. **build_dm_business_metrics**: Calculate daily metrics for dashboard
   - Strategy: DELETE period + INSERT (incremental)
   - Duration: ~30 seconds
   - Depends on: tasks 1 and 2

4. **data_quality_check**: Verify data completeness and log results
   - Strategy: Count rows and log to `dm.etl_runs`
   - Duration: ~5 seconds
   - Depends on: task 3

**Dependency Graph**:
```
load_stg_offers ──┐
                  ├──> build_dm_business_metrics ──> data_quality_check
load_stg_orders ──┘
```

**Connections Required**:
- `oltp_postgres`: Connection to source OLTP database
- `dwh_postgres`: Connection to target DWH database

---

## Data Refresh Schedule

| Layer | Table | Refresh Type | Frequency | Retention |
|-------|-------|--------------|-----------|-----------|
| STG | offers | Full | Daily | 7 days |
| STG | orders | Full | Daily | 7 days |
| DM | business_metrics | Incremental | Daily | 1 year |
| DM | etl_runs | Append | Per task | 1 year |

---

## Access Permissions

All tables are accessible to `dwh_user` with full permissions (SELECT, INSERT, UPDATE, DELETE).

For BI tools (Metabase), grant read-only access:

```sql
GRANT USAGE ON SCHEMA dm TO metabase_user;
GRANT SELECT ON ALL TABLES IN SCHEMA dm TO metabase_user;
```

---

## Monitoring & Alerts

### Key Metrics to Monitor:

1. **ETL Execution Time**: Should complete within 5 minutes
2. **Data Freshness**: `loaded_at` should be within 24 hours
3. **Data Quality Score**: Should be >= 0.8
4. **Row Counts**: STG tables should have non-zero rows

### Queries for Monitoring:

```sql
-- Check last ETL run status
SELECT * FROM dm.etl_runs 
ORDER BY execution_date DESC 
LIMIT 10;

-- Check data freshness
SELECT table_name, last_load_time 
FROM dm.data_quality_summary;

-- Check latest metrics
SELECT * FROM dm.business_metrics 
ORDER BY metric_date DESC 
LIMIT 7;
```

---

## Maintenance

### Weekly Tasks:
- Review ETL logs for errors
- Verify data quality scores
- Check disk space usage

### Monthly Tasks:
- Analyze query performance and add indexes if needed
- Review and optimize slow queries
- Backup DWH database

### Yearly Tasks:
- Purge old ETL logs (older than 1 year)
- Archive old business metrics if needed

---

## Contact & Support

**DWH Team**: dwh_team@scooters.com  
**On-call**: Use Airflow UI to monitor DAG runs at http://localhost:8082

---

*Document Version: 1.0*  
*Last Updated: December 2025*

