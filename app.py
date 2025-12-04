from flask import Flask, abort, render_template, request, jsonify, redirect, url_for, session, make_response
import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional, Any
import secrets
from functools import wraps

from dotenv import load_dotenv

# Constants for templates
TEMPLATE_ADMIN_LOGIN = 'admin_login.html'
TEMPLATE_RECUPERAR_PASSWORD = 'recuperar_password.html'
TEMPLATE_RESTABLECER_PASSWORD = 'restablecer_password.html'
TEMPLATE_ADMIN_REGISTER = 'admin_register.html'
TEMPLATE_ADMIN_DASHBOARD = 'admin_dashboard.html'
TEMPLATE_ERROR = 'error.html'

# Importar módulos refactorizados
from config import Config
from extensions import db
from models import UserDB, CandidatoDB, ResultadoDB, RecoveryToken
from shared import candidatos_registrados, candidato_actual, PREGUNTAS
from utils import (
    setup_logging, 
    validar_email_simple, 
    enviar_email, 
    get_tema_activo, 
    cargar_preguntas_desde_excel, 
    registrar_candidato_simple, 
    seed_or_update_admin_user,
    _actualizar_candidato_final
)
from services import EvaluacionService
from security import (
    SecurityManager, 
    token_requerido, 
    aplicar_headers_seguridad,
    handle_errors
)

# Cargar variables de entorno
load_dotenv()

# Importar generador de PDF si está disponible
try:
    from pdf_generator import generar_pdf_evaluacion
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    generar_pdf_evaluacion = None
    logging.warning("Generador de PDF no disponible")

# Importar integración con Drive si está disponible
try:
    from drive_integration import save_pdf_to_drive
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False
    save_pdf_to_drive = None
    logging.warning("Integración con Drive no disponible")

# Configurar logging
logger = setup_logging()

# Inicializar Flask
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS

# Inicializar extensiones
db.init_app(app)

# ===== DECORADORES =====
def admin_required(f):
    """Decorador para rutas que requieren autenticación admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ===== RUTAS PRINCIPALES =====

@app.route('/')
def home():
    # Si no hay usuarios, iniciar flujo de primer usuario
    try:
        if UserDB.query.count() == 0:
            return redirect(url_for('first_run_register'))
    except Exception as e:
        logger.warning(f"Error verificando usuarios iniciales: {e}")
    return redirect(url_for('admin_login'))

@app.route('/admin/login')
def admin_login():
    return render_template(TEMPLATE_ADMIN_LOGIN)

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
        session['token_expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
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
        session['token_expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        
        logger.info(f"Admin login (legacy) exitoso: {username} - Token generado")
        return redirect(url_for('admin_dashboard'))
    else:
        logger.warning(f"Intento de login fallido: {username}")
        return render_template(TEMPLATE_ADMIN_LOGIN, error="Credenciales incorrectas")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    logger.info("Admin logout")
    return redirect(url_for('admin_login'))

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
        session['token_expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        
        logger.info("Token renovado exitosamente")
        
        return jsonify({
            'success': True,
            'access_token': nuevos_tokens['access_token'],
            'expires_in': nuevos_tokens['expires_in'],
            'renewed_at': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Error renovando token: {e}")
        return jsonify({'error': 'Error renovando token', 'message': str(e)}), 401

# ===== RECUPERACIÓN DE CONTRASEÑA =====

@app.route('/admin/recuperar-password', methods=['GET', 'POST'])
@handle_errors
def recuperar_password():
    """Solicitar enlace de recuperación de contraseña (envío por email). Acepta usuario o email."""
    if request.method == 'GET':
        return render_template(TEMPLATE_RECUPERAR_PASSWORD)

    identifier = request.form.get('username', '').strip()

    if not identifier:
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="Usuario o email requerido")

    # Buscar usuario por username o email
    user = UserDB.query.filter((UserDB.username==identifier) | (UserDB.email==identifier)).first()
    if not user:
        logger.warning(f"Intento de recuperación para usuario inexistente: {identifier}")
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="El usuario o correo no existe en el sistema.")

    # Generar token aleatorio single-use y guardarlo con expiración
    token = secrets.token_urlsafe(32)
    expira = datetime.now(timezone.utc) + timedelta(minutes=30)
    try:
        rec = RecoveryToken(user_id=user.id, token=token, expires_at=expira)
        db.session.add(rec)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error guardando RecoveryToken: {e}")
        db.session.rollback()
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="No se pudo generar el enlace de recuperación. Intenta más tarde.")

    # Construir enlace absoluto
    try:
        base_url = request.host_url.rstrip('/')
        reset_link = f"{base_url}/admin/restablecer-password?token={token}"
    except Exception as e:
        logger.warning(f"Error construyendo URL absoluta: {e}")
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
            return render_template(TEMPLATE_RECUPERAR_PASSWORD, error=f"No se pudo enviar el correo de recuperación. Detalle: {error_envio}")
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="No se pudo enviar el correo de recuperación. Verifica la configuración SMTP o intenta más tarde.")
    else:
        logger.info(f"Email de recuperación enviado a {user.email}")
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, mensaje_exito=f"Enviamos un enlace de recuperación a: {user.email}")


@app.route('/admin/restablecer-password', methods=['GET'])
@handle_errors
def mostrar_form_restablecer_password():
    """Muestra el formulario de restablecimiento si el token es válido (no consumido aún)."""
    token = request.args.get('token', '').strip()
    if not token:
        return redirect(url_for('recuperar_password'))

    rec = RecoveryToken.query.filter_by(token=token).first()
    if not rec or rec.used or rec.is_expired():
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="Enlace inválido o expirado. Solicita uno nuevo.")

    return render_template(TEMPLATE_RESTABLECER_PASSWORD, token=token)


@app.route('/admin/restablecer-password', methods=['POST'])
@handle_errors
def restablecer_password():
    """Restablecer contraseña a partir de un token enviado por email"""
    token = request.form.get('token', '').strip()
    nueva_password = request.form.get('nueva_password')
    confirmar_password = request.form.get('confirmar_password')

    if not all([token, nueva_password, confirmar_password]):
        return render_template(TEMPLATE_RESTABLECER_PASSWORD, token=token, error="Todos los campos son requeridos")

    if nueva_password != confirmar_password:
        return render_template(TEMPLATE_RESTABLECER_PASSWORD, token=token, error="Las contraseñas no coinciden")

    if len(nueva_password) < 6:
        return render_template(TEMPLATE_RESTABLECER_PASSWORD, token=token, error="La contraseña debe tener al menos 6 caracteres")

    rec = RecoveryToken.query.filter_by(token=token).first()
    if not rec or rec.used or rec.is_expired():
        return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="Enlace inválido o expirado. Solicita uno nuevo.")

    try:
        # Actualizar contraseña del usuario
        user = UserDB.query.get(rec.user_id)
        if not user or not user.is_active:
            return render_template(TEMPLATE_RECUPERAR_PASSWORD, error="Usuario inválido. Solicita un nuevo enlace.")
        user.password_hash = SecurityManager.hash_password(nueva_password)

        # Marcar token como usado
        rec.used = True
        db.session.commit()

        logger.info(f"Contraseña restablecida exitosamente para usuario_id: {rec.user_id}")
        return render_template(TEMPLATE_ADMIN_LOGIN, error="✅ Contraseña cambiada exitosamente. Por favor, inicia sesión.")
    except Exception as e:
        logger.error(f"Error restableciendo contraseña: {e}")
        db.session.rollback()
        return render_template(TEMPLATE_RESTABLECER_PASSWORD, token=token, error="Error al restablecer contraseña")

# ===== Bootstrap de primer usuario (solo si no hay usuarios) =====
@app.route('/admin/first-run', methods=['GET', 'POST'])
def first_run_register():
    # Si ya existe algún usuario, redirigir al login
    if UserDB.query.count() > 0:
        return redirect(url_for('admin_login'))

    if request.method == 'GET':
        return render_template(TEMPLATE_ADMIN_REGISTER)

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm', '')

    if not all([username, email, password, confirm]):
        return render_template(TEMPLATE_ADMIN_REGISTER, error='Todos los campos son requeridos')
    if password != confirm:
        return render_template(TEMPLATE_ADMIN_REGISTER, error='Las contraseñas no coinciden')
    if len(password) < 6:
        return render_template(TEMPLATE_ADMIN_REGISTER, error='La contraseña debe tener al menos 6 caracteres')

    try:
        if UserDB.query.filter((UserDB.username==username) | (UserDB.email==email)).first():
            return render_template(TEMPLATE_ADMIN_REGISTER, error='Usuario o email ya existe')
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
        return render_template(TEMPLATE_ADMIN_REGISTER, error='Error creando usuario')

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
    return render_template(TEMPLATE_ADMIN_DASHBOARD, candidatos=candidatos_db, resultados=resultados_dict, tema_activo=tema_activo)

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
            try:
                url_eval = url_for('evaluacion', codigo=candidato.codigo, _external=True)
            except Exception as e:
                logger.warning(f"Error generando URL para candidato {candidato.codigo}: {e}")
                url_eval = f"/evaluacion/{candidato.codigo}"
            candidatos_list.append({
                "codigo": candidato.codigo,
                "tipo_documento": getattr(candidato, "tipo_documento", ""),
                "numero_documento": getattr(candidato, "numero_documento", ""),
                "nombre_completo": candidato.nombre_completo,
                "email": candidato.email,
                "telefono": getattr(candidato, "telefono", ""),
                "cargo": getattr(candidato, "cargo", ""),
                "evaluacion_completada": getattr(candidato, "evaluacion_completada", False),
                "url_evaluacion": url_eval
            })
        return jsonify(candidatos_list)
    
    candidatos_db = CandidatoDB.query.all()
    return render_template('panel_admin.html', candidatos=candidatos_db)

def _registrar_candidato_json(data):
    tipo_documento = data.get('tipo_documento', '').strip()
    numero_documento = data.get('numero_documento', '').strip()
    nombre = data.get('nombre_completo', '').strip()
    email = data.get('email', '').strip()
    cargo = data.get('cargo', '').strip()
    tema = data.get('tema', '').strip()
    
    try:
        candidato = registrar_candidato_simple(tipo_documento, numero_documento, nombre, email, cargo, tema)
        _guardar_candidato_db(candidato, tipo_documento, numero_documento, nombre, email, cargo, tema)
        return jsonify({"success": True, "candidato": candidato})
    except Exception as e:
        logger.error(f"Error registrando candidato (JSON): {e}")
        return jsonify({'error': "Error interno al registrar candidato"}), 500

def _guardar_candidato_db(candidato, tipo_documento, numero_documento, nombre, email, cargo, tema):
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

def _registrar_candidato_form(form):
    validation_errors = []
    email = form.get('email', '').strip()
    numero_documento = form.get('numero_documento', '').strip()
    
    valid_email, email_error = validar_email_simple(email)
    if not valid_email:
        validation_errors.append(f"Email: {email_error}")
    
    # Verificar duplicados
    for candidato in candidatos_registrados.values():
        if candidato.get('numero_documento', '').lower() == numero_documento.lower():
            validation_errors.append('Ya existe un candidato con este número de documento')
            break
        if candidato['email'].lower() == email.lower():
            validation_errors.append('Ya existe un candidato con este email')
            break
            
    if validation_errors:
        error_msg = '; '.join(validation_errors)
        logger.warning(f"Errores de validación (Form): {error_msg}")
        return render_template(TEMPLATE_ADMIN_DASHBOARD, error=error_msg)
            
    try:
        registrar_candidato_simple(
            form.get('tipo_documento', '').strip(),
            numero_documento,
            form.get('nombre_completo', '').strip(),
            email,
            form.get('cargo', '').strip(),
            form.get('tema', '').strip()
        )
        return redirect(url_for('admin_candidatos'))
    except Exception as e:
        logger.error(f"Error registrando candidato (Form): {e}")
        return render_template(TEMPLATE_ADMIN_DASHBOARD, error="Error interno al registrar candidato")

@app.route('/admin/registrar_candidato', methods=['POST'])
@admin_required
@handle_errors
def registrar_candidato():
    if request.is_json:
        return _registrar_candidato_json(request.get_json())
    return _registrar_candidato_form(request.form)

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
        preguntas_cargadas = cargar_preguntas_desde_excel()
        PREGUNTAS.clear()
        PREGUNTAS.extend(preguntas_cargadas)
    return jsonify({'success': True, 'archivo': archivo.filename})

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
        json.dump(config, f, ensure_ascii=False, indent=2)
    # Recargar preguntas automáticamente
    global PREGUNTAS
    preguntas_cargadas = cargar_preguntas_desde_excel()
    PREGUNTAS.clear()
    PREGUNTAS.extend(preguntas_cargadas)
    return jsonify({'success': True, 'tema_activo': nombre_archivo})

@app.route('/temas/', methods=['GET'])
def listar_archivos_temas():
    temas_dir = os.path.join(os.getcwd(), 'temas')
    if not os.path.exists(temas_dir):
        return jsonify({'archivos': []})
    archivos = [f for f in os.listdir(temas_dir) if f.endswith('.xlsx') or f.endswith('.xls')]
    return jsonify({'archivos': archivos})

# ===== RUTAS DE EVALUACIÓN =====

@app.route('/evaluacion/<codigo>')
@handle_errors
def evaluacion(codigo):
    # Si el candidato no está en memoria, buscar en la base de datos y poblar el diccionario
    if codigo not in candidatos_registrados:
        candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
        if not candidato_db:
            logger.warning(f"Código de candidato inválido: {codigo}")
            return make_response(render_template(TEMPLATE_ERROR, mensaje="Código de candidato inválido"), 404)
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
        return make_response(render_template(TEMPLATE_ERROR, mensaje="Esta evaluación ya ha sido completada"), 403)
    return render_template('cuestionario.html', candidato=candidato)

@app.route('/iniciar_evaluacion', methods=['POST'])
@handle_errors
def iniciar_evaluacion():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos JSON requeridos"}), 400
    
    documento = data.get('documento', '')
    acepta_terminos = int(data.get('acepta_terminos', 0))
    telefono = data.get('telefono', '')

    logger.info(f"Iniciando evaluación para: {documento}")
    
    success, message = EvaluacionService.iniciar_evaluacion(documento, acepta_terminos, telefono)
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": message}), 400

@app.route('/obtener_pregunta')
@handle_errors
def obtener_pregunta():
    pregunta, error = EvaluacionService.obtener_siguiente_pregunta()
    
    if error:
        return jsonify({"error": error})
    
    if not pregunta:
        return jsonify({"error": "No se pudo obtener pregunta"}), 400
        
    # Construir respuesta
    nivel_actual = candidato_actual.get("nivel_actual", 1)
    preguntas_nivel_actual = candidato_actual.get("preguntas_nivel", 0)
    
    return jsonify({
        "id": pregunta["id"],
        "pregunta": pregunta["pregunta"],
        "opciones": pregunta["opciones"],
        "imagen": pregunta.get("imagen"),
        "pregunta_numero": len(candidato_actual["preguntas_mostradas"]),
        "total_preguntas": Config.TOTAL_PREGUNTAS,
        "multiple": pregunta.get("multiple", False),
        "respuestas_correctas_count": len(pregunta.get("respuestas_correctas", [])),
        "nivel_actual": nivel_actual,
        "preguntas_del_nivel": preguntas_nivel_actual + 1,
        "correctas_nivel": candidato_actual.get("correctas_nivel", 0)
    })

@app.route('/responder', methods=['POST'])
@handle_errors
def responder():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos JSON requeridos"}), 400
        
    response, status_code = EvaluacionService.procesar_respuesta(data)
    return jsonify(response), status_code

@app.route('/estado_evaluacion')
@handle_errors
def estado_evaluacion():
    response, status_code = EvaluacionService.obtener_estado()
    return jsonify(response), status_code

def _actualizar_estado_candidato(codigo):
    candidato_actual["evaluacion_completa"] = True
    if codigo in candidatos_registrados:
        candidatos_registrados[codigo]["evaluacion_completada"] = True
        candidatos_registrados[codigo]["nivel_final"] = candidato_actual.get("nivel_actual", 1)
    
    candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
    if candidato_db:
        candidato_db.evaluacion_completada = True
        candidato_db.nivel_final = candidato_actual.get("nivel_actual", 1)
        db.session.commit()

def _guardar_resultados_db(codigo, correctas, total, porcentaje):
    candidato_db = CandidatoDB.query.filter_by(codigo=codigo).first()
    if candidato_db:
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

def _generar_y_subir_pdf(candidato_data):
    pdf_path = None
    drive_result = {"success": False, "error": "PDF no generado"}
    
    try:
        if REPORTLAB_AVAILABLE:
            pdf_path = generar_pdf_evaluacion(candidato_data, candidato_actual)
            logger.info(f"PDF generado: {pdf_path}")
            
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
        
    return pdf_path, drive_result

@app.route('/generar_pdf_final', methods=['POST'])
@handle_errors
def generar_pdf_final():
    codigo = candidato_actual.get("datos_personales", {}).get("codigo")
    if not codigo:
        return jsonify({"error": "No hay evaluación activa"}), 400
        
    _actualizar_estado_candidato(codigo)
    
    try:
        respuestas = candidato_actual.get('respuestas', [])
        correctas = len([r for r in respuestas if r.get('correcta', False)])
        total = len(respuestas)
        porcentaje = (correctas / max(total, 1)) * 100
        
        _actualizar_candidato_final()
        _guardar_resultados_db(codigo, correctas, total, porcentaje)

        candidato_data = candidatos_registrados.get(codigo, {})
        candidato_data["acepta_terminos"] = candidato_actual.get("acepta_terminos", candidato_data.get("acepta_terminos", 0))
        
        pdf_path, drive_result = _generar_y_subir_pdf(candidato_data)
        
        response_data = {
            "success": True,
            "mensaje": "Evaluación completada correctamente",
            "correctas": correctas,
            "total": total,
            "porcentaje": round(porcentaje, 1),
            "nivel_final": candidato_actual.get("nivel_actual", candidato_actual.get("nivel_final", 1)),
            "puntos": candidato_actual.get("puntos", 0),
            "pdf_generado": pdf_path is not None,
            "drive_upload": drive_result.get("success", False),
            "drive_error": drive_result.get("error") if not drive_result.get("success") else None
        }
        
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

# ===== RUTAS API =====

@app.route('/api/configuracion')
@handle_errors
def api_configuracion():
    """API para obtener configuración de la evaluación"""
    return jsonify({
        "total_preguntas": Config.TOTAL_PREGUNTAS,
        "tema_activo": get_tema_activo(),
        "archivos_temas": [f for f in os.listdir(os.path.join(os.getcwd(), 'temas')) if f.endswith('.xlsx') or f.endswith('.xls')]
    })

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

# ===== CONTEXT PROCESSORS =====
@app.context_processor
def inject_admin_email():
    return {'admin_email': Config.ADMIN_EMAIL or 'soporte@empresa.com'}

# ===== MANEJO DE ERRORES =====

@app.errorhandler(404)
def pagina_no_encontrada(error):
    logger.warning(f"Página no encontrada: {request.url} - {error}")
    return make_response(render_template(TEMPLATE_ERROR, mensaje="Página no encontrada"), 404)

@app.errorhandler(500)
def error_interno_servidor(error):
    logger.error(f"Error interno del servidor: {error}")
    return render_template(TEMPLATE_ERROR, mensaje="Error interno del servidor"), 500

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
            tiempo_restante = (expires_at - datetime.now(timezone.utc)).total_seconds()
            
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
    preguntas_cargadas = cargar_preguntas_desde_excel()
    PREGUNTAS.clear()
    PREGUNTAS.extend(preguntas_cargadas)
    
    if PREGUNTAS:
        logger.info(f"✅ Sistema listo con {len(PREGUNTAS)} preguntas cargadas")
        return True
    else:
        logger.error(f"❌ Error: No se pudieron cargar las preguntas. Verificar archivo '{Config.ARCHIVO_EXCEL}'")
        return False

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
