// Core configuration for frontend
// Centralize API prefix, storage keys, and common constants

export const API_PREFIX = '/api/v2';

export const STORAGE_KEYS = {
  accessToken: 'access_token',
  refreshToken: 'refresh_token',
  currentUser: 'current_user',
};

export const HTTP = {
  // milliseconds
  defaultTimeout: 30000,
  retryOnUnauthorized: true,
};

export const ROUTES = {
  login: '/login',
  home: '/',
  admin: '/admin',
};

export function isAbsoluteUrl(url) {
  return /^https?:\/\//i.test(url);
}
