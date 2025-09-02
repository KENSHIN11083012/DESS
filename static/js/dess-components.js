/**
 * DESS Components JavaScript
 * Sistema de componentes interactivos para DESS
 */

// === DESS MODAL SYSTEM ===
const DESSModals = {
  // Abrir modal
  open: (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
      
      // Evento para cerrar con ESC
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          DESSModals.close(modalId);
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);
    }
  },

  // Cerrar modal
  close: (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = 'auto';
    }
  },

  // Confirmar acción
  confirm: (options) => {
    const modalId = 'dess-confirm-modal';
    
    // Crear modal de confirmación si no existe
    if (!document.getElementById(modalId)) {
      const modalHTML = `
        <div id="${modalId}" class="dess-modal-overlay">
          <div class="dess-modal" style="max-width: 400px;">
            <div class="dess-modal-header">
              <h4 class="dess-modal-title">Confirmar acción</h4>
            </div>
            <div class="dess-modal-body">
              <p id="dess-confirm-message">¿Estás seguro de realizar esta acción?</p>
            </div>
            <div class="dess-modal-footer">
              <button type="button" class="dess-btn dess-btn-outline" onclick="DESSModals.close('${modalId}')">
                Cancelar
              </button>
              <button type="button" class="dess-btn dess-btn-primary" id="dess-confirm-btn">
                Confirmar
              </button>
            </div>
          </div>
        </div>
      `;
      document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // Configurar mensaje y callback
    document.getElementById('dess-confirm-message').textContent = options.message || '¿Estás seguro?';
    document.getElementById('dess-confirm-btn').onclick = () => {
      DESSModals.close(modalId);
      if (options.onConfirm) options.onConfirm();
    };

    DESSModals.open(modalId);
  }
};

// === DESS NOTIFICATIONS ===
const DESSNotifications = {
  show: (message, type = 'info', duration = 5000) => {
    const notification = document.createElement('div');
    notification.className = `dess-notification dess-notification-${type}`;
    notification.innerHTML = `
      <div class="dess-notification-content">
        <span class="dess-notification-message">${message}</span>
        <button class="dess-notification-close" onclick="this.parentElement.parentElement.remove()">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    `;

    // Estilos inline para las notificaciones
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      background: white;
      border-radius: 8px;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
      padding: 16px;
      min-width: 300px;
      border-left: 4px solid var(--dess-${type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'});
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Animación de entrada
    requestAnimationFrame(() => {
      notification.style.transform = 'translateX(0)';
    });

    // Auto-remove
    if (duration > 0) {
      setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
      }, duration);
    }
  },

  success: (message, duration = 5000) => DESSNotifications.show(message, 'success', duration),
  error: (message, duration = 7000) => DESSNotifications.show(message, 'error', duration),
  warning: (message, duration = 6000) => DESSNotifications.show(message, 'warning', duration),
  info: (message, duration = 5000) => DESSNotifications.show(message, 'info', duration)
};

// === DESS FORMS ===
const DESSForms = {
  validate: (formId) => {
    const form = document.getElementById(formId);
    if (!form) return false;

    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');

    inputs.forEach(input => {
      DESSForms.clearError(input);
      
      if (!input.value.trim()) {
        DESSForms.showError(input, 'Este campo es obligatorio');
        isValid = false;
      } else if (input.type === 'email' && !DESSForms.isValidEmail(input.value)) {
        DESSForms.showError(input, 'Por favor ingresa un email válido');
        isValid = false;
      }
    });

    return isValid;
  },

  showError: (input, message) => {
    input.classList.add('error');
    
    let errorElement = input.parentElement.querySelector('.dess-form-error');
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'dess-form-error';
      errorElement.style.cssText = 'color: var(--dess-error); font-size: 0.875rem; margin-top: 0.25rem;';
      input.parentElement.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
  },

  clearError: (input) => {
    input.classList.remove('error');
    const errorElement = input.parentElement.querySelector('.dess-form-error');
    if (errorElement) {
      errorElement.remove();
    }
  },

  isValidEmail: (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
};

// === DESS TABLES ===
const DESSTables = {
  sort: (tableId, columnIndex, type = 'string') => {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
      const aValue = a.cells[columnIndex].textContent.trim();
      const bValue = b.cells[columnIndex].textContent.trim();

      if (type === 'number') {
        return parseFloat(aValue) - parseFloat(bValue);
      } else if (type === 'date') {
        return new Date(aValue) - new Date(bValue);
      } else {
        return aValue.localeCompare(bValue);
      }
    });

    rows.forEach(row => tbody.appendChild(row));
  },

  filter: (tableId, searchTerm) => {
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');
    const searchLower = searchTerm.toLowerCase();

    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(searchLower) ? '' : 'none';
    });
  }
};

// === DESS LOADING ===
const DESSLoading = {
  show: (target = 'body') => {
    const container = typeof target === 'string' ? document.querySelector(target) : target;
    if (!container) return;

    const loader = document.createElement('div');
    loader.className = 'dess-loader';
    loader.innerHTML = `
      <div class="dess-spinner">
        <div class="dess-spinner-circle"></div>
      </div>
    `;
    
    loader.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    `;

    container.style.position = container.style.position || 'relative';
    container.appendChild(loader);
  },

  hide: (target = 'body') => {
    const container = typeof target === 'string' ? document.querySelector(target) : target;
    if (!container) return;

    const loader = container.querySelector('.dess-loader');
    if (loader) {
      loader.remove();
    }
  }
};

// === GLOBAL FUNCTIONS ===
window.openModal = (modalId) => DESSModals.open(modalId);
window.closeModal = (modalId) => DESSModals.close(modalId);
window.showNotification = (message, type, duration) => DESSNotifications.show(message, type, duration);

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function() {
  // Auto-cerrar modales al hacer click fuera
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('dess-modal-overlay')) {
      e.target.classList.remove('active');
      document.body.style.overflow = 'auto';
    }
  });

  // Auto-validación de formularios
  document.querySelectorAll('form[data-dess-validate]').forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!DESSForms.validate(form.id)) {
        e.preventDefault();
      }
    });
  });

  console.log('🎯 DESS Components initialized successfully');
});

// === CSS STYLES FOR COMPONENTS ===
const styles = `
  .dess-notification {
    animation: slideIn 0.3s ease;
  }
  
  @keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
  }
  
  .dess-notification-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  
  .dess-notification-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--dess-gray-400);
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;
  }
  
  .dess-notification-close:hover {
    color: var(--dess-gray-600);
    background: var(--dess-gray-100);
  }
  
  .dess-spinner-circle {
    width: 40px;
    height: 40px;
    border: 4px solid var(--dess-gray-200);
    border-top: 4px solid var(--dess-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// Inyectar estilos
const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

// Exportar para uso modular
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    DESSModals,
    DESSNotifications,
    DESSForms,
    DESSTables,
    DESSLoading
  };
}