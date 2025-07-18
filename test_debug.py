"""
Script de prueba simple para verificar OAuth y Google Drive
"""
from drive_integration import GoogleDriveManager

def test_simple():
    print("=== PRUEBA SIMPLE OAUTH + DRIVE ===")
    
    try:
        print("Importando GoogleDriveManager...")
        # Crear manager
        drive_manager = GoogleDriveManager()
        print("✅ Manager creado")
        
        print("Verificando servicio...")
        if drive_manager.service:
            print("✅ Servicio OAuth establecido")
            
            # Probar acceso a la carpeta específica
            folder_id = "1xYYkbJniRP1K7PawanI7741M2pEJ-RkD"
            print(f"Probando acceso a carpeta: {folder_id}")
            
            try:
                folder_info = drive_manager.service.files().get(fileId=folder_id).execute()
                print(f"✅ Carpeta encontrada: '{folder_info.get('name')}'")
                
                # Datos de prueba mínimos
                test_data = {"mensaje": "Prueba exitosa", "timestamp": "2025-07-17"}
                print("Datos de prueba preparados")
                
                print("Intentando guardar archivo...")
                result = drive_manager.save_user_results(test_data, folder_id=folder_id)
                
                print(f"Resultado completo: {result}")
                
                if result.get('success'):
                    print("🎉 ¡EXITO TOTAL!")
                    print(f"Archivo: {result.get('file_name')}")
                    if 'link' in result:
                        print(f"Link: {result['link']}")
                else:
                    print(f"❌ Error: {result.get('error', 'Error desconocido')}")
                    
            except Exception as e:
                print(f"❌ Error con carpeta: {e}")
                import traceback
                traceback.print_exc()
                
        else:
            print("❌ No se pudo crear el servicio")
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
