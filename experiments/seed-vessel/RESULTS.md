# Experiment 01 — The Hollow Germination Shrine

**Mode:** Source-informed independent artistic construction in real Sandspiel; **not** an engine port of a CyberSand design pack. **Do not merge this experiment by default.**

## Source selection and artistic transformation

Reference: [CyberSand PR #454](https://github.com/techrote/cybersand/pull/454), [Ashroot Nursery](https://github.com/techrote/cybersand/blob/c4aab63eed538a25687c66d368b0801d2d2e04d0/docs/world-design/ashroot-nursery/README.md), specifically its alternate **The Hollow Seed Vessel** (`ashroot-descending-seed-ossuary-02`). Reviewed source description and design notes at PR head `c4aab63eed538a25687c66d368b0801d2d2e04d0`. This is an **inspiration based on source documentation**, not a pixel-accurate replica of the 960×390 flat SVG or an assessment of its inaccessible Godot lighting.

Reinterpret the broken ceiling, unequal fossil-root support, suspended annular seed witness, lower archaeological chambers and cultivation walkway as one 300×300 Sandspiel scene. Use existing **Sandspiel** Wall/Stone/Wood/Ice/Sand/Plant/Fungus/Seed/Water/Dust. No new material physics, shader lighting, actual mechanical function or native CyberSand importer is claimed.

The parallel blind implementer received an equivalent **text-only artistic brief**, without the source name, PR link, preview or geometry. The blind branch is `agent/experiments/seed-vessel-blind` and shares independent baseline `7bb2e997fd2f9cd05f08d0a13aa4e23a28da724e`. The informed branch must not inspect or modify the blind branch during its construction; compare only after both complete.

## Real browser results

| Session | Exact branch commit / real Actions run | Accepted commands | Native simulation steps | Result |
| --- | --- | --- | --- | --- |
| V1, first composition | `224c759e621dff8fb87b0e81c7b27ac7463cc1c4` — [42389639730](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42389639730) | 88/88 | 480 | PASS; `page_errors=[]`, [browser/cell/video artifact 13580604370](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42389639730/artifacts/13580604370) |
| V2, observational revision | `8fd1473cbef901a9ede107189c611a458d682a5f` — [42390347534](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42390347534) | 90/90 | 480 | PASS; `page_errors=[]`, [browser/cell/video artifact 13580384320](https://github.com/techrote/sandspiel-agent-lab/actions/runs/42390347534/artifacts/13580384320) |

V1 was found to be visually sparse despite a readable silhouette and correct functioning controller. V2 uses the same focal geometry but replaces ten low-value details with twelve meaningful geological/architectural/ecological edits: irregular strata, two broken lower chambers, engraved fragment traces, pale ring accents, sediment pockets and additional fungus/plant growth. This is a directly **observation-driven revision**, not a post-hoc artistic success claim.

Both sessions were born from the same blank starter logic. They are **separate actual WASM/Playwright runs**, not bit-identical rollbacks of a saved RNG/wind/GPU-fluid state. The runner's cells-only checkpoint is expressly incomplete for exact continuity.

## Event and visual observation ledger — V2

All `t=` entries below are the **native `step` count within the recorded Sandspiel run**; they are not recording wall-clock time. Sample frames are in the published GitHub Actions evidence ZIP, with file names keyed to command indices.

| Step / evidence frame | Observed and measured | Interpretation / uncertainty |
| --- | --- | --- |
| `t=0`, `082-inspect.png` | Intentionally fractured dark roof, two unequal root-bearing slopes, incomplete seed annulus with a wood/ice core, terraced walkways, two asymmetric undercroft niches, falling Water above open-topped right cistern, sparse Plant/Fungus | Authored construction visible; no simulation growth yet and no working machines claimed |
| `t=45`, `083-step.png` | Light pink particles emerge near root shoulders and a lower-west shelf. Water moves down toward basin. Small Sand deposits settle on ledges. | Material evolution consistent with actual Fungus/Water/Sand, but precise movement and reaction path between samples unobserved |
| `t=120`, `084-step.png` | More pink fungus around roots; Water visibly gathers at bottom of cistern; western and eastern living elements extend along structural edges | Native eastern region (95×100 cells) reports `Water=474`, `Wall=2820`, `Plant=67`, `Sand=67`; no global conservation or perfect seal claim |
| `t=240`, `086-step.png` | Cistern has settled into a shallow blue level; pink plume persists at roots and lower shelf; lower niches retain silhouette | No fire, explosion or major collapse. Stability is a sampled visual observation, not a permanence guarantee |
| `t=360`, `087-step.png` | Continued fungal presence and narrow green growth along roots; water remains in bowl | Change from t=240 is comparatively small; do not manufacture a dramatic event |
| `t=480`, `088-step.png` / `999-finish.png` | Central crown fungal region expands. V2 95×100 central region `Fungus 5→280`, `Plant 21→65`, `Ice 172→172`, `Wood 502→539`, `Stone 400→308`, `Wall 1169→1169`. Eastern region `Water=477`, `Wall=2820` | Fungus and Plant increase within the measured central region; Water changes by +3 cells within the sampled cistern region since t=120, **not** evidence of global creation or a spill. Material-count changes do not isolate individual reactions |

### Dramatic / interesting outcomes

1. **Biological emergence:** the small initial Fungus patches develop into noticeable pink plumes adjacent to the main roots and in the lower gallery. Central native inspection verifies an increase from 5 to 280 Fungus cells by t=480.
2. **Water settlement:** initially airborne Water falls into the constructed cistern and forms a visible shallow waterline by t=240; inspection still shows 477 Water cells within the same eastern sample at t=480.
3. **Quiet structural preservation:** the broken ring and two lower architectural recesses remain legible during the run despite biological growth. No sustained combustion, structural collapse or unexpected environmental cascade is supported.

**No spectacle was invented to improve the event report.** Neither pass demonstrated a destructive or genuinely novel physics interaction. The screenshots do not reveal unobserved actions between sample times; no private agent reasoning or source-game implementation is inferred.

## Artistic assessment

| Dimension | Qualitative assessment (V2) |
| --- | --- |
| Macro composition | **Stronger:** central suspended ring and opposing roots remain recognizable at full scene scale; large negative spaces are intentional |
| Meso detail | **Improved:** unequal undercroft chambers, weathered shelf edges, mineral strata and warm sediment pockets add history |
| Micro detail | **Still limited:** small registers and pale mineral accents are legible mostly in close inspection; actual art quality is far below a finished CyberSand shader capture |
| Colour / focal hierarchy | Brown roots, slate-grey Wall, pale Ice, faint pink fungal growth, green Plant and blue Water form separated accents; overall scene remains too pale and geometrically flat |
| Simulation use | Actual growth, sediment settling and cistern retention over 480 steps; no claim of physics mechanisms that were not measured |
| Narrative | A failed fossil nursery with a suspended seed witness, broken service terraces and abandoned water equipment is recognizable, but the fictional operation is not a working machine |

**Verdict:** Successful creative/engineering experiment with visible improvement on the second attempt. **Not** independently accepted as a higher-quality mockup than the CyberSand source; no actual Godot or comparable source-material rendering was produced. The current Sandspiel canvas lacks some of the richer fixed-material palette and rendering effects of CyberSand, and detailed artwork requires more tool-budget-efficient geometric primitives.

## Next comparison

Wait for the independent blind run on its isolated branch. Compare matching phase captures (authored t=0, at least two evolved states), effective native cell counts, artistic hierarchy and event reporting under the same command/step limits. Compare the informed concept against both the source schematic *and* the blind text-only interpretation, but don't confuse visual adherence with autonomous creativity. Do not merge experiment branches into product main without a separate decision.
