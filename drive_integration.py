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
    try:
        if not os.path.exists(pdf_path):
            return {'success': False, 'error': f'Archivo no encontrado: {pdf_path}'}
        
        service = get_drive_service()
        filename = os.path.basename(pdf_path)
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
        file = service.files().create(body=file_metadata, media_body=media, fields='id,name,webViewLink').execute()
        
        # Eliminar archivo local después de subirlo
        os.remove(pdf_path)
        
        return {'success': True, 'file_name': file.get('name'), 'link': file.get('webViewLink')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_session_to_drive(usuario_actual, preguntas_respondidas):
    try:
        service = get_drive_service()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultados_cuestionario_{timestamp}.json"
        temp_file = f"temp_{filename}"
        
        session_data = {
            'datos_personales': usuario_actual.get('datos_personales', {}),
            'evaluacion': {
                'nivel': usuario_actual.get('nivel', 1),
                'puntos': usuario_actual.get('puntos', 0),
                'respuestas_correctas_nivel': usuario_actual.get('respuestas_correctas_nivel', 0),
                'preguntas_mostradas': usuario_actual.get('preguntas_mostradas', [])
            },
            'preguntas_respondidas': preguntas_respondidas,
            'fecha_evaluacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaFileUpload(temp_file, mimetype='application/json')
        file = service.files().create(body=file_metadata, media_body=media, fields='id,name,webViewLink').execute()
        
        os.remove(temp_file)
        return {'success': True, 'file_name': file.get('name'), 'link': file.get('webViewLink')}
    except Exception as e:
        return {'success': False, 'error': str(e)}
