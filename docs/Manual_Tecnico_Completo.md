# Manual Técnico - Sistema de Evaluación FWS PAN

Última actualización: 2025-10-28

Este manual técnico describe en detalle la arquitectura, instalación, configuración, despliegue, integración con servicios externos y resolución de problemas para la aplicación de evaluación desarrollada en Flask.

---

## 1. Resumen del sistema

- Tecnología principal: Python 3.11+, Flask, SQLAlchemy.
- Plantillas: Jinja2.
- PDF: reportlab + python-docx (para generación de manuales).
- Almacenamiento: PostgreSQL (recomendado en producción).
- Integraciones: SMTP (Gmail/SendGrid), Google Drive (opcional), Cloudflare Tunnel (para exponer localmente), opcional S3 para almacenamiento.

Casos de uso principales:
- Registro y gestión de candidatos (admin).
- Evaluación adaptativa por niveles con máximo 40 preguntas.
- Generación automática de PDF con resultados al finalizar la evaluación.
- Recuperación de contraseña por email con token de un solo uso y expiración.

## 2. Estructura del repositorio (resumen)

- `app.py` - Entrada principal de la aplicación Flask, rutas, utilidades y configuración central.
- `pdf_generator.py` - Lógica para crear reportes PDF.
- `drive_integration.py` - (Opcional) helpers para subir PDFs a Google Drive.
- `templates/` - Plantillas Jinja2 (vistas HTML) y plantillas de correo `templates/email/`.
- `static/` - CSS, JS, imágenes.
- `requirements.txt` - Dependencias del proyecto.
- `scripts/` - Scripts auxiliares (p. ej. generación de manual DOCX).
- `docs/` - Documentación, incluyendo este manual.

## 3. Requisitos previos

- Python 3.11+.
- pip y virtualenv.
- PostgreSQL (para producción) o SQLite para pruebas locales.
- Cuenta Google (si se usa integración Drive) y credenciales de servicio (JSON).
- Cuenta SMTP o App Password (Gmail con 2FA o proveedor externo como SendGrid).

## 4. Instalación y ejecución local (Windows ejemplo)

1. Crear entorno virtual e instalar dependencias:

```cmd
cd C:\Users\USUARIO\Documents\Empresa
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Variables de entorno básicas (puedes crear `.env`):

```
SECRET_KEY=una_clave_secreta
FLASK_ENV=development
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu@email.com
EMAIL_PASSWORD=tu_app_password
EMAIL_FROM=tu@email.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SIGN_NAME=Yeivi Julieth Peinado H.
SIGN_TITLE=Gerente de Servicios Ciberseguridad
SIGN_PHONE=+57 3013407054
SIGN_LOCATION=Bogotá, Colombia
SIGN_WEBSITE=https://www.axity.com
SIGN_BANNER_URL=https://tuservidor/imagenes/axity-banner.png
BASE_URL=http://localhost:5000
```

3. Ejecutar la app en desarrollo:

```cmd
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

4. Visitar: `http://localhost:5000`

## 5. Variables de configuración importantes

Describe las variables definidas en `Config` dentro de `app.py` (resumen):

- SECRET_KEY: clave para sesiones y JWT.
- DEBUG / FLASK_ENV: modo debug.
- PORT: puerto por defecto.
- ADMIN_USER, ADMIN_PASS, ADMIN_EMAIL: credenciales admin (evitar valores por defecto en prod).
- EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM: configuración SMTP.
- SIGN_*: variables usadas por plantillas de correo (firma).
- EVALUACION_CONFIG: parámetros de la lógica de evaluación (preguntas por nivel, min correctas, terminación temprana).
- GDRIVE / CLIENT_CREDENTIALS: manejar credenciales Drive via variable de entorno o archivo seguro.

## 6. Flujo de recuperación de contraseña (detalle técnico)

- Ruta: `GET/POST /admin/recuperar-password`.
- Proceso:
  - Validar identificador (username o email).
  - Generar token único `secrets.token_urlsafe(32)` y `expires_at = now + 30m`.
  - Guardar `RecoveryToken(user_id, token, expires_at)` en DB.
  - Renderizar plantillas `templates/email/reset_password.txt` y `.html` con `reset_link` y firma.
  - Llamar `enviar_email(destinatario, asunto, texto, html)`.
- Seguridad:
  - Token single-use y expiración corta.
  - No revelar si usuario existe (puedes variar comportamiento según política).

## 7. Envío de correo (enviar_email)

- Soporta SSL implícito (port 465) y STARTTLS (port 587).
- Verifica que `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_FROM` estén configurados.
- Retorna `(True, None)` o `(False, 'mensaje')` para diagnóstico.
- Log de errores detallado cuando `Config.DEBUG` es True.

## 8. Generación de PDF

- `pdf_generator.py` centraliza la creación de reportes con reportlab.
- Input: datos de la evaluación (preguntas, respuestas, estadísticas, nivel final).
- Output: archivo PDF temporal que puede guardarse local o subirse a Drive.
- Recomendación de producción: ejecutar generación en background (Celery + Redis o RQ) para evitar bloquear request/response.

## 9. Integración con Google Drive

- Uso de service account o credenciales OAuth2 (seguro para servidor).
- Recomendado: guardar JSON de credenciales en variable de entorno `GDRIVE_JSON` y en startup escribirlo a archivo temporal para la librería.
- No incluir `client_credentials.json` en el repo.

Ejemplo para escribir credenciales desde env (Python):

```python
import os, json, tempfile
creds_json = os.getenv('GDRIVE_JSON')
if creds_json:
    path = os.path.join(tempfile.gettempdir(), 'client_credentials.json')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(creds_json)
    # usar path para inicializar cliente
```

## 10. Base de datos y modelos (resumen)

- Modelos principales:
  - UserDB: usuarios/admins (username, email, password_hash, roles).
  - RecoveryToken: token de recuperación (user_id, token, expires_at, used).
  - CandidatoDB: datos de candidatos (nombre, email, codigo, estado).
  - ResultadoDB: resultados por evaluación (puntos, nivel_final, datos por pregunta).
- Migraciones: si se añade Alembic, añadir scripts `alembic/` para manejar cambios de esquema.

## 11. Endpoints importantes (listado)

- `/` - Home / inicio de prueba
- `/iniciar-evaluacion/<codigo>` - Inicio evaluación por candidato
- `/obtener_pregunta` - API para obtener pregunta actual
- `/responder` - Registrar respuesta y avanzar
- `/generar_pdf_final` - Finaliza y genera PDF
- `/admin/recuperar-password` - Solicitar token
- `/admin/restablecer-password` - Restablecer con token
- `/admin/*` - Rutas de administración (login, dashboard, CRUD candidatos)

(Ver `app.py` para nombres exactos y argumentos)

## 12. Frontend y assets

- `templates/` contienen vistas generadas por el servidor con Jinja2.
- `static/` contiene CSS, JS y assets. Considerar servir `static/` desde un CDN (Netlify) para mejorar rendimiento.
- `static/js/cuestionario.js` controla la lógica cliente de la evaluación.
- `static/js/admin-dashboard.js` controla panel admin (editar candidatos en modal y actualizar filas en la UI).

## 13. Logging y monitoreo

- Logging integrado con `logger` en `app.py`.
- Para producción, configurar handler a fichero o a servicios externos (Papertrail, LogDNA, Datadog).
- Exportar métricas de health y uso si se requiere.

## 14. Despliegue (recomendaciones)

### Opción rápida (todo en un único servicio)
- Plataforma recomendada: Render, Fly.io o Railway.
- Comandos de inicio (Gunicorn):

```cmd
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

- Variables de entorno: configurar todas las ENV críticas (DATABASE_URL, EMAIL_*, SECRET_KEY, SIGN_*).
- Base de datos: usar Managed Postgres.
- Drive: poner JSON en `GDRIVE_JSON` o usar storage seguro.

### Opción híbrida (frontend en Netlify, backend en Render)
- Extrae `static/` y publica en Netlify.
- Mantén APIs y generación de PDFs en Render.
- Configurar CORS y auth (preferible JWT para API).

### Docker
- Ejemplo `Dockerfile` (simple):

```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Cloudflare Tunnel (exponer localmente)
- Para pruebas: `cloudflared tunnel --url http://localhost:5000` → trycloudflare URL.
- Para producción: crear named tunnel, mapear DNS y ejecutar como servicio.

## 15. Seguridad

- No commit de secretos ni credenciales en el repo.
- Usar App Passwords o proveedores transaccionales para SMTP.
- Proteger panel admin con autenticación fuerte; usar rate-limiting y controles de IP si es necesario.
- Validar y sanear todas las entradas (formularios y APIs).

## 16. Backup y mantenimiento

- Respaldar la base de datos regularmente.
- Mantener copia de seguridad de configuraciones críticas y claves.
- Mantener rotación de logs y monitor de disco.

## 17. Troubleshooting (errores comunes)

- 502 / connection refused en Cloudflare Tunnel: app no escucha en el puerto configurado. Asegúrate de `flask run --host=0.0.0.0 --port=5000` y reinicia tunnel.
- SMTP 535 BadCredentials: revisar `EMAIL_PASSWORD` y remover espacios; utilizar App Password si Gmail con 2FA.
- PDF que no genera o falla: revisar excepciones en `pdf_generator.py` y aumentar memoria/tiempo de ejecución o mover a worker.
- Error al actualizar candidato (500): revisar logs; validar que `validar_email_simple` y demás helpers estén definidos antes de su uso.

## 18. FAQ y operaciones comunes

- ¿Cómo cambiar el contenido del correo de recuperación?
  - Editar `templates/email/reset_password.html` y `.txt`.
- ¿Dónde personalizo la firma?
  - Variables `SIGN_*` en `.env` o directamente en `app.py`.
- ¿Cómo forzar que `BASE_URL` sea la URL pública en emails?
  - Definir `BASE_URL` en env y usarla en `recuperar-password` para construir `reset_link`.

## 19. Apéndices

### A. Comandos útiles (Windows)

```cmd
# activar venv
venv\Scripts\activate
# instalar deps
pip install -r requirements.txt
# ejecutar pruebas unitarias (si existen)
pytest -q
# comprobar puerto 5000
netstat -ano | findstr :5000
```

### B. Recomendaciones de escala

- Separar generación de PDFs a workers asíncronos.
- Usar almacenamiento externo (S3/Drive) para archivos.
- Usar caching para assets y resultados que puedan ser reusados.

---

Si quieres, puedo:

- Generar una versión Word (.docx) del manual (ya existe script en `scripts/` que puedo adaptar). 
- Añadir una checklist desplegable en `docs/` con pasos de producción concretos.
- Crear plantillas de `render.yaml` y `Dockerfile` específicas para tu repo.

Dime cuál prefieres y lo agrego.
