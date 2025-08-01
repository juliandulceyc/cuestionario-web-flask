from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
import os
from datetime import datetime

class CandidateReportGenerator:
    def generate_candidate_report(self, candidato_actual):
        nombre = candidato_actual.get('datos_personales', {}).get('nombre', 'Candidato')
        email = candidato_actual.get('datos_personales', {}).get('email', '')
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"reporte_{nombre.replace(' ', '_')}_{fecha}.pdf"
        filepath = os.path.join(os.getcwd(), filename)

        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter

        # TÍTULO PRINCIPAL
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(HexColor('#2E86C1'))
        title = "REPORTE DE EVALUACIÓN DE CANDIDATO"
        title_width = c.stringWidth(title, "Helvetica-Bold", 16)
        c.drawString((width - title_width) / 2, height - 50, title)

        # SUBTÍTULO
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor('#000000'))
        y_pos = height - 75
        c.drawString(50, y_pos, "Sistema de Evaluación de Candidatos")
        y_pos -= 12
        c.drawString(50, y_pos, "Desarrollado para Procesos de Selección de Personal")
        y_pos -= 12
        c.drawString(50, y_pos, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # INFORMACIÓN DEL CANDIDATO (TÍTULO)
        y_pos -= 30
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor('#2E86C1'))
        c.drawString(50, y_pos, "INFORMACIÓN DEL CANDIDATO")

        # TABLA DE INFORMACIÓN DEL CANDIDATO
        y_pos -= 25
        c.setFillColor(HexColor('#000000'))
        c.setFont("Helvetica", 10)

        # Líneas de la tabla
        table_y = y_pos
        row_height = 15
        col1_x = 50
        col2_x = 200
        table_width = 450

        # Encabezados y datos
        info_data = [
            ("Nombre Completo:", nombre),
            ("Documento de Identidad:", candidato_actual.get('datos_personales', {}).get('codigo', 'N/A')),
            ("Email:", email),
            ("Teléfono:", candidato_actual.get('datos_personales', {}).get('telefono', 'N/A')),
            ("Fecha de Evaluación:", datetime.now().strftime("%Y-%m-%d"))
        ]

        # Dibujar tabla con bordes
        for i, (label, value) in enumerate(info_data):
            y = table_y - (i * row_height)
            # Bordes de la tabla
            c.rect(col1_x, y - 12, 150, row_height, stroke=1, fill=0)
            c.rect(col2_x, y - 12, 250, row_height, stroke=1, fill=0)
            # Texto
            c.drawString(col1_x + 5, y - 5, label)
            c.drawString(col2_x + 5, y - 5, str(value))

        # RESUMEN DE RESULTADOS (TÍTULO)
        y_pos -= 120
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor('#2E86C1'))
        c.drawString(50, y_pos, "RESUMEN DE RESULTADOS")

        # TABLA DE RESULTADOS
        y_pos -= 25
        c.setFillColor(HexColor('#000000'))
        c.setFont("Helvetica", 10)

        nivel_actual = candidato_actual.get('nivel', 1)
        puntos_totales = candidato_actual.get('puntos', 0)
        preguntas_respondidas = len(candidato_actual.get('preguntas_mostradas', []))
        respuestas_correctas = candidato_actual.get('respuestas_correctas_nivel', 0)
        porcentaje_acierto = (respuestas_correctas / max(preguntas_respondidas, 1)) * 100 if preguntas_respondidas > 0 else 0

        # Determinar estado
        if nivel_actual >= 5:
            estado = "✓ APROBADO"
            color_estado = HexColor('#27ae60')
        else:
            estado = "✗ NO APROBADO"
            color_estado = HexColor('#e74c3c')

        resultados_data = [
            ("Nivel Máximo Alcanzado:", f"{nivel_actual} de 5"),
            ("Puntuación Total:", f"{puntos_totales} puntos"),
            ("Preguntas Respondidas:", str(preguntas_respondidas)),
            ("Porcentaje de Acierto:", f"{porcentaje_acierto:.1f}%"),
            ("ESTADO:", estado)
        ]

        table_y = y_pos
        for i, (label, value) in enumerate(resultados_data):
            y = table_y - (i * row_height)
            # Bordes
            c.rect(col1_x, y - 12, 150, row_height, stroke=1, fill=0)
            c.rect(col2_x, y - 12, 250, row_height, stroke=1, fill=0)
            
            # Texto
            c.setFillColor(HexColor('#000000'))
            c.drawString(col1_x + 5, y - 5, label)
            
            # Color especial para el estado
            if label == "ESTADO:":
                c.setFillColor(color_estado)
                c.setFont("Helvetica-Bold", 10)
            
            c.drawString(col2_x + 5, y - 5, str(value))
            c.setFillColor(HexColor('#000000'))
            c.setFont("Helvetica", 10)

        # ANÁLISIS DETALLADO POR NIVELES (TÍTULO)
        y_pos -= 120
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor('#2E86C1'))
        c.drawString(50, y_pos, "ANÁLISIS DETALLADO POR NIVELES")

        # LISTA DE NIVELES
        y_pos -= 20
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor('#000000'))

        niveles_info = [
            ("Nivel 1: Conocimientos Básicos/Fundamentales", "✓ COMPLETADO" if nivel_actual >= 1 else "✗ NO EVALUADO"),
            ("El candidato demuestra competencia en conocimientos básicos/fundamentales", ""),
            ("Nivel 2: Conocimientos Intermedios", "✓ COMPLETADO" if nivel_actual >= 2 else "✗ NO EVALUADO"),
            ("Nivel de desarrollo durante la evaluación", ""),
            ("Nivel 3: Conocimientos Avanzados", "✓ COMPLETADO" if nivel_actual >= 3 else "✗ NO EVALUADO"),
            ("Nivel de desarrollo durante la evaluación", ""),
            ("Nivel 4: Conocimientos Especializados", "✓ COMPLETADO" if nivel_actual >= 4 else "✗ NO EVALUADO"),
            ("Nivel de desarrollo durante la evaluación", ""),
            ("Nivel 5: Conocimientos de Máximo Nivel/Experto", "✓ COMPLETADO" if nivel_actual >= 5 else "✗ NO EVALUADO"),
            ("Nivel de desarrollo durante la evaluación", "")
        ]

        for desc, status in niveles_info:
            if status:  # Solo mostrar líneas con estado
                c.setFillColor(HexColor('#000000'))
                c.drawString(50, y_pos, desc)
                
                if "COMPLETADO" in status:
                    c.setFillColor(HexColor('#27ae60'))
                elif "NO EVALUADO" in status:
                    c.setFillColor(HexColor('#e74c3c'))
                
                if status:
                    c.drawString(400, y_pos, status)
                    
            y_pos -= 12

        # RECOMENDACIÓN PARA RECURSOS HUMANOS (TÍTULO)
        y_pos -= 20
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor('#2E86C1'))
        c.drawString(50, y_pos, "RECOMENDACIÓN PARA RECURSOS HUMANOS")

        # CAJA DE RECOMENDACIÓN
        y_pos -= 30
        box_height = 60
        c.setFillColor(HexColor('#E3F2FD'))
        c.rect(50, y_pos - box_height, 500, box_height, fill=1, stroke=1)

        # TEXTO DE RECOMENDACIÓN
        c.setFont("Helvetica-Bold", 10)
        if nivel_actual >= 5:
            c.setFillColor(HexColor('#27ae60'))
            recomendacion = "CANDIDATO RECOMENDADO:"
            detalle = "Alcanza el nivel mínimo requerido. Se sugiere buscar candidatos con mayor preparación técnica."
        else:
            c.setFillColor(HexColor('#e74c3c'))
            recomendacion = "CANDIDATO NO RECOMENDADO:"
            detalle = "No alcanza el nivel mínimo requerido. Se sugiere buscar candidatos con mayor preparación técnica."

        c.drawString(60, y_pos - 20, recomendacion)
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor('#000000'))
        c.drawString(60, y_pos - 35, detalle)
        c.drawString(60, y_pos - 50, "Este reporte fue generado automáticamente por el Sistema de Evaluación de Candidatos.")

        # PIE DE PÁGINA
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor('#000000'))
        c.drawString(50, 50, "Confidencial: Reporte técnico y actividades; confidencial al área de Sistemas.")

        c.save()
        return filepath