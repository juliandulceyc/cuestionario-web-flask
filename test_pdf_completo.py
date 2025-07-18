"""
Script de prueba para generar un reporte PDF empresarial completo
"""
from pdf_generator import CandidateReportGenerator
from drive_integration import GoogleDriveManager
from datetime import datetime
import os

def generar_reporte_completo():
    print("=== GENERANDO REPORTE PDF EMPRESARIAL ===")
    
    # Datos de ejemplo más completos
    datos_candidato = {
        'datos_personales': {
            'nombre_completo': 'Julian Rodriguez Martinez',
            'documento': '1234567890',
            'email': 'julian.rodriguez@email.com',
            'telefono': '+57 300 123 4567',
            'fecha_evaluacion': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        },
        'evaluacion': {
            'nivel': 3,
            'puntos': 150,
            'respuestas_correctas_nivel': 8,
            'total_preguntas_respondidas': 15,
            'preguntas_mostradas': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        },
        'nivel': 3,
        'puntos': 150,
        'total_preguntas_respondidas': 15,
        'preguntas_respondidas': [
            {
                'pregunta': '¿Cómo se clasifican las aplicaciones en Palo Alto?',
                'respuesta_seleccionada': 'Por zona',
                'es_correcta': True,
                'puntos': 10
            },
            {
                'pregunta': '¿Qué protocolo se usa para VPN SSL?',
                'respuesta_seleccionada': 'HTTPS',
                'es_correcta': True,
                'puntos': 10
            },
            {
                'pregunta': '¿Cuál es el puerto estándar para SSH?',
                'respuesta_seleccionada': '22',
                'es_correcta': True,
                'puntos': 10
            }
        ],
        'metadata': {
            'version_app': '2.0',
            'tipo_evaluacion': 'Evaluación Técnica Cyberseguridad',
            'fecha_evaluacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'duracion_evaluacion': '25 minutos'
        }
    }
    
    try:
        # 1. Generar PDF
        print("1. Generando reporte PDF...")
        generator = CandidateReportGenerator()
        pdf_path = generator.generate_candidate_report(datos_candidato)
        print(f"✅ PDF generado: {pdf_path}")
        
        # 2. Verificar que el archivo existe
        if os.path.exists(pdf_path):
            print(f"✅ Archivo confirmado: {os.path.getsize(pdf_path)} bytes")
        else:
            print("❌ ERROR: Archivo PDF no encontrado")
            return
        
        # 3. Subir a Google Drive
        print("2. Subiendo a Google Drive...")
        drive_manager = GoogleDriveManager()
        
        if drive_manager.service:
            folder_id = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"
            
            from googleapiclient.http import MediaFileUpload
            
            filename = os.path.basename(pdf_path)
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(pdf_path, mimetype='application/pdf')
            
            pdf_file = drive_manager.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            print(f"✅ PDF subido a Drive: {pdf_file.get('name')}")
            print(f"📄 Link: {pdf_file.get('webViewLink')}")
            print(f"🔗 ID: {pdf_file.get('id')}")
            
        else:
            print("❌ ERROR: No se pudo conectar a Google Drive")
            
        print("\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print(f"📁 Archivo local: {pdf_path}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generar_reporte_completo()
