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


MAX_COMMANDS = 90
MAX_TICKS = 600
MAX_CAPTURES = 20
MAX_PRESENTATION_FRAMES = 1200
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
    "resume": {"ticks"},
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
    require(set(data) <= {"format", "name", "commands", "persistCells", "recording"}, "unknown session metadata")
    recording = data.get("recording", {"mode": "fast"})
    require(isinstance(recording, dict) and set(recording) <= {"mode", "fps", "stampsPerFrame"}, "invalid recording options")
    require(recording.get("mode", "fast") in {"fast", "paced"}, "unknown recording mode")
    fps = recording.get("fps", 12)
    stamps_per_frame = recording.get("stampsPerFrame", 12)
    require(type(fps) is int and 4 <= fps <= 20, "recording fps must be integer [4, 20]")
    require(type(stamps_per_frame) is int and 1 <= stamps_per_frame <= 80, "stampsPerFrame must be integer [1, 80]")
    presentation_frames = 0
    def position(value, index):
        require(isinstance(value, dict) and set(value) == {"x", "y"}, f"command {index}: malformed point")
        for coordinate in ("x", "y"):
            require(type(value[coordinate]) is int and 0 <= value[coordinate] < 300, f"command {index}: point out of bounds")
        return value
    def estimate(command, index):
        op = command["op"]
        if op == "paint":
            position({"x": command.get("x"), "y": command.get("y")}, index)
            return 1
        if op == "rect":
            x, y, w, h = (command.get(k) for k in ("x", "y", "width", "height"))
            require(all(type(v) is int for v in (x, y, w, h)) and 0 <= x < 300 and 0 <= y < 300
                    and 1 <= w <= 300-x and 1 <= h <= 300-y and w*h <= 6000, f"command {index}: invalid rectangle")
            return w*h  # conservative even for outline rectangles
        def segment(a, b):
            import math
            diameter = command.get("diameter", 1)
            require(type(diameter) is int and 1 <= diameter <= 45, f"command {index}: invalid diameter")
            return math.ceil(math.hypot(a["x"]-b["x"], a["y"]-b["y"]) / max(1, diameter/3)) + 1
        if op == "line":
            return segment(position(command.get("from"), index), position(command.get("to"), index))
        if op == "stroke":
            points = command.get("points")
            require(isinstance(points, list) and 2 <= len(points) <= 100, f"command {index}: invalid stroke points")
            points = [position(p, index) for p in points]
            return sum(segment(a, b) for a, b in zip(points, points[1:]))
        return 0
    commands = data.get("commands")
    require(isinstance(commands, list) and 0 < len(commands) <= MAX_COMMANDS, "session needs 1–90 commands")
    require(isinstance(data.get("persistCells", False), bool), "persistCells must be boolean")
    ticks = 0
    captures = 2  # initial and final
    for i, command in enumerate(commands):
        require(isinstance(command, dict), f"command {i} must be an object")
        op = command.get("op")
        require(isinstance(op, str) and op in ALLOWED_FIELDS, f"command {i}: unsupported operation {op!r}")
        require(set(command) <= COMMON_FIELDS | ALLOWED_FIELDS[op], f"command {i}: unknown fields")
        require(isinstance(command.get("capture", False), bool), f"command {i}: capture must be boolean")
        if "label" in command:
            require(isinstance(command["label"], str) and len(command["label"]) <= 100, f"command {i}: label must be a string of at most 100 characters")
        if "expectedRevision" in command:
            rev = command["expectedRevision"]
            require(type(rev) is int and 0 <= rev <= 2**53 - 1, f"command {i}: expectedRevision must be a nonnegative safe integer")
        if op == "rect" and "fill" in command:
            require(isinstance(command["fill"], bool), f"command {i}: fill must be boolean")
        if op == "inspect" and "includeCells" in command:
            require(isinstance(command["includeCells"], bool), f"command {i}: includeCells must be boolean")
        if command.get("capture") or op in {"reset", "pause", "resume"}: captures += 1
        if recording.get("mode", "fast") == "paced" and op in {"paint", "line", "stroke", "rect"}:
            stamps = estimate(command, i)
            require(stamps <= (6000 if op == "rect" else 3000), f"command {i}: stamp limit exceeded")
            presentation_frames += (stamps + stamps_per_frame - 1) // stamps_per_frame + 1
            require(presentation_frames <= MAX_PRESENTATION_FRAMES, "presentation frame budget exceeded")
        if op in {"step", "resume"}:
            count = command.get("ticks")
            require(type(count) is int and 1 <= count <= 240, f"command {i}: ticks must be an integer in [1, 240]")
            ticks += count
            require(ticks <= MAX_TICKS, "session simulation budget exceeded")
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



def source_identity(dist):
    """Git checkout/tree and compiled executable bundle hashes (cache-independent)."""
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    files = sorted(p for p in Path(dist).rglob("*") if p.is_file() and p.suffix in {".wasm", ".js", ".html"})
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.relative_to(dist).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(file.read_bytes()).digest())
    return {
        "checkout_commit": git("rev-parse", "HEAD"),
        "checkout_tree": git("rev-parse", "HEAD^{tree}"),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_ref": os.environ.get("GITHUB_REF"),
        "bundle_sha256": digest.hexdigest(),
        "bundle_files_hashed": len(files),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commands", default="sessions/active.json")
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--out", default="evidence/session")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    errors = []
    report = {"status": "unconfirmed", "name": "unvalidated session",
              "source_commit": os.environ.get("GITHUB_SHA"), "commands_expected": 0,
              "commands_applied": 0, "ticks": 0, "live_ticks": 0, "step_ticks": 0}
    try:
        data = parse_commands(args.commands)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report.update({"status": "refused", "stage": "preflight", "error": str(error), "page_errors": []})
        (out / "session.json").write_text("[]\n", encoding="utf-8")
        (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        raise SystemExit(2)

    report["name"] = str(data.get("name", "session"))[:120]
    report["commands_expected"] = len(data["commands"])
    recording = data.get("recording", {"mode": "fast"})
    mode = recording.get("mode", "fast")
    recording_fps = recording.get("fps", 12)
    presentation = {"fps": recording_fps, "stampsPerFrame": recording.get("stampsPerFrame", 12)}
    report["recording_mode"] = mode
    report["source_identity"] = source_identity(args.dist)
    (out / "build-identity.json").write_text(json.dumps(report["source_identity"], indent=2), encoding="utf-8")
    from playwright.sync_api import sync_playwright
    from recording_integrity import inspect_recording

    server = None
    failure = None
    try:
        with (out / "server.log").open("wb") as log:
            server = subprocess.Popen(["python3", "-m", "http.server", "8765",
                                       "--bind", "127.0.0.1", "--directory", str(args.dist)],
                                      stdout=log, stderr=subprocess.STDOUT)
            wait_server(8765)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True, args=["--enable-webgl", "--use-gl=angle",
                                         "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
                context = browser.new_context(viewport={"width": 820, "height": 720},
                                              device_scale_factor=1, accept_downloads=True,
                                              record_video_dir=str(out / "viewport-video"),
                                              record_video_size={"width": 820, "height": 720})
                page = context.new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                started = False
                try:
                    page.goto("http://127.0.0.1:8765/agent.html",
                              wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_function("window.agentLab && window.agentLab.status().ready && window.agentCapture",
                                           timeout=60000)
                    require(page.evaluate("Boolean(document.getElementById('sand-canvas').getContext('webgl'))"),
                            "WebGL missing")
                    require(page.evaluate("window.agentLab.status().paused"), "simulation must start paused")
                    page.screenshot(path=str(out / "000-start.png"))
                    report["canvas_capture"] = page.evaluate(
                        "opts => window.agentCapture.start(opts)", {"fps": recording_fps})
                    started = True
                    # Preserve initial blank scene in genuine browser-recorded frames.
                    page.wait_for_timeout(300)
                    initial = page.evaluate("window.agentLab.status()")
                    prior_ticks = initial["ticksObserved"]
                    for i, record in enumerate(data["commands"]):
                        cmd = {k: v for k, v in record.items() if k not in {"capture", "label"}}
                        before = page.evaluate("""() => ({
                            elapsedMs: window.agentCapture.elapsedMs(),
                            ...window.agentLab.status()
                        })""")
                        if mode == "paced" and cmd["op"] in {"paint", "line", "stroke", "rect"}:
                            result = page.evaluate(
                                "args => window.agentLab.runPaced(args.command, args.options)",
                                {"command": cmd, "options": presentation})
                        else:
                            result = page.evaluate("command => window.agentLab.run(command)", cmd)
                        if result.get("status") not in {"applied", "observed"}:
                            raise RuntimeError(f"operation {i} {cmd['op']} refused: {result.get('reason')}")
                        if cmd["op"] == "resume":
                            require(result["paused"] is False, "resume was not acknowledged")
                            expected = before["ticksObserved"] + cmd["ticks"]
                            page.wait_for_function(
                                "target => window.agentLab.status().paused && window.agentLab.status().ticksObserved >= target",
                                arg=expected, timeout=30000, polling=50)
                            after_resume = page.evaluate("window.agentLab.status()")
                            require(after_resume["ticksObserved"] == expected,
                                    f"native live-tick budget exceeded: expected {expected}, got {after_resume['ticksObserved']}")
                        after = page.evaluate("""() => ({
                            elapsedMs: window.agentCapture.elapsedMs(),
                            ...window.agentLab.status()
                        })""")
                        executed = after["ticksObserved"] - before["ticksObserved"]
                        require(executed >= 0, "native tick counter went backwards")
                        if cmd["op"] == "resume":
                            require(executed == cmd["ticks"], "resume tick count mismatch")
                            report["live_ticks"] += executed
                        if cmd["op"] == "step":
                            require(executed == result["stepsApplied"], "stepping acknowledgment mismatch")
                            report["step_ticks"] += executed
                        report["ticks"] = after["ticksObserved"] - initial["ticksObserved"]
                        require(report["ticks"] <= MAX_TICKS, "runtime simulation budget exceeded")
                        entries.append({
                            "index": i, "label": str(record.get("label", ""))[:100],
                            "command": cmd, "result": result,
                            "recordingMsStart": round(before["elapsedMs"], 3),
                            "recordingMsEnd": round(after["elapsedMs"], 3),
                            "ticksBefore": before["ticksObserved"],
                            "ticksAfter": after["ticksObserved"],
                            "pausedAfter": after["paused"],
                        })
                        report["commands_applied"] += 1
                        if record.get("capture") or cmd["op"] in {"reset", "pause", "resume"}:
                            page.screenshot(path=str(out / f"{i+1:03d}-{cmd['op']}.png"))
                    require(page.evaluate("window.agentLab.status().paused"),
                            "session finished running; an explicit pause is required")
                    page.screenshot(path=str(out / "999-finish.png"))
                    snapshot = page.evaluate("window.agentLab.run({op:'exportCells'})")
                    require(snapshot["status"] == "observed", "exportCells refused")
                    raw = base64.b64decode(snapshot["cellsBase64"])
                    report["cells_sha256"] = hashlib.sha256(raw).hexdigest()
                    report["cells_fidelity"] = snapshot["fidelity"]
                    report["final_status"] = page.evaluate("window.agentLab.status()")
                    if data.get("persistCells", False):
                        (out / "cells-only.json").write_text(
                            json.dumps({k: snapshot[k] for k in
                                        ("format", "width", "height", "cellsBase64", "fidelity")}),
                            encoding="utf-8")
                    # Final evolving state must remain visible for multiple video frames.
                    page.wait_for_timeout(400)
                except Exception as error:
                    failure = error
                    report["status"] = "failed"
                    report["stage"] = "browser"
                    report["error"] = repr(error)
                    try:
                        report["final_status"] = page.evaluate("window.agentLab.status()")
                        page.screenshot(path=str(out / "failure.png"))
                    except Exception:
                        pass
                finally:
                    if started:
                        try:
                            with page.expect_download(timeout=30000) as download_info:
                                report["canvas_capture_stop"] = page.evaluate(
                                    "async () => await window.agentCapture.stop()")
                            download_info.value.save_as(str(out / "recording.webm"))
                        except Exception as error:
                            report["recording_error"] = repr(error)
                            if failure is None: failure = error
                    context.close()
                    try:
                        source = Path(page.video.path())
                        if source.exists():
                            shutil.copyfile(source, out / "viewport-recording.webm")
                    except Exception as error:
                        report["viewport_video_error"] = repr(error)
                    browser.close()
    except Exception as error:
        if failure is None: failure = error
        report.update({"status": "failed", "stage": report.get("stage", "setup"), "error": repr(error)})
    finally:
        if server:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill()
        report["page_errors"] = errors

    if not failure and errors:
        failure = RuntimeError("browser page errors: " + "; ".join(errors[:3]))
    if (out / "recording.webm").exists():
        try:
            metadata, integrity = inspect_recording(out / "recording.webm", entries, mode)
            report["video_metadata"] = metadata
            report["recording_integrity"] = integrity
            (out / "video-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            (out / "recording-integrity.json").write_text(json.dumps(integrity, indent=2), encoding="utf-8")
            if not failure and shutil.which("ffmpeg"):
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                                str(out / "recording.webm"), "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", str(out / "recording.mp4")],
                               timeout=60, check=False)
        except Exception as error:
            report["integrity_error"] = repr(error)
            if failure is None: failure = error
    elif failure is None:
        failure = RuntimeError("continuous canvas WebM missing")
    if failure is not None:
        report["status"] = "failed"
        report["error"] = repr(failure)
    else:
        report["status"] = "passed"
    (out / "session.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failure is not None: raise SystemExit(1)


if __name__ == "__main__":
    main()
