from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_static_site_exposes_mobile_mvp_dashboard() -> None:
    html = (ROOT / "docs" / "index.html").read_text()

    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in html
    assert "How cheap can you go before anyone notices?" in html
    assert "data-threshold=\"1\"" in html
    assert "data-threshold=\"3\"" in html
    assert "data-threshold=\"5\"" in html
    assert "benchmark-select" in html


def test_static_site_javascript_does_not_classify_unsaturated_as_saturated() -> None:
    js = (ROOT / "docs" / "app.js").read_text()

    assert "kind.includes('saturated')" not in js
    assert "kind === 'saturated' || kind === 'near_saturated'" in js


def test_static_site_data_matches_mvp_benchmarks() -> None:
    data_js = (ROOT / "docs" / "data.js").read_text()
    prefix = "window.SUBSTITUTION_BENCH_DATA = "
    assert data_js.startswith(prefix)
    payload = json.loads(data_js[len(prefix):].rstrip(";\n"))

    assert sorted(payload["configs"]) == ["GPQA Diamond", "MATH-500", "SWE-bench Verified"]
    assert {1, 3, 5} == set(payload["thresholds"])
    assert any(row["model"] == "Qwen3 30B A3B Thinking" for row in payload["observations"])
    assert any(row["model"] == "Claude Opus 4.8" for row in payload["observations"])
