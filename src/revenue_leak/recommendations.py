from __future__ import annotations

import pandas as pd


ACTION_PLAYBOOK = {
    "Commercial": "Offer value-based packaging and proactive renewal outreach for price-sensitive segments.",
    "Product": "Prioritize roadmap fixes for templates/performance gaps and publish release communication to affected accounts.",
    "Operational": "Reduce support response time with SLA escalation for high-priority tickets and onboarding checkpoints.",
    "Competitive": "Strengthen competitive battlecards and focus sales demos on collaboration + AI differentiation.",
    "Adoption / Value Realization": "Launch customer success activation program for low-usage accounts within first 30 days.",
    "Uncategorized": "Perform manual review of notes to enrich taxonomy and improve root-cause tagging quality.",
}


def build_recommendations(revenue_loss_summary_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    category_view = (
        revenue_loss_summary_df.groupby("category", as_index=False)
        .agg(total_lost_revenue=("lost_revenue", "sum"), source_records=("source_records", "sum"))
        .sort_values("total_lost_revenue", ascending=False)
        .head(top_n)
    )
    category_view["recommended_action"] = category_view["category"].map(ACTION_PLAYBOOK).fillna(
        ACTION_PLAYBOOK["Uncategorized"]
    )
    category_view["priority"] = range(1, len(category_view) + 1)
    return category_view[["priority", "category", "total_lost_revenue", "source_records", "recommended_action"]]
