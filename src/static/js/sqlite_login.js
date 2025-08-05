// JavaScript para la página de login con JWT Auth

// ========== FUNCIONES DE AUTENTICACIÓN ==========

// Función para limpiar autenticación
function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_user');
    // Limpiar cookie
    document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
}

// Verificar si ya está logueado
function checkExistingAuth() {
    const accessToken = localStorage.getItem('access_token');
    const currentUser = localStorage.getItem('current_user');
    
    if (accessToken && currentUser) {
        try {
            const user = JSON.parse(currentUser);
            console.log('Usuario ya autenticado, redirigiendo...');
            
            // Redirigir según el rol
            if (user.role === 'admin') {
                window.location.href = '/admin';
            } else {
                window.location.href = '/';
            }
        } catch (error) {
            // Si hay error parseando, limpiar tokens y cookies
            clearAuth();
        }
    }
}

// ========== MANEJO DEL FORMULARIO DE LOGIN ==========

// Manejar el envío del formulario de login
async function handleLoginForm(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('login-btn');
    const errorDiv = document.getElementById('error-message');
    const successDiv = document.getElementById('success-message');
    
    // Limpiar mensajes anteriores
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    // Deshabilitar botón
    loginBtn.disabled = true;
    loginBtn.textContent = 'Iniciando sesión...';
    
    try {
        const response = await fetch('/api/v2/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Guardar tokens JWT en localStorage
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('current_user', JSON.stringify(data.user));
            
            // TAMBIÉN guardar token en cookie para autenticación de páginas
            document.cookie = `access_token=${data.access_token}; path=/; max-age=${data.expires_in}; SameSite=Strict`;
            
            successDiv.textContent = 'Inicio de sesión exitoso. Redirigiendo...';
            successDiv.style.display = 'block';
            
            // Redirigir según el rol
            setTimeout(() => {
                if (data.user.role === 'admin') {
                    window.location.href = '/admin';
                } else {
                    window.location.href = '/';
                }
            }, 1000);
        } else {
            errorDiv.textContent = data.error || 'Error en el inicio de sesión';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Error de conexión. Inténtalo de nuevo.';
        errorDiv.style.display = 'block';
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Iniciar Sesión';
    }
}

// ========== INICIALIZACIÓN ==========

// Inicializar la página de login cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si ya está autenticado
    checkExistingAuth();
    
    // Configurar el formulario de login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginForm);
    }
});
