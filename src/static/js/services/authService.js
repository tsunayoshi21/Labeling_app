import { http } from '../core/http.js';
import { JWT } from '../core/jwt.js';

export const authService = {
  async login(username, password) {
    const data = await http('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (data?.access_token) {
      JWT.setTokens(data.access_token, data.refresh_token);
      if (data.user) JWT.setUser(data.user);
    }
    return data;
  },
  async logout() {
    try { await http('/logout', { method: 'POST' }); } catch {}
    JWT.clear();
  },
  async me() {
    return http('/me', { method: 'GET' });
  },
};
