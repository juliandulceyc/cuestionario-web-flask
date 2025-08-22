document.addEventListener('DOMContentLoaded', function() {
    var form = document.querySelector('form');
    var usernameField = document.getElementById('username');
    var passwordField = document.getElementById('password');
    var submitBtn = document.querySelector('.login-btn');
    var btnText = document.querySelector('.btn-text');
    var btnLoader = document.querySelector('.btn-loader');
    var loginStatus = document.getElementById('login-status');

    setupFieldValidation();
    
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    function setupFieldValidation() {
        if (usernameField) {
            usernameField.addEventListener('blur', function() {
                validateUsername();
            });
            usernameField.addEventListener('input', function() {
                clearError(usernameField, 'username-error');
            });
        }

        if (passwordField) {
            passwordField.addEventListener('blur', function() {
                validatePassword();
            });
            passwordField.addEventListener('input', function() {
                clearError(passwordField, 'password-error');
            });
        }
    }

    function validateUsername() {
        var value = usernameField.value.trim();
        var errorElement = document.getElementById('username-error');
        
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

    function validatePassword() {
        var value = passwordField.value;
        var errorElement = document.getElementById('password-error');
        
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

    function showError(field, errorElement, message) {
        if (field && errorElement) {
            field.setAttribute('aria-invalid', 'true');
            errorElement.textContent = message;
        }
    }

    function clearError(field, errorId) {
        var errorElement = document.getElementById(errorId);
        if (field && errorElement) {
            field.setAttribute('aria-invalid', 'false');
            errorElement.textContent = '';
        }
    }

    function handleFormSubmit(e) {
        var isUsernameValid = validateUsername();
        var isPasswordValid = validatePassword();
        
        if (!isUsernameValid || !isPasswordValid) {
            e.preventDefault();
            announceToScreenReader('Por favor corrige los errores en el formulario');
            
            var firstErrorField = form.querySelector('[aria-invalid="true"]');
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
    }

    function announceToScreenReader(message) {
        if (loginStatus) {
            loginStatus.textContent = message;
            setTimeout(function() {
                loginStatus.textContent = '';
            }, 3000);
        }
    }

    if (usernameField && usernameField.value.trim() && passwordField) {
        passwordField.focus();
    }
});
