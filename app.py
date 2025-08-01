from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import random
import json
from datetime import datetime
import os

app = Flask(__name__)

# Variables globales
candidatos_registrados = {}
candidato_actual = {}
NIVELES = [1, 2, 3, 4, 5]
PREGUNTAS = []

try:
    from PIL import Image
    import io
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️ Pillow no disponible - funcionalidad de imagen limitada")

def cargar_preguntas():
    """Carga las preguntas desde el archivo Excel"""
    global PREGUNTAS
    try:
        archivo_excel = 'Evaluación FWS PAN V2.xlsx'
        print(f"🔍 Buscando archivo: {archivo_excel}")
        
        if os.path.exists(archivo_excel):
            print(f"✅ Archivo encontrado, cargando...")
            df = pd.read_excel(archivo_excel)
            print(f"📊 Excel cargado con {len(df)} filas")
            print(f"🔤 Columnas encontradas: {list(df.columns)}")
            
            PREGUNTAS = []
            for index, row in df.iterrows():
                try:
                    # PREGUNTA - usar columna 'PREGUNTA'
                    pregunta_texto = str(row.get('PREGUNTA', '')).strip()
                    if not pregunta_texto or pregunta_texto in ['nan', 'NaN', '', None] or len(pregunta_texto) < 10:
                        continue
                    
                    # OPCIONES - usar columnas A, B, C, D
                    opciones = []
                    for letra in ['A', 'B', 'C', 'D']:
                        opcion = str(row.get(letra, '')).strip()
                        if opcion and opcion not in ['nan', 'NaN', '', None]:
                            opciones.append(opcion)
                        else:
                            opciones.append(f"Opción {letra}")
                    
                    # IMAGEN - LEER DIRECTAMENTE DEL EXCEL ← CAMBIAR ESTO
                    imagen_data = None
                    imagen_base64 = None
                    
                    try:
                        # Intentar obtener la imagen del Excel
                        imagen_raw = row.get('IMAGEN')
                        
                        if imagen_raw is not None and str(imagen_raw).strip() not in ['nan', 'NaN', '', None]:
                            # Si ya es una cadena base64
                            if isinstance(imagen_raw, str) and imagen_raw.startswith('data:image'):
                                imagen_base64 = imagen_raw
                            else:
                                # Leer la imagen como archivo
                                imagen_path = str(imagen_raw).strip()
                                if os.path.exists(imagen_path):
                                    with open(imagen_path, "rb") as img_file:
                                        imagen_data = img_file.read()
                                        imagen_base64 = f"data:image/jpeg;base64,{base64.b64encode(imagen_data).decode()}"
                                else:
                                    print(f"⚠️ Imagen no encontrada en ruta: {imagen_path}")
                    
                    except Exception as e:
                        print(f"⚠️ Error leyendo imagen: {e}")
                    
                    # RESPUESTAS CORRECTAS - usar RESPUESTA CORRECTA 1 y 2
                    respuesta1 = str(row.get('RESPUESTA CORRECTA 1', '')).upper().strip()
                    respuesta2 = str(row.get('RESPUESTA CORRECTA 2', '')).upper().strip()
                    
                    # Filtrar respuestas válidas
                    respuestas_correctas = []
                    for resp in [respuesta1, respuesta2]:
                        if resp and resp in ['A', 'B', 'C', 'D']:
                            respuestas_correctas.append(resp)
                    
                    # Si no hay respuestas válidas, usar A por defecto
                    if not respuestas_correctas:
                        respuestas_correctas = ['A']
                    
                    # Determinar si es pregunta múltiple
                    multiple = len(respuestas_correctas) > 1
                    
                    # NIVEL - usar columna 'NIVEL'
                    try:
                        nivel = int(row.get('NIVEL', 1))
                        if nivel not in [1, 2, 3, 4, 5]:
                            nivel = 1
                    except:
                        nivel = 1
                    
                    pregunta = {
                        "id": len(PREGUNTAS) + 1,
                        "pregunta": pregunta_texto,
                        "opciones": opciones,
                        "imagen": imagen_base64,  # ← AGREGAR ESTO
                        "respuesta_correcta": respuestas_correctas[0],
                        "respuestas_correctas": respuestas_correctas,
                        "multiple": multiple,
                        "nivel": nivel
                    }
                    
                    PREGUNTAS.append(pregunta)
                    
                    # Mostrar las primeras 3 preguntas para debug
                    if len(PREGUNTAS) <= 3:
                        respuesta_info = f"Respuesta: {respuestas_correctas[0]}"
                        if multiple:
                            respuesta_info += f" (Múltiple: {respuestas_correctas})"
                        imagen_info = f" | Imagen: {'Sí' if imagen_base64 else 'No'}"  # ← AGREGAR ESTO
                        print(f"📝 Pregunta {len(PREGUNTAS)}: {pregunta_texto[:50]}...")
                        print(f"   Opciones: {len(opciones)} | {respuesta_info} | Nivel: {nivel}{imagen_info}")
                        
                except Exception as e:
                    print(f"⚠️ Error procesando fila {index + 1}: {e}")
                    continue
            
            print(f"✅ {len(PREGUNTAS)} preguntas válidas cargadas")
            
            # Mostrar estadísticas
            niveles = {}
            preguntas_multiples = 0
            preguntas_con_imagen = 0  # ← AGREGAR ESTO
            for p in PREGUNTAS:
                nivel = p["nivel"]
                niveles[nivel] = niveles.get(nivel, 0) + 1
                if p["multiple"]:
                    preguntas_multiples += 1
                if p.get("imagen"):  # ← AGREGAR ESTO
                    preguntas_con_imagen += 1
            
            print(f"📈 Distribución por nivel: {niveles}")
            print(f"🔢 Preguntas con respuesta múltiple: {preguntas_multiples}")
            print(f"🖼️ Preguntas con imagen: {preguntas_con_imagen}")  # ← AGREGAR ESTO
            
        else:
            print(f"❌ Archivo {archivo_excel} no encontrado")
            print("📁 Archivos Excel en el directorio:")
            for archivo in os.listdir('.'):
                if archivo.endswith('.xlsx') or archivo.endswith('.xls'):
                    print(f"  - {archivo}")
            
            print(f"⚠️ No se pudieron cargar preguntas. Sistema no funcionará correctamente.")
            PREGUNTAS = []
            
    except Exception as e:
        print(f"❌ Error crítico cargando preguntas: {e}")
        PREGUNTAS = []
        import traceback
        traceback.print_exc()
        print(f"⚠️ Sistema no funcionará sin archivo Excel.")

# Cargar preguntas al iniciar
cargar_preguntas()

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
            "evaluacion_completa": False
        }
        
        print(f"✅ Evaluación iniciada para: {candidato_encontrado['nombre_completo']}")
        return jsonify({"mensaje": "Evaluación iniciada correctamente"})
    else:
        print(f"❌ Candidato no encontrado: {documento}")
        return jsonify({"error": "Candidato no registrado"})

@app.route('/obtener_pregunta')
def obtener_pregunta():
    if not candidato_actual:
        return jsonify({"error": "Evaluación no iniciada"})
    
    # Inicializar campos si no existen
    if "nivel" not in candidato_actual:
        candidato_actual["nivel"] = 1
    if "preguntas_mostradas" not in candidato_actual:
        candidato_actual["preguntas_mostradas"] = []
    if "evaluacion_completa" not in candidato_actual:
        candidato_actual["evaluacion_completa"] = False
    
    # Verificar límite
    if len(candidato_actual["preguntas_mostradas"]) >= 15:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "Evaluación completada"})
    
    # Buscar preguntas disponibles
    nivel_actual = candidato_actual["nivel"]
    preguntas_mostradas = candidato_actual["preguntas_mostradas"]
    
    preguntas_disponibles = [
        p for p in PREGUNTAS
        if p["nivel"] == nivel_actual and p["id"] not in preguntas_mostradas
    ]
    
    if not preguntas_disponibles:
        siguientes = [n for n in NIVELES if n > nivel_actual]
        if siguientes:
            candidato_actual["nivel"] = siguientes[0]
            candidato_actual["respuestas_correctas_nivel"] = 0
            preguntas_disponibles = [
                p for p in PREGUNTAS
                if p["nivel"] == candidato_actual["nivel"] and p["id"] not in preguntas_mostradas
            ]
    
    if not preguntas_disponibles:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "No hay más preguntas"})
    
    # Seleccionar pregunta
    pregunta_seleccionada = random.choice(preguntas_disponibles)
    candidato_actual["preguntas_mostradas"].append(pregunta_seleccionada["id"])
    
    return jsonify({
        "id": pregunta_seleccionada["id"],
        "pregunta": pregunta_seleccionada["pregunta"],
        "opciones": pregunta_seleccionada["opciones"],
        "imagen": pregunta_seleccionada.get("imagen"),  # ← AGREGAR ESTO
        "nivel": candidato_actual["nivel"],
        "pregunta_numero": len(candidato_actual["preguntas_mostradas"]),
        "total_preguntas": 15,
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
    
    # Buscar la pregunta
    pregunta = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
    if not pregunta:
        return jsonify({"error": "Pregunta no encontrada"})
    
    # Evaluar respuesta con soporte múltiple
    es_correcta, puntos_obtenidos = evaluar_respuesta(pregunta, respuesta_usuario)
    
    # Actualizar puntos (INTERNAMENTE, sin mostrar al usuario)
    candidato_actual["puntos"] = candidato_actual.get("puntos", 0) + puntos_obtenidos
    candidato_actual["respuestas_correctas_nivel"] = candidato_actual.get("respuestas_correctas_nivel", 0) + puntos_obtenidos
    
    # Verificar si hay más preguntas
    hay_mas_preguntas = len(candidato_actual.get("preguntas_mostradas", [])) < 15 and not candidato_actual.get("evaluacion_completa", False)
    
    # Registrar respuesta para el reporte
    if "respuestas" not in candidato_actual:
        candidato_actual["respuestas"] = []
    
    candidato_actual["respuestas"].append({
        "pregunta_id": pregunta_id,
        "pregunta": pregunta["pregunta"],
        "respuesta": respuesta_usuario,
        "respuestas_seleccionadas": respuestas_seleccionadas,
        "correcta": es_correcta,
        "puntos": puntos_obtenidos,
        "nivel": pregunta["nivel"],
        "respuestas_correctas": pregunta.get("respuestas_correctas", [pregunta["respuesta_correcta"]]),
        "multiple": pregunta.get("multiple", False)
    })
    
    # Actualizar estado si terminó
    if not hay_mas_preguntas:
        candidato_actual["evaluacion_completa"] = True
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        
        if codigo and codigo in candidatos_registrados:
            candidatos_registrados[codigo]["evaluacion_completada"] = True
            candidatos_registrados[codigo]["puntos_finales"] = candidato_actual.get("puntos", 0)
            print(f"✅ Evaluación completada para: {codigo} | Puntos: {candidato_actual.get('puntos', 0)}")
    
    # Log de debug (SOLO EN SERVIDOR)
    print(f"📝 Respuesta: {respuesta_usuario} | Correcta: {es_correcta} | Puntos: {puntos_obtenidos} | Total: {candidato_actual.get('puntos', 0)}")
    if pregunta.get("multiple", False):
        print(f"🔢 Pregunta múltiple - Respuestas correctas: {pregunta.get('respuestas_correctas', [])} | Usuario eligió: {respuestas_seleccionadas}")
    
    # RESPUESTA SIN REVELAR INFORMACIÓN DE CORRECCIÓN
    return jsonify({
        "success": True,                    # Solo confirmar que se guardó
        "hay_mas": hay_mas_preguntas,      # Si hay más preguntas
        "nivel": candidato_actual.get("nivel", 1),  # Nivel actual
        "pregunta_numero": len(candidato_actual.get("preguntas_mostradas", [])),  # Progreso
        "message": "Respuesta guardada correctamente"  # Mensaje neutral
        # NO ENVIAR: correcto, puntos_obtenidos, respuesta_correcta, etc.
    })

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    try:
        from pdf_generator import CandidateReportGenerator
        generator = CandidateReportGenerator()
        pdf_path = generator.generate_candidate_report(candidato_actual)
        return jsonify({"success": True, "pdf_path": pdf_path})
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/guardar_en_drive', methods=['POST'])
def guardar_en_drive():
    try:
        from drive_integration import DriveUploader
        uploader = DriveUploader()
        # Implementar lógica de subida
        return jsonify({"success": True, "message": "PDF guardado en Drive"})
    except Exception as e:
        print(f"Error subiendo a Drive: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/finalizar_evaluacion', methods=['POST'])
def finalizar_evaluacion():
    """Endpoint para finalizar evaluación: generar PDF y subir a Drive"""
    try:
        if not candidato_actual:
            return jsonify({"success": False, "error": "No hay evaluación activa"})
        
        print("🏁 Iniciando finalización de evaluación...")
        
        # 1. Generar PDF
        pdf_path = None
        pdf_generado = False
        try:
            from pdf_generator import CandidateReportGenerator
            generator = CandidateReportGenerator()
            pdf_path = generator.generate_candidate_report(candidato_actual)
            pdf_generado = True
            print(f"✅ PDF generado: {pdf_path}")
        except Exception as e:
            print(f"❌ Error generando PDF: {e}")
            pdf_generado = False
        
        # 2. Subir a Google Drive
        drive_result = {"success": False, "error": "PDF no generado"}
        if pdf_path and os.path.exists(pdf_path):
            try:
                from drive_integration import save_pdf_to_drive
                drive_result = save_pdf_to_drive(pdf_path)
                print(f"📤 Resultado Drive: {drive_result}")
            except Exception as e:
                print(f"❌ Error subiendo a Drive: {e}")
                drive_result = {"success": False, "error": str(e)}
        
        # 3. Marcar evaluación como completada
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        if codigo and codigo in candidatos_registrados:
            candidatos_registrados[codigo]["evaluacion_completada"] = True
            candidatos_registrados[codigo]["fecha_completado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            candidatos_registrados[codigo]["puntos_obtenidos"] = candidato_actual.get("puntos", 0)
            candidatos_registrados[codigo]["nivel_alcanzado"] = candidato_actual.get("nivel", 1)
            
            if drive_result.get("success"):
                candidatos_registrados[codigo]["drive_url"] = drive_result.get("link")
                candidatos_registrados[codigo]["drive_file"] = drive_result.get("file_name")
            
            print(f"✅ Candidato {codigo} marcado como completado")
        
        return jsonify({
            "success": True,
            "pdf_generated": pdf_generado,
            "drive_upload": drive_result.get("success", False),
            "drive_url": drive_result.get("link"),
            "drive_file": drive_result.get("file_name"),
            "error": drive_result.get("error") if not drive_result.get("success") else None
        })
        
    except Exception as e:
        print(f"❌ Error en finalizar_evaluacion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

def evaluar_respuesta(pregunta, respuesta_usuario):
    """Evalúa respuesta with soporte para múltiples respuestas correctas"""
    respuestas_correctas = pregunta.get("respuestas_correctas", [pregunta["respuesta_correcta"]])
    multiple = pregunta.get("multiple", False)
    
    # Convertir respuesta del usuario a lista
    if ',' in respuesta_usuario:
        respuestas_usuario = [r.strip().upper() for r in respuesta_usuario.split(',')]
    else:
        respuestas_usuario = [respuesta_usuario.upper().strip()]
    
    # Contar respuestas correctas
    aciertos = 0
    for respuesta in respuestas_usuario:
        if respuesta in [r.upper() for r in respuestas_correctas]:
            aciertos += 1
    
    if multiple and len(respuestas_correctas) > 1:
        # PREGUNTA MÚLTIPLE
        if aciertos == len(respuestas_correctas) and len(respuestas_usuario) == len(respuestas_correctas):
            # Todas las respuestas correctas y ninguna incorrecta
            return True, 1.0
        elif aciertos > 0:
            # Al menos una respuesta correcta
            return True, 0.5
        else:
            # Ninguna respuesta correcta
            return False, 0.0
    else:
        # PREGUNTA ÚNICA
        if aciertos > 0:
            return True, 1.0
        else:
            return False, 0.0

if __name__ == '__main__':
    print("🚀 Sistema de Evaluación de Candidatos")
    print(f"📊 Preguntas cargadas: {len(PREGUNTAS)}")
    print(f"🔗 Acceso: http://localhost:5000")
    print(f"👤 Admin: http://localhost:5000/admin/login")
    print(f"📋 Usuario: admin | Contraseña: 123456")
    print("-" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)