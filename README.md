# Cuestionario Web

Aplicación web desarrollada en Flask que lee preguntas desde un archivo Excel y genera un cuestionario interactivo con progresión por niveles.

## Instalación inicial

Para la primera ejecución, instalar las dependencias:

1. Abrir terminal en la carpeta del proyecto
2. Activar el entorno virtual:
   ```cmd
   venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```cmd
   pip install -r requirements.txt
   ```

## Ejecutar aplicación

1. Abrir terminal en la carpeta del proyecto
2. Activar el entorno virtual:
   ```cmd
   venv\Scripts\activate
   ```
3. Ejecutar la aplicación:
   ```cmd
   python app.py
   ```

**Método alternativo (sin activar entorno):**
```cmd
venv\Scripts\python.exe app.py
```

Luego abrir en el navegador: **http://localhost:5000**

## Estructura del proyecto

- `app.py` - Aplicación Flask principal
- `Evaluación FWS PAN V2.xlsx` - Archivo de preguntas de la empresa
- `requirements.txt` - Lista de dependencias Python
- `templates/cuestionario.html` - Plantilla HTML principal
- `static/css/style.css` - Estilos de la interfaz
- `static/js/script.js` - JavaScript para interactividad
- `venv/` - Entorno virtual de Python

## Comandos útiles

**Crear entorno virtual (si no existe):**
```cmd
python -m venv venv
```

**Activar entorno virtual:**
```cmd
venv\Scripts\activate
```

**Desactivar entorno virtual:**
```cmd
deactivate
```

**Instalar nueva dependencia:**
```cmd
pip install nombre_paquete
pip freeze > requirements.txt
```

## Funcionamiento

1. Lee preguntas del Excel según la estructura de columnas establecida
2. Inicia siempre en nivel 1
3. Progresa al siguiente nivel disponible con respuestas correctas
4. Sistema de puntuación: 10 puntos por respuesta correcta
5. Interfaz responsive para desktop y móvil

## Deployment a Producción

### Pasos generales para llevar a producción:

1. **Cambiar configuración de desarrollo:**
   - Cambiar `debug=True` a `debug=False` en app.py
   - Configurar un servidor WSGI como Gunicorn en lugar de Flask dev server

2. **Elegir plataforma de hosting:**
   - **Heroku/Railway/Render**: Fácil deployment, solo subir código
   - **VPS (DigitalOcean/AWS)**: Más control, requiere configuración de servidor
   - **Servidor de la empresa**: Si tienen infraestructura propia

3. **Consideraciones de seguridad:**
   - Configurar HTTPS
   - Proteger el archivo Excel con permisos adecuados
   - Configurar variables de entorno para datos sensibles

4. **Mejoras recomendadas:**
   - Usar base de datos en lugar de estado en memoria
   - Implementar sistema de usuarios
   - Agregar backup del archivo Excel
   - Configurar logging para errores

## Notas técnicas

- El Excel debe tener las columnas: PREGUNTA, A, B, C, D, RESPUESTA CORRECTA 1, NIVEL
- Soporta formatos de nivel como "Nivel 1", "Nivel 3 AO", etc.
- Carga hasta 50 preguntas para mantener performance óptima
- Prioriza preguntas de nivel 1 para asegurar que el usuario pueda empezar

## Mejoras sugeridas para el futuro

- Sistema de usuarios y autenticación
- Guardado de progreso individual
- Estadísticas de desempeño
- Temporizador por pregunta
- Base de datos en lugar de estado en memoria
- Tests automatizados