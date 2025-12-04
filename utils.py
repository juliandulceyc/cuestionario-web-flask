import os
import json
import pandas as pd
import smtplib
import logging
import re
import random
from datetime import datetime
from email.message import EmailMessage
from typing import List, Dict, Any, Tuple, Optional

from config import Config
from shared import PREGUNTAS, candidatos_registrados, candidato_actual
from extensions import db
from models import UserDB, CandidatoDB, ResultadoDB
from security import SecurityManager

logger = logging.getLogger(__name__)

def setup_logging():
    """Configura el sistema de logging"""
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
    return logging.getLogger('evaluacion_system')

def get_tema_activo():
    if not os.path.exists('config_tema.json'):
        return None
    with open('config_tema.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('archivo_excel')

def _extraer_opciones(row):
    opciones = []
    for letra in ['A', 'B', 'C', 'D', 'E']:
        if letra in row:
            opt = str(row.get(letra, '')).strip()
            if opt:
                opciones.append(opt)
    return opciones

def _extraer_respuestas_correctas(row):
    respuestas_correctas = []
    for col in ['RESPUESTA CORRECTA', 'RESPUESTA CORRECTA 1', 'RESPUESTA CORRECTA 2']:
        val = row.get(col)
        if val and not pd.isna(val):
            val_str = str(val).strip().upper()
            if val_str in ['A', 'B', 'C', 'D', 'E']:
                respuestas_correctas.append(val_str)
    return respuestas_correctas

def _procesar_fila_pregunta(row, idx, used_ids):
    """Procesa una fila del Excel para extraer una pregunta"""
    opciones = _extraer_opciones(row)
    if len(opciones) < 2:
        return None
        
    respuestas_correctas = _extraer_respuestas_correctas(row)
    if not respuestas_correctas:
        return None
        
    respuestas_validas = [r for r in respuestas_correctas if r]
    es_multiple = len(respuestas_validas) > 1
    pregunta_id_raw = row.get('NUM')
    try:
        pregunta_id = int(''.join(filter(str.isdigit, str(pregunta_id_raw))))
    except Exception:
        pregunta_id = idx + 1
        
    while pregunta_id in used_ids or pregunta_id == 0:
        pregunta_id += 1
    used_ids.add(pregunta_id)
    
    nivel_raw = row.get('NIVEL', 1)
    try:
        nivel_str = str(nivel_raw)
        nivel_num = int(''.join(filter(str.isdigit, nivel_str)))
        if nivel_num < 1 or nivel_num > 5:
            nivel_num = 1
    except Exception:
        nivel_num = 1
        
    pregunta_texto = row.get('PREGUNTA', row.get('TIPO DE PREGUNTA', ''))
    return {
        'id': pregunta_id,
        'pregunta': pregunta_texto,
        'opciones': opciones,
        'respuesta_correcta': respuestas_validas[0] if respuestas_validas else '',
        'respuestas_correctas': respuestas_validas,
        'nivel': nivel_num,
        'categoria': row.get('CATEGORIA', ''),
        'multiple': es_multiple
    }

def cargar_preguntas_desde_excel():
    archivo_excel = get_tema_activo()
    if not archivo_excel:
        return []
    temas_dir = os.path.join(os.getcwd(), 'temas')
    ruta_excel = os.path.join(temas_dir, archivo_excel)
    if not os.path.exists(ruta_excel):
        return []
    
    try:
        df = pd.read_excel(ruta_excel)
    except Exception as e:
        logger.error(f"Error leyendo Excel: {e}")
        return []

    preguntas = []
    used_ids = set()
    for idx, row in df.iterrows():
        pregunta = _procesar_fila_pregunta(row, idx, used_ids)
        if pregunta:
            preguntas.append(pregunta)
            
    return preguntas

def validar_email_simple(email):
    if not email or '@' not in email:
        return False, 'Formato de email inválido'
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(regex, email):
        return False, 'Formato de email inválido'
    return True, ''

def _configurar_mensaje_email(destinatario, asunto, cuerpo_texto, cuerpo_html):
    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = Config.EMAIL_FROM
    msg['To'] = destinatario
    msg.set_content(cuerpo_texto)
    if cuerpo_html:
        msg.add_alternative(cuerpo_html, subtype='html')
    return msg

def _enviar_smtp(msg, use_ssl=False):
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_cls(Config.EMAIL_HOST, Config.EMAIL_PORT, timeout=20) as smtp:
        if Config.DEBUG:
            try:
                smtp.set_debuglevel(1)
            except Exception: pass
        
        if not use_ssl:
            smtp.starttls()
            
        if Config.EMAIL_USER and Config.EMAIL_PASSWORD:
            smtp.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
        smtp.send_message(msg)

def enviar_email(destinatario: str, asunto: str, cuerpo_texto: str, cuerpo_html: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    try:
        if not (Config.EMAIL_HOST and Config.EMAIL_PORT and Config.EMAIL_FROM):
            logger.warning("SMTP no configurado correctamente. EMAIL_HOST/PORT/FROM faltantes")
            return False, "SMTP no configurado (falta HOST/PORT/FROM)"
            
        msg = _configurar_mensaje_email(destinatario, asunto, cuerpo_texto, cuerpo_html)
        use_ssl = str(Config.EMAIL_PORT) == '465'
        
        _enviar_smtp(msg, use_ssl)
        
        logger.info(f"Email enviado a {destinatario}")
        return True, None
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False, str(e)

def _determinar_nivel_pregunta(pregunta_numero: int, nivel_candidato: int) -> int:
    if pregunta_numero <= 10:
        return 1
    elif pregunta_numero <= 12:
        return 2
    else:
        return nivel_candidato

def _buscar_pregunta_fallback(preguntas_mostradas: List[int], nivel_busqueda: int) -> List[Dict[str, Any]]:
    max_nivel = Config.EVALUACION_CONFIG.get("niveles_maximos", 5)
    # Preferir niveles inferiores
    for lvl in range(nivel_busqueda - 1, 0, -1):
        preguntas_alt = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p.get("nivel", 1) == lvl]
        if preguntas_alt:
            return preguntas_alt
    # Si no, superiores
    for lvl in range(nivel_busqueda + 1, max_nivel + 1):
        preguntas_alt = [p for p in PREGUNTAS if p["id"] not in preguntas_mostradas and p.get("nivel", 1) == lvl]
        if preguntas_alt:
            return preguntas_alt
    return []

def _actualizar_candidato_final():
    codigo = candidato_actual.get("datos_personales", {}).get("codigo")
    if codigo and codigo in candidatos_registrados:
        candidatos_registrados[codigo]["evaluacion_completada"] = True
        candidatos_registrados[codigo]["puntos_finales"] = candidato_actual.get("puntos", 0)
        candidatos_registrados[codigo]["nivel_final"] = candidato_actual.get("nivel_actual", 1)

def registrar_candidato_simple(tipo_documento, numero_documento, nombre, email, cargo, tema):
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

def seed_or_update_admin_user(admin_email: str):
    try:
        admin_username = Config.ADMIN_USER
        user = UserDB.query.filter_by(username=admin_username).first()
        if user:
            if user.email != admin_email:
                user.email = admin_email
                db.session.commit()
                logger.info(f"Admin email actualizado a: {admin_email}")
        else:
            u = UserDB(
                username=admin_username,
                email=admin_email,
                password_hash=SecurityManager.hash_password(Config.ADMIN_PASS),
                role='admin',
                is_active=True
            )
            db.session.add(u)
            db.session.commit()
            logger.info(f"Admin user creado: {admin_username}")
    except Exception as e:
        logger.error(f"Error en seed_or_update_admin_user: {e}")
        db.session.rollback()

def inicializar_sistema():
    logger.info("🚀 Iniciando sistema de evaluación...")
    global PREGUNTAS
    # Actualizar la variable global en shared
    preguntas_cargadas = cargar_preguntas_desde_excel()
    PREGUNTAS.clear()
    PREGUNTAS.extend(preguntas_cargadas)
    
    if PREGUNTAS:
        logger.info(f"✅ Sistema listo con {len(PREGUNTAS)} preguntas cargadas")
        return True
    else:
        logger.error("❌ Error: No se pudieron cargar las preguntas.")
        return False
