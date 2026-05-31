from __future__ import annotations

import csv
import html
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Observation:
    benchmark: str
    domain: str
    model: str
    score: float
    input_price_per_m: float | None
    output_price_per_m: float | None
    total_params_b: float | None
    active_params_b: float | None
    eval_mode: str
    source_quality: str
    source_url: str
    notes: str


@dataclass(frozen=True)
class BenchmarkConfig:
    benchmark: str
    jnd_points: float
    frontier_model: str
    frontier_score: float
    benchmark_kind: str
    notes: str


@dataclass(frozen=True)
class ScoredObservation:
    observation: Observation
    frontier_score: float
    jnd_points: float
    frontier_coverage: float
    score_gap: float
    jnd_equivalent: bool


def _float_or_none(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    return float(value)


def load_observations(path: str | Path) -> list[Observation]:
    with Path(path).open(newline="") as f:
        rows = csv.DictReader(f)
        return [
            Observation(
                benchmark=row["benchmark"],
                domain=row["domain"],
                model=row["model"],
                score=float(row["score"]),
                input_price_per_m=_float_or_none(row.get("input_price_per_m", "")),
                output_price_per_m=_float_or_none(row.get("output_price_per_m", "")),
                total_params_b=_float_or_none(row.get("total_params_b", "")),
                active_params_b=_float_or_none(row.get("active_params_b", "")),
                eval_mode=row.get("eval_mode", "") or "unknown",
                source_quality=row.get("source_quality", "") or "unknown",
                source_url=row.get("source_url", ""),
                notes=row.get("notes", ""),
            )
            for row in rows
        ]


def load_benchmark_config(path: str | Path) -> dict[str, BenchmarkConfig]:
    with Path(path).open(newline="") as f:
        rows = csv.DictReader(f)
        return {
            row["benchmark"]: BenchmarkConfig(
                benchmark=row["benchmark"],
                jnd_points=float(row["jnd_points"]),
                frontier_model=row["frontier_model"],
                frontier_score=float(row["frontier_score"]),
                benchmark_kind=row["benchmark_kind"],
                notes=row.get("notes", ""),
            )
            for row in rows
        }


def score_observations(
    observations: Iterable[Observation], configs: dict[str, BenchmarkConfig]
) -> list[ScoredObservation]:
    scored: list[ScoredObservation] = []
    for obs in observations:
        cfg = configs[obs.benchmark]
        gap = cfg.frontier_score - obs.score
        scored.append(
            ScoredObservation(
                observation=obs,
                frontier_score=cfg.frontier_score,
                jnd_points=cfg.jnd_points,
                frontier_coverage=obs.score / cfg.frontier_score * 100,
                score_gap=gap,
                jnd_equivalent=gap <= cfg.jnd_points,
            )
        )
    return scored


def cheapest_equivalent(scored: Iterable[ScoredObservation]) -> dict[str, ScoredObservation]:
    winners: dict[str, ScoredObservation] = {}
    for item in scored:
        obs = item.observation
        if not item.jnd_equivalent or obs.input_price_per_m is None:
            continue
        current = winners.get(obs.benchmark)
        if current is None or obs.input_price_per_m < current.observation.input_price_per_m:  # type: ignore[operator]
            winners[obs.benchmark] = item
    return winners


def smallest_equivalent(scored: Iterable[ScoredObservation]) -> dict[str, ScoredObservation]:
    winners: dict[str, ScoredObservation] = {}
    for item in scored:
        obs = item.observation
        params = obs.active_params_b if obs.active_params_b is not None else obs.total_params_b
        if not item.jnd_equivalent or params is None:
            continue
        current = winners.get(obs.benchmark)
        if current is None:
            winners[obs.benchmark] = item
            continue
        current_obs = current.observation
        current_params = current_obs.active_params_b if current_obs.active_params_b is not None else current_obs.total_params_b
        if current_params is None or params < current_params:
            winners[obs.benchmark] = item
    return winners


def frontier_coverage_by_model(scored: Iterable[ScoredObservation]) -> dict[str, dict[str, float]]:
    by_model: dict[str, dict[str, float]] = {}
    for item in scored:
        model = item.observation.model
        row = by_model.setdefault(model, {"benchmarks": 0, "jnd_equivalent": 0, "coverage_sum": 0.0})
        row["benchmarks"] += 1
        row["coverage_sum"] += item.frontier_coverage
        if item.jnd_equivalent:
            row["jnd_equivalent"] += 1
    for row in by_model.values():
        row["mean_frontier_coverage"] = row["coverage_sum"] / row["benchmarks"]
        row["task_space_coverage_pct"] = row["jnd_equivalent"] / row["benchmarks"] * 100
    return by_model


def write_metrics_csv(scored: Iterable[ScoredObservation], path: str | Path) -> None:
    fieldnames = [
        "benchmark",
        "domain",
        "model",
        "score",
        "frontier_score",
        "frontier_coverage",
        "score_gap",
        "jnd_points",
        "jnd_equivalent",
        "input_price_per_m",
        "output_price_per_m",
        "total_params_b",
        "active_params_b",
        "eval_mode",
        "source_quality",
        "source_url",
    ]
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in scored:
            obs = item.observation
            writer.writerow(
                {
                    "benchmark": obs.benchmark,
                    "domain": obs.domain,
                    "model": obs.model,
                    "score": f"{obs.score:.3f}",
                    "frontier_score": f"{item.frontier_score:.3f}",
                    "frontier_coverage": f"{item.frontier_coverage:.3f}",
                    "score_gap": f"{item.score_gap:.3f}",
                    "jnd_points": f"{item.jnd_points:.3f}",
                    "jnd_equivalent": str(item.jnd_equivalent).lower(),
                    "input_price_per_m": "" if obs.input_price_per_m is None else obs.input_price_per_m,
                    "output_price_per_m": "" if obs.output_price_per_m is None else obs.output_price_per_m,
                    "total_params_b": "" if obs.total_params_b is None else obs.total_params_b,
                    "active_params_b": "" if obs.active_params_b is None else obs.active_params_b,
                    "eval_mode": obs.eval_mode,
                    "source_quality": obs.source_quality,
                    "source_url": obs.source_url,
                }
            )


def write_summary_csv(scored: Iterable[ScoredObservation], path: str | Path) -> None:
    scored_list = list(scored)
    cheapest = cheapest_equivalent(scored_list)
    smallest = smallest_equivalent(scored_list)
    benchmarks = sorted({item.observation.benchmark for item in scored_list})
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "benchmark",
                "frontier_score",
                "jnd_points",
                "equivalent_models",
                "cheapest_equivalent_model",
                "cheapest_input_price_per_m",
                "smallest_equivalent_model",
                "smallest_params_b",
            ],
        )
        writer.writeheader()
        for benchmark in benchmarks:
            rows = [item for item in scored_list if item.observation.benchmark == benchmark]
            cheap = cheapest.get(benchmark)
            small = smallest.get(benchmark)
            small_params = None
            if small:
                small_obs = small.observation
                small_params = small_obs.active_params_b if small_obs.active_params_b is not None else small_obs.total_params_b
            writer.writerow(
                {
                    "benchmark": benchmark,
                    "frontier_score": f"{rows[0].frontier_score:.3f}",
                    "jnd_points": f"{rows[0].jnd_points:.3f}",
                    "equivalent_models": sum(1 for item in rows if item.jnd_equivalent),
                    "cheapest_equivalent_model": "" if cheap is None else cheap.observation.model,
                    "cheapest_input_price_per_m": "" if cheap is None else cheap.observation.input_price_per_m,
                    "smallest_equivalent_model": "" if small is None else small.observation.model,
                    "smallest_params_b": "" if small_params is None else small_params,
                }
            )


def write_threshold_sensitivity_csv(scored: Iterable[ScoredObservation], path: str | Path, thresholds: tuple[float, ...] = (1.0, 3.0, 5.0)) -> None:
    scored_list = list(scored)
    benchmarks = sorted({item.observation.benchmark for item in scored_list})
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "benchmark",
                "threshold_points",
                "equivalent_models",
                "cheapest_equivalent_model",
                "cheapest_input_price_per_m",
                "smallest_equivalent_model",
                "smallest_params_b",
            ],
        )
        writer.writeheader()
        for benchmark in benchmarks:
            rows = [item for item in scored_list if item.observation.benchmark == benchmark]
            for threshold in thresholds:
                equivalent = [item for item in rows if item.score_gap <= threshold]
                priced = [item for item in equivalent if item.observation.input_price_per_m is not None]
                sized = [
                    item
                    for item in equivalent
                    if (item.observation.active_params_b if item.observation.active_params_b is not None else item.observation.total_params_b) is not None
                ]
                cheap = min(priced, key=lambda item: item.observation.input_price_per_m or float("inf"), default=None)
                small = min(
                    sized,
                    key=lambda item: item.observation.active_params_b if item.observation.active_params_b is not None else item.observation.total_params_b or float("inf"),
                    default=None,
                )
                small_params = None
                if small:
                    small_params = small.observation.active_params_b if small.observation.active_params_b is not None else small.observation.total_params_b
                writer.writerow(
                    {
                        "benchmark": benchmark,
                        "threshold_points": threshold,
                        "equivalent_models": len(equivalent),
                        "cheapest_equivalent_model": "" if cheap is None else cheap.observation.model,
                        "cheapest_input_price_per_m": "" if cheap is None else cheap.observation.input_price_per_m,
                        "smallest_equivalent_model": "" if small is None else small.observation.model,
                        "smallest_params_b": "" if small_params is None else small_params,
                    }
                )


def _scale(value: float, min_value: float, max_value: float, out_min: float, out_max: float) -> float:
    if max_value == min_value:
        return (out_min + out_max) / 2
    return out_min + (value - min_value) / (max_value - min_value) * (out_max - out_min)


def write_substitution_curve_svg(scored: Iterable[ScoredObservation], benchmark: str, path: str | Path) -> None:
    rows = [item for item in scored if item.observation.benchmark == benchmark and item.observation.input_price_per_m is not None]
    rows.sort(key=lambda item: item.observation.input_price_per_m or 0)
    width, height = 980, 520
    left, right, top, bottom = 80, 40, 45, 80
    max_price = max(item.observation.input_price_per_m or 0 for item in rows)
    min_price = min(item.observation.input_price_per_m or 0 for item in rows)
    min_cov = max(0.0, min(item.frontier_coverage for item in rows) - 3)
    max_cov = 101.0
    points = []
    for item in rows:
        obs = item.observation
        x = _scale(obs.input_price_per_m or 0, min_price, max_price, left, width - right)
        y = _scale(item.frontier_coverage, min_cov, max_cov, height - bottom, top)
        points.append((x, y, item))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
    frontier_y = _scale(100, min_cov, max_cov, height - bottom, top)
    jnd_y = _scale(rows[0].jnd_points / rows[0].frontier_score * 100, 0, 100, 0, 0)  # unused; clarity
    band_min = (rows[0].frontier_score - rows[0].jnd_points) / rows[0].frontier_score * 100
    band_y = _scale(band_min, min_cov, max_cov, height - bottom, top)
    circles = []
    labels = []
    benchmark_cheapest = cheapest_equivalent(rows).get(benchmark)
    for x, y, item in points:
        obs = item.observation
        color = "#16a34a" if item.jnd_equivalent else "#dc2626"
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"><title>{html.escape(obs.model)}: {item.frontier_coverage:.1f}% coverage, ${obs.input_price_per_m}/M input</title></circle>')
        should_label = (
            (benchmark_cheapest is not None and obs.model == benchmark_cheapest.observation.model)
            or obs.input_price_per_m == max_price
            or item.frontier_coverage < band_min - 8
        )
        if should_label:
            labels.append(f'<text x="{x:.1f}" y="{y-10:.1f}" font-size="11" text-anchor="middle">{html.escape(obs.model[:24])}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>text {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; fill: #111827; }} .axis {{ stroke: #374151; stroke-width: 1.2; }} .grid {{ stroke: #e5e7eb; stroke-width: 1; }} .band {{ fill: #dcfce7; opacity: .8; }}</style>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="{width/2}" y="26" text-anchor="middle" font-size="20" font-weight="700">{html.escape(benchmark)} substitution curve</text>
  <rect class="band" x="{left}" y="{top}" width="{width-left-right}" height="{band_y-top:.1f}"/>
  <line class="grid" x1="{left}" x2="{width-right}" y1="{frontier_y:.1f}" y2="{frontier_y:.1f}"/>
  <line class="grid" x1="{left}" x2="{width-right}" y1="{band_y:.1f}" y2="{band_y:.1f}" stroke-dasharray="5 5"/>
  <line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}"/>
  <line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}"/>
  <polyline points="{line}" fill="none" stroke="#2563eb" stroke-width="2"/>
  {''.join(circles)}
  {''.join(labels)}
  <text x="{width/2}" y="{height-28}" text-anchor="middle" font-size="14">Input price ($ / 1M tokens), sorted cheapest → frontier</text>
  <text x="20" y="{height/2}" transform="rotate(-90 20 {height/2})" text-anchor="middle" font-size="14">Frontier coverage (%)</text>
  <text x="{width-right-8}" y="{height-bottom-8}" font-size="12" text-anchor="end">Green band = within JND threshold ({rows[0].jnd_points:g} points)</text>
</svg>'''
    Path(path).write_text(svg)


def write_benchmark_summary_svg(scored: Iterable[ScoredObservation], path: str | Path) -> None:
    scored_list = list(scored)
    cheapest = cheapest_equivalent(scored_list)
    benchmarks = sorted({item.observation.benchmark for item in scored_list})
    width, height = 1320, 320
    left, top = 260, 55
    bar_h, gap = 42, 28
    bars = []
    for i, benchmark in enumerate(benchmarks):
        item = cheapest.get(benchmark)
        y = top + i * (bar_h + gap)
        if item is None:
            label = "No priced equivalent in current data"
            coverage = 0
            price = 0
            color = "#9ca3af"
        else:
            label = f"{item.observation.model} — ${item.observation.input_price_per_m}/M input — {item.frontier_coverage:.1f}% coverage"
            coverage = item.frontier_coverage
            price = item.observation.input_price_per_m or 0
            color = "#16a34a" if item.jnd_equivalent else "#dc2626"
        w = max(4, (coverage / 100) * 560)
        bars.append(f'<text x="20" y="{y+27}" font-size="15" font-weight="600">{html.escape(benchmark)}</text><rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" fill="{color}" rx="5"/><text x="{left+w+10:.1f}" y="{y+27}" font-size="13">{html.escape(label)}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>text {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; fill: #111827; }}</style>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="{width/2}" y="30" text-anchor="middle" font-size="20" font-weight="700">Cheapest frontier-equivalent model by benchmark</text>
  {''.join(bars)}
  <text x="{left}" y="{height-20}" font-size="12">MVP threshold: within configured JND points of benchmark frontier score. Lower price wins.</text>
</svg>'''
    Path(path).write_text(svg)


def write_markdown_report(scored: Iterable[ScoredObservation], configs: dict[str, BenchmarkConfig], path: str | Path) -> None:
    scored_list = list(scored)
    cheapest = cheapest_equivalent(scored_list)
    smallest = smallest_equivalent(scored_list)
    lines = [
        "# SubstitutionBench MVP Metrics",
        "",
        "> Generated from `data/benchmark_observations.csv` using `scripts/build_mvp_metrics.py`.",
        "",
        "## MVP metric definitions",
        "",
        "- **Frontier score:** pinned top/reference score for the benchmark version/date.",
        "- **Frontier Coverage %:** `model_score / frontier_score * 100`.",
        "- **JND-equivalent:** model is within the configured percentage-point threshold of the frontier score.",
        "- **Cheapest equivalent:** lowest input $/M token model inside the JND-equivalent band.",
        "- **Smallest equivalent:** lowest known active-parameter count, falling back to total parameters, inside the JND-equivalent band.",
        "- **Threshold sensitivity:** recompute the floor at 1, 3, and 5 percentage-point JND bands so the conclusion does not depend on one arbitrary cutoff.",
        "",
        "## Benchmark substitution floors",
        "",
    ]
    for benchmark in sorted(configs):
        cfg = configs[benchmark]
        cheap = cheapest.get(benchmark)
        small = smallest.get(benchmark)
        lines += [f"### {benchmark}", ""]
        lines.append(f"- Frontier: **{cfg.frontier_model}** at **{cfg.frontier_score:g}%**")
        lines.append(f"- JND band: within **{cfg.jnd_points:g} percentage points**")
        if cheap:
            o = cheap.observation
            lines.append(f"- Cheapest equivalent: **{o.model}** at **${o.input_price_per_m}/M input**, score **{o.score:g}%**, coverage **{cheap.frontier_coverage:.1f}%**")
        else:
            lines.append("- Cheapest equivalent: not available in current priced data")
        if small:
            o = small.observation
            params = o.active_params_b if o.active_params_b is not None else o.total_params_b
            lines.append(f"- Smallest equivalent: **{o.model}** at **{params:g}B params**")
        else:
            lines.append("- Smallest equivalent: not available in current parameter data")
        lines.append("")
    lines += [
        "## Plots",
        "",
        "- `reports/plots/cheapest-equivalent.svg`",
        "- `reports/plots/math-500-substitution-curve.svg`",
        "- `reports/plots/gpqa-diamond-substitution-curve.svg`",
        "- `reports/plots/swe-bench-verified-substitution-curve.svg`",
        "",
        "## Generated CSVs",
        "",
        "- `data/mvp_metrics.csv` — per-row frontier coverage and JND-equivalence flags.",
        "- `data/mvp_substitution_floors.csv` — cheapest/smallest equivalent at configured benchmark thresholds.",
        "- `data/mvp_threshold_sensitivity.csv` — floor recomputed at 1/3/5 point thresholds.",
        "",
        "## Caveats",
        "",
        "- This is an MVP from currently gathered public rows, not the final canonical dataset.",
        "- Eval mode matters. Thinking/xhigh/non-thinking rows are deliberately kept separate.",
        "- Some rows are aggregator/vendor/community quality and need confirmation before publication-grade claims.",
        "- Saturation is treated as positive signal: the point is to find the floor, not crown the frontier winner.",
        "",
    ]
    Path(path).write_text("\n".join(lines))
