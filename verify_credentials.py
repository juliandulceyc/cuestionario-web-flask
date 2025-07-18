#!/usr/bin/env python3
"""
Verificar que el nuevo archivo credentials.json es válido
"""

import json
import os

def verify_credentials():
    print("=== VERIFICANDO CREDENTIALS.JSON ===")
    
    if not os.path.exists('credentials.json'):
        print("❌ ERROR: No se encuentra credentials.json")
        print("Por favor, descarga el archivo de Google Cloud Console")
        return False
    
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        
        for field in required_fields:
            if field not in creds:
                print(f"❌ ERROR: Falta el campo '{field}' en credentials.json")
                return False
        
        print("✅ EXITO: credentials.json es válido")
        print(f"   Proyecto: {creds['project_id']}")
        print(f"   Email: {creds['client_email']}")
        print(f"   Tipo: {creds['type']}")
        
        # Verificar que la clave privada parece válida
        if creds['private_key'].startswith('-----BEGIN PRIVATE KEY-----'):
            print("✅ EXITO: Clave privada tiene formato correcto")
        else:
            print("❌ ERROR: Clave privada no tiene formato correcto")
            return False
        
        return True
        
    except json.JSONDecodeError:
        print("❌ ERROR: credentials.json no es un JSON válido")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    if verify_credentials():
        print("\n🎉 Archivo credentials.json está listo!")
        print("Ahora puedes ejecutar: venv\\Scripts\\python.exe test_final_quick.py")
    else:
        print("\n❌ Necesitas descargar un nuevo archivo credentials.json")
        print("Ve a Google Cloud Console y crea nuevas credenciales")
