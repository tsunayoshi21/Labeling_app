// HTTP wrapper with automatic JWT header and 401 refresh
import { API_PREFIX, HTTP } from './config.js';
import { JWT } from './jwt.js';

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const id = setTimeout(() => reject(new Error('Request timeout')), ms);
    promise.then((res) => { clearTimeout(id); resolve(res); })
           .catch((err) => { clearTimeout(id); reject(err); });
  });
}

function buildUrl(url) {
  if (url.startsWith('/')) return `${API_PREFIX}${url.replace(/^\/api\/v2/, '')}`; // avoid double prefixes if caller passes full path
  return url;
}

async function doFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = JWT.getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  const finalOptions = { ...options, headers };
  const target = buildUrl(url);
  const res = await withTimeout(fetch(target, finalOptions), HTTP.defaultTimeout);
  return res;
}

export async function http(url, options = {}) {
  let res = await doFetch(url, options);
  if (res.status === 401 && HTTP.retryOnUnauthorized) {
    const newToken = await JWT.refresh();
    if (newToken) {
      res = await doFetch(url, options);
    }
  }
  // Explicitly handle 204 (No Content) early – no body to parse
  if (res.status === 204) {
    return null; // callers can interpret null as "no data"
  }
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      message = data.error || data.message || message;
    } catch {}
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }
  // Try JSON first
  try { return await res.json(); } catch { return await res.text(); }
}
