import { JWT } from '../core/jwt.js';
import { authService } from '../services/authService.js';
import { ROUTES } from '../core/config.js';

function qs(sel) { return document.querySelector(sel); }

function show(el) { el.style.display = 'block'; }
function hide(el) { el.style.display = 'none'; }

function bindLoginForm() {
  const form = qs('#login-form');
  const errorDiv = qs('#error-message');
  const successDiv = qs('#success-message');
  const btn = qs('#login-form button, #login-btn');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hide(errorDiv); hide(successDiv);
    if (btn) { btn.disabled = true; if (btn.textContent) btn.textContent = 'Iniciando sesión...'; }
    const username = qs('#username')?.value?.trim();
    const password = qs('#password')?.value || '';
    try {
      const data = await authService.login(username, password);
      show(successDiv); successDiv.textContent = 'Inicio de sesión exitoso. Redirigiendo...';
      const role = data?.user?.role;
      setTimeout(() => {
        window.location.href = role === 'admin' ? ROUTES.admin : ROUTES.home;
      }, 600);
    } catch (err) {
      show(errorDiv); errorDiv.textContent = err.message || 'Error en el inicio de sesión';
    } finally {
      if (btn) { btn.disabled = false; if (btn.textContent) btn.textContent = 'Iniciar Sesión'; }
    }
  });
}

(async function init() {
  bindLoginForm();
  // Validar sesión existente realmente con el backend antes de redirigir
  if (JWT.getAccessToken() && JWT.getUser()) {
    try {
      const data = await authService.me();
      const role = data?.user?.role || JWT.getUser()?.role;
      if (role) {
        window.location.href = role === 'admin' ? ROUTES.admin : ROUTES.home;
        return;
      }
    } catch (e) {
      // Token inválido / expirado: limpiar y permanecer en login
      JWT.clear();
    }
  }
})();
