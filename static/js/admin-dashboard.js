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
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                toast: true,
                position: 'top-end',
                icon: tipo === 'error' ? 'error' : 'success',
                title: mensaje,
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer)
                    toast.addEventListener('mouseleave', Swal.resumeTimer)
                }
            });
            return;
        }

        // Fallback implementation
        if (typeof globalThis.mostrarNotificacion === 'function' && globalThis.mostrarNotificacion !== Utils.mostrarNotificacion) {
            globalThis.mostrarNotificacion(mensaje, tipo);
            return;
        }
        
        const notification = document.createElement('div');
        const isSuccess = tipo === 'success';
        
        notification.className = `fixed top-5 right-5 z-50 max-w-sm w-full shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden ${isSuccess ? 'bg-green-50 text-green-800 ring-green-600/20' : 'bg-red-50 text-red-800 ring-red-600/20'}`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', tipo === 'error' ? 'assertive' : 'polite');
        
        notification.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <span class="material-symbols-outlined ${isSuccess ? 'text-green-400' : 'text-red-400'}">${isSuccess ? 'check_circle' : 'error'}</span>
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium">${mensaje}</p>
                    </div>
                    <div class="ml-4 flex flex-shrink-0">
                        <button type="button" class="inline-flex rounded-md bg-transparent text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2" onclick="this.closest('[role=alert]').remove()">
                            <span class="sr-only">Close</span>
                            <span class="material-symbols-outlined text-sm">close</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        notification.style.animation = 'slideInRight 0.3s ease-out';

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

    const filas = document.querySelectorAll('.fila-resultado');
    let visibleCount = 0;

    for (const fila of filas) {
        if (allEmpty) {
            fila.style.display = '';
            visibleCount++;
            continue;
        }

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
            return data[key].includes(filters[key]);
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

// ==========================================
// Inicialización y Eventos
// ==========================================

function handleCopyClick(btnCopiar) {
    const url = btnCopiar.dataset.url;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url)
            .then(() => {
                Utils.mostrarNotificacion('📋 URL copiada', 'success');
                const originalText = btnCopiar.innerHTML;
                btnCopiar.innerHTML = '✅ Copiado!';
                setTimeout(() => { btnCopiar.innerHTML = originalText; }, 2000);
            })
            .catch(() => Utils.fallbackCopyURL(url));
    } else {
        Utils.fallbackCopyURL(url);
    }
}

function handleGlobalClick(e) {
    // Botón Editar
    const btnEditar = e.target.closest('.edit-btn, .btn-editar');
    if (btnEditar) {
        e.preventDefault();
        console.log('Click en editar', btnEditar);
        globalThis.abrirEditarCandidatoDesdeBoton(btnEditar);
        return;
    }

    // Botón Eliminar
    const btnEliminar = e.target.closest('.delete-btn, .btn-eliminar');
    if (btnEliminar) {
        e.preventDefault();
        const codigo = btnEliminar.dataset.codigo;
        globalThis.eliminarCandidato(codigo, btnEliminar);
        return;
    }

    // Botón Copiar URL
    const btnCopiar = e.target.closest('.copy-btn, .btn-copiar-url');
    if (btnCopiar) {
        e.preventDefault();
        handleCopyClick(btnCopiar);
    }
}


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
                    tr.className = 'hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors';
                    
                    const tdNombre = document.createElement('td');
                    tdNombre.textContent = nombre;
                    tdNombre.className = 'whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-white sm:pl-6';
                    
                    const tdAccion = document.createElement('td');
                    tdAccion.className = 'whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400';
                    
                    const btn = document.createElement('button');
                    btn.className = 'btn-eliminar-tema inline-flex items-center rounded bg-red-600 px-2 py-1 text-xs font-semibold text-white shadow-sm hover:bg-red-500 transition-colors';
                    btn.innerHTML = '<span class="material-symbols-outlined text-sm mr-1">delete</span> Eliminar';
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
            listaCandidatos.innerHTML = '<div class="col-span-full text-center py-10 text-gray-500 dark:text-gray-400"><span class="material-symbols-outlined text-4xl mb-2 block">assignment_late</span>No hay candidatos registrados</div>';
            return;
        }

        const html = candidatos.map(c => {
            const statusBadge = c.evaluacion_completada 
                ? '<span class="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-300">Completada</span>' 
                : '<span class="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">Pendiente</span>';
            
            let actionsHtml = '';
            if (!c.evaluacion_completada) {
                actionsHtml = `
                    <div class="flex gap-2">
                        <button type="button" data-url="${c.url_evaluacion || ''}" class="copy-btn flex-1 inline-flex justify-center items-center rounded bg-blue-600 px-2 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-500 transition-colors">
                            <span class="material-symbols-outlined text-sm mr-1">content_copy</span> Copiar URL
                        </button>
                        <a href="${c.url_evaluacion || '#'}" target="_blank" class="eval-link flex-1 inline-flex justify-center items-center rounded bg-green-600 px-2 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-green-500 transition-colors no-underline">
                            <span class="material-symbols-outlined text-sm mr-1">open_in_new</span> Abrir
                        </a>
                    </div>`;
            }

            return `
                <div class="candidato-card bg-white dark:bg-gray-800 overflow-hidden rounded-lg shadow border border-gray-200 dark:border-gray-700 flex flex-col" data-cedula="${c.codigo}" data-nombre="${Utils.escapeHtml(c.nombre_completo)}" data-estado="${c.evaluacion_completada ? 'completada' : 'pendiente'}">
                    <div class="px-4 py-5 sm:p-6 flex-1">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-medium leading-6 text-gray-900 dark:text-white truncate" title="${Utils.escapeHtml(c.nombre_completo)}">${Utils.escapeHtml(c.nombre_completo)}</h3>
                            ${statusBadge}
                        </div>
                        <div class="space-y-2 text-sm text-gray-500 dark:text-gray-400">
                            ${c.tipo_documento && c.numero_documento ? `<p class="flex items-center"><span class="material-symbols-outlined text-base mr-2">badge</span> ${Utils.escapeHtml(c.tipo_documento)}: ${Utils.escapeHtml(c.numero_documento)}</p>` : ''}
                            <p class="flex items-center"><span class="material-symbols-outlined text-base mr-2">mail</span> <span class="truncate">${Utils.escapeHtml(c.email)}</span></p>
                            <p class="flex items-center"><span class="material-symbols-outlined text-base mr-2">key</span> Código: ${Utils.escapeHtml(c.codigo)}</p>
                            <p class="flex items-center"><span class="material-symbols-outlined text-base mr-2">work</span> ${Utils.escapeHtml(c.cargo || 'N/A')}</p>
                            ${c.telefono && c.telefono !== 'N/A' ? `<p class="flex items-center"><span class="material-symbols-outlined text-base mr-2">call</span> ${Utils.escapeHtml(c.telefono)}</p>` : ''}
                        </div>
                    </div>
                    <div class="bg-gray-50 dark:bg-gray-700/50 px-4 py-4 sm:px-6 flex flex-col gap-2">
                        ${actionsHtml}
                        <div class="flex gap-2 mt-2">
                            <button type="button" class="edit-btn flex-1 inline-flex justify-center items-center rounded bg-gray-600 px-2 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-gray-500 transition-colors" 
                                data-codigo="${c.codigo || ''}"
                                data-tipo-documento="${c.tipo_documento || ''}"
                                data-numero-documento="${c.numero_documento || ''}"
                                data-nombre-completo="${c.nombre_completo || ''}"
                                data-email="${c.email || ''}"
                                data-telefono="${c.telefono || ''}"
                                data-cargo="${c.cargo || ''}">
                                <span class="material-symbols-outlined text-sm mr-1">edit</span> Editar
                            </button>
                            <button type="button" class="delete-btn flex-1 inline-flex justify-center items-center rounded bg-red-600 px-2 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-red-500 transition-colors" data-codigo="${c.codigo}">
                                <span class="material-symbols-outlined text-sm mr-1">delete</span> Eliminar
                            </button>
                        </div>
                    </div>
                </div>`;
        }).join('');

        listaCandidatos.innerHTML = html;
        // bindDynamicEvents(); // Ya no es necesario por la delegación
    }

    function setupEventListeners() {
        // Delegación de eventos
        document.addEventListener('click', handleGlobalClick);

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

        // AJAX para selección de tema
        const formSeleccionarTema = document.getElementById('form-seleccionar-tema');
        if (formSeleccionarTema) {
            formSeleccionarTema.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                
                fetch(this.action, {
                    method: 'POST',
                    body: formData
                })
                .then(r => {
                    if (r.redirected) {
                        // Si el servidor redirige, asumimos éxito y actualizamos UI
                        // Pero idealmente el servidor debería devolver JSON
                        // Como no podemos cambiar el backend fácilmente, recargamos o intentamos inferir
                        // Si el backend devuelve HTML, esto fallará al parsear JSON.
                        // Vamos a asumir que el backend redirige a /admin/dashboard
                        window.location.reload(); 
                        return;
                    }
                    // Si devuelve texto/html, probablemente sea la página recargada
                    return r.text().then(text => {
                        // Actualizar solo el texto del tema activo si es posible
                        // O mostrar alerta y recargar
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                title: '¡Tema Activado!',
                                text: 'El tema de evaluación ha sido actualizado.',
                                icon: 'success',
                                confirmButtonText: 'Aceptar'
                            }).then(() => {
                                window.location.reload();
                            });
                        } else {
                            alert('Tema actualizado');
                            window.location.reload();
                        }
                    });
                })
                .catch(err => {
                    console.error(err);
                    Utils.mostrarNotificacion('Error al cambiar tema', 'error');
                });
            });
        }

        // AJAX para subir tema
        const formSubirTema = document.getElementById('form-subir-tema');
        if (formSubirTema) {
            formSubirTema.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const btnSubmit = this.querySelector('button[type="submit"]');
                const originalText = btnSubmit.innerHTML;
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = 'Subiendo...';

                fetch(this.action, {
                    method: 'POST',
                    body: formData
                })
                .then(r => {
                    // Similar logic: check if redirect or content
                    // Assuming backend redirects on success
                    if (r.redirected || r.ok) {
                         if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                title: '¡Archivo Subido!',
                                text: 'El nuevo tema ha sido cargado correctamente.',
                                icon: 'success',
                                confirmButtonText: 'Aceptar'
                            }).then(() => {
                                window.location.reload();
                            });
                        } else {
                            alert('Archivo subido');
                            window.location.reload();
                        }
                    } else {
                        throw new Error('Error en la subida');
                    }
                })
                .catch(err => {
                    Utils.mostrarNotificacion('Error al subir archivo', 'error');
                    btnSubmit.disabled = false;
                    btnSubmit.innerHTML = originalText;
                });
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
            
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¡Actualizado!',
                    text: 'Candidato actualizado correctamente',
                    icon: 'success',
                    confirmButtonText: 'Aceptar'
                });
            } else {
                Utils.mostrarNotificacion('Candidato actualizado', 'success');
            }
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
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¡Registrado!',
                    text: 'Candidato registrado correctamente',
                    icon: 'success',
                    confirmButtonText: 'Aceptar'
                });
            } else {
                Utils.mostrarNotificacion('✅ Candidato registrado correctamente', 'success');
            }
            ocultarFormulario();
            cargarCandidatos();
        })
        .catch(err => Utils.mostrarNotificacion(err, 'error'));
    }

    // Exponer funciones necesarias globalmente
    globalThis.recargarCandidatos = cargarCandidatos;
    
    globalThis.eliminarTemaExcel = function(nombre) {
        const performDelete = () => {
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

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: '¿Estás seguro?',
                text: `¿Deseas eliminar el archivo ${nombre}?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    performDelete();
                }
            });
        } else {
            if (confirm('¿Seguro que deseas eliminar el archivo ' + nombre + '?')) {
                performDelete();
            }
        }
    };

    globalThis.eliminarCandidato = function(codigo, botonElement) {
        const performDelete = () => {
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

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: '¿Estás seguro?',
                text: "No podrás revertir esta acción",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    performDelete();
                }
            });
        } else {
            if (confirm('¿Estás seguro de que deseas eliminar este candidato?')) {
                performDelete();
            }
        }
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
    if (!modal) {
        console.error('Modal #modal-editar no encontrado en el DOM');
        return;
    }
    
    for (const key of ['codigo', 'tipo_documento', 'numero_documento', 'nombre_completo', 'email', 'telefono', 'cargo']) {
        const el = document.getElementById(`edit-${key}`);
        if (el) el.value = c[key] || '';
    }
    
    modal.classList.remove('hidden');
    // Ensure aria-hidden is updated for accessibility
    modal.setAttribute('aria-hidden', 'false');
    console.log('Modal abierto para:', c.codigo);
};

globalThis.abrirEditarCandidatoDesdeBoton = function(btn) {
    const c = {};
    for (const key of ['codigo', 'tipo_documento', 'numero_documento', 'nombre_completo', 'email', 'telefono', 'cargo']) {
        // Handle both hyphenated attributes and camelCase dataset properties if needed, 
        // but getAttribute is safer for the exact HTML attribute name.
        let val = btn.getAttribute(`data-${key.replace('_', '-')}`);
        if (val === null) val = '';
        c[key] = val;
    }
    globalThis.abrirEditarCandidato(c);
};

globalThis.cerrarModalEditar = function() {
    const modal = document.getElementById('modal-editar');
    if (modal) {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
    }
};

globalThis.copiarURL = Utils.copiarURL;
