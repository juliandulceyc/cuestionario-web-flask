# 🚀 GUÍA COMPLETA - CONFIGURACIÓN GOOGLE DRIVE
## Sistema de Evaluación de Candidatos

---

## 📋 **PASO 1: INSTALACIÓN DE DEPENDENCIAS**

```bash
pip install -r requirements.txt
```

Si tienes problemas, instala manualmente:
```bash
pip install reportlab Pillow
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

---

## 🔧 **PASO 2: CONFIGURACIÓN DE GOOGLE CLOUD CONSOLE**

### 2.1 Crear Proyecto en Google Cloud
1. **Ir a:** [Google Cloud Console](https://console.cloud.google.com)
2. **Clic en:** "Seleccionar proyecto" (parte superior)
3. **Clic en:** "NUEVO PROYECTO"
4. **Datos del proyecto:**
   - **Nombre:** `Evaluacion-Candidatos-SENA`
   - **Organización:** (dejar por defecto)
5. **Clic en:** "CREAR"
6. **Esperar** que se cree el proyecto (30-60 segundos)
7. **Seleccionar** el proyecto recién creado

### 2.2 Habilitar Google Drive API
1. **En el menú lateral izquierdo:** "APIs y servicios" → "Biblioteca"
2. **Buscar:** "Google Drive API"
3. **Clic en:** "Google Drive API" (primer resultado)
4. **Clic en:** "HABILITAR"
5. **Esperar** confirmación (aparecerá "API habilitada")

---

## 🔐 **PASO 3: CREAR CUENTA DE SERVICIO**

### 3.1 Configurar Credenciales
1. **En el menú lateral:** "APIs y servicios" → "Credenciales"
2. **Clic en:** "CREAR CREDENCIALES" → "Cuenta de servicio"

### 3.2 Completar Datos de la Cuenta de Servicio
**Paso 1 de 3:**
- **Nombre de la cuenta de servicio:** `evaluacion-candidatos-service`
- **ID de la cuenta de servicio:** `evaluacion-candidatos-service` (se auto-completa)
- **Descripción:** `Servicio para guardar resultados de evaluación de candidatos`
- **Clic en:** "CREAR Y CONTINUAR"

**Paso 2 de 3:**
- **Función:** Seleccionar "Editor" en el menú desplegable
- **Clic en:** "CONTINUAR"

**Paso 3 de 3:**
- **Dejar en blanco** (es opcional)
- **Clic en:** "LISTO"

### 3.3 Generar Archivo de Credenciales JSON
1. **En la lista de cuentas de servicio:** Clic en la que acabas de crear
2. **Ir a la pestaña:** "CLAVES"
3. **Clic en:** "AGREGAR CLAVE" → "Crear nueva clave"
4. **Seleccionar:** "JSON"
5. **Clic en:** "CREAR"
6. **Se descarga automáticamente** un archivo JSON
7. **IMPORTANTE:** Guardar este archivo en lugar seguro

---

## 📁 **PASO 4: CONFIGURAR EL PROYECTO**

### 4.1 Colocar Archivo de Credenciales
1. **Renombrar** el archivo descargado como: `credentials.json`
2. **Copiar** el archivo al directorio del proyecto:
   ```
   c:\Users\USUARIO\Documents\Empresa\credentials.json
   ```
3. **Verificar** que esté al mismo nivel que `app.py`

### 4.2 Estructura Final del Proyecto
```
📁 Empresa/
├── 📄 app.py
├── 📄 credentials.json          ⬅️ ARCHIVO IMPORTANTE
├── 📄 drive_integration.py
├── 📄 pdf_generator.py
├── 📄 requirements.txt
├── 📁 templates/
│   └── 📄 cuestionario.html
├── 📁 static/
└── 📊 Evaluación FWS PAN V2.xlsx
```

---

## 🗂️ **PASO 5: CREAR CARPETA EN GOOGLE DRIVE**

### 5.1 Crear Carpeta para Resultados
1. **Ir a:** [Google Drive](https://drive.google.com)
2. **Clic derecho** en espacio vacío → "Nueva carpeta"
3. **Nombre:** `Resultados_Evaluacion_Candidatos`
4. **Clic en:** "Crear"

### 5.2 Obtener Email de la Cuenta de Servicio
1. **Abrir** el archivo `credentials.json` con Notepad
2. **Buscar** la línea que dice: `"client_email"`
3. **Copiar** el email (ejemplo: `evaluacion-candidatos-service@tu-proyecto.iam.gserviceaccount.com`)

### 5.3 Compartir Carpeta con la Cuenta de Servicio
1. **Clic derecho** en la carpeta `Resultados_Evaluacion_Candidatos`
2. **Clic en:** "Compartir"
3. **En "Añadir personas y grupos":** Pegar el email de la cuenta de servicio
4. **Permisos:** Seleccionar "Editor"
5. **DESMARCAR:** "Notificar a las personas"
6. **Clic en:** "Enviar"

---

## 🔒 **PASO 6: CONFIGURACIÓN DE SEGURIDAD**

### 6.1 Crear Archivo .gitignore
**Crear** archivo `.gitignore` en el directorio del proyecto:
```gitignore
credentials.json
*.json
__pycache__/
*.pyc
.env
reportes_pdf/
```

### 6.2 Verificar Seguridad
- ❌ **NUNCA** subir `credentials.json` a GitHub
- ✅ **Siempre** mantener el archivo en local
- ✅ **Backup** del archivo en lugar seguro

---

## 🧪 **PASO 7: PRUEBAS DE FUNCIONAMIENTO**

### 7.1 Probar Instalación
```bash
cd "c:\Users\USUARIO\Documents\Empresa"
python -c "import reportlab; print('✅ ReportLab OK')"
python -c "from google.oauth2 import service_account; print('✅ Google Auth OK')"
```

### 7.2 Probar Generación de PDF
```bash
python pdf_generator.py
```
**Resultado esperado:** Se crea archivo `reporte_ejemplo.pdf` en carpeta `reportes_pdf/`

### 7.3 Probar Aplicación Completa
```bash
python app.py
```
**Resultado esperado:**
```
✅ Google Drive integration disponible
✅ Generación de PDF disponible
Cargando preguntas desde Excel...
...
Iniciando Cuestionario Web
```

---

## 🌐 **PASO 8: USAR EL SISTEMA**

### 8.1 Acceder al Sistema
1. **Ejecutar:** `python app.py`
2. **Abrir navegador:** http://localhost:5000
3. **Completar** datos del candidato
4. **Responder** preguntas del cuestionario

### 8.2 Generar Reportes
**Al finalizar la evaluación aparecerán botones:**
- 📄 **Generar Reporte PDF** - Crea PDF local
- 💾 **Guardar en Drive** - Sube datos a Google Drive

### 8.3 Ubicación de Archivos
- **PDFs locales:** `reportes_pdf/`
- **Datos en Drive:** Carpeta `Resultados_Evaluacion_Candidatos`

---

## ❗ **SOLUCIÓN DE PROBLEMAS COMUNES**

### Error: "No module named 'reportlab'"
```bash
pip install reportlab Pillow
```

### Error: "credentials.json not found"
- Verificar que el archivo esté en el directorio correcto
- Verificar que se llame exactamente `credentials.json`

### Error: "Access denied" en Google Drive
- Verificar que la carpeta esté compartida con la cuenta de servicio
- Verificar el email en `credentials.json`
- Verificar permisos de "Editor"

### Error: "API not enabled"
- Verificar que Google Drive API esté habilitado en Google Cloud Console
- Esperar 5-10 minutos después de habilitar la API

---

## 📞 **SOPORTE TÉCNICO**

Si tienes problemas:
1. **Verificar** todos los pasos de esta guía
2. **Revisar** los logs en la consola
3. **Consultar** la documentación del proyecto

---

**✅ CONFIGURACIÓN COMPLETA**
Una vez completados todos los pasos, el sistema estará listo para:
- Evaluar candidatos
- Generar reportes PDF profesionales
- Guardar automáticamente en Google Drive
- Proporcionar análisis completos para RRHH
