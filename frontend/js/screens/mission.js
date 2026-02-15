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

async function initMission(config) {
    _mission.config = config;
    _mission.currentIdx = 0;
    _mission.streak = 0;
    _mission.correct = 0;
    _mission.total = 0;
    _mission.startTime = Date.now();
    
    // Try to load real Phase 8 structured content
    _mission.segments = await _loadMissionSegments(config);
    if (!_mission.segments || _mission.segments.length === 0) {
        // Fallback to demo data
        _mission.segments = _buildDemoSegments(config);
    }
    
    // Inject creature encounter if present
    if (config.creature) {
        const creatureIdx = Math.min(3, _mission.segments.length - 1);
        _mission.segments.splice(creatureIdx, 0, {
            type: 'creature',
            creature_emoji: config.creature.emoji,
            creature_name: config.creature.name,
            grimble_taunt: config.creature.grimbleTaunt,
            freed_dialogue: config.creature.freedDialogue,
            tile_id: config.tileId,
        });
    }
    
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
    // Support both nested (demo) and flat (Phase 8) question formats
    const q = seg.question || {
        stem: seg.question_text || '',
        options: (seg.options || []).map((opt, i) => ({
            text: typeof opt === 'string' ? opt : opt.text || opt,
            correct: seg.correct_index === i || opt.correct || false,
        })),
        passage: seg.passage || null,
        correct_feedback: seg.correct_response || 'Correct!',
        wrong_feedback: seg.wrong_response || 'Not quite.',
    };
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
        
        // Check question streak bonus
        if (typeof checkQuestionStreakBonus === 'function') {
            const bonus = checkQuestionStreakBonus(_mission.streak);
            if (bonus) showToast(bonus.message);
        }
        
        // Resonance strike VFX
        _spawnResonanceVFX(btn);
        Mobile.hapticNotification('success');
    } else {
        btn.classList.add('incorrect');
        _mission.streak = 0;
        _updateStreakDisplay();
        Mobile.hapticNotification('error');
        
        // Corruption flash
        const block = btn.closest('.question-block');
        if (block) block.classList.add('corruption-flash');
    }
    
    // Show feedback — safely access from nested or flat format
    const q = seg.question || {};
    const feedback = isCorrect
        ? (q.correct_feedback || seg.correct_response || 'Correct!')
        : (q.wrong_feedback || seg.wrong_response || 'Not quite — let\'s reinforce this.');
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
        // Free the creature and show freed dialogue
        if (seg.tile_id && typeof freeCreature === 'function') {
            freeCreature(seg.tile_id);
        }
        
        // Show freed animation
        body.innerHTML = `
            <div class="creature-encounter creature-freed">
                <div class="creature-sprite" style="filter: none; opacity: 0.9;">${seg.creature_emoji || '👾'}</div>
                <h3 class="creature-name" style="color: var(--success);">${seg.creature_name || 'Creature'} Freed!</h3>
                <p style="color: var(--text-accent);">${seg.freed_dialogue || 'Thank you for freeing me!'}</p>
                <div class="creature-reward">+10 ✨ crystals</div>
            </div>
        `;
        footer.innerHTML = `<button class="btn btn-primary btn-large" id="btn-continue">Continue</button>`;
        document.getElementById('btn-continue').addEventListener('click', () => {
            _showSegment(_mission.currentIdx + 1);
        });
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
    
    // Award crystals to player
    addCrystals(crystals + perfectBonus, 'mission_complete');
    
    // Update streak
    updateDailyStreak();
    
    // Start fog timer for the cleared tile (spaced repetition)
    if (typeof advanceFogTimer === 'function') {
        advanceFogTimer(_mission.config.tileId, true);
    }
    
    // Generate field note from mission content
    _generateFieldNote();
    
    // Submit to leaderboard
    if (typeof submitLeaderboardScore === 'function') {
        submitLeaderboardScore(_mission.config.planetId);
    }
    
    // Show reward popup
    showRewardPopup(
        _mission.config.type === 'review' ? 'Signal Stabilized!' : 'Sector Stabilized!',
        { xp, crystals: crystals + perfectBonus }
    );
    
    // Return to planet map
    document.getElementById('btn-collect-rewards')?.addEventListener('click', () => {
        showScreen('planet-map-screen');
        updateHUD();
    }, { once: true });
}

// ─── Phase 8 Data Loader ────────────────────────────────

/**
 * Load real mission content from Phase 8 structured output.
 * Tries Firestore first, then local files for dev mode.
 * 
 * Config provides: { planetId, sectorIdx, tileIdx, tileId }
 * Maps to: {subject}/{sectionId}.json → levels[] → interleaved segments
 */
async function _loadMissionSegments(config) {
    const subject = _subjectForPlanet(config.planetId);
    if (!subject) return null;
    
    // Build section file name from tile info
    // tileId format: "{planetId}_s{N}_t{M}" → maps to chapter N, section M
    const match = config.tileId?.match(/_s(\d+)_t(\d+)$/);
    if (!match) return null;
    
    const chapter = parseInt(match[1]);
    const sectionNum = parseInt(match[2]);
    const sectionId = `${chapter}.${sectionNum}`;
    
    let data = null;
    
    // Try Firestore first
    if (typeof db !== 'undefined' && db) {
        try {
            const doc = await db.collection('concepts').doc(subject)
                .collection('sections').doc(sectionId).get();
            if (doc.exists) data = doc.data();
        } catch (e) {
            console.warn('Firestore load failed for mission:', e);
        }
    }
    
    // Try local Phase 8 files (dev mode)
    if (!data) {
        try {
            // Try fetching structured content files
            const basePaths = ['../phases/phase8/output/structured', 'phases/phase8/output/structured'];
            for (const base of basePaths) {
                try {
                    const dirRes = await fetch(`${base}/${subject}/`);
                    if (!dirRes.ok) continue;
                    
                    // Try to find matching section file by sectionId prefix
                    const files = await dirRes.text();
                    const fileMatch = files.match(new RegExp(`${sectionId}[^"]*\\.json`, 'i'));
                    if (fileMatch) {
                        const fileRes = await fetch(`${base}/${subject}/${fileMatch[0]}`);
                        if (fileRes.ok) {
                            data = await fileRes.json();
                            break;
                        }
                    }
                } catch { continue; }
            }
        } catch (e) {
            console.warn('Local Phase 8 load failed:', e);
        }
    }
    
    if (!data || !data.levels) return null;
    
    // Convert Phase 8 structure to mission segments
    return _convertPhase8ToSegments(data, subject);
}

/**
 * Convert Phase 8 structured content into a flat array of mission segments.
 * Interleaves: briefing → learn → question → learn → question → ...
 */
function _convertPhase8ToSegments(data, subject) {
    const segments = [];
    const specialist = getSpecialistForSubject(subject);
    const specialistName = specialist ? specialist.display_name : 'Specialist';
    
    // Mission briefing
    if (data.mission_briefing) {
        segments.push({
            type: 'learn',
            speaker_id: 'lyra',
            narrator_text: data.mission_briefing.lyra_intro || data.mission_briefing,
        });
    }
    
    // Interleave learn segments and questions from all levels
    for (const level of data.levels) {
        // Learn segments
        const learns = level.learn_segments || [];
        const checks = level.check_questions || [];
        const apply = level.apply_question;
        
        // Interleave: 2 learns, then 1 question, repeat
        let learnIdx = 0;
        let questionIdx = 0;
        
        while (learnIdx < learns.length || questionIdx < checks.length) {
            // Add 2 learn segments
            for (let i = 0; i < 2 && learnIdx < learns.length; i++, learnIdx++) {
                const seg = learns[learnIdx];
                segments.push({
                    type: 'learn',
                    speaker_id: seg.speaker_id || 'specialist',
                    specialist_name: specialistName,
                    narrator_text: seg.narrator_text || '',
                    display_text: seg.display_text || seg.narrator_text || '',
                    key_term: seg.key_term || null,
                    mnemonic: seg.mnemonic || null,
                    figure_ref: seg.figure_ref || null,
                });
            }
            
            // Add 1 check question
            if (questionIdx < checks.length) {
                const q = checks[questionIdx++];
                segments.push({
                    type: 'question',
                    question_type: q.question_type || 'pick_one',
                    question_text: q.question_text || '',
                    options: q.options || [],
                    correct_index: q.correct_index,
                    correct_response: q.correct_response || 'Correct!',
                    wrong_response: q.wrong_response || 'Not quite.',
                    wrong_explanations: q.wrong_explanations || {},
                });
            }
        }
        
        // Apply question at end of level
        if (apply) {
            segments.push({
                type: 'question',
                question_type: apply.question_type || 'pick_one',
                question_text: apply.question_text || '',
                options: apply.options || [],
                correct_index: apply.correct_index,
                correct_response: apply.correct_response || 'Excellent!',
                wrong_response: apply.wrong_response || 'Review and try again.',
                wrong_explanations: apply.wrong_explanations || {},
            });
        }
        
        // Pro tips
        const tips = level.pro_tips || [];
        for (const tip of tips) {
            segments.push({
                type: 'learn',
                speaker_id: 'lyra',
                narrator_text: `Pro tip: ${tip.text || tip}`,
                is_pro_tip: true,
            });
        }
    }
    
    return segments;
}

// ─── Auto-Generate Field Notes ──────────────────────────

function _generateFieldNote() {
    // Scan mission segments for key terms / learn content
    for (const seg of _mission.segments) {
        if (seg.type === 'learn' && seg.key_term) {
            const conceptId = `${_mission.config.planetId}_${seg.key_term.replace(/\s+/g, '_').toLowerCase()}`;
            addFieldNote(conceptId, {
                conceptName: seg.key_term,
                subject: _subjectForPlanet(_mission.config.planetId),
                chapter: _mission.config.sectorIdx + 1,
                summary: seg.narrator_text?.substring(0, 200) || '',
                mnemonics: seg.mnemonic || null,
                text: seg.display_text || seg.narrator_text || '',
            });
        }
    }
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
