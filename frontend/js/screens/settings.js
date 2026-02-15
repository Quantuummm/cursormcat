/**
 * MCAT Mastery — Settings Screen
 * 
 * Controls: TTS, Music, SFX toggles, TTS speed, reset data,
 * Firebase sync, about info.
 */

function initSettings() {
    const body = document.getElementById('settings-body');
    if (!body) return;
    
    const s = Player.settings;
    
    body.innerHTML = `
        <div class="settings-section">
            <h3 class="settings-title">🔊 Audio</h3>
            
            <div class="setting-row">
                <span class="setting-label">Text-to-Speech (LYRA & Specialists)</span>
                <label class="toggle">
                    <input type="checkbox" id="set-tts" ${s.ttsEnabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="setting-row">
                <span class="setting-label">Background Music</span>
                <label class="toggle">
                    <input type="checkbox" id="set-music" ${s.musicEnabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="setting-row">
                <span class="setting-label">Sound Effects</span>
                <label class="toggle">
                    <input type="checkbox" id="set-sfx" ${s.sfxEnabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="setting-row">
                <span class="setting-label">TTS Speed</span>
                <div class="setting-range">
                    <input type="range" id="set-tts-speed" min="0.5" max="2.0" step="0.1" 
                           value="${s.ttsSpeed || 1.0}">
                    <span class="range-val" id="tts-speed-val">${s.ttsSpeed || 1.0}x</span>
                </div>
            </div>
        </div>
        
        <div class="settings-section">
            <h3 class="settings-title">💾 Data</h3>
            
            <div class="setting-row">
                <span class="setting-label">Sync to Cloud</span>
                <button class="btn btn-secondary btn-sm" id="btn-sync-cloud">Sync Now</button>
            </div>
            
            <div class="setting-row">
                <span class="setting-label">Clear Local Cache</span>
                <button class="btn btn-secondary btn-sm" id="btn-clear-cache">Clear</button>
            </div>
            
            <div class="setting-row setting-danger">
                <span class="setting-label">Reset All Progress</span>
                <button class="btn btn-danger btn-sm" id="btn-reset-all">Reset</button>
            </div>
        </div>
        
        <div class="settings-section">
            <h3 class="settings-title">ℹ️ About</h3>
            <div class="about-info">
                <p><strong>MCAT Mastery</strong> — Gamified MCAT Study Platform</p>
                <p>Version 1.0.0</p>
                <p>Commander: ${Player.commanderName || 'Unknown'}</p>
                <p>UID: ${App.user?.uid?.substring(0, 8) || 'offline'}...</p>
            </div>
        </div>
    `;
    
    // Wire toggles
    document.getElementById('set-tts').addEventListener('change', (e) => {
        Player.settings.ttsEnabled = e.target.checked;
        _saveLocal();
    });
    
    document.getElementById('set-music').addEventListener('change', (e) => {
        Player.settings.musicEnabled = e.target.checked;
        _saveLocal();
    });
    
    document.getElementById('set-sfx').addEventListener('change', (e) => {
        Player.settings.sfxEnabled = e.target.checked;
        _saveLocal();
    });
    
    document.getElementById('set-tts-speed').addEventListener('input', (e) => {
        const speed = parseFloat(e.target.value);
        Player.settings.ttsSpeed = speed;
        document.getElementById('tts-speed-val').textContent = `${speed.toFixed(1)}x`;
        _saveLocal();
    });
    
    // Wire buttons
    document.getElementById('btn-sync-cloud').addEventListener('click', async () => {
        if (App.db && App.user) {
            await syncToFirebase(App.db, App.user.uid);
            showToast('Progress synced to cloud!');
        } else {
            showToast('Not signed in — sync unavailable');
        }
    });
    
    document.getElementById('btn-clear-cache').addEventListener('click', () => {
        if (confirm('Clear local cache? Your cloud data is safe.')) {
            localStorage.removeItem('mcat_game_data');
            showToast('Cache cleared');
        }
    });
    
    document.getElementById('btn-reset-all').addEventListener('click', () => {
        if (confirm('⚠️ This will permanently delete ALL progress. Are you sure?')) {
            if (confirm('Really? This cannot be undone.')) {
                localStorage.clear();
                location.reload();
            }
        }
    });
}
