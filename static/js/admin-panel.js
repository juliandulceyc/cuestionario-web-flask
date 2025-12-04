// ==========================================
// Funciones de UI y Utilidades
// ==========================================

function mostrarResultado(msg, isError = false) {
    const div = document.getElementById('tema-resultado');
    if (div) {
        div.textContent = msg;
        div.style.color = isError ? '#dc3545' : '#28a745';
    }
}

async function fetchTemasDisponibles() {
    try {
        const response = await fetch('/temas/');
        const data = await response.json();
        
        const select = document.getElementById('archivo_excel');
        if (!select) return;
        
        select.innerHTML = '';
        for (const nombre of (data.archivos || [])) {
            const opt = document.createElement('option');
            opt.value = nombre;
            opt.textContent = nombre;
            select.appendChild(opt);
        }
    } catch (error) {
        console.error('Error al cargar temas:', error);
        mostrarResultado('Error al cargar la lista de temas', true);
    }
}

// ==========================================
// Manejadores de Eventos
// ==========================================

async function handleSubirTema(e) {
    e.preventDefault();
    const input = document.getElementById('archivo_tema');
    if (!input?.files?.length) return;

    const formData = new FormData();
    formData.append('archivo_tema', input.files[0]);

    try {
        const response = await fetch('/admin/subir_tema', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            mostrarResultado(`Archivo subido: ${data.archivo}`);
            fetchTemasDisponibles();
            input.value = ''; // Limpiar input
        } else {
            mostrarResultado(`Error: ${data.error || 'No se pudo subir'}`, true);
        }
    } catch (error) {
        console.error('Error subiendo tema:', error);
        mostrarResultado('Error de conexión al subir archivo', true);
    }
}

async function handleSeleccionarTema(e) {
    e.preventDefault();
    const select = document.getElementById('archivo_excel');
    const archivo = select.value;

    try {
        const response = await fetch('/admin/seleccionar_tema', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ archivo_excel: archivo })
        });
        const data = await response.json();

        if (data.success) {
            mostrarResultado(`Tema activo: ${data.tema_activo}`);
        } else {
            mostrarResultado(`Error: ${data.error || 'No se pudo activar tema'}`, true);
        }
    } catch (error) {
        console.error('Error seleccionando tema:', error);
        mostrarResultado('Error de conexión al seleccionar tema', true);
    }
}

// ==========================================
// Funciones Globales (para onclick)
// ==========================================

// Copiar desde input (Legacy support)
globalThis.copiarUrl = function(btn) {
    const input = btn.parentElement?.querySelector('input[type="text"]');
    if (input) {
        input.select();
        input.setSelectionRange(0, 99999);
        
        // Fallback seguro
        try {
            document.execCommand('copy'); // NOSONAR
            const originalText = btn.textContent;
            btn.textContent = 'Copiado!';
            btn.style.background = '#28a745';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
            }, 1200);
        } catch (err) {
            console.error('Error al copiar', err);
        }
    }
};

// Copiar desde enlace (Modern)
globalThis.copiarURL = function(btn) {
    const link = btn.nextElementSibling;
    if (!link?.href) return;
    
    const url = link.href;
    navigator.clipboard.writeText(url).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<span class="icono-copiar"></span>Copiado!';
        setTimeout(() => { btn.innerHTML = originalHtml; }, 1200);
    }).catch(err => console.error('Error al copiar URL:', err));
};

// ==========================================
// Inicialización
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    fetchTemasDisponibles();

    const formSubir = document.getElementById('form-subir-tema');
    if (formSubir) {
        formSubir.addEventListener('submit', handleSubirTema);
    }

    const formSeleccionar = document.getElementById('form-seleccionar-tema');
    if (formSeleccionar) {
        formSeleccionar.addEventListener('submit', handleSeleccionarTema);
    }
});
