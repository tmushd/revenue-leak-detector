from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.revenue_leak.config import ARTIFACTS_DIR, PROCESSED_DIR
from src.revenue_leak.pipeline import run_pipeline


st.set_page_config(page_title="Revenue Leak Detector", layout="wide")


REQUIRED_FILES = [
    PROCESSED_DIR / "account_risk_scores.csv",
    PROCESSED_DIR / "revenue_loss_summary.csv",
    PROCESSED_DIR / "revenue_loss_trend.csv",
    PROCESSED_DIR / "recommendations.csv",
    PROCESSED_DIR / "segment_loss.csv",
    PROCESSED_DIR / "sales_notes_classified.csv",
    PROCESSED_DIR / "support_tickets_classified.csv",
    PROCESSED_DIR / "cancellations_classified.csv",
    ARTIFACTS_DIR / "model_metrics.json",
]


def artifacts_ready() -> bool:
    return all(path.exists() for path in REQUIRED_FILES)


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "risk_scores": pd.read_csv(PROCESSED_DIR / "account_risk_scores.csv"),
        "loss_summary": pd.read_csv(PROCESSED_DIR / "revenue_loss_summary.csv"),
        "loss_trend": pd.read_csv(PROCESSED_DIR / "revenue_loss_trend.csv"),
        "recommendations": pd.read_csv(PROCESSED_DIR / "recommendations.csv"),
        "segment_loss": pd.read_csv(PROCESSED_DIR / "segment_loss.csv"),
        "sales_notes": pd.read_csv(PROCESSED_DIR / "sales_notes_classified.csv"),
        "support_tickets": pd.read_csv(PROCESSED_DIR / "support_tickets_classified.csv"),
        "cancellations": pd.read_csv(PROCESSED_DIR / "cancellations_classified.csv"),
        "model_metrics": pd.read_json(ARTIFACTS_DIR / "model_metrics.json", typ="series"),
    }


st.title("Revenue Leak Detector")
st.caption(
    "Analyze churn and lost-deal drivers, inspect high-risk accounts, and prioritize actions to reduce SaaS revenue leakage."
)

if not artifacts_ready():
    st.warning("Processed analytics files were not found yet.")
    if st.button("Run full pipeline now"):
        with st.spinner("Running analytics + modeling pipeline..."):
            result = run_pipeline()
        st.success(
            f"Pipeline complete. Processed {result['risk_rows']} accounts with total modeled loss ${result['revenue_loss_total']:,.2f}."
        )
        st.rerun()
    st.stop()

data = load_data()
risk_scores = data["risk_scores"]
loss_summary = data["loss_summary"]
loss_trend = data["loss_trend"]
recommendations = data["recommendations"]
segment_loss = data["segment_loss"]
sales_notes = data["sales_notes"]
support_tickets = data["support_tickets"]
cancellations = data["cancellations"]
model_metrics = data["model_metrics"]


with st.sidebar:
    st.header("Filters")
    plan_filter = st.multiselect(
        "Plan Type",
        options=sorted(risk_scores["plan_type"].dropna().unique().tolist()),
        default=sorted(risk_scores["plan_type"].dropna().unique().tolist()),
    )
    region_filter = st.multiselect(
        "Region",
        options=sorted(risk_scores["region"].dropna().unique().tolist()),
        default=sorted(risk_scores["region"].dropna().unique().tolist()),
    )
    risk_threshold = st.slider("Churn Risk Threshold", min_value=0.1, max_value=0.9, value=0.5, step=0.05)

filtered_risk = risk_scores[
    risk_scores["plan_type"].isin(plan_filter) & risk_scores["region"].isin(region_filter)
].copy()

total_revenue_at_risk = filtered_risk["estimated_monthly_revenue_at_risk"].sum()
critical_accounts = int((filtered_risk["churn_probability"] >= risk_threshold).sum())
mean_risk = filtered_risk["churn_probability"].mean()

churn_revenue_loss = (
    loss_summary.loc[loss_summary["source"] == "churn", "lost_revenue"].sum()
    if not loss_summary.empty
    else 0.0
)
lost_deal_value = (
    loss_summary.loc[loss_summary["source"] == "lost_deal", "lost_revenue"].sum()
    if not loss_summary.empty
    else 0.0
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Monthly Revenue at Risk", f"${total_revenue_at_risk:,.0f}")
metric_2.metric("High-Risk Accounts", f"{critical_accounts:,}")
metric_3.metric("Modeled Churn Loss", f"${churn_revenue_loss:,.0f}")
metric_4.metric("Modeled Lost Deal Value", f"${lost_deal_value:,.0f}")

st.subheader("Revenue Loss Breakdown")
loss_plot = (
    loss_summary.groupby(["category", "source"], as_index=False)["lost_revenue"].sum().sort_values("lost_revenue", ascending=False)
)
fig_loss = px.bar(
    loss_plot,
    x="category",
    y="lost_revenue",
    color="source",
    barmode="group",
    title="Revenue leakage by root-cause category",
    labels={"lost_revenue": "Revenue Loss ($)"},
)
st.plotly_chart(fig_loss, use_container_width=True)


st.subheader("Revenue Loss Trend")
trend_melt = loss_trend.melt(
    id_vars=["period"],
    value_vars=["churn_revenue_lost", "lost_deal_value", "total_revenue_loss"],
    var_name="metric",
    value_name="value",
)
fig_trend = px.line(
    trend_melt,
    x="period",
    y="value",
    color="metric",
    markers=True,
    title="Monthly churn and deal-loss trends",
    labels={"period": "Month", "value": "Revenue Loss ($)"},
)
st.plotly_chart(fig_trend, use_container_width=True)


st.subheader("At-Risk Accounts")
top_risk = filtered_risk[filtered_risk["churn_probability"] >= risk_threshold].copy()
top_risk = top_risk.sort_values("estimated_monthly_revenue_at_risk", ascending=False).head(50)
st.dataframe(
    top_risk[
        [
            "account_id",
            "plan_type",
            "region",
            "industry",
            "churn_probability",
            "risk_tier",
            "monthly_revenue",
            "estimated_monthly_revenue_at_risk",
        ]
    ],
    use_container_width=True,
)

st.subheader("Most Affected Customer Segments")
segment_view = segment_loss.sort_values("total_revenue_loss", ascending=False).head(25)
segment_view["segment"] = (
    segment_view["plan_type"].astype(str)
    + " | "
    + segment_view["region"].astype(str)
    + " | "
    + segment_view["industry"].astype(str)
)
fig_segments = px.bar(
    segment_view,
    x="segment",
    y="total_revenue_loss",
    title="Top segments by combined churn + lost-deal revenue leakage",
    labels={"total_revenue_loss": "Revenue Loss ($)", "segment": "Plan | Region | Industry"},
)
fig_segments.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_segments, use_container_width=True)
st.dataframe(
    segment_view[
        [
            "plan_type",
            "region",
            "industry",
            "churn_revenue_lost",
            "lost_deal_value",
            "total_revenue_loss",
            "churn_events",
            "lost_deal_events",
        ]
    ],
    use_container_width=True,
)


st.subheader("Model Quality")
model_cols = st.columns(5)
for col, metric_name in zip(
    model_cols, ["roc_auc", "pr_auc", "accuracy", "recall", "f1"], strict=False
):
    metric_value = float(model_metrics.get(metric_name, 0.0))
    col.metric(metric_name.upper(), f"{metric_value:.3f}")
st.caption(f"Average churn probability in filtered view: {mean_risk:.3f}")


st.subheader("Recommended Actions")
st.dataframe(recommendations, use_container_width=True)


st.subheader("Evidence Explorer")
tab1, tab2, tab3 = st.tabs(["Cancellation Feedback", "Support Tickets", "Sales Notes"])

with tab1:
    st.dataframe(
        cancellations[
            [
                "account_id",
                "cancellation_date",
                "churned_revenue",
                "category",
                "subcategory",
                "cancellation_reason_text",
            ]
        ].sort_values("cancellation_date", ascending=False),
        use_container_width=True,
        height=300,
    )

with tab2:
    st.dataframe(
        support_tickets[
            [
                "account_id",
                "created_date",
                "ticket_type",
                "priority",
                "resolution_hours",
                "category",
                "subcategory",
                "ticket_summary",
            ]
        ].sort_values("created_date", ascending=False),
        use_container_width=True,
        height=300,
    )

with tab3:
    st.dataframe(
        sales_notes[
            [
                "deal_id",
                "account_id",
                "note_date",
                "category",
                "subcategory",
                "note_text",
            ]
        ].sort_values("note_date", ascending=False),
        use_container_width=True,
        height=300,
    )
