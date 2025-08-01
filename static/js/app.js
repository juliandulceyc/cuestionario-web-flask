// Sistema de Evaluación - Funcionalidades principales
// Variables globales
let respuestaSeleccionada = null, preguntaActual = null;

function iniciarEvaluacion() {
    const nombre = document.getElementById('nombre_completo').value.trim();
    const email = document.getElementById('email').value.trim();
    if (!nombre || !email) return alert('Completa todos los campos obligatorios');
    fetch('/iniciar_evaluacion', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ nombre_completo: nombre, email })
    })
    .then(r => r.json())
    .then(() => {
        document.getElementById('datos-candidato').style.display = 'none';
        document.getElementById('info-evaluacion').style.display = 'block';
        document.getElementById('pregunta-container').style.display = 'block';
        document.getElementById('nombre-candidato').textContent = nombre;
        cargarPregunta();
    });
}

function cargarPregunta() {
    fetch('/obtener_pregunta')
    .then(r => r.json())
    .then(data => {
        if (data.error) return mostrarMensaje(data.error);
        preguntaActual = data;
        document.getElementById('pregunta-texto').textContent = data.pregunta;
        const container = document.getElementById('opciones-container');
        container.innerHTML = '';
        data.opciones.forEach((op, i) => {
            const div = document.createElement('div');
            div.className = 'opcion';
            div.textContent = `${String.fromCharCode(65 + i)}) ${op}`;
            div.onclick = () => seleccionarOpcion(i, div);
            container.appendChild(div);
        });
        respuestaSeleccionada = null;
        document.getElementById('btn-responder').disabled = true;
        document.getElementById('btn-responder').style.display = 'inline-block';
        document.getElementById('btn-siguiente').style.display = 'none';
        document.getElementById('mensaje').style.display = 'none';
    });
}

function seleccionarOpcion(index, el) {
    document.querySelectorAll('.opcion').forEach(op => op.classList.remove('seleccionada'));
    el.classList.add('seleccionada');
    respuestaSeleccionada = index;
    document.getElementById('btn-responder').disabled = false;
}

function responder() {
    if (respuestaSeleccionada === null || !preguntaActual) return alert('Selecciona una respuesta');
    fetch('/responder', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ respuesta: respuestaSeleccionada, pregunta_id: preguntaActual.id })
    })
    .then(r => r.json())
    .then(data => {
        document.querySelectorAll('.opcion').forEach(op => op.style.pointerEvents = 'none');
        document.getElementById('btn-responder').style.display = 'none';
        if (data.hay_mas) document.getElementById('btn-siguiente').style.display = 'inline-block';
        else { 
            console.log("=== EVALUACIÓN TERMINADA ===");
            mostrarMensajeFinalizacion(); 
            console.log("Llamando a generarPDFAutomatico...");
            generarPDFAutomatico(); 
        }
    });
}

function siguientePregunta() {
    document.querySelectorAll('.opcion').forEach(op => {
        op.style.pointerEvents = 'auto'; op.classList.remove('seleccionada');
    });
    document.getElementById('btn-responder').style.display = 'inline-block';
    document.getElementById('btn-siguiente').style.display = 'none';
    document.getElementById('mensaje').style.display = 'none';
    cargarPregunta();
}

function mostrarMensaje(texto) {
    const mensaje = document.getElementById('mensaje');
    mensaje.textContent = texto;
    mensaje.style.display = 'block';
}

function mostrarMensajeFinalizacion() {
    document.getElementById('mensaje').innerHTML = `
        <div style="text-align:center;padding:30px;background:#27ae60;color:white;border-radius:15px;margin:20px 0;">
            <h2>🎉 ¡Evaluación Completada!</h2>
            <p>Gracias por completar la evaluación. Sus respuestas han sido registradas.</p>
        </div>`;
    document.getElementById('mensaje').style.display = 'block';
    document.getElementById('pregunta-container').style.display = 'none';
    document.getElementById('info-evaluacion').innerHTML = `<strong>Candidato:</strong> <span id="nombre-candidato">${document.getElementById('nombre-candidato').textContent}</span> | <strong>✅ Evaluación Finalizada</strong>`;
}

function generarPDFAutomatico() {
    console.log('Generando PDF automáticamente...');
    fetch('/generar_pdf', { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        console.log('Respuesta de generar_pdf:', data);
        if (data.archivo) {
            console.log('Subiendo PDF a Drive:', data.archivo);
            fetch('/guardar_en_drive', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ pdf_path: data.archivo })
            })
            .then(r => r.json())
            .then(resp => {
                console.log('Respuesta de guardar_en_drive:', resp);
                if (resp.link) {
                    console.log('PDF guardado exitosamente en Drive:', resp.link);
                } else {
                    console.error('Error guardando en Drive:', resp.error);
                }
            })
            .catch(err => console.error('Error en guardar_en_drive:', err));
        } else {
            console.error('No se generó el PDF:', data.error);
        }
    })
    .catch(err => console.error('Error en generar_pdf:', err));
}
