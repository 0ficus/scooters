# DWH for Scooter Rental Service

Data Warehouse implementation for analyzing scooter rental business metrics.

## 🏗️ Architecture

- **STG Layer**: Staging tables with raw replicas from OLTP
- **DM Layer**: Aggregated business metrics for dashboards
- **ETL**: Apache Airflow with daily scheduled DAGs
- **BI**: Metabase dashboards

See [architecture_diagram.md](docs/architecture_diagram.md) for detailed architecture.

## 📊 Dashboard Metrics

1. **Total Revenue** - Revenue from completed orders
2. **Orders Count** - Number of rental orders
3. **Conversion Rate** - Offers → Orders conversion
4. **Avg Ride Duration** - Average ride time in minutes
5. **Avg Order Price** - Average revenue per order
6. **Active Users** - Unique users count

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Existing OLTP service running (`order-offer-service`)

### 1. Start All Services

From project root:

```bash
docker-compose up -d dwh-postgres airflow metabase
```

Wait 1-2 minutes for initialization.

### 2. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

Expected services:
- `dwh-postgres` - Port 5434
- `airflow` - Port 8082
- `metabase` - Port 3000

### 3. Access UIs

**Airflow**:
- URL: http://localhost:8082
- Username: `admin`
- Password: `admin`

**Metabase**:
- URL: http://localhost:3000
- First time: Follow setup wizard
- Database connection details:
  - Type: PostgreSQL
  - Host: `dwh-postgres`
  - Port: `5432`
  - Database: `dwh_db`
  - Username: `dwh_user`
  - Password: `dwh_pass`

### 4. Generate Test Data (Optional)

If OLTP database is empty, generate test data:

```bash
# Create some test offers and orders
curl -X PUT "http://localhost:8080/offers/create?user_id=1"
curl -X PUT "http://localhost:8080/orders/start?user_id=1&offer_id=1"
# ... etc
```

### 5. Run ETL Manually

In Airflow UI:
1. Navigate to DAGs
2. Find `scooter_rental_etl`
3. Click "Trigger DAG" (play button)
4. Wait for completion (~5 minutes)

### 6. Create Metabase Dashboard

In Metabase:
1. Add database connection (see step 3)
2. Create new dashboard
3. Add 6 questions (one per metric):
   - Query table: `dm.business_metrics`
   - Visualizations: Line charts, numbers, gauges

## 📁 Project Structure

```
src/dwh/
├── README.md                       # This file
├── init/
│   ├── 01-dwh-schema.sql          # Database schema
│   └── 02-documentation.md        # Tables documentation
├── dags/
│   └── etl_main_dag.py            # Airflow ETL DAG
└── docs/
    └── architecture_diagram.md    # Architecture documentation
```

## 🔧 Configuration

### Airflow Connections

Connections are automatically configured via environment variables:

- **oltp_postgres**: Source OLTP database
  ```
  postgresql://orders_user:orders_pass@postgres:5432/orders_db
  ```

- **dwh_postgres**: Target DWH database
  ```
  postgresql://dwh_user:dwh_pass@dwh-postgres:5432/dwh_db
  ```

### ETL Schedule

Default: Daily at midnight (`@daily`)

To change schedule, edit `src/dwh/dags/etl_main_dag.py`:

```python
schedule_interval='@daily',  # Change to '@hourly', '0 */4 * * *', etc.
```

## 📝 Documentation

- **Tables**: [02-documentation.md](init/02-documentation.md)
- **Architecture**: [architecture_diagram.md](docs/architecture_diagram.md)
- **SQL Schema**: [01-dwh-schema.sql](init/01-dwh-schema.sql)

## 🔍 Monitoring

### Check ETL Status

```sql
-- Connect to dwh_db
SELECT * FROM dm.etl_runs 
ORDER BY execution_date DESC 
LIMIT 10;
```

### Check Data Freshness

```sql
SELECT * FROM dm.data_quality_summary;
```

### Check Latest Metrics

```sql
SELECT * FROM dm.business_metrics 
ORDER BY metric_date DESC 
LIMIT 7;
```

## 🐛 Troubleshooting

### ETL DAG Not Appearing in Airflow

1. Check DAG file for syntax errors:
   ```bash
   docker-compose exec airflow airflow dags list
   ```

2. Check Airflow logs:
   ```bash
   docker-compose logs airflow
   ```

### No Data in DM Layer

1. Verify STG tables have data:
   ```sql
   SELECT COUNT(*) FROM stg.offers;
   SELECT COUNT(*) FROM stg.orders;
   ```

2. Check if OLTP has data:
   ```bash
   docker-compose exec postgres psql -U orders_user -d orders_db -c "SELECT COUNT(*) FROM offers;"
   ```

3. Run ETL manually in Airflow UI

### Metabase Can't Connect to Database

1. Verify dwh-postgres is running:
   ```bash
   docker-compose ps dwh-postgres
   ```

2. Test connection:
   ```bash
   docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT 1;"
   ```

3. Use `dwh-postgres` as hostname (not `localhost`)

## 🧪 Testing

### Manual ETL Test

```bash
# Trigger DAG via Airflow CLI
docker-compose exec airflow airflow dags trigger scooter_rental_etl

# Watch DAG run
docker-compose exec airflow airflow dags list-runs -d scooter_rental_etl
```

### Data Quality Check

```sql
-- Connect to dwh_db
SELECT 
    metric_date,
    orders_count,
    offers_count,
    conversion_rate,
    data_quality_score
FROM dm.business_metrics
WHERE data_quality_score < 0.8
ORDER BY metric_date DESC;
```

## 📈 Performance

Expected ETL execution times:

| Task | Duration | Threshold |
|------|----------|-----------|
| load_stg_offers | 1-2 min | < 5 min |
| load_stg_orders | 2-3 min | < 10 min |
| build_dm_metrics | 30 sec | < 2 min |
| data_quality_check | 5 sec | < 30 sec |
| **Total** | **4-6 min** | **< 15 min** |

## 🔐 Security

- All credentials stored in `docker-compose.yml` environment variables
- Airflow has read-only access to OLTP database
- Metabase has read-only access to DM schema

## 📦 Backup & Recovery

### Backup DWH Database

```bash
docker-compose exec dwh-postgres pg_dump -U dwh_user dwh_db > dwh_backup.sql
```

### Restore DWH Database

```bash
cat dwh_backup.sql | docker-compose exec -T dwh-postgres psql -U dwh_user dwh_db
```

### Rebuild from Scratch

```bash
# Drop and recreate DWH
docker-compose down dwh-postgres
docker volume rm scooters_dwh-postgres-data
docker-compose up -d dwh-postgres

# Wait 30 seconds for init
sleep 30

# Run ETL
docker-compose exec airflow airflow dags trigger scooter_rental_etl
```

## 🎓 Learning Resources

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [Metabase Docs](https://www.metabase.com/docs/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

## 📞 Support

For questions or issues:
1. Check logs: `docker-compose logs [service-name]`
2. Review documentation in `init/` and `docs/`
3. Contact DWH team

---

**Version**: 1.0  
**Last Updated**: December 2025

