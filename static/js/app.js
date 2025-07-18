/**
 * Sistema de Evaluación - JavaScript
 * Funcionalidades principales para la interfaz de evaluación
 */

// Variables globales
let respuestaSeleccionada = null;
let preguntaActual = null;
let evaluacionIniciada = false;

/**
 * Función para iniciar la evaluación del candidato
 */
function iniciarEvaluacion() {
    // Validar campos requeridos
    const nombre = document.getElementById('nombre_completo').value.trim();
    const documento = document.getElementById('documento').value.trim();
    const email = document.getElementById('email').value.trim();
    
    if (!nombre || !documento || !email) {
        alert('Por favor completa todos los campos marcados con *');
        return;
    }
    
    // Enviar datos al servidor
    fetch('/iniciar_evaluacion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            nombre_completo: nombre,
            documento: documento,
            email: email,
            telefono: document.getElementById('telefono').value.trim()
        })
    })
    .then(response => response.json())
    .then(data => {
        // Ocultar formulario y mostrar evaluación
        document.getElementById('datos-candidato').style.display = 'none';
        document.getElementById('info-evaluacion').style.display = 'block';
        document.getElementById('pregunta-container').style.display = 'block';
        document.getElementById('nombre-candidato').textContent = nombre;
        
        evaluacionIniciada = true;
        
        // Cargar primera pregunta
        cargarPregunta();
        
        // Solo mostrar mensaje de inicio, sin revelar información de puntos
        mostrarMensaje('✅ Evaluación iniciada. Responde cada pregunta y presiona "Siguiente" para continuar.', 'completado');
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error iniciando evaluación', 'completado');
    });
}

/**
 * Función para cargar una nueva pregunta desde el servidor
 */
function cargarPregunta() {
    fetch('/obtener_pregunta')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            mostrarMensaje(data.error, 'completado');
            return;
        }
        
        // Almacenar la pregunta actual
        preguntaActual = data;
        
        // NO mostrar información del nivel o puntos al candidato
        document.getElementById('pregunta-texto').textContent = data.pregunta;
        
        // Crear opciones
        const container = document.getElementById('opciones-container');
        container.innerHTML = '';
        
        data.opciones.forEach((opcion, index) => {
            const div = document.createElement('div');
            div.className = 'opcion';
            div.textContent = `${String.fromCharCode(65 + index)}) ${opcion}`;
            div.onclick = () => seleccionarOpcion(index, div);
            container.appendChild(div);
        });
        
        // Resetear estado
        respuestaSeleccionada = null;
        document.getElementById('btn-responder').disabled = true;
        document.getElementById('btn-responder').style.display = 'inline-block';
        document.getElementById('btn-siguiente').style.display = 'none';
        document.getElementById('mensaje').style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error cargando pregunta', 'completado');
    });
}

/**
 * Función para seleccionar una opción de respuesta
 * @param {number} index - Índice de la opción seleccionada
 * @param {HTMLElement} elemento - Elemento DOM de la opción
 */
function seleccionarOpcion(index, elemento) {
    // Remover selección anterior
    document.querySelectorAll('.opcion').forEach(op => {
        op.classList.remove('seleccionada');
    });
    
    // Seleccionar nueva opción
    elemento.classList.add('seleccionada');
    respuestaSeleccionada = index;
    document.getElementById('btn-responder').disabled = false;
}

/**
 * Función para enviar la respuesta seleccionada al servidor
 */
function responder() {
    if (respuestaSeleccionada === null) {
        alert('Por favor selecciona una respuesta');
        return;
    }
    
    if (!preguntaActual) {
        alert('Error: No hay pregunta cargada');
        return;
    }
    
    fetch('/responder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            respuesta: respuestaSeleccionada,
            pregunta_id: preguntaActual.id
        })
    })
    .then(response => response.json())
    .then(data => {
        // NO mostrar información de puntos o nivel al candidato
        // NO mostrar si la respuesta es correcta o incorrecta
        
        // Deshabilitar opciones
        document.querySelectorAll('.opcion').forEach(op => {
            op.style.pointerEvents = 'none';
        });
        
        document.getElementById('btn-responder').style.display = 'none';
        
        if (data.hay_mas) {
            document.getElementById('btn-siguiente').style.display = 'inline-block';
        } else {
            mostrarMensaje('🎉 ¡Evaluación completada! Gracias por participar.', 'completado');
            document.getElementById('btn-reiniciar').style.display = 'inline-block';
            document.getElementById('btn-generar-pdf').style.display = 'inline-block';
            document.getElementById('btn-guardar-drive').style.display = 'inline-block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error enviando respuesta', 'completado');
    });
}

/**
 * Función para avanzar a la siguiente pregunta
 */
function siguientePregunta() {
    // Habilitar opciones
    document.querySelectorAll('.opcion').forEach(op => {
        op.style.pointerEvents = 'auto';
        op.classList.remove('seleccionada');
    });
    
    // Mostrar el botón responder y ocultar el de siguiente
    document.getElementById('btn-responder').style.display = 'inline-block';
    document.getElementById('btn-siguiente').style.display = 'none';
    document.getElementById('mensaje').style.display = 'none';
    
    cargarPregunta();
}

/**
 * Función para reiniciar el cuestionario
 */
function reiniciar() {
    fetch('/reiniciar', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('btn-reiniciar').style.display = 'none';
        document.getElementById('btn-responder').style.display = 'inline-block';
        cargarPregunta();
    });
}

/**
 * Función para mostrar mensajes al usuario
 * @param {string} texto - Texto del mensaje
 * @param {string} tipo - Tipo de mensaje (completado, error, etc.)
 */
function mostrarMensaje(texto, tipo) {
    const mensaje = document.getElementById('mensaje');
    mensaje.textContent = texto;
    mensaje.className = 'mensaje ' + tipo;
    mensaje.style.display = 'block';
}

/**
 * Función para guardar resultados en Google Drive
 */
function guardarEnDrive() {
    // Deshabilitar botón mientras se procesa
    const btn = document.getElementById('btn-guardar-drive');
    btn.disabled = true;
    btn.textContent = '⏳ Guardando...';
    
    fetch('/guardar_en_drive', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Respuesta del servidor:', data);
        
        if (data.error) {
            const errorMsg = data.detalle ? `${data.error}: ${data.detalle}` : data.error;
            mostrarMensaje('Error: ' + errorMsg, 'completado');
        } else {
            mostrarMensaje('✅ ' + data.mensaje, 'completado');
            if (data.link) {
                // Opcional: abrir el archivo en Drive
                console.log('Archivo guardado:', data.link);
                // Mostrar link en la interfaz
                mostrarMensaje('✅ ' + data.mensaje + '\n🔗 Ver archivo: ' + data.link, 'completado');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error de conexión', 'completado');
    })
    .finally(() => {
        // Rehabilitar botón
        btn.disabled = false;
        btn.textContent = '💾 Guardar en Drive';
    });
}

/**
 * Función para generar reporte PDF
 */
function generarPDF() {
    // Deshabilitar botón mientras se procesa
    const btn = document.getElementById('btn-generar-pdf');
    btn.disabled = true;
    btn.textContent = '⏳ Generando PDF...';
    
    fetch('/generar_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            mostrarMensaje('Error: ' + data.error, 'completado');
        } else {
            mostrarMensaje('✅ ' + data.mensaje + ' - Archivo: ' + data.archivo, 'completado');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error generando PDF', 'completado');
    })
    .finally(() => {
        // Rehabilitar botón
        btn.disabled = false;
        btn.textContent = '📄 Generar Reporte PDF';
    });
}
