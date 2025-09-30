from flask import Flask, abort, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import re
import json
import random
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import base64
from dataclasses import dataclass
from functools import wraps

# ===== INICIALIZACIÓN DE FLASK =====
app = Flask(__name__)

# ...existing code...

# ===== INICIALIZACIÓN AUTOMÁTICA DE PREGUNTAS =====
def inicializar_preguntas_global():
    global PREGUNTAS
    try:
        PREGUNTAS = cargar_preguntas_desde_excel()
        if not PREGUNTAS:
            print("[ERROR] No se cargaron preguntas. Verifica el archivo de tema activo y su contenido.")
        else:
            print(f"[INFO] Preguntas cargadas: {len(PREGUNTAS)}")
    except Exception as e:
        print(f"[ERROR] Fallo al cargar preguntas: {e}")

# ...existing code...

# Al final de la definición de cargar_preguntas_desde_excel (después de la línea 430 aprox)
# inicializar_preguntas_global()

@app.route('/', methods=['GET', 'POST'])
def root_block():
    abort(404)
try:
    from pdf_generator import generar_pdf_evaluacion
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    generar_pdf_evaluacion = None
    logging.warning("Generador de PDF no disponible")

# Importar dependencias para PDF y Drive
try:
    from drive_integration import save_pdf_to_drive
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False
    save_pdf_to_drive = None
    logging.warning("Integración con Drive no disponible")

# ===== CONFIGURACIÓN Y CONSTANTES =====
class Config:
    """Configuración centralizada de la aplicación"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Configuración de evaluación
    TOTAL_PREGUNTAS = 40
    ARCHIVO_EXCEL = 'Evaluación FWS PAN V2.xlsx'
    
    # Credenciales admin (en producción usar variables de entorno)
    ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
    ADMIN_PASS = os.getenv('ADMIN_PASS', '123456')
    
    # Configuración de evaluación
    EVALUACION_CONFIG = {
        "total_preguntas": 40,
        "evaluacion_cada": 5,
        "min_correctas_avance": 3,
        "distribucion_niveles": {
            "nivel_1": {"preguntas": "1-10", "descripcion": "Básico"},
            "nivel_2": {"preguntas": "11-12", "descripcion": "Transición"},  
            "nivel_3": {"preguntas": "13-22", "descripcion": "Intermedio"},
            "nivel_4": {"preguntas": "23-30", "descripcion": "Avanzado"},
            "nivel_5": {"preguntas": "31-40", "descripcion": "Experto"}
        },
        "niveles_maximos": 5,
        "preguntas_nivel_1": 10,
        "min_correctas_nivel_1": 6,
        "terminacion_temprana": {
            "errores_consecutivos": 5,
            "porcentaje_minimo_mitad": 40
        }
    }

@dataclass
class Candidato:
    """Clase para representar un candidato"""
    codigo: str
    nombre_completo: str
    email: str
    telefono: str = ""
    cargo: str = ""
    fecha_registro: str = ""
    evaluacion_completada: bool = False
    link_evaluacion: str = ""
    # url_evaluacion eliminado, se genera dinámicamente
    puntos_finales: float = 0.0
    nivel_final: int = 1

@dataclass
class Pregunta:
    """Clase para representar una pregunta"""
    id: int
    pregunta: str
    opciones: List[str]
    respuesta_correcta: str
    respuestas_correctas: List[str]
    nivel: int
    multiple: bool = False
    imagen: Optional[str] = None
    categoria: str = "General"
    fila_excel: int = 0

# ===== CONFIGURACIÓN DE LOGGING =====
def setup_logging():
    """Configura el sistema de logging"""
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname('evaluacion_system.log') or '.'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('evaluacion_system.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ===== INICIALIZACIÓN DE FLASK =====

from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
# Configuración de conexión a PostgreSQL (solo la correcta)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://empresa_user:qwerty@localhost:5432/empresa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de Candidato
class CandidatoDB(db.Model):
    __tablename__ = 'candidatos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30))
    cargo = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime)
    evaluacion_completada = db.Column(db.Boolean, default=False)
    puntos_finales = db.Column(db.Float, default=0)
    nivel_final = db.Column(db.Integer, default=1)
    acepta_terminos = db.Column(db.Boolean, default=False)
    tema = db.Column(db.String(120))
    resultados = db.relationship('ResultadoDB', backref='candidato', cascade='all, delete-orphan', lazy=True)

# Modelo de Resultado
class ResultadoDB(db.Model):
    __tablename__ = 'resultados'
    id = db.Column(db.Integer, primary_key=True)
    candidato_id = db.Column(db.Integer, db.ForeignKey('candidatos.id'))
    correctas = db.Column(db.Integer)
    total = db.Column(db.Integer)
    porcentaje = db.Column(db.Float)
    puntos = db.Column(db.Float)
    nivel_final = db.Column(db.Integer)
    fecha_evaluacion = db.Column(db.DateTime)
    tema = db.Column(db.String(120))

# ===== VARIABLES GLOBALES =====
candidatos_registrados: Dict[str, Dict[str, Any]] = {}
candidato_actual: Dict[str, Any] = {}
PREGUNTAS: List[Dict[str, Any]] = []

# Utilidad: obtener texto de opción a partir de una letra (A-D)
def _safe_opt(opciones: List[str], letra: str) -> str:
    try:
        if not letra:
            return ''
        idx = ord(letra.upper()[0]) - ord('A')
        if 0 <= idx < len(opciones):
            return opciones[idx]
        return ''
    except Exception:
        return ''

# ===== DECORADORES =====
def admin_required(f):
    """Decorador para rutas que requieren autenticación admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(f):
    """Decorador para manejo centralizado de errores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {f.__name__}: {str(e)}")
            return jsonify({"error": "Error interno del servidor"}), 500
    return decorated_function


# ===== ENDPOINT ELIMINAR CANDIDATO =====
@app.route('/admin/eliminar_candidato', methods=['POST'])
@admin_required
@handle_errors
def eliminar_candidato():
    try:
        data = request.get_json()
        codigo = data.get('codigo', '').strip()
        if not codigo:
            logger.error('Código de candidato no proporcionado')
            return jsonify({'error': 'Código requerido'}), 400
        candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
        if not candidato_db:
            logger.error(f'Candidato no encontrado: {codigo}')
            return jsonify({'error': 'Candidato no encontrado'}), 404
        # Eliminar resultados asociados
        resultados = ResultadoDB.query.filter_by(candidato_id=candidato_db.id).all()
        for resultado in resultados:
            try:
                db.session.delete(resultado)
            except Exception as e:
                logger.error(f'Error eliminando resultado {resultado.id}: {e}')
        try:
            db.session.delete(candidato_db)
            db.session.commit()
        except Exception as e:
            logger.error(f'Error eliminando candidato {codigo}: {e}')
            db.session.rollback()
            return jsonify({'error': f'Error eliminando candidato: {str(e)}'}), 500
        # Eliminar también de memoria si existe
        if codigo in candidatos_registrados:
            del candidatos_registrados[codigo]
        logger.info(f'Candidato eliminado correctamente: {codigo}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error inesperado en eliminar_candidato: {e}')
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

# ===== ENDPOINT ELIMINAR ARCHIVO EXCEL DE TEMA =====
@app.route('/admin/eliminar_tema', methods=['POST'])
@admin_required
@handle_errors
def eliminar_tema():
    data = request.get_json(force=True)
    archivo_excel = data.get('archivo_excel')
    if not archivo_excel:
        return jsonify({'success': False, 'error': 'Nombre de archivo requerido'}), 400
    temas_dir = os.path.join(os.getcwd(), 'temas')
    ruta_excel = os.path.join(temas_dir, archivo_excel)
    if not os.path.exists(ruta_excel):
        return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
    try:
        os.remove(ruta_excel)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== EVALUADOR DE RESPUESTAS =====
class EvaluadorRespuestas:
    @staticmethod
    def evaluar_respuesta(pregunta, respuesta_usuario, respuesta_letra):
        # Lógica básica: respuesta correcta por letra o texto
        correctas = pregunta.get('respuestas_correctas', [pregunta.get('respuesta_correcta')])
        multiple = pregunta.get('multiple', False)
        puntos = 0
        es_correcta = False
        if multiple:
            # Si es múltiple, otorgar 0.5 puntos por cada respuesta correcta seleccionada
            if isinstance(respuesta_usuario, list):
                aciertos = len([r for r in respuesta_usuario if r in correctas])
                total_correctas = len(correctas)
                puntos = aciertos / total_correctas if total_correctas > 0 else 0
                es_correcta = puntos == 1.0
            else:
                es_correcta = False
                puntos = 0
        else:
            # Respuesta única
            if respuesta_letra and respuesta_letra in correctas:
                es_correcta = True
                puntos = 1
            elif respuesta_usuario and respuesta_usuario in correctas:
                es_correcta = True
                puntos = 1
        return es_correcta, puntos

    @staticmethod
    def verificar_terminacion_temprana(candidato):
        # Implementa tu lógica de terminación temprana aquí
        return False, None

    @staticmethod
    def verificar_avance_nivel(candidato):
        # Implementa tu lógica de avance de nivel aquí
        return False, candidato.get('nivel', 1)

# ===== RUTAS PRINCIPALES =====
@app.route('/responder', methods=['POST'])
@handle_errors
def responder():
    global candidato_actual
    data = request.get_json()
    pregunta_numero = len(candidato_actual.get("preguntas_mostradas", [])) - 1
    orden_preguntas = candidato_actual.get("orden_preguntas", [])
    # Usar el índice actual para obtener el ID y la pregunta
    if 0 <= pregunta_numero < len(orden_preguntas):
        pregunta_id = orden_preguntas[pregunta_numero]
        pregunta = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
    else:
        pregunta = None
    respuestas_usuario = data.get("respuestas", [])
    if not pregunta:
        logger.error(f"Pregunta no encontrada. pregunta_numero={pregunta_numero}, orden_preguntas={orden_preguntas}")
        return jsonify({"error": "Pregunta no encontrada"}), 400
    # Calcular puntaje
    puntaje = 0
    es_multiple = pregunta.get("multiple", False)
    respuestas_correctas = pregunta.get("respuestas_correctas", [])
    if es_multiple:
        if set(respuestas_usuario) == set(respuestas_correctas):
            puntaje = 1
        elif any(r in respuestas_correctas for r in respuestas_usuario):
            puntaje = 0.5
    else:
        if respuestas_usuario and respuestas_usuario[0] in respuestas_correctas:
            puntaje = 1
    candidato_actual["puntos"] = candidato_actual.get("puntos", 0) + puntaje
    candidato_actual.setdefault("respuestas", []).append({
        "id": pregunta_id,
        "respuestas": respuestas_usuario,
        "correctas": respuestas_correctas,
        "puntaje": puntaje,
        "nivel": pregunta.get("nivel", 1)
    })
    # Lógica adaptativa de avance de nivel
    adaptativo = candidato_actual.get("adaptativo", False)
    nivel_actual = candidato_actual.get("nivel_actual", 1)
    if adaptativo:
        if pregunta.get("nivel", 1) == nivel_actual:
            candidato_actual["preguntas_nivel"] += 1
            if puntaje == 1:
                candidato_actual["correctas_nivel"] += 1
            # Si ya respondió 8 preguntas de este nivel
            if candidato_actual["preguntas_nivel"] == 8:
                if candidato_actual["correctas_nivel"] >= 5:
                    candidato_actual["nivel_actual"] += 1
                else:
                    candidato_actual["evaluacion_completa"] = True
                candidato_actual["preguntas_nivel"] = 0
                candidato_actual["correctas_nivel"] = 0
    # Determinar si hay más preguntas
    preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
    total_preguntas = Config.TOTAL_PREGUNTAS
    hay_mas = len(preguntas_mostradas) < total_preguntas

    return jsonify({"success": True, "hay_mas": hay_mas})
# Endpoint para listar archivos Excel disponibles
@app.route('/temas/', methods=['GET'])
def listar_archivos_temas():
    temas_dir = os.path.join(os.getcwd(), 'temas')
    if not os.path.exists(temas_dir):
        return jsonify({'archivos': []})
    archivos = [f for f in os.listdir(temas_dir) if f.endswith('.xlsx') or f.endswith('.xls')]
    return jsonify({'archivos': archivos})
import pandas as pd

# Ruta para subir archivos Excel de preguntas
@app.route('/admin/subir_tema', methods=['POST'])
@admin_required
def subir_tema():
    if 'archivo_tema' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400
    archivo = request.files['archivo_tema']
    if archivo.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    temas_dir = os.path.join(os.getcwd(), 'temas')
    if not os.path.exists(temas_dir):
        os.makedirs(temas_dir)
    ruta_destino = os.path.join(temas_dir, archivo.filename)
    archivo.save(ruta_destino)
    # Recargar preguntas automáticamente si el archivo subido es el tema activo
    tema_activo = get_tema_activo()
    if tema_activo and tema_activo == archivo.filename:
        global PREGUNTAS
        PREGUNTAS = cargar_preguntas_desde_excel()
    return jsonify({'success': True, 'archivo': archivo.filename})

# Ruta para seleccionar el tema activo
@app.route('/admin/seleccionar_tema', methods=['POST'])
@admin_required
def seleccionar_tema():
    data = request.form if not request.is_json else request.get_json()
    nombre_archivo = data.get('archivo_excel')
    if not nombre_archivo:
        return jsonify({'error': 'Nombre de archivo requerido'}), 400
    config = {
        'archivo_excel': nombre_archivo
    }
    with open('config_tema.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(config, f, ensure_ascii=False, indent=2)
    # Recargar preguntas automáticamente
    global PREGUNTAS
    PREGUNTAS = cargar_preguntas_desde_excel()
    return jsonify({'success': True, 'tema_activo': nombre_archivo})

# Función para obtener el tema activo
def get_tema_activo():
    import json
    if not os.path.exists('config_tema.json'):
        return None
    with open('config_tema.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('archivo_excel')

# Función para cargar preguntas desde el tema activo
def cargar_preguntas_desde_excel():
    archivo_excel = get_tema_activo()
    if not archivo_excel:
        return []
    temas_dir = os.path.join(os.getcwd(), 'temas')
    ruta_excel = os.path.join(temas_dir, archivo_excel)
    if not os.path.exists(ruta_excel):
        return []
    df = pd.read_excel(ruta_excel)
    preguntas = []
    used_ids = set()
    for idx, row in df.iterrows():
        opciones = []
        for letra in ['A', 'B', 'C', 'D', 'E']:
            if letra in df.columns:
                opt = str(row.get(letra, '')).strip()
                if opt:
                    opciones.append(opt)
        # Solo incluir preguntas que tengan al menos dos opciones (A y B)
        if len(opciones) < 2:
            continue
        # Validar que las respuestas correctas sean solo letras permitidas
        respuestas_correctas = []
        for col in ['RESPUESTA CORRECTA', 'RESPUESTA CORRECTA 1', 'RESPUESTA CORRECTA 2']:
            val = row.get(col)
            if val and not pd.isna(val):
                val_str = str(val).strip().upper()
                if val_str in ['A', 'B', 'C', 'D', 'E']:
                    respuestas_correctas.append(val_str)
        if not respuestas_correctas:
            continue  # Saltar preguntas sin respuesta válida tipo letra
        respuestas_validas = [r for r in respuestas_correctas if r]
        es_multiple = len(respuestas_validas) > 1
        pregunta_id_raw = row.get('NUM')
        try:
            pregunta_id = int(''.join(filter(str.isdigit, str(pregunta_id_raw))))
        except:
            pregunta_id = idx + 1
        # Si el ID ya existe, asignar uno nuevo consecutivo
        while pregunta_id in used_ids or pregunta_id == 0:
            pregunta_id += 1
        used_ids.add(pregunta_id)
        nivel_raw = row.get('NIVEL', 1)
        try:
            nivel_str = str(nivel_raw)
            nivel_num = int(''.join(filter(str.isdigit, nivel_str)))
            if nivel_num < 1 or nivel_num > 5:
                nivel_num = 1
        except:
            nivel_num = 1
        pregunta_texto = row.get('PREGUNTA', row.get('TIPO DE PREGUNTA', ''))
        preguntas.append({
            'id': pregunta_id,
            'pregunta': pregunta_texto,
            'opciones': opciones,
            'respuesta_correcta': respuestas_validas[0] if respuestas_validas else '',
            'respuestas_correctas': respuestas_validas,
            'nivel': nivel_num,
            'categoria': row.get('CATEGORIA', ''),
            'multiple': es_multiple
        })
    return preguntas

    # Inicializar preguntas globales después de definir la función
    inicializar_preguntas_global()

@app.route('/')
def home():
    return redirect(url_for('admin_login'))

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/authenticate', methods=['POST'])
@handle_errors
def admin_authenticate():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == Config.ADMIN_USER and password == Config.ADMIN_PASS:
        session['admin_logged_in'] = True
        logger.info(f"Admin login exitoso: {username}")
        return redirect(url_for('admin_dashboard'))
    else:
        logger.warning(f"Intento de login fallido: {username}")
        return render_template('admin_login.html', error="Credenciales incorrectas")


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Obtener candidatos y resultados desde la base de datos
    candidatos_db = CandidatoDB.query.all()
    resultados_db = ResultadoDB.query.all()
    # Crear diccionario de resultados por candidato
    resultados_dict = {}
    for r in resultados_db:
        resultados_dict[r.candidato_id] = {
            "tema": r.tema,
            "correctas": r.correctas,
            "total": r.total,
            "porcentaje": r.porcentaje,
            "puntos": r.puntos,
            "nivel_final": r.nivel_final,
            "fecha_evaluacion": r.fecha_evaluacion
        }
    tema_activo = get_tema_activo() or "No seleccionado"
    return render_template('admin_dashboard.html', candidatos=candidatos_db, resultados=resultados_dict, tema_activo=tema_activo)

@app.route('/admin/candidatos')
@admin_required
@handle_errors
def admin_candidatos():
    # Detectar si es petición AJAX
    if (request.headers.get('Accept', '').find('application/json') != -1 or 
        request.args.get('format') == 'json'):
        candidatos_db = CandidatoDB.query.all()
        candidatos_list = []
        for candidato in candidatos_db:
            candidatos_list.append({
                "codigo": candidato.codigo,
                "nombre_completo": candidato.nombre_completo,
                "email": candidato.email,
                "telefono": getattr(candidato, "telefono", ""),
                "cargo": getattr(candidato, "cargo", ""),
                "evaluacion_completada": getattr(candidato, "evaluacion_completada", False),
                "url_evaluacion": f"/evaluacion/{candidato.codigo}"
            })
        return jsonify(candidatos_list)
    
    candidatos_db = CandidatoDB.query.all()
    return render_template('panel_admin.html', candidatos=candidatos_db)

@app.route('/admin/registrar_candidato', methods=['POST'])
@admin_required
@handle_errors
def registrar_candidato():
    # Detectar si es JSON o formulario
    if request.is_json:
        data = request.get_json()
        tipo_documento = data.get('tipo_documento', '').strip()
        numero_documento = data.get('numero_documento', '').strip()
        nombre = data.get('nombre_completo', '').strip()
        email = data.get('email', '').strip()
        cargo = data.get('cargo', '').strip()
        tema = data.get('tema', '').strip()
        try:
            candidato = registrar_candidato_simple(tipo_documento, numero_documento, nombre, email, cargo, tema)

            # Guardar candidato en la base de datos con el tema seleccionado
            candidato_db = CandidatoDB.query.filter_by(codigo=candidato["codigo"]).first()
            if not candidato_db:
                candidato_db = CandidatoDB(
                    codigo=candidato["codigo"],
                    nombre_completo=nombre,
                    email=email,
                    telefono=candidato.get("telefono", ""),
                    cargo=cargo,
                    fecha_registro=datetime.now(),
                    evaluacion_completada=False,
                    acepta_terminos=False,
                    tema=tema,
                )
                db.session.add(candidato_db)
                db.session.commit()

            if request.is_json:
                return jsonify({"success": True, "candidato": candidato})
            else:
                return redirect(url_for('admin_candidatos'))
        except Exception as e:
            logger.error(f"Error registrando candidato: {e}")
            error_msg = "Error interno al registrar candidato"
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            else:
                return render_template('admin_dashboard.html', error=error_msg)
    # Fin del bloque try/except, no se requiere else ni except adicional aquí
    validation_errors = []
    valid_email, email_error = validar_email_simple(email)
    if not valid_email:
        validation_errors.append(f"Email: {email_error}")
    # Verificar duplicados de documento y email
    for candidato in candidatos_registrados.values():
        if candidato.get('numero_documento', '').lower() == numero_documento.lower():
            validation_errors.append('Ya existe un candidato con este número de documento')
            break
        if candidato['email'].lower() == email.lower():
            validation_errors.append('Ya existe un candidato con este email')
            break
    if validation_errors:
        error_msg = '; '.join(validation_errors)
        logger.warning(f"Errores de validación al registrar candidato: {error_msg}")
        if request.is_json:
            return jsonify({'error': error_msg}), 400
        else:
            return render_template('admin_dashboard.html', error=error_msg)
    try:
        candidato = registrar_candidato_simple(tipo_documento, numero_documento, nombre, email, cargo, tema)
        if request.is_json:
            return jsonify({"success": True, "candidato": candidato})
        else:
            return redirect(url_for('admin_candidatos'))
    except Exception as e:
        logger.error(f"Error registrando candidato: {e}")
        error_msg = "Error interno al registrar candidato"
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            return render_template('admin_dashboard.html', error=error_msg)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    logger.info("Admin logout")
    return redirect(url_for('admin_login'))

@app.route('/evaluacion/<codigo>')
@handle_errors
def evaluacion(codigo):
    # Si el candidato no está en memoria, buscar en la base de datos y poblar el diccionario
    if codigo not in candidatos_registrados:
        candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
        if not candidato_db:
            logger.warning(f"Código de candidato inválido: {codigo}")
            return render_template('error.html', mensaje="Código de candidato inválido")
        # Poblar el diccionario en memoria
        candidatos_registrados[codigo] = {
            "codigo": candidato_db.codigo,
            "nombre_completo": candidato_db.nombre_completo,
            "email": candidato_db.email,
            "telefono": getattr(candidato_db, "telefono", ""),
            "cargo": getattr(candidato_db, "cargo", ""),
            "fecha_registro": str(candidato_db.fecha_registro),
            "evaluacion_completada": candidato_db.evaluacion_completada,
            "url_evaluacion": f"/evaluacion/{candidato_db.codigo}"
        }
    candidato = candidatos_registrados[codigo]
    if candidato.get("evaluacion_completada", False):
        logger.warning(f"Evaluación ya completada para: {codigo}")
        return render_template('error.html', mensaje="Esta evaluación ya ha sido completada")
    return render_template('cuestionario.html', candidato=candidato)

@app.route('/iniciar_evaluacion', methods=['POST'])
@handle_errors
def iniciar_evaluacion():
    global candidato_actual
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos JSON requeridos"}), 400
    
    documento = data.get('documento', '')
    acepta_terminos = int(data.get('acepta_terminos', 0))

    logger.info(f"Iniciando evaluación para: {documento}")

    if documento and documento in candidatos_registrados:
        candidato_encontrado = candidatos_registrados[documento]
        # REINICIAR COMPLETAMENTE candidato_actual
        candidato_actual = {
            "datos_personales": {
                "codigo": documento,
                "nombre": candidato_encontrado.get("nombre_completo", ""),
                "email": candidato_encontrado.get("email", ""),
                "telefono": candidato_encontrado.get("telefono", data.get('telefono', ''))
            },
            "nivel": 1,
            "puntos": 0,
            "preguntas_mostradas": [],
            "evaluacion_completa": False,
            "respuestas": [],
            "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "acepta_terminos": acepta_terminos
        }
        candidatos_registrados[documento]["evaluacion_completada"] = False
        candidatos_registrados[documento]["acepta_terminos"] = acepta_terminos

        # Actualizar en la base de datos
        candidato_db = CandidatoDB.query.filter_by(codigo=documento).first()
        if candidato_db:
            candidato_db.acepta_terminos = bool(acepta_terminos)
            db.session.commit()

        # Generar orden aleatorio de preguntas agrupadas por nivel
        global PREGUNTAS
        PREGUNTAS = cargar_preguntas_desde_excel()
        preguntas_por_nivel = {}
        for p in PREGUNTAS:
            nivel = p.get("nivel", 1)
            preguntas_por_nivel.setdefault(nivel, []).append(p["id"])
        orden_preguntas = []
        adaptativo = sum(len(ids) for ids in preguntas_por_nivel.values()) >= 40
        if adaptativo:
            # Seleccionar 8 aleatorias por nivel y mezclar
            for nivel in sorted(preguntas_por_nivel.keys()):
                ids = preguntas_por_nivel[nivel]
                seleccionadas = random.sample(ids, min(8, len(ids)))
                random.shuffle(seleccionadas)
                orden_preguntas.extend(seleccionadas)
        else:
            # Secuencial, todas las preguntas por nivel en orden
            for nivel in sorted(preguntas_por_nivel.keys()):
                ids = preguntas_por_nivel[nivel]
                orden_preguntas.extend(ids)
        candidato_actual["orden_preguntas"] = orden_preguntas
        candidato_actual["adaptativo"] = adaptativo
        candidato_actual["nivel_actual"] = 1
        candidato_actual["correctas_nivel"] = 0
        candidato_actual["preguntas_nivel"] = 0
        logger.info(f"Evaluación iniciada para: {candidato_encontrado['nombre_completo']}")
        return jsonify({"mensaje": "Evaluación iniciada correctamente"})
    else:
        logger.warning(f"Candidato no encontrado: {documento}")
        return jsonify({"error": "Candidato no registrado"}), 404

@app.route('/obtener_pregunta')
@handle_errors
def obtener_pregunta():
    """Obtiene la siguiente pregunta para el candidato"""
    # Recargar preguntas en tiempo real desde el Excel
    global PREGUNTAS
    PREGUNTAS = cargar_preguntas_desde_excel()
    if not candidato_actual or len(PREGUNTAS) == 0:
        return jsonify({"error": "Evaluación no iniciada"}), 400
    
    preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
    orden_preguntas = candidato_actual.get("orden_preguntas", [])
    adaptativo = candidato_actual.get("adaptativo", False)
    nivel_actual = candidato_actual.get("nivel_actual", 1)
    pregunta_numero = len(preguntas_mostradas)
    if pregunta_numero >= len(orden_preguntas):
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "No hay más preguntas disponibles"})
    pregunta_id = orden_preguntas[pregunta_numero]
    pregunta_seleccionada = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
    if not pregunta_seleccionada:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "No hay más preguntas disponibles"})
    candidato_actual["preguntas_mostradas"].append(pregunta_seleccionada["id"])
    candidato_actual["pregunta_actual_nivel"] = pregunta_seleccionada.get("nivel", 1)
    # ...existing code...

    return jsonify({
        "id": pregunta_seleccionada["id"],
        "pregunta": pregunta_seleccionada["pregunta"],
        "opciones": pregunta_seleccionada["opciones"],
        "imagen": pregunta_seleccionada.get("imagen"),
        "pregunta_numero": len(candidato_actual["preguntas_mostradas"]),
        "total_preguntas": Config.TOTAL_PREGUNTAS,
        "multiple": pregunta_seleccionada.get("multiple", False),
        "respuestas_correctas_count": len(pregunta_seleccionada.get("respuestas_correctas", []))
    })

def _determinar_nivel_pregunta(pregunta_numero: int, nivel_candidato: int) -> int:
    """Determina el nivel de pregunta según el progreso"""
    if pregunta_numero <= 10:
        return 1
    elif pregunta_numero <= 12:
        return 2
    else:
        return nivel_candidato

def _buscar_pregunta_fallback(preguntas_mostradas: List[int], nivel_busqueda: int) -> List[Dict[str, Any]]:
    """Busca preguntas de niveles alternativos"""
    for nivel_alt in [nivel_busqueda-1, nivel_busqueda+1, 1, 2, 3, 4, 5]:
        if nivel_alt < 1 or nivel_alt > 5:
            continue
        preguntas_alt = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p["nivel"] == nivel_alt]
        if preguntas_alt:
            return preguntas_alt
    return []

def _actualizar_candidato_final():
    """Actualiza el candidato al finalizar la evaluación"""
    codigo = candidato_actual.get("datos_personales", {}).get("codigo")
    if codigo and codigo in candidatos_registrados:
        candidatos_registrados[codigo]["evaluacion_completada"] = True
        candidatos_registrados[codigo]["puntos_finales"] = candidato_actual.get("puntos", 0)
        # Guardar el nivel final alcanzado
        nivel_final = candidato_actual.get("nivel_actual", 1)
        candidatos_registrados[codigo]["nivel_final"] = nivel_final

# ===== GENERADOR DE PDF =====
@app.route('/generar_pdf_final', methods=['POST'])
@handle_errors
def generar_pdf_final():
    global candidato_actual
    global candidato_actual, candidatos_registrados
    codigo = candidato_actual.get("datos_personales", {}).get("codigo")
    if not codigo:
        return
    # Marcar como completada en memoria
    candidato_actual["evaluacion_completa"] = True
    if codigo in candidatos_registrados:
        candidatos_registrados[codigo]["evaluacion_completada"] = True
        candidatos_registrados[codigo]["nivel_final"] = candidato_actual.get("nivel_actual", 1)
    # Marcar como completada en la base de datos
    candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
    if candidato_db:
        candidato_db.evaluacion_completada = True
        candidato_db.nivel_final = candidato_actual.get("nivel_actual", 1)
        db.session.commit()
    if not candidato_actual:
        return jsonify({"error": "No hay evaluación activa"}), 400
    
    try:
        # Calcular estadísticas finales
        respuestas = candidato_actual.get('respuestas', [])
        correctas = len([r for r in respuestas if r.get('correcta', False)])
        total = len(respuestas)
        porcentaje = (correctas / max(total, 1)) * 100
        
        # Marcar evaluación como completada
        candidato_actual["evaluacion_completa"] = True
        _actualizar_candidato_final()

        # Guardar resultado en la base de datos
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
        if candidato_db:
            # Verificar si ya existe resultado para este candidato
            resultado_existente = ResultadoDB.query.filter_by(candidato_id=candidato_db.id).first()
            if not resultado_existente:
                resultado_db = ResultadoDB(
                    candidato_id=candidato_db.id,
                    correctas=correctas,
                    total=total,
                    porcentaje=porcentaje,
                    puntos=candidato_actual.get("puntos", 0),
                    nivel_final=candidato_actual.get("nivel", 1),
                    fecha_evaluacion=datetime.now(),
                    tema=get_tema_activo()
                )
                db.session.add(resultado_db)
                db.session.commit()

        # Obtener datos del candidato
        candidato_data = candidatos_registrados.get(codigo, {})
        # Asegurar que el valor de aceptación de términos esté presente
        candidato_data["acepta_terminos"] = candidato_actual.get("acepta_terminos", candidato_data.get("acepta_terminos", 0))
        
        # Generar PDF usando el generador especializado
        pdf_path = None
        drive_result = {"success": False, "error": "PDF no generado"}
        
        try:
            if REPORTLAB_AVAILABLE:
                pdf_path = generar_pdf_evaluacion(candidato_data, candidato_actual)
                logger.info(f"PDF generado: {pdf_path}")
                
                # Enviar a Google Drive si está disponible
                if DRIVE_AVAILABLE and pdf_path and os.path.exists(pdf_path):
                    drive_result = save_pdf_to_drive(pdf_path)
                    if drive_result.get("success"):
                        logger.info(f"PDF enviado a Drive: {drive_result.get('file_name')}")
                    else:
                        logger.error(f"Error enviando a Drive: {drive_result.get('error')}")
                else:
                    drive_result = {"success": False, "error": "Drive no disponible"}
            else:
                drive_result = {"success": False, "error": "Generador PDF no disponible"}
                
        except Exception as e:
            logger.error(f"Error en generación/envío PDF: {e}")
            drive_result = {"success": False, "error": str(e)}
        
        # Respuesta al cliente
        response_data = {
            "success": True,
            "mensaje": "Evaluación completada correctamente",
            "correctas": correctas,
            "total": total,
            "porcentaje": round(porcentaje, 1),
            "nivel_final": candidato_actual.get("nivel", 1),
            "puntos": candidato_actual.get("puntos", 0),
            "pdf_generado": pdf_path is not None,
            "drive_upload": drive_result.get("success", False),
            "drive_error": drive_result.get("error") if not drive_result.get("success") else None
        }
        
        # Incluir link de Drive si está disponible
        if drive_result.get("success") and drive_result.get("link"):
            response_data["drive_link"] = drive_result.get("link")
        
        logger.info("Evaluación finalizada - Proceso completado")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error en proceso final: {e}")
        return jsonify({
            "success": False,
            "error": f"Error procesando evaluación: {str(e)}",
            "pdf_generado": False,
            "drive_upload": False
        }), 500

# ===== REGISTRO DE CANDIDATO SIN CandidatoManager =====
def registrar_candidato_simple(tipo_documento, numero_documento, nombre, email, cargo, tema):
    # Generar código único
    codigo = f"{tipo_documento[:2].upper()}{random.randint(10000,99999)}"
    candidato = {
        "codigo": codigo,
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
        "nombre_completo": nombre,
        "email": email,
        "cargo": cargo,
        "tema": tema,
        "telefono": "",
        "fecha_registro": datetime.now().isoformat(),
        "evaluacion_completada": False,
        "puntos_finales": 0.0,
        "nivel_final": 1,
    }
    candidatos_registrados[codigo] = candidato
    return candidato

# ===== RUTAS API =====

@app.route('/api/configuracion')
@handle_errors
def api_configuracion():
    """API para obtener configuración de la evaluación"""
    return jsonify(get_configuracion_evaluacion())

@app.route('/reporte')
@admin_required
def reporte():
    return render_template('reporte.html', candidatos=candidatos_registrados.values())

@app.route('/api/candidatos')
@admin_required
@handle_errors
def api_candidatos():
    return jsonify(candidatos_registrados)

@app.route('/api/preguntas')
@admin_required
@handle_errors
def api_preguntas():
    return jsonify(PREGUNTAS)

@app.route('/api/estadisticas')
@admin_required
@handle_errors
def api_estadisticas():
    return jsonify({
        "total_candidatos": len(candidatos_registrados),
        "total_preguntas": len(PREGUNTAS),
        "niveles_disponibles": [1, 2, 3, 4, 5]
    })

# ===== MANEJO DE ERRORES =====

@app.errorhandler(404)
def pagina_no_encontrada(error):
    logger.warning(f"Página no encontrada: {request.url}")
    return render_template('error.html', mensaje="Página no encontrada"), 404

@app.errorhandler(500)
def error_interno_servidor(error):
    logger.error(f"Error interno del servidor: {error}")
    return render_template('error.html', mensaje="Error interno del servidor"), 500

# ===== CONFIGURACIÓN DE EVALUACIÓN SIMPLE =====
def get_configuracion_evaluacion():
    return {
        "total_preguntas": Config.TOTAL_PREGUNTAS,
        "tema_activo": get_tema_activo(),
        "archivos_temas": [f for f in os.listdir(os.path.join(os.getcwd(), 'temas')) if f.endswith('.xlsx') or f.endswith('.xls')]
    }

# ===== INICIALIZACIÓN =====

def inicializar_sistema():
    """Inicializa el sistema de evaluación"""
    logger.info("🚀 Iniciando sistema de evaluación...")
    logger.info(f"📊 Configurado para {Config.TOTAL_PREGUNTAS} preguntas")
    
    global PREGUNTAS
    PREGUNTAS = cargar_preguntas_desde_excel()
    if PREGUNTAS:
        logger.info(f"✅ Sistema listo con {len(PREGUNTAS)} preguntas cargadas")
        return True
    else:
        logger.error(f"❌ Error: No se pudieron cargar las preguntas. Verificar archivo '{Config.ARCHIVO_EXCEL}'")
        return False

# ===== PUNTO DE ENTRADA =====

if __name__ == "__main__":
    # Crear las tablas en la base de datos PostgreSQL si no existen
    with app.app_context():
        db.create_all()
    if inicializar_sistema():
        logger.info("\n🚀 SERVIDOR INICIADO")
        logger.info("=" * 50)
        logger.info(f"📊 Configuración actual: {Config.TOTAL_PREGUNTAS} preguntas máximo")
        logger.info(f"Admin: http://localhost:{Config.PORT}/admin/login")
        logger.info(f"Usuario/Pass: {Config.ADMIN_USER} / {Config.ADMIN_PASS}")
        logger.info("=" * 50)
        
        app.run(debug=Config.DEBUG, port=Config.PORT, host='0.0.0.0')
    else:
        logger.error("No se pudo iniciar el sistema debido a errores en la carga de preguntas")

# ===== VALIDADOR DE EMAIL SIMPLE =====
def validar_email_simple(email):
    import re
    if not email or '@' not in email:
        return False, 'Formato de email inválido'
    # Expresión regular básica para emails
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(regex, email):
        return False, 'Formato de email inválido'
    return True, ''