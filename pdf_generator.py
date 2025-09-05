import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Generador especializado de reportes PDF para evaluaciones"""
    
    def __init__(self):
        self.output_dir = "reportes_pdf"
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Asegura que existe el directorio de salida"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Directorio creado: {self.output_dir}")
    
    def generar_reporte_evaluacion(self, candidato_data: Dict[str, Any], evaluacion_data: Dict[str, Any]) -> str:
        """
        Genera reporte PDF completo de evaluación
        
        Args:
            candidato_data: Información del candidato
            evaluacion_data: Datos de la evaluación completa
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        try:
            # Generar nombre único del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_candidato = candidato_data.get('nombre_completo', 'Candidato').replace(' ', '_')
            filename = f"Evaluacion_{nombre_candidato}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Construir contenido del PDF
            story.extend(self._crear_encabezado(candidato_data, styles))
            story.extend(self._crear_resumen_resultados(evaluacion_data, styles))
            story.extend(self._crear_detalle_niveles(evaluacion_data, styles))
            story.extend(self._crear_estadisticas_adicionales(evaluacion_data, styles))
            story.extend(self._crear_pie_documento(styles))
            
            # Generar PDF
            doc.build(story)
            
            logger.info(f"PDF generado exitosamente: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            raise
    
    def _crear_encabezado(self, candidato_data: Dict[str, Any], styles) -> List:
        """Crea encabezado con información del candidato"""
        elementos = []
        
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1
        )
        
        elementos.append(Paragraph("REPORTE DE EVALUACIÓN TÉCNICA", title_style))
        elementos.append(Spacer(1, 20))
        
        # Información del candidato
        info_candidato = [
            ['Tipo de documento:', candidato_data.get('tipo_documento', '')],
            ['Número de documento:', candidato_data.get('numero_documento', '')],
            ['Nombre completo:', candidato_data.get('nombre_completo', 'N/A')],
            ['Email:', candidato_data.get('email', 'N/A')],
            ['Cargo:', candidato_data.get('cargo', 'N/A')],
            ['Código:', candidato_data.get('codigo', 'N/A')],
            ['Fecha Evaluación:', datetime.now().strftime("%d/%m/%Y %H:%M")],
                ['Tratamiento de datos:', 'Sí' if candidato_data.get('acepta_terminos') else 'No']
        ]
        
        tabla_info = Table(info_candidato, colWidths=[2*inch, 4*inch])
        tabla_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elementos.append(tabla_info)
        elementos.append(Spacer(1, 30))
        
        return elementos
    
    def _crear_resumen_resultados(self, evaluacion_data: Dict[str, Any], styles) -> List:
        """Crea resumen ejecutivo de resultados"""
        elementos = []
        
        elementos.append(Paragraph("RESUMEN DE RESULTADOS", styles['Heading2']))
        elementos.append(Spacer(1, 15))
        
        # Calcular estadísticas
        respuestas = evaluacion_data.get('respuestas', [])
        total_preguntas = len(respuestas)
        correctas = len([r for r in respuestas if r.get('correcta', False)])
        porcentaje = (correctas / max(total_preguntas, 1)) * 100
        puntos_totales = evaluacion_data.get('puntos', 0)
        nivel_final = evaluacion_data.get('nivel', 1)
        
        # Determinar calificación
        if porcentaje >= 90:
            calificacion = "EXCELENTE"
            color_calificacion = colors.green
        elif porcentaje >= 75:
            calificacion = "BUENO"
            color_calificacion = colors.blue
        elif porcentaje >= 60:
            calificacion = "REGULAR"
            color_calificacion = colors.orange
        else:
            calificacion = "INSUFICIENTE"
            color_calificacion = colors.red
        
        # Tabla de resultados
        datos_resultados = [
            ['Preguntas Respondidas:', f"{total_preguntas}/40"],
            ['Respuestas Correctas:', f"{correctas}/{total_preguntas}"],
            ['Porcentaje de Acierto:', f"{porcentaje:.1f}%"],
            ['Puntos Obtenidos:', f"{puntos_totales:.1f}"],
            ['Nivel Alcanzado:', f"Nivel {nivel_final}/5"],
            ['Calificación:', calificacion]
        ]
        
        tabla_resultados = Table(datos_resultados, colWidths=[2.5*inch, 1.5*inch])
        tabla_resultados.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('BACKGROUND', (0, -1), (1, -1), color_calificacion),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (0, -1), (1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elementos.append(tabla_resultados)
        elementos.append(Spacer(1, 30))
        
        return elementos
    
    def _crear_detalle_niveles(self, evaluacion_data: Dict[str, Any], styles) -> List:
        """Crea detalle de rendimiento por nivel"""
        elementos = []
        
        elementos.append(Paragraph("RENDIMIENTO POR NIVELES", styles['Heading2']))
        elementos.append(Spacer(1, 15))
        
        respuestas = evaluacion_data.get('respuestas', [])
        
        # Agrupar respuestas por nivel
        respuestas_por_nivel = {}
        for respuesta in respuestas:
            nivel = respuesta.get('nivel_pregunta', 1)
            if nivel not in respuestas_por_nivel:
                respuestas_por_nivel[nivel] = []
            respuestas_por_nivel[nivel].append(respuesta)
        
        # Crear detalle por cada nivel
        for nivel in sorted(respuestas_por_nivel.keys()):
            respuestas_nivel = respuestas_por_nivel[nivel]
            correctas_nivel = len([r for r in respuestas_nivel if r.get('correcta', False)])
            total_nivel = len(respuestas_nivel)
            porcentaje_nivel = (correctas_nivel / max(total_nivel, 1)) * 100
            
            nivel_text = f"Nivel {nivel}: {correctas_nivel}/{total_nivel} correctas ({porcentaje_nivel:.1f}%)"
            elementos.append(Paragraph(nivel_text, styles['Heading3']))
            elementos.append(Spacer(1, 10))
        
        return elementos
    
    def _crear_estadisticas_adicionales(self, evaluacion_data: Dict[str, Any], styles) -> List:
        """Crea estadísticas adicionales"""
        elementos = []
        
        elementos.append(Paragraph("INFORMACIÓN ADICIONAL", styles['Heading2']))
        elementos.append(Spacer(1, 15))
        
        respuestas = evaluacion_data.get('respuestas', [])
        
        # Análisis por tipo de pregunta
        multiples = [r for r in respuestas if r.get('multiple', False)]
        simples = [r for r in respuestas if not r.get('multiple', False)]
        
        estadisticas = [
            ['Preguntas Simples:', f"{len(simples)} respondidas"],
            ['Preguntas Múltiples:', f"{len(multiples)} respondidas"],
            ['Inicio Evaluación:', evaluacion_data.get('fecha_inicio', 'N/A')],
            ['Estado Final:', 'COMPLETADA' if evaluacion_data.get('evaluacion_completa', False) else 'INCOMPLETA']
        ]
        
        if evaluacion_data.get('terminacion_temprana', False):
            estadisticas.append(['Terminación:', evaluacion_data.get('razon_terminacion', 'Temprana')])
        
        tabla_stats = Table(estadisticas, colWidths=[2.5*inch, 2*inch])
        tabla_stats.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elementos.append(tabla_stats)
        elementos.append(Spacer(1, 30))
        # Sección de preguntas falladas
        preguntas_falladas = [r for r in respuestas if not r.get('correcta', False)]
        if preguntas_falladas:
            elementos.append(Paragraph("PREGUNTAS FALLADAS", styles['Heading2']))
            elementos.append(Spacer(1, 10))
            for idx, r in enumerate(preguntas_falladas, 1):
                pregunta_txt = r.get('pregunta', 'Pregunta no disponible')
                respuesta_correcta = ', '.join(r.get('respuestas_correctas', []))
                respuesta_usuario = r.get('respuesta', '')
                elementos.append(Paragraph(f"<b>{idx}.</b> {pregunta_txt}", styles['Normal']))
                elementos.append(Paragraph(f"<b>Respuesta correcta:</b> {respuesta_correcta}", styles['Normal']))
                elementos.append(Paragraph(f"<b>Respuesta dada:</b> {respuesta_usuario}", styles['Normal']))
                elementos.append(Spacer(1, 8))
            elementos.append(Spacer(1, 20))
        return elementos
    
    def _crear_pie_documento(self, styles) -> List:
        """Crea pie del documento"""
        elementos = []
        
        elementos.append(Spacer(1, 50))
        elementos.append(Paragraph("Reporte generado automáticamente por el Sistema de Evaluación Técnica", styles['Normal']))
        elementos.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
        
        return elementos

# Función de interfaz para app.py
def generar_pdf_evaluacion(candidato_data: Dict[str, Any], evaluacion_data: Dict[str, Any]) -> str:
    """
    Función principal para generar PDF desde app.py
    
    Args:
        candidato_data: Datos del candidato
        evaluacion_data: Datos de la evaluación
        
    Returns:
        str: Ruta del archivo PDF generado
    """
    generator = PDFGenerator()
    return generator.generar_reporte_evaluacion(candidato_data, evaluacion_data)