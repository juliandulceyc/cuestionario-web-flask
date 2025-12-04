document.addEventListener('DOMContentLoaded', function() {
    // Cargar lista de archivos Excel disponibles
    fetchTemasDisponibles();

    // Subir archivo Excel
    const formSubir = document.getElementById('form-subir-tema');
    if (formSubir) {
        formSubir.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('archivo_tema');
            if (!input.files.length) return;
            const formData = new FormData();
            formData.append('archivo_tema', input.files[0]);
            fetch('/admin/subir_tema', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    mostrarResultado('Archivo subido: ' + data.archivo);
                    fetchTemasDisponibles();
                } else {
                    mostrarResultado('Error: ' + (data.error || 'No se pudo subir'));
                }
            });
        });
    }

    // Seleccionar tema activo
    const formSeleccionar = document.getElementById('form-seleccionar-tema');
    if (formSeleccionar) {
        formSeleccionar.addEventListener('submit', function(e) {
            e.preventDefault();
            const select = document.getElementById('archivo_excel');
            const archivo = select.value;
            fetch('/admin/seleccionar_tema', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ archivo_excel: archivo })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    mostrarResultado('Tema activo: ' + data.tema_activo);
                } else {
                    mostrarResultado('Error: ' + (data.error || 'No se pudo activar tema'));
                }
            });
        });
    }

    function fetchTemasDisponibles() {
        fetch('/temas/')
            .then(r => r.json())
            .then(data => {
                const select = document.getElementById('archivo_excel');
                if (!select) return;
                select.innerHTML = '';
                (data.archivos || []).forEach(function(nombre) {
                    const opt = document.createElement('option');
                    opt.value = nombre;
                    opt.textContent = nombre;
                    select.appendChild(opt);
                });
            });
    }

    function mostrarResultado(msg) {
        const div = document.getElementById('tema-resultado');
        if (div) div.textContent = msg;
    }
});
function copiarUrl(btn) {
    var input = btn.parentElement.querySelector('input[type="text"]');
    if (input) {
        input.select();
        input.setSelectionRange(0, 99999);
        document.execCommand('copy');
        btn.textContent = 'Copiado!';
        btn.style.background = '#28a745';
        setTimeout(function(){
            btn.textContent = 'Copiar URL';
            btn.style.background = '';
        }, 1200);
    }
}


window.copiarURL = function(btn) {
    const url = btn.nextElementSibling.href;
    navigator.clipboard.writeText(url);
    btn.innerHTML = '<span class=\icono-copiar\></span>Copiado!';
    setTimeout(() => { btn.innerHTML = '<span class=\icono-copiar\></span>Copiar URL'; }, 1200);
}
