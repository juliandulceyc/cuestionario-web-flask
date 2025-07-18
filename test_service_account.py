"""
Script de prueba para verificar que Service Account funciona
creando carpeta en el Drive de la cuenta de servicio
"""
from drive_integration import save_session_to_drive

def test_service_account():
    print("=== PROBANDO SERVICE ACCOUNT ===")
    
    # Datos de prueba de un aspirante
    usuario_actual = {
        'datos_personales': {
            'nombre': 'Juan Pérez',
            'email': 'juan.prueba@test.com',
            'telefono': '123456789'
        },
        'nivel': 2,
        'puntos': 85,
        'respuestas_correctas_nivel': 8,
        'preguntas_mostradas': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
    
    preguntas_respondidas = [
        {
            'pregunta': '¿Cuál es la capital de Francia?',
            'respuesta_usuario': 'París',
            'es_correcta': True,
            'tiempo_respuesta': 5.2
        },
        {
            'pregunta': '¿Cuánto es 2+2?',
            'respuesta_usuario': '4',
            'es_correcta': True,
            'tiempo_respuesta': 2.1
        }
    ]
    
    try:
        result = save_session_to_drive(usuario_actual, preguntas_respondidas)
        
        if result['success']:
            print("🎉 EXITO TOTAL: Archivo guardado en Drive de la cuenta de servicio!")
            print(f"Archivo: {result['file_name']}")
            print(f"Link: {result['link']}")
        else:
            print(f"❌ ERROR: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")

if __name__ == "__main__":
    test_service_account()
