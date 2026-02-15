/**
 * MCAT Mastery — Game Data Bridge Layer
 * 
 * Loads all game configuration from Firebase Firestore and provides
 * a clean API for frontend screens to access game data.
 * 
 * This is the bridge between the Python pipeline output (uploaded to Firestore)
 * and the frontend game screens.
 */

// ─── Data Cache ─────────────────────────────────────────────
const GameData = {
    world: null,
    characters: {},      // lyra, grimble, commanders, specialists
    planets: {},         // verdania, glycera, luminara, etc.
    creatures: null,
    systems: {},         // resonance, economy, energy, streaks, fog, progression
    audioConfig: {},     // music_and_sfx, tts_voices
    _loaded: false,
};

// ─── Core Loaders ───────────────────────────────────────────

/**
 * Initialize all game data from Firestore.
 * Call this once at app startup.
 */
async function loadGameData(db) {
    if (GameData._loaded) return GameData;

    console.log('🎮 Loading game data...');

    // Load in parallel for speed
    const [world, creatures] = await Promise.all([
        _loadDoc(db, 'game_config', 'world'),
        _loadDoc(db, 'game_config', 'creatures'),
    ]);

    GameData.world = world;
    GameData.creatures = creatures;

    // Load characters (stored as game_config/character_*)
    const charIds = ['lyra', 'commanders', 'specialists'];
    const charDocs = await Promise.all(
        charIds.map(id => _loadDoc(db, 'game_config', `character_${id}`))
    );
    charIds.forEach((id, i) => { GameData.characters[id] = charDocs[i]; });
    // Grimble is inside lyra.json
    GameData.characters.grimble = charDocs[0];

    // Load planets (stored as game_config/planet_*)
    const planetIndex = await _loadDoc(db, 'game_config', 'planet_index');
    if (planetIndex && planetIndex.planets) {
        const planetIds = planetIndex.planets.map(p => p.planet_id);
        const planetDocs = await Promise.all(
            planetIds.map(id => _loadDoc(db, 'game_config', `planet_${id}`))
        );
        planetIds.forEach((id, i) => { GameData.planets[id] = planetDocs[i]; });
        GameData.planets.index = planetIndex;
    }

    // Load game systems (stored as game_config/system_*)
    const systemIds = ['resonance', 'economy', 'energy', 'streaks', 'fog', 'progression'];
    const systemDocs = await Promise.all(
        systemIds.map(id => _loadDoc(db, 'game_config', `system_${id}`))
    );
    systemIds.forEach((id, i) => { GameData.systems[id] = systemDocs[i]; });

    // Load audio config (stored as game_config/audio_*)
    const audioIds = ['music_and_sfx', 'tts_voices'];
    const audioDocs = await Promise.all(
        audioIds.map(id => _loadDoc(db, 'game_config', `audio_${id}`))
    );
    audioIds.forEach((id, i) => { GameData.audioConfig[id] = audioDocs[i]; });

    GameData._loaded = true;
    console.log('✅ Game data loaded');

    // Cache to localStorage for offline access
    _cacheToLocal(GameData);

    return GameData;
}

/**
 * Load game data from localStorage cache (offline fallback).
 */
function loadGameDataFromCache() {
    try {
        const cached = localStorage.getItem('mcat_game_data');
        if (cached) {
            const data = JSON.parse(cached);
            Object.assign(GameData, data);
            GameData._loaded = true;
            console.log('📦 Loaded game data from cache');
            return true;
        }
    } catch (e) {
        console.warn('Cache load failed:', e);
    }
    return false;
}

/**
 * Load game data directly from lore/ JSON files (dev mode / pre-Firestore).
 * Works when serving the repo root or frontend/ with a local server.
 * Tries ../lore/ first (when serving from frontend/), then lore/ (repo root).
 */
async function loadGameDataFromLore() {
    if (GameData._loaded) return GameData;
    console.log('📂 Loading game data from local lore files...');

    // Detect base path — try ../lore/ first, fall back to lore/
    let basePath = '../lore';
    try {
        const test = await fetch(`${basePath}/world.json`);
        if (!test.ok) throw new Error('not found');
    } catch {
        basePath = 'lore';
    }

    async function _fetchJSON(path) {
        try {
            const r = await fetch(`${basePath}/${path}`);
            return r.ok ? await r.json() : null;
        } catch { return null; }
    }

    // Load in parallel
    const [world, creatures, lyra, commanders, specialists,
           planetIndex, musicSfx, ttsVoices,
           resonance, economy, energy, streaks, fog, progression] = await Promise.all([
        _fetchJSON('world.json'),
        _fetchJSON('creatures.json'),
        _fetchJSON('characters/lyra.json'),
        _fetchJSON('characters/commanders.json'),
        _fetchJSON('characters/specialists.json'),
        _fetchJSON('planets/index.json'),
        _fetchJSON('audio/music_and_sfx.json'),
        _fetchJSON('audio/tts_voices.json'),
        _fetchJSON('systems/resonance.json'),
        _fetchJSON('systems/economy.json'),
        _fetchJSON('systems/energy.json'),
        _fetchJSON('systems/streaks.json'),
        _fetchJSON('systems/fog.json'),
        _fetchJSON('systems/progression.json'),
    ]);

    GameData.world = world;
    GameData.creatures = creatures;
    GameData.characters = { lyra, grimble: lyra, commanders, specialists };

    // Load individual planet files listed in index
    if (planetIndex && planetIndex.planets) {
        const planetIds = planetIndex.planets.map(p => p.planet_id);
        const planetDocs = await Promise.all(
            planetIds.map(id => _fetchJSON(`planets/${id}.json`))
        );
        planetIds.forEach((id, i) => { GameData.planets[id] = planetDocs[i]; });
        GameData.planets.index = planetIndex;
    }

    GameData.systems = { resonance, economy, energy, streaks, fog, progression };
    GameData.audioConfig = { music_and_sfx: musicSfx, tts_voices: ttsVoices };
    GameData._loaded = true;

    console.log('✅ Game data loaded from lore files');
    _cacheToLocal(GameData);
    return GameData;
}

// ─── Data Access API ────────────────────────────────────────

/**
 * Get the specialist for a given subject.
 * Returns the full specialist object from specialists.json.
 */
function getSpecialistForSubject(subject) {
    const world = GameData.world;
    if (!world || !world.subjects || !world.subjects[subject]) return null;
    
    const specialistId = world.subjects[subject].specialist_id;
    const specialists = GameData.characters.specialists;
    if (!specialists || !specialists.specialists) return null;
    
    return specialists.specialists[specialistId] || null;
}

/**
 * Get the planet for a given subject.
 * Returns the full planet object.
 */
function getPlanetForSubject(subject) {
    const world = GameData.world;
    if (!world || !world.subjects || !world.subjects[subject]) return null;
    
    const planetId = world.subjects[subject].planet_id;
    return GameData.planets[planetId] || null;
}

/**
 * Get glossary data from pipeline output or build from game data.
 * Returns { term: definition } map.
 */
function getGlossary(subject) {
    // Try Firestore glossary collection first (Phase 4 output)
    // For now, build from world/planet descriptions as a starter glossary
    const glossary = {};
    
    // Pull terms from planet data (lore-based glossary)
    for (const [planetId, planet] of Object.entries(GameData.planets)) {
        if (planetId === 'index') continue;
        if (subject && _subjectForPlanetId(planetId) !== subject) continue;
        
        if (planet?.key_terms) {
            for (const [term, def] of Object.entries(planet.key_terms)) {
                glossary[term] = { definition: def, subject: _subjectForPlanetId(planetId) };
            }
        }
        if (planet?.glossary) {
            for (const [term, def] of Object.entries(planet.glossary)) {
                glossary[term] = typeof def === 'string' ? { definition: def } : def;
            }
        }
    }
    
    // Also pull from player's field notes (user-generated glossary)
    const state = typeof getPlayerState === 'function' ? getPlayerState() : {};
    const notes = state.fieldNotes || {};
    for (const [key, note] of Object.entries(notes)) {
        if (note.conceptName && !glossary[note.conceptName]) {
            glossary[note.conceptName] = { 
                definition: note.summary || note.text || '', 
                subject: note.subject || 'general',
            };
        }
    }
    
    return glossary;
}

function _subjectForPlanetId(planetId) {
    const map = {
        verdania: 'biology', glycera: 'biochemistry', luminara: 'gen_chem',
        synthara: 'org_chem', aethon: 'physics', miravel: 'psych_soc', lexara: 'cars',
    };
    return map[planetId] || 'general';
}

/**
 * Get LYRA's data.
 */
function getLyra() {
    const lyraData = GameData.characters.lyra;
    return lyraData ? lyraData.lyra : null;
}

/**
 * Get Grimble's data.
 */
function getGrimble() {
    const lyraData = GameData.characters.lyra;
    return lyraData ? lyraData.grimble : null;
}

/**
 * Get all available commanders for character selection.
 */
function getCommanders() {
    return GameData.characters.commanders;
}

/**
 * Get a game system config by name.
 * @param {string} systemName - resonance, economy, energy, streaks, fog, or progression
 */
function getSystem(systemName) {
    return GameData.systems[systemName] || null;
}

/**
 * Get creature data for a specific planet.
 * @param {string} planetId - e.g., "verdania"
 */
function getCreaturesForPlanet(planetId) {
    if (!GameData.creatures || !GameData.creatures.creatures) return null;
    
    return Object.values(GameData.creatures.creatures).find(
        c => c.planet === planetId
    ) || null;
}

/**
 * Get TTS voice config for a speaker.
 * @param {string} speakerId - lyra, grimble, specialist id, etc.
 */
function getVoiceConfig(speakerId) {
    const voices = GameData.audioConfig.tts_voices;
    if (!voices || !voices.voice_assignments) return null;
    return voices.voice_assignments[speakerId] || null;
}

/**
 * Get the subject-to-planet-to-specialist mapping table.
 * Useful for navigation and UI rendering.
 */
function getSubjectMapping() {
    const world = GameData.world;
    if (!world || !world.subjects) return {};
    
    const mapping = {};
    for (const [subject, config] of Object.entries(world.subjects)) {
        const specialist = getSpecialistForSubject(subject);
        const planet = GameData.planets[config.planet_id];
        
        mapping[subject] = {
            subject,
            planet_id: config.planet_id,
            planet_name: planet ? planet.planet_name : config.planet_id,
            specialist_id: config.specialist_id,
            specialist_name: specialist ? specialist.display_name : config.specialist_id,
            subject_label: config.label || subject,
        };
    }
    return mapping;
}

// ─── Helpers ────────────────────────────────────────────────

async function _loadDoc(db, collection, docId) {
    try {
        const doc = await db.collection(collection).doc(docId).get();
        return doc.exists ? doc.data() : null;
    } catch (e) {
        console.warn(`Failed to load ${collection}/${docId}:`, e);
        return null;
    }
}

function _cacheToLocal(data) {
    try {
        // Remove _loaded flag before caching
        const toCache = { ...data };
        delete toCache._loaded;
        localStorage.setItem('mcat_game_data', JSON.stringify(toCache));
    } catch (e) {
        console.warn('Cache save failed (storage full?):', e);
    }
}

// ─── Exports ────────────────────────────────────────────────
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        GameData, loadGameData, loadGameDataFromCache, loadGameDataFromLore,
        getSpecialistForSubject, getPlanetForSubject, getLyra, getGrimble,
        getCommanders, getSystem, getCreaturesForPlanet, getVoiceConfig,
        getSubjectMapping,
    };
}
