import pytest
from app import create_app

def test_app_creation():
    """Prueba básica para verificar que la aplicación se crea correctamente"""
    app = create_app()
    assert app is not None
    assert app.config['TESTING'] is False  # Por defecto no es testing a menos que se configure
