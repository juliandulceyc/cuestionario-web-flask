from dotenv import load_dotenv
import os

# Cargar variables de entorno antes de importar cualquier otra cosa
load_dotenv()

from app import create_app
from app.config import Config
from app.extensions import db
from app.utils import cargar_preguntas_desde_excel, seed_or_update_admin_user
from app.shared import PREGUNTAS
import logging
from sqlalchemy import inspect, text

app = create_app()
logger = logging.getLogger(__name__)

def inicializar_sistema():
    """Inicializa el sistema de evaluación"""
    logger.info("🚀 Iniciando sistema de evaluación...")
    logger.info(f"📊 Configurado para {Config.TOTAL_PREGUNTAS} preguntas")
    
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
    with app.app_context():
        # Verificar/migrar esquema simple de recovery_tokens si quedó antiguo
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'recovery_tokens' in tables:
                cols = [col['name'] for col in inspector.get_columns('recovery_tokens')]
                if ('username' in cols) and ('user_id' not in cols):
                    logger.warning("Esquema antiguo de recovery_tokens detectado. Eliminando tabla para recrear correctamente...")
                    with db.engine.begin() as conn:
                        conn.execute(text('DROP TABLE recovery_tokens'))
                    logger.info("Tabla recovery_tokens eliminada. Será recreada por create_all().")
        except Exception as e:
            logger.error(f"Error verificando esquema de recovery_tokens: {e}")
        db.create_all()
        seed_or_update_admin_user('julian_castellanosd@soy.sena.edu.co')

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
