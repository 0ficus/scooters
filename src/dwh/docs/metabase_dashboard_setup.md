# Metabase Dashboard Setup Guide

Step-by-step guide to create the business metrics dashboard in Metabase.

## Prerequisites

- Metabase running on http://localhost:3000
- DWH database populated with data
- ETL DAG has run at least once

## Step 1: Initial Setup

1. Open http://localhost:3000 in your browser
2. If first time:
   - Select "Let's get started"
   - Create admin account (any email/password)
   - Click "Next"

## Step 2: Add Database Connection

1. Click "Add a database"
2. Fill in the details:

   ```
   Database type: PostgreSQL
   Name: Scooters DWH
   Host: dwh-postgres
   Port: 5432
   Database name: dwh_db
   Username: dwh_user
   Password: dwh_pass
   ```

3. Click "Save"
4. Wait for "Connected successfully" message

## Step 3: Create Dashboard

1. Click "New" → "Dashboard"
2. Name it: "Scooters Business Metrics"
3. Description: "Daily business metrics for scooter rental service"
4. Click "Create"

## Step 4: Add Metric Cards

Now we'll add 6 cards (questions) for each metric.

### Card 1: Total Revenue

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics` (from `dm` schema)
4. Add filter: `Metric Date is in the past 30 days`
5. Summarize by: `Sum of Total Revenue`
6. Visualization: **Number**
7. Click "Save"
8. Name: "Total Revenue (Last 30 Days)"
9. Click "Save" and add to dashboard

**Formatting**:
- Click on the card → Settings
- Style: Number
- Number format: Currency (divide by 100 for rubles)
- Prefix: "₽"

---

### Card 2: Orders Count

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Summarize by: `Sum of Orders Count`
6. Visualization: **Number**
7. Click "Save"
8. Name: "Total Orders (Last 30 Days)"
9. Click "Save" and add to dashboard

**Formatting**:
- Style: Number
- Number format: Integer
- Show trend: Enable (compare to previous 30 days)

---

### Card 3: Conversion Rate

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Summarize by: `Average of Conversion Rate`
6. Visualization: **Gauge**
7. Click "Save"
8. Name: "Offer → Order Conversion Rate"
9. Click "Save" and add to dashboard

**Formatting**:
- Gauge style: Dial
- Min: 0
- Max: 100
- Suffix: "%"
- Color ranges:
  - 0-50%: Red
  - 50-75%: Yellow
  - 75-100%: Green

---

### Card 4: Average Ride Duration

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Summarize by: `Average of Avg Ride Duration Minutes`
6. Visualization: **Number**
7. Click "Save"
8. Name: "Average Ride Duration"
9. Click "Save" and add to dashboard

**Formatting**:
- Style: Number
- Number format: Float (1 decimal)
- Suffix: " min"
- Show trend: Enable

---

### Card 5: Average Order Price

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Summarize by: `Average of Avg Order Price`
6. Visualization: **Number**
7. Click "Save"
8. Name: "Average Order Price"
9. Click "Save" and add to dashboard

**Formatting**:
- Style: Number
- Number format: Currency (divide by 100)
- Prefix: "₽"
- Show trend: Enable

---

### Card 6: Active Users Count

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Summarize by: `Sum of Active Users Count`
6. Visualization: **Number**
7. Click "Save"
8. Name: "Active Users (Last 30 Days)"
9. Click "Save" and add to dashboard

**Formatting**:
- Style: Number
- Number format: Integer
- Show trend: Enable
- Icon: User

---

## Step 5: Add Trend Charts

For better visualization, add trend line charts:

### Revenue Trend

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Group by: `Metric Date` (by Day)
6. Summarize: `Sum of Total Revenue`
7. Visualization: **Line chart**
8. Save as: "Revenue Trend (30 Days)"
9. Add to dashboard

**Formatting**:
- X-axis: Date
- Y-axis: Revenue (currency format)
- Line color: Green
- Show data points: Yes

### Orders Trend

1. Click "Add a question"
2. Choose "Simple question"
3. Select table: `Business Metrics`
4. Add filter: `Metric Date is in the past 30 days`
5. Group by: `Metric Date` (by Day)
6. Summarize: `Sum of Orders Count`
7. Visualization: **Line chart**
8. Save as: "Orders Trend (30 Days)"
9. Add to dashboard

**Formatting**:
- X-axis: Date
- Y-axis: Orders Count
- Line color: Blue
- Show goal line: Optional (e.g., 3000 orders/month)

---

## Step 6: Dashboard Layout

Arrange cards in a logical layout:

```
┌─────────────────────────────────────────────────┐
│  Scooters Business Metrics Dashboard            │
├──────────────┬──────────────┬──────────────────┤
│ Total Revenue│ Orders Count │ Active Users     │
│   (Number)   │   (Number)   │   (Number)       │
├──────────────┼──────────────┼──────────────────┤
│ Avg Order $  │ Avg Duration │ Conversion Rate  │
│   (Number)   │   (Number)   │   (Gauge)        │
├──────────────┴──────────────┴──────────────────┤
│         Revenue Trend (Line Chart)              │
├─────────────────────────────────────────────────┤
│         Orders Trend (Line Chart)               │
└─────────────────────────────────────────────────┘
```

To arrange:
1. Click "Edit dashboard"
2. Drag cards to desired positions
3. Resize cards by dragging corners
4. Click "Save"

---

## Step 7: Add Filters (Optional)

Add date range filter for interactivity:

1. Click "Edit dashboard"
2. Click "Add a filter"
3. Choose "Time"
4. Select "Date Filter"
5. Map to: `Metric Date` in all cards
6. Default: "Past 30 days"
7. Click "Done"
8. Save dashboard

Now users can change date range dynamically!

---

## Step 8: Dashboard Settings

1. Click dashboard settings (⚙️ icon)
2. Configure:
   - **Auto-refresh**: Enable, set to 5 minutes
   - **Caching**: Enable for faster loads
   - **Public sharing**: Disable (or enable for stakeholders)
3. Click "Save"

---

## Advanced: Custom SQL Questions

For more complex metrics, use custom SQL:

### Example: Conversion Funnel

```sql
SELECT 
    metric_date,
    offers_count as "Offers Created",
    orders_count as "Orders Started",
    completed_orders_count as "Orders Completed",
    conversion_rate as "Conversion %"
FROM dm.business_metrics
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date DESC;
```

1. Click "New" → "Question"
2. Choose "Native query"
3. Select database: "Scooters DWH"
4. Paste SQL above
5. Visualization: **Table** or **Funnel**
6. Save and add to dashboard

---

## Dashboard Maintenance

### Daily Tasks
- ✅ Verify dashboard loads without errors
- ✅ Check data is up-to-date (should update daily)

### Weekly Tasks
- ✅ Review metric trends for anomalies
- ✅ Adjust date ranges if needed
- ✅ Add new questions based on business needs

### Monthly Tasks
- ✅ Review and optimize slow queries
- ✅ Archive old dashboards
- ✅ Gather feedback from stakeholders

---

## Troubleshooting

### Dashboard Shows "No Results"

**Cause**: No data in `dm.business_metrics`

**Solution**:
1. Run ETL DAG in Airflow
2. Wait for completion
3. Refresh dashboard

### Metrics Show Zero

**Cause**: No completed orders in OLTP database

**Solution**:
1. Generate test data in OLTP service
2. Ensure orders have `time_finish` set
3. Re-run ETL DAG

### Dashboard is Slow

**Cause**: Large date ranges or no caching

**Solution**:
1. Reduce default date range to 30 days
2. Enable caching in dashboard settings
3. Add indexes to `dm.business_metrics`:
   ```sql
   CREATE INDEX idx_dm_metrics_date_desc 
   ON dm.business_metrics (metric_date DESC);
   ```

### Connection Errors

**Cause**: Database not accessible

**Solution**:
1. Verify `dwh-postgres` is running:
   ```bash
   docker-compose ps dwh-postgres
   ```
2. Test connection:
   ```bash
   docker-compose exec dwh-postgres psql -U dwh_user -d dwh_db -c "SELECT 1;"
   ```
3. Check network: Metabase and dwh-postgres in same Docker network

---

## Best Practices

### Visualization Choices

| Metric Type | Best Visualization |
|-------------|-------------------|
| Single number (current) | Number card |
| Percentage | Gauge or Number |
| Time series | Line chart |
| Comparison | Bar chart |
| Distribution | Histogram |
| Funnel | Funnel chart or Sankey |

### Color Coding

Use consistent colors:
- 🟢 Green: Revenue, positive metrics
- 🔵 Blue: Operational metrics (orders, users)
- 🟡 Yellow: Warning thresholds
- 🔴 Red: Critical issues or negative metrics

### Dashboard Organization

1. **Top row**: Key metrics (numbers)
2. **Middle rows**: Supporting metrics
3. **Bottom rows**: Detailed charts and tables

---

## Export & Sharing

### Export Dashboard

1. Click "Share" → "Export as PDF"
2. Choose layout: Landscape
3. Download

### Share with Stakeholders

1. Click "Share" → "Create a public link"
2. Copy link
3. Send to stakeholders
4. ⚠️ Warning: Anyone with link can view

**Better alternative**: Create user accounts for stakeholders

### Email Subscriptions

1. Click "Subscriptions" → "Create a subscription"
2. Choose frequency: Daily at 9 AM
3. Add email addresses
4. Dashboard will be emailed automatically

---

## Sample Dashboard Screenshot

Here's what the final dashboard should look like:

```
╔═══════════════════════════════════════════════════════╗
║  📊 Scooters Business Metrics Dashboard               ║
╠════════════════╦════════════════╦═════════════════════╣
║  💰 ₽1,234,567 ║  📦 3,456      ║  👥 1,234           ║
║  Total Revenue ║  Orders        ║  Active Users       ║
║  ↑ +12%        ║  ↑ +8%         ║  ↑ +5%              ║
╠════════════════╬════════════════╬═════════════════════╣
║  💵 ₽357       ║  ⏱ 23.5 min    ║  🎯 78%             ║
║  Avg Order     ║  Avg Duration  ║  Conversion Rate    ║
║  ↑ +3%         ║  → 0%          ║  [========·  ]      ║
╠════════════════╩════════════════╩═════════════════════╣
║  📈 Revenue Trend (Last 30 Days)                      ║
║    ·                              ·                    ║
║   · ·                            · ·                   ║
║  ·   ·     ·                    ·   ·                  ║
║ ·     ·   · ·   ·              ·     ·                 ║
║────────────────────────────────────────────────────────║
╠════════════════════════════════════════════════════════╣
║  📊 Orders Trend (Last 30 Days)                       ║
║      ·                                                 ║
║     · ·         ·                                      ║
║    ·   ·       · ·       ·                             ║
║   ·     ·     ·   ·     · ·                            ║
║  ·       ·   ·     ·   ·   ·                           ║
║────────────────────────────────────────────────────────║
╚════════════════════════════════════════════════════════╝
```

---

## Next Steps

1. ✅ Complete dashboard setup following this guide
2. ✅ Generate test data and verify metrics
3. ✅ Share dashboard with team for feedback
4. ✅ Set up email subscriptions for daily reports
5. ✅ Create additional dashboards as needed

---

**Guide Version**: 1.0  
**Last Updated**: December 2025  
**Author**: DWH Team

