// JavaScript para el panel de administración con JWT Auth

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
        
        // Verificar que sea admin
        if (user.role !== 'admin') {
            console.log('Usuario no es admin, redirigiendo');
            window.location.href = '/';
            return false;
        }
        
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

// ========== CLASES PRINCIPALES ==========

// Importar servicios JWT del archivo principal
// (En un entorno de producción usaríamos módulos ES6)

class AdminPanel {
    constructor() {
        this.checkAuthentication();
        this.init();
    }

    checkAuthentication() {
        // La verificación principal ya se hizo en checkJWTAuth()
        // Solo verificamos que tengamos token para las requests
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
    }

    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async makeRequest(url, options = {}) {
        options.headers = {
            ...options.headers,
            ...this.getAuthHeaders()
        };

        let response = await fetch(url, options);

        // Si el token expiró, intentar renovarlo
        if (response.status === 401) {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const refreshResponse = await fetch('/api/v2/refresh', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refresh_token: refreshToken })
                    });

                    if (refreshResponse.ok) {
                        const data = await refreshResponse.json();
                        localStorage.setItem('access_token', data.access_token);
                        if (data.refresh_token) {
                            localStorage.setItem('refresh_token', data.refresh_token);
                        }

                        // Reintentar la request original
                        options.headers = {
                            ...options.headers,
                            ...this.getAuthHeaders()
                        };
                        response = await fetch(url, options);
                    } else {
                        window.location.href = '/login';
                        return;
                    }
                } catch (error) {
                    window.location.href = '/login';
                    return;
                }
            } else {
                window.location.href = '/login';
                return;
            }
        }

        return response;
    }

    async init() {
        await this.loadGeneralStats();
        await this.loadRecentActivity();
        await this.loadUsers();
        await this.loadImages();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Form para crear usuario
        document.getElementById('create-user-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createUser();
        });
    }

    async loadGeneralStats() {
        try {
            const response = await this.makeRequest('/api/v2/admin/stats');
            if (response && response.ok) {
                const stats = await response.json();
                // Limpiar cualquier barra de progreso existente
                const existingProgress = document.querySelector('.progress-section');
                if (existingProgress) {
                    existingProgress.remove();
                }
                this.displayGeneralStats(stats);
            }
        } catch (error) {
            console.error('Error loading general stats:', error);
        }
    }

    displayGeneralStats(stats) {
        const statsContainer = document.getElementById('general-stats');
        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-number">${stats.total_users}</div>
                <div class="stat-label">Usuarios</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.total_images}</div>
                <div class="stat-label">Imágenes Totales</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.total_annotations}</div>
                <div class="stat-label">Anotaciones Asignadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.pending_tasks}</div>
                <div class="stat-label">Tareas Pendientes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.completed_tasks}</div>
                <div class="stat-label">Tareas Completadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${stats.unannotated_images}</div>
                <div class="stat-label">Imágenes Sin Anotar</div>
            </div>
        `;
        
        // Agregar barra de progreso después de las estadísticas
        const progressSection = document.createElement('div');
        progressSection.className = 'progress-section';
        progressSection.innerHTML = `
            <div class="progress-header">
                <h3>Progreso de Anotación</h3>
                <span class="progress-text">${stats.annotated_images} de ${stats.total_images} imágenes anotadas (${stats.progress_percentage}%)</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${stats.progress_percentage}%">
                    <span class="progress-percentage">${stats.progress_percentage}%</span>
                </div>
            </div>
        `;
        
        // Insertar la barra de progreso después del contenedor de estadísticas
        statsContainer.parentNode.insertBefore(progressSection, statsContainer.nextSibling);
    }

    async loadUsers() {
        try {
            const response = await this.makeRequest('/api/v2/admin/users');
            if (response && response.ok) {
                const data = await response.json();
                this.displayUsers(data.users);
                this.displayUsersForAssignment(data.users);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    displayUsers(users) {
        const tbody = document.querySelector('#users-table tbody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td><span class="status-badge ${user.role === 'admin' ? 'status-approved' : 'status-pending'}">${user.role}</span></td>
                <td>-</td>
                <td>-</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="viewUserStats(${user.id})">Ver Stats</button>
                </td>
            </tr>
        `).join('');
    }

    displayUsersForAssignment(users) {
        const container = document.getElementById('assignment-users');
        // Filtrar solo anotadores para asignaciones
        const annotators = users.filter(user => user.role === 'annotator');
        
        container.innerHTML = annotators.map(user => `
            <div class="checkbox-item">
                <input type="checkbox" id="user-${user.id}" value="${user.id}">
                <label for="user-${user.id}">${user.username}</label>
            </div>
        `).join('');
        
        // También popular el select de asignación automática
        const autoSelect = document.getElementById('auto-user-select');
        autoSelect.innerHTML = '<option value="">Seleccionar usuario...</option>' +
            annotators.map(user => `
                <option value="${user.id}">${user.username}</option>
            `).join('');
    }

    async loadImages() {
        try {
            const response = await this.makeRequest('/api/v2/admin/images');
            if (response && response.ok) {
                const data = await response.json();
                this.displayImages(data.images);
                this.displayImagesForAssignment(data.images);
            }
        } catch (error) {
            console.error('Error loading images:', error);
        }
    }

    displayImages(images) {
        const tbody = document.querySelector('#images-table tbody');
        // Mostrar solo las primeras 100 imágenes para no sobrecargar la interfaz
        const displayImages = images.slice(0, 100);
        
        tbody.innerHTML = displayImages.map(image => `
            <tr>
                <td>${image.id}</td>
                <td title="${image.image_path}">${image.image_path.length > 30 ? 
                    image.image_path.substring(0, 30) + '...' : image.image_path}</td>
                <td title="${image.initial_ocr_text}">${image.initial_ocr_text.length > 50 ? 
                    image.initial_ocr_text.substring(0, 50) + '...' : image.initial_ocr_text}</td>
                <td>-</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="viewImageAnnotations(${image.id})">Ver Anotaciones</button>
                </td>
            </tr>
        `).join('');
    }

    displayImagesForAssignment(images) {
        const container = document.getElementById('assignment-images');
        // Mostrar solo las primeras 50 imágenes para asignación manual
        const displayImages = images.slice(0, 50);
        
        container.innerHTML = displayImages.map(image => `
            <div class="checkbox-item">
                <input type="checkbox" id="image-${image.id}" value="${image.id}">
                <label for="image-${image.id}" title="${image.image_path}">
                    ${image.image_path.length > 40 ? 
                        image.image_path.substring(0, 40) + '...' : image.image_path}
                </label>
            </div>
        `).join('');
    }

    async createUser() {
        const username = document.getElementById('new-username').value;
        const password = document.getElementById('new-password').value;
        const role = document.getElementById('new-role').value;

        try {
            const response = await this.makeRequest('/api/v2/admin/users', {
                method: 'POST',
                body: JSON.stringify({ username, password, role })
            });

            if (response && response.ok) {
                alert('Usuario creado correctamente');
                this.closeModal('create-user-modal');
                await this.loadUsers();
                // Limpiar formulario
                document.getElementById('create-user-form').reset();
            } else {
                const error = await response.json();
                alert(error.error || 'Error creando usuario');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            alert('Error de conexión');
        }
    }

    async createAssignments() {
        const selectedUsers = Array.from(document.querySelectorAll('#assignment-users input:checked'))
            .map(input => parseInt(input.value));
        
        const selectedImages = Array.from(document.querySelectorAll('#assignment-images input:checked'))
            .map(input => parseInt(input.value));

        if (selectedUsers.length === 0) {
            alert('Por favor selecciona al menos un usuario');
            return;
        }

        if (selectedImages.length === 0) {
            alert('Por favor selecciona al menos una imagen');
            return;
        }

        try {
            const response = await this.makeRequest('/api/v2/admin/assignments', {
                method: 'POST',
                body: JSON.stringify({
                    user_ids: selectedUsers,
                    image_ids: selectedImages
                })
            });

            if (response && response.ok) {
                const result = await response.json();
                const resultDiv = document.getElementById('assignment-result');
                resultDiv.innerHTML = `
                    <div class="message success">
                        Se crearon ${result.assignments_created} asignaciones correctamente
                    </div>
                `;
                
                // Limpiar selecciones
                document.querySelectorAll('#assignment-users input:checked, #assignment-images input:checked')
                    .forEach(input => input.checked = false);
                
                // Actualizar stats
                await this.loadGeneralStats();
            } else {
                const error = await response.json();
                alert(error.error || 'Error creando asignaciones');
            }
        } catch (error) {
            console.error('Error creating assignments:', error);
            alert('Error de conexión');
        }
    }

    async createAutoAssignments() {
        const userId = document.getElementById('auto-user-select').value;
        const count = parseInt(document.getElementById('auto-count').value);
        const priorityUnannotated = document.querySelector('input[name="priority"]:checked').value === 'unannotated';
        
        if (!userId) {
            alert('Por favor selecciona un usuario');
            return;
        }

        if (!count || count <= 0) {
            alert('Por favor ingresa un número válido de imágenes');
            return;
        }

        try {
            const response = await this.makeRequest('/api/v2/admin/assignments/auto', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: parseInt(userId),
                    count: count,
                    priority_unannotated: priorityUnannotated
                })
            });

            if (response && response.ok) {
                const result = await response.json();
                const resultDiv = document.getElementById('auto-assignment-result');
                resultDiv.innerHTML = `
                    <div class="message success">
                        ${result.message}.
                    </div>
                `;
                
                // Limpiar formulario
                document.getElementById('auto-user-select').value = '';
                document.getElementById('auto-count').value = '10';
                document.querySelector('input[name="priority"][value="unannotated"]').checked = true;
                
                // Actualizar stats
                await this.loadGeneralStats();
            } else {
                const error = await response.json();
                const resultDiv = document.getElementById('auto-assignment-result');
                resultDiv.innerHTML = `
                    <div class="message error">
                        Error: ${error.error}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error creating auto assignments:', error);
            const resultDiv = document.getElementById('auto-assignment-result');
            resultDiv.innerHTML = `
                <div class="message error">
                    Error de conexión
                </div>
            `;
        }
    }

    async loadRecentActivity() {
        try {
            const response = await this.makeRequest('/api/v2/admin/recent-activity?limit=6');
            if (response && response.ok) {
                const data = await response.json();
                this.displayRecentActivity(data.recent_activity);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    displayRecentActivity(activity) {
        const activityContainer = document.getElementById('recent-activity');
        
        if (!activity || activity.length === 0) {
            activityContainer.innerHTML = `
                <div class="activity-empty">
                    <p>No hay actividad reciente</p>
                </div>
            `;
            return;
        }

        const activityHTML = activity.map(user => {
            const lastActivity = new Date(user.last_activity);
            const formattedDate = lastActivity.toLocaleDateString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            const formattedTime = lastActivity.toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const completionRate = user.total_assigned > 0 
                ? Math.round((user.completed / user.total_assigned) * 100) 
                : 0;

            return `
                <div class="activity-item">
                    <div class="activity-user">
                        <div class="user-name">${user.username}</div>
                        <div class="activity-date">${formattedDate} a las ${formattedTime}</div>
                    </div>
                    <div class="activity-stats">
                        <div class="stat-item">
                            <span class="stat-number">${user.total_assigned}</span>
                            <span class="stat-label">Asignadas</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${user.completed}</span>
                            <span class="stat-label">Revisadas</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${user.approved} (${user.approved_pct}%)</span>
                            <span class="stat-label">Aprobadas</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number stat-corrected">${user.corrected} (${user.corrected_pct}%)</span>
                            <span class="stat-label">Corregidas</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number stat-discarded">${user.discarded} (${user.discarded_pct}%)</span>
                            <span class="stat-label">Descartadas</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${completionRate}%</span>
                            <span class="stat-label">Progreso</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        activityContainer.innerHTML = activityHTML;
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }
}

// Instanciar el panel de administración
let adminPanel;

// Verificar autenticación al cargar la página y luego inicializar
document.addEventListener('DOMContentLoaded', function() {
    if (checkJWTAuth()) {
        adminPanel = new AdminPanel();
    }
    // Si checkJWTAuth() retorna false, ya redirigió a login
});

// Funciones globales
function showTab(tabName) {
    // Ocultar todas las tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remover clase active de todos los botones
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar tab seleccionada
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Activar botón correspondiente
    event.target.classList.add('active');
}

function showCreateUserModal() {
    document.getElementById('create-user-modal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

async function createAssignments() {
    await adminPanel.createAssignments();
}

async function createAutoAssignments() {
    await adminPanel.createAutoAssignments();
}

async function viewUserStats(userId) {
    // TODO: Implementar vista de estadísticas de usuario
    alert(`Ver estadísticas del usuario ${userId} (por implementar)`);
}

async function viewImageAnnotations(imageId) {
    try {
        const response = await adminPanel.makeRequest(`/api/v2/admin/images/${imageId}/annotations`);
        if (response && response.ok) {
            const data = await response.json();
            // TODO: Mostrar modal con anotaciones
            console.log('Anotaciones para imagen', imageId, data);
            alert(`Imagen ${imageId} tiene ${data.annotations.length} anotaciones`);
        }
    } catch (error) {
        console.error('Error loading image annotations:', error);
    }
}

async function logout() {
    try {
        const token = localStorage.getItem('access_token');
        if (token) {
            await fetch('/api/v2/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        }
        
        // Limpiar tokens locales usando la función centralizada
        clearAuth();
        
        window.location.href = '/login';
    } catch (error) {
        console.error('Error logging out:', error);
        // Limpiar tokens locales en caso de error
        clearAuth();
        window.location.href = '/login';
    }
}

// Función para ir a anotar (permite al admin anotar como usuario regular)
function goToAnnotation() {
    window.location.href = '/';
}

// Cerrar modales al hacer click fuera de ellos
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});
