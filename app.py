import os
import re
import json
import random
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import base64
from dataclasses import dataclass
from functools import wraps

# Importar dependencias para PDF y Drive
try:
    from pdf_generator import generar_pdf_evaluacion
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    generar_pdf_evaluacion = None
    logging.warning("Generador de PDF no disponible")

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
    TOTAL_PREGUNTAS = 5
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
    url_evaluacion: str = ""
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

# Configuración de conexión a PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:contraseña@localhost:5432/empresa_db'
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
app = Flask(__name__)

app.secret_key = Config.SECRET_KEY

# Configuración de conexión a PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:contraseña@localhost:5432/empresa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

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

# ===== UTILIDADES DE TEXTO =====
class TextUtils:
    """Utilidades para procesamiento de texto"""
    
    @staticmethod
    def limpiar_texto(texto: Any) -> str:
        """Limpia y normaliza texto eliminando caracteres problemáticos"""
        if not texto or pd.isna(texto):
            return ""
        
        texto_str = str(texto).strip()
        
        replacements = {
            '\r\n': '\n', '\r': '\n', '\t': ' ',
            '"': '"', '"': '"', ''': "'", ''': "'",
            '–': '-', '—': '-', '…': '...'
        }
        
        for old, new in replacements.items():
            texto_str = texto_str.replace(old, new)
        
        return re.sub(r'\s+', ' ', texto_str).strip()
    
    @staticmethod
    def extraer_numero_nivel(texto: Any) -> int:
        """Extrae el número de nivel de un texto"""
        if not texto or pd.isna(texto):
            return 1
        
        texto_str = str(texto).strip().upper()
        
        # Buscar número en el texto
        match = re.search(r'(\d+)', texto_str)
        if match:
            nivel = int(match.group(1))
            return max(1, min(5, nivel))
        
        # Mapeo de palabras a números
        nivel_map = {
            'UNO': 1, 'ONE': 1, 'PRIMERO': 1, 'BÁSICO': 1, 'BASICO': 1,
            'DOS': 2, 'TWO': 2, 'SEGUNDO': 2, 'INTERMEDIO': 2,
            'TRES': 3, 'THREE': 3, 'TERCERO': 3, 'AVANZADO': 3,
            'CUATRO': 4, 'FOUR': 4, 'CUARTO': 4, 'EXPERTO': 4,
            'CINCO': 5, 'FIVE': 5, 'QUINTO': 5, 'MAESTRO': 5, 'MASTER': 5
        }
        
        for palabra, numero in nivel_map.items():
            if palabra in texto_str:
                return numero
        
        return 1

# ===== PROCESAMIENTO DE IMÁGENES =====
class ImageProcessor:
    """Procesador de imágenes del Excel"""
    
    @staticmethod
    def procesar_imagen_excel(imagen_raw: Any) -> Optional[str]:
        """Procesa diferentes tipos de imagen del Excel"""
        if imagen_raw is None or str(imagen_raw).strip() in ['nan', 'NaN', '', None, 'None']:
            return None
        
        try:
            return ImageProcessor._procesar_imagen_embebida(imagen_raw) or \
                   ImageProcessor._procesar_datos_binarios(imagen_raw) or \
                   ImageProcessor._procesar_string_imagen(imagen_raw)
        except Exception as e:
            logger.warning(f"Error procesando imagen: {e}")
            return None
    
    @staticmethod
    def _procesar_imagen_embebida(imagen_raw: Any) -> Optional[str]:
        """Procesa imagen embebida de openpyxl"""
        if not hasattr(imagen_raw, '__class__'):
            return None
            
        class_name = str(type(imagen_raw).__name__)
        if 'Image' not in class_name and 'Picture' not in class_name:
            return None
        
        try:
            img_data = None
            for attr in ['_data', 'data', 'image', 'blob']:
                if hasattr(imagen_raw, attr):
                    data_method = getattr(imagen_raw, attr)
                    img_data = data_method() if callable(data_method) else data_method
                    break
            
            if img_data and len(img_data) > 0:
                imagen_base64 = base64.b64encode(img_data).decode()
                mime_type = ImageProcessor._detectar_tipo_imagen(img_data)
                return f"data:image/{mime_type};base64,{imagen_base64}"
                
        except Exception as e:
            logger.warning(f"Error procesando imagen embebida: {e}")
            
        return None
    
    @staticmethod
    def _procesar_datos_binarios(imagen_raw: Any) -> Optional[str]:
        """Procesa datos binarios directos"""
        if not isinstance(imagen_raw, bytes) or len(imagen_raw) <= 100:
            return None
        
        try:
            imagen_base64 = base64.b64encode(imagen_raw).decode()
            mime_type = ImageProcessor._detectar_tipo_imagen(imagen_raw)
            return f"data:image/{mime_type};base64,{imagen_base64}"
        except Exception as e:
            logger.warning(f"Error procesando bytes: {e}")
            return None
    
    @staticmethod
    def _procesar_string_imagen(imagen_raw: Any) -> Optional[str]:
        """Procesa string con datos de imagen"""
        imagen_str = str(imagen_raw).strip()
        
        if imagen_str.startswith('data:image'):
            return imagen_str
        
        if imagen_str.startswith(('http://', 'https://')):
            return imagen_str
        
        if os.path.exists(imagen_str):
            return ImageProcessor._cargar_imagen_archivo(imagen_str)
            
        return None
    
    @staticmethod
    def _cargar_imagen_archivo(ruta_archivo: str) -> Optional[str]:
        """Carga imagen desde archivo"""
        try:
            ext = os.path.splitext(ruta_archivo)[1].lower()
            mime_type = {
                '.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', 
                '.gif': 'gif', '.bmp': 'bmp', '.webp': 'webp'
            }.get(ext, 'jpeg')
            
            with open(ruta_archivo, "rb") as img_file:
                img_data = img_file.read()
                imagen_base64 = base64.b64encode(img_data).decode()
                return f"data:image/{mime_type};base64,{imagen_base64}"
        except Exception as e:
            logger.warning(f"Error leyendo archivo {ruta_archivo}: {e}")
            return None
    
    @staticmethod
    def _detectar_tipo_imagen(img_data: bytes) -> str:
        """Detecta el tipo de imagen por sus bytes"""
        if img_data.startswith(b'\x89PNG'):
            return 'png'
        elif img_data.startswith(b'\xFF\xD8\xFF'):
            return 'jpeg'
        elif img_data.startswith(b'GIF8'):
            return 'gif'
        else:
            return 'png'

# ===== CARGADOR DE PREGUNTAS =====
class PreguntaLoader:
    @staticmethod
    def _es_valor_vacio(val: Any) -> bool:
        try:
            if val is None:
                return True
            # pandas NaN
            if isinstance(val, float) and pd.isna(val):
                return True
            # Cadenas vacías o 'nan'/'none'
            s = str(val).strip()
            if s == '' or s.upper() in ['NAN', 'NONE', 'NULL']:
                return True
        except Exception:
            return False
        return False
    """Cargador de preguntas desde Excel"""
    
    @staticmethod
    def cargar_preguntas() -> bool:
        """Carga preguntas desde el archivo Excel activo seleccionado por el admin"""
        global PREGUNTAS
        try:
            archivo_excel = get_tema_activo()
            logger.info(f"Buscando archivo: {archivo_excel}")
            temas_dir = os.path.join(os.getcwd(), 'temas')
            ruta_excel = os.path.join(temas_dir, archivo_excel) if archivo_excel else None
            if not ruta_excel or not os.path.exists(ruta_excel):
                logger.error(f"Archivo no encontrado: {ruta_excel}")
                return False
            df = pd.read_excel(ruta_excel)
            PREGUNTAS = []
            estadisticas = PreguntaLoader._procesar_filas(df)
            return PreguntaLoader._finalizar_carga(estadisticas)
        except Exception as e:
            logger.error(f"Error crítico cargando preguntas: {e}")
            return False
    
    # _leer_excel ya no es necesario, se lee directo en cargar_preguntas
    
    @staticmethod
    def _procesar_filas(df: pd.DataFrame) -> Dict[str, int]:
        """Procesa las filas del DataFrame"""
        global PREGUNTAS
        
        filas_procesadas = 0
        filas_con_errores = 0
        
        for index, row in df.iterrows():
            try:
                pregunta_obj = PreguntaLoader._crear_pregunta(row, index)
                if pregunta_obj:
                    PREGUNTAS.append(pregunta_obj)
                    filas_procesadas += 1
                    
                    if filas_procesadas <= 3:
                        PreguntaLoader._debug_pregunta(pregunta_obj, filas_procesadas)
                else:
                    filas_con_errores += 1
                    
            except Exception as e:
                logger.warning(f"Error procesando fila {index + 2}: {e}")
                filas_con_errores += 1
        
        return {"procesadas": filas_procesadas, "errores": filas_con_errores}
    
    @staticmethod
    def _crear_pregunta(row: pd.Series, index: int) -> Optional[Dict[str, Any]]:
        """Crea objeto pregunta desde fila de Excel"""
        # Procesar pregunta
        pregunta_text = TextUtils.limpiar_texto(row.get('PREGUNTA', ''))
        if not pregunta_text or len(pregunta_text) < 10:
            logger.warning(f"Fila {index + 2}: Pregunta muy corta o vacía")
            return None
        
        # Procesar nivel
        nivel_numerico = TextUtils.extraer_numero_nivel(row.get('NIVEL', '1'))
        
        # Procesar imagen
        imagen_procesada = ImageProcessor.procesar_imagen_excel(row.get('IMAGEN', ''))
        
        # Procesar opciones
        opciones = PreguntaLoader._procesar_opciones(row)
        if len(opciones) < 2:
            logger.warning(f"Fila {index + 2}: Menos de 2 opciones válidas")
            return None
        
        # Determinar respuesta(s) correcta(s)
        # 0) Calcular si es múltiple SOLO si ambas columnas RC1 y RC2 contienen letras A-D
        rc1_raw, rc2_raw = PreguntaLoader._extraer_rc1_rc2(row)
        l1 = PreguntaLoader._contiene_letra_opcion(rc1_raw)
        l2 = PreguntaLoader._contiene_letra_opcion(rc2_raw)
        multiple_por_letras = (l1 is not None) and (l2 is not None)
        logger.info(
            f"Fila {index + 2}: RC1='{rc1_raw}' RC2='{rc2_raw}' -> letras=({l1},{l2}) => multiple={multiple_por_letras}"
        )

        respuestas_crudas = PreguntaLoader._obtener_valores_respuesta(row)
        respuestas_texto: List[str] = []
        for raw in respuestas_crudas:
            if raw is None or str(raw).strip() == '':
                continue
            texto = PreguntaLoader._determinar_respuesta_correcta(raw, opciones, index)
            if texto and texto not in respuestas_texto:
                respuestas_texto.append(texto)
        # Si no es múltiple por letras, quedarnos SOLO con la primera respuesta (RC1)
        if not multiple_por_letras and len(respuestas_texto) > 1:
            respuestas_texto = [respuestas_texto[0]]
        if not respuestas_texto:
            # Fallback por seguridad a la opción A
            respuestas_texto = [opciones[0]]
        
        return {
            "id": len(PREGUNTAS) + 1,
            "pregunta": pregunta_text,
            "opciones": opciones,
            "respuesta_correcta": respuestas_texto[0],
            "respuestas_correctas": respuestas_texto,
            "nivel": nivel_numerico,
            "multiple": multiple_por_letras,
            "imagen": imagen_procesada,
            "categoria": TextUtils.limpiar_texto(row.get('CATEGORIA', 'General')),
            "fila_excel": index + 2
        }
    
    @staticmethod
    def _procesar_opciones(row: pd.Series) -> List[str]:
        """Procesa las opciones de una pregunta"""
        opciones = []
        for letra in ['A', 'B', 'C', 'D']:
            opcion = str(row.get(letra, '')).strip()
            if opcion and opcion != 'nan':
                opcion_limpia = TextUtils.limpiar_texto(opcion)
                if opcion_limpia:
                    opciones.append(opcion_limpia)
        return opciones

    @staticmethod
    def _obtener_valor_respuesta(row: pd.Series) -> Any:
        """Obtiene el valor de respuesta desde la columna correcta del Excel.
        Prioriza 'RESPUESTA CORRECTA 1' y variantes; luego intenta detectar por patrones.
        """
        # 1) Intentos directos por nombres comunes
        candidatos = [
            'RESPUESTA CORRECTA 1', 'Respuesta Correcta 1', 'respuesta correcta 1',
            'RESPUESTA_CORRECTA_1', 'RESPUESTA CORRECTA1', 'RESPUESTA_1',
            'RESPUESTA', 'Respuesta'
        ]
        for key in candidatos:
            if key in row:
                val = row.get(key)
                logger.info(f"Columna de respuesta detectada: '{key}' -> '{val}'")
                return val

        # 2) Búsqueda por patrón case-insensitive
        try:
            for col in row.index:
                col_up = str(col).upper().strip()
                if re.search(r'^RESPUESTA\s*CORRECTA\s*1$', col_up):
                    val = row.get(col)
                    logger.info(f"Columna de respuesta detectada (patrón RC1): '{col}' -> '{val}'")
                    return val
            # Si no se encuentra exacto RC1, tomar la primera que parezca 'RESPUESTA' relevante
            for col in row.index:
                col_up = str(col).upper()
                if 'RESPUESTA' in col_up and ('CORRECTA' in col_up or col_up.strip() == 'RESPUESTA'):
                    val = row.get(col)
                    logger.info(f"Columna de respuesta detectada (patrón genérico): '{col}' -> '{val}'")
                    return val
        except Exception as e:
            logger.warning(f"Error detectando columna de respuesta: {e}")

        logger.warning("No se encontró columna de respuesta, usando vacío")
        return ''

    @staticmethod
    def _obtener_valores_respuesta(row: pd.Series) -> List[Any]:
        """Obtiene una lista con hasta dos valores de respuesta desde columnas RESPUESTA CORRECTA 1/2.
        Incluye fallback a una sola columna si la 2 no existe.
        """
        valores: List[Any] = []
        # Intento directo 1/2
        candidatos = [
            ['RESPUESTA CORRECTA 1', 'RESPUESTA CORRECTA 2'],
            ['Respuesta Correcta 1', 'Respuesta Correcta 2'],
            ['respuesta correcta 1', 'respuesta correcta 2'],
            ['RESPUESTA_CORRECTA_1', 'RESPUESTA_CORRECTA_2'],
            ['RESPUESTA 1', 'RESPUESTA 2'],
            ['RESPUESTA', 'RESPUESTA 2']
        ]
        for col1, col2 in candidatos:
            val1 = row.get(col1) if col1 in row else None
            val2 = row.get(col2) if col2 in row else None
            if not PreguntaLoader._es_valor_vacio(val1):
                valores.append(val1)
            if not PreguntaLoader._es_valor_vacio(val2):
                valores.append(val2)
            if valores:
                logger.info(f"Columnas de respuesta detectadas: '{col1}'='{val1}', '{col2}'='{val2}'")
                return valores

        # Patrón por índice 1/2
        try:
            cols_up = {str(c).upper().strip(): c for c in row.index}
            c1 = next((cols_up[k] for k in cols_up.keys() if re.search(r'^RESPUESTA\s*CORRECTA\s*1$', k)), None)
            c2 = next((cols_up[k] for k in cols_up.keys() if re.search(r'^RESPUESTA\s*CORRECTA\s*2$', k)), None)
            if c1 or c2:
                if c1:
                    v1 = row.get(c1)
                    if not PreguntaLoader._es_valor_vacio(v1):
                        valores.append(v1)
                if c2:
                    v2 = row.get(c2)
                    if not PreguntaLoader._es_valor_vacio(v2):
                        valores.append(v2)
                if valores:
                    logger.info(f"Columnas RC1/RC2 detectadas por patrón: '{c1}' y '{c2}'")
                    return valores
        except Exception as e:
            logger.warning(f"Error detectando columnas de respuesta 1/2: {e}")

        # Fallback a única columna genérica
        unico = PreguntaLoader._obtener_valor_respuesta(row)
        return [unico] if unico is not None else []

    @staticmethod
    def _extraer_rc1_rc2(row: pd.Series) -> Tuple[Optional[Any], Optional[Any]]:
        """Extrae crudos de RC1 y RC2 según nombres comunes o por patrón.
        Devuelve (rc1, rc2) sin filtrar.
        """
        # Intentos directos con nombres frecuentes
        parejas = [
            ('RESPUESTA CORRECTA 1', 'RESPUESTA CORRECTA 2'),
            ('Respuesta Correcta 1', 'Respuesta Correcta 2'),
            ('respuesta correcta 1', 'respuesta correcta 2'),
            ('RESPUESTA_CORRECTA_1', 'RESPUESTA_CORRECTA_2'),
            ('RESPUESTA 1', 'RESPUESTA 2'),
            ('RESPUESTA', 'RESPUESTA 2')
        ]
        for c1, c2 in parejas:
            rc1 = row.get(c1) if c1 in row else None
            rc2 = row.get(c2) if c2 in row else None
            if rc1 is not None or rc2 is not None:
                return rc1, rc2

        # Búsqueda por patrón case-insensitive
        try:
            cols_up = {str(c).upper().strip(): c for c in row.index}
            k1 = next((cols_up[k] for k in cols_up.keys() if re.search(r'^RESPUESTA\s*CORRECTA\s*1$', k)), None)
            k2 = next((cols_up[k] for k in cols_up.keys() if re.search(r'^RESPUESTA\s*CORRECTA\s*2$', k)), None)
            rc1 = row.get(k1) if k1 else None
            rc2 = row.get(k2) if k2 else None
            return rc1, rc2
        except Exception:
            return None, None

    @staticmethod
    def _contiene_letra_opcion(val: Any) -> Optional[str]:
        """Devuelve 'A'..'D' si el valor contiene una letra de opción; si no, None."""
        if val is None:
            return None
        s = str(val).strip().upper()
        if not s:
            return None
        # Quitar caracteres comunes como ')' o '.' y espacios
        s = re.sub(r'\s+', '', s)
        s = re.sub(r'[\.)]', '', s)
        if not s:
            return None
        letra = s[0]
        return letra if letra in ['A', 'B', 'C', 'D'] else None
    
    @staticmethod
    def _determinar_respuesta_correcta(respuesta_excel: Any, opciones: List[str], index: int) -> str:
        """Determina la respuesta correcta"""
        raw = str(respuesta_excel).strip()
        respuesta_norm = raw.upper()

        # 1) Normalizar formatos comunes: C), C., ' c ', etc.
        respuesta_norm = re.sub(r'\s+', '', respuesta_norm)  # quitar espacios
        respuesta_norm = re.sub(r'[\.)]', '', respuesta_norm)  # quitar ) y .

        # 2) Mapear números a letras
        mapa_num = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
        if respuesta_norm in mapa_num:
            respuesta_norm = mapa_num[respuesta_norm]

        # 3) Si es letra válida A-D
        if respuesta_norm in ['A', 'B', 'C', 'D']:
            indice_correcto = ord(respuesta_norm) - ord('A')
            if 0 <= indice_correcto < len(opciones):
                logger.info(f"Fila {index + 2}: Respuesta Excel '{raw}' normalizada a '{respuesta_norm}' → opción index {indice_correcto}")
                return opciones[indice_correcto]
            else:
                logger.warning(f"Fila {index + 2}: Respuesta {respuesta_norm} fuera de rango para {len(opciones)} opciones")

        # 4) Intentar match por texto exacto (insensible a mayúsculas/minúsculas)
        raw_limpio = TextUtils.limpiar_texto(raw)
        for i, op in enumerate(opciones):
            if raw_limpio and raw_limpio.lower() == str(op).strip().lower():
                logger.info(f"Fila {index + 2}: Respuesta Excel coincide por texto con opción {chr(65+i)}")
                return opciones[i]

        # 5) Fallback seguro a la primera opción y advertir
        logger.warning(f"Fila {index + 2}: Respuesta '{raw}' no válida, usando A por defecto")
        return opciones[0]
    
    @staticmethod
    def _debug_pregunta(pregunta_obj: Dict[str, Any], numero: int):
        """Debug de primeras preguntas"""
        logger.info(f"Pregunta {numero} cargada:")
        logger.info(f"   Nivel: {pregunta_obj['nivel']}")
        logger.info(f"   Pregunta: {pregunta_obj['pregunta'][:60]}...")
        logger.info(f"   Opciones: {len(pregunta_obj['opciones'])}")
        logger.info(f"   Correcta: {pregunta_obj['respuesta_correcta']}")
    
    @staticmethod
    def _finalizar_carga(estadisticas: Dict[str, int]) -> bool:
        """Finaliza la carga y muestra estadísticas"""
        logger.info(f"\nRESUMEN DE CARGA:")
        logger.info(f"   Preguntas cargadas: {len(PREGUNTAS)}")
        logger.info(f"   Filas con errores: {estadisticas['errores']}")
        
        if len(PREGUNTAS) > 0:
            PreguntaLoader._mostrar_distribucion_niveles()
            return True
        else:
            logger.error("No se cargaron preguntas válidas")
            return False
    
    @staticmethod
    def _mostrar_distribucion_niveles():
        """Muestra la distribución de preguntas por nivel"""
        niveles_count = {}
        for p in PREGUNTAS:
            nivel = p["nivel"]
            niveles_count[nivel] = niveles_count.get(nivel, 0) + 1
        
        logger.info("Distribución por nivel:")
        for nivel in sorted(niveles_count.keys()):
            logger.info(f"   Nivel {nivel}: {niveles_count[nivel]} preguntas")

# ===== EVALUADOR DE RESPUESTAS =====
class EvaluadorRespuestas:
    """Evaluador de respuestas y lógica de evaluación"""
    
    @staticmethod
    def evaluar_respuesta(pregunta: Dict[str, Any], respuesta_usuario: str, respuesta_letra: Optional[str] = None) -> Tuple[bool, float]:
        """Evalúa si la respuesta del usuario es correcta.
        Prioriza comparación por letra (A-D) si se proporciona; si no, cae a texto.
        """
        try:
            respuesta_correcta = pregunta.get("respuesta_correcta")
            nivel = pregunta.get("nivel", 1)
            
            logger.debug(f"Evaluando - Correcta: '{respuesta_correcta}' vs Usuario: '{respuesta_usuario}'")
            
            # 1) Comparación por letra, si viene respuesta_letra
            if respuesta_letra:
                letras_usuario = [s.strip().upper()[:1] for s in str(respuesta_letra).split(',') if s.strip()]
                letras_usuario = [l for l in letras_usuario if l in ['A','B','C','D']]
                opciones = pregunta.get("opciones", [])
                correctas_texto = pregunta.get("respuestas_correctas", [respuesta_correcta] if respuesta_correcta else [])
                letras_correctas = []
                for ct in correctas_texto:
                    try:
                        idx = opciones.index(ct)
                    except ValueError:
                        idx = 0
                    letras_correctas.append(chr(ord('A') + max(0, min(25, idx))))
                # Log comparativo
                textos_usuario = ", ".join([_safe_opt(opciones, l) for l in letras_usuario])
                textos_correctos = ", ".join([_safe_opt(opciones, l) for l in letras_correctas])
                logger.info(
                    "COMPARANDO (LETRA) -> ID=%s Nivel=%s '%s' | Usuario=%s (%s) vs Correcta=%s (%s)",
                    pregunta.get("id"), nivel, str(pregunta.get("pregunta", ""))[:160],
                    ",".join(letras_usuario), textos_usuario, ",".join(letras_correctas), textos_correctos
                )
                # Puntaje proporcional por aciertos, aunque haya errores
                aciertos = len([l for l in letras_usuario if l in letras_correctas])
                total_correctas = len(letras_correctas)
                puntos = (aciertos / total_correctas) * nivel if total_correctas > 0 else 0.0
                logger.info(f"RESULTADO: {aciertos} aciertos de {total_correctas} (+{puntos} puntos)")
                return aciertos == total_correctas, puntos
            # 2) Fallback: comparación por texto (admite múltiples separados por coma)
            if respuesta_usuario and respuesta_correcta:
                opciones = pregunta.get("opciones", [])
                correctas_texto = pregunta.get("respuestas_correctas", [respuesta_correcta])
                usuario_textos = [TextUtils.limpiar_texto(x) for x in str(respuesta_usuario).split(',') if str(x).strip()]
                logger.info(
                    "COMPARANDO (TEXTO) -> ID=%s Nivel=%s '%s' | Usuario='%s' vs Correcta='%s'",
                    pregunta.get("id"), nivel, str(pregunta.get("pregunta", ""))[:160],
                    ", ".join(usuario_textos), ", ".join(correctas_texto)
                )
                if set([u.lower() for u in usuario_textos]) == set([c.lower() for c in correctas_texto]) and len(usuario_textos) == len(correctas_texto):
                    puntos = 1.0 * nivel
                    logger.info(f"RESULTADO: CORRECTA (+{puntos} puntos)")
                    return True, puntos
                else:
                    logger.info("RESULTADO: INCORRECTA (+0 puntos)")
                    return False, 0.0
            else:
                logger.debug("DATOS FALTANTES")
                return False, 0.0
        except Exception as e:
            logger.error(f"Error evaluando respuesta: {e}")
            return False, 0.0
    
    @staticmethod
    def verificar_terminacion_temprana(candidato: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Verifica si la evaluación debe terminar antes de las 40 preguntas"""
        respuestas = candidato.get("respuestas", [])
        total_respuestas = len(respuestas)
        nivel_actual = candidato.get("nivel", 1)
        
        # LÍMITE 1: FALLO EN NIVEL 1
        if total_respuestas == 10 and nivel_actual == 1:
            correctas_nivel_1 = len([r for r in respuestas[:10] if r.get("correcta", False)])
            if correctas_nivel_1 < 6:
                return True, f"Rendimiento insuficiente en nivel básico ({correctas_nivel_1}/10 correctas)"
        
        # LÍMITE 2: 5 ERRORES CONSECUTIVOS
        if total_respuestas >= 5:
            ultimas_5 = respuestas[-5:]
            if all(not r.get("correcta", False) for r in ultimas_5):
                return True, "5 respuestas incorrectas consecutivas"
        
        # LÍMITE 3: RENDIMIENTO MUY BAJO A LA MITAD
        if total_respuestas == 20:
            correctas_total = len([r for r in respuestas if r.get("correcta", False)])
            porcentaje = (correctas_total / 20) * 100
            if porcentaje < 40:
                return True, f"Rendimiento muy bajo a la mitad ({porcentaje:.1f}% correctas)"
        
        return False, None
    
    @staticmethod
    def verificar_avance_nivel(candidato: Dict[str, Any]) -> Tuple[bool, int]:
        """Verifica si el candidato debe avanzar de nivel"""
        respuestas = candidato.get("respuestas", [])
        total_respuestas = len(respuestas)
        nivel_actual = candidato.get("nivel", 1)
        
        logger.debug(f"Verificando avance: Pregunta {total_respuestas}, Nivel {nivel_actual}")
        
        # NIVEL 1 → NIVEL 2 (después de 10 preguntas)
        if total_respuestas == 10 and nivel_actual == 1:
            correctas_nivel_1 = len([r for r in respuestas[:10] if r.get("correcta", False)])
            if correctas_nivel_1 >= 6:
                logger.info(f"AVANCE L1→L2: {correctas_nivel_1}/10 correctas")
                return True, 2
            else:
                logger.info(f"NO AVANZA: {correctas_nivel_1}/10 correctas (necesita 6)")
                return False, nivel_actual
        
        # NIVEL 2 → NIVEL 3 (después de 2 preguntas, automático)
        elif total_respuestas == 12 and nivel_actual == 2:
            logger.info("AVANCE AUTOMÁTICO L2→L3")
            return True, 3
        
        # NIVEL 3 → NIVEL 4 (después de 10 preguntas)
        elif total_respuestas == 22 and nivel_actual == 3:
            respuestas_nivel_3 = respuestas[12:22]
            correctas_nivel_3 = len([r for r in respuestas_nivel_3 if r.get("correcta", False)])
            if correctas_nivel_3 >= 7:
                logger.info(f"AVANCE L3→L4: {correctas_nivel_3}/10 correctas")
                return True, 4
            else:
                logger.info(f"NO AVANZA: {correctas_nivel_3}/10 correctas (necesita 7)")
                return False, nivel_actual
        
        # NIVEL 4 → NIVEL 5 (después de 8 preguntas)
        elif total_respuestas == 30 and nivel_actual == 4:
            respuestas_nivel_4 = respuestas[22:30]
            correctas_nivel_4 = len([r for r in respuestas_nivel_4 if r.get("correcta", False)])
            if correctas_nivel_4 >= 6:
                logger.info(f"AVANCE L4→L5: {correctas_nivel_4}/8 correctas")
                return True, 5
            else:
                logger.info(f"NO AVANZA: {correctas_nivel_4}/8 correctas (necesita 6)")
                return False, nivel_actual
        
        return False, nivel_actual

# ===== MANEJADOR DE CANDIDATOS =====
class CandidatoManager:
    """Manejador de operaciones con candidatos"""
    
    @staticmethod
    def generar_codigo() -> str:
        """Genera código único para candidato"""
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    @staticmethod
    def registrar_candidato(tipo_documento: str, numero_documento: str, nombre: str, email: str, cargo: str) -> Dict[str, Any]:
        """Registra un nuevo candidato"""
        codigo = CandidatoManager.generar_codigo()
        
        candidato = {
            "codigo": codigo,
            "tipo_documento": tipo_documento,
            "numero_documento": numero_documento,
            "nombre_completo": nombre,
            "email": email,
            "cargo": cargo,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "evaluacion_completada": False,
            "link_evaluacion": f"http://localhost:{Config.PORT}/evaluacion/{codigo}",
            "url_evaluacion": f"http://localhost:{Config.PORT}/evaluacion/{codigo}"
        }
        
        candidatos_registrados[codigo] = candidato
        logger.info(f"Candidato registrado: {nombre} - Código: {codigo}")
        
        return candidato

# ===== VALIDADORES DE ENTRADA =====
class InputValidator:
    @staticmethod
    def validate_cargo(cargo: str) -> Tuple[bool, str]:
        """Valida el campo cargo"""
        if not cargo or not cargo.strip():
            return False, "Cargo es obligatorio"
        cargo = cargo.strip()
        if len(cargo) < 2:
            return False, "Cargo debe tener al menos 2 caracteres"
        if len(cargo) > 100:
            return False, "Cargo demasiado largo"
        # Solo letras, espacios y caracteres acentuados
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', cargo):
            return False, "Cargo solo puede contener letras y espacios"
        return True, ""
    """Validador de entrada para datos del usuario"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Valida formato de email"""
        if not email or not email.strip():
            return False, "Email es obligatorio"
        
        email = email.strip()
        if len(email) > 254:
            return False, "Email demasiado largo"
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return False, "Formato de email inválido"
        
        return True, ""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Valida nombre completo"""
        if not name or not name.strip():
            return False, "Nombre es obligatorio"
        name = name.strip()
        if len(name) < 2:
            return False, "Nombre debe tener al menos 2 caracteres"
        if len(name) > 100:
            return False, "Nombre demasiado largo"
        # Solo letras, espacios y caracteres acentuados
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', name):
            return False, "Nombre solo puede contener letras y espacios"
        return True, ""

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Valida número de teléfono"""
        if not phone or not phone.strip():
            return True, ""  # Teléfono es opcional
        phone = phone.strip()
        if len(phone) < 7:
            return False, "Teléfono demasiado corto"
        if len(phone) > 15:
            return False, "Teléfono demasiado largo"
        # Solo números, espacios, guiones, paréntesis y +
        if not re.match(r'^[\d\s\-\+\(\)]+$', phone):
            return False, "Teléfono contiene caracteres inválidos"
        return True, ""
# ===== FUNCIONES DE UTILIDAD =====
def get_total_preguntas() -> int:
    """Función global para obtener el total de preguntas"""
    return Config.TOTAL_PREGUNTAS

def get_configuracion_evaluacion() -> Dict[str, Any]:
    """Configuración para 40 preguntas con progresión inteligente"""
    # Devolver una copia sincronizando el total con Config.TOTAL_PREGUNTAS
    cfg = dict(Config.EVALUACION_CONFIG)
    cfg["total_preguntas"] = Config.TOTAL_PREGUNTAS
    return cfg

# ===== RUTAS PRINCIPALES =====
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
    for _, row in df.iterrows():
        preguntas.append({
            'pregunta': row.get('pregunta', ''),
            'opciones': [row.get(f'opcion_{i}', '') for i in range(1, 5)],
            'respuesta_correcta': row.get('respuesta_correcta', ''),
            'nivel': row.get('nivel', 1),
            'categoria': row.get('categoria', ''),
            'multiple': bool(row.get('multiple', False))
        })
    return preguntas

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
    return render_template('admin_dashboard.html', candidatos=list(candidatos_registrados.values()))

@app.route('/admin/candidatos')
@admin_required
@handle_errors
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
    
    return render_template('panel_admin.html', candidatos=list(candidatos_registrados.values()))

@app.route('/admin/registrar_candidato', methods=['POST'])
@admin_required
@handle_errors
def registrar_candidato():
    # Detectar si es JSON o formulario
    if request.is_json:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        tipo_documento = data.get('tipo_documento', '').strip()
        numero_documento = data.get('numero_documento', '').strip()
        nombre = data.get('nombre_completo', '').strip()
        email = data.get('email', '').strip()
        cargo = data.get('cargo', '').strip()
    else:
        tipo_documento = request.form.get('tipo_documento', '').strip()
        numero_documento = request.form.get('numero_documento', '').strip()
        nombre = request.form.get('nombre_completo', '').strip()
        email = request.form.get('email', '').strip()
        cargo = request.form.get('cargo', '').strip()
    # Validaciones robustas
    validation_errors = []
    if not tipo_documento:
        validation_errors.append('Tipo de documento es obligatorio')
    if not numero_documento:
        validation_errors.append('Número de documento es obligatorio')
    valid_name, name_error = InputValidator.validate_name(nombre)
    if not valid_name:
        validation_errors.append(f"Nombre: {name_error}")
    valid_email, email_error = InputValidator.validate_email(email)
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
        candidato = CandidatoManager.registrar_candidato(tipo_documento, numero_documento, nombre, email, cargo)
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
    if codigo not in candidatos_registrados:
        logger.warning(f"Código de candidato inválido: {codigo}")
        return render_template('error.html', mensaje="Código de candidato inválido")
    
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
        logger.info(f"Evaluación iniciada para: {candidato_encontrado['nombre_completo']}")
        return jsonify({"mensaje": "Evaluación iniciada correctamente"})
    else:
        logger.warning(f"Candidato no encontrado: {documento}")
        return jsonify({"error": "Candidato no registrado"}), 404

@app.route('/obtener_pregunta')
@handle_errors
def obtener_pregunta():
    """Obtiene la siguiente pregunta para el candidato"""
    if not candidato_actual or len(PREGUNTAS) == 0:
        return jsonify({"error": "Evaluación no iniciada"}), 400
    
    preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
    
    # Verificar si ya terminó
    if (len(preguntas_mostradas) >= Config.TOTAL_PREGUNTAS or 
        candidato_actual.get("evaluacion_completa", False) or
        candidato_actual.get("terminacion_temprana", False)):
        return jsonify({"error": "Evaluación completada"})
    
    nivel_candidato_actual = candidato_actual.get("nivel", 1)
    pregunta_numero = len(preguntas_mostradas) + 1
    
    # Determinar nivel de pregunta según progreso
    nivel_busqueda = _determinar_nivel_pregunta(pregunta_numero, nivel_candidato_actual)
    
    # Buscar preguntas disponibles
    preguntas_disponibles = [
        p for p in PREGUNTAS 
        if p["id"] not in preguntas_mostradas and p["nivel"] == nivel_busqueda
    ]
    
    # Fallback si no hay preguntas del nivel buscado
    if not preguntas_disponibles:
        preguntas_disponibles = _buscar_pregunta_fallback(preguntas_mostradas, nivel_busqueda)
    
    if not preguntas_disponibles:
        candidato_actual["evaluacion_completa"] = True
        return jsonify({"error": "No hay más preguntas disponibles"})
    
    # Seleccionar pregunta aleatoria
    pregunta_seleccionada = random.choice(preguntas_disponibles)
    candidato_actual["preguntas_mostradas"].append(pregunta_seleccionada["id"])
    
    logger.debug(f"Pregunta {pregunta_numero}: ID {pregunta_seleccionada['id']}, Nivel {pregunta_seleccionada['nivel']}")
    # Log informativo de la pregunta enviada al cliente
    try:
        opciones_fmt = " | ".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(pregunta_seleccionada.get("opciones", []))])
        texto_trunc = str(pregunta_seleccionada.get("pregunta", ""))[:160]
        logger.info(
            "ENVIANDO PREGUNTA %s/%s -> ID=%s Nivel=%s Texto='%s' Opciones=[%s]",
            pregunta_numero, Config.TOTAL_PREGUNTAS, pregunta_seleccionada.get("id"),
            pregunta_seleccionada.get("nivel"), texto_trunc, opciones_fmt
        )
    except Exception as _e:
        logger.debug(f"No se pudo formatear log de pregunta: {_e}")
    
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
        preguntas_disponibles = [
            p for p in PREGUNTAS 
            if p["id"] not in preguntas_mostradas and p["nivel"] == nivel_alt
        ]
        if preguntas_disponibles:
            logger.debug(f"Usando nivel alternativo {nivel_alt}")
            return preguntas_disponibles
    return []

@app.route('/responder', methods=['POST'])
@handle_errors
def responder():
    """Procesa la respuesta del candidato"""
    global candidato_actual
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos JSON requeridos"}), 400
    
    respuesta_usuario = data.get('respuesta')
    respuesta_letra = data.get('respuesta_letra')
    pregunta_id = data.get('pregunta_id')
    respuestas_seleccionadas = data.get('respuestas_seleccionadas', [])
    
    # Buscar la pregunta
    pregunta = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
    if not pregunta:
        return jsonify({"error": "Pregunta no encontrada"}), 404
    
    # Evaluar respuesta
    es_correcta, puntos_obtenidos = EvaluadorRespuestas.evaluar_respuesta(pregunta, respuesta_usuario, respuesta_letra)
    
    # Actualizar candidato
    candidato_actual["puntos"] = candidato_actual.get("puntos", 0) + puntos_obtenidos
    
    if "respuestas" not in candidato_actual:
        candidato_actual["respuestas"] = []
    
    # Registrar respuesta
    nueva_respuesta = {
        "pregunta_id": pregunta_id,
        "pregunta": pregunta["pregunta"],
    "respuesta": respuesta_usuario,
    "respuesta_letra": respuesta_letra,
        "respuestas_seleccionadas": respuestas_seleccionadas,
        "correcta": es_correcta,
        "puntos": puntos_obtenidos,
        "nivel_pregunta": pregunta["nivel"],
        "nivel_candidato": candidato_actual.get("nivel", 1),
        "respuestas_correctas": pregunta.get("respuestas_correctas", [pregunta["respuesta_correcta"]]),
        "multiple": pregunta.get("multiple", False)
    }
    
    candidato_actual["respuestas"].append(nueva_respuesta)
    total_respuestas = len(candidato_actual["respuestas"])
    
    # Verificar terminación temprana
    terminacion_temprana, razon_terminacion = EvaluadorRespuestas.verificar_terminacion_temprana(candidato_actual)
    
    if terminacion_temprana:
        candidato_actual["evaluacion_completa"] = True
        candidato_actual["terminacion_temprana"] = True
        candidato_actual["razon_terminacion"] = razon_terminacion
        
        logger.info(f"TERMINACIÓN TEMPRANA: {razon_terminacion}")
        
        return jsonify({
            "success": True,
            "hay_mas": False,
            "terminacion_temprana": True,
            "razon": razon_terminacion,
            "pregunta_numero": total_respuestas,
            "message": f"Evaluación terminada: {razon_terminacion}"
        })
    
    # Verificar avance de nivel
    avanzar_nivel, nuevo_nivel = EvaluadorRespuestas.verificar_avance_nivel(candidato_actual)
    
    if avanzar_nivel:
        candidato_actual["nivel"] = nuevo_nivel
        logger.info(f"NIVEL UP: {candidato_actual.get('nivel', 1)} → {nuevo_nivel}")
    
    # Verificar si continúa
    hay_mas_preguntas = total_respuestas < Config.TOTAL_PREGUNTAS and not candidato_actual.get("evaluacion_completa", False)
    
    if not hay_mas_preguntas:
        candidato_actual["evaluacion_completa"] = True
        _actualizar_candidato_final()
        logger.info("Evaluación completada normalmente")
    
    return jsonify({
        "success": True,
        "hay_mas": hay_mas_preguntas,
        "pregunta_numero": total_respuestas,
        "message": "Respuesta guardada correctamente"
    })

def _actualizar_candidato_final():
    """Actualiza el candidato al finalizar la evaluación"""
    codigo = candidato_actual.get("datos_personales", {}).get("codigo")
    if codigo and codigo in candidatos_registrados:
        candidatos_registrados[codigo]["evaluacion_completada"] = True
        candidatos_registrados[codigo]["puntos_finales"] = candidato_actual.get("puntos", 0)
        candidatos_registrados[codigo]["nivel_final"] = candidato_actual.get("nivel", 1)

# ===== GENERADOR DE PDF =====
@app.route('/generar_pdf_final', methods=['POST'])
@handle_errors
def generar_pdf_final():
    """Genera el PDF final de la evaluación y lo envía a Google Drive"""
    global candidato_actual
    
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
        
        # Obtener datos del candidato
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
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

# ===== INICIALIZACIÓN =====

def inicializar_sistema():
    """Inicializa el sistema de evaluación"""
    logger.info("🚀 Iniciando sistema de evaluación...")
    logger.info(f"📊 Configurado para {Config.TOTAL_PREGUNTAS} preguntas")
    
    if PreguntaLoader.cargar_preguntas():
        logger.info(f"✅ Sistema listo con {len(PREGUNTAS)} preguntas cargadas")
        return True
    else:
        logger.error(f"❌ Error: No se pudieron cargar las preguntas. Verificar archivo '{Config.ARCHIVO_EXCEL}'")
        return False

# ===== PUNTO DE ENTRADA =====

if __name__ == '__main__':
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