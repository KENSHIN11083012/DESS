/**
 * DESS User Solutions JavaScript
 * Funcionalidades para la vista de soluciones del usuario
 */

// Configurar filtrado dinámico
function setupDynamicFiltering() {
    const searchInput = document.querySelector('input[name="search"]');
    const typeSelect = document.querySelector('select[name="type"]');
    const statusSelect = document.querySelector('select[name="status"]');
    const form = document.querySelector('form');
    const searchBtn = document.getElementById('searchBtn');
    const searchIcon = document.getElementById('searchIcon');
    const searchText = document.getElementById('searchText');
    
    // Función para mostrar estado de carga en el formulario
    function showFormLoading() {
        if (searchBtn && searchIcon && searchText) {
            searchBtn.disabled = true;
            searchBtn.classList.add('opacity-75');
            searchIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>';
            searchIcon.classList.add('loading-spinner');
            searchText.textContent = 'Buscando...';
        }
    }
    
    // Auto-submit en cambio de selects con indicador de carga
    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            showFormLoading();
            form.submit();
        });
    }
    
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            showFormLoading();
            form.submit();
        });
    }
    
    // Debounced search para evitar demasiadas peticiones
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                showFormLoading();
                form.submit();
            }, 800); // Esperar 800ms después de que el usuario pare de escribir
        });
        
        // Permitir búsqueda instantánea con Enter
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(searchTimeout);
                showFormLoading();
                form.submit();
            }
        });
    }
    
    // Submit del formulario con indicador de carga
    if (form) {
        form.addEventListener('submit', function() {
            showFormLoading();
        });
    }
}

// Función para alternar favoritos
function toggleFavorite(solutionId) {
    const btn = event.target.closest('.favorite-btn');
    
    // Obtener token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Llamada AJAX al endpoint
    fetch('/api/user/toggle-favorite/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
        },
        body: `solution_id=${solutionId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar UI basado en la respuesta
            const svg = btn.querySelector('svg');
            if (data.is_favorite) {
                btn.classList.add('active');
                svg.setAttribute('fill', 'currentColor');
                btn.setAttribute('title', 'Remover de favoritos');
            } else {
                btn.classList.remove('active');
                svg.setAttribute('fill', 'none');
                btn.setAttribute('title', 'Agregar a favoritos');
            }
            
            // Mostrar mensaje temporal usando la función personalizada
            showTemporaryMessage(data.message, 'success');
        } else {
            showTemporaryMessage('Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTemporaryMessage('Error al procesar la solicitud', 'error');
    });
}

// Configurar cambio de elementos por página
function setupPaginationSettings() {
    const itemsPerPageSelect = document.getElementById('itemsPerPageSelect');
    
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            
            // Obtener token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Mostrar mensaje de carga
            showTemporaryMessage('Actualizando configuración...', 'info');
            
            // Llamada AJAX para actualizar preferencias
            fetch('/api/user/update-pagination/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: `items_per_page=${selectedValue}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Recargar la página con la primera página para aplicar el cambio
                    const url = new URL(window.location);
                    url.searchParams.set('page', '1'); // Ir a la primera página
                    window.location = url.toString();
                } else {
                    showTemporaryMessage('Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showTemporaryMessage('Error al actualizar configuración de paginación', 'error');
            });
        });
    }
}

// Configurar loading states para paginación
function setupPaginationLoading() {
    const paginationLinks = document.querySelectorAll('a[href*="page="]');
    
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Agregar clase de loading a todos los enlaces
            paginationLinks.forEach(l => l.classList.add('pagination-loading'));
            
            // Mostrar mensaje de carga temporal
            showTemporaryMessage('Cargando página...', 'info');
        });
    });
}

// Configurar tooltips para botones de estado
function setupTooltips() {
    const buttons = document.querySelectorAll('[title]');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded shadow-lg opacity-0 transition-opacity duration-200';
            tooltip.textContent = this.getAttribute('title');
            tooltip.id = 'tooltip-' + Math.random().toString(36).substr(2, 9);
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.bottom + 5 + 'px';
            
            setTimeout(() => tooltip.classList.remove('opacity-0'), 100);
            
            this.addEventListener('mouseleave', function() {
                if (document.getElementById(tooltip.id)) {
                    tooltip.classList.add('opacity-0');
                    setTimeout(() => {
                        if (document.body.contains(tooltip)) {
                            document.body.removeChild(tooltip);
                        }
                    }, 200);
                }
            }, { once: true });
        });
    });
}

// Función para mostrar un mensaje temporal
function showTemporaryMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    let bgColor;
    
    switch(type) {
        case 'success':
            bgColor = 'bg-green-500';
            break;
        case 'error':
            bgColor = 'bg-red-500';
            break;
        case 'info':
            bgColor = 'bg-blue-500';
            break;
        default:
            bgColor = 'bg-gray-500';
    }
    
    messageDiv.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded-md shadow-lg z-50 transform transition-all duration-300 opacity-0 translate-x-full`;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    // Animación de entrada
    setTimeout(() => {
        messageDiv.classList.remove('opacity-0', 'translate-x-full');
    }, 100);
    
    // Remover mensaje después de 3 segundos
    setTimeout(() => {
        messageDiv.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => {
            if (document.body.contains(messageDiv)) {
                document.body.removeChild(messageDiv);
            }
        }, 300);
    }, 3000);
}

// Modal de información de solución
function showSolutionInfo(solutionId, solutionName) {
    const modal = document.getElementById('solutionInfoModal');
    const title = document.getElementById('solutionInfoTitle');
    const content = document.getElementById('solutionInfoContent');
    
    title.textContent = solutionName;
    content.innerHTML = `
        <div class="space-y-3">
            <div class="flex items-center text-sm">
                <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="font-medium">ID de Solución:</span> ${solutionId}
            </div>
            <div class="flex items-center text-sm">
                <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <span class="font-medium">Estado:</span> Disponible para uso
            </div>
            <div class="flex items-center text-sm">
                <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3a4 4 0 118 0v4m-4 12a4 4 0 100-8 4 4 0 000 8z"></path>
                </svg>
                <span class="font-medium">Acceso:</span> Autorizado para tu cuenta
            </div>
            <div class="mt-4 p-3 bg-blue-50 rounded-lg">
                <p class="text-sm text-blue-800">
                    <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Si tienes problemas para acceder a esta solución, contacta a tu administrador.
                </p>
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

function closeSolutionInfo() {
    const modal = document.getElementById('solutionInfoModal');
    modal.classList.add('hidden');
}

// Cerrar modal al hacer clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('solutionInfoModal');
    if (event.target == modal) {
        modal.classList.add('hidden');
    }
}

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    setupDynamicFiltering();
    setupPaginationSettings();
    setupPaginationLoading();
    setupTooltips();
    console.log('DESS User Solutions: Filtrado dinámico, paginación personalizable y UX mejorado cargados correctamente');
});