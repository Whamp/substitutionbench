from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import scripts.build_dashboard_data as dashboard_builder
from substitutionbench.registry import (
    DEFAULT_COMPONENTS,
    export_dashboard_payload,
    init_db,
    ingest_artificial_analysis_payload,
    ingest_livecodebench_payload,
    resolve_scores,
    write_dashboard_data,
)
from scripts.build_dashboard_data import build as build_dashboard_data


def aa_model(name: str, price: tuple[float | None, float | None, float | None], evaluations: dict[str, float]) -> dict:
    return {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "model_creator": {"id": "creator", "name": "Creator", "slug": "creator"},
        "pricing": {
            "price_1m_input_tokens": price[0],
            "price_1m_output_tokens": price[1],
            "price_1m_blended_3_to_1": price[2],
        },
        "median_output_tokens_per_second": 100,
        "median_time_to_first_token_seconds": 0.5,
        "evaluations": evaluations,
    }


def aa_payload() -> dict:
    return {
        "status": 200,
        "data": [
            aa_model(
                "Frontier Max",
                (10, 30, 15),
                {
                    "artificial_analysis_intelligence_index": 100,
                    "artificial_analysis_math_index": 100,
                    "artificial_analysis_coding_index": 100,
                    "gpqa": 0.96,
                    "hle": 0.45,
                    "livecodebench": 0.90,
                    "scicode": 0.60,
                    "lcr": 0.80,
                    "tau2": 0.99,
                    "terminalbench_hard": 0.60,
                    "ifbench": 0.84,
                },
            ),
            aa_model(
                "Cheap Sub",
                (0.2, 0.6, 0.3),
                {
                    "artificial_analysis_intelligence_index": 98,
                    "artificial_analysis_math_index": 97,
                    "artificial_analysis_coding_index": 96,
                    "gpqa": 0.94,
                    "hle": 0.43,
                    "livecodebench": 0.88,
                    "scicode": 0.58,
                    "lcr": 0.78,
                    "tau2": 0.97,
                    "terminalbench_hard": 0.58,
                    "ifbench": 0.82,
                },
            ),
            aa_model(
                "Zero Price Qualifier",
                (0, 0, 0),
                {
                    "artificial_analysis_intelligence_index": 97,
                    "artificial_analysis_math_index": 96,
                    "artificial_analysis_coding_index": 95,
                    "gpqa": 0.93,
                    "hle": 0.42,
                    "livecodebench": 0.87,
                    "scicode": 0.57,
                    "lcr": 0.77,
                    "tau2": 0.96,
                    "terminalbench_hard": 0.57,
                    "ifbench": 0.81,
                },
            ),
            aa_model(
                "Cheap Below",
                (0.05, 0.1, 0.06),
                {
                    "artificial_analysis_intelligence_index": 55,
                    "artificial_analysis_math_index": 50,
                    "artificial_analysis_coding_index": 52,
                    "gpqa": 0.40,
                    "hle": 0.20,
                    "livecodebench": 0.40,
                    "scicode": 0.30,
                    "lcr": 0.35,
                    "tau2": 0.50,
                    "terminalbench_hard": 0.20,
                    "ifbench": 0.40,
                },
            ),
            aa_model(
                "Partial Frontier",
                (5, 15, 7.5),
                {
                    "artificial_analysis_intelligence_index": 99,
                    "artificial_analysis_coding_index": 99,
                    "gpqa": 0.95,
                    "hle": 0.44,
                },
            ),
        ],
    }


def make_registry(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(tmp_path / "substitutionbench.sqlite")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    run_id = ingest_artificial_analysis_payload(
        conn,
        aa_payload(),
        endpoint="fixture://aa",
        fetched_at="2026-06-01T00:00:00+00:00",
        raw_path="fixtures/aa.json",
        checksum="fixture-aa",
        from_cache=False,
    )
    assert run_id > 0
    return conn


def test_sqlite_registry_preserves_raw_observations_resolutions_and_pricing_states(tmp_path: Path) -> None:
    conn = make_registry(tmp_path)
    resolve_scores(conn)

    assert conn.execute("select count(*) from sources").fetchone()[0] == 1
    assert conn.execute("select count(*) from fetch_runs").fetchone()[0] == 1
    assert conn.execute("select count(*) from benchmark_observations").fetchone()[0] > 20
    assert conn.execute("select count(*) from benchmark_resolutions").fetchone()[0] > 20
    assert conn.execute("select count(*) from index_versions").fetchone()[0] == 1

    states = {row[0] for row in conn.execute("select distinct normalized_state from pricing_observations")}
    assert "valid" in states
    assert "unknown_zero" in states


def test_dashboard_export_uses_resolved_scores_component_average_and_never_emits_secrets(tmp_path: Path) -> None:
    conn = make_registry(tmp_path)
    resolve_scores(conn)
    payload = export_dashboard_payload(conn)

    sb_index = next(index for index in payload["indexes"] if index["key"] == "substitutionbench-v1")
    cheap = next(model for model in sb_index["models"] if model["model"] == "Cheap Sub")
    component_values = [c["frontier_ratio"] for c in cheap["components"] if c["coverage_state"] == "complete"]
    assert cheap["frontier_ratio"] == round(sum(component_values) / len(component_values), 6)
    assert cheap["state"] == "substitute"

    zero = next(model for model in sb_index["models"] if model["model"] == "Zero Price Qualifier")
    assert zero["price_state"] == "unknown_zero"
    assert zero["state"] == "quality_expensive"

    partial = next(model for model in sb_index["models"] if model["model"] == "Partial Frontier")
    assert partial["coverage_state"] == "assumed_complete"
    assert partial["frontier_ratio"] is not None
    assert partial["frontier_eligibility"] == {
        "eligible": True,
        "policy": "aa_intelligence_top3_95pct",
        "score": 99,
        "cutoff": 94.05,
        "anchor": 99,
    }
    assumed_benchmark = next(
        benchmark
        for component in partial["components"]
        for benchmark in component["benchmarks"]
        if benchmark["coverage_state"] == "assumed"
    )
    assert assumed_benchmark["observation_kind"] == "assumed_frontier_anchor"
    assert assumed_benchmark["assumption_policy"] == "aa_intelligence_top3_95pct"
    assert assumed_benchmark["frontier_ratio"] == 1.0

    out = tmp_path / "data.js"
    write_dashboard_data(payload, out)
    text = out.read_text()
    assert "ARTIFICIAL_ANALYSIS_API_KEY" not in text
    assert "x-api-key" not in text
    assert text.startswith("window.SUBSTITUTION_BENCH_DATA = ")


def test_dashboard_export_includes_plain_english_task_cards_and_benchmark_floors(tmp_path: Path) -> None:
    conn = make_registry(tmp_path)
    resolve_scores(conn)
    payload = export_dashboard_payload(conn)

    benchmarks = {benchmark["key"]: benchmark for benchmark in payload["benchmarks"]}

    livecodebench = benchmarks["livecodebench"]
    assert livecodebench["plain_english_task"]
    assert "programming" in livecodebench["task_class"].lower()
    assert "tests" in livecodebench["substitution_claim_when_saturated"].lower()
    assert livecodebench["does_not_prove"]
    assert "coding" in livecodebench["aliases"]

    floor = livecodebench["substitution_floor"]
    assert floor["model"] == "Cheap Sub"
    assert floor["frontier_ratio"] >= 0.95
    assert floor["estimated_task_cost"] < floor["frontier_task_cost"]
    assert livecodebench["substitution_candidates"][0]["model"] == "Cheap Sub"


def test_dashboard_export_includes_router_policy_reference_points(tmp_path: Path) -> None:
    conn = make_registry(tmp_path)
    resolve_scores(conn)
    payload = export_dashboard_payload(conn)

    routers = payload["router_policy_references"]
    factory = next(router for router in routers if router["key"] == "factory_router")

    assert factory["candidate_type"] == "router_with_escalation_and_failover"
    assert factory["source_confidence"] == "vendor_claim_public_aggregate"
    assert "Terminal-Bench 2" in factory["summary"]

    terminal = next(point for point in factory["pareto_points"] if point["benchmark_key"] == "terminal_bench_2" and point["policy_label"] == "shipping")
    assert terminal["relative_pass_rate"] == 0.99
    assert terminal["relative_session_cost"] == 0.80
    assert terminal["relative_cost_per_success"] == 0.805
    assert terminal["floor_tier"] == "frontier_equivalent"

    legacy_aggressive = next(point for point in factory["pareto_points"] if point["benchmark_key"] == "legacy_bench" and point["policy_label"] == "aggressive")
    assert legacy_aggressive["relative_pass_rate"] == 0.49
    assert legacy_aggressive["floor_tier"] == "aggressive_degraded"


def test_livecodebench_official_rows_are_preserved_and_preferred_for_equivalent_conflicts(tmp_path: Path) -> None:
    conn = make_registry(tmp_path)
    ingest_livecodebench_payload(
        conn,
        {
            "models": [{"model_name": "cheap-sub", "model_repr": "Cheap Sub", "release_date": 1719705600000}],
            "performances": [
                {"model": "Cheap Sub", "date": 1719705600000, "difficulty": "easy", "pass@1": 90.0, "question_id": "1"},
                {"model": "Cheap Sub", "date": 1719705600000, "difficulty": "hard", "pass@1": 70.0, "question_id": "2"},
            ],
        },
        endpoint="fixture://livecodebench",
        fetched_at="2026-06-01T00:00:00+00:00",
        raw_path="fixtures/lcb.json",
        checksum="fixture-lcb",
        from_cache=False,
    )
    resolve_scores(conn)

    conflict_count = conn.execute(
        """
        select br.conflict_count
        from benchmark_resolutions br
        join models m on m.id = br.model_id
        join benchmarks b on b.id = br.benchmark_id
        where m.canonical_name = 'Cheap Sub' and b.key = 'livecodebench'
        """
    ).fetchone()[0]
    assert conflict_count == 1

    winning_source = conn.execute(
        """
        select s.name
        from benchmark_resolutions br
        join benchmark_observations bo on bo.id = br.observation_id
        join sources s on s.id = bo.source_id
        join models m on m.id = br.model_id
        join benchmarks b on b.id = br.benchmark_id
        where m.canonical_name = 'Cheap Sub' and b.key = 'livecodebench'
        """
    ).fetchone()[0]
    assert winning_source == "livecodebench"

    observed_scores = [row[0] for row in conn.execute("select score from benchmark_observations where benchmark_id = (select id from benchmarks where key='livecodebench')")]
    assert 0.8 in observed_scores  # official aggregate used for resolution
    assert 0.9 in observed_scores  # official row-level evidence preserved
    assert 0.7 in observed_scores  # official row-level evidence preserved
    assert any(abs(score - 0.88) < 1e-9 for score in observed_scores)  # AA alternate preserved

    aa_source = conn.execute("select attribution_url, notes from sources where name = 'artificial_analysis'").fetchone()
    assert aa_source[0] == "https://artificialanalysis.ai/"
    assert "Preferred source" in aa_source[1]


def test_livecodebench_resolution_does_not_collapse_protocol_incompatible_scores(tmp_path: Path) -> None:
    conn = make_registry(tmp_path)
    conn.execute(
        """
        update benchmark_observations
        set eval_mode = 'custom_livecodebench_variant'
        where benchmark_id = (select id from benchmarks where key = 'livecodebench')
          and model_id = (select id from models where canonical_name = 'Cheap Sub')
        """
    )
    ingest_livecodebench_payload(
        conn,
        {
            "models": [{"model_name": "cheap-sub", "model_repr": "Cheap Sub", "release_date": 1719705600000}],
            "performances": [
                {"model": "Cheap Sub", "date": 1719705600000, "difficulty": "easy", "pass@1": 90.0, "question_id": "1"},
                {"model": "Cheap Sub", "date": 1719705600000, "difficulty": "hard", "pass@1": 70.0, "question_id": "2"},
            ],
        },
        endpoint="fixture://livecodebench",
        fetched_at="2026-06-01T00:00:00+00:00",
        raw_path="fixtures/lcb.json",
        checksum="fixture-lcb",
        from_cache=False,
    )
    resolve_scores(conn)

    row = conn.execute(
        """
        select br.conflict_count, br.reason, s.name as winning_source
        from benchmark_resolutions br
        join benchmark_observations bo on bo.id = br.observation_id
        join sources s on s.id = bo.source_id
        join models m on m.id = br.model_id
        join benchmarks b on b.id = br.benchmark_id
        where m.canonical_name = 'Cheap Sub' and b.key = 'livecodebench'
        """
    ).fetchone()

    assert row["winning_source"] == "livecodebench"
    assert row["conflict_count"] == 0
    assert "protocol-incompatible" in row["reason"]


def test_build_preserves_existing_registry_file_instead_of_recreating_it(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "substitutionbench.sqlite"
    output_path = tmp_path / "data.js"
    conn = sqlite3.connect(db_path)
    conn.execute("create table sentinel(value text not null)")
    conn.execute("insert into sentinel(value) values ('history')")
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        dashboard_builder,
        "load_or_fetch_artificial_analysis",
        lambda refresh: (aa_payload(), dashboard_builder.CACHE_DIR / "fixture-aa.json", True),
    )
    monkeypatch.setattr(
        dashboard_builder,
        "load_or_fetch_livecodebench",
        lambda refresh: ({"models": [], "performances": []}, dashboard_builder.CACHE_DIR / "fixture-lcb.json", True),
    )

    summary = dashboard_builder.build(refresh=False, db_path=db_path, output_path=output_path)

    conn = sqlite3.connect(db_path)
    assert conn.execute("select value from sentinel").fetchone()[0] == "history"
    assert summary["fetch_runs"] == 2
    assert output_path.exists()


def test_default_components_are_equal_weight_and_domain_weighted_not_raw_benchmark_weighted() -> None:
    assert set(DEFAULT_COMPONENTS) == {"general", "math", "coding", "agentic"}
    assert {component.weight for component in DEFAULT_COMPONENTS.values()} == {0.25}
    raw_field_count = sum(len(component.benchmarks) for component in DEFAULT_COMPONENTS.values())
    assert raw_field_count > len(DEFAULT_COMPONENTS)
