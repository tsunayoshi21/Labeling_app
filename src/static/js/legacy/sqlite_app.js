// JavaScript para la interfaz principal de anotación SQLite con JWT Auth

// ========== FUNCIONES DE AUTENTICACIÓN ==========

// Función para limpiar autenticación (delegada al nuevo módulo JWT si existe)
function clearAuth() {
    const ModAPI = window.ModAPI || {};
    if (ModAPI.JWT && typeof ModAPI.JWT.clear === 'function') {
        ModAPI.JWT.clear();
    } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('current_user');
    }
    // Limpiar cookie
    try {
        document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    } catch {}
}

// Verificar autenticación JWT al cargar la página (usar JWT modular si está disponible)
function checkJWTAuth() {
    const ModAPI = window.ModAPI || {};

    // Ruta moderna: usar el JWT del nuevo módulo
    if (ModAPI.JWT && typeof ModAPI.JWT.requireAuthOrRedirect === 'function') {
        const ok = ModAPI.JWT.requireAuthOrRedirect();
        if (!ok) return false;
        try {
            const user = ModAPI.JWT.getUser?.();
            if (user) {
                const userInfoElement = document.querySelector('.user-info span');
                if (userInfoElement) {
                    userInfoElement.textContent = `👤 ${user.username} (${user.role})`;
                }
            }
        } catch {}
        return true;
    }

    // Fallback legado
    const accessToken = localStorage.getItem('access_token');
    const currentUser = localStorage.getItem('current_user');
    if (!accessToken || !currentUser) {
        console.log('No se encontraron tokens JWT, redirigiendo a login');
        clearAuth();
        window.location.href = '/login';
        return false;
    }
    try {
        const user = JSON.parse(currentUser);
        const userInfoElement = document.querySelector('.user-info span');
        if (userInfoElement) {
            userInfoElement.textContent = `👤 ${user.username} (${user.role})`;
        }
        return true;
    } catch (error) {
        console.error('Error parseando datos de usuario:', error);
        clearAuth();
        window.location.href = '/login';
        return false;
    }
}

// ========== SERVICIOS JWT Y API ==========

// Compatibilidad: JWTService ligero que delega al nuevo módulo JWT
class JWTService {
    static TOKEN_KEY = 'access_token';
    static REFRESH_TOKEN_KEY = 'refresh_token';
    static USER_KEY = 'current_user';

    static get _jwt() { return (window.ModAPI && window.ModAPI.JWT) || null; }

    static getToken() {
        return this._jwt?.getAccessToken?.() ?? localStorage.getItem(this.TOKEN_KEY);
    }

    static getRefreshToken() {
        return this._jwt?.getRefreshToken?.() ?? localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    static setTokens(accessToken, refreshToken) {
        if (this._jwt?.setTokens) {
            this._jwt.setTokens(accessToken, refreshToken);
            return;
        }
        if (accessToken) localStorage.setItem(this.TOKEN_KEY, accessToken);
        if (refreshToken) localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }

    static clearTokens() {
        if (this._jwt?.clear) return this._jwt.clear();
        clearAuth();
    }

    static setUser(user) {
        if (this._jwt?.setUser) return this._jwt.setUser(user);
        if (user) localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }

    static getUser() {
        if (this._jwt?.getUser) return this._jwt.getUser();
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
    }

    static isAuthenticated() {
        if (this._jwt?.isAuthenticated) return this._jwt.isAuthenticated();
        return !!this.getToken();
    }

    static async refreshToken() {
        if (this._jwt?.refresh) {
            const token = await this._jwt.refresh();
            if (!token) throw new Error('Token refresh failed');
            return token;
        }
        // Fallback muy básico si no hay módulo (no debería ocurrir en migración)
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) throw new Error('No refresh token available');
        const response = await fetch('/api/v2/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (!response.ok) {
            this.clearTokens();
            throw new Error('Token refresh failed');
        }
        const data = await response.json();
        this.setTokens(data.access_token, data.refresh_token);
        return data.access_token;
    }

    static getAuthHeaders() {
        const token = this.getToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    }
}

// Compatibilidad: APIService que delega a los nuevos servicios (taskService, statsService, authService)
class APIService {
    static get _task() { return window.ModAPI && window.ModAPI.taskService; }
    static get _stats() { return window.ModAPI && window.ModAPI.statsService; }
    static get _auth() { return window.ModAPI && window.ModAPI.authService; }

    static async getCurrentTask() {
        if (this._task?.getNextTask) {
            const data = await this._task.getNextTask();
            if (data === null) return { completed: true };
            if (!data || (typeof data === 'string' && data.trim() === '')) {
                return { completed: true };
            }
            return data;
        }
        const response = await fetch('/api/v2/task/next', { headers: JWTService.getAuthHeaders() });
        if (response.status === 204) return { completed: true };
        return await response.json();
    }

    static async getTaskHistory(limit = 10) {
        if (this._task?.getHistory) return this._task.getHistory(limit);
        const response = await fetch(`/api/v2/task/history?limit=${encodeURIComponent(limit)}`, { headers: JWTService.getAuthHeaders() });
        return await response.json();
    }

    static async getPendingPreview(limit = 10) {
        if (this._task?.getPendingPreview) return this._task.getPendingPreview(limit);
        const response = await fetch(`/api/v2/task/pending-preview?limit=${encodeURIComponent(limit)}`, { headers: JWTService.getAuthHeaders() });
        return await response.json();
    }

    static async loadSpecificTask(annotationId) {
        if (this._task?.loadTask) return this._task.loadTask(annotationId);
        const response = await fetch(`/api/v2/task/load/${annotationId}`, { headers: JWTService.getAuthHeaders() });
        if (!response.ok) throw new Error('Task not found');
        return await response.json();
    }

    static async submitAction(annotationId, action, correctedText = null) {
        if (this._task?.submitAction) return this._task.submitAction(annotationId, action, correctedText);
        const payload = { status: action };
        if (correctedText) payload.corrected_text = correctedText;
        const response = await fetch(`/api/v2/annotations/${annotationId}`, {
            method: 'PUT',
            headers: JWTService.getAuthHeaders(),
            body: JSON.stringify(payload)
        });
        return await response.json();
    }

    static async getUserStats() {
        if (this._stats?.myStats) return this._stats.myStats();
        const response = await fetch('/api/v2/stats', { headers: JWTService.getAuthHeaders() });
        return await response.json();
    }

    static async getUserInfo() {
        if (this._auth?.me) return this._auth.me();
        const response = await fetch('/api/v2/me', { headers: JWTService.getAuthHeaders() });
        return await response.json();
    }

    static async logout() {
        try {
            if (this._auth?.logout) await this._auth.logout();
            else await fetch('/api/v2/logout', { method: 'POST', headers: JWTService.getAuthHeaders() });
        } catch {}
        JWTService.clearTokens();
        return true;
    }
}

// === LEGACY PRUNING PHASE ===
// Se han migrado navegación, acciones, edición, pending list y stats a módulos ES (annotator.js + controller + components).
// Este archivo mantiene sólo compatibilidad básica (auth y bootstrap inicial) mientras se valida la nueva implementación.
// Las clases UIManager, EditModeManager, KeyboardHandler y métodos relacionados con acciones ya no se utilizan cuando
// window.modAnnotatorController está presente. Se marcan como deprecated para futura eliminación.

class UIManager { /* deprecated: usar uiAdapter + componentes modulares */ }
class EditModeManager { /* deprecated */ }
class KeyboardHandler { /* deprecated */ }

// App Controller - Controlador principal de la aplicación con JWT
class AppController {
    constructor() {
        // Sólo conservar lógica de usuario/admin mientras se migra al controller modular
        this.currentUser = null;
        this.init();
    }

    async init() {
        try {
            await this.loadUserInfo();
            // Si existe controlador modular, no continuar con lógica legacy
            if (window.modAnnotatorController) return;
        } catch (e) { console.error('Init legacy error', e); }
    }

    async loadUserInfo() {
        try {
            const cachedUser = JWTService.getUser();
            if (cachedUser) {
                this.currentUser = cachedUser;
                const el = document.getElementById('user-name');
                if (el) el.textContent = `${cachedUser.username} (${cachedUser.role})`;
                this.showAdminButtonIfNeeded();
            }
            const data = await APIService.getUserInfo();
            if (data?.user) {
                this.currentUser = data.user;
                JWTService.setUser(data.user);
                const el = document.getElementById('user-name');
                if (el) el.textContent = `${data.user.username} (${data.user.role})`;
                this.showAdminButtonIfNeeded();
            }
        } catch (e) { console.error('user info legacy', e); }
    }

    showAdminButtonIfNeeded() {
        if (!this.currentUser?.role) return;
        const existingBtn = document.getElementById('admin-panel-btn');
        if (existingBtn) existingBtn.remove();
        if (this.currentUser.role === 'admin') {
            const userInfo = document.querySelector('.user-info');
            if (!userInfo) return;
            const adminBtn = document.createElement('button');
            adminBtn.id = 'admin-panel-btn';
            adminBtn.className = 'logout-btn';
            adminBtn.style.marginRight = '1rem';
            adminBtn.innerHTML = '⚙️ Panel Admin';
            adminBtn.onclick = () => { window.location.href = '/admin'; };
            const logoutBtn = userInfo.querySelector('.logout-btn');
            userInfo.insertBefore(adminBtn, logoutBtn);
        }
    }

    async logout() { await APIService.logout(); window.location.href = '/login'; }
}

// Nota: A partir de Phase 4 se están migrando acciones, edición y toasts a módulos.
// Las funciones de UI (indicadores de estado y mensajes) serán reemplazadas gradualmente.
// Mantener por compatibilidad hasta completar migración y pruebas.

// Funciones globales para compatibilidad
async function loadNextTask() {
    if (window.appController) {
        await window.appController.loadCurrentTask();
    }
}

async function logout() {
    if (window.appController) {
        await window.appController.logout();
    }
}

// Inicialización: sólo crea AppController para info de usuario si no existe modular
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación primero, luego inicializar la aplicación
    if (checkJWTAuth()) {
        if (!window.appController) window.appController = new AppController();
    }
});
