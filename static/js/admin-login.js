// ==========================================
// Funciones de Validación y UI
// ==========================================

function showError(field, errorElement, message) {
    if (field && errorElement) {
        field.setAttribute('aria-invalid', 'true');
        errorElement.textContent = message;
    }
}

function clearError(field, errorId) {
    const errorElement = document.getElementById(errorId);
    if (field && errorElement) {
        field.setAttribute('aria-invalid', 'false');
        errorElement.textContent = '';
    }
}

function announceToScreenReader(message) {
    const loginStatus = document.getElementById('login-status');
    if (loginStatus) {
        loginStatus.textContent = message;
        setTimeout(() => {
            loginStatus.textContent = '';
        }, 3000);
    }
}

function validateUsername(usernameField) {
    if (!usernameField) return false;
    
    const value = usernameField.value.trim();
    const errorElement = document.getElementById('username-error');
    
    if (!value) {
        showError(usernameField, errorElement, 'El usuario es obligatorio');
        return false;
    }
    
    if (value.length < 3) {
        showError(usernameField, errorElement, 'El usuario debe tener al menos 3 caracteres');
        return false;
    }
    
    clearError(usernameField, 'username-error');
    return true;
}

function validatePassword(passwordField) {
    if (!passwordField) return false;

    const value = passwordField.value;
    const errorElement = document.getElementById('password-error');
    
    if (!value) {
        showError(passwordField, errorElement, 'La contraseña es obligatoria');
        return false;
    }
    
    if (value.length < 4) {
        showError(passwordField, errorElement, 'La contraseña debe tener al menos 4 caracteres');
        return false;
    }
    
    clearError(passwordField, 'password-error');
    return true;
}

// ==========================================
// Inicialización
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const usernameField = document.getElementById('username');
    const passwordField = document.getElementById('password');
    const submitBtn = document.querySelector('.login-btn');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');

    // Configuración de validación en tiempo real
    if (usernameField) {
        usernameField.addEventListener('blur', () => validateUsername(usernameField));
        usernameField.addEventListener('input', () => clearError(usernameField, 'username-error'));
    }

    if (passwordField) {
        passwordField.addEventListener('blur', () => validatePassword(passwordField));
        passwordField.addEventListener('input', () => clearError(passwordField, 'password-error'));
    }

    // Manejo del envío del formulario
    if (form) {
        form.addEventListener('submit', (e) => {
            const isUsernameValid = validateUsername(usernameField);
            const isPasswordValid = validatePassword(passwordField);
            
            if (!isUsernameValid || !isPasswordValid) {
                e.preventDefault();
                announceToScreenReader('Por favor corrige los errores en el formulario');
                
                const firstErrorField = form.querySelector('[aria-invalid="true"]');
                if (firstErrorField) {
                    firstErrorField.focus();
                }
                return;
            }

            if (submitBtn && btnText && btnLoader) {
                submitBtn.disabled = true;
                btnText.style.display = 'none';
                btnLoader.style.display = 'inline';
                announceToScreenReader('Iniciando sesión...');
            }
        });
    }

    // Auto-focus inteligente
    if (usernameField?.value.trim() && passwordField) {
        passwordField.focus();
    }
});
