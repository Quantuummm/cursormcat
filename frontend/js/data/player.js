/**
 * MCAT Mastery — Player State Manager
 * 
 * Manages all player-specific state: energy, crystals, streaks,
 * progress, resonance elements, and commander profile.
 * 
 * Syncs to Firebase for persistence, with localStorage as fallback.
 */

// ─── Player State ───────────────────────────────────────────
const Player = {
    // Identity
    commanderId: null,          // Selected commander (kai, zara, ryn, lira)
    commanderName: '',          // Custom name
    
    // Currency
    crystals: 0,               // Energy Crystals (single currency)
    
    // Energy System
    neuralCharge: {
        current: 6,            // Current charges
        max: 6,                // Max charges (upgradeable to 8)
        lastRegenAt: null,     // Timestamp of last regen
        regenRateMs: 7200000,  // 2 hours per charge
    },
    
    // Streaks
    streak: {
        currentDaily: 0,       // Current daily streak count
        lastPlayDate: null,    // YYYY-MM-DD of last play
        longestStreak: 0,      // All-time longest
        milestones: [],        // Claimed milestone IDs
    },
    
    // Resonance (6 elements, each 0-15 tier)
    resonance: {
        thermal: 0, tidal: 0, cryo: 0,
        lithic: 0, ferric: 0, lumen: 0,
    },
    
    // Cosmetics
    cosmetics: {
        shipSkin: 'default',
        trailEffect: 'default',
        badges: [],
    },
    
    // Progress per planet
    planetProgress: {
        // "verdania": { sectionsCompleted: 5, totalSections: 12, fogCleared: 0.4, ... }
    },
    
    // Field Notes (auto-generated, keyed by concept_id)
    fieldNotes: {},
    
    // Personal Notebook (player-created)
    notebook: [],
    
    // Bridge missions completed
    bridgesCompleted: [],
    
    // Creatures freed (array of creature encounter IDs)
    creaturesFreed: [],
    
    // Settings
    settings: {
        ttsEnabled: true,
        musicEnabled: true,
        sfxEnabled: true,
        ttsSpeed: 1.0,
    },
};

// ─── Energy Management ──────────────────────────────────────

/**
 * Check if player has enough Neural Charge for an activity.
 * @param {number} cost - Charge cost (1 for missions, 0 for review)
 */
function hasEnergy(cost = 1) {
    _regenCharges();
    return Player.neuralCharge.current >= cost;
}

/**
 * Spend Neural Charge.
 * @returns {boolean} true if spent successfully
 */
function spendEnergy(cost = 1) {
    _regenCharges();
    if (Player.neuralCharge.current < cost) return false;
    Player.neuralCharge.current -= cost;
    _saveLocal();
    return true;
}

function _regenCharges() {
    const nc = Player.neuralCharge;
    if (nc.current >= nc.max || !nc.lastRegenAt) return;
    
    const now = Date.now();
    const elapsed = now - nc.lastRegenAt;
    const regenCount = Math.floor(elapsed / nc.regenRateMs);
    
    if (regenCount > 0) {
        nc.current = Math.min(nc.max, nc.current + regenCount);
        nc.lastRegenAt = now;
    }
}

// ─── Crystal Management ─────────────────────────────────────

function addCrystals(amount, source) {
    Player.crystals += amount;
    console.log(`💎 +${amount} crystals (${source}). Total: ${Player.crystals}`);
    _saveLocal();
}

function spendCrystals(amount) {
    if (Player.crystals < amount) return false;
    Player.crystals -= amount;
    _saveLocal();
    return true;
}

// ─── Streak Management ──────────────────────────────────────

function updateDailyStreak() {
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
    
    if (Player.streak.lastPlayDate === today) return; // Already logged today
    
    if (Player.streak.lastPlayDate === yesterday) {
        Player.streak.currentDaily++;
    } else {
        Player.streak.currentDaily = 1; // Reset
    }
    
    Player.streak.lastPlayDate = today;
    Player.streak.longestStreak = Math.max(Player.streak.longestStreak, Player.streak.currentDaily);
    
    _saveLocal();
    return Player.streak.currentDaily;
}

// ─── Resonance Management ───────────────────────────────────

function upgradeResonance(element, cost) {
    if (!Player.resonance.hasOwnProperty(element)) return false;
    if (Player.resonance[element] >= 15) return false; // Max tier
    if (!spendCrystals(cost)) return false;
    
    Player.resonance[element]++;
    _saveLocal();
    return true;
}

// ─── Progress Tracking ──────────────────────────────────────

function updatePlanetProgress(planetId, sectionId, completed) {
    if (!Player.planetProgress[planetId]) {
        Player.planetProgress[planetId] = {
            sectionsCompleted: new Set(),
            fogCleared: 0,
        };
    }
    
    if (completed) {
        const progress = Player.planetProgress[planetId];
        if (typeof progress.sectionsCompleted === 'object' && !(progress.sectionsCompleted instanceof Set)) {
            progress.sectionsCompleted = new Set(progress.sectionsCompleted);
        }
        progress.sectionsCompleted.add(sectionId);
    }
    
    _saveLocal();
}

function addFieldNote(conceptId, note) {
    Player.fieldNotes[conceptId] = {
        ...note,
        addedAt: Date.now(),
    };
    _saveLocal();
}

function addNotebookEntry(entry) {
    Player.notebook.push({
        ...entry,
        id: `note_${Date.now()}`,
        createdAt: Date.now(),
    });
    _saveLocal();
}

// ─── Persistence ────────────────────────────────────────────

function _saveLocal() {
    try {
        // Convert Sets to arrays for JSON serialization
        const serializable = JSON.parse(JSON.stringify(Player, (key, val) => {
            if (val instanceof Set) return [...val];
            return val;
        }));
        localStorage.setItem('mcat_player', JSON.stringify(serializable));
    } catch (e) {
        console.warn('Player save failed:', e);
    }
}

function loadPlayerFromLocal() {
    try {
        const saved = localStorage.getItem('mcat_player');
        if (saved) {
            Object.assign(Player, JSON.parse(saved));
            return true;
        }
    } catch (e) {
        console.warn('Player load failed:', e);
    }
    return false;
}

/**
 * Sync player state to Firebase (call periodically or on major events).
 */
async function syncToFirebase(db, userId) {
    if (!db || !userId) return;
    try {
        const serializable = JSON.parse(JSON.stringify(Player, (key, val) => {
            if (val instanceof Set) return [...val];
            return val;
        }));
        await db.collection('players').doc(userId).set(serializable, { merge: true });
    } catch (e) {
        console.warn('Firebase sync failed:', e);
    }
}

/**
 * Load player state from Firebase.
 */
async function loadFromFirebase(db, userId) {
    if (!db || !userId) return false;
    try {
        const doc = await db.collection('players').doc(userId).get();
        if (doc.exists) {
            Object.assign(Player, doc.data());
            _saveLocal(); // Cache locally
            return true;
        }
    } catch (e) {
        console.warn('Firebase load failed:', e);
    }
    return false;
}

// ─── Exports ────────────────────────────────────────────────
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Player, hasEnergy, spendEnergy, addCrystals, spendCrystals,
        updateDailyStreak, upgradeResonance, updatePlanetProgress,
        addFieldNote, addNotebookEntry,
        loadPlayerFromLocal, syncToFirebase, loadFromFirebase,
    };
}
