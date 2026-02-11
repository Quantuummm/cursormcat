/**
 * MCAT Mastery — Mission Screen
 * 
 * Plays through a Guided Learning mission (Phase 8 output):
 *   learn_segment → question → feedback → learn_segment → ...
 * 
 * Handles: learn segments, 7 question types, creature encounters,
 * streak tracking, TTS playback, and rewards.
 */

let _mission = {
    config: null,      // { tileId, planetId, sectorIdx, tileIdx, type }
    segments: [],      // Array of learn/question/creature nodes
    currentIdx: 0,
    streak: 0,
    correct: 0,
    total: 0,
    startTime: 0,
};

function initMission(config) {
    _mission.config = config;
    _mission.currentIdx = 0;
    _mission.streak = 0;
    _mission.correct = 0;
    _mission.total = 0;
    _mission.startTime = Date.now();
    
    // Load mission segments from game data
    // In production: fetch from Firestore concepts/{subject}/levels/{chapter}
    // For now: use placeholder structure
    _mission.segments = _buildDemoSegments(config);
    
    _updateMissionProgress();
    _showSegment(0);
}

// ─── Segment Router ─────────────────────────────────────

function _showSegment(idx) {
    if (idx >= _mission.segments.length) {
        _completeMission();
        return;
    }
    
    _mission.currentIdx = idx;
    _updateMissionProgress();
    
    const seg = _mission.segments[idx];
    const body = document.getElementById('mission-body');
    const footer = document.getElementById('mission-footer');
    body.innerHTML = '';
    footer.innerHTML = '';
    
    switch (seg.type) {
        case 'learn':
            _renderLearnSegment(seg, body, footer);
            break;
        case 'question':
            _renderQuestion(seg, body, footer);
            break;
        case 'creature':
            _renderCreatureEncounter(seg, body, footer);
            break;
        default:
            _showSegment(idx + 1);
    }
}

// ─── Learn Segment ──────────────────────────────────────

function _renderLearnSegment(seg, body, footer) {
    const speakerName = seg.speaker_id === 'lyra' ? 'LYRA' :
                        seg.speaker_id === 'grimble' ? 'Grimble' :
                        seg.specialist_name || 'Specialist';
    
    const speakerColor = seg.speaker_id === 'lyra' ? 'var(--lyra-blue)' :
                         seg.speaker_id === 'grimble' ? 'var(--grimble-purple)' :
                         'var(--planet-primary, var(--text-accent))';
    
    body.innerHTML = `
        <div class="learn-segment">
            <div class="learn-speaker">
                <div class="learn-speaker-avatar" style="background: ${speakerColor}; width: 32px; height: 32px; border-radius: 50%;"></div>
                <span class="learn-speaker-name" style="color: ${speakerColor}">${speakerName}</span>
            </div>
            <div class="learn-text">${seg.narrator_text}</div>
        </div>
    `;
    
    footer.innerHTML = `
        <button class="btn btn-primary btn-large" id="btn-continue">Continue</button>
    `;
    
    // TTS playback
    if (seg.narrator_text) {
        speak(seg.narrator_text, seg.speaker_id, seg.audio_path);
    }
    
    document.getElementById('btn-continue').addEventListener('click', () => {
        stopSpeaking();
        _showSegment(_mission.currentIdx + 1);
    });
}

// ─── Question ───────────────────────────────────────────

function _renderQuestion(seg, body, footer) {
    const q = seg.question;
    _mission.total++;
    
    let optionsHtml = '';
    const labels = ['A', 'B', 'C', 'D', 'E', 'F'];
    
    if (q.options) {
        q.options.forEach((opt, i) => {
            optionsHtml += `
                <button class="answer-btn" data-idx="${i}" data-correct="${opt.correct || false}">
                    <span class="answer-label">${labels[i]}</span>
                    <span>${opt.text}</span>
                </button>
            `;
        });
    }
    
    body.innerHTML = `
        <div class="question-block">
            ${q.passage ? `<div class="question-passage">${q.passage}</div>` : ''}
            <div class="question-stem">${q.stem}</div>
            <div class="answer-options" id="answer-options">
                ${optionsHtml}
            </div>
        </div>
    `;
    
    // Wire answer buttons
    document.querySelectorAll('#answer-options .answer-btn').forEach(btn => {
        btn.addEventListener('click', () => _handleAnswer(btn, seg));
    });
}

function _handleAnswer(btn, seg) {
    const isCorrect = btn.getAttribute('data-correct') === 'true';
    const allBtns = document.querySelectorAll('#answer-options .answer-btn');
    
    // Disable all buttons
    allBtns.forEach(b => {
        b.style.pointerEvents = 'none';
        if (b.getAttribute('data-correct') === 'true') {
            b.classList.add('correct');
        }
    });
    
    if (isCorrect) {
        btn.classList.add('correct');
        _mission.correct++;
        _mission.streak++;
        _updateStreakDisplay();
        
        // Resonance strike VFX
        _spawnResonanceVFX(btn);
    } else {
        btn.classList.add('incorrect');
        _mission.streak = 0;
        _updateStreakDisplay();
        
        // Corruption flash
        const block = btn.closest('.question-block');
        if (block) block.classList.add('corruption-flash');
    }
    
    // Show feedback
    const feedback = isCorrect ? seg.question.correct_feedback : seg.question.wrong_feedback;
    const feedbackSpeaker = isCorrect ? 'specialist' : 'lyra';
    
    const feedbackCard = document.createElement('div');
    feedbackCard.className = `feedback-card ${isCorrect ? 'correct' : 'incorrect'}`;
    feedbackCard.innerHTML = `
        <div class="feedback-speaker">${isCorrect ? '✅' : '🔄'} ${isCorrect ? 'Neural pathway confirmed!' : 'Partial recall — reinforcing pathway'}</div>
        <p>${feedback || (isCorrect ? 'Correct!' : 'Not quite — let\'s reinforce this.')}</p>
    `;
    
    document.getElementById('mission-body').appendChild(feedbackCard);
    
    // TTS feedback
    if (feedback) speak(feedback, feedbackSpeaker);
    
    // Continue button
    const footer = document.getElementById('mission-footer');
    footer.innerHTML = `<button class="btn btn-primary btn-large" id="btn-continue">Continue</button>`;
    document.getElementById('btn-continue').addEventListener('click', () => {
        stopSpeaking();
        _showSegment(_mission.currentIdx + 1);
    });
}

// ─── Creature Encounter ─────────────────────────────────

function _renderCreatureEncounter(seg, body, footer) {
    body.innerHTML = `
        <div class="creature-encounter">
            <div class="creature-sprite">${seg.creature_emoji || '👾'}</div>
            <h3 class="creature-name">${seg.creature_name || 'Corrupted Creature'}</h3>
            <p>${seg.grimble_taunt || 'A corrupted creature blocks your path!'}</p>
        </div>
    `;
    
    // After a beat, show the bonus question
    footer.innerHTML = `<button class="btn btn-primary btn-large" id="btn-face-creature">Face the Creature</button>`;
    document.getElementById('btn-face-creature').addEventListener('click', () => {
        // Creature encounter is a bonus question
        _showSegment(_mission.currentIdx + 1);
    });
}

// ─── VFX ────────────────────────────────────────────────

function _spawnResonanceVFX(targetEl) {
    const rect = targetEl.getBoundingClientRect();
    const vfx = document.createElement('div');
    vfx.className = 'resonance-vfx';
    vfx.style.left = `${rect.left + rect.width / 2 - 60}px`;
    vfx.style.top = `${rect.top + rect.height / 2 - 60}px`;
    document.body.appendChild(vfx);
    setTimeout(() => vfx.remove(), 700);
    
    // Crystal popup
    const popup = document.createElement('div');
    popup.className = 'crystal-popup';
    popup.textContent = '+✨';
    popup.style.left = `${rect.right - 20}px`;
    popup.style.top = `${rect.top}px`;
    document.body.appendChild(popup);
    setTimeout(() => popup.remove(), 1100);
}

// ─── Progress & Streak ──────────────────────────────────

function _updateMissionProgress() {
    const fill = document.getElementById('mission-bar-fill');
    if (fill && _mission.segments.length > 0) {
        const pct = (_mission.currentIdx / _mission.segments.length) * 100;
        fill.style.width = `${pct}%`;
    }
}

function _updateStreakDisplay() {
    const numEl = document.getElementById('mission-streak-num');
    const container = document.querySelector('.mission-streak-counter');
    
    if (numEl) numEl.textContent = _mission.streak;
    
    if (container) {
        container.classList.toggle('hot', _mission.streak >= 3);
    }
}

// ─── Mission Complete ───────────────────────────────────

function _completeMission() {
    const accuracy = _mission.total > 0 ? _mission.correct / _mission.total : 1;
    const baseCrystals = _mission.config.type === 'review' ? 0 : 30;
    const crystals = Math.round(baseCrystals + (accuracy * 20));
    const xp = Math.round(50 + (accuracy * 50));
    const perfectBonus = accuracy === 1 ? 25 : 0;
    
    // Update player state
    if (_mission.config.type !== 'review') {
        markTileCleared(_mission.config.tileId);
    }
    
    // Update streak
    updateDailyStreak();
    
    // Show reward popup
    showRewardPopup(
        _mission.config.type === 'review' ? 'Signal Stabilized!' : 'Sector Stabilized!',
        { xp, crystals: crystals + perfectBonus }
    );
    
    // Return to planet map
    document.getElementById('btn-collect-rewards').addEventListener('click', () => {
        showScreen('planet-map-screen');
        updateHUD();
    }, { once: true });
}

// ─── Demo/Placeholder Segments ──────────────────────────

function _buildDemoSegments(config) {
    // In production, this fetches from Firestore per tile
    // For now, return a short demo sequence
    return [
        {
            type: 'learn',
            speaker_id: 'lyra',
            narrator_text: "Commander, we're entering a new sector. Let me brief you on what we know.",
        },
        {
            type: 'learn',
            speaker_id: 'specialist',
            specialist_name: 'Dr. Kade',
            narrator_text: "Welcome to my domain. The cells here hold the key to understanding life itself. Let's start with the basics of cell structure.",
        },
        {
            type: 'question',
            question: {
                stem: "Which organelle is responsible for producing ATP, the cell's primary energy currency?",
                options: [
                    { text: "Ribosome", correct: false },
                    { text: "Mitochondria", correct: true },
                    { text: "Golgi apparatus", correct: false },
                    { text: "Endoplasmic reticulum", correct: false },
                ],
                correct_feedback: "That's right! The mitochondria are the powerhouse of the cell, producing ATP through oxidative phosphorylation.",
                wrong_feedback: "Not quite. Remember, mitochondria are where aerobic respiration occurs — they're the cell's energy factories.",
            },
        },
        {
            type: 'learn',
            speaker_id: 'specialist',
            specialist_name: 'Dr. Kade',
            narrator_text: "Excellent work stabilizing that pathway. ATP is produced via the electron transport chain in the inner mitochondrial membrane.",
        },
        {
            type: 'question',
            question: {
                stem: "The inner mitochondrial membrane is the site of which process?",
                options: [
                    { text: "Glycolysis", correct: false },
                    { text: "Krebs cycle", correct: false },
                    { text: "Oxidative phosphorylation", correct: true },
                    { text: "Fermentation", correct: false },
                ],
                correct_feedback: "Correct! Oxidative phosphorylation occurs at the inner mitochondrial membrane via the electron transport chain and ATP synthase.",
                wrong_feedback: "Close — glycolysis occurs in the cytoplasm, and the Krebs cycle is in the mitochondrial matrix. The inner membrane hosts the ETC.",
            },
        },
        {
            type: 'learn',
            speaker_id: 'lyra',
            narrator_text: "Sector stabilizing, Commander. Your neural pathways are forming strong connections. One more challenge ahead.",
        },
    ];
}
