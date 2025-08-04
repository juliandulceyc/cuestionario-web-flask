from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import random
import json
from datetime import datetime
import os
import base64 
import re

app = Flask(__name__)

# Variables globales
candidatos_registrados = {}
candidato_actual = {}
NIVELES = [1, 2, 3, 4, 5]
PREGUNTAS = []
TOTAL_PREGUNTAS = 2 # Ajuste de numero de preguntas 

def get_total_preguntas():
    """Función global para obtener el total de preguntas desde cualquier parte"""
    return TOTAL_PREGUNTAS

def get_configuracion_evaluacion():
    """Configuración completa de la evaluación basada en TOTAL_PREGUNTAS"""
    total = TOTAL_PREGUNTAS
    
    # Calcular distribución automática
    if total <= 3:
        # Evaluaciones muy cortas
        preguntas_nivel_1 = total
        min_correctas_avance = max(1, total - 1)  # Todas menos 1
    elif total <= 6:
        # Evaluaciones cortas
        preguntas_nivel_1 = 3
        min_correctas_avance = 2
    elif total <= 15:
        # Evaluaciones normales
        preguntas_nivel_1 = 3
        min_correctas_avance = 2
    else:
        # Evaluaciones largas
        preguntas_nivel_1 = 5
        min_correctas_avance = 3
    
    return {
        "total_preguntas": total,
        "preguntas_nivel_1": preguntas_nivel_1,
        "min_correctas_avance": min_correctas_avance,
        "niveles_maximos": 5,
        "puntos_por_nivel": True
    }

try:
    from PIL import Image
    import io
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️ Pillow no disponible - funcionalidad de imagen limitada")

#  FUNCIÓN PARA PROCESAR IMÁGENES 
def procesar_imagen_excel(imagen_raw):
    """Procesa diferentes tipos de imagen del Excel - VERSIÓN MEJORADA PARA EMBEBIDAS"""
    if imagen_raw is None or str(imagen_raw).strip() in ['nan', 'NaN', '', None, 'None']:
        return None
    
    try:
        # ✅ CASO ESPECIAL 1: Imagen embebida de openpyxl
        if hasattr(imagen_raw, '__class__'):
            class_name = str(type(imagen_raw).__name__)
            if 'Image' in class_name or 'Picture' in class_name:
                print(f"🖼️ Imagen embebida detectada: {class_name}")
                try:
                    # Extraer datos binarios según el tipo
                    img_data = None
                    
                    # Para objetos de openpyxl
                    if hasattr(imagen_raw, '_data'):
                        img_data = imagen_raw._data()
                        print(f"📸 Datos extraídos con _data(): {len(img_data)} bytes")
                    elif hasattr(imagen_raw, 'data'):
                        img_data = imagen_raw.data
                        print(f"📸 Datos extraídos con .data: {len(img_data)} bytes")
                    elif hasattr(imagen_raw, 'image'):
                        img_data = imagen_raw.image
                        print(f"📸 Datos extraídos con .image: {len(img_data)} bytes")
                    elif hasattr(imagen_raw, 'blob'):
                        img_data = imagen_raw.blob
                        print(f"📸 Datos extraídos con .blob: {len(img_data)} bytes")
                    
                    if img_data and len(img_data) > 0:
                        imagen_base64 = base64.b64encode(img_data).decode()
                        
                        # Detectar tipo de imagen por magic bytes
                        if img_data.startswith(b'\x89PNG'):
                            mime_type = 'png'
                        elif img_data.startswith(b'\xFF\xD8\xFF'):
                            mime_type = 'jpeg'
                        elif img_data.startswith(b'GIF8'):
                            mime_type = 'gif'
                        elif img_data.startswith(b'BM'):
                            mime_type = 'bmp'
                        else:
                            mime_type = 'png'  # Default
                        
                        result = f"data:image/{mime_type};base64,{imagen_base64}"
                        print(f"✅ Imagen embebida procesada: {mime_type} ({len(imagen_base64)} chars)")
                        return result
                    else:
                        print(f"⚠️ No se pudieron extraer datos de la imagen embebida")
                        return None
                        
                except Exception as e:
                    print(f"⚠️ Error procesando imagen embebida: {e}")
                    return None
        
        # ✅ CASO 2: Datos binarios directos (bytes)
        if isinstance(imagen_raw, bytes):
            try:
                if len(imagen_raw) > 100:  # Validar que tenga contenido suficiente
                    imagen_base64 = base64.b64encode(imagen_raw).decode()
                    
                    # Detectar tipo por magic bytes
                    if imagen_raw.startswith(b'\x89PNG'):
                        mime_type = 'png'
                    elif imagen_raw.startswith(b'\xFF\xD8\xFF'):
                        mime_type = 'jpeg'
                    elif imagen_raw.startswith(b'GIF8'):
                        mime_type = 'gif'
                    else:
                        mime_type = 'png'
                    
                    print(f"✅ Bytes procesados: {mime_type} ({len(imagen_base64)} chars)")
                    return f"data:image/{mime_type};base64,{imagen_base64}"
                else:
                    print(f"⚠️ Datos binarios muy pequeños: {len(imagen_raw)} bytes")
                    return None
            except Exception as e:
                print(f"⚠️ Error procesando bytes: {e}")
                return None
        
        # ✅ CASO 3: String con datos
        imagen_str = str(imagen_raw).strip()
        
        # URL completa con data:image
        if imagen_str.startswith('data:image'):
            print(f"✅ Data URL encontrada")
            return imagen_str
        
        # URL externa
        if imagen_str.startswith(('http://', 'https://')):
            print(f"✅ URL externa encontrada")
            return imagen_str
        
        # Path de archivo local
        if os.path.exists(imagen_str):
            try:
                ext = os.path.splitext(imagen_str)[1].lower()
                mime_type = {
                    '.jpg': 'jpeg', '.jpeg': 'jpeg',
                    '.png': 'png', '.gif': 'gif',
                    '.bmp': 'bmp', '.webp': 'webp'
                }.get(ext, 'jpeg')
                
                with open(imagen_str, "rb") as img_file:
                    img_data = img_file.read()
                    imagen_base64 = base64.b64encode(img_data).decode()
                    print(f"✅ Archivo local procesado: {mime_type}")
                    return f"data:image/{mime_type};base64,{imagen_base64}"
            except Exception as e:
                print(f"⚠️ Error leyendo archivo {imagen_str}: {e}")
                return None
        
        # String base64 sin prefijo
        if len(imagen_str) > 100:
            try:
                # Intentar decodificar para verificar si es base64
                base64.b64decode(imagen_str[:100])
                print(f"✅ Base64 sin prefijo detectado")
                return f"data:image/png;base64,{imagen_str}"
            except:
                print(f"⚠️ String largo pero no es base64 válido")
                return None
        
        print(f"⚠️ Formato no reconocido: {type(imagen_raw)} - Contenido: {str(imagen_raw)[:50]}...")
        return None
        
    except Exception as e:
        print(f"⚠️ Error general procesando imagen: {e}")
        import traceback
        traceback.print_exc()
        return None

def cargar_preguntas():
    """Carga preguntas con soporte mejorado para imágenes embebidas"""
    global PREGUNTAS
    try:
        archivo_excel = 'Evaluación FWS PAN V2.xlsx'
        print(f"🔍 Buscando archivo: {archivo_excel}")
        
        if os.path.exists(archivo_excel):
            print(f"✅ Archivo encontrado, cargando...")
            
            # Cargar con pandas
            df = pd.read_excel(archivo_excel)
            print(f"📊 Excel cargado: {len(df)} filas")
            
            PREGUNTAS.clear()
            preguntas_cargadas = 0
            
            for index, row in df.iterrows():
                try:
                    # ✅ CONVERTIR NIVEL DE TEXTO A NÚMERO
                    nivel_raw = str(row.get('NIVEL', '')).strip()
                    
                    # Extraer número del texto "Nivel X"
                    if 'Nivel 1' in nivel_raw:
                        nivel_numerico = 1
                    elif 'Nivel 2' in nivel_raw:
                        nivel_numerico = 2
                    elif 'Nivel 3' in nivel_raw:
                        nivel_numerico = 3
                    elif 'Nivel 4' in nivel_raw:
                        nivel_numerico = 4
                    elif 'Nivel 5' in nivel_raw:
                        nivel_numerico = 5
                    else:
                        print(f"⚠️ Fila {index+2}: Nivel desconocido '{nivel_raw}', asignando nivel 1")
                        nivel_numerico = 1
                    
                    pregunta_text = str(row.get('PREGUNTA', '')).strip()
                    if not pregunta_text or pregunta_text == 'nan':
                        continue
                    
                    # ✅ PROCESAR OPCIONES - VERSIÓN CORREGIDA CON LIMPIEZA
                    opciones = []
                    respuesta_correcta_texto = None
                    respuesta_letra_excel = str(row.get('RESPUESTA', '')).strip().upper()

                    # Opciones A, B, C, D
                    for letra in ['A', 'B', 'C', 'D']:
                        opcion = str(row.get(letra, '')).strip()
                        if opcion and opcion != 'nan':
                            opciones.append(opcion)
                    
                    # ✅ LIMPIAR OPCIONES DE ESPACIOS Y CARACTERES RAROS
                    opciones_limpias = []
                    for opcion in opciones:
                        opcion_limpia = opcion.strip().replace('\r', '').replace('\n', '').replace('\t', ' ')
                        # Normalizar espacios múltiples
                        opcion_limpia = re.sub(r'\s+', ' ', opcion_limpia).strip()
                        opciones_limpias.append(opcion_limpia)
                    
                    opciones = opciones_limpias
                    
                    # ✅ ENCONTRAR RESPUESTA CORRECTA CON OPCIONES LIMPIAS
                    if respuesta_letra_excel in ['A', 'B', 'C', 'D']:
                        indice_correcto = ord(respuesta_letra_excel) - ord('A')  # A=0, B=1, C=2, D=3
                        if 0 <= indice_correcto < len(opciones):
                            respuesta_correcta_texto = opciones[indice_correcto]
                            print(f"✅ Respuesta correcta: {respuesta_letra_excel} = '{respuesta_correcta_texto}'")
                        else:
                            print(f"⚠️ Índice fuera de rango: {respuesta_letra_excel} para {len(opciones)} opciones")
                            respuesta_correcta_texto = opciones[0] if opciones else None
                    else:
                        print(f"⚠️ Respuesta inválida en Excel: '{respuesta_letra_excel}', usando primera opción")
                        respuesta_correcta_texto = opciones[0] if opciones else None

                    # ✅ DEBUG ESPECÍFICO PARA FIREWALL
                    if "firewall" in pregunta_text.lower():
                        print(f"\n🔥 DEBUG PREGUNTA FIREWALL:")
                        print(f"   Pregunta: {pregunta_text}")
                        print(f"   Respuesta letra Excel: '{respuesta_letra_excel}'")
                        print(f"   Opciones cargadas: {opciones}")
                        print(f"   Índice calculado: {ord(respuesta_letra_excel) - ord('A') if respuesta_letra_excel in ['A','B','C','D'] else 'INVÁLIDO'}")
                        print(f"   Respuesta correcta asignada: '{respuesta_correcta_texto}'")
                        print(f"   ¿Índice en rango?: {0 <= (ord(respuesta_letra_excel) - ord('A')) < len(opciones) if respuesta_letra_excel in ['A','B','C','D'] else False}")

                    if len(opciones) < 2:
                        print(f"⚠️ Muy pocas opciones ({len(opciones)}), saltando pregunta")
                        continue
                    
                    # Procesar imagen
                    imagen_procesada = procesar_imagen_excel(row.get('IMAGEN'))
                    
                    pregunta_obj = {
                        "id": len(PREGUNTAS) + 1,
                        "pregunta": pregunta_text,
                        "opciones": opciones,
                        "respuesta_correcta": respuesta_correcta_texto,  # ← TEXTO LIMPIO, no letra
                        "respuestas_correctas": [respuesta_correcta_texto] if respuesta_correcta_texto else [opciones[0]],
                        "nivel": nivel_numerico,
                        "multiple": False,  # Por ahora solo respuestas simples
                        "imagen": imagen_procesada,
                        "categoria": str(row.get('CATEGORIA', '')).strip()
                    }
                    
                    PREGUNTAS.append(pregunta_obj)
                    preguntas_cargadas += 1
                    
                    # Debug cada 50 preguntas
                    if preguntas_cargadas % 50 == 0:
                        print(f"   📝 Cargadas {preguntas_cargadas} preguntas...")
                
                except Exception as e:
                    print(f"❌ Error procesando fila {index+2}: {e}")
                    continue
            
            # ✅ MOSTRAR ESTADÍSTICAS POR NIVEL NUMÉRICO
            niveles_conteo = {}
            for p in PREGUNTAS:
                nivel = p["nivel"]
                if nivel not in niveles_conteo:
                    niveles_conteo[nivel] = 0
                niveles_conteo[nivel] += 1
            
            print(f"\n📊 RESUMEN FINAL:")
            print(f"   ✅ Preguntas cargadas: {len(PREGUNTAS)}")
            print(f"   📊 Distribución por nivel:")
            for nivel in sorted(niveles_conteo.keys()):
                print(f"      Nivel {nivel}: {niveles_conteo[nivel]} preguntas")
            
            # Verificar que hay preguntas de nivel 1
            if 1 in niveles_conteo and niveles_conteo[1] > 0:
                print(f"   ✅ Preguntas de nivel 1 disponibles: {niveles_conteo[1]}")
            else:
                print(f"   ❌ NO hay preguntas de nivel 1")
            
            return True
            
        else:
            print(f"❌ Archivo no encontrado: {archivo_excel}")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando preguntas: {e}")
        import traceback
        traceback.print_exc()
        return False

# Cargar preguntas al iniciar - VERSIÓN DEFINITIVA
print("🔄 Iniciando sistema de evaluación...")
print("=" * 50)
cargar_preguntas()
print("=" * 50)

if len(PREGUNTAS) > 0:
    print(f"✅ Sistema listo - {len(PREGUNTAS)} preguntas cargadas")
else:
    print(f"❌ Sistema no funcionará - 0 preguntas cargadas")
    print(f"🔧 Verificar archivo 'Evaluación FWS PAN V2.xlsx'")

# ✅ FUNCIÓN PARA EVALUAR RESPUESTAS - VERSIÓN MEJORADA CON LIMPIEZA
def evaluar_respuesta(pregunta, respuesta_usuario):
    """Evalúa si la respuesta del usuario es correcta - VERSIÓN MEJORADA"""
    try:
        respuesta_correcta = pregunta.get("respuesta_correcta")
        opciones = pregunta.get("opciones", [])
        nivel = pregunta.get("nivel", 1)
        
        print(f"🔍 DEBUG EVALUACIÓN:")
        print(f"   Pregunta: {pregunta['pregunta'][:50]}...")
        print(f"   Respuesta correcta: '{respuesta_correcta}'")
        print(f"   Respuesta usuario: '{respuesta_usuario}'")
        print(f"   Opciones: {opciones}")
        
        # ✅ LIMPIAR AMBAS RESPUESTAS PARA COMPARACIÓN
        if respuesta_usuario and respuesta_correcta:
            # Limpiar respuesta del usuario
            respuesta_usuario_limpia = respuesta_usuario.strip().replace('\r', '').replace('\n', '').replace('\t', ' ')
            respuesta_usuario_limpia = re.sub(r'\s+', ' ', respuesta_usuario_limpia).strip()
            
            # Limpiar respuesta correcta
            respuesta_correcta_limpia = respuesta_correcta.strip().replace('\r', '').replace('\n', '').replace('\t', ' ')
            respuesta_correcta_limpia = re.sub(r'\s+', ' ', respuesta_correcta_limpia).strip()
            
            print(f"   Comparación limpia:")
            print(f"      Usuario limpio: '{respuesta_usuario_limpia}'")
            print(f"      Correcta limpia: '{respuesta_correcta_limpia}'")
            
            # ✅ COMPARAR VERSIONES LIMPIAS (case-insensitive)
            if respuesta_usuario_limpia.lower() == respuesta_correcta_limpia.lower():
                puntos = 1.0 * nivel
                print(f"   ✅ CORRECTA - Puntos: {puntos}")
                return True, puntos
            else:
                print(f"   ❌ INCORRECTA")
                print(f"      No coinciden después de limpiar")
                return False, 0.0
        else:
            print(f"   ❌ INCORRECTA - Datos faltantes")
            return False, 0.0
                
    except Exception as e:
        print(f"❌ Error evaluando respuesta: {e}")
        import traceback
        traceback.print_exc()
        return False, 0.0

# RUTAS PRINCIPALES
@app.route('/')
def home():
    return redirect(url_for('admin_login'))

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == '123456':
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login.html', error="Credenciales incorrectas")

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html', candidatos=list(candidatos_registrados.values()))

@app.route('/admin/candidatos')
def admin_candidatos():
    # Detectar si es petición AJAX
    if (request.headers.get('Accept', '').find('application/json') != -1 or 
        request.args.get('format') == 'json'):
        
        candidatos_list = []
        for candidato in candidatos_registrados.values():
            candidatos_list.append({
                "codigo": candidato["codigo"],
                "nombre_completo": candidato["nombre_completo"],
                "email": candidato["email"],
                "telefono": candidato.get("telefono", ""),
                "cargo": candidato.get("cargo", ""),
                "evaluacion_completada": candidato.get("evaluacion_completada", False),
                "url_evaluacion": candidato.get("link_evaluacion", "")
            })
        return jsonify(candidatos_list)
    
    # Si es petición normal, devolver HTML
    return render_template('panel_admin.html', candidatos=list(candidatos_registrados.values()))

@app.route('/admin/registrar_candidato', methods=['POST'])
def registrar_candidato():
    # Detectar si es JSON (desde JavaScript) o formulario
    if request.is_json:
        # Datos desde JavaScript
        data = request.get_json()
        nombre = data.get('nombre_completo')
        email = data.get('email')
        telefono = data.get('telefono', '')
        cargo = data.get('cargo', '')
    else:
        # Datos desde formulario HTML
        nombre = request.form.get('nombre_completo')
        email = request.form.get('email')
        telefono = request.form.get('telefono', '')
        cargo = request.form.get('cargo', '')
    
    # Generar código único
    import string
    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    candidatos_registrados[codigo] = {
        "codigo": codigo,
        "nombre_completo": nombre,
        "email": email,
        "telefono": telefono,
        "cargo": cargo,
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "evaluacion_completada": False,
        "link_evaluacion": f"http://localhost:5000/evaluacion/{codigo}",
        "url_evaluacion": f"http://localhost:5000/evaluacion/{codigo}"  # Para JavaScript
    }
    
    print(f"✅ Candidato registrado: {nombre} - Código: {codigo}")
    
    # Responder según el tipo de petición
    if request.is_json:
        return jsonify({
            "success": True,
            "candidato": candidatos_registrados[codigo]
        })
    else:
        return redirect(url_for('admin_candidatos'))

# AGREGAR ESTE NUEVO ENDPOINT PARA LOGOUT
@app.route('/admin/logout')
def admin_logout():
    return redirect(url_for('admin_login'))

@app.route('/evaluacion/<codigo>')
def evaluacion(codigo):
    if codigo not in candidatos_registrados:
        return render_template('error.html', mensaje="Código de candidato inválido")
    
    candidato = candidatos_registrados[codigo]
    if candidato.get("evaluacion_completada", False):
        return render_template('error.html', mensaje="Esta evaluación ya ha sido completada")
    
    return render_template('cuestionario.html', candidato=candidato)

@app.route('/iniciar_evaluacion', methods=['POST'])
def iniciar_evaluacion():
    global candidato_actual
    
    data = request.get_json()
    nombre = data.get('nombre') or ""
    documento = data.get('documento') or ""
    email = data.get('email') or ""
    telefono = data.get('telefono') or ""
    
    print(f"=== INICIAR EVALUACIÓN ===")
    print(f"Buscando candidato: {documento}")
    
    # Buscar candidato
    candidato_encontrado = None
    codigo_encontrado = None
    
    if documento and documento in candidatos_registrados:
        candidato_encontrado = candidatos_registrados[documento]
        codigo_encontrado = documento
        print(f"✅ Candidato encontrado: {codigo_encontrado}")
    
    if candidato_encontrado:
        # ✅ REINICIAR COMPLETAMENTE candidato_actual
        candidato_actual = {
            "datos_personales": {
                "codigo": codigo_encontrado,
                "nombre": candidato_encontrado.get("nombre_completo", ""),
                "email": candidato_encontrado.get("email", ""),
                "telefono": candidato_encontrado.get("telefono", telefono)
            },
            "nivel": 1,
            "puntos": 0,
            "respuestas_correctas_nivel": 0,
            "preguntas_mostradas": [],
            "evaluacion_completa": False,  # ← ASEGURAR QUE ESTÁ EN FALSE
            "respuestas": []  # ← AGREGAR PARA EVITAR ERRORES
        }
        
        # ✅ LIMPIAR ESTADO ANTERIOR DEL CANDIDATO
        if codigo_encontrado in candidatos_registrados:
            candidatos_registrados[codigo_encontrado]["evaluacion_completada"] = False
        
        print(f"✅ Evaluación iniciada para: {candidato_encontrado['nombre_completo']}")
        print(f"   Estado limpio: preguntas_mostradas={len(candidato_actual['preguntas_mostradas'])}")
        print(f"   evaluacion_completa={candidato_actual['evaluacion_completa']}")
        
        return jsonify({"mensaje": "Evaluación iniciada correctamente"})
    else:
        print(f"❌ Candidato no encontrado: {documento}")
        return jsonify({"error": "Candidato no registrado"})

@app.route('/api/configuracion')
def api_configuracion():
    """Endpoint para que el frontend obtenga la configuración automáticamente"""
    config = get_configuracion_evaluacion()
    return jsonify(config)

@app.route('/obtener_pregunta')
def obtener_pregunta():
    print(f"🔍 DEBUG obtener_pregunta:")
    print(f"   Total PREGUNTAS disponibles: {len(PREGUNTAS)}")
    print(f"   candidato_actual existe: {bool(candidato_actual)}")
    
    if not candidato_actual:
        return jsonify({"error": "Evaluación no iniciada"})
    
    if len(PREGUNTAS) == 0:
        return jsonify({"error": "No hay preguntas disponibles"})
    
    # Inicializar campos
    if "preguntas_mostradas" not in candidato_actual:
        candidato_actual["preguntas_mostradas"] = []
    if "evaluacion_completa" not in candidato_actual:
        candidato_actual["evaluacion_completa"] = False
    
    preguntas_mostradas = candidato_actual["preguntas_mostradas"]
    
    # LÍMITE DE PREGUNTAS AUTOMÁTICO
    if len(preguntas_mostradas) >= TOTAL_PREGUNTAS:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "Evaluación completada"})
    
    # ✅ LÓGICA AUTOMÁTICA BASADA EN CONFIGURACIÓN
    config = get_configuracion_evaluacion()
    nivel_candidato = candidato_actual.get("nivel", 1)

    # Usar configuración automática para nivel 1
    if len(preguntas_mostradas) < config["preguntas_nivel_1"]:
        nivel_busqueda = 1
        print(f"🎯 FORZANDO NIVEL 1 - Pregunta {len(preguntas_mostradas) + 1}/{config['preguntas_nivel_1']}")
    else:
        nivel_busqueda = nivel_candidato
        print(f"📊 Usando nivel del candidato: {nivel_candidato}")
        print(f"🔍 DEBUG: Candidato ha avanzado - buscando preguntas nivel {nivel_busqueda}")
    
    # FILTRAR PREGUNTAS DISPONIBLES DEL NIVEL EXACTO
    preguntas_disponibles = [
        p for p in PREGUNTAS 
        if p["id"] not in preguntas_mostradas and p["nivel"] == nivel_busqueda
    ]
    
    print(f"📊 Preguntas disponibles nivel {nivel_busqueda}: {len(preguntas_disponibles)}")
    
    # DEBUG: Mostrar distribución de niveles en PREGUNTAS
    if len(preguntas_disponibles) == 0:
        print(f"❌ NO HAY PREGUNTAS DE NIVEL {nivel_busqueda}")
        
        # Mostrar qué niveles SÍ hay disponibles
        niveles_disponibles = {}
        for p in PREGUNTAS:
            if p["id"] not in preguntas_mostradas:
                nivel = p["nivel"]
                if nivel not in niveles_disponibles:
                    niveles_disponibles[nivel] = 0
                niveles_disponibles[nivel] += 1
        
        print(f"   📊 Niveles disponibles: {niveles_disponibles}")
        
        # Si es nivel 1 y no hay, es un error crítico
        if nivel_busqueda == 1:
            print(f"🚨 ERROR CRÍTICO: No hay preguntas de nivel 1")
            return jsonify({"error": "No hay preguntas básicas disponibles"})
        else:
            # Para otros niveles, finalizar evaluación
            candidato_actual["evaluacion_completa"] = True
            return jsonify({"error": "No hay más preguntas del nivel requerido"})
    
    # ✅ SELECCIÓN ALEATORIA SIMPLE
    pregunta_seleccionada = random.choice(preguntas_disponibles)
    
    print(f"📝 PREGUNTA SELECCIONADA:")
    print(f"   ID: {pregunta_seleccionada['id']}")
    print(f"   Nivel: {pregunta_seleccionada['nivel']} (Buscado: {nivel_busqueda})")
    print(f"   Pregunta: {pregunta_seleccionada['pregunta'][:60]}...")
    
    # VERIFICACIÓN DE SEGURIDAD
    if pregunta_seleccionada["nivel"] != nivel_busqueda:
        print(f"🚨 ALERTA: Pregunta nivel {pregunta_seleccionada['nivel']} cuando se buscaba nivel {nivel_busqueda}")
        print(f"   Esto NO debería pasar. Revisar datos del Excel.")
    
    # ✅ MARCAR PREGUNTA COMO MOSTRADA
    candidato_actual["preguntas_mostradas"].append(pregunta_seleccionada["id"])
    
    return jsonify({
        "id": pregunta_seleccionada["id"],
        "pregunta": pregunta_seleccionada["pregunta"],
        "opciones": pregunta_seleccionada["opciones"],
        "imagen": pregunta_seleccionada.get("imagen"),
        "nivel_pregunta": pregunta_seleccionada["nivel"],
        "nivel_candidato": candidato_actual.get("nivel", 1),
        "pregunta_numero": len(candidato_actual["preguntas_mostradas"]),
        "total_preguntas": TOTAL_PREGUNTAS,
        "multiple": pregunta_seleccionada.get("multiple", False),
        "respuestas_correctas_count": len(pregunta_seleccionada.get("respuestas_correctas", []))
    })

@app.route('/responder', methods=['POST'])
def responder():
    global candidato_actual
    
    data = request.get_json()
    respuesta_usuario = data.get('respuesta')
    pregunta_id = data.get('pregunta_id')
    respuestas_seleccionadas = data.get('respuestas_seleccionadas', [])
    
    print(f"🔍 DEBUG RESPONDER:")
    print(f"   Pregunta ID: {pregunta_id}")
    print(f"   Respuesta usuario: {respuesta_usuario}")
    
    # Buscar la pregunta
    pregunta = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
    if not pregunta:
        return jsonify({"error": "Pregunta no encontrada"})
    
    # Evaluar respuesta
    es_correcta, puntos_obtenidos = evaluar_respuesta(pregunta, respuesta_usuario)
    
    # Actualizar puntos
    candidato_actual["puntos"] = candidato_actual.get("puntos", 0) + puntos_obtenidos
    
    # ✅ LÓGICA CORREGIDA DE AVANCE DE NIVEL
    config = get_configuracion_evaluacion()
    nivel_candidato_actual = candidato_actual.get("nivel", 1)
    
    # Inicializar respuestas si no existe
    if "respuestas" not in candidato_actual:
        candidato_actual["respuestas"] = []
    
    # ✅ REGISTRAR RESPUESTA PRIMERO
    nueva_respuesta = {
        "pregunta_id": pregunta_id,
        "pregunta": pregunta["pregunta"],
        "respuesta": respuesta_usuario,
        "respuestas_seleccionadas": respuestas_seleccionadas,
        "correcta": es_correcta,
        "puntos": puntos_obtenidos,
        "nivel_pregunta": pregunta["nivel"],
        "nivel_candidato": nivel_candidato_actual,
        "respuestas_correctas": pregunta.get("respuestas_correctas", [pregunta["respuesta_correcta"]]),
        "multiple": pregunta.get("multiple", False)
    }
    
    candidato_actual["respuestas"].append(nueva_respuesta)
    
    # ✅ DEBUG DETALLADO NIVEL
    print(f"\n🔍 DEBUG DETALLADO NIVEL:")
    print(f"   Config completa: {config}")
    print(f"   Nivel candidato ANTES: {nivel_candidato_actual}")
    print(f"   Pregunta actual fue nivel: {pregunta['nivel']}")
    print(f"   ¿Pregunta fue correcta?: {es_correcta}")
    print(f"   Puntos obtenidos: {puntos_obtenidos}")
    
    # ✅ LÓGICA CORREGIDA - SIN DUPLICACIÓN
    todas_respuestas = candidato_actual["respuestas"]
    
    # Contar respuestas del nivel ACTUAL del candidato
    respuestas_nivel_actual = [
        r for r in todas_respuestas 
        if r.get("nivel_candidato") == nivel_candidato_actual
    ]
    
    # Contar correctas del nivel actual
    correctas_nivel_actual = len([
        r for r in respuestas_nivel_actual 
        if r.get("correcta", False)
    ])
    
    total_preguntas_nivel_actual = len(respuestas_nivel_actual)
    
    print(f"   Respuestas del candidato nivel {nivel_candidato_actual}: {len(respuestas_nivel_actual)}")
    print(f"   De esas, correctas: {correctas_nivel_actual}")
    print(f"   Configuración requiere {config['preguntas_nivel_1']} preguntas")
    print(f"   Configuración requiere {config['min_correctas_avance']} correctas")
    print(f"   ¿Cumple condición?: preguntas={total_preguntas_nivel_actual >= config['preguntas_nivel_1']}, correctas={correctas_nivel_actual >= config['min_correctas_avance']}, no_max={nivel_candidato_actual < 5}")
    
    # ✅ CONDICIÓN PARA AVANZAR DE CUALQUIER NIVEL
    avanzar_nivel = False
    
    if (total_preguntas_nivel_actual >= config["preguntas_nivel_1"] and 
        correctas_nivel_actual >= config["min_correctas_avance"] and 
        nivel_candidato_actual < 5):
        
        # ✅ CUMPLE CONDICIÓN PARA AVANZAR
        candidato_actual["nivel"] += 1
        avanzar_nivel = True
        print(f"🎉 ¡NIVEL UP! {nivel_candidato_actual} → {candidato_actual['nivel']}")
        print(f"   ✅ Logró {correctas_nivel_actual}/{config['min_correctas_avance']} correctas")
        print(f"   ✅ Completó {total_preguntas_nivel_actual}/{config['preguntas_nivel_1']} preguntas")
    elif nivel_candidato_actual >= 5:
        print(f"🏆 YA EN NIVEL MÁXIMO: {nivel_candidato_actual}")
    else:
        print(f"⏳ ESPERANDO EN NIVEL {nivel_candidato_actual}:")
        print(f"   Preguntas: {total_preguntas_nivel_actual}/{config['preguntas_nivel_1']}")
        print(f"   Correctas: {correctas_nivel_actual}/{config['min_correctas_avance']}")
    
    # Verificar si hay más preguntas
    preguntas_mostradas = len(candidato_actual.get("preguntas_mostradas", []))
    hay_mas_preguntas = preguntas_mostradas < TOTAL_PREGUNTAS and not candidato_actual.get("evaluacion_completa", False)
    
    # Actualizar estado si terminó
    if not hay_mas_preguntas:
        candidato_actual["evaluacion_completa"] = True
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        
        if codigo and codigo in candidatos_registrados:
            candidatos_registrados[codigo]["evaluacion_completada"] = True
            candidatos_registrados[codigo]["puntos_finales"] = candidato_actual.get("puntos", 0)
            candidatos_registrados[codigo]["nivel_final"] = candidato_actual.get("nivel", 1)
            print(f"✅ Evaluación completada para: {codigo}")
    
    # Log de debug final
    print(f"📝 RESULTADO FINAL:")
    print(f"   Respuesta: '{respuesta_usuario}' | Correcta: {es_correcta}")
    print(f"   Puntos ganados: {puntos_obtenidos}")
    print(f"   Nivel actual: {candidato_actual.get('nivel', 1)}")
    print(f"   ¿Avanzó de nivel?: {avanzar_nivel}")
    print(f"   Hay más preguntas: {hay_mas_preguntas}")
    
    # ✅ RESPUESTA ESPERADA POR EL FRONTEND
    return jsonify({
        "success": True,                    
        "hay_mas": hay_mas_preguntas,      
        "nivel": candidato_actual.get("nivel", 1),
        "pregunta_numero": preguntas_mostradas,  
        "message": "Respuesta guardada correctamente",
        "avanzar_nivel": avanzar_nivel,
        "correctas_nivel": correctas_nivel_actual,
        "total_nivel": total_preguntas_nivel_actual
    })

@app.route('/generar_pdf_final', methods=['POST'])
def generar_pdf_final():
    global candidato_actual
    
    if not candidato_actual:
        return jsonify({"error": "No hay evaluación activa"})
    
    try:
        # ✅ GENERAR PDF LOCAL
        from pdf_generator import CandidateReportGenerator
        generator = CandidateReportGenerator()
        pdf_path = generator.generate_candidate_report(candidato_actual)
        
        # ✅ SUBIR A GOOGLE DRIVE - USANDO TU ARCHIVO EXISTENTE
        drive_info = None
        try:
            from drive_integration import save_pdf_to_drive
            drive_result = save_pdf_to_drive(pdf_path)
            if drive_result.get('success'):
                drive_info = {
                    'link': drive_result.get('link'),
                    'name': drive_result.get('file_name')
                }
                print(f"☁️ PDF subido a Google Drive: {drive_info['link']}")
            else:
                print(f"⚠️ Error subiendo a Google Drive: {drive_result.get('error')}")
        except Exception as e:
            print(f"⚠️ Error con Google Drive: {e}")
        
        # Calcular estadísticas finales
        respuestas = candidato_actual.get('respuestas', [])
        correctas = len([r for r in respuestas if r.get('correcta', False)])
        total = len(respuestas)
        porcentaje = (correctas / max(total, 1)) * 100
        
        # Marcar evaluación como completada
        candidato_actual["evaluacion_completa"] = True
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        
        if codigo and codigo in candidatos_registrados:
            candidatos_registrados[codigo]["evaluacion_completada"] = True
            candidatos_registrados[codigo]["puntos_finales"] = candidato_actual.get("puntos", 0)
            candidatos_registrados[codigo]["nivel_final"] = candidato_actual.get("nivel", 1)
            if drive_info:
                candidatos_registrados[codigo]["google_drive_link"] = drive_info['link']
        
        print(f"✅ PDF generado: {pdf_path}")
        
        return jsonify({
            "success": True,
            "mensaje": "Evaluación completada y PDF generado",
            "correctas": correctas,
            "total": total,
            "porcentaje": round(porcentaje, 1),
            "nivel_final": candidato_actual.get("nivel", 1),
            "puntos": candidato_actual.get("puntos", 0),
            "pdf_generado": True,
            "pdf_path": pdf_path,
            "google_drive_link": drive_info['link'] if drive_info else None,
            "google_drive_subido": bool(drive_info)
        })
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": f"Error generando PDF: {str(e)}",
            "pdf_generado": False
        })

@app.route('/reporte')
def reporte():
    return render_template('reporte.html', candidatos=candidatos_registrados.values())

@app.route('/api/candidatos')
def api_candidatos():
    return jsonify(candidatos_registrados)

@app.route('/api/preguntas')
def api_preguntas():
    return jsonify(PREGUNTAS)

@app.route('/api/estadisticas')
def api_estadisticas():
    global candidatos_registrados
    return jsonify({
        "total_candidatos": len(candidatos_registrados),
        "total_preguntas": len(PREGUNTAS),
        "niveles_disponibles": NIVELES
    })

# Página de error personalizada
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('error.html', mensaje="Página no encontrada"), 404

@app.errorhandler(500)
def error_interno_servidor(error):
    return render_template('error.html', mensaje="Error interno del servidor"), 500

# Ejecutar la aplicación
if __name__ == '__main__':
    print("\n🚀 SERVIDOR INICIADO")
    print("=" * 50)
    print(f"📊 Configuración actual: {TOTAL_PREGUNTAS} preguntas máximo")
    print("Admin: http://localhost:5000/admin/login")
    print("Usuario/Pass: admin / 123456")
    print("=" * 50)
    app.run(debug=True, port=5000)