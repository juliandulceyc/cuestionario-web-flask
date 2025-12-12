import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    return app

def test_app_creation(app):
    """Prueba básica para verificar que la aplicación se crea correctamente"""
    assert app is not None
    assert app.config['TESTING'] is True
