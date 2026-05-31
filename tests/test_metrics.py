from __future__ import annotations

from pathlib import Path

from substitutionbench.metrics import (
    Observation,
    BenchmarkConfig,
    cheapest_equivalent,
    frontier_coverage_by_model,
    score_observations,
    smallest_equivalent,
    write_threshold_sensitivity_csv,
)


def obs(
    benchmark: str,
    model: str,
    score: float,
    price: float | None = None,
    total: float | None = None,
    active: float | None = None,
) -> Observation:
    return Observation(
        benchmark=benchmark,
        domain="Math",
        model=model,
        score=score,
        input_price_per_m=price,
        output_price_per_m=None,
        total_params_b=total,
        active_params_b=active,
        eval_mode="test",
        source_quality="test",
        source_url="https://example.com",
        notes="",
    )


def config() -> dict[str, BenchmarkConfig]:
    return {
        "MATH-500": BenchmarkConfig(
            benchmark="MATH-500",
            jnd_points=3.0,
            frontier_model="Frontier",
            frontier_score=100.0,
            benchmark_kind="saturated",
            notes="",
        )
    }


def test_scores_frontier_coverage_and_jnd_equivalence() -> None:
    scored = score_observations(
        [obs("MATH-500", "cheap-good", 98.0, price=0.1), obs("MATH-500", "too-low", 96.9, price=0.01)],
        config(),
    )

    assert scored[0].frontier_coverage == 98.0
    assert scored[0].score_gap == 2.0
    assert scored[0].jnd_equivalent is True
    assert scored[1].jnd_equivalent is False


def test_cheapest_equivalent_selects_lowest_priced_model_inside_jnd_band() -> None:
    scored = score_observations(
        [
            obs("MATH-500", "frontier", 100.0, price=5.0),
            obs("MATH-500", "cheap-good", 98.0, price=0.1),
            obs("MATH-500", "cheaper-but-bad", 96.0, price=0.01),
        ],
        config(),
    )

    winner = cheapest_equivalent(scored)["MATH-500"]

    assert winner.observation.model == "cheap-good"
    assert winner.observation.input_price_per_m == 0.1


def test_smallest_equivalent_prefers_active_params_when_available() -> None:
    scored = score_observations(
        [
            obs("MATH-500", "dense-14b", 98.0, total=14),
            obs("MATH-500", "moe-30b-a3b", 97.5, total=30, active=3),
        ],
        config(),
    )

    winner = smallest_equivalent(scored)["MATH-500"]

    assert winner.observation.model == "moe-30b-a3b"


def test_frontier_coverage_by_model_counts_jnd_task_space() -> None:
    scored = score_observations(
        [
            obs("MATH-500", "cheap-good", 98.0),
            obs("MATH-500", "too-low", 96.0),
        ],
        config(),
    )

    by_model = frontier_coverage_by_model(scored)

    assert by_model["cheap-good"]["task_space_coverage_pct"] == 100.0
    assert by_model["too-low"]["task_space_coverage_pct"] == 0.0


def test_threshold_sensitivity_changes_substitution_floor(tmp_path: Path) -> None:
    scored = score_observations(
        [
            obs("MATH-500", "expensive-at-1pt", 99.5, price=5.0),
            obs("MATH-500", "cheap-at-5pt", 96.0, price=0.1),
        ],
        config(),
    )
    out = tmp_path / "sensitivity.csv"

    write_threshold_sensitivity_csv(scored, out, thresholds=(1.0, 5.0))

    text = out.read_text()
    assert "1.0,1,expensive-at-1pt,5.0" in text
    assert "5.0,2,cheap-at-5pt,0.1" in text
