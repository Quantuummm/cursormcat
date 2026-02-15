/**
 * MCAT Mastery — Character Select Screen
 * 
 * New player flow: pick Commander → name → Resonance element → start.
 * Reads commander data from game-data.js, resonance elements from resonance.json.
 */

const RESONANCE_ELEMENTS = [
    { id: 'thermal', name: 'Thermal', emoji: '🔥', element: 'Fire' },
    { id: 'tidal',   name: 'Tidal',   emoji: '🌊', element: 'Water' },
    { id: 'cryo',    name: 'Cryo',    emoji: '❄️',  element: 'Ice' },
    { id: 'lithic',  name: 'Lithic',  emoji: '🪨', element: 'Earth' },
    { id: 'ferric',  name: 'Ferric',  emoji: '⚙️', element: 'Metal' },
    { id: 'lumen',   name: 'Lumen',   emoji: '✨', element: 'Light' },
];

let _selectedCommander = null;
let _selectedResonance = null;

function initCharacterSelect() {
    _renderCommanders();
    _renderResonancePicker();
    _wireStartButton();
}

// ─── Commanders ─────────────────────────────────────────

function _renderCommanders() {
    const grid = document.getElementById('commander-grid');
    if (!grid) return;
    grid.innerHTML = '';
    
    // Try to load from game data, fallback to defaults
    let commanders;
    const raw = getCommanders();
    
    if (Array.isArray(raw)) {
        commanders = raw;
    } else if (raw && Array.isArray(raw.commanders)) {
        // Firestore doc shape: { commanders: [ { id, display_name, ... } ] }
        commanders = raw.commanders.map(c => ({
            id: (c.id || '').replace('commander_', ''),
            name: (c.display_name || c.id || '').replace('Commander ', ''),
            emoji: c.emoji || _commanderEmoji(c.id),
            tagline: c.tagline || _commanderTagline((c.id || '').replace('commander_', '')),
        }));
    } else {
        commanders = _defaultCommanders();
    }
    
    commanders.forEach(cmd => {
        const card = document.createElement('div');
        card.className = 'commander-card';
        card.setAttribute('data-id', cmd.id);
        
        card.innerHTML = `
            <div class="commander-avatar">${cmd.emoji || '🧑‍🚀'}</div>
            <strong>${cmd.name}</strong>
            <small style="color: var(--text-muted)">${cmd.tagline || ''}</small>
        `;
        
        card.addEventListener('click', () => {
            grid.querySelectorAll('.commander-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            _selectedCommander = cmd.id;
            
            // Auto-fill name suggestion
            const nameInput = document.getElementById('player-name');
            if (nameInput && !nameInput.value) {
                nameInput.placeholder = cmd.name;
            }
            
            _checkReady();
        });
        
        grid.appendChild(card);
    });
}

function _defaultCommanders() {
    return [
        { id: 'kai',  name: 'Kai',  emoji: '🔥', tagline: 'Bold & driven' },
        { id: 'zara', name: 'Zara', emoji: '⚡', tagline: 'Calm & precise' },
        { id: 'ryn',  name: 'Ryn',  emoji: '🌿', tagline: 'Curious & kind' },
        { id: 'lira', name: 'Lira', emoji: '✨', tagline: 'Fierce & fast' },
    ];
}

function _commanderEmoji(id) {
    const map = { commander_kai: '🔥', kai: '🔥', commander_zara: '⚡', zara: '⚡', 
                  commander_ryn: '🌿', ryn: '🌿', commander_lira: '✨', lira: '✨' };
    return map[id] || '🧑‍🚀';
}

function _commanderTagline(id) {
    const map = { kai: 'Bold & driven', zara: 'Calm & precise', ryn: 'Curious & kind', lira: 'Fierce & fast' };
    return map[id] || '';
}

// ─── Resonance Picker ───────────────────────────────────

function _renderResonancePicker() {
    const grid = document.querySelector('.resonance-grid');
    if (!grid) return;
    grid.innerHTML = '';
    
    RESONANCE_ELEMENTS.forEach(el => {
        const option = document.createElement('div');
        option.className = 'resonance-option';
        option.setAttribute('data-element', el.id);
        
        option.innerHTML = `
            <span class="resonance-emoji">${el.emoji}</span>
            <span>${el.name}</span>
        `;
        
        option.addEventListener('click', () => {
            grid.querySelectorAll('.resonance-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            _selectedResonance = el.id;
            _checkReady();
        });
        
        grid.appendChild(option);
    });
}

// ─── Start Adventure ────────────────────────────────────

function _wireStartButton() {
    const btn = document.getElementById('btn-start-adventure');
    const nameInput = document.getElementById('player-name');
    
    if (nameInput) {
        nameInput.addEventListener('input', _checkReady);
    }
    
    if (btn) {
        btn.addEventListener('click', () => {
            const playerName = nameInput?.value.trim() || 'Commander';
            
            // Initialize player state
            createNewPlayer({
                name: playerName,
                commanderId: _selectedCommander,
                resonance: _selectedResonance,
            });
            
            // Save immediately
            _saveLocal();
            if (App.user) syncToFirebase(db, App.user.uid);
            
            // Transition to dashboard
            updateHUD();
            initDashboard();
            showScreen('dashboard-screen');
            
            showToast(`Welcome, Commander ${playerName}. The planets await.`);
        });
    }
}

function _checkReady() {
    const btn = document.getElementById('btn-start-adventure');
    if (btn) {
        btn.disabled = !(_selectedCommander && _selectedResonance);
    }
}

/**
 * Initialize a brand new player state.
 * Writes directly to the Player global (not the adapter) so saves work correctly.
 */
function createNewPlayer({ name, commanderId, resonance }) {
    // Write directly to Player global, not through getPlayerState() adapter
    Player.commanderId = commanderId;
    Player.commanderName = name;
    Player.crystals = 50; // Starter crystals
    Player.neuralCharge.current = 6;
    Player.neuralCharge.max = 6;
    Player.neuralCharge.lastRegenAt = Date.now();
    Player.streak.currentDaily = 0;
    Player.streak.lastPlayDate = null;
    Player.streak.longestStreak = 0;
    Player.streak.milestones = [];
    // Set primary resonance element
    for (const key of Object.keys(Player.resonance)) {
        Player.resonance[key] = key === resonance ? 1 : 0;
    }
    Player.planetProgress = {};
    Player.creaturesFreed = [];
    Player.bridgesCompleted = [];
    Player.fieldNotes = {};
    Player.notebook = [];
    Player.cosmetics = { shipSkin: 'default', trailEffect: 'default', badges: [] };
    Player.settings = { ttsEnabled: true, sfxEnabled: true, musicEnabled: true, ttsSpeed: 1.0 };
    _saveLocal();
}
