import os
import json
import random
import numpy as np
import boto3
from datetime import datetime, timedelta
from faker import Faker
from pydantic import BaseModel, Field
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns
from collections import defaultdict

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_SECURE = False
AWS_S3_BUCKET = 'orders-archive'

START_DATE = datetime(2025, 12, 15)
END_DATE = datetime(2025, 12, 22)
TOTAL_ORDERS = 5000

ZONES = {
    'center': 0.4,
    'north': 0.2,
    'south': 0.15,
    'east': 0.15,
    'west': 0.1
}

WEEKDAYS_RU = ['Mon', 'Tue', 'Wen', 'Thu', 'Fri', 'Sat', 'Sun']

class GenerationConfig:
    TOTAL_USERS = 1500
    ACTIVE_USERS = 800
    
    TOTAL_SCOOTERS = 350
    ACTIVE_SCOOTERS = 250
    
    RIDE_LAMBDA = 25
    
    COST_LAMBDA = 5000
    
    PEAK_HOURS = {
        'morning': (7, 10, 0.35),
        'day': (11, 16, 0.25),
        'evening': (17, 21, 0.30),
        'night': (22, 6, 0.1)
    }
    
    COMPLETION_RATE = 0.92
    
    WEEKDAY_WEIGHTS = {
        0: 1.0,
        1: 1.1,
        2: 1.2,
        3: 1.3,
        4: 1.4,
        5: 1.5,
        6: 0.7
    }

class Order(BaseModel):
    order_id: int
    user_id: int
    scooter_id: int
    zone_id: str
    total_amount: int
    time_start: datetime
    time_finish: Optional[datetime] = None
    ride_duration: Optional[int] = None
    ride_distance: Optional[int] = None
    
    model_config = {
        "populate_by_name": True
    }

fake = Faker('ru_RU')

def weighted_random_choice(choices):
    zones = list(choices.keys())
    weights = list(choices.values())
    return random.choices(zones, weights=weights, k=1)[0]

def generate_peak_hour_time(date):
    period = weighted_random_choice({
        'morning': GenerationConfig.PEAK_HOURS['morning'][2],
        'day': GenerationConfig.PEAK_HOURS['day'][2],
        'evening': GenerationConfig.PEAK_HOURS['evening'][2],
        'night': GenerationConfig.PEAK_HOURS['night'][2]
    })
    
    if period == 'morning':
        hour = random.randint(*GenerationConfig.PEAK_HOURS['morning'][:2])
    elif period == 'day':
        hour = random.randint(*GenerationConfig.PEAK_HOURS['day'][:2])
    elif period == 'evening':
        hour = random.randint(*GenerationConfig.PEAK_HOURS['evening'][:2])
    else:
        hour = random.randint(22, 23) if random.random() < 0.5 else random.randint(0, 6)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=hour,
        minute=minute,
        second=second
    )

def generate_ride_duration():
    duration = np.random.poisson(GenerationConfig.RIDE_LAMBDA)
    return max(1, min(duration, 120))

def generate_ride_cost(duration):
    base_cost = np.random.poisson(1500)
    minute_cost = np.random.poisson(70) * duration
    
    total_cost = base_cost + minute_cost
    total_cost = int(total_cost * (0.8 + random.random() * 0.4))
    
    return max(1000, min(total_cost, 30000))

def generate_ride_distance(duration):
    avg_speed = 166
    distance = int(avg_speed * duration * (0.7 + random.random() * 0.6))
    return max(100, min(distance, 10000))

def weighted_day_selection(start_date, end_date):
    delta = end_date - start_date
    days = []
    weights = []
    
    for i in range(delta.days):
        current_date = start_date + timedelta(days=i)
        weekday = current_date.weekday()
        days.append(current_date)
        weights.append(GenerationConfig.WEEKDAY_WEIGHTS[weekday])
    
    return random.choices(days, weights=weights, k=1)[0]

def generate_orders(total_orders):
    orders = []
    
    active_users = random.sample(range(1, GenerationConfig.TOTAL_USERS + 1), 
                                GenerationConfig.ACTIVE_USERS)
    active_scooters = random.sample(range(1, GenerationConfig.TOTAL_SCOOTERS + 1), 
                                   GenerationConfig.ACTIVE_SCOOTERS)
    
    print("Generation...")
    for order_id in range(1, total_orders + 1):
        if order_id % 500 == 0:
            print(f"  Generated: {order_id}/{total_orders}")
        
        date = weighted_day_selection(START_DATE, END_DATE)    
        time_start = generate_peak_hour_time(date)
        
        duration = generate_ride_duration()
        ride_distance = generate_ride_distance(duration)
        total_amount = generate_ride_cost(duration)
        
        is_completed = random.random() < GenerationConfig.COMPLETION_RATE
        time_finish = None
        if is_completed:
            time_finish = time_start + timedelta(minutes=duration)
        
        order = Order(
            order_id=order_id,
            user_id=random.choice(active_users),
            scooter_id=random.choice(active_scooters),
            zone_id=weighted_random_choice(ZONES),
            total_amount=total_amount,
            time_start=time_start,
            time_finish=time_finish,
            ride_duration=duration if is_completed else None,
            ride_distance=ride_distance if is_completed else None
        )
        orders.append(order)
    
    return orders

def upload_to_s3(orders):
    print("Upload in S3/MinIO...")
    
    session = boto3.session.Session()
    s3 = session.client(
        's3',
        endpoint_url=f'http://{MINIO_ENDPOINT}' if not MINIO_SECURE else f'https://{MINIO_ENDPOINT}',
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )
    
    uploaded = 0
    for order in orders:
        dt = order.time_start
        path = f"orders/zone_id={order.zone_id}/year={dt.year}/month={dt.month:02}/day={dt.day:02}/{order.order_id}.json"
        
        data = order.model_dump(mode='json')
        
        s3.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=path,
            Body=json.dumps(data, ensure_ascii=False, default=str, indent=2).encode('utf-8')
        )
        
        uploaded += 1
        if uploaded % 500 == 0:
            print(f"  Uploaded: {uploaded}/{len(orders)}")
    
    return uploaded

def main():
    orders = generate_orders(TOTAL_ORDERS)
    
    completed_orders = [o for o in orders if o.time_finish]
    total_revenue = sum(o.total_amount for o in orders)
    avg_duration = np.mean([o.ride_duration for o in completed_orders if o.ride_duration])
    avg_cost = np.mean([o.total_amount for o in orders])
    
    hour_stats = {}
    for hour in range(24):
        hour_stats[hour] = sum(1 for o in orders if o.time_start.hour == hour)
    
    zone_stats = {}
    for order in orders:
        zone_stats[order.zone_id] = zone_stats.get(order.zone_id, 0) + 1
    
    weekday_stats = {}
    for order in orders:
        weekday = order.time_start.weekday()
        weekday_stats[weekday] = weekday_stats.get(weekday, 0) + 1
    
    stats = {
        'generation_date': datetime.now().isoformat(),
        'period': {
            'start': START_DATE.isoformat(),
            'end': END_DATE.isoformat(),
            'days': (END_DATE - START_DATE).days
        },
        'orders': {
            'total': len(orders),
            'completed': len(completed_orders),
            'completion_rate': len(completed_orders) / len(orders),
            'cancelled': len(orders) - len(completed_orders)
        },
        'financial': {
            'total_revenue_kop': total_revenue,
            'total_revenue_rub': total_revenue / 100,
            'avg_cost_kop': avg_cost,
            'avg_cost_rub': avg_cost / 100,
            'avg_revenue_per_user': total_revenue / GenerationConfig.ACTIVE_USERS / 100
        },
        'duration': {
            'avg_minutes': float(avg_duration),
            'median_minutes': float(np.median([o.ride_duration for o in completed_orders if o.ride_duration])),
            'max_minutes': int(max(o.ride_duration for o in completed_orders if o.ride_duration))
        },
        'users': {
            'total_registered': GenerationConfig.TOTAL_USERS,
            'active_this_week': GenerationConfig.ACTIVE_USERS,
            'activity_rate': GenerationConfig.ACTIVE_USERS / GenerationConfig.TOTAL_USERS
        },
        'scooters': {
            'total': GenerationConfig.TOTAL_SCOOTERS,
            'active': GenerationConfig.ACTIVE_SCOOTERS,
            'utilization_rate': GenerationConfig.ACTIVE_SCOOTERS / GenerationConfig.TOTAL_SCOOTERS
        },
        'hourly_distribution': hour_stats,
        'zone_distribution': zone_stats,
        'weekday_distribution': {WEEKDAYS_RU[k]: v for k, v in weekday_stats.items()},
        'generation_config': {
            'ride_lambda': GenerationConfig.RIDE_LAMBDA,
            'cost_lambda': GenerationConfig.COST_LAMBDA,
            'completion_rate': GenerationConfig.COMPLETION_RATE
        }
    }
    
    print("\nStatistics:")
    print("=" * 40)
    print(f"Total trips: {stats['orders']['total']}")
    print(f"Completed: {stats['orders']['completed']} ({stats['orders']['completion_rate']*100:.1f}%)")
    print(f"Canceled: {stats['orders']['cancelled']}")
    print(f"Total revenue: {stats['financial']['total_revenue_rub']:,.2f} руб.")
    print(f"Average trip cost: {stats['financial']['avg_cost_rub']:.2f} руб.")
    print(f"Average duration: {stats['duration']['avg_minutes']:.1f} мин")
    print(f"Active users: {stats['users']['active_this_week']}")
    print(f"Active scooters: {stats['scooters']['active']}")
    print()
    
    print("Distribution by zones:")
    print("-" * 30)
    for zone, count in sorted(zone_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(orders) * 100
        print(f"  {zone:<10} {count:>5} ({percentage:>5.1f}%)")
    
    print()
    print("Distribution by days of the week:")
    print("-" * 30)
    for i in range(7):
        count = weekday_stats.get(i, 0)
        percentage = count / len(orders) * 100 if len(orders) > 0 else 0
        print(f"  {WEEKDAYS_RU[i]:<3} {count:>5} ({percentage:>5.1f}%)")
    
    print()
    print("Peak hours:")
    print("-" * 30)
    top_hours = sorted(hour_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for hour, count in top_hours:
        percentage = count / len(orders) * 100
        print(f"  {hour:02d}:00-{hour:02d}:59 {count:>5} ({percentage:>5.1f}%)")
    
    print("\n" + "=" * 40)
    
    uploaded_count = upload_to_s3(orders)
    print(f"Uploaded to S3: {uploaded_count} orders")
        
    with open('generation_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
    
    print("Statistics saved in 'generation_stats.json'")
    print("Data generation completed successfully")

if __name__ == "__main__":
    main()