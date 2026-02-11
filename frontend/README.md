# MCAT Mastery Frontend

Web app frontend for the MCAT Mastery gamified learning platform.

## Architecture

```
frontend/
├── index.html              # Entry point
├── css/
│   ├── main.css           # Core styles + CSS variables
│   ├── planets.css        # Planet-specific themes
│   └── animations.css     # Creature, fog, streak animations
├── js/
│   ├── app.js             # App initialization + routing
│   ├── firebase.js        # Firebase connection + auth
│   ├── data/
│   │   ├── game-data.js   # Load world, characters, planets from Firestore
│   │   ├── player.js      # Player state, energy, crystals, streaks
│   │   └── progress.js    # Mission progress, fog timers, field notes
│   ├── screens/
│   │   ├── dashboard.js   # Ship Dashboard (hub screen)
│   │   ├── planet-map.js  # Tile-based planet map with fog
│   │   ├── mission.js     # Guided learning mission player
│   │   ├── game-mode.js   # Game mode engines (7 types)
│   │   ├── bridge.js      # Bridge mission screen
│   │   ├── shop.js        # Powers shop (resonance upgrades)
│   │   ├── notebook.js    # Field Notes + Personal Notebook
│   │   └── profile.js     # Commander profile + stats
│   ├── engines/
│   │   ├── sequence-builder.js
│   │   ├── sort-buckets.js
│   │   ├── equation-forge.js
│   │   ├── rapid-recall.js
│   │   ├── label-text.js
│   │   ├── concept-clash.js
│   │   └── table-challenge.js
│   ├── systems/
│   │   ├── tts.js         # TTS playback (Cloud audio + browser fallback)
│   │   ├── fog.js         # Fog/spaced repetition timer system
│   │   ├── streak.js      # Streak tracking + milestone rewards
│   │   ├── energy.js      # Neural Charge management
│   │   ├── resonance.js   # Resonance element powers
│   │   └── creatures.js   # Creature encounter UI + animations
│   └── utils/
│       ├── audio.js       # Audio playback manager
│       ├── animations.js  # Animation helpers
│       └── storage.js     # Local storage utilities
└── assets/
    ├── sprites/           # Character + creature sprites
    ├── backgrounds/       # Planet backgrounds
    ├── icons/             # UI icons
    └── audio/             # Local audio fallbacks
```

## Design Language

- **Aesthetic**: "Stardew Valley coziness × Duolingo addiction × Clash Royale cartoon boldness"
- **Resolution**: 375×812 (iPhone) primary, responsive up
- **Typography**: Rounded sans-serif headers, clean body text
- **Colors**: Each planet has its own palette (defined in planets.css)
- **Animations**: Bouncy, satisfying. Creature-freeing animations, streak celebrations.

## Data Flow

```
Backend Pipeline (Python) → Firebase Firestore → Frontend (JS)
                                                    ↓
                                              Local Storage (offline cache)
```

## Getting Started

1. Set up Firebase project with Firestore
2. Run `python phases/phase11/phase11_upload_firestore.py --dry-run` to preview
3. Run `python phases/phase11/phase11_upload_firestore.py` to upload
4. Open `frontend/index.html` in browser (or serve with any HTTP server)
