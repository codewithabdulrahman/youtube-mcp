# ContrasteYT — Visual Production Prompt v3

**Single source of truth for shot-by-shot visual direction for ContrasteYT videos.**

This prompt is consumed by the automated pipeline. Using the completed script (GUION), generate per-scene visual direction for an editor assembling footage, graphics, animations, and overlays.

> Retention is the spine of every visual rule below. CTR is strong (~6.35%); average percentage viewed (~35%) is the growth bottleneck. Every visual choice exists to keep one viewer watching one more sentence — or to prime a comment that brings them back.

---

## 0. How this file is used

1. Receive the completed GUION for the topic.
2. Generate scene-by-scene visual directions following this prompt.
3. Return the full scene list + shot list summary table.

Do not output this prompt, the checklist, or production notes — only the scene list and shot list summary.

---

## 1. Channel Visual Identity

### 1.1 Footage Ratio (Golden Rule)
- **75–80% real footage** — archival, documentary, on-location
- **20–25% graphics / text overlays** — data, maps, Mode E text beats
- **0% AI-generated imagery** (default) — unless the producer explicitly approves a single AI sequence for a specific creative reason

Real footage = authenticity. ContrasteYT's authority is built on showing real places, real construction, real streets. AI imagery undercuts that.

### 1.2 Visual Modes

The channel uses five display modes. Reference them by name throughout the scene list:

| Mode | Description |
|------|-------------|
| **Mode A** | Full-frame B-roll — real footage, narration over it |
| **Mode B** | B-roll + lower-third text (statistic, proper noun, date) |
| **Mode C** | Full-screen graphic — chart, map, or comparison table |
| **Mode D** | Split-frame — left = US version, right = LATAM version (the channel's signature contrast device) |
| **Mode E** | Animated text over real footage — key phrase, question, or comment beat |

Mode D is the channel's **signature engagement device** — it makes the contrast visible. Use it deliberately: at Act 3's structural reveal, at Act 4's paradox launch, and at Comment Beat 1.

Mode E drives comment and share behavior. Use it only on lines the viewer should *feel*, not just hear — a key paradox, a comment beat, a reframe. Use sparingly so it lands with force when it appears.

---

## 2. Task

Using the script provided, create detailed visual directions for every scene in: **$topic**

Videos run **12–14 minutes** (~155 wpm Spanish TTS on 1,900–2,200 word scripts). Plan your scene count and shot durations to fill that runtime without padding.

---

## 3. Output Format — Per Scene

For each scene:

```
SCENE [NUMBER] — [TIMESTAMP] — [SCENE TYPE] — [MODE]

VISUAL: [What appears on screen — specific, not vague]
AUDIO: [Exact quote from script for this moment]
B-ROLL: [Stock footage description + 3 search terms for Pexels / Storyblocks / Envato]
GRAPHICS: [Text overlays, charts, animations — include exact text and animation style]
DURATION: [Estimated seconds]
NOTES: [Special instructions for the editor]
```

---

## 4. Scene Types

- **TALKING HEAD** — Presenter on camera
- **B-ROLL** — Supporting footage over narration (Mode A or B)
- **SCREEN RECORD** — Software or website demonstration
- **ANIMATION** — Animated graphics or explainer (Mode C)
- **TEXT ON SCREEN** — Animated text over footage (Mode E)
- **MAP** — Geographic visualization (Mode C variant)
- **CHART** — Data visualization (Mode C variant)
- **SPLIT SCREEN** — US vs. LATAM contrast (Mode D)

---

## 5. Visual Direction Standards

### For B-Roll (Mode A / Mode B)
- Always provide 3 alternative search terms (Pexels, Storyblocks, Envato)
- Specify: wide shot / medium shot / close-up
- Specify mood: professional, urgent, hopeful, cautionary, warm, contemplative
- Avoid generic office stock footage unless it perfectly fits
- Prefer footage that contains the **physical anchor object** from the script — show it, don't abstract it

### For Mode D (Split-Frame)
- Left panel = US version; right panel = LATAM version
- Each panel needs its own B-roll search term
- Specify whether labels appear (e.g., "ESTADOS UNIDOS" / "LATINOAMÉRICA") — always bold, fade in
- Preferred for any binary-choice moment — especially Comment Beat 1 (Section 7)

### For Mode E (Animated Text on Footage)
- Specify font weight: bold headline vs. body weight
- Specify animation: fade in, slide up, pop, typewriter
- Include the **exact text** to display
- 2–3 seconds hold after animation completes, then clear before the next scene
- Use sparingly: Mode E is punctuation, not wallpaper

### For Mode C (Charts / Maps / Tables)
- Specify chart type: bar, line, pie, comparison table
- Include exact numbers to display
- Color scheme: green = positive, red = negative, blue = neutral
- Source attribution in small text, bottom-right
- For maps: specify geographic scope (US national / LATAM regional / specific country), what to highlight or animate, labels required

---

## 6. Act-by-Act Visual Strategy

### Act 1 — Hook (0:00–~0:45) · ~70–90 script words

**Goal:** Snap attention in 5–12 seconds. No warmup.

- **First frame:** the physical anchor object — no titles, no channel card, no abstract opener
- **Pacing:** 2–3 seconds per shot, hard cuts only, no dissolves
- **Mode:** A or B — real footage only in the hook; no Mode E until the main loop is open
- **Withhold the answer:** show the object in its US context; cut before revealing the contrast. The viewer's curiosity is the loop.
- Do NOT show the LATAM counterpart here — that is Act 4's payoff

### Act 2 — Stakes (~0:45–1:30) · ~120–150 script words

**Goal:** Make the contrast personal. Earn the viewer's commitment.

- 3–4 second shots; slightly slower than the hook
- Mode B (lower-thirds) for any concrete statistic introduced
- One emotional close-up on the anchor object — something tactile the viewer can project onto
- No text-heavy scenes yet; let narration carry stakes, visuals support mood

### Act 3 — History / Mechanism (~1:30–7:30) · ~900–1,050 script words

**Goal:** Depth without drag. Visuals carry the information density.

- Alternate B-roll shot types every 4–6 seconds to prevent fatigue
- Mode B for every date, statistic, and proper noun introduced (lower-third confirms what the ear hears)
- Mode C for any multi-variable comparison or timeline (chart / map)
- **Anti-dump rule** mirrors the script: never hold a graphic for more than 10 seconds without cutting to B-roll
- At least one Mode D (split-frame) in Act 3 — make the structural contrast visible
- **Loop visual:** at each micro-loop payoff, use a close-up of the anchor object to re-anchor. When a loop re-opens, pull back to a wider shot — visually signals "more to come"

### Act 4 — LATAM Validation + Paradox (~7:30–10:00)

**Goal:** Pride, not envy. The tour of Latin America.

- Open Act 4 with a Mode D split-frame — US problem left / LATAM solution right — to launch the paradox frame
- **Country tour:** each country mentioned in the script gets its own B-roll moment. 5+ countries = 5+ distinct visual moments. Each country should feel visually different — no blurred stock-footage montage
- Mood shift: warmer color palette if the editor has color-grade control (amber / warm vs. the cooler institutional blue of Act 3's US footage)
- **Comment Beat 1 — declare your team (~80% mark):**

  When the script hits Beat 1, give it a **two-option on-screen treatment**. Best option: a **Mode D split-frame** — left = the US thing, right = the LATAM thing — so the screen literally shows the two camps the viewer is being asked to pick between. The channel's signature device doubles as the engagement punch. Alternative: **Mode E with two labels animating in** (the two choices as text). Either way: 2–3 seconds, animated entry. This is a deliberate **engagement beat**, not a warmth hold — a visible binary choice on screen lifts the reply rate, because people type the side they can see.

### Act 5 — Reframe + Series Promise + CTA (~10:00–end)

**Goal:** Emotional close, series continuity, and maximum comment launch.

- **Circle-back echo:** return to the same anchor object from Act 1 — same framing if possible. The visual rhyme signals resolution.
- **Series-promise montage / next-episode tease:** quick cuts previewing the next video's object — 3–5 shots, 1.5–2 seconds each. Fast, curious.

  **SERIES MONTAGE DOUBLES AS RIVALRY PRIMER:** if Beat 2 uses the rivalry variant ("¿qué país construye mejor?"), build the series-promise montage from quick real footage across 4–5 countries (Mexico, Colombia, Argentina, Peru, Chile) — so by the time the question lands, the viewer has already seen "their" country on screen and is primed to defend it.

- **Internal-link callout visual** (if the script includes a "watch next" soft tease per the script's Section 7): use a subtle Mode B lower-third for the linked video title — never a full-screen card mid-scene. The explicit endscreen callout lives in the endscreen itself, not in the narration scenes. The "watch next" overlay belongs in Act 5 only — never before the 60% payoff.

- **Comment Beat 2 — rivalry / crowdsource (right before the CTA):**

  On the rivalry/crowdsource line, put the question on screen as **Mode E animated text over real footage** — "¿Qué país construye mejor?" or "¿Qué otra cosa no te cuadra?". 2–3 seconds. This is the last text the viewer sees before the comment box, so it must be clean and readable. Place it immediately **BEFORE** the final silent hold.

- **Final silent hold — the closer:**

  The no-text silent hold is the **very last beat only**. Beat 2's Mode E comment question lands just BEFORE it and clears off screen before the silent image begins. **Order is: series montage / rivalry primer → Beat 2 question (Mode E text) → final silent beautiful hold (no text).** Never let the no-text rule cancel the comment question — that question is the highest-value engagement asset in the back half.

  Hold on **one real, beautiful image** tied to the video's emotional truth. No text. No overlay. 8–10 seconds. Let the narration carry it. The silence after the comment question gives the viewer space to act.

---

## 7. Retention Pacing Reference

| Segment | Pacing | Cut Style |
|---------|--------|-----------|
| Hook (0:00–0:30) | 2–3 seconds per shot | Hard cuts only |
| Act 2 | 3–4 seconds per shot | Hard cuts, occasional match cut |
| Act 3 body | 4–6 seconds per shot | Varies by mode |
| Mode C graphics | 6–10 seconds | Hold, then cut to B-roll |
| Act 4 country tour | 3–4 seconds per country | Rapid but purposeful |
| Comment Beat 1 (Mode D / Mode E) | 2–3 seconds | Animated entry, quick hold, clear |
| Act 5 series montage | 1.5–2 seconds per shot | Fast cuts |
| Comment Beat 2 (Mode E) | 2–3 seconds | Animated entry, hold, clear |
| Final silent hold | 8–10 seconds | — |

---

## 8. Loop Management — Visuals

The script's open loops are the retention engine. Visuals must support them, not spoil them.

- **While a loop is open:** wide or medium shots, incomplete compositions, footage that implies "there's more to see." Never show the full answer before the script's reveal.
- **At loop payoff:** close-up on the anchor object, warm hold, slower cut pace signals resolution.
- **Never flash forward:** do not pull B-roll from Act 4 or Act 5 into earlier acts — the editor must not accidentally "answer" the loop with early footage.

---

## 9. Thumbnail Harvest

During the scene list, flag **2–3 candidate thumbnail frames** — moments where:
- The contrast is maximally visible (a Mode D split that reads well as a static image)
- The hook object is front-and-center, close-up, high contrast
- A visual expression or composition beats the thumbnail competition in the same search category

Flag them in NOTES as: `THUMBNAIL CANDIDATE — [reason]`

---

## 10. Shot List Summary

End the output with a condensed table:

| Scene # | Timestamp | Type | Mode | Primary Visual | B-Roll Needed | Custom Graphic |
|---------|-----------|------|------|----------------|---------------|----------------|
| … | … | … | … | … | Yes / No | Yes / No |

---

## 11. Pre-Output Checklist — INTERNAL, DO NOT OUTPUT

**Retention**
- [ ] First frame is the physical anchor object — no titles, no warmup
- [ ] Hook pacing: 2–3 seconds per shot, hard cuts only
- [ ] LATAM solution NOT shown before Act 4
- [ ] No B-roll accidentally answers an open loop ahead of the script's reveal
- [ ] Act 3 graphics hold ≤10 seconds before cutting back to B-roll
- [ ] Mid-video re-hook scene present (~50% mark)

**Visual identity**
- [ ] Footage ratio: 75–80% real, 0% AI (unless producer-approved)
- [ ] Mode D used at least once in Act 3 and once at the Act 4 paradox launch
- [ ] Mode E used sparingly — only on lines the viewer must feel

**Engagement**
- [ ] Beat 1 (declare-your-team) gets a two-option visual in Act 4 — Mode D split-frame preferred, or two-label Mode E
- [ ] Beat 2 (rivalry/crowdsource) gets a Mode E text reinforcement in Act 5, placed BEFORE the final silent hold — never suppressed by it
- [ ] If Beat 2 uses the rivalry variant, the series montage cues 4+ countries as a rivalry primer
- [ ] Final silent hold is the very last beat — Beat 2 Mode E clears before it begins

**Internal linking**
- [ ] If the script references an older video before 60%, use a subtle Mode B lower-third — never a "watch now" overlay in the open-loop stretch
- [ ] The explicit "watch next" callout visual lives in Act 5 / endscreen only

**Completeness**
- [ ] 2–3 thumbnail candidates flagged in NOTES
- [ ] Shot list summary table completed
