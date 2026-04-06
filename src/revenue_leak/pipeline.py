from __future__ import annotations

import json
from pathlib import Path

import joblib

from .analytics import build_revenue_loss_summary, build_revenue_trend, build_segment_loss
from .config import ARTIFACTS_DIR, PROCESSED_DIR, RAW_DIR
from .features import (
    build_account_features,
    classify_cancellations,
    classify_sales_notes,
    classify_support_tickets,
    enrich_deals_with_loss_signals,
    load_raw_data,
)
from .modeling import train_churn_model
from .recommendations import build_recommendations


def _ensure_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _write_metrics(metrics: dict[str, float], path: Path) -> None:
    with path.open("w", encoding="utf-8") as fp:
        json.dump({k: round(v, 4) for k, v in metrics.items()}, fp, indent=2)


def run_pipeline() -> dict[str, object]:
    _ensure_dirs()
    data = load_raw_data(RAW_DIR)

    support_classified = classify_support_tickets(data.support)
    sales_notes_classified = classify_sales_notes(data.sales_notes)
    cancellations_classified = classify_cancellations(data.cancellations)
    deals_enriched = enrich_deals_with_loss_signals(data.deals, sales_notes_classified)

    account_features = build_account_features(
        accounts_df=data.accounts,
        deals_enriched_df=deals_enriched,
        usage_df=data.usage,
        support_df=support_classified,
        cancellations_df=cancellations_classified,
    )

    model_artifacts = train_churn_model(account_features_df=account_features)

    revenue_loss_summary = build_revenue_loss_summary(
        deals_enriched_df=deals_enriched,
        cancellations_classified_df=cancellations_classified,
    )
    revenue_loss_trend = build_revenue_trend(
        deals_enriched_df=deals_enriched,
        cancellations_classified_df=cancellations_classified,
    )
    segment_loss = build_segment_loss(
        accounts_df=data.accounts,
        cancellations_classified_df=cancellations_classified,
        deals_enriched_df=deals_enriched,
    )
    recommendations = build_recommendations(revenue_loss_summary)

    support_classified.to_csv(PROCESSED_DIR / "support_tickets_classified.csv", index=False)
    sales_notes_classified.to_csv(PROCESSED_DIR / "sales_notes_classified.csv", index=False)
    cancellations_classified.to_csv(PROCESSED_DIR / "cancellations_classified.csv", index=False)
    deals_enriched.to_csv(PROCESSED_DIR / "deals_enriched.csv", index=False)

    account_features.to_csv(PROCESSED_DIR / "account_features.csv", index=False)
    model_artifacts.scored_accounts.to_csv(PROCESSED_DIR / "account_risk_scores.csv", index=False)
    revenue_loss_summary.to_csv(PROCESSED_DIR / "revenue_loss_summary.csv", index=False)
    revenue_loss_trend.to_csv(PROCESSED_DIR / "revenue_loss_trend.csv", index=False)
    segment_loss.to_csv(PROCESSED_DIR / "segment_loss.csv", index=False)
    recommendations.to_csv(PROCESSED_DIR / "recommendations.csv", index=False)

    joblib.dump(model_artifacts.model, ARTIFACTS_DIR / "churn_model.joblib")
    _write_metrics(model_artifacts.metrics, ARTIFACTS_DIR / "model_metrics.json")

    return {
        "metrics": model_artifacts.metrics,
        "processed_dir": str(PROCESSED_DIR),
        "artifacts_dir": str(ARTIFACTS_DIR),
        "risk_rows": int(len(model_artifacts.scored_accounts)),
        "revenue_loss_total": float(revenue_loss_summary["lost_revenue"].sum()),
    }
