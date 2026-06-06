from __future__ import annotations

import json
import re
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
    assert "task-finder" in html
    assert "task-search-input" in html
    assert "router-frontier" in html
    assert "router-frontier-chart" in html
    assert "decision-domain" in html
    assert "No substitute yet" in html
    versions = re.findall(r'\b(?:href|src)="(?:styles|data|app)\.(?:css|js)\?v=([^"]+)"', html)
    assert versions == ["hidden-state-20260604", "hidden-state-20260604", "hidden-state-20260604"]
    assert "JND" not in html
    assert "just-noticeable" not in html


def test_static_site_javascript_uses_frontier_ratio_not_point_gap_language() -> None:
    js = (ROOT / "docs" / "app.js").read_text()

    assert "frontier_ratio" in js
    assert "renderIndexHeroChart" in js
    assert "renderCostRanking" in js
    assert "renderSourceTransparency" in js
    assert "renderTaskFinder" in js
    assert "renderRouterFrontier" in js
    assert "routerPolicyPoints" in js
    assert "taskSearchMatches" in js
    assert "decisionTreeMatches" in js
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
    assert all(model["coverage_state"] in {"complete", "assumed_complete", "partial", "unknown"} for model in index["models"])
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


def test_laptop_layout_constrains_wide_dashboard_sections() -> None:
    css = (ROOT / "docs" / "styles.css").read_text()

    # Regression coverage for laptop-width dogfood: CSS grid items default to
    # min-width:auto, which let the 30-column hero chart force the whole page to
    # ~2600px wide. The chart should scroll inside its panel, not the page.
    assert ".panel { border-radius: var(--radius-lg); padding: var(--space-5); overflow: hidden; }" in css
    assert ".metric-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));" in css
    assert ".component-drilldown { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));" in css
    assert ".transparency-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));" in css
    assert "grid-auto-columns: minmax(72px, 1fr)" in css
    assert "overscroll-behavior-inline: contain" in css
    assert "[hidden] { display: none !important; }" in css
    js = (ROOT / "docs" / "app.js").read_text()
    assert "function heroChartLimit()" in js
    assert "return 12;" in js
    assert "slice(0, heroChartLimit())" in js


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
          router_policy_references: [],
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


def test_router_frontier_renders_policy_points_and_source_confidence() -> None:
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
          indexes: [{{ key: 'fixture-index', label: 'Fixture Index', components: [], substitution_summary: {{}}, models: [] }}],
          benchmarks: [],
          router_policy_references: [{{
            key: 'factory_router',
            label: 'Factory Router',
            candidate_type: 'router_with_escalation_and_failover',
            source_confidence: 'vendor_claim_public_aggregate',
            summary: 'Public Factory claim on Terminal-Bench 2 and Legacy-Bench.',
            caveat: 'Vendor aggregate only.',
            pareto_points: [
              {{ benchmark_key: 'terminal_bench_2', benchmark_label: 'Terminal-Bench 2', policy_label: 'shipping', relative_pass_rate: 0.99, relative_session_cost: 0.80, relative_cost_per_success: 0.805, floor_tier: 'frontier_equivalent' }},
              {{ benchmark_key: 'legacy_bench', benchmark_label: 'Legacy-Bench', policy_label: 'aggressive', relative_pass_rate: 0.49, relative_session_cost: 0.30, relative_cost_per_success: null, floor_tier: 'aggressive_degraded' }}
            ]
          }}],
          source_summary: [], conflict_examples: [], cache_freshness: {{ policy: 'fixture', latest_fetch: null }}
        }};
        const context = {{ console, window: {{ SUBSTITUTION_BENCH_DATA: payload }}, document, Number, Math }};
        vm.createContext(context);
        vm.runInContext(fs.readFileSync({str(app_js)!r}, 'utf8'), context);
        const api = context.window.__SUBSTITUTION_BENCH_TEST__;
        const points = api.routerPolicyPoints(payload.router_policy_references[0]);
        if (points.length !== 2) throw new Error('expected two router policy points');
        api.renderRouterFrontier();
        const rendered = elements['router-frontier-chart'].innerHTML + elements['router-frontier-summary'].innerHTML;
        if (!rendered.includes('Factory Router')) throw new Error('missing router label: ' + rendered);
        if (!rendered.includes('Terminal-Bench 2')) throw new Error('missing benchmark point: ' + rendered);
        if (!rendered.includes('99.0% pass')) throw new Error('missing pass label: ' + rendered);
        if (!rendered.includes('80.5% cost/success')) throw new Error('missing cost per success: ' + rendered);
        if (!rendered.includes('vendor claim')) throw new Error('missing source confidence caveat: ' + rendered);
        """
    )
    subprocess.run(["node", "-e", script], check=True)


def test_task_finder_search_maps_plain_english_work_to_benchmark_cards() -> None:
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
          indexes: [{{ key: 'fixture-index', label: 'Fixture Index', components: [], substitution_summary: {{}}, models: [] }}],
          benchmarks: [
            {{
              key: 'swe_bench_verified',
              label: 'SWE-bench Verified',
              task_class: 'Code editing / software engineering',
              plain_english_task: 'Fix real bugs in existing GitHub repositories.',
              substitution_claim_when_saturated: 'Cheaper agent stacks can handle verified repo bug fixes.',
              does_not_prove: 'Does not prove product architecture judgment.',
              protocol_notes: 'Agent scaffold matters.',
              aliases: ['repo bugs', 'fix bugs', 'existing repo'],
              decision_tags: ['actions', 'verifiable', 'code_editing', 'repo_coupled'],
              substitution_candidates: [{{ model: 'Cheap Patch', frontier_ratio: 0.96, estimated_task_cost: 1, frontier_task_cost: 10 }}],
              substitution_floor: {{ model: 'Cheap Patch', frontier_ratio: 0.96, estimated_task_cost: 1, frontier_task_cost: 10 }}
            }},
            {{
              key: 'gpqa', label: 'GPQA', task_class: 'Science QA', plain_english_task: 'Answer hard graduate science questions.',
              substitution_claim_when_saturated: 'Cheaper models can answer some expert science QA.', does_not_prove: 'Does not prove lab work.',
              protocol_notes: '', aliases: ['science'], decision_tags: ['answer', 'verifiable', 'science'], substitution_candidates: [], substitution_floor: null
            }}
          ],
          router_policy_references: [],
          source_summary: [], conflict_examples: [], cache_freshness: {{ policy: 'fixture', latest_fetch: null }}
        }};
        const context = {{ console, window: {{ SUBSTITUTION_BENCH_DATA: payload }}, document, Number, Math }};
        vm.createContext(context);
        vm.runInContext(fs.readFileSync({str(app_js)!r}, 'utf8'), context);
        const api = context.window.__SUBSTITUTION_BENCH_TEST__;
        const searchHit = api.taskSearchMatches('fix bugs in an existing repo')[0];
        if (searchHit.key !== 'swe_bench_verified') throw new Error('expected SWE-bench search hit, got ' + searchHit.key);
        if (api.taskSearchMatches('make me a sandwich').length !== 0) throw new Error('irrelevant sandwich query should not produce benchmark matches');
        api.state.decisionWorkflow = 'actions';
        api.state.decisionDomain = 'code_editing';
        const treeHit = api.decisionTreeMatches()[0];
        if (treeHit.key !== 'swe_bench_verified') throw new Error('expected SWE-bench tree hit, got ' + treeHit.key);
        api.state.decisionWorkflow = 'actions';
        api.state.decisionDomain = 'science';
        if (api.decisionTreeMatches().length !== 0) throw new Error('conflicting chooser tags should not return OR matches');
        api.state.decisionWorkflow = '';
        api.state.decisionDomain = '';
        elements['task-search-input'].value = 'fix bugs in an existing repo';
        api.renderTaskFinder(false);
        const rendered = elements['task-results'].innerHTML;
        if (!rendered.includes('SWE-bench Verified')) throw new Error('missing rendered benchmark card: ' + rendered);
        if (!rendered.includes('Cheap Patch')) throw new Error('missing cheapest model floor: ' + rendered);
        if (!rendered.includes('Does not prove')) throw new Error('missing caveat copy: ' + rendered);
        """
    )
    subprocess.run(["node", "-e", script], check=True)
