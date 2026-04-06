# Tableau Conversion Pack

This folder contains Tableau-ready data extracts and dashboard build specs to replicate the Streamlit dashboard in Tableau.

## Export data for Tableau

```bash
python -m src.export_tableau_assets
```

Generated files are written to `tableau/exports/`.

## Files in `tableau/exports`

- `risk_scores_tableau.csv`: at-risk accounts + filter dimensions (Plan, Region)
- `revenue_loss_breakdown_tableau.csv`: grouped bar chart source (`category` x `source`)
- `revenue_loss_trend_long_tableau.csv`: long-form monthly trend lines
- `segment_loss_tableau.csv`: top affected segments and table view
- `model_metrics_tableau.csv`: model quality KPIs
- `kpi_snapshot_tableau.csv`: one-row summary for headline cards
- `recommendations_tableau.csv`: recommended actions table
- `evidence_cancellations_tableau.csv`: cancellation evidence table
- `evidence_support_tickets_tableau.csv`: support ticket evidence table
- `evidence_sales_notes_tableau.csv`: sales note evidence table
- `manifest.json`: export metadata and row/column counts

## Build spec

Use `tableau/dashboard_build_guide.md` for one-to-one mapping from Streamlit sections to Tableau sheets/dashboard layout.
