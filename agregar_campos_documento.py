"""
Script para agregar campos tipo_documento y numero_documento a la tabla candidatos
Ejecutar una sola vez: python agregar_campos_documento.py
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener URL de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://empresa_user:qwerty@localhost:5432/empresa_db')

def agregar_columnas():
    """Agrega las columnas tipo_documento y numero_documento a la tabla candidatos"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🔄 Verificando si las columnas ya existen...")
        
        # Verificar si la columna tipo_documento ya existe
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='candidatos' AND column_name='tipo_documento';
        """)
        tipo_doc_exists = cur.fetchone() is not None
        
        # Verificar si la columna numero_documento ya existe
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='candidatos' AND column_name='numero_documento';
        """)
        num_doc_exists = cur.fetchone() is not None
        
        # Agregar columna tipo_documento si no existe
        if not tipo_doc_exists:
            print("➕ Agregando columna 'tipo_documento'...")
            cur.execute("""
                ALTER TABLE candidatos 
                ADD COLUMN tipo_documento VARCHAR(10);
            """)
            print("✅ Columna 'tipo_documento' agregada exitosamente")
        else:
            print("ℹ️  Columna 'tipo_documento' ya existe")
        
        # Agregar columna numero_documento si no existe
        if not num_doc_exists:
            print("➕ Agregando columna 'numero_documento'...")
            cur.execute("""
                ALTER TABLE candidatos 
                ADD COLUMN numero_documento VARCHAR(50);
            """)
            print("✅ Columna 'numero_documento' agregada exitosamente")
        else:
            print("ℹ️  Columna 'numero_documento' ya existe")
        
        # Confirmar cambios
        conn.commit()
        
        # Mostrar estructura actualizada
        print("\n📋 Estructura actual de la tabla 'candidatos':")
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name='candidatos'
            ORDER BY ordinal_position;
        """)
        
        columnas = cur.fetchall()
        for col in columnas:
            col_name = col[0]
            col_type = col[1]
            col_length = col[2] if col[2] else ""
            print(f"  - {col_name}: {col_type}{f'({col_length})' if col_length else ''}")
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
        print("\n✅ ¡Migración completada exitosamente!")
        print("\n📝 Nota: Los candidatos existentes tendrán estos campos en NULL.")
        print("   Puedes actualizarlos manualmente desde el panel de administración.")
        
    except Exception as e:
        print(f"\n❌ Error al agregar columnas: {e}")
        print("\nAsegúrate de que:")
        print("  1. El archivo .env existe con DATABASE_URL correcta")
        print("  2. La base de datos está corriendo")
        print("  3. El usuario tiene permisos para modificar la tabla")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 MIGRACIÓN DE BASE DE DATOS")
    print("   Agregando campos: tipo_documento y numero_documento")
    print("=" * 60)
    print()
    
    respuesta = input("¿Deseas continuar? (s/n): ").lower().strip()
    
    if respuesta == 's':
        print()
        agregar_columnas()
    else:
        print("\n❌ Operación cancelada")
