/* ══════════════════════════════════════════════════════════
   Korean Biz Coach — Shared JS (Auth + API + Toast)
   ══════════════════════════════════════════════════════════ */

// ── Auth Helper ───────────────────────────────────────
const Auth = {
  get token() { return localStorage.getItem('token'); },
  get userId() { return localStorage.getItem('userId'); },
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    window.location.href = '/static/index.html';
  },
};

// ── API Helper ────────────────────────────────────────
const Api = {
  _headers() {
    const h = { 'Content-Type': 'application/json' };
    if (Auth.token) h['Authorization'] = 'Bearer ' + Auth.token;
    return h;
  },

  _activeController: null,

  async _fetch(method, url, body, opts = {}) {
    const fetchOpts = { method, headers: this._headers() };
    if (body) fetchOpts.body = JSON.stringify(body);
    if (opts.signal) fetchOpts.signal = opts.signal;
    const res = await fetch(url, fetchOpts);
    if (res.status === 401) {
      Auth.logout();
      throw new Error('Session expired, please log in again');
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
    return data;
  },

  get(url) { return this._fetch('GET', url); },
  post(url, body, opts) { return this._fetch('POST', url, body, opts); },
  put(url, body) { return this._fetch('PUT', url, body); },
  patch(url, body) { return this._fetch('PATCH', url, body); },
  del(url) { return this._fetch('DELETE', url); },
};

// ── Toast Notifications ───────────────────────────────
const Toast = {
  show(msg, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  },
};
