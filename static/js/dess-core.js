/**
 * DESS Core JavaScript - Funciones Unificadas
 * Eliminación de redundancias en JavaScript
 */

// Configuración global DESS (será sobrescrita por el template)
window.DESS = window.DESS || {
    apiUrl: '/api/',
    csrfToken: '',
    user: {
        id: null,
        username: '',
        isSuperAdmin: false
    },
    // Constantes para evitar magic numbers
    constants: {
        NOTIFICATION_DURATION: 3000,
        ALERT_AUTO_HIDE_DURATION: 5000,
        MODAL_TRANSITION_DURATION: 300,
        AJAX_TIMEOUT: 10000,
        SEARCH_DEBOUNCE_DELAY: 500,
        MIN_USERNAME_LENGTH: 3,
        MIN_PASSWORD_LENGTH: 8,
        MAX_FILE_SIZE_MB: 10
    }
};

// ============================================================================
// UTILIDADES GENERALES
// ============================================================================

/**
 * Confirmar acción con el usuario
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
    }
}

/**
 * Establecer estado de carga en botón
 */
function setButtonLoading(button, loading = true) {
    if (!button) return;
    
    if (loading) {
        // Guardar texto original
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        button.classList.add('dess-loading');
    } else {
        button.disabled = false;
        // Restaurar texto original
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
        button.classList.remove('dess-loading');
    }
}

/**
 * Mostrar notificación toast
 */
function showNotification(message, type = 'info', duration = window.DESS.constants.NOTIFICATION_DURATION) {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `dess-notification dess-notification-${type}`;
    notification.innerHTML = `
        <div class="dess-notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="dess-notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Añadir al DOM
    document.body.appendChild(notification);
    
    // Auto-remover después del tiempo especificado
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('dess-notification-fadeout');
            setTimeout(() => notification.remove(), window.DESS.constants.MODAL_TRANSITION_DURATION);
        }
    }, duration);
}

/**
 * Hacer petición AJAX con CSRF
 */
async function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.DESS.csrfToken || ''
        },
        timeout: window.DESS.constants.AJAX_TIMEOUT
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('AJAX Error:', error);
        showNotification('Error en la comunicación con el servidor', 'error');
        throw error;
    }
}

/**
 * Validar formulario genérico
 */
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Formatear números
 */
function formatNumber(num, decimals = 0) {
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

/**
 * Formatear fechas
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('es-ES', { ...defaultOptions, ...options }).format(new Date(date));
}

// ============================================================================
// FUNCIONES ESPECÍFICAS DEL DASHBOARD
// ============================================================================

/**
 * Actualizar métricas del sistema
 */
function refreshSystemMetrics() {
    const btn = event.target.closest('button');
    if (!btn) return;
    
    const icon = btn.querySelector('i');
    
    setButtonLoading(btn, true);
    if (icon) icon.classList.add('fa-spin');
    
    // Simular llamada AJAX - en producción usar ajaxRequest()
    setTimeout(() => {
        setButtonLoading(btn, false);
        if (icon) icon.classList.remove('fa-spin');
        showNotification('Métricas del sistema actualizadas correctamente', 'success');
    }, window.DESS.constants.NOTIFICATION_DURATION / 2);
}

/**
 * Exportar datos
 */
function exportData(type = 'excel') {
    showNotification(`Preparando exportación en formato ${type.toUpperCase()}...`, 'info');
    
    // Aquí iría la lógica real de exportación
    setTimeout(() => {
        showNotification('Exportación completada', 'success');
    }, window.DESS.constants.NOTIFICATION_DURATION - 1000);
}

/**
 * Filtrar tabla/grid
 */
function filterResults(searchTerm, targetSelector) {
    const items = document.querySelectorAll(targetSelector);
    const normalizedSearch = searchTerm.toLowerCase().trim();
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const shouldShow = !normalizedSearch || text.includes(normalizedSearch);
        
        item.style.display = shouldShow ? '' : 'none';
        item.classList.toggle('dess-filtered-out', !shouldShow);
    });
}

// ============================================================================
// INICIALIZACIÓN AUTOMÁTICA
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Asegurar que la configuración DESS esté disponible
    if (!window.DESS) {
        console.warn('DESS configuration not found, using defaults');
        window.DESS = {
            apiUrl: '/api/',
            csrfToken: '',
            user: { id: null, username: '', isSuperAdmin: false }
        };
    }
    
    // Auto-ocultar alertas después del tiempo configurado
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert && alert.parentElement) {
                alert.classList.add('fade');
                setTimeout(() => alert.remove(), window.DESS.constants.MODAL_TRANSITION_DURATION + 200);
            }
        });
    }, window.DESS.constants.ALERT_AUTO_HIDE_DURATION);
    
    // Inicializar tooltips de Bootstrap si están disponibles
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    }
    
    // Inicializar formularios
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Por favor, complete todos los campos requeridos', 'warning');
            }
        });
    });
    
    // Inicializar filtros de búsqueda
    const searchInputs = document.querySelectorAll('[data-filter-target]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const target = this.dataset.filterTarget;
            filterResults(this.value, target);
        });
    });
    
    console.log('DESS Core JavaScript initialized successfully');
    
    // Debug de configuración en modo desarrollo
    if (window.DESS.user && window.DESS.user.isSuperAdmin) {
        console.log('DESS Config:', window.DESS);
    }
});

// ============================================================================
// COMPATIBILIDAD Y POLYFILLS
// ============================================================================

// Polyfill para navegadores antiguos
if (!Element.prototype.closest) {
    Element.prototype.closest = function(selector) {
        let element = this;
        while (element && element.nodeType === 1) {
            if (element.matches(selector)) {
                return element;
            }
            element = element.parentElement;
        }
        return null;
    };
}
