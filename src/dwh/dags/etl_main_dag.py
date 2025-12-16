"""
Main ETL DAG for Scooter Rental DWH
Loads data from OLTP to STG layer and builds DM layer
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
import logging

# Default arguments for DAG
default_args = {
    'owner': 'dwh_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'scooter_rental_etl',
    default_args=default_args,
    description='ETL pipeline for Scooter Rental DWH',
    schedule_interval='@daily',  # Run daily at midnight
    catchup=False,
    tags=['dwh', 'etl', 'scooters'],
)


def load_stg_offers(**context):
    """
    Load data from OLTP orders_db.offers to STG layer
    Uses full refresh strategy for simplicity
    """
    logging.info("Starting STG load for offers table")
    
    # Get connections
    oltp_hook = PostgresHook(postgres_conn_id='oltp_postgres')
    dwh_hook = PostgresHook(postgres_conn_id='dwh_postgres')
    
    # Extract from OLTP
    extract_sql = """
        SELECT 
            offer_id,
            user_id,
            scooter_id,
            time_offer_creation,
            price_per_minute,
            price_unlock,
            deposit,
            ttl
        FROM offers
        ORDER BY offer_id
    """
    
    logging.info("Extracting data from OLTP...")
    oltp_conn = oltp_hook.get_conn()
    oltp_cursor = oltp_conn.cursor()
    oltp_cursor.execute(extract_sql)
    rows = oltp_cursor.fetchall()
    oltp_cursor.close()
    oltp_conn.close()
    
    logging.info(f"Extracted {len(rows)} rows from OLTP offers")
    
    if len(rows) == 0:
        logging.warning("No data found in OLTP offers table")
        return
    
    # Clear STG table
    dwh_hook.run("TRUNCATE TABLE stg.offers")
    logging.info("Truncated stg.offers table")
    
    # Load into STG
    insert_sql = """
        INSERT INTO stg.offers (
            offer_id, user_id, scooter_id, time_offer_creation,
            price_per_minute, price_unlock, deposit, ttl, loaded_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """
    
    dwh_conn = dwh_hook.get_conn()
    dwh_cursor = dwh_conn.cursor()
    dwh_cursor.executemany(insert_sql, rows)
    dwh_conn.commit()
    dwh_cursor.close()
    dwh_conn.close()
    
    logging.info(f"Loaded {len(rows)} rows into stg.offers")
    
    # Log to ETL metadata
    dwh_hook.run(f"""
        INSERT INTO dm.etl_runs (dag_id, task_id, execution_date, end_time, status, rows_processed)
        VALUES ('scooter_rental_etl', 'load_stg_offers', NOW(), NOW(), 'success', {len(rows)})
    """)


def load_stg_orders(**context):
    """
    Load data from OLTP orders_db.orders to STG layer
    Uses full refresh strategy for simplicity
    """
    logging.info("Starting STG load for orders table")
    
    # Get connections
    oltp_hook = PostgresHook(postgres_conn_id='oltp_postgres')
    dwh_hook = PostgresHook(postgres_conn_id='dwh_postgres')
    
    # Extract from OLTP
    extract_sql = """
        SELECT 
            order_id,
            user_id,
            scooter_id,
            time_start,
            time_finish,
            price_per_minute,
            price_unlock,
            deposit,
            ttl
        FROM orders
        ORDER BY order_id
    """
    
    logging.info("Extracting data from OLTP...")
    oltp_conn = oltp_hook.get_conn()
    oltp_cursor = oltp_conn.cursor()
    oltp_cursor.execute(extract_sql)
    rows = oltp_cursor.fetchall()
    oltp_cursor.close()
    oltp_conn.close()
    
    logging.info(f"Extracted {len(rows)} rows from OLTP orders")
    
    if len(rows) == 0:
        logging.warning("No data found in OLTP orders table")
        return
    
    # Clear STG table
    dwh_hook.run("TRUNCATE TABLE stg.orders")
    logging.info("Truncated stg.orders table")
    
    # Load into STG
    insert_sql = """
        INSERT INTO stg.orders (
            order_id, user_id, scooter_id, time_start, time_finish,
            price_per_minute, price_unlock, deposit, ttl, loaded_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """
    
    dwh_conn = dwh_hook.get_conn()
    dwh_cursor = dwh_conn.cursor()
    dwh_cursor.executemany(insert_sql, rows)
    dwh_conn.commit()
    dwh_cursor.close()
    dwh_conn.close()
    
    logging.info(f"Loaded {len(rows)} rows into stg.orders")
    
    # Log to ETL metadata
    dwh_hook.run(f"""
        INSERT INTO dm.etl_runs (dag_id, task_id, execution_date, end_time, status, rows_processed)
        VALUES ('scooter_rental_etl', 'load_stg_orders', NOW(), NOW(), 'success', {len(rows)})
    """)


# Task 1: Load offers to STG
task_load_stg_offers = PythonOperator(
    task_id='load_stg_offers',
    python_callable=load_stg_offers,
    dag=dag,
)

# Task 2: Load orders to STG
task_load_stg_orders = PythonOperator(
    task_id='load_stg_orders',
    python_callable=load_stg_orders,
    dag=dag,
)

# Task 3: Build DM business metrics
task_build_dm_metrics = PostgresOperator(
    task_id='build_dm_business_metrics',
    postgres_conn_id='dwh_postgres',
    sql="""
        -- Delete existing metrics for the period we're recalculating
        DELETE FROM dm.business_metrics 
        WHERE metric_date >= CURRENT_DATE - INTERVAL '7 days';
        
        -- Calculate and insert daily metrics
        INSERT INTO dm.business_metrics (
            metric_date,
            total_revenue,
            avg_order_price,
            orders_count,
            offers_count,
            conversion_rate,
            active_users_count,
            avg_ride_duration_minutes,
            total_ride_minutes,
            completed_orders_count,
            calculated_at,
            data_quality_score
        )
        SELECT
            DATE(COALESCE(o.time_start, of.time_offer_creation)) as metric_date,
            
            -- Revenue metrics
            COALESCE(SUM(
                CASE 
                    WHEN o.time_finish IS NOT NULL 
                    THEN dm.calculate_order_revenue(
                        o.price_unlock, 
                        o.price_per_minute, 
                        o.time_start, 
                        o.time_finish
                    )
                    ELSE 0
                END
            ), 0) as total_revenue,
            
            COALESCE(AVG(
                CASE 
                    WHEN o.time_finish IS NOT NULL 
                    THEN dm.calculate_order_revenue(
                        o.price_unlock, 
                        o.price_per_minute, 
                        o.time_start, 
                        o.time_finish
                    )
                    ELSE NULL
                END
            ), 0) as avg_order_price,
            
            -- Operational metrics
            COUNT(DISTINCT o.order_id) as orders_count,
            COUNT(DISTINCT of.offer_id) as offers_count,
            
            CASE 
                WHEN COUNT(DISTINCT of.offer_id) > 0 
                THEN (COUNT(DISTINCT o.order_id)::NUMERIC / COUNT(DISTINCT of.offer_id) * 100)
                ELSE 0 
            END as conversion_rate,
            
            -- User metrics
            COUNT(DISTINCT COALESCE(o.user_id, of.user_id)) as active_users_count,
            
            -- Ride metrics
            COALESCE(AVG(
                CASE 
                    WHEN o.time_finish IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (o.time_finish - o.time_start)) / 60
                    ELSE NULL
                END
            ), 0) as avg_ride_duration_minutes,
            
            COALESCE(SUM(
                CASE 
                    WHEN o.time_finish IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (o.time_finish - o.time_start)) / 60
                    ELSE 0
                END
            ), 0) as total_ride_minutes,
            
            COUNT(DISTINCT CASE WHEN o.time_finish IS NOT NULL THEN o.order_id END) as completed_orders_count,
            
            NOW() as calculated_at,
            
            -- Data quality: 1.0 if we have both offers and orders, 0.5 if only one
            CASE 
                WHEN COUNT(DISTINCT of.offer_id) > 0 AND COUNT(DISTINCT o.order_id) > 0 THEN 1.0
                WHEN COUNT(DISTINCT of.offer_id) > 0 OR COUNT(DISTINCT o.order_id) > 0 THEN 0.5
                ELSE 0.0
            END as data_quality_score
            
        FROM stg.offers of
        FULL OUTER JOIN stg.orders o 
            ON DATE(of.time_offer_creation) = DATE(o.time_start)
        WHERE DATE(COALESCE(o.time_start, of.time_offer_creation)) >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(COALESCE(o.time_start, of.time_offer_creation))
        ORDER BY metric_date DESC;
        
        -- Log ETL run
        INSERT INTO dm.etl_runs (dag_id, task_id, execution_date, end_time, status, rows_processed)
        VALUES ('scooter_rental_etl', 'build_dm_business_metrics', NOW(), NOW(), 'success', 
                (SELECT COUNT(*) FROM dm.business_metrics WHERE calculated_at >= NOW() - INTERVAL '1 minute'));
    """,
    dag=dag,
)

# Task 4: Data quality check
task_data_quality_check = PostgresOperator(
    task_id='data_quality_check',
    postgres_conn_id='dwh_postgres',
    sql="""
        DO $$
        DECLARE
            stg_offers_count INTEGER;
            stg_orders_count INTEGER;
            dm_metrics_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO stg_offers_count FROM stg.offers;
            SELECT COUNT(*) INTO stg_orders_count FROM stg.orders;
            SELECT COUNT(*) INTO dm_metrics_count FROM dm.business_metrics 
            WHERE calculated_at >= NOW() - INTERVAL '1 hour';
            
            RAISE NOTICE 'Data Quality Check:';
            RAISE NOTICE '  STG Offers: % rows', stg_offers_count;
            RAISE NOTICE '  STG Orders: % rows', stg_orders_count;
            RAISE NOTICE '  DM Metrics: % rows', dm_metrics_count;
            
            -- Log quality check
            INSERT INTO dm.etl_runs (dag_id, task_id, execution_date, end_time, status, rows_processed, error_message)
            VALUES ('scooter_rental_etl', 'data_quality_check', NOW(), NOW(), 'success', 
                    stg_offers_count + stg_orders_count + dm_metrics_count,
                    FORMAT('STG Offers: %s, STG Orders: %s, DM Metrics: %s', 
                           stg_offers_count, stg_orders_count, dm_metrics_count));
        END $$;
    """,
    dag=dag,
)

# Define task dependencies
task_load_stg_offers >> task_build_dm_metrics
task_load_stg_orders >> task_build_dm_metrics
task_build_dm_metrics >> task_data_quality_check

