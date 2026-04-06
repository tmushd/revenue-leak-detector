from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
TABLEAU_EXPORT_DIR = ROOT_DIR / "tableau" / "exports"


def _read_csv(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def _read_metrics() -> dict[str, float]:
    path = ARTIFACTS_DIR / "model_metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def export_tableau_assets() -> dict[str, object]:
    TABLEAU_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    risk_scores = _read_csv("account_risk_scores.csv")
    loss_summary = _read_csv("revenue_loss_summary.csv")
    loss_trend = _read_csv("revenue_loss_trend.csv")
    recommendations = _read_csv("recommendations.csv")
    segment_loss = _read_csv("segment_loss.csv")
    sales_notes = _read_csv("sales_notes_classified.csv")
    support_tickets = _read_csv("support_tickets_classified.csv")
    cancellations = _read_csv("cancellations_classified.csv")
    model_metrics = _read_metrics()

    # Data source 1: At-risk account lens (supports filters + risk table + risk KPIs)
    risk_tableau = risk_scores.copy()
    risk_tableau["risk_threshold_default"] = 0.50
    risk_tableau = risk_tableau.sort_values(
        ["estimated_monthly_revenue_at_risk", "churn_probability"], ascending=False
    ).reset_index(drop=True)

    # Data source 2: Revenue loss breakdown (category + source)
    loss_breakdown = (
        loss_summary.groupby(["category", "subcategory", "source"], as_index=False)
        .agg(
            source_records=("source_records", "sum"),
            lost_revenue=("lost_revenue", "sum"),
            pct_of_total_loss=("pct_of_total_loss", "sum"),
        )
        .sort_values("lost_revenue", ascending=False)
        .reset_index(drop=True)
    )

    # Data source 3: Trend in long format for easier Tableau line charting
    trend_long = loss_trend.melt(
        id_vars=["period"],
        value_vars=["churn_revenue_lost", "lost_deal_value", "total_revenue_loss"],
        var_name="metric",
        value_name="value",
    )
    metric_labels = {
        "churn_revenue_lost": "Churn Revenue Lost",
        "lost_deal_value": "Lost Deal Value",
        "total_revenue_loss": "Total Revenue Loss",
    }
    trend_long["metric_label"] = trend_long["metric"].map(metric_labels).fillna(trend_long["metric"])

    # Data source 4: Segment impact view
    segment_tableau = segment_loss.copy()
    segment_tableau["segment"] = (
        segment_tableau["plan_type"].astype(str)
        + " | "
        + segment_tableau["region"].astype(str)
        + " | "
        + segment_tableau["industry"].astype(str)
    )
    segment_tableau = segment_tableau.sort_values("total_revenue_loss", ascending=False).reset_index(drop=True)

    # Data source 5: Model quality in long format (for KPI sheet)
    metrics_order = ["roc_auc", "pr_auc", "accuracy", "recall", "f1", "optimal_threshold", "positive_rate"]
    model_metrics_long = pd.DataFrame(
        [
            {
                "metric": metric,
                "metric_label": metric.upper(),
                "metric_value": float(model_metrics.get(metric, 0.0)),
            }
            for metric in metrics_order
        ]
    )

    # Data source 6: KPI snapshot table (single-row summary, useful for title cards)
    kpi_snapshot = pd.DataFrame(
        [
            {
                "monthly_revenue_at_risk": float(risk_scores["estimated_monthly_revenue_at_risk"].sum()),
                "high_risk_accounts_at_0_50": int((risk_scores["churn_probability"] >= 0.50).sum()),
                "modeled_churn_loss": float(
                    loss_summary.loc[loss_summary["source"] == "churn", "lost_revenue"].sum()
                ),
                "modeled_lost_deal_value": float(
                    loss_summary.loc[loss_summary["source"] == "lost_deal", "lost_revenue"].sum()
                ),
                "average_churn_probability": float(risk_scores["churn_probability"].mean()),
                "default_risk_threshold": 0.50,
            }
        ]
    )

    # Evidence tables (used by Tableau dashboard tabs / navigation buttons)
    evidence_cancellations = cancellations.copy()
    evidence_support = support_tickets.copy()
    evidence_sales = sales_notes.copy()

    # Recommendations table for action panel
    recs = recommendations.copy()

    # Write exports
    outputs = {
        "risk_scores_tableau.csv": risk_tableau,
        "revenue_loss_breakdown_tableau.csv": loss_breakdown,
        "revenue_loss_trend_long_tableau.csv": trend_long,
        "segment_loss_tableau.csv": segment_tableau,
        "model_metrics_tableau.csv": model_metrics_long,
        "kpi_snapshot_tableau.csv": kpi_snapshot,
        "recommendations_tableau.csv": recs,
        "evidence_cancellations_tableau.csv": evidence_cancellations,
        "evidence_support_tickets_tableau.csv": evidence_support,
        "evidence_sales_notes_tableau.csv": evidence_sales,
    }

    for file_name, df in outputs.items():
        df.to_csv(TABLEAU_EXPORT_DIR / file_name, index=False)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(PROCESSED_DIR),
        "export_dir": str(TABLEAU_EXPORT_DIR),
        "files": {
            file_name: {
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
            }
            for file_name, df in outputs.items()
        },
    }

    (TABLEAU_EXPORT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = export_tableau_assets()
    print(json.dumps(result, indent=2))
