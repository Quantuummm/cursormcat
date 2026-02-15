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
    _renderFogAlerts();
    updateHUD();
}

// ─── Planet Grid ────────────────────────────────────────

function _renderPlanetOrbit() {
    const container = document.getElementById('planet-orbit');
    if (!container) return;
    container.innerHTML = '';
    
    const subjectMap = getSubjectMapping();
    const playerState = getPlayerState();
    
    const planetOrder = ['verdania', 'glycera', 'luminara', 'synthara', 'aethon', 'miravel', 'lexara'];
    const totalPlanets = planetOrder.length;
    
    // Get container size for orbit radius calculation
    const containerSize = container.parentElement.offsetWidth || 460;
    const orbitRadius = (containerSize / 2) - 50; // leave room for planet size
    const centerX = containerSize / 2;
    const centerY = containerSize / 2;
    const startAngle = -90; // start from top
    
    planetOrder.forEach((planetId, index) => {
        const btn = document.createElement('button');
        btn.className = 'planet-btn';
        btn.setAttribute('data-planet', planetId);
        
        // Calculate circular position
        const angleDeg = startAngle + (index * (360 / totalPlanets));
        const angleRad = (angleDeg * Math.PI) / 180;
        const x = centerX + orbitRadius * Math.cos(angleRad) - 28; // half of orb width
        const y = centerY + orbitRadius * Math.sin(angleRad) - 28;
        
        btn.style.left = `${x}px`;
        btn.style.top = `${y}px`;
        
        // Calculate progress
        const progress = playerState.planetProgress?.[planetId] || {};
        const sc = progress.sectionsCompleted;
        const clearedCount = progress.clearedTiles?.length || (sc instanceof Set ? sc.size : Array.isArray(sc) ? sc.length : 0);
        const pct = progress.percentCleared || Math.round((clearedCount / 96) * 100);
        
        btn.innerHTML = `
            <div class="planet-orb">${PLANET_EMOJIS[planetId] || '🌍'}</div>
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

// ─── Fog Alerts ─────────────────────────────────────────

function _renderFogAlerts() {
    // Show fog reclamation warnings on dashboard
    if (typeof getTilesNeedingReview !== 'function') return;
    
    const urgent = getTilesNeedingReview();
    if (urgent.length === 0) return;
    
    const container = document.getElementById('planet-orbit');
    if (!container) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'fog-alert';
    alertDiv.innerHTML = `
        <div class="fog-alert-header">⚠️ ${urgent.length} tile${urgent.length > 1 ? 's' : ''} at risk of fog reclamation!</div>
        <div class="fog-alert-list">
            ${urgent.slice(0, 3).map(t => `
                <button class="fog-alert-item" data-planet="${t.planetId}" data-tile="${t.tileId}">
                    ${PLANET_EMOJIS[t.planetId] || '🌍'} ${t.isExpired ? '🔴 Reclaimed!' : `⏱️ ${t.hoursLeft}h left`}
                </button>
            `).join('')}
        </div>
    `;
    container.parentNode.insertBefore(alertDiv, container);
    
    alertDiv.querySelectorAll('.fog-alert-item').forEach(btn => {
        btn.addEventListener('click', () => {
            openPlanetMap(btn.dataset.planet);
        });
    });
}

function _setLyraGreeting() {
    const msgEl = document.getElementById('lyra-message');
    if (!msgEl) return;
    
    const state = getPlayerState();
    
    // Context-aware greeting
    if ((state.streak.currentDaily || state.streak.current || 0) >= 7) {
        msgEl.textContent = `${state.streak.currentDaily || state.streak.current}-day streak! You're unstoppable, Commander!`;
    } else if (getCurrentEnergy() <= 1) {
        msgEl.textContent = "Neural Charge is low. Rest up — or recharge at the Crystal Exchange.";
    } else {
        const idx = Math.floor(Math.random() * LYRA_GREETINGS.length);
        msgEl.textContent = LYRA_GREETINGS[idx];
    }
}
