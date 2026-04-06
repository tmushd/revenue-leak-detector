from __future__ import annotations

import pandas as pd


def build_revenue_loss_summary(
    deals_enriched_df: pd.DataFrame,
    cancellations_classified_df: pd.DataFrame,
) -> pd.DataFrame:
    churn_summary = (
        cancellations_classified_df.groupby(["category", "subcategory"], dropna=False)
        .agg(
            source_records=("cancellation_id", "count"),
            lost_revenue=("churned_revenue", "sum"),
        )
        .reset_index()
    )
    churn_summary["source"] = "churn"

    lost_deals = deals_enriched_df[deals_enriched_df["deal_status"] == "lost"].copy()
    deal_summary = (
        lost_deals.groupby(["deal_loss_category", "deal_loss_subcategory"], dropna=False)
        .agg(
            source_records=("deal_id", "count"),
            lost_revenue=("effective_deal_value", "sum"),
        )
        .reset_index()
        .rename(columns={"deal_loss_category": "category", "deal_loss_subcategory": "subcategory"})
    )
    deal_summary["source"] = "lost_deal"

    summary = pd.concat([churn_summary, deal_summary], ignore_index=True)
    summary["lost_revenue"] = summary["lost_revenue"].round(2)
    total_loss = summary["lost_revenue"].sum()
    if total_loss > 0:
        summary["pct_of_total_loss"] = (summary["lost_revenue"] / total_loss * 100).round(2)
    else:
        summary["pct_of_total_loss"] = 0.0

    summary = summary.sort_values("lost_revenue", ascending=False).reset_index(drop=True)
    return summary


def build_revenue_trend(
    deals_enriched_df: pd.DataFrame,
    cancellations_classified_df: pd.DataFrame,
) -> pd.DataFrame:
    churn_trend = (
        cancellations_classified_df.assign(period=lambda df: df["cancellation_date"].dt.to_period("M").astype(str))
        .groupby("period")
        .agg(churn_revenue_lost=("churned_revenue", "sum"), churn_events=("cancellation_id", "count"))
        .reset_index()
    )
    lost_deal_trend = (
        deals_enriched_df[deals_enriched_df["deal_status"] == "lost"]
        .assign(period=lambda df: df["close_date"].dt.to_period("M").astype(str))
        .groupby("period")
        .agg(lost_deal_value=("effective_deal_value", "sum"), lost_deal_events=("deal_id", "count"))
        .reset_index()
    )

    trend = churn_trend.merge(lost_deal_trend, on="period", how="outer").fillna(0)
    trend["total_revenue_loss"] = trend["churn_revenue_lost"] + trend["lost_deal_value"]
    trend = trend.sort_values("period").reset_index(drop=True)
    return trend


def build_segment_loss(
    accounts_df: pd.DataFrame,
    cancellations_classified_df: pd.DataFrame,
    deals_enriched_df: pd.DataFrame,
) -> pd.DataFrame:
    churn_segments = (
        cancellations_classified_df.merge(
            accounts_df[["account_id", "plan_type", "region", "industry"]],
            on="account_id",
            how="left",
        )
        .groupby(["plan_type", "region", "industry"], dropna=False)
        .agg(churn_revenue_lost=("churned_revenue", "sum"), churn_events=("cancellation_id", "count"))
        .reset_index()
    )

    lost_deal_segments = (
        deals_enriched_df[deals_enriched_df["deal_status"] == "lost"]
        .merge(accounts_df[["account_id", "plan_type", "region", "industry"]], on="account_id", how="left")
        .groupby(["plan_type", "region", "industry"], dropna=False)
        .agg(lost_deal_value=("effective_deal_value", "sum"), lost_deal_events=("deal_id", "count"))
        .reset_index()
    )

    combined = churn_segments.merge(
        lost_deal_segments, on=["plan_type", "region", "industry"], how="outer"
    ).fillna(0)
    combined["total_revenue_loss"] = combined["churn_revenue_lost"] + combined["lost_deal_value"]
    return combined.sort_values("total_revenue_loss", ascending=False).reset_index(drop=True)
