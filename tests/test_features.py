import pytest
from app import create_app, db
from app.models import TemaDB, PreguntaDB
from app.utils import cargar_preguntas_desde_excel
import json
import os

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_rate_limiting(client):
    """Prueba que el rate limiting bloquea después de 5 intentos"""
    # 5 intentos permitidos
    for _ in range(5):
        response = client.post('/admin/authenticate', data={
            'username': 'wrong',
            'password': 'wrong'
        })
        assert response.status_code != 429
    
    # El 6to debe fallar
    response = client.post('/admin/authenticate', data={
        'username': 'wrong',
        'password': 'wrong'
    })
    assert response.status_code == 429

def test_web_editor_models(app):
    """Prueba la creación de Temas y Preguntas en DB"""
    with app.app_context():
        tema = TemaDB(nombre="Tema Test", descripcion="Descripción Test")
        db.session.add(tema)
        db.session.commit()
        
        assert tema.id is not None
        
        pregunta = PreguntaDB(
            tema_id=tema.id,
            texto="¿Pregunta de prueba?",
            opciones=["A", "B", "C", "D"],
            respuesta_correcta="A",
            nivel=1
        )
        db.session.add(pregunta)
        db.session.commit()
        
        assert pregunta.id is not None
        assert pregunta.tema.nombre == "Tema Test"

def test_multiple_banks_loading(app):
    """Prueba que se carguen preguntas desde la DB si el tema coincide"""
    with app.app_context():
        # Crear tema y pregunta en DB
        tema_nombre = "TemaDB_Test"
        tema = TemaDB(nombre=tema_nombre)
        db.session.add(tema)
        db.session.commit()
        
        pregunta = PreguntaDB(
            tema_id=tema.id,
            texto="Pregunta DB",
            opciones=["1", "2"],
            respuesta_correcta="1",
            nivel=1
        )
        db.session.add(pregunta)
        db.session.commit()
        
        # Simular configuración de tema activo
        # Mockear get_tema_activo o escribir archivo temporal
        # Como get_tema_activo lee archivo, mejor mockearlo
        # Pero para este test simple, podemos llamar a la lógica interna de utils si la expusiéramos
        # O escribir el archivo config
        
        config_path = os.path.join('config', 'config_tema.json')
        os.makedirs('config', exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump({'archivo_excel': tema_nombre}, f)
            
        # Cargar preguntas
        preguntas = cargar_preguntas_desde_excel()
        
        # Verificar
        assert len(preguntas) == 1
        assert preguntas[0]['pregunta'] == "Pregunta DB"
