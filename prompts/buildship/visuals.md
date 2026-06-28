# Build & Ship — Visual Production Prompt v1

**Single source of truth for shot-by-shot visual direction for Build & Ship videos.**

This prompt is consumed by the automated pipeline. Using the completed SCRIPT, generate per-scene
visual direction for an editor cutting a talking-head + b-roll commentary video.

> Retention is the spine of every visual rule below. This is a **builder-commentator** channel: the
> host's face and judgment are the product. Visuals exist to keep one builder watching one more
> sentence — to make a number land, to prove a claim is real, and to break the monotony of a static
> talking head. Never let the screen go flat for more than a few seconds.

---

## 0. How this file is used

1. Receive the completed SCRIPT for the topic.
2. Generate scene-by-scene visual directions following this prompt.
3. Return the full scene list + a shot-list summary table.

Do not output this prompt, the checklist, or production notes — only the scene list and shot-list
summary.

---

## 1. Channel visual identity

### 1.1 Footage ratio (golden rule)
This is a **talking-head-led** channel. The mix, across the whole video:
- **~50–60% talking head** — the host on camera, direct address. This is the spine, not the filler.
- **~20–25% source inserts / screen-capture** — the actual study, tweet, dashboard, code editor,
  news headline, chart being discussed. This is where the channel's "I actually checked" authority
  comes from. Show the real thing.
- **~15–25% graphics / kinetic text** — animated numbers, comparisons, the payoff line on screen.
- **Light, purposeful b-roll only** — never generic "developer typing in a dark room" wallpaper
  unless it genuinely fits. A few seconds, as illustration, never as a crutch.
- **0% AI-generated imagery** by default — the host built real things; fake footage undercuts the
  "measured, not vibed" credibility. Use only if the producer explicitly approves one sequence.

> Rule of thumb: when in doubt, cut back to the host's face. The parasocial trust is the moat. But
> never hold a *static* talking head longer than ~8–10 seconds without a cutaway, overlay, or
> reframe — that's where viewers drop.

### 1.2 Visual modes

Reference these by name throughout the scene list:

| Mode | Description |
|------|-------------|
| **Mode A** | **Talking head** — host on camera, direct address. The default for hooks, POV lines, reframes, CTAs. |
| **Mode B** | **Talking head + overlay** — host on camera with a lower-third or floating graphic beside them (a number, a name, a source citation). |
| **Mode C** | **Full-screen graphic** — animated chart, stat reveal, or comparison table. Narration over it. |
| **Mode D** | **Source insert / b-roll** — screen-capture of the real artifact (study PDF, tweet, dashboard, code, headline) or light illustrative b-roll, over narration. |
| **Mode E** | **Kinetic text** — one bold line or number animating on screen. For the hook number, the payoff line, and comment beats. Punctuation, not wallpaper. |
| **Mode F** | **Split-screen contrast** — two panels making a contradiction visible (feel vs clock, 65% vs 40%, with-axis vs no-axis). The channel's "make the gap visible" device. |

**Mode F** is the signature device for this channel's contradiction-driven takes. Use it on the core
tension of the video — the two-number gap, the two camps, the before/after.

**Mode E** drives comments and shares. Use it only on lines the viewer should *feel* — the payoff,
a punch number, a comment beat. Overuse kills it.

---

## 2. Task

Using the SCRIPT provided, create detailed visual directions for every scene in: **$topic**

Videos run **~8–12 minutes** (~165 wpm English delivery on ~1,500–2,000 word scripts). Plan scene
count and shot durations to fill the runtime without padding. Expect roughly **20–30 scenes**.

---

## 3. Output format — per scene

For each scene:

```
SCENE [NUMBER] — [TIMESTAMP] — [SCENE TYPE] — [MODE]

VISUAL: [What's on screen — specific, not vague]
AUDIO: [Exact quote from the script for this moment]
SOURCE/B-ROLL: [If Mode D: exact artifact to screen-capture (URL/source) OR stock b-roll description + 3 search terms for Pexels / Storyblocks / Envato. If none: "N/A — talking head"]
GRAPHICS: [Text overlays, charts, kinetic text — exact text + animation style]
DURATION: [Estimated seconds]
NOTES: [Editor instructions — pacing, emphasis, thumbnail flag]
```

---

## 4. Scene types

- **TALKING HEAD** — host on camera (Mode A / B)
- **SOURCE INSERT** — screen-capture of the real study, tweet, dashboard, headline, code (Mode D)
- **B-ROLL** — illustrative supporting footage over narration (Mode D)
- **GRAPHIC** — full-screen chart / stat / table (Mode C)
- **KINETIC TEXT** — animated line or number on screen (Mode E)
- **SPLIT SCREEN** — two-panel contrast (Mode F)

---

## 5. Visual direction standards

### Talking head (Mode A / B)
- Vary the framing across the video so it never feels static: alternate between a **medium** (chest-up,
  the default), a **close-up** (for the punch lines and the payoff), and a **wide / B-cam angle** (for
  the steelman or a tonal shift). Note the framing in VISUAL.
- Use a **B-cam jump-cut** or a small push-in on the most important lines, so the talking head itself
  carries energy.
- Mode B floats the number/name beside the host the moment the ear hears it.

### Source inserts (Mode D) — the credibility engine
- When the script names a study, a stat, a tweet, a company, a dashboard — **show the real artifact.**
  Specify exactly what to capture (e.g., "the METR paper title page + the figure showing −19%",
  "the actual Indie Hackers thread", "a redacted MRR screenshot with no axis").
- Highlight/annotate the specific number on screen (circle, underline, color pop) so the eye lands
  where the ear is.
- Keep inserts short — 3–6 seconds — then cut back to the host or a graphic.

### Graphics (Mode C)
- Specify chart type (bar, line, comparison table) and the exact numbers.
- Color scheme: **green = the good/measured outcome, red = the bad/illusion outcome, neutral = blue/grey.**
- Animate the number counting up or the bar growing — motion holds attention.
- Source attribution in small text, bottom corner.

### Kinetic text (Mode E)
- Include the **exact text**, font weight (bold headline vs body), and animation (fade, slide-up, pop,
  typewriter).
- Hold 2–3 seconds after the animation completes, then clear before the next scene.
- Reserve for the hook number, the payoff line, and the two comment beats.

### Split-screen contrast (Mode F)
- Define the **left panel** and **right panel** explicitly (e.g., left = "FELT: +20% faster" / right =
  "REAL: −19% slower"). Label each panel, bold, fade in.
- Use on the video's core contradiction and at Comment Beat 1 when it's a two-camp question.

---

## 6. Beat-by-beat visual strategy

The SCRIPT follows the five-beat structure from the script prompt. Map visuals to it.

### Beat 1 — Cold-open hook (0:00–~0:30)
**Goal:** stop the scroll in the first 3–10 seconds.
- **Open on the host (Mode A), OR open on a Mode E kinetic stat** if the hook leads with a number —
  whichever hits harder. No channel card, no logo sting, no "intro."
- Hard cuts only, fast energy. If the hook has a number (e.g., "19% slower"), punch it as Mode E or a
  Mode F split the instant it's said.
- **Withhold the resolution** — show the contradiction, not the answer. The main loop is the curiosity.
- Flag a **THUMBNAIL CANDIDATE** here — the hook number or the host's expression on the hook line.

### Beat 2 — Stakes / why-you-should-care (~0:30–1:30)
**Goal:** make it personal; establish the host actually lived this.
- Mostly Mode A (host on camera) — this is a trust beat, the face sells it.
- On the credibility line ("I've shipped this mistake myself"), consider a 2–3s Mode D b-roll cutaway
  that illustrates the lived experience, then back to the host.
- Mode B lower-third for any concrete number introduced.

### Beat 3 — The evidence / the argument (~1:30–7:00)
**Goal:** information density without going flat. Visuals carry the proof.
- This is the **Mode D + Mode C** zone: show the study, the screenshot, the dashboard; build the chart.
- **Source-insert every named study/stat/company** the moment it's spoken (credibility engine).
- **Anti-flat rule:** never hold one mode >8–10 seconds. Rotate host ↔ insert ↔ graphic.
- Build the **core contrast as Mode F** when the key two-number gap lands (e.g., 65% vs 40%, predicted
  vs actual).
- **Steelman moment:** shift the talking-head framing (B-cam / wider) so the viewer *feels* the host
  switching to "the other side's strongest case," then cut back to the main angle on the turn.
- **The "it's worse than that" escalation:** punch it with a Mode E line or a sharp Mode D reveal.

### Mid-video re-hook (~50%)
- On the re-hook line, cut to a **clean Mode A close-up** (or Mode E question) that re-opens curiosity.
  A visual reset at the halfway cliff.

### Beat 4 — The reframe / what to do (~7:00–9:30)
**Goal:** deliver the payoff and make it usable.
- **Payoff line = Mode E kinetic text**, full force (e.g., "Feeling fast ≠ being fast"). This is the
  most-clipped moment — make it clean and screenshot-able. Flag **THUMBNAIL CANDIDATE**.
- The rule/model = **Mode C** — number the steps on screen as the host says them ("1. Time it.
  2. Tutor, not ghostwriter.") so it's save-able.
- **Comment Beat 1 (declare your side, ~75–80%):** put the two camps on screen — **Mode F split** (the
  two options) or **Mode E** with the two labels animating in. 2–3s, animated entry. A visible binary
  lifts reply rate — people type the side they can see.

### Beat 5 — Persona close + series promise + CTA (~9:30–end)
**Goal:** brand continuity + maximum comment launch.
- **Persona note** = Mode A close-up, host direct to camera. The "measured, not vibed" line is the
  brand brick — let the face carry it, no distractions.
- **Series promise / next-angle tease:** 2–3 quick Mode D cuts previewing the next topic (1.5–2s each).
- **Comment Beat 2 (crowdsource/rivalry):** put the question on screen as **Mode E kinetic text**,
  placed immediately **before** the final beat. This is the last text before the comment box — clean,
  readable.
- **Internal-link callout:** only if the script includes a "watch next" tease — a subtle **Mode B
  lower-third** with the linked title, or an endscreen card. Never a full-screen "watch now" overlay
  before the 60% payoff.
- **Final hold:** end on a confident Mode A close-up of the host (or a clean Mode E channel tag).
  2–4s. The face is the closer on a personal-brand channel.

---

## 7. Retention pacing reference

| Segment | Pacing | Cut style |
|---------|--------|-----------|
| Hook (0:00–0:30) | 2–3 s per shot | Hard cuts only |
| Beat 2 (stakes) | 3–5 s per shot | Hard cuts, host-led |
| Beat 3 (evidence) | 4–8 s per shot | Rotate host ↔ insert ↔ graphic; never >10s static |
| Mode C graphics | 5–8 s | Animate, then cut |
| Source inserts (Mode D) | 3–6 s | Quick, annotated, cut back |
| Payoff (Mode E) | 2–3 s | Animated entry, hold, clear |
| Comment Beat 1 (Mode F / E) | 2–3 s | Animated entry, quick hold |
| Series tease | 1.5–2 s per shot | Fast cuts |
| Comment Beat 2 (Mode E) | 2–3 s | Animated entry, hold, clear |
| Final hold | 2–4 s | — |

---

## 8. Loop management — visuals

The script's open loops are the retention engine. Visuals must support them, not spoil them.
- **While a loop is open:** keep the resolving graphic/number off screen. Tease, don't reveal.
- **At loop payoff:** bring the Mode E / Mode F reveal in at full force — the visual lands with the line.
- **Never flash forward:** don't show the Beat 4 payoff graphic during Beat 3.

---

## 9. Thumbnail harvest

Flag **2–3 candidate thumbnail frames** in NOTES, where:
- A punch number reads big and clean as a static image (e.g., "−19%", "65% vs 40%").
- The host's expression on the hook or payoff line is high-contrast and clickable.
- A Mode F split reads instantly as a contradiction.

Flag as: `THUMBNAIL CANDIDATE — [reason]`

---

## 10. Shot list summary

End with a condensed table:

| Scene # | Timestamp | Type | Mode | Primary Visual | Source/B-Roll Needed | Custom Graphic |
|---------|-----------|------|------|----------------|----------------------|----------------|
| … | … | … | … | … | Yes / No | Yes / No |

---

## 11. Pre-output checklist — INTERNAL, DO NOT OUTPUT

**Retention**
- [ ] Opens on host or hook stat — no logo sting, no intro card
- [ ] Hook pacing 2–3 s/shot, hard cuts; hook number punched (Mode E/F) if present
- [ ] No static talking head held >8–10 s without cutaway/overlay/reframe
- [ ] Beat 3 rotates host ↔ source insert ↔ graphic; no mode held >10 s
- [ ] Mid-video re-hook scene present (~50%)
- [ ] Payoff graphic/number not shown before its Beat 4 reveal

**Visual identity**
- [ ] Footage mix roughly 50–60% talking head, 0% AI (unless producer-approved)
- [ ] Every named study/stat/company gets a real source insert (Mode D)
- [ ] Mode F used on the core contradiction
- [ ] Mode E reserved for hook number, payoff line, comment beats

**Engagement**
- [ ] Comment Beat 1 (declare your side) gets a Mode F split or two-label Mode E in Beat 4
- [ ] Comment Beat 2 (crowdsource/rivalry) gets Mode E text in Beat 5, just before the final hold
- [ ] Persona note delivered as a clean Mode A close-up

**Internal linking**
- [ ] Any pre-60% video reference is a subtle Mode B lower-third — never a "watch now" overlay
- [ ] Explicit "watch next" visual lives in Beat 5 / endscreen only

**Completeness**
- [ ] 2–3 thumbnail candidates flagged in NOTES
- [ ] Shot list summary table completed
