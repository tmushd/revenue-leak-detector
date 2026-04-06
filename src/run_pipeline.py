from __future__ import annotations

import json

from src.revenue_leak.pipeline import run_pipeline


def main() -> None:
    summary = run_pipeline()
    print("Pipeline complete.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
