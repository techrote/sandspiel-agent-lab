#!/usr/bin/env python3
"""Replay bounded Sandspiel JSON operations in an actual Chromium session.

Inputs are data, never executable JavaScript, shell commands or URLs.
This is an ephemeral browser session; saved cells are not a full native checkpoint.
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ALLOWED = {"status", "catalog", "inspect", "pause", "resume", "reset",
           "paint", "line", "stroke", "rect", "step", "exportCells"}
MAX_COMMANDS = 70
MAX_TOTAL_TICKS = 2000

def validate(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("commands"), list):
        raise ValueError("scenario must contain a JSON commands array")
    cmds = data["commands"]
    if len(cmds) < 1 or len(cmds) > MAX_COMMANDS:
        raise ValueError("command count out of range")
    steps = 0
    for c in cmds:
        if not isinstance(c, dict) or c.get("op") not in ALLOWED | {"capture"}:
            raise ValueError("unsupported or malformed command")
        if c["op"] == "step":
            n = c.get("ticks")
            if type(n) is not int or not (1 <= n <= 240):
                raise ValueError("invalid step count")
            steps += n
        if c["op"] == "capture":
            if not isinstance(c.get("label"), str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", c["label"]):
                raise ValueError("invalid capture label")
    if steps > MAX_TOTAL_TICKS:
        raise ValueError("scenario step budget exceeded")
    return cmds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", default="evidence/remote-session")
    ap.add_argument("--url", default="http://127.0.0.1:8765/agent.html")
    args = ap.parse_args()
    source = Path(args.scenario).resolve()
    # Never read a command file outside the approved repository scenario directory.
    permitted = (Path.cwd() / "sessions").resolve()
    if permitted not in source.parents or source.suffix != ".json":
        raise ValueError("scenario must be a JSON file under sessions/")
    commands = validate(source)
    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    report = {"scenario": source.name, "receipts": [], "page_errors": [], "status": "started"}
    (dest / "scenario.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=[
            "--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader"])
        ctx = browser.new_context(viewport={"width": 900, "height": 750},
                                  device_scale_factor=1,
                                  record_video_dir=str(dest / "video"))
        page = ctx.new_page()
        page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function("window.agentLab && window.agentLab.status().ready", timeout=60000)
            report["native_status_initial"] = page.evaluate("window.agentLab.status()")
            assert page.evaluate("Boolean(document.getElementById('sand-canvas').getContext('webgl'))")
            page.screenshot(path=str(dest / "00-start.png"))
            for seq, cmd in enumerate(commands, start=1):
                if cmd["op"] == "capture":
                    page.screenshot(path=str(dest / f"{seq:02d}-{cmd['label']}.png"))
                    report["receipts"].append({"index": seq, "operation": "capture", "label": cmd["label"], "status": "captured"})
                    page.wait_for_timeout(200)
                    continue
                receipt = page.evaluate("command => window.agentLab.run(command)", cmd)
                sanitized = {k: v for k, v in receipt.items() if k != "cellsBase64"}
                if cmd["op"] == "exportCells":
                    checkpoint = {k: receipt[k] for k in ("format", "width", "height", "cellsBase64", "fidelity")}
                    (dest / f"checkpoint-{seq:02d}.json").write_text(json.dumps(checkpoint), encoding="utf-8")
                report["receipts"].append({"index": seq, "command": cmd, "result": sanitized})
                if receipt.get("status") == "refused":
                    raise AssertionError(f"Refused at command {seq}: {receipt.get('reason')}")
            report["native_status_final"] = page.evaluate("window.agentLab.status()")
            page.screenshot(path=str(dest / "99-final.png"))
            page.wait_for_timeout(400)
            report["status"] = "passed"
        except Exception as exc:
            report["status"] = "failed"
            report["error"] = repr(exc)
            try:
                page.screenshot(path=str(dest / "failure.png"))
            except Exception:
                pass
            raise
        finally:
            (dest / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            ctx.close()
            try:
                recording = Path(page.video.path())
                if recording.exists() and recording.stat().st_size and shutil.which("ffmpeg"):
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                                    str(recording), "-c:v", "libx264", "-pix_fmt",
                                    "yuv420p", str(dest / "session.mp4")],
                                   check=False, timeout=120)
            except Exception as error:
                (dest / "video-error.txt").write_text(repr(error), encoding="utf-8")
            browser.close()

if __name__ == "__main__":
    main()
