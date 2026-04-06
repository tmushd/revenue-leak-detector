from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .text_taxonomy import classify_text


@dataclass
class RawData:
    accounts: pd.DataFrame
    deals: pd.DataFrame
    usage: pd.DataFrame
    support: pd.DataFrame
    sales_notes: pd.DataFrame
    cancellations: pd.DataFrame


def load_raw_data(raw_dir: str | pd.io.common.FilePath | object) -> RawData:
    raw_path = pd.io.common.stringify_path(raw_dir)
    accounts = pd.read_csv(f"{raw_path}/accounts.csv", parse_dates=["signup_date"])
    deals = pd.read_csv(f"{raw_path}/deals.csv", parse_dates=["created_date", "close_date"])
    usage = pd.read_csv(f"{raw_path}/product_usage.csv", parse_dates=["week_start"])
    support = pd.read_csv(f"{raw_path}/support_tickets.csv", parse_dates=["created_date"])
    sales_notes = pd.read_csv(f"{raw_path}/sales_notes.csv", parse_dates=["note_date"])
    cancellations = pd.read_csv(f"{raw_path}/cancellations.csv", parse_dates=["cancellation_date"])
    return RawData(
        accounts=accounts,
        deals=deals,
        usage=usage,
        support=support,
        sales_notes=sales_notes,
        cancellations=cancellations,
    )


def classify_support_tickets(support_df: pd.DataFrame) -> pd.DataFrame:
    enriched = support_df.copy()
    classified = enriched["ticket_summary"].apply(classify_text).apply(pd.Series)
    enriched = pd.concat([enriched, classified], axis=1)
    return enriched


def classify_sales_notes(sales_notes_df: pd.DataFrame) -> pd.DataFrame:
    enriched = sales_notes_df.copy()
    classified = enriched["note_text"].apply(classify_text).apply(pd.Series)
    enriched = pd.concat([enriched, classified], axis=1)
    return enriched


def classify_cancellations(cancellations_df: pd.DataFrame) -> pd.DataFrame:
    enriched = cancellations_df.copy()
    classified = enriched["cancellation_reason_text"].apply(classify_text).apply(pd.Series)
    enriched = pd.concat([enriched, classified], axis=1)
    return enriched


def enrich_deals_with_loss_signals(deals_df: pd.DataFrame, classified_sales_notes_df: pd.DataFrame) -> pd.DataFrame:
    note_rank = (
        classified_sales_notes_df.sort_values("confidence", ascending=False)
        .drop_duplicates(subset=["deal_id"], keep="first")[["deal_id", "category", "subcategory", "confidence"]]
        .rename(
            columns={
                "category": "deal_loss_category",
                "subcategory": "deal_loss_subcategory",
                "confidence": "deal_loss_confidence",
            }
        )
    )
    deals = deals_df.merge(note_rank, on="deal_id", how="left")

    missing = deals["deal_loss_category"].isna()
    deals.loc[missing & (deals["competitor_mentioned"] != "None"), "deal_loss_category"] = "Competitive"
    deals.loc[missing & (deals["competitor_mentioned"] != "None"), "deal_loss_subcategory"] = "competitor_switch"
    deals.loc[missing & (deals["discount_pct"] >= 20), "deal_loss_category"] = "Commercial"
    deals.loc[missing & (deals["discount_pct"] >= 20), "deal_loss_subcategory"] = "pricing_concerns"
    deals["deal_loss_category"] = deals["deal_loss_category"].fillna("Uncategorized")
    deals["deal_loss_subcategory"] = deals["deal_loss_subcategory"].fillna("unclear_signal")
    deals["deal_loss_confidence"] = deals["deal_loss_confidence"].fillna(0.3)
    deals["effective_deal_value"] = deals["deal_value"] * (1 - deals["discount_pct"] / 100.0)
    return deals


def build_account_features(
    accounts_df: pd.DataFrame,
    deals_enriched_df: pd.DataFrame,
    usage_df: pd.DataFrame,
    support_df: pd.DataFrame,
    cancellations_df: pd.DataFrame,
) -> pd.DataFrame:
    usage_summary = (
        usage_df.groupby("account_id")
        .agg(
            avg_projects_created=("projects_created", "mean"),
            avg_templates_used=("templates_used", "mean"),
            avg_ai_usage=("ai_design_tool_usage", "mean"),
            avg_exports=("exports_count", "mean"),
            avg_collaboration=("collaboration_sessions", "mean"),
            avg_weekly_active_users=("weekly_active_users", "mean"),
            recent_projects_created=("projects_created", lambda s: s.tail(4).mean()),
            recent_weekly_active_users=("weekly_active_users", lambda s: s.tail(4).mean()),
        )
        .reset_index()
    )

    support_summary = (
        support_df.assign(
            is_high_priority=support_df["priority"].eq("high").astype(int),
            is_performance=support_df["ticket_type"].eq("performance_issue").astype(int),
            is_billing=support_df["ticket_type"].eq("billing").astype(int),
            is_feature_request=support_df["ticket_type"].eq("feature_request").astype(int),
        )
        .groupby("account_id")
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_resolution_hours=("resolution_hours", "mean"),
            avg_csat=("csat_score", "mean"),
            high_priority_tickets=("is_high_priority", "sum"),
            performance_tickets=("is_performance", "sum"),
            billing_tickets=("is_billing", "sum"),
            feature_request_tickets=("is_feature_request", "sum"),
        )
        .reset_index()
    )

    deal_summary = (
        deals_enriched_df.assign(
            is_lost=deals_enriched_df["deal_status"].eq("lost").astype(int),
            competitor_mention=deals_enriched_df["competitor_mentioned"].ne("None").astype(int),
        )
        .groupby("account_id")
        .agg(
            total_deals=("deal_id", "count"),
            lost_deals=("is_lost", "sum"),
            avg_discount_pct=("discount_pct", "mean"),
            avg_deal_value=("deal_value", "mean"),
            competitor_mention_rate=("competitor_mention", "mean"),
        )
        .reset_index()
    )
    deal_summary["lost_deal_rate"] = deal_summary["lost_deals"] / deal_summary["total_deals"].clip(lower=1)

    churn_labels = (
        cancellations_df[["account_id"]]
        .assign(is_churned=1)
        .drop_duplicates(subset=["account_id"])
    )

    features = (
        accounts_df.merge(usage_summary, on="account_id", how="left")
        .merge(support_summary, on="account_id", how="left")
        .merge(deal_summary, on="account_id", how="left")
        .merge(churn_labels, on="account_id", how="left")
    )

    features["is_churned"] = features["is_churned"].fillna(0).astype(int)
    features["account_age_days"] = (
        pd.Timestamp("2026-03-12") - pd.to_datetime(features["signup_date"])
    ).dt.days.clip(lower=0)

    numeric_columns = [
        col
        for col in features.columns
        if col
        not in {
            "account_id",
            "company_size",
            "industry",
            "region",
            "plan_type",
            "signup_date",
        }
    ]
    features[numeric_columns] = features[numeric_columns].fillna(0)
    return features
