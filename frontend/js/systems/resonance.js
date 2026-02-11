/**
 * MCAT Mastery — Resonance System
 * 
 * 6 elements × 15 tier upgrades.
 * Strike = auto on correct answer (fog tile clears).
 * Surge = charged by 5-question streak (clears tile cluster).
 * Aura = passive glow based on element + tier.
 */

const MAX_RESONANCE_TIER = 15;

const TIER_COSTS = [
    0, 100, 150, 200, 300, 400, 500, 650, 800, 1000,
    1200, 1500, 1800, 2200, 2500, // tiers 1-15
];

/**
 * Get current resonance state.
 */
function getResonanceState() {
    const state = getPlayerState();
    return state.resonance || { primary: 'thermal', tiers: {} };
}

/**
 * Get the tier of an element.
 */
function getElementTier(elementId) {
    const res = getResonanceState();
    return res.tiers?.[elementId] || 0;
}

/**
 * Upgrade an element's tier. Returns success boolean.
 */
function upgradeResonanceTier(elementId) {
    const state = getPlayerState();
    const res = state.resonance || { primary: 'thermal', tiers: {} };
    const currentTier = res.tiers[elementId] || 0;
    
    if (currentTier >= MAX_RESONANCE_TIER) return false;
    
    const cost = TIER_COSTS[currentTier + 1] || TIER_COSTS[TIER_COSTS.length - 1];
    if (state.crystals < cost) return false;
    
    spendCrystals(cost);
    res.tiers[elementId] = currentTier + 1;
    state.resonance = res;
    _saveLocal();
    return true;
}

/**
 * Get upgrade cost for next tier.
 */
function getUpgradeCost(elementId) {
    const currentTier = getElementTier(elementId);
    if (currentTier >= MAX_RESONANCE_TIER) return null;
    return TIER_COSTS[currentTier + 1] || TIER_COSTS[TIER_COSTS.length - 1];
}

/**
 * Calculate strike power based on element tier.
 * Higher tier = more visual intensity, small gameplay bonuses.
 */
function getStrikePower(elementId) {
    const tier = getElementTier(elementId);
    return {
        tier,
        visualScale: 1 + (tier * 0.05),       // 1.0 → 1.75 at tier 15
        xpMultiplier: 1 + (tier * 0.02),       // 1.0 → 1.30 at tier 15
        particleCount: 3 + Math.floor(tier / 2), // 3 → 10 particles
    };
}

/**
 * Check if surge is charged (5+ question streak).
 */
function isSurgeCharged(missionStreak) {
    return missionStreak >= 5;
}

/**
 * Trigger surge effect: clears a cluster of tiles.
 * Returns number of bonus tiles cleared.
 */
function triggerSurge(elementId, planetId) {
    const tier = getElementTier(elementId);
    const bonusTiles = 1 + Math.floor(tier / 5); // 1-4 bonus tiles
    
    // In production, this would clear adjacent fogged tiles
    // For now, return the count for the caller to handle
    return bonusTiles;
}

/**
 * Get the visual config for an element (colors, effects).
 * Used by the VFX system.
 */
function getElementVisuals(elementId) {
    const visuals = {
        thermal: { color: '#FF6B35', glow: '#FF4500', particle: 'ember', emoji: '🔥' },
        tidal:   { color: '#1E90FF', glow: '#4169E1', particle: 'droplet', emoji: '🌊' },
        cryo:    { color: '#E0F7FA', glow: '#B3E5FC', particle: 'frost', emoji: '❄️' },
        lithic:  { color: '#D4A574', glow: '#CD853F', particle: 'debris', emoji: '🪨' },
        ferric:  { color: '#C0C0C0', glow: '#E8E8E8', particle: 'spark', emoji: '⚙️' },
        lumen:   { color: '#FFD700', glow: '#FFF8DC', particle: 'mote', emoji: '✨' },
    };
    return visuals[elementId] || visuals.thermal;
}
