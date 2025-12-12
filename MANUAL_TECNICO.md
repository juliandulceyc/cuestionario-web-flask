# Manual Técnico - Sistema de Evaluación de Candidatos

## 1. Introducción

### 1.1 Propósito
El Sistema de Evaluación de Candidatos es una plataforma web integral diseñada para administrar, ejecutar y calificar pruebas técnicas o psicotécnicas. Su objetivo es simplificar el proceso de selección de personal mediante la automatización de cuestionarios, calificación instantánea y generación de reportes detallados.

### 1.2 Alcance y Funcionalidades
La aplicación cubre el ciclo completo de evaluación con las siguientes características avanzadas:
- **Gestión de Usuarios**: Autenticación segura para administradores con protección contra ataques de fuerza bruta (Rate Limiting).
- **Bancos de Preguntas Híbridos**: Soporte para cargar preguntas desde archivos Excel o gestionarlas directamente desde una interfaz web (CRUD de Temas y Preguntas).
- **Evaluación Robusta**:
    - Lógica de niveles de dificultad.
    - Temporizador y control de tiempo.
    - **Recuperación de Sesión**: Si el navegador se cierra o recarga, el candidato puede retomar la prueba exactamente donde la dejó.
- **Registro de Candidatos**: Formulario de registro con validación de duplicados.
- **Reportes Automáticos**: Generación de PDFs con resultados detallados y almacenamiento automático en Google Drive.
- **Notificaciones**: Envío de correos electrónicos con resultados o enlaces de recuperación de contraseña.

### 1.3 Tecnologías Utilizadas
- **Backend**: Python 3.10+, Flask, SQLAlchemy (ORM), Flask-Limiter.
- **Base de Datos**: SQLite (por defecto, autoconfigurable), compatible con PostgreSQL/MySQL.
- **Frontend**: HTML5, TailwindCSS, JavaScript (Vanilla), Jinja2.
- **Integraciones**: Google Drive API v3, SMTP (Email).
- **Seguridad**: BCrypt (Hashing), PyJWT (Tokens), Rate Limiting.

---

## 2. Instalación y Configuración (Cualquier Entorno)

Esta guía asegura que la aplicación funcione en Windows, macOS o Linux.

### 2.1 Requisitos Previos
- **Python 3.10** o superior instalado.
- **Git** (opcional, para clonar el repositorio).
- Acceso a internet para instalar dependencias.

### 2.2 Paso a Paso

#### 1. Obtener el Código
Clone el repositorio o descargue y descomprima el archivo ZIP del proyecto.
```bash
git clone <url-del-repositorio>
cd appCuestionario
```

#### 2. Crear un Entorno Virtual
Es crucial usar un entorno virtual para aislar las dependencias.

*   **Windows**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **macOS / Linux**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

#### 3. Instalar Dependencias
Ejecute el siguiente comando para instalar todas las librerías necesarias:
```bash
pip install -r requirements.txt
```

#### 4. Configurar Variables de Entorno
Cree un archivo llamado `.env` en la raíz del proyecto (puede copiar el ejemplo si existe). Configure las siguientes variables clave:

```env
# Seguridad
SECRET_KEY=cambiar_por_una_clave_muy_segura_y_larga
FLASK_DEBUG=False  # Poner en True solo para desarrollo

# Servidor
PORT=5000

# Base de Datos (Opcional, por defecto usa SQLite local)
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# Credenciales Admin Iniciales (Se crean al primer inicio)
ADMIN_USER=admin
ADMIN_PASS=12345678
ADMIN_EMAIL=admin@empresa.com

# Configuración SMTP (Correo)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
EMAIL_FROM=no-reply@empresa.com
```

#### 5. Configuración de Google Drive (Opcional)
Para que funcione la subida automática a Drive:
1.  Obtenga el archivo `client_credentials.json` de su proyecto en Google Cloud Console (OAuth 2.0 Client ID).
2.  Colóquelo en la carpeta `config/`.
3.  Al primer uso, el sistema pedirá autenticación y generará `config/token.json`.

---

## 3. Base de Datos

El sistema utiliza **SQLAlchemy** como ORM, lo que abstrae el motor de base de datos subyacente.

### 3.1 Inicialización Automática
**No es necesario ejecutar scripts SQL manualmente.**
Al ejecutar la aplicación por primera vez (`python run.py`), el sistema detecta si la base de datos existe. Si no, crea automáticamente todas las tablas necesarias en `data/instance/evaluacion.db` (para SQLite).

### 3.2 Esquema Relacional
A continuación se describe la estructura de datos que el sistema genera:

#### Tabla: `users` (Administradores)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer (PK) | Identificador único |
| username | String | Nombre de usuario (único) |
| email | String | Correo electrónico (único) |
| password_hash | String | Hash seguro de la contraseña |
| role | String | Rol (ej. 'admin') |
| is_active | Boolean | Estado de la cuenta |

#### Tabla: `temas` (Bancos de Preguntas)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer (PK) | Identificador único |
| nombre | String | Nombre del banco (único) |
| descripcion | String | Descripción opcional |
| activo | Boolean | Si está disponible para uso |

#### Tabla: `preguntas`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer (PK) | Identificador único |
| tema_id | Integer (FK) | Relación con `temas` |
| texto | Text | Enunciado de la pregunta |
| opciones | JSON | Lista de opciones ["A) ...", "B) ..."] |
| respuesta_correcta | String | Letra correcta (ej. "A") |
| nivel | Integer | Dificultad (1-5) |
| multiple | Boolean | Si permite múltiples respuestas |

#### Tabla: `candidatos`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer (PK) | Identificador único |
| codigo | String | Código de acceso único |
| nombre_completo | String | Nombre del candidato |
| email | String | Correo electrónico |
| evaluacion_completada | Boolean | Estado de la prueba |
| nivel_final | Integer | Nivel alcanzado |
| tema | String | Tema asignado |

#### Tabla: `resultados`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer (PK) | Identificador único |
| candidato_id | Integer (FK) | Relación con `candidatos` |
| correctas | Integer | Cantidad de aciertos |
| total | Integer | Total de preguntas |
| porcentaje | Float | Rendimiento (0-100) |

---

## 4. Ejecución y Uso

### 4.1 Iniciar el Servidor
Desde la terminal, en la raíz del proyecto y con el entorno virtual activado:

```bash
python run.py
```

Verá logs indicando que el sistema se ha iniciado, la configuración de preguntas cargada y la dirección de acceso (usualmente `http://localhost:5000`).

### 4.2 Acceso al Sistema
1.  Abra su navegador web.
2.  Vaya a `http://localhost:5000/admin/login`.
3.  Ingrese con las credenciales configuradas en `.env` (Default: `admin` / `12345678`).

### 4.3 Flujo de Trabajo Típico
1.  **Preparar Preguntas**:
    *   *Opción A (Web)*: Ir a "Bancos" -> "Crear Tema" -> Agregar preguntas manualmente.
    *   *Opción B (Excel)*: Colocar un archivo `.xlsx` en `data/temas/` y seleccionarlo desde el Dashboard.
2.  **Registrar Candidato**: En el Dashboard, llenar el formulario de registro.
3.  **Realizar Prueba**: El candidato accede con su número de documento (o enlace generado).
4.  **Ver Resultados**: Al finalizar, el admin puede ver los resultados en el Dashboard y descargar el PDF.

---

## 5. Mantenimiento y Solución de Problemas

### 5.1 Logs del Sistema
El archivo `evaluacion_system.log` contiene información detallada de errores y eventos. Revíselo si algo falla.

### 5.2 Problemas Comunes

*   **Error "ModuleNotFoundError"**: Asegúrese de haber activado el entorno virtual y ejecutado `pip install -r requirements.txt`.
*   **Error de Base de Datos / Migraciones**: Si cambia la estructura de los modelos y la base de datos ya existe, puede haber conflictos.
    *   *Solución Rápida (Desarrollo)*: Borre el archivo `data/instance/evaluacion.db` y reinicie la aplicación. Se creará una nueva DB limpia.
*   **Rate Limiting (429 Too Many Requests)**: Si se bloquea por muchos intentos de login fallidos, espere 1 minuto antes de intentar nuevamente.
*   **Google Drive Falla**: Verifique que `config/token.json` sea válido. Si duda, bórrelo para re-autenticar.

### 5.3 Respaldo
Para respaldar la información, copie regularmente la carpeta `data/`. Esta contiene:
- La base de datos (`instance/`).
- Los reportes generados (`reportes_pdf/`).
- Los archivos de temas (`temas/`).

---

## 6. Estructura del Proyecto

```
appCuestionario/
├── app/                        # Núcleo de la aplicación
│   ├── models.py               # Definición de tablas (BD)
│   ├── routes.py               # Controladores y rutas Web
│   ├── services.py             # Lógica de negocio (Evaluación)
│   ├── templates/              # Vistas HTML
│   └── static/                 # CSS y JS
├── config/                     # Archivos de configuración
├── data/                       # Almacenamiento de datos
├── run.py                      # Script de inicio
├── requirements.txt            # Lista de dependencias
└── MANUAL_TECNICO.md           # Esta documentación
```

---

## 7. Pruebas y Calidad de Código

El proyecto incluye una suite de pruebas automatizadas utilizando `pytest` para garantizar la estabilidad del sistema.

### 7.1 Ejecutar Pruebas
Para correr las pruebas unitarias y de integración, ejecute el siguiente comando desde la raíz del proyecto (con el entorno virtual activo):

```bash
python -m pytest
```

Esto ejecutará todos los tests ubicados en la carpeta `tests/` y mostrará un reporte de éxito o fallo.

### 7.2 Cobertura de Código (Coverage)
Si desea ver qué porcentaje del código está cubierto por las pruebas, puede usar `coverage`:

```bash
pip install coverage
coverage run -m pytest
coverage report -m
```

### 7.3 Análisis Estático (SonarCloud)
El proyecto está configurado con GitHub Actions para ejecutar un análisis de calidad en SonarCloud cada vez que se hace un push a la rama `master`. El archivo de configuración se encuentra en `.github/workflows/sonarcloud.yml`.

