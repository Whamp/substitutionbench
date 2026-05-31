from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import websockets

URL = "http://100.112.72.93:8765/"
OUT = Path("reports/mobile-benchmark-field-deck.png")
PORT = 9223


async def send(ws, method: str, params: dict | None = None, seq: int = 1) -> dict:
    await ws.send(json.dumps({"id": seq, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == seq:
            return msg


def debug_url() -> str:
    deadline = time.time() + 10
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1) as resp:
                targets = json.loads(resp.read().decode())
                page = next(target for target in targets if target.get("type") == "page")
                return page["webSocketDebuggerUrl"]
        except Exception as exc:  # pragma: no cover - diagnostic path
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"Chrome debugging endpoint did not start: {last_error}")


async def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([
        "chromium",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--remote-debugging-port={PORT}",
        "--window-size=390,1200",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = debug_url()
        async with websockets.connect(ws_url, max_size=8_000_000) as ws:
            seq = 1
            for method, params in [
                ("Page.enable", {}),
                ("Runtime.enable", {}),
                ("Emulation.setDeviceMetricsOverride", {
                    "width": 390,
                    "height": 1200,
                    "deviceScaleFactor": 1,
                    "mobile": True,
                }),
                ("Page.navigate", {"url": URL}),
            ]:
                await send(ws, method, params, seq); seq += 1

            await asyncio.sleep(1.0)
            await send(ws, "Runtime.evaluate", {
                "expression": "document.querySelector('#benchmark-bars-title').scrollIntoView({block: 'start'}); window.scrollBy(0, -12);",
                "awaitPromise": False,
            }, seq); seq += 1
            await asyncio.sleep(0.4)
            shot = await send(ws, "Page.captureScreenshot", {"format": "png", "fromSurface": True}, seq)
            OUT.write_bytes(base64.b64decode(shot["result"]["data"]))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
