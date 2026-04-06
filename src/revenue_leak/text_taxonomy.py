from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TaxonomyRule:
    category: str
    subcategory: str
    keywords: tuple[str, ...]


RULES: tuple[TaxonomyRule, ...] = (
    TaxonomyRule(
        category="Commercial",
        subcategory="pricing_concerns",
        keywords=("pricing", "price", "budget", "cost", "invoice", "billing", "discount", "renewal"),
    ),
    TaxonomyRule(
        category="Product",
        subcategory="missing_templates",
        keywords=("template", "templates", "library", "variety"),
    ),
    TaxonomyRule(
        category="Product",
        subcategory="missing_features",
        keywords=("feature", "capability", "advanced", "permissions", "controls"),
    ),
    TaxonomyRule(
        category="Product",
        subcategory="performance_reliability",
        keywords=("slow", "lag", "crash", "performance", "failed", "imports", "unstable", "loading"),
    ),
    TaxonomyRule(
        category="Product",
        subcategory="export_limitations",
        keywords=("export", "watermark", "preview"),
    ),
    TaxonomyRule(
        category="Operational",
        subcategory="onboarding_confusion",
        keywords=("onboarding", "time to value", "adoption", "confusion", "setup"),
    ),
    TaxonomyRule(
        category="Operational",
        subcategory="support_quality",
        keywords=("support", "resolution", "ticket", "unresolved", "response"),
    ),
    TaxonomyRule(
        category="Competitive",
        subcategory="competitor_switch",
        keywords=("competitor", "switched", "canva", "adobe express", "figma", "piktochart"),
    ),
    TaxonomyRule(
        category="Competitive",
        subcategory="competitor_advantage",
        keywords=("already uses", "familiarity", "existing workflows", "stronger"),
    ),
    TaxonomyRule(
        category="Adoption / Value Realization",
        subcategory="low_usage",
        keywords=("low usage", "weak adoption", "did not create", "limited engagement", "justify the subscription"),
    ),
    TaxonomyRule(
        category="Adoption / Value Realization",
        subcategory="low_team_adoption",
        keywords=("team adoption", "stakeholders", "team already uses"),
    ),
)


def _find_rule_hits(text: str, rules: Iterable[TaxonomyRule]) -> list[tuple[TaxonomyRule, list[str]]]:
    text_lower = text.lower()
    hits: list[tuple[TaxonomyRule, list[str]]] = []
    for rule in rules:
        matched = [kw for kw in rule.keywords if kw in text_lower]
        if matched:
            hits.append((rule, matched))
    return hits


def classify_text(text: str) -> dict[str, object]:
    if not isinstance(text, str) or not text.strip():
        return {
            "category": "Uncategorized",
            "subcategory": "unclear_signal",
            "matched_terms": "",
            "confidence": 0.1,
        }

    hits = _find_rule_hits(text, RULES)
    if not hits:
        return {
            "category": "Uncategorized",
            "subcategory": "unclear_signal",
            "matched_terms": "",
            "confidence": 0.25,
        }

    best_rule, matched_terms = max(hits, key=lambda item: len(item[1]))
    confidence = min(0.95, 0.5 + 0.1 * len(matched_terms))
    return {
        "category": best_rule.category,
        "subcategory": best_rule.subcategory,
        "matched_terms": ", ".join(sorted(set(matched_terms))),
        "confidence": round(confidence, 2),
    }
