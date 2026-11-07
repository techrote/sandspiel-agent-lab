#!/usr/bin/env python3
"""Safe, bounded Sandspiel browser-session runner for GitHub Actions.

Reads a versioned JSON command file from the checked-out repository. It does
NOT run arbitrary JS, URLs, scripts, GitHub comments, or shell supplied by it.
Runs real native WASM simulation and writes verifiable screenshots/video/logs.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

from playwright.sync_api import sync_playwright

MAX_COMMANDS = 90
MAX_TICKS = 600
MAX_CAPTURES = 20
ALLOWED_FIELDS = {
    "reset": set(),
    "pause": set(),
    "status": set(),
    "catalog": set(),
    "inspect": {"x", "y", "width", "height", "includeCells"},
    "paint": {"x", "y", "diameter", "material"},
    "line": {"from", "to", "diameter", "material"},
    "stroke": {"points", "diameter", "material"},
    "rect": {"x", "y", "width", "height", "fill", "material", "diameter"},
    "step": {"ticks"},
}
COMMON_FIELDS = {"op", "expectedRevision", "capture", "label"}


def require(value, message):
    if not value:
        raise ValueError(message)


def parse_commands(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 80_000, "session file exceeds 80 KB")
    data = json.loads(raw)
    require(isinstance(data, dict) and data.get("format") == "sandspiel-lab-session/v1", "invalid session format")
    require(set(data) <= {"format", "name", "commands", "persistCells"}, "unknown session metadata")
    commands = data.get("commands")
    require(isinstance(commands, list) and 0 < len(commands) <= MAX_COMMANDS, "session needs 1–90 commands")
    require(isinstance(data.get("persistCells", False), bool), "persistCells must be boolean")
    ticks = 0
    captures = 2  # initial and final
    for i, command in enumerate(commands):
        require(isinstance(command, dict), f"command {i} must be an object")
        op = command.get("op")
        require(op in ALLOWED_FIELDS, f"command {i}: unsupported operation {op!r}")
        require(set(command) <= COMMON_FIELDS | ALLOWED_FIELDS[op], f"command {i}: unknown fields")
        require(isinstance(command.get("capture", False), bool), f"command {i}: capture must be boolean")
        if command.get("capture"): captures += 1
        if op == "step":
            require(isinstance(command.get("ticks"), int) and not isinstance(command.get("ticks"), bool), "steps must be integer")
            ticks += command["ticks"]
    require(ticks <= MAX_TICKS, "session simulation budget exceeded")
    require(captures <= MAX_CAPTURES, "session capture budget exceeded")
    return data


def wait_server(port, timeout=10):
    for _ in range(int(timeout * 10)):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("local HTTP server failed to start")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--commands", default="sessions/active.json")
    a.add_argument("--dist", default="dist")
    a.add_argument("--out", default="evidence/session")
    args = a.parse_args()
    data = parse_commands(args.commands)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    errors = []
    report = {"status": "unconfirmed", "name": str(data.get("name", "session"))[:120], "source_commit": os.environ.get("GITHUB_SHA"), "commands_expected": len(data["commands"]), "commands_applied": 0, "ticks": 0}
    server = subprocess.Popen(["python3", "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", str(args.dist)], stdout=(out / "server.log").open("wb"), stderr=subprocess.STDOUT)
    try:
        wait_server(8765)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            context = browser.new_context(viewport={"width": 820, "height": 720}, device_scale_factor=1, record_video_dir=str(out / "video"), record_video_size={"width": 820, "height": 720})
            page = context.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            try:
                page.goto("http://127.0.0.1:8765/agent.html", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_function("window.agentLab && window.agentLab.status().ready", timeout=60000)
                require(page.evaluate("Boolean(document.getElementById('sand-canvas').getContext('webgl'))"), "WebGL missing")
                page.screenshot(path=str(out / "000-start.png"))
                for i, record in enumerate(data["commands"]):
                    cmd = {k:v for k,v in record.items() if k not in {"capture", "label"}}
                    result = page.evaluate("c => window.agentLab.run(c)", cmd)
                    entries.append({"index":i,"label":str(record.get("label", ""))[:100],"command":cmd,"result":result})
                    if result.get("status") not in {"applied", "observed"}:
                        raise RuntimeError(f"operation {i} refused: {result.get('reason')}")
                    report["commands_applied"] += 1
                    if cmd["op"] == "step": report["ticks"] += result["stepsApplied"]
                    if record.get("capture"):
                        page.screenshot(path=str(out / f"{i+1:03d}-{cmd['op']}.png"))
                        page.wait_for_timeout(175)
                page.screenshot(path=str(out / "999-finish.png"))
                snapshot = page.evaluate("window.agentLab.run({op:'exportCells'})")
                require(snapshot["status"] == "observed", "exportCells refused")
                raw = base64.b64decode(snapshot["cellsBase64"])
                report["cells_sha256"] = hashlib.sha256(raw).hexdigest()
                report["cells_fidelity"] = snapshot["fidelity"]
                report["final_status"] = page.evaluate("window.agentLab.status()")
                if data.get("persistCells", False):
                    (out / "cells-only.json").write_text(json.dumps({k:snapshot[k] for k in ("format", "width", "height", "cellsBase64", "fidelity")}), encoding="utf-8")
                report["status"] = "passed"
            except Exception as error:
                report["status"] = "failed"
                report["error"] = repr(error)
                try: page.screenshot(path=str(out / "failure.png"))
                except Exception: pass
                raise
            finally:
                report["page_errors"] = errors
                (out / "session.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
                (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                context.close()
                try:
                    video_path=Path(page.video.path())
                    if video_path.exists() and shutil.which("ffmpeg"):
                        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "recording.mp4")], check=False)
                except Exception as e:
                    (out / "video-error.txt").write_text(repr(e), encoding="utf-8")
                browser.close()
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired: server.kill()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()