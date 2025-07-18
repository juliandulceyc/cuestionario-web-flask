"""
Script para verificar archivos en la carpeta de Google Drive
"""
from drive_integration import GoogleDriveManager

def verificar_carpeta():
    print("=== VERIFICANDO ARCHIVOS EN CARPETA ===")
    
    try:
        drive_manager = GoogleDriveManager()
        folder_id = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"
        
        # Listar archivos en la carpeta
        query = f"'{folder_id}' in parents"
        results = drive_manager.service.files().list(
            q=query,
            pageSize=10,
            fields="nextPageToken, files(id, name, createdTime, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        print(f"Archivos encontrados en la carpeta: {len(files)}")
        print("-" * 50)
        
        for i, file in enumerate(files, 1):
            print(f"{i}. {file['name']}")
            print(f"   ID: {file['id']}")
            print(f"   Creado: {file['createdTime']}")
            print(f"   Link: {file.get('webViewLink', 'No disponible')}")
            print()
            
        if files:
            print("🎉 ¡Exito! Se encontraron archivos en la carpeta")
        else:
            print("❌ No se encontraron archivos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_carpeta()
