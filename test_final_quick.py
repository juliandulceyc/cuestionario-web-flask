#!/usr/bin/env python3
"""
Test final - Verificacion completa de Google Drive
"""

from drive_integration import save_session_to_drive
from datetime import datetime

def test_final_google_drive():
    print("=== TEST FINAL DE GOOGLE DRIVE ===")
    
    # Datos de prueba mínimos
    candidato_actual = {
        'datos_personales': {
            'nombre_completo': 'Test Final',
            'documento': '12345678',
            'email': 'test@test.com'
        },
        'nivel': 1,
        'puntos': 20,
        'respuestas_correctas_nivel': 2,
        'preguntas_mostradas': [1, 2]
    }
    
    preguntas_respondidas = [
        {
            'id': 1,
            'pregunta': 'Pregunta test 1',
            'nivel': 1,
            'fecha_respuesta': datetime.now().isoformat()
        }
    ]
    
    print("Ejecutando save_session_to_drive...")
    
    try:
        result = save_session_to_drive(candidato_actual, preguntas_respondidas)
        
        print(f"\nRESULTADO:")
        print(f"Success: {result.get('success')}")
        
        if result.get('success'):
            print("SUCCESS: Google Drive funciona correctamente!")
            print(f"Archivo: {result.get('file_name')}")
            print(f"Link: {result.get('link')}")
            return True
        else:
            print(f"ERROR: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"EXCEPCION: {e}")
        return False

if __name__ == "__main__":
    success = test_final_google_drive()
    if success:
        print("\n🎉 SISTEMA LISTO PARA USAR!")
    else:
        print("\n❌ Aún hay problemas con Google Drive")
