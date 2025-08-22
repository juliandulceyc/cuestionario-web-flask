# DOCUMENTACIÓN TÉCNICA - SISTEMA DE EVALUACIÓN FWS PAN  
Bitácora de Desarrollo - Práctica Profesional

---

## 1. INFORMACIÓN GENERAL DEL PROYECTO

### 1.1 Datos del Proyecto
- **Nombre del Proyecto:** Sistema de Evaluación FWS PAN
- **Desarrollador:** [Tu Nombre Completo]
- **Empresa:** [Nombre de la Empresa]
- **Fecha de Inicio:** [Fecha de inicio]
- **Fecha de Finalización:** [Fecha de finalización]
- **Programa/Formación:** [Programa académico o área]

### 1.2 Descripción General
Sistema web desarrollado en Python Flask para la evaluación técnica de candidatos mediante cuestionarios adaptativos. Utiliza preguntas almacenadas en Excel, progresión por niveles, sistema de puntuación y reportes automáticos.

### 1.3 Objetivos del Proyecto
- **Objetivo General:** Automatizar el proceso de evaluación técnica de personal mediante una aplicación web interactiva.
- **Objetivos Específicos:**
  - Crear una interfaz web intuitiva y responsive.
  - Implementar lectura y validación de preguntas desde Excel.
  - Desarrollar lógica de progresión por niveles y terminación temprana.
  - Integrar sistema de puntuación y generación de reportes PDF.
  - Facilitar la gestión de candidatos y resultados para RRHH.

---

## 2. ANÁLISIS TÉCNICO

### 2.1 Tecnologías Utilizadas

| Tecnología   | Versión | Propósito                        |
|--------------|--------|-----------------------------------|
| Python       | 3.8+   | Lenguaje principal                |
| Flask        | 2.x    | Framework web backend             |
| Pandas       | 2.x    | Procesamiento de datos Excel      |
| openpyxl     | 3.x    | Lectura de archivos Excel         |
| HTML5/CSS3   | -      | Estructura y estilos frontend     |
| JavaScript   | ES6+   | Interactividad frontend           |

### 2.2 Arquitectura del Sistema

```
Empresa/
├── pdf_generator.py            # Aplicación principal
├── Evaluación FWS PAN V2.xlsx  # Base de datos de preguntas
├── templates/
│   ├── admin_login.html        # Login administrativo
│   ├── admin_dashboard.html    # Panel principal
│   ├── panel_admin.html        # Gestión de candidatos
│   ├── cuestionario.html       # Interfaz de evaluación
│   ├── reporte.html            # Reportes de resultados
│   └── error.html              # Páginas de error
├── static/
│   ├── css/                    # Estilos frontend
│   ├── js/                     # Scripts JS
│   └── images/                 # Recursos gráficos
└── requirements.txt            # Dependencias
```

### 2.3 Flujo de Datos

1. **Carga Inicial:** Lectura y validación de preguntas desde Excel.
2. **Registro:** El administrador registra candidatos y genera códigos únicos.
3. **Evaluación:** El candidato accede con su código y responde preguntas adaptativas.
4. **Procesamiento:** El sistema evalúa respuestas, calcula puntos y determina avance de nivel.
5. **Finalización:** Generación automática de reporte y visualización de resultados.

---

## 3. DESARROLLO PASO A PASO

### 3.1 Configuración del Entorno

```bash
# Instalación de dependencias
pip install flask pandas openpyxl xlrd

# Estructura de directorios
mkdir templates static static/css static/js
```

### 3.2 Backend (pdf_generator.py)

- **Importación de librerías:**  
  `from flask import Flask, render_template, request, jsonify`
  `import pandas as pd`

- **Carga de datos:**  
  Lectura de preguntas desde Excel, validación de campos obligatorios, clasificación por niveles y detección de preguntas múltiples.

- **Sistema de rutas:**  
  - `/admin/login` - Login administrativo  
  - `/admin/dashboard` - Panel principal  
  - `/admin/candidatos` - Gestión de candidatos  
  - `/evaluacion/<codigo>` - Acceso a evaluación  
  - `/obtener_pregunta` - API para obtener preguntas  
  - `/responder` - Procesar respuesta  
  - `/generar_pdf_final` - Finalizar y generar reporte

### 3.3 Frontend

- **HTML:**  
  Estructura responsive, contenedores para preguntas y opciones, botones de navegación.

- **CSS:**  
  Diseño moderno, retroalimentación visual, colores por estado.

- **JavaScript:**  
  Comunicación AJAX con backend, manejo de estados, validación de respuestas.

---

## 4. FUNCIONALIDADES IMPLEMENTADAS

### 4.1 Gestión de Preguntas
- Carga automática desde Excel.
- Validación de datos completos.
- Clasificación por niveles y tipo (simple/múltiple).

### 4.2 Sistema de Progresión
- Niveles adaptativos (1-5) según rendimiento.
- Criterios de avance y terminación temprana.
- Reciclaje de preguntas si se agotan.

### 4.3 Interfaz de Usuario
- Diseño responsive.
- Retroalimentación inmediata.
- Navegación intuitiva.

### 4.4 Sistema de Puntuación
- Puntos por respuesta correcta (1.0 x nivel).
- Puntos parciales en preguntas múltiples (0.5 x nivel).
- Visualización de progreso y resultados.

### 4.5 Gestión de Candidatos y Reportes
- Registro y seguimiento de candidatos.
- Generación automática de reportes PDF.
- Panel de administración y monitoreo en tiempo real.

---

## 5. PROBLEMAS ENCONTRADOS Y SOLUCIONES

### 5.1 Error: Archivo Excel no encontrado
- **Causa:** Nombre incorrecto o ubicación errónea.
- **Solución:** Verificar nombre y ruta del archivo.

### 5.2 Error: No se cargaron preguntas válidas
- **Causa:** Formato o columnas incorrectas en Excel.
- **Solución:** Validar estructura y datos obligatorios.

### 5.3 Error: Evaluación no iniciada
- **Causa:** Código de candidato inválido o sesión expirada.
- **Solución:** Verificar registro y reiniciar evaluación.

### 5.4 Error de puerto en uso
- **Causa:** Puerto 5000 ocupado.
- **Solución:** Cambiar puerto en `app.run(port=5001)` o cerrar procesos.

### 5.5 Problemas de rendimiento
- **Causa:** Muchos candidatos simultáneos.
- **Solución:** Limitar usuarios y reiniciar servidor periódicamente.

---

## 6. TESTING Y VALIDACIÓN

### 6.1 Pruebas Funcionales
- ✅ Carga correcta de preguntas desde Excel.
- ✅ Navegación y progresión por niveles.
- ✅ Cálculo de puntuación y avance.
- ✅ Generación de reportes PDF.

### 6.2 Pruebas de Interfaz
- ✅ Responsividad en diferentes dispositivos.
- ✅ Retroalimentación visual adecuada.
- ✅ Usabilidad intuitiva.

### 6.3 Pruebas de Rendimiento
- ✅ Carga rápida de preguntas.
- ✅ Respuesta inmediata a interacciones.
- ✅ Manejo eficiente de memoria.

---

## 7. DEPLOYMENT Y CONFIGURACIÓN

### 7.1 Requisitos del Sistema
- Python 3.8 o superior
- 2 GB RAM mínimo
- 500 MB espacio en disco
- Navegador web moderno

### 7.2 Instalación

```bash
# Clonar repositorio
git clone [URL_DEL_REPOSITORIO]

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python pdf_generator.py
```

### 7.3 Configuración
- El archivo Excel debe estar en el directorio raíz.
- Puerto por defecto: 5000
- Modo debug habilitado para desarrollo.

---

## 8. MANTENIMIENTO Y MEJORAS FUTURAS

### 8.1 Mantenimiento Preventivo
- Backup regular del archivo Excel y reportes.
- Monitoreo de logs de errores.
- Actualización de dependencias.

### 8.2 Mejoras Propuestas
- Migración a base de datos SQL para persistencia.
- Sistema de usuarios y roles diferenciados (Administrador, RRHH, Candidato).
- Reportes avanzados y estadísticas.
- Temporizador por pregunta.
- Integración con sistemas externos.

---

## 9. CONCLUSIONES

### 9.1 Objetivos Alcanzados
- Sistema funcional de evaluación técnica web.
- Interfaz intuitiva y responsive.
- Integración exitosa con datos Excel.
- Progresión adaptativa por niveles.

### 9.2 Competencias Desarrolladas
- Programación Backend: Python, Flask, APIs.
- Programación Frontend: HTML, CSS, JavaScript.
- Manejo de datos: Pandas, Excel.
- Control de versiones: Git.
- Resolución de problemas y testing.

### 9.3 Aprendizajes Obtenidos
- Importancia de la planificación y documentación.
- Valor del testing continuo.
- Metodologías de desarrollo iterativo.

---

## 10. ANEXOS

### 10.1 Código Fuente Principal
- Referencia a archivos del proyecto.

### 10.2 Capturas de Pantalla
- Imágenes de la interfaz funcionando.

### 10.3 Logs de Desarrollo
- Registro cronológico de cambios importantes.

---

**Elaborado por:** [Tu Nombre Completo]  
**Fecha:** [Fecha de elaboración]  
**Programa:** [Programa académico]  
**Empresa:** [Nombre de la Empresa]  
**Versión:** 2.0  
**© 2025 Sistema de Evaluación FWS