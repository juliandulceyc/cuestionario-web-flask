#!/usr/bin/env python3
"""
Script para verificar acceso a carpeta específica de Google Drive
"""

from drive_integration import GoogleDriveManager

def verify_specific_folder():
    """Verificar acceso a la carpeta específica"""
    print("=== VERIFICANDO ACCESO A CARPETA ESPECIFICA ===")
    
    # ID de la carpeta que quieres usar
    FOLDER_ID = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"
    
    manager = GoogleDriveManager()
    
    if not manager.service:
        print("ERROR: No se pudo conectar a Google Drive")
        return
    
    print(f"Verificando carpeta: {FOLDER_ID}")
    print(f"Cuenta de servicio: evaluacion-service@ornate-producer-403316.iam.gserviceaccount.com")
    print()
    
    try:
        folder_info = manager.service.files().get(fileId=FOLDER_ID).execute()
        print("✅ EXITO: Carpeta encontrada y accesible")
        print(f"   Nombre: {folder_info.get('name')}")
        print(f"   ID: {folder_info.get('id')}")
        print(f"   Link: {folder_info.get('webViewLink', 'N/A')}")
        print()
        print("La carpeta esta correctamente configurada.")
        
    except Exception as e:
        print("❌ ERROR: No se puede acceder a la carpeta")
        print(f"   Error: {e}")
        print()
        print("SOLUCION:")
        print("1. Ve a Google Drive en tu navegador")
        print("2. Encuentra o crea la carpeta donde quieres guardar los resultados")
        print("3. Clic derecho → Compartir")
        print("4. Agregar: evaluacion-service@ornate-producer-403316.iam.gserviceaccount.com")
        print("5. Darle permisos de 'Editor'")
        print("6. Copiar el ID de la carpeta desde la URL")
        print(f"7. Actualizar DRIVE_FOLDER_ID en drive_integration.py con el nuevo ID")

if __name__ == "__main__":
    verify_specific_folder()
