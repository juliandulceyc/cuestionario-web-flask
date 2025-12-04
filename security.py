import jwt
import bcrypt
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Gestor de seguridad"""
    
    # Configuración de tokens
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or secrets.token_hex(32)
    JWT_ALGORITHM = 'HS256'
    TOKEN_EXPIRATION_MINUTES = 15
    REFRESH_TOKEN_EXPIRATION_DAYS = 7
    
    @staticmethod
    def generar_token(usuario_id: str, rol: str = 'admin') -> dict:
        """
        Genera un token JWT con expiración de 15 minutos
        
        Args:
            usuario_id: Identificador del usuario
            rol: Rol del usuario (admin, candidato, etc.)
            
        Returns:
            dict: Token de acceso y refresh token
        """
        now = datetime.utcnow()
        
        # Token de acceso (15 minutos)
        access_payload = {
            'user_id': usuario_id,
            'rol': rol,
            'exp': now + timedelta(minutes=SecurityManager.TOKEN_EXPIRATION_MINUTES),
            'iat': now,
            'type': 'access'
        }
        
        # Refresh token (7 días)
        refresh_payload = {
            'user_id': usuario_id,
            'rol': rol,
            'exp': now + timedelta(days=SecurityManager.REFRESH_TOKEN_EXPIRATION_DAYS),
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, SecurityManager.JWT_SECRET_KEY, algorithm=SecurityManager.JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, SecurityManager.JWT_SECRET_KEY, algorithm=SecurityManager.JWT_ALGORITHM)
        
        logger.info(f"Token generado para usuario {usuario_id} - Expira en {SecurityManager.TOKEN_EXPIRATION_MINUTES} minutos")
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': SecurityManager.TOKEN_EXPIRATION_MINUTES * 60,  # en segundos
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def verificar_token(token: str) -> dict:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            dict: Payload del token si es válido
            
        Raises:
            jwt.ExpiredSignatureError: Si el token ha expirado
            jwt.InvalidTokenError: Si el token es inválido
        """
        try:
            payload = jwt.decode(token, SecurityManager.JWT_SECRET_KEY, algorithms=[SecurityManager.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"Token inválido: {e}")
            raise
    
    @staticmethod
    def renovar_token(refresh_token: str) -> dict:
        """
        Renueva un token de acceso usando el refresh token
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            dict: Nuevo token de acceso
        """
        try:
            payload = SecurityManager.verificar_token(refresh_token)
            
            if payload.get('type') != 'refresh':
                raise jwt.InvalidTokenError("Token no es de tipo refresh")
            
            # Generar nuevo token de acceso
            return SecurityManager.generar_token(
                usuario_id=payload['user_id'],
                rol=payload['rol']
            )
        except Exception as e:
            logger.error(f"Error renovando token: {e}")
            raise
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Encripta una contraseña usando bcrypt
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verificar_password(password: str, hashed: str) -> bool:
        """
        Verifica una contraseña contra su hash
        
        Args:
            password: Contraseña en texto plano
            hashed: Hash de la contraseña
            
        Returns:
            bool: True si la contraseña es correcta
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def token_requerido(f):
    """
    Decorador para rutas que requieren token JWT válido
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Buscar token en el header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401
        
        # Buscar token en cookies como fallback
        if not token and 'access_token' in request.cookies:
            token = request.cookies.get('access_token')
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        try:
            payload = SecurityManager.verificar_token(token)
            request.current_user = payload
            
            # Verificar si el token está próximo a expirar (menos de 5 minutos)
            exp = datetime.fromtimestamp(payload['exp'])
            tiempo_restante = (exp - datetime.utcnow()).total_seconds()
            
            if tiempo_restante < 300:  # 5 minutos
                logger.info(f"Token próximo a expirar para usuario {payload['user_id']}")
                # Agregar header indicando que debe renovar
                request.debe_renovar_token = True
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado', 'code': 'TOKEN_EXPIRED'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            logger.error(f"Error verificando token: {e}")
            return jsonify({'error': 'Error de autenticación'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def validar_entrada(data: dict, campos_requeridos: list) -> tuple:
    """
    Valida que los campos requeridos estén presentes y no vacíos
    
    Args:
        data: Diccionario con los datos a validar
        campos_requeridos: Lista de nombres de campos requeridos
        
    Returns:
        tuple: (bool, str) - (es_valido, mensaje_error)
    """
    errores = []
    
    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            errores.append(f"Campo '{campo}' es requerido")
    
    if errores:
        return False, "; ".join(errores)
    
    return True, ""


def sanitizar_entrada(texto: str, max_length: int = 500) -> str:
    """
    Sanitiza texto de entrada para prevenir inyecciones
    
    Args:
        texto: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    # Limitar longitud
    texto = str(texto)[:max_length]
    
    # Eliminar caracteres peligrosos
    caracteres_peligrosos = ['<', '>', '"', "'", '&', ';', '|', '`']
    for char in caracteres_peligrosos:
        texto = texto.replace(char, '')
    
    return texto.strip()


# Headers de seguridad HTTP
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
}


def aplicar_headers_seguridad(response):
    """
    Aplica headers de seguridad HTTP a la respuesta
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


def handle_errors(f):
    """
    Decorador para manejar errores de forma centralizada
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error no manejado en {f.__name__}: {str(e)}")
            # Importar render_template aquí para evitar importación circular si es necesario
            from flask import render_template
            if request.is_json:
                return jsonify({'error': 'Error interno del servidor', 'message': str(e)}), 500
            return render_template('error.html', mensaje="Error interno del servidor"), 500
    return decorated

