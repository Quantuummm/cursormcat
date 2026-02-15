/**
 * MCAT Mastery — Leaderboard System
 * 
 * Duolingo-style per-planet leaderboard that resets monthly.
 * Uses Firestore for real-time rankings.
 * 
 * Structure in Firestore:
 *   leaderboards/{planetId}/months/{YYYY-MM}/entries/{userId}
 *   - score: number (sections * 100 + streak_bonus + speed_bonus)
 *   - name: string
 *   - commanderId: string
 *   - level: number
 *   - updatedAt: timestamp
 */

const Leaderboard = {
    currentPlanet: 'all',
    currentMonth: _getCurrentMonth(),
    entries: [],
    playerRank: null,
};

function _getCurrentMonth() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Initialize the leaderboard screen.
 */
function initLeaderboard(planetFilter = 'all') {
    Leaderboard.currentPlanet = planetFilter;
    Leaderboard.currentMonth = _getCurrentMonth();
    
    const body = document.getElementById('leaderboard-body');
    if (!body) return;
    
    body.innerHTML = `
        <div class="lb-filter-bar">
            <select id="lb-planet-filter" class="lb-select">
                <option value="all" ${planetFilter === 'all' ? 'selected' : ''}>🌌 All Planets</option>
                <option value="verdania">🌿 Verdania (Biology)</option>
                <option value="glycera">🧬 Glycera (Biochemistry)</option>
                <option value="luminara">⚗️ Luminara (Gen Chem)</option>
                <option value="synthara">🔬 Synthara (Org Chem)</option>
                <option value="aethon">⚡ Aethon (Physics)</option>
                <option value="miravel">🧠 Miravel (Psych/Soc)</option>
                <option value="lexara">📖 Lexara (CARS)</option>
            </select>
            <span class="lb-month">${_formatMonth(Leaderboard.currentMonth)}</span>
        </div>
        
        <div class="lb-podium" id="lb-podium">
            <!-- Top 3 -->
        </div>
        
        <div class="lb-list" id="lb-list">
            <div class="lb-loading">Loading rankings...</div>
        </div>
        
        <div class="lb-player-rank" id="lb-player-rank">
            <!-- Current player's rank -->
        </div>
    `;
    
    // Wire filter
    document.getElementById('lb-planet-filter')?.addEventListener('change', (e) => {
        initLeaderboard(e.target.value);
    });
    
    // Load data
    _loadLeaderboardData(planetFilter);
}

function _formatMonth(ym) {
    const [y, m] = ym.split('-');
    const months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];
    return `${months[parseInt(m)]} ${y}`;
}

/**
 * Load leaderboard data from Firestore.
 */
async function _loadLeaderboardData(planetId) {
    const entries = [];
    
    try {
        if (typeof db !== 'undefined' && db) {
            const collPath = planetId === 'all' 
                ? `leaderboards/global/months/${Leaderboard.currentMonth}/entries`
                : `leaderboards/${planetId}/months/${Leaderboard.currentMonth}/entries`;
            
            const snapshot = await db.collection(collPath)
                .orderBy('score', 'desc')
                .limit(50)
                .get();
            
            snapshot.forEach(doc => {
                entries.push({ id: doc.id, ...doc.data() });
            });
        }
    } catch (e) {
        console.warn('Leaderboard fetch failed, using demo data:', e);
    }
    
    // If no Firestore data, show demo entries
    if (entries.length === 0) {
        entries.push(..._generateDemoLeaderboard());
    }
    
    Leaderboard.entries = entries;
    
    // Find player rank
    const state = getPlayerState();
    const playerScore = _computePlayerScore(state, planetId);
    let playerInList = false;
    
    entries.forEach((e, i) => {
        e._rank = i + 1;
        if (e.name === state.name) {
            Leaderboard.playerRank = i + 1;
            playerInList = true;
        }
    });
    
    if (!playerInList) {
        // Insert player into the right position
        const rank = entries.filter(e => e.score > playerScore).length + 1;
        Leaderboard.playerRank = rank;
    }
    
    _renderLeaderboard(entries, playerScore);
}

function _computePlayerScore(state, planetId) {
    let score = 0;
    
    if (planetId === 'all') {
        for (const prog of Object.values(state.planetProgress || {})) {
            const sc = prog.sectionsCompleted;
            score += (sc instanceof Set ? sc.size : Array.isArray(sc) ? sc.length : 0) * 100;
        }
    } else {
        const prog = state.planetProgress?.[planetId] || {};
        const sc = prog.sectionsCompleted;
        score += (sc instanceof Set ? sc.size : Array.isArray(sc) ? sc.length : 0) * 100;
    }
    
    // Streak bonus
    score += (state.streak.currentDaily || state.streak.current || 0) * 25;
    // Level bonus
    score += (state.level || 1) * 50;
    
    return score;
}

function _renderLeaderboard(entries, playerScore) {
    const podium = document.getElementById('lb-podium');
    const list = document.getElementById('lb-list');
    const rankEl = document.getElementById('lb-player-rank');
    
    if (!podium || !list) return;
    
    // Podium (top 3)
    const top3 = entries.slice(0, 3);
    const medals = ['🥇', '🥈', '🥉'];
    
    podium.innerHTML = top3.map((e, i) => `
        <div class="podium-entry podium-${i + 1}">
            <span class="podium-medal">${medals[i]}</span>
            <div class="podium-avatar ${e.commanderId || 'kai'}"></div>
            <span class="podium-name">${e.name}</span>
            <span class="podium-score">${e.score.toLocaleString()} pts</span>
        </div>
    `).join('');
    
    // Rest of list (4-50)
    const rest = entries.slice(3);
    list.innerHTML = rest.map(e => `
        <div class="lb-row ${e.name === getPlayerState().name ? 'lb-row-self' : ''}">
            <span class="lb-rank">#${e._rank}</span>
            <div class="lb-avatar-sm ${e.commanderId || 'kai'}"></div>
            <span class="lb-name">${e.name}</span>
            <span class="lb-lvl">Lv${e.level || 1}</span>
            <span class="lb-score">${e.score.toLocaleString()}</span>
        </div>
    `).join('');
    
    // Player rank footer
    const state = getPlayerState();
    if (rankEl) {
        rankEl.innerHTML = `
            <div class="lb-row lb-row-self">
                <span class="lb-rank">#${Leaderboard.playerRank}</span>
                <div class="lb-avatar-sm ${state.commanderId || 'kai'}"></div>
                <span class="lb-name">${state.name} (You)</span>
                <span class="lb-lvl">Lv${state.level}</span>
                <span class="lb-score">${playerScore.toLocaleString()}</span>
            </div>
        `;
    }
}

/**
 * Submit player score to leaderboard (call after completing missions).
 */
async function submitLeaderboardScore(planetId) {
    const state = getPlayerState();
    const score = _computePlayerScore(state, planetId);
    const month = _getCurrentMonth();
    
    const entry = {
        name: state.name,
        commanderId: state.commanderId,
        level: state.level,
        score: score,
        updatedAt: new Date().toISOString(),
    };
    
    try {
        if (typeof db !== 'undefined' && db && typeof App !== 'undefined' && App.user) {
            // Per-planet leaderboard
            if (planetId && planetId !== 'all') {
                await db.collection(`leaderboards/${planetId}/months/${month}/entries`)
                    .doc(App.user.uid).set(entry, { merge: true });
            }
            // Also update global
            await db.collection(`leaderboards/global/months/${month}/entries`)
                .doc(App.user.uid).set(entry, { merge: true });
        }
    } catch (e) {
        console.warn('Leaderboard submission failed:', e);
    }
}

function _generateDemoLeaderboard() {
    const names = [
        'AstroMedic', 'NeuroNinja', 'ChemQueen', 'BioBlaster', 'PhysicsPro',
        'MCATCrusher', 'StudyStar', 'DrDream', 'ScienceSlayer', 'BrainStorm',
        'MoleculeMax', 'CellSurgeon', 'AtomAce', 'ReactionKing', 'GeneMachine',
        'OrganOracle', 'WaveRider', 'SynapseSniper', 'CatalystCat', 'HelixHero',
    ];
    const commanders = ['kai', 'zara', 'ryn', 'lira'];
    
    return names.map((name, i) => ({
        name,
        commanderId: commanders[i % 4],
        level: Math.max(1, 15 - Math.floor(i * 0.7)),
        score: Math.max(100, 5000 - i * 230 + Math.floor(Math.random() * 200)),
        _rank: i + 1,
    }));
}
