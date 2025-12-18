import os
import json
import random
import boto3
from datetime import datetime, timedelta
from faker import Faker
from pydantic import BaseModel, Field

MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_SECURE = False

AWS_S3_BUCKET = 'orders-archive'

START_DATE = datetime(2025, 12, 17)
END_DATE = datetime(2025, 12, 18)

TOTAL_ORDERS = 1000

ZONES = ['center']

class Order(BaseModel):
    order_id: int
    user_id: int
    scooter_id: int
    total_amount: int
    time_start: datetime
    time_finish: datetime | None = None

    model_config = {
        "populate_by_name": True
    }

fake = Faker()

def random_datetime(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

def random_finish(start, probability_finished=0.8):
    if random.random() < probability_finished:
        interval = random.expovariate(1/60)
        finish = start + timedelta(minutes=interval)
        finish = min(finish, start + timedelta(minutes=60))
        finish = max(finish, start + timedelta(seconds=1))
        return finish
    else:
        return None

orders = []
for order_id in range(1, TOTAL_ORDERS + 1):
    start_time = random_datetime(START_DATE, END_DATE)
    order = Order(
        order_id=order_id,
        user_id=random.randint(1, 1000),
        scooter_id=random.randint(1, 200),
        total_amount=random.randint(100, 10000),
        time_start=start_time,
        time_finish=random_finish(start_time),
    )
    orders.append(order)

session = boto3.session.Session()
s3 = session.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}' if not MINIO_SECURE else f'https://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

for order in orders:
    zone_id = random.choice(ZONES)
    dt = order.time_start
    path = f"orders/zone_id/{dt.year}/{dt.month:02}/{dt.day:02}/{order.order_id}.json"

    data = order.model_dump(mode='json')

    s3.put_object(
        Bucket=AWS_S3_BUCKET,
        Key=path,
        Body=json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
    )

    print(f"Uploaded: s3://{AWS_S3_BUCKET}/{path}")

print("Done!")
