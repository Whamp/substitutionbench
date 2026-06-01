from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_payload() -> dict:
    data_js = (ROOT / "docs" / "data.js").read_text()
    prefix = "window.SUBSTITUTION_BENCH_DATA = "
    assert data_js.startswith(prefix)
    return json.loads(data_js[len(prefix):].rstrip(";\n"))


def test_static_site_exposes_mobile_first_frontier_ratio_dashboard_sections() -> None:
    html = (ROOT / "docs" / "index.html").read_text()

    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in html
    assert "SubstitutionBench Index v1" in html
    assert "threshold-slider" in html
    assert "index-selector" in html
    assert "index-hero-chart" in html
    assert "cost-ranking" in html
    assert "source-transparency" in html
    assert "No substitute yet" in html
    assert "JND" not in html
    assert "just-noticeable" not in html


def test_static_site_javascript_uses_frontier_ratio_not_point_gap_language() -> None:
    js = (ROOT / "docs" / "app.js").read_text()

    assert "frontier_ratio" in js
    assert "renderIndexHeroChart" in js
    assert "renderCostRanking" in js
    assert "renderSourceTransparency" in js
    assert "renderNoSubstituteState" in js
    assert "vertical-separator" in js
    assert "JND" not in js
    assert "score_gap" not in js
    assert "frontier_score - row.score" not in js


def test_generated_data_matches_substitutionbench_index_contract() -> None:
    payload = load_payload()

    assert payload["default_index"] == "substitutionbench-v1"
    assert payload["default_threshold"] == 0.95
    assert {0.9, 0.93, 0.95, 0.98} <= set(payload["thresholds"])

    index = next(item for item in payload["indexes"] if item["key"] == "substitutionbench-v1")
    assert index["label"] == "SubstitutionBench Index v1"
    assert {component["key"] for component in index["components"]} == {"general", "math", "coding", "agentic"}
    assert {component["weight"] for component in index["components"]} == {0.25}
    assert all("frontier_ratio" in model for model in index["models"])
    assert all(model["coverage_state"] in {"complete", "partial", "unknown"} for model in index["models"])
    assert len(index["models"]) == index["substitution_summary"]["total_models"]


def test_generated_data_supports_cost_provenance_conflict_and_no_substitute_states() -> None:
    payload = load_payload()
    text = json.dumps(payload)

    assert "source_summary" in payload
    assert "cache_freshness" in payload
    assert "conflict_examples" in payload
    assert "conflict_count" in text
    assert "resolution_reason" in text
    assert "unknown_zero" in text or "price_unknown" in text
    assert any(index["substitution_summary"]["no_substitute"] for index in payload["indexes"])
    assert any(model["state"] == "frontier" for index in payload["indexes"] for model in index["models"])
    assert any(model["state"] in {"substitute", "quality_expensive", "below_cutoff"} for index in payload["indexes"] for model in index["models"])


def test_no_credentials_or_local_cache_paths_are_emitted_to_static_assets() -> None:
    for path in [ROOT / "docs" / "data.js", ROOT / "docs" / "app.js", ROOT / "docs" / "index.html"]:
        text = path.read_text()
        assert "ARTIFICIAL_ANALYSIS_API_KEY" not in text
        assert "x-api-key" not in text
        assert ".env" not in text


def test_dashboard_recomputes_summary_counts_when_threshold_changes() -> None:
    app_js = ROOT / "docs" / "app.js"
    script = textwrap.dedent(
        f"""
        const fs = require('fs');
        const vm = require('vm');
        const elements = {{}};
        const document = {{
          getElementById(id) {{
            if (!elements[id]) elements[id] = {{ innerHTML: '', textContent: '', hidden: false, value: '', oninput: null, onchange: null }};
            return elements[id];
          }}
        }};
        const payload = {{
          default_index: 'fixture-index',
          default_threshold: 0.95,
          indexes: [{{
            key: 'fixture-index',
            label: 'Fixture Index',
            components: [],
            substitution_summary: {{ complete: 3, partial: 0, unknown: 0, qualifying: 1, substitutes: 0, no_substitute: true, total_models: 3 }},
            models: [
              {{ model: 'Frontier', frontier_ratio: 1.0, coverage_state: 'complete', price_state: 'valid', estimated_task_cost: 10, components: [], conflict_count: 0 }},
              {{ model: 'Cheap 92', frontier_ratio: 0.92, coverage_state: 'complete', price_state: 'valid', estimated_task_cost: 1, components: [], conflict_count: 0 }},
              {{ model: 'Cheap 89', frontier_ratio: 0.89, coverage_state: 'complete', price_state: 'valid', estimated_task_cost: 1, components: [], conflict_count: 0 }}
            ]
          }}],
          source_summary: [],
          conflict_examples: [],
          cache_freshness: {{ policy: 'fixture', latest_fetch: null }}
        }};
        const context = {{ console, window: {{ SUBSTITUTION_BENCH_DATA: payload }}, document, Number, Math }};
        vm.createContext(context);
        vm.runInContext(fs.readFileSync({str(app_js)!r}, 'utf8'), context);
        context.window.__SUBSTITUTION_BENCH_TEST__.state.threshold = 0.90;
        context.window.__SUBSTITUTION_BENCH_TEST__.renderHeadline();
        context.window.__SUBSTITUTION_BENCH_TEST__.renderMetricStrip();
        const headline = elements['headline-chips'].innerHTML;
        const metrics = elements['metric-strip'].innerHTML;
        if (!headline.includes('1 substitutes')) throw new Error('headline substitute count did not update: ' + headline);
        if (!headline.includes('2/3 qualify')) throw new Error('headline qualifying count did not update: ' + headline);
        if (!metrics.includes('2/3')) throw new Error('metric strip qualifying count did not update: ' + metrics);
        """
    )
    subprocess.run(["node", "-e", script], check=True)
