# Actions-backed Sandspiel gameplay driver

This is the first proven way to run **real Sandspiel** from ordinary ChatGPT through its connected GitHub repository, without Work mode or a modified local browser policy. It is not a continuous shared live session or a generic remote shell.

## How it works

- The baseline game and `window.agentLab.run` are built from upstream Sandspiel with unchanged native material physics (see `RAG.md` and `AGENT_LAB.md`).
- `.github/workflows/lab-play.yml` obtains the **known-good compiled game** from successful build run [42374743617](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42374743617).
- `scripts/agent_play.py` loads a **repository-owned JSON scenario** from `sessions/` and executes its commands in Playwright Chromium against a locally hosted copy of the compiled game.
- The driver publishes actual screenshots, a native operation receipt log, optional cells-only export, and an actual browser WebM recording. No scene evidence is simulated.
- Actions artifacts can be downloaded through the connected GitHub integration directly into ChatGPT's container for inspection, optional MP4 conversion and user delivery.

## First independently authored smoke session

[Run 42375551155](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375551155) at commit `171f0cc0b3a67ece38ea515bb3014f80c5107841` succeeded with `sessions/garden-smoke.json`:
- Two Sand blocks, three Wood strokes, Seed, Water and Plant placed through validated Sandspiel commands.
- Scene observed before and after 120 acknowledged native+WebGL-fluid simulation steps.
- Region inspection and a cells-only export succeeded.
- Result status passed; no browser page errors were recorded; video artifact contains nonzero bytes.
- This was a **bounded technique demonstration**, not completion of Luna's garden/apparatus/ignition benchmark.

## Repeat a bounded session

Within a branch containing the new workflow, update `sessions/garden-smoke.json` with a JSON `commands` array, then push the branch. The `push` trigger runs this workflow for matching branches/paths. The `workflow_dispatch` entry is also available where the GitHub interface permits it.

Every command is a data object. Supported operations are `status`, `catalog`, `inspect`, `pause`, `resume`, `reset`, `paint`, `line`, `stroke`, `rect`, `step`, `exportCells` and runner-only `capture` with an alphanumeric label. No script/code evaluation, arbitrary URL input, arbitrary file access, shell commands or arbitrary imports from scenario JSON. The adapter enforces its own coordinate/stamp bounds. Runner additionally limits commands to 70 and total requested ticks to 2,000.

To request additional captures, insert `{"op":"capture","label":"after-trunks"}`. Successful runs contain `report.json`, `scenario.json`, labelled PNG frames and a WebM under `video/`. Failed runs retain a failure screenshot, reason and any finalized video.

## Critical limits

- The current game binary is **pinned to the successful GitHub Actions artifact** from build run `42374743617`, stored for only 14 days (expiry approximately 2026-11-21). Update the pinned build artifact deliberately and record both branch SHA and compiled source identity. A PR build may use a GitHub-generated merge commit rather than the branch head; compare source trees before claiming exact-head equivalence.
- Each run starts in a fresh paused 300×300 world. To modify an evolved world across runs, either replay prior operations or implement a state transfer with explicit fidelity limits. Exported cells **do not include** full RNG, wind, combustion or WebGL fluid state.
- Structured geometric authoring has an advantage over Luna's recorded mouse-only interaction. For a fair comparison, implement and qualify mouse-equivalent commands as a separately labelled experimental mode, then use the same initial scene/objectives and immutable action budget.
- The installed Chromium executable in ChatGPT's local container is subject to a managed URL blocklist, including localhost; do not alter or bypass it. The proven browser execution environment is GitHub-hosted Chromium.
- Keep the workflow isolated and bounded. Do not accept arbitrary user issue comments as executable code. A future authenticated command ingress requires an explicit permission and schema design.

## Next qualification target

Create a **second bounded scenario** with a procedurally empty or generated garden, multiple trees, chamber partitions, and a controlled ignition task. Record both authored and evolved states and a visible/structured material census. Preserve challenge budgets in scenario metadata. Treat unconfirmed fire versus gas as inconclusive until native cell inspection confirms actual Fire in the intended region. Do not merge either PR until source-matched full tests and an independent integration review are complete.
