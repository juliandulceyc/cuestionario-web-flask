document.addEventListener('DOMContentLoaded', function () {
    // Estado
    let respuestasSeleccionadas = [];
    let preguntaActual = null;
    let CONFIGURACION_EVALUACION = null;
    let candidateData = null;

    // Elementos del DOM
    const confirmationSection = document.getElementById('formulario-confirmacion');
    const progressContainer = document.getElementById('progreso-container');
    const questionContainer = document.getElementById('pregunta-container');
    const candidateForm = document.getElementById('candidate-form');
    const progressBar = document.getElementById('barraProgreso');
    const progressText = document.getElementById('progreso-texto');
    const questionText = document.getElementById('pregunta-texto');
    const optionsContainer = document.getElementById('opciones-container');
    const answerBtn = document.getElementById('btn-responder');
    const messageDiv = document.getElementById('mensaje');
    const answerStatus = document.getElementById('answer-status');

    // Importar utilidades
    // Si usas ES Modules, usa: import { mostrarNotificacion, mostrarError, announceToScreenReader } from './utils.js';
    // Si usas <script>, agrega utils.js antes y usa window.mostrarNotificacion, etc.

    // Init
    init();

    function init() {
        loadCandidateData();
        obtenerConfiguracion();
        setupEventListeners();
    }

    function loadCandidateData() {
        const candidateDataElement = document.getElementById('candidate-data');
        if (!candidateDataElement) return;
        try {
            candidateData = JSON.parse(candidateDataElement.textContent);
        } catch (e) {
            console.error('Error parseando candidate-data:', e);
        }
    }

    function setupEventListeners() {
        if (candidateForm) candidateForm.addEventListener('submit', handleCandidateFormSubmit);
        if (answerBtn) answerBtn.addEventListener('click', responder);
        document.addEventListener('keydown', handleKeyboardNavigation);
        setupFieldValidation();
    }

    function setupFieldValidation() {
        const fields = [
            { id: 'nombre_completo', errorId: 'nombre-completo-error' },
            { id: 'email', errorId: 'email-error' },
            { id: 'telefono', errorId: 'telefono-error' }
        ];
        fields.forEach(({ id, errorId }) => {
            const field = document.getElementById(id);
            const errorEl = document.getElementById(errorId);
            if (!field || !errorEl) return;
            field.addEventListener('blur', () => validateField(field, errorEl));
            field.addEventListener('input', () => clearFieldError(field, errorEl));
        });
    }

        function validateField(field, errorElement) {
            if (!field || !errorElement) return false;
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        if (isRequired && !value) {
            showFieldError(field, errorElement, 'Este campo es obligatorio');
            return false;
        }
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showFieldError(field, errorElement, 'Ingresa un email válido');
                return false;
            }
        }
        if (field.type === 'tel' && value) {
            const phoneRegex = /^[\d\s\-\+\(\)]{7,15}$/;
            if (!phoneRegex.test(value)) {
                showFieldError(field, errorElement, 'Ingresa un teléfono válido');
                return false;
            }
        }
        clearFieldError(field, errorElement);
        return true;
    }

    function showFieldError(field, errorElement, message) {
        field.setAttribute('aria-invalid', 'true');
        errorElement.textContent = message;
    }

    function clearFieldError(field, errorElement) {
        field.setAttribute('aria-invalid', 'false');
        errorElement.textContent = '';
    }

    function obtenerConfiguracion() {
        fetch('/api/configuracion')
            .then(r => {
                if (!r.ok) throw new Error('Error en respuesta del servidor');
                return r.json();
            })
            .then(data => {
                CONFIGURACION_EVALUACION = data;
                actualizarElementosConfiguracion();
            })
            .catch(() => {
                CONFIGURACION_EVALUACION = {
                    total_preguntas: 40,
                    preguntas_nivel_1: 10,
                    min_correctas_avance: 6,
                    niveles_maximos: 5
                };
                actualizarElementosConfiguracion();
            });
    }

    function actualizarElementosConfiguracion() {
        if (!CONFIGURACION_EVALUACION) return;
        document.querySelectorAll('.total-preguntas').forEach(el => {
            el.textContent = CONFIGURACION_EVALUACION.total_preguntas;
        });
        if (progressBar) progressBar.setAttribute('aria-valuemax', CONFIGURACION_EVALUACION.total_preguntas);
        const configDisplay = document.getElementById('config-display');
        if (configDisplay) configDisplay.style.display = 'block';
    }

    function handleCandidateFormSubmit(e) {
        e.preventDefault();
        if (!validateAllFields()) {
            announceToScreenReader('Por favor corrige los errores en el formulario');
            const firstError = candidateForm.querySelector('[aria-invalid="true"]');
            if (firstError) firstError.focus();
            return;
        }
        iniciarEvaluacion();
    }

    function validateAllFields() {
        if (!candidateForm) return false;
        const validations = [
            { field: document.getElementById('nombre_completo'), error: document.getElementById('nombre-completo-error') },
            { field: document.getElementById('email'), error: document.getElementById('email-error') },
            { field: document.getElementById('telefono'), error: document.getElementById('telefono-error') }
        ];
        let allValid = true;
        validations.forEach(v => {
            if (v.field && v.error && v.field.hasAttribute('required')) {
                if (!validateField(v.field, v.error)) allValid = false;
            }
        });
        return allValid;
    }

    function iniciarEvaluacion() {
        const formData = {
            nombre: getValue('nombre_completo'),
            documento: getValue('documento'),
            email: getValue('email'),
            telefono: getValue('telefono')
        };
        const submitBtn = candidateForm ? candidateForm.querySelector('button[type="submit"]') : null;
        if (!submitBtn) return;
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Iniciando...';
        announceToScreenReader('Iniciando evaluación...');

        fetch('/iniciar_evaluacion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                if (data.mensaje) {
                    if (confirmationSection) confirmationSection.style.display = 'none';
                    if (progressContainer) progressContainer.style.display = 'block';
                    if (questionContainer) questionContainer.style.display = 'block';
                    announceToScreenReader('Evaluación iniciada correctamente');
                    setTimeout(cargarPregunta, 400);
                } else {
                    throw new Error(data.error || 'Error iniciando evaluación');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                announceToScreenReader('Error iniciando evaluación');
                mostrarError('❌ Error iniciando evaluación: ' + err.message);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
    }

    function getValue(id) {
        const el = document.getElementById(id);
        return el ? el.value.trim() : '';
    }

    function cargarPregunta() {
        fetch('/obtener_pregunta')
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                if (data.error) {
                    mostrarEvaluacionCompleta();
                } else {
                    mostrarPregunta(data);
                }
            })
            .catch(err => {
                console.error('Error cargando pregunta:', err);
                mostrarError('❌ Error cargando pregunta. Intenta recargar la página.');
            });
    }

    function mostrarPregunta(data) {
        preguntaActual = data;
        respuestasSeleccionadas = [];
        if (progressBar && progressText) {
            const progreso = (data.pregunta_numero / data.total_preguntas) * 100;
            progressBar.style.width = progreso + '%';
            progressBar.setAttribute('aria-valuenow', data.pregunta_numero);
            progressBar.setAttribute('aria-valuemax', data.total_preguntas);
            progressText.textContent = 'Pregunta ' + data.pregunta_numero + ' de ' + data.total_preguntas;
        }
        // Mostrar badge de múltiple si corresponde
        if (window.mostrarBadgeMultiple) {
            window.mostrarBadgeMultiple(!!data.multiple, data.respuestas_correctas_count || 1);
        }
        if (questionText) {
            questionText.innerHTML =
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">' +
        '<strong>Pregunta ' + data.pregunta_numero + ' de ' + data.total_preguntas + '</strong>' +
                '</div>' + data.pregunta;
        }
        mostrarOpciones(data.opciones, !!data.multiple);
        if (answerBtn) {
            answerBtn.disabled = true;
            answerBtn.textContent = 'Responder';
            answerBtn.style.backgroundColor = '#007bff';
        }
        announceToScreenReader('Pregunta ' + data.pregunta_numero + ' de ' + data.total_preguntas + ' cargada');
    }

    function mostrarOpciones(opciones, esMultiple) {
        if (!optionsContainer) return;
        optionsContainer.innerHTML = '';
        opciones.forEach((opcion, index) => {
            const div = document.createElement('div');
            div.className = 'opcion';
            div.innerHTML = String.fromCharCode(65 + index) + '. ' + opcion;
            div.tabIndex = 0;
            div.dataset.index = String(index);
            div.dataset.optionText = opcion;
            div.addEventListener('click', () => seleccionarOpcion(index, div, esMultiple));
            div.addEventListener('keydown', (e) => {
                if (e.key === ' ' || e.key === 'Enter') {
                    e.preventDefault();
                    seleccionarOpcion(index, div, esMultiple);
                }
            });
            optionsContainer.appendChild(div);
        });
    }

    function seleccionarOpcion(index, elemento, esMultiple) {
        const isSelected = elemento.classList.contains('seleccionada');
        const letra = String.fromCharCode(65 + index);
        if (esMultiple) {
            if (isSelected) {
                deseleccionarOpcion(elemento, letra);
            } else {
                if (respuestasSeleccionadas.length < 2) {
                    seleccionarElemento(elemento, letra);
                } else {
                    announceToScreenReader('Máximo 2 respuestas permitidas para esta pregunta');
                        mostrarError('⚠️ Esta pregunta requiere exactamente 2 respuestas');
                    return;
                }
            }
        } else {
            if (isSelected) {
                deseleccionarOpcion(elemento, letra);
            } else {
                if (optionsContainer) {
                    const opciones = optionsContainer.querySelectorAll('.opcion');
                    opciones.forEach((op) => {
                        if (op !== elemento && op.classList.contains('seleccionada')) {
                            const idx = Number(op.getAttribute('data-index')) || 0;
                            const letraOp = String.fromCharCode(65 + idx);
                            deseleccionarOpcion(op, letraOp);
                        }
                    });
                }
                seleccionarElemento(elemento, letra);
            }
        }
        if (answerBtn) {
            if (esMultiple) {
                answerBtn.disabled = respuestasSeleccionadas.length !== 2;
            } else {
                answerBtn.disabled = respuestasSeleccionadas.length === 0;
            }
        }
    }

    function seleccionarElemento(elemento, letra) {
        elemento.classList.add('seleccionada');
        respuestasSeleccionadas.push(letra);
        announceToScreenReader('Opción ' + letra + ' seleccionada');
    }

    function deseleccionarOpcion(elemento, letra) {
        elemento.classList.remove('seleccionada');
        respuestasSeleccionadas = respuestasSeleccionadas.filter(r => r !== letra);
        announceToScreenReader('Opción ' + letra + ' deseleccionada');
    }

    function handleKeyboardNavigation(e) {
        if (!questionContainer || questionContainer.style.display === 'none' || !optionsContainer) return;
        const opciones = Array.from(optionsContainer.querySelectorAll('.opcion'));
        const currentIndex = opciones.findIndex(op => op === document.activeElement);
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                opciones[(currentIndex + 1) % opciones.length].focus();
                break;
            case 'ArrowUp':
                e.preventDefault();
                opciones[currentIndex <= 0 ? opciones.length - 1 : currentIndex - 1].focus();
                break;
        }
    }

    function responder() {
        if (!preguntaActual) {
            announceToScreenReader('Selecciona al menos una respuesta');
            return;
        }
        if (preguntaActual.multiple) {
            if (respuestasSeleccionadas.length !== 2) {
                announceToScreenReader('Esta pregunta requiere exactamente 2 respuestas');
                mostrarError('⚠️ Esta pregunta requiere exactamente 2 respuestas');
                return;
            }
        } else if (respuestasSeleccionadas.length === 0) {
            announceToScreenReader('Selecciona al menos una respuesta');
            return;
        }
        if (answerBtn) {
            answerBtn.disabled = true;
            answerBtn.textContent = '⏳ Guardando...';
        }
        announceToScreenReader('Guardando respuesta...');
        enviarRespuesta();
    }

    function enviarRespuesta() {
        const respuestaEnviarLetras = respuestasSeleccionadas.join(',');
        // También enviar los textos seleccionados para compatibilidad y análisis
        let respuestaEnviarTextos = '';
        if (optionsContainer) {
            const seleccionadas = optionsContainer.querySelectorAll('.opcion.seleccionada');
            const textos = Array.from(seleccionadas).map(el => el.getAttribute('data-option-text') || '');
            respuestaEnviarTextos = textos.join(',');
        }
        fetch('/responder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                respuesta: respuestaEnviarTextos,
                respuesta_letra: respuestaEnviarLetras,
                pregunta_id: preguntaActual.id,
                respuestas_seleccionadas: respuestasSeleccionadas
            })
        })
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                if (data.success) {
                    mostrarMensajeGuardadoRapido();
                    announceToScreenReader('Respuesta guardada correctamente');
                    setTimeout(() => {
                        if (data.hay_mas) {
                            siguientePregunta();
                        } else {
                            generarPDFAutomatico();
                        }
                    }, 1200);
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            })
            .catch(err => {
                console.error('Error enviando respuesta:', err);
                announceToScreenReader('Error enviando respuesta');
                mostrarError('❌ Error enviando respuesta: ' + err.message);
                rehabilitarBotonResponder();
            });
    }

    function mostrarMensajeGuardadoRapido() {
        if (optionsContainer) {
            const opciones = optionsContainer.querySelectorAll('.opcion');
            opciones.forEach(op => {
                op.style.pointerEvents = 'none';
                op.style.opacity = '0.7';
                op.tabIndex = -1;
            });
        }
        if (answerBtn) {
            answerBtn.textContent = '✅ Guardado';
            answerBtn.style.backgroundColor = '#28a745';
        }
    }

    function rehabilitarBotonResponder() {
        if (answerBtn) {
            answerBtn.disabled = false;
            answerBtn.textContent = 'Responder';
            answerBtn.style.backgroundColor = '#007bff';
        }
    }

    function siguientePregunta() {
        if (optionsContainer) {
            const opciones = optionsContainer.querySelectorAll('.opcion');
            opciones.forEach(op => {
                op.style.pointerEvents = 'auto';
                op.style.opacity = '1';
                op.tabIndex = 0;
                op.classList.remove('seleccionada');
            });
        }
        rehabilitarBotonResponder();
        if (answerBtn) answerBtn.disabled = true;
        respuestasSeleccionadas = [];
        cargarPregunta();
    }

    function generarPDFAutomatico() {
        announceToScreenReader('Generando reporte final...');
        fetch('/generar_pdf_final', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                if (data.success) {
                    mostrarEvaluacionCompleta(data);
                } else {
                    mostrarEvaluacionCompleta(null, 'Error generando reporte: ' + data.error);
                }
            })
            .catch(err => {
                console.error('Error generando PDF:', err);
                mostrarEvaluacionCompleta(null, 'Error de conexión generando reporte');
            });
    }

    function mostrarEvaluacionCompleta(datosResultado, errorPDF) {
        if (questionContainer) questionContainer.style.display = 'none';
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', progressBar.getAttribute('aria-valuemax'));
            }
        if (progressText) progressText.textContent = '¡Evaluación Completada!';
        let mensajeResultados = '';
        let mensajePDF = '';
        if (datosResultado && datosResultado.success) {
            mensajeResultados =
                '<div style="background:#d4edda;color:#155724;padding:15px;border-radius:8px;margin-bottom:15px;">' +
                '<h3>📊 Resultados de tu Evaluación:</h3>' +
                '<ul style="margin:10px 0; padding-left:20px;">' +
                '<li><strong>Respuestas correctas:</strong> ' + datosResultado.correctas + '/' + datosResultado.total + ' (' + datosResultado.porcentaje + '%)</li>' +
                '<li><strong>Nivel final alcanzado:</strong> ' + datosResultado.nivel_final + '/5</li>' +
                '<li><strong>Puntuación total:</strong> ' + datosResultado.puntos + ' puntos</li>' +
                '</ul>' +
                '</div>';
            mensajePDF = datosResultado.pdf_generado
                ? '<div style="background:#cce5ff;color:#004085;padding:10px;border-radius:5px;">✅ Reporte PDF generado correctamente</div>'
                : '<div style="background:#fff3cd;color:#856404;padding:10px;border-radius:5px;">⚠️ Evaluación guardada, reporte en proceso</div>';
        }
        if (errorPDF) {
            mensajePDF = '<div style="background:#f8d7da;color:#721c24;padding:10px;border-radius:5px;">⚠️ ' + errorPDF + '</div>';
        }
        if (messageDiv) {
            messageDiv.innerHTML =
                '<div style="text-align:center;">' +
                '<div style="background:#d4edda;color:#155724;padding:30px;border-radius:10px;border:1px solid #c3e6cb;margin-bottom:20px;">' +
                '<h2>🎉 ¡Evaluación Completada!</h2>' +
                '<p>Todas tus respuestas han sido guardadas correctamente.</p>' +
                mensajeResultados +
                mensajePDF +
                '<div style="margin-top:20px;">' +
                '<p><strong>Los resultados serán enviados a Recursos Humanos.</strong></p>' +
                '<small style="color:#6c757d;">Puedes cerrar esta ventana de forma segura.</small>' +
                '</div>' +
                '</div>' +
                '</div>';
            messageDiv.style.display = 'block';
        }
        announceToScreenReader('Evaluación completada exitosamente. Los resultados han sido enviados.');
    }

    function mostrarError(mensaje) {
        if (typeof window.mostrarError === 'function') {
            window.mostrarError(mensaje);
        } else {
            // Fallback si utils.js no está cargado
            const notification = document.createElement('div');
            notification.style.cssText = 'position:fixed;top:20px;right:20px;background:#f8d7da;color:#721c24;padding:15px 20px;border:1px solid #f5c6cb;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:1000;max-width:400px;';
            notification.textContent = mensaje;
            document.body.appendChild(notification);
            setTimeout(() => {
                if (notification.parentNode) notification.remove();
            }, 5000);
        }
    }

    function announceToScreenReader(message) {
        if (typeof window.announceToScreenReader === 'function') {
            window.announceToScreenReader(message);
        } else {
            if (!answerStatus) return;
            answerStatus.textContent = message;
            setTimeout(() => {
                answerStatus.textContent = '';
            }, 3000);
        }
    }

    // Agregar estilos para animaciones solo una vez
    if (!document.querySelector('#cuestionario-animations')) {
        const style = document.createElement('style');
        style.id = 'cuestionario-animations';
        style.textContent =
            '@keyframes slideInRight {' +
            '  from { transform: translateX(100%); opacity: 0; }' +
            '  to { transform: translateX(0); opacity: 1; }' +
            '}';
        document.head.appendChild(style);
    }
});
