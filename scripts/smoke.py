#!/usr/bin/env python3
"""One genuine Chromium/Playwright Sandspiel Agent Lab smoke session.

Produces before/after frames, native command results, a cells-only checkpoint,
and a browser recording; fails on unobserved or refused operations.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


def demand(result, expected="applied"):
    if result.get("status") != expected:
        raise AssertionError(f"Expected {expected}: {result}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765/agent.html")
    parser.add_argument("--out", default="evidence/smoke")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    history = []
    console_errors = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        context = browser.new_context(viewport={"width": 820, "height": 720}, device_scale_factor=1, record_video_dir=str(out / "video"), record_video_size={"width": 820, "height": 720})
        page = context.new_page()
        page.on("pageerror", lambda error: console_errors.append(str(error)))
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function("window.agentLab && window.agentLab.status().ready", timeout=60000)
            page.wait_for_timeout(500)

            def invoke(command, expect="applied"):
                result = page.evaluate("command => window.agentLab.run(command)", command)
                history.append({"command": command if command.get("op") != "importCells" else {"op": "importCells", "format": command.get("format")}, "result": {k: v for k, v in result.items() if k != "cellsBase64"}})
                return demand(result, expect)

            catalog = invoke({"op": "catalog"}, "observed")
            assert {"Wood", "Water", "Wall"}.issubset({m["name"] for m in catalog["materials"]})
            assert page.evaluate("Boolean(document.getElementById('sand-canvas').getContext('webgl'))"), "WebGL context missing"
            page.screenshot(path=str(out / "00-blank.png"))

            first = invoke({"op": "line", "material": "Wood", "from": {"x": 28, "y": 230}, "to": {"x": 28, "y": 270}, "diameter": 3})
            assert first["changedCells"] >= 20, first
            original = invoke({"op": "inspect", "x": 24, "y": 226, "width": 10, "height": 50}, "observed")
            assert original["region"]["counts"].get("Wood", 0) >= 20
            page.screenshot(path=str(out / "01-wood.png"))
            invoke({"op": "rect", "material": "Wall", "x": 102, "y": 205, "width": 80, "height": 75, "fill": False})
            invoke({"op": "paint", "material": "Water", "x": 140, "y": 180, "diameter": 28})
            water_before = invoke({"op": "inspect", "x": 102, "y": 160, "width": 80, "height": 120}, "observed")
            assert water_before["region"]["counts"].get("Water", 0) > 0
            page.screenshot(path=str(out / "02-water-before.png"))

            # Advance native physics AND WebGL fluid, while remaining paused between commands.
            invoke({"op": "step", "ticks": 120})
            page.wait_for_timeout(300)
            water_after = invoke({"op": "inspect", "x": 102, "y": 160, "width": 80, "height": 120}, "observed")
            assert water_after["region"]["counts"].get("Wall", 0) > 0
            page.screenshot(path=str(out / "03-after-120.png"))

            before_export_wood = invoke({"op": "inspect", "x": 24, "y": 226, "width": 10, "height": 50}, "observed")
            exported = invoke({"op": "exportCells"}, "observed")
            checkpoint = {"format": exported["format"], "width": exported["width"], "height": exported["height"], "cellsBase64": exported["cellsBase64"], "fidelity": exported["fidelity"]}
            (out / "checkpoint-cells-only.json").write_text(json.dumps(checkpoint), encoding="utf-8")
            invoke({"op": "reset"})
            empty = invoke({"op": "inspect", "x": 24, "y": 226, "width": 10, "height": 50}, "observed")
            assert not empty["region"]["counts"].get("Wood", 0)
            invoke({"op": "importCells", **checkpoint})
            restored = invoke({"op": "inspect", "x": 24, "y": 226, "width": 10, "height": 50}, "observed")
            assert restored["region"]["counts"] == before_export_wood["region"]["counts"], "Restored census differs from pre-export state"
            reexported = invoke({"op": "exportCells"}, "observed")
            assert reexported["cellsBase64"] == exported["cellsBase64"], "Cell byte roundtrip mismatch"
            page.screenshot(path=str(out / "04-restored.png"))

            stale = invoke({"op": "paint", "material": "Wood", "x": 10, "y": 10, "expectedRevision": 0}, "refused")
            assert "stale" in stale["reason"]
            bad = invoke({"op": "paint", "material": "NotAMaterial", "x": 10, "y": 10}, "refused")
            assert "unknown material" in bad["reason"]
            report = {"ok": True, "source_sha": os.environ.get("GITHUB_SHA"), "steps": 120, "initial_wood": original["region"]["counts"]["Wood"], "pre_export_wood": before_export_wood["region"]["counts"].get("Wood", 0), "restored_wood": restored["region"]["counts"].get("Wood", 0), "water_before": water_before["region"]["counts"].get("Water", 0), "water_after": water_after["region"]["counts"].get("Water", 0), "final_status": page.evaluate("window.agentLab.status()"), "page_errors": console_errors}
            (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        except Exception as error:
            (out / "failure.txt").write_text(repr(error), encoding="utf-8")
            try:
                page.screenshot(path=str(out / "failure.png"))
            except Exception:
                pass
            raise
        finally:
            (out / "session.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
            context.close()
            try:
                video_path = Path(page.video.path())
                if video_path.exists() and shutil.which("ffmpeg"):
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out / "session.mp4")], check=False)
            except Exception as video_error:
                (out / "video-error.txt").write_text(repr(video_error), encoding="utf-8")
            browser.close()

    # Verify screenshot pixels changed rather than assuming screenshots reflect gameplay.
    with Image.open(out / "00-blank.png") as before, Image.open(out / "03-after-120.png") as after:
        assert ImageChops.difference(before.convert("RGB"), after.convert("RGB")).getbbox() is not None, "Viewport did not change"
    print(json.dumps({"result": "passed", "report": str(out / "report.json"), "video": str(out / "video")}, indent=2))


if __name__ == "__main__":
    main()