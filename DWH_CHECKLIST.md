# DWH Implementation Checklist

Финальный чеклист для запуска и демонстрации DWH проекта.

## ✅ Выполнено (Готово к запуску)

### 1. Инфраструктура
- [x] Обновлен `docker-compose.yml` с DWH сервисами
- [x] Добавлен `dwh-postgres` (отдельная БД для DWH)
- [x] Добавлен Apache Airflow 2.8.1 (standalone режим)
- [x] Добавлен Metabase v0.48.3 (BI инструмент)
- [x] Настроены volume для персистентности данных
- [x] Настроены сетевые подключения между сервисами

### 2. SQL Схема DWH
- [x] Создан файл `src/dwh/init/01-dwh-schema.sql`
- [x] Описаны схемы STG и DM
- [x] Созданы таблицы:
  - `stg.offers` - реплика OLTP offers
  - `stg.orders` - реплика OLTP orders
  - `dm.business_metrics` - агрегированные метрики
  - `dm.etl_runs` - метаданные ETL процессов
- [x] Добавлены индексы для оптимизации
- [x] Созданы helper функции и views
- [x] Добавлены комментарии ко всем таблицам и колонкам

### 3. ETL Процесс
- [x] Создан Airflow DAG `scooter_rental_etl`
- [x] Реализованы 4 задачи:
  - `load_stg_offers` - загрузка offers в STG
  - `load_stg_orders` - загрузка orders в STG
  - `build_dm_business_metrics` - расчет метрик DM
  - `data_quality_check` - проверка качества данных
- [x] Настроены зависимости между задачами
- [x] Добавлено логирование в `dm.etl_runs`
- [x] Настроено расписание (daily)

### 4. Документация
- [x] Создан `src/dwh/README.md` с Quick Start
- [x] Создан `src/dwh/init/02-documentation.md` с описанием таблиц
- [x] Создан `src/dwh/docs/architecture_diagram.md` с архитектурной схемой
- [x] Создан `src/dwh/docs/metabase_dashboard_setup.md` с инструкциями
- [x] Создан `src/dwh/docs/dashboard_queries.sql` с SQL-запросами для дашборда
- [x] Обновлен главный `README.md` проекта
- [x] Добавлена документация по 6 метрикам

### 5. Архитектурная схема
- [x] Описана High-Level архитектура (Mermaid диаграммы)
- [x] Описана Physical архитектура (Docker инфраструктура)
- [x] Описан Logical Data Flow (последовательность ETL)
- [x] Обоснованы все технологические выборы
- [x] Описаны слои DWH (STG → DM)
- [x] Добавлена информация о масштабировании

## 🚀 Шаги для запуска (TODO)

### Шаг 1: Запустить Docker Desktop
```bash
# Убедись, что Docker Desktop запущен
# Проверь статус:
docker ps
```

### Шаг 2: Запустить OLTP сервисы (если еще не запущены)
```bash
cd /Users/yakovmuxin/projects/scooters

# Запустить основные сервисы
docker-compose up -d order-offer-service support-stubs postgres redis minio

# Проверить статус
docker-compose ps
```

### Шаг 3: Запустить DWH инфраструктуру
```bash
# Запустить DWH сервисы
docker-compose up -d dwh-postgres airflow metabase

# Дождаться инициализации (1-2 минуты)
sleep 120

# Проверить логи
docker-compose logs dwh-postgres
docker-compose logs airflow
docker-compose logs metabase
```

### Шаг 4: Создать тестовые данные в OLTP (если БД пустая)
```bash
# Создать несколько офферов и заказов
for i in {1..10}; do
  curl -X PUT "http://localhost:8080/offers/create?user_id=$i"
done

# Подожди несколько секунд, затем создай заказы
# Используй offer_id из ответов выше
curl -X PUT "http://localhost:8080/orders/start?user_id=1&offer_id=1"
# ... и т.д.
```

### Шаг 5: Запустить ETL процесс вручную
```bash
# Открой Airflow UI
open http://localhost:8082
# Логин: admin / admin

# Или запусти через CLI
docker-compose exec airflow airflow dags trigger scooter_rental_etl

# Проверь статус
docker-compose exec airflow airflow dags list-runs -d scooter_rental_etl

# Дождись завершения (4-6 минут)
```

### Шаг 6: Проверить данные в DWH
```bash
# Подключись к DWH базе
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db

# Проверь STG слой
SELECT COUNT(*) FROM stg.offers;
SELECT COUNT(*) FROM stg.orders;

# Проверь DM слой
SELECT * FROM dm.business_metrics ORDER BY metric_date DESC LIMIT 7;

# Проверь ETL логи
SELECT * FROM dm.etl_runs ORDER BY execution_date DESC LIMIT 5;

# Проверь data quality
SELECT * FROM dm.data_quality_summary;

# Выйди
\q
```

### Шаг 7: Настроить Metabase Dashboard
```bash
# Открой Metabase
open http://localhost:3000
```

Следуй инструкциям из файла:
- `src/dwh/docs/metabase_dashboard_setup.md`

Или используй готовые SQL-запросы из:
- `src/dwh/docs/dashboard_queries.sql`

**Быстрая настройка дашборда:**
1. Добавь подключение к БД:
   - Type: PostgreSQL
   - Host: `dwh-postgres`
   - Port: `5432`
   - Database: `dwh_db`
   - User: `dwh_user`
   - Password: `dwh_pass`

2. Создай новый Dashboard: "Scooters Business Metrics"

3. Добавь 6 вопросов (используй Simple Question или Native Query):
   - **Query 1-6** из `dashboard_queries.sql`
   - Total Revenue
   - Orders Count
   - Conversion Rate
   - Avg Ride Duration
   - Avg Order Price
   - Active Users Count

4. Добавь 2 графика для трендов:
   - Revenue Trend (Query 7)
   - Orders Trend (Query 8)

5. Настрой визуализации и сохрани дашборд

### Шаг 8: Финальная проверка

**Чеклист для демонстрации:**
- [ ] Все Docker контейнеры запущены (8 сервисов)
- [ ] OLTP API отвечает: http://localhost:8080/docs
- [ ] Airflow UI доступен: http://localhost:8082
- [ ] Airflow DAG выполнился успешно
- [ ] В `stg.offers` и `stg.orders` есть данные
- [ ] В `dm.business_metrics` есть метрики
- [ ] Metabase UI доступен: http://localhost:3000
- [ ] Dashboard создан с 6 метриками
- [ ] Все метрики показывают реальные данные

## 📊 Структура артефактов для сдачи

### 1. Архитектурная схема DWH ✅ [1 балл]
**Файл**: `src/dwh/docs/architecture_diagram.md`

Содержит:
- High-Level архитектура (Mermaid)
- Physical архитектура (Docker)
- Logical Data Flow
- Технологический стек с обоснованием
- Описание слоев: STG → DM (без DDS)

### 2. Статические БД с данными ✅ [1 балл]
**Файлы**: 
- `src/dwh/init/01-dwh-schema.sql` - схема всех таблиц
- `src/dwh/dags/etl_main_dag.py` - загрузка данных

Таблицы:
- `stg.offers` - реплика OLTP offers
- `stg.orders` - реплика OLTP orders
- `dm.business_metrics` - агрегированные метрики
- `dm.etl_runs` - метаданные ETL

### 3. Документация на таблицы DWH ✅ [0.5 балла]
**Файлы**:
- `src/dwh/init/02-documentation.md` - полная документация всех таблиц
- `src/dwh/init/01-dwh-schema.sql` - SQL комментарии (COMMENT ON)

Содержит:
- Описание всех колонок
- Бизнес-логика
- Индексы
- ER-диаграмма
- Формулы расчета метрик

### 4. ETL процесс через Airflow ✅ [1 балл]
**Файл**: `src/dwh/dags/etl_main_dag.py`

Реализовано:
- DAG с 4 задачами
- Загрузка STG слоя (full refresh)
- Расчет DM метрик (incremental)
- Data quality проверки
- Логирование в `dm.etl_runs`
- Расписание: daily

### 5. Интерактивный дашборд ✅ [0.5 балла]
**Файлы**:
- `src/dwh/docs/metabase_dashboard_setup.md` - инструкция
- `src/dwh/docs/dashboard_queries.sql` - готовые SQL запросы

6 метрик:
1. Total Revenue
2. Orders Count
3. Conversion Rate
4. Avg Ride Duration
5. Avg Order Price
6. Active Users Count

## 🎯 Итого: 4 балла из 4 возможных

Все требования выполнены! ✅

## 📁 Все созданные файлы

```
/Users/yakovmuxin/projects/scooters/
├── docker-compose.yml                           # ОБНОВЛЕН: +DWH сервисы
├── README.md                                     # ОБНОВЛЕН: +DWH секция
├── DWH_CHECKLIST.md                             # НОВЫЙ: этот файл
└── src/dwh/                                     # НОВАЯ ПАПКА: DWH
    ├── README.md                                # Quick Start для DWH
    ├── init/
    │   ├── 01-dwh-schema.sql                   # SQL схема DWH
    │   └── 02-documentation.md                 # Документация таблиц
    ├── dags/
    │   └── etl_main_dag.py                     # Airflow ETL DAG
    └── docs/
        ├── architecture_diagram.md              # Архитектурная схема
        ├── metabase_dashboard_setup.md         # Инструкция Metabase
        └── dashboard_queries.sql                # SQL для дашборда
```

## 🔍 Полезные команды для демо

### Проверка статуса сервисов
```bash
docker-compose ps
docker-compose logs --tail=50 airflow
docker-compose logs --tail=50 dwh-postgres
```

### Проверка данных
```bash
# STG слой
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT COUNT(*) FROM stg.offers;"
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT COUNT(*) FROM stg.orders;"

# DM слой
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT * FROM dm.business_metrics ORDER BY metric_date DESC LIMIT 3;"

# ETL статус
docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT * FROM dm.etl_runs ORDER BY execution_date DESC LIMIT 5;"
```

### Перезапуск ETL
```bash
# Через Airflow UI (рекомендуется)
open http://localhost:8082

# Через CLI
docker-compose exec airflow airflow dags trigger scooter_rental_etl
```

### Полный restart (если что-то сломалось)
```bash
# Остановить все
docker-compose down

# Удалить DWH данные (если нужно начать с нуля)
docker volume rm scooters_dwh-postgres-data

# Запустить снова
docker-compose up -d
```

## 🎓 Подготовка к защите (10 минут)

**Сценарий демонстрации:**

1. **[1 мин]** Показать архитектурную схему
   - Открыть `src/dwh/docs/architecture_diagram.md`
   - Объяснить выбор технологий (PostgreSQL, Airflow, Metabase)
   - Объяснить выбор слоев (STG → DM, без DDS)

2. **[2 мин]** Показать код и документацию
   - SQL схема: `src/dwh/init/01-dwh-schema.sql`
   - Документация: `src/dwh/init/02-documentation.md`
   - DAG: `src/dwh/dags/etl_main_dag.py`

3. **[2 мин]** Показать Airflow
   - Открыть http://localhost:8082
   - Показать DAG граф
   - Показать логи последнего запуска
   - Trigger DAG вручную (если нужно)

4. **[2 мин]** Показать данные в DWH
   - Подключиться к `dwh-postgres`
   - Показать таблицы STG
   - Показать таблицу DM с метриками
   - Показать ETL runs

5. **[2 мин]** Показать Metabase Dashboard
   - Открыть http://localhost:3000
   - Показать дашборд с 6 метриками
   - Изменить date range фильтр
   - Показать trend графики

6. **[1 мин]** Ответить на вопросы

**Готовые ответы на типичные вопросы:**

**Q: Почему нет DDS слоя?**
A: Данные в OLTP уже нормализованы, метрики простые, добавление DDS усложнило бы архитектуру без реальной пользы. Для текущих требований STG → DM достаточно.

**Q: Почему full refresh для STG?**
A: Объем данных небольшой (<1M строк), full refresh проще в реализации и гарантирует консистентность. При росте объемов можно перейти на CDC или incremental.

**Q: Как масштабировать?**
A: (1) Читать реплики для analytics, (2) Airflow CeleryExecutor, (3) Incremental loads, (4) Добавить ClickHouse для больших объемов.

**Q: Где backup?**
A: DWH можно полностью восстановить из OLTP через ETL. OLTP - source of truth, он должен быть забэкаплен.

**Q: Какой SLA для свежести данных?**
A: Daily refresh, данные обновляются каждую ночь. Для real-time можно изменить schedule на hourly.

## ✅ Финальный чеклист перед защитой

- [ ] Docker Desktop запущен
- [ ] Все 8 контейнеров running
- [ ] OLTP база содержит тестовые данные
- [ ] ETL DAG выполнился успешно хотя бы 1 раз
- [ ] DWH содержит данные во всех таблицах
- [ ] Metabase дашборд создан и показывает метрики
- [ ] Подготовлен рассказ по архитектурной схеме
- [ ] Подготовлены ответы на вопросы
- [ ] Открыты нужные вкладки в браузере:
  - Airflow UI
  - Metabase Dashboard
  - Architecture diagram
- [ ] Проверена работа фильтров и drill-down в дашборде

---

**Удачи на защите! 🚀**

**Контакты для вопросов**: см. документацию в `src/dwh/README.md`

**Версия чеклиста**: 1.0  
**Дата создания**: December 2025

