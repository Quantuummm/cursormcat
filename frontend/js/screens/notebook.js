/**
 * MCAT Mastery — Notebook Screen (Neural Archive)
 * 
 * Tabs: Field Notes | Glossary | Equations | Figures
 * Loads data from player state + game-data, filterable by planet/subject.
 */

function initNotebook(tab = 'notes') {
    _wireNotebookTabs(tab);
    _loadNotebookTab(tab);
}

function _wireNotebookTabs(activeTab) {
    document.querySelectorAll('.notebook-tabs .tab').forEach(tabEl => {
        tabEl.classList.toggle('active', tabEl.dataset.tab === activeTab);
        
        // Replace onclick to use our renderer
        tabEl.onclick = () => {
            document.querySelectorAll('.notebook-tabs .tab').forEach(t => t.classList.remove('active'));
            tabEl.classList.add('active');
            _loadNotebookTab(tabEl.dataset.tab);
        };
    });
}

function _loadNotebookTab(tab) {
    const content = document.getElementById('notebook-content');
    if (!content) return;
    
    switch (tab) {
        case 'notes':    _renderFieldNotes(content); break;
        case 'glossary': _renderGlossary(content);   break;
        case 'equations':_renderEquations(content);   break;
        case 'figures':  _renderFigures(content);     break;
    }
}

// ─── Field Notes Tab ────────────────────────────────────────

function _renderFieldNotes(container) {
    const state = getPlayerState();
    const notes = state.fieldNotes || {};
    const noteKeys = Object.keys(notes);
    
    if (noteKeys.length === 0) {
        container.innerHTML = `
            <div class="notebook-empty">
                <span class="empty-icon">📝</span>
                <h3>No Field Notes Yet</h3>
                <p>Complete missions to auto-generate notes on key concepts. 
                   You can also add your own notes during missions!</p>
            </div>
        `;
        return;
    }
    
    // Group by subject
    const grouped = {};
    noteKeys.forEach(key => {
        const note = notes[key];
        const subj = note.subject || 'general';
        if (!grouped[subj]) grouped[subj] = [];
        grouped[subj].push({ id: key, ...note });
    });
    
    let html = `
        <div class="notebook-search">
            <input type="text" id="note-search" placeholder="🔍 Search notes..." class="nb-search">
        </div>
    `;
    
    for (const [subject, subjectNotes] of Object.entries(grouped)) {
        html += `
            <div class="nb-section" data-subject="${subject}">
                <h3 class="nb-section-title">${_subjectDisplayName(subject)}</h3>
                ${subjectNotes.map(n => `
                    <div class="nb-card" data-id="${n.id}">
                        <div class="nb-card-header">
                            <span class="nb-concept">${n.conceptName || n.id}</span>
                            <span class="nb-chapter">Ch${n.chapter || '?'}</span>
                        </div>
                        <p class="nb-card-body">${n.summary || n.text || ''}</p>
                        ${n.mnemonics ? `<div class="nb-mnemonic">💡 ${n.mnemonics}</div>` : ''}
                        <div class="nb-card-footer">
                            <span class="nb-date">${_timeAgo(n.addedAt)}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    container.innerHTML = html;
    
    // Wire search
    document.getElementById('note-search')?.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll('.nb-card').forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(q) ? '' : 'none';
        });
    });
}

// ─── Glossary Tab ───────────────────────────────────────────

function _renderGlossary(container) {
    // Try to load glossary from game data
    let glossaryData = {};
    
    try {
        if (typeof getGlossary === 'function') {
            glossaryData = getGlossary() || {};
        }
    } catch (e) {
        // Fall back to demo
    }
    
    const entries = Object.entries(glossaryData);
    
    if (entries.length === 0) {
        container.innerHTML = `
            <div class="notebook-empty">
                <span class="empty-icon">📖</span>
                <h3>Glossary Loading...</h3>
                <p>The glossary will populate as you explore planets and complete missions.
                   Each planet has its own subject-specific terminology.</p>
            </div>
        `;
        return;
    }
    
    // Sort alphabetically
    entries.sort((a, b) => a[0].localeCompare(b[0]));
    
    // Group by first letter
    const grouped = {};
    entries.forEach(([term, def]) => {
        const letter = term[0].toUpperCase();
        if (!grouped[letter]) grouped[letter] = [];
        grouped[letter].push({ term, definition: typeof def === 'string' ? def : def.definition || '' });
    });
    
    let html = `
        <div class="notebook-search">
            <input type="text" id="glossary-search" placeholder="🔍 Search terms..." class="nb-search">
        </div>
        <div class="glossary-alpha">
            ${Object.keys(grouped).map(l => `<a href="#gl-${l}" class="alpha-link">${l}</a>`).join('')}
        </div>
    `;
    
    for (const [letter, terms] of Object.entries(grouped)) {
        html += `
            <div class="gl-section" id="gl-${letter}">
                <h3 class="gl-letter">${letter}</h3>
                ${terms.map(t => `
                    <div class="gl-entry">
                        <span class="gl-term">${t.term}</span>
                        <span class="gl-def">${t.definition}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    container.innerHTML = html;
    
    // Wire search
    document.getElementById('glossary-search')?.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll('.gl-entry').forEach(entry => {
            const text = entry.textContent.toLowerCase();
            entry.style.display = text.includes(q) ? '' : 'none';
        });
    });
}

// ─── Equations Tab ──────────────────────────────────────────

function _renderEquations(container) {
    // Pre-defined key MCAT equations organized by subject
    const equationSets = [
        {
            subject: 'physics',
            title: '⚡ Physics Formulas',
            equations: [
                { name: 'Kinematic Equation', formula: 'v = v₀ + at', notes: 'Constant acceleration' },
                { name: 'Newton\'s 2nd Law', formula: 'F = ma', notes: 'Net force' },
                { name: 'Kinetic Energy', formula: 'KE = ½mv²', notes: '' },
                { name: 'Potential Energy', formula: 'PE = mgh', notes: 'Near earth surface' },
                { name: 'Work', formula: 'W = Fd cos θ', notes: '' },
                { name: 'Power', formula: 'P = W/t = Fv', notes: '' },
                { name: 'Coulomb\'s Law', formula: 'F = kq₁q₂/r²', notes: 'k = 8.99×10⁹ N⋅m²/C²' },
                { name: 'Ohm\'s Law', formula: 'V = IR', notes: '' },
                { name: 'Pressure', formula: 'P = F/A', notes: '' },
                { name: 'Ideal Gas Law', formula: 'PV = nRT', notes: 'R = 8.314 J/(mol⋅K)' },
                { name: 'Snell\'s Law', formula: 'n₁ sin θ₁ = n₂ sin θ₂', notes: '' },
                { name: 'Doppler Effect', formula: 'f\' = f(v ± v₀)/(v ∓ vₛ)', notes: '' },
            ],
        },
        {
            subject: 'gen_chem',
            title: '⚗️ General Chemistry',
            equations: [
                { name: 'pH', formula: 'pH = -log[H⁺]', notes: '' },
                { name: 'Henderson-Hasselbalch', formula: 'pH = pKa + log([A⁻]/[HA])', notes: '' },
                { name: 'Gibbs Free Energy', formula: 'ΔG = ΔH - TΔS', notes: '' },
                { name: 'Nernst Equation', formula: 'E = E° - (RT/nF)lnQ', notes: '' },
                { name: 'Rate Law', formula: 'Rate = k[A]ᵐ[B]ⁿ', notes: '' },
                { name: 'Arrhenius Equation', formula: 'k = Ae^(-Eₐ/RT)', notes: '' },
                { name: 'Molarity', formula: 'M = mol/L', notes: '' },
                { name: 'Dilution', formula: 'M₁V₁ = M₂V₂', notes: '' },
            ],
        },
        {
            subject: 'biochemistry',
            title: '🧬 Biochemistry',
            equations: [
                { name: 'Michaelis-Menten', formula: 'v = Vmax[S]/(Km + [S])', notes: '' },
                { name: 'Lineweaver-Burk', formula: '1/v = (Km/Vmax)(1/[S]) + 1/Vmax', notes: 'Double reciprocal' },
                { name: 'ΔG of ATP Hydrolysis', formula: 'ΔG°\' = -30.5 kJ/mol', notes: 'Standard conditions' },
                { name: 'ATP Yield (Glucose)', formula: 'C₆H₁₂O₆ → ~30-32 ATP', notes: 'Aerobic respiration' },
            ],
        },
    ];
    
    let html = `
        <div class="notebook-search">
            <input type="text" id="eq-search" placeholder="🔍 Search equations..." class="nb-search">
        </div>
    `;
    
    equationSets.forEach(set => {
        html += `
            <div class="eq-section" data-subject="${set.subject}">
                <h3 class="eq-title">${set.title}</h3>
                <div class="eq-grid">
                    ${set.equations.map(eq => `
                        <div class="eq-card">
                            <span class="eq-name">${eq.name}</span>
                            <span class="eq-formula">${eq.formula}</span>
                            ${eq.notes ? `<span class="eq-notes">${eq.notes}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Wire search
    document.getElementById('eq-search')?.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll('.eq-card').forEach(card => {
            card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
}

// ─── Figures Tab ────────────────────────────────────────────

function _renderFigures(container) {
    container.innerHTML = `
        <div class="notebook-empty">
            <span class="empty-icon">🖼️</span>
            <h3>Figure Gallery</h3>
            <p>Key diagrams, charts, and illustrations from your studies will appear here.
               Complete missions to unlock figures for each chapter.</p>
        </div>
    `;
}

// ─── Helpers ────────────────────────────────────────────────

function _subjectDisplayName(subj) {
    const map = {
        biology: '🌿 Biology', biochemistry: '🧬 Biochemistry',
        gen_chem: '⚗️ General Chemistry', org_chem: '🔬 Organic Chemistry',
        physics: '⚡ Physics', psych_soc: '🧠 Psych/Soc',
        cars: '📖 CARS', general: '📌 General',
    };
    return map[subj] || subj;
}

function _timeAgo(timestamp) {
    if (!timestamp) return '';
    const diff = Date.now() - timestamp;
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
}
