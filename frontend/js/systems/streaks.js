/**
 * MCAT Mastery — Streak System
 * 
 * Daily streak tracking with crystal bonuses.
 * In-mission question streak for combo rewards.
 */

const STREAK_MILESTONES = {
    7:   { crystals: 100, message: '7-day streak! 🔥 100 crystals!' },
    30:  { crystals: 300, message: '30-day streak! 🔥🔥 300 crystals!' },
    100: { crystals: 1000, message: '100-day streak! 🔥🔥🔥 1000 crystals!' },
};

const QUESTION_STREAK_BONUSES = {
    3:  { crystals: 5,  message: '3-streak! +5 ✨' },
    6:  { crystals: 15, message: '6-streak! +15 ✨' },
    10: { crystals: 30, message: '10-streak! +30 ✨' },
};

/**
 * Check and update daily streak on mission complete.
 * Returns any milestone reward earned.
 */
function checkDailyStreak() {
    const state = getPlayerState();
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    
    if (state.streak.lastPlayDate === today) {
        // Already counted today
        return null;
    }
    
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    
    if (state.streak.lastPlayDate === yesterday) {
        // Consecutive day
        state.streak.currentDaily++;
    } else if (!state.streak.lastPlayDate) {
        // First day
        state.streak.currentDaily = 1;
    } else {
        // Streak broken
        state.streak.currentDaily = 1;
    }
    
    state.streak.lastPlayDate = today;
    state.streak.longestStreak = Math.max(state.streak.longestStreak || 0, state.streak.currentDaily);
    _saveLocal();
    
    // Check milestones
    const milestone = STREAK_MILESTONES[state.streak.currentDaily];
    if (milestone) {
        addCrystals(milestone.crystals, 'streak_milestone');
        return milestone;
    }
    
    return null;
}

/**
 * Check if a question streak earns bonus crystals.
 * @param {number} streak Current in-mission question streak
 * @returns {object|null} Bonus info if earned
 */
function checkQuestionStreakBonus(streak) {
    const bonus = QUESTION_STREAK_BONUSES[streak];
    if (bonus) {
        addCrystals(bonus.crystals);
        return bonus;
    }
    return null;
}

/**
 * Get current daily streak info for display.
 */
function getStreakInfo() {
    const state = getPlayerState();
    const today = new Date().toISOString().slice(0, 10);
    const isActive = state.streak.lastPlayDate === today;
    
    // Next milestone
    let nextMilestone = null;
    for (const day of Object.keys(STREAK_MILESTONES).map(Number).sort((a, b) => a - b)) {
        if (state.streak.currentDaily < day) {
            nextMilestone = { day, daysAway: day - state.streak.currentDaily };
            break;
        }
    }
    
    return {
        current: state.streak.currentDaily,
        isActiveToday: isActive,
        nextMilestone,
    };
}
