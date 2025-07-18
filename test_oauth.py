"""
Script de prueba para verificar que OAuth funciona correctamente
"""
from drive_integration import GoogleDriveManager

def test_oauth_connection():
    print("=== PROBANDO CONEXION OAUTH ===")
    
    try:
        # Crear manager de Drive
        drive_manager = GoogleDriveManager()
        
        if drive_manager.service:
            print("✅ EXITO: Conexión OAuth establecida")
            
            # Probar acceso a carpeta
            folder_id = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"
            try:
                folder_info = drive_manager.service.files().get(fileId=folder_id).execute()
                print(f"✅ EXITO: Acceso a carpeta '{folder_info.get('name')}'")
                
                # Datos de prueba simples
                test_data = {
                    "test": True,
                    "timestamp": "2025-01-17 20:30:00",
                    "mensaje": "Prueba OAuth exitosa"
                }
                
                # Intentar guardar
                result = drive_manager.save_user_results(test_data, folder_id=folder_id)
                
                if result['success']:
                    print("🎉 EXITO TOTAL: Archivo guardado en Drive!")
                    print(f"Archivo: {result['file_name']}")
                    print(f"Link: {result['link']}")
                else:
                    print(f"❌ ERROR guardando: {result['error']}")
                    
            except Exception as e:
                print(f"❌ ERROR accediendo a carpeta: {str(e)}")
                print(f"Tipo de error: {type(e).__name__}")
                
                # Intentar listar archivos en la raíz para probar permisos
                try:
                    files = drive_manager.service.files().list(pageSize=5).execute()
                    print("✅ Permisos básicos de Drive funcionan")
                    print(f"Archivos encontrados: {len(files.get('files', []))}")
                except Exception as e2:
                    print(f"❌ ERROR en permisos básicos: {str(e2)}")
                
        else:
            print("❌ ERROR: No se pudo establecer conexión OAuth")
            
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")

if __name__ == "__main__":
    test_oauth_connection()
