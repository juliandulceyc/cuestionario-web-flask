# DOCUMENTACIÓN TÉCNICA - SISTEMA DE EVALUACIÓN DE CANDIDATOS
## BITÁCORA DE DESARROLLO - APRENDIZ SENA

---

## 1. INFORMACIÓN GENERAL DEL PROYECTO

### 1.1 Datos del Proyecto
- **Nombre del Proyecto:** Sistema de Evaluación de Candidatos para Selección de Personal
- **Aprendiz:** [Tu Nombre]
- **Empresa:** [Nombre de la Empresa]
- **Fecha de Inicio:** [Fecha]
- **Fecha de Finalización:** [Fecha]
- **Programa de Formación:** [Tu Programa SENA]

### 1.2 Descripción General
Sistema web desarrollado en Python Flask que permite evaluar candidatos para procesos de selección de personal mediante cuestionarios interactivos. El sistema captura datos del candidato, presenta preguntas de múltiples niveles de dificultad, calcula puntuaciones automáticamente y genera reportes para el área de Recursos Humanos. Los resultados se guardan automáticamente en Google Drive para revisión posterior.

### 1.3 Objetivos del Proyecto
- **Objetivo General:** Desarrollar una aplicación web para la evaluación automática de candidatos en procesos de selección de personal
- **Objetivos Específicos:**
  - Capturar datos personales del candidato de forma estructurada (nombre, documento, email)
  - Evaluar conocimientos mediante cuestionarios de múltiples niveles
  - Calcular automáticamente puntuaciones y porcentajes de acierto
  - Generar reportes automáticos para el área de RRHH
  - Integrar sistema de almacenamiento en la nube (Google Drive)
  - Determinar automáticamente si el candidato aprueba o no la evaluación

---

## 2. ANÁLISIS TÉCNICO

### 2.1 Tecnologías Utilizadas
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.x | Lenguaje de programación principal |
| Flask | 3.x | Framework web para backend |
| Pandas | 2.x | Procesamiento de datos Excel |
| Google Drive API | 2.x | Almacenamiento automático de resultados |
| ReportLab | 4.x | Generación de reportes PDF profesionales |
| Pillow | 10.x | Procesamiento de imágenes para PDF |
| HTML5 | - | Estructura de la interfaz web |
| CSS3 | - | Estilos y diseño visual |
| JavaScript | ES6+ | Interactividad frontend |

### 2.2 Arquitectura del Sistema
```
Sistema de Evaluación/
├── app.py                       # Aplicación principal Flask
├── drive_integration.py         # Integración con Google Drive
├── pdf_generator.py            # Generación de reportes PDF profesionales
├── credentials.json            # Credenciales Google Drive (NO subir a git)
├── templates/
│   └── cuestionario.html       # Interfaz de evaluación
├── static/
│   ├── css/
│   │   └── style.css           # Estilos CSS
│   └── js/
│       └── script.js           # Funcionalidades JavaScript
├── reportes_pdf/               # Directorio para reportes PDF generados
├── Evaluación FWS PAN V2.xlsx # Base de datos de preguntas
├── requirements.txt            # Dependencias del proyecto
├── GUIA_GOOGLE_DRIVE.md       # Documentación de configuración Drive
└── GUIA_CONFIGURACION_COMPLETA.md # Guía paso a paso completa
```

### 2.3 Flujo de Evaluación Adaptativa
1. **Registro del Candidato:** Captura de datos personales (nombre, documento, email)
2. **Inicio de Evaluación:** Se registra timestamp de inicio y se inicializa el estado en Nivel 1
3. **Presentación de Preguntas:** Sistema presenta preguntas del nivel actual de dificultad
4. **Evaluación de Respuestas:** Se registra cada respuesta con timestamp y corrección automática
5. **Monitoreo de Progreso:** Sistema cuenta respuestas correctas en el nivel actual
6. **Decisión de Avance:** 
   - **Si alcanza 3 aciertos:** Avanza automáticamente al siguiente nivel de dificultad
   - **Si responde incorrectamente:** Continúa en el mismo nivel (no retrocede)
   - **Si agota preguntas del nivel:** Sistema avanza automáticamente al siguiente nivel disponible
7. **Progresión Adaptativa:** Las preguntas se vuelven más difíciles progresivamente
8. **Finalización Inteligente:** 
   - **Completa todos los niveles:** Candidato demuestra competencia máxima
   - **Tiempo límite:** Sistema finaliza automáticamente (configurable)
   - **Criterio mínimo:** Al alcanzar número mínimo de preguntas evaluadas
9. **Cálculo Final:** Sistema determina nivel máximo alcanzado y porcentaje de acierto
10. **Generación de Reporte:** Se crea automáticamente un reporte PDF profesional con análisis completo
11. **Guardado Automático:** Resultados se guardan automáticamente en Google Drive
12. **Reporte RRHH:** Se genera archivo completo con análisis de competencias por nivel y recomendaciones

---

## 3. DESARROLLO PASO A PASO

### 3.1 Configuración del Entorno
```bash
# Instalación de dependencias
pip install flask pandas openpyxl

# Estructura de directorios
mkdir templates static static/css static/js
```

### 3.2 Desarrollo del Backend (app.py)

#### 3.2.1 Importación de Librerías
```python
from flask import Flask, render_template, request, jsonify
import pandas as pd
```

#### 3.2.2 Función de Carga de Datos
**Propósito:** Leer y procesar el archivo Excel con las preguntas
**Características:**
- Validación de datos completos
- Separación por niveles
- Manejo de errores robusto

#### 3.2.3 Sistema de Rutas
- **`/`** - Página principal
- **`/obtener_pregunta`** - API para obtener preguntas
- **`/responder`** - API para procesar respuestas
- **`/reiniciar`** - API para reiniciar el cuestionario

### 3.3 Desarrollo del Frontend

#### 3.3.1 Estructura HTML
- Layout responsive
- Contenedores para preguntas y opciones
- Botones de navegación dinámicos

#### 3.3.2 Estilos CSS
- Diseño moderno y limpio
- Efectos hover para interactividad
- Código de colores para retroalimentación

#### 3.3.3 JavaScript
- Comunicación AJAX con el backend
- Manejo de estados de la interfaz
- Validación de selecciones

---

## 4. FUNCIONALIDADES IMPLEMENTADAS

### 4.1 Gestión de Preguntas
- **Carga desde Excel:** Lectura automática de preguntas desde archivo Excel
- **Validación de Datos:** Verificación de completitud de preguntas
- **Clasificación por Niveles:** Organización automática según dificultad

### 4.2 Sistema de Progresión Adaptativa
- **Niveles Múltiples de Dificultad:** El sistema presenta preguntas de diferentes niveles (1, 2, 3, 4, 5)
- **Progresión Rápida:** Cuando el candidato responde correctamente **3 preguntas** del mismo nivel, automáticamente avanza al siguiente nivel de dificultad
- **Sin Repetición:** Las preguntas nunca se repiten durante toda la evaluación, garantizando una experiencia única
- **Evaluación Escalonada:** 
  - **Nivel 1:** Preguntas básicas/fundamentales
  - **Nivel 2:** Preguntas intermedias
  - **Nivel 3:** Preguntas avanzadas
  - **Nivel 4:** Preguntas expertas
  - **Nivel 5:** Preguntas de máxima dificultad
- **Adaptabilidad:** El sistema se adapta rápidamente al conocimiento del candidato
- **Finalización Automática:** Si se agotan las preguntas de un nivel, se avanza automáticamente o se finaliza la evaluación
- **Requisito de Avance:** Solo 3 respuestas correctas por nivel para demostrar competencia básica del nivel

### 4.3 Lógica de Evaluación Adaptativa
El sistema implementa un algoritmo eficiente que:
1. **Inicia en Nivel 1:** Todos los candidatos comienzan con preguntas básicas
2. **Monitorea Rendimiento:** Cuenta respuestas correctas por nivel actual
3. **Evalúa Competencia Rápida:** Al alcanzar 3 aciertos, considera competencia suficiente en ese nivel
4. **Avanza Dificultad:** Promociona automáticamente al siguiente nivel disponible
5. **Mantiene Historial:** Registra el nivel máximo alcanzado como indicador de competencia
6. **No Repite Preguntas:** Cada pregunta se presenta solo una vez durante toda la evaluación
7. **Finaliza Inteligentemente:** La evaluación termina cuando se agotan las preguntas disponibles

Este sistema permite:
- **Evaluación Eficiente:** Evaluación rápida sin preguntas repetitivas
- **Identificación Ágil:** Determina rápidamente el nivel de competencia del candidato
- **Experiencia Única:** Cada candidato tiene una experiencia de evaluación diferente
- **Optimización de Tiempo:** Reduce significativamente el tiempo de evaluación

### 4.4 Interfaz de Usuario
- **Diseño Responsive:** Adaptable a diferentes dispositivos
- **Experiencia Neutra:** El candidato no ve puntuación, nivel de dificultad ni retroalimentación de respuestas
- **Navegación Intuitiva:** Botones contextuales simples
- **Evaluación Ciega:** Garantiza evaluación objetiva sin influencia de resultados parciales

### 4.6 Sistema de Reportes PDF
- **Generación Automática:** Crea reportes PDF profesionales al finalizar cada evaluación
- **Formato Empresarial:** Diseño profesional con información estructurada
- **Análisis Completo:** Incluye datos del candidato, resultados por nivel y recomendaciones
- **Archivo Local:** Se guarda en directorio `reportes_pdf/` para fácil acceso
- **Integración con Drive:** Opción de subir también a Google Drive para backup
### 4.7 Sistema de Puntuación y Calificación
- **Evaluación Interna:** 10 puntos por respuesta correcta (no visible para el candidato)
- **Seguimiento Interno:** Sistema registra nivel y puntos internamente
- **Cálculo Automático:** Se calcula automáticamente el porcentaje de acierto para RRHH
- **Criterio de Aprobación:** Mínimo 70% de respuestas correctas para aprobar (evaluado internamente)
- **Nivel Máximo Alcanzado:** Se registra el nivel de dificultad más alto completado (para reporte RRHH)
- **Experiencia Neutra:** El candidato no recibe retroalimentación durante la evaluación

---

## 5. PROBLEMAS ENCONTRADOS Y SOLUCIONES

### 5.1 Problema: Progresión de Preguntas
**Descripción:** Inicialmente el sistema no mostraba botón "Siguiente" después de responder
**Causa:** Falta de envío del ID de pregunta desde frontend
**Solución:** 
- Implementación de variable `preguntaActual` en JavaScript
- Envío de `pregunta_id` en peticiones AJAX

### 5.2 Problema: Botón Responder Desaparecía
**Descripción:** Al pasar a siguiente pregunta no aparecía el botón "Responder"
**Causa:** Manejo incorrecto de visibilidad de elementos DOM
**Solución:**
- Modificación de función `siguientePregunta()`
- Reset correcto del estado de botones

### 5.4 Implementación del Sistema Adaptativo
**Descripción:** El sistema necesitaba adaptar la dificultad de las preguntas según el rendimiento del candidato
**Causa:** Evaluación estática no permite identificar el verdadero nivel de competencia
**Solución:**
- Implementación de algoritmo de progresión por niveles
- Sistema de conteo de respuestas correctas por nivel
- Avance automático al alcanzar 10 aciertos consecutivos
- Registro del nivel máximo alcanzado para el reporte final

### 5.5 Optimización del Criterio de Avance
**Descripción:** Se optimizó el sistema para ser más ágil y eficiente
**Causa:** 10 respuestas correctas por nivel era demasiado extenso para evaluación de candidatos
**Solución:**
- Reducción del requisito a 3 respuestas correctas por nivel
- Eliminación del sistema de reciclaje de preguntas
- Implementación de avance automático cuando se agotan preguntas de un nivel
- Finalización inteligente cuando no hay más preguntas disponibles

### 5.6 Eliminación de Repetición de Preguntas
**Descripción:** Se necesitaba garantizar que cada pregunta se presente solo una vez
**Causa:** La repetición de preguntas reduce la validez de la evaluación
**Solución:**
- Eliminación completa del sistema de reciclaje
- Seguimiento estricto de preguntas ya mostradas
- Avance automático entre niveles cuando se agotan preguntas
- Finalización de evaluación cuando se agotan todas las preguntas disponibles

---

## 6. TESTING Y VALIDACIÓN

### 6.1 Pruebas Funcionales
- ✅ Carga correcta de todas las preguntas desde Excel (sin límites)
- ✅ Navegación entre preguntas sin repetición
- ✅ Cálculo correcto de puntuación (interno, no visible al candidato)
- ✅ Progresión rápida de niveles (3 respuestas correctas, interno)
- ✅ Avance automático al agotar preguntas de un nivel
- ✅ Finalización automática de evaluación
- ✅ Guardado automático en Google Drive
- ✅ Captura de datos del candidato
- ✅ Generación de reportes para RRHH
- ✅ Interfaz neutra sin retroalimentación de respuestas

### 6.2 Pruebas de Interfaz
- ✅ Responsividad en diferentes dispositivos
- ✅ Retroalimentación visual adecuada
- ✅ Usabilidad intuitiva

### 6.3 Pruebas de Rendimiento
- ✅ Carga rápida de preguntas
- ✅ Respuesta inmediata a interacciones
- ✅ Manejo eficiente de memoria

---

## 7. DEPLOYMENT Y CONFIGURACIÓN

### 7.1 Requisitos del Sistema
- Python 3.7 o superior
- 512 MB RAM mínimo
- 100 MB espacio en disco
- Navegador web moderno

### 7.2 Instalación
```bash
# Clonar repositorio
git clone [URL_DEL_REPOSITORIO]

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python app.py
```

### 7.3 Configuración
- Archivo Excel debe estar en directorio raíz
- Puerto por defecto: 5000
- Modo debug habilitado para desarrollo

---

## 8. MANTENIMIENTO Y MEJORAS FUTURAS

### 8.1 Mantenimiento Preventivo
- Backup regular del archivo Excel
- Monitoreo de logs de errores
- Actualización de dependencias

### 8.2 Mejoras Propuestas
- Base de datos SQL para mejor escalabilidad
- Sistema de usuarios y sesiones
- Reportes de resultados
- Modo administrador para gestión de preguntas
- Temporizador por pregunta
- Estadísticas avanzadas

---

## 9. CONCLUSIONES

### 9.1 Objetivos Alcanzados
El proyecto cumplió exitosamente todos los objetivos planteados:
- Sistema funcional de cuestionarios web
- Interfaz intuitiva y responsive
- Integración exitosa con datos Excel
- Sistema de progresión por niveles

### 9.2 Competencias Desarrolladas
- **Programación Backend:** Python, Flask, manejo de APIs
- **Programación Frontend:** HTML, CSS, JavaScript, AJAX
- **Manejo de Datos:** Pandas, procesamiento de Excel
- **Control de Versiones:** Git, GitHub
- **Resolución de Problemas:** Debug, testing, optimización

### 9.3 Aprendizajes Obtenidos
- Importancia de la planificación en desarrollo
- Valor del testing continuo
- Beneficios de la documentación detallada
- Metodologías de desarrollo iterativo

---

## 10. ANEXOS

### 10.1 Código Fuente Principal
[Referencia a archivos del proyecto]

### 10.2 Capturas de Pantalla
[Imágenes de la interfaz funcionando]

### 10.3 Logs de Desarrollo
[Registro cronológico de cambios importantes]

---

**Elaborado por:** [Tu Nombre]  
**Fecha:** [Fecha Actual]  
**Programa SENA:** [Tu Programa]  
**Empresa:** [Nombre Empresa]
