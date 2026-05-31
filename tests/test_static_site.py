from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_static_site_exposes_mobile_first_dashboard_sections() -> None:
    html = (ROOT / "docs" / "index.html").read_text()

    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in html
    assert "Substitution floors, not leaderboards." in html
    assert "status-board" in html
    assert "price-floor-chart" in html
    assert "threshold-matrix" in html
    assert "evidence-ladder" in html
    assert "mobile-threshold" in html


def test_static_site_javascript_does_not_classify_unsaturated_as_saturated() -> None:
    js = (ROOT / "docs" / "app.js").read_text()

    assert "kind.includes('saturated')" not in js
    assert "kind === 'saturated' || kind === 'near_saturated'" in js


def test_static_site_uses_visual_price_and_gap_encodings() -> None:
    js = (ROOT / "docs" / "app.js").read_text()
    css = (ROOT / "docs" / "styles.css").read_text()

    assert "savingsMultiple" in js
    assert "renderPriceFloorChart" in js
    assert "renderThresholdMatrix" in js
    assert "renderEvidenceLadder" in js
    assert ".price-track" in css
    assert ".gap-track" in css


def test_static_site_data_matches_mvp_benchmarks() -> None:
    data_js = (ROOT / "docs" / "data.js").read_text()
    prefix = "window.SUBSTITUTION_BENCH_DATA = "
    assert data_js.startswith(prefix)
    payload = json.loads(data_js[len(prefix):].rstrip(";\n"))

    assert sorted(payload["configs"]) == ["GPQA Diamond", "MATH-500", "SWE-bench Verified"]
    assert {1, 3, 5} == set(payload["thresholds"])
    assert any(row["model"] == "Qwen3 30B A3B Thinking" for row in payload["observations"])
    assert any(row["model"] == "Claude Opus 4.8" for row in payload["observations"])
