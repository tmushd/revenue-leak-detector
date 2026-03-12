"""
We generate sythetic datasets for:
accounts.csv
deals.csv
product_usage.csv
"""


from __future__ import annotations
#for type hints

import random
from datetime import datetime, timedelta
#represents datetime, representa a time difference
from pathlib import Path

import numpy as np
import pandas as pd



# Setup

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_ACCOUNTS = 2000
N_DEALS = 5000
WEEKS_OF_USAGE = 16

TODAY = datetime(2026, 3, 12)



# Helper functions

def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def weighted_choice(options: list[str], probs: list[float]) -> str:
    return np.random.choice(options, p=probs)



# 1. Accounts table:

def generate_accounts(n_accounts: int) -> pd.DataFrame:
    company_sizes = ["solo", "small_business", "mid_market"]
    size_probs = [0.35, 0.45, 0.20]

    industries = [
        "ecommerce",
        "marketing_agency",
        "education",
        "real_estate",
        "media",
        "tech_startup",
    ]
    industry_probs = [0.22, 0.20, 0.12, 0.12, 0.14, 0.20]

    regions = ["North America", "Europe", "Asia", "Latin America"]
    region_probs = [0.45, 0.25, 0.20, 0.10]

    rows = []

    for i in range(1, n_accounts + 1):
        account_id = f"A{i:05d}"

        company_size = weighted_choice(company_sizes, size_probs)
        industry = weighted_choice(industries, industry_probs)
        region = weighted_choice(regions, region_probs)

        # Plan depends somewhat on company size
        if company_size == "solo":
            plan_type = weighted_choice(["free", "pro"], [0.55, 0.45])
        elif company_size == "small_business":
            plan_type = weighted_choice(["free", "pro", "team"], [0.20, 0.55, 0.25])
        else:
            plan_type = weighted_choice(["pro", "team"], [0.25, 0.75])

        signup_date = random_date(datetime(2024, 1, 1), TODAY)

        if plan_type == "free":
            monthly_revenue = 0
        elif plan_type == "pro":
            monthly_revenue = random.choice([12, 24, 36, 48])
        else:
            if company_size == "small_business":
                monthly_revenue = random.choice([60, 90, 120, 150])
            else:
                monthly_revenue = random.choice([180, 240, 300, 450])

        rows.append(
            {
                "account_id": account_id,
                "company_size": company_size,
                "industry": industry,
                "region": region,
                "plan_type": plan_type,
                "signup_date": signup_date.date(),
                "monthly_revenue": monthly_revenue,
            }
        )

    return pd.DataFrame(rows)



# 2. Deals table

def generate_deals(accounts_df: pd.DataFrame, n_deals: int) -> pd.DataFrame:
    lead_sources = ["website", "referral", "outbound", "ads"]
    lead_probs = [0.38, 0.22, 0.20, 0.20]

    stages = ["demo", "proposal", "negotiation"]

    competitor_pool = ["Canva", "Adobe Express", "Figma", "Piktochart", "None"]
    competitor_probs = [0.38, 0.24, 0.10, 0.08, 0.20]

    rows = []

    sampled_accounts = accounts_df["account_id"].sample(n=n_deals, replace=True).tolist()
    account_lookup = accounts_df.set_index("account_id").to_dict("index")

    for i, account_id in enumerate(sampled_accounts, start=1):
        account = account_lookup[account_id]
        company_size = account["company_size"]

        lead_source = weighted_choice(lead_sources, lead_probs)
        created_date = random_date(datetime(2025, 1, 1), TODAY)
        stage = random.choice(stages)
        competitor_mentioned = weighted_choice(competitor_pool, competitor_probs)

        # Deal value tied to size
        if company_size == "solo":
            deal_value = random.choice([60, 120, 180])
        elif company_size == "small_business":
            deal_value = random.choice([240, 360, 480, 720])
        else:
            deal_value = random.choice([1200, 1800, 2400, 3600])

        # Discount more common for bigger deals
        if company_size == "mid_market":
            discount_pct = random.choice([0, 10, 15, 20, 25])
        else:
            discount_pct = random.choice([0, 0, 10, 15, 20])

        # Win/loss probability with simple business logic
        win_prob = 0.58

        if competitor_mentioned != "None":
            win_prob -= 0.12
        if discount_pct >= 20:
            win_prob -= 0.05
        if lead_source == "referral":
            win_prob += 0.10
        if company_size == "mid_market":
            win_prob -= 0.08

        deal_status = "won" if random.random() < win_prob else "lost"
        close_date = created_date + timedelta(days=random.randint(7, 60))

        rows.append(
            {
                "deal_id": f"D{i:05d}",
                "account_id": account_id,
                "lead_source": lead_source,
                "created_date": created_date.date(),
                "deal_value": deal_value,
                "discount_pct": discount_pct,
                "competitor_mentioned": competitor_mentioned,
                "stage": stage,
                "close_date": close_date.date(),
                "deal_status": deal_status,
            }
        )

    return pd.DataFrame(rows)



# 3. Product usage table

def generate_product_usage(accounts_df: pd.DataFrame, weeks_of_usage: int) -> pd.DataFrame:
    rows = []

    for _, row in accounts_df.iterrows():
        account_id = row["account_id"]
        plan_type = row["plan_type"]
        company_size = row["company_size"]
        signup_date = pd.to_datetime(row["signup_date"])

        # Base engagement levels by plan/company
        if plan_type == "free":
            base_projects = np.random.randint(0, 3)
            base_templates = np.random.randint(0, 4)
            base_ai_usage = np.random.randint(0, 2)
        elif plan_type == "pro":
            base_projects = np.random.randint(2, 7)
            base_templates = np.random.randint(3, 10)
            base_ai_usage = np.random.randint(1, 5)
        else:
            base_projects = np.random.randint(5, 12)
            base_templates = np.random.randint(6, 16)
            base_ai_usage = np.random.randint(2, 8)

        if company_size == "solo":
            base_wau = np.random.randint(1, 3)
            base_collab = 0
        elif company_size == "small_business":
            base_wau = np.random.randint(2, 8)
            base_collab = np.random.randint(1, 5)
        else:
            base_wau = np.random.randint(5, 20)
            base_collab = np.random.randint(3, 12)

        for week in range(weeks_of_usage):
            week_start = TODAY - timedelta(days=(weeks_of_usage - week) * 7)

            # Skip usage before signup
            if week_start < signup_date.to_pydatetime():
                continue

            noise = np.random.normal(1.0, 0.25)

            projects_created = max(0, int(base_projects * noise))
            templates_used = max(0, int(base_templates * noise))
            ai_design_tool_usage = max(0, int(base_ai_usage * noise))
            exports_count = max(0, int(projects_created * np.random.uniform(0.7, 1.4)))
            collaboration_sessions = max(0, int(base_collab * noise))
            weekly_active_users = max(1, int(base_wau * noise)) if plan_type != "free" else max(0, int(base_wau * noise))

            rows.append(
                {
                    "account_id": account_id,
                    "week_start": week_start.date(),
                    "projects_created": projects_created,
                    "templates_used": templates_used,
                    "ai_design_tool_usage": ai_design_tool_usage,
                    "exports_count": exports_count,
                    "collaboration_sessions": collaboration_sessions,
                    "weekly_active_users": weekly_active_users,
                }
            )

    return pd.DataFrame(rows)

def make_ticket_summary(ticket_type: str) -> str:
    templates = {
        "bug": [
            "User reported export failing on large files.",
            "Customer hit a recurring editor crash while saving a design.",
            "Bug reported in image upload flow causing failed imports.",
        ],
        "billing": [
            "Customer asked about an unexpected billing charge.",
            "User reported confusion about plan renewal pricing.",
            "Billing issue raised after duplicate invoice appeared.",
        ],
        "feature_request": [
            "Customer requested more premium templates for social campaigns.",
            "User asked for advanced brand kit controls.",
            "Team requested deeper collaboration permissions.",
        ],
        "performance_issue": [
            "User reported slow loading times in the editor.",
            "Customer experienced lag during export and preview.",
            "Team reported performance issues on large collaborative projects.",
        ],
    }
    return random.choice(templates[ticket_type])


#customer problems 
#bugs, billing issues, feature requests, performance complains as such
def generate_support_tickets(accounts_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ticket_counter = 1

    for _, row in accounts_df.iterrows():
        account_id = row["account_id"]
        plan_type = row["plan_type"]
        company_size = row["company_size"]
        monthly_revenue = row["monthly_revenue"]

        if plan_type == "free":
            n_tickets = np.random.poisson(0.4)
        elif plan_type == "pro":
            n_tickets = np.random.poisson(1.2)
        else:
            n_tickets = np.random.poisson(2.2)

        if company_size == "mid_market":
            n_tickets += 1

        for _ in range(n_tickets):
            ticket_type = weighted_choice(
                ["bug", "billing", "feature_request", "performance_issue"],
                [0.30, 0.20, 0.25, 0.25],
            )
            priority = weighted_choice(["low", "medium", "high"], [0.45, 0.40, 0.15])

            if priority == "high":
                resolution_hours = random.randint(24, 120)
                csat_score = random.choice([1, 2, 3])
            elif priority == "medium":
                resolution_hours = random.randint(8, 72)
                csat_score = random.choice([2, 3, 4])
            else:
                resolution_hours = random.randint(1, 24)
                csat_score = random.choice([3, 4, 5])

            if ticket_type == "performance_issue":
                resolution_hours += random.randint(4, 24)
                csat_score = max(1, csat_score - 1)

            created_date = random_date(datetime(2025, 1, 1), TODAY)
            ticket_summary = make_ticket_summary(ticket_type)

            rows.append(
                {
                    "ticket_id": f"T{ticket_counter:05d}",
                    "account_id": account_id,
                    "created_date": created_date.date(),
                    "ticket_type": ticket_type,
                    "priority": priority,
                    "resolution_hours": resolution_hours,
                    "csat_score": csat_score,
                    "ticket_summary": ticket_summary,
                    "account_revenue": monthly_revenue,
                }
            )
            ticket_counter += 1

    return pd.DataFrame(rows)

#What happened during sales conversations 
#competitor comparisons, pricing objections, onboarind concerns, product strengths
def make_sales_note(competitor: str, deal_status: str, stage: str) -> str:
    lost_templates = [
        f"Prospect liked the product but said {competitor} has stronger template variety.",
        f"Customer raised concerns that {competitor} is already adopted by the team.",
        f"Deal slowed after prospect compared collaboration features with {competitor}.",
        "Buyer mentioned pricing pressure and unclear ROI during evaluation.",
        "Prospect said onboarding seemed harder than expected for their team.",
    ]

    won_templates = [
        "Customer responded well to collaboration features and ease of use.",
        "Prospect liked the template library and fast export workflow.",
        "Buyer saw strong value in the AI-assisted design tools.",
        "Team liked the ease of onboarding and quick time to value.",
    ]

    neutral_templates = [
        f"Discussion focused on {stage} stage objections and next steps.",
        "Customer asked for more information about pricing and user seats.",
        "Prospect requested a follow-up demo for additional stakeholders.",
    ]

    if deal_status == "lost":
        if competitor != "None":
            return random.choice(lost_templates[:3])
        return random.choice(lost_templates[3:])
    if deal_status == "won":
        return random.choice(won_templates)
    return random.choice(neutral_templates)


def generate_sales_notes(deals_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    note_counter = 1

    for _, row in deals_df.iterrows():
        notes_per_deal = random.choice([1, 1, 2, 2, 3])

        for _ in range(notes_per_deal):
            note_date = pd.to_datetime(row["created_date"]) + timedelta(days=random.randint(0, 30))
            note_text = make_sales_note(
                competitor=row["competitor_mentioned"],
                deal_status=row["deal_status"],
                stage=row["stage"],
            )

            rows.append(
                {
                    "note_id": f"N{note_counter:05d}",
                    "deal_id": row["deal_id"],
                    "account_id": row["account_id"],
                    "note_date": note_date.date(),
                    "note_text": note_text,
                }
            )
            note_counter += 1

    return pd.DataFrame(rows)

#why customers churned
#low useage, pricing, competitor switch, performance issues etc (mentioning a few as of now)

def make_cancellation_reason(reason_type: str) -> str:
    templates = {
        "low_usage": [
            "Customer cancelled after low product usage over the last month.",
            "User did not create enough projects to justify the subscription.",
            "Account showed weak adoption and limited ongoing engagement.",
        ],
        "competitor_switch": [
            "Customer switched to Canva because the broader team already uses it.",
            "User moved to Adobe Express for familiarity and existing workflows.",
            "Account churned after preferring a competitor's template ecosystem.",
        ],
        "pricing": [
            "Customer said the subscription cost no longer felt justified.",
            "User cited budget pressure and reduced willingness to renew.",
            "Account cancelled due to pricing concerns relative to usage.",
        ],
        "performance": [
            "Customer reported repeated performance issues and slow editing experience.",
            "User cited lag and unstable exports as key reasons for cancellation.",
            "Account churned after unresolved speed and reliability complaints.",
        ],
    }
    return random.choice(templates[reason_type])


def generate_cancellations(accounts_df: pd.DataFrame, usage_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cancellation_counter = 1

    usage_summary = (
        usage_df.groupby("account_id")[["projects_created", "weekly_active_users"]]
        .mean()
        .reset_index()
        .rename(
            columns={
                "projects_created": "avg_projects_created",
                "weekly_active_users": "avg_weekly_active_users",
            }
        )
    )

    merged = accounts_df.merge(usage_summary, on="account_id", how="left")

    for _, row in merged.iterrows():
        plan_type = row["plan_type"]
        monthly_revenue = row["monthly_revenue"]
        signup_date = pd.to_datetime(row["signup_date"])
        avg_projects = row["avg_projects_created"] if not pd.isna(row["avg_projects_created"]) else 0
        avg_wau = row["avg_weekly_active_users"] if not pd.isna(row["avg_weekly_active_users"]) else 0

        churn_prob = 0.06

        if plan_type == "free":
            churn_prob = 0.00
        elif plan_type == "pro":
            churn_prob += 0.05
        else:
            churn_prob += 0.08

        if avg_projects < 2:
            churn_prob += 0.10
        if avg_wau < 2:
            churn_prob += 0.08

        if monthly_revenue >= 180:
            churn_prob -= 0.03

        if random.random() < churn_prob and monthly_revenue > 0:
            reason_type = weighted_choice(
                ["low_usage", "competitor_switch", "pricing", "performance"],
                [0.35, 0.25, 0.20, 0.20],
            )
            cancellation_date = random_date(max(signup_date.to_pydatetime(), datetime(2025, 1, 1)), TODAY)
            tenure_months = max(
                1,
                int((cancellation_date.date() - signup_date.date()).days / 30),
            )
            refund_requested = random.choice([True, False, False])

            rows.append(
                {
                    "cancellation_id": f"C{cancellation_counter:05d}",
                    "account_id": row["account_id"],
                    "cancellation_date": cancellation_date.date(),
                    "tenure_months": tenure_months,
                    "refund_requested": refund_requested,
                    "cancellation_reason_text": make_cancellation_reason(reason_type),
                    "churned_revenue": monthly_revenue,
                    "reason_type": reason_type,
                }
            )
            cancellation_counter += 1

    return pd.DataFrame(rows)


# Save outputs

def main() -> None:
    accounts_df = generate_accounts(N_ACCOUNTS)
    deals_df = generate_deals(accounts_df, N_DEALS)
    usage_df = generate_product_usage(accounts_df, WEEKS_OF_USAGE)

    accounts_df.to_csv(RAW_DIR / "accounts.csv", index=False)
    deals_df.to_csv(RAW_DIR / "deals.csv", index=False)
    usage_df.to_csv(RAW_DIR / "product_usage.csv", index=False)

    print("Done.")
    print(f"Saved: {RAW_DIR / 'accounts.csv'} ({len(accounts_df):,} rows)")
    print(f"Saved: {RAW_DIR / 'deals.csv'} ({len(deals_df):,} rows)")
    print(f"Saved: {RAW_DIR / 'product_usage.csv'} ({len(usage_df):,} rows)")


if __name__ == "__main__":
    main()

