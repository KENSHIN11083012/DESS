/**
 * DESS Tutorial System
 * Sistema de tutorial guiado interactivo para usuarios
 */

class DESSTutorial {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.steps = [];
        this.overlay = null;
        this.tooltip = null;
        this.skipButton = null;
        this.nextButton = null;
        this.prevButton = null;
        this.progressBar = null;
        this.stepCounter = null;
        
        this.init();
    }

    init() {
        this.createTutorialElements();
        this.bindEvents();
    }

    createTutorialElements() {
        // Crear overlay oscuro
        this.overlay = document.createElement('div');
        this.overlay.id = 'dess-tutorial-overlay';
        this.overlay.className = 'dess-tutorial-overlay hidden';
        
        // Crear tooltip container
        this.tooltip = document.createElement('div');
        this.tooltip.id = 'dess-tutorial-tooltip';
        this.tooltip.className = 'dess-tutorial-tooltip';
        
        // Crear controles del tutorial
        this.tooltip.innerHTML = `
            <div class="dess-tutorial-content">
                <div class="dess-tutorial-header">
                    <div class="dess-tutorial-progress">
                        <div class="dess-tutorial-progress-bar" id="dess-progress-bar"></div>
                    </div>
                    <div class="dess-tutorial-step-counter" id="dess-step-counter">1 / 1</div>
                    <button class="dess-tutorial-close" id="dess-tutorial-close" title="Cerrar tutorial">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="dess-tutorial-body">
                    <h3 class="dess-tutorial-title" id="dess-tutorial-title"></h3>
                    <p class="dess-tutorial-description" id="dess-tutorial-description"></p>
                </div>
                <div class="dess-tutorial-footer">
                    <button class="dess-tutorial-btn dess-tutorial-skip" id="dess-tutorial-skip">
                        Saltar tutorial
                    </button>
                    <div class="dess-tutorial-navigation">
                        <button class="dess-tutorial-btn dess-tutorial-prev" id="dess-tutorial-prev">
                            Anterior
                        </button>
                        <button class="dess-tutorial-btn dess-tutorial-next dess-tutorial-primary" id="dess-tutorial-next">
                            Siguiente
                        </button>
                    </div>
                </div>
            </div>
            <div class="dess-tutorial-arrow" id="dess-tutorial-arrow"></div>
        `;

        // Agregar estilos CSS
        this.addStyles();
        
        // Agregar elementos al DOM
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.tooltip);
        
        // Referencias a elementos
        this.progressBar = document.getElementById('dess-progress-bar');
        this.stepCounter = document.getElementById('dess-step-counter');
        this.skipButton = document.getElementById('dess-tutorial-skip');
        this.nextButton = document.getElementById('dess-tutorial-next');
        this.prevButton = document.getElementById('dess-tutorial-prev');
    }

    addStyles() {
        if (document.getElementById('dess-tutorial-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'dess-tutorial-styles';
        styles.textContent = `
            .dess-tutorial-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9998;
                transition: opacity 0.3s ease;
            }
            
            .dess-tutorial-overlay.hidden {
                opacity: 0;
                pointer-events: none;
            }
            
            .dess-tutorial-tooltip {
                position: fixed;
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                z-index: 9999;
                max-width: 320px;
                min-width: 280px;
                opacity: 0;
                transform: scale(0.9);
                transition: all 0.3s ease;
                pointer-events: none;
            }
            
            .dess-tutorial-tooltip.show {
                opacity: 1;
                transform: scale(1);
                pointer-events: auto;
            }
            
            .dess-tutorial-content {
                padding: 0;
            }
            
            .dess-tutorial-header {
                display: flex;
                align-items: center;
                padding: 16px 16px 12px;
                border-bottom: 1px solid #e5e7eb;
                position: relative;
            }
            
            .dess-tutorial-progress {
                flex: 1;
                height: 4px;
                background: #e5e7eb;
                border-radius: 2px;
                margin-right: 12px;
                overflow: hidden;
            }
            
            .dess-tutorial-progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #4A9EE0, #1E3A5F);
                border-radius: 2px;
                transition: width 0.3s ease;
                width: 0%;
            }
            
            .dess-tutorial-step-counter {
                font-size: 12px;
                color: #6b7280;
                font-weight: 500;
                margin-right: 8px;
            }
            
            .dess-tutorial-close {
                background: none;
                border: none;
                cursor: pointer;
                color: #6b7280;
                padding: 4px;
                border-radius: 4px;
                transition: all 0.2s ease;
            }
            
            .dess-tutorial-close:hover {
                background: #f3f4f6;
                color: #374151;
            }
            
            .dess-tutorial-body {
                padding: 16px;
            }
            
            .dess-tutorial-title {
                font-size: 16px;
                font-weight: 600;
                color: #111827;
                margin: 0 0 8px 0;
                line-height: 1.4;
            }
            
            .dess-tutorial-description {
                font-size: 14px;
                color: #6b7280;
                margin: 0;
                line-height: 1.5;
            }
            
            .dess-tutorial-footer {
                padding: 12px 16px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .dess-tutorial-navigation {
                display: flex;
                gap: 8px;
            }
            
            .dess-tutorial-btn {
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .dess-tutorial-btn:hover {
                background: #f9fafb;
            }
            
            .dess-tutorial-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .dess-tutorial-primary {
                background: #4A9EE0 !important;
                color: white !important;
                border-color: #4A9EE0 !important;
            }
            
            .dess-tutorial-primary:hover {
                background: #3b8bd4 !important;
            }
            
            .dess-tutorial-skip {
                color: #6b7280;
                border: none;
                background: none;
                text-decoration: underline;
            }
            
            .dess-tutorial-skip:hover {
                color: #4b5563;
                background: none;
            }
            
            .dess-tutorial-arrow {
                position: absolute;
                width: 0;
                height: 0;
                border: 8px solid transparent;
            }
            
            .dess-tutorial-arrow.top {
                top: -16px;
                left: 50%;
                transform: translateX(-50%);
                border-bottom-color: white;
            }
            
            .dess-tutorial-arrow.bottom {
                bottom: -16px;
                left: 50%;
                transform: translateX(-50%);
                border-top-color: white;
            }
            
            .dess-tutorial-arrow.left {
                left: -16px;
                top: 50%;
                transform: translateY(-50%);
                border-right-color: white;
            }
            
            .dess-tutorial-arrow.right {
                right: -16px;
                top: 50%;
                transform: translateY(-50%);
                border-left-color: white;
            }
            
            .dess-tutorial-highlight {
                position: relative;
                z-index: 9997;
                box-shadow: 0 0 0 4px rgba(74, 158, 224, 0.3), 0 0 20px rgba(74, 158, 224, 0.3);
                border-radius: 4px;
                transition: all 0.3s ease;
            }
            
            .dess-tutorial-pulse {
                animation: dess-tutorial-pulse 2s infinite;
            }
            
            @keyframes dess-tutorial-pulse {
                0%, 100% {
                    box-shadow: 0 0 0 4px rgba(74, 158, 224, 0.3), 0 0 20px rgba(74, 158, 224, 0.3);
                }
                50% {
                    box-shadow: 0 0 0 8px rgba(74, 158, 224, 0.2), 0 0 30px rgba(74, 158, 224, 0.2);
                }
            }
        `;
        document.head.appendChild(styles);
    }

    bindEvents() {
        // Botón cerrar
        document.getElementById('dess-tutorial-close').addEventListener('click', () => this.end());
        
        // Botón saltar
        this.skipButton.addEventListener('click', () => this.end());
        
        // Botón siguiente
        this.nextButton.addEventListener('click', () => this.nextStep());
        
        // Botón anterior
        this.prevButton.addEventListener('click', () => this.prevStep());
        
        // Cerrar con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isActive) {
                this.end();
            }
        });
    }

    start(steps) {
        if (!steps && !this.defaultSteps) {
            this.steps = userDashboardTutorial.steps;
        } else if (steps) {
            this.steps = steps;
        } else {
            this.steps = this.defaultSteps;
        }
        
        if (this.steps.length === 0) return;
        
        this.currentStep = 0;
        this.isActive = true;
        
        // Mostrar overlay
        this.overlay.classList.remove('hidden');
        
        // Comenzar primer paso
        setTimeout(() => this.showStep(0), 100);
    }

    showStep(stepIndex) {
        if (stepIndex >= this.steps.length) {
            this.end();
            return;
        }
        
        let step = this.steps[stepIndex];
        
        // Si es un paso opcional y el elemento no existe, saltar al siguiente
        if (step.optional && step.element) {
            const element = document.querySelector(step.element);
            if (!element) {
                console.log(`Saltando paso opcional: ${step.title} (elemento ${step.element} no encontrado)`);
                // Saltamos al siguiente paso
                this.showStep(stepIndex + 1);
                return;
            }
        }
        
        this.currentStep = stepIndex;
        
        // Actualizar contenido
        document.getElementById('dess-tutorial-title').textContent = step.title;
        document.getElementById('dess-tutorial-description').textContent = step.description;
        
        // Actualizar progreso
        const progress = ((stepIndex + 1) / this.steps.length) * 100;
        this.progressBar.style.width = `${progress}%`;
        this.stepCounter.textContent = `${stepIndex + 1} / ${this.steps.length}`;
        
        // Actualizar botones
        this.prevButton.disabled = stepIndex === 0;
        this.nextButton.textContent = stepIndex === this.steps.length - 1 ? 'Finalizar' : 'Siguiente';
        
        // Limpiar highlights anteriores
        this.clearHighlights();
        
        // Resaltar elemento
        if (step.element) {
            this.highlightElement(step.element);
            this.positionTooltip(step.element, step.position || 'bottom');
        }
        
        // Ejecutar callback onShow si existe
        if (step.onShow && typeof step.onShow === 'function') {
            step.onShow();
        }
        
        // Mostrar tooltip
        setTimeout(() => {
            this.tooltip.classList.add('show');
        }, 100);
        
        // Ejecutar callback si existe
        if (step.onShow && typeof step.onShow === 'function') {
            step.onShow();
        }
    }

    highlightElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.add('dess-tutorial-highlight', 'dess-tutorial-pulse');
            // Hacer scroll al elemento
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    clearHighlights() {
        const highlighted = document.querySelectorAll('.dess-tutorial-highlight');
        highlighted.forEach(el => {
            el.classList.remove('dess-tutorial-highlight', 'dess-tutorial-pulse');
        });
    }

    positionTooltip(selector, position = 'bottom') {
        const element = document.querySelector(selector);
        if (!element) return;
        
        const rect = element.getBoundingClientRect();
        const tooltip = this.tooltip;
        const arrow = document.getElementById('dess-tutorial-arrow');
        
        // Reset arrow classes
        arrow.className = 'dess-tutorial-arrow';
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top - tooltip.offsetHeight - 20;
                left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2);
                arrow.classList.add('bottom');
                break;
                
            case 'bottom':
                top = rect.bottom + 20;
                left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2);
                arrow.classList.add('top');
                break;
                
            case 'left':
                top = rect.top + (rect.height / 2) - (tooltip.offsetHeight / 2);
                left = rect.left - tooltip.offsetWidth - 20;
                arrow.classList.add('right');
                break;
                
            case 'right':
                top = rect.top + (rect.height / 2) - (tooltip.offsetHeight / 2);
                left = rect.right + 20;
                arrow.classList.add('left');
                break;
        }
        
        // Ajustar si se sale de la pantalla
        const maxLeft = window.innerWidth - tooltip.offsetWidth - 20;
        const maxTop = window.innerHeight - tooltip.offsetHeight - 20;
        
        left = Math.max(20, Math.min(left, maxLeft));
        top = Math.max(20, Math.min(top, maxTop));
        
        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
    }

    nextStep() {
        this.tooltip.classList.remove('show');
        setTimeout(() => {
            if (this.currentStep >= this.steps.length - 1) {
                this.end(true); // Tutorial completado exitosamente
            } else {
                this.showStep(this.currentStep + 1);
            }
        }, 200);
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.tooltip.classList.remove('show');
            setTimeout(() => {
                this.showStep(this.currentStep - 1);
            }, 200);
        }
    }

    end(completed = false) {
        this.isActive = false;
        this.tooltip.classList.remove('show');
        this.overlay.classList.add('hidden');
        this.clearHighlights();
        
        // Marcar tutorial como completado si se completó exitosamente
        if (completed || this.currentStep >= this.steps.length - 1) {
            localStorage.setItem('dess_tutorial_completed', 'true');
            localStorage.setItem('dess_tutorial_completed_date', new Date().toISOString());
            this.showCompletionMessage();
        } else {
            // Solo marcar como iniciado si se saltó
            localStorage.setItem('dess_tutorial_started', 'true');
        }
        
        // Callback de finalización
        if (this.onComplete && typeof this.onComplete === 'function') {
            this.onComplete(completed);
        }
    }
    
    showCompletionMessage() {
        // Mostrar mensaje de felicitación
        setTimeout(() => {
            if (typeof showModal === 'function') {
                showModal('¡Tutorial Completado! 🎉', 
                    'Has completado exitosamente el tutorial de DESS. Ahora puedes explorar todas las funcionalidades del sistema. ¡Que tengas una excelente experiencia!');
            }
        }, 500);
    }

    hasCompletedTutorial() {
        return localStorage.getItem('dess_tutorial_completed') === 'true';
    }
    
    hasStartedTutorial() {
        return localStorage.getItem('dess_tutorial_started') === 'true' || this.hasCompletedTutorial();
    }
    
    getCompletionDate() {
        const dateString = localStorage.getItem('dess_tutorial_completed_date');
        return dateString ? new Date(dateString) : null;
    }
    
    getTutorialStatus() {
        if (this.hasCompletedTutorial()) {
            return {
                status: 'completed',
                date: this.getCompletionDate(),
                message: 'Tutorial completado exitosamente'
            };
        } else if (this.hasStartedTutorial()) {
            return {
                status: 'started',
                date: null,
                message: 'Tutorial iniciado pero no completado'
            };
        } else {
            return {
                status: 'not_started',
                date: null,
                message: 'Tutorial no iniciado'
            };
        }
    }

    resetTutorial() {
        localStorage.removeItem('dess_tutorial_completed');
        localStorage.removeItem('dess_tutorial_completed_date');
        localStorage.removeItem('dess_tutorial_started');
    }
    
    // Función para mostrar tutorial automáticamente para nuevos usuarios
    autoShowForNewUsers() {
        if (!this.hasStartedTutorial()) {
            // Mostrar después de 2 segundos para nuevos usuarios
            setTimeout(() => {
                this.showWelcomeModal();
            }, 2000);
        }
    }
    
    // Modal de bienvenida para nuevos usuarios
    showWelcomeModal() {
        // Crear modal personalizado de DESS
        const modal = document.createElement('div');
        modal.id = 'welcome-tutorial-modal';
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
        
        modal.innerHTML = `
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-dess-primary bg-opacity-10">
                        <svg class="h-8 w-8 text-dess-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg leading-6 font-semibold text-gray-900 mt-4 text-center">
                        ¡Bienvenido a DESS! 👋
                    </h3>
                    <div class="mt-4 px-7 py-3">
                        <p class="text-sm text-gray-600 text-center leading-relaxed">
                            ¿Te gustaría hacer un <strong>tour rápido</strong> por las funcionalidades principales de DESS? 
                            Te llevará solo unos minutos y te ayudará a familiarizarte con el sistema.
                        </p>
                        <div class="mt-4 p-3 bg-blue-50 rounded-lg">
                            <p class="text-xs text-blue-700 text-center">
                                💡 Puedes salir del tutorial en cualquier momento y siempre tendrás acceso desde el menú de ayuda
                            </p>
                        </div>
                    </div>
                    <div class="items-center px-4 py-3 flex justify-center space-x-3">
                        <button id="start-tour-btn" class="px-6 py-2 bg-dess-primary text-white text-sm font-medium rounded-md shadow-sm hover:bg-dess-primary-dark transition duration-150 focus:outline-none focus:ring-2 focus:ring-dess-primary focus:ring-offset-1">
                            ✨ Iniciar Tour
                        </button>
                        <button id="skip-tour-btn" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-md transition duration-150 focus:outline-none focus:ring-2 focus:ring-gray-300">
                            Ahora No
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Agregar eventos
        document.getElementById('start-tour-btn').addEventListener('click', () => {
            document.body.removeChild(modal);
            this.start();
        });
        
        document.getElementById('skip-tour-btn').addEventListener('click', () => {
            document.body.removeChild(modal);
            // Marcar como iniciado para que no vuelva a aparecer
            localStorage.setItem('dess_tutorial_started', 'true');
        });
        
        // Cerrar al hacer clic fuera del modal (opcional)
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
                localStorage.setItem('dess_tutorial_started', 'true');
            }
        });
        
        // Cerrar con ESC
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                document.body.removeChild(modal);
                localStorage.setItem('dess_tutorial_started', 'true');
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }
}

// Tutorial específico para el dashboard de usuario
const userDashboardTutorial = {
    steps: [
        {
            title: "¡Bienvenido a DESS!",
            description: "Te guiaremos por las funcionalidades principales del sistema. Puedes saltar este tutorial en cualquier momento presionando ESC o el botón 'Saltar'.",
            element: "main",
            position: "bottom"
        },
        {
            title: "Navegación Principal",
            description: "Usa estas pestañas para moverte entre las diferentes secciones: Panel Principal (dashboard), Mis Soluciones (todas tus soluciones) y Mi Perfil (configuración personal).",
            element: "#user-navigation",
            position: "bottom"
        },
        {
            title: "Panel Principal",
            description: "El dashboard te muestra un resumen de toda tu actividad y acceso rápido a las funciones más importantes.",
            element: "#nav-dashboard", 
            position: "bottom"
        },
        {
            title: "Mis Soluciones",
            description: "Aquí puedes ver, buscar y filtrar todas las soluciones que tienes asignadas, así como acceder a ellas.",
            element: "#nav-solutions",
            position: "bottom"
        },
        {
            title: "Mi Perfil",
            description: "Configura tu información personal, revisa estadísticas detalladas y administra las preferencias de tu cuenta.",
            element: "#nav-profile",
            position: "bottom"
        },
        {
            title: "Estadísticas del Dashboard",
            description: "Aquí puedes ver un resumen de tus soluciones asignadas, las que están listas para usar, tus favoritas y accesos recientes.",
            element: "#stats-section",
            position: "bottom"
        },
        {
            title: "Soluciones Asignadas",
            description: "Esta tarjeta muestra el total de soluciones que tienes asignadas en el sistema.",
            element: "#assigned-solutions-stat",
            position: "bottom"
        },
        {
            title: "Soluciones Listas",
            description: "Aquí puedes ver cuántas de tus soluciones están completamente configuradas y listas para usar.",
            element: "#ready-solutions-stat", 
            position: "bottom"
        },
        {
            title: "Tus Favoritas",
            description: "Las soluciones que has marcado como favoritas se cuentan aquí. Úsalas para acceso rápido.",
            element: "#favorites-stat",
            position: "bottom"
        },
        {
            title: "Soluciones Favoritas",
            description: "Si tienes soluciones marcadas como favoritas, aparecerán en esta sección para acceso rápido. Puedes hacer clic en la estrella ⭐ en cualquier solución para marcarla como favorita.",
            element: "#favorites-section",
            position: "bottom",
            optional: true,
            onShow: function() {
                // Hacer scroll a la sección si existe
                const favSection = document.querySelector('#favorites-section');
                if (favSection) {
                    favSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        },
        {
            title: "Acceso a Soluciones",
            description: "Desde aquí puedes ver todas tus soluciones o filtrar solo las que están disponibles para usar.",
            element: "#quick-access-section",
            position: "right"
        },
        {
            title: "Ver Todas las Soluciones", 
            description: "Haz clic en este botón para ir a la página completa de tus soluciones donde puedes buscar, filtrar y acceder a ellas.",
            element: "#view-all-solutions-btn",
            position: "top"
        },
        {
            title: "Tu Perfil",
            description: "Administra tu información personal, configuración y preferencias desde la sección de perfil.",
            element: "#profile-section",
            position: "right"
        },
        {
            title: "Ver tu Perfil",
            description: "Accede a tu perfil para ver estadísticas detalladas y configurar tu cuenta.",
            element: "#view-profile-btn",
            position: "top"
        },
        {
            title: "Ayuda y Soporte",
            description: "¿Necesitas ayuda? Desde esta sección puedes acceder al centro de ayuda, contactar soporte o repetir este tutorial.",
            element: "#help-section",
            position: "left"
        },
        {
            title: "Actividad Reciente",
            description: "Revisa tu actividad reciente y los últimos accesos a tus soluciones en esta sección.",
            element: "#activity-section",
            position: "top"
        },
        {
            title: "¡Tutorial Completado!",
            description: "¡Perfecto! Ahora conoces todas las funcionalidades básicas del dashboard de DESS. ¡Explora y comienza a usar tus soluciones!",
            element: "main",
            position: "center"
        }
    ]
};

// Inicializar tutorial global
window.DESSTutorial = DESSTutorial;
window.userDashboardTutorial = userDashboardTutorial;