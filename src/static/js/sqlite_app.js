// JavaScript para la interfaz principal de anotación SQLite con JWT Auth

// ========== FUNCIONES DE AUTENTICACIÓN ==========

// Función para limpiar autenticación
function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_user');
    // Limpiar cookie
    document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
}

// Verificar autenticación JWT al cargar la página
function checkJWTAuth() {
    const accessToken = localStorage.getItem('access_token');
    const currentUser = localStorage.getItem('current_user');
    
    if (!accessToken || !currentUser) {
        console.log('No se encontraron tokens JWT, redirigiendo a login');
        clearAuth(); // Limpiar todo por si acaso
        window.location.href = '/login';
        return false;
    }
    
    try {
        const user = JSON.parse(currentUser);
        console.log('Usuario autenticado:', user.username);
        
        // Actualizar información del usuario en el header
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

// JWT Service - Maneja tokens de autenticación
class JWTService {
    static TOKEN_KEY = 'access_token';
    static REFRESH_TOKEN_KEY = 'refresh_token';
    static USER_KEY = 'current_user';

    static getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static getRefreshToken() {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    static setTokens(accessToken, refreshToken) {
        localStorage.setItem(this.TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
        }
    }

    static clearTokens() {
        // Usar la función centralizada
        clearAuth();
    }

    static setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }

    static getUser() {
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
    }

    static isAuthenticated() {
        return !!this.getToken();
    }

    static async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await fetch('/api/v2/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            this.setTokens(data.access_token, data.refresh_token);
            return data.access_token;
        } else {
            this.clearTokens();
            throw new Error('Token refresh failed');
        }
    }

    static getAuthHeaders() {
        const token = this.getToken();
        if (token) {
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };
        }
        return { 'Content-Type': 'application/json' };
    }
}

// API Service - Maneja todas las llamadas al backend con JWT
class APIService {
    static async makeRequest(url, options = {}) {
        // Agregar headers de autenticación
        options.headers = {
            ...options.headers,
            ...JWTService.getAuthHeaders()
        };

        let response = await fetch(url, options);

        // Si el token expiró, intentar renovarlo
        if (response.status === 401 && JWTService.getRefreshToken()) {
            try {
                await JWTService.refreshToken();
                // Reintentar la request con el nuevo token
                options.headers = {
                    ...options.headers,
                    ...JWTService.getAuthHeaders()
                };
                response = await fetch(url, options);
            } catch (error) {
                // Refresh falló, redirigir a login
                window.location.href = '/login';
                return;
            }
        }

        // Si aún no está autorizado, redirigir a login
        if (response.status === 401) {
            JWTService.clearTokens();
            window.location.href = '/login';
            return;
        }

        return response;
    }

    static async getCurrentTask() {
        const response = await this.makeRequest('/api/v2/task/next');
        if (response.status === 204) {
            return { completed: true };
        }
        return await response.json();
    }

    static async getTaskHistory(limit = 10) {
        const response = await this.makeRequest(`/api/v2/task/history?limit=${limit}`);
        return await response.json();
    }

    static async getPendingPreview(limit = 10) {
        const response = await this.makeRequest(`/api/v2/task/pending-preview?limit=${limit}`);
        return await response.json();
    }

    static async loadSpecificTask(annotationId) {
        const response = await this.makeRequest(`/api/v2/task/load/${annotationId}`);
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Task not found');
    }

    static async submitAction(annotationId, action, correctedText = null) {
        const payload = { status: action };
        if (correctedText) {
            payload.corrected_text = correctedText;
        }

        const response = await this.makeRequest(`/api/v2/annotations/${annotationId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    }

    static async getUserStats() {
        const response = await this.makeRequest('/api/v2/stats');
        return await response.json();
    }

    static async getUserInfo() {
        const response = await this.makeRequest('/api/v2/me');
        return await response.json();
    }

    static async logout() {
        const response = await this.makeRequest('/api/v2/logout', {
            method: 'POST'
        });
        
        // Limpiar tokens locales
        JWTService.clearTokens();
        
        return response.ok;
    }
}

// UI Manager - Maneja la interfaz de usuario (similar a la versión original)
class UIManager {
    constructor() {
        this.previousStats = {};
    }

    showLoading(show) {
        const loadingDiv = document.getElementById('loadingDiv');
        const workArea = document.getElementById('workArea');
        
        if (show) {
            loadingDiv.classList.remove('hidden');
            workArea.classList.add('hidden');
        } else {
            loadingDiv.classList.add('hidden');
            workArea.classList.remove('hidden');
        }
    }

    showCompletion() {
        document.getElementById('workArea').classList.add('hidden');
        document.getElementById('completionDiv').classList.remove('hidden');
    }

    showError(message) {
        const errorDiv = document.getElementById('errorDiv');
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    }

    highlightButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button || button.classList.contains('hidden')) return;
        
        button.style.transform = 'scale(1.1)';
        button.style.boxShadow = '0 0 20px rgba(255,255,255,0.8)';
        
        setTimeout(() => {
            button.style.transform = '';
            button.style.boxShadow = '';
        }, 200);
    }

    softHighlightButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button || button.classList.contains('hidden')) return;
        
        // Efecto más suave: solo un ligero cambio de opacidad y escala
        button.style.transform = 'scale(1.05)';
        button.style.opacity = '0.8';
        button.style.transition = 'all 0.15s ease-out';
        
        setTimeout(() => {
            button.style.transform = '';
            button.style.opacity = '';
            button.style.transition = '';
        }, 150);
    }

    updateImage(imageData) {
        const imageElement = document.getElementById('currentImage');
        const noImageMessage = document.getElementById('noImageMessage');
        
        if (imageData.image_path) {
            // Extraer solo el nombre del archivo de la ruta completa
            const imageName = imageData.image_path.split('/').pop();
            imageElement.src = `/images/${imageName}`;
            imageElement.classList.remove('hidden');
            noImageMessage.classList.add('hidden');
            
            imageElement.onload = function() {
                // Ajustar tamaño para imágenes pequeñas (como en la versión original)
                if (this.naturalWidth < 200 || this.naturalHeight < 100) {
                    this.classList.add('small-image');
                    this.style.minWidth = '400px';
                } else {
                    this.classList.remove('small-image');
                    this.style.minWidth = '';
                }
            };

            imageElement.onerror = function() {
                // Si la imagen no carga, mostrar mensaje de error
                imageElement.classList.add('hidden');
                noImageMessage.classList.remove('hidden');
            };
        } else {
            imageElement.classList.add('hidden');
            noImageMessage.classList.remove('hidden');
        }
    }

    updateProgress(stats) {
        const total = stats.total;
        const completed = stats.corrected + stats.approved + stats.discarded;
        const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
        
        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
    }

    updateStats(stats) {
        const statsToUpdate = [
            { id: 'totalTasks', value: stats.total, key: 'total' },
            { id: 'pendingTasks', value: stats.pending, key: 'pending' },
            { id: 'correctedTasks', value: stats.corrected, key: 'corrected' },
            { id: 'approvedTasks', value: stats.approved, key: 'approved' },
            { id: 'discardedTasks', value: stats.discarded, key: 'discarded' }
        ];
        
        statsToUpdate.forEach(stat => {
            const element = document.getElementById(stat.id);
            const statContainer = element.closest('.stat');
            
            // Efecto de highlight cuando cambia el valor
            if (this.previousStats[stat.key] !== undefined && 
                this.previousStats[stat.key] !== stat.value) {
                
                statContainer.classList.remove('highlight');
                statContainer.offsetHeight; // Force reflow
                statContainer.classList.add('highlight');
                
                setTimeout(() => {
                    statContainer.classList.remove('highlight');
                }, 1000);
            }
            
            element.textContent = stat.value;
        });
        
        this.previousStats = {
            total: stats.total,
            pending: stats.pending,
            corrected: stats.corrected,
            approved: stats.approved,
            discarded: stats.discarded
        };

        this.updateProgress(stats);
    }
}

// Edit Mode Manager - Maneja el modo de edición (igual que la versión original)
class EditModeManager {
    constructor() {
        this.isEditMode = false;
    }

    toggleEditMode(transcription) {
        this.isEditMode = true;
        const transcriptionDisplay = document.getElementById('transcriptionDisplay');
        const editInput = document.getElementById('editInput');
        const correctBtn = document.getElementById('correctBtn');
        const editBtn = document.getElementById('editBtn');
        const discardBtn = document.getElementById('discardBtn');
        const saveEditBtn = document.getElementById('saveEditBtn');
        const cancelBtn = document.getElementById('cancelBtn');
        
        transcriptionDisplay.classList.add('hidden');
        editInput.classList.remove('hidden');
        editInput.value = transcription;
        editInput.focus();
        editInput.select();
        
        correctBtn.classList.add('hidden');
        editBtn.classList.add('hidden');
        discardBtn.classList.add('hidden');
        saveEditBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
    }

    cancelEdit() {
        this.isEditMode = false;
        const transcriptionDisplay = document.getElementById('transcriptionDisplay');
        const editInput = document.getElementById('editInput');
        const correctBtn = document.getElementById('correctBtn');
        const editBtn = document.getElementById('editBtn');
        const discardBtn = document.getElementById('discardBtn');
        const saveEditBtn = document.getElementById('saveEditBtn');
        const cancelBtn = document.getElementById('cancelBtn');
        
        transcriptionDisplay.classList.remove('hidden');
        editInput.classList.add('hidden');
        
        correctBtn.classList.remove('hidden');
        editBtn.classList.remove('hidden');
        discardBtn.classList.remove('hidden');
        saveEditBtn.classList.add('hidden');
        cancelBtn.classList.add('hidden');
    }

    getEditedText() {
        return document.getElementById('editInput').value.trim();
    }
}

// Keyboard Handler - Maneja los atajos de teclado (igual que la versión original)
class KeyboardHandler {
    constructor(appController) {
        this.appController = appController;
        this.setupKeyboardListeners();
    }

    setupKeyboardListeners() {
        document.addEventListener('keydown', (e) => {
            // Si estamos en modo edición
            if (this.appController.editModeManager.isEditMode) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.appController.saveEdit();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    this.appController.cancelEdit();
                }
                return;
            }
            
            // Atajos globales
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('correctBtn');
                    this.appController.submitAction('approved');
                    break;
                case '2':
                case 'e':
                case 'E':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('editBtn');
                    this.appController.toggleEditMode();
                    break;
                case '3':
                case 'Delete':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('discardBtn');
                    this.appController.submitAction('discarded');
                    break;
                case ' ':
                    if (!e.ctrlKey && !e.altKey && !e.shiftKey) {
                        e.preventDefault();
                        this.appController.uiManager.highlightButton('correctBtn');
                        this.appController.submitAction('approved');
                    }
                    break;
                case 'l':
                case 'L':
                    if (!e.ctrlKey && !e.altKey && !e.shiftKey) {
                        e.preventDefault();
                        this.appController.logout();
                    }
                    break;
            }
        });
    }
}

// App Controller - Controlador principal de la aplicación
// App Controller - Controlador principal de la aplicación con JWT
class AppController {
    constructor() {
        this.currentTask = null;
        this.currentAnnotationId = null;
        this.taskHistory = [];
        this.pendingTasks = [];
        this.historyIndex = -1; // -1 significa que estamos en la tarea actual (no en historial)
        this.currentUser = null; // Almacenar información del usuario actual
        this.uiManager = new UIManager();
        this.editModeManager = new EditModeManager();
        this.keyboardHandler = new KeyboardHandler(this);
        
        this.init();
    }

    async init() {
        // La verificación de autenticación ya se hizo en checkJWTAuth()
        try {
            await this.loadUserInfo();
            await this.updateStats();
            await this.loadTaskHistory(); // Cargar historial primero
            await this.loadCurrentTask();
            await this.updatePendingPreview();
            this.setupEventListeners();
        } catch (error) {
            console.error('Error initializing app:', error);
            // Si hay error de autenticación, redirigir a login
            if (error.message.includes('401') || error.message.includes('Token')) {
                JWTService.clearTokens();
                window.location.href = '/login';
            }
        }
    }

    async loadUserInfo() {
        try {
            // Primero intentar obtener del localStorage
            const cachedUser = JWTService.getUser();
            if (cachedUser) {
                this.currentUser = cachedUser;
                document.getElementById('user-name').textContent = 
                    `${cachedUser.username} (${cachedUser.role})`;
                this.showAdminButtonIfNeeded();
            }

            // Luego verificar con el servidor
            const data = await APIService.getUserInfo();
            if (data.user) {
                this.currentUser = data.user;
                JWTService.setUser(data.user); // Actualizar cache
                document.getElementById('user-name').textContent = 
                    `${data.user.username} (${data.user.role})`;
                
                // Mostrar botón de admin si el usuario es admin
                this.showAdminButtonIfNeeded();
            }
        } catch (error) {
            console.error('Error loading user info:', error);
            throw error;
        }
    }

    showAdminButtonIfNeeded() {
        // Remover botón existente si existe
        const existingBtn = document.getElementById('admin-panel-btn');
        if (existingBtn) {
            existingBtn.remove();
        }

        // Agregar botón de admin si el usuario es admin
        if (this.currentUser && this.currentUser.role === 'admin') {
            const userInfo = document.querySelector('.user-info');
            const adminBtn = document.createElement('button');
            adminBtn.id = 'admin-panel-btn';
            adminBtn.className = 'logout-btn';
            adminBtn.style.marginRight = '1rem';
            adminBtn.innerHTML = '⚙️ Panel Admin';
            adminBtn.onclick = () => {
                window.location.href = '/admin';
            };
            
            // Insertar antes del botón de cerrar sesión
            const logoutBtn = userInfo.querySelector('.logout-btn');
            userInfo.insertBefore(adminBtn, logoutBtn);
        }
    }

    setupEventListeners() {
        document.getElementById('correctBtn').addEventListener('click', () => this.submitAction('approved'));
        document.getElementById('editBtn').addEventListener('click', () => this.toggleEditMode());
        document.getElementById('discardBtn').addEventListener('click', () => this.submitAction('discarded'));
        document.getElementById('saveEditBtn').addEventListener('click', () => this.saveEdit());
        document.getElementById('cancelBtn').addEventListener('click', () => this.cancelEdit());
        
        // Navegación
        document.getElementById('prevBtn').addEventListener('click', () => this.navigatePrevious());
        document.getElementById('nextBtn').addEventListener('click', () => this.navigateNext());
        
        // Hotkeys para navegación
        document.addEventListener('keydown', (e) => {
            // Solo activar hotkeys si no estamos editando texto
            if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigatePrevious();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateNext();
                    break;
            }
        });
        
        document.getElementById('editInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.saveEdit();
            }
        });
    }

    async loadCurrentTask() {
        try {
            this.uiManager.showLoading(true);
            const taskData = await APIService.getCurrentTask();
            
            if (taskData.completed) {
                this.uiManager.showCompletion();
                return;
            }
            
            this.currentTask = taskData;
            this.currentAnnotationId = taskData.annotation_id;
            this.historyIndex = -1; // Resetear a tarea actual
            this.updateUI();
            // Solo actualizar botones si ya tenemos historial o si taskHistory está definido
            if (this.taskHistory !== undefined) {
                this.updateNavigationButtons();
            }
            console.log('Current task loaded:', taskData.annotation_id);
        } catch (error) {
            console.error('Error loading task:', error);
            this.uiManager.showError('Error cargando tarea');
        } finally {
            this.uiManager.showLoading(false);
        }
    }

    updateUI() {
        if (!this.currentTask) return;
        
        this.uiManager.updateImage(this.currentTask);
        
        // Mostrar el texto corregido si existe, sino el OCR original
        const displayText = this.currentTask.corrected_text || this.currentTask.initial_ocr_text;
        const transcriptionDisplay = document.getElementById('transcriptionDisplay');
        transcriptionDisplay.textContent = displayText;
        
        // Manejar indicadores visuales según el estado
        const transcriptionContainer = transcriptionDisplay.parentElement;
        let statusIndicator = transcriptionContainer.querySelector('.status-indicator');
        
        // Remover indicador anterior si existe
        if (statusIndicator) {
            statusIndicator.remove();
        }
        
        // Restablecer TODOS los estilos
        transcriptionDisplay.style.color = '';
        transcriptionDisplay.style.fontWeight = '';
        transcriptionDisplay.style.textDecoration = ''; // Limpiar texto tachado
        
        if (this.currentTask.status === 'discarded') {
            // Mostrar indicador de imagen descartada
            statusIndicator = document.createElement('div');
            statusIndicator.className = 'status-indicator discarded-indicator';
            statusIndicator.style.cssText = 'color: #e74c3c; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px;';
            statusIndicator.textContent = '🗑️ Imagen Descartada';
            transcriptionContainer.insertBefore(statusIndicator, transcriptionDisplay);
            transcriptionDisplay.style.color = '#e74c3c';
            transcriptionDisplay.style.fontWeight = 'bold';
            transcriptionDisplay.style.textDecoration = 'line-through';
        } else if (this.currentTask.status === 'corrected') {
            // Mostrar indicador de texto corregido
            statusIndicator = document.createElement('div');
            statusIndicator.className = 'status-indicator corrected-indicator';
            statusIndicator.style.cssText = 'color: #27ae60; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px;';
            statusIndicator.textContent = '✓ Texto Corregido';
            transcriptionContainer.insertBefore(statusIndicator, transcriptionDisplay);
            transcriptionDisplay.style.color = '#27ae60';
            transcriptionDisplay.style.fontWeight = 'bold';
        } else if (this.currentTask.status === 'approved') {
            // Mostrar indicador de texto aprobado
            statusIndicator = document.createElement('div');
            statusIndicator.className = 'status-indicator approved-indicator';
            statusIndicator.style.cssText = 'color: #3498db; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px;';
            statusIndicator.textContent = '✓ Texto Aprobado';
            transcriptionContainer.insertBefore(statusIndicator, transcriptionDisplay);
            transcriptionDisplay.style.color = '#3498db';
            transcriptionDisplay.style.fontWeight = 'bold';
        }
        
        // Actualizar ID de imagen
        document.getElementById('currentImageId').textContent = this.currentTask.image_id || '-';
        
        // Actualizar campo de edición con el texto apropiado
        const editText = this.currentTask.corrected_text || this.currentTask.initial_ocr_text;
        document.getElementById('editInput').value = editText;
        
        // Actualizar vista previa si estamos en tarea actual
        if (this.historyIndex === -1) {
            this.updatePendingUI();
        }
    }

    async updateStats() {
        try {
            const stats = await APIService.getUserStats();
            this.uiManager.updateStats(stats);
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    async loadTaskHistory() {
        try {
            const data = await APIService.getTaskHistory(10);
            this.taskHistory = data.history;
            this.updateNavigationButtons();
            console.log('Task history loaded:', this.taskHistory.length, 'items');
        } catch (error) {
            console.error('Error loading task history:', error);
            this.taskHistory = [];
        }
    }

    async updatePendingPreview() {
        try {
            const data = await APIService.getPendingPreview(10);
            this.pendingTasks = data.pending;
            this.updatePendingUI();
        } catch (error) {
            console.error('Error updating pending preview:', error);
        }
    }

    updatePendingUI() {
        const container = document.getElementById('pendingTasksPreview');
        if (this.pendingTasks.length === 0) {
            container.innerHTML = '<div class="pending-item">No hay tareas pendientes</div>';
            return;
        }

        container.innerHTML = this.pendingTasks.map((task, index) => {
            const isCurrent = this.currentTask && task.annotation_id === this.currentTask.annotation_id;
            
            // Determinar indicador de estado
            let statusIcon = '';
            let statusClass = '';
            if (task.status === 'corrected') {
                statusIcon = '✓';
                statusClass = 'corrected';
            } else if (task.status === 'approved') {
                statusIcon = '✓';
                statusClass = 'approved';
            } else if (task.status === 'discarded') {
                statusIcon = '🗑️';
                statusClass = 'discarded';
            }
            
            return `
                <div class="pending-item ${isCurrent ? 'current' : ''} ${statusClass}" 
                     onclick="window.appController.loadTaskFromPreview(${task.annotation_id})"
                     title="Clic para cargar esta tarea">
                    ${statusIcon} ID: ${task.image_id}
                </div>
            `;
        }).join('');
    }

    async loadTaskFromPreview(annotationId) {
        try {
            this.uiManager.showLoading(true);
            const taskData = await APIService.loadSpecificTask(annotationId);
            
            this.currentTask = taskData;
            this.currentAnnotationId = taskData.annotation_id;
            this.historyIndex = -1; // Resetear a tarea actual
            this.updateUI();
            await this.updatePendingPreview();
            this.updateNavigationButtons();
        } catch (error) {
            console.error('Error loading task from preview:', error);
            this.uiManager.showError('Error cargando tarea');
        } finally {
            this.uiManager.showLoading(false);
        }
    }

    async navigatePrevious() {
        console.log('Navigate previous - current state:', {
            historyIndex: this.historyIndex,
            historyLength: this.taskHistory.length
        });
        
        // Efecto visual de confirmación suave
        this.uiManager.softHighlightButton('prevBtn');
        
        if (this.historyIndex === -1) {
            // Estamos en tarea actual, ir al historial más reciente
            if (this.taskHistory.length > 0) {
                this.historyIndex = 0;
                this.loadTaskFromHistory(this.taskHistory[0]);
                console.log('Moved to history index 0');
            } else {
                console.log('No history available');
            }
        } else if (this.historyIndex < this.taskHistory.length - 1) {
            // Ir más atrás en el historial
            this.historyIndex++;
            this.loadTaskFromHistory(this.taskHistory[this.historyIndex]);
            console.log('Moved to history index', this.historyIndex);
        } else {
            console.log('Already at oldest history item');
        }
        
        this.updateNavigationButtons();
    }

    async navigateNext() {
        console.log('Navigate next - current state:', {
            historyIndex: this.historyIndex,
            historyLength: this.taskHistory.length
        });
        
        // Efecto visual de confirmación suave
        this.uiManager.softHighlightButton('nextBtn');
        
        if (this.historyIndex > 0) {
            // Ir hacia adelante en el historial (más reciente)
            this.historyIndex--;
            this.loadTaskFromHistory(this.taskHistory[this.historyIndex]);
            console.log('Moved to history index', this.historyIndex);
        } else if (this.historyIndex === 0) {
            // Volver a la tarea actual
            this.historyIndex = -1;
            await this.loadCurrentTask();
            console.log('Returned to current task');
        } else {
            console.log('Already at current task');
        }
        
        this.updateNavigationButtons();
    }

    loadTaskFromHistory(taskData) {
        this.currentTask = taskData;
        this.currentAnnotationId = taskData.annotation_id;
        this.updateUI();
        
        // Mostrar que estamos en modo historial
        const imageHeader = document.querySelector('.image-header');
        if (!imageHeader.querySelector('.history-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'history-indicator';
            indicator.style.cssText = 'color: #f39c12; font-size: 0.8rem; font-weight: bold;';
            indicator.textContent = '📖 Modo Historial';
            imageHeader.appendChild(indicator);
        }
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        // Botón anterior: habilitado si hay historial disponible o podemos ir más atrás en el historial
        const canGoPrev = (this.historyIndex === -1 && this.taskHistory.length > 0) || 
                         (this.historyIndex >= 0 && this.historyIndex < this.taskHistory.length - 1);
        
        // Botón siguiente: habilitado si estamos en el historial
        const canGoNext = this.historyIndex >= 0;
        
        prevBtn.disabled = !canGoPrev;
        nextBtn.disabled = !canGoNext;
        
        // Debug para entender el estado
        console.log('Navigation state:', {
            historyIndex: this.historyIndex,
            historyLength: this.taskHistory.length,
            canGoPrev: canGoPrev,
            canGoNext: canGoNext
        });
        
        // Remover indicador de historial si estamos en tarea actual
        if (this.historyIndex === -1) {
            const indicator = document.querySelector('.history-indicator');
            if (indicator) {
                indicator.remove();
            }
        }
    }

    async submitAction(action) {
        if (!this.currentAnnotationId) return;
        
        // Si estamos en modo historial, no permitir cambios
        if (this.historyIndex >= 0) {
            this.uiManager.showError('No puedes modificar tareas del historial. Ve a la tarea actual primero.');
            return;
        }
        
        try {
            // Deshabilitar botones durante el procesamiento
            this.disableButtons(true);
            
            await APIService.submitAction(this.currentAnnotationId, action);
            
            // Actualizar inmediatamente el estado para mostrar confirmación visual
            if (this.currentTask) {
                this.currentTask.status = action;
                this.updateUI(); // Mostrar el cambio de estado inmediatamente
                
                // Mostrar mensaje de confirmación apropiado
                if (action === 'discarded') {
                    this.showSuccessMessage('🗑️ Imagen descartada exitosamente');
                } else if (action === 'approved') {
                    this.showSuccessMessage('✓ Imagen aprobada exitosamente');
                }
            }
            
            await this.updateStats();
            
            // Efecto de parpadeo más dramático (como en la versión original)
            const mainArea = document.querySelector('.main-work-area');
            mainArea.style.transition = 'opacity 0.1s ease-in-out';
            mainArea.style.opacity = '0.2';
            
            setTimeout(async () => {
                mainArea.style.opacity = '1';
                
                // Actualizar historial para incluir la tarea recién completada
                await this.loadTaskHistory();
                
                await this.loadCurrentTask();
                await this.updatePendingPreview();
                this.disableButtons(false);
            }, 150);
            
        } catch (error) {
            console.error('Error submitting action:', error);
            this.uiManager.showError('Error procesando acción');
            this.disableButtons(false);
        }
    }

    disableButtons(disabled) {
        const buttons = ['correctBtn', 'editBtn', 'discardBtn'];
        buttons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.disabled = disabled;
                button.style.opacity = disabled ? '0.6' : '1';
                button.style.cursor = disabled ? 'not-allowed' : 'pointer';
            }
        });
    }

    toggleEditMode() {
        if (!this.currentTask) return;
        
        // Usar el texto corregido si existe, sino el OCR original
        const textToEdit = this.currentTask.corrected_text || this.currentTask.initial_ocr_text;
        this.editModeManager.toggleEditMode(textToEdit);
    }

    async saveEdit() {
        const newTranscription = this.editModeManager.getEditedText();
        
        if (!newTranscription) {
            this.uiManager.showError('Por favor, ingresa el texto corregido');
            return;
        }
        
        try {
            // Deshabilitar botones durante el procesamiento
            this.disableButtons(true);
            
            await APIService.submitAction(this.currentAnnotationId, 'corrected', newTranscription);
            this.editModeManager.cancelEdit();
            
            // Actualizar inmediatamente la tarea actual con el texto corregido para mostrar confirmación visual
            if (this.currentTask) {
                this.currentTask.corrected_text = newTranscription;
                this.currentTask.status = 'corrected'; // Asegurar que el estado sea corrected
                this.updateUI(); // Mostrar el texto corregido inmediatamente
                
                // Mostrar mensaje de confirmación temporal
                this.showSuccessMessage('✓ Corrección guardada exitosamente');
            }
            
            await this.updateStats();
            
            // Efecto de parpadeo
            const mainArea = document.querySelector('.main-work-area');
            mainArea.style.transition = 'opacity 0.1s ease-in-out';
            mainArea.style.opacity = '0.2';
            
            setTimeout(async () => {
                mainArea.style.opacity = '1';
                
                // Actualizar historial
                await this.loadTaskHistory();
                
                await this.loadCurrentTask();
                await this.updatePendingPreview();
                this.disableButtons(false);
            }, 150);
            
        } catch (error) {
            console.error('Error saving edit:', error);
            this.uiManager.showError('Error guardando corrección');
            this.disableButtons(false);
        }
    }

    cancelEdit() {
        this.editModeManager.cancelEdit();
    }

    async logout() {
        try {
            const success = await APIService.logout();
            // Los tokens ya se limpian en APIService.logout()
            window.location.href = '/login';
        } catch (error) {
            console.error('Error logging out:', error);
            // Limpiar tokens localmente en caso de error
            JWTService.clearTokens();
            window.location.href = '/login';
        }
    }

    showSuccessMessage(message) {
        // Crear o reutilizar el div de mensaje de éxito
        let successDiv = document.getElementById('successDiv');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'successDiv';
            successDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                z-index: 1001;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                transform: translateX(100%);
                transition: transform 0.3s ease-in-out;
            `;
            document.body.appendChild(successDiv);
        }
        
        successDiv.textContent = message;
        successDiv.classList.remove('hidden');
        
        // Animación de entrada
        requestAnimationFrame(() => {
            successDiv.style.transform = 'translateX(0)';
        });
        
        // Ocultar después de 2 segundos
        setTimeout(() => {
            successDiv.style.transform = 'translateX(100%)';
            setTimeout(() => {
                successDiv.classList.add('hidden');
            }, 300);
        }, 2000);
    }
}

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

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación primero, luego inicializar la aplicación
    if (checkJWTAuth()) {
        window.appController = new AppController();
    }
    // Si checkJWTAuth() retorna false, ya redirigió a login
});
