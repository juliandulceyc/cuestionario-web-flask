"""
Prueba OAuth como administrador - los aspirantes no se autentican
"""
from drive_integration import save_session_to_drive

def test_oauth_admin():
    print("=== PROBANDO OAUTH COMO ADMINISTRADOR ===")
    
    # Datos de prueba de un aspirante
    usuario_actual = {
        'datos_personales': {
            'nombre': 'María García',
            'email': 'maria.prueba@test.com',
            'telefono': '987654321'
        },
        'nivel': 3,
        'puntos': 92,
        'respuestas_correctas_nivel': 9,
        'preguntas_mostradas': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
    
    preguntas_respondidas = [
        {
            'pregunta': '¿Cuál es la capital de España?',
            'respuesta_usuario': 'Madrid',
            'es_correcta': True,
            'tiempo_respuesta': 3.8
        },
        {
            'pregunta': '¿Cuánto es 5+3?',
            'respuesta_usuario': '8',
            'es_correcta': True,
            'tiempo_respuesta': 1.9
        }
    ]
    
    try:
        result = save_session_to_drive(usuario_actual, preguntas_respondidas)
        
        if result['success']:
            print("🎉 EXITO TOTAL: Archivo guardado en TU Google Drive!")
            print(f"Archivo: {result['file_name']}")
            print(f"Link: {result['link']}")
            print("\n✅ PERFECTO: Los aspirantes podrán usar la app sin autenticarse")
        else:
            print(f"❌ ERROR: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")

if __name__ == "__main__":
    test_oauth_admin()
