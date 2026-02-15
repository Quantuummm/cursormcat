# Master Build Prompt: MCAT Mastery Web Game

## Project Overview

Build a **cozy, addictive web-based learning game** that disguises MCAT exam preparation as an engaging tile-clearing progression game. The game uses **spaced repetition learning** hidden behind the metaphor of reclaiming corrupted territories. Target: Web app (HTML/CSS/JS/WebGL) deployable to any hosting platform, optimized for desktop and mobile browsers.

**Core Fantasy:** Player is a powerful agent clearing "corrupted" territories across 7 distinct worlds by correctly answering MCAT questions. Each correct answer = environmental transformation from dark → vibrant. Wrong answers = content queued for review. The entire experience feels like an RPG progression system but is actually an optimized study tool with built-in spaced repetition.

**Design Pillars:**
1. **ADHD-First:** 15-30 second micro-lessons, questions every 2-3 minutes, instant feedback, multi-sensory (TTS audio + visual + animation)
2. **Cozy & Addictive:** Warm visuals, satisfying feedback loops, visible progress, never punishing
3. **Autonomy:** Recommended path suggested, never forced - player chooses what to study
4. **Disguised Spaced Repetition:** "Fog returns" = review trigger. Players defend territory, not "drill flashcards"

---

## Technical Stack Requirements

### Core Engine
- **WebGL** for 3D rendering (use Three.js or Babylon.js)
- **React** or **Vue.js** for UI framework
- **Web Audio API** for sound effects
- **Web Speech API** OR **ElevenLabs API** for text-to-speech narration
- **IndexedDB** for client-side progress persistence
- **Firebase** (Firestore + Auth) for cloud sync and analytics

### Performance Targets
- Load time: <3 seconds on 4G
- Frame rate: 60fps on mid-range devices
- Mobile-first responsive design
- Progressive Web App (PWA) with offline capability for review missions

### Asset Requirements
- Low-poly 3D models (8k-40k tris per model)
- PBR materials with emissive properties for "glow" effects
- Particle systems for spell/attack effects
- 2D UI elements (SVG preferred for scalability)
- Sound effects library (chimes, whooshes, ambient loops)

---

## Data Architecture

### Content Structure
```javascript
{
  worlds: [
    {
      id: "world_01",
      subjectId: "biology",
      colorPalette: {primary: "#10B981", secondary: "#34D399", accent: "#059669"},
      sectors: [
        {
          id: "sector_01",
          name: "The Cell",
          tiles: [
            {
              id: "tile_001",
              contentType: "guided_lesson",
              microconcepts: [
                {
                  text: "Cell membrane is selectively permeable...",
                  ttsEnabled: true,
                  duration: 15,
                  diagrams: ["cell_membrane.svg"]
                }
              ],
              questions: [
                {
                  type: "multiple_choice",
                  stem: "What structure...",
                  choices: [
                    {id: "a", text: "...", correct: true},
                    {id: "b", text: "...", correct: false}
                  ],
                  explanation: "The correct answer is A because...",
                  difficulty: 2
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Player State Schema
```javascript
{
  playerId: "uuid",
  selectedCommander: {id: "commander_01", resonanceType: "thermal"},
  
  progress: {
    world_01: {
      sector_01: {
        tile_001: {
          completed: true,
          accuracy: 0.85,
          lastAttempt: timestamp,
          nextReviewDue: timestamp,
          attempts: 3
        }
      },
      overallCompletion: 0.45  // 45% of tiles cleared
    }
  },
  
  mastery: {
    // Spaced repetition tracking
    tile_001: {
      easeFactor: 2.5,
      interval: 7,  // days until next review
      repetitions: 4,
      lastReview: timestamp
    }
  },
  
  economy: {
    energyCharges: 4,
    maxCharges: 6,
    lastChargeTime: timestamp,
    crystals: 2450
  },
  
  upgrades: {
    strike: {level: 3, purchased: true},
    surge: {level: 2, purchased: true},
    aura: {level: 1, purchased: false},
    energyCapacity: 6
  },
  
  streaks: {
    currentDaily: 12,
    longestDaily: 45,
    currentInMission: 0,
    longestInMission: 18
  }
}
```

---

## Core Game Loop (Step-by-Step)

### 1. App Launch Flow
```
1. Loading screen (check auth state, load player data)
2. IF first time:
   → Character selection screen (4 commanders, visual only - no gameplay difference)
   → Resonance selection (6 elements, determines visual effects only)
   → Brief tutorial mission (forcedTutorial: true)
3. ELSE:
   → Direct to Ship Dashboard
```

### 2. Ship Dashboard (Home Screen)
**Visual:** Clean UI showing 7 world icons in hexagonal grid or orbital pattern

**UI Elements:**
- Top bar: Energy indicator (4/6), Daily streak counter (🔥 12), Crystals (💎 2,450)
- Large "Continue" button (highlights next recommended tile based on algorithm)
- World grid - each world shows:
  - Completion % ring
  - Fog status indicator (clear / stirring / critical)
  - Tap to open World Map
- Bottom nav: 📓 Notes | ✨ Powers | 👤 Profile | 🔄 Review

**Logic:**
- Display notification badges if fog is returning (red dot on world icon)
- "Continue" button algorithm:
  1. Check for critical fog reclamation (priority)
  2. Else: next incomplete tile in player's last active world
  3. Else: recommend world with lowest completion %

### 3. World Map View
**Visual:** Large, beautiful illustrated/3D tile-based map filling viewport

**Implementation:**
- Grid or hex-based tile layout
- Each tile = 1 lesson/concept
- Tiles grouped into visible sectors (bordered/labeled)
- Camera: pan/zoom controls OR auto-fit all tiles in view
- Fog overlay on uncompleted tiles (dark shader + blur + desaturation)
- Completed tiles: full color, slight glow effect

**Tile States:**
```javascript
{
  locked: {visual: "dark + padlock icon", clickable: false},
  available: {visual: "dark fog overlay", clickable: true, glowPulse: true},
  completed: {visual: "full color + checkmark", clickable: true, glow: "subtle"},
  reviewing: {visual: "slight fog creeping back", clickable: true, badge: "⚠️"}
}
```

**Interactions:**
- Tap tile → Check energy → Launch mission OR show "out of energy" modal
- Long press tile → Preview modal (tile name, question count, energy cost, last accuracy)

### 4. Mission Structure (Guided Clearing)

**Screen Layout:**
```
┌─────────────────────────────────────┐
│ [Back] Title        Energy: 3/6     │  ← Header
├─────────────────────────────────────┤
│                                     │
│     LESSON CONTENT AREA             │  ← 60% of screen
│   (text + diagrams + TTS player)    │     Teaching phase
│                                     │
│   OR: Question card (when active)   │     Question phase
│                                     │
├─────────────────────────────────────┤
│                                     │
│   LIVE TILE MAP (mini version)      │  ← 40% of screen
│   Shows fog clearing in real-time   │     Visual feedback
│   as player answers correctly       │
│                                     │
└─────────────────────────────────────┘
```

**Mission Flow Loop:**
```
1. MISSION START
   → Play intro audio (AI narrator voice)
   → Display mission brief (which tile, how many questions)
   → Deduct 1 energy charge
   
2. TEACHING PHASE (repeats 3-5 times per mission)
   → Display microconcept text (animated in)
   → Auto-play TTS narration (with play/pause/skip controls)
   → Show accompanying diagram/visual if available
   → Duration: 15-30 seconds per segment
   → [Next] button appears after audio finishes
   
3. QUESTION PHASE (every 2-3 teaching segments)
   → Fade to question card
   → Display question stem + answer choices
   → Start invisible timer (track time-to-answer for analytics, but don't pressure player)
   → Player selects answer
   
   IF CORRECT:
     → Green flash animation
     → Play satisfying chime sound
     → Trigger Resonance Strike animation:
       - Commander character appears briefly with hand raised
       - Elemental attack shoots toward tile map
       - Fog on one mini-tile clears with particle burst
       - +XP popup (+25)
       - +Crystal popup (+5)
     → Update streak counter (+1)
     → Display brief explanation (optional read)
     → Continue to next teaching segment
     
   IF WRONG:
     → Gentle red pulse (not punishing)
     → Play soft "miss" sound
     → Strike "fizzles" animation (small spark, no tile clear)
     → Narrator voice reframe: "Partial recall - let's reinforce this pathway"
     → Display full explanation (required read)
     → Mark tile for review (fog will return faster)
     → Streak resets to 0
     → Continue to next teaching segment
     
4. CREATURE ENCOUNTER (random 20% chance during mission)
   → Dark particles swirl on one mini-tile
   → 3D creature model appears with "corrupted" shader (dark aura)
   → Battle music intensifies slightly
   → Display bonus question (slightly harder than normal)
   → Same correct/wrong flow as above
   
   IF DEFEATED:
     → Creature's dark aura shatters (particle effect)
     → Creature transforms to "cute" version (shader swap)
     → Cute animation (hop, spin, wave)
     → Bonus rewards: +10 crystals, +50 XP
     
   IF MISSED:
     → Creature absorbs hit but stays on tile
     → Mission continues (can encounter again later)
     
5. STREAK BONUSES (checked after each correct answer)
   3 correct in a row:
     → "+5 Crystals!" popup
     → Three-note ascending chime
     → "NICE!" text animation
     → Tile glow pulses
     
   6 correct in a row:
     → "+15 Crystals!" popup
     → Six-note fanfare
     → "ON FIRE!" text animation
     → Screen edge warm glow effect
     → Surge meter fills faster
     
   10 correct in a row:
     → "+30 Crystals!" popup
     → Epic orchestral hit
     → "UNSTOPPABLE!" text animation
     → Full-screen Resonance burst
     → Surge ability instantly ready
     
6. MISSION COMPLETE
   → Final tile clears
   → Completion summary screen:
     - Accuracy % (with progress bar animation)
     - Tiles cleared: X/Y
     - XP earned (animate counter)
     - Crystals earned (animate counter)
     - Creatures defeated: N
     - Time spent: MM:SS
     - Streak achieved: X
   → Auto-save progress
   → Generate Field Notes entry (clean summary of concepts covered)
   → Show rewards unlocked (if any)
   → Buttons: [Continue Next Tile] [Review This Tile] [Return to Map]
```

### 5. Spaced Repetition System (Fog Reclamation)

**Algorithm (SuperMemo SM-2 variant):**
```javascript
function calculateNextReview(tile, wasCorrect) {
  if (wasCorrect) {
    tile.repetitions += 1;
    if (tile.repetitions === 1) {
      tile.interval = 1;  // Review tomorrow
    } else if (tile.repetitions === 2) {
      tile.interval = 3;  // Review in 3 days
    } else {
      tile.interval = Math.round(tile.interval * tile.easeFactor);
    }
    tile.easeFactor = Math.max(1.3, tile.easeFactor + (0.1 - (5 - tile.accuracy) * (0.08 + (5 - tile.accuracy) * 0.02)));
  } else {
    tile.repetitions = 0;
    tile.interval = 1;  // Review tomorrow
    tile.easeFactor = Math.max(1.3, tile.easeFactor - 0.2);
  }
  
  tile.nextReviewDue = Date.now() + (tile.interval * 24 * 60 * 60 * 1000);
  tile.fogStatus = determineFogStatus(tile.accuracy, tile.interval);
  return tile;
}

function determineFogStatus(accuracy, interval) {
  if (accuracy >= 0.95) return {level: "clear", returnAfter: interval};
  if (accuracy >= 0.80) return {level: "stirring", returnAfter: interval * 0.75};
  if (accuracy >= 0.60) return {level: "reclaiming", returnAfter: interval * 0.5};
  return {level: "critical", returnAfter: Math.max(1, interval * 0.25)};
}
```

**Visual Representation:**
- **Clear (95%+ accuracy):** Tile fully vibrant, no fog, soft glow
- **Stirring (80-94%):** Slight dark edges creeping in, yellow ⚠️ badge
- **Reclaiming (60-79%):** Partial fog coverage, orange 🔶 badge, pulsing
- **Critical (<60%):** Heavy fog returning, red 🔴 badge, urgent pulse

**Notification System:**
- Dashboard shows count of tiles needing review per world
- Daily check: if `tile.nextReviewDue < Date.now()`, flag for review
- AI narrator message: "Commander, fog is returning to [Sector Name]. A quick memory sweep will hold it."

**Review Mission (Free, Costs 0 Energy):**
- Rapid-fire: 5-10 questions from that tile's content
- No teaching segments, just pure recall practice
- Same correct/wrong feedback + fog clearing
- Rewards: 20-30 crystals, updates mastery tracking
- Goal: Get accuracy above threshold to "stabilize" tile

---

## Energy System

**Mechanics:**
```javascript
const ENERGY_CONFIG = {
  maxCharges: 6,
  regenRateMinutes: 120,  // 1 charge every 2 hours
  costGuidedMission: 1,
  costReviewMission: 0,
  costBridgeMission: 2,
  
  crystalRefill: {
    single: {cost: 50, charges: 1},
    full: {cost: 250, charges: 6}
  }
};

function updateEnergy(player) {
  const now = Date.now();
  const minutesSinceLastCharge = (now - player.lastChargeTime) / 60000;
  const chargesToAdd = Math.floor(minutesSinceLastCharge / ENERGY_CONFIG.regenRateMinutes);
  
  if (chargesToAdd > 0) {
    player.energyCharges = Math.min(ENERGY_CONFIG.maxCharges, player.energyCharges + chargesToAdd);
    player.lastChargeTime = now;
  }
  
  return player;
}
```

**UI Display:**
- Header: `⚡ 4/6` with timer showing next charge (e.g., "⚡ 4/6 • Next in 1h 23m")
- Empty state modal when attempting mission at 0 energy:
  - "Out of energy! Your neural charge is recharging."
  - "You can still do Review missions (free) or refill using crystals."
  - Buttons: [Review Missions] [Refill: 50💎] [Refill Full: 250💎] [Wait]

**Why This Works:**
- Prevents cognitive fatigue (can't cram for 6 hours straight)
- Encourages spaced study sessions (optimal for retention)
- Creates return loop (come back when energy refills)
- Never blocks progress (review missions always available)

---

## Economy System (Single Currency: Crystals)

**Earning Crystals:**
```javascript
const CRYSTAL_REWARDS = {
  guidedMission: {
    baseReward: 30,
    accuracyBonus: (accuracy) => Math.floor(accuracy * 25),  // Max +25 for 100%
    perCorrectAnswer: 5,
    creatureDefeat: 10
  },
  
  streakBonuses: {
    daily: {3: 50, 7: 100, 14: 200, 30: 500, 60: 1000, 100: 2000},
    inMission: {3: 5, 6: 15, 10: 30}
  },
  
  reviewMission: {baseReward: 20, accuracyBonus: 10},
  bridgeMission: {baseReward: 50},
  
  dailyLogin: 15
};

function calculateMissionReward(missionData) {
  let total = CRYSTAL_REWARDS.guidedMission.baseReward;
  total += CRYSTAL_REWARDS.guidedMission.accuracyBonus(missionData.accuracy);
  total += missionData.correctAnswers * CRYSTAL_REWARDS.guidedMission.perCorrectAnswer;
  total += missionData.creaturesDefeated * CRYSTAL_REWARDS.guidedMission.creatureDefeat;
  total += missionData.streakBonuses;
  return total;
}
```

**Spending Crystals (Powers Shop):**

UI: Tabbed interface accessible from Dashboard

**Tab 1 - Upgrades (Permanent):**
```javascript
const UPGRADES = {
  strike: [
    {level: 1, cost: 100, effect: "Base strike (single tile clear)"},
    {level: 2, cost: 200, effect: "Enhanced VFX (wider visual blast)"},
    {level: 3, cost: 300, effect: "Cleared tiles get subtle glow"},
    {level: 4, cost: 400, effect: "Double-strike animation on 2+ streak"},
    {level: 5, cost: 500, effect: "Legendary Strike Skin (unique element animation)"}
  ],
  surge: [
    {level: 1, cost: 150, effect: "Base surge (clears small cluster)"},
    {level: 2, cost: 250, effect: "Larger visual burst + more tiles"},
    {level: 3, cost: 350, effect: "Narrator voiceline: 'Outstanding recall!'"},
    {level: 4, cost: 450, effect: "Surge-cleared tiles get permanent glow"},
    {level: 5, cost: 600, effect: "Legendary Surge Skin"}
  ],
  aura: [
    {level: 1, cost: 100, effect: "Faint glow around commander"},
    {level: 2, cost: 200, effect: "Particle trail (element-specific)"},
    {level: 3, cost: 300, effect: "Ambient effects around commander"},
    {level: 4, cost: 400, effect: "Full-body aura with idle animation"},
    {level: 5, cost: 400, effect: "Legendary Aura (transformation effect)"}
  ],
  energyCapacity: [
    {from: 6, to: 7, cost: 500},
    {from: 7, to: 8, cost: 750}
  ]
};
```

**Tab 2 - Cosmetics (Permanent):**
- Alternate element colors (300-600 crystals)
- Commander outfit variants (400-800 crystals)
- World decoration themes (300-500 crystals)

**Tab 3 - Consumables:**
```javascript
const CONSUMABLES = {
  quickCharge: {cost: 50, effect: "+1 energy", maxHold: 5},
  fullCharge: {cost: 250, effect: "Refill to max energy", maxHold: 2},
  streakFreeze: {cost: 200, effect: "Protect daily streak for 1 day", maxHold: 2}
};
```

**UI for Powers Shop:**
- Card-based layout
- Each upgrade shows: icon, name, description, cost, current level, "Buy" button
- Purchased items show checkmark
- Insufficient crystals: button grayed out with tooltip "Need X more crystals"
- Purchase confirmation modal with preview of effect

---

## Bridge Missions (Cross-Subject Mastery)

**Unlock Trigger:**
```javascript
function checkBridgeUnlock(player, worldA, worldB) {
  const worldAProgress = player.progress[worldA].overallCompletion;
  const worldBProgress = player.progress[worldB].overallCompletion;
  
  // Unlock when player has cleared at least 1 sector in BOTH worlds
  if (worldAProgress >= 0.15 && worldBProgress >= 0.15) {
    return {
      unlocked: true,
      bridgeId: `${worldA}_${worldB}`,
      description: "Detect signal bridge between [Concept A] and [Concept B]"
    };
  }
  return {unlocked: false};
}
```

**Bridge Visual:**
- On Ship Dashboard world map: visible glowing line connecting two worlds
- Pulses when available to play
- Shows "✓" checkmark when completed (permanent - never needs review)

**Bridge Mission Format:**
```
1. Brief intro (15 sec): Narrator explains connection between subjects
2. 3-5 hybrid questions pulling from BOTH subjects
   Example: "Given this amino acid structure [biochem], 
            which functional group [orgo chem] is responsible for polarity?"
3. 1 rapid matching game: Connect terms from Subject A to Subject B
4. Completion: Permanent unlock, cannot be reclaimed by fog
```

**Rewards:**
- 40-60 crystals
- Bridge decoration (cosmetic) appears on world map
- Achievement badge in profile
- Counts toward "mastery%" calculation

---

## Progression & Milestones

**Achievement System:**
```javascript
const ACHIEVEMENTS = {
  firstTileClear: {reward: "Welcome Badge", icon: "🎯"},
  firstWorldComplete: {reward: "100 Crystals + World Victory Skin", icon: "🌍"},
  threeWorldsComplete: {reward: "Commander Outfit Variant", icon: "👕"},
  allBridgesComplete: {reward: "'Bridge Walker' Aura Effect", icon: "🌉"},
  defeatAllCreatureTypes: {reward: "Creature Codex Unlock", icon: "📖"},
  sevenDayStreak: {reward: "100 Crystals + Streak Badge", icon: "🔥"},
  thirtyDayStreak: {reward: "500 Crystals + Legendary Aura", icon: "🔥🔥"},
  hundredDayStreak: {reward: "2000 Crystals + Prestige Title", icon: "🔥🔥🔥"}
};
```

**Mastery Milestones (Per World):**
- 25%: Unlock specialist character portrait
- 50%: Unlock world-themed cosmetic
- 75%: Unlock legendary creature defeat animation
- 100%: Unlock Resonance Victory Skin (element takes on world's visual theme)

**Global Progress Tracking:**
```javascript
function calculateGlobalProgress(player) {
  const totalTiles = getAllTiles().length;
  const completedTiles = player.completedTiles.length;
  const masteryScore = calculateWeightedMastery(player);  // Factors in accuracy + retention
  
  return {
    tilesCleared: completedTiles,
    totalTiles: totalTiles,
    percentComplete: (completedTiles / totalTiles) * 100,
    masteryScore: masteryScore,  // 0-100 scale
    worldBreakdown: getWorldBreakdown(player)
  };
}
```

---

## Field Notes & Notebook System

**Auto-Generated Field Notes:**
After each mission, generate clean summary:

```javascript
function generateFieldNotes(mission) {
  return {
    id: mission.tileId,
    title: mission.tileName,
    worldName: mission.worldName,
    sectorName: mission.sectorName,
    dateCompleted: Date.now(),
    accuracy: mission.accuracy,
    
    keyConcepts: extractKeyConcepts(mission.content),  // Bulleted list
    importantTerms: extractTerms(mission.content),      // Highlighted vocab
    equations: extractEquations(mission.content),        // Formatted formulas
    diagrams: mission.diagrams,                          // Reference to visual aids
    
    fogStatus: mission.tile.fogStatus,
    nextReview: mission.tile.nextReviewDue
  };
}
```

**UI for Field Notes:**
- Organized hierarchically: World > Sector > Tile
- Searchable (full-text search across all notes)
- Filterable (by world, by fog status, by accuracy)
- Exportable (PDF download of all notes)
- Accessible during missions (slide-out panel from right edge)

**Personal Notebook:**
- Rich text editor: bold, italic, highlight, bullet points, color coding
- Create custom folders (e.g., "Weak Areas", "Exam Day Review")
- Drag-and-drop organization
- Link notes to specific tiles (click linked tile → jump to that tile on map)
- Accessible from Dashboard and during missions

---

## Sound & Music Design

**Audio Requirements:**

**Background Music (looping, adaptive):**
- Ship Dashboard: Ambient space pad (calming, home feeling)
- World 1: Soft acoustic with nature ambience
- World 2: Lo-fi synth with organic pads
- World 3: Crystal chimes + electronic arpeggios
- World 4: Ethereal cave echoes
- World 5: Open orchestral + wind instruments
- World 6: Warm jazz-inspired + city ambient
- World 7: Gentle piano + string quartet
- Mission Active: Intensity increases slightly (add percussion layer)
- Creature Encounter: Battle music swell (temporary, returns after defeat)

**Sound Effects:**
```javascript
const SFX_LIBRARY = {
  // UI
  buttonClick: "soft_click.wav",
  panelOpen: "whoosh_in.wav",
  panelClose: "whoosh_out.wav",
  
  // Feedback
  correctAnswer: "ascending_chime.wav",
  wrongAnswer: "soft_descend.wav",
  streak3: "three_note_rise.wav",
  streak6: "fanfare_short.mp3",
  streak10: "orchestral_hit.mp3",
  
  // Combat
  thermalStrike: "fire_whoosh.wav",
  tidalStrike: "water_splash.wav",
  cryoStrike: "ice_shatter.wav",
  lithicStrike: "stone_impact.wav",
  ferricStrike: "metal_clang.wav",
  lumenStrike: "light_chime.wav",
  
  strikeFizzle: "dampened_thud.wav",
  surgeTrigger: "energy_charge.wav",
  surgeBlast: "massive_explosion.wav",
  
  // Creatures
  creatureAppear: "dark_rumble.wav",
  creatureDefeat: "crystal_shatter.wav",
  creatureReveal: "cute_chirp.wav",
  
  // Progression
  levelUp: "level_up_fanfare.mp3",
  tileClear: "satisfying_pop.wav",
  sectorComplete: "victory_jingle.mp3",
  worldComplete: "triumphant_theme.mp3",
  
  // Currency
  crystalEarn: "coin_collect.wav",
  xpGain: "xp_gain.wav",
  purchaseSuccess: "purchase_confirm.wav"
};
```

**TTS Integration:**
```javascript
// Option 1: ElevenLabs API (higher quality, costs money)
async function playNarration(text, voiceId="narrator_lyra") {
  const audioUrl = await elevenLabs.textToSpeech(text, voiceId);
  const audio = new Audio(audioUrl);
  audio.play();
}

// Option 2: Web Speech API (free, lower quality)
function playNarrationLocal(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.voice = getPreferredVoice();  // Select from available system voices
  speechSynthesis.speak(utterance);
}

// UI: Always include play/pause/skip controls + speed adjustment
```

---

## UI/UX Polish Requirements

**Animations (All should feel smooth, never janky):**
- Page transitions: 200ms fade with slight scale (0.98 → 1.0)
- Tile fog clearing: 1 second gradient fade + particle burst
- Correct answer: Green pulse (300ms) → strike animation (800ms) → tile clear (1s)
- Modal open: Backdrop fade (200ms) + modal slide up (300ms) with spring easing
- Button feedback: Scale to 0.95 on press, return with bounce
- Currency gain: Number counter animation + icon pop
- Streak milestones: Screen shake (subtle) + particle confetti

**Responsive Design:**
- Breakpoints: Mobile (<768px), Tablet (768-1024px), Desktop (>1024px)
- Mobile mission layout: Stack content area above tile map
- Touch targets: Minimum 44x44px for all buttons
- Gesture support: Swipe to go back, pinch to zoom on tile maps

**Accessibility:**
- All text meets WCAG AA contrast standards
- Keyboard navigation support (tab through all interactive elements)
- Screen reader labels on all UI elements
- Colorblind mode toggle (changes red/green to blue/orange)
- Font size adjustment (3 sizes: normal, large, extra-large)
- Reduced motion toggle (disables particle effects, reduces animations)

**Loading States:**
- Show skeleton screens while content loads
- Never block entire UI - load sections progressively
- Explicit loading indicators for API calls (TTS generation, save progress)

**Error Handling:**
- Offline detection: Show banner "You're offline. Changes will sync when reconnected."
- Save failure: Retry logic (3 attempts) → show error modal with manual retry button
- API timeout: Graceful fallback (e.g., if TTS fails, show text only)
- Missing content: Show placeholder with "Content coming soon" message

---

## Analytics & Tracking (Privacy-Respectful)

**Events to Track (Anonymized):**
```javascript
const ANALYTICS_EVENTS = {
  // Engagement
  sessionStart: {dailyActive, returningUser},
  sessionEnd: {duration, tilesCompleted},
  
  // Learning
  questionAnswered: {correct, timeToAnswer, difficulty, subject},
  tileCompleted: {accuracy, timeSpent, retryCount},
  reviewTriggered: {fogLevel, daysSinceLastAttempt},
  
  // Progression
  levelUp: {newLevel, crystalsEarned},
  achievementUnlocked: {achievementId},
  purchaseMade: {itemType, cost},
  
  // Retention
  streakBroken: {length, lastLoginDate},
  energyRefill: {method: "wait" | "crystals"},
  
  // Drop-off points
  missionAbandoned: {progressPercent, lastQuestion},
  appBackgrounded: {currentScreen}
};
```

**Use Analytics For:**
1. Identifying difficult questions (high wrong rate) → flag for content review
2. Optimal energy regeneration rate (balance engagement vs fatigue)
3. Most effective reward types (what drives return behavior)
4. Bottlenecks in progression (where players get stuck)

**Privacy:**
- No personal identifiable information collected
- Allow user to opt-out completely
- Data retained for 90 days max
- Transparent privacy policy linked in settings

---

## Deployment Requirements

**Build Output:**
- Single-page application (SPA)
- Production build: <5MB total (including assets)
- Code splitting: Lazy-load worlds (only load assets for active world)
- Image optimization: WebP with PNG fallback
- Minified JS/CSS bundles
- Service worker for offline capability

**Hosting Recommendations:**
- Vercel / Netlify (automatic CI/CD from Git)
- Cloudflare Pages (great CDN performance)
- Firebase Hosting (if using Firebase backend)

**Environment Variables:**
```
FIREBASE_API_KEY=xxx
FIREBASE_AUTH_DOMAIN=xxx
ELEVENLABS_API_KEY=xxx (if using TTS)
ANALYTICS_ID=xxx
```

**Performance Monitoring:**
- Lighthouse score: Target 90+ on all metrics
- Core Web Vitals tracking
- Error reporting (Sentry or similar)

---

## Content Integration Strategy

**How MCAT Content Gets Into the System:**

Since you have Python scripts that process MCAT content, the AI orchestrator should:

1. **Accept JSON Content Structure** matching the schema defined above
2. **Provide CLI Tool** for bulk importing:
   ```bash
   npm run import-content --world=biology --file=biology_content.json
   ```
3. **Validate Content** on import:
   - All required fields present
   - Questions have correct answers marked
   - TTS text is clean (no special characters that break narration)
   - Diagrams referenced actually exist
4. **Generate Fallbacks**:
   - If TTS text missing, use question stem as fallback
   - If diagram missing, render text-only version

**Content Management UI (optional future feature):**
- Admin panel for editing questions/answers
- Preview mode for testing before publishing
- Bulk operations (hide/show questions, adjust difficulty)

---

## Testing Checklist

Before considering the build complete, verify:

**Core Functionality:**
- [ ] Character + Resonance selection saves correctly
- [ ] Tile unlocking logic works (sequential unlock)
- [ ] Correct answer → fog clears, wrong answer → fog remains
- [ ] Energy system charges over time correctly
- [ ] Spaced repetition: fog returns at correct intervals
- [ ] Currency earning + spending works
- [ ] Streaks calculate and reward correctly
- [ ] Upgrades persist and apply effects
- [ ] Field Notes generate and save
- [ ] Progress syncs to cloud (if online)

**Edge Cases:**
- [ ] What happens if user force-closes during mission?
- [ ] What if user completes tile but network fails → does it retry?
- [ ] What if user has 100% accuracy but never reviews → does fog still return?
- [ ] What if user tries to access locked tile directly via URL?
- [ ] What if TTS fails to load → does mission continue?

**Cross-Browser Testing:**
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS + iOS)
- [ ] Mobile browsers (Chrome Android, Safari iOS)

**Performance:**
- [ ] App loads in <3 seconds on 4G
- [ ] No frame drops during animations
- [ ] WebGL rendering stable across devices
- [ ] Works on devices with 2GB RAM

---

## Success Metrics

**After launch, track these to measure effectiveness:**

1. **Engagement:** Daily Active Users (DAU), Session duration, Missions per session
2. **Retention:** Day 1, Day 7, Day 30 retention rates
3. **Learning:** Average accuracy over time, Retention rate on reviewed tiles
4. **Monetization (if applicable):** Conversion rate, Average revenue per user
5. **Quality:** Crash rate, Load time, User-reported bugs

**Target Metrics (Aspirational):**
- 70%+ Day 1 retention
- 40%+ Day 7 retention
- 20%+ Day 30 retention
- 15+ minutes average session duration
- 80%+ accuracy on reviewed tiles (showing spaced repetition works)
- <2% crash rate
- 4.5+ star rating (if listed on app stores)

---

## Final Notes for AI Orchestrator

**Philosophy:**
- Every game mechanic serves learning outcomes
- Never punish wrong answers - reframe as learning opportunities
- Make progress visible and satisfying
- Cozy > competitive (no leaderboards, no social pressure)
- Respect player's time (quick sessions, auto-save everywhere)

**Known Challenges:**
- TTS quality varies by browser/API - test extensively
- WebGL performance on older mobile devices - provide fallback mode (2D only)
- Content balance - ensure difficulty progression feels natural
- Spaced repetition tuning - may need adjustment based on real user data

**Future Expansion Ideas (Post-MVP):**
- Multiplayer "co-op study" mode (clear tiles together)
- Community-created questions (with moderation)
- Comprehensive analytics dashboard for students to track weak areas
- Study group features (shared progress, friendly competition)
- Anki/Quizlet import for supplementary content

**Build Priority Order:**
1. Core game loop (missions, fog clearing, energy system)
2. Spaced repetition algorithm
3. Progress persistence (IndexedDB + cloud sync)
4. All 7 worlds functional (even with placeholder content)
5. Polish (animations, sounds, TTS)
6. Upgrades & cosmetics
7. Bridge missions
8. Advanced features (notebook, analytics)

---

**Estimated Development Time:** 3-6 months for single full-stack developer, assuming content is provided in correct format.

**Recommended Tech Stack:**
- Frontend: React + Three.js + TypeScript
- Backend: Firebase (Firestore, Auth, Hosting, Functions)
- Build: Vite
- Styling: TailwindCSS + Framer Motion (animations)
- State: Zustand or Redux Toolkit
- Audio: Howler.js

---

This prompt should give any competent AI orchestrator or full-stack developer everything needed to build MCAT Mastery from scratch. The game mechanics are fully specified, edge cases considered, and technical stack recommended. Focus on building a polished, cozy, addictive learning experience that makes studying feel like play.
