/**
 * Sistema de Renovación Automática de Tokens JWT (Modo Silencioso)
 * Renueva el token cada 12 minutos sin mostrar alertas al usuario
 */

(function() {
    'use strict';
    
    const TOKEN_EXPIRATION_MS = 15 * 60 * 1000; // 15 minutos
    const RENEWAL_INTERVAL_MS = 12 * 60 * 1000; // Renovar cada 12 minutos
    
    let tokenExpirationTime = null;
    let renewalInterval = null;
    
    /**
     * Inicializa el sistema de renovación silenciosa de tokens
     */
    function inicializarRenovacionTokens() {
        tokenExpirationTime = Date.now() + TOKEN_EXPIRATION_MS;
        
        // Log solo en consola (para debugging si es necesario)
        console.log('[Token] Sistema de renovación iniciado');
        
        // Iniciar renovación automática
        iniciarRenovacionAutomatica();
    }
    
    /**
     * Inicia el intervalo de renovación automática
     */
    function iniciarRenovacionAutomatica() {
        // Limpiar intervalo anterior si existe
        if (renewalInterval) {
            clearInterval(renewalInterval);
        }
        
        // Configurar nuevo intervalo
        renewalInterval = setInterval(function() {
            renovarToken();
        }, RENEWAL_INTERVAL_MS);
        
        console.log('[Token] Renovación automática configurada (cada 12 minutos)');
    }
    
    /**
     * Renueva el token JWT
     */
    function renovarToken() {
        console.log('[Token] Renovando token...');
        
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
                console.log('[Token] Token renovado exitosamente');
            } else {
                console.error('[Token] Error al renovar:', data.error);
                manejarErrorRenovacion(data.error);
            }
        })
        .catch(function(error) {
            console.error('[Token] Error en la renovación:', error);
            manejarErrorRenovacion(error.message);
        });
    }
    
    /**
     * Maneja errores de renovación
     */
    function manejarErrorRenovacion(mensaje) {
        // Si el token expiró, redirigir al login
        if (mensaje && (mensaje.includes('expirado') || mensaje.includes('inválido'))) {
            console.warn('[Token] Token inválido, redirigiendo al login...');
            setTimeout(function() {
                window.location.href = '/admin/login';
            }, 2000);
        }
    }
    
    /**
     * Verifica si el token está próximo a expirar
     */
    function verificarExpiracion() {
        if (!tokenExpirationTime) return;
        
        const tiempoRestante = tokenExpirationTime - Date.now();
        
        // Si quedan menos de 2 minutos, intentar renovar inmediatamente
        if (tiempoRestante < 2 * 60 * 1000 && tiempoRestante > 0) {
            console.warn('[Token] Próximo a expirar, renovando...');
            renovarToken();
        }
        
        // Si ya expiró, redirigir al login
        if (tiempoRestante <= 0) {
            console.error('[Token] Token expirado, redirigiendo al login...');
            window.location.href = '/admin/login';
        }
    }
    
    // Verificar expiración cada minuto
    setInterval(verificarExpiracion, 60 * 1000);
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarRenovacionTokens);
    } else {
        inicializarRenovacionTokens();
    }
    
    // Exponer función para renovar manualmente (opcional)
    window.renovarTokenManual = renovarToken;
    
})();
