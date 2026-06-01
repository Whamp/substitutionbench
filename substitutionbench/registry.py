from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ComponentSpec:
    key: str
    label: str
    weight: float
    benchmarks: tuple[str, ...]


DEFAULT_COMPONENTS: dict[str, ComponentSpec] = {
    "general": ComponentSpec(
        key="general",
        label="General Index",
        weight=0.25,
        benchmarks=("artificial_analysis_intelligence_index",),
    ),
    "math": ComponentSpec(
        key="math",
        label="Math Index",
        weight=0.25,
        benchmarks=("artificial_analysis_math_index",),
    ),
    "coding": ComponentSpec(
        key="coding",
        label="Coding Index",
        weight=0.25,
        benchmarks=("artificial_analysis_coding_index", "livecodebench"),
    ),
    "agentic": ComponentSpec(
        key="agentic",
        label="Agentic Index",
        weight=0.25,
        benchmarks=("tau2", "terminalbench_hard", "ifbench"),
    ),
}

BENCHMARK_LABELS = {
    "artificial_analysis_intelligence_index": "AA Intelligence Index",
    "artificial_analysis_math_index": "AA Math Index",
    "artificial_analysis_coding_index": "AA Coding Index",
    "livecodebench": "LiveCodeBench",
    "gpqa": "GPQA",
    "hle": "Humanity's Last Exam",
    "aime": "AIME",
    "aime_25": "AIME 2025",
    "math_500": "MATH-500",
    "mmlu_pro": "MMLU-Pro",
    "scicode": "SciCode",
    "lcr": "LCR",
    "tau2": "τ²-bench",
    "terminalbench_hard": "Terminal-Bench Hard",
    "ifbench": "IFBench",
}

AA_ENDPOINT = "https://artificialanalysis.ai/api/v2/data/llms/models"
LIVE_CODE_BENCH_ENDPOINT = "https://livecodebench.github.io/performances_generation.json"
DEFAULT_THRESHOLD = 0.95
DEFAULT_THRESHOLDS = [0.90, 0.93, 0.95, 0.98]
DEFAULT_INPUT_TOKENS = 1_000_000
DEFAULT_OUTPUT_TOKENS = 3_000_000


SCHEMA = """
pragma foreign_keys = on;

create table if not exists sources (
  id integer primary key,
  name text not null unique,
  base_url text not null,
  trust_tier text not null,
  attribution_url text,
  notes text
);

create table if not exists fetch_runs (
  id integer primary key,
  source_id integer not null references sources(id),
  endpoint text not null,
  fetched_at text not null,
  status text not null,
  checksum text not null,
  raw_path text,
  from_cache integer not null default 0
);

create table if not exists models (
  id integer primary key,
  canonical_name text not null unique,
  source_model_id text,
  slug text,
  creator_name text
);

create table if not exists model_aliases (
  id integer primary key,
  model_id integer not null references models(id),
  source_id integer not null references sources(id),
  alias text not null,
  unique(source_id, alias)
);

create table if not exists benchmarks (
  id integer primary key,
  key text not null unique,
  label text not null,
  component text,
  saturation_policy text not null default 'active_or_unknown',
  source_benchmark text,
  higher_is_better integer not null default 1
);

create table if not exists benchmark_observations (
  id integer primary key,
  source_id integer not null references sources(id),
  model_id integer not null references models(id),
  benchmark_id integer not null references benchmarks(id),
  fetch_run_id integer references fetch_runs(id),
  score real not null,
  score_unit text not null default 'ratio_or_index_score',
  observed_at text,
  eval_mode text,
  reasoning_effort text,
  scaffold_type text,
  source_url text,
  freshness_label text not null default 'current_from_source',
  trust_tier text not null default 'preferred',
  observation_kind text not null default 'source_score'
);

create table if not exists pricing_observations (
  id integer primary key,
  source_id integer not null references sources(id),
  model_id integer not null references models(id),
  fetch_run_id integer references fetch_runs(id),
  input_price_per_m real,
  output_price_per_m real,
  blended_price_per_m real,
  normalized_state text not null,
  billing_assumption text not null default 'source_reported_per_1m_tokens'
);

create table if not exists benchmark_resolutions (
  id integer primary key,
  model_id integer not null references models(id),
  benchmark_id integer not null references benchmarks(id),
  observation_id integer not null references benchmark_observations(id),
  index_version text not null default 'substitutionbench-v1',
  resolved_score real not null,
  resolution_policy text not null,
  conflict_count integer not null default 0,
  reason text not null,
  unique(model_id, benchmark_id, index_version)
);

create table if not exists index_versions (
  id integer primary key,
  key text not null unique,
  label text not null,
  default_threshold real not null,
  weighting_policy text not null
);

create table if not exists index_components (
  id integer primary key,
  index_version_id integer not null references index_versions(id),
  component_key text not null,
  label text not null,
  weight real not null,
  unique(index_version_id, component_key)
);

create table if not exists component_benchmarks (
  id integer primary key,
  component_key text not null,
  benchmark_id integer not null references benchmarks(id),
  weight real not null default 1,
  unique(component_key, benchmark_id)
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    ensure_index_version(conn)
    conn.commit()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_benchmark_label(key: str) -> str:
    return BENCHMARK_LABELS.get(key, key.replace("_", " ").title())


def component_for_benchmark(key: str) -> str | None:
    for component in DEFAULT_COMPONENTS.values():
        if key in component.benchmarks:
            return component.key
    return None


def ensure_source(conn: sqlite3.Connection, name: str, base_url: str, trust_tier: str, attribution_url: str | None = None, notes: str | None = None) -> int:
    conn.execute(
        """
        insert into sources(name, base_url, trust_tier, attribution_url, notes)
        values (?, ?, ?, ?, ?)
        on conflict(name) do update set
          base_url=excluded.base_url,
          trust_tier=excluded.trust_tier,
          attribution_url=coalesce(excluded.attribution_url, sources.attribution_url),
          notes=coalesce(excluded.notes, sources.notes)
        """,
        (name, base_url, trust_tier, attribution_url, notes),
    )
    return int(conn.execute("select id from sources where name = ?", (name,)).fetchone()[0])


def ensure_model(conn: sqlite3.Connection, name: str, source_id: int, source_model_id: str | None = None, slug: str | None = None, creator_name: str | None = None) -> int:
    conn.execute(
        """
        insert into models(canonical_name, source_model_id, slug, creator_name)
        values (?, ?, ?, ?)
        on conflict(canonical_name) do update set
          source_model_id=coalesce(models.source_model_id, excluded.source_model_id),
          slug=coalesce(models.slug, excluded.slug),
          creator_name=coalesce(models.creator_name, excluded.creator_name)
        """,
        (name, source_model_id, slug, creator_name),
    )
    model_id = int(conn.execute("select id from models where canonical_name = ?", (name,)).fetchone()[0])
    for alias in {name, slug or ""} - {""}:
        conn.execute(
            """
            insert into model_aliases(model_id, source_id, alias)
            values (?, ?, ?)
            on conflict(source_id, alias) do nothing
            """,
            (model_id, source_id, alias),
        )
    return model_id


def resolve_model_id(conn: sqlite3.Connection, source_id: int, alias: str) -> int | None:
    row = conn.execute(
        """
        select model_id from model_aliases where source_id = ? and alias = ?
        union
        select id from models where canonical_name = ?
        limit 1
        """,
        (source_id, alias, alias),
    ).fetchone()
    if row:
        return int(row[0])
    row = conn.execute("select id from models where lower(canonical_name) = lower(?)", (alias,)).fetchone()
    return int(row[0]) if row else None


def ensure_benchmark(conn: sqlite3.Connection, key: str, component: str | None = None, source_benchmark: str | None = None) -> int:
    conn.execute(
        """
        insert into benchmarks(key, label, component, source_benchmark)
        values (?, ?, ?, ?)
        on conflict(key) do update set
          label=excluded.label,
          component=coalesce(benchmarks.component, excluded.component),
          source_benchmark=coalesce(benchmarks.source_benchmark, excluded.source_benchmark)
        """,
        (key, canonical_benchmark_label(key), component or component_for_benchmark(key), source_benchmark or key),
    )
    benchmark_id = int(conn.execute("select id from benchmarks where key = ?", (key,)).fetchone()[0])
    if component or component_for_benchmark(key):
        conn.execute(
            """
            insert into component_benchmarks(component_key, benchmark_id, weight)
            values (?, ?, 1)
            on conflict(component_key, benchmark_id) do nothing
            """,
            (component or component_for_benchmark(key), benchmark_id),
        )
    return benchmark_id


def ensure_index_version(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        insert into index_versions(key, label, default_threshold, weighting_policy)
        values ('substitutionbench-v1', 'SubstitutionBench Index v1', ?, 'equal_component_weight')
        on conflict(key) do update set default_threshold=excluded.default_threshold, weighting_policy=excluded.weighting_policy
        """,
        (DEFAULT_THRESHOLD,),
    )
    index_id = int(conn.execute("select id from index_versions where key='substitutionbench-v1'").fetchone()[0])
    for component in DEFAULT_COMPONENTS.values():
        conn.execute(
            """
            insert into index_components(index_version_id, component_key, label, weight)
            values (?, ?, ?, ?)
            on conflict(index_version_id, component_key) do update set label=excluded.label, weight=excluded.weight
            """,
            (index_id, component.key, component.label, component.weight),
        )
        for benchmark in component.benchmarks:
            ensure_benchmark(conn, benchmark, component.key)


def add_fetch_run(conn: sqlite3.Connection, source_id: int, endpoint: str, fetched_at: str, status: str, checksum: str, raw_path: str | None, from_cache: bool) -> int:
    cur = conn.execute(
        """
        insert into fetch_runs(source_id, endpoint, fetched_at, status, checksum, raw_path, from_cache)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (source_id, endpoint, fetched_at, status, checksum, raw_path, int(from_cache)),
    )
    return int(cur.lastrowid)


def checksum_payload(payload: Any) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def pricing_state(input_price: Any, output_price: Any, blended_price: Any) -> str:
    prices = [input_price, output_price, blended_price]
    if all(value is None for value in prices):
        return "missing"
    numeric = []
    for value in prices:
        if value is None:
            continue
        try:
            numeric.append(float(value))
        except (TypeError, ValueError):
            return "invalid"
    if numeric and any(value == 0 for value in numeric):
        return "unknown_zero"
    if numeric and all(value > 0 for value in numeric):
        return "valid"
    return "invalid"


def maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def ingest_artificial_analysis_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    endpoint: str = AA_ENDPOINT,
    fetched_at: str | None = None,
    raw_path: str | None = None,
    checksum: str | None = None,
    from_cache: bool = False,
) -> int:
    init_db(conn)
    source_id = ensure_source(
        conn,
        "artificial_analysis",
        "https://artificialanalysis.ai/",
        "preferred_aggregator",
        "https://artificialanalysis.ai/",
        "Preferred source for current model roster, pricing, speed, and actively maintained eval fields.",
    )
    wrapped_payload = payload.get("payload", payload)
    run_id = add_fetch_run(
        conn,
        source_id,
        endpoint,
        fetched_at or now_utc(),
        str(wrapped_payload.get("status", "ok")),
        checksum or checksum_payload(wrapped_payload),
        raw_path,
        from_cache,
    )
    models = wrapped_payload.get("data", [])
    for model in models:
        creator = model.get("model_creator") or {}
        model_id = ensure_model(
            conn,
            str(model.get("name") or model.get("slug") or model.get("id")),
            source_id,
            source_model_id=model.get("id"),
            slug=model.get("slug"),
            creator_name=creator.get("name"),
        )
        pricing = model.get("pricing") or {}
        input_price = maybe_float(pricing.get("price_1m_input_tokens"))
        output_price = maybe_float(pricing.get("price_1m_output_tokens"))
        blended_price = maybe_float(pricing.get("price_1m_blended_3_to_1"))
        conn.execute(
            """
            insert into pricing_observations(
              source_id, model_id, fetch_run_id, input_price_per_m, output_price_per_m, blended_price_per_m, normalized_state
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (source_id, model_id, run_id, input_price, output_price, blended_price, pricing_state(input_price, output_price, blended_price)),
        )
        for key, raw_score in (model.get("evaluations") or {}).items():
            score = maybe_float(raw_score)
            if score is None:
                continue
            benchmark_id = ensure_benchmark(conn, key)
            conn.execute(
                """
                insert into benchmark_observations(
                  source_id, model_id, benchmark_id, fetch_run_id, score, observed_at,
                  eval_mode, reasoning_effort, scaffold_type, source_url, freshness_label, trust_tier, observation_kind
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    model_id,
                    benchmark_id,
                    run_id,
                    score,
                    fetched_at or now_utc(),
                    eval_mode_for_aa(key),
                    effort_from_name(str(model.get("name") or "")),
                    None,
                    endpoint,
                    freshness_label_for_aa(key),
                    "preferred_aggregator",
                    "source_score",
                ),
            )
    conn.commit()
    return run_id


def effort_from_name(name: str) -> str | None:
    lower = name.lower()
    for effort in ("xhigh", "high", "medium", "low", "reasoning", "non-reasoning"):
        if effort in lower:
            return effort
    return None


def freshness_label_for_aa(key: str) -> str:
    if key in {"math_500", "aime", "aime_25", "mmlu_pro"}:
        return "may_be_saturated_or_not_refreshed"
    return "current_from_source"


def eval_mode_for_aa(key: str) -> str | None:
    if key == "livecodebench":
        return "generation:aggregate_mean_pass_at_1"
    return None


def ingest_livecodebench_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    endpoint: str = LIVE_CODE_BENCH_ENDPOINT,
    fetched_at: str | None = None,
    raw_path: str | None = None,
    checksum: str | None = None,
    from_cache: bool = False,
) -> int:
    init_db(conn)
    source_id = ensure_source(
        conn,
        "livecodebench",
        "https://livecodebench.github.io/",
        "official_benchmark",
        "https://livecodebench.github.io/leaderboard.html",
        "Official LiveCodeBench public JSON; preferred for equivalent LiveCodeBench rows.",
    )
    run_id = add_fetch_run(
        conn,
        source_id,
        endpoint,
        fetched_at or now_utc(),
        "ok",
        checksum or checksum_payload(payload),
        raw_path,
        from_cache,
    )
    benchmark_id = ensure_benchmark(conn, "livecodebench", "coding", "performances_generation")
    model_meta = {model.get("model_repr") or model.get("model_name"): model for model in payload.get("models", [])}
    grouped: dict[str, list[dict[str, Any]]] = {}
    aa_source_row = conn.execute("select id from sources where name = 'artificial_analysis'").fetchone()
    aa_source_id = int(aa_source_row[0]) if aa_source_row else None
    for performance in payload.get("performances", []):
        model_name = str(performance.get("model") or "").strip()
        score = maybe_float(performance.get("pass@1"))
        if not model_name or score is None:
            continue
        grouped.setdefault(model_name, []).append(performance)
    for model_name, performances in grouped.items():
        existing_model_id = resolve_model_id(conn, source_id, model_name)
        if existing_model_id is None and aa_source_id is not None:
            existing_model_id = resolve_model_id(conn, aa_source_id, model_name)
        meta = model_meta.get(model_name, {})
        model_id = existing_model_id or ensure_model(conn, model_name, source_id, slug=meta.get("model_name"))
        conn.execute(
            """
            insert into model_aliases(model_id, source_id, alias)
            values (?, ?, ?)
            on conflict(source_id, alias) do nothing
            """,
            (model_id, source_id, model_name),
        )
        scores: list[float] = []
        dates: list[int] = []
        for performance in performances:
            score = maybe_float(performance.get("pass@1"))
            if score is None:
                continue
            scores.append(score / 100.0)
            date_value = performance.get("date")
            observed_at = fetched_at or now_utc()
            if isinstance(date_value, int):
                dates.append(date_value)
                observed_at = datetime.fromtimestamp(date_value / 1000, tz=timezone.utc).date().isoformat()
            difficulty = performance.get("difficulty") or "unknown"
            question_id = performance.get("question_id") or "unknown_question"
            conn.execute(
                """
                insert into benchmark_observations(
                  source_id, model_id, benchmark_id, fetch_run_id, score, observed_at,
                  eval_mode, reasoning_effort, scaffold_type, source_url, freshness_label, trust_tier, observation_kind
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    model_id,
                    benchmark_id,
                    run_id,
                    score / 100.0,
                    observed_at,
                    f"generation:{difficulty}:{question_id}",
                    None,
                    None,
                    endpoint,
                    "official_time_sliced_row",
                    "official_benchmark",
                    "supporting_row",
                ),
            )
        if not scores:
            continue
        observed_at = fetched_at or now_utc()
        if dates:
            observed_at = datetime.fromtimestamp(max(dates) / 1000, tz=timezone.utc).date().isoformat()
        conn.execute(
            """
            insert into benchmark_observations(
              source_id, model_id, benchmark_id, fetch_run_id, score, observed_at,
              eval_mode, reasoning_effort, scaffold_type, source_url, freshness_label, trust_tier, observation_kind
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                model_id,
                benchmark_id,
                run_id,
                sum(scores) / len(scores),
                observed_at,
                "generation:aggregate_mean_pass_at_1",
                None,
                None,
                endpoint,
                "official_time_sliced_aggregate",
                "official_benchmark",
                "aggregate_score",
            ),
        )
    conn.commit()
    return run_id


def source_priority(source_name: str, benchmark_key: str) -> int:
    if benchmark_key == "livecodebench" and source_name == "livecodebench":
        return 0
    if source_name == "artificial_analysis":
        return 1
    if source_name == "livecodebench":
        return 2
    return 10


def protocol_key(row: sqlite3.Row) -> str:
    benchmark_key = row["benchmark_key"]
    if benchmark_key == "livecodebench":
        return ":".join(
            [
                benchmark_key,
                str(row["score_unit"] or "unknown_unit"),
                str(row["eval_mode"] or "unknown_eval_mode"),
                str(row["scaffold_type"] or "unknown_scaffold"),
            ]
        )
    return benchmark_key


def resolve_scores(conn: sqlite3.Connection, index_version: str = "substitutionbench-v1") -> None:
    init_db(conn)
    conn.execute("delete from benchmark_resolutions where index_version = ?", (index_version,))
    pairs = conn.execute(
        """
        select distinct model_id, benchmark_id from benchmark_observations
        """
    ).fetchall()
    for pair in pairs:
        observations = conn.execute(
            """
            select bo.*, s.name as source_name, b.key as benchmark_key
            from benchmark_observations bo
            join sources s on s.id = bo.source_id
            join benchmarks b on b.id = bo.benchmark_id
            where bo.model_id = ? and bo.benchmark_id = ? and bo.observation_kind != 'supporting_row'
            order by bo.id
            """,
            (pair[0], pair[1]),
        ).fetchall()
        if not observations:
            continue
        ranked_all = sorted(observations, key=lambda row: (source_priority(row["source_name"], row["benchmark_key"]), -row["id"]))
        preferred_protocol = protocol_key(ranked_all[0])
        compatible_observations = [row for row in observations if protocol_key(row) == preferred_protocol]
        incompatible_count = len(observations) - len(compatible_observations)
        ranked = sorted(compatible_observations, key=lambda row: (source_priority(row["source_name"], row["benchmark_key"]), -row["id"]))
        winner = ranked[0]
        distinct_alternates = {(row["source_name"], round(float(row["score"]), 12)) for row in compatible_observations}
        conflict_count = max(0, len(distinct_alternates) - 1)
        policy = "preferred_source_hierarchy"
        reason = f"Selected {winner['source_name']} for {winner['benchmark_key']} via preferred-source hierarchy among protocol-equivalent observations ({preferred_protocol})."
        if conflict_count:
            reason += f" Preserved {conflict_count} alternate observation(s)."
        if incompatible_count:
            reason += f" Preserved {incompatible_count} protocol-incompatible observation(s) without collapsing them into the resolved score."
        conn.execute(
            """
            insert into benchmark_resolutions(
              model_id, benchmark_id, observation_id, index_version, resolved_score, resolution_policy, conflict_count, reason
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (winner["model_id"], winner["benchmark_id"], winner["id"], index_version, winner["score"], policy, conflict_count, reason),
        )
    conn.commit()


def latest_pricing(conn: sqlite3.Connection, model_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """
        select * from pricing_observations
        where model_id = ?
        order by id desc
        limit 1
        """,
        (model_id,),
    ).fetchone()


def estimated_task_cost(row: sqlite3.Row | None, input_tokens: int = DEFAULT_INPUT_TOKENS, output_tokens: int = DEFAULT_OUTPUT_TOKENS) -> float | None:
    if row is None or row["normalized_state"] != "valid":
        return None
    if row["input_price_per_m"] is None or row["output_price_per_m"] is None:
        return None
    return (float(row["input_price_per_m"]) * (input_tokens / 1_000_000)) + (float(row["output_price_per_m"]) * (output_tokens / 1_000_000))


def benchmark_anchors(conn: sqlite3.Connection) -> dict[str, float]:
    anchors: dict[str, float] = {}
    for row in conn.execute("select id, key from benchmarks"):
        scores = [float(score[0]) for score in conn.execute(
            "select resolved_score from benchmark_resolutions where benchmark_id = ? order by resolved_score desc",
            (row["id"],),
        ).fetchall()]
        if scores:
            top = scores[:3]
            anchors[row["key"]] = sum(top) / len(top)
    return anchors


def score_for(conn: sqlite3.Connection, model_id: int, benchmark_key: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        select br.*, b.key as benchmark_key, b.label as benchmark_label, bo.freshness_label, bo.source_url, s.name as source_name
        from benchmark_resolutions br
        join benchmarks b on b.id = br.benchmark_id
        join benchmark_observations bo on bo.id = br.observation_id
        join sources s on s.id = bo.source_id
        where br.model_id = ? and b.key = ? and br.index_version = 'substitutionbench-v1'
        """,
        (model_id, benchmark_key),
    ).fetchone()


def component_result(conn: sqlite3.Connection, model_id: int, component: ComponentSpec, anchors: dict[str, float]) -> dict[str, Any]:
    benchmark_results = []
    ratios = []
    missing = []
    conflicts = 0
    for benchmark_key in component.benchmarks:
        resolution = score_for(conn, model_id, benchmark_key)
        anchor = anchors.get(benchmark_key)
        if resolution is None or not anchor:
            missing.append(benchmark_key)
            benchmark_results.append({
                "key": benchmark_key,
                "label": canonical_benchmark_label(benchmark_key),
                "coverage_state": "unknown",
                "frontier_ratio": None,
            })
            continue
        ratio = float(resolution["resolved_score"]) / anchor
        ratios.append(ratio)
        conflicts += int(resolution["conflict_count"])
        benchmark_results.append({
            "key": benchmark_key,
            "label": canonical_benchmark_label(benchmark_key),
            "coverage_state": "complete",
            "score": round(float(resolution["resolved_score"]), 6),
            "frontier_anchor": round(anchor, 6),
            "frontier_ratio": round(ratio, 6),
            "source": resolution["source_name"],
            "freshness_label": resolution["freshness_label"],
            "conflict_count": int(resolution["conflict_count"]),
            "resolution_reason": resolution["reason"],
        })
    if len(ratios) == len(component.benchmarks):
        state = "complete"
        value = sum(ratios) / len(ratios)
    elif ratios:
        state = "partial"
        value = None
    else:
        state = "unknown"
        value = None
    return {
        "key": component.key,
        "label": component.label,
        "weight": component.weight,
        "coverage_state": state,
        "frontier_ratio": round(value, 6) if value is not None else None,
        "benchmarks": benchmark_results,
        "missing_benchmarks": missing,
        "conflict_count": conflicts,
    }


def classify_models(models: list[dict[str, Any]], threshold: float = DEFAULT_THRESHOLD) -> None:
    complete = [model for model in models if model.get("frontier_ratio") is not None]
    if not complete:
        for model in models:
            model["state"] = "unknown"
        return
    top_ratio = max(float(model["frontier_ratio"]) for model in complete)
    frontier_candidates = [model for model in complete if abs(float(model["frontier_ratio"]) - top_ratio) < 1e-9]
    frontier_costs = [model["estimated_task_cost"] for model in frontier_candidates if model.get("estimated_task_cost") is not None]
    frontier_cost = min(frontier_costs) if frontier_costs else None
    for model in models:
        ratio = model.get("frontier_ratio")
        if ratio is None:
            model["state"] = "unknown"
        elif abs(float(ratio) - top_ratio) < 1e-9:
            model["state"] = "frontier"
        elif float(ratio) < threshold:
            model["state"] = "below_cutoff"
        elif model.get("estimated_task_cost") is not None and frontier_cost is not None and model["estimated_task_cost"] < frontier_cost:
            model["state"] = "substitute"
        else:
            model["state"] = "quality_expensive"


def build_index_payload(conn: sqlite3.Connection, index_key: str, label: str, components: Iterable[ComponentSpec], anchors: dict[str, float]) -> dict[str, Any]:
    component_list = list(components)
    model_rows = conn.execute("select id, canonical_name, creator_name from models order by canonical_name").fetchall()
    models = []
    for model_row in model_rows:
        component_results = [component_result(conn, int(model_row["id"]), component, anchors) for component in component_list]
        complete_values = [component["frontier_ratio"] for component in component_results if component["coverage_state"] == "complete"]
        conflict_count = sum(int(component["conflict_count"]) for component in component_results)
        if len(complete_values) == len(component_results):
            frontier_ratio = sum(float(value) * component_list[i].weight for i, value in enumerate(complete_values)) / sum(c.weight for c in component_list)
            coverage_state = "complete"
        elif complete_values:
            frontier_ratio = None
            coverage_state = "partial"
        else:
            frontier_ratio = None
            coverage_state = "unknown"
        price = latest_pricing(conn, int(model_row["id"]))
        cost = estimated_task_cost(price)
        models.append({
            "model_id": int(model_row["id"]),
            "model": model_row["canonical_name"],
            "creator": model_row["creator_name"],
            "frontier_ratio": round(frontier_ratio, 6) if frontier_ratio is not None else None,
            "coverage_state": coverage_state,
            "components": component_results,
            "conflict_count": conflict_count,
            "price_state": price["normalized_state"] if price else "missing",
            "input_price_per_m": price["input_price_per_m"] if price else None,
            "output_price_per_m": price["output_price_per_m"] if price else None,
            "blended_price_per_m": price["blended_price_per_m"] if price else None,
            "estimated_task_cost": round(cost, 6) if cost is not None else None,
        })
    classify_models(models, DEFAULT_THRESHOLD)
    models.sort(key=lambda item: (item["frontier_ratio"] is None, -(item["frontier_ratio"] or -1), item["estimated_task_cost"] is None, item["estimated_task_cost"] or 10**9, item["model"]))
    summary = {
        "complete": sum(1 for model in models if model["coverage_state"] == "complete"),
        "partial": sum(1 for model in models if model["coverage_state"] == "partial"),
        "unknown": sum(1 for model in models if model["coverage_state"] == "unknown"),
        "qualifying": sum(1 for model in models if model.get("frontier_ratio") is not None and model["frontier_ratio"] >= DEFAULT_THRESHOLD),
        "substitutes": sum(1 for model in models if model.get("state") == "substitute"),
        "no_substitute": not any(model.get("state") == "substitute" for model in models),
        "total_models": len(models),
    }
    return {
        "key": index_key,
        "label": label,
        "threshold": DEFAULT_THRESHOLD,
        "components": [{"key": component.key, "label": component.label, "weight": component.weight, "benchmarks": list(component.benchmarks)} for component in component_list],
        "substitution_summary": summary,
        "models": models,
    }


def source_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {
            "source": row["name"],
            "trust_tier": row["trust_tier"],
            "fetch_runs": int(row["fetch_runs"] or 0),
            "observations": int(row["observations"] or 0),
            "latest_fetch": row["latest_fetch"],
            "attribution_url": row["attribution_url"],
        }
        for row in conn.execute(
            """
            select s.name, s.trust_tier, s.attribution_url,
                   count(distinct fr.id) as fetch_runs,
                   count(distinct bo.id) as observations,
                   max(fr.fetched_at) as latest_fetch
            from sources s
            left join fetch_runs fr on fr.source_id = s.id
            left join benchmark_observations bo on bo.source_id = s.id
            group by s.id
            order by s.name
            """
        )
    ]


def conflict_examples(conn: sqlite3.Connection, limit: int = 12) -> list[dict[str, Any]]:
    examples = []
    rows = conn.execute(
        """
        select br.id as resolution_id, br.model_id, br.benchmark_id, br.resolved_score,
               br.conflict_count, br.reason, m.canonical_name as model, b.key as benchmark_key,
               b.label as benchmark_label, s.name as winning_source, bo.freshness_label
        from benchmark_resolutions br
        join models m on m.id = br.model_id
        join benchmarks b on b.id = br.benchmark_id
        join benchmark_observations bo on bo.id = br.observation_id
        join sources s on s.id = bo.source_id
        where br.conflict_count > 0
        order by br.conflict_count desc, br.id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    for row in rows:
        alternates = [
            {
                "source": alt["source_name"],
                "score": round(float(alt["score"]), 6),
                "observed_at": alt["observed_at"],
                "freshness_label": alt["freshness_label"],
                "observation_kind": alt["observation_kind"],
            }
            for alt in conn.execute(
                """
                select s.name as source_name, bo.score, bo.observed_at, bo.freshness_label, bo.observation_kind
                from benchmark_observations bo
                join sources s on s.id = bo.source_id
                where bo.model_id = ? and bo.benchmark_id = ? and bo.observation_kind != 'supporting_row'
                order by s.name, bo.score desc
                """,
                (row["model_id"], row["benchmark_id"]),
            )
        ]
        examples.append({
            "model": row["model"],
            "benchmark_key": row["benchmark_key"],
            "benchmark_label": row["benchmark_label"],
            "resolved_score": round(float(row["resolved_score"]), 6),
            "winning_source": row["winning_source"],
            "freshness_label": row["freshness_label"],
            "conflict_count": int(row["conflict_count"]),
            "resolution_reason": row["reason"],
            "observations": alternates,
        })
    return examples


def export_dashboard_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    anchors = benchmark_anchors(conn)
    top_index = build_index_payload(conn, "substitutionbench-v1", "SubstitutionBench Index v1", DEFAULT_COMPONENTS.values(), anchors)
    component_indexes = [
        build_index_payload(conn, f"{component.key}-index", component.label, [component], anchors)
        for component in DEFAULT_COMPONENTS.values()
    ]
    return {
        "generated_at": now_utc(),
        "default_index": "substitutionbench-v1",
        "default_threshold": DEFAULT_THRESHOLD,
        "thresholds": DEFAULT_THRESHOLDS,
        "task_assumptions": {
            "input_tokens": DEFAULT_INPUT_TOKENS,
            "output_tokens": DEFAULT_OUTPUT_TOKENS,
            "cost_formula": "input_price_per_m * input_tokens/1M + output_price_per_m * output_tokens/1M",
        },
        "cache_freshness": {
            "latest_fetch": max((row["latest_fetch"] for row in source_summary(conn) if row["latest_fetch"]), default=None),
            "policy": "server-side/local SQLite cache; static dashboard consumes generated resolved-score artifact",
        },
        "source_summary": source_summary(conn),
        "conflict_examples": conflict_examples(conn),
        "benchmarks": [dict(row) for row in conn.execute("select key, label, component, saturation_policy from benchmarks order by key")],
        "indexes": [top_index, *component_indexes],
    }


def write_dashboard_data(payload: dict[str, Any], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("window.SUBSTITUTION_BENCH_DATA = " + json.dumps(payload, sort_keys=True, separators=(",", ":")) + ";\n")
