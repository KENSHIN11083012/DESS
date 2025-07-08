/**
 * DESS Profile Module
 * Clean Architecture: Separation of Concerns
 * Business Logic separated from presentation
 */

const ProfileModule = {
    // Configuration - usando constantes del core DESS
    config: {
        endpoints: {
            validateField: '/dashboard/validate-field/',
            updateProfile: window.location.pathname + 'update/',
            changePassword: window.location.pathname + 'change-password/'
        },
        timeouts: {
            redirect: window.DESS?.constants?.NOTIFICATION_DURATION / 2 || 1500,
            validation: window.DESS?.constants?.SEARCH_DEBOUNCE_DELAY || 500
        }
    },

    // Initialize module
    init() {
        this.bindEvents();
        this.setupValidation();
    },

    // Event binding
    bindEvents() {
        // Close modals with ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal('editModal');
                this.closeModal('passwordModal');
            }
        });

        // Close modals when clicking outside
        window.onclick = (event) => {
            const editModal = document.getElementById('editModal');
            const passwordModal = document.getElementById('passwordModal');
            
            if (event.target === editModal) {
                this.closeModal('editModal');
            } else if (event.target === passwordModal) {
                this.closeModal('passwordModal');
            }
        };

        // Form submissions
        this.bindFormSubmissions();
    },

    // Setup validation
    setupValidation() {
        // Email validation
        const emailField = document.getElementById('email');
        if (emailField) {
            emailField.addEventListener('blur', () => {
                const email = emailField.value.trim();
                const feedback = document.getElementById('email-feedback');
                const originalEmail = emailField.getAttribute('data-original') || '';
                
                if (email && email !== originalEmail) {
                    this.validateField('email', email, feedback);
                }
            });
        }

        // Password confirmation validation
        const confirmPasswordField = document.getElementById('confirm_password');
        if (confirmPasswordField) {
            confirmPasswordField.addEventListener('input', () => {
                this.validatePasswordConfirmation();
            });
        }
    },

    // Modal management
    openEditModal() {
        const modal = document.getElementById('editModal');
        if (modal) {
            modal.style.display = 'block';
            // Store original email value
            const emailField = document.getElementById('email');
            if (emailField) {
                emailField.setAttribute('data-original', emailField.value);
            }
        }
    },

    openPasswordModal() {
        const modal = document.getElementById('passwordModal');
        if (modal) {
            modal.style.display = 'block';
        }
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            this.resetForm(modalId);
        }
    },

    resetForm(modalId) {
        const forms = {
            'editModal': 'editForm',
            'passwordModal': 'passwordForm'
        };
        
        const formId = forms[modalId];
        if (formId) {
            const form = document.getElementById(formId);
            if (form) {
                form.reset();
                // Clear feedback messages
                const feedbacks = form.querySelectorAll('.feedback');
                feedbacks.forEach(feedback => feedback.innerHTML = '');
            }
        }
    },

    // Validation methods
    validateField(field, value, feedbackElement) {
        fetch('/dashboard/validate-field/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                field: field,
                value: value
            })
        })
        .then(response => response.json())
        .then(data => {
            const icon = data.valid ? 'check' : 'times';
            const color = data.valid ? 'green' : 'red';
            
            if (feedbackElement) {
                feedbackElement.innerHTML = 
                    `<span style="color: ${color};"><i class="fas fa-${icon}"></i> ${data.message}</span>`;
            }
        })
        .catch(error => {
            console.error('Validation error:', error);
            if (feedbackElement) {
                feedbackElement.innerHTML = 
                    '<span style="color: red;">Error en validación</span>';
            }
        });
    },

    validatePasswordConfirmation() {
        const newPassword = document.getElementById('new_password')?.value || '';
        const confirmPassword = document.getElementById('confirm_password')?.value || '';
        const feedback = document.getElementById('password-feedback');
        
        if (!feedback) return;

        if (confirmPassword) {
            if (newPassword === confirmPassword) {
                feedback.innerHTML = 
                    '<span style="color: green;"><i class="fas fa-check"></i> Las contraseñas coinciden</span>';
            } else {
                feedback.innerHTML = 
                    '<span style="color: red;"><i class="fas fa-times"></i> Las contraseñas no coinciden</span>';
            }
        } else {
            feedback.innerHTML = '';
        }
    },

    // Form submission handling
    bindFormSubmissions() {
        // Profile form
        const editForm = document.getElementById('editForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleProfileSubmission(editForm);
            });
        }

        // Password form
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handlePasswordSubmission(passwordForm);
            });
        }
    },

    handleProfileSubmission(form) {
        const btn = document.getElementById('saveProfileBtn');
        if (!btn) return;

        this.setLoadingState(btn, true);

        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert('Perfil actualizado exitosamente', 'success');
                
                if (data.user) {
                    this.updateProfileDisplay(data.user);
                }
                
                this.closeModal('editModal');
                
                setTimeout(() => {
                    location.reload();
                }, this.config.timeouts.redirect);
            } else {
                this.showAlert(data.message || 'Error al actualizar perfil', 'error');
            }
        })
        .catch(error => {
            console.error('Profile update error:', error);
            this.showAlert('Error al actualizar perfil', 'error');
        })
        .finally(() => {
            this.setLoadingState(btn, false);
        });
    },

    handlePasswordSubmission(form) {
        const newPassword = document.getElementById('new_password')?.value || '';
        const confirmPassword = document.getElementById('confirm_password')?.value || '';
        
        if (newPassword !== confirmPassword) {
            this.showAlert('Las contraseñas no coinciden', 'error');
            return;
        }

        const btn = document.getElementById('savePasswordBtn');
        if (!btn) return;

        this.setLoadingState(btn, true);

        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert('Contraseña cambiada exitosamente', 'success');
                this.closeModal('passwordModal');
            } else {
                this.showAlert(data.message || 'Error al cambiar contraseña', 'error');
            }
        })
        .catch(error => {
            console.error('Password change error:', error);
            this.showAlert('Error al cambiar contraseña', 'error');
        })
        .finally(() => {
            this.setLoadingState(btn, false);
        });
    },

    // UI utilities
    setLoadingState(button, isLoading) {
        const btnText = button.querySelector('.btn-text');
        const loading = button.querySelector('.loading');
        
        if (btnText && loading) {
            if (isLoading) {
                btnText.style.display = 'none';
                loading.style.display = 'inline-block';
                button.disabled = true;
            } else {
                btnText.style.display = 'inline';
                loading.style.display = 'none';
                button.disabled = false;
            }
        }
    },

    showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = message;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alert, container.firstChild);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
    },

    updateProfileDisplay(userData) {
        // Update email
        const emailElements = document.querySelectorAll('[data-field="email"]');
        emailElements.forEach(el => el.textContent = userData.email);
        
        // Update full name
        const nameElements = document.querySelectorAll('[data-field="full_name"]');
        nameElements.forEach(el => el.textContent = userData.full_name);
    },

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ProfileModule.init();
});
