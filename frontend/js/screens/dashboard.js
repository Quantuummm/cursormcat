/**
 * MCAT Mastery — Ship Dashboard Screen
 * 
 * Hub screen: shows 7 planet buttons, LYRA greeting,
 * and quick-access to notebook/shop/bridges.
 */

const PLANET_EMOJIS = {
    verdania: '🌿',
    glycera:  '🧬',
    luminara: '⚗️',
    synthara: '🔬',
    aethon:   '⚡',
    miravel:  '🧠',
    lexara:   '📖',
};

const PLANET_LABELS = {
    verdania: 'Verdania',
    glycera:  'Glycera',
    luminara: 'Luminara',
    synthara: 'Synthara',
    aethon:   'Aethon',
    miravel:  'Miravel',
    lexara:   'Lexara',
};

const LYRA_GREETINGS = [
    "Welcome back, Commander. Where shall we deploy today?",
    "Grimble's fog is retreating. Keep pushing!",
    "Your neural pathways are getting stronger. I can feel it.",
    "Multiple sectors are signaling for help. Which planet needs us?",
    "The creatures are counting on us, Commander. Let's move.",
    "I've analyzed the fog patterns. Fresh review targets detected.",
    "Commander, your streak is looking strong. Let's not break it!",
];

function initDashboard() {
    _renderPlanetOrbit();
    _setLyraGreeting();
    updateHUD();
}

// ─── Planet Grid ────────────────────────────────────────

function _renderPlanetOrbit() {
    const container = document.getElementById('planet-orbit');
    if (!container) return;
    container.innerHTML = '';
    
    const subjectMap = getSubjectMapping();
    const playerState = getPlayerState();
    
    // Use planet order from game data, or fallback
    const planetOrder = ['verdania', 'glycera', 'luminara', 'synthara', 'aethon', 'miravel', 'lexara'];
    
    planetOrder.forEach(planetId => {
        const btn = document.createElement('button');
        btn.className = 'planet-btn';
        btn.setAttribute('data-planet', planetId);
        
        // Calculate progress
        const progress = playerState.planetProgress?.[planetId] || {};
        const pct = progress.percentCleared || 0;
        
        btn.innerHTML = `
            <div class="planet-icon">${PLANET_EMOJIS[planetId] || '🌍'}</div>
            <span class="planet-label">${PLANET_LABELS[planetId] || planetId}</span>
            <span class="planet-pct">${pct}%</span>
        `;
        
        btn.addEventListener('click', () => {
            openPlanetMap(planetId);
        });
        
        container.appendChild(btn);
    });
}

function openPlanetMap(planetId) {
    // Set planet context for the map screen
    const planetData = getPlanetForSubject(_subjectForPlanet(planetId));
    
    const nameEl = document.getElementById('planet-name');
    const subjEl = document.getElementById('planet-subject');
    const mapScreen = document.getElementById('planet-map-screen');
    
    if (nameEl) nameEl.textContent = PLANET_LABELS[planetId] || planetId;
    if (subjEl) subjEl.textContent = _subjectDisplayName(_subjectForPlanet(planetId));
    if (mapScreen) mapScreen.setAttribute('data-planet', planetId);
    
    initPlanetMap(planetId, planetData);
    showScreen('planet-map-screen');
}

function _subjectForPlanet(planetId) {
    const map = {
        verdania: 'biology', glycera: 'biochemistry', luminara: 'gen_chem',
        synthara: 'org_chem', aethon: 'physics', miravel: 'psych_soc', lexara: 'cars',
    };
    return map[planetId] || 'biology';
}

function _subjectDisplayName(subject) {
    const names = {
        biology: 'Biology', biochemistry: 'Biochemistry', gen_chem: 'General Chemistry',
        org_chem: 'Organic Chemistry', physics: 'Physics', psych_soc: 'Psychology & Sociology',
        cars: 'Critical Analysis & Reasoning',
    };
    return names[subject] || subject;
}

// ─── LYRA Greeting ──────────────────────────────────────

function _setLyraGreeting() {
    const msgEl = document.getElementById('lyra-message');
    if (!msgEl) return;
    
    const state = getPlayerState();
    
    // Context-aware greeting
    if (state.streak.current >= 7) {
        msgEl.textContent = `${state.streak.current}-day streak! You're unstoppable, Commander!`;
    } else if (getCurrentEnergy() <= 1) {
        msgEl.textContent = "Neural Charge is low. Rest up — or recharge at the Crystal Exchange.";
    } else {
        const idx = Math.floor(Math.random() * LYRA_GREETINGS.length);
        msgEl.textContent = LYRA_GREETINGS[idx];
    }
}
