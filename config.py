import os


class Config:
    """Configuración centralizada de la aplicación extraída desde app.py
    Este módulo permite mantener la configuración en un archivo separado
    para facilitar revisiones y refactorizaciones posteriores.
    """
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
    SIGN_BANNER_URL = (os.getenv('SIGN_BANNER_URL') or '').strip()

    # Configuración de evaluación
    EVALUACION_CONFIG = {
        "total_preguntas": 40,
        "evaluacion_cada": 5,
        "min_correctas_avance": 5,
        # Parámetros nuevos para la política B (no interrumpir bloque)
        "racha_para_flag": 3,
        "min_correctas_para_avanzar": 4,
        "contar_parciales_para_avance": True,
        "preguntas_por_nivel": 8,
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
            "errores_consecutivos": None,
            "porcentaje_minimo_mitad": 40
        }
    }
