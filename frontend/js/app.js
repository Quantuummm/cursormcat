/**
 * MCAT Mastery — App Entry Point
 * 
 * Boots the game: auth → load data → restore player → show correct screen.
 */

const App = {
    currentScreen: null,
    db: null,
    user: null,
};

// ─── Screen Management ──────────────────────────────────────

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) {
        target.classList.add('active');
        App.currentScreen = screenId;
    }
}

function showToast(message, duration = 2500) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    
    requestAnimationFrame(() => toast.classList.add('visible'));
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function showRewardPopup(title, rewards) {
    const popup = document.getElementById('reward-popup');
    document.getElementById('reward-title').textContent = title;
    
    const itemsEl = document.getElementById('reward-items');
    itemsEl.innerHTML = '';
    
    if (rewards.xp) {
        itemsEl.innerHTML += `<div class="reward-row">⭐ ${rewards.xp} XP</div>`;
    }
    if (rewards.crystals) {
        itemsEl.innerHTML += `<div class="reward-row">✨ ${rewards.crystals} Crystals</div>`;
    }
    if (rewards.resonance_bonus) {
        itemsEl.innerHTML += `<div class="reward-row">🔮 Resonance Bonus</div>`;
    }
    
    popup.classList.remove('hidden');
    
    document.getElementById('btn-collect-rewards').onclick = () => {
        popup.classList.add('hidden');
        if (rewards.crystals) addCrystals(rewards.crystals);
    };
}

// ─── Navigation Wiring ──────────────────────────────────────

function wireNavigation() {
    // Dashboard buttons
    const btnProfile  = document.getElementById('btn-profile');
    const btnNotebook = document.getElementById('btn-notebook');
    const btnShop     = document.getElementById('btn-shop');
    const btnBridges  = document.getElementById('btn-bridges');
    
    if (btnProfile)  btnProfile.onclick  = () => showScreen('profile-screen');
    if (btnNotebook) btnNotebook.onclick = () => showScreen('notebook-screen');
    if (btnShop)     btnShop.onclick     = () => showScreen('shop-screen');
    if (btnBridges)  btnBridges.onclick  = () => showScreen('bridge-screen');
    
    // Back buttons
    document.getElementById('btn-back-dashboard')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-planet')?.addEventListener('click', () => showScreen('planet-map-screen'));
    document.getElementById('btn-back-from-game')?.addEventListener('click', () => showScreen('planet-map-screen'));
    document.getElementById('btn-back-from-bridge')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-notebook')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-shop')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-profile')?.addEventListener('click', () => showScreen('dashboard-screen'));
    
    // Notebook tabs
    document.querySelectorAll('.notebook-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.notebook-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // TODO: load tab content
        });
    });
    
    // Shop tabs
    document.querySelectorAll('.shop-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.shop-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // TODO: load shop content
        });
    });
}

// ─── HUD Updates ────────────────────────────────────────────

function updateHUD() {
    const state = getPlayerState();
    
    document.getElementById('hud-player-name').textContent = state.name || 'Commander';
    document.getElementById('hud-level').textContent = `Lv ${state.level || 1}`;
    document.getElementById('hud-crystal-count').textContent = state.crystals;
    
    // Energy with regen
    const current = getCurrentEnergy();
    document.getElementById('hud-energy-count').textContent = `${current}/${state.energyMax || 6}`;
    
    document.getElementById('hud-streak-count').textContent = state.streak.current;
    
    // Shop balance
    const shopCount = document.getElementById('shop-crystal-count');
    if (shopCount) shopCount.textContent = state.crystals;
}

// ─── Loading Flow ───────────────────────────────────────────

function setLoadingStatus(msg, pct) {
    const status = document.getElementById('loading-status');
    const bar    = document.getElementById('loading-bar');
    if (status) status.textContent = msg;
    if (bar) bar.style.width = `${pct}%`;
}

async function boot() {
    try {
        // 1. Authenticate
        setLoadingStatus('Establishing neural link...', 10);
        App.user = await ensureAuth();
        App.db = db;
        
        // 2. Load game data from Firestore (with cache fallback)
        setLoadingStatus('Downloading star charts...', 30);
        try {
            await loadGameData(db);
        } catch (e) {
            console.warn('Firestore load failed, trying cache:', e);
            loadGameDataFromCache();
        }
        
        // 3. Initialize systems
        setLoadingStatus('Calibrating Resonance...', 50);
        const voiceConfig = getVoiceConfig();
        if (voiceConfig) initTTS(voiceConfig, 'browser');
        
        // 4. Load or create player
        setLoadingStatus('Waking Commander from cryo-sleep...', 70);
        let hasPlayer = false;
        if (App.user) {
            hasPlayer = await loadFromFirebase(db, App.user.uid);
        }
        if (!hasPlayer) {
            hasPlayer = loadPlayerFromLocal();
        }
        
        // 5. Wire navigation
        setLoadingStatus('Systems online.', 90);
        wireNavigation();
        
        // 6. Determine start screen
        setLoadingStatus('LYRA online. Ready.', 100);
        
        await new Promise(r => setTimeout(r, 500)); // Brief pause for effect
        
        if (hasPlayer && getPlayerState().commanderId) {
            // Returning player → dashboard
            updateHUD();
            initDashboard();
            showScreen('dashboard-screen');
        } else {
            // New player → character select
            initCharacterSelect();
            showScreen('character-select-screen');
        }
        
    } catch (e) {
        console.error('Boot failed:', e);
        setLoadingStatus('Connection lost. Retrying...', 0);
        setTimeout(boot, 3000);
    }
}

// ─── Start ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', boot);
