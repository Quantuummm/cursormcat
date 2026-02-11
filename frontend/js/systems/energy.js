/**
 * MCAT Mastery — Energy System (Neural Charge)
 * 
 * Prevents cognitive overload / cramming.
 * - 6 max (upgradeable to 8)
 * - 1 charge per Guided Learning / Bridge Mission
 * - Review missions & Mem-Games are FREE
 * - Regenerates 1 charge every 2 hours
 * - Can buy refills with crystals
 */

const ENERGY_REGEN_MS = 2 * 60 * 60 * 1000; // 2 hours

/**
 * Calculate current energy with passive regeneration.
 */
function getCurrentEnergy() {
    const state = getPlayerState();
    const nc = state.neuralCharge || { current: 6, max: 6, lastRegenTime: Date.now() };
    
    if (nc.current >= nc.max) return nc.max;
    
    const elapsed = Date.now() - nc.lastRegenTime;
    const regenCharges = Math.floor(elapsed / ENERGY_REGEN_MS);
    
    if (regenCharges > 0) {
        nc.current = Math.min(nc.max, nc.current + regenCharges);
        nc.lastRegenTime = nc.lastRegenTime + (regenCharges * ENERGY_REGEN_MS);
        state.neuralCharge = nc;
        _saveLocal();
    }
    
    return nc.current;
}

/**
 * Check if player has at least 1 charge.
 */
function hasEnergy() {
    return getCurrentEnergy() > 0;
}

/**
 * Spend energy charges.
 */
function spendEnergy(amount = 1) {
    const current = getCurrentEnergy(); // triggers regen calc
    const state = getPlayerState();
    const nc = state.neuralCharge;
    
    if (nc.current < amount) return false;
    
    nc.current -= amount;
    nc.lastRegenTime = Date.now();
    _saveLocal();
    return true;
}

/**
 * Get time until next charge regenerates.
 * Returns { minutes, seconds } or null if full.
 */
function getRegenTimer() {
    const state = getPlayerState();
    const nc = state.neuralCharge || { current: 6, max: 6, lastRegenTime: Date.now() };
    
    if (nc.current >= nc.max) return null;
    
    const elapsed = Date.now() - nc.lastRegenTime;
    const remaining = ENERGY_REGEN_MS - (elapsed % ENERGY_REGEN_MS);
    
    return {
        minutes: Math.floor(remaining / 60000),
        seconds: Math.floor((remaining % 60000) / 1000),
    };
}

/**
 * Quick charge: restore 1 charge for 50 crystals.
 */
function quickCharge() {
    const cost = 50;
    const state = getPlayerState();
    
    if (state.crystals < cost) return false;
    if (getCurrentEnergy() >= (state.neuralCharge?.max || 6)) return false;
    
    spendCrystals(cost);
    state.neuralCharge.current = Math.min(state.neuralCharge.max, state.neuralCharge.current + 1);
    _saveLocal();
    return true;
}

/**
 * Full charge: restore all charges for 250 crystals.
 */
function fullCharge() {
    const cost = 250;
    const state = getPlayerState();
    
    if (state.crystals < cost) return false;
    
    spendCrystals(cost);
    state.neuralCharge.current = state.neuralCharge.max || 6;
    state.neuralCharge.lastRegenTime = Date.now();
    _saveLocal();
    return true;
}
