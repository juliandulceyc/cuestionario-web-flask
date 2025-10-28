"""
Script para actualizar candidatos existentes con tipo y número de documento
Ejecutar: python actualizar_candidatos_existentes.py
"""

import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://empresa_user:qwerty@localhost:5432/empresa_db')

def actualizar_candidatos():
    """Actualiza los candidatos existentes con información de documentos"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("📋 Candidatos sin documento registrado:\n")
        
        # Obtener candidatos sin documento
        cur.execute("""
            SELECT id, codigo, nombre_completo, email 
            FROM candidatos 
            WHERE numero_documento IS NULL OR numero_documento = ''
            ORDER BY id;
        """)
        
        candidatos = cur.fetchall()
        
        if not candidatos:
            print("✅ Todos los candidatos tienen documento registrado!")
            cur.close()
            conn.close()
            return
        
        for candidato in candidatos:
            id_candidato, codigo, nombre, email = candidato
            print(f"ID: {id_candidato} | Código: {codigo} | Nombre: {nombre}")
        
        print("\n" + "="*60)
        print("Ahora actualizaremos los documentos de estos candidatos")
        print("="*60)
        
        for candidato in candidatos:
            id_candidato, codigo, nombre, email = candidato
            
            print(f"\n👤 Candidato: {nombre}")
            print(f"   Código: {codigo}")
            
            # Solicitar tipo de documento
            print("\nTipos de documento disponibles:")
            print("  1. CC - Cédula de ciudadanía")
            print("  2. TI - Tarjeta de identidad")
            print("  3. CE - Cédula de extranjería")
            print("  4. PA - Pasaporte")
            print("  5. Saltar (dejar en NULL)")
            
            opcion = input("\nSelecciona el tipo (1-5): ").strip()
            
            if opcion == '5':
                print("⏭️  Candidato omitido")
                continue
            
            tipos = {'1': 'CC', '2': 'TI', '3': 'CE', '4': 'PA'}
            tipo_doc = tipos.get(opcion, 'CC')
            
            # Solicitar número de documento
            numero_doc = input(f"Ingresa el número de documento ({tipo_doc}): ").strip()
            
            if not numero_doc:
                print("⏭️  Sin número, candidato omitido")
                continue
            
            # Actualizar en la base de datos
            cur.execute("""
                UPDATE candidatos 
                SET tipo_documento = %s, numero_documento = %s 
                WHERE id = %s;
            """, (tipo_doc, numero_doc, id_candidato))
            
            print(f"✅ Actualizado: {tipo_doc} - {numero_doc}")
        
        # Confirmar cambios
        conn.commit()
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("📊 RESUMEN DE ACTUALIZACIONES")
        print("="*60 + "\n")
        
        cur.execute("""
            SELECT codigo, nombre_completo, tipo_documento, numero_documento 
            FROM candidatos 
            WHERE tipo_documento IS NOT NULL
            ORDER BY id;
        """)
        
        actualizados = cur.fetchall()
        
        for candidato in actualizados:
            codigo, nombre, tipo_doc, numero_doc = candidato
            print(f"✅ {nombre}")
            print(f"   🆔 {tipo_doc}: {numero_doc}")
            print(f"   🔑 Código: {codigo}\n")
        
        cur.close()
        conn.close()
        
        print("✅ ¡Actualización completada!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ACTUALIZAR CANDIDATOS EXISTENTES")
    print("   Agregar tipo y número de documento")
    print("=" * 60)
    print()
    
    actualizar_candidatos()
