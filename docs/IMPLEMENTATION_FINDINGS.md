# Sandspiel Agent Lab — verified implementation findings

**As of:** 2026-11-07 · **Upstream baseline:** `MaxBittker/sandspiel` `9936e06b07a583aedfba9589c0cead2917f405fb` · **Implementation branch at documentation start:** `feat/agent-lab-v1` `90d4b99c4393747ac4f7ca465da3cb16d6abf5ad`. Follow the current PR head for all subsequent source-matched qualification.

## Outcome summary

The original Rust/WebAssembly Sandspiel client has been compiled, exercised and recorded in GitHub-hosted Chromium. The native physics source is unchanged at the upstream baseline. GitHub-connected ChatGPT can author a finite JSON action batch, trigger a runner by a branch push, retrieve ZIP evidence and inspect the actual game state and imagery. This **proves a batch-operated environment**, not persistent interactive browser control or an independent completion of Luna's recorded full challenge.

### First principles confirmed from source

- `crate/src/lib.rs` exposes `Universe.paint`, `tick`, `cells`, `reset`, and native undo. Cells are X-major and four bytes each; material IDs should be obtained from the current Wasm material catalogue rather than guessed from rendered colour.
- `js/index.js` owns the visual frame loop. An acknowledged `step` in the lab advances both native simulation and WebGL fluid while paused; the browser screenshot is actual rendered output.
- Original paint semantics generally insert into Empty cells; `Empty` erases. Use bounded operations and verify changed-cell counts. `status:applied` is not by itself proof that material was placed.
- `agent.html` bypasses the normal site's auto-generated startup terrain, tracking scripts and promotional UI; original `index.html` remains available.
- Browser-level `window.agentLab` is a convenience adapter, not a sandbox or a remotely authenticated API. The Actions runner is the current validated ingress.

### Evidence ledger

| Run / source | Observed result | Qualification |
| --- | --- | --- |
| [42374201807](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42374201807) | Native build and browser actions reached screenshot capture; smoke assertion compared Wood before simulation with Wood after evolution | Failed **test assertion**; no evidence of engine failure |
| [42374743617](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42374743617), `62d1952763` | Real browser smoke: Wood/Wall/Water, 120 steps, native inspection and byte-identical cells-only export/import | Passed |
| [42375713505](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375713505), `dae4e23d99` | Build and browser suite after the canonical Actions session runner was added | Passed |
| [42375727238](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375727238), `agent/sessions` `c7fdbbf9d8` | Two-tree woodland, 20 operations, 240 native+fluid ticks, region census, screenshots/video and cells hash | Passed |
| [42376224346](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376224346), `90d4b99c43` | Exact implementation branch browser qualification including source-hashed cache workflow | Passed |
| [42376259313](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376259313), `cee7f24f6c` | Cold session on new source-hash key, five ticks; cache created | Passed |
| [42376483034](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376483034), `78bb3201c8` | Cache **hit** with same source hash; Node/Rust/wasm-pack/webpack stages skipped; real Chromium session still completed five steps | Passed |
| [42375551155](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375551155), `171f0cc0b3` | Alternative Actions-driven Garden smoke scenario: validated Sand/Wood/Seed/Water/Plant placement, 120 steps and video | Passed; implementation superseded |

The [alternate draft PR #2](https://github.com/techrote/sandspiel-agent-lab/pull/2) was closed **without merge**. Its runner provided a useful proof of reuse of a compiled browser artifact but duplicated `session-run.yml`, exposed a less complete input schema and relied on an expiring, manually pinned artifact. The canonical path is PR #1 + `agent/sessions`.

### Evidence portability

Both a compiled browser-bundle ZIP and screenshot/video evidence ZIPs have been downloaded into this ChatGPT session through the connected GitHub integration. This proves binary artifact transfer from GitHub Actions; it does **not** override the session container's Chromium navigation policy (`net::ERR_BLOCKED_BY_ADMINISTRATOR` on local HTTP). The tested way to execute the game from ordinary chat is GitHub-hosted Chromium.

Recording files are produced by Playwright during an actual browser session. The scene screenshots and inspected cell counts are evidence of the game, but elapsed recording duration includes browser and tool waiting time; it must not be used to infer simulation steps or AI reaction latency.

### Lessons learned

1. **Evidence must be source-matched and state-matched.** The first failing smoke test compared original Wood against post-simulation Wood. The corrected test checks the exported post-step state against its own reimport, including all cell bytes.
2. **Observation matters more than command acknowledgement.** A valid draw operation can have zero effect on occupied cells; the simulation can redistribute matter substantially during a short bounded run. Inspect native cells as well as screenshots.
3. **Structured geometry has a clear advantage, but changes the benchmark.** The first two-tree scene used exact lines and shapes. A mouse-equivalent mode must be qualified before claiming the same conditions as Luna's original browser playthrough.
4. **Build caching is valuable and has now been demonstrated.** One cold run populated a source-hashed browser cache, and the next warm run skipped toolchain and compilation. The cache must be checked for source completeness and provenance before release.
5. **Free-running simulation is not a persistent authoring session.** The present cells-only interchange omits native RNG, wind, burn, generation and GPU fluid. It cannot be promised as bit-exact replay or a cross-run live world.
6. **Avoid multiple overlapping drivers.** The two real runs demonstrated the same concept. Consolidating on the stricter canonical runner avoided redundant workflows and divergent command contracts.

### Unfinished work

- Independent technical and security review of latest PR #1 head, all workflows and the documented credential handover.
- Full Luna comparison: attractive dense forest; isolated material apparatus; separate preparation/repair/challenge allowances; permitted ignition; actual `Fire` versus `Gas` inspection; human-free recording. Not yet demonstrated.
- Mouse-equivalent baseline distinct from structured drawing; independent comparison must start from equivalent source and world state.
- Explicit native/full-GPU checkpoint semantics if truly persistent evolving sessions become necessary.
- Optional provider key integration **only once the provider and scope are specified**; current GitHub-backed simulation needs none.

### Review and next gate

Read `docs/REVIEWER_BRIEF.md`. **Do not merge PR #1 simply because the smoke CI is green.** Validate the exact current PR head and the distinct `agent/sessions` runner head, including the cache, command limits, reported outcomes and absence of credential leakage. After independent review, perform source-matched gates and a guarded merge decision.
