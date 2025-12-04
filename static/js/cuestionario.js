// ==========================================
// Estado y Configuración
// ==========================================

const State = {
    respuestasSeleccionadas: [],
    preguntaActual: null,
    configuracion: null,
    candidateData: null
};

// ==========================================
// Utilidades de UI
// ==========================================

const UI = {
    announceToScreenReader: (message) => {
        const answerStatus = document.getElementById('answer-status');
        if (answerStatus) {
            answerStatus.textContent = message;
            setTimeout(() => { answerStatus.textContent = ''; }, 3000);
        }
    },

    mostrarError: (mensaje) => {
        const notification = document.createElement('div');
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: '#f8d7da',
            color: '#721c24',
            padding: '15px 20px',
            border: '1px solid #f5c6cb',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: '1000',
            maxWidth: '400px'
        });
        notification.textContent = mensaje;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    },

    showFieldError: (field, errorElement, message) => {
        if (field && errorElement) {
            field.setAttribute('aria-invalid', 'true');
            errorElement.textContent = message;
        }
    },

    clearFieldError: (field, errorElement) => {
        if (field && errorElement) {
            field.setAttribute('aria-invalid', 'false');
            errorElement.textContent = '';
        }
    },

    updateProgressBar: (current, total) => {
        const progressBar = document.getElementById('barraProgreso');
        const progressText = document.getElementById('progreso-texto');
        if (progressBar && progressText) {
            const progreso = (current / total) * 100;
            progressBar.style.width = `${progreso}%`;
            progressBar.setAttribute('aria-valuenow', current);
            progressBar.setAttribute('aria-valuemax', total);
            progressText.textContent = `Pregunta ${current} de ${total}`;
        }
    }
};

// ==========================================
// Lógica de Negocio
// ==========================================

async function obtenerConfiguracion() {
    try {
        const response = await fetch('/api/configuracion');
        if (!response.ok) throw new Error('Error en respuesta del servidor');
        State.configuracion = await response.json();
    } catch (error) {
        State.configuracion = {
            total_preguntas: 40,
            preguntas_nivel_1: 10,
            min_correctas_avance: 6,
            niveles_maximos: 5
        };
    }
    actualizarElementosConfiguracion();
}

function actualizarElementosConfiguracion() {
    if (!State.configuracion) return;
    
    for (const el of document.querySelectorAll('.total-preguntas')) {
        el.textContent = State.configuracion.total_preguntas;
    }
    
    const progressBar = document.getElementById('barraProgreso');
    if (progressBar) {
        progressBar.setAttribute('aria-valuemax', State.configuracion.total_preguntas);
    }
    
    const configDisplay = document.getElementById('config-display');
    if (configDisplay) configDisplay.style.display = 'block';
}

function validateField(field, errorElement) {
    if (!field || !errorElement) return false;
    const value = field.value.trim();
    
    if (field.hasAttribute('required') && !value) {
        UI.showFieldError(field, errorElement, 'Este campo es obligatorio');
        return false;
    }
    
    if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        UI.showFieldError(field, errorElement, 'Ingresa un email válido');
        return false;
    }
    
    if (field.type === 'tel' && value && !/^[\d\s\-+()]{7,15}$/.test(value)) {
        UI.showFieldError(field, errorElement, 'Ingresa un teléfono válido');
        return false;
    }
    
    UI.clearFieldError(field, errorElement);
    return true;
}

async function iniciarEvaluacion() {
    const candidateForm = document.getElementById('candidate-form');
    if (!candidateForm) return;

    const formData = {
        nombre: document.getElementById('nombre_completo')?.value.trim(),
        documento: document.getElementById('documento')?.value.trim(),
        email: document.getElementById('email')?.value.trim(),
        telefono: document.getElementById('telefono')?.value.trim(),
        acepta_terminos: document.getElementById('acepta_terminos')?.checked ? 1 : 0
    };

    const submitBtn = candidateForm.querySelector('button[type="submit"]');
    if (!submitBtn) return;

    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Iniciando...';
    UI.announceToScreenReader('Iniciando evaluación...');

    try {
        const response = await fetch('/iniciar_evaluacion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        let data = {};
        try { data = await response.json(); } catch (e) { /* ignore */ }

        if (response.status === 404) {
            throw new Error('Candidato no registrado');
        }
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        if (data.success || data.mensaje) {
            document.getElementById('formulario-confirmacion').style.display = 'none';
            document.getElementById('progreso-container').style.display = 'block';
            document.getElementById('pregunta-container').style.display = 'block';
            UI.announceToScreenReader('Evaluación iniciada correctamente');
            setTimeout(cargarPregunta, 400);
        } else {
            throw new Error(data.error || 'Error iniciando evaluación');
        }
    } catch (err) {
        const msg = err.message === 'Candidato no registrado' 
            ? '❌ Candidato no registrado. Verifica tu código.' 
            : `❌ Error: ${err.message}`;
        
        UI.mostrarError(msg);
        UI.announceToScreenReader(msg);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

async function cargarPregunta() {
    try {
        const response = await fetch('/obtener_pregunta');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        if (data.error) {
            mostrarEvaluacionCompleta();
        } else {
            mostrarPregunta(data);
        }
    } catch (err) {
        console.error('Error cargando pregunta:', err);
        UI.mostrarError('❌ Error cargando pregunta. Intenta recargar la página.');
    }
}

function mostrarPregunta(data) {
    State.preguntaActual = data;
    State.respuestasSeleccionadas = [];
    
    UI.updateProgressBar(data.pregunta_numero, data.total_preguntas);
    
    const badge = document.getElementById('badge-multiple');
    if (badge) {
        const isMultiple = data.multiple && data.respuestas_correctas_count > 1;
        badge.style.display = isMultiple ? 'block' : 'none';
        if (isMultiple) {
            badge.innerHTML = `<span style="background:#ffc107;color:#212529;padding:6px 14px;border-radius:8px;font-weight:bold;">⚠️ Selección múltiple: Elige ${data.respuestas_correctas_count} opciones</span>`;
        }
    }

    const questionText = document.getElementById('pregunta-texto');
    if (questionText) {
        questionText.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                <strong>Pregunta ${data.pregunta_numero} de ${data.total_preguntas}</strong>
            </div>
            ${data.pregunta}`;
    }

    mostrarOpciones(data.opciones, !!data.multiple);
    
    const answerBtn = document.getElementById('btn-responder');
    if (answerBtn) {
        answerBtn.disabled = true;
        answerBtn.textContent = 'Responder';
        answerBtn.style.backgroundColor = '#007bff';
    }
    
    UI.announceToScreenReader(`Pregunta ${data.pregunta_numero} cargada`);
}

function mostrarOpciones(opciones, esMultiple) {
    const container = document.getElementById('opciones-container');
    if (!container) return;
    
    container.innerHTML = '';
    opciones.forEach((opcion, index) => {
        const div = document.createElement('div');
        div.className = 'opcion';
        div.innerHTML = `${String.fromCharCode(65 + index)}. ${opcion}`;
        div.tabIndex = 0;
        div.dataset.index = String(index);
        div.dataset.optionText = opcion;
        
        const handler = () => seleccionarOpcion(index, div, esMultiple);
        div.addEventListener('click', handler);
        div.addEventListener('keydown', (e) => {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                handler();
            }
        });
        container.appendChild(div);
    });
}

function seleccionarOpcion(index, elemento, esMultiple) {
    const letra = String.fromCharCode(65 + index);
    const isSelected = elemento.classList.contains('seleccionada');
    const answerBtn = document.getElementById('btn-responder');

    if (esMultiple) {
        if (isSelected) {
            deseleccionarOpcion(elemento, letra);
        } else if (State.respuestasSeleccionadas.length < 2) {
            seleccionarElemento(elemento, letra);
        } else {
            const msg = '⚠️ Esta pregunta requiere exactamente 2 respuestas';
            UI.announceToScreenReader(msg);
            UI.mostrarError(msg);
            return;
        }
        if (answerBtn) answerBtn.disabled = State.respuestasSeleccionadas.length !== 2;
    } else {
        if (!isSelected) {
            // Deseleccionar otros
            for (const op of document.querySelectorAll('.opcion.seleccionada')) {
                if (op !== elemento) {
                    const idx = Number(op.dataset.index);
                    deseleccionarOpcion(op, String.fromCharCode(65 + idx));
                }
            }
            seleccionarElemento(elemento, letra);
        } else {
            deseleccionarOpcion(elemento, letra);
        }
        if (answerBtn) answerBtn.disabled = State.respuestasSeleccionadas.length === 0;
    }
}

function seleccionarElemento(elemento, letra) {
    elemento.classList.add('seleccionada');
    State.respuestasSeleccionadas.push(letra);
    UI.announceToScreenReader(`Opción ${letra} seleccionada`);
}

function deseleccionarOpcion(elemento, letra) {
    elemento.classList.remove('seleccionada');
    State.respuestasSeleccionadas = State.respuestasSeleccionadas.filter(r => r !== letra);
    UI.announceToScreenReader(`Opción ${letra} deseleccionada`);
}

async function enviarRespuesta() {
    const answerBtn = document.getElementById('btn-responder');
    const optionsContainer = document.getElementById('opciones-container');
    
    const respuestaEnviarLetras = State.respuestasSeleccionadas.join(',');
    let respuestaEnviarTextos = '';
    
    if (optionsContainer) {
        const seleccionadas = optionsContainer.querySelectorAll('.opcion.seleccionada');
        respuestaEnviarTextos = Array.from(seleccionadas)
            .map(el => el.dataset.optionText || '')
            .join(',');
    }

    try {
        const response = await fetch('/responder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                respuesta: respuestaEnviarTextos,
                respuesta_letra: respuestaEnviarLetras,
                pregunta_id: State.preguntaActual.id,
                respuestas_seleccionadas: State.respuestasSeleccionadas
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.success) {
            if (optionsContainer) {
                for (const op of optionsContainer.querySelectorAll('.opcion')) {
                    op.style.pointerEvents = 'none';
                    op.style.opacity = '0.7';
                    op.tabIndex = -1;
                }
            }
            if (answerBtn) {
                answerBtn.textContent = '✅ Guardado';
                answerBtn.style.backgroundColor = '#28a745';
            }
            
            UI.announceToScreenReader('Respuesta guardada correctamente');
            
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
    } catch (err) {
        console.error('Error enviando respuesta:', err);
        UI.mostrarError(`❌ Error: ${err.message}`);
        if (answerBtn) {
            answerBtn.disabled = false;
            answerBtn.textContent = 'Responder';
            answerBtn.style.backgroundColor = '#007bff';
        }
    }
}

function siguientePregunta() {
    const optionsContainer = document.getElementById('opciones-container');
    const answerBtn = document.getElementById('btn-responder');
    
    if (optionsContainer) {
        for (const op of optionsContainer.querySelectorAll('.opcion')) {
            op.style.pointerEvents = 'auto';
            op.style.opacity = '1';
            op.tabIndex = 0;
            op.classList.remove('seleccionada');
        }
    }
    
    if (answerBtn) {
        answerBtn.disabled = true;
        answerBtn.textContent = 'Responder';
        answerBtn.style.backgroundColor = '#007bff';
    }
    
    State.respuestasSeleccionadas = [];
    cargarPregunta();
}

async function generarPDFAutomatico() {
    UI.announceToScreenReader('Generando reporte final...');
    try {
        const response = await fetch('/generar_pdf_final', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        if (data.success) {
            mostrarEvaluacionCompleta(data);
        } else {
            mostrarEvaluacionCompleta(null, `Error: ${data.error}`);
        }
    } catch (err) {
        mostrarEvaluacionCompleta(null, 'Error de conexión generando reporte');
    }
}

function mostrarEvaluacionCompleta(datosResultado, errorPDF) {
    document.getElementById('pregunta-container').style.display = 'none';
    const progressBar = document.getElementById('barraProgreso');
    if (progressBar) {
        progressBar.style.width = '100%';
        progressBar.setAttribute('aria-valuenow', progressBar.getAttribute('aria-valuemax'));
    }
    
    document.getElementById('progreso-texto').textContent = '¡Evaluación Completada!';
    
    let mensajeResultados = '';
    let mensajePDF = '';
    
    if (datosResultado?.success) {
        mensajeResultados = `
            <div style="background:#d4edda;color:#155724;padding:15px;border-radius:8px;margin-bottom:15px;">
                <h3>📊 Resultados de tu Evaluación:</h3>
                <ul style="margin:10px 0; padding-left:20px;">
                    <li><strong>Respuestas correctas:</strong> ${datosResultado.correctas}/${datosResultado.total} (${datosResultado.porcentaje}%)</li>
                    <li><strong>Nivel final alcanzado:</strong> ${datosResultado.nivel_final}/5</li>
                    <li><strong>Puntuación total:</strong> ${datosResultado.puntos} puntos</li>
                </ul>
            </div>`;
            
        mensajePDF = datosResultado.pdf_generado
            ? '<div style="background:#cce5ff;color:#004085;padding:10px;border-radius:5px;">✅ Reporte PDF generado correctamente</div>'
            : '<div style="background:#fff3cd;color:#856404;padding:10px;border-radius:5px;">⚠️ Evaluación guardada, reporte en proceso</div>';
    }
    
    if (errorPDF) {
        mensajePDF = `<div style="background:#f8d7da;color:#721c24;padding:10px;border-radius:5px;">⚠️ ${errorPDF}</div>`;
    }
    
    const messageDiv = document.getElementById('mensaje');
    if (messageDiv) {
        messageDiv.innerHTML = `
            <div style="text-align:center;">
                <div style="background:#d4edda;color:#155724;padding:30px;border-radius:10px;border:1px solid #c3e6cb;margin-bottom:20px;">
                    <h2>🎉 ¡Evaluación Completada!</h2>
                    <p>Todas tus respuestas han sido guardadas correctamente.</p>
                    ${mensajeResultados}
                    ${mensajePDF}
                    <div style="margin-top:20px;">
                        <p><strong>Los resultados serán enviados a Recursos Humanos.</strong></p>
                        <small style="color:#6c757d;">Puedes cerrar esta ventana de forma segura.</small>
                    </div>
                </div>
            </div>`;
        messageDiv.style.display = 'block';
    }
    UI.announceToScreenReader('Evaluación completada exitosamente.');
}

// ==========================================
// Inicialización
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    obtenerConfiguracion();

    const candidateForm = document.getElementById('candidate-form');
    if (candidateForm) {
        candidateForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const fields = [
                { el: document.getElementById('nombre_completo'), err: document.getElementById('nombre-completo-error') },
                { el: document.getElementById('email'), err: document.getElementById('email-error') },
                { el: document.getElementById('telefono'), err: document.getElementById('telefono-error') }
            ];
            
            let isValid = true;
            for (const f of fields) {
                if (f.el?.hasAttribute('required') && !validateField(f.el, f.err)) {
                    isValid = false;
                }
            }
            
            if (!isValid) {
                UI.announceToScreenReader('Por favor corrige los errores');
                candidateForm.querySelector('[aria-invalid="true"]')?.focus();
                return;
            }
            
            iniciarEvaluacion();
        });
    }

    const answerBtn = document.getElementById('btn-responder');
    if (answerBtn) {
        answerBtn.addEventListener('click', () => {
            if (!State.preguntaActual) return;
            
            const isMultiple = State.preguntaActual.multiple;
            const count = State.respuestasSeleccionadas.length;
            
            if (isMultiple && count !== 2) {
                const msg = '⚠️ Esta pregunta requiere exactamente 2 respuestas';
                UI.announceToScreenReader(msg);
                UI.mostrarError(msg);
                return;
            }
            
            if (!isMultiple && count === 0) {
                UI.announceToScreenReader('Selecciona una respuesta');
                return;
            }
            
            answerBtn.disabled = true;
            answerBtn.textContent = '⏳ Guardando...';
            UI.announceToScreenReader('Guardando respuesta...');
            enviarRespuesta();
        });
    }

    // Validación en tiempo real
    const fields = [
        { id: 'nombre_completo', errorId: 'nombre-completo-error' },
        { id: 'email', errorId: 'email-error' },
        { id: 'telefono', errorId: 'telefono-error' }
    ];
    
    for (const f of fields) {
        const el = document.getElementById(f.id);
        const err = document.getElementById(f.errorId);
        if (el && err) {
            el.addEventListener('blur', () => validateField(el, err));
            el.addEventListener('input', () => UI.clearFieldError(el, err));
        }
    }

    // Navegación por teclado
    document.addEventListener('keydown', (e) => {
        const container = document.getElementById('opciones-container');
        if (!container || container.style.display === 'none') return;
        
        const opciones = Array.from(container.querySelectorAll('.opcion'));
        const currentIndex = opciones.indexOf(document.activeElement);
        
        if (currentIndex === -1) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            opciones[(currentIndex + 1) % opciones.length].focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            opciones[(currentIndex - 1 + opciones.length) % opciones.length].focus();
        }
    });

    // Términos y condiciones
    const checkbox = document.getElementById('acepta_terminos');
    const btnAceptar = document.getElementById('btn-aceptar');
    if (checkbox && btnAceptar) {
        checkbox.addEventListener('change', () => {
            btnAceptar.disabled = !checkbox.checked;
        });
    }
});
