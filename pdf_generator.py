from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from datetime import datetime
import os

# OBTENER TOTAL DE PREGUNTAS
def get_total_preguntas():
    """Función local para obtener total de preguntas"""
    return 2 #Ajuste de numero de preguntas

class CandidateReportGenerator:
    def generate_candidate_report(self, candidato_actual):
        try:
            # Datos del candidato
            datos_personales = candidato_actual.get('datos_personales', {})
            nombre = datos_personales.get('nombre', 'Candidato')
            codigo = datos_personales.get('codigo', 'N/A')
            email = datos_personales.get('email', '')
            telefono = datos_personales.get('telefono', 'N/A')
            
            # Generar nombre del archivo
            fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"reporte_{nombre.replace(' ', '_')}_{codigo}_{fecha}.pdf"
            filepath = os.path.join(os.getcwd(), "reportes")
            
            # Crear directorio si no existe
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            
            full_path = os.path.join(filepath, filename)
            
            # Crear el PDF
            c = canvas.Canvas(full_path, pagesize=letter)
            width, height = letter

            # ✅ EXTRAER ESTADÍSTICAS REALES DEL CANDIDATO
            respuestas = candidato_actual.get('respuestas', [])
            total_respondidas = len(respuestas)
            correctas_totales = len([r for r in respuestas if r.get('correcta', False)])
            incorrectas_totales = total_respondidas - correctas_totales
            
            # Porcentaje de acierto real
            porcentaje_acierto = (correctas_totales / max(total_respondidas, 1)) * 100 if total_respondidas > 0 else 0
            
            # Estadísticas por nivel
            stats_por_nivel = {}
            for i in range(1, 6):  # Niveles 1-5
                respuestas_nivel = [r for r in respuestas if r.get('nivel_candidato') == i]
                correctas_nivel = len([r for r in respuestas_nivel if r.get('correcta', False)])
                stats_por_nivel[i] = {
                    'total': len(respuestas_nivel),
                    'correctas': correctas_nivel,
                    'porcentaje': (correctas_nivel / max(len(respuestas_nivel), 1)) * 100 if respuestas_nivel else 0
                }
            
            nivel_maximo = candidato_actual.get('nivel', 1)
            puntos_totales = candidato_actual.get('puntos', 0)
            evaluacion_completa = candidato_actual.get('evaluacion_completa', False)

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
            c.drawString(50, y_pos, "Sistema de Evaluación de Candidatos - Evaluación Técnica de Firewall PAN")
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
                ("Código de Candidato:", codigo),
                ("Email:", email),
                ("Teléfono:", telefono),
                ("Fecha de Evaluación:", datetime.now().strftime("%d/%m/%Y")),
                ("Estado de Evaluación:", "COMPLETADA" if evaluacion_completa else "PARCIAL")
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

            # ✅ ESTADÍSTICAS GENERALES (TÍTULO)
            y_pos -= 140
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(HexColor('#2E86C1'))
            c.drawString(50, y_pos, "ESTADÍSTICAS GENERALES")

            # TABLA DE ESTADÍSTICAS GENERALES
            y_pos -= 25
            c.setFillColor(HexColor('#000000'))
            c.setFont("Helvetica", 10)

            # ✅ USAR CONFIGURACIÓN AUTOMÁTICA
            total_maximo = get_total_preguntas()  # ← USAR FUNCIÓN AUTOMÁTICA

            # Determinar estado de aprobación
            if nivel_maximo >= 5:
                estado = "✓ APROBADO"
                color_estado = HexColor('#27ae60')
            elif nivel_maximo >= 3:
                estado = "⚠ PARCIAL"
                color_estado = HexColor('#f39c12')
            else:
                estado = "✗ NO APROBADO"
                color_estado = HexColor('#e74c3c')

            estadisticas_data = [
                ("Preguntas Respondidas:", f"{total_respondidas} de {total_maximo}"),  # ← AUTOMÁTICO
                ("Respuestas Correctas:", f"{correctas_totales}/{total_respondidas}"),
                ("Respuestas Incorrectas:", f"{incorrectas_totales}/{total_respondidas}"),
                ("Porcentaje de Aciertos:", f"{porcentaje_acierto:.1f}%"),
                ("Puntuación Total:", f"{puntos_totales} puntos"),
                ("Nivel Final Alcanzado:", f"Nivel {nivel_maximo}"),
                ("RESULTADO FINAL:", estado)
            ]

            table_y = y_pos
            for i, (label, value) in enumerate(estadisticas_data):
                y = table_y - (i * row_height)
                # Bordes
                c.rect(col1_x, y - 12, 150, row_height, stroke=1, fill=0)
                c.rect(col2_x, y - 12, 250, row_height, stroke=1, fill=0)
                
                # Texto
                c.setFillColor(HexColor('#000000'))
                c.drawString(col1_x + 5, y - 5, label)
                
                # Color especial para el resultado final
                if label == "RESULTADO FINAL:":
                    c.setFillColor(color_estado)
                    c.setFont("Helvetica-Bold", 10)
                elif "Correctas" in label:
                    c.setFillColor(HexColor('#27ae60'))
                elif "Incorrectas" in label:
                    c.setFillColor(HexColor('#e74c3c'))
                
                c.drawString(col2_x + 5, y - 5, str(value))
                c.setFillColor(HexColor('#000000'))
                c.setFont("Helvetica", 10)

            # ✅ ANÁLISIS DETALLADO POR NIVELES (TÍTULO)
            y_pos -= 140
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(HexColor('#2E86C1'))
            c.drawString(50, y_pos, "DESEMPEÑO POR NIVELES DE DIFICULTAD")

            # ENCABEZADOS DE TABLA
            y_pos -= 25
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(HexColor('#34495e'))
            
            # Encabezados
            headers = ["NIVEL", "DESCRIPCIÓN", "PREGUNTAS", "CORRECTAS", "% ACIERTO", "ESTADO"]
            col_widths = [40, 200, 80, 70, 70, 80]
            col_positions = [50, 90, 290, 370, 440, 510]
            
            # Dibujar encabezados
            for i, (header, pos) in enumerate(zip(headers, col_positions)):
                c.drawString(pos, y_pos, header)
            
            # Línea separadora
            y_pos -= 5
            c.line(50, y_pos, 590, y_pos)
            y_pos -= 10

            # DATOS POR NIVEL
            c.setFont("Helvetica", 9)
            
            niveles_descripciones = {
                1: "Conocimientos Básicos",
                2: "Conocimientos Intermedios", 
                3: "Conocimientos Avanzados",
                4: "Conocimientos Especializados",
                5: "Conocimientos de Experto"
            }
            
            for nivel in range(1, 6):
                stats = stats_por_nivel[nivel]
                
                # Determinar estado del nivel
                if stats['total'] == 0:
                    estado_nivel = "NO EVALUADO"
                    color_nivel = HexColor('#95a5a6')
                elif nivel <= nivel_maximo:
                    if stats['correctas'] >= 2:  # Requisito de 2 correctas
                        estado_nivel = "✓ APROBADO"
                        color_nivel = HexColor('#27ae60')
                    else:
                        estado_nivel = "✗ NO APROBADO"
                        color_nivel = HexColor('#e74c3c')
                else:
                    estado_nivel = "NO ALCANZADO"
                    color_nivel = HexColor('#f39c12')
                
                # Datos del nivel
                nivel_data = [
                    str(nivel),
                    niveles_descripciones[nivel],
                    f"{stats['total']}" if stats['total'] > 0 else "0",
                    f"{stats['correctas']}/{stats['total']}" if stats['total'] > 0 else "0/0",
                    f"{stats['porcentaje']:.1f}%" if stats['total'] > 0 else "0%",
                    estado_nivel
                ]
                
                # Dibujar fila
                for i, (data, pos) in enumerate(zip(nivel_data, col_positions)):
                    if i == 5:  # Columna de estado
                        c.setFillColor(color_nivel)
                        if "APROBADO" in estado_nivel:
                            c.setFont("Helvetica-Bold", 8)
                    else:
                        c.setFillColor(HexColor('#000000'))
                        c.setFont("Helvetica", 9)
                    
                    c.drawString(pos, y_pos, data)
                
                y_pos -= 15

            # ✅ DETALLE DE TODAS LAS RESPUESTAS
            y_pos -= 30
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(HexColor('#2E86C1'))
            c.drawString(50, y_pos, "DETALLE DE RESPUESTAS")

            # ENCABEZADOS DE TABLA DE RESPUESTAS
            y_pos -= 25
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(HexColor('#34495e'))
            
            resp_headers = ["#", "PREGUNTA", "RESPUESTA DADA", "CORRECTA", "NIVEL", "PUNTOS"]
            resp_positions = [50, 80, 300, 420, 480, 520]
            
            for header, pos in zip(resp_headers, resp_positions):
                c.drawString(pos, y_pos, header)
            
            # Línea separadora
            y_pos -= 5
            c.line(50, y_pos, 550, y_pos)
            y_pos -= 10

            # DATOS DE RESPUESTAS
            c.setFont("Helvetica", 7)
            
            for i, resp in enumerate(respuestas, 1):
                if y_pos < 100:  # Nueva página si no hay espacio
                    c.showPage()
                    y_pos = height - 50
                    c.setFont("Helvetica", 7)
                
                # Preparar datos
                pregunta_corta = resp.get('pregunta', '')[:35] + '...' if len(resp.get('pregunta', '')) > 35 else resp.get('pregunta', '')
                respuesta_corta = resp.get('respuesta', '')[:20] + '...' if len(resp.get('respuesta', '')) > 20 else resp.get('respuesta', '')
                es_correcta = resp.get('correcta', False)
                nivel_candidato = resp.get('nivel_candidato', 1)
                puntos = resp.get('puntos', 0)
                
                # Datos de la fila
                resp_data = [
                    str(i),
                    pregunta_corta,
                    respuesta_corta,
                    "✓" if es_correcta else "✗",
                    f"N{nivel_candidato}",
                    f"{puntos:.1f}"
                ]
                
                # Dibujar fila
                for j, (data, pos) in enumerate(zip(resp_data, resp_positions)):
                    if j == 3:  # Columna correcta
                        c.setFillColor(HexColor('#27ae60') if es_correcta else HexColor('#e74c3c'))
                    else:
                        c.setFillColor(HexColor('#000000'))
                    
                    c.drawString(pos, y_pos, data)
                
                y_pos -= 12
            
            # RECOMENDACIÓN PARA RECURSOS HUMANOS (nueva página si es necesario)
            if y_pos < 200:
                c.showPage()
                y_pos = height - 50

            y_pos -= 30
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(HexColor('#2E86C1'))
            c.drawString(50, y_pos, "RECOMENDACIÓN PARA RECURSOS HUMANOS")

            # CAJA DE RECOMENDACIÓN
            y_pos -= 30
            box_height = 100
            c.setFillColor(HexColor('#E3F2FD'))
            c.rect(50, y_pos - box_height, 500, box_height, fill=1, stroke=1)

            # ✅ RECOMENDACIÓN BASADA EN ESTADÍSTICAS REALES
            c.setFont("Helvetica-Bold", 11)
            
            if nivel_maximo >= 5 and porcentaje_acierto >= 80:
                c.setFillColor(HexColor('#27ae60'))
                recomendacion = "CANDIDATO ALTAMENTE RECOMENDADO"
                detalle1 = f"Excelente desempeño: {correctas_totales}/{total_respondidas} correctas ({porcentaje_acierto:.1f}%)"
                detalle2 = f"Alcanzó el nivel máximo ({nivel_maximo}/5) con sólidos conocimientos técnicos."
                detalle3 = "Se recomienda su contratación inmediata para posiciones técnicas especializadas."
                detalle4 = f"Puntuación total: {puntos_totales} puntos - Candidato excepcional."
            elif nivel_maximo >= 4 and porcentaje_acierto >= 60:
                c.setFillColor(HexColor('#f39c12'))
                recomendacion = "CANDIDATO RECOMENDADO CON RESERVAS"
                detalle1 = f"Buen desempeño: {correctas_totales}/{total_respondidas} correctas ({porcentaje_acierto:.1f}%)"
                detalle2 = f"Alcanzó nivel {nivel_maximo}/5, requiere capacitación adicional en temas avanzados."
                detalle3 = "Apto para posiciones junior con mentoría técnica."
                detalle4 = f"Puntuación total: {puntos_totales} puntos - Potencial de crecimiento."
            elif nivel_maximo >= 3 and porcentaje_acierto >= 40:
                c.setFillColor(HexColor('#e67e22'))
                recomendacion = "CANDIDATO ACEPTABLE"
                detalle1 = f"Desempeño regular: {correctas_totales}/{total_respondidas} correctas ({porcentaje_acierto:.1f}%)"
                detalle2 = f"Conocimientos básicos-intermedios (nivel {nivel_maximo}/5)."
                detalle3 = "Requiere capacitación extensiva antes de asignación técnica."
                detalle4 = f"Puntuación total: {puntos_totales} puntos - Considerar según necesidades."
            else:
                c.setFillColor(HexColor('#e74c3c'))
                recomendacion = "CANDIDATO NO RECOMENDADO"
                detalle1 = f"Desempeño insuficiente: {correctas_totales}/{total_respondidas} correctas ({porcentaje_acierto:.1f}%)"
                detalle2 = f"No alcanzó conocimientos mínimos requeridos (nivel {nivel_maximo}/5)."
                detalle3 = "Se sugiere buscar candidatos con mayor preparación técnica."
                detalle4 = f"Puntuación total: {puntos_totales} puntos - No cumple estándares mínimos."

            c.drawString(60, y_pos - 20, recomendacion)
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor('#000000'))
            c.drawString(60, y_pos - 35, detalle1)
            c.drawString(60, y_pos - 48, detalle2)
            c.drawString(60, y_pos - 61, detalle3)
            c.drawString(60, y_pos - 74, detalle4)
            c.drawString(60, y_pos - 87, "Este reporte fue generado automáticamente por el Sistema de Evaluación.")

            # PIE DE PÁGINA
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor('#666666'))
            c.drawString(50, 30, f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} - Confidencial")
            c.drawString(400, 30, f"Total preguntas configuradas: {total_maximo}")

            c.save()
            
            print(f"✅ PDF generado exitosamente: {full_path}")
            print(f"📊 Estadísticas incluidas: {correctas_totales}/{total_respondidas} correctas ({porcentaje_acierto:.1f}%)")
            print(f"🎯 Nivel alcanzado: {nivel_maximo}/5")
            print(f"💯 Puntuación total: {puntos_totales} puntos")
            
            return full_path
            
        except Exception as e:
            print(f"❌ Error generando PDF: {e}")
            import traceback
            traceback.print_exc()
            return None