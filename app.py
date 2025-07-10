"""
Cuestionario Web - Aplicación Flask
===================================

Aplicación web que lee preguntas desde un archivo Excel y 
crea un cuestionario interactivo con progresión por niveles.

Desarrollado para la empresa - 2025
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

def cargar_preguntas_desde_excel():
    """
    Carga las preguntas desde el archivo Excel de la empresa
    
    Parámetros a ajustar:
    - Nombre del archivo Excel
    - Mapeo de columnas según estructura del Excel
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
        
        # Estrategia: buscar preguntas de nivel 1 primero para asegurar que el usuario pueda empezar
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
                        
                        # Limitar a 10 preguntas de nivel 1 para no sobrecargar
                        if len(preguntas_nivel_1) >= 10:
                            break
        
        # Agregar las preguntas de nivel 1 al conjunto principal
        preguntas.extend(preguntas_nivel_1)
        print(f"Total preguntas de nivel 1 cargadas: {len(preguntas_nivel_1)}")
        
        # Segunda pasada: agregar preguntas de otros niveles
        print("Cargando preguntas de otros niveles...")
        for i, row in df.iterrows():
            # Límite total de preguntas para mantener la aplicación ágil
            if len(preguntas) >= 50:
                break
                
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

# Estado global del usuario (en una aplicación real esto estaría en una base de datos o sesión)
usuario_actual = {
    "nivel": 1,
    "puntos": 0
}

@app.route('/')
def inicio():
    """Página principal - renderiza la interfaz del cuestionario"""
    return render_template('cuestionario.html')

@app.route('/obtener_pregunta')
def obtener_pregunta():
    """
    API endpoint que devuelve una pregunta del nivel actual del usuario
    """
    print(f"Solicitando pregunta de nivel {usuario_actual['nivel']}")
    print(f"Total de preguntas disponibles: {len(PREGUNTAS)}")
    
    # Debug: mostrar distribución de preguntas por nivel
    niveles_count = {}
    for p in PREGUNTAS:
        nivel = p["nivel"]
        niveles_count[nivel] = niveles_count.get(nivel, 0) + 1
    
    print(f"Distribución de preguntas: {niveles_count}")
    
    # Buscar una pregunta del nivel actual
    pregunta = None
    for p in PREGUNTAS:
        if p["nivel"] == usuario_actual["nivel"]:
            pregunta = p
            print(f"Pregunta encontrada: {p['pregunta'][:50]}...")
            break
    
    if not pregunta:
        print(f"No hay preguntas disponibles para nivel {usuario_actual['nivel']}")
        return jsonify({"error": "No hay más preguntas disponibles"})
    
    # Devolver la pregunta en formato JSON
    return jsonify({
        "id": pregunta["id"],
        "pregunta": pregunta["pregunta"],
        "opciones": pregunta["opciones"],
        "nivel": pregunta["nivel"],
        "puntos": usuario_actual["puntos"]
    })

@app.route('/responder', methods=['POST'])
def responder():
    """
    API endpoint que procesa la respuesta del usuario
    Calcula puntos, determina si avanza de nivel, y devuelve retroalimentación
    """
    data = request.get_json()
    respuesta_usuario = int(data.get('respuesta'))
    
    # Encontrar la pregunta actual
    pregunta = None
    for p in PREGUNTAS:
        if p["nivel"] == usuario_actual["nivel"]:
            pregunta = p
            break
    
    if not pregunta:
        return jsonify({"error": "Pregunta no encontrada"})
    
    # Evaluar la respuesta
    es_correcta = respuesta_usuario == pregunta["respuesta_correcta"]
    
    if es_correcta:
        # Otorgar puntos por respuesta correcta
        usuario_actual["puntos"] += 10
        
        # Lógica de progresión: buscar el siguiente nivel disponible
        siguiente_nivel = None
        for nivel in niveles_disponibles:
            if nivel > usuario_actual["nivel"]:
                siguiente_nivel = nivel
                break
        
        if siguiente_nivel:
            usuario_actual["nivel"] = siguiente_nivel
            mensaje = f"¡Correcto! Avanzaste al nivel {siguiente_nivel}."
        else:
            mensaje = "¡Correcto! Has completado todos los niveles disponibles."
    else:
        # Mostrar la respuesta correcta cuando se equivoque
        mensaje = f"Incorrecto. La respuesta correcta era: {pregunta['opciones'][pregunta['respuesta_correcta']]}"
    
    # Verificar si hay más preguntas en el nivel actual
    hay_mas_preguntas = any(p["nivel"] == usuario_actual["nivel"] for p in PREGUNTAS)
    
    return jsonify({
        "correcto": es_correcta,
        "mensaje": mensaje,
        "puntos": usuario_actual["puntos"],
        "nivel_actual": usuario_actual["nivel"],
        "hay_mas": hay_mas_preguntas,
        "respuesta_correcta": pregunta["opciones"][pregunta["respuesta_correcta"]]
    })

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    """
    API endpoint para reiniciar el cuestionario
    Vuelve al nivel 1 y resetea los puntos
    """
    usuario_actual["nivel"] = 1
    usuario_actual["puntos"] = 0
    return jsonify({"mensaje": "Cuestionario reiniciado"})

if __name__ == '__main__':
    print("Iniciando Cuestionario Web")
    print(f"Preguntas cargadas: {len(PREGUNTAS)}")
    for i, p in enumerate(PREGUNTAS):
        print(f"   {i+1}. Nivel {p['nivel']}: {p['pregunta'][:50]}...")
    app.run(debug=True)
