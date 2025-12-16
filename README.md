# Scooter Rental Service

Backend service for electric scooter short-term rentals with integrated Data Warehouse for business analytics.

## 📚 Documentation

- **ADR (Architecture Decision Record)**: [ADR.md](docs/ADR.md)
- **DWH Documentation**: [src/dwh/README.md](src/dwh/README.md)
- **DWH Architecture**: [src/dwh/docs/architecture_diagram.md](src/dwh/docs/architecture_diagram.md)

## 🏗️ Architecture

### OLTP Service (Microservice)
- **Service**: `order-offer-service` - FastAPI application for scooter rentals
- **Database**: PostgreSQL (offers, orders tables)
- **Storage**: MinIO S3 for order archives
- **Cache**: Redis for zone and config caching

### DWH (Data Warehouse)
- **Database**: PostgreSQL DWH (separate instance)
- **ETL**: Apache Airflow with daily scheduled DAGs
- **BI**: Metabase dashboards
- **Layers**: STG (Staging) → DM (Data Marts)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 8 GB RAM minimum
- Ports available: 8080, 8081, 8082, 3000, 5433, 5434, 6379, 9000, 9001

### 1. Start All Services

```bash
# Start OLTP services
docker-compose up -d order-offer-service support-stubs postgres redis minio

# Start DWH services
docker-compose up -d dwh-postgres airflow metabase
```

### 2. Verify Services

```bash
docker-compose ps
```

Expected services:
- `order-offer-service` - Port 8080 (OLTP API)
- `support-stubs` - Port 8081 (Mock external services)
- `postgres` - Port 5433 (OLTP database)
- `dwh-postgres` - Port 5434 (DWH database)
- `airflow` - Port 8082 (ETL orchestration)
- `metabase` - Port 3000 (BI dashboards)
- `redis` - Port 6379 (Cache)
- `minio` - Port 9000, 9001 (S3 storage)

### 3. Access Services

**OLTP API**:
- URL: http://localhost:8080
- Docs: http://localhost:8080/docs

**Airflow (ETL)**:
- URL: http://localhost:8082
- Username: `admin`
- Password: `admin`

**Metabase (Dashboards)**:
- URL: http://localhost:3000
- Setup required on first run

**MinIO Console**:
- URL: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

## 📊 DWH & Analytics

### ETL Pipeline

Daily ETL process loads data from OLTP to DWH:

1. **STG Layer**: Replica OLTP tables (offers, orders)
2. **DM Layer**: Aggregated business metrics

### Dashboard Metrics (6 Key Metrics)

1. **Total Revenue** - Revenue from completed orders
2. **Orders Count** - Number of rental orders
3. **Conversion Rate** - Offers → Orders conversion %
4. **Avg Ride Duration** - Average ride time in minutes
5. **Avg Order Price** - Average revenue per order
6. **Active Users Count** - Unique users

### Run ETL Manually

```bash
# Trigger ETL DAG in Airflow
docker-compose exec airflow airflow dags trigger scooter_rental_etl

# Check ETL status
docker-compose exec airflow airflow dags list-runs -d scooter_rental_etl
```

See [DWH README](src/dwh/README.md) for detailed setup instructions.

## 🧪 Testing

### Run Tests

```bash
docker-compose up tests
```

### Manual API Testing

```bash
# Create offer
curl -X PUT "http://localhost:8080/offers/create?user_id=1"

# Start order (use offer_id from previous response)
curl -X PUT "http://localhost:8080/orders/start?user_id=1&offer_id=1"

# Get order info
curl -X GET "http://localhost:8080/orders/get?user_id=1&order_id=1"

# Stop order
curl -X PUT "http://localhost:8080/orders/stop?user_id=1&order_id=1"
```

## 🗂️ Project Structure

```
scooters/
├── docker-compose.yml              # All services configuration
├── README.md                       # This file
├── docs/
│   ├── ADR.md                      # Architecture decisions
│   └── scooters_scheme.svg         # Architecture diagram
├── src/
│   ├── order_offer_service/        # OLTP microservice
│   │   ├── app/                    # FastAPI application
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── support_stubs/              # Mock external services
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── postgres/
│   │   └── init/
│   │       └── 01-schema.sql       # OLTP schema
│   └── dwh/                        # Data Warehouse (NEW)
│       ├── README.md               # DWH documentation
│       ├── init/
│       │   ├── 01-dwh-schema.sql   # DWH schema
│       │   └── 02-documentation.md # Tables docs
│       ├── dags/
│       │   └── etl_main_dag.py     # Airflow ETL DAG
│       └── docs/
│           ├── architecture_diagram.md
│           └── metabase_dashboard_setup.md
└── TestingRecord.md                # Testing documentation
```

## 🔧 Configuration

### Environment Variables

All configuration is in `docker-compose.yml`:

- **OLTP Database**: `orders_user:orders_pass@postgres:5432/orders_db`
- **DWH Database**: `dwh_user:dwh_pass@dwh-postgres:5432/dwh_db`
- **S3 Storage**: `minioadmin:minioadmin@minio:9000`
- **Redis Cache**: `redis://redis:6379/0`

### ETL Schedule

Default: Daily at midnight

To change, edit `src/dwh/dags/etl_main_dag.py`:

```python
schedule_interval='@daily',  # Change to '@hourly', etc.
```

## 🐛 Troubleshooting

### OLTP Service Issues

```bash
# Check logs
docker-compose logs order-offer-service

# Restart service
docker-compose restart order-offer-service
```

### ETL/DWH Issues

```bash
# Check Airflow logs
docker-compose logs airflow

# Check DWH database
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db

# Verify data in STG layer
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT COUNT(*) FROM stg.offers;"
```

### Database Connection Issues

```bash
# Test OLTP database
docker-compose exec postgres psql -U orders_user -d orders_db -c "SELECT 1;"

# Test DWH database
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT 1;"
```

## 📈 Performance

### OLTP Service
- **RPS**: 100 orders/sec (design capacity)
- **Latency**: < 200ms for offer creation
- **Storage**: Orders archived to S3 after completion

### DWH ETL
- **Frequency**: Daily
- **Duration**: 4-6 minutes
- **Data Volume**: ~30k offers, ~720k orders

## 🔐 Security

- All services isolated in Docker network
- No public database access
- Credentials in environment variables (change in production!)
- S3 buckets with TTL for GDPR compliance

## 📦 Backup & Recovery

### Backup OLTP Database

```bash
docker-compose exec postgres pg_dump -U orders_user orders_db > oltp_backup.sql
```

### Backup DWH Database

```bash
docker-compose exec dwh-postgres pg_dump -U dwh_user dwh_db > dwh_backup.sql
```

### Restore Database

```bash
cat oltp_backup.sql | docker-compose exec -T postgres psql -U orders_user orders_db
```

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Apache Airflow**: https://airflow.apache.org/docs/
- **Metabase**: https://www.metabase.com/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/

## 📞 Support

For questions or issues:
1. Check service logs: `docker-compose logs [service-name]`
2. Review documentation in respective folders
3. Check `TestingRecord.md` for known issues

---

**Project Version**: 2.0 (with DWH)  
**Last Updated**: December 2025
