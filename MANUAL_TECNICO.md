# Manual Técnico - Sistema de Evaluación de Candidatos

## 1. Introducción

### 1.1 Propósito
El Sistema de Evaluación de Candidatos es una aplicación web diseñada para administrar y realizar pruebas técnicas o de conocimientos a candidatos. Permite a los administradores gestionar el banco de preguntas, registrar candidatos y visualizar resultados, mientras que los candidatos pueden realizar las evaluaciones en un entorno controlado. El sistema genera reportes automáticos en PDF y los almacena en Google Drive.

### 1.2 Alcance
La aplicación cubre el ciclo completo de evaluación:
- Autenticación y gestión de administradores con protección contra fuerza bruta (Rate Limiting).
- Gestión de bancos de preguntas y temas vía interfaz Web o carga desde Excel.
- Registro y validación de candidatos.
- Presentación de cuestionarios con lógica de niveles y tiempos.
- Recuperación automática de sesión ante cierres inesperados.
- Calificación automática.
- Generación de reportes en PDF.
- Envío de notificaciones por correo electrónico.
- Respaldo de reportes en la nube (Google Drive).

### 1.3 Tecnologías Utilizadas
- **Lenguaje Principal**: Python 3.x
- **Framework Web**: Flask
- **Base de Datos**: SQLite (por defecto), compatible con PostgreSQL/MySQL vía SQLAlchemy.
- **ORM**: Flask-SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Jinja2 Templates.
- **Generación de PDF**: ReportLab
- **Integración Cloud**: Google Drive API v3
- **Procesamiento de Datos**: Pandas, OpenPyXL
- **Seguridad**: BCrypt, PyJWT

---

## 2. Arquitectura del Sistema

### 2.1 Estructura de Directorios
```
appCuestionario/
├── app/                        # Código fuente de la aplicación
│   ├── __init__.py             # Fábrica de la aplicación (App Factory)
│   ├── routes.py               # Rutas y controladores (Blueprint)
│   ├── models.py               # Modelos de base de datos
│   ├── services.py             # Lógica de negocio
│   ├── utils.py                # Utilidades
│   ├── config.py               # Configuración
│   ├── security.py             # Seguridad y autenticación
│   ├── extensions.py           # Extensiones (DB, etc.)
│   ├── shared.py               # Variables compartidas
│   ├── drive_integration.py    # Integración con Google Drive
│   ├── pdf_generator.py        # Generador de PDFs
│   ├── static/                 # Archivos estáticos (CSS, JS)
│   └── templates/              # Plantillas HTML
├── config/                     # Archivos de configuración y credenciales
│   ├── client_credentials.json
│   ├── token.json
│   └── config_tema.json
├── data/                       # Datos generados y almacenamiento
│   ├── instance/               # Base de datos SQLite
│   ├── reportes_pdf/           # PDFs generados
│   ├── states/                 # Estados temporales de evaluación
│   └── temas/                  # Archivos Excel de preguntas
├── run.py                      # Punto de entrada para ejecutar la app
├── requirements.txt            # Dependencias
└── MANUAL_TECNICO.md           # Documentación técnica
```

### 2.2 Flujo de Datos
1.  **Carga de Datos**: Al iniciar, el sistema carga las preguntas desde un archivo Excel configurado en `data/temas/`.
2.  **Interacción Usuario**: Las peticiones HTTP son manejadas por `app/routes.py`, que delega la lógica a `services.py` o `security.py`.
3.  **Persistencia**: Los datos transaccionales se guardan en la base de datos SQL (`data/instance/`). El estado temporal de una evaluación en curso se guarda en archivos JSON en `data/states/` para recuperación ante fallos.
4.  **Salida**: Al finalizar una evaluación, se genera un PDF (`pdf_generator.py`), se envía por correo (`utils.py`) y se sube a Drive (`drive_integration.py`).

---

## 3. Base de Datos

El sistema utiliza **SQLAlchemy** como ORM. El esquema relacional consta de las siguientes tablas:

### 3.1 Modelos (`models.py`)

#### `UserDB` (Administradores)
- `id`: Identificador único.
- `username`: Nombre de usuario.
- `email`: Correo electrónico.
- `password_hash`: Hash de la contraseña (BCrypt).
- `role`: Rol del usuario (ej. 'admin').

#### `CandidatoDB`
- `id`: Identificador único.
- `codigo`: Código único de acceso a la prueba.
- `nombre_completo`: Nombre del candidato.
- `email`: Correo de contacto.
- `evaluacion_completada`: Booleano de estado.
- `puntos_finales`: Calificación obtenida.
- `nivel_final`: Nivel alcanzado en la prueba.
- `resultados`: Relación 1:N con `ResultadoDB`.

#### `ResultadoDB`
- `id`: Identificador único.
- `candidato_id`: Clave foránea a `CandidatoDB`.
- `correctas`: Número de respuestas correctas.
- `total`: Total de preguntas.
- `porcentaje`: Porcentaje de acierto.
- `tema`: Tema de la evaluación.

#### `TemaDB`
- `id`: Identificador único.
- `nombre`: Nombre del banco de preguntas.
- `descripcion`: Descripción opcional.

#### `PreguntaDB`
- `id`: Identificador único.
- `tema_id`: Clave foránea a `TemaDB`.
- `texto`: Enunciado de la pregunta.
- `opciones`: Lista de opciones (JSON).
- `respuesta_correcta`: Opción correcta (ej. "A").
- `nivel`: Nivel de dificultad (1-5).

#### `RecoveryToken`
- `token`: Token único para recuperación de contraseña.
- `expires_at`: Fecha de expiración.
- `used`: Estado del token.

---

## 4. Componentes del Backend

### 4.1 `run.py` y `app/routes.py`
- **`run.py`**: Punto de entrada. Inicializa la aplicación, crea las tablas de base de datos y arranca el servidor.
- **`app/routes.py`**: Define las rutas URL (Blueprint), configura el logging y gestiona el ciclo de vida de las peticiones. Implementa decoradores como `@admin_required` y `@limiter.limit` para protección de rutas.

### 4.2 `app/services.py`
Contiene la lógica core de la evaluación:
- **`EvaluadorRespuestas`**: Evalúa respuestas simples y múltiples.
- **`EvaluacionService`**: Gestiona el estado de la evaluación (guardar/cargar progreso en `data/states/`), verifica avance de nivel y terminación temprana. Implementa la lógica de recuperación de sesión.

### 4.3 `app/drive_integration.py`
Maneja la autenticación OAuth2 con Google y la subida de archivos.
- Requiere `config/client_credentials.json` y genera `config/token.json`.
- Sube los PDFs a una carpeta específica definida por `DRIVE_FOLDER_ID`.

### 4.4 `app/pdf_generator.py`
Utiliza `ReportLab` para crear documentos PDF dinámicos.
- Genera encabezados con datos del candidato.
- Crea tablas de resultados.
- Guarda el archivo localmente en `data/reportes_pdf/` antes de la subida.

### 4.5 `app/utils.py`
- **Email**: Envío de correos SMTP (`smtplib`).
- **Excel**: Lectura y parseo de preguntas usando `pandas`.
- **Logging**: Configuración centralizada de logs.

---

## 5. Frontend

El frontend es renderizado desde el servidor (Server-Side Rendering) usando **Jinja2**.

### 5.1 Templates Principales
- `admin_dashboard.html`: Panel de control para administradores.
- `admin_temas.html`: Gestión de bancos de preguntas.
- `admin_preguntas.html`: Editor de preguntas para un tema específico.
- `cuestionario.html`: Interfaz de la evaluación para el candidato. Maneja la lógica de presentación de preguntas y temporizador vía JavaScript.
- `admin_login.html`: Formulario de acceso.

### 5.2 Archivos Estáticos (`static/`)
- **CSS**: Estilos modulares (`admin-dashboard.css`, `cuestionario.css`, `theme.css`).
- **JS**: Lógica del lado del cliente.
    - `cuestionario.js`: Maneja la interacción en la prueba, envío de respuestas AJAX y control de tiempo.
    - `admin-panel.js`: Funcionalidades del dashboard.

---

## 6. Configuración e Instalación

### 6.1 Requisitos Previos
- Python 3.10 o superior.
- Cuenta de Google Cloud Platform (para API de Drive).
- Servidor SMTP (para correos).

### 6.2 Variables de Entorno (`.env`)
Crear un archivo `.env` en la raíz con las siguientes variables:

```env
SECRET_KEY=tu_clave_secreta_segura
FLASK_DEBUG=True
PORT=5000
# DATABASE_URL es opcional para SQLite (por defecto usa data/instance/evaluacion.db)
# DATABASE_URL=sqlite:///data/instance/evaluacion.db

# Credenciales Admin Iniciales
# Si se cambia ADMIN_PASS aquí, se actualizará automáticamente en la BD al reiniciar
ADMIN_USER=admin
ADMIN_PASS=12345678
ADMIN_EMAIL=admin@empresa.com

# Configuración SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
EMAIL_FROM=no-reply@empresa.com

# Firma de Correos
SIGN_NAME=Nombre Admin
SIGN_TITLE=Cargo
```

### 6.3 Archivos de Credenciales
- **`config/client_credentials.json`**: Descargar desde Google Cloud Console (OAuth 2.0 Client ID) y colocar en la carpeta `config/`.

### 6.4 Instalación
1. Crear entorno virtual: `python -m venv venv`
2. Activar entorno: `venv\Scripts\activate` (Windows)
3. Instalar dependencias: `pip install -r requirements.txt`
4. Ejecutar aplicación: `python run.py` (Esto inicializará la base de datos y creará las carpetas necesarias).

---

## 7. Seguridad

- **Autenticación**: Sesiones de Flask firmadas para admins. Tokens de acceso único para candidatos.
- **Contraseñas**: Hashing con `bcrypt`.
- **Protección CSRF**: Implementada en formularios críticos.
- **Headers**: Se aplican cabeceras de seguridad HTTP (HSTS, X-Frame-Options, etc.) en `security.py`.
- **Sanitización**: Limpieza de logs para evitar inyección de caracteres de control.

---

## 8. Mantenimiento y Solución de Problemas

### 8.1 Logs
El sistema escribe logs detallados en `evaluacion_system.log`. Revisar este archivo ante errores 500.

### 8.2 Actualización de Preguntas
1. Modificar el archivo Excel configurado (ej. `Evaluación FWS PAN V2.xlsx`).
2. Asegurar que las columnas coincidan con lo esperado por `utils.py` (Pregunta, A, B, C, D, Respuesta Correcta, Nivel, Tema).
3. Reiniciar la aplicación o recargar la configuración desde el panel admin (si está implementado).

### 8.3 Errores Comunes
- **Error de Google Drive**: Si el token expira o es revocado, borrar `config/token.json` y volver a autenticar al iniciar la app.
- **Error de SMTP**: Verificar que la contraseña de aplicación (App Password) sea correcta y que el puerto 587 esté habilitado.
- **Permisos de Escritura**: Asegurar que la aplicación tenga permisos de escritura en la carpeta `data/` y sus subcarpetas (`instance/`, `reportes_pdf/`, `states/`).
- **Login Loop / Sesión Inválida**: Si no se puede iniciar sesión, verificar que `SECRET_KEY` esté configurada en `.env`. Si cambia la clave, las sesiones antiguas se invalidarán.
- **Candidatos no aparecen**: Verificar que la base de datos `data/instance/evaluacion.db` tenga permisos de escritura. El sistema guarda automáticamente los registros en esta ubicación.
