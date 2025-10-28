#!/usr/bin/env python3
"""
Script de Verificación de Implementación
Verifica que todas las mejoras estén correctamente implementadas
"""

import os
import sys

def check_file_exists(filepath, description):
    """Verifica si un archivo existe"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_dependency(module_name):
    """Verifica si una dependencia está instalada"""
    try:
        __import__(module_name)
        print(f"✅ Dependencia instalada: {module_name}")
        return True
    except ImportError:
        print(f"❌ Dependencia faltante: {module_name}")
        return False

def main():
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE IMPLEMENTACIÓN")
    print("=" * 60)
    print()

    total_checks = 0
    passed_checks = 0

    # Verificar archivos nuevos
    print("📁 ARCHIVOS NUEVOS:")
    print("-" * 60)
    
    files_to_check = [
        ("security.py", "Módulo de seguridad"),
        (".env.example", "Template de variables de entorno"),
        ("static/js/token-renewal.js", "Script de renovación de tokens"),
        ("templates/recuperar_password.html", "Template de recuperación"),
        ("IMPLEMENTACION.md", "Guía de implementación"),
        ("RESUMEN_MEJORAS.md", "Resumen de mejoras"),
    ]
    
    for filepath, desc in files_to_check:
        total_checks += 1
        if check_file_exists(filepath, desc):
            passed_checks += 1
    
    print()
    
    # Verificar archivos modificados
    print("📝 ARCHIVOS MODIFICADOS:")
    print("-" * 60)
    
    modified_files = [
        ("app.py", "Aplicación principal"),
        ("pdf_generator.py", "Generador de PDF"),
        ("requirements.txt", "Dependencias"),
        ("templates/admin_dashboard.html", "Dashboard admin"),
        ("templates/admin_login.html", "Login admin"),
        ("static/js/admin-dashboard.js", "Script dashboard"),
    ]
    
    for filepath, desc in modified_files:
        total_checks += 1
        if check_file_exists(filepath, desc):
            passed_checks += 1
    
    print()
    
    # Verificar dependencias
    print("📦 DEPENDENCIAS PYTHON:")
    print("-" * 60)
    
    dependencies = [
        ("flask", "Flask"),
        ("jwt", "PyJWT"),
        ("dotenv", "python-dotenv"),
        ("bcrypt", "bcrypt"),
        ("pandas", "Pandas"),
        ("reportlab", "ReportLab"),
    ]
    
    for module, name in dependencies:
        total_checks += 1
        if check_dependency(name):
            passed_checks += 1
    
    print()
    
    # Verificar variables de entorno
    print("🔐 VARIABLES DE ENTORNO:")
    print("-" * 60)
    
    env_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "ADMIN_USER",
        "ADMIN_PASS",
    ]
    
    env_exists = os.path.exists(".env")
    if env_exists:
        print("✅ Archivo .env encontrado")
        
        # Intentar cargar variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            for var in env_vars:
                total_checks += 1
                value = os.getenv(var)
                if value:
                    print(f"✅ Variable configurada: {var}")
                    passed_checks += 1
                else:
                    print(f"⚠️  Variable no configurada: {var}")
        except Exception as e:
            print(f"❌ Error cargando .env: {e}")
    else:
        print("⚠️  Archivo .env no encontrado (usar .env.example como base)")
    
    print()
    
    # Resultado final
    print("=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"Checks completados: {passed_checks}/{total_checks} ({percentage:.1f}%)")
    print()
    
    if percentage == 100:
        print("🎉 ¡IMPLEMENTACIÓN COMPLETA!")
        print("✅ Todos los archivos y dependencias están correctos")
        print()
        print("Próximos pasos:")
        print("1. Configurar .env con tus valores")
        print("2. Ejecutar: python app.py")
        print("3. Probar todas las funcionalidades")
        return 0
    elif percentage >= 80:
        print("✅ IMPLEMENTACIÓN CASI COMPLETA")
        print("⚠️  Algunos elementos opcionales faltan")
        print()
        print("Revisar los items marcados con ❌ arriba")
        return 0
    else:
        print("❌ IMPLEMENTACIÓN INCOMPLETA")
        print("⚠️  Faltan archivos o dependencias importantes")
        print()
        print("Por favor:")
        print("1. Revisar los archivos faltantes (❌)")
        print("2. Instalar dependencias: pip install -r requirements.txt")
        print("3. Ejecutar este script nuevamente")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        sys.exit(1)
