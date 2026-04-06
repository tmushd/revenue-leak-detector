from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, precision_recall_curve, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .config import SEED


@dataclass
class ModelArtifacts:
    model: Pipeline
    feature_matrix: pd.DataFrame
    scored_accounts: pd.DataFrame
    metrics: dict[str, float]


def _build_model_pipeline(categorical_columns: list[str], numeric_columns: list[str]) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_columns,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_columns,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=4,
        random_state=SEED,
        class_weight="balanced_subsample",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", classifier),
        ]
    )


def train_churn_model(account_features_df: pd.DataFrame) -> ModelArtifacts:
    model_df = account_features_df.copy()

    target = model_df["is_churned"]
    feature_columns = [
        col
        for col in model_df.columns
        if col not in {"is_churned", "signup_date"}
    ]
    X = model_df[feature_columns]

    categorical_columns = ["company_size", "industry", "region", "plan_type"]
    numeric_columns = [col for col in feature_columns if col not in {"account_id", *categorical_columns}]

    train_ids = X["account_id"]
    X_model = X.drop(columns=["account_id"])

    X_train, X_test, y_train, y_test = train_test_split(
        X_model,
        target,
        test_size=0.25,
        stratify=target,
        random_state=SEED,
    )

    model = _build_model_pipeline(categorical_columns=categorical_columns, numeric_columns=numeric_columns)
    model.fit(X_train, y_train)

    test_prob = model.predict_proba(X_test)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_test, test_prob)
    f1_scores = (2 * precision * recall) / np.where((precision + recall) == 0, 1, (precision + recall))
    if len(thresholds) > 0:
        best_index = int(np.nanargmax(f1_scores[:-1]))
        optimal_threshold = float(thresholds[best_index])
    else:
        optimal_threshold = 0.5
    test_pred = (test_prob >= optimal_threshold).astype(int)

    metrics = {
        "roc_auc": float(roc_auc_score(y_test, test_prob)),
        "pr_auc": float(average_precision_score(y_test, test_prob)),
        "accuracy": float(accuracy_score(y_test, test_pred)),
        "recall": float(recall_score(y_test, test_pred)),
        "f1": float(f1_score(y_test, test_pred)),
        "optimal_threshold": float(optimal_threshold),
        "positive_rate": float(np.mean(target)),
    }

    full_prob = model.predict_proba(X_model)[:, 1]
    scored_accounts = account_features_df[["account_id", "monthly_revenue", "plan_type", "region", "industry"]].copy()
    scored_accounts["churn_probability"] = full_prob
    scored_accounts["risk_tier"] = pd.cut(
        scored_accounts["churn_probability"],
        bins=[-0.01, 0.25, 0.5, 0.75, 1.0],
        labels=["Low", "Medium", "High", "Critical"],
    )
    scored_accounts["estimated_monthly_revenue_at_risk"] = (
        scored_accounts["monthly_revenue"] * scored_accounts["churn_probability"]
    ).round(2)
    scored_accounts = scored_accounts.sort_values(
        ["estimated_monthly_revenue_at_risk", "churn_probability"], ascending=False
    )

    return ModelArtifacts(
        model=model,
        feature_matrix=account_features_df,
        scored_accounts=scored_accounts,
        metrics=metrics,
    )
