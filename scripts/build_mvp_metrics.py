#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from substitutionbench.metrics import (
    load_benchmark_config,
    load_observations,
    score_observations,
    write_benchmark_summary_svg,
    write_markdown_report,
    write_metrics_csv,
    write_substitution_curve_svg,
    write_summary_csv,
    write_threshold_sensitivity_csv,
)

DATA = ROOT / "data"
REPORTS = ROOT / "reports"
PLOTS = REPORTS / "plots"


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)

    observations = load_observations(DATA / "benchmark_observations.csv")
    configs = load_benchmark_config(DATA / "benchmark_config.csv")
    scored = score_observations(observations, configs)

    write_metrics_csv(scored, DATA / "mvp_metrics.csv")
    write_summary_csv(scored, DATA / "mvp_substitution_floors.csv")
    write_threshold_sensitivity_csv(scored, DATA / "mvp_threshold_sensitivity.csv")
    write_benchmark_summary_svg(scored, PLOTS / "cheapest-equivalent.svg")
    for benchmark in sorted(configs):
        slug = benchmark.lower().replace(" ", "-")
        write_substitution_curve_svg(scored, benchmark, PLOTS / f"{slug}-substitution-curve.svg")
    write_markdown_report(scored, configs, REPORTS / "mvp-metrics.md")

    print("Generated MVP metrics:")
    print(f"- {DATA / 'mvp_metrics.csv'}")
    print(f"- {DATA / 'mvp_substitution_floors.csv'}")
    print(f"- {DATA / 'mvp_threshold_sensitivity.csv'}")
    print(f"- {REPORTS / 'mvp-metrics.md'}")
    print(f"- {PLOTS}")


if __name__ == "__main__":
    main()
