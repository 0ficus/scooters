# Scooter Rental DWH

## 1. Общее описание

Данный репозиторий содержит реализацию **хранилища данных (DWH)** для сервиса аренды самокатов.  
DWH предназначено для сбора, хранения, агрегации и аналитического использования данных о поездках пользователей.

Решение построено по классической аналитической архитектуре и включает:
- ingestion данных из объектного хранилища (S3 / MinIO),
- хранение и агрегацию данных в ClickHouse,
- оркестрацию ETL-процессов через Airflow,
- визуализацию метрик в Metabase.

---

## 2. Архитектура DWH

### 2.1 Логическая архитектура
```text
+----------------+
|  Микросервисы  |
+----------------+
         |
         ▼
+-------------------------+
|  S3 / MinIO             |
|  (Raw JSON orders)      |
+-------------------------+
         |
         ▼
+----------------+
|  Airflow ETL   |
+----------------+
         |
         ▼
+-------------------------+
|       ClickHouse        |
|-------------------------|
|  orders (ODS)           |
|  aggregated_metrics     |
|  (DDS / Data Mart)      |
+-------------------------+
         |
         ▼
+----------------+
|   Metabase     |
|  BI Dashboard  |
+----------------+
```

### 2.2 Физические технологии

| Слой | Технология |
|---|---|
| Object Storage | MinIO (S3-compatible) |
| ETL / Orchestration | Apache Airflow |
| DWH | ClickHouse |
| BI / Visualization | Metabase |
| Формат данных | JSON (raw), таблицы ClickHouse |

---

## 3. Модель данных DWH

### 3.1 Таблица `orders` (ODS слой)

**Описание:**  
Сырые данные о завершённых поездках, загружаемые напрямую из JSON-файлов микросервисов.  
В DWH ключевым полем для агрегаций является `total_amount`.

| Поле | Тип | Описание |
|---|---|---|
| order_id | UInt64 | Уникальный идентификатор заказа |
| user_id | UInt64 | Идентификатор пользователя |
| scooter_id | UInt64 | Идентификатор самоката |
| time_start | DateTime | Время начала поездки |
| time_finish | DateTime | Время окончания поездки |
| total_amount | UInt32 | Общая стоимость поездки |
| price_per_minute | UInt32 | Стоимость поездки за минуту  |
| price_unlock | UInt32 | Стоимость разблокировки самоката  |
| deposit | UInt32 | Депозит пользователя |
| ttl | UInt32 | Время жизни записи / служебное поле |

---

### 3.2 Материализованное представление `aggregated_metrics` (DDS / витрина)

**Описание:**  
Агрегированная витрина метрик, автоматически пересчитываемая при вставке данных в `orders`.

| Поле | Тип | Описание |
|---|---|---|
| metric_date | Date | Дата поездки |
| metric_tenmin | DateTime | Временной интервал 10 минут |
| total_revenue | UInt64 | Общая выручка |
| avg_order_price | Float64 | Средняя стоимость заказа |
| orders_count | UInt64 | Количество заказов |
| users_count | UInt64 | Количество уникальных пользователей |
| avg_ride_duration_minutes | Float64 | Средняя длительность поездки (мин) |
| calculated_at | DateTime | Время расчёта агрегата |

**Тип:**  
Materialized View (ClickHouse)

---

## 4. ETL-процессы

### 4.1 Оркестрация

ETL реализован в виде **Airflow DAG**:  
`scooter_rental_etl`

**Расписание:**  
Каждые 30 минут (`*/30 * * * *`)

---

### 4.2 Этапы ETL

#### Extract
- Источник: S3 / MinIO (`/orders/zone={zone-id}/year={year}/month={month}/day={day}/{order_id}.json`)
- Формат: JSON
- Загружаются **только новые файлы**
- Учёт обработанных файлов ведётся в:
etl/processed/YYYY-MM-DD.json

#### Transform
- Приведение типов
- Валидация дат
- Исключение незавершённых заказов
- Расчёт длительности поездки

#### Load
- Вставка данных в таблицу `orders`
- Материализованное представление `aggregated_metrics` обновляется автоматически

#### Post-load
- Проверка доступности Metabase
- Автообновление BI-дашбордов

---

## 5. Airflow DAG

**Файл:**  
`src/airflow/dags/scooter_rental_etl.py`

**Задачи DAG:**

| Task ID | Назначение |
|---|---|
| extract_from_s3 | Загрузка новых заказов из S3 |
| load_to_clickhouse | Запись данных в ClickHouse |
| refresh_dashboards | Проверка и обновление Metabase |

Порядок выполнения:
extract_from_s3 → load_to_clickhouse → refresh_dashboards

---

## 6. Инициализация ClickHouse

**Файл:**  
`/src/clickhouse/init/init-db.sh`

**Что делает скрипт:**
1. Ждёт доступности ClickHouse
2. Создаёт таблицу `orders`
3. Создаёт materialized view `aggregated_metrics`

Используется движок `MergeTree` для высокой производительности аналитических запросов.

---

## 7. BI и дашборды

### 7.1 Инструмент

**Metabase**

Подключается напрямую к ClickHouse.

---

### 7.2 Дашборд

**Название:**  
`Scooter Rental Analytics`

**Основные метрики:**
- Total Revenue
- Orders Count
- Users Count
- Average Ride Duration
- Average Order Price
- Revenue Over Time
- Orders Over Time
- Hourly Activity

Метрики строятся на основе таблицы `aggregated_metrics`.

---

### 7.3 Автоматический сетап дашбордов

**Файл:**  
`/src/metabase/setup/setup_dashboards.py`

**Возможности:**
- Авторизация в Metabase
- Создание подключения к ClickHouse
- Создание дашбордов и карточек
- Добавление карточек на дашборд

Конфигурация описана в файле:
`/src/metabase/setup/dashboards.json`

---
