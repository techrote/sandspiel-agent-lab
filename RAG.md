# Sandspiel Agent Lab — RAG Engineering Plan and Living Handoff

**Repository:** `techrote/sandspiel-agent-lab`  
**Upstream:** `MaxBittker/sandspiel` at `9936e06b07a583aedfba9589c0cead2917f405fb` (MIT)  
**Project objective:** let an agent inside ordinary ChatGPT interact with the *actual* Sandspiel client, observe real rendering and native cell data, and record reproducible sessions. **Do not require Work mode, rewrite physics, or pretend an offline surrogate is a gameplay result.**  
**Status (2026-11-07):** The real Sandspiel Rust/WASM browser build, bounded Playwright control and screenshot/video evidence pipeline are proven. Source-matched browser CI passed [42376224346](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376224346); independently authored woodland [42375727238](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375727238) passed (20 commands, 240 native ticks). Both the browser bundle and evidence ZIP were transferred to ChatGPT. The local Chromium navigation policy blocks localhost; GitHub-hosted Chromium and the `agent/sessions` JSON workflow are the operational route. Warm cache [42376483034](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376483034) succeeded and skipped Rust/WASM/webpack rebuild. Full Luna challenge, mouse-equivalent comparison and exact evolving-state persistence are **not complete**. PR #1 is draft and unmerged; this documentation commit requires fresh exact-head CI.

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
10. [Verified consolidation and credential handover](#10-verified-consolidation-and-credential-handover-2026-11-07) — passing runs, canonical driver and optional keys.

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
GitHub repository (Sandspiel + agent-control adapter)
    |
    +--> CI Rust/WASM + Webpack -> source-hashed dist cache
    |                                      |
    |                              real Playwright/Chromium
    |
ChatGPT -> connected GitHub -> agent/sessions JSON push
                              |  allowlisted command runner
                              v
                     source-matched dist cache
                              |
                     actual Sandspiel WASM
                              |
                  screenshots / native cells / video
                              |
                      GitHub Actions artifacts
                              |
                     ChatGPT review and iteration
```

**Verified:** the compiled bundle and browser evidence archives transfer through the connected GitHub integration. **Blocked by environment policy:** direct local Chromium navigation to localhost; do not bypass it. Use the tested GitHub-hosted runner. The source-hashed compiled `dist` cache hit was confirmed in run 42376483034; cross-run native state is not persisted. A Pages tab is a static, independent world, not the live world in Actions.

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
- First browser test incorrectly compared restored *post-tick* Wood to a *pre-tick* measurement. The corrected test compares to the matching post-tick export and requires byte-identical cell serialization; this passed in run [42374743617](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42374743617).
- The first evidence ZIP (artifact `13574329014`) transferred through the GitHub connector. Subsequently, both the compiled Web bundle ZIP and the successful browser-evidence ZIP transferred; file transfer is proven but local-browser navigation remains blocked.
- Browser recording file remained zero bytes in the failed run because the script aborted before closing its Playwright context; a `finally` cleanup was added so failures also produce media and command history.

### Chat environment browser policy finding

This session's Playwright/Chromium cannot open a local HTTP origin (`net::ERR_BLOCKED_BY_ADMINISTRATOR`), despite containing browser binaries and the successful GitHub Actions bundle. Do not attempt to evade platform policy or claim local play. **Use the dedicated GitHub-hosted session runner instead**, which executes the *real compiled original game* in Actions Chromium, reads only bounded `sessions/active.json`, and exports actual screenshots, cell inspections and video for transfer back into ChatGPT. A successful short smoke and a 240-step authored woodland run have both been obtained; this bridge is operational for bounded batch sessions.

### Chat-triggered session evidence (2026-11-07)

- **Source:** session branch `agent/sessions` commit `c7fdbbf9d8203f17e2c7e46771bc3a95f8108070`, same physics and app code as the implementation branch; only the session JSON differs.
- **Execution:** GitHub Actions [run 42375727238](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375727238); all 20 commands accepted, `ticks=240`, `page_errors=[]`; `cells_sha256=73e4814751b18c09e52bfaf8123834dd774c685cfd0e8e254ac28709b89a95c9`.
- **Observed:** a Sand floor, two Wood trunks with branches, four Plant canopy patches, Seeds and Water. After 120 ticks, a native 100×100 inspection counted `Plant=1932`, `Wood=720`, `Empty=7348`; 120 further ticks showed additional hanging growth and a small flower. Actual screenshots and WebM uploaded as [artifact 13575348807](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375727238/artifacts/13575348807); video also converted in ChatGPT to a 30.44-second MP4.
- **Limitations:** this is programmatic drawing with structure and observation, not a mouse-equivalent test or a full garden/apparatus/fire experiment. Playwright video duration is **not** simulation time. Cell bytes alone do not preserve RNG, wind, burn or GPU fluid state; runs are independent unless command history is replayed. Source-hashed browser bundle caching was subsequently shown to hit in [42376483034](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376483034), skipping the expensive build steps.

## 7. Fallback and MCP roadmap

The compiled artifact transferred successfully but local HTTP navigation was blocked by host policy. The tested fallback design uses authenticated GitHub connector writes to `sessions/active.json` on a dedicated `agent/sessions` branch. An allowlisted JSON document (at most 90 commands, 600 native ticks and 20 screenshots) triggers `.github/workflows/session-run.yml`, which builds upstream physics, executes a real Chromium session and returns typed action evidence and MP4/WebM recordings. It never evaluates input JavaScript, executes command-supplied shell, or visits user-supplied URLs. On each edit, update the single session JSON and use the returned artifact to decide the next command batch. Authenticated GitHub edits triggering the dedicated branch workflow have been verified by actual successful runs. Avoid running one job per pixel.

Later, an authenticated session service could present the same schema over an MCP server or ChatGPT plugin, **only after verifying write-tool access on this account**. Do not spend effort on a remote daemon before the Actions/browser capture path works. Greenshot-multibinds is optional for Windows desktop capture; Linux Playwright recording is the initial baseline.

## 8. Security, resource and provenance policy

- Keep the original MIT notice, upstream source hash and physics code intact.
- Do not execute untrusted issue-comment text, shell strings, arbitrary JS or remote URLs. Only pass schema-validated JSON through an action bridge.
- Public Pages is static; never embed GitHub tokens or user secrets. Lab harness omits production ad/tracker scripts, and does not depend on production Firebase functionality for agent gameplay.
- Limit brush radius, total stamps, inspection sizes, run ticks and CI time. Log refusals and runtime source identity.
- No automatic PR merges. Coordinate branch state, exact-head CI and user-approved integration; resolve conflicts instead of force-pushing accepted work.

## 9. Codex operating handoff

**Next: independent review, then guarded integration.** The Actions build, Playwright smoke, artifact handoff, structured woodland and cached batch execution are proven. Refresh PR #1 and `agent/sessions` heads; review the browser adapter and the remote command/CI boundaries, repair only substantiated defects, then rerun the exact-head suite. Do not merge without explicit owner instruction. After that, attempt the full Luna challenge in both mouse-equivalent and structured authoring modes with recorded evidence and a fixed allowance ledger. Maintain unchanged native physics; do not broaden into an unrelated agent platform.

**Progress record template:** `accepted source SHA / build run / bundle artifact / browser status / action+cell evidence / recording artifact / transfer result / blockers / next bounded action`. Update this RAG when evidence materially changes the decision.

## References

- Upstream source: https://github.com/MaxBittker/sandspiel
- Target fork: https://github.com/techrote/sandspiel-agent-lab
- Existing GitHub workflows: https://github.com/techrote/sandspiel-agent-lab/actions
- User-recording evidence: original 33-minute Sandspiel session analysed separately; findings require no physics changes.

## 10. Verified consolidation and credential handover (2026-11-07)

The more detailed source- and run-linked record is [`docs/IMPLEMENTATION_FINDINGS.md`](docs/IMPLEMENTATION_FINDINGS.md). The new project-specific [`README.md`](README.md) replaces the original upstream project introduction, while retaining upstream attribution and MIT licensing.

- The source-matched browser implementation is still in **draft PR #1**, not yet merged; the `agent/sessions` branch executes approved, bounded JSON in real GitHub-hosted Chromium. The alternate PR #2 was closed **without merge** as redundant.
- Key evidence: feature-head [42376224346](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376224346) succeeded; independent woodland [42375727238](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375727238) succeeded after 20 operations and 240 native steps; source-hashed bundle cache cold [42376259313](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376259313) then warm [42376483034](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376483034) both succeeded, with the warm hit actually skipping build toolchain and webpack.
- The **current gameplay bridge requires no external API key**. If a future model or remote-control provider needs one, use the owner-controlled, short-lived, credit-limited **server-side** handover described in [`docs/CREDENTIAL_HANDOVER.md`](docs/CREDENTIAL_HANDOVER.md). Do not ask for a raw key in chat, do not wire secrets into baseline game CI and do not expose a secret in the static page.
- Independent review scope and exact-head verification requests are in [`docs/REVIEWER_BRIEF.md`](docs/REVIEWER_BRIEF.md). Source-matched smoke passing is necessary but not sufficient for merging or for claiming Luna-equivalent success.

**Next objective:** independent review and guarded PR #1 integration, then a controlled mouse-equivalent versus structured authoring comparison for the full forest/apparatus challenge.
