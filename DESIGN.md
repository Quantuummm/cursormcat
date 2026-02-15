# Design System: MCAT Mastery — Conquer the Stars

## 1. Design Philosophy

**Core Vision:** "Humanity was meant to conquer the stars."

A hopeful, cosmic learning odyssey that blends Duolingo's clean, addictive UX with the vibrant character energy of Clash Royale — all wrapped in an interstellar exploration theme. Every pixel should whisper *discovery*, *wonder*, and *progress*.

### Design Pillars

| Pillar | Principle |
|--------|-----------|
| **Cosmic Clarity** | Clean interfaces with generous whitespace. Information hierarchy through size and color, never clutter. Duolingo-level simplicity meets space-opera aesthetics. |
| **Living Universe** | Subtle, constant motion — star shimmer, orbital drift, soft particle effects. The UI should feel *alive* without being distracting. ~10% of screen area has gentle animation. |
| **Dual Atmosphere** | Full dark mode (deep space) and light mode (nebula dawn). Both feel premium. Dark = default. |
| **Hopeful Boldness** | Warm accent colors on cosmic backgrounds. Rounded, friendly shapes. Characters and planets that radiate personality. Nothing feels clinical or sterile. |
| **Mobile-First Cosmos** | Swipe-native navigation between planets. Touch targets that feel generous. Content centered vertically. Left/right margins kept clean. |

### Tone & Mood

- **Adjectives:** Hopeful, vibrant, cozy-cosmic, playful-bold, inviting, expansive
- **NOT:** Dark-gritty, cold-clinical, retro-pixel, minimalist-corporate
- **Inspirations:** Duolingo (UX flow, simplicity, gamification), Clash Royale (character boldness, cartoon energy), Destiny 2 (cosmic vibe, lore depth), Stardew Valley (warmth, coziness)

---

## 2. Color Palette

### Dark Mode (Default — "Deep Space")

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Background | Void Black | `#0A0E17` | Page background, canvas |
| Surface | Nebula Dark | `#111827` | Cards, panels, modals |
| Surface Elevated | Star Dust | `#1F2937` | Elevated cards, active states |
| Border | Cosmic Edge | `#374151` | Subtle borders, dividers |
| Text Primary | Star White | `#F9FAFB` | Headings, body text |
| Text Secondary | Lunar Gray | `#9CA3AF` | Subtitles, labels |
| Text Muted | Asteroid Gray | `#6B7280` | Hints, disabled text |
| Accent Primary | Nova Blue | `#3B82F6` | Links, primary actions, active tabs |
| Accent Success | Aurora Green | `#10B981` | Correct answers, progress, success |
| Accent Warning | Solar Gold | `#F59E0B` | Crystals, streaks, currency |
| Accent Danger | Red Dwarf | `#EF4444` | Errors, wrong answers |
| Accent Magic | Nebula Purple | `#8B5CF6` | Resonance, special abilities, magic effects |
| Accent Energy | Plasma Cyan | `#06B6D4` | Energy, power-ups |
| Galaxy Shimmer | Shimmer White | `rgba(255, 255, 255, 0.03)` | Background star particles |

### Light Mode ("Nebula Dawn")

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Background | Cloud White | `#F8FAFC` | Page background |
| Surface | Mist White | `#FFFFFF` | Cards, panels |
| Surface Elevated | Frost | `#F1F5F9` | Elevated cards |
| Border | Morning Edge | `#E2E8F0` | Borders |
| Text Primary | Deep Space | `#0F172A` | Headings, body |
| Text Secondary | Twilight | `#475569` | Subtitles |
| Accent Primary | Daylight Blue | `#2563EB` | Primary actions |
| Galaxy Shimmer | Shimmer Black | `rgba(0, 0, 0, 0.02)` | Background particles |

### Planet Accent Colors (Used per-planet UI tinting)

| Planet | Subject | Primary | Glow |
|--------|---------|---------|------|
| Verdania | Biology | `#10B981` | `#6EE7B7` |
| Glycera | Biochemistry | `#F59E0B` | `#FCD34D` |
| Luminara | Gen Chemistry | `#3B82F6` | `#93C5FD` |
| Synthara | Org Chemistry | `#8B5CF6` | `#C4B5FD` |
| Aethon | Physics | `#EF4444` | `#FCA5A5` |
| Miravel | Psych/Soc | `#EC4899` | `#F9A8D4` |
| Lexara | CARS | `#06B6D4` | `#67E8F9` |

---

## 3. Typography

| Role | Font | Weight | Size (Desktop) | Size (Mobile) |
|------|------|--------|-----------------|---------------|
| Display/Hero | **Fredoka One** | 400 | 48-64px | 32-40px |
| Heading H1 | **Fredoka One** | 400 | 32-40px | 24-28px |
| Heading H2 | **Nunito** | 800 | 24-28px | 20-22px |
| Heading H3 | **Nunito** | 700 | 18-20px | 16-18px |
| Body | **Nunito** | 600 | 16px | 15px |
| Body Small | **Nunito** | 400 | 14px | 13px |
| Button Text | **Nunito** | 800 | 16px | 15px |
| Caption/Label | **Nunito** | 600 | 12-13px | 11-12px |

**Letter spacing:** Headings: -0.02em. Body: normal. Buttons: 0.02em uppercase or normal case.

---

## 4. Component Language

### Buttons

- **Primary:** Solid fill with accent color. Rounded-full (pill shape). Bold text. Subtle bottom shadow (3D depth like Duolingo). Hover: slight lift + glow.
- **Secondary:** Ghost/outlined style. Same pill shape. Hover: fill with 10% opacity of accent.
- **Icon Button:** Circular. Subtle background. 40-48px hit target.

### Cards

- Rounded-xl (16px radius). Subtle border in dark mode, soft shadow in light mode.
- Hover: gentle lift (translateY -2px) + border glow.
- Content padding: 20-24px.

### Navigation

- **Top Bar (Desktop):** Logo left, nav center (minimal), Login/Sign Up right. Clean. 64px height. Subtle backdrop blur.
- **Bottom Bar (Mobile):** 5 tabs max. Icon + label. Active = accent color. 56px height.
- **Left/Right sides of main content: CLEAN.** No sidebars in default view.

### Planet Nodes

- Circular, 80-120px diameter on dashboard.
- Animated: slow orbital drift, subtle glow pulse matching planet color.
- Clear visual state: locked (dim + lock icon), active (glowing border), completed (checkmark badge).
- On click: rapid zoom transition (scale up from circle to full screen, ~300ms ease-out).

### Tile System (Planet Map)

- Vertical scroll path (like Duolingo's lesson tree).
- Tiles: 64px circles connected by a winding path line.
- States: locked (gray), available (glowing), completed (filled + check), boss (larger + special border).
- Sections grouped with chapter labels.

---

## 5. Layout Principles

### Landing Page (Pre-Login) — Duolingo Style

```
┌─────────────────────────────────────────────────────┐
│  [Logo]           [Nav Links]      [Login] [Sign Up]│  <- 64px nav bar
├─────────────────────────────────────────────────────┤
│                                                     │
│          "The free, fun way to                      │
│           master the MCAT"                          │  <- Hero: big heading,
│                                                     │     subtext, CTA button
│          [GET STARTED]                              │     + character/mascot art
│                                                     │     on the right
│                    [Mascot/Ship Art]                 │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Feature Section 1: "Backed by Science"             │  <- Alternating
│  Feature Section 2: "Stay Motivated"                │     text + image
│  Feature Section 3: "Explore the Cosmos"            │     sections
├─────────────────────────────────────────────────────┤
│  App Download / CTA Section                         │
├─────────────────────────────────────────────────────┤
│  Footer                                             │
└─────────────────────────────────────────────────────┘
```

### Dashboard (Post-Login) — Cosmic Hub

```
┌─────────────────────────────────────────────────────┐
│  [Logo]  [Resources] [Streak] [Crystals]  [Profile] │  <- HUD bar
├─────────────────────────────────────────────────────┤
│                                                     │
│              ☆ Galaxy Background ☆                  │
│          (subtle shimmer particles ~10%)             │
│                                                     │
│        ○ Verdania     ○ Glycera                     │
│     ○ Luminara           ○ Synthara                 │  <- 7 planets in
│        ○ Aethon      ○ Miravel                      │     orbital arrangement
│              ○ Lexara                               │
│                                                     │
│              🚀 [SHIP HUB]                          │  <- Center: ship with
│         [Games] [Notes] [Custom] [Social]           │     quick actions
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Planet View (After Zoom)

```
┌─────────────────────────────────────────────────────┐
│  [← Back]     [Planet Name]        [Progress Ring]  │  <- Header
├─────────────────────────────────────────────────────┤
│                                                     │
│          ☆ Galaxy shimmer background ☆              │
│          + Planet surface art (subtle, bg)           │
│                                                     │
│              ◉ Tile 5 (Boss)                        │
│              │                                      │
│           ◉──┘ Tile 4                               │  <- Winding path
│           │                                         │     of tiles
│           └──◉ Tile 3                               │
│              │                                      │
│           ◉──┘ Tile 2                               │
│           │                                         │
│           ◉ Tile 1 (Start)                          │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [Games] [Notes] [Shop] [Bridges]                   │  <- Bottom nav
└─────────────────────────────────────────────────────┘
```

---

## 6. Galaxy Shimmer Background (Critical Ambient Effect)

The defining visual element. Both dark and light modes feature this.

### Implementation Spec

- **Canvas or CSS-based** star field with 50-100 tiny particles.
- **Movement:** Very slow drift (0.1-0.3px/frame). Random direction per particle.
- **Opacity:** Individual particles at 0.1-0.4 opacity. Occasional gentle pulse (opacity 0.1 → 0.5 → 0.1 over 3-6 seconds).
- **Colors:** In dark mode, white/blue-white. In light mode, soft gold/silver.
- **Coverage:** Distributed across entire background but visually subtle — user should notice it only after a moment. ~10% visual intensity.
- **Performance:** Use CSS animations or lightweight canvas. No heavy GPU usage. requestAnimationFrame with throttle to 30fps max.

---

## 7. Animation Guidelines

| Animation | Duration | Easing | Notes |
|-----------|----------|--------|-------|
| Screen transition | 300ms | ease-out | Fade + slight scale |
| Planet zoom-in | 400ms | cubic-bezier(0.34, 1.56, 0.64, 1) | Scale from planet circle to full view |
| Planet orbital drift | 20-40s loop | linear | Slow, continuous circular motion |
| Particle shimmer | 3-6s loop | ease-in-out | Opacity pulse on individual particles |
| Button hover | 150ms | ease | Subtle lift + glow |
| Card hover | 200ms | ease | translateY(-2px) + shadow enhancement |
| Tile unlock | 500ms | spring | Pop + glow burst |
| Planet swipe (mobile) | 250ms | ease-out | Horizontal slide between planets |
| Theme toggle | 400ms | ease-in-out | Smooth color interpolation |

---

## 8. Dark/Light Mode Strategy

- CSS custom properties for all colors (`:root` for dark, `[data-theme="light"]` for light).
- Toggle in nav bar (sun/moon icon).
- Persist preference in localStorage + respect `prefers-color-scheme`.
- Transition: 400ms ease-in-out on `background-color` and `color` properties.
- Galaxy shimmer adapts particle colors automatically.

---

## 9. Mobile-Specific Design

- **Planet Navigation:** Horizontal swipe carousel. Current planet centered and enlarged. Adjacent planets visible but smaller.
- **Bottom Navigation Bar:** 5 icons — Home, Ship, Games, Notes, Profile.
- **No side panels.** Everything centered or top/bottom.
- **Touch targets:** Minimum 44px.
- **Planet zoom:** Same animation, fills viewport.
- **Tile path:** Full-width vertical scroll. Generous vertical spacing between tiles.

---

## 10. 3D Character Art Direction

### Style Reference
- **Clash Royale / Clash of Clans** cartoon boldness: chunky proportions, exaggerated features, vibrant colors
- **Duolingo** character friendliness: rounded, approachable, expressive
- **Space Commander aesthetic:** helmets, visors, armor plating, glowing accents

### Character Types Needed
1. **Player Commanders** (4 variants) — customizable armor colors, helmet styles, resonance element glow
2. **Planet Specialists** (7) — each themed to their planet/subject
3. **Creatures** (7 base × 3 variants each = 21) — corrupted + freed states
4. **LYRA** (AI companion) — holographic, friendly, floating orb/figure
5. **Grimble** (antagonist) — imposing but cartoonishly villainous

### Technical Requirements
- **Format:** glTF 2.0 (.glb) for web compatibility
- **Poly count:** 2,000-8,000 triangles per character (mobile-friendly)
- **Textures:** 512×512 or 1024×1024 max, PBR-lite (diffuse + emission for glows)
- **Animations:** Idle (breathing/bobbing), victory, defeat, attack — 2-4 per character
- **Rendering:** Three.js or `<model-viewer>` web component for lightweight 3D display
- **Fallback:** 2D sprite renders for low-end devices

---

## 11. Design System Notes for Stitch Generation

**DESIGN SYSTEM (REQUIRED):**

When generating screens in Stitch, always include this block:

```
Visual Style: Cosmic-hopeful, clean and spacious like Duolingo but with a deep space aesthetic. 
Font: Fredoka One for headings, Nunito for body text. Bold, rounded, friendly.
Colors (Dark): Background #0A0E17, Surface #111827, Accent Blue #3B82F6, Success Green #10B981, Gold #F59E0B, Purple #8B5CF6, Text White #F9FAFB.
Colors (Light): Background #F8FAFC, Surface #FFFFFF, Accent Blue #2563EB, Text Dark #0F172A.
Shapes: Pill-shaped buttons with subtle 3D shadow (Duolingo-style). Cards with 16px radius. Generous whitespace.
Spacing: 16px base grid. 24-32px between sections. 64px nav height.
Mood: Hopeful, vibrant, cozy-cosmic. "Humanity was meant to conquer the stars." Think warm, inviting space exploration — not cold sci-fi.
Animations: Subtle. Gentle hover lifts. Background has faint galaxy shimmer particles drifting slowly.
Layout: Content centered. Left/right margins clean. No sidebars. Mobile-first responsive.
```
