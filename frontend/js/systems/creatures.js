/**
 * MCAT Mastery — Creature System
 * 
 * Corrupted natives on fogged tiles.
 * Defeat (free) them by answering a bonus question.
 * 3 variants per type: Scout → Warden → Captain (increasing difficulty).
 */

const CREATURE_EMOJIS = {
    sproutlings: '🌱',
    glowmites:   '🪲',
    sparklings:  '⚡',
    cave_wisps:  '👻',
    windlings:   '🌪️',
    echoes:      '🔮',
    inklings:    '🖋️',
};

/**
 * Check if a tile has a creature encounter.
 * In production, this comes from Phase 8 output.
 * For now, uses probability based on planet data.
 */
function hasCreatureEncounter(tileId, planetId) {
    const state = getPlayerState();
    if (state.creaturesFreed?.includes(tileId)) return false;
    
    // Deterministic "random" based on tileId hash
    const hash = _simpleHash(tileId);
    return (hash % 5) === 0; // ~20% chance
}

/**
 * Generate a creature encounter for a tile.
 */
function getCreatureForTile(tileId, planetId) {
    const creaturesData = getCreaturesForPlanet(planetId);
    const creatureType = creaturesData?.creature_type || 'sproutlings';
    
    // Variant based on sector depth
    const parts = tileId.split('_');
    const sectorNum = parseInt(parts[1]?.replace('s', '') || '1');
    const variant = sectorNum <= 4 ? 'scout' : sectorNum <= 8 ? 'warden' : 'captain';
    
    const emoji = CREATURE_EMOJIS[creatureType] || '👾';
    
    return {
        type: creatureType,
        variant,
        emoji,
        name: `${_capitalize(variant)} ${_capitalize(creatureType.replace(/_/g, ' '))}`,
        corrupted: true,
        grimbleTaunt: _getGrimbleTaunt(variant),
        freedDialogue: _getFreedDialogue(creatureType),
    };
}

/**
 * Free a creature after defeating its bonus question.
 */
function freeCreature(tileId) {
    const state = getPlayerState();
    if (!state.creaturesFreed) state.creaturesFreed = [];
    
    if (!state.creaturesFreed.includes(tileId)) {
        state.creaturesFreed.push(tileId);
        addCrystals(10); // creature defeat reward
        _saveLocal();
    }
}

/**
 * Get total creatures freed count.
 */
function getCreaturesFreedCount() {
    const state = getPlayerState();
    return state.creaturesFreed?.length || 0;
}

// ─── Dialogue Templates ─────────────────────────────────

function _getGrimbleTaunt(variant) {
    const taunts = {
        scout: [
            "Ha! Even my weakest servants will stop you!",
            "You think you can reclaim this? Try harder!",
            "My little scout will keep this tile corrupted forever!",
        ],
        warden: [
            "My wardens are stronger than your pitiful knowledge!",
            "This one won't fall so easily, Commander...",
            "You'll need more than luck to free this one!",
        ],
        captain: [
            "Meet my captain — your neural pathways end here!",
            "AHAHA! My strongest servant guards this place!",
            "No amount of study can save you from my captain!",
        ],
    };
    
    const options = taunts[variant] || taunts.scout;
    return options[Math.floor(Math.random() * options.length)];
}

function _getFreedDialogue(creatureType) {
    const dialogues = {
        sproutlings: "Thank you! The forest breathes again... I remember now.",
        glowmites:   "You broke the spell! I can see the light once more!",
        sparklings:  "Free! The energy flows pure again!",
        cave_wisps:  "The darkness lifts... I remember who I was.",
        windlings:   "I can fly again! The wind carries truth, not lies!",
        echoes:      "My thoughts are my own again. Thank you, Commander.",
        inklings:    "The words make sense now. Grimble's static is fading!",
    };
    return dialogues[creatureType] || "Thank you for freeing me!";
}

// ─── Helpers ────────────────────────────────────────────

function _simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash);
}

function _capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
