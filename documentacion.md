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

### 2.4 Estructura Requerida del Archivo Excel para Evaluaciones

Para que el sistema cargue correctamente una prueba, el archivo Excel debe cumplir con la siguiente estructura:

| Columna                | Descripción                                                                                   | Ejemplo                                    |
|------------------------|----------------------------------------------------------------------------------------------|--------------------------------------------|
| NUM                    | Identificador único de la pregunta (numérico, sin repetir)                                   | 101                                        |
| TIPO DE PREGUNTA       | Tipo de pregunta: "Selección Multiple" o "Selección Única"                                   | Selección Multiple                         |
| PREGUNTA               | Texto de la pregunta                                                                         | ¿Qué es un firewall?                       |
| A                      | Opción A                                                                                     | Un dispositivo de red                      |
| B                      | Opción B                                                                                     | Un software de oficina                     |
| C                      | Opción C                                                                                     | Un protocolo de enrutamiento               |
| D                      | Opción D                                                                                     | Un sistema operativo                       |
| RESPUESTA CORRECTA 1   | Letra de la opción correcta principal (A, B, C o D)                                          | A                                          |
| RESPUESTA CORRECTA 2   | (Opcional) Letra de la segunda opción correcta (solo para selección múltiple)                | C                                          |
| IMAGEN                 | (Opcional) Ruta o nombre de imagen asociada                                                  | imagen1.png                                |
| CATEGORIA              | Categoría o área de la pregunta                                                              | Seguridad                                  |
| NIVEL                  | Nivel de dificultad (1, 2, 3, 4, 5) SOLO el número, sin texto adicional                      | 1                                          |

**Notas importantes:**
- El archivo debe tener al menos 20 preguntas por cada nivel (1 a 5) para asegurar variedad y adaptatividad.
- Solo se cargarán preguntas que tengan opciones A y B (y preferiblemente C y D).
- Las preguntas abiertas (sin opciones A-D) no serán tomadas en cuenta.
- El campo NIVEL debe contener solo el número del nivel (ejemplo: 1, 2, 3, 4, 5).
- Las respuestas correctas deben ser letras (A, B, C, D) y coincidir con las opciones dadas.
- Si el archivo tiene menos de 40 preguntas, el sistema presentará todas en orden de nivel, sin adaptatividad.

---

## 2.5 Ejemplo de Archivo Excel Válido

| NUM | TIPO DE PREGUNTA   | PREGUNTA                      | A                    | B                   | C                        | D                  | RESPUESTA CORRECTA 1 | RESPUESTA CORRECTA 2 | IMAGEN | CATEGORIA | NIVEL |
|-----|--------------------|-------------------------------|----------------------|---------------------|--------------------------|--------------------|----------------------|----------------------|--------|-----------|-------|
| 101 | Selección Multiple | ¿Qué es un firewall?          | Dispositivo de red   | Software de oficina | Protocolo de enrutamiento| Sistema operativo  | A                    |                      |        | Seguridad | 1     |
| 102 | Selección Única    | ¿Qué es una IP pública?       | Dirección privada    | Dirección pública   |                          |                    | B                    |                      |        | Redes     | 1     |
| 103 | Selección Multiple | ¿Qué protocolos usa TCP/IP?   | TCP                  | UDP                 | HTTP                     | FTP                | A                    | B                    |        | Redes     | 2     |

---

## 2.6 Lógica Adaptativa y Reglas de Evaluación

- El sistema selecciona 8 preguntas aleatorias por nivel si el Excel tiene al menos 40 preguntas (20 por nivel recomendado).
- El candidato avanza al siguiente nivel si responde al menos 5 de 8 preguntas correctas; nunca regresa a niveles anteriores.
- Si el Excel tiene menos de 40 preguntas, se presentan todas en orden de nivel, sin lógica adaptativa.
- Cada pregunta correcta suma 1 punto; en preguntas múltiples, 1 punto si responde todas bien, 0.5 si responde solo una.
- El nivel final alcanzado se guarda correctamente en la base de datos y en el PDF de resultados.

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

### 7.4 Requerimientos para el Despliegue de la Aplicación

Para que la empresa pueda desplegar y operar el sistema de evaluación, se recomienda lo siguiente:

### Requerimientos Técnicos

- **Plataforma recomendada:**
  - Preferiblemente desplegar en Microsoft Azure (App Service, VM o Container Instance)

- **Servidor o máquina virtual con:**
  - 8 GB de RAM
  - Procesador de 4 núcleos
  - Python 3.8 o superior instalado
  - Sistema operativo Windows 10/11, Linux o macOS
  - Al menos 10 GB de espacio libre en disco
  - Acceso a red local o Internet para los usuarios

- **Dependencias Python:**
  - Flask
  - pandas
  - openpyxl
  - xlrd
  - fpdf2 (para reportes PDF)
  - (Opcional) gunicorn o waitress para despliegue en producción

- **Navegador web moderno** (Chrome, Firefox, Edge)

### Requerimientos de Configuración

- El archivo Excel de preguntas debe estar en la carpeta `/temas` del proyecto y cumplir la estructura indicada.
- Configurar el archivo de tema activo desde el panel de administración.
- Definir el puerto de escucha (por defecto 5000) y asegurarse de que esté libre.
- (Opcional) Configurar backup automático de archivos Excel y reportes PDF.

### Requerimientos de Seguridad y Acceso

- Acceso restringido al panel de administración mediante usuario y contraseña.
- Realizar backups periódicos de la carpeta `/temas` y de los reportes generados.
- Mantener actualizado el entorno Python y las dependencias.

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