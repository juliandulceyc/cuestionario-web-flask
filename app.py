"""
Cuestionario Web - Aplicación Flask
===================================

Aplicación web cuestionario
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime
import json

# Importar integración con Google Drive (opcional)
try:
    from drive_integration import save_session_to_drive
    DRIVE_ENABLED = True
    print("EXITO: Google Drive integration disponible")
except ImportError:
    DRIVE_ENABLED = False
    print("ADVERTENCIA: Google Drive integration no disponible (instala: pip install google-api-python-client)")

# Importar generación de PDF (opcional)
try:
    from pdf_generator import CandidateReportGenerator
    PDF_ENABLED = True
    print("EXITO: Generacion de PDF disponible")
except ImportError:
    PDF_ENABLED = False
    print("ADVERTENCIA: Generacion de PDF no disponible (instala: pip install reportlab)")

app = Flask(__name__)

def cargar_preguntas_desde_excel():
    """
    Carga las preguntas desde el archivo Excel 
    """
    try:
        # Cargar el archivo Excel principal
        print("Cargando preguntas desde Excel...")
        df = pd.read_excel('Evaluación FWS PAN V2.xlsx')
        
        print(f"Excel cargado correctamente: {len(df)} filas, {len(df.columns)} columnas")
        print("Columnas disponibles:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. '{col}'")
        
        # Mostrar algunas filas para verificar la estructura
        print(f"\nPrimeras filas del Excel:")
        for i in range(min(2, len(df))):
            fila = df.iloc[i]
            print(f"\nFila {i+1}:")
            print(f"   PREGUNTA: {fila.get('PREGUNTA', 'NO ENCONTRADA')}")
            print(f"   A: {fila.get('A', 'NO ENCONTRADA')}")
            print(f"   B: {fila.get('B', 'NO ENCONTRADA')}")
            print(f"   RESPUESTA CORRECTA 1: {fila.get('RESPUESTA CORRECTA 1', 'NO ENCONTRADA')}")
            print(f"   NIVEL: {fila.get('NIVEL', 'NO ENCONTRADA')}")
        
        preguntas = []
        
        # buscar preguntas de nivel 1 primero para asegurar que el usuario pueda empezar
        print("Buscando preguntas de nivel 1...")
        preguntas_nivel_1 = []
        
        for i, row in df.iterrows():
            # Verificar que la fila tenga todos los datos necesarios
            if (pd.notna(row['PREGUNTA']) and 
                pd.notna(row['A']) and pd.notna(row['B']) and 
                pd.notna(row['C']) and pd.notna(row['D']) and 
                pd.notna(row['RESPUESTA CORRECTA 1'])):
                
                nivel = extraer_nivel(row['NIVEL'])
                
                # Solo agregar preguntas de nivel 1 en esta primera pasada
                if nivel == 1:
                    pregunta = {
                        "id": i + 1,
                        "nivel": nivel,
                        "pregunta": str(row['PREGUNTA']),    
                        "opciones": [
                            str(row['A']),                          
                            str(row['B']),                          
                            str(row['C']),                          
                            str(row['D'])                           
                        ],
                        "respuesta_correcta": convertir_respuesta(row['RESPUESTA CORRECTA 1'])
                    }
                    
                    # Validar que la pregunta esté completa
                    if (pregunta["pregunta"] and 
                        str(pregunta["pregunta"]).strip() and 
                        str(pregunta["pregunta"]) != 'nan' and
                        pregunta["respuesta_correcta"] is not None):
                        preguntas_nivel_1.append(pregunta)
                        print(f"   Pregunta nivel 1 encontrada: {pregunta['pregunta'][:40]}...")
                        
                        # Cargar todas las preguntas de nivel 1 disponibles
                        # Sin límite artificial
        
        # Agregar las preguntas de nivel 1 al conjunto principal
        preguntas.extend(preguntas_nivel_1)
        print(f"Total preguntas de nivel 1 cargadas: {len(preguntas_nivel_1)}")
        
        # Segunda pasada: agregar preguntas de otros niveles
        print("Cargando preguntas de otros niveles...")
        for i, row in df.iterrows():
            # Cargar TODAS las preguntas disponibles sin límite
                
            if (pd.notna(row['PREGUNTA']) and 
                pd.notna(row['A']) and pd.notna(row['B']) and 
                pd.notna(row['C']) and pd.notna(row['D']) and 
                pd.notna(row['RESPUESTA CORRECTA 1'])):
                
                pregunta = {
                    "id": i + 1,
                    "nivel": extraer_nivel(row['NIVEL']),
                    "pregunta": str(row['PREGUNTA']),    
                    "opciones": [
                        str(row['A']),                          
                        str(row['B']),                          
                        str(row['C']),                          
                        str(row['D'])                           
                    ],
                    "respuesta_correcta": convertir_respuesta(row['RESPUESTA CORRECTA 1'])
                }
                
                # Evitar duplicar preguntas de nivel 1 (ya las agregamos)
                if pregunta["nivel"] != 1:
                    if (pregunta["pregunta"] and 
                        str(pregunta["pregunta"]).strip() and 
                        str(pregunta["pregunta"]) != 'nan' and
                        pregunta["respuesta_correcta"] is not None):
                        preguntas.append(pregunta)
                        print(f"   Pregunta nivel {pregunta['nivel']}: {pregunta['pregunta'][:30]}...")
            
        print(f"Total de preguntas cargadas: {len(preguntas)}")
        return preguntas
        
    except Exception as e:
        print(f"Error al cargar el Excel: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        print("Verificando si el archivo existe...")
        
        import os
        if os.path.exists('Evaluación FWS PAN V2.xlsx'):
            print("El archivo Excel existe en el directorio")
        else:
            print("ERROR: No se encuentra el archivo Excel")
            
        # No continuar sin el Excel - es crítico para la aplicación
        raise Exception(f"No se pudo cargar el Excel: {e}")

def convertir_respuesta(respuesta_excel):
    """
    Convierte la respuesta del Excel al formato interno de la aplicación
    
    El Excel puede tener respuestas como 'A', 'B', 'C', 'D' o '1', '2', '3', '4'
    La aplicación internamente usa índices: 0, 1, 2, 3
    """
    respuesta = str(respuesta_excel).upper().strip()
    
    # Mapeo de respuestas a índices
    if respuesta == 'A' or respuesta == '1':
        return 0
    elif respuesta == 'B' or respuesta == '2':
        return 1
    elif respuesta == 'C' or respuesta == '3':
        return 2
    elif respuesta == 'D' or respuesta == '4':
        return 3
    else:
        print(f"Respuesta no reconocida en Excel: {respuesta_excel}, usando A por defecto")
        return 0

def extraer_nivel(nivel_texto):
    """
    Extrae el número de nivel del texto de la columna NIVEL
    
    El Excel tiene formatos como:
    - "Nivel 1"
    - "Nivel 3 AO" 
    - "Nivel 4 I"
    
    Esta función extrae solo el número para la lógica de progresión
    """
    if pd.isna(nivel_texto):
        return 1
    
    texto = str(nivel_texto).strip()
    
    # Buscar el primer número en el texto
    import re
    numeros = re.findall(r'\d+', texto)
    
    if numeros:
        nivel = int(numeros[0])
        # Asegurar que el nivel esté en rango válido (1-5)
        return min(max(nivel, 1), 5)
    else:
        # Si no encuentra número, asumir nivel 1
        return 1

# Cargar todas las preguntas al iniciar la aplicación
PREGUNTAS = cargar_preguntas_desde_excel()

# Obtener los niveles disponibles para la lógica de progresión
niveles_disponibles = sorted({p["nivel"] for p in PREGUNTAS})

print(f"Niveles disponibles en el Excel: {niveles_disponibles}")
print("La aplicación siempre iniciará en nivel 1")

# Estado global del candidato (en una aplicación real esto estaría en una base de datos)
candidato_actual = {
    "nivel": 1,
    "puntos": 0,
    "preguntas_mostradas": [],  # IDs de preguntas ya mostradas
    "respuestas_correctas_nivel": 0,  # Respuestas correctas en el nivel actual
    "datos_personales": {},  # Información del candidato
    "respuestas_detalladas": [],  # Historial completo de respuestas
    "fecha_inicio": None,
    "fecha_finalizacion": None,
    "evaluacion_completa": False
}

@app.route('/')
def inicio():
    """Página principal - renderiza la interfaz del cuestionario"""
    return render_template('cuestionario.html')

@app.route('/iniciar_evaluacion', methods=['POST'])
def iniciar_evaluacion():
    """
    API endpoint para iniciar la evaluación con datos del candidato
    """
    data = request.get_json()
    
    # Capturar datos del candidato
    candidato_actual["datos_personales"] = {
        "nombre_completo": data.get('nombre_completo', ''),
        "documento": data.get('documento', ''),
        "email": data.get('email', ''),
        "telefono": data.get('telefono', ''),
        "fecha_evaluacion": datetime.now().isoformat()
    }
    
    candidato_actual["fecha_inicio"] = datetime.now().isoformat()
    
    return jsonify({
        "mensaje": "Evaluación iniciada correctamente",
        "candidato": candidato_actual["datos_personales"]["nombre_completo"]
    })

@app.route('/obtener_pregunta')
def obtener_pregunta():
    """
    API endpoint que devuelve una pregunta del nivel actual del usuario
    """
    print(f"Solicitando pregunta de nivel {candidato_actual['nivel']}")
    print(f"Total de preguntas disponibles: {len(PREGUNTAS)}")
    print(f"Preguntas ya mostradas: {candidato_actual['preguntas_mostradas']}")
    
    # Debug: mostrar distribución de preguntas por nivel
    niveles_count = {}
    for p in PREGUNTAS:
        nivel = p["nivel"]
        niveles_count[nivel] = niveles_count.get(nivel, 0) + 1
    
    print(f"Distribución de preguntas: {niveles_count}")
    
    # Buscar preguntas del nivel actual que NO hayan sido mostradas
    preguntas_disponibles = [
        p for p in PREGUNTAS 
        if p["nivel"] == candidato_actual["nivel"] and p["id"] not in candidato_actual["preguntas_mostradas"]
    ]
    
    # Si no hay más preguntas disponibles en este nivel, finalizar evaluación
    if not preguntas_disponibles:
        print(f"Se agotaron las preguntas del nivel {candidato_actual['nivel']}")
        
        # Buscar si hay niveles superiores con preguntas disponibles
        niveles_superiores = [n for n in niveles_disponibles if n > candidato_actual["nivel"]]
        
        if niveles_superiores:
            # Avanzar al siguiente nivel disponible
            siguiente_nivel = min(niveles_superiores)
            candidato_actual["nivel"] = siguiente_nivel
            candidato_actual["respuestas_correctas_nivel"] = 0
            
            # Buscar preguntas del nuevo nivel
            preguntas_disponibles = [
                p for p in PREGUNTAS 
                if p["nivel"] == candidato_actual["nivel"] and p["id"] not in candidato_actual["preguntas_mostradas"]
            ]
            
        if not preguntas_disponibles:
            # No hay más preguntas en ningún nivel
            candidato_actual["evaluacion_completa"] = True
            candidato_actual["fecha_finalizacion"] = datetime.now().isoformat()
            guardar_evaluacion_automatica()
            return jsonify({"error": "Evaluación completada - No hay más preguntas disponibles"})
    
    # Tomar la primera pregunta disponible
    pregunta = preguntas_disponibles[0]
    
    # Marcar esta pregunta como mostrada
    candidato_actual["preguntas_mostradas"].append(pregunta["id"])
    
    print(f"Pregunta encontrada: {pregunta['pregunta'][:50]}...")
    
    # Devolver la pregunta en formato JSON
    return jsonify({
        "id": pregunta["id"],
        "pregunta": pregunta["pregunta"],
        "opciones": pregunta["opciones"],
        "nivel": pregunta["nivel"],
        "puntos": candidato_actual["puntos"]
    })

@app.route('/responder', methods=['POST'])
def responder():
    """
    API endpoint que procesa la respuesta del usuario
    Calcula puntos, determina si avanza de nivel, y devuelve retroalimentación
    """
    data = request.get_json()
    respuesta_usuario = int(data.get('respuesta'))
    pregunta_id = data.get('pregunta_id')  # Obtener ID de la pregunta actual
    
    # Encontrar la pregunta específica por ID
    pregunta = None
    for p in PREGUNTAS:
        if p["id"] == pregunta_id:
            pregunta = p
            break
    
    if not pregunta:
        return jsonify({"error": "Pregunta no encontrada"})
    
    # Evaluar la respuesta
    es_correcta = respuesta_usuario == pregunta["respuesta_correcta"]
    
    if es_correcta:
        # Otorgar puntos por respuesta correcta
        candidato_actual["puntos"] += 10
        candidato_actual["respuestas_correctas_nivel"] += 1
        
        # Avanzar de nivel después de 3 respuestas correctas en el mismo nivel
        if candidato_actual["respuestas_correctas_nivel"] >= 3:
            # Buscar el siguiente nivel disponible
            siguiente_nivel = None
            for nivel in niveles_disponibles:
                if nivel > candidato_actual["nivel"]:
                    siguiente_nivel = nivel
                    break
            
            if siguiente_nivel:
                candidato_actual["nivel"] = siguiente_nivel
                candidato_actual["respuestas_correctas_nivel"] = 0  # Resetear contador
                mensaje = f"¡Excelente! Completaste el nivel {candidato_actual['nivel']-1}. ¡Avanzaste al nivel {siguiente_nivel}!"
            else:
                mensaje = "¡Perfecto! Has completado todos los niveles disponibles."
                candidato_actual["evaluacion_completa"] = True
                candidato_actual["fecha_finalizacion"] = datetime.now().isoformat()
                # Guardar automáticamente al completar
                guardar_evaluacion_automatica()
        else:
            # Mensaje para seguir en el mismo nivel
            restantes = 3 - candidato_actual["respuestas_correctas_nivel"]
            mensaje = f"¡Correcto! Te faltan {restantes} respuestas correctas para avanzar al siguiente nivel."
    else:
        # Respuesta incorrecta - no reiniciar contador, solo mostrar respuesta correcta
        mensaje = f"Incorrecto. La respuesta correcta era: {pregunta['opciones'][pregunta['respuesta_correcta']]}"
    
    # Guardar detalle de la respuesta para el reporte
    candidato_actual["respuestas_detalladas"].append({
        "pregunta_id": pregunta["id"],
        "pregunta_texto": pregunta["pregunta"],
        "nivel": pregunta["nivel"],
        "respuesta_candidato": respuesta_usuario,
        "respuesta_correcta": pregunta["respuesta_correcta"],
        "es_correcta": es_correcta,
        "timestamp": datetime.now().isoformat()
    })
    
    # Verificar si hay más preguntas en el nivel actual (excluyendo las ya mostradas)
    preguntas_disponibles = [
        p for p in PREGUNTAS 
        if p["nivel"] == candidato_actual["nivel"] and p["id"] not in candidato_actual["preguntas_mostradas"]
    ]
    hay_mas_preguntas = len(preguntas_disponibles) > 0
    
    return jsonify({
        "correcto": es_correcta,
        "mensaje": mensaje,
        "puntos": candidato_actual["puntos"],
        "nivel_actual": candidato_actual["nivel"],
        "hay_mas": hay_mas_preguntas,
        "respuesta_correcta": pregunta["opciones"][pregunta["respuesta_correcta"]],
        "respuestas_correctas_nivel": candidato_actual["respuestas_correctas_nivel"],
        "evaluacion_completa": candidato_actual.get("evaluacion_completa", False)
    })

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    """
    API endpoint para reiniciar la evaluación
    Vuelve al nivel 1 y resetea los puntos
    """
    candidato_actual["nivel"] = 1
    candidato_actual["puntos"] = 0
    candidato_actual["preguntas_mostradas"] = []
    candidato_actual["respuestas_correctas_nivel"] = 0
    candidato_actual["respuestas_detalladas"] = []
    candidato_actual["evaluacion_completa"] = False
    candidato_actual["fecha_inicio"] = datetime.now().isoformat()
    candidato_actual["fecha_finalizacion"] = None
    return jsonify({"mensaje": "Evaluación reiniciada"})

def guardar_evaluacion_automatica():
    """
    Guarda automáticamente la evaluación cuando se completa
    """
    if DRIVE_ENABLED:
        try:
            # Calcular estadísticas finales
            total_preguntas = len(candidato_actual["respuestas_detalladas"])
            respuestas_correctas = sum(1 for r in candidato_actual["respuestas_detalladas"] if r["es_correcta"])
            porcentaje_acierto = (respuestas_correctas / total_preguntas * 100) if total_preguntas > 0 else 0
            
            # Determinar si aprueba (ejemplo: 70% mínimo)
            aprueba = porcentaje_acierto >= 70
            
            datos_evaluacion = {
                "candidato": candidato_actual["datos_personales"],
                "resultados": {
                    "puntos_totales": candidato_actual["puntos"],
                    "nivel_alcanzado": candidato_actual["nivel"],
                    "total_preguntas": total_preguntas,
                    "respuestas_correctas": respuestas_correctas,
                    "porcentaje_acierto": round(porcentaje_acierto, 2),
                    "aprueba": aprueba,
                    "fecha_inicio": candidato_actual["fecha_inicio"],
                    "fecha_finalizacion": candidato_actual["fecha_finalizacion"]
                },
                "respuestas_detalladas": candidato_actual["respuestas_detalladas"],
                "evaluacion_completada": True
            }
            
            result = save_session_to_drive(datos_evaluacion, [])
            print(f"EXITO: Evaluacion guardada automaticamente: {result}")
            
        except Exception as e:
            print(f"ERROR: Error guardando evaluacion automatica: {e}")

@app.route('/guardar_en_drive', methods=['POST'])
def guardar_en_drive():
    """
    API endpoint para guardar manualmente los resultados en Google Drive
    """
    if not DRIVE_ENABLED:
        return jsonify({
            "error": "Google Drive no está configurado",
            "mensaje": "Instala las dependencias: pip install google-api-python-client"
        })
    
    try:
        # Preparar datos de la sesión
        preguntas_respondidas = []
        for pregunta_id in candidato_actual["preguntas_mostradas"]:
            # Buscar la pregunta por ID
            for p in PREGUNTAS:
                if p["id"] == pregunta_id:
                    preguntas_respondidas.append({
                        "id": p["id"],
                        "pregunta": p["pregunta"],
                        "nivel": p["nivel"],
                        "fecha_respuesta": datetime.now().isoformat()
                    })
                    break
        
        # Guardar en Drive
        result = save_session_to_drive(candidato_actual, preguntas_respondidas)
        
        print(f"DEBUG: Resultado de save_session_to_drive: {result}")
        
        if result and result.get('success'):
            return jsonify({
                "mensaje": "Datos guardados exitosamente en Google Drive",
                "archivo": result.get('file_name'),
                "link": result.get('link')
            })
        else:
            error_msg = result.get('error', 'Error desconocido') if result else 'No se pudo conectar a Google Drive'
            print(f"ERROR: Error guardando en Drive: {error_msg}")
            return jsonify({
                "error": "Error guardando en Google Drive",
                "detalle": error_msg
            })
            
    except Exception as e:
        return jsonify({
            "error": "Error interno",
            "detalle": str(e)
        })

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    """
    API endpoint para generar reporte PDF del candidato y subirlo a Google Drive
    """
    if not PDF_ENABLED:
        return jsonify({
            "error": "Generación de PDF no está disponible",
            "mensaje": "Instala las dependencias: pip install reportlab Pillow"
        })
    
    try:
        # Verificar que hay datos del candidato
        if not candidato_actual.get("datos_personales"):
            return jsonify({
                "error": "No hay datos de candidato para generar reporte"
            })
        
        # Generar el reporte PDF
        generator = CandidateReportGenerator()
        pdf_path = generator.generate_candidate_report(candidato_actual)
        
        resultado = {
            "mensaje": "Reporte PDF generado exitosamente",
            "archivo": pdf_path,
            "ruta_completa": pdf_path
        }
        
        # Intentar subir el PDF a Google Drive si está disponible
        if DRIVE_ENABLED:
            try:
                from drive_integration import GoogleDriveManager
                drive_manager = GoogleDriveManager()
                
                if drive_manager.service:
                    # Subir PDF a Google Drive
                    folder_id = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"  # Tu carpeta de resultados
                    
                    # Metadatos del PDF
                    from googleapiclient.http import MediaFileUpload
                    import os
                    
                    filename = os.path.basename(pdf_path)
                    file_metadata = {
                        'name': filename,
                        'parents': [folder_id]
                    }
                    
                    media = MediaFileUpload(pdf_path, mimetype='application/pdf')
                    
                    pdf_file = drive_manager.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id,name,webViewLink'
                    ).execute()
                    
                    resultado.update({
                        "drive_guardado": True,
                        "drive_file_id": pdf_file.get('id'),
                        "drive_link": pdf_file.get('webViewLink'),
                        "mensaje": "Reporte PDF generado y guardado en Google Drive"
                    })
                else:
                    resultado["drive_guardado"] = False
                    resultado["drive_error"] = "No se pudo conectar a Google Drive"
                    
            except Exception as drive_error:
                resultado["drive_guardado"] = False
                resultado["drive_error"] = f"Error subiendo a Drive: {str(drive_error)}"
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            "error": "Error generando PDF",
            "detalle": str(e)
        })

if __name__ == '__main__':
    print("Iniciando Cuestionario Web")
    print(f"Preguntas cargadas: {len(PREGUNTAS)}")
    for i, p in enumerate(PREGUNTAS):
        print(f"   {i+1}. Nivel {p['nivel']}: {p['pregunta'][:50]}...")
    app.run(debug=True)
