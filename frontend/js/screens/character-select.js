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
    const commanders = getCommanders() || _defaultCommanders();
    
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
 */
function createNewPlayer({ name, commanderId, resonance }) {
    const state = getPlayerState();
    state.name = name;
    state.commanderId = commanderId;
    state.level = 1;
    state.xp = 0;
    state.crystals = 50; // Starter crystals
    state.neuralCharge = { current: 6, max: 6, lastRegenTime: Date.now() };
    state.streak = { current: 0, lastDate: null };
    state.resonance = {
        primary: resonance,
        tiers: { [resonance]: 1 },
    };
    state.planetProgress = {};
    state.creaturesFreed = [];
    state.bridgesCompleted = [];
    state.fieldNotes = [];
    state.notebook = [];
    state.cosmetics = { equipped: {} };
    state.settings = { ttsEnabled: true, sfxEnabled: true, musicEnabled: true };
    _saveLocal();
}
