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
    };
}

// ─── Navigation Wiring ──────────────────────────────────────

function wireNavigation() {
    // Dashboard buttons
    const btnProfile  = document.getElementById('btn-profile');
    const btnNotebook = document.getElementById('btn-notebook');
    const btnShop     = document.getElementById('btn-shop');
    const btnBridges  = document.getElementById('btn-bridges');
    const btnMemGames = document.getElementById('btn-memgames');
    
    if (btnProfile)  btnProfile.onclick  = () => { showScreen('profile-screen'); initProfile(); };
    if (btnNotebook) btnNotebook.onclick = () => { showScreen('notebook-screen'); initNotebook(); };
    if (btnShop)     btnShop.onclick     = () => { showScreen('shop-screen'); initShop(); };
    if (btnBridges)  btnBridges.onclick  = () => { showScreen('bridge-screen'); initBridge(); };
    if (btnMemGames) btnMemGames.onclick = () => { _showMemGamePicker(); };
    
    // Back buttons
    document.getElementById('btn-back-dashboard')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-planet')?.addEventListener('click', () => showScreen('planet-map-screen'));
    document.getElementById('btn-back-from-game')?.addEventListener('click', () => {
        const dest = (typeof _gameReturnScreen !== 'undefined') ? _gameReturnScreen : 'planet-map-screen';
        showScreen(dest);
        if (dest === 'dashboard-screen') initDashboard();
    });
    document.getElementById('btn-back-from-bridge')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-notebook')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-shop')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-profile')?.addEventListener('click', () => showScreen('dashboard-screen'));
    document.getElementById('btn-back-from-leaderboard')?.addEventListener('click', () => showScreen('profile-screen'));
    document.getElementById('btn-back-from-calendar')?.addEventListener('click', () => showScreen('profile-screen'));
    document.getElementById('btn-back-from-settings')?.addEventListener('click', () => showScreen('profile-screen'));
    
    // Notebook tabs — handled by notebook.js initNotebook()
    // Shop tabs — handled by shop.js initShop()
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
    
    document.getElementById('hud-streak-count').textContent = state.streak.currentDaily || 0;
    
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
        // 0. Initialize theme & galaxy shimmer (always, even before auth)
        ThemeSystem.init();
        GalaxyShimmer.init();
        LandingScreen.init();

        // 0b. Native mobile setup
        if (typeof Mobile !== 'undefined') await Mobile.init();
        
        // 1. Check for existing auth session (don't auto-create anonymous user)
        setLoadingStatus('Establishing neural link...', 10);
        const existingUser = await new Promise(resolve => {
            const unsubscribe = auth.onAuthStateChanged(user => {
                unsubscribe();
                resolve(user);
            });
        });

        if (!existingUser) {
            // No existing session — show landing page, wait for user action
            console.log('No auth session, showing landing page');
            showScreen('landing-screen');
            return;
        }

        App.user = existingUser;
        App.db = db;

        // User is authenticated — show loading and continue boot
        showScreen('loading-screen');
        
        // 2. Load game data from Firestore (with cache fallback, then lore files)
        setLoadingStatus('Downloading star charts...', 30);
        try {
            await loadGameData(db);
        } catch (e) {
            console.warn('Firestore load failed, trying cache:', e);
            if (!loadGameDataFromCache()) {
                console.warn('Cache miss, loading from lore files...');
                await loadGameDataFromLore();
            }
        }
        
        // 3. Initialize systems
        setLoadingStatus('Calibrating Resonance...', 50);
        const voiceConfig = getVoiceConfig('lyra');
        if (voiceConfig) initTTS(voiceConfig, 'browser');
        
        // Process expired fog timers (spaced repetition)
        if (typeof processExpiredFog === 'function') {
            const reclaimed = processExpiredFog();
            if (reclaimed.length > 0) {
                setTimeout(() => showToast(`⚠️ ${reclaimed.length} tile(s) reclaimed by fog! Review to reclaim.`), 2000);
            }
        }
        
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
        // Only retry on network-type errors, not code bugs
        const isNetworkError = e.message && (
            e.message.includes('network') || e.message.includes('fetch') ||
            e.message.includes('Failed to get document') || e.message.includes('unavailable') ||
            e.name === 'FirebaseError'
        );
        if (isNetworkError) {
            setLoadingStatus('Connection lost. Retrying...', 0);
            setTimeout(boot, 3000);
        } else {
            setLoadingStatus(`Error: ${e.message || 'Unknown error'}. Check console.`, 0);
        }
    }
}

// ─── Mem-Game Picker ────────────────────────────────────

function _showMemGamePicker() {
    const arena = document.getElementById('game-arena');
    document.getElementById('game-mode-title').textContent = '🎮 Mem-Games';
    showScreen('game-mode-screen');
    
    const modes = [
        { engine: 'rapid_recall',     icon: '⚡', name: 'Rapid Recall',     desc: 'Term → definition flashcards' },
        { engine: 'sort_buckets',     icon: '🪣', name: 'Sort & Classify',  desc: 'Categorize items into groups' },
        { engine: 'equation_forge',   icon: '⚗️', name: 'Equation Forge',   desc: 'Build equations from parts' },
        { engine: 'concept_clash',    icon: '⚔️', name: 'Concept Clash',    desc: 'True/false rapid-fire' },
        { engine: 'sequence_builder', icon: '📋', name: 'Sequence Builder', desc: 'Order steps correctly' },
        { engine: 'label_text',       icon: '🏷️', name: 'Label Master',     desc: 'Fill in the blanks' },
        { engine: 'table_challenge',  icon: '📊', name: 'Table Challenge',  desc: 'Complete comparison tables' },
    ];
    
    arena.innerHTML = `
        <div style="width:100%;max-width:560px;">
            <p style="color: var(--text-secondary); text-align: center; margin-bottom: var(--gap-md);">
                Free practice games — no Neural Charge needed!
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:var(--gap-md,12px);">
                ${modes.map(m => `
                    <button class="game-pick-card" data-engine="${m.engine}"
                        style="display:flex;flex-direction:column;align-items:center;gap:6px;padding:16px;
                               background:var(--bg-card,#1e293b);border:1px solid var(--border,#334155);
                               border-radius:12px;cursor:pointer;color:var(--text-primary,#e2e8f0);
                               font-family:inherit;transition:transform .15s,border-color .2s;">
                        <span style="font-size:2rem;">${m.icon}</span>
                        <strong>${m.name}</strong>
                        <small style="color:var(--text-muted,#94a3b8);font-size:0.75rem;">${m.desc}</small>
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    arena.querySelectorAll('.game-pick-card').forEach(card => {
        card.addEventListener('click', () => {
            const engine = card.dataset.engine;
            launchGameMode(_buildDemoModeData(engine), 'dashboard-screen');
        });
    });
}

function _buildDemoModeData(engine) {
    const demos = {
        rapid_recall: {
            engine: 'rapid_recall',
            items: [
                { term: 'Mitochondria', definition: 'Powerhouse of the cell — produces ATP via oxidative phosphorylation' },
                { term: 'Ribosome', definition: 'Reads mRNA and assembles amino acids into proteins' },
                { term: 'Golgi apparatus', definition: 'Modifies, sorts, and packages proteins for secretion or delivery' },
                { term: 'Endoplasmic reticulum', definition: 'Network of membranes for protein folding (rough) and lipid synthesis (smooth)' },
                { term: 'Lysosome', definition: 'Contains digestive enzymes to break down waste and cellular debris' },
                { term: 'Nucleus', definition: 'Houses DNA and controls gene expression' },
            ],
        },
        sort_buckets: {
            engine: 'sort_buckets',
            categories: [
                { name: 'Prokaryotic', items: ['No nucleus', 'Circular DNA', 'Binary fission', '70S ribosomes'] },
                { name: 'Eukaryotic', items: ['Membrane-bound organelles', 'Linear chromosomes', 'Mitotic division', '80S ribosomes'] },
            ],
        },
        concept_clash: {
            engine: 'concept_clash',
            items: [
                { statement: 'DNA replication is semi-conservative', correct_answer: true },
                { statement: 'RNA polymerase requires a primer to begin transcription', correct_answer: false },
                { statement: 'Enzymes lower the activation energy of a reaction', correct_answer: true },
                { statement: 'Competitive inhibitors change Vmax', correct_answer: false },
                { statement: 'ATP is produced by chemiosmosis in the mitochondria', correct_answer: true },
                { statement: 'Glycolysis occurs in the mitochondrial matrix', correct_answer: false },
            ],
        },
        sequence_builder: {
            engine: 'sequence_builder',
            title: 'Order the stages of mitosis',
            steps: ['Prophase', 'Prometaphase', 'Metaphase', 'Anaphase', 'Telophase'],
        },
        equation_forge: {
            engine: 'equation_forge',
            equations: [{
                name: 'Cellular Respiration',
                components: ['C₆H₁₂O₆', '+', '6O₂', '→', '6CO₂', '+', '6H₂O', '+', 'ATP'],
            }],
        },
        label_text: {
            engine: 'label_text',
            title: 'Fill in the amino acid properties',
            text: 'Amino acids have an amine group, a carboxyl group, and a unique R-group. At physiological pH, the amine group is protonated and the carboxyl group is deprotonated.',
            blanks: [
                { answer: 'amine' },
                { answer: 'carboxyl' },
                { answer: 'R-group' },
            ],
        },
        table_challenge: {
            engine: 'table_challenge',
            title: 'Compare DNA vs RNA',
            columns: ['Feature', 'DNA', 'RNA'],
            rows: [
                { cells: ['Sugar', 'Deoxyribose', 'Ribose'] },
                { cells: ['Bases', 'A, T, G, C', 'A, U, G, C'] },
                { cells: ['Strands', 'Double', 'Single'] },
                { cells: ['Location', 'Nucleus', 'Nucleus & Cytoplasm'] },
            ],
            hidden_cells: [
                { row: 0, col: 2 },
                { row: 1, col: 1 },
                { row: 2, col: 2 },
                { row: 3, col: 1 },
            ],
        },
    };
    return demos[engine] || demos.rapid_recall;
}

// ─── Start ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', boot);
// ─── Service Worker (Offline Mode) ─────────────────────
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('SW registered:', reg.scope))
            .catch(err => console.warn('SW registration failed:', err));
        
        // Listen for sync messages
        navigator.serviceWorker.addEventListener('message', (event) => {
            if (event.data.type === 'ONLINE_SYNC') {
                console.log('Back online — syncing progress...');
                if (App.db && App.user) {
                    syncToFirebase(App.db, App.user.uid);
                    showToast('Progress synced!');
                }
            }
        });
    });
}

// ─── Online/Offline indicators ─────────────────────────
window.addEventListener('offline', () => showToast('📡 You\'re offline — cached content still available'));
window.addEventListener('online', () => showToast('✅ Back online — syncing...'));