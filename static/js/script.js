// Variables globales
let respuestaSeleccionada = null;
let cuestionarioActivo = false;

// Elementos del DOM
const elementos = {
    // Pantallas
    pantallaInicio: document.getElementById('pantalla-inicio'),
    pantallaCuestionario: document.getElementById('pantalla-cuestionario'),
    pantallaResultados: document.getElementById('pantalla-resultados'),
    loading: document.getElementById('loading'),
    
    // Pantalla de inicio
    nombreUsuario: document.getElementById('nombre-usuario'),
    btnIniciar: document.getElementById('btn-iniciar'),
    
    // Pantalla de cuestionario
    nombreDisplay: document.getElementById('nombre-display'),
    nivelActual: document.getElementById('nivel-actual'),
    puntuacionActual: document.getElementById('puntuacion-actual'),
    preguntaNumero: document.getElementById('pregunta-numero'),
    preguntaTexto: document.getElementById('pregunta-texto'),
    opcionesContainer: document.getElementById('opciones-container'),
    btnResponder: document.getElementById('btn-responder'),
    btnSiguiente: document.getElementById('btn-siguiente'),
    mensajeRetroalimentacion: document.getElementById('mensaje-retroalimentacion'),
    
    // Pantalla de resultados
    puntuacionFinal: document.getElementById('puntuacion-final'),
    clasificacion: document.getElementById('clasificacion'),
    nivelFinal: document.getElementById('nivel-final'),
    respuestasCorrectas: document.getElementById('respuestas-correctas'),
    porcentajeAciertos: document.getElementById('porcentaje-aciertos'),
    tiempoTotal: document.getElementById('tiempo-total'),
    btnReiniciar: document.getElementById('btn-reiniciar')
};

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventListeners();
    elements.nombreUsuario.focus();
});

function inicializarEventListeners() {
    // Pantalla de inicio
    elementos.btnIniciar.addEventListener('click', iniciarCuestionario);
    elementos.nombreUsuario.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            iniciarCuestionario();
        }
    });
    
    // Pantalla de cuestionario
    elementos.btnResponder.addEventListener('click', enviarRespuesta);
    elementos.btnSiguiente.addEventListener('click', siguientePregunta);
    
    // Pantalla de resultados
    elementos.btnReiniciar.addEventListener('click', reiniciarCuestionario);
}

// Funciones de navegación entre pantallas
function mostrarPantalla(pantalla) {
    // Ocultar todas las pantallas
    document.querySelectorAll('.pantalla').forEach(p => {
        p.classList.remove('active');
    });
    
    // Mostrar la pantalla solicitada
    pantalla.classList.add('active');
}

function mostrarLoading(mostrar = true) {
    elementos.loading.style.display = mostrar ? 'flex' : 'none';
}

// Función para iniciar el cuestionario
async function iniciarCuestionario() {
    const nombre = elementos.nombreUsuario.value.trim();
    
    if (!nombre) {
        alert('Por favor, ingresa tu nombre');
        elementos.nombreUsuario.focus();
        return;
    }
    
    try {
        mostrarLoading(true);
        
        const response = await fetch('/iniciar_cuestionario', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nombre: nombre })
        });
        
        if (!response.ok) {
            throw new Error('Error al iniciar el cuestionario');
        }
        
        const data = await response.json();
        
        // Actualizar UI
        elementos.nombreDisplay.textContent = nombre;
        cuestionarioActivo = true;
        
        // Cambiar a pantalla de cuestionario
        mostrarPantalla(elementos.pantallaCuestionario);
        
        // Cargar primera pregunta
        await cargarPregunta();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al iniciar el cuestionario. Por favor, intenta de nuevo.');
    } finally {
        mostrarLoading(false);
    }
}

// Función para cargar una nueva pregunta
async function cargarPregunta() {
    try {
        mostrarLoading(true);
        
        const response = await fetch('/obtener_pregunta');
        
        if (!response.ok) {
            throw new Error('Error al cargar la pregunta');
        }
        
        const data = await response.json();
        
        // Actualizar información del progreso
        elementos.nivelActual.textContent = data.nivel;
        elementos.puntuacionActual.textContent = data.puntuacion_actual;
        elementos.preguntaNumero.textContent = data.numero_pregunta;
        
        // Mostrar pregunta
        elementos.preguntaTexto.textContent = data.pregunta;
        
        // Crear opciones
        crearOpciones(data.opciones);
        
        // Resetear estado
        respuestaSeleccionada = null;
        elementos.btnResponder.disabled = true;
        elementos.btnSiguiente.style.display = 'none';
        elementos.mensajeRetroalimentacion.style.display = 'none';
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar la pregunta. Por favor, recarga la página.');
    } finally {
        mostrarLoading(false);
    }
}

// Función para crear las opciones de respuesta
function crearOpciones(opciones) {
    elementos.opcionesContainer.innerHTML = '';
    
    const letras = ['A', 'B', 'C', 'D'];
    
    opciones.forEach((opcion, index) => {
        const opcionElement = document.createElement('div');
        opcionElement.className = 'opcion';
        opcionElement.dataset.letra = letras[index];
        opcionElement.dataset.valor = letras[index].toLowerCase();
        opcionElement.textContent = opcion;
        
        opcionElement.addEventListener('click', function() {
            seleccionarOpcion(this);
        });
        
        elementos.opcionesContainer.appendChild(opcionElement);
    });
}

// Función para seleccionar una opción
function seleccionarOpcion(opcionElement) {
    // Remover selección anterior
    document.querySelectorAll('.opcion').forEach(o => {
        o.classList.remove('selected');
    });
    
    // Seleccionar nueva opción
    opcionElement.classList.add('selected');
    respuestaSeleccionada = opcionElement.dataset.valor;
    
    // Habilitar botón de responder
    elementos.btnResponder.disabled = false;
}

// Función para enviar la respuesta
async function enviarRespuesta() {
    if (!respuestaSeleccionada) {
        alert('Por favor, selecciona una respuesta');
        return;
    }
    
    try {
        mostrarLoading(true);
        
        const response = await fetch('/responder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ respuesta: respuestaSeleccionada })
        });
        
        if (!response.ok) {
            throw new Error('Error al enviar la respuesta');
        }
        
        const data = await response.json();
        
        // Mostrar retroalimentación
        mostrarRetroalimentacion(data);
        
        // Actualizar puntuación
        elementos.puntuacionActual.textContent = data.puntuacion;
        elementos.nivelActual.textContent = data.nivel_actual;
        
        // Deshabilitar opciones y mostrar respuesta correcta
        mostrarRespuestaCorrecta(data.respuesta_correcta, data.es_correcta);
        
        // Cambiar botones
        elementos.btnResponder.style.display = 'none';
        
        if (data.continuar) {
            elementos.btnSiguiente.style.display = 'inline-flex';
        } else {
            // Mostrar resultados finales
            setTimeout(() => {
                mostrarResultadosFinales(data.resultado_final);
            }, 2000);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al enviar la respuesta. Por favor, intenta de nuevo.');
    } finally {
        mostrarLoading(false);
    }
}

// Función para mostrar retroalimentación
function mostrarRetroalimentacion(data) {
    const mensaje = elementos.mensajeRetroalimentacion;
    mensaje.style.display = 'block';
    
    // Limpiar clases anteriores
    mensaje.className = 'mensaje';
    
    let textoMensaje = '';
    
    if (data.es_correcta) {
        mensaje.classList.add('correcto');
        textoMensaje = '¡Correcto! ';
        
        // Calcular puntos ganados
        const puntosGanados = 10 * data.nivel_actual;
        textoMensaje += `Has ganado ${puntosGanados} puntos.`;
    } else {
        mensaje.classList.add('incorrecto');
        textoMensaje = '❌ Incorrecto. ';
        textoMensaje += `La respuesta correcta era la opción ${data.respuesta_correcta.toUpperCase()}.`;
    }
    
    // Agregar mensaje de cambio de nivel si existe
    if (data.mensaje_nivel) {
        textoMensaje += ` ${data.mensaje_nivel}`;
        mensaje.classList.add('nivel');
    }
    
    mensaje.textContent = textoMensaje;
    
    // Scroll al mensaje
    mensaje.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Función para mostrar la respuesta correcta
function mostrarRespuestaCorrecta(respuestaCorrecta, esCorrecta) {
    const opciones = document.querySelectorAll('.opcion');
    
    opciones.forEach(opcion => {
        // Deshabilitar clic
        opcion.style.pointerEvents = 'none';
        
        if (opcion.dataset.valor === respuestaCorrecta) {
            opcion.classList.add('correcta');
        } else if (opcion.classList.contains('selected') && !esCorrecta) {
            opcion.classList.add('incorrecta');
        }
    });
}

// Función para cargar la siguiente pregunta
async function siguientePregunta() {
    // Resetear estado visual de las opciones
    document.querySelectorAll('.opcion').forEach(opcion => {
        opcion.style.pointerEvents = 'auto';
        opcion.classList.remove('selected', 'correcta', 'incorrecta');
    });
    
    // Resetear botones
    elementos.btnResponder.style.display = 'inline-flex';
    elementos.btnResponder.disabled = true;
    elementos.btnSiguiente.style.display = 'none';
    
    // Cargar nueva pregunta
    await cargarPregunta();
}

// Función para mostrar resultados finales
function mostrarResultadosFinales(resultados) {
    // Actualizar elementos con los resultados
    elementos.puntuacionFinal.textContent = resultados.puntuacion_final;
    elementos.clasificacion.textContent = resultados.clasificacion;
    elementos.nivelFinal.textContent = resultados.nivel_final;
    elementos.respuestasCorrectas.textContent = `${resultados.respuestas_correctas}/${resultados.preguntas_respondidas}`;
    elementos.porcentajeAciertos.textContent = `${resultados.porcentaje_aciertos}%`;
    elementos.tiempoTotal.textContent = resultados.tiempo_total;
    
    // Cambiar color de clasificación según el desempeño
    const clasificacionElement = elementos.clasificacion;
    const porcentaje = resultados.porcentaje_aciertos;
    
    if (porcentaje >= 90) {
        clasificacionElement.style.color = '#28a745';
    } else if (porcentaje >= 75) {
        clasificacionElement.style.color = '#17a2b8';
    } else if (porcentaje >= 60) {
        clasificacionElement.style.color = '#ffc107';
    } else {
        clasificacionElement.style.color = '#dc3545';
    }
    
    // Mostrar pantalla de resultados
    mostrarPantalla(elementos.pantallaResultados);
    
    // Efecto de animación en la puntuación
    animarPuntuacion(resultados.puntuacion_final);
}

// Función para animar la puntuación final
function animarPuntuacion(puntuacionFinal) {
    const elemento = elementos.puntuacionFinal;
    const duracion = 2000; // 2 segundos
    const incremento = puntuacionFinal / (duracion / 50); // Actualizar cada 50ms
    let puntuacionActual = 0;
    
    const intervalo = setInterval(() => {
        puntuacionActual += incremento;
        
        if (puntuacionActual >= puntuacionFinal) {
            puntuacionActual = puntuacionFinal;
            clearInterval(intervalo);
        }
        
        elemento.textContent = Math.floor(puntuacionActual);
    }, 50);
}

// Función para reiniciar el cuestionario
async function reiniciarCuestionario() {
    try {
        mostrarLoading(true);
        
        const response = await fetch('/reiniciar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error('Error al reiniciar el cuestionario');
        }
        
        // Resetear estado
        cuestionarioActivo = false;
        respuestaSeleccionada = null;
        
        // Limpiar campos
        elementos.nombreUsuario.value = '';
        
        // Volver a pantalla de inicio
        mostrarPantalla(elementos.pantallaInicio);
        elementos.nombreUsuario.focus();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al reiniciar. Por favor, recarga la página.');
    } finally {
        mostrarLoading(false);
    }
}

// Función utilitaria para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo = 'info') {
    // Esta función se puede expandir para mostrar notificaciones toast
    console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
}

// Manejo de errores globales
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    mostrarNotificacion('Ha ocurrido un error inesperado', 'error');
});

// Prevenir salida accidental durante el cuestionario
window.addEventListener('beforeunload', function(e) {
    if (cuestionarioActivo) {
        e.preventDefault();
        e.returnValue = '¿Estás seguro de que quieres salir? Perderás tu progreso.';
        return e.returnValue;
    }
});

// Funciones adicionales para mejorar la experiencia
function ajustarTamanoTexto() {
    // Función para ajustar el tamaño del texto según la longitud
    const pregunta = elementos.preguntaTexto;
    const longitud = pregunta.textContent.length;
    
    if (longitud > 150) {
        pregunta.style.fontSize = '1.2rem';
    } else if (longitud > 100) {
        pregunta.style.fontSize = '1.3rem';
    } else {
        pregunta.style.fontSize = '1.4rem';
    }
}

// Soporte para teclado
document.addEventListener('keydown', function(e) {
    if (!cuestionarioActivo) return;
    
    // Teclas A, B, C, D para seleccionar opciones
    const teclaAOpcion = {
        'KeyA': 'a',
        'KeyB': 'b', 
        'KeyC': 'c',
        'KeyD': 'd'
    };
    
    if (teclaAOpcion[e.code]) {
        const opcion = document.querySelector(`[data-valor="${teclaAOpcion[e.code]}"]`);
        if (opcion && opcion.style.pointerEvents !== 'none') {
            seleccionarOpcion(opcion);
        }
    }
    
    // Enter para responder
    if (e.key === 'Enter' && !elementos.btnResponder.disabled) {
        enviarRespuesta();
    }
    
    // Espacio para siguiente pregunta
    if (e.key === ' ' && elementos.btnSiguiente.style.display !== 'none') {
        e.preventDefault();
        siguientePregunta();
    }
});

console.log('🎯 Cuestionario Inteligente cargado correctamente');
console.log('💡 Usa las teclas A, B, C, D para seleccionar opciones');
console.log('⌨️ Usa Enter para responder y Espacio para siguiente pregunta');
