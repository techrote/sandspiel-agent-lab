/* Real-time, actual Sandspiel WebGL canvas recording; no screenshot animation. */
export function createAgentCapture(canvas) {
  let recorder = null;
  let stream = null;
  let startedAt = null;
  let chunks = [];
  let chosenMime = "";

  const elapsedMs = () => startedAt === null ? null : Math.max(0, performance.now() - startedAt);
  const active = () => recorder !== null && recorder.state === "recording";
  async function start({fps = 12} = {}) {
    if (active()) throw new Error("recording already active");
    if (!Number.isSafeInteger(fps) || fps < 4 || fps > 20) throw new Error("recording FPS out of range");
    if (!canvas || typeof canvas.captureStream !== "function" || typeof MediaRecorder === "undefined") {
      throw new Error("canvas MediaRecorder unavailable");
    }
    const preferred = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"];
    chosenMime = preferred.find(type => MediaRecorder.isTypeSupported(type));
    if (!chosenMime) throw new Error("WebM recording codec unavailable");
    stream = canvas.captureStream(fps);
    const tracks = stream.getVideoTracks();
    if (tracks.length !== 1) throw new Error("captureStream yielded no video track");
    chunks = [];
    recorder = new MediaRecorder(stream, {mimeType: chosenMime, videoBitsPerSecond: 2000000});
    recorder.addEventListener("dataavailable", e => { if (e.data.size > 0) chunks.push(e.data); });
    await new Promise((resolve, reject) => {
      recorder.addEventListener("start", resolve, {once: true});
      recorder.addEventListener("error", event => reject(new Error(String(event.error || "MediaRecorder error"))), {once: true});
      recorder.start(200);
    });
    startedAt = performance.now();
    return {source: "sand-canvas.captureStream", mimeType: chosenMime, requestedFps: fps, trackSettings: tracks[0].getSettings()};
  }
  async function stop() {
    if (!active()) throw new Error("recording is not active");
    const durationMs = elapsedMs();
    await new Promise((resolve, reject) => {
      recorder.addEventListener("stop", resolve, {once: true});
      recorder.addEventListener("error", event => reject(new Error(String(event.error || "MediaRecorder error"))), {once: true});
      recorder.stop();
    });
    for (const track of stream.getTracks()) track.stop();
    const blob = new Blob(chunks, {type: chosenMime});
    if (!blob.size) throw new Error("browser recorded zero bytes");
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "canvas-recording.webm";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    // Keep the object URL available until Playwright's download finishes.
    return {source: "sand-canvas.captureStream", mimeType: chosenMime, durationMs, byteLength: blob.size};
  }
  return Object.freeze({start, stop, elapsedMs, active});
}
