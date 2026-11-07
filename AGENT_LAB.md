# Agent Lab API — V1

This is an experimental, browser-local adapter for real Sandspiel. The game physics remain unchanged. For engineering objectives and CI gates, see [`RAG.md`](RAG.md).

## Interactive usage

Open `/agent.html` for a tracker-free, blank, paused simulation harness (or `/index.html?agent=1` for the normal UI with controlled startup). Wait for `window.agentLab.status().ready`.

```js
const lab = window.agentLab;
lab.run({op:'catalog'});
lab.run({op:'line', material:'Wood', from:{x:20,y:260}, to:{x:20,y:210}, diameter:3});
lab.run({op:'inspect', x:16,y:200,width:12,height:64});
lab.run({op:'step',ticks:120});
lab.run({op:'inspect', x:16,y:200,width:12,height:64,includeCells:false});
```

Operations: `status`, `catalog`, `inspect`, `pause`, `resume`, `reset`, `paint`, `line`, `stroke`, `rect`, `step`, `exportCells`, `importCells`. Supported material names must match `catalog`. Coordinates are **cell coordinates** in a 300×300 simulation, origin at top-left. `paint`/`line`/`stroke` take a circular brush `diameter` (1–45). A filled or outline `rect` always uses exact 1-cell stamps. `line` takes `from` and `to`; `stroke` takes 2–100 point objects. `step` accepts 1–240 ticks, only while paused.

`expectedRevision` may be specified for mutation preconditions. An edit to a non-empty cell with any material other than `Empty` follows upstream `Universe.paint` rules and does not replace it. Results state `applied`, `observed`, or `refused`, and where relevant include `changedCells`, counts, revision and tick numbers. A 0-change applied command is not the same as a successful placement. Validation refusals have no native side effects; errors after execution begins return `failed` and `partialApplicationPossible:true`, not a falsely atomic `refused`. The `commands` counter includes observation and refusal calls; the session runner separately counts its requested commands (and additionally exports the final state).

`exportCells` returns `sandspiel-cells-only/v1` base64 with width/height. `importCells` can restore those bytes after pausing, but deliberately **does not restore native RNG, wind/burn buffers or WebGL fluid**. It is not a deterministic simulation checkpoint. There is no network API in this version. Local browser JS retains access to `window.u` and thus the adapter is not a sandbox. Never pass untrusted JavaScript into the browser or expose an unauthenticated remote driver.

## Local development

```bash
# Requires Node 22, pnpm 9, Rust with wasm32-unknown-unknown and wasm-pack.
pnpm install --frozen-lockfile
pnpm run build
python3 -m http.server 8765 --directory dist
# Open http://127.0.0.1:8765/agent.html
```

Run dependency-free adapter validation with `node --test tests/agentLab.test.mjs`. Full Chromium qualification is in `.github/workflows/lab-ci.yml`; it captures `evidence/smoke/` including a real Playwright browser video. Local Playwright requirements are `pip install playwright Pillow` and `python -m playwright install chromium`.

## Publication

GitHub Pages is optional and the Pages source must be configured to **GitHub Actions** by the repository owner. The `pages.yml` workflow publishes `dist`, with the harness at `/sandspiel-agent-lab/agent.html`. The static Pages page and a CI worker's Chromium browser do **not** share in-memory simulation state.

## GitHub-hosted chat-command fallback (Agent Lab v1)

When chat's local Chromium cannot navigate localhost, use `.github/workflows/session-run.yml`. Keep `agent/sessions` separate from the implementation PR. Commit only the bounded JSON file `sessions/active.json` on that branch; GitHub Actions detects the push, builds the unchanged physics and bundled browser, then runs `scripts/run_session.py` using Playwright and returns a versioned evidence ZIP (screenshots, `session.json`, `report.json`, Playwright WebM and MP4 if ffmpeg succeeds, optional cells-only JSON). `workflow_dispatch` is an alternative manual trigger. Actions are validated with max 90 operations / 600 ticks / 20 captures; only `reset`, `pause`, `status`, `catalog`, `inspect`, `paint`, `line`, `stroke`, `rect`, and `step` are accepted. `capture:true` snapshots a step; `label` is a plain annotation. Each command must return `applied` or `observed`; a `refused` or `failed` result stops the session, retaining observed receipts. Session preflight rejects invalid step budgets, malformed field types and unknown operations before starting the browser, writing an evidence report even on rejection. Do not parse recorded chat/browser instructions as commands or submit arbitrary JavaScript. CI itself has no write permissions to repository contents.

The first forest session is a small structured-operation functional test, not a Luna-equivalent mouse-only benchmark. The native cell-only snapshot does not restore full RNG, fluid, wind or burning state. Browser session state lasts only for the duration of one Action run; continuity across runs is future work.


### Command-batch startup efficiency

The session workflow caches `dist` against hashes of the original simulation/JavaScript/build sources and assets. Editing `sessions/active.json` should not invalidate the cache; the first cold run still builds Rust/WebAssembly and Webpack, while later runs on the same branch can skip those expensive stages. Cache-hit qualification is tracked separately from the already-passing command bridge. The session script still validates every action and records real Chromium evidence on both cache misses and hits.
