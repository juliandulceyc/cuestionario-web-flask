// ==========================================
// Utilidades Globales
// ==========================================

const Utils = {
    escapeHtml: function(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replaceAll(/[&<>"']/g, function(m) { return map[m]; });
    },

    escapeAttr: function(text) {
        if (!text && text !== 0) return '';
        return String(text)
            .replaceAll('&', '&amp;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;');
    },

    mostrarNotificacion: function(mensaje, tipo) {
        if (typeof globalThis.mostrarNotificacion === 'function') {
            globalThis.mostrarNotificacion(mensaje, tipo);
            return;
        }
        // Fallback
        const notification = document.createElement('div');
        const isSuccess = tipo === 'success';
        
        notification.style.background = isSuccess ? '#d4edda' : '#f8d7da';
        notification.style.color = isSuccess ? '#155724' : '#721c24';
        notification.style.border = isSuccess ? '1px solid #c3e6cb' : '1px solid #f5c6cb';
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', tipo === 'error' ? 'assertive' : 'polite');
        notification.textContent = mensaje;
        
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: '1000',
            maxWidth: '400px',
            animation: 'slideInRight 0.3s ease-out'
        });

        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 4000);
    },

    fallbackCopyURL: function(url) {
        const tempInput = document.createElement('input');
        tempInput.value = url;
        document.body.appendChild(tempInput);
        tempInput.select();

        try {
            document.execCommand('copy'); // NOSONAR
            Utils.mostrarNotificacion('📋 URL copiada al portapapeles', 'success');
        } catch (err) {
            console.error('Error copiando URL:', err);
            Utils.mostrarNotificacion('❌ No se pudo copiar la URL', 'error');
        }
        tempInput.remove();
    },

    copiarURL: function(url) {
        if (!url) return;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(function() {
                Utils.mostrarNotificacion('📋 URL copiada al portapapeles', 'success');
            }).catch(function(err) {
                console.error('Error copiando URL:', err);
                Utils.fallbackCopyURL(url);
            });
        } else {
            Utils.fallbackCopyURL(url);
        }
    }
};

// ==========================================
// Lógica de Negocio (Funciones Puras/Independientes)
// ==========================================

function actualizarFilaResultados(candidato) {
    try {
        const tabla = document.getElementById('tabla-resultados');
        if (!tabla || !candidato?.codigo) return;
        
        const fila = tabla.querySelector(`.fila-resultado[data-codigo="${candidato.codigo}"]`);
        if (!fila) return;
        
        const celdas = fila.getElementsByTagName('td');
        if (!celdas || celdas.length < 3) return;

        // Actualizar celdas
        celdas[0].textContent = candidato.nombre_completo || '-';
        
        if (candidato.tipo_documento && candidato.numero_documento) {
            celdas[1].textContent = `${candidato.tipo_documento}: ${candidato.numero_documento}`;
            fila.dataset.cedula = String(candidato.numero_documento.toLowerCase());
        } else {
            celdas[1].textContent = '-';
            fila.dataset.cedula = '';
        }
        
        celdas[2].textContent = candidato.email || '-';
        
        // Actualizar atributos de datos
        fila.dataset.nombre = (candidato.nombre_completo || ''.toLowerCase());
        fila.dataset.email = (candidato.email || ''.toLowerCase());
    } catch (e) {
        console.warn('No se pudo actualizar la fila de resultados:', e);
    }
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
        const phoneRegex = /^[\d\s\-+()]{7,15}$/;
        if (!phoneRegex.test(value)) {
            showFieldError(field, errorElement, 'Ingresa un teléfono válido');
            return false;
        }
    }

    if ((field.id === 'nombre_completo' || field.id === 'cargo') && value && value.length < 2) {
        const fieldName = field.id === 'nombre_completo' ? 'El nombre' : 'El cargo';
        showFieldError(field, errorElement, `${fieldName} debe tener al menos 2 caracteres`);
        return false;
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

// ==========================================
// Inicialización y Eventos
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Referencias DOM
    const listaTemas = document.getElementById('lista-temas');
    const formularioRegistro = document.getElementById('formularioRegistro');
    const candidatoForm = document.getElementById('candidatoForm');
    const listaCandidatos = document.getElementById('candidatos-lista');
    const addCandidateBtn = document.querySelector('.add-candidate-btn');

    // Inicialización
    init();

    function init() {
        setupEventListeners();
        cargarCandidatos();
        cargarArchivosTemas();
        injectStyles();
    }

    function injectStyles() {
        if (!document.querySelector('#admin-animations')) {
            const style = document.createElement('style');
            style.id = 'admin-animations';
            style.textContent = `
                @keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
                @keyframes slideOutRight { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
            `;
            document.head.appendChild(style);
        }
    }

    function cargarArchivosTemas() {
        fetch('/temas/')
            .then(r => r.json())
            .then(data => {
                if (!listaTemas) return;
                listaTemas.innerHTML = '';
                for (const nombre of (data.archivos || [])) {
                    const tr = document.createElement('tr');
                    
                    const tdNombre = document.createElement('td');
                    tdNombre.textContent = nombre;
                    tdNombre.style.fontWeight = 'bold';
                    
                    const tdAccion = document.createElement('td');
                    const btn = document.createElement('button');
                    btn.className = 'btn-eliminar-tema';
                    btn.textContent = 'Eliminar';
                    btn.onclick = () => eliminarTemaExcel(nombre);
                    
                    tdAccion.appendChild(btn);
                    tr.appendChild(tdNombre);
                    tr.appendChild(tdAccion);
                    listaTemas.appendChild(tr);
                }
            });
    }

    function cargarCandidatos() {
        if (!listaCandidatos) return;
        listaCandidatos.innerHTML = '<div class="loading">Cargando candidatos...</div>';

        fetch('/admin/candidatos?format=json')
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(mostrarCandidatos)
            .catch(error => {
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

        const html = candidatos.map(c => {
            const statusClass = c.evaluacion_completada ? 'status-completada' : 'status-pendiente';
            const statusText = c.evaluacion_completada ? '✅ Completada' : '⏳ Pendiente';
            
            let actionsHtml = '';
            if (!c.evaluacion_completada) {
                actionsHtml = `
                    <div style="margin-top:8px;display:flex;gap:8px;">
                        <button type="button" class="copy-btn" data-url="${c.url_evaluacion || ''}" style="background:#007bff;color:white;padding:4px 10px;border-radius:5px;border:none;cursor:pointer;">📋 Copiar URL</button>
                        <a href="${c.url_evaluacion || '#'}" target="_blank" class="eval-link" style="background:#28a745;color:white;padding:4px 10px;border-radius:5px;text-decoration:none;display:inline-block;">🔗 Abrir Evaluación</a>
                    </div>`;
            }

            return `
                <div class="candidato-card">
                    <div class="candidato-info">
                        <h3>${Utils.escapeHtml(c.nombre_completo)}</h3>
                        ${c.tipo_documento && c.numero_documento ? `<p>🆔 ${Utils.escapeHtml(c.tipo_documento)}: ${Utils.escapeHtml(c.numero_documento)}</p>` : ''}
                        <p>📧 ${Utils.escapeHtml(c.email)}</p>
                        <p>🔑 Código: ${Utils.escapeHtml(c.codigo)}</p>
                        <p>👔 ${Utils.escapeHtml(c.cargo || 'N/A')}</p>
                        ${c.telefono && c.telefono !== 'N/A' ? `<p>📞 ${Utils.escapeHtml(c.telefono)}</p>` : ''}
                    </div>
                    <div class="candidato-status">
                        <span class="${statusClass}">${statusText}</span>
                        ${actionsHtml}
                        <div style="margin-top:8px;display:flex;gap:8px;">
                            <button type="button" class="edit-btn" 
                                data-codigo="${c.codigo || ''}"
                                data-tipo-documento="${c.tipo_documento || ''}"
                                data-numero-documento="${c.numero_documento || ''}"
                                data-nombre-completo="${c.nombre_completo || ''}"
                                data-email="${c.email || ''}"
                                data-telefono="${c.telefono || ''}"
                                data-cargo="${c.cargo || ''}"
                                style="background:#6c757d;color:white;padding:4px 10px;border-radius:5px;border:none;cursor:pointer;">✏️ Editar</button>
                            <button type="button" class="delete-btn" data-codigo="${c.codigo}" style="background:#dc3545;color:white;padding:4px 10px;border-radius:5px;border:none;cursor:pointer;">🗑️ Eliminar</button>
                        </div>
                    </div>
                </div>`;
        }).join('');

        listaCandidatos.innerHTML = html;
        bindDynamicEvents();
    }

    function bindDynamicEvents() {
        const onCopySuccess = (btn) => {
            Utils.mostrarNotificacion('📋 URL copiada al portapapeles', 'success');
            const originalText = btn.innerHTML;
            btn.innerHTML = '✅ Copiado!';
            setTimeout(() => { btn.innerHTML = originalText; }, 2000);
        };
        // Copy URL buttons
        for (const btn of document.querySelectorAll('.copy-btn')) {
            btn.onclick = () => {
                const url = btn.dataset.url;
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(url)
                        .then(() => onCopySuccess(btn))
                        .catch(() => Utils.fallbackCopyURL(url));
                } else {
                    Utils.fallbackCopyURL(url);
                }
            };
        }

        // Delete buttons
        for (const btn of document.querySelectorAll('.delete-btn')) {
            btn.onclick = () => {
                const codigo = btn.dataset.codigo;
                eliminarCandidato(codigo, btn);
            };
        }

        // Edit buttons
        for (const btn of document.querySelectorAll('.edit-btn')) {
            btn.onclick = () => globalThis.abrirEditarCandidatoDesdeBoton(btn);
        }
    }

    function setupEventListeners() {
        if (addCandidateBtn) {
            addCandidateBtn.addEventListener('click', mostrarFormulario);
        }

        const cancelBtn = document.querySelector('button[data-action="cancel"]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', ocultarFormulario);
        }

        if (candidatoForm) {
            candidatoForm.addEventListener('submit', e => {
                e.preventDefault();
                registrarCandidato();
            });
        }

        // Validación en tiempo real
        const fields = [
            { id: 'nombre_completo', errorId: 'nombre-completo-error' },
            { id: 'email', errorId: 'email-error' },
            { id: 'telefono', errorId: 'telefono-error' },
            { id: 'cargo', errorId: 'cargo-error' }
        ];

        for (const f of fields) {
            const input = document.getElementById(f.id);
            const errorElement = document.getElementById(f.errorId);
            if (input && errorElement) {
                input.addEventListener('blur', () => validateField(input, errorElement));
                input.addEventListener('input', () => clearFieldError(input, errorElement));
            }
        }

        // Formulario de edición
        const editForm = document.getElementById('form-editar-candidato');
        if (editForm) {
            editForm.addEventListener('submit', handleEditSubmit);
        }

        // Botones estáticos
        for (const btn of document.querySelectorAll('.btn-copiar-url')) {
            btn.addEventListener('click', function() {
                Utils.copiarURL(this.dataset.url);
            });
        }

        const btnCerrarModal = document.querySelector('#modal-editar .btn-secondary');
        if (btnCerrarModal) {
            btnCerrarModal.addEventListener('click', globalThis.cerrarModalEditar);
        }

        const btnLimpiarFiltros = document.querySelector('.btn-limpiar-filtros');
        if (btnLimpiarFiltros) {
            btnLimpiarFiltros.addEventListener('click', globalThis.limpiarFiltrosResultados);
        }
    }

    function handleEditSubmit(e) {
        e.preventDefault();
        const payload = {
            codigo: document.getElementById('edit-codigo').value,
            tipo_documento: document.getElementById('edit-tipo_documento').value,
            numero_documento: document.getElementById('edit-numero_documento').value,
            nombre_completo: document.getElementById('edit-nombre_completo').value,
            email: document.getElementById('edit-email').value,
            telefono: document.getElementById('edit-telefono').value,
            cargo: document.getElementById('edit-cargo').value
        };

        fetch('/admin/actualizar_candidato', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            if (!data.success) throw new Error(data.error || 'Error al actualizar');
            globalThis.cerrarModalEditar();
            cargarCandidatos();
            if (data.candidato) actualizarFilaResultados(data.candidato);
            Utils.mostrarNotificacion('Candidato actualizado', 'success');
        })
        .catch(err => Utils.mostrarNotificacion(err.message, 'error'));
    }

    function mostrarFormulario() {
        if (formularioRegistro) {
            formularioRegistro.style.display = 'block';
            formularioRegistro.scrollIntoView({ behavior: 'smooth', block: 'start' });
            const firstField = document.getElementById('nombre_completo');
            if (firstField) setTimeout(() => firstField.focus(), 300);
        }
    }

    function ocultarFormulario() {
        if (formularioRegistro) formularioRegistro.style.display = 'none';
        if (candidatoForm) {
            candidatoForm.reset();
            for (const el of candidatoForm.querySelectorAll('.error-message')) { el.textContent = ''; }
            for (const el of candidatoForm.querySelectorAll('input')) { el.style.borderColor = ''; }
        }
    }

    function registrarCandidato() {
        const fields = ['tipo_documento', 'numero_documento', 'nombre_completo', 'email', 'cargo'];
        const data = {};
        let hasEmpty = false;

        for (const id of fields) {
            const val = document.getElementById(id).value;
            if (!val) hasEmpty = true;
            data[id] = val;
        }

        if (hasEmpty) {
            Utils.mostrarNotificacion('Todos los campos son obligatorios', 'error');
            return;
        }

        fetch('/admin/registrar_candidato', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(() => {
            Utils.mostrarNotificacion('✅ Candidato registrado correctamente', 'success');
            ocultarFormulario();
            cargarCandidatos();
        })
        .catch(err => Utils.mostrarNotificacion(err, 'error'));
    }

    // Exponer funciones necesarias globalmente
    globalThis.recargarCandidatos = cargarCandidatos;
    
    globalThis.eliminarTemaExcel = function(nombre) {
        if (!confirm('¿Seguro que deseas eliminar el archivo ' + nombre + '?')) return;
        fetch('/admin/eliminar_tema', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ archivo_excel: nombre })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                Utils.mostrarNotificacion('Archivo eliminado correctamente', 'success');
                cargarArchivosTemas();
            } else {
                Utils.mostrarNotificacion('Error eliminando archivo: ' + (data.error || 'Desconocido'), 'error');
            }
        });
    };

    globalThis.eliminarCandidato = function(codigo, botonElement) {
        if (!confirm('¿Estás seguro de que deseas eliminar este candidato?')) return;
        
        botonElement.disabled = true;
        botonElement.textContent = '⏳ Eliminando...';
        
        fetch('/admin/eliminar_candidato', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo: codigo })
        })
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            if (data.success) {
                const cardElement = botonElement.closest('.candidato-card');
                if (cardElement) {
                    cardElement.style.transition = 'opacity 0.3s, transform 0.3s';
                    cardElement.style.opacity = '0';
                    cardElement.style.transform = 'scale(0.9)';
                    setTimeout(() => {
                        cardElement.remove();
                        Utils.mostrarNotificacion('✅ Candidato eliminado exitosamente', 'success');
                        if (document.querySelectorAll('.candidato-card').length === 0) {
                            listaCandidatos.innerHTML = '<div style="text-align:center;padding:40px;color:#999;font-size:18px;"><p>📭 No hay candidatos registrados</p></div>';
                        }
                    }, 300);
                }
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            Utils.mostrarNotificacion('❌ Error al eliminar candidato: ' + err.message, 'error');
            botonElement.disabled = false;
            botonElement.textContent = '🗑️ Eliminar';
        });
    };

    globalThis.aplicarFiltrosResultados = function() {
        const ids = ['nombre', 'cedula', 'email', 'tema', 'estado', 'nivel'];
        const filters = {};
        let allEmpty = true;

        for (const key of ids) {
            const el = document.getElementById(`filtro-resultado-${key}`);
            if (el?.value) {
                filters[key] = el.value.toLowerCase();
                allEmpty = false;
            }
        }

        if (allEmpty) return; // Opcional: mostrar todos si no hay filtros

        const filas = document.querySelectorAll('.fila-resultado');
        let visibleCount = 0;

        for (const fila of filas) {
            const data = {
                nombre: fila.dataset.nombre || '',
                cedula: fila.dataset.cedula || '',
                email: fila.dataset.email || '',
                tema: fila.dataset.tema || '',
                nivel: fila.dataset.nivel || '',
                estado: fila.dataset.tieneResultado || 'no'
            };

            const matches = ids.every(key => {
                if (!filters[key]) return true;
                return data[key].includes(filters[key]) || data[key] === filters[key];
            });

            if (matches) {
                fila.style.display = '';
                visibleCount++;
            } else {
                fila.style.display = 'none';
            }
        }

        const contadorDiv = document.getElementById('contador-resultados');
        if (contadorDiv) {
            contadorDiv.textContent = visibleCount === filas.length 
                ? `📊 Mostrando todos los resultados (${filas.length})`
                : `📊 Mostrando ${visibleCount} de ${filas.length} resultados`;
        }
    };

    globalThis.limpiarFiltrosResultados = function() {
        for (const key of ['nombre', 'cedula', 'email', 'tema', 'estado', 'nivel']) {
            const el = document.getElementById(`filtro-resultado-${key}`);
            if (el) el.value = '';
        }
        globalThis.aplicarFiltrosResultados();
    };

    // Bind filter events
    for (const key of ['nombre', 'cedula', 'email', 'tema', 'estado', 'nivel']) {
        const el = document.getElementById(`filtro-resultado-${key}`);
        if (el) {
            el.addEventListener('input', globalThis.aplicarFiltrosResultados);
            el.addEventListener('change', globalThis.aplicarFiltrosResultados);
        }
    }
});

// Global helpers needed for modal interaction
globalThis.abrirEditarCandidato = function(c) {
    const modal = document.getElementById('modal-editar');
    if (!modal) return;
    
    for (const key of ['codigo', 'tipo_documento', 'numero_documento', 'nombre_completo', 'email', 'telefono', 'cargo']) {
        const el = document.getElementById(`edit-${key}`);
        if (el) el.value = c[key] || '';
    }
    
    modal.style.display = 'flex';
};

globalThis.abrirEditarCandidatoDesdeBoton = function(btn) {
    const c = {};
    for (const key of ['codigo', 'tipo_documento', 'numero_documento', 'nombre_completo', 'email', 'telefono', 'cargo']) {
        c[key] = btn.getAttribute(`data-${key.replace('_', '-')}`) || '';
    }
    globalThis.abrirEditarCandidato(c);
};

globalThis.cerrarModalEditar = function() {
    const modal = document.getElementById('modal-editar');
    if (modal) modal.style.display = 'none';
};

globalThis.copiarURL = Utils.copiarURL;
