# Integración con Google Drive para guardar resultados
# Usa OAuth con la cuenta del administrador

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import json
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'client_credentials.json'
DRIVE_FOLDER_ID = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def save_pdf_to_drive(pdf_path):
    """Sube un archivo PDF a Google Drive"""
    try:
        if not os.path.exists(pdf_path):
            return {'success': False, 'error': f'Archivo no encontrado: {pdf_path}'}
        
        service = get_drive_service()
        filename = os.path.basename(pdf_path)
        
        # Metadata del archivo con timestamp en el nombre
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        drive_filename = f"[{timestamp}] {filename}"
        
        file_metadata = {
            'name': drive_filename, 
            'parents': [DRIVE_FOLDER_ID],
            'description': f'Reporte de evaluación generado el {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'

        }
        
        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id,name,webViewLink,webContentLink'
        ).execute()
        
        # Eliminar archivo local después de subirlo exitosamente
        try:
            os.remove(pdf_path)
            print(f"✅ Archivo local eliminado: {pdf_path}")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar archivo local: {e}")
        
        return {
            'success': True, 
            'file_id': file.get('id'),
            'file_name': file.get('name'), 
            'link': file.get('webViewLink'),
            'download_link': file.get('webContentLink')
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_session_to_drive(candidato_data, evaluacion_data):
    """Guarda los datos de la sesión como JSON en Drive"""
    try:
        service = get_drive_service()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidato_name = candidato_data.get('nombre_completo', 'Candidato').replace(' ', '_')
        filename = f"Datos_Evaluacion_{candidato_name}_{timestamp}.json"
        temp_file = f"temp_{filename}"
        
        session_data = {
            'candidato': candidato_data,
            'evaluacion': {
                'nivel_final': evaluacion_data.get('nivel', 1),
                'puntos_totales': evaluacion_data.get('puntos', 0),
                'respuestas_totales': len(evaluacion_data.get('respuestas', [])),
                'respuestas_correctas': len([r for r in evaluacion_data.get('respuestas', []) if r.get('correcta', False)]),
                'fecha_inicio': evaluacion_data.get('fecha_inicio'),
                'fecha_finalizacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'evaluacion_completa': evaluacion_data.get('evaluacion_completa', False),
                'terminacion_temprana': evaluacion_data.get('terminacion_temprana', False),
                'razon_terminacion': evaluacion_data.get('razon_terminacion')
            },
            'respuestas_detalladas': evaluacion_data.get('respuestas', [])
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        file_metadata = {
            'name': filename, 
            'parents': [DRIVE_FOLDER_ID],
            'description': f'Datos de evaluación de {candidato_data.get("nombre_completo", "Candidato")}'

        }
        media = MediaFileUpload(temp_file, mimetype='application/json')
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id,name,webViewLink'
        ).execute()
        
        # Limpiar archivo temporal
        os.remove(temp_file)
        
        return {
            'success': True, 
            'file_name': file.get('name'), 
            'link': file.get('webViewLink')
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
