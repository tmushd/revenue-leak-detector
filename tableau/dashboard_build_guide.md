# Tableau Dashboard Build Guide (Streamlit -> Tableau)

This guide maps each Streamlit element in `app.py` to a Tableau implementation.

## 1) Data sources to add in Tableau

Connect these CSV files from `tableau/exports/`:

1. `risk_scores_tableau.csv`
2. `revenue_loss_breakdown_tableau.csv`
3. `revenue_loss_trend_long_tableau.csv`
4. `segment_loss_tableau.csv`
5. `model_metrics_tableau.csv`
6. `kpi_snapshot_tableau.csv`
7. `recommendations_tableau.csv`
8. `evidence_cancellations_tableau.csv`
9. `evidence_support_tickets_tableau.csv`
10. `evidence_sales_notes_tableau.csv`

Use separate data sources per sheet (same behavior as Streamlit, where sections are built from different tables).

## 2) Parameters and filters

### Parameter: `Risk Threshold`
- Data type: Float
- Range: 0.10 to 0.90
- Step: 0.05
- Current value: 0.50

### Global filters (on sheets backed by `risk_scores_tableau.csv`)
- `plan_type` (multi-select)
- `region` (multi-select)

## 3) Calculated fields (Tableau syntax)

### For `risk_scores_tableau.csv`
- `High Risk Account Flag`
```tableau
IF [churn_probability] >= [Risk Threshold] THEN 1 ELSE 0 END
```
- `High Risk Accounts`
```tableau
SUM([High Risk Account Flag])
```
- `Monthly Revenue At Risk`
```tableau
SUM([estimated_monthly_revenue_at_risk])
```
- `Average Churn Probability`
```tableau
AVG([churn_probability])
```

### For `revenue_loss_breakdown_tableau.csv`
- `Modeled Churn Loss`
```tableau
{ FIXED : SUM(IF [source] = "churn" THEN [lost_revenue] END) }
```
- `Modeled Lost Deal Value`
```tableau
{ FIXED : SUM(IF [source] = "lost_deal" THEN [lost_revenue] END) }
```

### For `segment_loss_tableau.csv`
- `Segment Label`
```tableau
[plan_type] + " | " + [region] + " | " + [industry]
```

## 4) Sheet mapping

### KPI cards row
1. KPI - Monthly Revenue at Risk (`risk_scores_tableau.csv`)
2. KPI - High-Risk Accounts (`risk_scores_tableau.csv`, uses `Risk Threshold`)
3. KPI - Modeled Churn Loss (`revenue_loss_breakdown_tableau.csv`)
4. KPI - Modeled Lost Deal Value (`revenue_loss_breakdown_tableau.csv`)

### Revenue Loss Breakdown
- Chart: Grouped bar
- Columns: `category`
- Rows: `SUM(lost_revenue)`
- Color: `source`

### Revenue Loss Trend
- Chart: Line chart
- Columns: `period`
- Rows: `SUM(value)`
- Color: `metric_label`

### At-Risk Accounts
- Chart: Text table
- Data source: `risk_scores_tableau.csv`
- Filter: `churn_probability >= [Risk Threshold]`
- Sort: `estimated_monthly_revenue_at_risk` descending
- Display top 50 rows

### Most Affected Customer Segments
- Chart: Bar + detail table
- Bar chart: `Segment Label` vs `SUM(total_revenue_loss)`
- Supporting table columns:
  - `plan_type`, `region`, `industry`
  - `churn_revenue_lost`, `lost_deal_value`, `total_revenue_loss`
  - `churn_events`, `lost_deal_events`

### Model Quality
- KPI tiles from `model_metrics_tableau.csv`
- Show `ROC_AUC`, `PR_AUC`, `ACCURACY`, `RECALL`, `F1`
- Subtitle: average churn probability from `risk_scores_tableau.csv`

### Recommended Actions
- Text table from `recommendations_tableau.csv`

### Evidence Explorer
Create 3 worksheets (or 3 navigation targets):
1. Cancellation Feedback (`evidence_cancellations_tableau.csv`)
2. Support Tickets (`evidence_support_tickets_tableau.csv`)
3. Sales Notes (`evidence_sales_notes_tableau.csv`)

## 5) Dashboard layout suggestion

- Dashboard size: Automatic (or 1400x2200)
- Top: title + filters + KPI cards
- Middle:
  - Revenue Loss Breakdown
  - Revenue Loss Trend
  - At-Risk Accounts table
  - Segment bar + segment detail table
- Bottom:
  - Model Quality KPI strip
  - Recommended Actions
  - Evidence Explorer sheets

## 6) Validation checklist

- `plan_type` and `region` filters update risk KPI and at-risk account table
- Risk threshold parameter updates high-risk count and at-risk table
- Breakdown and trend totals match CSVs
- Segment bar ordering matches top `total_revenue_loss`
- Evidence tables preserve latest-date ordering where needed
