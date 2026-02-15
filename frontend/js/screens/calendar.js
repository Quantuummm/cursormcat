/**
 * MCAT Mastery — Study Calendar / Pacing System
 * 
 * Supports 30, 45, 60, 75, 90, 105, 120 day study plans.
 * Player inputs their test date and the system auto-generates a daily plan
 * distributing all 7 subjects evenly with review spirals built in.
 */

const Calendar = {
    plan: null,           // { testDate, startDate, daysTotal, dailyPlan: [...] }
    selectedDuration: 90, // default
};

const PLAN_DURATIONS = [30, 45, 60, 75, 90, 105, 120];

const SUBJECTS_ORDER = [
    { id: 'biology',     planet: 'verdania',  name: 'Biology',       chapters: 12, weight: 1.0 },
    { id: 'biochemistry',planet: 'glycera',   name: 'Biochemistry',  chapters: 12, weight: 1.0 },
    { id: 'gen_chem',    planet: 'luminara',  name: 'Gen Chem',      chapters: 12, weight: 0.9 },
    { id: 'org_chem',    planet: 'synthara',  name: 'Org Chem',      chapters: 12, weight: 0.8 },
    { id: 'physics',     planet: 'aethon',    name: 'Physics',       chapters: 12, weight: 0.8 },
    { id: 'psych_soc',   planet: 'miravel',   name: 'Psych/Soc',     chapters: 12, weight: 1.0 },
    { id: 'cars',        planet: 'lexara',    name: 'CARS',          chapters: 12, weight: 0.7 },
];

function initCalendar() {
    const body = document.getElementById('calendar-body');
    if (!body) return;
    
    // Load saved plan
    const saved = _loadPlan();
    
    if (saved) {
        Calendar.plan = saved;
        _renderActivePlan(body);
    } else {
        _renderPlanSetup(body);
    }
}

function _renderPlanSetup(body) {
    body.innerHTML = `
        <div class="cal-setup">
            <h3>📅 Create Your Study Plan</h3>
            <p class="cal-subtitle">Choose your MCAT test date and study duration. 
               LYRA will build a personalized daily plan covering all 7 subjects.</p>
            
            <div class="cal-field">
                <label>MCAT Test Date</label>
                <input type="date" id="cal-test-date" class="cal-input" 
                       min="${_formatDate(new Date())}" 
                       value="${_formatDate(_addDays(new Date(), 90))}">
            </div>
            
            <div class="cal-field">
                <label>Study Duration</label>
                <div class="duration-grid" id="duration-grid">
                    ${PLAN_DURATIONS.map(d => `
                        <button class="duration-btn ${d === Calendar.selectedDuration ? 'selected' : ''}" 
                                data-days="${d}">
                            ${d} days
                            <span class="duration-pace">${_describePace(d)}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
            
            <div class="cal-preview" id="cal-preview">
                ${_renderPlanPreview(Calendar.selectedDuration)}
            </div>
            
            <button class="btn btn-primary btn-large" id="btn-create-plan">
                🚀 Launch Study Plan
            </button>
        </div>
    `;
    
    // Wire duration buttons
    document.querySelectorAll('.duration-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.duration-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            Calendar.selectedDuration = parseInt(btn.dataset.days);
            document.getElementById('cal-preview').innerHTML = _renderPlanPreview(Calendar.selectedDuration);
        });
    });
    
    // Wire create button
    document.getElementById('btn-create-plan')?.addEventListener('click', () => {
        const testDateStr = document.getElementById('cal-test-date').value;
        if (!testDateStr) {
            showToast('Please select your MCAT test date');
            return;
        }
        
        const testDate = new Date(testDateStr);
        const plan = _generatePlan(testDate, Calendar.selectedDuration);
        Calendar.plan = plan;
        _savePlan(plan);
        _renderActivePlan(body);
        showToast(`${Calendar.selectedDuration}-day plan created! Let's go!`);
    });
}

function _describePace(days) {
    if (days <= 30)  return 'Intense';
    if (days <= 45)  return 'Aggressive';
    if (days <= 60)  return 'Focused';
    if (days <= 75)  return 'Balanced';
    if (days <= 90)  return 'Standard';
    if (days <= 105) return 'Relaxed';
    return 'Extended';
}

function _renderPlanPreview(days) {
    const totalSections = SUBJECTS_ORDER.reduce((sum, s) => sum + s.chapters * 3, 0); // ~3 sections per chapter
    const sectionsPerDay = Math.ceil(totalSections / (days * 0.7)); // 70% new content, 30% review
    const reviewDays = Math.floor(days * 0.3);
    
    return `
        <div class="preview-stats">
            <div class="preview-stat">
                <span class="pv-num">${sectionsPerDay}</span>
                <span class="pv-label">Sections/Day</span>
            </div>
            <div class="preview-stat">
                <span class="pv-num">${reviewDays}</span>
                <span class="pv-label">Review Days</span>
            </div>
            <div class="preview-stat">
                <span class="pv-num">~${Math.round(sectionsPerDay * 15)}</span>
                <span class="pv-label">Min/Day</span>
            </div>
        </div>
    `;
}

function _generatePlan(testDate, durationDays) {
    const startDate = _addDays(testDate, -durationDays);
    const dailyPlan = [];
    
    // Build task queue: all chapters × all subjects, weighted
    const tasks = [];
    for (const subj of SUBJECTS_ORDER) {
        for (let ch = 1; ch <= subj.chapters; ch++) {
            // Each chapter has: learn, practice, review
            tasks.push({ 
                subject: subj.id, 
                planet: subj.planet,
                chapter: ch, 
                type: 'learn', 
                label: `${subj.name} Ch${ch} — Learn`,
                weight: subj.weight,
                done: false,
            });
            tasks.push({ 
                subject: subj.id, 
                planet: subj.planet,
                chapter: ch, 
                type: 'practice', 
                label: `${subj.name} Ch${ch} — Practice`,
                weight: subj.weight,
                done: false,
            });
        }
    }
    
    // Distribute tasks across days
    // First 70% of days: new content
    // Last 30%: review & full practice tests
    const contentDays = Math.floor(durationDays * 0.7);
    const reviewDays = durationDays - contentDays;
    const tasksPerDay = Math.ceil(tasks.length / contentDays);
    
    let taskIdx = 0;
    
    // Content days
    for (let d = 0; d < contentDays; d++) {
        const date = _addDays(startDate, d);
        const dayTasks = [];
        
        for (let t = 0; t < tasksPerDay && taskIdx < tasks.length; t++, taskIdx++) {
            dayTasks.push({ ...tasks[taskIdx] });
        }
        
        // Add a review item every 3rd day
        if (d > 0 && d % 3 === 0 && d >= 6) {
            const reviewChapter = Math.max(1, Math.floor(d / 3));
            const reviewSubj = SUBJECTS_ORDER[d % SUBJECTS_ORDER.length];
            dayTasks.push({
                subject: reviewSubj.id,
                planet: reviewSubj.planet,
                chapter: Math.min(reviewChapter, reviewSubj.chapters),
                type: 'review',
                label: `🔄 Review: ${reviewSubj.name} Ch${Math.min(reviewChapter, reviewSubj.chapters)}`,
                weight: 0.5,
                done: false,
            });
        }
        
        dailyPlan.push({
            date: _formatDate(date),
            dayNumber: d + 1,
            phase: 'content',
            tasks: dayTasks,
        });
    }
    
    // Review days
    for (let d = 0; d < reviewDays; d++) {
        const date = _addDays(startDate, contentDays + d);
        const subjects = [];
        
        // Distribute subjects across review days
        const subjIdx = d % SUBJECTS_ORDER.length;
        const subj = SUBJECTS_ORDER[subjIdx];
        
        const reviewTasks = [];
        // Review 3-4 chapters per day during review phase
        const chaptersToReview = Math.min(4, subj.chapters);
        for (let ch = 1; ch <= chaptersToReview; ch++) {
            const adjustedCh = ((d * chaptersToReview + ch - 1) % subj.chapters) + 1;
            reviewTasks.push({
                subject: subj.id,
                planet: subj.planet,
                chapter: adjustedCh,
                type: 'review',
                label: `🔄 Review: ${subj.name} Ch${adjustedCh}`,
                weight: 0.5,
                done: false,
            });
        }
        
        // Add a bridge mission on review days
        if (d % 2 === 0) {
            reviewTasks.push({
                subject: 'bridge',
                planet: null,
                chapter: null,
                type: 'bridge',
                label: '🌉 Bridge Mission',
                weight: 0.5,
                done: false,
            });
        }
        
        dailyPlan.push({
            date: _formatDate(date),
            dayNumber: contentDays + d + 1,
            phase: 'review',
            tasks: reviewTasks,
        });
    }
    
    return {
        testDate: _formatDate(testDate),
        startDate: _formatDate(startDate),
        daysTotal: durationDays,
        createdAt: new Date().toISOString(),
        dailyPlan,
    };
}

function _renderActivePlan(body) {
    const plan = Calendar.plan;
    if (!plan) return;
    
    const today = _formatDate(new Date());
    const todayEntry = plan.dailyPlan.find(d => d.date === today);
    const dayNum = todayEntry ? todayEntry.dayNumber : 0;
    const daysLeft = plan.daysTotal - dayNum;
    const completedTasks = plan.dailyPlan.reduce((sum, d) => sum + d.tasks.filter(t => t.done).length, 0);
    const totalTasks = plan.dailyPlan.reduce((sum, d) => sum + d.tasks.length, 0);
    const overallPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    
    body.innerHTML = `
        <div class="cal-header-stats">
            <div class="cal-stat">
                <span class="cal-stat-val">${daysLeft > 0 ? daysLeft : 0}</span>
                <span class="cal-stat-lbl">Days Left</span>
            </div>
            <div class="cal-stat">
                <span class="cal-stat-val">${overallPct}%</span>
                <span class="cal-stat-lbl">Complete</span>
            </div>
            <div class="cal-stat">
                <span class="cal-stat-val">Day ${dayNum || '-'}</span>
                <span class="cal-stat-lbl">of ${plan.daysTotal}</span>
            </div>
            <div class="cal-stat">
                <span class="cal-stat-val">📅 ${_formatDateShort(plan.testDate)}</span>
                <span class="cal-stat-lbl">Test Day</span>
            </div>
        </div>
        
        <div class="cal-progress-bar">
            <div class="cal-prog-fill" style="width: ${overallPct}%"></div>
        </div>
        
        ${todayEntry ? `
            <div class="cal-today">
                <h3>🎯 Today's Mission — Day ${todayEntry.dayNumber}</h3>
                <div class="cal-today-phase">${todayEntry.phase === 'review' ? '🔄 Review Phase' : '📚 Content Phase'}</div>
                <div class="today-tasks">
                    ${todayEntry.tasks.map((task, i) => `
                        <div class="today-task ${task.done ? 'done' : ''}" data-task-idx="${i}">
                            <span class="task-check">${task.done ? '✅' : '⬜'}</span>
                            <span class="task-label">${task.label}</span>
                            <button class="btn btn-sm btn-go" data-planet="${task.planet}" 
                                    data-chapter="${task.chapter}" ${task.done ? 'disabled' : ''}>
                                ${task.done ? 'Done' : 'Go →'}
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : `
            <div class="cal-today cal-rest">
                <h3>😌 No tasks today</h3>
                <p>Enjoy your rest day, Commander.</p>
            </div>
        `}
        
        <div class="cal-week-view" id="cal-week-view">
            <h3>📆 This Week</h3>
            <div class="week-grid">
                ${_renderWeekView(plan, today)}
            </div>
        </div>
        
        <div class="cal-actions">
            <button class="btn btn-secondary" id="btn-reset-plan">🔄 Reset Plan</button>
        </div>
    `;
    
    // Wire task buttons
    document.querySelectorAll('.btn-go').forEach(btn => {
        btn.addEventListener('click', () => {
            const planet = btn.dataset.planet;
            if (planet && planet !== 'null') {
                // Navigate to planet map
                openPlanetMap(planet);
            } else {
                showScreen('bridge-screen');
            }
        });
    });
    
    // Wire task checkboxes
    document.querySelectorAll('.today-task').forEach(el => {
        el.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-go')) return;
            const idx = parseInt(el.dataset.taskIdx);
            if (todayEntry && todayEntry.tasks[idx]) {
                todayEntry.tasks[idx].done = !todayEntry.tasks[idx].done;
                _savePlan(Calendar.plan);
                _renderActivePlan(body);
            }
        });
    });
    
    // Wire reset
    document.getElementById('btn-reset-plan')?.addEventListener('click', () => {
        if (confirm('Reset your study plan? This cannot be undone.')) {
            Calendar.plan = null;
            _clearPlan();
            _renderPlanSetup(body);
            showToast('Study plan reset');
        }
    });
}

function _renderWeekView(plan, today) {
    const todayDate = new Date(today);
    const weekStart = new Date(todayDate);
    weekStart.setDate(todayDate.getDate() - todayDate.getDay()); // Sunday
    
    let html = '';
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    for (let i = 0; i < 7; i++) {
        const date = _addDays(weekStart, i);
        const dateStr = _formatDate(date);
        const entry = plan.dailyPlan.find(d => d.date === dateStr);
        const isToday = dateStr === today;
        const completed = entry ? entry.tasks.filter(t => t.done).length : 0;
        const total = entry ? entry.tasks.length : 0;
        const allDone = total > 0 && completed === total;
        
        html += `
            <div class="week-day ${isToday ? 'today' : ''} ${allDone ? 'completed' : ''}">
                <span class="wd-name">${dayNames[i]}</span>
                <span class="wd-date">${date.getDate()}</span>
                <span class="wd-status">${entry ? (allDone ? '✅' : `${completed}/${total}`) : '—'}</span>
            </div>
        `;
    }
    
    return html;
}

// ─── Helpers ────────────────────────────────────────────────

function _formatDate(date) {
    if (typeof date === 'string') return date;
    return date.toISOString().split('T')[0];
}

function _formatDateShort(dateStr) {
    const d = new Date(dateStr);
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${months[d.getMonth()]} ${d.getDate()}`;
}

function _addDays(date, days) {
    const d = new Date(typeof date === 'string' ? date : date.getTime());
    d.setDate(d.getDate() + days);
    return d;
}

function _savePlan(plan) {
    try {
        localStorage.setItem('mcat_study_plan', JSON.stringify(plan));
    } catch (e) {
        console.warn('Plan save failed:', e);
    }
}

function _loadPlan() {
    try {
        const saved = localStorage.getItem('mcat_study_plan');
        return saved ? JSON.parse(saved) : null;
    } catch (e) {
        return null;
    }
}

function _clearPlan() {
    localStorage.removeItem('mcat_study_plan');
}
