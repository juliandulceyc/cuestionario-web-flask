document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    var formularioRegistro = document.getElementById('formularioRegistro');
    var candidatoForm = document.getElementById('candidatoForm');
    var listaCandidatos = document.getElementById('listaCandidatos');
    var addCandidateBtn = document.querySelector('.add-candidate-btn');
    
    // Inicializar
    init();
    
    function init() {
        console.log('🔄 Inicializando panel de administración...');
        
        setupEventListeners();
        cargarCandidatos();
        
        console.log('✅ Panel inicializado correctamente');
// ...existing code...
    
    function setupEventListeners() {
        // Botón para mostrar formulario
        if (addCandidateBtn) {
            addCandidateBtn.addEventListener('click', function() {
                mostrarFormulario();
            });
        }
        
        // Botón cancelar
        var cancelBtn = document.querySelector('button[data-action="cancel"]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                ocultarFormulario();
            });
        }
        
        // Formulario de registro
        if (candidatoForm) {
            candidatoForm.addEventListener('submit', function(e) {
                e.preventDefault();
                registrarCandidato();
            });
        }
        
        // Validación en tiempo real
        setupFieldValidation();
    }
    
    function setupFieldValidation() {
        var fields = [
            { id: 'nombre_completo', errorId: 'nombre-completo-error' },
            { id: 'email', errorId: 'email-error' },
            { id: 'telefono', errorId: 'telefono-error' },
            { id: 'cargo', errorId: 'cargo-error' }
        ];
        
        fields.forEach(function(field) {
            var input = document.getElementById(field.id);
            var errorElement = document.getElementById(field.errorId);
            
            if (input && errorElement) {
                input.addEventListener('blur', function() {
                    validateField(input, errorElement);
                });
                input.addEventListener('input', function() {
                    clearFieldError(input, errorElement);
                });
            }
        });
    }
    
    function validateField(field, errorElement) {
        if (!field || !errorElement) return false;
        
        var value = field.value.trim();
        var fieldType = field.type;
        var isRequired = field.hasAttribute('required');
        
        if (isRequired && !value) {
            showFieldError(field, errorElement, 'Este campo es obligatorio');
            return false;
        }
        
        if (fieldType === 'email' && value) {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showFieldError(field, errorElement, 'Ingresa un email válido');
                return false;
            }
        }
        
        if (fieldType === 'tel' && value) {
            var phoneRegex = /^[\d\s\-\+\(\)]{7,15}$/;
            if (!phoneRegex.test(value)) {
                showFieldError(field, errorElement, 'Ingresa un teléfono válido');
                return false;
            }
        }
        
        if (field.id === 'nombre_completo' && value) {
            if (value.length < 2) {
                showFieldError(field, errorElement, 'El nombre debe tener al menos 2 caracteres');
                return false;
            }
        }
        
        if (field.id === 'cargo' && value) {
            if (value.length < 2) {
                showFieldError(field, errorElement, 'El cargo debe tener al menos 2 caracteres');
                return false;
            }
        }
        
        clearFieldError(field, errorElement);
        return true;
    }
    
    function showFieldError(field, errorElement, message) {
        if (field && errorElement) {
            field.style.borderColor = '#dc3545';
            errorElement.textContent = message;
            errorElement.style.color = '#dc3545';
        }
    }
    
    function clearFieldError(field, errorElement) {
        if (field && errorElement) {
            field.style.borderColor = '';
            errorElement.textContent = '';
        }
    }
    
    function mostrarFormulario() {
        if (formularioRegistro) {
            formularioRegistro.style.display = 'block';
            
            // Scroll al formulario
            formularioRegistro.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
            
            // Focus en primer campo
            var firstField = document.getElementById('nombre_completo');
            if (firstField) {
                setTimeout(function() {
                    firstField.focus();
                }, 300);
            }
        }
    }
    
    function ocultarFormulario() {
        if (formularioRegistro) {
            formularioRegistro.style.display = 'none';
        }
        
        // Limpiar formulario
        if (candidatoForm) {
            candidatoForm.reset();
            
            // Limpiar errores
            var errorElements = candidatoForm.querySelectorAll('.error-message');
            errorElements.forEach(function(element) {
                element.textContent = '';
            });
            
            // Limpiar estilos de error
            var inputs = candidatoForm.querySelectorAll('input');
            inputs.forEach(function(input) {
                input.style.borderColor = '';
            });
        }
    }
    
    function registrarCandidato() {
        if (!candidatoForm) return;
        
        // Validar todos los campos
        var isValid = validateAllFields();
        
        if (!isValid) {
            mostrarNotificacion('Por favor corrige los errores en el formulario', 'error');
            return;
        }
        
        // Obtener datos del formulario
        var formData = {
            nombre_completo: getValue('nombre_completo'),
            email: getValue('email'),
            telefono: getValue('telefono'),
            cargo: getValue('cargo')
        };
        
        var submitBtn = candidatoForm.querySelector('button[type="submit"]');
        var originalText = submitBtn ? submitBtn.textContent : '';
        
        // Estado de carga
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Registrando...';
        }
        
        // Enviar datos
        fetch('/admin/registrar_candidato', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                mostrarNotificacion('✅ Candidato registrado correctamente', 'success');
                ocultarFormulario();
                cargarCandidatos(); // Recargar lista
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            mostrarNotificacion('❌ Error al registrar candidato: ' + error.message, 'error');
        })
        .finally(function() {
            // Restaurar botón
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
    
    function validateAllFields() {
        if (!candidatoForm) return false;
        
        var validations = [
            { field: document.getElementById('nombre_completo'), error: document.getElementById('nombre-completo-error') },
            { field: document.getElementById('email'), error: document.getElementById('email-error') },
            { field: document.getElementById('telefono'), error: document.getElementById('telefono-error') },
            { field: document.getElementById('cargo'), error: document.getElementById('cargo-error') }
        ];
        
        var allValid = true;
        
        validations.forEach(function(validation) {
            if (validation.field && validation.error) {
                if (!validateField(validation.field, validation.error)) {
                    allValid = false;
                }
            }
        });
        
        return allValid;
    }
    
    function getValue(id) {
        var element = document.getElementById(id);
        return element ? element.value.trim() : '';
    }
    
    function cargarCandidatos() {
        if (!listaCandidatos) return;
        
        listaCandidatos.innerHTML = '<div class="loading">Cargando candidatos...</div>';
        
        fetch('/admin/candidatos?format=json')
        .then(function(response) {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.json();
        })
        .then(function(candidatos) {
            mostrarCandidatos(candidatos);
        })
        .catch(function(error) {
            console.error('Error cargando candidatos:', error);
            listaCandidatos.innerHTML = '<div class="error">❌ Error cargando candidatos</div>';
        });
    }
    
    function mostrarCandidatos(candidatos) {
        if (!listaCandidatos) return;
        
        if (!candidatos || candidatos.length === 0) {
            listaCandidatos.innerHTML = '<div class="no-candidates">📝 No hay candidatos registrados</div>';
            return;
        }
        
        var html = '';
        
        candidatos.forEach(function(candidato) {
            var statusClass = candidato.evaluacion_completada ? 'status-completada' : 'status-pendiente';
            var statusText = candidato.evaluacion_completada ? '✅ Completada' : '⏳ Pendiente';
            
            html += '<div class="candidato-card">';
            html += '  <div class="candidato-info">';
            html += '    <h3>' + escapeHtml(candidato.nombre_completo) + '</h3>';
            html += '    <p>📧 ' + escapeHtml(candidato.email) + '</p>';
            html += '    <p>🔑 ' + escapeHtml(candidato.codigo) + '</p>';
            html += '    <p>👔 ' + escapeHtml(candidato.cargo || 'N/A') + '</p>';
            html += '    <p>📞 ' + escapeHtml(candidato.telefono || 'N/A') + '</p>';
            html += '  </div>';
            html += '  <div class="candidato-status">';
            html += '    <span class="' + statusClass + '">' + statusText + '</span>';
            
            if (!candidato.evaluacion_completada && candidato.url_evaluacion) {
                html += '    <button class="copy-btn" onclick="copiarURL(\'' + candidato.url_evaluacion + '\')">';
                html += '      📋 Copiar URL';
                html += '    </button>';
                html += '    <a href="' + candidato.url_evaluacion + '" target="_blank" class="eval-link">';
                html += '      🔗 Abrir Evaluación';
                html += '    </a>';
            }
            
            html += '  </div>';
            html += '</div>';
        });
        
        listaCandidatos.innerHTML = html;
    }
    
    function escapeHtml(text) {
        if (!text) return '';
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    function mostrarNotificacion(mensaje, tipo) {
        var notification = document.createElement('div');
        notification.className = 'notification ' + tipo;
        notification.textContent = mensaje;
        
        document.body.appendChild(notification);
        
        setTimeout(function() {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Función global para copiar URL
    window.copiarURL = function(url) {
        if (!url) return;
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(function() {
                mostrarNotificacion('📋 URL copiada al portapapeles', 'success');
            }).catch(function(err) {
                console.error('Error copiando URL:', err);
                fallbackCopyURL(url);
            });
        } else {
            fallbackCopyURL(url);
        }
    };
    
    function fallbackCopyURL(url) {
        // Crear elemento temporal
        var tempInput = document.createElement('input');
        tempInput.value = url;
        document.body.appendChild(tempInput);
        tempInput.select();
        
        try {
            document.execCommand('copy');
            mostrarNotificacion('📋 URL copiada al portapapeles', 'success');
        } catch (err) {
            console.error('Error copiando URL:', err);
            mostrarNotificacion('❌ No se pudo copiar la URL', 'error');
        }
        
        document.body.removeChild(tempInput);
    }
    
    // Agregar estilos de animación solo una vez
    if (!document.querySelector('#admin-animations')) {
        var style = document.createElement('style');
        style.id = 'admin-animations';
        style.textContent =
            '@keyframes slideInRight {' +
            '  from { transform: translateX(100%); opacity: 0; }' +
            '  to { transform: translateX(0); opacity: 1; }' +
            '}';
        document.head.appendChild(style);
    }
// ...existing code...
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '15px 20px';
        notification.style.borderRadius = '8px';
        notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        notification.style.zIndex = '1000';
        notification.style.maxWidth = '400px';
        notification.style.whiteSpace = 'pre-line';
        notification.style.animation = 'slideInRight 0.3s ease-out';
        if (tipo === 'success') {
            notification.style.background = '#d4edda';
            notification.style.color = '#155724';
            notification.style.border = '1px solid #c3e6cb';
        } else if (tipo === 'error') {
            notification.style.background = '#f8d7da';
            notification.style.color = '#721c24';
            notification.style.border = '1px solid #f5c6cb';
        }
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', tipo === 'error' ? 'assertive' : 'polite');
        notification.textContent = mensaje;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, duracion);
    }

    function announceToScreenReader(message) {
        if (formStatus) {
            formStatus.textContent = message;
            setTimeout(() => {
                formStatus.textContent = '';
            }, 3000);
        }
    }

    // Función global para recargar candidatos
    window.recargarCandidatos = cargarCandidatos;
});
