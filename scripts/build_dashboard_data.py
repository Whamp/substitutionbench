from __future__ import annotations

import argparse
import json
import os
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from substitutionbench.registry import (
    AA_ENDPOINT,
    LIVE_CODE_BENCH_ENDPOINT,
    checksum_payload,
    export_dashboard_payload,
    ingest_artificial_analysis_payload,
    ingest_livecodebench_payload,
    init_db,
    resolve_scores,
    write_dashboard_data,
)

ENV_PATH = ROOT / ".env"
CACHE_DIR = ROOT / "data" / "cache"
AA_CACHE_PATH = CACHE_DIR / "artificial_analysis_llms_models_raw.json"
AA_LEGACY_CACHE_PATH = ROOT / "data" / "artificial_analysis" / "llms_models_raw.json"
LCB_CACHE_PATH = CACHE_DIR / "livecodebench_performances_generation.json"
DB_PATH = ROOT / "data" / "registry" / "substitutionbench.sqlite"
DASHBOARD_DATA_PATH = ROOT / "docs" / "data.js"


def load_env_key() -> str | None:
    key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY", "").strip()
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("ARTIFICIAL_ANALYSIS_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def unwrap_cache_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if "payload" in payload and isinstance(payload["payload"], dict):
        return payload["payload"]
    return payload


def fetch_json(endpoint: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(endpoint, headers=headers or {"User-Agent": "SubstitutionBench data fetcher", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def load_or_fetch_artificial_analysis(refresh: bool) -> tuple[dict[str, Any], Path, bool]:
    if not refresh:
        for path in (AA_CACHE_PATH, AA_LEGACY_CACHE_PATH):
            if path.exists():
                return unwrap_cache_payload(path), path, True
    api_key = load_env_key()
    if not api_key:
        raise SystemExit("Missing ARTIFICIAL_ANALYSIS_API_KEY and no AA cache found. Keep .env local; do not commit it.")
    payload = fetch_json(
        AA_ENDPOINT,
        headers={
            "x-api-key": api_key,
            "User-Agent": "SubstitutionBench data fetcher",
            "Accept": "application/json",
        },
    )
    AA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    AA_CACHE_PATH.write_text(json.dumps({"fetched_at": now_utc(), "source": AA_ENDPOINT, "payload": payload}, indent=2, sort_keys=True))
    return payload, AA_CACHE_PATH, False


def load_or_fetch_livecodebench(refresh: bool) -> tuple[dict[str, Any], Path, bool]:
    if LCB_CACHE_PATH.exists() and not refresh:
        return unwrap_cache_payload(LCB_CACHE_PATH), LCB_CACHE_PATH, True
    payload = fetch_json(LIVE_CODE_BENCH_ENDPOINT)
    LCB_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LCB_CACHE_PATH.write_text(json.dumps({"fetched_at": now_utc(), "source": LIVE_CODE_BENCH_ENDPOINT, "payload": payload}, indent=2, sort_keys=True))
    return payload, LCB_CACHE_PATH, False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build(refresh: bool = False, db_path: Path = DB_PATH, output_path: Path = DASHBOARD_DATA_PATH) -> dict[str, Any]:
    aa_payload, aa_path, aa_from_cache = load_or_fetch_artificial_analysis(refresh)
    lcb_payload, lcb_path, lcb_from_cache = load_or_fetch_livecodebench(refresh)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    ingest_artificial_analysis_payload(
        conn,
        aa_payload,
        endpoint=AA_ENDPOINT,
        fetched_at=now_utc(),
        raw_path=str(aa_path.relative_to(ROOT)),
        checksum=checksum_payload(aa_payload),
        from_cache=aa_from_cache,
    )
    ingest_livecodebench_payload(
        conn,
        lcb_payload,
        endpoint=LIVE_CODE_BENCH_ENDPOINT,
        fetched_at=now_utc(),
        raw_path=str(lcb_path.relative_to(ROOT)),
        checksum=checksum_payload(lcb_payload),
        from_cache=lcb_from_cache,
    )
    resolve_scores(conn)
    payload = export_dashboard_payload(conn)
    write_dashboard_data(payload, output_path)
    summary = {
        "db_path": display_path(db_path),
        "dashboard_data_path": display_path(output_path),
        "aa_cache": display_path(aa_path),
        "aa_from_cache": aa_from_cache,
        "livecodebench_cache": display_path(lcb_path),
        "livecodebench_from_cache": lcb_from_cache,
        "sources": conn.execute("select count(*) from sources").fetchone()[0],
        "fetch_runs": conn.execute("select count(*) from fetch_runs").fetchone()[0],
        "models": conn.execute("select count(*) from models").fetchone()[0],
        "observations": conn.execute("select count(*) from benchmark_observations").fetchone()[0],
        "resolutions": conn.execute("select count(*) from benchmark_resolutions").fetchone()[0],
        "indexes": len(payload["indexes"]),
    }
    conn.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the SubstitutionBench SQLite registry and static dashboard data.")
    parser.add_argument("--refresh", action="store_true", help="Fetch fresh remote source data instead of using local cache when available.")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite database output path.")
    parser.add_argument("--output", type=Path, default=DASHBOARD_DATA_PATH, help="docs/data.js output path.")
    args = parser.parse_args()
    print(json.dumps(build(refresh=args.refresh, db_path=args.db, output_path=args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
