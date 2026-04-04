/**
 * ArogyaAI — Shared JS Utilities v3.0
 * frontend/js/app.js
 * SECURITY: All user-facing strings use textContent (never innerHTML) where possible.
 * AUTH: Refresh token flow silently renews access tokens on 401.
 */

// ── Config ────────────────────────────────────────────────
const CONFIG = {
  API_BASE:    '',                 // same-origin; set to https://api.arogyaai.in for cross-origin
  TOKEN_KEY:   'arogya_token',
  REFRESH_KEY: 'arogya_refresh',
  USER_KEY:    'arogya_user',
  LANG_KEY:    'arogya_lang',
  SESSION_KEY: 'arogya_session',
};

// ── XSS-Safe HTML Escape ──────────────────────────────────
function escapeHtml(str) {
  if (!str && str !== 0) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── API Client ────────────────────────────────────────────
const API = {
  _refreshPromise: null,

  /**
   * Make authenticated API requests.
   * • Always attaches JWT if available.
   * • On 401: attempts silent refresh, retries once, then logs out.
   * • Throws on error so callers can try/catch cleanly.
   */
  async request(method, path, body = null) {
    const makeReq = async (token) => {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const opts = { method, headers };
      if (body !== null) opts.body = JSON.stringify(body);
      return fetch(`${CONFIG.API_BASE}${path}`, opts);
    };

    try {
      let token = Auth.getToken();
      let res = await makeReq(token);

      // ── Silent token refresh on 401 ──────────────────────
      if (res.status === 401 && Auth.getRefreshToken()) {
        // Deduplicate concurrent refresh calls
        if (!this._refreshPromise) {
          this._refreshPromise = Auth.refreshAccessToken().finally(() => {
            this._refreshPromise = null;
          });
        }
        const newToken = await this._refreshPromise;
        if (newToken) {
          res = await makeReq(newToken);
        } else {
          Auth.logout();
          throw new Error('Session expired. Please log in again.');
        }
      } else if (res.status === 401) {
        Auth.logout();
        throw new Error('Session expired. Please log in again.');
      }

      let data;
      try { data = await res.json(); } catch { data = {}; }

      if (!res.ok) {
        const msg = data?.detail?.error || data?.detail || data?.message || 'Something went wrong.';
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
      return data;
    } catch (e) {
      if (e instanceof TypeError) {
        throw new Error('Network error. Check your connection.');
      }
      throw e;
    }
  },

  get:    (path)        => API.request('GET',    path),
  post:   (path, body)  => API.request('POST',   path, body),
  put:    (path, body)  => API.request('PUT',    path, body),
  delete: (path)        => API.request('DELETE', path),

  async uploadFile(path, formData) {
    const headers = {};
    const token = Auth.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    try {
      const res = await fetch(`${CONFIG.API_BASE}${path}`, { method: 'POST', headers, body: formData });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || 'Upload failed.');
      return data;
    } catch (e) {
      throw new Error(e.message || 'Network error.');
    }
  },
};

// ── Auth ──────────────────────────────────────────────────
const Auth = {
  getToken()        { return localStorage.getItem(CONFIG.TOKEN_KEY); },
  getRefreshToken() { return localStorage.getItem(CONFIG.REFRESH_KEY); },
  getUser() {
    try { return JSON.parse(localStorage.getItem(CONFIG.USER_KEY) || 'null'); }
    catch { return null; }
  },
  isLoggedIn() { return !!this.getToken(); },
  isPremium()  { return this.getUser()?.is_premium || false; },

  saveTokens(accessToken, refreshToken, user) {
    localStorage.setItem(CONFIG.TOKEN_KEY, accessToken);
    if (refreshToken) localStorage.setItem(CONFIG.REFRESH_KEY, refreshToken);
    if (user) localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
  },

  /** @deprecated Use saveTokens() */
  login(token, user) { this.saveTokens(token, null, user); },

  async refreshAccessToken() {
    const refreshTok = this.getRefreshToken();
    if (!refreshTok) return null;
    try {
      const resp = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTok }),
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      if (data.access_token) {
        localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
        return data.access_token;
      }
      return null;
    } catch {
      return null;
    }
  },

  logout() {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.REFRESH_KEY);
    localStorage.removeItem(CONFIG.USER_KEY);
    localStorage.removeItem('onboarding_done');
    window.location.href = '/login';
  },

  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.href = '/login';
      return false;
    }
    return true;
  },

  redirectIfLoggedIn() {
    if (this.isLoggedIn()) {
      window.location.href = '/dashboard';
    }
  },
};

// ── Toast Notifications ───────────────────────────────────
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 3500) {
    this.init();
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} animate-slide-down`;
    // SECURITY: Use textContent to prevent XSS from AI-generated or server content
    const iconEl = document.createElement('span');
    iconEl.textContent = icons[type] || 'ℹ️';
    const msgEl = document.createElement('span');
    msgEl.textContent = message;  // Safe: textContent, not innerHTML
    toast.appendChild(iconEl);
    toast.appendChild(msgEl);
    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-8px)';
      toast.style.transition = '300ms';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success: (msg) => Toast.show(msg, 'success'),
  error:   (msg) => Toast.show(msg, 'error', 5000),
  warning: (msg) => Toast.show(msg, 'warning'),
  info:    (msg) => Toast.show(msg, 'info'),
};

// ── Language ──────────────────────────────────────────────
const Lang = {
  get()    { return localStorage.getItem(CONFIG.LANG_KEY) || 'en'; },
  set(l)   { localStorage.setItem(CONFIG.LANG_KEY, l); },
  getName(code) {
    const names = { en: 'English', hi: 'हिंदी', gu: 'ગુજરાતી', mr: 'मराठी', ta: 'தமிழ்', te: 'తెలుగు', bn: 'বাংলা', kn: 'ಕನ್ನಡ' };
    return names[code] || code;
  },
};

// ── Markdown → HTML (minimal, safe) ──────────────────────
function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    // Escape HTML first
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // Bold: **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic: *text*
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Headers: ## heading
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    // HR
    .replace(/^---$/gm, '<hr>')
    // Unordered list
    .replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/(<li>.*<\/li>(\n|$))+/g, m => `<ul>${m}</ul>`)
    // Line breaks
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  // Wrap in paragraph if not already structured
  if (!html.includes('<h') && !html.includes('<ul') && !html.includes('<p>')) {
    html = `<p>${html}</p>`;
  }
  return html;
}

// ── Health Score Color ────────────────────────────────────
function scoreColor(score) {
  if (score >= 85) return '#22c55e';
  if (score >= 65) return '#84cc16';
  if (score >= 45) return '#f59e0b';
  return '#ef4444';
}

function scoreLabel(score) {
  if (score >= 85) return 'Excellent';
  if (score >= 65) return 'Good';
  if (score >= 45) return 'Fair';
  return 'Poor';
}

// ── SVG Score Ring ────────────────────────────────────────
function renderScoreRing(score, size = 120, label = 'Arogya Score') {
  const r = (size / 2) - 10;
  const circ = 2 * Math.PI * r;
  const fill = ((score || 0) / 100) * circ;
  const color = scoreColor(score || 0);
  return `
    <div class="score-ring" style="width:${size}px;height:${size}px">
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle class="score-ring-track" cx="${size/2}" cy="${size/2}" r="${r}"/>
        <circle class="score-ring-fill" cx="${size/2}" cy="${size/2}" r="${r}"
          stroke="${color}"
          stroke-dasharray="${circ}"
          stroke-dashoffset="${circ - fill}"/>
      </svg>
      <div class="score-ring-label">
        <div class="score-ring-number" style="color:${color}">${score || '--'}</div>
        <div class="score-ring-text">${label}</div>
      </div>
    </div>`;
}

// ── Format date/time ──────────────────────────────────────
function formatTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  const diffH   = Math.floor(diffMin / 60);
  const diffD   = Math.floor(diffH / 24);

  if (diffMin < 1)  return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffH < 24)   return `${diffH}h ago`;
  if (diffD < 7)    return `${diffD}d ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

// ── Share via WhatsApp ─────────────────────────────────────
function shareWhatsApp(text) {
  const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
  window.open(url, '_blank');
}

// ── Bottom Nav active state ───────────────────────────────
function setActiveNav(page) {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === page);
  });
}

// ── Debounce ──────────────────────────────────────────────
function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

// ── Loading button state ──────────────────────────────────
function setLoading(btn, loading, originalText) {
  if (loading) {
    btn.disabled = true;
    btn.dataset.original = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.original || originalText || btn.innerHTML;
  }
}

// ── Premium Chat Modal UI ─────────────────────────────────
let premiumChatModule = null;
let premiumChatHistory = [];

window.showPremiumChat = function(module, title) {
  let modal = document.getElementById('premium-chat-modal');
  if (!modal) {
    const html = `
      <div id="premium-chat-modal" class="premium-chat-overlay" style="display:none;">
        <div class="premium-chat-box">
          <div class="premium-chat-header">
            <div style="display:flex;align-items:center;gap:12px;">
              <div class="chat-avatar">AI</div>
              <div>
                <div id="pc-title" style="font-weight:800;color:var(--n-900);"></div>
                <div style="font-size:0.75rem;color:var(--color-primary);font-weight:700;">ArogyaAI Premium ✦</div>
              </div>
            </div>
            <button onclick="closePremiumChat()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--n-500);">&times;</button>
          </div>
          <div id="pc-messages" class="premium-chat-messages">
          </div>
          <div class="premium-chat-input-area">
            <input type="text" id="pc-input" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendPremiumMessage()">
            <button onclick="sendPremiumMessage()" id="pc-send">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
    modal = document.getElementById('premium-chat-modal');
  }

  document.getElementById('pc-title').innerText = title;
  premiumChatModule = module;
  premiumChatHistory = [];
  document.getElementById('pc-messages').innerHTML = `
    <div class="pc-msg pc-sys">
      <div>Hello! I am your AI ${title}. How can I assist you with your health goals today?</div>
    </div>
  `;
  
  modal.style.display = 'flex';
  setTimeout(() => document.getElementById('pc-input').focus(), 100);
}

window.closePremiumChat = function() {
  const modal = document.getElementById('premium-chat-modal');
  if (modal) modal.style.display = 'none';
}

window.sendPremiumMessage = async function() {
  const input = document.getElementById('pc-input');
  const msgText = input.value.trim();
  if (!msgText) return;
  
  input.value = '';
  const msgContainer = document.getElementById('pc-messages');
  
  // Add user message — SECURITY: escape user input before innerHTML
  const userDiv = document.createElement('div');
  userDiv.className = 'pc-msg pc-user';
  const userInner = document.createElement('div');
  userInner.textContent = msgText;   // XSS-safe: textContent not innerHTML
  userDiv.appendChild(userInner);
  msgContainer.appendChild(userDiv);
  premiumChatHistory.push({ role: "user", content: msgText });
  msgContainer.scrollTo({ top: msgContainer.scrollHeight, behavior: 'smooth' });

  // Loading indicator
  const loadingId = 'loading-' + Date.now();
  const loadingDiv = document.createElement('div');
  loadingDiv.id = loadingId;
  loadingDiv.className = 'pc-msg pc-sys';
  loadingDiv.innerHTML = `<div><span class="spinner" style="width:14px;height:14px;border-color:var(--color-primary);border-top-color:transparent;margin-right:6px;display:inline-block"></span>Thinking…</div>`;
  msgContainer.appendChild(loadingDiv);
  msgContainer.scrollTo({ top: msgContainer.scrollHeight, behavior: 'smooth' });

  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await fetch(`/api/premium/${premiumChatModule}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        message: msgText,
        history: premiumChatHistory.slice(-10),
        language: Lang.get(),
      })
    });

    const data = await res.json();
    document.getElementById(loadingId)?.remove();

    if (!res.ok) {
      const errMsg = typeof (data?.detail?.error || data?.detail) === 'string'
        ? (data?.detail?.error || data?.detail) : 'Something went wrong.';
      const errDiv = document.createElement('div');
      errDiv.className = 'pc-msg pc-sys';
      errDiv.innerHTML = `<div style="color:var(--color-danger)">⚠️ ${escapeHtml(errMsg)}</div>`;
      msgContainer.appendChild(errDiv);
    } else {
      const aiText = data.reply || data.response || '';
      premiumChatHistory.push({ role: "assistant", content: aiText });
      // renderMarkdown escapes HTML first, so this is XSS-safe
      const rendered = window.renderMarkdown ? window.renderMarkdown(aiText) : escapeHtml(aiText);
      const aiDiv = document.createElement('div');
      aiDiv.className = 'pc-msg pc-sys';
      aiDiv.innerHTML = `<div>${rendered}</div>`;
      msgContainer.appendChild(aiDiv);
    }
  } catch(e) {
    document.getElementById(loadingId)?.remove();
    const connErrDiv = document.createElement('div');
    connErrDiv.className = 'pc-msg pc-sys';
    connErrDiv.innerHTML = `<div style="color:var(--color-danger)">⚠️ Connection error. Please try again.</div>`;
    msgContainer.appendChild(connErrDiv);
  }
  msgContainer.scrollTo({ top: msgContainer.scrollHeight, behavior: 'smooth' });
}

document.addEventListener('click', (e) => {
  // Only intercept explicit premium-chat triggers (not generic Start/Ask buttons)
  const btn = e.target.closest('[data-premium-module]');
  if (!btn) return;
  const module = btn.dataset.premiumModule;
  const title  = btn.dataset.premiumTitle || 'AI Specialist';
  showPremiumChat(module, title);
  e.preventDefault();
});

// ── Shared Layout Components ──────────────────────────────
function injectSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  const p = window.location.pathname;

  const link = (path, icon, label, isEmoji=false) => {
    const active = p === path ? 'active' : '';
    const iconHtml = isEmoji
      ? `<span style="font-size:1.05rem;width:20px;text-align:center;flex-shrink:0">${icon}</span>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" style="width:18px;height:18px;stroke-width:1.8;flex-shrink:0">${icon}</svg>`;
    return `<div class="sidebar-link ${active}" onclick="window.location.href='${path}'">${iconHtml}${label}</div>`;
  };

  sidebar.innerHTML = `
    <div class="sidebar-brand" onclick="window.location.href='/dashboard'">
      <div class="sidebar-brand-icon">🌿</div>
      <div>
        <div class="sidebar-brand-name">Arogya<span>AI</span></div>
        <div style="font-size:.58rem;font-weight:800;color:var(--color-accent-dark);text-transform:uppercase;letter-spacing:.1em;margin-top:1px">World's Best AI Doctor</div>
      </div>
    </div>
    <nav class="sidebar-nav">
      ${link('/dashboard','<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>','Dashboard')}
      ${link('/chat','<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>','AI Doctor Chat')}

      <div class="sidebar-section-label">AI Modules</div>
      ${link('/nutrition','🥗','Diet &amp; Nutrition',true)}
      ${link('/fitness','🏃','Fitness Coach',true)}
      ${link('/mindfulness','🧘','Mind &amp; Peace',true)}
      ${link('/genetics','🧬','DNA Insights',true)}
      ${link('/food-scanner','🔍','Food Scanner',true)}
      ${link('/drug-checker','💊','Drug Checker',true)}

      <div class="sidebar-section-label">Health Records</div>
      ${link('/family','<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>','Family Health')}
      ${link('/reports','<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>','Lab Reports')}
      ${link('/profile','<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>','My Profile')}
      <div class="sidebar-link ${p==='/emergency'?'active':''}" onclick="window.location.href='/emergency'" style="color:var(--color-danger)">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" style="width:18px;height:18px;stroke-width:1.8;flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        Emergency SOS
      </div>
    </nav>
    <div class="sidebar-footer">
      <div class="sidebar-link" onclick="Auth.logout()" style="color:var(--color-danger)">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" style="width:18px;height:18px;stroke-width:1.8;flex-shrink:0"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        Logout
      </div>
    </div>
  `;
}

// Inject components immediately on load (assuming script is near body close)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { injectSidebar(); injectBottomNav(); });
} else {
  injectSidebar();
  injectBottomNav();
}

function injectBottomNav() {
  // Only inject if not already present and if not on login/signup pages
  if (document.querySelector('.bottom-nav')) return;
  const path = window.location.pathname;
  if (path === '/' || path.includes('login') || path.includes('signup')) return;

  const nav = document.createElement('nav');
  nav.className = 'bottom-nav';
  
  const isDashboard = path === '/dashboard' || path === '/';
  const isChat = path === '/chat';
  const isFamily = path === '/family';
  const isProfile = path === '/profile';

  nav.innerHTML = `
    <button class="nav-item ${isDashboard ? 'active' : ''}" onclick="window.location.href='/dashboard'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      Home
    </button>
    <button class="nav-item ${isChat ? 'active' : ''}" onclick="window.location.href='/chat'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Chat
    </button>
    <button class="nav-item ${isFamily ? 'active' : ''}" onclick="window.location.href='/family'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
      Family
    </button>
    <button class="nav-item ${isProfile ? 'active' : ''}" onclick="window.location.href='/profile'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      Profile
    </button>
    <button class="nav-item" onclick="window.location.href='/emergency'" style="color:#FF6B6B">
      <svg viewBox="0 0 24 24" fill="none" stroke="#FF6B6B"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      SOS
    </button>
  `;
  document.body.appendChild(nav);
}

// ── Privacy-First Analytics ───────────────────────────────
const Analytics = {
  _sessionId: null,

  _getSessionId() {
    if (!this._sessionId) {
      this._sessionId = localStorage.getItem(CONFIG.SESSION_KEY) ||
        Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(CONFIG.SESSION_KEY, this._sessionId);
    }
    return this._sessionId;
  },

  async track(event, properties = {}) {
    // Fire-and-forget: never block the UI for analytics
    try {
      await fetch('/api/analytics/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event,
          properties: { ...properties, path: window.location.pathname },
          session_id: this._getSessionId(),
        }),
      });
    } catch { /* Non-fatal */ }
  },

  pageView(path)                       { this.track('page_view', { path: path || window.location.pathname }); },
  chatSent(messageLength)              { this.track('chat_sent', { message_length: messageLength }); },
  upgradeClicked(source)               { this.track('upgrade_clicked', { source }); },
  premiumPurchased(plan, amount)       { this.track('premium_purchased', { plan, amount_inr: amount }); },
  featureUsed(feature)                 { this.track('feature_used', { feature }); },
  emergencyDetected()                  { this.track('emergency_detected'); },
};

// ── Expose globals ────────────────────────────────────────
window.API = API;
window.Auth = Auth;
window.Toast = Toast;
window.Lang = Lang;
window.Analytics = Analytics;
window.escapeHtml = escapeHtml;
window.renderMarkdown = renderMarkdown;
window.renderScoreRing = renderScoreRing;
window.scoreColor = scoreColor;
window.scoreLabel = scoreLabel;
window.formatTime = formatTime;
window.shareWhatsApp = shareWhatsApp;
window.setActiveNav = setActiveNav;
window.debounce = debounce;
window.setLoading = setLoading;
window.injectSidebar = injectSidebar;
