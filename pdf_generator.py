"""
Módulo para generar reportes PDF de evaluación de candidatos
Desarrollado para Sistema de Evaluación SENA
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

class CandidateReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configurar estilos personalizados para el PDF"""
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86C1')
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2E86C1')
        ))
        
        # Estilo para información destacada
        self.styles.add(ParagraphStyle(
            name='HighlightText',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=10,
            backColor=colors.HexColor('#EBF5FF'),
            borderColor=colors.HexColor('#2E86C1'),
            borderWidth=1,
            borderPadding=10
        ))

    def generate_candidate_report(self, candidate_data, filename=None):
        """
        Generar reporte PDF para un candidato
        
        Args:
            candidate_data (dict): Datos del candidato y su evaluación
            filename (str): Nombre del archivo (opcional)
        
        Returns:
            str: Ruta del archivo generado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            doc_number = candidate_data.get('datos_personales', {}).get('documento', 'SIN_DOC')
            filename = f"reporte_evaluacion_{doc_number}_{timestamp}.pdf"
        
        # Crear directorio para reportes si no existe
        reports_dir = "reportes_pdf"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        filepath = os.path.join(reports_dir, filename)
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Construir contenido del PDF
        story = []
        story.extend(self._build_header(candidate_data))
        story.extend(self._build_candidate_info(candidate_data))
        story.extend(self._build_results_summary(candidate_data))
        story.extend(self._build_detailed_analysis(candidate_data))
        story.extend(self._build_recommendation(candidate_data))
        story.extend(self._build_footer())
        
        # Generar PDF
        doc.build(story)
        return filepath

    def _build_header(self, candidate_data):
        """Construir encabezado del reporte"""
        elements = []
        
        # Título principal
        title = Paragraph("REPORTE DE EVALUACIÓN DE CANDIDATO", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información de la empresa/sistema
        empresa_info = Paragraph(
            "<b>Sistema de Evaluación de Candidatos</b><br/>"
            "Desarrollado para Procesos de Selección de Personal<br/>"
            f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Normal']
        )
        elements.append(empresa_info)
        elements.append(Spacer(1, 20))
        
        return elements

    def _build_candidate_info(self, candidate_data):
        """Construir sección de información del candidato"""
        elements = []
        
        # Título de sección
        section_title = Paragraph("INFORMACIÓN DEL CANDIDATO", self.styles['CustomHeading'])
        elements.append(section_title)
        
        # Obtener datos personales
        datos = candidate_data.get('datos_personales', {})
        
        # Crear tabla con información del candidato
        candidate_info_data = [
            ['Nombre Completo:', datos.get('nombre_completo', 'N/A')],
            ['Documento de Identidad:', datos.get('documento', 'N/A')],
            ['Email:', datos.get('email', 'N/A')],
            ['Teléfono:', datos.get('telefono', 'N/A')],
            ['Fecha de Evaluación:', datos.get('fecha_evaluacion', 'N/A')[:10] if datos.get('fecha_evaluacion') else 'N/A']
        ]
        
        candidate_table = Table(candidate_info_data, colWidths=[2*inch, 4*inch])
        candidate_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        
        elements.append(candidate_table)
        elements.append(Spacer(1, 20))
        
        return elements

    def _build_results_summary(self, candidate_data):
        """Construir resumen de resultados"""
        elements = []
        
        # Título de sección
        section_title = Paragraph("RESUMEN DE RESULTADOS", self.styles['CustomHeading'])
        elements.append(section_title)
        
        # Calcular estadísticas
        nivel_actual = candidate_data.get('nivel', 1)
        puntos_totales = candidate_data.get('puntos', 0)
        total_preguntas = candidate_data.get('total_preguntas_respondidas', 0)
        porcentaje_acierto = (puntos_totales / (total_preguntas * 10)) * 100 if total_preguntas > 0 else 0
        
        # Determinar estado de aprobación
        estado = "✅ APROBADO" if porcentaje_acierto >= 70 else "❌ NO APROBADO"
        color_estado = colors.green if porcentaje_acierto >= 70 else colors.red
        
        # Crear tabla de resultados
        results_data = [
            ['Nivel Máximo Alcanzado:', f"{nivel_actual} de 5"],
            ['Puntuación Total:', f"{puntos_totales} puntos"],
            ['Preguntas Respondidas:', f"{total_preguntas}"],
            ['Porcentaje de Acierto:', f"{porcentaje_acierto:.1f}%"],
            ['ESTADO:', estado]
        ]
        
        results_table = Table(results_data, colWidths=[2.5*inch, 3.5*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -2), colors.HexColor('#F8F9FA')),
            ('BACKGROUND', (0, -1), (0, -1), colors.HexColor('#FFF3CD')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('TEXTCOLOR', (1, -1), (1, -1), color_estado),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
            ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        
        elements.append(results_table)
        elements.append(Spacer(1, 20))
        
        return elements

    def _build_detailed_analysis(self, candidate_data):
        """Construir análisis detallado por niveles"""
        elements = []
        
        # Título de sección
        section_title = Paragraph("ANÁLISIS DETALLADO POR NIVELES", self.styles['CustomHeading'])
        elements.append(section_title)
        
        # Análisis por nivel
        nivel_actual = candidate_data.get('nivel', 1)
        
        level_descriptions = {
            1: "Conocimientos Básicos/Fundamentales",
            2: "Conocimientos Intermedios",
            3: "Conocimientos Avanzados",
            4: "Conocimientos de Experto",
            5: "Conocimientos de Máxima Dificultad"
        }
        
        analysis_text = []
        for i in range(1, 6):
            if i <= nivel_actual:
                status = "✅ COMPLETADO"
                description = f"El candidato demostró competencia en {level_descriptions[i].lower()}"
            else:
                status = "⏸️ NO EVALUADO"
                description = f"Nivel no alcanzado durante la evaluación"
            
            analysis_text.append(f"<b>Nivel {i}:</b> {level_descriptions[i]} - {status}<br/>{description}<br/><br/>")
        
        analysis_paragraph = Paragraph("".join(analysis_text), self.styles['Normal'])
        elements.append(analysis_paragraph)
        elements.append(Spacer(1, 20))
        
        return elements

    def _build_recommendation(self, candidate_data):
        """Construir recomendación para RRHH"""
        elements = []
        
        # Título de sección
        section_title = Paragraph("RECOMENDACIÓN PARA RECURSOS HUMANOS", self.styles['CustomHeading'])
        elements.append(section_title)
        
        # Calcular recomendación basada en resultados
        nivel_actual = candidate_data.get('nivel', 1)
        puntos_totales = candidate_data.get('puntos', 0)
        total_preguntas = candidate_data.get('total_preguntas_respondidas', 0)
        porcentaje_acierto = (puntos_totales / (total_preguntas * 10)) * 100 if total_preguntas > 0 else 0
        
        if porcentaje_acierto >= 85:
            recommendation = "CANDIDATO ALTAMENTE RECOMENDADO: Demuestra excelente competencia técnica y alta capacidad de aprendizaje. Ideal para posiciones de responsabilidad."
        elif porcentaje_acierto >= 70:
            recommendation = "CANDIDATO RECOMENDADO: Cumple con los requisitos técnicos mínimos. Apto para el cargo con posibilidad de capacitación complementaria."
        else:
            recommendation = "CANDIDATO NO RECOMENDADO: No alcanza el nivel mínimo requerido. Se sugiere buscar candidatos con mayor preparación técnica."
        
        recommendation_paragraph = Paragraph(recommendation, self.styles['HighlightText'])
        elements.append(recommendation_paragraph)
        elements.append(Spacer(1, 20))
        
        return elements

    def _build_footer(self):
        """Construir pie de página"""
        elements = []
        
        # Información del sistema
        footer_info = Paragraph(
            "<i>Este reporte fue generado automáticamente por el Sistema de Evaluación de Candidatos.<br/>"
            "Para consultas técnicas o aclaraciones, contacte al área de Sistemas.</i>",
            self.styles['Normal']
        )
        elements.append(footer_info)
        
        return elements

def test_pdf_generation():
    """Función de prueba para generar un PDF de ejemplo"""
    sample_data = {
        'datos_personales': {
            'nombre_completo': 'Juan Pérez García',
            'documento': '12345678',
            'email': 'juan.perez@email.com',
            'telefono': '3001234567',
            'fecha_evaluacion': '2025-07-17T14:30:00'
        },
        'nivel': 4,
        'puntos': 180,
        'total_preguntas_respondidas': 20
    }
    
    generator = CandidateReportGenerator()
    filepath = generator.generate_candidate_report(sample_data, "reporte_ejemplo.pdf")
    print(f"Reporte de ejemplo generado: {filepath}")

if __name__ == "__main__":
    test_pdf_generation()
