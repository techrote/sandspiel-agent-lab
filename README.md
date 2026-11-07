# Sandspiel Agent Lab

**Real Sandspiel, operated and observed by software agents, with a reproducible browser recording.** This is an experimental fork of [Max Bittker's Sandspiel](https://github.com/MaxBittker/sandspiel) built to discover how a human and an AI agent can collaboratively author a falling-sand world.

The project uses **the existing Rust/WebAssembly simulation and WebGL renderer**. Its purpose is to make the actual game inspectable and controllable from ordinary ChatGPT conversations, without requiring ChatGPT Work mode or constructing a substitute physics engine.

> **Project state — 7 November 2026:** The implementation is in [draft PR #1](https://github.com/techrote/sandspiel-agent-lab/pull/1), not yet merged to `master`. The source-matched build and browser smoke tests pass. GitHub-hosted Chromium has completed and recorded bounded agent-driven authoring sessions. The full independent reproduction of Luna's forest/apparatus/ignition challenge is **not yet done**.

## What works

- An opt-in `/agent.html` harness creates a blank, paused 300×300 Sandspiel world without the regular page's ad/analytics dependencies.
- A browser-local adapter exposes `window.agentLab.run(command)`: material catalogue, native cell-region inspection, bounded paint/line/stroke/rectangle, pause, steps, reset, and cells-only export/import.
- Explicit revision checks, material validation and bounded commands provide useful failure/receipt semantics. Native painting still follows upstream rules (normally add into Empty cells; painting Empty erases).
- GitHub Actions compiles the real Rust/WASM game, starts it in Chromium using Playwright, performs native operations, advances both native physics and WebGL fluid, and captures PNGs, video, region counts and command receipts.
- Ordinary ChatGPT can update a validated JSON session through the connected GitHub repository, trigger that runner, retrieve the evidence artifact and examine its results.
- A source-hashed compiled browser cache has demonstrated a **warm hit**, avoiding repeated Rust/WASM/webpack compilation when only the command JSON changes.

### Execution model

```text
ChatGPT + connected GitHub
        |  edit a bounded session JSON
        v
agent/sessions branch -> GitHub Actions session-run.yml
        |  source-hashed browser bundle (compile if cache miss)
        v
real Sandspiel WASM + WebGL in Playwright Chromium
        |  validated commands, native cells, screenshots, video
        v
versioned evidence artifact -> GitHub -> ChatGPT for inspection
```

This is **batch-based control**, not persistent live browser sharing. A new workflow run starts a new world unless commands or a documented, limited state representation are replayed. Frames in a recording are not simulation ticks.

## Reproduce an agent session

The current test implementation lives on [`feat/agent-lab-v1`](https://github.com/techrote/sandspiel-agent-lab/tree/feat/agent-lab-v1). The execution branch is [`agent/sessions`](https://github.com/techrote/sandspiel-agent-lab/tree/agent/sessions).

1. Inspect the schema and limits in [`AGENT_LAB.md`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/AGENT_LAB.md) and the checked-in example at [`sessions/active.json`](https://github.com/techrote/sandspiel-agent-lab/blob/agent/sessions/sessions/active.json).
2. Update the **JSON** scenario on `agent/sessions` (not executable code), keeping within its allowlist. A push affecting `sessions/active.json` triggers [`session-run.yml`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/.github/workflows/session-run.yml).
3. Inspect the GitHub Actions run and its downloadable screenshots, command receipts, WebM/MP4 and optional cells-only snapshot. Make the next revision based on observed results—not on an unverified success claim.
4. For the original local game, build as below and visit `/agent.html`. The normal Sandspiel UI remains at `/index.html`.

**Session limits (current):** up to 90 commands, 600 requested native steps and 20 captures including baseline/final. The runner only accepts the supported authoring/inspection operations. It does not execute arbitrary JavaScript supplied in JSON.

### Build locally

Prerequisites: Node.js 22, pnpm 9, Rust, `wasm32-unknown-unknown`, `wasm-pack` and Python 3. For browser tests, install Playwright Chromium.

```bash
pnpm install --frozen-lockfile
pnpm run build
node --test tests/agentLab.test.mjs
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
# open http://127.0.0.1:8765/agent.html
```

The compiled site can optionally be published using [`pages.yml`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/.github/workflows/pages.yml), after configuring GitHub Pages to deploy from Actions. GitHub Pages hosting alone does **not** create a shared live agent session.

## Evidence, not demonstrations by assertion

| Evidence | What it verifies |
| --- | --- |
| [Build and smoke run 42374743617](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42374743617) | Real Chromium/WebGL, Wood/Wall/Water edits, 120 native + fluid steps, cells-only round-trip |
| [Current feature-head CI 42376224346](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376224346) | Rust/WASM and real-browser validation passed at implementation head `90d4b99c` |
| [Woodland session 42375727238](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42375727238) | 20 accepted commands, 240 native steps, observed growth, actual screenshot/video and material census |
| [Cold cache 42376259313](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376259313) / [warm cache 42376483034](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42376483034) | Source-matched browser cache reused successfully; warm run skipped build toolchain and webpack |

The first agent test uses **structured geometric commands**, which are more accurate than ordinary mouse drawing. It must **not** be described as an independent, like-for-like completion of Luna's recorded challenge.

## Important limitations

- **State fidelity:** `exportCells` saves cell bytes, not native RNG, wind, combustion buffers, generation or WebGL fluid. It is an authored-scene interchange, **not an exact replayable runtime checkpoint**.
- **No persistent in-browser session across Actions jobs.** Interactive observation is batched; persistent remote state and a live shared service would require additional integration.
- **This chat container's Chromium cannot navigate local HTTP origins** because of an administrator policy. The verified execution path is GitHub-hosted Chromium; do not bypass the local browser policy.
- **No new physics.** Material behavior and recipes remain Sandspiel's upstream rules.
- **API keys:** None are required for the current GitHub-backed gameplay bridge. Third-party provider credentials, if later required, must stay out of chat, Git, browser bundles, screenshots and workflow artifacts. See [credential handover](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/docs/CREDENTIAL_HANDOVER.md).

## Project documents

- [Original Luna session: lossless primary frames, provenance, and constraint ledger](research/luna-authoring-session/EVIDENCE_INDEX.md)
- [Experiment context and relevance to the existing CyberSand client](docs/EXPERIMENT_CONTEXT.md)

- [Engineering plan, evidence ledger and handoff — `RAG.md`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/RAG.md)
- [Browser agent-control API — `AGENT_LAB.md`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/AGENT_LAB.md)
- [Implementation findings and evidence — `docs/IMPLEMENTATION_FINDINGS.md`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/docs/IMPLEMENTATION_FINDINGS.md)
- [Optional credential handover — `docs/CREDENTIAL_HANDOVER.md`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/docs/CREDENTIAL_HANDOVER.md)
- [Independent reviewer brief — `docs/REVIEWER_BRIEF.md`](https://github.com/techrote/sandspiel-agent-lab/blob/feat/agent-lab-v1/docs/REVIEWER_BRIEF.md)

## Upstream, attribution and licence

Sandspiel was created by [Max Bittker](https://github.com/MaxBittker/sandspiel). The fork's initial upstream source commit is [`9936e06b`](https://github.com/MaxBittker/sandspiel/commit/9936e06b07a583aedfba9589c0cead2917f405fb). The original simulation source, upstream credit and MIT licence are retained. The WebGL fluid simulation in Sandspiel includes work adopted from [PavelDoGreat/WebGL-Fluid-Simulation](https://github.com/PavelDoGreat/WebGL-Fluid-Simulation).

The Agent Lab is an experimental derivative, not the official Sandspiel service.
