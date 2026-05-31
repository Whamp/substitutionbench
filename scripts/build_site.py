#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from substitutionbench.metrics import (  # noqa: E402
    load_benchmark_config,
    load_observations,
    score_observations,
)

DATA = ROOT / "data"
DOCS = ROOT / "docs"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    observations = load_observations(DATA / "benchmark_observations.csv")
    configs = load_benchmark_config(DATA / "benchmark_config.csv")
    scored = score_observations(observations, configs)

    payload = {
        "generated_from": [
            "data/benchmark_observations.csv",
            "data/benchmark_config.csv",
        ],
        "thresholds": [1, 3, 5],
        "configs": {
            name: {
                "benchmark": cfg.benchmark,
                "jnd_points": cfg.jnd_points,
                "frontier_model": cfg.frontier_model,
                "frontier_score": cfg.frontier_score,
                "benchmark_kind": cfg.benchmark_kind,
                "notes": cfg.notes,
            }
            for name, cfg in configs.items()
        },
        "observations": [
            {
                "benchmark": item.observation.benchmark,
                "domain": item.observation.domain,
                "model": item.observation.model,
                "score": item.observation.score,
                "frontier_score": item.frontier_score,
                "frontier_coverage": item.frontier_coverage,
                "score_gap": item.score_gap,
                "jnd_points": item.jnd_points,
                "jnd_equivalent": item.jnd_equivalent,
                "input_price_per_m": item.observation.input_price_per_m,
                "output_price_per_m": item.observation.output_price_per_m,
                "total_params_b": item.observation.total_params_b,
                "active_params_b": item.observation.active_params_b,
                "eval_mode": item.observation.eval_mode,
                "source_quality": item.observation.source_quality,
                "source_url": item.observation.source_url,
                "notes": item.observation.notes,
            }
            for item in scored
        ],
    }
    out = DOCS / "data.js"
    out.write_text("window.SUBSTITUTION_BENCH_DATA = " + json.dumps(payload, indent=2) + ";\n")
    print(f"Generated {out}")


if __name__ == "__main__":
    main()
