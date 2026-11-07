/* Sandspiel Agent Lab v1: a bounded adapter around the existing Universe.
 * No changes to the upstream Rust material physics.  Browser-only; never eval input.
 */
const MAX_BRUSH = 45;
const MAX_STAMPS = 3000;
const MAX_RECT_CELLS = 6000;
const MAX_INSPECT_CELLS = 10000;
const MAX_STEP = 240;
const MAX_CELL_PAYLOAD = 1024;

function integer(value, name, min, max) {
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    throw new Error(`${name} must be an integer in [${min}, ${max}]`);
  }
  return value;
}
function plain(value, name) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${name} must be a JSON object`);
  }
  return value;
}
function booleanOption(value, name, fallback = false) {
  if (value === undefined) return fallback;
  if (typeof value !== "boolean") throw new Error(`${name} must be a boolean`);
  return value;
}
function point(value, width, height) {
  plain(value, "point");
  return {
    x: integer(value.x, "x", 0, width - 1),
    y: integer(value.y, "y", 0, height - 1),
  };
}
function encode(bytes) {
  const blocks = [];
  for (let i = 0; i < bytes.length; i += 8192) {
    blocks.push(String.fromCharCode(...bytes.subarray(i, i + 8192)));
  }
  return btoa(blocks.join(""));
}
function decode(data) {
  if (typeof data !== "string" || !/^[A-Za-z0-9+/]*={0,2}$/.test(data)) {
    throw new Error("cells must be base64");
  }
  const raw = atob(data);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes;
}

/**
 * @param {Object} dependencies Existing Sandspiel instance and WASM exports.
 */
export function createAgentLab({ universe, memory, species, fluid, render, mode = "interactive" }) {
  const width = universe.width();
  const height = universe.height();
  if (!Number.isInteger(width) || !Number.isInteger(height) || !memory?.buffer) {
    throw new Error("Sandspiel WASM universe or memory not ready");
  }
  const names = Object.entries(species)
    .filter(([name, id]) => !/^\d+$/.test(name) && Number.isInteger(id) && id >= 0 && id < 256)
    .sort((a, b) => a[1] - b[1]);
  const labels = new Map(names.map(([name, id]) => [id, name]));
  const byName = new Map(names);
  let revision = 0;
  let ticks = 0;
  let commands = 0;
  let liveTicksRemaining = 0;
  let pacing = false;

  const status = () => ({
    ready: true,
    api: "sandspiel-agent-lab/v1",
    mode,
    paused: Boolean(window.paused),
    revision,
    ticksObserved: ticks,
    liveTicksRemaining,
    commands,
    width,
    height,
  });
  const cells = () => new Uint8Array(memory.buffer, universe.cells(), width * height * 4);
  const changedCount = (previous) => {
    const next = cells();
    let changed = 0;
    for (let i = 0; i < previous.length; i += 4) {
      if (next[i] !== previous[i] || next[i + 1] !== previous[i + 1] || next[i + 2] !== previous[i + 2] || next[i + 3] !== previous[i + 3]) changed++;
    }
    return changed;
  };
  const material = (value) => {
    const id = typeof value === "string" ? byName.get(value) : value;
    if (!Number.isInteger(id) || !labels.has(id)) throw new Error(`unknown material: ${String(value)}`);
    return id;
  };
  const setPause = (paused) => {
    if (paused) liveTicksRemaining = 0;
    window.paused = paused;
    if (window.UI) {
      const method = paused ? "pause" : "play";
      if (typeof window.UI[method] === "function") window.UI[method]();
    }
  };
  const stopBoot = () => { window.stopboot = true; };
  const stamp = (x, y, size, id) => universe.paint(x, y, size, id);
  const paintLine = (a, b, diameter, id, tracker) => {
    const steps = Math.ceil(Math.hypot(b.x - a.x, b.y - a.y) / Math.max(1, diameter / 3));
    if (tracker.stamps + steps + 1 > MAX_STAMPS) throw new Error("stroke stamp limit exceeded");
    for (let j = 0; j <= steps; j++) {
      const t = steps ? j / steps : 0;
      stamp(Math.round(a.x + (b.x - a.x) * t), Math.round(a.y + (b.y - a.y) * t), diameter, id);
      tracker.stamps++;
    }
  };
  const checkRevision = (command) => {
    if (command.expectedRevision !== undefined && integer(command.expectedRevision, "expectedRevision", 0, Number.MAX_SAFE_INTEGER) !== revision) {
      throw new Error(`stale scene revision: expected ${command.expectedRevision}, current ${revision}`);
    }
  };
  const inspect = (command) => {
    const x = integer(command.x, "x", 0, width - 1);
    const y = integer(command.y, "y", 0, height - 1);
    const w = integer(command.width, "width", 1, width - x);
    const h = integer(command.height, "height", 1, height - y);
    if (w * h > MAX_INSPECT_CELLS) throw new Error("inspection area too large");
    const includeCells = booleanOption(command.includeCells, "includeCells");
    if (includeCells && w * h > MAX_CELL_PAYLOAD) throw new Error("cell payload area too large");
    const data = cells();
    const counts = {};
    const detailed = [];
    for (let yy = y; yy < y + h; yy++) {
      for (let xx = x; xx < x + w; xx++) {
        // Sandspiel stores cells by X-major order, four bytes each.
        const i = (xx * height + yy) * 4;
        const id = data[i];
        const name = labels.get(id) || `unknown:${id}`;
        counts[name] = (counts[name] || 0) + 1;
        if (includeCells) detailed.push({ x: xx, y: yy, material: name, id, ra: data[i+1], rb: data[i+2], clock: data[i+3] });
      }
    }
    return { x, y, width: w, height: h, counts, ...(includeCells ? { cells: detailed } : {}) };
  };

  const run = (input) => {
    const beforeRevision = revision;
    let operationStarted = false;
    let sceneMutationStarted = false;
    let editSnapshot = null;
    let nativeTicksCompleted = 0;
    commands++;
    try {
      const command = plain(input, "command");
      if (typeof command.op !== "string") throw new Error("op must be a string");
      if (pacing && command.op !== 'status') throw new Error('paced edit already executing');
      checkRevision(command);
      let output = {};
      let mutated = false;
      switch (command.op) {
        case "status": return { status: "observed", ...status() };
        case "catalog": return { status: "observed", materials: names.map(([name, id]) => ({ name, id })), ...status() };
        case "inspect": return { status: "observed", region: inspect(command), ...status() };
        case "pause": operationStarted = true; setPause(true); output = { paused: true }; break;
        case "resume": {
          // Interactive no-tick resume remains available; session JSON requires ticks.
          const allowance = command.ticks === undefined ? 0 : integer(command.ticks, "ticks", 1, MAX_STEP);
          operationStarted = true;
          liveTicksRemaining = allowance;
          setPause(false);
          output = { paused: false, liveTicksBudget: allowance };
          break;
        }
        case "reset": {
          operationStarted = true;
          sceneMutationStarted = true;
          stopBoot(); setPause(true);
          fluid.reset(); fluid.update(); fluid.reset(); fluid.update();
          universe.reset();
          universe.flush_undos();
          mutated = true;
          output = { reset: true, note: "Native RNG and fluid state are not rewound to an original seed" };
          break;
        }
        case "step": {
          if (!window.paused) throw new Error("pause before stepping; concurrent render-loop ticks would invalidate the result");
          const count = integer(command.ticks, "ticks", 1, MAX_STEP);
          operationStarted = true;
          sceneMutationStarted = true;
          for (let i = 0; i < count; i++) {
            universe.tick(); ticks++; revision++; nativeTicksCompleted++;
            fluid.update();
          }
          output = { stepsApplied: count };
          break;
        }
        case "paint":
        case "line":
        case "stroke":
        case "rect": {
          if (!window.paused) throw new Error("pause before bounded edits");
          const id = material(command.material);
          const diameter = integer(command.diameter ?? 1, "diameter", 1, MAX_BRUSH);
          const previous = cells().slice();
          editSnapshot = previous;
          const tracker = { stamps: 0 };
          if (command.op === "paint") {
            const p = point(command, width, height);
            operationStarted = sceneMutationStarted = true;
            stopBoot();
            stamp(p.x, p.y, diameter, id);
            tracker.stamps++;
          } else if (command.op === "line") {
            const from = point(command.from, width, height);
            const to = point(command.to, width, height);
            const stamps = Math.ceil(Math.hypot(to.x - from.x, to.y - from.y) / Math.max(1, diameter / 3)) + 1;
            if (stamps > MAX_STAMPS) throw new Error("stroke stamp limit exceeded");
            operationStarted = sceneMutationStarted = true;
            stopBoot();
            paintLine(from, to, diameter, id, tracker);
          } else if (command.op === "stroke") {
            if (!Array.isArray(command.points) || command.points.length < 2 || command.points.length > 100) throw new Error("stroke needs 2-100 points");
            const points = command.points.map(p => point(p, width, height));
            // Validate total work *before* doing any painting (atomic refusal).
            const expected = points.slice(1).reduce((n, p, i) => n + Math.ceil(Math.hypot(p.x - points[i].x, p.y - points[i].y) / Math.max(1, diameter / 3)) + 1, 0);
            if (expected > MAX_STAMPS) throw new Error("stroke stamp limit exceeded");
            operationStarted = sceneMutationStarted = true;
            stopBoot();
            for (let i = 1; i < points.length; i++) paintLine(points[i - 1], points[i], diameter, id, tracker);
          } else {
            const x = integer(command.x, "x", 0, width - 1);
            const y = integer(command.y, "y", 0, height - 1);
            const w = integer(command.width, "width", 1, width - x);
            const h = integer(command.height, "height", 1, height - y);
            if (w * h > MAX_RECT_CELLS) throw new Error("rectangle too large");
            const filled = booleanOption(command.fill, "fill", true);
            operationStarted = sceneMutationStarted = true;
            stopBoot();
            // Pixel-exact rectangles: diameter=1 regardless of brush choice.
            for (let xx = x; xx < x + w; xx++) {
              for (let yy = y; yy < y + h; yy++) {
                if (filled || xx === x || xx === x + w - 1 || yy === y || yy === y + h - 1) {
                  stamp(xx, yy, 1, id); tracker.stamps++;
                }
              }
            }
          }
          const changedCells = changedCount(previous);
          mutated = changedCells > 0;
          output = { material: labels.get(id), stamps: tracker.stamps, changedCells, note: "Native paint replaces Empty cells only, except Empty erases existing materials" };
          break;
        }
        case "exportCells": {
          return {
            status: "observed", ...status(),
            format: "sandspiel-cells-only/v1",
            fidelity: "cells only; native RNG, wind and fluid state are not captured",
            cellsBase64: encode(cells()),
          };
        }
        case "importCells": {
          if (!window.paused) throw new Error("pause before importing cells");
          stopBoot();
          if (command.format !== "sandspiel-cells-only/v1") throw new Error("unsupported snapshot format");
          if (command.width !== width || command.height !== height) throw new Error("snapshot dimensions mismatch");
          const bytes = decode(command.cellsBase64);
          if (bytes.length !== width * height * 4) throw new Error("snapshot byte length mismatch");
          for (let i = 0; i < bytes.length; i += 4) {
            if (!labels.has(bytes[i])) throw new Error(`invalid material ID at cell ${i/4}`);
          }
          operationStarted = true;
          sceneMutationStarted = true;
          fluid.reset(); fluid.update(); fluid.reset(); fluid.update();
          universe.reset();
          cells().set(bytes);
          universe.flush_undos();
          mutated = true;
          output = { restoredCells: width * height, fidelity: "cells only; not a bit-exact simulation checkpoint" };
          break;
        }
        default: throw new Error(`unsupported operation: ${command.op}`);
      }
      if (mutated) revision++;
      render();
      return { status: "applied", beforeRevision, afterRevision: revision, ...output, ...status() };
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      if (operationStarted) {
        let changedCells;
        if (editSnapshot) {
          try { changedCells = changedCount(editSnapshot); } catch (_) { /* WASM memory may be unavailable after a runtime failure. */ }
        }
        if (sceneMutationStarted && revision === beforeRevision && (changedCells === undefined || changedCells > 0)) revision++;
        return {
          status: "failed", reason, beforeRevision, partialApplicationPossible: true,
          ...(changedCells === undefined ? {} : { changedCells }),
          ...(nativeTicksCompleted ? { nativeTicksCompleted } : {}),
          ...status(),
        };
      }
      return { status: "refused", reason, beforeRevision, ...status() };
    }
  };

  // Produce the exact original native stamp sequence. Validation completes before
  // any native painting, and the fast 'run' path above is unchanged.
  const planPacedStamps = (command) => {
    if (!["paint", "line", "stroke", "rect"].includes(command.op)) throw new Error("paced operation must paint");
    if (!window.paused) throw new Error("pause before bounded edits");
    const id = material(command.material);
    const diameter = integer(command.diameter ?? 1, "diameter", 1, MAX_BRUSH);
    const stamps = [];
    const segment = (a, b) => {
      const steps = Math.ceil(Math.hypot(b.x - a.x, b.y - a.y) / Math.max(1, diameter / 3));
      if (stamps.length + steps + 1 > MAX_STAMPS) throw new Error("stroke stamp limit exceeded");
      for (let j = 0; j <= steps; j++) {
        const t = steps ? j / steps : 0;
        stamps.push([Math.round(a.x + (b.x - a.x) * t), Math.round(a.y + (b.y - a.y) * t), diameter]);
      }
    };
    if (command.op === "paint") {
      const p = point(command, width, height);
      stamps.push([p.x, p.y, diameter]);
    } else if (command.op === "line") {
      segment(point(command.from, width, height), point(command.to, width, height));
    } else if (command.op === "stroke") {
      if (!Array.isArray(command.points) || command.points.length < 2 || command.points.length > 100) throw new Error("stroke needs 2-100 points");
      const points = command.points.map(p => point(p, width, height));
      for (let i = 1; i < points.length; i++) segment(points[i - 1], points[i]);
    } else {
      const x = integer(command.x, "x", 0, width - 1);
      const y = integer(command.y, "y", 0, height - 1);
      const w = integer(command.width, "width", 1, width - x);
      const h = integer(command.height, "height", 1, height - y);
      if (w * h > MAX_RECT_CELLS) throw new Error("rectangle too large");
      const filled = booleanOption(command.fill, "fill", true);
      for (let xx = x; xx < x + w; xx++) {
        for (let yy = y; yy < y + h; yy++) {
          if (filled || xx === x || xx === x + w - 1 || yy === y || yy === y + h - 1) stamps.push([xx, yy, 1]);
        }
      }
    }
    return {id, stamps};
  };

  const runPaced = async (input, options = {}) => {
    const beforeRevision = revision;
    let started = false;
    let previous;
    commands++;
    try {
      if (pacing) throw new Error("paced edit already executing");
      const command = plain(input, "command");
      const opts = plain(options, "pacing options");
      const fps = integer(opts.fps ?? 12, "fps", 4, 20);
      const stampsPerFrame = integer(opts.stampsPerFrame ?? 12, "stampsPerFrame", 1, 80);
      checkRevision(command);
      const {id, stamps} = planPacedStamps(command);
      previous = cells().slice();
      pacing = true;
      started = true;
      stopBoot();
      const interval = Math.ceil(1000 / fps);
      for (let i = 0; i < stamps.length; i += stampsPerFrame) {
        for (const [x, y, diameter] of stamps.slice(i, i + stampsPerFrame)) {
          stamp(x, y, diameter, id);
        }
        render();
        // Yield actual presentation time to Chromium's compositor/MediaRecorder.
        // This is a fixed, validated visual interval, not user-provided JavaScript.
        await new Promise(resolve => setTimeout(resolve, interval));
      }
      const changedCells = changedCount(previous);
      if (changedCells) revision++;
      render();
      await new Promise(resolve => setTimeout(resolve, interval));
      return {
        status: "applied", beforeRevision, afterRevision: revision,
        material: labels.get(id), stamps: stamps.length, changedCells,
        paced: true, presentationFrames: Math.ceil(stamps.length / stampsPerFrame),
        note: "Same native stamp coordinates/order as the fast path; painting is presented progressively",
        ...status(),
      };
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      if (started) {
        let changedCells;
        try { changedCells = changedCount(previous); } catch (_) {}
        if (changedCells === undefined || changedCells > 0) revision++;
        return {
          status: "failed", reason, beforeRevision, partialApplicationPossible: true,
          ...(changedCells === undefined ? {} : {changedCells}), ...status(),
        };
      }
      return { status: "refused", reason, beforeRevision, ...status() };
    } finally {
      pacing = false;
    }
  };

  return Object.freeze({
    status,
    run,
    runPaced,
    // Hooks for upstream human brush/loop operations. They are not a security boundary.
    notifyManualEdit() { revision++; },
    notifyTick() {
      ticks++; revision++;
      if (liveTicksRemaining > 0 && --liveTicksRemaining === 0) setPause(true);
    },
  });
}