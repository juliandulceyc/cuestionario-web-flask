from flask import Flask
from .config import Config
from .extensions import db
from .utils import setup_logging
import secrets

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Asegurar que existe una secret key
    if not app.config.get('SECRET_KEY'):
        app.secret_key = secrets.token_hex(32)

    # Inicializar extensiones
    db.init_app(app)
    setup_logging()

    # Registrar blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
