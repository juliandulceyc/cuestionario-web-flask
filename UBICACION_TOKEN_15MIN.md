# 🔐 Ubicación del Token de 15 Minutos en el Código

## 📍 Ubicaciones del Token de 15 Minutos

El token JWT con expiración de **15 minutos** está configurado en **3 lugares principales**:

---

## 1️⃣ **Configuración Principal** - `security.py`

### **Línea 21** - Constante de configuración

```python
# security.py - LÍNEA 21
class SecurityManager:
    """Gestor de seguridad centralizado"""
    
    # Configuración de tokens
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu_secret_key_super_segura_cambiar_en_produccion')
    JWT_ALGORITHM = 'HS256'
    TOKEN_EXPIRATION_MINUTES = 15  # ← 🎯 AQUÍ ESTÁ LA CONFIGURACIÓN PRINCIPAL
    REFRESH_TOKEN_EXPIRATION_DAYS = 7
```

**Ubicación**: `c:\Users\USUARIO\Documents\Empresa\security.py` - **Línea 21**

**Propósito**: Define cuántos minutos dura el token de acceso

---

### **Línea 42** - Uso en generación de token

```python
# security.py - LÍNEA 42
@staticmethod
def generar_token(usuario_id: str, rol: str = 'admin') -> dict:
    """
    Genera un token JWT con expiración de 15 minutos
    """
    now = datetime.utcnow()
    
    # Token de acceso (15 minutos)
    access_payload = {
        'user_id': usuario_id,
        'rol': rol,
        'exp': now + timedelta(minutes=SecurityManager.TOKEN_EXPIRATION_MINUTES),  # ← 🎯 USA LA CONSTANTE
        'iat': now,
        'type': 'access'
    }
```

**Ubicación**: `c:\Users\USUARIO\Documents\Empresa\security.py` - **Línea 42**

**Propósito**: Calcula la fecha de expiración del token al generarlo

---

### **Línea 64** - Información de expiración

```python
# security.py - LÍNEA 64
return {
    'access_token': access_token,
    'refresh_token': refresh_token,
    'expires_in': SecurityManager.TOKEN_EXPIRATION_MINUTES * 60,  # ← 🎯 15 * 60 = 900 segundos
    'token_type': 'Bearer'
}
```

**Ubicación**: `c:\Users\USUARIO\Documents\Empresa\security.py` - **Línea 64**

**Propósito**: Informa al cliente en cuántos segundos expira (900 segundos = 15 minutos)

---

## 2️⃣ **Login de Administrador** - `app.py`

### **Línea 643** - Al iniciar sesión

```python
# app.py - LÍNEA 643
if username == Config.ADMIN_USER and password == Config.ADMIN_PASS:
    session['admin_logged_in'] = True
    
    # Generar token JWT para APIs
    tokens = SecurityManager.generar_token(usuario_id=username, rol='admin')
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']
    session['token_expires_at'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()  # ← 🎯 GUARDA CUANDO EXPIRA
    
    logger.info(f"Admin login exitoso: {username} - Token generado")
    return redirect(url_for('admin_dashboard'))
```

**Ubicación**: `c:\Users\USUARIO\Documents\Empresa\app.py` - **Línea 643**

**Propósito**: Guarda en la sesión cuándo expira el token (15 minutos desde el login)

---

## 3️⃣ **Renovación de Token** - `app.py`

### **Línea 667** - Al renovar el token

```python
# app.py - LÍNEA 667
@app.route('/admin/renovar-token', methods=['POST'])
def renovar_token():
    """Endpoint para renovar el token de acceso cada 15 minutos"""
    refresh_token = request.json.get('refresh_token') or session.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token no proporcionado'}), 401
    
    try:
        nuevos_tokens = SecurityManager.renovar_token(refresh_token)
        
        # Actualizar sesión
        session['access_token'] = nuevos_tokens['access_token']
        session['token_expires_at'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()  # ← 🎯 RENUEVA POR OTROS 15 MIN
        
        logger.info("Token renovado exitosamente")
```

**Ubicación**: `c:\Users\USUARIO\Documents\Empresa\app.py` - **Línea 667**

**Propósito**: Al renovar el token, extiende la sesión por otros 15 minutos

---

## 4️⃣ **Sistema de Renovación Silenciosa** - JavaScript

### **`token-renewal-silent.js`** - Renovación automática cada 12 minutos

```javascript
// token-renewal-silent.js
const TOKEN_RENEWAL_INTERVAL = 12 * 60 * 1000; // 12 minutos en milisegundos

function iniciarRenovacionAutomatica() {
    setInterval(() => {
        renovarTokenSilencioso();
    }, TOKEN_RENEWAL_INTERVAL); // ← 🎯 Se renueva cada 12 min (antes de los 15)
}
```

**Ubicación**: `c:\Users\USUARIO\Documents\Empresa\static\js\token-renewal-silent.js`

**Propósito**: Renueva el token automáticamente cada 12 minutos (antes de que expire a los 15)

---

## 📊 Diagrama de Flujo del Token

```
┌─────────────────────────────────────────────────────┐
│ 1. USUARIO INICIA SESIÓN                           │
│    app.py - Línea 643                              │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│ 2. SE GENERA TOKEN (security.py - Línea 42)        │
│    - Duración: 15 minutos                          │
│    - Expiración: now + 15 minutos                  │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│ 3. SE GUARDA EN SESSION (app.py - Línea 643)       │
│    - access_token: "eyJ0eXAiOiJKV1..."            │
│    - token_expires_at: "2025-10-07T14:16:42"      │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│ 4. JAVASCRIPT MONITOREA (token-renewal-silent.js)  │
│    - Cada 12 minutos llama a /admin/renovar-token  │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│ 5. SE RENUEVA TOKEN (app.py - Línea 667)           │
│    - Genera nuevo token válido por otros 15 min    │
│    - Actualiza token_expires_at                    │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
         [BUCLE SE REPITE]
```

---

## 🔧 Cómo Cambiar la Duración del Token

### **Opción 1: Cambiar en `security.py` (Recomendado)**

```python
# security.py - Línea 21
TOKEN_EXPIRATION_MINUTES = 30  # Cambiar de 15 a 30 minutos
```

✅ **Esto afectará automáticamente**:
- Generación de tokens (línea 42)
- Tiempo reportado al cliente (línea 64)
- Logs del sistema (línea 59)

### **Opción 2: Usar Variable de Entorno**

```python
# .env
TOKEN_EXPIRATION_MINUTES=30
```

```python
# security.py - Línea 21
TOKEN_EXPIRATION_MINUTES = int(os.getenv('TOKEN_EXPIRATION_MINUTES', 15))
```

---

## ⚠️ Importante: Sincronización con JavaScript

Si cambias el tiempo de expiración del token, **también debes ajustar** el intervalo de renovación en JavaScript:

```javascript
// token-renewal-silent.js
// Si cambias a 30 minutos, renovar cada 25 minutos (5 min antes)
const TOKEN_RENEWAL_INTERVAL = 25 * 60 * 1000;
```

**Regla**: Renovar **3-5 minutos antes** de la expiración para evitar que caduque.

---

## 📝 Resumen de Ubicaciones

| Archivo | Línea | Propósito |
|---------|-------|-----------|
| **security.py** | 21 | 🎯 **Configuración principal** (15 min) |
| **security.py** | 42 | Cálculo de expiración al generar |
| **security.py** | 64 | Información de expiración (900 seg) |
| **app.py** | 643 | Guardar expiración en login |
| **app.py** | 667 | Renovar token cada 15 min |
| **token-renewal-silent.js** | - | Renovación automática cada 12 min |

---

## 🚀 Estado Actual

✅ **Token configurado a**: 15 minutos  
✅ **Renovación automática**: Cada 12 minutos  
✅ **Margen de seguridad**: 3 minutos antes de expirar

El sistema está funcionando correctamente y los tokens se renuevan automáticamente en segundo plano sin interrumpir al usuario. 🎉
