from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_static_site_exposes_mobile_first_dashboard_sections() -> None:
    html = (ROOT / "docs" / "index.html").read_text()

    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in html
    assert "Substitution floors, not leaderboards." in html
    assert "status-board" in html
    assert "plot deck" in html.lower()
    assert "value-map" in html
    assert "benchmark-bars" in html
    assert "cost-economics" in html
    assert "substitution-leaderboard" in html
    assert "model-universe" in html
    assert "JND, or just-noticeable difference" in html
    assert "mobile-threshold" in html


def test_static_site_javascript_does_not_classify_unsaturated_as_saturated() -> None:
    js = (ROOT / "docs" / "app.js").read_text()

    assert "kind.includes('saturated')" not in js
    assert "kind === 'saturated' || kind === 'near_saturated'" in js


def test_static_site_uses_visual_price_and_gap_encodings() -> None:
    js = (ROOT / "docs" / "app.js").read_text()
    css = (ROOT / "docs" / "styles.css").read_text()

    assert "savingsMultiple" in js
    assert "renderValueMap" in js
    assert "renderBenchmarkBars" in js
    assert "renderCostEconomics" in js
    assert "renderSubstitutionCurve" in js
    assert "renderBenchmarkGuide" in js
    assert "renderModelUniverse" in js
    assert "qualificationLine" in js
    assert ".value-map" in css
    assert ".bench-chart" in css
    assert ".bench-bar" in css
    assert ".safe-zone" in css
    assert ".cost-stack" in css
    assert ".curve-bar-wrap" in css
    assert ".curve-cutoff" in css
    assert ".substitution-curve" in css
    assert ".benchmark-guide" in css
    assert ".model-list" in css


def test_static_site_data_matches_mvp_benchmarks() -> None:
    data_js = (ROOT / "docs" / "data.js").read_text()
    prefix = "window.SUBSTITUTION_BENCH_DATA = "
    assert data_js.startswith(prefix)
    payload = json.loads(data_js[len(prefix):].rstrip(";\n"))

    assert sorted(payload["configs"]) == ["GPQA Diamond", "MATH-500", "SWE-bench Verified"]
    assert {1, 3, 5} == set(payload["thresholds"])
    assert any(row["model"] == "Qwen3 30B A3B Thinking" for row in payload["observations"])
    assert any(row["model"] == "Claude Opus 4.8" for row in payload["observations"])
