# THE MOTH-LIGHT OBSERVATORY — Round 2A Art Journal

**Selected final world:** `experiments/round2-open/final.session.json` (same bounded command score as `sessions/active.json`)
**Executed source commit:** `12a5801e8a9b3bb44613fb0910837f1ba886bf6f`
**Executed checkout tree:** `a134abbea7d52750e2ef8f4458bbf7b4c4a7bb93`
**Compiled browser bundle SHA-256:** `b51e0e59584f21f9cf34833436cbb2de98e014bb1e614c37053a303c1d7949ec`
**Branch:** `agent/experiments/round2-open`; **no merge**.
**Native physics:** unchanged. The authoring harness and continuous recorder were copied from provisional PR #5 onto this isolated artistic experiment branch; no modifications to that agent's branch.
**Replay limits:** Sandspiel cells-only export does not reproduce native RNG/wind/fluid; reruns can vary.

## Concept and composition

An abandoned stone observatory encloses a fractured, crystalline eclipse ring. A woody seed-heart hangs in its center; green hanging gardens and mauve fungal shelves colonize opposing towers. Beneath it sits a half-ruined water reliquary, fed by a tiny surviving spring. The scene uses **negative sky space** above the structure and an intentionally constrained palette: charcoal Wall, umber Wood, cyan Ice/Water, green Plant, soft-pink Fungus, and warm Sand/Seed.

The center ring and botanical heart are the principal focal points. The outer ruins frame the picture but remain deliberately incomplete to suggest ancient damage. Simulation time contributes drooping foliage, germinated seedlings, a flowing basin, and a sustaining water trickle.

## Observed attempt history (replayable JSON and unmodified original capture preserved)

| Attempt | Executed SHA | Action run | Result | Actual decoded video |
| --- | --- | --- | --- | --- |
| v1, architectural prototype | `d00390703c32b817418a7492c29968cbf098100c` | [42396235771](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42396235771) | Native commands 70/70 and 460/460 ticks; post-run verification failed because Chromium WebM lacks `format.duration` | 591 frames / 81.411 s / 7.247 FPS |
| v2, seeded terraces and living chandelier | `21c4a6bd45a7f548beb62d1c2801e3e8003b8562` | [42397093629](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42397093629) | Actions **SUCCESS**; 89/89 commands, 460 live ticks, no page errors | 587 frames / 60.831 s / 9.633 FPS |
| **v3, selected living spring** | **`12a5801e8a9b3bb44613fb0910837f1ba886bf6f`** | **[42397653399](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42397653399)** | **Actions SUCCESS**; **90/90 commands**, **460 live ticks**, no page errors | **607 frames / 59.581 s / 10.171 FPS** |

Significant full-process original video and screenshots are retained in each run's evidence archive. GH Actions evidence retention is finite; download the ZIPs before they expire. Final v3 artifact: [sandspiel-agent-session-42397653399](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42397653399/artifacts/13584237254). V2 artifact: [13584176600](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42397093629/artifacts/13584176600). V1 artifact: [13583428819](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42396235771/artifacts/13583428819).

### Actual construction → native evolution → observed adaptation

1. **v1 prototype:** Carved the twin broken monoliths, incomplete orbit, inner seed cage and pool. Executed actual native intervals **0→110**, **110→240**, **240→370**, **370→460**, interspersed with live-bounded edits. Visually inspected the original screenshots and continuous WebM. The composition had good visual hierarchy, but the center appeared too isolated, the shallow pool too static, and two attempted native material placements produced no changed cells. No image improvements were assumed without inspection.
2. **v2 after v1 observation:** Removed the failed seed-in-occupied-foliage placement and relocated obstructed greenery. Added paired hanging vines inside the orbit, four ground seeds supported by moist Sand terraces, cyan ornaments and a short descending water stroke. Native growth produced visible pink flowering stalks on both banks and fuller descending greenery. In parallel fixed the video verifier by calculating duration from genuine decoded frame timestamps (Chromium MediaRecorder frequently omits WebM `format.duration`). All gates passed. Final basin visible, but the waterfall only persisted briefly.
3. **v3 after v2 observation:** Removed two isolated sky glints that read as accidental pixels. Added **one native Cloner cell at (149,229)** and seeded its adjacent cell with **Water at (148,229)** after the first evolution, retaining all four independent live intervals. Native final cell state at (149,229) was `[5,200,3,222]`: species **5=Cloner**, parameter `rb=3` identifies learned **Water**. A thin recurring droplet column now appears between the orbit and lower pool without obscuring the seed-heart. Final native water census: **952 Water cells**, including **926** in the x=100–199, y=249–284 basin-region window. Its original video shows the living spring and the whole authoring progression. Retained the successful v2 variant as fallback.

These are real visual observations and native receipts. The scenario uses its allotted **90 bounded authoring operations**, including four actual render-loop `resume` intervals totaling 460 ticks; no screenshots were substituted for frame-by-frame construction capture.

## Final native material inventory (300×300 = 90,000 cells)

| Species | Cells |
| --- | ---: |
| Empty | 63,984 |
| Wall | 14,438 |
| Wood | 2,727 |
| Plant | 5,136 |
| Fungus | 1,880 |
| Ice | 583 |
| Water | 952 |
| Sand | 203 |
| Seed | 96 |
| Cloner | 1 |

Read from v3 final `cells-only.json` (cell-major WASM representation). This is a material snapshot, **not** a full RNG/fluid/native checkpoint.

## Event log: visible / inferred / unobserved

- **E1: First shower and plant evolution, ticks 0–110.** Native render-loop ticks acknowledged; initial Ice crescent stayed structurally stable; water shifted in the upper orbit and the basin. Visible in video and 055-resume.png.
- **E2: Root elongation and terraced growth, ticks 110–240.** Paused painting introduced new living roots, moisture and the v3 one-cell source. The final cell's `rb=3` establishes the native generator learned Water. Later footage shows small blue droplets below the ring. Native counts are measured; the exact per-tick production rate was not measured.
- **E3: Fungal and leaf continuation, ticks 240–370.** Hanging foliage became fuller, with filament-like undersides; seedlings developed visible flower stalks on terrace edges. Visually inspected in video and 079-resume.png.
- **E4: Final stabilization, ticks 370–460.** The source remained one Cloner cell and the floor pool retained Water; a narrow droplet trace continued above the pool. Final screenshot and v3 native census confirm the observed state. No structural collapse or destructive ignition was observed.
- **Failed placement discovery:** In v1, the planned central `Seed` placement had 0 changed cells (blocked by occupied Plant); it was removed in v2. Another right-side Plant stamp also had 0 changed cells and was relocated.

## Recording qualification

The v3 `recording.webm` comes directly from Chromium's real `sand-canvas.captureStream`/MediaRecorder. Independent ffprobe confirmation: **607 decoded VP9 frames**, source dimension **300×300**, **59.581 s** and **10.171 observed FPS** (not merely a nominal FPS label). Source SHA-256: `0f5bb963b8688ab49cbcd78320673319b856800e969c1c107a506c08e8b1aca5`. The native JS/Playwright ledger proves 90 commands and four separately acknowledged live intervals. The repository recording-integrity script passed; a separate independent pixel-change audit found **17** painting operations with multiple significantly different intermediate frames. The MP4 is a derived compatibility transcode; **the WebM is authoritative** for frame-level acceptance.

## Candid artistic critique and stopping decision

**Successful:** Strong identifiable silhouette with a breathing upper void; recurring annular eye motif and a genuinely living botanical center; asymmetric wood/fungus detail; stable stone framing contrasted with moving water; evolved terrace flowers; subtle but sustained source-fed trickle in v3. This result is significantly stronger than the original v1 without sacrificing composition.

**Limitations:** The pale default Sandspiel backdrop, fixed 300×300 native raster, and its preset materials prevent bespoke lighting or painterly colours without modifying the simulation. The trickle is intentionally thin and reads better in motion than in a still. Some free Sand at the bottom falls toward the boundary and is visually secondary. Reruns are not deterministic because cells-only export excludes native RNG, fluid, wind and burn buffers. v2/v3 differences should not all be attributed to changed commands because the native RNG also varies.

**Stop rationale:** After three visually inspected complete attempts and repeated four-interval native evolution, the remaining changes would chiefly introduce ornamental clutter or risk uncontrolled spread, rather than improve the focal composition. Selected **v3** rather than adding a risky fire, acid, or high-volume generator. Neither `master` nor other agents' branches were modified.

## Reproduction and source authority

The JSON is a bounded versioned `sandspiel-lab-session/v1` command score. To replay the selected score on a compatible checkout, use `sessions/active.json` and `.github/workflows/session-run.yml` on the dedicated branch, or use the equivalent `experiments/round2-open/final.session.json`; local build/runner instructions are in `AGENT_LAB.md`. Because this is stochastic art, compare qualitative behaviours and native receipts, not exact bytes across fresh executions.

The experimental recording adapter was transferred to this branch from draft PR #5 and validated by actual independent execution; its presence on this artistic branch is **not** a claim that PR #5 has merged into `master`.
