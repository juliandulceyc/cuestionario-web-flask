from flask import Flask, abort, render_template, request, jsonify, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
import os
import re
import json
import random
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import base64
from dataclasses import dataclass
from functools import wraps
from dotenv import load_dotenv
import secrets
import smtplib
from email.message import EmailMessage

# Cargar variables de entorno
load_dotenv()

# Importar módulo de seguridad
from security import (
    SecurityManager, 
    token_requerido, 
    aplicar_headers_seguridad,
    validar_entrada,
    sanitizar_entrada
)

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
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')  # Email del administrador para recuperación

    # Config SMTP
    # SMTP: limpiar espacios accidentales para evitar fallos de autenticación
    EMAIL_HOST = (os.getenv('EMAIL_HOST') or '').strip() or None
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587')) if os.getenv('EMAIL_PORT') else None
    EMAIL_USER = (os.getenv('EMAIL_USER') or '').strip() or None
    EMAIL_PASSWORD = (os.getenv('EMAIL_PASSWORD') or '').strip() or None
    EMAIL_FROM = (os.getenv('EMAIL_FROM') or EMAIL_USER or '').strip() or None
    
    # Firma de correos (personalizable por variables de entorno)
    SIGN_NAME = os.getenv('SIGN_NAME', 'Yeivi Julieth Peinado H.')
    SIGN_TITLE = os.getenv('SIGN_TITLE', 'Gerente de Servicios Ciberseguridad')
    SIGN_PHONE = os.getenv('SIGN_PHONE', '+57 3013407054')
    SIGN_LOCATION = os.getenv('SIGN_LOCATION', 'Bogotá, Colombia')
    SIGN_WEBSITE = os.getenv('SIGN_WEBSITE', 'https://www.axity.com')
    # URL pública de una imagen/banner de firma (opcional). Si está vacía no se mostrará imagen.
    SIGN_BANNER_URL = (os.getenv('SIGN_BANNER_URL') or '').strip()
    
    # Configuración de evaluación
    EVALUACION_CONFIG = {
        "total_preguntas": 40,
        "evaluacion_cada": 5,
        "min_correctas_avance": 5,  # Se necesitan 5 correctas para avanzar
        # Parámetros nuevos para la política B (no interrumpir bloque)
        "racha_para_flag": 3,                  # 3 correctas consecutivas marcan suficiencia (flag), pero no interrumpen el bloque
        "min_correctas_para_avanzar": 4,       # Suma de puntajes (parciales cuentan 0.5) necesaria para avanzar al final del bloque
        "contar_parciales_para_avance": True,  # Si True, los parciales (0.5) cuentan para la suma de avance
        "preguntas_por_nivel": 8,   # 8 preguntas por nivel
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
        "limite_preguntas_total": 40,
        "terminacion_temprana": {
            # Si se desea habilitar terminación por errores consecutivos, poner un entero >0.
            # Para comportamiento clásico (igual a FWS) poner None o 0 para deshabilitar.
            "errores_consecutivos": None,
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

# Modelo de Usuario (admins del sistema)
class UserDB(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo de Candidato
class CandidatoDB(db.Model):
    __tablename__ = 'candidatos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    tipo_documento = db.Column(db.String(10))  # CC, TI, CE, PA, etc.
    numero_documento = db.Column(db.String(50))  # Número del documento
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

# Modelo para tokens de recuperación de contraseña (single-use)
class RecoveryToken(db.Model):
    __tablename__ = 'recovery_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('UserDB')

    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at

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

# ===== ENDPOINT ACTUALIZAR CANDIDATO =====
@app.route('/admin/actualizar_candidato', methods=['POST'])
@admin_required
@handle_errors
def actualizar_candidato():
    try:
        data = request.get_json(force=True)
        codigo = (data.get('codigo') or '').strip()
        if not codigo:
            return jsonify({'error': 'Código requerido'}), 400

        candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
        if not candidato_db:
            return jsonify({'error': 'Candidato no encontrado'}), 404

        # Campos permitidos para actualización
        campos = {
            'tipo_documento': str,
            'numero_documento': str,
            'nombre_completo': str,
            'email': str,
            'telefono': str,
            'cargo': str,
        }

        # Validación básica
        email = (data.get('email') or '').strip()
        if email:
            ok, err = validar_email_simple(email)
            if not ok:
                return jsonify({'error': f'Email inválido: {err}'}), 400

        # Aplicar cambios
        for campo, tipo in campos.items():
            if campo in data and data[campo] is not None:
                valor = data[campo]
                if isinstance(valor, str):
                    valor = valor.strip()
                setattr(candidato_db, campo, valor)

        db.session.commit()

        logger.info(f"Candidato actualizado: {codigo}")
        return jsonify({
            'success': True,
            'candidato': {
                'codigo': candidato_db.codigo,
                'tipo_documento': getattr(candidato_db, 'tipo_documento', ''),
                'numero_documento': getattr(candidato_db, 'numero_documento', ''),
                'nombre_completo': candidato_db.nombre_completo,
                'email': candidato_db.email,
                'telefono': getattr(candidato_db, 'telefono', ''),
                'cargo': getattr(candidato_db, 'cargo', ''),
                'evaluacion_completada': getattr(candidato_db, 'evaluacion_completada', False)
            }
        })
    except Exception as e:
        logger.error(f"Error actualizando candidato: {e}")
        db.session.rollback()
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
    
    if not candidato_actual:
        return jsonify({"error": "No hay evaluación activa"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos JSON requeridos"}), 400
    
    # Obtener la última pregunta mostrada
    preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
    if not preguntas_mostradas:
        return jsonify({"error": "No hay pregunta activa"}), 400
    
    # La última pregunta en la lista es la que se está respondiendo
    pregunta_id = preguntas_mostradas[-1]
    pregunta = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
    
    if not pregunta:
        logger.error(f"Pregunta no encontrada. pregunta_id={pregunta_id}")
        return jsonify({"error": "Pregunta no encontrada"}), 400
    
    # Obtener respuestas del usuario (compatibilidad con diferentes formatos del frontend)
    respuestas_usuario = data.get("respuestas_seleccionadas", [])
    
    # Si no viene respuestas_seleccionadas, intentar otros campos
    if not respuestas_usuario:
        respuesta_letra = data.get("respuesta_letra", "")
        if respuesta_letra:
            # Si viene como string separado por comas, convertir a lista
            respuestas_usuario = [r.strip() for r in respuesta_letra.split(",") if r.strip()]
        else:
            respuestas_usuario = data.get("respuestas", [])
    
    # Si viene como string, convertir a lista
    if isinstance(respuestas_usuario, str):
        respuestas_usuario = [respuestas_usuario]
    
    # Logging para debug
    logger.info(f"Respuesta recibida - ID: {pregunta_id}, Respuestas: {respuestas_usuario}, Data: {data}")
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
    
    # Determinar si la respuesta es correcta (FIJACIÓN DEL CONTADOR)
    es_correcta = puntaje >= 1.0  # Solo contar como correcta si obtuvo el puntaje completo
    
    candidato_actual.setdefault("respuestas", []).append({
        "id": pregunta_id,
        "pregunta": pregunta.get("pregunta", ""),
        "respuestas": respuestas_usuario,
        "correctas": respuestas_correctas,
        "puntaje": puntaje,
        "correcta": es_correcta,  # ← AGREGAR CAMPO CORRECTA
        "nivel": pregunta.get("nivel", 1)
    })
    # Lógica adaptativa de avance de nivel
    adaptativo = candidato_actual.get("adaptativo", False)
    nivel_actual = candidato_actual.get("nivel_actual", 1)
    
    if adaptativo:
        # Solo contar si la pregunta es del nivel actual
        if pregunta.get("nivel", 1) == nivel_actual:
            candidato_actual["preguntas_nivel"] = candidato_actual.get("preguntas_nivel", 0) + 1
            if puntaje == 1:  # Respuesta completamente correcta
                candidato_actual["correctas_nivel"] = candidato_actual.get("correctas_nivel", 0) + 1
                candidato_actual["racha_actual"] = candidato_actual.get("racha_actual", 0) + 1
                # Si alcanza la racha configurada, marcar flag_racha
                racha_cfg = Config.EVALUACION_CONFIG.get("racha_para_flag", 3)
                try:
                    if candidato_actual["racha_actual"] >= int(racha_cfg):
                        candidato_actual["flag_racha"] = True
                except Exception:
                    pass
            else:
                # Caso especial: si es parcial en pregunta múltiple y viene después
                # de (racha_cfg - 1) correctas consecutivas, considerarlo como
                # cumplimiento de la racha para efectos de avance, pero sin
                # incrementar "correctas_nivel" (parcial sigue contando 0.5 en puntaje).
                racha_cfg = Config.EVALUACION_CONFIG.get("racha_para_flag", 3)
                if es_multiple and puntaje > 0 and candidato_actual.get("racha_actual", 0) >= max(0, int(racha_cfg) - 1):
                    # marcar la racha como cumplida
                    candidato_actual["racha_actual"] = candidato_actual.get("racha_actual", 0) + 1
                    candidato_actual["flag_racha"] = True
                    logger.info(f"Parcial considerado para racha: pregunta {pregunta_id}, puntaje={puntaje}, racha now={candidato_actual['racha_actual']}")
                else:
                    # si no fue completa y no entra en el caso especial, la racha se rompe
                    candidato_actual["racha_actual"] = 0

            # Sumar puntaje al acumulado del nivel y total
            candidato_actual["suma_puntaje_nivel"] = candidato_actual.get("suma_puntaje_nivel", 0.0) + float(puntaje)
            candidato_actual["suma_puntaje_total"] = candidato_actual.get("suma_puntaje_total", 0.0) + float(puntaje)
            # Actualizar contador de errores consecutivos (para terminación temprana)
            if puntaje >= 1:
                candidato_actual["errores_consecutivos"] = 0
            else:
                candidato_actual["errores_consecutivos"] = candidato_actual.get("errores_consecutivos", 0) + 1

            # Verificar regla de terminación temprana por errores consecutivos
            errores_limite = Config.EVALUACION_CONFIG.get("terminacion_temprana", {}).get("errores_consecutivos")
            if errores_limite and candidato_actual.get("errores_consecutivos", 0) >= errores_limite:
                candidato_actual["evaluacion_completa"] = True
                candidato_actual["terminacion_temprana"] = True
                candidato_actual["razon_finalizacion"] = f"Terminación temprana: {candidato_actual.get('errores_consecutivos',0)} respuestas incorrectas consecutivas en nivel {nivel_actual}"
                candidato_actual["razon_terminacion"] = candidato_actual["razon_finalizacion"]
                logger.warning(f"Evaluación terminada por errores consecutivos ({candidato_actual.get('errores_consecutivos',0)}) en nivel {nivel_actual}")
            
            # Verificar condiciones de finalización/avance al completar el bloque de preguntas del nivel
            correctas_nivel = candidato_actual.get("correctas_nivel", 0)
            preguntas_nivel = candidato_actual.get("preguntas_nivel", 0)
            preguntas_por_nivel = Config.EVALUACION_CONFIG.get("preguntas_por_nivel", 8)
            # Permitir un umbral distinto para el nivel 1 si está configurado
            if nivel_actual == 1:
                min_req = Config.EVALUACION_CONFIG.get("min_correctas_nivel_1", Config.EVALUACION_CONFIG.get("min_correctas_avance", 5))
            else:
                min_req = Config.EVALUACION_CONFIG.get("min_correctas_avance", 5)

            # Sólo decidir avance/terminación cuando se han presentado todas las preguntas del nivel
            if preguntas_nivel >= preguntas_por_nivel:
                # Para la política B: usar la suma de puntajes del nivel (parciales cuentan 0.5)
                min_req_avance = Config.EVALUACION_CONFIG.get("min_correctas_para_avanzar", 4)
                suma_puntaje = candidato_actual.get("suma_puntaje_nivel", 0.0)

                logger.info(f"Evaluando bloque nivel {nivel_actual}: suma_puntaje={suma_puntaje}, min_req={min_req_avance}, correctas_completas={correctas_nivel}")

                # Avanza si cumplió la suma mínima O si durante el bloque obtuvo la racha requerida
                flag_racha = candidato_actual.get("flag_racha", False)
                # Regla adicional: si tiene al menos 3 respuestas completamente correctas
                # (no necesariamente consecutivas) y además existe al menos un parcial
                # en el bloque (por ejemplo suma_puntaje >= 3.5), permitir avance.
                correctas_nivel = candidato_actual.get("correctas_nivel", 0)
                regla_correctas_mas_parcial = False
                try:
                    if correctas_nivel >= 3 and suma_puntaje >= 3.5:
                        regla_correctas_mas_parcial = True
                except Exception:
                    regla_correctas_mas_parcial = False

                if suma_puntaje >= float(min_req_avance) or flag_racha or regla_correctas_mas_parcial:
                    # Avanzar al siguiente nivel
                    logger.info(f"Candidato avanzó de nivel {nivel_actual} a {nivel_actual + 1} con suma_puntaje={suma_puntaje} en {preguntas_nivel} preguntas")
                    candidato_actual["nivel_actual"] += 1
                    candidato_actual["preguntas_nivel"] = 0
                    candidato_actual["correctas_nivel"] = 0
                    candidato_actual["suma_puntaje_nivel"] = 0.0
                    candidato_actual["racha_actual"] = 0
                    candidato_actual["flag_racha"] = False
                    # Resetear errores consecutivos al cambiar de nivel
                    candidato_actual["errores_consecutivos"] = 0

                    # Si alcanzó (o excedió) el nivel máximo, mantener en nivel máximo pero no terminar automáticamente
                    if candidato_actual["nivel_actual"] > Config.EVALUACION_CONFIG.get("niveles_maximos", 5):
                        candidato_actual["nivel_actual"] = Config.EVALUACION_CONFIG.get("niveles_maximos", 5)
                        logger.info("Candidato alcanzó nivel máximo; permanecerá en nivel máximo hasta completar las preguntas totales")
                else:
                    # NO terminar: en lugar de terminar, descender un nivel (si es posible) y continuar
                    logger.info(f"Candidato no alcanzó el mínimo en nivel {nivel_actual} (suma_puntaje={suma_puntaje}/{min_req_avance}). Se aplicará democión en lugar de terminar y continuará hasta completar {Config.EVALUACION_CONFIG.get('limite_preguntas_total', Config.TOTAL_PREGUNTAS)} preguntas")
                    if nivel_actual > 1:
                        nuevo_nivel = max(1, nivel_actual - 1)
                        candidato_actual["nivel_actual"] = nuevo_nivel
                        candidato_actual["preguntas_nivel"] = 0
                        candidato_actual["correctas_nivel"] = 0
                        candidato_actual["suma_puntaje_nivel"] = 0.0
                        candidato_actual["errores_consecutivos"] = 0
                        candidato_actual["demoted_times"] = candidato_actual.get("demoted_times", 0) + 1
                        logger.info(f"Candidato demotado a nivel {nuevo_nivel}. demoted_times={candidato_actual.get('demoted_times')}")
                    else:
                        # Si ya está en nivel 1, simplemente resetear contadores y continuar
                        candidato_actual["preguntas_nivel"] = 0
                        candidato_actual["correctas_nivel"] = 0
                        candidato_actual["suma_puntaje_nivel"] = 0.0
                        candidato_actual["errores_consecutivos"] = 0
                        logger.info("Candidato en nivel 1 no alcanzó mínimo; se mantiene en nivel 1 y continuará hasta completar el total de preguntas")
            else:
                # Aún quedan preguntas del nivel por mostrar; no cambiar nivel todavía
                logger.debug(f"Nivel {nivel_actual}: {correctas_nivel} correctas en {preguntas_nivel}/{preguntas_por_nivel} preguntas — esperando completar el bloque del nivel antes de decidir avance")
        else:
            # Si por alguna razón se muestra una pregunta de otro nivel, no contar
            logger.warning(f"Pregunta de nivel {pregunta.get('nivel', 1)} mostrada cuando el candidato está en nivel {nivel_actual}")
    
    # Verificar límite total de preguntas (40 preguntas máximo)
    limite_total = Config.EVALUACION_CONFIG.get("limite_preguntas_total", 40)
    if len(candidato_actual.get("preguntas_mostradas", [])) >= limite_total:
        candidato_actual["evaluacion_completa"] = True
        candidato_actual["razon_finalizacion"] = f"Límite de {limite_total} preguntas alcanzado"
    # Determinar si hay más preguntas
    preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
    total_preguntas = Config.TOTAL_PREGUNTAS
    # Si la evaluación fue marcada como completa por cualquier razón, no hay más preguntas
    hay_mas = (not candidato_actual.get("evaluacion_completa", False)) and (len(preguntas_mostradas) < total_preguntas)

    # Información adicional para el frontend
    info_nivel = {}
    if adaptativo:
        info_nivel = {
            "nivel_actual": candidato_actual.get("nivel_actual", 1),
            "preguntas_respondidas_nivel": candidato_actual.get("preguntas_nivel", 0),
            "correctas_nivel": candidato_actual.get("correctas_nivel", 0),
            "evaluacion_completa": candidato_actual.get("evaluacion_completa", False)
        }

    return jsonify({
        "success": True, 
        "hay_mas": hay_mas,
        "info_nivel": info_nivel,
        "puntaje": puntaje,
        "es_correcta": puntaje > 0
    })
@app.route('/estado_evaluacion')
@handle_errors
def estado_evaluacion():
    """Obtiene el estado actual de la evaluación"""
    if not candidato_actual:
        return jsonify({"error": "No hay evaluación activa"}), 400
    
    adaptativo = candidato_actual.get("adaptativo", False)
    
    estado = {
        "candidato": candidato_actual.get("datos_personales", {}),
        "preguntas_respondidas": len(candidato_actual.get("preguntas_mostradas", [])),
        "total_preguntas": Config.TOTAL_PREGUNTAS,
        "puntos_totales": candidato_actual.get("puntos", 0),
        "evaluacion_completa": candidato_actual.get("evaluacion_completa", False),
        "adaptativo": adaptativo
    }
    
    if adaptativo:
        estado.update({
            "nivel_actual": candidato_actual.get("nivel_actual", 1),
            "preguntas_nivel_actual": candidato_actual.get("preguntas_nivel", 0),
            "correctas_nivel_actual": candidato_actual.get("correctas_nivel", 0),
            "necesitas_para_avanzar": max(0, 5 - candidato_actual.get("correctas_nivel", 0)),
            "preguntas_restantes_nivel": max(0, 8 - candidato_actual.get("preguntas_nivel", 0))
        })
    
    return jsonify(estado)

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
    # Si no hay usuarios, iniciar flujo de primer usuario
    try:
        if UserDB.query.count() == 0:
            return redirect(url_for('first_run_register'))
    except Exception:
        pass
    return redirect(url_for('admin_login'))

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/authenticate', methods=['POST'])
@handle_errors
def admin_authenticate():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # 1) Intentar con usuarios en BD
    user = UserDB.query.filter((UserDB.username==username)).first()
    if user and user.is_active and SecurityManager.verificar_password(password, user.password_hash):
        session['admin_logged_in'] = True
        session['admin_username'] = user.username
        session['admin_user_id'] = user.id
        tokens = SecurityManager.generar_token(usuario_id=user.username, rol=user.role or 'admin')
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens['refresh_token']
        session['token_expires_at'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        logger.info(f"Admin login (BD) exitoso: {user.username}")
        return redirect(url_for('admin_dashboard'))

    # 2) Fallback: admin legacy por Config si no hay usuarios en BD
    if UserDB.query.count() == 0 and username == Config.ADMIN_USER and password == Config.ADMIN_PASS:
        session['admin_logged_in'] = True
        session['admin_username'] = username
        session['admin_user_id'] = 0
        
        # Generar token JWT para APIs
        tokens = SecurityManager.generar_token(usuario_id=username, rol='admin')
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens['refresh_token']
        session['token_expires_at'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        
        logger.info(f"Admin login (legacy) exitoso: {username} - Token generado")
        return redirect(url_for('admin_dashboard'))
    else:
        logger.warning(f"Intento de login fallido: {username}")
        return render_template('admin_login.html', error="Credenciales incorrectas")


# ===== RENOVACIÓN DE TOKEN JWT =====
@app.route('/api/renovar-token', methods=['POST'])
@handle_errors
def renovar_token():
    """Endpoint para renovar el token de acceso cada 15 minutos"""
    refresh_token = request.json.get('refresh_token') or session.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token no proporcionado'}), 401
    
    try:
        nuevos_tokens = SecurityManager.renovar_token(refresh_token)
        
        # Actualizar sesión
        session['access_token'] = nuevos_tokens['access_token']
        session['token_expires_at'] = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        
        logger.info("Token renovado exitosamente")
        
        return jsonify({
            'success': True,
            'access_token': nuevos_tokens['access_token'],
            'expires_in': nuevos_tokens['expires_in'],
            'renewed_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error renovando token: {e}")
        return jsonify({'error': 'Error renovando token', 'message': str(e)}), 401


# ===== UTILIDADES DE EMAIL =====
def validar_email_simple(email):
    """Valida formato básico de email: contiene @ y cumple una regex simple.
    Retorna (True, '') si es válido; (False, 'motivo') si no lo es.
    """
    import re as _re
    if not email or '@' not in email:
        return False, 'Formato de email inválido'
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not _re.match(regex, email):
        return False, 'Formato de email inválido'
    return True, ''

def enviar_email(destinatario: str, asunto: str, cuerpo_texto: str, cuerpo_html: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Envía un email simple usando configuración SMTP.
    Retorna (True, None) si se envió; (False, 'motivo') si falló.
    """
    try:
        if not (Config.EMAIL_HOST and Config.EMAIL_PORT and Config.EMAIL_FROM):
            logger.warning("SMTP no configurado correctamente. EMAIL_HOST/PORT/FROM faltantes")
            return False, "SMTP no configurado (falta HOST/PORT/FROM)"
        msg = EmailMessage()
        msg['Subject'] = asunto
        msg['From'] = Config.EMAIL_FROM
        msg['To'] = destinatario
        msg.set_content(cuerpo_texto)
        if cuerpo_html:
            msg.add_alternative(cuerpo_html, subtype='html')

        if str(Config.EMAIL_PORT) == '465':
            # SSL implícito
            with smtplib.SMTP_SSL(Config.EMAIL_HOST, Config.EMAIL_PORT, timeout=20) as smtp:
                try:
                    if Config.DEBUG:
                        smtp.set_debuglevel(1)
                except Exception:
                    pass
                if Config.EMAIL_USER and Config.EMAIL_PASSWORD:
                    smtp.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            # STARTTLS (por defecto 587)
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT, timeout=20) as smtp:
                try:
                    if Config.DEBUG:
                        smtp.set_debuglevel(1)
                except Exception:
                    pass
                smtp.starttls()
                if Config.EMAIL_USER and Config.EMAIL_PASSWORD:
                    smtp.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                smtp.send_message(msg)
        logger.info(f"Email enviado a {destinatario} usando {Config.EMAIL_HOST}:{Config.EMAIL_PORT} como {Config.EMAIL_FROM}")
        return True, None
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False, str(e)

# ===== RECUPERACIÓN DE CONTRASEÑA =====

@app.route('/admin/recuperar-password', methods=['GET', 'POST'])
@handle_errors
def recuperar_password():
    """Solicitar enlace de recuperación de contraseña (envío por email). Acepta usuario o email."""
    if request.method == 'GET':
        return render_template('recuperar_password.html')

    identifier = request.form.get('username', '').strip()

    if not identifier:
        return render_template('recuperar_password.html', error="Usuario o email requerido")

    # Buscar usuario por username o email
    user = UserDB.query.filter((UserDB.username==identifier) | (UserDB.email==identifier)).first()
    if not user:
        logger.warning(f"Intento de recuperación para usuario inexistente: {identifier}")
        return render_template('recuperar_password.html', error="El usuario o correo no existe en el sistema.")

    # Generar token aleatorio single-use y guardarlo con expiración
    token = secrets.token_urlsafe(32)
    expira = datetime.utcnow() + timedelta(minutes=30)
    try:
        rec = RecoveryToken(user_id=user.id, token=token, expires_at=expira)
        db.session.add(rec)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error guardando RecoveryToken: {e}")
        db.session.rollback()
        return render_template('recuperar_password.html', error="No se pudo generar el enlace de recuperación. Intenta más tarde.")

    # Construir enlace absoluto
    try:
        base_url = request.host_url.rstrip('/')
        reset_link = f"{base_url}/admin/restablecer-password?token={token}"
    except Exception:
        reset_link = f"/admin/restablecer-password?token={token}"

    # Enviar email al usuario (usando plantillas con firma)
    asunto = "Instrucciones para restablecer tu contraseña"
    # Plantillas TXT y HTML con firma personalizable
    texto = render_template(
        'email/reset_password.txt',
        reset_link=reset_link,
        nombre=Config.SIGN_NAME,
        cargo=Config.SIGN_TITLE,
        telefono=Config.SIGN_PHONE,
        ubicacion=Config.SIGN_LOCATION,
        sitio_web=Config.SIGN_WEBSITE,
    )
    html = render_template(
        'email/reset_password.html',
        reset_link=reset_link,
        nombre=Config.SIGN_NAME,
        cargo=Config.SIGN_TITLE,
        telefono=Config.SIGN_PHONE,
        ubicacion=Config.SIGN_LOCATION,
        sitio_web=Config.SIGN_WEBSITE,
        banner_url=Config.SIGN_BANNER_URL,
    )

    enviado, error_envio = enviar_email(user.email, asunto, texto, html)
    if not enviado:
        logger.error("Fallo el envío de email de recuperación al usuario.")
        # En modo DEBUG, muestra un mensaje más detallado para facilitar diagnóstico
        if Config.DEBUG and error_envio:
            return render_template('recuperar_password.html', error=f"No se pudo enviar el correo de recuperación. Detalle: {error_envio}")
        return render_template('recuperar_password.html', error="No se pudo enviar el correo de recuperación. Verifica la configuración SMTP o intenta más tarde.")
    else:
        logger.info(f"Email de recuperación enviado a {user.email}")
        return render_template('recuperar_password.html', mensaje_exito=f"Enviamos un enlace de recuperación a: {user.email}")


@app.route('/admin/restablecer-password', methods=['GET'])
@handle_errors
def mostrar_form_restablecer_password():
    """Muestra el formulario de restablecimiento si el token es válido (no consumido aún)."""
    token = request.args.get('token', '').strip()
    if not token:
        return redirect(url_for('recuperar_password'))

    rec = RecoveryToken.query.filter_by(token=token).first()
    if not rec or rec.used or rec.is_expired():
        return render_template('recuperar_password.html', error="Enlace inválido o expirado. Solicita uno nuevo.")

    return render_template('restablecer_password.html', token=token)


@app.route('/admin/restablecer-password', methods=['POST'])
@handle_errors
def restablecer_password():
    """Restablecer contraseña a partir de un token enviado por email"""
    token = request.form.get('token', '').strip()
    nueva_password = request.form.get('nueva_password')
    confirmar_password = request.form.get('confirmar_password')

    if not all([token, nueva_password, confirmar_password]):
        return render_template('restablecer_password.html', token=token, error="Todos los campos son requeridos")

    if nueva_password != confirmar_password:
        return render_template('restablecer_password.html', token=token, error="Las contraseñas no coinciden")

    if len(nueva_password) < 6:
        return render_template('restablecer_password.html', token=token, error="La contraseña debe tener al menos 6 caracteres")

    rec = RecoveryToken.query.filter_by(token=token).first()
    if not rec or rec.used or rec.is_expired():
        return render_template('recuperar_password.html', error="Enlace inválido o expirado. Solicita uno nuevo.")

    try:
        # Actualizar contraseña del usuario
        user = UserDB.query.get(rec.user_id)
        if not user or not user.is_active:
            return render_template('recuperar_password.html', error="Usuario inválido. Solicita un nuevo enlace.")
        user.password_hash = SecurityManager.hash_password(nueva_password)

        # Marcar token como usado
        rec.used = True
        db.session.commit()

        logger.info(f"Contraseña restablecida exitosamente para usuario_id: {rec.user_id}")
        return render_template('admin_login.html', error="✅ Contraseña cambiada exitosamente. Por favor, inicia sesión.")
    except Exception as e:
        logger.error(f"Error restableciendo contraseña: {e}")
        db.session.rollback()
        return render_template('restablecer_password.html', token=token, error="Error al restablecer contraseña")


# ===== Bootstrap de primer usuario (solo si no hay usuarios) =====
@app.route('/admin/first-run', methods=['GET', 'POST'])
def first_run_register():
    # Si ya existe algún usuario, redirigir al login
    if UserDB.query.count() > 0:
        return redirect(url_for('admin_login'))

    if request.method == 'GET':
        return render_template('admin_register.html')

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm', '')

    if not all([username, email, password, confirm]):
        return render_template('admin_register.html', error='Todos los campos son requeridos')
    if password != confirm:
        return render_template('admin_register.html', error='Las contraseñas no coinciden')
    if len(password) < 6:
        return render_template('admin_register.html', error='La contraseña debe tener al menos 6 caracteres')

    try:
        if UserDB.query.filter((UserDB.username==username) | (UserDB.email==email)).first():
            return render_template('admin_register.html', error='Usuario o email ya existe')
        u = UserDB(
            username=username,
            email=email,
            password_hash=SecurityManager.hash_password(password),
            role='admin',
            is_active=True,
        )
        db.session.add(u)
        db.session.commit()
        logger.info(f"Primer usuario creado: {username}")
        return redirect(url_for('admin_login'))
    except Exception as e:
        logger.error(f"Error creando primer usuario: {e}")
        db.session.rollback()
        return render_template('admin_register.html', error='Error creando usuario')


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
                "tipo_documento": getattr(candidato, "tipo_documento", ""),
                "numero_documento": getattr(candidato, "numero_documento", ""),
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
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
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
            "nivel_actual": 1,
            "puntos": 0,
            "preguntas_mostradas": [],
            "evaluacion_completa": False,
            "respuestas": [],
            # Contadores adaptativos por nivel
            "preguntas_nivel": 0,
            "correctas_nivel": 0,
            "suma_puntaje_nivel": 0.0,
            "suma_puntaje_total": 0.0,
            "racha_actual": 0,
            "flag_racha": False,
            "demoted_times": 0,
            "errores_consecutivos": 0,
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

        # Verificar disponibilidad de preguntas y configurar modo adaptativo
        global PREGUNTAS
        PREGUNTAS = cargar_preguntas_desde_excel()
        
        # Agrupar preguntas por nivel para verificar disponibilidad
        preguntas_por_nivel = {}
        for p in PREGUNTAS:
            nivel = p.get("nivel", 1)
            preguntas_por_nivel.setdefault(nivel, []).append(p["id"])

        # Verificar disponibilidad por nivel y rechazar inicio si hay niveles incompletos
        required_per_level = Config.EVALUACION_CONFIG.get("preguntas_por_nivel", 8)
        max_nivel = Config.EVALUACION_CONFIG.get("niveles_maximos", 5)
        niveles_faltantes = {}
        for lvl in range(1, max_nivel + 1):
            cnt = len(preguntas_por_nivel.get(lvl, []))
            if cnt < required_per_level:
                niveles_faltantes[lvl] = cnt
        if niveles_faltantes:
            # Bloquear inicio y comunicar qué niveles están incompletos
            mensaje = {
                "error": "Banco de preguntas incompleto",
                "detalle": {
                    "requeridas_por_nivel": required_per_level,
                    "niveles_disponibles": {str(k): len(v) for k, v in preguntas_por_nivel.items()},
                    "niveles_faltantes": niveles_faltantes
                },
                "accion_sugerida": "Agregar preguntas faltantes al archivo de preguntas o ajustar Config.EVALUACION_CONFIG['preguntas_por_nivel']"
            }
            logger.warning(f"Intento de iniciar evaluación pero banco incompleto: {niveles_faltantes}")
            return jsonify(mensaje), 400

        # Verificar si hay suficientes preguntas para modo adaptativo
        # Necesitamos al menos `required_per_level` preguntas en el nivel 1 para empezar
        nivel_1_disponibles = len(preguntas_por_nivel.get(1, []))
        adaptativo = nivel_1_disponibles >= required_per_level
        
        if adaptativo:
            # Modo adaptativo: las preguntas se seleccionan dinámicamente
            candidato_actual["adaptativo"] = True
            candidato_actual["orden_preguntas"] = []  # No se usa en modo adaptativo
            logger.info(f"Modo adaptativo activado. Preguntas por nivel: {[(k, len(v)) for k, v in preguntas_por_nivel.items()]}")
        else:
            # Modo secuencial: usar todas las preguntas disponibles
            candidato_actual["adaptativo"] = False
            orden_preguntas = []
            for nivel in sorted(preguntas_por_nivel.keys()):
                ids = preguntas_por_nivel[nivel]
                random.shuffle(ids)  # Mezclar preguntas del mismo nivel
                orden_preguntas.extend(ids)
            candidato_actual["orden_preguntas"] = orden_preguntas
            logger.info(f"Modo secuencial activado. Total preguntas: {len(orden_preguntas)}")
        
        # Inicializar variables de control adaptativo
        candidato_actual["nivel_actual"] = 1
        candidato_actual["correctas_nivel"] = 0
        candidato_actual["preguntas_nivel"] = 0
        candidato_actual["intentos_nivel"] = 0  # Contador de intentos por nivel
        # Contador de errores consecutivos para terminación temprana
        candidato_actual["errores_consecutivos"] = 0
        candidato_actual["razon_terminacion"] = ""
        logger.info(f"Evaluación iniciada para: {candidato_encontrado['nombre_completo']}")
        return jsonify({"mensaje": "Evaluación iniciada correctamente"})
    else:
        logger.warning(f"Candidato no encontrado: {documento}")
        return jsonify({"error": "Candidato no registrado"}), 404

@app.route('/obtener_pregunta')
@handle_errors
def obtener_pregunta():
    """Obtiene la siguiente pregunta para el candidato con lógica adaptativa real"""
    # Recargar preguntas en tiempo real desde el Excel
    global PREGUNTAS
    PREGUNTAS = cargar_preguntas_desde_excel()
    if not candidato_actual or len(PREGUNTAS) == 0:
        return jsonify({"error": "Evaluación no iniciada"}), 400
    
    preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
    adaptativo = candidato_actual.get("adaptativo", False)
    nivel_actual = candidato_actual.get("nivel_actual", 1)
    preguntas_nivel_actual = candidato_actual.get("preguntas_nivel", 0)
    
    # Verificar si ya completó la evaluación
    if candidato_actual.get("evaluacion_completa", False):
        return jsonify({"error": "Evaluación completada"})
    
    # Verificar si ya alcanzó el nivel máximo y completó las 8 preguntas
    if nivel_actual > 5:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "Evaluación completada - Nivel máximo alcanzado"})
    
    # Verificar límite total de preguntas (40 preguntas máximo)
    limite_total = Config.EVALUACION_CONFIG.get("limite_preguntas_total", 40)
    if len(preguntas_mostradas) >= limite_total:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": f"Evaluación completada - Máximo de {limite_total} preguntas alcanzado"})

    if adaptativo:
        # LÓGICA ADAPTATIVA REAL: Seleccionar pregunta del nivel actual
        preguntas_disponibles = [
            p for p in PREGUNTAS 
            if p["id"] not in preguntas_mostradas 
            and p.get("nivel", 1) == nivel_actual
        ]
        
        if not preguntas_disponibles:
            # Si no hay más preguntas del nivel actual, aplicar fallback preferente:
            # 1) buscar preguntas de niveles inferiores (más cercanos primero)
            # 2) si no hay, buscar preguntas de niveles superiores (más cercanos primero)
            candidatos = []
            max_nivel = Config.EVALUACION_CONFIG.get("niveles_maximos", 5)
            # buscar niveles inferiores
            for lvl in range(nivel_actual - 1, 0, -1):
                candidatos = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p.get("nivel", 1) == lvl]
                if candidatos:
                    logger.info(f"Fallback: no hay preguntas nivel {nivel_actual}, usando nivel inferior {lvl}")
                    break

            # si no hay en niveles inferiores, buscar superiores
            if not candidatos:
                for lvl in range(nivel_actual + 1, max_nivel + 1):
                    candidatos = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p.get("nivel", 1) == lvl]
                    if candidatos:
                        logger.info(f"Fallback: no hay preguntas nivel {nivel_actual}, usando nivel superior {lvl}")
                        break

            if not candidatos:
                candidato_actual["evaluacion_completa"] = True
                return jsonify({"error": "No hay más preguntas disponibles"})

            # Seleccionar una pregunta aleatoria de los candidatos encontrados
            pregunta_seleccionada = random.choice(candidatos)
        else:
            # Seleccionar una pregunta aleatoria del nivel actual
            pregunta_seleccionada = random.choice(preguntas_disponibles)
        
    else:
        # Modo no adaptativo (uso del orden predeterminado)
        orden_preguntas = candidato_actual.get("orden_preguntas", [])
        pregunta_numero = len(preguntas_mostradas)
        
        if pregunta_numero >= len(orden_preguntas):
            candidato_actual["evaluacion_completa"] = True
            return jsonify({"error": "No hay más preguntas disponibles"})
            
        pregunta_id = orden_preguntas[pregunta_numero]
        pregunta_seleccionada = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
        
        if not pregunta_seleccionada:
            candidato_actual["evaluacion_completa"] = True
            return jsonify({"error": "Pregunta no encontrada"})
    
    # Registrar la pregunta mostrada
    candidato_actual["preguntas_mostradas"].append(pregunta_seleccionada["id"])
    candidato_actual["pregunta_actual_nivel"] = pregunta_seleccionada.get("nivel", 1)

    return jsonify({
        "id": pregunta_seleccionada["id"],
        "pregunta": pregunta_seleccionada["pregunta"],
        "opciones": pregunta_seleccionada["opciones"],
        "imagen": pregunta_seleccionada.get("imagen"),
        "pregunta_numero": len(candidato_actual["preguntas_mostradas"]),
        "total_preguntas": Config.TOTAL_PREGUNTAS,
        "multiple": pregunta_seleccionada.get("multiple", False),
        "respuestas_correctas_count": len(pregunta_seleccionada.get("respuestas_correctas", [])),
        "nivel_actual": nivel_actual,
        "preguntas_del_nivel": preguntas_nivel_actual + 1,
        "correctas_nivel": candidato_actual.get("correctas_nivel", 0)
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
    max_nivel = Config.EVALUACION_CONFIG.get("niveles_maximos", 5)
    # Preferir niveles inferiores (más cercanos) primero
    for lvl in range(nivel_busqueda - 1, 0, -1):
        preguntas_alt = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p.get("nivel", 1) == lvl]
        if preguntas_alt:
            logger.info(f"Fallback helper: usando nivel inferior {lvl} para búsqueda desde {nivel_busqueda}")
            return preguntas_alt
    # Si no hay, buscar niveles superiores (más cercanos primero)
    for lvl in range(nivel_busqueda + 1, max_nivel + 1):
        preguntas_alt = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p.get("nivel", 1) == lvl]
        if preguntas_alt:
            logger.info(f"Fallback helper: usando nivel superior {lvl} para búsqueda desde {nivel_busqueda}")
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
                    nivel_final=candidato_actual.get("nivel_actual", 1),
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
            # Nivel final alcanzado; prioriza el nivel_actual, cae a nivel_final almacenado y por defecto 1
            "nivel_final": candidato_actual.get("nivel_actual", candidato_actual.get("nivel_final", 1)),
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

# ===== MIDDLEWARES DE SEGURIDAD =====
@app.after_request
def aplicar_seguridad(response):
    """Aplica headers de seguridad HTTP a todas las respuestas"""
    return aplicar_headers_seguridad(response)


@app.before_request
def verificar_expiracion_token():
    """Verifica si el token está próximo a expirar y notifica al cliente"""
    if 'admin_logged_in' in session and 'token_expires_at' in session:
        try:
            expires_at = datetime.fromisoformat(session['token_expires_at'])
            tiempo_restante = (expires_at - datetime.utcnow()).total_seconds()
            
            # Si quedan menos de 5 minutos, agregar header para renovar
            if tiempo_restante < 300 and tiempo_restante > 0:
                request.debe_renovar_token = True
                
            # Si ya expiró, cerrar sesión
            if tiempo_restante <= 0:
                logger.warning("Token expirado - cerrando sesión")
                session.clear()
                
        except Exception as e:
            logger.error(f"Error verificando expiración de token: {e}")


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

def seed_or_update_admin_user(admin_email: str):
    """Crea o actualiza el usuario 'admin' con el email proporcionado.
    Si no existe, lo crea con la contraseña de Config.ADMIN_PASS.
    """
    try:
        admin_username = Config.ADMIN_USER
        user = UserDB.query.filter_by(username=admin_username).first()
        if user:
            if admin_email and user.email != admin_email:
                # Verificar conflicto de email
                if UserDB.query.filter((UserDB.email==admin_email) & (UserDB.id!=user.id)).first():
                    logger.warning(f"No se puede asignar email {admin_email} al usuario admin: ya está en uso.")
                else:
                    user.email = admin_email
                    db.session.commit()
                    logger.info(f"Email del admin actualizado a {admin_email}")
        else:
            if not admin_email:
                logger.warning("ADMIN_EMAIL vacío; no se crea usuario admin en BD")
                return
            if UserDB.query.filter_by(email=admin_email).first():
                logger.warning(f"No se crea usuario admin: email {admin_email} ya está en uso por otro usuario")
                return
            pwd_hash = SecurityManager.hash_password(Config.ADMIN_PASS)
            new_admin = UserDB(
                username=admin_username,
                email=admin_email,
                password_hash=pwd_hash,
                role='admin',
                is_active=True,
            )
            db.session.add(new_admin)
            db.session.commit()
            logger.info(f"Usuario admin creado con email {admin_email}")
    except Exception as e:
        logger.error(f"Error en seed_or_update_admin_user: {e}")
        db.session.rollback()

if __name__ == "__main__":
    # Crear las tablas en la base de datos PostgreSQL si no existen
    with app.app_context():
        # Verificar/migrar esquema simple de recovery_tokens si quedó antiguo
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'recovery_tokens' in tables:
                cols = [col['name'] for col in inspector.get_columns('recovery_tokens')]
                # Si encontramos 'username' y no 'user_id', dropeamos la tabla para recrearla correctamente
                if ('username' in cols) and ('user_id' not in cols):
                    logger.warning("Esquema antiguo de recovery_tokens detectado. Eliminando tabla para recrear correctamente...")
                    with db.engine.begin() as conn:
                        conn.execute(text('DROP TABLE recovery_tokens'))
                    logger.info("Tabla recovery_tokens eliminada. Será recreada por create_all().")
        except Exception as e:
            logger.error(f"Error verificando esquema de recovery_tokens: {e}")
        db.create_all()
        # Asignar email al usuario admin por solicitud
        seed_or_update_admin_user('brad.castellanos@axity.com')
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