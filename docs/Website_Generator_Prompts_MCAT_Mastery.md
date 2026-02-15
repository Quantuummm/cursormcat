# MCAT Mastery — Website Generator Prompt Pack

Use these prompts directly in your website/UI generator. They are written to produce a cohesive app experience from landing page through mission gameplay.

---

## 0) Master Direction Prompt (Use First)

**Prompt:**
Build a production-ready web app UI called **MCAT Mastery** with this tone: **Stardew Valley coziness × Duolingo addictive clarity × Clash Royale cartoon boldness**. The app fantasy is: **a Commander reclaims 7 corrupted planets by answering MCAT questions**. The antagonist is **Grimble** (dramatic, theatrical, plushie-villain), and the AI companion is **LYRA** (warm, calm, never shaming).

Design for **ADHD-first learning**: short sessions, instant feedback, clear progress, warm and non-punishing copy. Use **mobile-first responsive layout**, smooth transitions, highly readable hierarchy, and very clear call-to-action buttons.

### Required brand / design system
- Dark mode default, light mode optional.
- Font style: rounded, friendly, bold headings, clean body text.
- Shape language: rounded cards, pill buttons, soft glows, subtle depth.
- Keep side clutter minimal. Center the core gameplay.
- Add subtle ambient motion in background (star shimmer, drifting particles).
- Accessibility: high contrast, large touch targets, visible focus states, readable text.

### Color palette (use exactly)
- Background: `#0A0E17`
- Surface: `#111827`
- Elevated Surface: `#1F2937`
- Border: `#374151`
- Primary Text: `#F9FAFB`
- Secondary Text: `#9CA3AF`
- Accent Primary (UI actions): `#3B82F6`
- Success: `#10B981`
- Warning/Currency: `#F59E0B`
- Danger/Error: `#EF4444`
- Magic/Resonance: `#8B5CF6`
- Energy/Cyan: `#06B6D4`

### Planet accent colors
- Verdania (Biology): `#10B981`
- Glycera (Biochem): `#F59E0B`
- Luminara (Gen Chem): `#3B82F6`
- Synthara (Org Chem): `#8B5CF6`
- Aethon (Physics): `#EF4444`
- Miravel (Psych/Soc): `#EC4899`
- Lexara (CARS): `#06B6D4`

### Core UX rules
- Every major action confirms immediately (visual + micro-sound).
- Wrong answers are reframed as “partial recall,” never punitive.
- Progress is always visible: streak, energy, crystals, planet mastery.
- Keep interactions 30–60s where possible.
- Use smooth transitions between pages (200–400ms).

Deliver complete page designs, reusable components, and interaction specs.

---

## 1) Landing Page Prompt

**Prompt:**
Create the landing page for **MCAT Mastery**, a cozy interplanetary MCAT game. Must feel premium, playful, and motivating.

### Above the fold
- Top nav: logo left, links center (`How It Works`, `Planets`, `Pricing`, `FAQ`), `Log In` and `Get Started` right.
- Hero headline: “Reclaim the Light. Master the MCAT.”
- Subheadline: “The ADHD-friendly, gamified MCAT tutor where each correct answer clears darkness from a living galaxy.”
- Primary CTA: `Start Free`
- Secondary CTA: `Watch 60s Overview`
- Hero visual: ship bridge window showing 7 fogged planets orbiting in space + subtle LYRA hologram.

### Mid sections
1. **How it works (3 steps)**
   - Learn in short guided bursts
   - Answer and cast Resonance
   - Clear fog and unlock planets
2. **7 planets section**
   - Show 7 cards with unique color tint and subject label.
3. **Why this works**
   - Micro-learning
   - Spaced repetition disguised as fog reclamation
   - Friendly reinforcement
4. **Game feel section**
   - Show creatures, streak moments, and “NICE!” celebration visuals.

### Footer
- Links, social, legal, privacy, contact.

### Visual behavior
- Ambient star shimmer in background.
- Planet cards gently pulse with color-specific glow.
- CTA button has subtle hover lift and glow.

---

## 2) Login / Sign Up Prompt

**Prompt:**
Design a cozy, high-conversion login/sign-up screen for MCAT Mastery.

### Layout
- Split panel layout on desktop, stacked on mobile.
- Left side: atmosphere art (ship interior, stars, LYRA quote).
- Right side: auth card with tabs (`Log In`, `Sign Up`).

### Inputs
- Email, password, remember me, forgot password.
- Social login: Google + Apple.
- Optional anonymous guest mode with clear upgrade path.

### Copy tone
- Warm and supportive: “Welcome back, Commander.”
- Non-threatening errors: “That didn’t connect — try again.”

### Micro-interactions
- Input focus glow in accent color.
- Success state: green check + soft chime.
- Error state: gentle red pulse, no harsh shake.

### Background
- Galaxy shimmer + very soft animated planet silhouettes.

---

## 3) Post-Login Home / Ship Dashboard Prompt (Most Important)

**Prompt:**
Design the main logged-in hub as a **Ship Dashboard** overlooking all 7 planets. This is the most important screen.

### Top HUD
- Left: menu and app logo.
- Center/right status chips:
  - Energy (e.g., `⚡ 4/6`)
  - Streak (e.g., `🔥 12`)
  - Crystals (e.g., `✨ 2,450`)
  - Profile avatar
- Include daily objective chip: “Complete 1 mission to protect streak.”

### Main composition
- Central panoramic “glass deck” with 7 planets in a curved orbital arrangement.
- Planets are large circular interactive nodes with:
  - planet name + subject
  - progress ring (% cleared)
  - fog status (`Clear`, `Stirring`, `Reclaimed`)
  - specialist portrait badge
  - recommended tag on best next planet

### Main action row
- Large primary buttons:
  - `Continue Mission`
  - `Planets`
  - `Review`
- Secondary row:
  - `Field Notes`
  - `Powers`
  - `Profile`

### Motion
- Slow orbital drift for planets.
- Subtle glow pulse tied to each planet’s accent color.
- Recommended planet has a soft beacon pulse.

### UX behavior
- Clicking a planet triggers a fast cinematic zoom (300–400ms) into that world.
- Right side panel (optional) shows current alerts:
  - Fog reclaim warning from specialist
  - Streak reminder
  - Bridge mission available

---

## 4) Planets Overview Prompt (Planet Select Grid + Orbit)

**Prompt:**
Create a dedicated Planets screen that can toggle between **Orbit View** and **Grid View**.

### Orbit View
- Large center star map with 7 interactive planets in orbit.
- Hover/tap card reveals:
  - subject
  - mastery %
  - sectors completed / total
  - native creature + corrupted variant icon

### Grid View
- 7 premium cards with unique thematic artwork:
  - Verdania: bioluminescent forests
  - Glycera: glowing bio-mechanical channels
  - Luminara: crystal and aurora world
  - Synthara: iridescent cave structures
  - Aethon: floating stones and force arcs
  - Miravel: warm social city of light bridges
  - Lexara: white-gold library canyons and ink rivers

### Sorting/filtering
- Recommended first
- Most fogged first
- Highest mastery first

### CTA
- Each card has `Enter Planet`.

---

## 5) Planet Detail Prompt (Hex Tile Map + Fog)

**Prompt:**
Design the full Planet View using a **hexagonal tile map** where each hex is a chapter/mission node. Unfinished nodes are covered by dark crystal fog.

### Map behavior
- Pannable/zoomable map with chapter sectors grouped by boundaries and labels.
- Hex tiles represent chapter missions and sub-missions.
- States:
  - **Locked**: dim, heavy fog, no glow
  - **Available**: soft pulse + clear outline
  - **Completed**: vibrant terrain revealed, checkmark sparkle
  - **Corrupted Return (review)**: partial fog creeping back animation

### Fog system visuals
- Dark overlay + slight blur + desaturation over hidden tiles.
- Clearing a tile removes fog with dissolving smoke and color bloom.
- Cleared areas remain bright while uncleared areas stay muted.

### Planet header
- Back button, planet name, subject icon, mastery ring.
- Specialist portrait + one contextual line.
- Buttons: `Start Recommended`, `Review Fog`, `Field Notes`.

### Ambient life
- Tiny native creatures roam clear zones.
- Corrupted variants idle on fogged zones.

---

## 6) Mission Entry Prompt (Before Questions Start)

**Prompt:**
Create a Mission Start panel shown after clicking a hex tile.

### Content
- Mission title + chapter/topic.
- Duration estimate (`~3–6 min` full mission or `~30–60 sec` quick check).
- Mission type badge (`Guided Learning`, `Review Sweep`, `Bridge`, `Boss Creature`).
- Quick goals list:
  - clear X tiles
  - maintain streak
  - defeat creature (optional)
- Rewards preview: XP, crystals, mastery gain.

### Buttons
- `Start Mission` (primary)
- `Preview Concepts`
- `Cancel`

### Flavor
- LYRA mission line and occasional Grimble taunt bubble.

---

## 7) Mission Screen Prompt (Question UI + Real-Time Tile Clearing)

**Prompt:**
Design the mission gameplay screen with a split layout:
- Top 60%: lesson/question card area
- Bottom 40%: mini hex map showing tile progress in real-time

### Question card design
- Clean rounded card with question text, diagram slot, and answer controls.
- Support interaction types:
  - multiple choice
  - drag/drop labels
  - hotspot click
  - sequence order
  - mini graph slider
- Timer is subtle (not stressful), shown as ring around question index.

### Answer interactions
- On select: immediate feedback state and explanation chip.
- Correct: green flash + resonance strike animation to bottom map.
- Wrong: soft red pulse + “partial recall” helper message from LYRA.

### Bottom map reaction
- Correct answers clear fog on 1+ hex tiles.
- Wrong answers keep tile fogged and queue it for review.
- Streak increases charge meter for Surge ability.

### Side utility
- Notebook quick drawer.
- Mute/voice toggle for LYRA.

---

## 8) Correct Answer, Streak, and Failure Feedback Prompt

**Prompt:**
Create delightful feedback animations and sound behavior inspired by Duolingo’s celebratory style but with cosmic magic identity.

### Correct answer event
- Visual sequence (600–900ms):
  1. Button confirms with bright highlight.
  2. Commander casts Resonance strike (element-colored projectile).
  3. Target hex fog explodes softly into spark particles.
  4. Floating text appears: `NICE!` or `PATHWAY CONFIRMED`.
- Sound: short bright chime + element impact SFX.

### Wrong answer event
- Visual: small fizzle, muted pulse on target fog tile.
- Copy: “Partial recall — let’s reinforce it.”
- Sound: soft descending tone, not harsh.

### Streak milestones
- At 3: `NICE!` + small glow burst + bonus crystals
- At 6: `ON FIRE!` + border aura + faster surge charge
- At 10: `UNSTOPPABLE!` + full-screen resonance wave + instant surge ready

### Streak UI
- Persistent streak meter with flame icon and tier labels.
- Meter should feel exciting but never distracting.

---

## 9) Creature Encounter Prompt (Bonus Mini-Game)

**Prompt:**
Design random creature interruption events during missions.

### Event flow
1. Corrupted creature emerges from a fogged hex.
2. It applies a small gameplay modifier (e.g., blocks next tile).
3. User must complete a 30–45 second bonus question to free creature.
4. Success purifies creature with comedic cozy animation.

### Visual style
- Corrupted version: darker tones, violet fog veins, unstable aura.
- Freed version: bright, cute, grateful animation.

### Reward
- Bonus crystals + bonus XP + “creature freed” stat.

---

## 10) Powers / Upgrades Screen Prompt

**Prompt:**
Create a `Powers` screen with three tabs: `Upgrades`, `Cosmetics`, `Items`.

### Upgrades tab
- Tracks: Strike, Surge, Aura (5 tiers each).
- Card UI with tier preview, lock state, crystal price, and buy button.

### Cosmetics tab
- Element color variants, commander outfits, planet victory skins.

### Items tab
- Streak Freeze
- Quick Energy Charge
- Full Energy Charge

### UX
- Real-time crystal deduction.
- Purchase confirmation animation with glow pulse.

---

## 11) Notes & Field Notes Prompt

**Prompt:**
Design a notes system with two tabs:
- `Field Notes` (auto-generated summaries by planet/sector/tile)
- `My Notebook` (user-created folders and notes)

### Required elements
- Search across all notes.
- Fog status tags in notes (`Clear`, `Stirring`, `Reclaimed`).
- “Open during mission” quick drawer mode.

### Visuals
- Soft paper-card look but still cosmic.
- Keep writing interface calm and minimal.

---

## 12) Bridge Missions Prompt (Cross-Subject Challenges)

**Prompt:**
Design Bridge Missions as short 3–5 minute cross-subject challenges that unlock permanent links between planets.

### Flow
- Intro line from LYRA describing the connection.
- 3–5 hybrid questions + 1 rapid match mini-game.
- Completion creates glowing line between two planets on ship map.

### Rewards
- Crystals
- bridge cosmetic
- permanent bridge marker

### Visual language
- Distinct from normal missions: use dual-color gradient from both planet accents.

---

## 13) Audio + Music Direction Prompt

**Prompt:**
Generate an audio direction spec for the web app with cozy, satisfying, non-fatiguing sound design.

### Music
- Unique ambient loop for each planet theme.
- Ship dashboard uses safe/home ambient pad.

### SFX categories
- UI clicks (soft)
- Correct answer chimes
- Wrong answer muted tones
- Resonance element impacts (6 variants)
- Streak fanfares (3, 6, 10)
- Fog clear dissolve
- Creature free celebration chirp

### Audio UX rules
- Never loud or jarring.
- Layered but sparse.
- Include independent volume sliders for music/voice/SFX.

---

## 14) Motion & Transition Prompt

**Prompt:**
Define animation system for smooth, premium, low-latency interactions.

### Timing rules
- Hover: 120–180ms
- Screen transitions: 250–350ms
- Planet zoom: 350–450ms
- Tile clear effect: 500–900ms

### Key animations
- Planet orbital drift (very slow)
- Star shimmer particles (subtle, ~10% visual intensity)
- Fog creep-back animation for review reminders
- Resonance surge burst at streak milestones

### Performance constraints
- 60fps target on modern devices
- fallback simplification on low-power devices
- avoid heavy shaders; prefer CSS transforms + lightweight canvas particles

---

## 15) End-to-End User Journey Prompt (Generator Should Build Entire Flow)

**Prompt:**
Generate the complete user journey for MCAT Mastery with all screens connected and consistent styles:

1. Landing page
2. Authentication
3. First-time onboarding (choose commander + resonance)
4. Ship dashboard (7 planets visible)
5. Planet select and zoom transition
6. Hex tile planet map with fog states
7. Mission start panel
8. Mission gameplay with question card + live tile clearing
9. Correct/wrong/streak feedback animations and sounds
10. Creature encounters
11. Mission summary and rewards
12. Return loop to ship dashboard
13. Optional routes: review, bridge missions, powers, notes, profile

Ensure every route has clear CTAs and no dead ends. Keep all copy warm, motivating, and ADHD-friendly.

---

## 16) Mega Prompt (Single-Paste Version)

**Prompt:**
Create a full web app design for **MCAT Mastery**, a cozy sci-fi MCAT learning game with Duolingo-like clarity and satisfying feedback loops. Use dark mode cosmic UI with rounded friendly components, subtle galaxy shimmer background, and responsive mobile-first layout. The story: player is a Commander guided by LYRA to clear Grimble’s dark fog from 7 subject planets.

Must include:
- Landing page, login/sign-up, onboarding
- Main Ship Dashboard with 7 interactive planets and HUD for energy/streak/crystals
- Planet detail pages with **hexagonal mission tiles** covered by fog until cleared
- Mission flow from tile click to start panel to live gameplay
- Split mission UI: top question/lesson area, bottom live hex progress map
- Correct feedback with element strike, tile clear animation, celebratory text (`NICE!`)
- Wrong feedback as gentle partial-recall guidance
- Streak milestones with escalating visual/sound payoff
- Creature encounter bonus mini-game
- Powers/Upgrades, Field Notes/Notebook, Bridge missions, Profile

Use exact visual language:
- Cozy + bold + magical, never sterile
- Warm motivational copy and non-punitive feedback
- Smooth 200–400ms transitions
- Planet-specific color tints and thematic art
- Fog overlays (dark, blurred, desaturated) that dissolve on success

Also generate:
- full component list
- page-by-page layout specs
- state variants (locked/available/completed/reclaimed)
- animation and SFX event table
- responsive behavior notes
- accessibility checklist

Output should be implementation-ready for modern web stack.

---

## 17) Optional: Prompt for the 50 Hard Concept Mini-Games

**Prompt:**
Using the 50 hard MCAT concepts list, generate one 30–60 second micro-game per concept using a cozy interactive style. Each mini-game should define:
- objective
- interaction type
- win condition
- feedback animation/sound
- how it affects tile clearing/mastery

Align visuals with the same MCAT Mastery design system and mission UI.
