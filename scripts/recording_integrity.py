"""Inspect *decoded original browser video* and correlate frame changes with paced edits.

No frames are synthesized or interpolated. A nominal/container FPS alone is not
sufficient to pass an authoring recording.
"""
import hashlib
import json
from pathlib import Path
import subprocess

PIXELS = 160 * 160

def call_json(arguments):
    result = subprocess.run(arguments, check=True, text=True, capture_output=True, timeout=60)
    return json.loads(result.stdout)

def inspect_recording(path, ledger, mode="paced"):
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("empty WebM recording")
    probe = call_json(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                       "-show_streams", "-show_format", "-of", "json", str(path)])
    streams = probe.get("streams", [])
    if len(streams) != 1:
        raise ValueError("expected one actual canvas video stream")
    stream = streams[0]
    duration = float(probe["format"]["duration"])
    frames = int(stream["nb_read_frames"])
    fps = frames / duration if duration > 0 else 0.0
    metadata = {
        "source": "actual Sandspiel sand-canvas via MediaRecorder.captureStream",
        "codec": stream.get("codec_name"),
        "width": stream.get("width"), "height": stream.get("height"),
        "duration_seconds": duration, "decoded_frame_count": frames,
        "observed_fps": round(fps, 3),
        "nominal_rate": stream.get("r_frame_rate"),
        "container_rate": stream.get("avg_frame_rate"),
        "file_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    if fps < 4:
        raise ValueError(f"actual decoded frame rate below 4 FPS: {fps:.2f}")
    timestamps = call_json(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_frames", "-show_entries", "frame=best_effort_timestamp_time",
                            "-of", "json", str(path)])
    times = [float(frame["best_effort_timestamp_time"]) for frame in timestamps["frames"]
             if "best_effort_timestamp_time" in frame]
    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0",
         "-vf", "scale=160:160,format=gray", "-vsync", "0",
         "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"],
        check=True, capture_output=True, timeout=90).stdout
    if len(decoded) % PIXELS:
        raise ValueError("decoded video frame data is corrupt")
    images = [memoryview(decoded)[i:i + PIXELS] for i in range(0, len(decoded), PIXELS)]
    if not images or abs(len(images) - frames) > 2 or abs(len(times) - len(images)) > 2:
        raise ValueError("frame metadata and decoded source frames disagree")
    count = min(len(images), len(times))
    images, times = images[:count], times[:count]
    fingerprints = [hashlib.sha256(image).digest() for image in images]
    # A few non-identical gray pixels from GPU noise do not qualify as drawing.
    def pixels_changed(first, second):
        return sum(abs(a - b) >= 24 for a, b in zip(first, second))
    significant = [False] + [pixels_changed(images[i - 1], images[i]) >= 15
                              for i in range(1, count)]
    events = []
    intermediate = []
    for record in ledger:
        if not record.get("result", {}).get("paced") or record["result"].get("changedCells", 0) <= 0:
            continue
        start, end = record["recordingMsStart"] / 1000, record["recordingMsEnd"] / 1000
        within = [i for i, t in enumerate(times) if start <= t <= end]
        hashes = {fingerprints[i] for i in within}
        changes = sum(significant[i] for i in within if i > 0 and times[i-1] >= start)
        event = {
            "index": record["index"], "label": record["label"], "op": record["command"]["op"],
            "stamps": record["result"]["stamps"],
            "changedCells": record["result"]["changedCells"],
            "recordedFramesDuringCommand": len(within),
            "distinctFramesDuringCommand": len(hashes),
            "significantFrameTransitions": changes,
            "durationMs": round(end * 1000 - start * 1000, 1),
        }
        event["intermediatePaintingVisible"] = (
            record["result"]["presentationFrames"] >= 3
            and len(within) >= 3 and len(hashes) >= 3 and changes >= 2
        )
        if event["intermediatePaintingVisible"]:
            intermediate.append(record["index"])
        events.append(event)
    integrity = {
        "distinct_full_video_frames": len(set(fingerprints)),
        "significant_full_video_transitions": sum(significant),
        "paced_material_edit_events": events,
        "intermediate_painting_command_indexes": intermediate,
        "allows_unchanged_frames": True,
        "analysis": "Decoded real WebM frames; per-command camera time windows; no reconstructed screenshots",
    }
    if len(set(fingerprints)) < 4 or sum(significant) < 3:
        raise ValueError("recording has insufficient real visual scene changes")
    if mode == "paced" and not intermediate:
        raise ValueError("no actual intermediate painting states found inside paced editing command windows")
    return metadata, integrity
