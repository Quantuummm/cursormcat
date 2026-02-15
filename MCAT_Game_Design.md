# MCAT MASTERY — COMPLETE GAME DESIGN DOCUMENT (v2)

> **Tone:** Stardew Valley coziness × Duolingo addiction × Clash Royale cartoon boldness
> **Platform:** Web App (HTML/CSS/JS — fully implementable by a single dev)
> **Core Fantasy:** You are a superpowered Commander reclaiming corrupted planets through the power of learning.

---

# 1) GAME OVERVIEW

## Core Pitch
A cozy, addictive sci-fi learning game where mastering MCAT content = clearing magical darkness from seven beautiful planets. Every correct answer is a spell cast. Every chapter completed reveals a stunning new region. Every day you return, you push back the darkness further.

## Design Pillars (Non-Negotiable)
1. **ADHD-First:** ~15-second micro-lessons + questions every 2–3 min. Instant feedback (0ms). Multi-sensory (TTS + visuals + animations + sounds).
2. **Cozy & Addictive:** Warm visuals, satisfying sounds, visible progress, rewarding loops. Never punishing.
3. **Simple to Build:** 2D/2.5D web app. Tile-based maps. CSS animations. No game engine required.
4. **Autonomy:** Recommended path, never forced. Player chooses what to study.
5. **Spaced Repetition Disguised as Gameplay:** Fog reclamation = forced review. Players never feel "drilled."

---

# 2) STORY & PREMISE

## The World
A solar system of seven vibrant planets, each home to unique indigenous creatures and ecosystems. These worlds were once brilliant, magical, and alive — until **Grimble** arrived.

## The Inciting Event
Grimble, wielding the **Dark Crystal**, has blanketed all seven planets in a corrupting fog. The fog doesn't just hide the planets — it **corrupts the native creatures**, turning them into mindless servants of darkness. The planets' beauty, knowledge, and life are all being smothered.

Your ship, a long-range exploration vessel, detects the disturbance. The ship AI, **LYRA**, wakes you — the Commander — from cryo-sleep. A mysterious energy shimmer passes through the ship and bonds to your nervous system, giving you **Resonance** — elemental superpowers that can burn away Grimble's fog.

But there's a catch: the Dark Crystal's pulse also caused a **Memory Fracture** in your mind. Your knowledge is scattered. As LYRA guides you through each lesson, you're not just learning — you're **rebuilding your fractured memory**, piece by piece.

## Opening Flow
1. **Intro Cutscene** (illustrated panels + TTS narration, ~60 seconds): Shows the planets being consumed by Grimble's fog, the shimmer bonding to you, LYRA waking you up.
2. **Character Selection:** Pick your Commander (4 premade options) + name + Resonance element.
3. **Ship Dashboard:** You stand at the glass deck, overlooking the 7 darkened planets. LYRA gives you your first mission briefing.
4. **First Deploy:** Tap the recommended planet → first chapter → first guided lesson. No travel animation — instant transition.

---

# 3) THE ANTAGONIST — GRIMBLE

## Identity
- **Name:** Grimble
- **Full Title (in lore):** Grimble, the Eternal Dusk
- **What players call him:** Just "Grimble" (he hates that they don't use his full title)

## Personality
Dramatic, theatrical, takes himself WAY too seriously — which makes him funny. He delivers "menacing" monologues but they come off as pompous and slightly pathetic. He throws tantrums when you clear his fog. He's CLEARLY evil but in a cartoonish, cozy-villain way. Think: if the Duolingo owl became a dark overlord but was still kind of adorable.

## Art Direction
- **Build:** Medium-small, slightly round/hunched. Clash Royale goblin-king proportions — big head, expressive face, smaller body.
- **Face:** Large glowing purple/magenta eyes, small sharp teeth in a perpetual smirk or scowl, small pointed features.
- **Crown:** A tilted crown of dark crystal shards that grows from his head — part of him, slightly askew.
- **Attire:** An oversized tattered cloak, dark purple with faint starlight sparkles in the fabric. It drags on the ground dramatically.
- **Weapon:** The Dark Crystal — a large, cracked, pulsing amethyst crystal on a gnarled staff that's comically taller than him.
- **Effects:** Dark misty tendrils curl from his cloak edges. Dark particles float around him constantly.
- **Colors:** Deep purple body, magenta/violet eye glow, dark amethyst crystal, midnight-blue cloak.
- **Plushie Test:** You could absolutely make a Grimble plushie and people would buy it. That's the vibe.

## The Dark Crystal
Grimble's power source. A massive cracked crystal that pulses with violet energy. It allows him to:
- Generate the corrupting fog that blankets planets
- Take control of indigenous creatures, turning them into dark servants
- Slowly reclaim territory that the Commander has freed (fog creeps back)

The Dark Crystal is NOT invincible. As the Commander clears all 7 planets to 100%, the crystal weakens and cracks further — setting up the endgame confrontation.

## How Grimble Manifests in Gameplay
- **Mission start:** Occasionally appears as a small floating hologram taunting you before the mission begins.
- **During missions:** His fog is everywhere. His corrupted creatures block your path. His presence is felt, not seen.
- **When you clear a sector:** A brief cutscene shows Grimble reacting with annoyance/frustration.
- **Planet 100%:** Grimble throws a dramatic tantrum and retreats from that world.
- **Fog reclamation alerts:** Grimble taunts you: *"Miss me, Commander? I told you I always come back."*

## Example Dialogue
- *"You think clearing ONE sector matters? I have SEVEN planets!"* (you've cleared 4)
- *"My creatures will— wait, did you just clear another tile?!"*
- *"This is TEMPORARY. The fog always returns. Always."*
- (when you hit 100%) *"...Fine. You win THIS round."*
- (fog reclamation) *"Oh look, your precious little sector is getting dark again. Shame."*

---

# 4) PLAYER CHARACTER — THE COMMANDER

## Character Selection (at game start)
**4 Premade Commanders** — 2 female, 2 male. Diverse ethnicities and styles. Each has a unique visual design but identical gameplay.

| Commander | Gender | Visual Style |
|---|---|---|
| **Commander Kai** | Male | Warm-toned, undercut, confident stance |
| **Commander Zara** | Female | Cool-toned, braided hair, sharp gaze |
| **Commander Ryn** | Male | Earth-toned, relaxed, approachable |
| **Commander Lira** | Female | Vibrant, natural hair, warm smile |

## Name Selection
A premade list of ~20 commander names for easy TTS compatibility:
Kai, Zara, Ryn, Lira, Nova, Jace, Mira, Cole, Sera, Quinn, Dex, Aria, Reed, Opal, Cruz, Wren, Sol, Jade, Nash, Skye

## Resonance Selection (done during character creation)
Choose 1 of 6 elements (see Section 8 for full details). This determines your combat visuals and upgrade path.

---

# 5) LYRA — THE OPERATOR AI

## Role
LYRA is the ship's AI and your constant companion. She speaks through TTS during every mission, serving as both **teacher and tactical operator**. She is the primary voice of the game.

## Personality
Calm, warm, precise. Never shames — always reframes mistakes as learning signals. She's protective of you and genuinely invested in your recovery. Think of her as a brilliant tutor who also happens to be your co-pilot.

## Lore Connection to TTS Teaching
LYRA isn't just "reading lessons" — she's **reconstructing your fractured memory**. Every micro-lesson is framed as LYRA helping you rebuild neural pathways that Grimble's Dark Crystal shattered. This means:
- Learning new content = "Memory Reconstruction"
- Review = "Signal Stabilization"
- Getting questions right = "Neural pathway confirmed"
- Getting questions wrong = "Partial recall — let me reinforce that pathway"

## Example In-Mission Dialogue
- (teaching) *"Commander, your neural map is rebuilding. Let's reinforce this pathway: the citric acid cycle begins when..."*
- (correct answer) *"Pathway confirmed. Strong recall, Commander."*
- (wrong answer) *"Partial recall — that's normal after a fracture. The key distinction is... Let's try again."*
- (streak of 3) *"Outstanding focus. Your Resonance is surging."*
- (streak of 10) *"Commander, your cognitive signal is the strongest I've recorded. Grimble can't hold this sector."*
- (mission complete) *"Sector stabilized at 87%. Excellent work. Your memory grows stronger every session."*

---

# 6) THE SEVEN SPECIALISTS

Each specialist is stationed on their planet's Stronghold (once unlocked). They serve as:
- The subject expert and lore voice for that planet
- The person who alerts you when fog is creeping back
- A companion whose portrait appears during subject-specific content

| # | Specialist | Planet | Subject | Vibe |
|---|---|---|---|---|
| 1 | **Dr. Pax "Cal" Calder** | Luminara | Gen. Chemistry | Goofy, explosive enthusiasm |
| 2 | **Dr. Imani Kade** | Verdania | Biology | Grounded, systems-first mentor |
| 3 | **Dr. Rowan Vale** | Glycera | Biochemistry | Smooth optimizer |
| 4 | **Dr. Elara Finch** | Synthara | Organic Chemistry | Witty detective |
| 5 | **Cmdr. Mara Voss** | Aethon | Physics | Concise, disciplined, dry humor |
| 6 | **Dr. Nia Solomon** | Miravel | Psych/Soc | Empathetic strategist |
| 7 | **Prof. Adrian Rhee** | Lexara | CARS | Measured, elegant, incisive |

## Specialist Fog Alerts (Examples)
- **Dr. Kade (Bio):** *"Commander, the Blight Sprouts are reforming in the Synapse Network. A quick review sweep should hold the sector."*
- **Dr. Finch (Orgo):** *"Something's off in the Hexring Caverns. Grimble's fog is seeping back. Can you deploy for a quick refresher?"*
- **Cal (Gen Chem):** *"HEY COMMANDER! The pH Cascades are going dark again! Get down here before I lose my favorite sunset!"*

---

# 7) THE SEVEN PLANETS

## Overview

All planets begin fully covered in Grimble's dark fog. As you complete chapters (zones), sectors of the planet are revealed — transforming from dark, corrupted tiles into vibrant, magical landscapes. Each planet is a **large, interactive tile-based map** that the player can scroll/pan to view all sectors.

| Planet | Subject | Visual Theme | Specialist | Native Creatures |
|---|---|---|---|---|
| **Verdania** | Biology | Bioluminescent forests, rivers, magic flora | Dr. Imani Kade | Sproutlings |
| **Glycera** | Biochemistry | Bio-mechanical cities, glowing pathways | Dr. Rowan Vale | Glowmites |
| **Luminara** | General Chemistry | Crystal seas, neon auroras, prismatic light | Dr. Pax Calder | Sparklings |
| **Synthara** | Organic Chemistry | Iridescent caverns, ring-shaped crystals | Dr. Elara Finch | Cave Wisps |
| **Aethon** | Physics | Open skyfields, magnetic arcs, floating stones | Cmdr. Mara Voss | Windlings |
| **Miravel** | Psych/Soc | Warm layered city, social light-bridges | Dr. Nia Solomon | Echoes |
| **Lexara** | CARS | White-gold canyon libraries, ink rivers | Prof. Adrian Rhee | Inklings |

## Planet Map Design (UI Implementation)

When a player taps a planet from the Ship Dashboard, they see the **full planet map** — a large, illustrated tile grid:

- **Visual:** A beautiful 2D illustrated map (think fantasy RPG world map meets Stardew Valley)
- **Tiles:** Each tile represents a lesson/subchapter within a chapter (zone)
- **Fog state:** Uncompleted tiles have a dark crystal fog overlay (CSS: dark overlay + blur + desaturation)
- **Cleared state:** Completed tiles show vibrant, colorful illustrated terrain
- **Camera:** Scrollable/pannable OR zoomable to fit all tiles in one view. Player can freely explore the map.
- **Sectors:** Tiles are grouped into sectors (chapters). Each sector has a name label and boundary.
- **Implementation:** HTML/CSS grid or SVG map with tile elements. Fog = CSS filter overlay. Clearing = remove filter + fade-in animation.

---

## VERDANIA (Biology) — Sector Map

**Planet Theme:** A lush, bioluminescent world of glowing forests, crystal-clear rivers, and magic-imbued flora. Every living thing pulses with soft light.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Living Seeds** | The Cell | Bioluminescent garden beds with floating cell-shaped lights |
| 2 | **The Dividing Meadows** | Reproduction / Cell Division | Flower fields in perpetual bloom, splitting and multiplying |
| 3 | **The Cradle Pools** | Embryogenesis & Development | Warm crystalline pools with glowing developing forms |
| 4 | **The Synapse Network** | The Nervous System | Vast web of glowing neural bridges spanning canyons |
| 5 | **The Hormone Falls** | The Endocrine System | Cascading waterfalls that shift in color and warmth |
| 6 | **The Breath Peaks** | The Respiratory System | Misty highlands where clouds pulse with gentle oxygen light |
| 7 | **The Pulse River** | The Cardiovascular System | A great river system that rhythmically glows crimson |
| 8 | **The Guardian Canopy** | The Immune System | Towering trees forming a protective dome of light |
| 9 | **The Ember Caverns** | The Digestive System | Warm amber caverns with flowing enzymatic streams |
| 10 | **The Crystal Lakes** | The Excretory System | Serene lakes with beautiful visible filtration patterns |
| 11 | **The Ironwood Ridges** | The Musculoskeletal System | Mountain ridges with fibrous, muscle-like bark trees |
| 12 | **The Memory Roots** | Genetics & Evolution | Ancient root system glowing with hereditary light patterns |

**Native Creatures:** **Sproutlings** — Small, adorable plant creatures with glowing leaf-ears and petal tails. When corrupted by Grimble: **Blight Sprouts** — same shape but dark purple veins, foggy eyes, wilted petals. When freed, they pop back to their cute, glowing selves.

---

## GLYCERA (Biochemistry) — Sector Map

**Planet Theme:** A warm bio-mechanical world where organic pathways flow like glowing canals through living cities. Everything is connected, everything flows.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Peptide Springs** | Amino Acids & Peptides | Hot springs with color-shifting molecular chains |
| 2 | **The Catalyst Gardens** | Enzymes | Gardens where flowers accelerate nearby growth in real-time |
| 3 | **The Folding Terraces** | Protein Function & Analysis | Cascading terraces folding into origami-like formations |
| 4 | **The Sugar Groves** | Carbohydrate Structure | Crystalline forests with ring-shaped tree crowns |
| 5 | **The Membrane Shores** | Lipid Structure / Membranes | Beaches with dual-layered shimmering waves |
| 6 | **The Helix Towers** | DNA & Biotechnology | Spiraling towers of intertwined light |
| 7 | **The Transcript Reefs** | RNA & Genetic Code | Coral structures that translate colors into patterns |
| 8 | **The Glycolysis Stream** | Carbohydrate Metabolism | Flowing streams that break down into energy sparks |
| 9 | **The Beta Furnace** | Lipid & Amino Acid Metabolism | Warm glowing forges processing fuel |
| 10 | **The ATP Nexus** | Bioenergetics & Regulation | Central hub where all streams converge in brilliant light |

**Native Creatures:** **Glowmites** — Tiny bioluminescent bugs with amber shells. Corrupted: **Rust Mites** — dark, corroded shells, erratic movement. Freed: glow returns, they hum happily.

---

## LUMINARA (General Chemistry) — Sector Map

**Planet Theme:** A world of prismatic light, crystal formations, and neon auroras. Chemical reactions manifest as visible light shows across the landscape.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Particle Fields** | Atomic Structure | Fields of floating light particles in orbital patterns |
| 2 | **The Element Prism** | The Periodic Table | Vast prismatic cliff face with organized crystal formations |
| 3 | **The Bond Bridges** | Bonding & Interactions | Bridges formed from interlocking light beams |
| 4 | **The Balance Gardens** | Stoichiometry | Perfectly symmetrical gardens that adjust in real-time |
| 5 | **The Velocity Rapids** | Chemical Kinetics | Fast-moving rivers of colored light |
| 6 | **The Still Waters** | Equilibrium | A perfectly balanced lake reflecting everything in harmony |
| 7 | **The Thermal Vents** | Thermochemistry | Geysers of warm, colored energy |
| 8 | **The Floating Isles** | The Gas Phase | Islands suspended by visible gas currents |
| 9 | **The Crystal Lagoon** | Solutions | Lagoon where liquids visibly dissolve and mix beautifully |
| 10 | **The pH Cascades** | Acids & Bases | Waterfalls shifting from warm red to cool blue |
| 11 | **The Electron Vale** | Redox Reactions | Valley where electrons visibly transfer between formations |
| 12 | **The Charged Spires** | Electrochemistry | Tall spires crackling with gentle electrical light |

**Native Creatures:** **Sparklings** — Small energy sprites with prismatic bodies. Corrupted: **Flicker Imps** — glitchy, unstable, neon-dark. Freed: stable, warm glow returns.

---

## SYNTHARA (Organic Chemistry) — Sector Map

**Planet Theme:** An underground world of iridescent caverns, glowing ring-structures, and rainbow crystal seams. Molecular architecture made magical.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Naming Stones** | Nomenclature | Ancient standing stones with glowing rune-like names |
| 2 | **The Mirror Fields** | Isomers | Fields where every structure has a reflected counterpart |
| 3 | **The Orbital Groves** | Bonding | Trees with visible electron-cloud canopies |
| 4 | **The Chain Meadows** | Alkanes, Alkyl Halides, Alcohols | Rolling meadows of interconnected flower chains |
| 5 | **The Carbonyl Cliffs** | Aldehydes & Ketones | Dramatic cliffs with double-bond crystal formations |
| 6 | **The Acid Springs** | Carboxylic Acids | Bubbling springs with OH-group crystal formations |
| 7 | **The Nitrogen Gardens** | Amines | Purple-blue gardens with nitrogen-rich glowing flora |
| 8 | **The Hexring Caverns** | Aromatic Compounds | Caverns with hexagonal glowing crystal formations |
| 9 | **The Spectrum Peaks** | Spectroscopy | Mountain peaks that split light into visible spectra |
| 10 | **The Filtration Falls** | Separations & Purifications | Multi-layered waterfalls separating into distinct streams |

**Native Creatures:** **Cave Wisps** — Iridescent bat-like creatures with arrow-shaped wings. Corrupted: **Gloom Bats** — dark, disoriented, erratic. Freed: rainbow shimmer returns.

---

## AETHON (Physics) — Sector Map

**Planet Theme:** Vast open skyfields with visible forces — magnetic arcs, wind vectors, floating gravity stones. A world where physics is visible and beautiful.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Velocity Plains** | Kinematics & Dynamics | Open grasslands where wind traces visible motion vectors |
| 2 | **The Force Gorge** | Work & Energy | A grand canyon where energy visibly transforms |
| 3 | **The Thermal Expanse** | Thermodynamics | Shifting landscape of warm and cool zones |
| 4 | **The Pressure Depths** | Fluids | Deep underwater canyons with visible pressure gradients |
| 5 | **The Charge Fields** | Electrostatics & Magnetism | Open fields with floating charged particles and arcs |
| 6 | **The Current River** | Circuits | Glowing river branching into parallel and series streams |
| 7 | **The Resonance Valley** | Waves & Sound | Valley that amplifies and visualizes sound waves |
| 8 | **The Prism Heights** | Light & Optics | High peaks with rainbow light refracting through crystals |
| 9 | **The Core Sanctum** | Atomic & Nuclear Physics | Deep underground chamber with a glowing central core |

**Native Creatures:** **Windlings** — Small floating wisps pulled by invisible forces. Corrupted: **Drift Wraiths** — dark, chaotic movement. Freed: gentle, graceful float returns.

---

## MIRAVEL (Psychology & Sociology) — Sector Map

**Planet Theme:** A warm, layered city world where social connections are visible as bridges of light. Buildings respond to emotion. Streets glow with empathy.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Sense Quarter** | Sensation & Perception | District where buildings respond to sight, sound, touch |
| 2 | **The Neural Plaza** | Brain & Nervous System | Central plaza with branching pathways like neurons |
| 3 | **The Memory Lanes** | Learning & Memory | Warm streets that light up as you walk, leaving trails |
| 4 | **The Thought Towers** | Cognition, Language, Intelligence | Tall towers with visible thought-bubble windows |
| 5 | **The Heartstreet Market** | Motivation & Emotion | Bustling market that changes colors with emotion |
| 6 | **The Mirror District** | Identity & Personality | Buildings with reflective surfaces showing perspectives |
| 7 | **The Quiet Block** | Psychological Disorders | A dimmer area that brightens as understanding grows |
| 8 | **The Connection Bridges** | Social Psychology | Bridges of light between buildings = social bonds |
| 9 | **The Institution Halls** | Sociology: Institutions & Culture | Grand civic buildings with glowing organizational charts |
| 10 | **The Mosaic Court** | Demographics & Health Disparities | A courtyard with a living mosaic showing populations |

**Native Creatures:** **Echoes** — Friendly translucent humanoid figures that mirror emotions. Corrupted: **Echo Shades** — dark, distorted, identity confused. Freed: warm glow returns, expressions soften.

---

## LEXARA (CARS) — Sector Map

**Planet Theme:** A white-gold world of canyon libraries, paragraph towers, and flowing ink rivers. Knowledge is architecture. Reading is exploration.

| # | Sector Name | Chapter Topic | Revealed Landscape |
|---|---|---|---|
| 1 | **The Reading Hall** | Foundations of Comprehension | Grand library hall with floating, glowing books |
| 2 | **The Debate Forum** | Argument Analysis | Amphitheater where texts project visible argument structures |
| 3 | **The Hidden Passages** | Inference & Deduction | Secret corridors that reveal hidden meanings |
| 4 | **The Echo Chamber** | Tone & Rhetoric | Walls that reflect and visualize tone/emphasis |
| 5 | **The Art Gallery** | Humanities Passages | Visual arts and philosophy rendered as living paintings |
| 6 | **The Chronicle Wing** | Social Science Passages | History corridors with timeline murals |
| 7 | **The Pattern Library** | Natural Science Passages | Science texts organized as visible logical structures |
| 8 | **The Clocktower** | Timed Practice | Grand clocktower for timed CARS practice |
| 9 | **The Apex Observatory** | Advanced Reasoning | Highest point on Lexara, panoramic view, hardest passages |

**Native Creatures:** **Inklings** — Small sentient ink creatures with expressive dot-eyes. Corrupted: **Ink Blots** — dark, smeared, illegible. Freed: crisp, colorful, calligraphic forms.

---

# 8) THE RESONANCE SYSTEM (Magic / Superpowers)

## Core Fantasy
You are a superpowered Commander. The shimmer gave you **Resonance** — raw elemental force that burns away Grimble's darkness. Every correct answer channels your power. You're not passively studying — you're actively wielding magic to free worlds.

## Choose Your Resonance (Character Creation)

| Resonance | Element | Color Palette | Attack Visual |
|---|---|---|---|
| **Thermal** | 🔥 Fire | Orange-gold, ember particles | Fireball burst, flame wave |
| **Tidal** | 🌊 Water | Deep blue, mist trails | Water jet, tidal surge |
| **Cryo** | ❄️ Ice | White-blue, frost crystals | Ice shard, freeze blast |
| **Lithic** | 🪨 Earth | Amber-brown, floating debris | Rock smash, ground slam |
| **Ferric** | ⚙️ Metal | Silver-chrome, magnetic sparks | Metal spike, shrapnel burst |
| **Lumen** | ✨ Light | Soft gold-white, prismatic glow | Light beam, radiance wave |

## Abilities (Simple: 1 Primary + 1 Ultimate)

### Primary — "Strike"
- Fires automatically when you answer correctly
- Your element blasts a fog tile, clearing it with a 1-second particle VFX
- Wrong answer = strike fizzles with a "miss" effect, tile stays fogged

### Ultimate — "Surge"
- Charges when you build a **streak** (fills at 6+ correct in a row)
- Triggers: clears a **cluster of surrounding tiles** with a big, flashy animation
- Feels like a powerful combo reward — massive visual + audio payoff

### Passive — "Aura"
- Always-on glow around your Commander on the tile map
- Visual indicator of your power level / mastery
- Upgradeable cosmetically with Energy Crystals

## Upgrade System (Energy Crystals → Power Growth)

**15 total tiers across 3 tracks (5 each). Linear progression — no complex choices.**

### Strike Upgrades (5 tiers, 100–500 crystals each):
1. Base strike (single tile clear)
2. Enhanced VFX (wider visual blast)
3. Clarity Mark (cleared tiles get a subtle glow)
4. Double-strike animation on 2+ streak
5. **Legendary Strike Skin** (unique element animation)

### Surge Upgrades (5 tiers, 150–600 crystals each):
1. Base surge (small cluster clear)
2. Larger visual burst
3. LYRA voiceline trigger ("Outstanding recall, Commander!")
4. Permanent planet glow on surge-cleared areas
5. **Legendary Surge Skin** (unique element transformation)

### Aura Upgrades (5 tiers, 100–400 crystals each):
1. Faint glow
2. Particle trail (embers, snowflakes, sparks, etc.)
3. Ambient element effects around Commander
4. Full-body aura with idle animation
5. **Legendary Aura** (element-specific full transformation)

## Cosmetic Mastery Unlocks
These are earned through gameplay milestones, NOT purchased:

| Milestone | Unlock |
|---|---|
| First planet at 50% | Alternate element color (e.g., blue fire, pink ice) |
| First planet at 100% | Planet Victory Skin (Resonance takes on planet's visual theme) |
| 3 planets at 100% | Commander outfit variant |
| All bridges completed | "Bridge Walker" aura effect |
| All 7 planets at 100% | "Grimble's Bane" legendary title + prestige glow |
| Defeat Grimble (endgame) | Dark Crystal Resonance skin (your element + dark crystal aesthetic) |

---

# 9) MISSION STRUCTURE — What Happens in a Chapter

## Deployment Flow
```
Ship Dashboard → Tap Planet → Planet Map → Tap Sector → Tap Tile → MISSION START
```
**No travel animation.** Clean fade transition with a brief element-colored wash. Duolingo-speed.

## Inside a Mission — "The Guided Clearing"

### Layout
The mission screen is a **split view**:
- **Top 60%:** Lesson content area (text, diagrams, visuals, question cards)
- **Bottom 40%:** Tile map showing fog tiles being cleared in real-time as you answer

### Phase 1: LYRA Teaches (15–30 seconds per segment)
- LYRA's TTS voice plays over animated text + diagrams
- Captions display simultaneously (multi-sensory)
- Content is broken into micro-segments (~15 seconds each)
- **Lore framing:** *"Your neural map is rebuilding, Commander. This knowledge was always in you — Grimble's crystal just scattered it. Let's restore this pathway..."*

### Phase 2: Question Check (every 2–3 minutes)
- Question appears in the content area (multiple choice, drag-drop, fill-in, etc.)
- Player answers:
  - ✅ **Correct:** Commander raises hand → Resonance blast → fog tile clears → satisfying VFX + chime + XP popup
  - ❌ **Wrong:** Strike fizzles → fog pulses darker → gentle "miss" sound → LYRA reframe → tile queued for review

### Phase 3: Creature Encounter (1–3 per mission, random)
- A **corrupted native creature** emerges from a fog tile with a dark aura
- The creature blocks your next strike (you can't advance until you deal with it)
- To defeat: answer a **bonus question** (application-level, slightly harder)
  - ✅ **Defeat:** Creature's dark aura shatters → cute creature underneath is freed → comedic defeat animation → bonus XP + bonus crystals
  - ❌ **Miss:** Creature absorbs the hit, stays on tile → can try again next question OR creature retreats at mission end

### Phase 4: Mission Complete
- **Summary Screen:** Accuracy %, tiles cleared, XP earned, crystals earned, creatures freed
- **Field Notes Update:** Clean summary of chapter content auto-added to your Field Notes
- **LYRA Debrief:** *"Sector stabilized at 85%. Strong work, Commander. Grimble's hold weakens."*
- **Return to ship** with prominent "Next Mission" button

### Post-Mission Options:
1. **Continue** → next tile/sector
2. **Review** → re-clear fogged tiles from this session
3. **Ship** → return to dashboard

---

# 10) THE FOG SYSTEM (Spaced Repetition Disguised as Warfare)

## How Fog Maps to Mastery

Each tile = a lesson/concept. Your accuracy on that tile = your mastery of that concept.

### During Mission:
- **Correct answer** → tile clears, planet surface revealed
- **Wrong answer** → tile stays fogged, queued for review
- **End of mission:** Your accuracy % = the % of tiles cleared
  - 100% accuracy = all tiles clear = full sector glow
  - 75% accuracy = 75% clear, 25% still fogged
  - 50% = half remain dark

### Fog Reclamation (Spaced Repetition):

| Your Accuracy | Fog Returns After | Alert Level |
|---|---|---|
| 100% | 5–7 days | Gentle: *"Fog stirring in [sector]"* |
| 80–99% | 3–4 days | Moderate: *"[Specialist] requests backup"* |
| 60–79% | 1–2 days | Urgent: *"Grimble reclaiming [sector]!"* |
| < 60% | Same day | Critical: *"Signal lost in [sector]"* |

### When Fog Returns:
The specialist on that planet sends an in-game notification:
> *"Commander, Grimble's fog is creeping back into the Synapse Network. A quick memory sweep should hold it. — Dr. Kade"*

The **memory sweep** is a quick review mission: 5–10 rapid-fire recall questions on that tile's content. Fast, focused, no new content — pure retention reinforcement.

### Why This Works:
- Players SEE mastery visually (clear planet = strong knowledge)
- Fog return IS spaced repetition — players don't know they're being "drilled"
- Creates natural return loops ("defend your territory")
- High accuracy = longer peace = feels rewarding
- Low accuracy = fog comes back faster = natural corrective pressure

---

# 11) CREATURE SYSTEM

## Design Philosophy
Think "Duolingo owl gone evil" — cute enough to adore, distinct per planet, thematically connected to the subject. They are **corrupted native creatures**, not invaders. Defeating them FREES them, not kills them.

## Creature Table

| Planet | Native | Corrupted Form | Visual | Ability (triggers bonus Q) |
|---|---|---|---|---|
| Verdania | Sproutlings | Blight Sprouts | Dark plant, foggy eyes, wilted petals | **Root Tangle** — blocks your tile |
| Glycera | Glowmites | Rust Mites | Corroded amber bugs, erratic | **Pathway Jam** — clogs your next strike |
| Luminara | Sparklings | Flicker Imps | Glitchy neon sprites | **Unstable Reaction** — backfires your strike |
| Synthara | Cave Wisps | Gloom Bats | Dark bats, disoriented | **Mechanism Scramble** — scrambles tile progress |
| Aethon | Windlings | Drift Wraiths | Chaotic dark wisps | **Vector Shift** — pushes strike off target |
| Miravel | Echoes | Echo Shades | Distorted shadow figures | **Identity Confusion** — disguises answer choices |
| Lexara | Inklings | Ink Blots | Smeared dark ink puddles | **Redaction** — blacks out part of question text |

## Creature Variation (within each planet)
To avoid 20 clones on screen, each planet has **3 visual variants**:
1. **Scout** (small, simple, 1 bonus question to clear)
2. **Warden** (medium, slightly different colors/features, also 1 bonus question but worth more XP)
3. **Captain** (larger, distinct markings, may require 2 consecutive correct answers to free)

## Defeat Animations (comedic, cozy)
- **Blight Sprout:** Dark aura pops off like a sneeze, sproutling shakes itself clean and does a little happy dance
- **Rust Mite:** Corrosion flakes off revealing shiny amber shell, mite chirps happily
- **Flicker Imp:** Stabilizes with a satisfying "click," does a little bow
- **Gloom Bat:** Shadow dissolves revealing iridescent wings, does a barrel roll of joy
- **Drift Wraith:** Snaps back to stable hover, does a graceful loop
- **Echo Shade:** Dark distortion clears revealing warm translucent form, waves at you
- **Ink Blot:** Splashes into a colorful smiley face puddle, reforms as a crisp little inkling

---

# 12) ENERGY SYSTEM — "Neural Charge"

## Purpose
Prevents cognitive fatigue/cramming. Forces healthy study spacing. Keeps the game sustainable.

| Element | Detail |
|---|---|
| **Max Charges** | 6 (upgradeable to 8 via crystals) |
| **Cost: Guided Learning** | 1 charge per mission |
| **Cost: Review Missions** | FREE (always accessible) |
| **Cost: Mem-Games** | FREE (2-4 per chapter, always playable) |
| **Regeneration** | 1 charge every 2 hours (full refill ~12 hours) |
| **Refill via crystals** | Quick Charge (1): 50 crystals / Full Charge: 250 crystals |

## Why This Works
- **Energy empty?** → Player naturally shifts to free review/mem-games (reinforcement!)
- **Prevents cramming** (which hurts retention anyway)
- **Encourages spaced sessions** (play 3 missions → come back → play 3 more)
- **Never feels punishing** — there's always something to do at 0 energy

---

# 13) ECONOMY — Energy Crystals (Single Currency)

## Earning

| Source | Crystals |
|---|---|
| Complete Guided Learning mission | 30–50 (scaled by accuracy) |
| 100% accuracy bonus | +25 |
| Defeat a creature (bonus Q) | +10 each |
| Complete a Mem-Game | 10–20 |
| Complete a Bridge Mission | 40–60 |
| Daily login | 15 |
| Defend fog reclamation (review) | 20–30 |
| 3-question streak | +5 bonus |
| 6-question streak | +15 bonus |
| 10-question streak | +30 bonus |
| Streak milestone (7 days) | 100 |
| Streak milestone (30 days) | 300 |
| Streak milestone (100 days) | 1000 |

## Spending

Accessed via **"✨ Powers"** button on Ship Dashboard. Clean card-based UI with 3 tabs:

**Tab 1 — Upgrades:**
- Strike tiers (100–500 per tier)
- Surge tiers (150–600 per tier)
- Aura tiers (100–400 per tier)
- Energy capacity upgrade (500 crystals: 6→7, 750: 7→8)

**Tab 2 — Cosmetics:**
- Element color variants (300–600)
- Commander outfit variants (400–800)
- Planet-themed decorations (300–500)

**Tab 3 — Items:**
- Streak Freeze (200 crystals, max hold 2)
- Quick Energy Charge (50 crystals for 1 charge)
- Full Energy Charge (250 crystals)

---

# 14) STREAK & REWARD SYSTEM

## Daily Streak
- Play at least 1 mission OR 1 review = streak maintained
- Visible on Ship Dashboard (flame icon + day count)
- **Streak Freeze:** Buy with 200 crystals, holds 1 missed day, max 2 in inventory

## Streak Milestone Rewards

| Days | Reward |
|---|---|
| 3 | 50 crystals + "Warming Up" badge |
| 7 | 100 crystals + Aura particle upgrade |
| 14 | 200 crystals + Element color variant |
| 30 | 500 crystals + Legendary Strike skin |
| 60 | 1000 crystals + Commander outfit |
| 100 | 2000 crystals + "Grimble's Bane" title + unique aura |

## Question Streak Bonuses (in-mission)

| Streak | Reward | Sound/Visual |
|---|---|---|
| 3 correct | +5 crystals | Ascending 3-note chime, "NICE!" text pop, tile glow pulse |
| 6 correct | +15 crystals | Energetic 6-note fanfare, "ON FIRE!" text, screen edge glow, Surge charges faster |
| 10 correct | +30 crystals | Epic orchestral hit, "UNSTOPPABLE!" text, full-screen Resonance burst, instant Surge ready |

## Planet Mastery Rewards

| % Cleared | Reward |
|---|---|
| 25% | Specialist companion portrait unlocked |
| 50% | Planet-themed Commander cosmetic |
| 75% | Legendary creature defeat animation |
| 100% | Planet Victory Skin (Resonance takes on planet's visual theme) |

---

# 15) FIELD NOTES & NOTEBOOK

## Field Notes (Auto-Generated)
After every Guided Learning mission, a clean summary is auto-added.

**Structure:**
- Organized by: Planet → Sector → Tile
- Each entry contains:
  - Key concepts (bulleted)
  - Important equations / pathways / terms
  - Your accuracy % and date completed
  - Fog status indicator (clear / stirring / reclaimed)

**Lore:** LYRA frames it as *"Your neural archive, Commander. Everything we reconstruct from the fracture is logged here."*

## Personal Notebook (Player-Created)
- Create custom **folders** and **notes**
- Rich text: bold, highlight, bullet points, color coding
- Organize however the student wants
- **Accessible during missions** (slide-out panel) for on-the-fly note-taking
- Search function across all notes
- Accessible from Ship Dashboard via 📓 button

---

# 16) BRIDGE MISSIONS (Cross-Subject Mastery)

## What They Are
Short cross-subject challenges proving transfer of knowledge — the skill Grimble's crystal specifically targets.

## Unlock Trigger
Available when you've cleared at least 1 sector in BOTH connected subjects. LYRA suggests them:
> *"Commander, I'm detecting a signal bridge between amino acid structure and organic functional groups. Clearing this weakens Grimble's grip on both worlds."*

## Format (3–5 minutes)
1. LYRA brief (15 sec): explains the cross-subject connection
2. 3–5 hybrid questions (concepts from both subjects)
3. 1 rapid memory match (connect terms across subjects)

## Rewards
- 40–60 Energy Crystals
- Permanent **Bridge Link** on ship map (visible connection line between planets)
- Bonus planet cosmetic (bridge-themed decoration)
- Bridge links are **permanent** — Grimble can't reclaim them. True understanding endures.

---

# 17) SOUND & MUSIC DESIGN

## Planet Music (Unique per World)

| Planet | Music Style | Mood |
|---|---|---|
| **Verdania** | Soft acoustic + nature ambience, gentle woodwinds | Peaceful forest morning |
| **Glycera** | Lo-fi synth + organic pads, flowing rhythms | Warm laboratory groove |
| **Luminara** | Crystal chimes + electronic arpeggios | Energetic, prismatic |
| **Synthara** | Ethereal cave echoes + soft percussion | Mysterious, beautiful |
| **Aethon** | Open orchestral + wind instruments | Vast, empowering |
| **Miravel** | Warm jazz-inspired + city ambient | Cozy, humanistic |
| **Lexara** | Gentle piano + string quartet | Elegant, scholarly |
| **Ship Dashboard** | Soft ambient space + warm synth pads | Home, safety |

## Combat / Spell Sounds

| Action | Sound |
|---|---|
| **Thermal Strike** | Whooshing fireball + impact crackle |
| **Tidal Strike** | Rushing water + splash |
| **Cryo Strike** | Crystalline shatter + ice crack |
| **Lithic Strike** | Deep rumble + stone impact |
| **Ferric Strike** | Metallic clang + magnetic hum |
| **Lumen Strike** | Bright chime + light burst |
| **Surge (any)** | Building energy → massive elemental explosion |
| **Strike Fizzle (wrong)** | Soft dampened thud + fading spark |

## Creature Sounds

| Event | Sound |
|---|---|
| Creature appears | Low rumble + dark crystal hum |
| Creature ability triggers | Short menacing chord + ability-specific SFX |
| Creature defeated/freed | Dark shatter → cute chirp/chime as creature reverts |

## Question Feedback Sounds

| Event | Sound + Visual |
|---|---|
| **Correct** | Bright ascending chime + green flash + XP pop |
| **Wrong** | Soft descending tone + subtle red pulse + LYRA reframe |
| **3-streak** | Three ascending notes + "NICE!" text pop + tile glow |
| **6-streak** | Six-note fanfare + "ON FIRE!" + screen edge warm glow |
| **10-streak** | Epic orchestral hit + "UNSTOPPABLE!" + full screen Resonance burst |

---

# 18) UI / UX FLOW — Complete App Map

```
┌─ INTRO (first time only) ─────────────────────────────┐
│  Illustrated cutscene (panels + TTS) → Character       │
│  Selection → Resonance Selection → Ship Dashboard      │
└────────────────────────────────────────────────────────┘

┌─ SHIP DASHBOARD (Home) ────────────────────────────────┐
│                                                         │
│  [Glass Deck View — 7 planets visible through window]   │
│                                                         │
│  Top Bar: ☰ Menu | ⚡ Energy 4/6 | 🔥 Streak: 12      │
│  Currency: ✨ 2,450 crystals                            │
│                                                         │
│  Main Buttons:                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │▶ CONTINUE│ │🪐 PLANETS│ │🔄 REVIEW │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │📓 NOTES  │ │✨ POWERS │ │👤 PROFILE│               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                         │
│  Bottom: Commander portrait + name + Resonance icon     │
└────────────────────────────────────────────────────────┘

┌─ PLANETS VIEW ─────────────────────────────────────────┐
│  7 planet cards/icons with:                             │
│  - Planet name + subject label                          │
│  - Progress ring (% cleared)                            │
│  - Fog status indicator                                 │
│  - Specialist portrait                                  │
│  - "Recommended" tag on next best planet                │
│  Tap planet → PLANET MAP                                │
└────────────────────────────────────────────────────────┘

┌─ PLANET MAP (large, scrollable/pannable) ──────────────┐
│  Full illustrated tile map of the planet                │
│  - Sectors labeled with chapter names                   │
│  - Tiles: dark/fogged (locked) or vibrant (cleared)     │
│  - Creature icons on corrupted tiles                    │
│  - Stronghold at center (specialist's base)             │
│  - Bridge connection points at sector edges             │
│  Tap tile → MISSION START (instant transition)          │
└────────────────────────────────────────────────────────┘

┌─ MISSION (Guided Clearing) ────────────────────────────┐
│  TOP: Lesson content (text + diagrams + TTS)            │
│  BOTTOM: Tile progress map (fog clearing in real-time)  │
│  SIDE: Notebook slide-out panel (optional)              │
│                                                         │
│  Loop: Teach → Question → Strike/Fizzle → Repeat       │
│  Creatures: appear randomly, trigger bonus questions    │
│  End: Summary → Field Notes update → Rewards            │
└────────────────────────────────────────────────────────┘

┌─ POST-MISSION ─────────────────────────────────────────┐
│  Accuracy %, Tiles cleared, XP, Crystals earned         │
│  Creatures freed count                                  │
│  Streak status                                          │
│  Buttons: [Continue] [Review] [Ship]                    │
│  Optional: Bridge Mission suggestion if available       │
└────────────────────────────────────────────────────────┘

┌─ POWERS (Shop replacement) ────────────────────────────┐
│  Tab 1: Upgrades (Strike/Surge/Aura tiers)              │
│  Tab 2: Cosmetics (colors, outfits, planet skins)       │
│  Tab 3: Items (Streak Freeze, Energy Refill)            │
│  Clean card UI, tap to preview, tap to buy              │
└────────────────────────────────────────────────────────┘

┌─ NOTES ────────────────────────────────────────────────┐
│  Tab 1: Field Notes (auto, organized by planet/sector)  │
│  Tab 2: My Notebook (player-created folders + notes)    │
│  Search bar across all notes                            │
└────────────────────────────────────────────────────────┘

┌─ PROFILE ──────────────────────────────────────────────┐
│  Commander portrait + name + Resonance display          │
│  Overall stats (total mastery %, planets cleared, etc.) │
│  Streak history                                         │
│  Achievement badges                                     │
│  Equipped cosmetics                                     │
└────────────────────────────────────────────────────────┘
```

---

# 19) ENDGAME — DEFEATING GRIMBLE

## Unlock Condition
**All 7 planets must be at 100% mastery** (all tiles cleared, all sectors stabilized). This means the player has:
- Completed every Guided Learning mission
- Cleared all fog
- Maintained mastery long enough for the game to confirm retention

When this threshold is met, LYRA announces:
> *"Commander... Grimble's Dark Crystal is fracturing. His grip on the system is failing. For the first time, I'm detecting his location. He's retreating to the void between worlds. We can end this. Are you ready?"*

## The Final Mission
- A special one-time mission accessible from the Ship Dashboard
- **Format:** A comprehensive review challenge pulling questions from ALL 7 subjects
- **Length:** 30–50 questions across all domains (the ultimate knowledge check)
- **Mechanics:** Same tile-clearing system but on a special "Dark Crystal Core" map
- Each correct answer cracks the Dark Crystal further
- Grimble taunts you throughout, increasingly desperate
- At 100% accuracy: the Dark Crystal shatters completely
- **Cinematic ending:** Grimble's fog dissolves across all 7 planets simultaneously. The planets burst into full vibrant color. Specialists celebrate. LYRA delivers a final message.

## Post-Endgame
- **All planets remain fully playable** — fog still reclaims over time
- The game continues as a mastery maintenance tool
- Grimble is "defeated" but the fog mechanic persists (knowledge needs upkeep)
- LYRA reframes it: *"Grimble is gone, but knowledge fades without practice, Commander. Keep the signal strong."*
- Players can replay the final mission for fun/achievement

---

# 20) COMPLETE GAMEPLAY LOOP

```
DAILY LOOP (~15-30 min):
1. Open app → Ship Dashboard
2. Check: streak status, fog alerts, energy level
3. Tap "Continue" (or choose planet manually)
4. Deploy to mission (instant) → Guided Clearing
   - LYRA teaches via TTS (15-sec segments)
   - Questions every 2-3 min → Strike/Fizzle
   - Creatures appear → bonus questions
   - 2-6 min per mission → micro-win
5. Mission complete → rewards → Field Notes update
6. Continue / Review / Return to Ship
7. If energy remains → more missions
8. If energy empty → free Review or Mem-Games
9. Check Powers → upgrade if enough crystals
10. Close app → streak maintained ✓

WEEKLY LOOP:
- Fog reclamation alerts → review missions (free)
- Bridge Missions unlock → cross-subject wins
- Streak milestones → cosmetic rewards
- Planet % grows → visible world transformation

MONTHLY ARC:
- Planets transforming from dark to vibrant
- Commander power visibly growing
- Grimble's territory shrinking on the system map
- Full planet clears → major celebrations

ENDGAME (after months of mastery):
- All 7 planets at 100%
- Final Grimble confrontation unlocks
- Defeat Grimble → ultimate reward
- Continue for maintenance + prestige
```

---

# 21) WHAT'S STILL NEEDED

## ✅ Fully Defined
- Antagonist (Grimble) — name, personality, art direction, dialogue, Dark Crystal
- Player Character — selection, names, Resonance choice
- LYRA — role, personality, TTS integration, lore connection, dialogue
- 7 Specialists — identity, role, alert system
- 7 Planets — names, themes, ALL sector reveals, native creatures
- Resonance System — 6 elements, 2 abilities, 15-tier upgrade path, cosmetic unlocks
- Mission Structure — full guided clearing loop, phases, creature encounters
- Fog System — accuracy mapping, reclamation timers, review missions
- Creature System — 7 types, 3 variants each, abilities, defeat animations
- Energy System — charges, costs, regen, refills
- Economy — single currency, earn/spend rates, shop replacement
- Streak System — daily streak, milestones, in-mission streaks, bonuses
- Field Notes + Notebook — auto-generated + player-created
- Bridge Missions — format, triggers, rewards
- Sound Design — per-planet music, combat SFX, feedback sounds
- UI/UX Flow — complete app map
- Endgame — Grimble confrontation, post-game
- Complete Gameplay Loop — daily/weekly/monthly/endgame

## 🟡 Partially Defined (need specifics during development)
- Intro cutscene script (deferred until design is final)
- Exact Kaplan chapter-to-sector mapping (depends on your content pipeline)
- Mem-Game types (you have 7 ready — account for 2-4 per chapter in rewards)
- Creature art assets (descriptions done, actual illustrations needed)
- Planet map illustrations (descriptions done, actual art needed)
- TTS voice generation (LYRA script templates done, actual voice needed)
- Exact spaced repetition algorithm (timers defined, exact decay curve TBD)

## 🔴 Not Yet Defined
- Accessibility features (colorblind modes, font sizing, screen reader support)
- Notification system (push vs. in-app only for fog alerts)
- Onboarding tutorial (first 5 minutes of guided experience)
- Social features (leaderboards, study groups, sharing — if any)
- Monetization model (free? freemium? one-time purchase?)
- Analytics/tracking (what data to collect for learning optimization)
- Offline mode (can players study without internet?)
