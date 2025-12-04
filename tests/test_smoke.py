def test_smoke():
    """Prueba mínima para asegurar que el pipeline CI puede ejecutar pytest.

    Esta prueba no valida lógica de negocio; su objetivo es garantizar que
    Coverage/pytest generen un reporte en la CI mientras se añaden pruebas
    reales para la aplicación.
    """
    assert True
