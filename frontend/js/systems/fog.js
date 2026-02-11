/**
 * MCAT Mastery — Fog System (Spaced Repetition)
 * 
 * SM-2 inspired fog reclamation:
 * - Cleared tiles start a fog timer
 * - If not reviewed before timer expires, fog reclaims the tile
 * - Review missions defend against fog (free, no energy cost)
 * - "Disguised spaced repetition" — player never feels drilled
 */

const FOG_INTERVALS = [
    1  * 24 * 60 * 60 * 1000,   // Level 0 → 1 day
    3  * 24 * 60 * 60 * 1000,   // Level 1 → 3 days
    7  * 24 * 60 * 60 * 1000,   // Level 2 → 7 days
    14 * 24 * 60 * 60 * 1000,   // Level 3 → 14 days
    30 * 24 * 60 * 60 * 1000,   // Level 4 → 30 days
    60 * 24 * 60 * 60 * 1000,   // Level 5 → 60 days (mastered)
];

/**
 * Get the fog timer for a tile.
 * Returns { level, nextReview, isExpired, hoursLeft }
 */
function getFogStatus(tileId) {
    const state = getPlayerState();
    const fogData = state.fogTimers?.[tileId];
    
    if (!fogData) {
        return { level: 0, nextReview: null, isExpired: false, hoursLeft: 0 };
    }
    
    const now = Date.now();
    const isExpired = now >= fogData.nextReview;
    const hoursLeft = Math.max(0, Math.floor((fogData.nextReview - now) / (60 * 60 * 1000)));
    
    return {
        level: fogData.level,
        nextReview: fogData.nextReview,
        isExpired,
        hoursLeft,
    };
}

/**
 * Start or advance the fog timer after a tile is cleared/reviewed.
 */
function advanceFogTimer(tileId, wasCorrect = true) {
    const state = getPlayerState();
    if (!state.fogTimers) state.fogTimers = {};
    
    const current = state.fogTimers[tileId] || { level: 0 };
    
    if (wasCorrect) {
        // Advance to next interval level
        const newLevel = Math.min(current.level + 1, FOG_INTERVALS.length - 1);
        const interval = FOG_INTERVALS[newLevel];
        
        state.fogTimers[tileId] = {
            level: newLevel,
            lastReview: Date.now(),
            nextReview: Date.now() + interval,
        };
    } else {
        // Failed review: regress one level
        const newLevel = Math.max(0, current.level - 1);
        const interval = FOG_INTERVALS[newLevel];
        
        state.fogTimers[tileId] = {
            level: newLevel,
            lastReview: Date.now(),
            nextReview: Date.now() + interval,
        };
    }
    
    _saveLocal();
}

/**
 * Get all tiles that need review (fog is about to reclaim).
 * Returns array of { tileId, hoursLeft, planetId }
 */
function getTilesNeedingReview() {
    const state = getPlayerState();
    const fogTimers = state.fogTimers || {};
    const now = Date.now();
    const urgentThreshold = 6 * 60 * 60 * 1000; // 6 hours warning
    
    const urgent = [];
    
    for (const [tileId, data] of Object.entries(fogTimers)) {
        const timeLeft = data.nextReview - now;
        
        if (timeLeft <= urgentThreshold) {
            const planetId = tileId.split('_')[0];
            urgent.push({
                tileId,
                planetId,
                hoursLeft: Math.max(0, Math.floor(timeLeft / (60 * 60 * 1000))),
                isExpired: timeLeft <= 0,
            });
        }
    }
    
    // Sort by most urgent first
    urgent.sort((a, b) => a.hoursLeft - b.hoursLeft);
    return urgent;
}

/**
 * Reclaim tiles whose fog timer has expired.
 * Called periodically or on app load.
 * Returns array of reclaimed tileIds.
 */
function processExpiredFog() {
    const state = getPlayerState();
    const fogTimers = state.fogTimers || {};
    const now = Date.now();
    const reclaimed = [];
    
    for (const [tileId, data] of Object.entries(fogTimers)) {
        if (now >= data.nextReview) {
            // Reset to fogged state
            const planetId = tileId.split('_')[0];
            const progress = state.planetProgress?.[planetId];
            
            if (progress?.clearedTiles) {
                const idx = progress.clearedTiles.indexOf(tileId);
                if (idx !== -1) {
                    progress.clearedTiles.splice(idx, 1);
                    // Recalculate percent
                    progress.percentCleared = Math.max(0, (progress.percentCleared || 0) - 1);
                    reclaimed.push(tileId);
                }
            }
            
            // Reset fog timer
            delete fogTimers[tileId];
        }
    }
    
    if (reclaimed.length > 0) {
        _saveLocal();
    }
    
    return reclaimed;
}
