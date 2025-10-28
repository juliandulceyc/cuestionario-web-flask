# Manual de Usuario — Sistema de Evaluación Técnica

Fecha: 21/10/2025
Versión del sistema: 1.0

## Tabla de contenido
- [1. Descripción general](#1-descripción-general)
- [2. Requisitos del sistema](#2-requisitos-del-sistema)
- [3. Acceso y roles](#3-acceso-y-roles)
- [4. Panel de Administración](#4-panel-de-administración)
  - [4.1. Inicio de sesión](#41-inicio-de-sesión)
  - [4.2. Gestión de candidatos](#42-gestión-de-candidatos)
  - [4.3. Resultados de evaluaciones](#43-resultados-de-evaluaciones)
  - [4.4. Gestión de temas (banco de preguntas)](#44-gestión-de-temas-banco-de-preguntas)
- [5. Evaluación del candidato](#5-evaluación-del-candidato)
  - [5.1. Flujo](#51-flujo)
  - [5.2. Reglas de avance y finalización](#52-reglas-de-avance-y-finalización)
  - [5.3. Interfaz de evaluación](#53-interfaz-de-evaluación)
- [6. Reportes PDF](#6-reportes-pdf)
- [7. Recuperación de contraseña (Administrador)](#7-recuperación-de-contraseña-administrador)
- [8. Solución de problemas](#8-solución-de-problemas)
- [9. Seguridad](#9-seguridad)
- [10. Glosario](#10-glosario)
- [11. Historial de versiones (extracto)](#11-historial-de-versiones-extracto)
- [12. Contacto y soporte](#12-contacto-y-soporte)

## 1. Descripción general
El Sistema de Evaluación Técnica permite gestionar candidatos, aplicar evaluaciones por niveles y generar reportes PDF con los resultados. Incluye un panel de administración para registrar/editar candidatos, ver resultados y gestionar el banco de temas (archivo Excel). La evaluación del candidato se realiza mediante un enlace único.

Funciones clave:
- Gestión de candidatos: registro, edición y eliminación.
- Enlaces de evaluación por candidato.
- Evaluación adaptativa por niveles (1 a 5) con reglas de avance/terminación.
- Generación automática de reporte PDF al finalizar.
- Recuperación de contraseña de administrador por email (SMTP).
- (Opcional) Envío del PDF a Google Drive.

Perfiles:
- Administrador
- Candidato

## 2. Requisitos del sistema
- Sistema operativo: Windows 10/11 (recomendado) o equivalente.
- Navegador: Chrome/Edge/Firefox actualizados.
- Python 3.10+ (recomendado 3.11 ó 3.13).
- Dependencias Python (ver `requirements.txt`).
- SMTP funcional (Gmail u otro) para recuperación de contraseña.
- Base de datos PostgreSQL si se desea persistencia en BD (configurada en `.env`).

## 3. Acceso y roles
- Administrador:
  - URL de acceso: `http://localhost:PORT/admin/login` (por defecto PORT=5000).
  - Recuperación de contraseña: `http://localhost:PORT/admin/recuperar-password`.
  - Primer uso (si no hay usuarios): `http://localhost:PORT/admin/first-run`.
- Candidato:
  - Acceso mediante un enlace único, por ejemplo: `http://localhost:PORT/evaluacion/<CODIGO>`.

## 4. Panel de Administración
### 4.1. Inicio de sesión
1. Ir a `Admin > Iniciar sesión`.
2. Ingresar usuario y contraseña.
3. Si olvidaste la contraseña, usa "Recuperar contraseña" y recibirás un enlace por email si tu usuario existe.

### 4.2. Gestión de candidatos
- Registrar candidato: botón "➕ Registrar Candidato" y completar el formulario.
- Editar candidato: botón "✏️ Editar" en la tarjeta del candidato, modificar y Guardar. Los cambios se reflejan en vivo.
- Eliminar candidato: botón "🗑️ Eliminar".
- Copiar URL de evaluación: botón "📋 Copiar URL".
- Abrir evaluación (vista candidato): link "🔗 Abrir Evaluación".

Notas:
- Campos editables: Tipo/Número de documento, Nombre completo, Email, Teléfono, Cargo.
- Validación de email: el sistema valida formato; mostrará error si no es válido.

### 4.3. Resultados de evaluaciones
- Tabla con: Tema, Correctas, Total, Porcentaje, Puntos, Nivel final, Fecha.
- Filtros por nombre, documento, email, tema, estado (con/sin resultado) y nivel.
- Al editar datos de candidato (nombre/documento/email), la fila se actualiza en vivo.

### 4.4. Gestión de temas (banco de preguntas)
- Se cargan desde un archivo Excel (por defecto `Evaluación FWS PAN V2.xlsx`).
- En la sección de temas puedes listar y eliminar archivos Excel cargados.

## 5. Evaluación del candidato
### 5.1. Flujo
1. El candidato abre su enlace de evaluación.
2. Responde cada pregunta y pulsa "Responder".
3. El sistema avanza preguntas y niveles de forma adaptativa.
4. Al terminar, se muestra un resumen y se genera el PDF automáticamente.

### 5.2. Reglas de avance y finalización
- Niveles: 1 a 5.
- Avance de nivel: requiere 5 respuestas correctas dentro del nivel actual.
- Máximo por nivel: 8 preguntas; si no se alcanzan 5 correctas en esas 8, la evaluación termina anticipadamente.
- Límite total: 40 preguntas.
- Motivos de finalización que puede registrar el sistema:
  - Completó todos los niveles.
  - Terminación temprana por no alcanzar 5 correctas en 8 preguntas del nivel.
  - Alcanzó el límite total de preguntas.

### 5.3. Interfaz de evaluación
- Preguntas de selección única y múltiple.
- Indicadores de progreso y accesibilidad.
- Al finalizar se muestra el resumen de resultados y el estado de generación del PDF.

## 6. Reportes PDF
- Se generan automáticamente al finalizar la evaluación.
- Contenido principal:
  - Resumen (preguntas respondidas, correctas, porcentaje, puntos, nivel alcanzado, calificación).
  - Rendimiento por niveles.
  - Detalle de preguntas incorrectas.
- Ubicación de archivos: carpeta `reportes_pdf/`.
- (Opcional) Envío a Google Drive si la integración está configurada.

## 7. Recuperación de contraseña (Administrador)
1. Ir a `Admin > Recuperar contraseña`.
2. Ingresa tu usuario ó email registrado.
3. Si existe, verás un mensaje de confirmación y se enviará un enlace a tu email.
4. Abre el enlace para definir una nueva contraseña (válido 30 minutos, un solo uso).

Requisitos SMTP (ejemplo Gmail):
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587 (STARTTLS) o 465 (SSL)
- EMAIL_USER=tu-cuenta@gmail.com
- EMAIL_FROM=tu-cuenta@gmail.com (debe coincidir con EMAIL_USER)
- EMAIL_PASSWORD=Contraseña de aplicación (16 caracteres, sin espacios)

Si aparece error 535 5.7.8 (BadCredentials):
- Verifica que EMAIL_USER=EMAIL_FROM y que usas una contraseña de aplicación.
- Revisa que no haya espacios extra en `.env`.
- Reinicia la app tras cambios en `.env`.

## 8. Solución de problemas
- No llegan correos de recuperación:
  - Revisa `.env` y credenciales SMTP.
  - Observa la consola: en modo DEBUG se muestra el detalle del error SMTP.
- Error HTTP 500 al editar candidato:
  - Validación de email incorrecta o formato inválido. Corrige y vuelve a guardar.
- No se genera el PDF:
  - Verifica que `reportlab` esté instalado y que el sistema finalice la evaluación.
  - Revisa la carpeta `reportes_pdf/` y la consola de logs.

## 9. Seguridad
- Sesiones con tokens renovables; expiración automática y cierre de sesión al expirar.
- Encabezados de seguridad en respuestas HTTP.

## 10. Glosario
- Candidato: Persona evaluada.
- Nivel: Dificultad de las preguntas (1 a 5).
- Terminación temprana: Fin del proceso por no alcanzar 5 correctas en 8 preguntas del nivel.

## 11. Historial de versiones (extracto)
- 1.0 — Flujo de recuperación por email, edición de candidatos en vivo, PDF ajustado (se removió la sección "Información Adicional"), mejoras de SMTP.

## 12. Contacto y soporte
- Para incidencias técnicas, adjunta captura de pantalla y el log `evaluacion_system.log`.
