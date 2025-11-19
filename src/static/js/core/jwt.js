// JWT service: single source of truth for tokens and user
import { STORAGE_KEYS, API_PREFIX, ROUTES } from './config.js';

function getItem(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function setItem(key, value) {
  try { localStorage.setItem(key, value); } catch {}
}
function removeItem(key) {
  try { localStorage.removeItem(key); } catch {}
}

export const JWT = {
  getAccessToken() { return getItem(STORAGE_KEYS.accessToken); },
  getRefreshToken() { return getItem(STORAGE_KEYS.refreshToken); },
  getUser() {
    const raw = getItem(STORAGE_KEYS.currentUser);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  },
  setTokens(access, refresh) {
    if (access) setItem(STORAGE_KEYS.accessToken, access);
    if (refresh) setItem(STORAGE_KEYS.refreshToken, refresh);
    // also update cookie for server-rendered pages if needed
    try {
      document.cookie = `access_token=${access || ''}; path=/; max-age=${60*60*8}; SameSite=Strict`;
    } catch {}
  },
  setUser(user) {
    if (user) setItem(STORAGE_KEYS.currentUser, JSON.stringify(user));
  },
  clear() {
    removeItem(STORAGE_KEYS.accessToken);
    removeItem(STORAGE_KEYS.refreshToken);
    removeItem(STORAGE_KEYS.currentUser);
    try { document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'; } catch {}
  },
  isAuthenticated() { return !!this.getAccessToken() && !!this.getUser(); },
  async refresh() {
    const rt = this.getRefreshToken();
    if (!rt) return null;
    try {
      const res = await fetch(`${API_PREFIX}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!res.ok) return null;
      const data = await res.json();
      if (data && data.access_token) {
        this.setTokens(data.access_token, data.refresh_token || rt);
        if (data.user) this.setUser(data.user);
        return data.access_token;
      }
    } catch {}
    return null;
  },
  requireAuthOrRedirect() {
    if (!this.isAuthenticated()) {
      window.location.href = ROUTES.login;
      return false;
    }
    return true;
  },
  requireAdminOrRedirect() {
    const user = this.getUser();
    if (!this.isAuthenticated() || !user || user.role !== 'admin') {
      window.location.href = ROUTES.home;
      return false;
    }
    return true;
  },
};
