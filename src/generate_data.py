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
