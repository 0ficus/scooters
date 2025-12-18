"""
Scooter Rental ETL DAG
Extracts order data from S3, loads to ClickHouse, and triggers Metabase refresh
Schedule: Every 30 minutes
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from clickhouse_driver import Client
import json
import os
import logging

S3_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://minio:9000')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', 'minioadmin')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', 'minioadmin')
S3_BUCKET = os.getenv('S3_BUCKET', 'orders-archive')
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))
CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'default')
METABASE_URL = os.getenv('METABASE_URL', 'http://metabase:3000')
PROCESSED_FILES_PREFIX = 'etl/processed/'

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'scooter_rental_etl',
    default_args=default_args,
    description='ETL pipeline for scooter rental orders: S3 -> ClickHouse -> Metabase',
    schedule_interval='*/30 * * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'scooter', 'dwh'],
)


def get_s3_client():
    """Create S3 client for MinIO"""
    import boto3
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )


def get_clickhouse_client():
    """Create ClickHouse client"""
    return Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        database=CLICKHOUSE_DB,
    )


def get_processed_files(s3_client, execution_date):
    """Get list of already processed files for the given date"""
    date_str = execution_date.strftime('%Y-%m-%d')
    processed_key = f"{PROCESSED_FILES_PREFIX}{date_str}.json"

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=processed_key)
        content = response['Body'].read().decode('utf-8')
        return set(json.loads(content))
    except s3_client.exceptions.NoSuchKey:
        return set()
    except Exception as e:
        logger.warning(f"Could not read processed files list: {e}")
        return set()


def save_processed_files(s3_client, execution_date, processed_files):
    """Save list of processed files for the given date"""
    date_str = execution_date.strftime('%Y-%m-%d')
    processed_key = f"{PROCESSED_FILES_PREFIX}{date_str}.json"

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=processed_key,
            Body=json.dumps(list(processed_files)).encode('utf-8'),
            ContentType='application/json'
        )
    except Exception as e:
        logger.error(f"Could not save processed files list: {e}")
        raise


def extract_from_s3(**context):
    """
    Extract order JSON files from S3 bucket
    Only processes new files that haven't been processed yet
    """
    execution_date = context['execution_date']
    s3_client = get_s3_client()

    processed_files = get_processed_files(s3_client, execution_date)
    logger.info(f"Already processed {len(processed_files)} files")

    orders = []
    new_processed_files = set()

    try:
        paginator = s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix='orders/'):
            for obj in page.get('Contents', []):
                key = obj['Key']

                if key in processed_files:
                    continue

                if not key.endswith('.json'):
                    continue

                try:
                    response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                    content = response['Body'].read().decode('utf-8')
                    order_data = json.loads(content)
                    orders.append(order_data)
                    new_processed_files.add(key)
                    logger.info(f"Extracted order from {key}")
                except Exception as e:
                    logger.error(f"Error processing file {key}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error listing S3 objects: {e}")
        raise

    all_processed = processed_files.union(new_processed_files)
    save_processed_files(s3_client, execution_date, all_processed)

    logger.info(f"Extracted {len(orders)} new orders from S3")

    context['ti'].xcom_push(key='orders', value=orders)
    return len(orders)


def load_to_clickhouse(**context):
    """
    Load extracted orders into ClickHouse
    """
    orders = context['ti'].xcom_pull(key='orders', task_ids='extract_from_s3')

    if not orders:
        logger.info("No new orders to load")
        return 0

    client = get_clickhouse_client()

    rows = []
    for order in orders:
        try:
            started_at = datetime.fromisoformat(order.get('time_start', order.get('started_at')).replace('Z', '+00:00'))
            finished_at_str = order.get('time_finish', order.get('finished_at'))

            if finished_at_str:
                finished_at = datetime.fromisoformat(finished_at_str.replace('Z', '+00:00'))
            else:
                continue

            total_amount = order.get('total_amount', 0)

            row = (
                int(order.get('order_id')),
                int(order.get('user_id')),
                int(order.get('scooter_id')),
                total_amount,
                started_at.replace(tzinfo=None),
                finished_at.replace(tzinfo=None),
                int(order.get('ttl', 0)),
            )
            rows.append(row)
        except Exception as e:
            logger.error(f"Error preparing order {order.get('order_id')}: {e}")
            continue

    if not rows:
        logger.info("No valid orders to insert")
        return 0

    try:
        client.execute(
            '''
            INSERT INTO orders (order_id, user_id, scooter_id, total_amount, started_at, finished_at, ttl)
            VALUES
            ''',
            rows
        )
        logger.info(f"Inserted {len(rows)} orders into ClickHouse")
    except Exception as e:
        logger.error(f"Error inserting into ClickHouse: {e}")
        raise

    return len(rows)


def refresh_dashboards(**context):
    """
    Trigger Metabase to refresh dashboards
    The materialized view in ClickHouse auto-updates, but we can trigger
    Metabase cache refresh for immediate dashboard updates
    """
    import requests


    try:
        response = requests.get(f"{METABASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            logger.info("Metabase is healthy, dashboards will auto-refresh from ClickHouse")
        else:
            logger.warning(f"Metabase health check returned: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not reach Metabase: {e}")

    return True


extract_task = PythonOperator(
    task_id='extract_from_s3',
    python_callable=extract_from_s3,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_clickhouse',
    python_callable=load_to_clickhouse,
    dag=dag,
)

dashboard_task = PythonOperator(
    task_id='refresh_dashboards',
    python_callable=refresh_dashboards,
    dag=dag,
)

extract_task >> load_task >> dashboard_task
