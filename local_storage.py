"""
Sistema de almacenamiento local para resultados de evaluaciones
Ideal para aplicativos públicos sin necesidad de autenticación
"""

import json
import os
from datetime import datetime
from pathlib import Path

class LocalStorageManager:
    def __init__(self, storage_dir='resultados_evaluaciones'):
        """
        Inicializa el manager de almacenamiento local
        
        Args:
            storage_dir: Directorio donde guardar los resultados
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_user_results(self, usuario_data, crear_pdf=True):
        """
        Guarda los resultados del usuario localmente
        
        Args:
            usuario_data: Diccionario con datos del usuario
            crear_pdf: Si generar PDF automáticamente
        """
        try:
            # Preparar timestamp y nombre
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_candidato = usuario_data.get('datos_personales', {}).get('nombre', 'Candidato')
            nombre_archivo = f"evaluacion_{nombre_candidato.replace(' ', '_')}_{timestamp}"
            
            # Guardar JSON
            json_file = self.storage_dir / f"{nombre_archivo}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(usuario_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ EXITO: Resultados guardados en {json_file}")
            
            # Generar PDF si se solicita
            pdf_file = None
            if crear_pdf:
                try:
                    from pdf_generator import generar_reporte_pdf
                    pdf_file = self.storage_dir / f"{nombre_archivo}.pdf"
                    generar_reporte_pdf(usuario_data, str(pdf_file))
                    print(f"✅ EXITO: PDF generado en {pdf_file}")
                except Exception as pdf_error:
                    print(f"⚠️ WARNING: No se pudo generar PDF: {pdf_error}")
            
            return {
                'success': True,
                'json_file': str(json_file),
                'pdf_file': str(pdf_file) if pdf_file else None,
                'candidato': nombre_candidato,
                'timestamp': timestamp
            }
            
        except Exception as e:
            print(f"❌ ERROR: Error guardando localmente: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_evaluations(self):
        """Lista todas las evaluaciones guardadas"""
        try:
            json_files = list(self.storage_dir.glob("*.json"))
            pdf_files = list(self.storage_dir.glob("*.pdf"))
            
            evaluaciones = []
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Buscar PDF correspondiente
                    pdf_correspondiente = json_file.with_suffix('.pdf')
                    tiene_pdf = pdf_correspondiente.exists()
                    
                    evaluaciones.append({
                        'archivo_json': str(json_file),
                        'archivo_pdf': str(pdf_correspondiente) if tiene_pdf else None,
                        'candidato': data.get('datos_personales', {}).get('nombre', 'Sin nombre'),
                        'email': data.get('datos_personales', {}).get('email', 'Sin email'),
                        'puntos': data.get('evaluacion', {}).get('puntos', 0),
                        'nivel': data.get('evaluacion', {}).get('nivel', 1),
                        'fecha': data.get('timestamp', 'Sin fecha'),
                        'tiene_pdf': tiene_pdf
                    })
                except Exception as e:
                    print(f"Error leyendo {json_file}: {e}")
            
            return evaluaciones
            
        except Exception as e:
            print(f"Error listando evaluaciones: {e}")
            return []
    
    def export_to_drive_batch(self, drive_manager=None):
        """
        Exporta todas las evaluaciones a Google Drive (cuando sea posible)
        """
        if not drive_manager:
            print("⚠️ No hay manager de Drive configurado")
            return False
        
        evaluaciones = self.list_evaluations()
        exportados = 0
        
        for eval_data in evaluaciones:
            try:
                # Leer datos JSON
                with open(eval_data['archivo_json'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Intentar subir a Drive
                result = drive_manager.save_user_results(data)
                if result['success']:
                    exportados += 1
                    print(f"✅ Exportado: {eval_data['candidato']}")
                else:
                    print(f"❌ Error exportando {eval_data['candidato']}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Error procesando {eval_data['candidato']}: {e}")
        
        print(f"📊 Resumen: {exportados}/{len(evaluaciones)} evaluaciones exportadas")
        return exportados > 0

# Función para integrar con la app Flask
def save_session_locally(usuario_actual, preguntas_respondidas):
    """
    Guarda la sesión actual del usuario localmente
    
    Args:
        usuario_actual: Estado actual del usuario
        preguntas_respondidas: Lista de preguntas respondidas
    """
    print("DEBUG: Iniciando save_session_locally")
    
    storage_manager = LocalStorageManager()
    
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
    
    # Guardar localmente
    result = storage_manager.save_user_results(session_data, crear_pdf=True)
    
    print(f"DEBUG: Resultado final de save_session_locally: {result}")
    return result

if __name__ == "__main__":
    # Demostración del sistema
    storage = LocalStorageManager()
    evaluaciones = storage.list_evaluations()
    print(f"📊 Evaluaciones guardadas: {len(evaluaciones)}")
    for eval_data in evaluaciones:
        print(f"- {eval_data['candidato']}: {eval_data['puntos']} puntos")
