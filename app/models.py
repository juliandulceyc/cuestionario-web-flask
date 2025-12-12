from datetime import datetime, timezone
from .extensions import db
from .security import SecurityManager

def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Modelo de Usuario (admins del sistema)
class UserDB(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)

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

# Modelo de Tema (Banco de Preguntas)
class TemaDB(db.Model):
    __tablename__ = 'temas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    preguntas = db.relationship('PreguntaDB', backref='tema', cascade='all, delete-orphan', lazy=True)

# Modelo de Pregunta
class PreguntaDB(db.Model):
    __tablename__ = 'preguntas'
    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey('temas.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    opciones = db.Column(db.JSON, nullable=False)  # Lista de opciones ["A) ...", "B) ..."]
    respuesta_correcta = db.Column(db.String(10), nullable=False)  # "A", "B", etc.
    nivel = db.Column(db.Integer, default=1)
    multiple = db.Column(db.Boolean, default=False)
    respuestas_correctas = db.Column(db.JSON)  # Lista ["A", "C"] si es multiple
    created_at = db.Column(db.DateTime, default=get_utc_now)

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
    created_at = db.Column(db.DateTime, default=get_utc_now)
    user = db.relationship('UserDB')

    def is_expired(self) -> bool:
        return get_utc_now() >= self.expires_at
