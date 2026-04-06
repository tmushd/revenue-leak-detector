from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


TODAY_STR = "2026-03-12"
SEED = 42


LOSS_CATEGORIES = [
    "Commercial",
    "Product",
    "Operational",
    "Competitive",
    "Adoption / Value Realization",
]
