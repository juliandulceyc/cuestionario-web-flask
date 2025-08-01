import pandas as pd
import os

def leer_excel_simple():
    archivo = 'Evaluación FWS PAN V2.xlsx'
    
    if not os.path.exists(archivo):
        print(f"❌ No existe: {archivo}")
        return None
    
    try:
        df = pd.read_excel(archivo)
        columnas = list(df.columns)
        
        print(f"📊 Archivo: {archivo}")
        print(f"📏 Filas: {len(df)} | Columnas: {len(columnas)}")
        print(f"🔤 Columnas detectadas:")
        for i, col in enumerate(columnas, 1):
            print(f"  {i}. '{col}'")
        
        # Detectar mapeo automático
        mapeo = {}
        
        # Buscar pregunta
        for col in columnas:
            if 'pregunta' in col.lower() or 'question' in col.lower():
                mapeo['pregunta'] = col
                break
        
        # Buscar opciones
        opciones = []
        for col in columnas:
            if 'opci' in col.lower() or 'option' in col.lower():
                opciones.append(col)
        mapeo['opciones'] = opciones
        
        # Buscar respuesta
        for col in columnas:
            if 'respuesta' in col.lower() or 'correcta' in col.lower():
                mapeo['respuesta'] = col
                break
        
        # Buscar nivel
        for col in columnas:
            if 'nivel' in col.lower() or 'dificultad' in col.lower():
                mapeo['nivel'] = col
                break
        
        print(f"\n🗺️ Mapeo detectado:")
        for key, value in mapeo.items():
            print(f"  {key}: {value}")
        
        # Generar código para app.py
        codigo = generar_codigo_app(mapeo)
        
        with open('codigo_app_corregido.txt', 'w', encoding='utf-8') as f:
            f.write(codigo)
        
        print(f"\n✅ Código generado en 'codigo_app_corregido.txt'")
        
        return mapeo, df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def generar_codigo_app(mapeo):
    pregunta_col = mapeo.get('pregunta', 'Pregunta')
    respuesta_col = mapeo.get('respuesta', 'Respuesta Correcta')
    nivel_col = mapeo.get('nivel', 'Nivel')
    opciones_cols = mapeo.get('opciones', [])
    
    codigo_opciones = ""
    if opciones_cols:
        for col in opciones_cols[:4]:
            codigo_opciones += f"                opciones.append(str(row['{col}'] or 'Opción'))\n"
    else:
        codigo_opciones = """                for col in ['A', 'B', 'C', 'D']:
                    if col in row.index:
                        opciones.append(str(row[col] or f'Opción {col}'))"""
    
    return f'''def cargar_preguntas():
    global PREGUNTAS
    try:
        df = pd.read_excel('Evaluación FWS PAN V2.xlsx')
        print(f"✅ Excel cargado: {{len(df)}} filas")
        
        PREGUNTAS = []
        for index, row in df.iterrows():
            try:
                pregunta_texto = str(row['{pregunta_col}'] or '').strip()
                if len(pregunta_texto) < 10:
                    continue
                
                opciones = []
{codigo_opciones}
                
                respuesta = str(row['{respuesta_col}'] or 'A').upper().strip()
                
                try:
                    nivel = int(row['{nivel_col}'] or 1)
                except:
                    nivel = 1
                
                respuestas_correctas = [respuesta]
                multiple = False
                if ',' in respuesta or ';' in respuesta:
                    respuestas_correctas = [r.strip() for r in respuesta.replace(';', ',').split(',')]
                    multiple = len(respuestas_correctas) > 1
                
                pregunta = {{
                    "id": len(PREGUNTAS) + 1,
                    "pregunta": pregunta_texto,
                    "opciones": opciones,
                    "respuesta_correcta": respuestas_correctas[0],
                    "respuestas_correctas": respuestas_correctas,
                    "multiple": multiple,
                    "nivel": nivel
                }}
                
                PREGUNTAS.append(pregunta)
                
            except Exception as e:
                print(f"Error fila {{index}}: {{e}}")
        
        print(f"✅ {{len(PREGUNTAS)}} preguntas cargadas")
        
    except Exception as e:
        print(f"❌ Error cargando Excel: {{e}}")
        PREGUNTAS = []

def evaluar_respuesta(pregunta, respuesta_usuario):
    respuestas_correctas = pregunta.get("respuestas_correctas", [pregunta["respuesta_correcta"]])
    multiple = pregunta.get("multiple", False)
    
    if respuesta_usuario.upper() in [r.upper() for r in respuestas_correctas]:
        if multiple and len(respuestas_correctas) > 1:
            return True, 0.5
        else:
            return True, 1.0
    
    return False, 0.0'''

if __name__ == "__main__":
    leer_excel_simple()