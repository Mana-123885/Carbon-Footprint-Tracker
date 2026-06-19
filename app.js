/* ═══════════════════════════════════════════════════
   EcoTrack — Main Application Logic
   ═══════════════════════════════════════════════════ */

const API = '';  // same origin
let token = localStorage.getItem('eco_token');
let currentUser = null;
let categories = {};
let selectedCategory = 'transport';
let selectedActivityType = null;
let weeklyChart = null, categoryChart = null, scoreHistoryChart = null;

// ═══ API Helper ═══
async function api(method, path, data = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    try {
        const res = await axios({ method, url: `${API}${path}`, data, headers });
        return res.data;
    } catch (err) {
        const msg = err.response?.data?.detail || err.message;
        throw new Error(msg);
    }
}

// ═══ Init ═══
document.addEventListener('DOMContentLoaded', async () => {
    applyTheme();
    if (token) {
        try {
            currentUser = await api('GET', '/api/me');
            showApp();
        } catch { logout(); }
    }
});

// ═══ Auth ═══
function showAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.auth-tab[onclick*="${tab}"]`).classList.add('active');
    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
    document.getElementById('auth-error').classList.add('hidden');
}

async function handleLogin(e) {
    e.preventDefault();
    try {
        const data = await api('POST', '/api/login', {
            email: document.getElementById('login-email').value,
            password: document.getElementById('login-password').value,
        });
        token = data.access_token;
        localStorage.setItem('eco_token', token);
        currentUser = data.user;
        showApp();
    } catch (err) { showAuthError(err.message); }
}

async function handleRegister(e) {
    e.preventDefault();
    try {
        const data = await api('POST', '/api/register', {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            password: document.getElementById('reg-password').value,
            full_name: document.getElementById('reg-fullname').value,
        });
        token = data.access_token;
        localStorage.setItem('eco_token', token);
        currentUser = data.user;
        showApp();
    } catch (err) { showAuthError(err.message); }
}

function showAuthError(msg) {
    const el = document.getElementById('auth-error');
    el.textContent = msg;
    el.classList.remove('hidden');
}

function handleLogout() { logout(); }
function logout() {
    token = null; currentUser = null;
    localStorage.removeItem('eco_token');
    document.getElementById('app').classList.add('hidden');
    document.getElementById('mobile-nav').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
}

// ═══ App Shell ═══
async function showApp() {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    document.getElementById('mobile-nav').classList.remove('hidden');
    applyTheme(currentUser?.theme);
    try { categories = await api('GET', '/api/categories'); } catch {}
    loadDashboard();
}

// ═══ Navigation ═══
function navigateTo(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById(`page-${page}`).classList.remove('hidden');
    document.querySelectorAll('.nav-item,.mob-nav-item').forEach(n => {
        n.classList.toggle('active', n.dataset.page === page);
    });
    closeSidebar();
    // Load page data
    if (page === 'dashboard') loadDashboard();
    else if (page === 'add-activity') loadActivityPage();
    else if (page === 'insights') loadInsights();
    else if (page === 'goals') loadGoals();
    else if (page === 'challenges') loadChallenges();
    else if (page === 'education') loadEducation();
    else if (page === 'settings') loadSettings();
}

function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }
function closeSidebar() { document.getElementById('sidebar').classList.remove('open'); }

// ═══ Theme ═══
function applyTheme(theme) {
    const t = theme || localStorage.getItem('eco_theme') || 'light';
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem('eco_theme', t);
    const cb = document.getElementById('theme-toggle-cb');
    if (cb) cb.checked = t === 'dark';
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    if (token) api('PUT', '/api/settings', { theme: next }).catch(() => {});
}

// ═══ Dashboard ═══
async function loadDashboard() {
    try {
        const d = await api('GET', '/api/get-dashboard');
        // Greeting
        const h = new Date().getHours();
        const greet = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
        document.getElementById('greeting').textContent = `${greet}! 🌱`;
        document.getElementById('user-greeting-name').textContent = `Welcome back, ${d.user.full_name || d.user.username}`;

        // Eco Score Ring
        updateScoreRing(d.eco_score);
        document.getElementById('eco-level-badge').textContent = `${d.level.icon} ${d.level.name}`;

        // Stats
        document.getElementById('today-carbon').textContent = d.today_carbon_kg.toFixed(1);
        document.getElementById('week-carbon').textContent = d.week_carbon_kg.toFixed(1);
        document.getElementById('month-carbon').textContent = d.month_carbon_kg.toFixed(1);
        document.getElementById('budget-percent').textContent = `${d.budget_percent}%`;

        // Budget bar
        const bp = Math.min(d.budget_percent, 100);
        const bar = document.getElementById('budget-progress-bar');
        bar.style.width = `${bp}%`;
        bar.style.background = bp > 80 ? 'var(--danger)' : bp > 50 ? 'var(--accent2)' : '';
        document.getElementById('budget-used').textContent = d.month_carbon_kg.toFixed(1);
        document.getElementById('budget-total').textContent = d.monthly_budget_kg;

        // Charts
        renderWeeklyChart(d.daily_totals);
        renderCategoryChart(d.category_breakdown);

        // Recent activities
        const container = document.getElementById('recent-activities');
        if (d.recent_activities.length === 0) {
            container.innerHTML = '<p class="empty-state">No activities yet. Start tracking! 🌱</p>';
        } else {
            container.innerHTML = d.recent_activities.map(a => activityItemHTML(a)).join('');
        }
    } catch (err) { console.error('Dashboard error:', err); }
}

function updateScoreRing(score) {
    document.getElementById('eco-score-value').textContent = score;
    const pct = score / 1000;
    const circumference = 2 * Math.PI * 85;
    const offset = circumference * (1 - pct);
    const fill = document.getElementById('score-ring-fill');
    fill.style.stroke = `hsl(${120 * pct}, 65%, 50%)`;
    fill.style.strokeDasharray = circumference;
    fill.style.strokeDashoffset = offset;
}

function activityItemHTML(a) {
    const icons = {transport:'🚗',food:'🍽️',energy:'⚡',waste:'♻️'};
    const icon = icons[a.category] || '📝';
    const date = new Date(a.date).toLocaleDateString('en-US', {month:'short',day:'numeric'});
    const sign = a.carbon_kg >= 0 ? '+' : '';
    return `<div class="activity-item">
        <div class="act-icon">${icon}</div>
        <div class="act-info">
            <div class="act-name">${a.description || a.activity_type}</div>
            <div class="act-detail">${a.quantity} ${a.unit} · ${date}</div>
        </div>
        <div class="act-carbon">${sign}${a.carbon_kg.toFixed(2)} kg</div>
    </div>`;
}

// ═══ Charts ═══
function renderWeeklyChart(dailyTotals) {
    const ctx = document.getElementById('weekly-chart');
    if (!ctx) return;
    const labels = Object.keys(dailyTotals).map(d => {
        const dt = new Date(d); return dt.toLocaleDateString('en-US', {weekday:'short'});
    });
    const data = Object.values(dailyTotals);
    if (weeklyChart) weeklyChart.destroy();
    weeklyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'kg CO₂', data, borderRadius: 8,
                backgroundColor: 'rgba(76,175,80,0.5)',
                borderColor: 'rgba(76,175,80,1)', borderWidth: 1.5,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderCategoryChart(breakdown) {
    const ctx = document.getElementById('category-chart');
    if (!ctx) return;
    const labels = Object.keys(breakdown).map(c => c.charAt(0).toUpperCase() + c.slice(1));
    const data = Object.values(breakdown);
    const colors = ['#66BB6A','#42A5F5','#FFA726','#AB47BC','#EF5350'];
    if (categoryChart) categoryChart.destroy();
    if (data.length === 0) {
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: { labels: ['No data'], datasets: [{ data: [1], backgroundColor: ['#E0E0E0'] }] },
            options: { responsive: true, maintainAspectRatio: false }
        });
        return;
    }
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels, datasets: [{
                data, backgroundColor: colors.slice(0, data.length),
                borderWidth: 2, borderColor: 'var(--card)',
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { position: 'bottom', labels: { padding: 12, font: { size: 11 } } } }
        }
    });
}

// ═══ Add Activity ═══
function loadActivityPage() {
    selectedCategory = 'transport';
    selectedActivityType = null;
    document.querySelectorAll('.cat-tab').forEach(t => t.classList.toggle('active', t.dataset.cat === 'transport'));
    renderActivityGrid('transport');
    document.getElementById('add-form').classList.add('hidden');
    document.getElementById('activity-result').classList.add('hidden');
}

function selectCategory(cat) {
    selectedCategory = cat;
    selectedActivityType = null;
    document.querySelectorAll('.cat-tab').forEach(t => t.classList.toggle('active', t.dataset.cat === cat));
    renderActivityGrid(cat);
    document.getElementById('add-form').classList.add('hidden');
}

function renderActivityGrid(cat) {
    const grid = document.getElementById('activity-grid');
    const acts = categories[cat] || {};
    grid.innerHTML = Object.entries(acts).map(([key, a]) => `
        <button class="activity-btn" onclick="selectActivityType('${cat}','${key}')">
            <span class="act-btn-icon">${a.icon}</span>
            <span class="act-btn-label">${a.label}</span>
            <span class="act-btn-factor">${a.factor} kg/${a.unit}</span>
        </button>
    `).join('');
}

function selectActivityType(cat, type) {
    selectedCategory = cat;
    selectedActivityType = type;
    document.querySelectorAll('.activity-btn').forEach(b => b.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    const info = categories[cat][type];
    document.getElementById('add-form').classList.remove('hidden');
    document.getElementById('activity-result').classList.add('hidden');
    document.getElementById('add-form-title').textContent = `${info.icon} ${info.label}`;
    document.getElementById('add-form-unit').textContent = info.unit;
    document.getElementById('add-quantity').value = '';
    document.getElementById('add-description').value = '';
    document.getElementById('carbon-preview').classList.add('hidden');
    // Live preview
    document.getElementById('add-quantity').oninput = function() {
        const qty = parseFloat(this.value);
        if (qty > 0) {
            const co2 = (qty * info.factor).toFixed(2);
            document.getElementById('preview-value').textContent = `${co2} kg CO₂`;
            document.getElementById('carbon-preview').classList.remove('hidden');
        } else {
            document.getElementById('carbon-preview').classList.add('hidden');
        }
    };
}

async function submitActivity() {
    if (!selectedActivityType) return;
    const qty = parseFloat(document.getElementById('add-quantity').value);
    if (!qty || qty <= 0) return showToast('Enter a valid quantity');
    try {
        const result = await api('POST', '/api/add-activity', {
            category: selectedCategory,
            activity_type: selectedActivityType,
            quantity: qty,
            description: document.getElementById('add-description').value,
        });
        document.getElementById('add-form').classList.add('hidden');
        const res = document.getElementById('activity-result');
        res.classList.remove('hidden');
        const cr = result.carbon_result;
        const sc = result.score_change;
        const scoreClass = sc >= 0 ? 'color:var(--primary)' : 'color:var(--danger)';
        document.getElementById('result-details').innerHTML = `
            <p style="font-size:1.2rem;font-weight:700;margin:0.5rem 0">${cr.icon} ${cr.label}</p>
            <p>${cr.quantity} ${cr.unit} = <strong>${cr.carbon_kg.toFixed(2)} kg CO₂</strong></p>
            <p style="${scoreClass};font-weight:600">Eco Score: ${sc >= 0 ? '+' : ''}${sc} → ${result.eco_score}</p>
        `;
        // Alternatives
        const alts = result.alternatives || [];
        if (alts.length > 0) {
            document.getElementById('result-alternatives').innerHTML = `
                <h4 style="margin-top:1rem;margin-bottom:0.5rem">🌿 Greener Alternatives:</h4>
                ${alts.slice(0, 3).map(a => `
                    <div class="alt-card">
                        <span>${a.icon}</span>
                        <span><strong>${a.label}</strong></span>
                        <span style="color:var(--primary)">-${a.savings_percent}%</span>
                    </div>
                `).join('')}
            `;
        } else {
            document.getElementById('result-alternatives').innerHTML = '';
        }
        showToast('Activity logged! 🌱');
    } catch (err) { showToast(err.message); }
}

function resetAddForm() {
    document.getElementById('activity-result').classList.add('hidden');
    selectedActivityType = null;
    document.querySelectorAll('.activity-btn').forEach(b => b.classList.remove('selected'));
}

// ═══ Insights ═══
async function loadInsights() {
    try {
        const d = await api('GET', '/api/get-insights');
        document.getElementById('insights-summary').innerHTML = `
            <h3>📊 Your Impact</h3>
            <p style="font-size:1.1rem;margin-top:0.5rem">${d.summary}</p>
            ${d.total_carbon_kg !== undefined ? `<p style="margin-top:0.5rem;opacity:0.9">Total this month: <strong>${d.total_carbon_kg} kg CO₂</strong></p>` : ''}
        `;
        const tipsEl = document.getElementById('insights-tips');
        tipsEl.innerHTML = (d.tips || []).map(t => `<div class="tip-item">${t}</div>`).join('');
        // Score history chart
        if (d.score_history && d.score_history.length > 0) {
            const hist = d.score_history.slice().reverse();
            const labels = hist.map(h => new Date(h.date).toLocaleDateString('en-US', {month:'short',day:'numeric'}));
            const scores = hist.map(h => h.score);
            const ctx = document.getElementById('score-history-chart');
            if (scoreHistoryChart) scoreHistoryChart.destroy();
            scoreHistoryChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Eco Score', data: scores,
                        borderColor: '#66BB6A', backgroundColor: 'rgba(102,187,106,0.1)',
                        fill: true, tension: 0.4, pointRadius: 3,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { display: false, min: 0, max: 1000 },
                        x: { display: false }
                    },
                    layout: { padding: 0 }
                }
            });
        }
    } catch (err) { console.error('Insights error:', err); }
}

// ═══ AI Coach Chat ═══
async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    addChatBubble(msg, 'user');
    try {
        const data = await api('POST', '/api/ai-chat', { message: msg });
        addChatBubble(data.response, 'bot');
    } catch { addChatBubble('Sorry, something went wrong. Try again!', 'bot'); }
}

function quickChat(msg) {
    document.getElementById('chat-input').value = msg;
    sendChat();
}

function addChatBubble(text, role) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.innerHTML = `
        <div class="chat-avatar">${role === 'bot' ? '🤖' : '🧑'}</div>
        <div class="chat-bubble">${text}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ═══ Goals ═══
async function loadGoals() {
    try {
        const goals = await api('GET', '/api/goals');
        const container = document.getElementById('goals-list');
        if (goals.length === 0) {
            container.innerHTML = '<p class="empty-state">No goals yet. Set your first goal! 🎯</p>';
        } else {
            container.innerHTML = goals.map(g => `
                <div class="goal-card ${g.is_completed ? 'completed' : ''}">
                    <h4>${g.is_completed ? '✅' : '🎯'} ${g.title}</h4>
                    ${g.description ? `<p style="font-size:0.85rem;color:var(--text-secondary)">${g.description}</p>` : ''}
                    <div class="goal-meta">
                        <span>Target: ${g.target_reduction_kg} kg CO₂</span>
                        <span>Category: ${g.category}</span>
                    </div>
                    <div class="goal-actions">
                        ${!g.is_completed ? `<button class="btn btn-sm btn-primary" onclick="completeGoal(${g.id})">Complete</button>` : ''}
                        <button class="btn btn-sm btn-outline" onclick="deleteGoal(${g.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (err) { console.error('Goals error:', err); }
}

function showGoalForm() {
    document.getElementById('goal-form').classList.toggle('hidden');
}

async function createGoal() {
    const title = document.getElementById('goal-title').value.trim();
    const target = parseFloat(document.getElementById('goal-target').value);
    const category = document.getElementById('goal-category').value;
    if (!title || !target) return showToast('Fill in all fields');
    try {
        await api('POST', '/api/goals', { title, target_reduction_kg: target, category });
        document.getElementById('goal-form').classList.add('hidden');
        document.getElementById('goal-title').value = '';
        document.getElementById('goal-target').value = '';
        showToast('Goal created! 🎯');
        loadGoals();
    } catch (err) { showToast(err.message); }
}

async function completeGoal(id) {
    try {
        await api('PUT', `/api/goals/${id}`, { is_completed: true });
        showToast('Goal completed! 🎉');
        loadGoals();
    } catch (err) { showToast(err.message); }
}

async function deleteGoal(id) {
    try {
        await api('DELETE', `/api/goals/${id}`);
        loadGoals();
    } catch (err) { showToast(err.message); }
}

// ═══ Challenges ═══
async function loadChallenges() {
    try {
        const challenges = await api('GET', '/api/get-challenges');
        const container = document.getElementById('challenges-list');
        container.innerHTML = challenges.map(c => `
            <div class="challenge-card">
                <h4>${c.title}</h4>
                <p>${c.description}</p>
                <div class="challenge-meta">
                    <span>🏅 ${c.reward_points} pts</span>
                    <span>${c.type}</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width:${c.joined ? Math.min((c.progress / c.target_value) * 100, 100) : 0}%"></div>
                </div>
                ${!c.joined ? `<button class="btn btn-primary btn-sm btn-full" onclick="joinChallenge(${c.id})">Join Challenge</button>`
                    : c.is_completed ? `<button class="btn btn-outline btn-sm btn-full" disabled>✅ Completed</button>`
                    : `<button class="btn btn-outline btn-sm btn-full" disabled>Joined — In Progress</button>`}
            </div>
        `).join('');
    } catch (err) { console.error('Challenges error:', err); }
}

async function joinChallenge(id) {
    try {
        await api('POST', `/api/join-challenge/${id}`);
        showToast('Challenge joined! 🏆');
        loadChallenges();
    } catch (err) { showToast(err.message); }
}

// ═══ Education ═══
async function loadEducation() {
    try {
        const d = await api('GET', '/api/education');
        document.getElementById('education-cards').innerHTML = (d.cards || []).map(c => `
            <div class="edu-card">
                <div class="edu-icon">${c.icon}</div>
                <h4>${c.title}</h4>
                <p>${c.content}</p>
            </div>
        `).join('');
        document.getElementById('eco-facts').innerHTML = (d.facts || []).map(f =>
            `<div class="fact-item">💡 ${f}</div>`
        ).join('');
    } catch (err) { console.error('Education error:', err); }
}

// ═══ Settings ═══
function loadSettings() {
    if (!currentUser) return;
    document.getElementById('settings-budget').value = currentUser.monthly_budget_kg || 300;
    document.getElementById('settings-name').value = currentUser.full_name || '';
    const cb = document.getElementById('theme-toggle-cb');
    cb.checked = document.documentElement.getAttribute('data-theme') === 'dark';
}

async function saveBudget() {
    const budget = parseFloat(document.getElementById('settings-budget').value);
    if (!budget || budget < 50) return showToast('Min budget is 50 kg');
    try {
        currentUser = await api('PUT', '/api/settings', { monthly_budget_kg: budget });
        showToast('Budget updated! 🎯');
    } catch (err) { showToast(err.message); }
}

async function saveProfile() {
    const name = document.getElementById('settings-name').value.trim();
    if (!name) return showToast('Enter your name');
    try {
        currentUser = await api('PUT', '/api/settings', { full_name: name });
        showToast('Profile updated! ✅');
    } catch (err) { showToast(err.message); }
}

// ═══ Toast ═══
function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.remove('hidden');
    setTimeout(() => t.classList.add('hidden'), 3000);
}
