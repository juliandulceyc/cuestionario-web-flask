/**
 * Sistema de Renovación Automática de Tokens JWT
 * Renueva el token cada 15 minutos automáticamente
 */

(function() {
    'use strict';
    
    const TOKEN_EXPIRATION_MS = 15 * 60 * 1000; // 15 minutos en milisegundos
    const RENEWAL_INTERVAL_MS = 12 * 60 * 1000; // Renovar cada 12 minutos (3 min antes)
    const WARNING_TIME_MS = 2 * 60 * 1000; // Mostrar advertencia 2 min antes
    
    let tokenExpirationTime = null;
    let renewalInterval = null;
    let warningTimeout = null;
    let logDiv = null;
    
    /**
     * Inicializa el sistema de renovación de tokens
     */
    function inicializarRenovacionTokens() {
        // Crear div para mostrar logs de renovación
        crearDivLogs();
        
        // Obtener tiempo de expiración inicial del servidor
        tokenExpirationTime = Date.now() + TOKEN_EXPIRATION_MS;
        
        // Log inicial
        logRenovacion('🔐 Sistema de renovación de tokens iniciado');
        logRenovacion(`⏰ Token expira en: ${formatearTiempo(TOKEN_EXPIRATION_MS)}`);
        
        // Configurar intervalo de renovación automática
        iniciarRenovacionAutomatica();
        
        // Configurar advertencia antes de expirar
        programarAdvertencia();
        
        // Mostrar contador en tiempo real
        iniciarContador();
    }
    
    /**
     * Crea el div para mostrar logs de renovación
     */
    function crearDivLogs() {
        logDiv = document.createElement('div');
        logDiv.id = 'token-renewal-log';
        logDiv.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.85);
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-width: 350px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 10000;
            box-shadow: 0 4px 15px rgba(0, 255, 0, 0.3);
            border: 1px solid #00ff00;
        `;
        
        const titulo = document.createElement('div');
        titulo.style.cssText = 'font-weight: bold; margin-bottom: 10px; color: #00ff00; border-bottom: 1px solid #00ff00; padding-bottom: 5px;';
        titulo.textContent = '🔐 Monitor de Tokens JWT';
        logDiv.appendChild(titulo);
        
        const contenido = document.createElement('div');
        contenido.id = 'token-renewal-content';
        logDiv.appendChild(contenido);
        
        // Botón para cerrar/minimizar
        const btnMinimizar = document.createElement('button');
        btnMinimizar.textContent = '−';
        btnMinimizar.style.cssText = `
            position: absolute;
            top: 5px;
            right: 5px;
            background: transparent;
            border: 1px solid #00ff00;
            color: #00ff00;
            cursor: pointer;
            width: 20px;
            height: 20px;
            border-radius: 3px;
            font-size: 16px;
            line-height: 1;
        `;
        btnMinimizar.onclick = function() {
            const content = document.getElementById('token-renewal-content');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                btnMinimizar.textContent = '−';
            } else {
                content.style.display = 'none';
                btnMinimizar.textContent = '+';
            }
        };
        logDiv.appendChild(btnMinimizar);
        
        document.body.appendChild(logDiv);
    }
    
    /**
     * Registra un mensaje en el log de renovación
     */
    function logRenovacion(mensaje) {
        const contenido = document.getElementById('token-renewal-content');
        if (!contenido) return;
        
        const timestamp = new Date().toLocaleTimeString('es-ES');
        const linea = document.createElement('div');
        linea.style.marginBottom = '5px';
        linea.textContent = `[${timestamp}] ${mensaje}`;
        
        contenido.appendChild(linea);
        
        // Mantener solo las últimas 10 líneas
        while (contenido.children.length > 10) {
            contenido.removeChild(contenido.firstChild);
        }
        
        // Auto-scroll al final
        contenido.scrollTop = contenido.scrollHeight;
        
        console.log(`[Token Renewal] ${mensaje}`);
    }
    
    /**
     * Inicia el proceso de renovación automática
     */
    function iniciarRenovacionAutomatica() {
        // Limpiar intervalo anterior si existe
        if (renewalInterval) {
            clearInterval(renewalInterval);
        }
        
        // Renovar cada 12 minutos (3 min antes de expirar)
        renewalInterval = setInterval(function() {
            renovarToken();
        }, RENEWAL_INTERVAL_MS);
        
        logRenovacion(`🔄 Renovación automática configurada cada ${formatearTiempo(RENEWAL_INTERVAL_MS)}`);
    }
    
    /**
     * Renueva el token JWT
     */
    function renovarToken() {
        logRenovacion('🔄 Iniciando renovación de token...');
        
        fetch('/api/renovar-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Error HTTP: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                tokenExpirationTime = Date.now() + TOKEN_EXPIRATION_MS;
                logRenovacion('✅ Token renovado exitosamente');
                logRenovacion(`⏰ Nuevo token expira en: ${formatearTiempo(TOKEN_EXPIRATION_MS)}`);
                
                // Reprogramar advertencia
                programarAdvertencia();
                
                // Mostrar notificación visual
                mostrarNotificacion('✅ Token renovado', 'success');
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(function(error) {
            logRenovacion('❌ Error renovando token: ' + error.message);
            console.error('Error renovando token:', error);
            
            // Mostrar notificación de error
            mostrarNotificacion('❌ Error renovando token', 'error');
            
            // Si falla, intentar de nuevo en 1 minuto
            setTimeout(renovarToken, 60000);
        });
    }
    
    /**
     * Programa la advertencia antes de expirar
     */
    function programarAdvertencia() {
        // Limpiar timeout anterior
        if (warningTimeout) {
            clearTimeout(warningTimeout);
        }
        
        // Mostrar advertencia 2 minutos antes
        warningTimeout = setTimeout(function() {
            logRenovacion('⚠️ ADVERTENCIA: Token expirará pronto');
            mostrarNotificacion('⚠️ Token expirará en 2 minutos', 'warning');
        }, TOKEN_EXPIRATION_MS - WARNING_TIME_MS);
    }
    
    /**
     * Inicia el contador en tiempo real
     */
    function iniciarContador() {
        const contadorDiv = document.createElement('div');
        contadorDiv.id = 'token-countdown';
        contadorDiv.style.cssText = `
            position: fixed;
            top: 10px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            color: #fff;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 9999;
            font-family: monospace;
        `;
        document.body.appendChild(contadorDiv);
        
        setInterval(function() {
            const tiempoRestante = tokenExpirationTime - Date.now();
            if (tiempoRestante > 0) {
                contadorDiv.textContent = `🔐 Token expira en: ${formatearTiempo(tiempoRestante)}`;
                
                // Cambiar color según tiempo restante
                if (tiempoRestante < WARNING_TIME_MS) {
                    contadorDiv.style.background = 'rgba(255, 0, 0, 0.7)';
                } else if (tiempoRestante < 5 * 60 * 1000) {
                    contadorDiv.style.background = 'rgba(255, 165, 0, 0.7)';
                } else {
                    contadorDiv.style.background = 'rgba(0, 128, 0, 0.7)';
                }
            } else {
                contadorDiv.textContent = '🔐 Token expirado';
                contadorDiv.style.background = 'rgba(255, 0, 0, 0.9)';
            }
        }, 1000);
    }
    
    /**
     * Formatea tiempo en milisegundos a formato legible
     */
    function formatearTiempo(ms) {
        const segundos = Math.floor(ms / 1000);
        const minutos = Math.floor(segundos / 60);
        const segundosRestantes = segundos % 60;
        
        if (minutos > 0) {
            return `${minutos}m ${segundosRestantes}s`;
        }
        return `${segundos}s`;
    }
    
    /**
     * Muestra una notificación temporal
     */
    function mostrarNotificacion(mensaje, tipo) {
        const notif = document.createElement('div');
        notif.textContent = mensaje;
        notif.style.cssText = `
            position: fixed;
            top: 50px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 10001;
            animation: slideIn 0.3s ease-out;
        `;
        
        switch(tipo) {
            case 'success':
                notif.style.background = '#28a745';
                break;
            case 'error':
                notif.style.background = '#dc3545';
                break;
            case 'warning':
                notif.style.background = '#ffc107';
                notif.style.color = '#000';
                break;
            default:
                notif.style.background = '#007bff';
        }
        
        document.body.appendChild(notif);
        
        setTimeout(function() {
            notif.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(function() {
                notif.remove();
            }, 300);
        }, 3000);
    }
    
    // Agregar estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(400px); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarRenovacionTokens);
    } else {
        inicializarRenovacionTokens();
    }
    
})();
