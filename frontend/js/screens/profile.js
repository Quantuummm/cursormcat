/**
 * MCAT Mastery — Profile Screen
 * 
 * Displays commander stats, resonance tree, achievements,
 * study calendar, and links to leaderboard.
 */

function initProfile() {
    const body = document.getElementById('profile-body');
    if (!body) return;
    
    const state = getPlayerState();
    
    body.innerHTML = `
        <div class="profile-card">
            <div class="profile-avatar ${state.commanderId || 'kai'}">
                <div class="avatar-level">${state.level}</div>
            </div>
            <div class="profile-identity">
                <h3 class="profile-name">${state.name}</h3>
                <div class="profile-xp">
                    <div class="xp-bar">
                        <div class="xp-fill" style="width: ${_xpProgressPct(state)}%"></div>
                    </div>
                    <span class="xp-label">${state.xp} XP — Level ${state.level}</span>
                </div>
            </div>
        </div>

        <div class="profile-stats-grid">
            <div class="stat-box">
                <span class="stat-value">${state.streak.currentDaily || 0}</span>
                <span class="stat-label">🔥 Day Streak</span>
            </div>
            <div class="stat-box">
                <span class="stat-value">${state.streak.longestStreak || 0}</span>
                <span class="stat-label">🏆 Best Streak</span>
            </div>
            <div class="stat-box">
                <span class="stat-value">${state.crystals}</span>
                <span class="stat-label">✨ Crystals</span>
            </div>
            <div class="stat-box">
                <span class="stat-value">${state.creaturesFreed?.length || 0}</span>
                <span class="stat-label">🐾 Creatures Freed</span>
            </div>
            <div class="stat-box">
                <span class="stat-value">${_totalSectionsCompleted(state)}</span>
                <span class="stat-label">📚 Sections Done</span>
            </div>
            <div class="stat-box">
                <span class="stat-value">${state.bridgesCompleted?.length || 0}</span>
                <span class="stat-label">🌉 Bridges Crossed</span>
            </div>
        </div>

        <div class="profile-section">
            <h3>⚡ Resonance Elements</h3>
            <div class="resonance-bars">
                ${_renderResonanceBars(state.resonance)}
            </div>
        </div>

        <div class="profile-section">
            <h3>🪐 Planet Progress</h3>
            <div class="planet-progress-list">
                ${_renderPlanetProgressList(state)}
            </div>
        </div>

        <div class="profile-section">
            <h3>🏆 Achievements</h3>
            <div class="achievements-grid" id="achievements-grid">
                ${_renderAchievements(state)}
            </div>
        </div>

        <div class="profile-actions">
            <button class="btn btn-secondary" id="btn-study-plan">📅 Study Plan</button>
            <button class="btn btn-secondary" id="btn-leaderboard">🏅 Leaderboard</button>
            <button class="btn btn-secondary" id="btn-settings">⚙️ Settings</button>
        </div>
    `;
    
    // Wire buttons
    document.getElementById('btn-study-plan')?.addEventListener('click', () => {
        showScreen('calendar-screen');
        initCalendar();
    });
    document.getElementById('btn-leaderboard')?.addEventListener('click', () => {
        showScreen('leaderboard-screen');
        initLeaderboard();
    });
    document.getElementById('btn-settings')?.addEventListener('click', () => {
        showScreen('settings-screen');
        initSettings();
    });
}

function _xpProgressPct(state) {
    const xp = state.xp || 0;
    const level = state.level || 1;
    const currentThreshold = level <= 1 ? 0 : Math.pow((level - 1), 2) * 250;
    const nextThreshold = Math.pow(level, 2) * 250;
    const range = nextThreshold - currentThreshold;
    return range > 0 ? Math.min(100, ((xp - currentThreshold) / range) * 100) : 0;
}

function _totalSectionsCompleted(state) {
    let total = 0;
    for (const planet of Object.values(state.planetProgress || {})) {
        const sc = planet.sectionsCompleted;
        total += sc instanceof Set ? sc.size : Array.isArray(sc) ? sc.length : 0;
    }
    return total;
}

function _renderResonanceBars(resonance) {
    const elements = [
        { id: 'thermal', name: 'Thermal', color: '#ff6b35', icon: '🔥' },
        { id: 'tidal',   name: 'Tidal',   color: '#4ecdc4', icon: '🌊' },
        { id: 'cryo',    name: 'Cryo',    color: '#a8dadc', icon: '❄️' },
        { id: 'lithic',  name: 'Lithic',  color: '#8b6914', icon: '🪨' },
        { id: 'ferric',  name: 'Ferric',  color: '#c0c0c0', icon: '⚙️' },
        { id: 'lumen',   name: 'Lumen',   color: '#ffd700', icon: '✨' },
    ];
    
    return elements.map(el => {
        const tier = resonance?.[el.id] || 0;
        const pct = (tier / 15) * 100;
        return `
            <div class="res-bar-row">
                <span class="res-icon">${el.icon}</span>
                <span class="res-name">${el.name}</span>
                <div class="res-bar">
                    <div class="res-fill" style="width: ${pct}%; background: ${el.color}"></div>
                </div>
                <span class="res-tier">${tier}/15</span>
            </div>
        `;
    }).join('');
}

function _renderPlanetProgressList(state) {
    const planets = [
        { id: 'verdania',  name: 'Verdania',  subject: 'Biology',       icon: '🌿' },
        { id: 'glycera',   name: 'Glycera',   subject: 'Biochemistry',  icon: '🧬' },
        { id: 'luminara',  name: 'Luminara',  subject: 'Gen Chem',      icon: '⚗️' },
        { id: 'synthara',  name: 'Synthara',  subject: 'Org Chem',      icon: '🔬' },
        { id: 'aethon',    name: 'Aethon',    subject: 'Physics',       icon: '⚡' },
        { id: 'miravel',   name: 'Miravel',   subject: 'Psych/Soc',     icon: '🧠' },
        { id: 'lexara',    name: 'Lexara',    subject: 'CARS',          icon: '📖' },
    ];
    
    return planets.map(p => {
        const prog = state.planetProgress?.[p.id] || {};
        const pct = prog.percentCleared || 0;
        return `
            <div class="planet-prog-row">
                <span class="planet-icon">${p.icon}</span>
                <span class="planet-prog-name">${p.name}</span>
                <div class="planet-prog-bar">
                    <div class="planet-prog-fill" style="width: ${pct}%"></div>
                </div>
                <span class="planet-prog-pct">${Math.round(pct)}%</span>
            </div>
        `;
    }).join('');
}

function _renderAchievements(state) {
    const achievements = [
        { id: 'first_mission',    icon: '🚀', name: 'First Mission',     desc: 'Complete your first mission',       check: s => _totalSectionsCompleted(s) >= 1 },
        { id: 'streak_7',         icon: '🔥', name: 'Week Warrior',      desc: '7-day streak',                      check: s => (s.streak.longestStreak || 0) >= 7 },
        { id: 'streak_30',        icon: '💫', name: 'Monthly Master',    desc: '30-day streak',                     check: s => (s.streak.longestStreak || 0) >= 30 },
        { id: 'creature_10',      icon: '🐾', name: 'Creature Whisperer',desc: 'Free 10 creatures',                 check: s => (s.creaturesFreed?.length || 0) >= 10 },
        { id: 'planet_clear',     icon: '🌍', name: 'Planet Liberator',  desc: 'Clear one planet completely',        check: s => Object.values(s.planetProgress || {}).some(p => (p.percentCleared || 0) >= 100) },
        { id: 'bridge_5',         icon: '🌉', name: 'Bridge Builder',    desc: 'Complete 5 bridge missions',         check: s => (s.bridgesCompleted?.length || 0) >= 5 },
        { id: 'crystal_1000',     icon: '💎', name: 'Crystal Hoarder',   desc: 'Accumulate 1000 crystals',           check: s => s.crystals >= 1000 },
        { id: 'sections_50',      icon: '📚', name: 'Scholar',           desc: 'Complete 50 sections',               check: s => _totalSectionsCompleted(s) >= 50 },
        { id: 'resonance_max',    icon: '🔮', name: 'Resonance Master',  desc: 'Max out any resonance element',      check: s => Object.values(s.resonance || {}).some(v => v >= 15) },
    ];
    
    return achievements.map(a => {
        const unlocked = a.check(state);
        return `
            <div class="achievement ${unlocked ? 'unlocked' : 'locked'}">
                <span class="ach-icon">${a.icon}</span>
                <div class="ach-info">
                    <span class="ach-name">${a.name}</span>
                    <span class="ach-desc">${a.desc}</span>
                </div>
            </div>
        `;
    }).join('');
}
