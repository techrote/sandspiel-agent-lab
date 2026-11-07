# Sandspiel Agent Lab — RAG Engineering Plan and Living Handoff

**Repository:** `techrote/sandspiel-agent-lab`  
**Upstream:** `MaxBittker/sandspiel` at `9936e06b07a583aedfba9589c0cead2917f405fb` (MIT)  
**Project objective:** let an agent inside ordinary ChatGPT interact with the *actual* Sandspiel client, observe real rendering and native cell data, and record reproducible sessions. **Do not require Work mode, rewrite physics, or pretend an offline surrogate is a gameplay result.**  
**Status (2026-11-07):** real Sandspiel/WASM CI build and browser smoke passed ([42374743617](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42374743617)); compiled bundle and real browser artifacts transferred into ChatGPT. Local Chromium is administratively URL-blocked (including localhost), so browser execution currently uses GitHub-hosted Chromium. A new bounded scenario runner succeeded ([42375551155](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375551155)), with actual material painting, 120 native+fluid simulation steps, screenshots, region inspection, cells export and video. Full Luna comparative challenge remains unattempted; source-qualified integration and merge decisions remain pending.

## Contents

1. [Goal and non-goals](#1-goal-and-non-goals) — boundaries and evidence standard.
2. [Verified source baseline](#2-verified-source-baseline) — native and browser affordances.
3. [Execution architecture](#3-execution-architecture) — Actions, Pages, local browser and fallback.
4. [Agent command contract](#4-agent-command-contract) — bounded operations, observation and revisions.
5. [State and recording semantics](#5-state-and-recording-semantics) — what evidence represents.
6. [Incremental qualification](#6-incremental-qualification) — concrete tests and gates.
7. [Fallback and MCP roadmap](#7-fallback-and-mcp-roadmap) — adapt to connector limitations.
8. [Security, resource and provenance policy](#8-security-resource-and-provenance-policy) — preserve trust and avoid waste.
9. [Codex operating handoff](#9-codex-operating-handoff) — next actions and stopping conditions.

## 1. Goal and non-goals

**Primary user outcome:** independently reproduce the Luna-in-Sandspiel garden → forest → separated apparatus → constrained ignition exercise, with genuine screenshots and recording, without live human assistance. The comparative benchmark must use a separate mouse-equivalent mode first; structured geometric operations must be clearly labelled and measured separately.

**Non-goals:** adding new materials, changing native reaction rules, creating an alternative simulation, claiming shared real-time multi-user edits without a shared backend, or treating a saved cell palette as an exact simulation checkpoint. Build the smallest useful mechanism first.

## 2. Verified source baseline

- Source is already forked, unchanged at `9936e06...`, under `techrote/sandspiel-agent-lab`, branch `master`; not an empty repository.
- `crate/src/lib.rs`: `Universe.paint`, `.tick`, `.cells`, `.width/.height`, `.push_undo/.pop_undo`, `.reset` (WASM). Cell layout is X-major, four bytes per cell; inspect `js/components/ui.js` before touching it.
- `js/index.js`: native render loop advances `Universe.tick()` **and** WebGL fluid update; exposes `window.u`. `js/paint.js` owns human mouse strokes. `js/components/ui.js` owns pause, material selection, cell upload/loading.
- `Universe.paint` writes into Empty cells, except `Empty` material erases occupied cells. Narrow apparatus edits must respect this behavior rather than silently replacing existing materials.
- Native state also contains wind, burns, generation and SplitMix64 RNG; the GPU fluid simulation holds other evolving state. `cells()` alone does **not** save an exact ongoing runtime.
- Upstream license is MIT; retain copyright notices and attribution.

## 3. Execution architecture

```text
Github master / feature branch (pinned upstream physics)
       |
       +--> GitHub Actions (Rust + wasm-pack, pnpm/webpack)
                   |              |
             browser bundle    Playwright smoke + frames + browser video
                   |
           versioned artifact -----------> local-chat artifact handoff (FIRST GATE)
                   |                          |
            optional Pages                if materializable: local HTTP/Chromium
                                              |
                                              +--> direct ChatGPT observation/actions
                   |
             no handoff? --> bounded Actions command-run fallback
                                 (future; validate authenticated issue events)
```

A GitHub Pages tab is not the same live world as a headless ChatGPT Chromium tab. Reopening requires an explicit export/replay; do not promise continuous shared state. The GitHub connector's binary artifact-reference materialization into this container has **not yet been proven**.

**Initial implementation:** optional `/agent.html` harness without production adverts and without auto-generated boot terrain; the original human-facing app remains usable on `/`.

## 4. Agent command contract

Agent operations are exposed as `window.agentLab.run({...})` in an explicit lab harness; browser script access is **not a security boundary**. The future remote command ingress must reject arbitrary JS, shell commands and untrusted URLs, and permit only schema-validated JSON commands.

V1 operations: `status`, `catalog`, `inspect`, `pause`, `resume`, `reset`, `paint`, `line`, `stroke`, `rect`, `step`, `exportCells`, `importCells`. Mutations may include `expectedRevision` to reject stale scene edits. `step` must run only while paused, increment both native simulation and WebGL fluid, and advance an observable tick count. Normal human mouse paint and live render ticks update revision accounting through hooks, though other legacy native updates may still need integration.

Bound commands: no out-of-range coordinates or unknown material IDs; limited brush, line stamps, rectangle area, inspection area and batch steps; refuse malformed inputs without partial drawing. Return `applied`, `observed` or `refused` with changed-cell counts where possible. Browser screenshots and real image evidence are captured by Playwright, not inferred from chat.

Example:

```js
window.agentLab.run({ op: 'pause' });
window.agentLab.run({ op: 'line', material: 'Wood', from: {x:20,y:240}, to: {x:20,y:180}, diameter:3 });
window.agentLab.run({ op: 'step', ticks:120 });
window.agentLab.run({ op: 'inspect', x:15, y:175, width:20, height:70 });
```

## 5. State and recording semantics

`exportCells` and `importCells` are explicitly **cells-only**, keyed by dimensions and version. They preserve species and per-cell registers but do not restore native RNG, wind/burn state or WebGL fluid textures. They are intended to resume *authored setups*, not promise bit-exact evolving simulation. Do not label them complete checkpoints.

Every experiment should publish source commit, command/event JSON, observed revisions, bounded tick count, native region/material summaries, before/after screenshots, browser video (WebM/MP4), and a fidelity label. Playback frames are not simulation ticks. A real video artifact must come from an actual Chromium session, never fabricated stills.

## 6. Incremental qualification

| Gate | Must demonstrate | If blocked |
| --- | --- | --- |
| A. Build | GitHub runner compiles upstream Rust/WASM and Webpack into a runnable static bundle | Fix toolchain/build before adding features |
| B. Observe | Playwright loads actual WebGL, native catalogue and canvas | Investigate browser/SwiftShader; no false game success |
| C. Act | Bounded Wood stroke, cell census, 120 actual native+fluid ticks, screenshot difference | Repair integration and repeat |
| D. Save | Cells-only setup exports, resets and restores exact material counts | Preserve session within one run until fixed |
| E. Capture | Recording, keyframes, structured JSON artifact | No recording claims without actual media |
| F. Handoff | Connected GitHub artifact can reach current chat container | Switch to Actions command execution, not base64 text copying |
| G. Host | Pages serves the exact compiled game, with correct subpath assets | Keep Actions artifact available while Pages configured |
| H. Comparison | Independently reproduce two-phase Luna benchmark, action budget fixed | Report failure or partial result; do not change budget silently |

**Available initial tests:** dependency-free Node tests of command validation and fake native adapter; Python Playwright real-browser smoke test in Actions.

### Observed first-run evidence (2026-11-07)

- GitHub Actions run `42374201807`: upstream native physics compiled to WebAssembly, Webpack emitted both browser entrypoints, Node unit tests passed, and Chromium initialized actual WebGL.
- Actual screenshot artifacts show a Wood stroke, a Wall chamber and Water before stepping, and a changed world after 120 acknowledged native+fluid ticks. Snapshot display differs from initial state, as expected for a simulation.
- First browser test incorrectly compared the restored *post-tick* scene to a *pre-tick* Wood measurement. The corrected test compares against a matching pre-export snapshot and requires byte-identical cell serialization after import; this remains to be requalified.
- Artifact ID `13574329014` transferred successfully through the connected GitHub action into `/mnt/data` in ChatGPT. This proves artifact transport for this evidence ZIP, **not yet the compiled Web app ZIP**.
- Browser recording file remained zero bytes in the failed run because the script aborted before closing its Playwright context; a `finally` cleanup was added so failures also produce media and command history.

### Verified remote execution (2026-11-07)

- `feat/agent-lab-actions-driver` carries an Actions-hosted Playwright runner and `sessions/garden-smoke.json`, with instructions in `ACTIONS_DRIVER.md`.
- Successful run [42375551155](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375551155) captured actual before/after browser frames, a nonzero WebM video, and JSON receipts for Sand/Wood/Seed/Water/Plant placement, 120 native+WebGL steps, inspection and export. The result was an infrastructure smoke, not Luna benchmark success.
- Local browser invocation from this ChatGPT container failed with `net::ERR_BLOCKED_BY_ADMINISTRATOR`; installed Chromium has a managed URL blocklist. Do not modify or bypass that policy. The compiled WebAssembly bundle remains available locally for static inspection.
- The run pins a known-good compiled bundle artifact with a 14-day retention, so archive or rebuild from a recorded source tree before it expires. PR test `GITHUB_SHA` may refer to a synthetic merge commit.
- Next: implement a meaningful two-mode (mouse-equivalent versus structured) comparative authoring trial; do not accept invented material outcomes.

## 7. Fallback and MCP roadmap

If artifact handoff succeeds, run locally in the chat container using Python Playwright and FFmpeg. If not, use `issue_comment`/branch-push triggered GitHub Actions with strict authentication, a dedicated session issue, replayable command JSON, bounded run size, idempotency and evidence artifacts. Confirm that the linked GitHub connection's write calls trigger workflow events before depending on them. Avoid one CI job per individual pixel; batch coherent actions.

Later, an authenticated session service could present the same schema over an MCP server or ChatGPT plugin, **only after verifying write-tool access on this account**. Do not spend effort on a remote daemon before the Actions/browser capture path works. Greenshot-multibinds is optional for Windows desktop capture; Linux Playwright recording is the initial baseline.

## 8. Security, resource and provenance policy

- Keep the original MIT notice, upstream source hash and physics code intact.
- Do not execute untrusted issue-comment text, shell strings, arbitrary JS or remote URLs. Only pass schema-validated JSON through an action bridge.
- Public Pages is static; never embed GitHub tokens or user secrets. Lab harness omits production ad/tracker scripts, and does not depend on production Firebase functionality for agent gameplay.
- Limit brush radius, total stamps, inspection sizes, run ticks and CI time. Log refusals and runtime source identity.
- No automatic PR merges. Coordinate branch state, exact-head CI and user-approved integration; resolve conflicts instead of force-pushing accepted work.

## 9. Codex operating handoff

**Finish the vertical slice rather than invent new investigations.** First obtain a passing Actions build and real browser smoke video. Then test artifact materialization into ChatGPT and drive one actual observation/action pair locally. If impossible, implement the bounded Actions command fallback, with source-matched evidence. Maintain exact original simulation material behavior. Do not broaden into a standalone client architecture, new physics, speculative AI platform or unrelated features.

**Progress record template:** `accepted source SHA / build run / bundle artifact / browser status / action+cell evidence / recording artifact / transfer result / blockers / next bounded action`. Update this RAG when evidence materially changes the decision.

## References

- Upstream source: https://github.com/MaxBittker/sandspiel
- Target fork: https://github.com/techrote/sandspiel-agent-lab
- Existing GitHub workflows: https://github.com/techrote/sandspiel-agent-lab/actions
- User-recording evidence: original 33-minute Sandspiel session analysed separately; findings require no physics changes.