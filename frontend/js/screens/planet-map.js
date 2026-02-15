/**
 * MCAT Mastery — Planet Map Screen
 * 
 * Renders sector tabs + tile grid for a planet.
 * Tiles show cleared/available/fogged states.
 * Tap an available tile → start mission.
 */

let _currentPlanet = null;
let _currentSector = 0;

function initPlanetMap(planetId, planetData) {
    _currentPlanet = planetId;
    _currentSector = 0;
    
    _renderSectorTabs(planetData);
    _renderTileGrid(planetData, 0);
    _updatePlanetProgress(planetId);
}

// ─── Sector Tabs ────────────────────────────────────────

function _renderSectorTabs(planetData) {
    const container = document.getElementById('sector-list');
    if (!container) return;
    container.innerHTML = '';
    
    const sectors = planetData?.sectors || [];
    
    sectors.forEach((sector, idx) => {
        const tab = document.createElement('button');
        tab.className = `sector-tab ${idx === 0 ? 'active' : ''}`;
        tab.textContent = sector.name || `Sector ${idx + 1}`;
        tab.title = sector.chapter_topic || '';
        
        tab.addEventListener('click', () => {
            container.querySelectorAll('.sector-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            _currentSector = idx;
            _renderTileGrid(planetData, idx);
        });
        
        container.appendChild(tab);
    });
}

// ─── Tile Grid ──────────────────────────────────────────

function _renderTileGrid(planetData, sectorIdx) {
    const grid = document.getElementById('tile-grid');
    if (!grid) return;
    grid.innerHTML = '';
    
    const playerState = getPlayerState();
    const planetProgress = playerState.planetProgress?.[_currentPlanet] || {};
    const clearedTiles = planetProgress.clearedTiles || [];
    
    const sector = planetData?.sectors?.[sectorIdx];
    const tileCount = 8;
    
    // S-curve offsets: tiles snake left→center→right→center→left
    // Pattern repeats every 4 tiles: center, right, center, left
    const sCurveOffsets = [0, 80, 0, -80, 0, 80, 0, -80];
    
    for (let i = 0; i < tileCount; i++) {
        const tileId = `${_currentPlanet}_s${sectorIdx + 1}_t${i + 1}`;
        const isCleared = clearedTiles.includes(tileId);
        const prevCleared = i === 0 ? (sectorIdx === 0 || _isSectorCleared(planetProgress, sectorIdx - 1)) : clearedTiles.includes(`${_currentPlanet}_s${sectorIdx + 1}_t${i}`);
        const isAvailable = !isCleared && prevCleared;
        
        const tile = document.createElement('div');
        tile.className = `tile ${isCleared ? 'cleared' : isAvailable ? 'available' : 'fogged'}`;
        tile.setAttribute('data-tile-id', tileId);
        
        // Apply S-curve horizontal offset
        const offset = sCurveOffsets[i % sCurveOffsets.length];
        tile.style.transform = `translateX(${offset}px)`;
        
        // Creature overlay (random 20% chance on non-cleared tiles)
        const hasCreature = !isCleared && Math.random() < 0.2;
        
        const icon = isCleared ? '⭐' : isAvailable ? '▶' : '🔒';
        
        tile.innerHTML = `
            <span class="tile-icon">${icon}</span>
            ${hasCreature ? '<div class="tile-creature">👾</div>' : ''}
        `;
        
        if (isAvailable) {
            tile.addEventListener('click', () => {
                _startTileMission(tileId, sectorIdx, i);
            });
        } else if (isCleared) {
            tile.addEventListener('click', () => {
                _startReviewMission(tileId, sectorIdx, i);
            });
        }
        
        grid.appendChild(tile);
    }
}

function _isSectorCleared(planetProgress, sectorIdx) {
    const clearedTiles = planetProgress.clearedTiles || [];
    // Check if all tiles in a sector are cleared (simplified)
    const prefix = `${_currentPlanet}_s${sectorIdx + 1}_`;
    const sectorTiles = clearedTiles.filter(t => t.startsWith(prefix));
    return sectorTiles.length >= 8; // matches tileCount
}

// ─── Mission Launch ─────────────────────────────────────

function _startTileMission(tileId, sectorIdx, tileIdx) {
    // Check energy
    if (!hasEnergy()) {
        showToast('Neural Charge depleted! Wait for recharge or visit the Crystal Exchange.');
        return;
    }
    
    spendEnergy(1);
    updateHUD();
    
    // Check for creature encounter on this tile
    let creatureData = null;
    if (typeof hasCreatureEncounter === 'function' && hasCreatureEncounter(tileId, _currentPlanet)) {
        creatureData = typeof getCreatureForTile === 'function' ? getCreatureForTile(tileId, _currentPlanet) : null;
    }
    
    // Launch mission screen
    initMission({
        tileId,
        planetId: _currentPlanet,
        sectorIdx,
        tileIdx,
        type: 'guided_learning',
        creature: creatureData,
    });
    showScreen('mission-screen');
}

function _startReviewMission(tileId, sectorIdx, tileIdx) {
    // Review missions are FREE
    initMission({
        tileId,
        planetId: _currentPlanet,
        sectorIdx,
        tileIdx,
        type: 'review',
    });
    showScreen('mission-screen');
}

// ─── Progress Display ───────────────────────────────────

function _updatePlanetProgress(planetId) {
    const playerState = getPlayerState();
    const progress = playerState.planetProgress?.[planetId] || {};
    const clearedCount = progress.clearedTiles?.length || 0;
    const pct = progress.percentCleared || Math.round((clearedCount / 96) * 100);
    
    const pctEl = document.getElementById('planet-progress-pct');
    if (pctEl) pctEl.textContent = `${pct}%`;
}

/**
 * Called after a mission completes to mark tile as cleared.
 */
function markTileCleared(tileId) {
    // Update player state — pass completed=true to actually record it
    updatePlanetProgress(_currentPlanet, tileId, true);
    
    // Animate the tile
    const tile = document.querySelector(`[data-tile-id="${tileId}"]`);
    if (tile) {
        tile.className = 'tile cleared just-cleared';
        tile.querySelector('.tile-icon').textContent = '✨';
    }
    
    // Re-render to update available neighbors
    // (deferred to let animation play)
    setTimeout(() => {
        const planetData = getPlanetForSubject(_subjectForPlanet(_currentPlanet));
        _renderTileGrid(planetData, _currentSector);
        _updatePlanetProgress(_currentPlanet);
        updateHUD();
    }, 900);
}
