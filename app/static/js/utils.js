// Módulo de utilidades para notificaciones y accesibilidad
// Uso: importar en cualquier JS y llamar mostrarNotificacion, mostrarError, announceToScreenReader

export function mostrarNotificacion(mensaje, tipo = 'success', duracion = 4000) {
    const notification = document.createElement('div');
    notification.className = 'notification ' + tipo;
    notification.textContent = mensaje;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', tipo === 'error' ? 'assertive' : 'polite');
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, duracion);
}

export function mostrarError(mensaje, duracion = 5000) {
    mostrarNotificacion(mensaje, 'error', duracion);
}

export function announceToScreenReader(message) {
    let srDiv = document.getElementById('screenreader-status');
    if (!srDiv) {
        srDiv = document.createElement('div');
        srDiv.id = 'screenreader-status';
        srDiv.setAttribute('aria-live', 'polite');
        srDiv.style.position = 'absolute';
        srDiv.style.left = '-9999px';
        document.body.appendChild(srDiv);
    }
    srDiv.textContent = message;
    setTimeout(() => { srDiv.textContent = ''; }, 3000);
}
