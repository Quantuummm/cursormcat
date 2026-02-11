# MCAT Mastery

**The world's first ADHD-friendly, gamified MCAT tutor — disguised as an interplanetary adventure.**

> *"Reclaim the Light. Defeat Grimble."*

You play as a Commander, woken from cryo-sleep by your AI companion **LYRA**, to reclaim seven corrupted planets — each representing an MCAT subject. Every correct answer fires your Resonance element, clears fog from the planet surface, and rebuilds your fractured memory. The villain **Grimble** (a theatrical, plushie-worthy overlord) constantly tries to reclaim territory with his Dark Crystal. Spaced repetition *is* the fog. You never know you're being drilled.

---

## Table of Contents

1. [Project Purpose & Origin](#1-project-purpose--origin)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Pipeline Phase Map (Phases 0–11)](#4-pipeline-phase-map-phases-011)
5. [Phase-by-Phase Deep Dive](#5-phase-by-phase-deep-dive)
6. [Step-by-Step Guide: Phase 9 → Phase 11 (No Way You Mess Up)](#6-step-by-step-guide-phase-9--phase-11)
7. [Testing & Demo (Post-Pipeline)](#7-testing--demo-post-pipeline)
8. [Front-End Design Bible](#8-front-end-design-bible)
9. [Front-End Build Plan & Tooling Options](#9-front-end-build-plan--tooling-options)
10. [iOS App & Cross-Platform Sync](#10-ios-app--cross-platform-sync)
11. [Google Cloud Hosting & Deployment](#11-google-cloud-hosting--deployment)
12. [Game Mechanics Deep Dive](#12-game-mechanics-deep-dive)
13. [Lore, Characters & World](#13-lore-characters--world)
14. [Audio System (TTS + Music + SFX)](#14-audio-system-tts--music--sfx)
15. [Future Roadmap](#15-future-roadmap)
16. [Folder Organization](#16-folder-organization)
17. [Key Scripts & Tools](#17-key-scripts--tools)
18. [AI Agent Startup Protocol](#18-ai-agent-startup-protocol)
19. [Contributing & Best Practices](#19-contributing--best-practices)

---

## 1. Project Purpose & Origin

This project transforms **7 Kaplan MCAT review PDFs** (Biology, Biochemistry, Gen Chem, Org Chem, Physics, Psych/Soc, CARS) into a fully interactive, gamified learning application. The pipeline:

1. **Extracts** raw content from PDFs (text, figures, glossaries, assessments)
2. **Restructures** it into ADHD-optimized "Guided Learning" micro-lessons (~15-second TTS segments + immediate comprehension checks)
3. **Generates** deterministic game modes (Definition Match, Process Sorter, Table Drill, Figure Label)
4. **Enriches** with cross-subject Bridge Missions, multi-voice TTS audio, and creature encounters
5. **Uploads** everything to Firebase Firestore for a web + mobile front-end to consume

### Core Design Pillars

| Pillar | Description |
|--------|-------------|
| **ADHD-First** | ~15-second micro-lessons. Questions every 2-3 min. Instant feedback. Multi-sensory (TTS + visuals + animations + sounds). |
| **Cozy & Addictive** | Warm visuals, satisfying sounds, visible progress, rewarding loops. Never punishing. |
| **Simple to Build** | 2D/2.5D web app. Tile-based maps. CSS animations. No game engine required. |
| **Autonomy** | Recommended path, never forced. Player chooses what to study. |
| **Disguised Spaced Rep** | Fog reclamation = forced review. Players never feel drilled. |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PDF SOURCE FILES                         │
│            (7 Kaplan MCAT Review Books in pdfs/)            │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  EXTRACTION PIPELINE │
              │  Phases 0–5          │
              │  (PyMuPDF + Gemini)  │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  REFINEMENT PIPELINE │
              │  Phases 6–8.2        │
              │  (Gemini + Python)   │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  DELIVERY PIPELINE   │
              │  Phases 9–11         │
              │  (Gemini + GCloud)   │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌─────▼─────┐   ┌─────▼─────┐
    │Firestore│    │Cloud TTS  │   │Cloud       │
    │(Content)│    │(Audio MP3)│   │Storage     │
    │         │    │           │   │(Figures)   │
    └────┬────┘    └─────┬─────┘   └─────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────▼──────────┐
              │    FRONT-END APP     │
              │  Web (PWA) + iOS     │
              │  React/Next.js       │
              │  Firebase Auth       │
              └─────────────────────┘
```

---

## 3. Tech Stack

### Backend Pipeline
| Component | Technology |
|-----------|-----------|
| Orchestration | Custom Python pipeline (`scripts/run_pipeline.py`) |
| AI Primary | `gemini-3-flash-preview` (all extraction + creative tasks) |
| AI Fallback | `gemini-2.5-flash` (auto-failover for safety filters/rate limits) |
| PDF Engine | PyMuPDF (raw text + image extraction) |
| Rate Limiting | 14 RPM (free tier safe), ~4.3s between requests |
| Checkpointing | `pipeline_checkpoint.json` — resume-safe after crashes |

### Cloud Infrastructure
| Component | Technology |
|-----------|-----------|
| Database | Firebase Firestore |
| Auth | Firebase Authentication (Anonymous → Email/Google) |
| File Storage | Google Cloud Storage (figures, audio MP3s) |
| TTS | Google Cloud Text-to-Speech (Studio/Journey Neural2 voices) |
| Hosting | Google Cloud Run or Firebase Hosting |
| Domain | Custom domain via Google Cloud DNS |

### Front-End (Current Prototype)
| Component | Technology |
|-----------|-----------|
| Framework | Vanilla HTML/CSS/JS (prototype) |
| Fonts | Fredoka One (headings), Nunito (body) |
| Firebase SDK | v10.12.0 compat |
| CSS Architecture | CSS Variables, BEM-inspired, data-attribute theming |

---

## 4. Pipeline Phase Map (Phases 0–11)

| Phase | Title | Type | Core Function | Primary Output |
|-------|-------|------|---------------|----------------|
| **0** | Extract Images | `deterministic` | PyMuPDF raw figure extraction | `phases/phase0/output/assets/` |
| **1** | Extract TOC | `AI` | Chapter titles, sections, metadata | `phases/phase1/output/extracted/` |
| **2** | Extract Assessments | `AI` | Chapter diagnostic MCQs | `phases/phase2/output/extracted/` |
| **3** | Extract Sections | `AI` | Full text blocks, equations, concept checks, shared concepts | `phases/phase3/output/extracted/` |
| **4** | Extract Glossary | `AI` | Term/definition pairs per book | `phases/phase4/output/extracted/` |
| **5** | Catalog Figures | `AI` | Match figure IDs/captions to extracted images | `phases/phase5/output/extracted/` |
| **6** | Enrich Wrong Answers | `AI` | Generate per-option wrong-answer explanations | `phases/phase6/output/enriched/` |
| **6.1** | Verify Wrong Answers | `AI loop` | Audit + auto-fix wrong-answer explanations | `phases/phase6_1/output/verified/` |
| **7** | Build Primitives | `deterministic` | Typed game objects (terms, processes, tables, figures) | `phases/phase7/output/primitives/` |
| **8** | Restructure Guided Learning | `AI` | ADHD-optimized micro-lessons with levels | `phases/phase8/output/structured/` |
| **8.1** | Compile Modes | `deterministic` | Engine-ready game mode payloads | `phases/phase8_1/output/compiled/` |
| **8.2** | Verify & Fix Guided Learning | `AI loop` | Audit + auto-fix structured content JSON | `phases/phase8_2/output/verified/` |
| **9** | Enrich Bridges | `AI` | Cross-subject bridge missions | `phases/phase9/output/bridges/` |
| **10** | Generate TTS | `Cloud API` | Multi-voice MP3 audio files | `phases/phase10/output/audio/` |
| **11** | Upload to Firestore | `Cloud API` | Push all data to production database | Firebase Firestore |

---

## 5. Phase-by-Phase Deep Dive

### Phases 0–5: Ingestion
Raw PDFs → structured JSON. Each chapter is split into sections with learning objectives, content blocks, equations, concept checks, and shared concepts (cross-book references).

### Phase 6 + 6.1: Wrong-Answer Enrichment
Every MCQ distractor gets a personalized explanation of *why* it's wrong (not just "incorrect"). Phase 6.1 runs a verify-fix loop to catch AI errors.

### Phase 7: Build Primitives (No AI)
Pure Python logic that categorizes extracted content into typed game objects:
- **TermPrimitive**: Key term + definition pairs → Definition Match game
- **ProcessPrimitive**: Ordered steps → Process Sorter game
- **TablePrimitive**: Key-value data → Table Drill game
- **FigurePrimitive**: Labeled diagram → Figure Label game

### Phase 8 + 8.2: Guided Learning Restructure
The signature ADHD-first format. Each section becomes a "concept" with 3-5 levels:
```
Level → Learn Segments (TTS narration, ~15s each)
      → Check Questions (comprehension MCQs)
      → Apply Question (scenario-based boss challenge)
      → Creature Encounter (optional bonus question)
      → Pro Tips (LYRA's coaching notes)
```
Phase 8.2 runs a verify-fix loop against the original extraction to catch hallucinations.

### Phase 8.1: Compile Modes
Turns Phase 7 primitives into engine-ready game payloads with all the UI data the front-end needs.

---

## 6. Step-by-Step Guide: Phase 9 → Phase 11

> **Prerequisites**: All 7 books completed through Phase 8.2. Structured content in `phases/phase8_2/output/verified/` (or `phases/phase8/output/structured/` fallback) and compiled modes in `phases/phase8_1/output/compiled/`.

---

### PHASE 9: Enrich Bridges

**What it does**: Scans ALL books' shared_concepts and generates cross-subject Bridge Missions — MCAT-style questions requiring knowledge from two subjects.

**Prerequisites**:
- Phase 3 complete for ALL books (needs `shared_concepts` in chapter JSONs)
- Gemini API key in `.env`

**Steps**:

```bash
# Step 1: Verify shared_concepts data exists
python scripts/check_phase_outputs.py

# Step 2: Run Phase 9 (no PDF argument — processes ALL books at once)
python phases/phase9/phase9_enrich_bridges.py

# OR via pipeline:
python scripts/run_pipeline.py --phase 9
```

**What to expect**:
- Collects shared_concepts from every chapter JSON across all 7 books
- Deduplicates A↔B pairs
- Calls Gemini for each unique pair with `bridge_enrichment.txt` prompt
- Saves to `phases/phase9/output/bridges/`
- Builds bridge graph: `phases/phase9/output/bridges/_bridge_graph.json`

**Verify**:
```bash
dir phases\phase9\output\bridges\*.json /b | find /c /v ""
python -c "import json; g=json.load(open('phases/phase9/output/bridges/_bridge_graph.json')); print(f'Nodes: {g[\"total_nodes\"]}, Edges: {g[\"total_edges\"]}')"
```

---

### PHASE 10: Generate TTS Audio

**What it does**: Multi-voice MP3 audio via Google Cloud TTS. Each character gets unique voice/pitch/speed.

**Prerequisites**:
- Phase 8/8.2 complete
- Google Cloud project with TTS API enabled
- Service account JSON with TTS permissions
- `pip install google-cloud-texttospeech`

**One-time setup**:
```bash
pip install google-cloud-texttospeech

# Enable TTS API: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
# Create service account → Download JSON key
# Update .env:
#   GOOGLE_CLOUD_PROJECT_ID=your-project-id
#   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
```

**Run**:
```bash
# All subjects
python phases/phase10/phase10_generate_tts.py

# One subject (saves credits during testing)
python phases/phase10/phase10_generate_tts.py biology

# Via pipeline
python scripts/run_pipeline.py --phase 10
```

**Cost**: ~$16/1M chars, ~$56 total. Skip during dev — browser TTS fallback works.

**Output**: `phases/phase10/output/audio/{subject}/{concept_id}/*.mp3`

---

### PHASE 11: Upload to Firestore

**What it does**: Pushes ALL data (13 categories) to Firebase Firestore.

**Prerequisites**:
- All content phases complete
- Firebase project with Firestore in Native mode
- `pip install firebase-admin`
- `.env` has `GOOGLE_CLOUD_PROJECT_ID` and `GOOGLE_APPLICATION_CREDENTIALS`

**One-time setup**:
```bash
pip install firebase-admin

# Create Firebase project: https://console.firebase.google.com
# Enable Firestore → Native mode
# Ensure service account has "Cloud Datastore User" role
```

**Run**:
```bash
# ALWAYS dry-run first
python phases/phase11/phase11_upload_firestore.py --dry-run

# Lore only (game config, no content)
python phases/phase11/phase11_upload_firestore.py --lore-only

# One subject
python phases/phase11/phase11_upload_firestore.py biology

# Everything
python phases/phase11/phase11_upload_firestore.py
```

**What gets uploaded** (13 categories):

| Collection | Source | Content |
|------------|--------|---------|
| `game_config/world` | `lore/world.json` | Core settings, subjects |
| `characters/*` | `lore/characters/` | LYRA, Grimble, commanders, specialists |
| `planets/*` | `lore/planets/` | Planet configs, sector counts |
| `game_config/creatures` | `lore/creatures.json` | Creature types/variants |
| `game_systems/*` | `lore/systems/` | Resonance, economy, energy, streaks, fog, progression |
| `audio_config/*` | `lore/audio/` | TTS voices, music/SFX |
| `concepts/*` | Phase 8/8.2 | Guided learning (levels as subcollection) |
| `compiled_modes/*` | Phase 8.1 | Game payloads (instances as subcollection) |
| `glossaries/*` | Phase 4 | Per-subject glossary |
| `assessments/*` | Phase 2/6 | Diagnostic MCQs |
| `equations/*` | Phase 3 | Per-chapter equations |
| `figures/*` | Phase 5 | Figure catalog |
| `bridge_missions/*` | Phase 9 | Cross-subject bridges + graph |

---

## 7. Testing & Demo (Post-Pipeline)

### Console Demo
```bash
python scripts/demo_pipeline_output.py gen_chem 1.1
```
Interactive terminal walkthrough — types out narration, presents questions, shows feedback.

### 3-Layer Content Verification
```bash
python scripts/verify_content.py biology 1.1   # One section
python scripts/verify_content.py biology 1      # One chapter
python scripts/verify_content.py biology        # All sections
```

### Front-End Testing
```bash
cd frontend && npx serve .
# OR: python -m http.server 8080
```

### Game Logic Checklist
- [ ] Correct answers: XP popup, crystal popup, streak++, fog clears
- [ ] Wrong answers: LYRA reframes, tile stays fogged, streak resets
- [ ] Streaks: 3→"NICE!", 6→"ON FIRE!", 10→"UNSTOPPABLE!"
- [ ] Creatures: Block tiles, bonus questions to free them
- [ ] Energy: Missions cost 1, reviews FREE
- [ ] Fog reclamation: Tiles fog based on accuracy/time
- [ ] Bridge missions: Cross-subject questions
- [ ] TTS: Browser fallback + Cloud MP3 when available
- [ ] Persistence: localStorage + Firebase sync

---

## 8. Front-End Design Bible

### The Experience: Loading → Defeating Grimble

**Loading Screen**: Deep space gradient, shimmer loading bar, thematic status messages ("Waking Commander from cryo-sleep..."). Feels like booting a spaceship, not a study app.

**Character Select**: 2×2 grid, 4 diverse commanders (Clash Royale proportions), 6 Resonance elements. Identity creation = ownership = retention.

**Ship Dashboard**: HUD (crystals✨, energy⚡, streak🔥) + LYRA greeting + 7 planet orbit + Notebook/Shop/Bridges. "Home" feeling — Stardew Valley's farm as a spaceship.

**Planet Map**: Sector tabs + tile grid. Fogged tiles = dark/blurred, cleared = vibrant/glowing. The map IS the progress bar — fog lifting off tiles is the core reward.

**Mission**: 15-second learn → check question → feedback → repeat. Constant dopamine micro-hits. Never punishment for wrong answers (LYRA reframes).

**Endgame**: All 7 planets at 100% → Dark Crystal Core mission → 30-50 all-subject questions → Grimble defeated → cinematic fog dissolve.

### Design Choices

| Choice | Reasoning |
|--------|-----------|
| Dark background (#0D1117) | Reduces eye strain, cinematic mood for long study sessions |
| Fredoka One fonts | Rounded, friendly — says "game" not "homework" |
| <1s animations | ADHD impatience threshold — never wait |
| No punishment VFX | Soft pulse, never screen shake — reduces anxiety |
| Planet-specific colors | Subject identity through color alone (7 unique palettes) |
| Crystal gold (#FFD700) | Psychologically associated with value |
| LYRA blue (#58A6FF) | Calming authority for teaching |
| Grimble purple (#8B5CF6) | Mystical threat, never harsh |
| `prefers-reduced-motion` | Full a11y support — all animations collapse |

### Inspirations
- **Duolingo**: Streak obsession, bite-sized lessons, encouraging tone
- **Stardew Valley**: Cozy warmth, low-stress progression  
- **Clash Royale**: Cartoon-bold characters, colorful UI
- **Cortana/Ghibli**: LYRA's warm holographic presence

---

## 9. Front-End Build Plan & Tooling Options

### Option A: Next.js + React (RECOMMENDED)
```
Next.js 14+ (App Router) | React 18 | Tailwind CSS | Framer Motion
Zustand (state) | Firebase JS SDK | next-pwa
Deploy: Cloud Run or Firebase Hosting
```
Best for production-grade PWA. SSR for fast loads. Image optimization. Easy Docker→Cloud Run.

### Option B: Vite + React (Lighter)
```
Vite 5+ | React 18 | Tailwind CSS | Framer Motion | Zustand | Firebase
Deploy: Firebase Hosting (static)
```
Faster dev iteration, no SSR (fine for a game app).

### Option C: Flutter Web + iOS (Single Codebase)
```
Flutter 3.x | Dart | Riverpod | cloud_firestore | flutter_tts
Deploy: Firebase Hosting (web) + App Store (iOS)
```
True native, single codebase, but Dart learning curve.

### Recommended: Next.js (Web PWA) + React Native Expo (iOS)
70% shared logic. Same Firebase backend. Synced progress across platforms.

---

## 10. iOS App & Cross-Platform Sync

Both web and iOS share a single Firebase backend. **Firebase Auth** provides the same UID across platforms. **Firestore `players/{uid}`** stores all progress. Real-time `onSnapshot` listeners for instant sync. Offline persistence queues writes.

iOS-specific: Push notifications for fog alerts, haptic feedback on correct answers, native audio via AVAudioPlayer, Apple Sign-In.

---

## 11. Google Cloud Hosting & Deployment

```bash
# Firebase Hosting (simplest)
firebase init hosting && firebase deploy

# Cloud Run (containerized, more control)
docker build -t mcat-mastery . && gcloud run deploy mcat-mastery --image gcr.io/PROJECT/mcat-mastery

# Custom domain: Add in Firebase/Cloud Run console → verify DNS → auto-SSL
```

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Firestore | Content + player data | 50K reads/day, 20K writes/day |
| Cloud Storage | Audio + figures | 5GB storage, 1GB/day egress |
| Cloud TTS | Audio gen (one-time) | ~$56 total |
| Cloud Run | Web hosting | 2M requests/month |
| Firebase Auth | Authentication | Free for all providers |

---

## 12. Game Mechanics Deep Dive

**Resonance**: 6 elements (Thermal🔥, Tidal🌊, Cryo❄️, Lithic🪨, Ferric⚙️, Lumen✨). Strike on correct, Surge on 6+ streak, Aura passive glow. 5 upgrade tiers each.

**Energy (Neural Charge)**: 6 max (upgradable to 8). Guided Learning = 1 charge. Reviews/Mem-Games = FREE. Regenerates 1/2hrs. Prevents cramming.

**Fog (Disguised Spaced Rep)**: Accuracy determines fog return timer (100%→5-7 days, <60%→same day). Modified SM-2 algorithm. Players see mastery visually.

**Creatures**: 7 types (one per planet). Corrupted by Grimble, freed (not killed) on correct answers. Scout/Warden/Captain variants.

**Economy**: Energy Crystals✨ earned through gameplay. Spent on upgrades, cosmetics, streak freezes.

**Streaks**: In-mission (3/6/10) + daily. Milestone rewards at 3/7/14/30/60/100 days.

---

## 13. Lore, Characters & World

**LYRA** (narrator): Calm, warm AI companion. Holographic appearance. Never shames.

**Grimble** (villain): Theatrical, pompous, funny. "Duolingo owl as dark overlord." Plushie-worthy.

**7 Specialists**: Dr. Calder (gen chem, goofy), Dr. Kade (bio, grounded), Dr. Vale (biochem, smooth), Dr. Finch (org chem, detective), Cmdr. Voss (physics, dry humor), Dr. Solomon (psych/soc, empathetic), Prof. Rhee (CARS, elegant).

**4 Commanders**: Kai, Zara, Ryn, Lira — diverse, Clash Royale cartoon-bold, purely cosmetic choice.

**7 Planets**: Verdania🟢, Glycera🩷, Luminara🟡, Synthara🟣, Aethon🔵, Miravel🟠, Lexara🩵.

---

## 14. Audio System

**TTS**: Google Cloud TTS with 9 unique voices. SSML with `[PAUSE]` → `<break>`. ~$56 total. Browser TTS fallback.

**Music**: Per-planet ambient styles (defined in `lore/audio/music_and_sfx.json`).

**SFX**: Element-specific strike sounds, creature appear/freed, streak fanfares, correct/wrong chimes.

---

## 15. Future Roadmap

### Phase 1: Pipeline & Web MVP
- [ ] Run Phases 9-11 for all books
- [ ] Build Next.js front-end (all screens)
- [ ] Implement mission player + 4 Mem-Game engines
- [ ] Connect Firestore + browser TTS
- [ ] Deploy to Cloud Run

### Phase 2: Game Systems
- [ ] Fog (SM-2), Energy, Streaks, Creatures, Economy, Resonance VFX
- [ ] Bridge Mission player, Notebook, Shop

### Phase 3: Art & Production Audio
- [ ] Character art, planet maps, creature sprites
- [ ] Run Phase 10 for Cloud TTS audio
- [ ] Grimble cutscenes

### Phase 4: iOS App
- [ ] React Native (Expo) with shared logic
- [ ] Firebase cross-platform sync
- [ ] Push notifications, haptics, Apple Sign-In
- [ ] App Store submission

### Phase 5: Endgame & Social
- [ ] Dark Crystal Core final mission  
- [ ] Cosmetic unlocks, leaderboards, study groups

### Phase 6: Advanced
- [ ] Adaptive difficulty, weak-topic detection
- [ ] MCAT score predictor, analytics dashboard
- [ ] Teacher/tutor dashboard

---

## 16. Folder Organization

```
cursormcat/
├── README.md                   # This file
├── MCAT_Game_Design_v2.md      # Original game design document
├── env.example                 # Environment variable template
├── pipeline_checkpoint.json    # Pipeline resume state
├── pdfs/                       # Source Kaplan PDFs (git-ignored)
├── phases/                     # Pipeline: phase0/ through phase11/
│   └── each contains: script.py, README.md, output/
├── scripts/                    # Orchestration, verification, demos
│   ├── run_pipeline.py         # Master pipeline runner
│   ├── config.py               # Central configuration
│   ├── verify_content.py       # 3-layer audit
│   ├── demo_pipeline_output.py # Interactive console demo
│   └── utils/                  # Gemini client, checkpoint manager, mode compiler
├── lore/                       # Game world data → Firestore
│   ├── world.json, creatures.json
│   ├── characters/             # LYRA, commanders, specialists
│   ├── planets/                # 7 planet configs + index
│   ├── systems/                # resonance, economy, energy, streaks, fog, progression
│   └── audio/                  # TTS voices, music/SFX specs
├── frontend/                   # Web prototype
│   ├── index.html              # Full SPA scaffold
│   ├── css/                    # main.css, planets.css, animations.css
│   └── js/                     # app.js, screens/, engines/, systems/, data/
├── tests/                      # Golden chapter regression tests
└── logs/                       # Pipeline interrupt logs
```

---

## 17. Key Scripts

```bash
python scripts/run_pipeline.py "MCAT Biology Review.pdf"       # Full pipeline
python scripts/run_pipeline.py --resume                         # Resume last
python scripts/run_pipeline.py --report                         # Status report
python scripts/run_pipeline.py --phase 9                        # Single phase
python scripts/verify_content.py biology 1.1                    # Verify section
python scripts/demo_pipeline_output.py gen_chem 1.1             # Interactive demo
python scripts/check_phase_outputs.py                           # Check outputs
python phases/phase11/phase11_upload_firestore.py --dry-run     # Preview upload
```

---

## 18. AI Agent Startup Protocol
If you are an AI assistant starting a new session:

1. **Check Status**: `python scripts/run_pipeline.py --report`
2. **Review progress**: Which subjects/chapters completed which phases
3. **Continue**: `python scripts/run_pipeline.py --resume` or `--from [NEXT_PHASE]`
4. **Read this README** for full architecture context
5. **Check `lore/`** for game world data

---

## 19. Contributing & Best Practices

- **Checkpointing**: Always use `run_pipeline.py`. `pipeline_checkpoint.json` prevents wasted API credits.
- **Deterministic First**: If Python logic can do it (Phase 7), don't use an LLM.
- **Models**: `gemini-3-flash-preview` first, `gemini-2.5-flash` auto-fallback.
- **Rate Limits**: 14 RPM free tier. Pipeline auto-throttles.
- **Cost**: Phase 10 TTS ~$56 total. Skip during dev — browser TTS fallback works.
- **ADHD test**: Every decision must pass: "Would this keep a distracted student engaged for 15 more seconds?"

---

*Built with obsessive attention to detail, because MCAT students deserve better than flashcards.*
