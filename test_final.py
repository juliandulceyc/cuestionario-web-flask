#!/usr/bin/env python3
"""
Test final de la funcionalidad completa
"""

from drive_integration import save_session_to_drive
from datetime import datetime

def test_complete_flow():
    print("TEST FINAL: Funcionalidad completa")
    print("=" * 50)
    
    # Simular datos de candidato completos
    candidato_actual = {
        'datos_personales': {
            'nombre_completo': 'Juan Perez Test',
            'documento': '12345678',
            'email': 'juan.test@email.com',
            'telefono': '555-1234',
            'fecha_evaluacion': datetime.now().isoformat()
        },
        'nivel': 3,
        'puntos': 80,
        'respuestas_correctas_nivel': 2,
        'preguntas_mostradas': [1, 5, 12, 25, 30],
        'respuestas_detalladas': [
            {
                'pregunta_id': 1,
                'pregunta_texto': 'Pregunta sobre redes',
                'nivel': 1,
                'respuesta_candidato': 0,
                'respuesta_correcta': 0,
                'es_correcta': True,
                'timestamp': datetime.now().isoformat()
            },
            {
                'pregunta_id': 5,
                'pregunta_texto': 'Pregunta sobre firewalls',
                'nivel': 2,
                'respuesta_candidato': 1,
                'respuesta_correcta': 2,
                'es_correcta': False,
                'timestamp': datetime.now().isoformat()
            }
        ],
        'fecha_inicio': datetime.now().isoformat(),
        'fecha_finalizacion': datetime.now().isoformat(),
        'evaluacion_completa': True
    }
    
    preguntas_respondidas = [
        {
            'id': 1,
            'pregunta': 'Pregunta sobre redes',
            'nivel': 1,
            'fecha_respuesta': datetime.now().isoformat()
        },
        {
            'id': 5,
            'pregunta': 'Pregunta sobre firewalls',
            'nivel': 2,
            'fecha_respuesta': datetime.now().isoformat()
        }
    ]
    
    print("Datos de prueba preparados")
    print(f"Candidato: {candidato_actual['datos_personales']['nombre_completo']}")
    print(f"Puntos: {candidato_actual['puntos']}")
    print(f"Nivel alcanzado: {candidato_actual['nivel']}")
    print(f"Preguntas respondidas: {len(candidato_actual['respuestas_detalladas'])}")
    
    # Ejecutar el guardado
    try:
        print("\nEjecutando save_session_to_drive...")
        result = save_session_to_drive(candidato_actual, preguntas_respondidas)
        
        print("\nRESULTADO:")
        print(f"Success: {result.get('success', 'N/A')}")
        
        if result.get('success'):
            print("EXITO: Google Drive integration funciona correctamente!")
            print(f"Archivo: {result.get('file_name', 'N/A')}")
            print(f"ID: {result.get('file_id', 'N/A')}")
            print(f"Link: {result.get('link', 'N/A')}")
            print("\nEl sistema está listo para usar en producción.")
        else:
            print(f"ERROR: {result.get('error', 'Error desconocido')}")
            print("Revisar configuración de Google Drive.")
            
    except Exception as e:
        print(f"EXCEPCION: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_complete_flow()
