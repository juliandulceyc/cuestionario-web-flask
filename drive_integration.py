"""
Integración con Google Drive para guardar resultados del cuestionario
Usa OAuth con la cuenta del administrador - sin autenticación de aspirantes
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import os
from datetime import datetime

class GoogleDriveManager:
    def __init__(self, credentials_file='client_credentials.json'):
        """
        Inicializa el manager de Google Drive con OAuth del administrador
        
        Args:
            credentials_file: Archivo JSON con las credenciales OAuth
        """
        self.credentials_file = credentials_file
        self.service = None
        self.setup_service()
    
    def setup_service(self):
        """Configura el servicio de Google Drive con OAuth"""
        try:
            # Scopes necesarios para Drive
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            creds = None
            token_file = 'token.json'
            
            # El archivo token.json almacena los tokens del administrador
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # Si no hay credenciales válidas, autenticar al administrador
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                # Guardar las credenciales para futuras ejecuciones
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            # Crear servicio
            self.service = build('drive', 'v3', credentials=creds)
            print("EXITO: Conexion a Google Drive establecida con OAuth (administrador)")
            
        except Exception as e:
            print(f"ERROR: Error conectando a Google Drive: {e}")
            self.service = None
    
    def save_user_results(self, usuario_data, folder_id=None):
        """
        Guarda los resultados del usuario en Google Drive
        
        Args:
            usuario_data: Diccionario con datos del usuario
            folder_id: ID de la carpeta en Drive (opcional)
        """
        if not self.service:
            print("ERROR: No hay conexion a Google Drive")
            return {'success': False, 'error': 'No hay conexión a Google Drive'}
        
        temp_file = None  # Inicializar variable para uso en except
        
        try:
            # Verificar que el folder_id es válido
            if folder_id:
                print(f"INFO: Verificando acceso a carpeta: {folder_id}")
                # Intentar acceder a la carpeta
                try:
                    folder_info = self.service.files().get(fileId=folder_id).execute()
                    print(f"EXITO: Carpeta encontrada: {folder_info.get('name')}")
                except Exception as folder_error:
                    print(f"ERROR: Error accediendo a carpeta: {folder_error}")
                    return {'success': False, 'error': f'No se puede acceder a la carpeta: {folder_error}'}
            
            # Preparar datos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resultados_cuestionario_{timestamp}.json"
            
            # Crear archivo temporal con nombre único
            temp_file = f"temp_resultados_cuestionario_{timestamp}.json"
            print(f"INFO: Creando archivo temporal: {temp_file}")
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(usuario_data, f, ensure_ascii=False, indent=2)
            
            print("EXITO: Archivo temporal creado correctamente")
            
            # Metadatos del archivo
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            print("INFO: Subiendo archivo a Drive...")
            print(f"Metadatos: {file_metadata}")
            
            # Subir archivo
            media = MediaFileUpload(temp_file, mimetype='application/json')
            print(f"Media objeto creado para: {temp_file}")
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            print(f"Archivo creado en Drive: {file}")
            
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print("INFO: Archivo temporal eliminado")
                except PermissionError as pe:
                    print(f"WARNING: No se pudo eliminar archivo temporal inmediatamente: {pe}")
                    # Intentar cerrar todos los handles y volver a intentar
                    import time
                    time.sleep(1)
                    try:
                        os.remove(temp_file)
                        print("INFO: Archivo temporal eliminado en segundo intento")
                    except Exception as e2:
                        print(f"WARNING: Archivo temporal no eliminado: {e2} - Se eliminará automáticamente")
            
            print(f"EXITO: Archivo guardado en Drive: {file.get('name')}")
            print(f"LINK: {file.get('webViewLink')}")
            
            return {
                'success': True,
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'link': file.get('webViewLink')
            }
            
        except Exception as e:
            print(f"ERROR: Error detallado guardando en Drive: {type(e).__name__}: {e}")
            # Limpiar archivo temporal si existe
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print("INFO: Archivo temporal limpiado después del error")
                except Exception as cleanup_error:
                    print(f"WARNING: No se pudo limpiar archivo temporal: {cleanup_error}")
            return {'success': False, 'error': f'{type(e).__name__}: {str(e)}'}
    
    def create_folder_if_not_exists(self, folder_name="Evaluaciones_Candidatos"):
        """
        Crea una carpeta en Drive si no existe y devuelve su ID
        """
        try:
            # Buscar si ya existe una carpeta con ese nombre
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                print(f"EXITO: Carpeta existente encontrada: {folder_name} (ID: {folder_id})")
                return folder_id
            else:
                # Crear nueva carpeta
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id,name,webViewLink'
                ).execute()
                
                folder_id = folder.get('id')
                print(f"EXITO: Nueva carpeta creada: {folder_name} (ID: {folder_id})")
                print(f"LINK: {folder.get('webViewLink')}")
                return folder_id
                
        except Exception as e:
            print(f"ERROR: No se pudo crear/encontrar carpeta: {e}")
            return None

    def save_excel_backup(self, excel_file_path, folder_id=None):
        """
        Guarda una copia de seguridad del Excel en Drive
        
        Args:
            excel_file_path: Ruta del archivo Excel
            folder_id: ID de la carpeta en Drive
        """
        if not self.service:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_preguntas_{timestamp}.xlsx"
            
            file_metadata = {
                'name': backup_name,
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaFileUpload(
                excel_file_path, 
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name'
            ).execute()
            
            print(f"EXITO: Backup del Excel guardado: {file.get('name')}")
            return True
            
        except Exception as e:
            print(f"ERROR: Error guardando backup: {e}")
            return False

# Función para integrar con la app Flask
def save_session_to_drive(usuario_actual, preguntas_respondidas):
    """
    Guarda la sesión actual del usuario en Google Drive
    
    Args:
        usuario_actual: Estado actual del usuario
        preguntas_respondidas: Lista de preguntas respondidas
    """
    print("DEBUG: Iniciando save_session_to_drive")
    print(f"DEBUG: usuario_actual keys: {list(usuario_actual.keys()) if usuario_actual else 'None'}")
    print(f"DEBUG: preguntas_respondidas count: {len(preguntas_respondidas) if preguntas_respondidas else 0}")
    
    drive_manager = GoogleDriveManager()
    
    if not drive_manager.service:
        print("ERROR: No se pudo crear el servicio de Google Drive")
        return {'success': False, 'error': 'No hay conexión a Google Drive'}
    
    # Preparar datos para guardar
    session_data = {
        'timestamp': datetime.now().isoformat(),
        'datos_personales': usuario_actual.get('datos_personales', {}),
        'evaluacion': {
            'nivel': usuario_actual.get('nivel', 1),
            'puntos': usuario_actual.get('puntos', 0),
            'respuestas_correctas_nivel': usuario_actual.get('respuestas_correctas_nivel', 0),
            'total_preguntas_respondidas': len(usuario_actual.get('preguntas_mostradas', [])),
            'preguntas_mostradas': usuario_actual.get('preguntas_mostradas', [])
        },
        'preguntas_respondidas': preguntas_respondidas,
        'metadata': {
            'version_app': '1.0',
            'tipo_evaluacion': 'Cuestionario Web Interactivo',
            'fecha_evaluacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    # Usar tu carpeta existente en Google Drive
    DRIVE_FOLDER_ID = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"  # Tu carpeta Resultados_Evaluacion
    
    print(f"DEBUG: Guardando en carpeta especificada: {DRIVE_FOLDER_ID}")
    
    # Guardar en Drive
    result = drive_manager.save_user_results(session_data, folder_id=DRIVE_FOLDER_ID)
    
    print(f"DEBUG: Resultado final de save_user_results: {result}")
    return result

# Configuración para uso con Service Account
def setup_drive_credentials():
    """
    Instrucciones para configurar credenciales de Service Account
    """
    instructions = """
    CONFIGURACIÓN DE GOOGLE DRIVE CON SERVICE ACCOUNT:
    
    1. Ve a Google Cloud Console (console.cloud.google.com)
    2. Crea un nuevo proyecto o selecciona uno existente
    3. Habilita la API de Google Drive
    4. Ve a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
    5. Descarga el archivo JSON de credenciales
    6. Renómbralo como 'credentials.json'
    7. Colócalo en el directorio del proyecto
    
    VENTAJAS:
    - No requiere autenticación de usuarios
    - Perfecto para aplicaciones web públicas
    - Los resultados se guardan en el Drive de la cuenta de servicio
    - Acceso controlado y centralizado
    """
    return instructions

if __name__ == "__main__":
    print(setup_drive_credentials())
