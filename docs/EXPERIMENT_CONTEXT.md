# Experiment context: human–agent Sandspiel authoring

**Project:** [Sandspiel Agent Lab](../README.md) · **Research input:** 33:01 user-provided screen recording, analysed 2026-11-07 · **Development destination:** the *existing CyberSand client*, not a replacement agent-specific client.

## Why this experiment exists

The owner is experimenting with whether AI agents can act as useful **creative authors of evolving simulated worlds** while a person remains able to steer, correct, constrain and revise the work. The Sandspiel recording is a real example of a model controlling a browser-based falling-sand game, first creating an ornamental landscape and later solving an apparatus/reaction task. The goal is to compare actual **observation → intention → edit → simulation → inspection → correction**, not merely confirm that tool commands can be called.

The current Agent Lab fork is an **experimental instrument** for this research: make real Sandspiel controllable, inspectable and recordable from ordinary ChatGPT without Work mode. It preserves Sandspiel's native Rust/WASM physics. The original video was of Luna using Sandspiel in an interactive browser; Agent Lab's GitHub-hosted Chromium runner is *not* the environment that produced that original recording.

### Connection to CyberSand

User-supplied CyberSand background (not proven by this video): the existing client has live workbench editing, sources, actors, pause/step and saved setups; Generation Workbench 2 already supports procedural recipes, previews, validation, provenance inspection and recipe undo/redo; hierarchical generation has stable feature identities; semantic generation spans material planes; unified manual/procedural history and persistent reconciliation remain incomplete. Authoritative cells belong to the native simulation. Any eventual agent interface should use **validated operations inside the existing CyberSand client**.

This means Sandspiel Agent Lab should supply evidence about useful operations and collaboration patterns, **not** grow into an independent CyberSand clone, a new physics editor or a parallel agent-first simulation client. The research questions are: when is ordinary visual/mouse input sufficient; where do precise cell or feature operations remove friction; how can a user preserve agreed content; when should an agent pause/step/inspect; and how do human or procedural edits coexist with agent revisions?

## Original recording and curation

The original recording was uploaded in this ChatGPT conversation as `output.mp4` on 2026-11-07. It is **not** placed in this public repository, per the owner's preference for a small, carefully selected frame corpus instead of the ~222 MiB video. The provenance reference and exact media hash are in [the evidence manifest](../research/luna-authoring-session/manifest.json). The 31 curated frames and sequences are indexed in [EVIDENCE_INDEX.md](../research/luna-authoring-session/EVIDENCE_INDEX.md). The source may be absent in a future ChatGPT agent's context; do not pretend the full video is recoverable from this repository.

The selected frames are *full screen* at the original decoded resolution, including the user's chat and the simulation pane. They were losslessly encoded as WebP with **per-pixel equality to decoded PNG extraction verified** and SHA-256 hashes recorded. Crucially, the original recording is already H.264 lossy: lossless screenshots prevent **additional** alteration; they cannot prove that any subpixel colour artefact originated in the simulation. Navigation thumbnails (if generated later) are not primary evidence.

Use **elapsed video timestamps**, not the separate time shown beside chat messages. The game displays an FPS label, but that cannot establish recording speed, tool latency or simulation tick counts. Some tool details are collapsed; no hidden browser action or source-code finding may be inferred from a screenshot. The chat composer can show a *draft that has not yet been submitted* (especially around 16:00 and 27:20); do not count drafts as active instructions until subsequent visibly sent chat.

## The experiment's actual progression

| Elapsed time | Direct evidence | What changes |
| --- | --- | --- |
| 00:00–03:50 | [initial frames](../research/luna-authoring-session/EVIDENCE_INDEX.md#initial-garden-and-revised-brief) | Start with a small existing flower meadow; Luna adds Seed and Water and gets more flowers. The human initially requires avoiding accidental fire. |
| ~03:55–07:50 | [growth sequence](../research/luna-authoring-session/EVIDENCE_INDEX.md#forest-construction-series) | Human asks for a dense, varied forest; Luna draws Wood trunks/branches, then applies Plant so the simulation develops broad canopies and trailing growth. |
| ~08:00–16:30 | [apparatus frames](../research/luna-authoring-session/EVIDENCE_INDEX.md#material-apparatus-and-challenge) | Agent erects multiple Wall-separated compartments at the right edge. User later changes objective to preparing reactive materials and deliberately setting the forest on fire under constrained edits. |
| ~19:40–23:40 | [repair sequence](../research/luna-authoring-session/EVIDENCE_INDEX.md#acid-overflow-repair-and-budget-reset) | Erasing excess Acid also damages a wall; user forgives that erase, then authorises a repair and *resets* the challenge allowance. |
| ~24:00–27:40 | [diagnosis frames](../research/luna-authoring-session/EVIDENCE_INDEX.md#ignition-and-regrowth-series) | Initial Wood/Oil/Ice strategy does not establish a forest fire. The user corrects the agent's interpretation of Gas as Fire and grants an additional careful erase. |
| ~28:10–30:00 | [ignition and regrowth](../research/luna-authoring-session/EVIDENCE_INDEX.md#ignition-and-regrowth-series) | Red burning visibly propagates through the forest, then substantial destruction and green regrowth follow. Distinguish combustion being visible from proving exactly which cell interaction caused it. |

The [constraint and allowance ledger](../research/luna-authoring-session/CONSTRAINT_LEDGER.md) is the normative *historical description* of the recorded task. It is not a command list for future agents to execute without explicit owner instruction.

## Evidence interpretation rules

- **Observed:** on-screen scene pixels, selected tools, visible edit outcomes, submitted chat and interface state.
- **Agent-stated:** Luna's assertions or plans, which must be checked against the viewport and later observations.
- **User-stated:** human directions, corrections and assessments; significant evidence but not necessarily independent confirmation of material identity.
- **Inferred:** an explanation consistent with the samples, never evidence for an unobserved tool call or uninspected state.
- **Unknown:** exact mouse paths, native material IDs for visually ambiguous pixels, hidden source research, tick counts, precise fill fractions, causal isolation of a reaction and any events between samples.

In particular: a pink gas plume is not verified fire; an announced ignition is not the same as an observed burn; a drawn seed or plant patch is not the same as every later leaf being placed individually. **The task changes over time**. The initial requirement to avoid accidentally setting the forest on fire is superseded when the human later explicitly asks for controlled ignition.

## How to benchmark the lab against Luna

**Keep the two modes separate:**

1. **Mouse-equivalent comparison**: initial condition, browser-visible controls and interaction limits should be as comparable as practical to Luna's recording. No unlimited direct cell writes or revised material mechanics. Fix human constraints in advance, track their revisions and mark deviations.
2. **Structured-tool experiment**: explicitly allow cell/region inspection and bounded painting/lines/rectangles/openings. Compare edit precision, observability, damage/recovery and total intervention count, not just the prettiness of the end state.

Both modes should produce an actual scene, screenshots of *authored* and *evolved* states, confirmed native material census where available, a log of agent decisions and commands, and a candid result (success/partial/failure/unknown). A prerecorded script that creates a plausible forest without observing feedback is an **infrastructure test**, not evidence of independent creative problem-solving. No future experiment should silently inherit the recorded user's changing restrictions as a new live instruction.

## Immediate engineering implications for CyberSand

Prioritise *narrow integration* with the existing workbench rather than a new platform: (a) visual screenshots paired with authoritative native cell/region inspection; (b) exact bounded strokes/openings and clear operation receipts; (c) protected selections and explicit Empty cuts reconciled with regeneration; (d) shared meaningful edit history; (e) preview/revision checks when a human intervenes; (f) acknowledged pause, bounded steps and state observations; (g) authored starting setup distinguished from evolved runtime state. Keep creating a scene with existing materials separate from changing material physics.

## Decisions and next actions

- The current independent reviewer is best placed to continue **coding/review/integration**. Evidence curation belongs to a separate documentation branch; do not merge or modify the reviewer's feature branch to add these frames.
- The documentation owner may update this curated corpus if a claim is disproven, but must retain provenance, frame hashes and an append-only correction note explaining any changed interpretation. Do not mutate historical pixels.
- No external API key is needed by the verified GitHub-backed simulation bridge. The provider and usage of any future 24-hour, credit-limited key remain **undecided**, and no credential belongs in this research archive.
- Preserve these high-value frames and the constraint ledger in Git. The full source video remains a separately held reference, identified by hash and upload context, not a promised permanent repo asset.