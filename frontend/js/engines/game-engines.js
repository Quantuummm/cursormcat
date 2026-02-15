/**
 * MCAT Mastery — Game Mode Engines
 * 
 * 7 Mem-Game engines that render different mini-game types.
 * Each engine takes a mode payload (from Firestore compiled_modes)
 * and renders into the #game-arena container.
 * 
 * Engines:
 *   1. rapid_recall    — Timed flashcard-style term → definition matching
 *   2. sort_buckets    — Drag/tap items into correct category buckets
 *   3. equation_forge  — Build equations from shuffled components
 *   4. concept_clash   — True/false or A vs B rapid-fire
 *   5. sequence_builder— Order steps/processes into correct sequence
 *   6. label_text      — Fill in blanks on diagrams or passages
 *   7. table_challenge — Complete comparison tables (fill cells)
 * 
 * All engines are FREE (no Neural Charge cost).
 * Reward: 10-20 crystals per completion.
 */

const GameEngines = {};
let _gameReturnScreen = 'planet-map-screen';

// ─── Engine Registry ────────────────────────────────────

const ENGINE_REGISTRY = {
    rapid_recall:     renderRapidRecall,
    sort_buckets:     renderSortBuckets,
    equation_forge:   renderEquationForge,
    concept_clash:    renderConceptClash,
    sequence_builder: renderSequenceBuilder,
    label_text:       renderLabelText,
    table_challenge:  renderTableChallenge,
};

/**
 * Launch a game mode by engine type.
 * @param {object} modeData - Full mode payload from compiled_modes
 */
function launchGameMode(modeData, returnScreen) {
    const engine = ENGINE_REGISTRY[modeData.engine];
    if (!engine) {
        console.error(`Unknown engine: ${modeData.engine}`);
        return;
    }
    
    _gameReturnScreen = returnScreen || 'planet-map-screen';
    document.getElementById('game-mode-title').textContent = _engineDisplayName(modeData.engine);
    showScreen('game-mode-screen');
    
    engine(modeData);
}

function _engineDisplayName(engineId) {
    const names = {
        rapid_recall:     'Rapid Recall',
        sort_buckets:     'Sort & Classify',
        equation_forge:   'Equation Forge',
        concept_clash:    'Concept Clash',
        sequence_builder: 'Sequence Builder',
        label_text:       'Label Master',
        table_challenge:  'Table Challenge',
    };
    return names[engineId] || engineId;
}

// ─── 1. RAPID RECALL ────────────────────────────────────
// Timed flashcard-style: see a term → pick the definition (or vice versa)

function renderRapidRecall(mode) {
    const arena = document.getElementById('game-arena');
    const items = mode.instances || mode.items || [];
    let currentIdx = 0;
    let score = 0;
    let startTime = Date.now();
    let answering = false;
    
    function showCard() {
        if (currentIdx >= items.length) {
            _completeGame(mode, score, items.length, startTime);
            return;
        }
        answering = false;
        
        const item = items[currentIdx];
        const correct = item.definition || item.answer;
        const distractors = _pickDistractors(items, currentIdx, 3).map(d => d.definition || d.answer);
        const options = _shuffle([correct, ...distractors]);
        
        arena.innerHTML = `
            <div class="game-card">
                <h3 class="game-prompt">${item.term || item.question}</h3>
                <div class="game-options">
                    ${options.map((opt, i) => `
                        <button class="answer-btn game-option" data-correct="${opt === correct}">
                            <span>${opt}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        arena.querySelectorAll('.game-option').forEach(btn => {
            btn.addEventListener('click', () => {
                if (answering) return;
                answering = true;
                const isCorrect = btn.getAttribute('data-correct') === 'true';
                btn.classList.add(isCorrect ? 'correct' : 'incorrect');
                if (isCorrect) score++;
                
                // Show correct briefly
                arena.querySelectorAll('.game-option').forEach(b => {
                    b.style.pointerEvents = 'none';
                    if (b.getAttribute('data-correct') === 'true') b.classList.add('correct');
                });
                
                setTimeout(() => { currentIdx++; showCard(); }, 800);
            });
        });
    }
    
    showCard();
}

// ─── 2. SORT BUCKETS ───────────────────────────────────
// Categorize items into correct groups

function renderSortBuckets(mode) {
    const arena = document.getElementById('game-arena');
    const buckets = mode.categories || mode.buckets || [];
    const allItems = [];
    
    buckets.forEach(bucket => {
        (bucket.items || []).forEach(item => {
            allItems.push({ text: item, correctBucket: bucket.name || bucket.label });
        });
    });
    
    const shuffled = _shuffle([...allItems]);
    let currentIdx = 0;
    let score = 0;
    const startTime = Date.now();
    
    function showItem() {
        if (currentIdx >= shuffled.length) {
            _completeGame(mode, score, shuffled.length, startTime);
            return;
        }
        
        const item = shuffled[currentIdx];
        
        arena.innerHTML = `
            <div class="game-card">
                <h3 class="game-prompt">${item.text}</h3>
                <p style="color: var(--text-muted); margin-bottom: var(--gap-md);">Which category?</p>
                <div class="game-options">
                    ${buckets.map(b => `
                        <button class="answer-btn game-option" data-bucket="${b.name || b.label}" data-correct="${(b.name || b.label) === item.correctBucket}">
                            <span>${b.name || b.label}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        arena.querySelectorAll('.game-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const isCorrect = btn.getAttribute('data-correct') === 'true';
                btn.classList.add(isCorrect ? 'correct' : 'incorrect');
                if (isCorrect) score++;
                
                arena.querySelectorAll('.game-option').forEach(b => {
                    b.style.pointerEvents = 'none';
                    if (b.getAttribute('data-correct') === 'true') b.classList.add('correct');
                });
                
                setTimeout(() => { currentIdx++; showItem(); }, 800);
            });
        });
    }
    
    showItem();
}

// ─── 3. EQUATION FORGE ──────────────────────────────────
// Build equations from shuffled components

function renderEquationForge(mode) {
    const arena = document.getElementById('game-arena');
    const equations = mode.equations || mode.instances || [];
    let currentIdx = 0;
    let score = 0;
    const startTime = Date.now();
    
    function showEquation() {
        if (currentIdx >= equations.length) {
            _completeGame(mode, score, equations.length, startTime);
            return;
        }
        
        const eq = equations[currentIdx];
        const components = _shuffle([...(eq.components || eq.parts || [])]);
        let selected = [];
        
        arena.innerHTML = `
            <div class="game-card">
                <h3 class="game-prompt">${eq.name || eq.equation_name || 'Build the equation'}</h3>
                <div class="equation-workspace" id="eq-workspace">
                    <div class="equation-answer" id="eq-answer"></div>
                    <div class="equation-parts" id="eq-parts">
                        ${components.map((c, i) => `
                            <button class="btn btn-secondary equation-part" data-idx="${i}" data-value="${c}">${c}</button>
                        `).join('')}
                    </div>
                </div>
                <button class="btn btn-primary" id="eq-check" style="margin-top: var(--gap-md)">Check</button>
            </div>
        `;
        
        // Tap parts to add to answer
        arena.querySelectorAll('.equation-part').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.classList.contains('used')) return;
                btn.classList.add('used');
                selected.push(btn.getAttribute('data-value'));
                document.getElementById('eq-answer').textContent = selected.join(' ');
            });
        });
        
        document.getElementById('eq-check').addEventListener('click', () => {
            const answer = selected.join(' ');
            const correct = (eq.components || eq.parts || []).join(' ');
            const isCorrect = answer === correct;
            
            if (isCorrect) {
                score++;
                document.getElementById('eq-answer').style.borderColor = 'var(--health-green)';
            } else {
                document.getElementById('eq-answer').style.borderColor = 'var(--danger-red)';
                document.getElementById('eq-answer').textContent = `Correct: ${correct}`;
            }
            
            setTimeout(() => { currentIdx++; showEquation(); }, 1200);
        });
    }
    
    showEquation();
}

// ─── 4. CONCEPT CLASH ───────────────────────────────────
// True/false or A-vs-B rapid fire

function renderConceptClash(mode) {
    const arena = document.getElementById('game-arena');
    const items = mode.instances || mode.items || [];
    let currentIdx = 0;
    let score = 0;
    const startTime = Date.now();
    
    function showClash() {
        if (currentIdx >= items.length) {
            _completeGame(mode, score, items.length, startTime);
            return;
        }
        
        const item = items[currentIdx];
        
        arena.innerHTML = `
            <div class="game-card">
                <h3 class="game-prompt">${item.statement || item.question}</h3>
                <div class="game-options" style="flex-direction: row; justify-content: center; gap: var(--gap-lg);">
                    <button class="btn btn-large game-clash-btn" data-answer="true" style="background: var(--health-green); color: #fff; min-width: 120px;">
                        ${item.option_a || 'TRUE'}
                    </button>
                    <button class="btn btn-large game-clash-btn" data-answer="false" style="background: var(--danger-red); color: #fff; min-width: 120px;">
                        ${item.option_b || 'FALSE'}
                    </button>
                </div>
            </div>
        `;
        
        arena.querySelectorAll('.game-clash-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const playerAnswer = btn.getAttribute('data-answer');
                const correctAnswer = String(item.correct_answer ?? item.is_true ?? true);
                const isCorrect = playerAnswer === correctAnswer;
                
                btn.style.boxShadow = isCorrect ? '0 0 16px var(--health-green)' : '0 0 16px var(--danger-red)';
                if (isCorrect) score++;
                
                arena.querySelectorAll('.game-clash-btn').forEach(b => b.style.pointerEvents = 'none');
                
                setTimeout(() => { currentIdx++; showClash(); }, 700);
            });
        });
    }
    
    showClash();
}

// ─── 5. SEQUENCE BUILDER ────────────────────────────────
// Order steps into correct sequence

function renderSequenceBuilder(mode) {
    const arena = document.getElementById('game-arena');
    const steps = mode.correct_order || mode.steps || [];
    const shuffled = _shuffle([...steps]);
    let selected = [];
    const startTime = Date.now();
    
    function render() {
        arena.innerHTML = `
            <div class="game-card">
                <h3 class="game-prompt">${mode.title || mode.prompt || 'Put these in order'}</h3>
                <div class="sequence-selected" id="seq-selected" style="min-height: 60px; background: var(--bg-elevated); padding: var(--gap-md); border-radius: var(--radius-md); margin-bottom: var(--gap-md);">
                    ${selected.map((s, i) => `<div class="seq-item" style="padding: 6px; border-bottom: 1px solid var(--border);">${i + 1}. ${s}</div>`).join('')}
                </div>
                <div class="game-options" id="seq-options">
                    ${shuffled.filter(s => !selected.includes(s)).map(s => `
                        <button class="answer-btn game-option" data-value="${s}"><span>${s}</span></button>
                    `).join('')}
                </div>
                ${selected.length === steps.length ? '<button class="btn btn-primary" id="seq-check" style="margin-top: var(--gap-md);">Check Order</button>' : ''}
            </div>
        `;
        
        arena.querySelectorAll('#seq-options .game-option').forEach(btn => {
            btn.addEventListener('click', () => {
                selected.push(btn.getAttribute('data-value'));
                render();
            });
        });
        
        const checkBtn = document.getElementById('seq-check');
        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                const isCorrect = selected.every((s, i) => s === steps[i]);
                _completeGame(mode, isCorrect ? 1 : 0, 1, startTime);
            });
        }
    }
    
    render();
}

// ─── 6. LABEL TEXT ──────────────────────────────────────
// Fill in blanks on text/diagrams

function renderLabelText(mode) {
    const arena = document.getElementById('game-arena');
    const blanks = mode.blanks || mode.labels || [];
    let answers = {};
    const startTime = Date.now();
    
    // Build text with blanks
    let text = mode.text || mode.passage || '';
    blanks.forEach((blank, i) => {
        text = text.replace(blank.answer || blank.correct, `<input type="text" class="label-blank" data-idx="${i}" placeholder="___" style="width: 120px; text-align: center; border: 2px solid var(--border); border-radius: var(--radius-sm); padding: 4px 8px; background: var(--bg-elevated); color: var(--text-primary); font-family: var(--font-body);">`);
    });
    
    arena.innerHTML = `
        <div class="game-card">
            <h3 class="game-prompt">${mode.title || 'Fill in the blanks'}</h3>
            <div class="label-text-body" style="line-height: 2; font-size: 1rem;">${text}</div>
            <button class="btn btn-primary" id="label-check" style="margin-top: var(--gap-lg);">Check</button>
        </div>
    `;
    
    document.getElementById('label-check').addEventListener('click', () => {
        let score = 0;
        arena.querySelectorAll('.label-blank').forEach(input => {
            const idx = parseInt(input.getAttribute('data-idx'));
            const correct = (blanks[idx]?.answer || blanks[idx]?.correct || '').toLowerCase().trim();
            const given = input.value.toLowerCase().trim();
            
            if (given === correct) {
                score++;
                input.style.borderColor = 'var(--health-green)';
            } else {
                input.style.borderColor = 'var(--danger-red)';
                input.value = blanks[idx]?.answer || blanks[idx]?.correct || '';
            }
        });
        
        setTimeout(() => _completeGame(mode, score, blanks.length, startTime), 1500);
    });
}

// ─── 7. TABLE CHALLENGE ─────────────────────────────────
// Complete comparison tables

function renderTableChallenge(mode) {
    const arena = document.getElementById('game-arena');
    const rows = mode.rows || [];
    const columns = mode.columns || mode.headers || [];
    const hiddenCells = mode.hidden_cells || [];
    const startTime = Date.now();
    
    let tableHtml = '<table class="game-table" style="width: 100%; border-collapse: collapse;">';
    
    // Header
    tableHtml += '<tr>';
    columns.forEach(col => {
        tableHtml += `<th style="padding: 8px; border: 1px solid var(--border); background: var(--bg-elevated); font-weight: 700;">${col}</th>`;
    });
    tableHtml += '</tr>';
    
    // Rows
    rows.forEach((row, ri) => {
        tableHtml += '<tr>';
        (row.cells || row).forEach((cell, ci) => {
            const cellId = `${ri}-${ci}`;
            const isHidden = hiddenCells.some(h => h.row === ri && h.col === ci);
            
            if (isHidden) {
                tableHtml += `<td style="padding: 8px; border: 1px solid var(--border);">
                    <input type="text" class="table-cell-input" data-row="${ri}" data-col="${ci}" data-answer="${cell}" placeholder="?" style="width: 100%; border: none; background: transparent; color: var(--text-primary); text-align: center; font-family: var(--font-body);">
                </td>`;
            } else {
                tableHtml += `<td style="padding: 8px; border: 1px solid var(--border);">${cell}</td>`;
            }
        });
        tableHtml += '</tr>';
    });
    
    tableHtml += '</table>';
    
    arena.innerHTML = `
        <div class="game-card">
            <h3 class="game-prompt">${mode.title || 'Complete the table'}</h3>
            ${tableHtml}
            <button class="btn btn-primary" id="table-check" style="margin-top: var(--gap-lg);">Check</button>
        </div>
    `;
    
    document.getElementById('table-check').addEventListener('click', () => {
        let score = 0;
        arena.querySelectorAll('.table-cell-input').forEach(input => {
            const correct = (input.getAttribute('data-answer') || '').toLowerCase().trim();
            const given = input.value.toLowerCase().trim();
            
            if (given === correct) {
                score++;
                input.style.color = 'var(--health-green)';
            } else {
                input.style.color = 'var(--danger-red)';
                input.value = input.getAttribute('data-answer');
            }
        });
        
        setTimeout(() => _completeGame(mode, score, hiddenCells.length || 1, startTime), 1500);
    });
}

// ─── Shared Completion ──────────────────────────────────

function _completeGame(mode, score, total, startTime) {
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    const accuracy = total > 0 ? score / total : 1;
    const crystals = Math.round(10 + (accuracy * 10));
    
    const arena = document.getElementById('game-arena');
    arena.innerHTML = `
        <div class="game-card" style="text-align: center;">
            <h3 style="color: var(--crystal); margin-bottom: var(--gap-md);">
                ${accuracy >= 0.8 ? '⭐ Great Work!' : accuracy >= 0.5 ? '👍 Good Effort!' : '💪 Keep Practicing!'}
            </h3>
            <p style="font-size: 1.2rem; font-weight: 700;">${score}/${total} correct</p>
            <p style="color: var(--text-muted);">Time: ${elapsed}s</p>
            <div style="margin: var(--gap-lg) 0;">
                <div class="reward-row">✨ ${crystals} Crystals</div>
            </div>
            <button class="btn btn-primary btn-large" id="btn-game-done">Continue</button>
        </div>
    `;
    
    addCrystals(crystals);
    
    document.getElementById('btn-game-done').addEventListener('click', () => {
        showScreen(_gameReturnScreen);
        updateHUD();
        if (_gameReturnScreen === 'dashboard-screen') initDashboard();
    });
}

// ─── Helpers ────────────────────────────────────────────

function _shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function _pickDistractors(items, excludeIdx, count) {
    const pool = items.filter((_, i) => i !== excludeIdx);
    return _shuffle(pool).slice(0, count);
}
