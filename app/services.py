import random
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .config import Config
from .shared import PREGUNTAS, candidato_actual, candidatos_registrados
from .utils import cargar_preguntas_desde_excel, _determinar_nivel_pregunta, _buscar_pregunta_fallback
from .models import CandidatoDB
from .extensions import db

from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class EvaluadorRespuestas:
    @staticmethod
    def evaluar_respuesta(pregunta, respuesta_usuario, respuesta_letra):
        # Lógica básica: respuesta correcta por letra o texto
        correctas = pregunta.get('respuestas_correctas', [pregunta.get('respuesta_correcta')])
        multiple = pregunta.get('multiple', False)
        
        if multiple:
            return EvaluadorRespuestas._evaluar_multiple(respuesta_usuario, correctas)
        
        return EvaluadorRespuestas._evaluar_simple(respuesta_usuario, respuesta_letra, correctas)

    @staticmethod
    def _evaluar_multiple(respuesta_usuario, correctas):
        if not isinstance(respuesta_usuario, list):
            return False, 0
            
        aciertos = len([r for r in respuesta_usuario if r in correctas])
        total_correctas = len(correctas)
        puntos = aciertos / total_correctas if total_correctas > 0 else 0
        return abs(puntos - 1.0) < 1e-9, puntos

    @staticmethod
    def _evaluar_simple(respuesta_usuario, respuesta_letra, correctas):
        if (respuesta_letra and respuesta_letra in correctas) or \
           (respuesta_usuario and respuesta_usuario in correctas):
            return True, 1
        return False, 0

    @staticmethod
    def verificar_terminacion_temprana(_):
        # Implementa tu lógica de terminación temprana aquí
        return False, None

    @staticmethod
    def verificar_avance_nivel(candidato):
        # Implementa tu lógica de avance de nivel aquí
        return False, candidato.get('nivel', 1)

class EvaluacionService:
    @staticmethod
    def _get_state_path(codigo: str) -> str:
        states_dir = os.path.join(os.getcwd(), 'data', 'states')
        if not os.path.exists(states_dir):
            os.makedirs(states_dir)
        return os.path.join(states_dir, f"{codigo}.json")

    @staticmethod
    def _guardar_estado(codigo: str):
        try:
            path = EvaluacionService._get_state_path(codigo)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(candidato_actual, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando estado para {codigo}: {e}")

    @staticmethod
    def _cargar_estado(codigo: str) -> bool:
        try:
            path = EvaluacionService._get_state_path(codigo)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    estado = json.load(f)
                    candidato_actual.clear()
                    candidato_actual.update(estado)
                return True
        except Exception as e:
            logger.error(f"Error cargando estado para {codigo}: {e}")
        return False

    @staticmethod
    def limpiar_estado(codigo: str):
        try:
            path = EvaluacionService._get_state_path(codigo)
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.error(f"Error limpiando estado para {codigo}: {e}")

    @staticmethod
    def iniciar_evaluacion(documento: str, acepta_terminos: int, telefono: str = '') -> Tuple[bool, str]:
        if documento and documento in candidatos_registrados:
            # Intentar cargar estado previo
            if EvaluacionService._cargar_estado(documento):
                # Verificar si ya estaba completada
                if candidato_actual.get("evaluacion_completa", False):
                    return False, "La evaluación ya fue completada anteriormente"
                
                # Actualizar datos personales por si cambiaron (opcional, pero seguro)
                candidato_encontrado = candidatos_registrados[documento]
                candidato_actual["datos_personales"] = {
                    "codigo": documento,
                    "nombre": candidato_encontrado.get("nombre_completo", ""),
                    "email": candidato_encontrado.get("email", ""),
                    "telefono": candidato_encontrado.get("telefono", telefono)
                }
                
                # Recargar preguntas
                preguntas_cargadas = cargar_preguntas_desde_excel()
                PREGUNTAS.clear()
                PREGUNTAS.extend(preguntas_cargadas)
                
                return True, "Sesión restaurada"

            candidato_encontrado = candidatos_registrados[documento]
            
            # Actualizar candidato_actual in-place para mantener la referencia
            candidato_actual.clear()
            candidato_actual.update({
                "datos_personales": {
                    "codigo": documento,
                    "nombre": candidato_encontrado.get("nombre_completo", ""),
                    "email": candidato_encontrado.get("email", ""),
                    "telefono": candidato_encontrado.get("telefono", telefono)
                },
                "nivel": 1,
                "nivel_actual": 1,
                "puntos": 0,
                "preguntas_mostradas": [],
                "evaluacion_completa": False,
                "respuestas": [],
                # Contadores adaptativos por nivel
                "preguntas_nivel": 0,
                "correctas_nivel": 0,
                "suma_puntaje_nivel": 0.0,
                "suma_puntaje_total": 0.0,
                "racha_actual": 0,
                "flag_racha": False,
                "demoted_times": 0,
                "errores_consecutivos": 0,
                "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "acepta_terminos": acepta_terminos,
                "adaptativo": True # Asumimos adaptativo por defecto según lógica vista
            })
            
            candidatos_registrados[documento]["evaluacion_completada"] = False
            candidatos_registrados[documento]["acepta_terminos"] = acepta_terminos

            # Actualizar en la base de datos
            try:
                candidato_db = CandidatoDB.query.filter_by(codigo=documento).first()
                if candidato_db:
                    candidato_db.acepta_terminos = bool(acepta_terminos)
                    db.session.commit()
            except SQLAlchemyError as e:
                logger.error(f"Error de base de datos en inicio evaluación: {e}")
                db.session.rollback()
            except Exception as e:
                logger.error(f"Error inesperado en inicio evaluación: {e}")

            # Recargar preguntas
            preguntas_cargadas = cargar_preguntas_desde_excel()
            PREGUNTAS.clear()
            PREGUNTAS.extend(preguntas_cargadas)
            
            # Validar preguntas (lógica simplificada para brevedad, la original tenía chequeos complejos)
            if not PREGUNTAS:
                 return False, "No hay preguntas cargadas en el sistema"

            # Guardar estado inicial
            EvaluacionService._guardar_estado(documento)

            return True, ""
        return False, "Candidato no encontrado"

    @staticmethod
    def obtener_siguiente_pregunta() -> Tuple[Optional[Dict], Optional[str]]:
        # Recargar preguntas en tiempo real
        preguntas_cargadas = cargar_preguntas_desde_excel()
        PREGUNTAS.clear()
        PREGUNTAS.extend(preguntas_cargadas)

        error = EvaluacionService._validar_estado_evaluacion()
        if error:
            return None, error

        # Verificar si hay una pregunta pendiente (mostrada pero no respondida)
        preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
        respuestas = candidato_actual.get("respuestas", [])
        
        if preguntas_mostradas:
            last_id = preguntas_mostradas[-1]
            # Verificar si ya fue respondida
            answered = any(r["id"] == last_id for r in respuestas)
            if not answered:
                # Retornar la misma pregunta
                pregunta = next((p for p in PREGUNTAS if p["id"] == last_id), None)
                if pregunta:
                    candidato_actual["pregunta_actual_nivel"] = pregunta.get("nivel", 1)
                    return pregunta, None
                else:
                    # Si la pregunta ya no existe en el excel, la removemos del historial
                    candidato_actual["preguntas_mostradas"].pop()

        pregunta_seleccionada = EvaluacionService._seleccionar_pregunta()
        if not pregunta_seleccionada:
            candidato_actual["evaluacion_completa"] = True
            return None, "No hay más preguntas disponibles"
        
        candidato_actual["preguntas_mostradas"].append(pregunta_seleccionada["id"])
        candidato_actual["pregunta_actual_nivel"] = pregunta_seleccionada.get("nivel", 1)
        
        # Guardar estado tras seleccionar pregunta
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        if codigo:
            EvaluacionService._guardar_estado(codigo)

        return pregunta_seleccionada, None

    @staticmethod
    def _validar_estado_evaluacion() -> Optional[str]:
        if not candidato_actual or len(PREGUNTAS) == 0:
            return "Evaluación no iniciada"
        
        if candidato_actual.get("evaluacion_completa", False):
            return "Evaluación completada"
        
        nivel_actual = candidato_actual.get("nivel_actual", 1)
        if nivel_actual > 5:
            candidato_actual["evaluacion_completa"] = True
            return "Evaluación completada - Nivel máximo alcanzado"
        
        limite_total = Config.EVALUACION_CONFIG.get("limite_preguntas_total", 40)
        if len(candidato_actual.get("preguntas_mostradas", [])) >= limite_total:
            candidato_actual["evaluacion_completa"] = True
            return f"Evaluación completada - Máximo de {limite_total} preguntas alcanzado"
            
        return None

    @staticmethod
    def _seleccionar_pregunta() -> Optional[Dict]:
        adaptativo = candidato_actual.get("adaptativo", False)
        preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
        nivel_actual = candidato_actual.get("nivel_actual", 1)

        if adaptativo:
            return EvaluacionService._seleccionar_pregunta_adaptativa(preguntas_mostradas, nivel_actual)
        else:
            return EvaluacionService._seleccionar_pregunta_secuencial(preguntas_mostradas)

    @staticmethod
    def _seleccionar_pregunta_adaptativa(preguntas_mostradas, nivel_actual):
        preguntas_disponibles = [
            p for p in PREGUNTAS 
            if p["id"] not in preguntas_mostradas 
            and p.get("nivel", 1) == nivel_actual
        ]
        
        if not preguntas_disponibles:
            candidatos = _buscar_pregunta_fallback(preguntas_mostradas, nivel_actual)
            if not candidatos:
                return None
            return random.choice(candidatos)
        
        return random.choice(preguntas_disponibles)

    @staticmethod
    def _seleccionar_pregunta_secuencial(preguntas_mostradas):
        orden_preguntas = candidato_actual.get("orden_preguntas", [])
        pregunta_numero = len(preguntas_mostradas)
        if pregunta_numero >= len(orden_preguntas):
            return None
        pregunta_id = orden_preguntas[pregunta_numero]
        return next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)

    @staticmethod
    def procesar_respuesta(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        if not candidato_actual:
            return {"error": "No hay evaluación activa"}, 400
        
        preguntas_mostradas = candidato_actual.get("preguntas_mostradas", [])
        if not preguntas_mostradas:
            return {"error": "No hay pregunta activa"}, 400
        
        pregunta_id = preguntas_mostradas[-1]
        pregunta = next((p for p in PREGUNTAS if p["id"] == pregunta_id), None)
        
        if not pregunta:
            return {"error": "Pregunta no encontrada"}, 400
        
        respuestas_usuario = data.get("respuestas_seleccionadas", [])
        if not respuestas_usuario:
            respuesta_letra = data.get("respuesta_letra", "")
            if respuesta_letra:
                respuestas_usuario = [r.strip() for r in respuesta_letra.split(",") if r.strip()]
            else:
                respuestas_usuario = data.get("respuestas", [])
        
        if isinstance(respuestas_usuario, str):
            respuestas_usuario = [respuestas_usuario]
        
        _, puntaje = EvaluadorRespuestas.evaluar_respuesta(pregunta, respuestas_usuario, None)
        
        candidato_actual["puntos"] = candidato_actual.get("puntos", 0) + puntaje
        
        candidato_actual.setdefault("respuestas", []).append({
            "id": pregunta_id,
            "pregunta": pregunta.get("pregunta", ""),
            "respuestas": respuestas_usuario,
            "correctas": pregunta.get("respuestas_correctas", []),
            "puntaje": puntaje,
            "correcta": puntaje >= 1.0,
            "nivel": pregunta.get("nivel", 1)
        })
        
        # Lógica de avance (simplificada/extraída de app.py)
        EvaluacionService._actualizar_progreso(pregunta, puntaje)
        
        # Guardar estado tras responder
        codigo = candidato_actual.get("datos_personales", {}).get("codigo")
        if codigo:
            EvaluacionService._guardar_estado(codigo)

        hay_mas = (not candidato_actual.get("evaluacion_completa", False)) and (len(preguntas_mostradas) < Config.TOTAL_PREGUNTAS)
        
        info_nivel = {}
        if candidato_actual.get("adaptativo", False):
            info_nivel = {
                "nivel_actual": candidato_actual.get("nivel_actual", 1),
                "preguntas_respondidas_nivel": candidato_actual.get("preguntas_nivel", 0),
                "correctas_nivel": candidato_actual.get("correctas_nivel", 0),
                "evaluacion_completa": candidato_actual.get("evaluacion_completa", False)
            }

        return {
            "success": True, 
            "hay_mas": hay_mas,
            "info_nivel": info_nivel,
            "puntaje": puntaje,
            "es_correcta": puntaje > 0
        }, 200

    @staticmethod
    def _actualizar_progreso(pregunta, puntaje):
        adaptativo = candidato_actual.get("adaptativo", False)
        nivel_actual = candidato_actual.get("nivel_actual", 1)
        
        if adaptativo and pregunta.get("nivel", 1) == nivel_actual:
            candidato_actual["preguntas_nivel"] = candidato_actual.get("preguntas_nivel", 0) + 1
            
            EvaluacionService._actualizar_racha(pregunta, puntaje)
            EvaluacionService._actualizar_puntajes(puntaje)
            EvaluacionService._verificar_terminacion_errores()
            EvaluacionService._verificar_avance_nivel()

        limite_total = Config.EVALUACION_CONFIG.get("limite_preguntas_total", 40)
        if len(candidato_actual.get("preguntas_mostradas", [])) >= limite_total:
            candidato_actual["evaluacion_completa"] = True
            candidato_actual["razon_finalizacion"] = f"Límite de {limite_total} preguntas alcanzado"

    @staticmethod
    def _actualizar_racha(pregunta, puntaje):
        racha_cfg = int(Config.EVALUACION_CONFIG.get("racha_para_flag", 3))
        
        # Usar >= para comparación segura de floats
        if puntaje >= 1.0:
            candidato_actual["correctas_nivel"] = candidato_actual.get("correctas_nivel", 0) + 1
            candidato_actual["racha_actual"] = candidato_actual.get("racha_actual", 0) + 1
            if candidato_actual["racha_actual"] >= racha_cfg:
                candidato_actual["flag_racha"] = True
        else:
            # Lógica de racha parcial
            es_multiple = pregunta.get("multiple", False)
            if es_multiple and puntaje > 0 and candidato_actual.get("racha_actual", 0) >= max(0, racha_cfg - 1):
                candidato_actual["racha_actual"] = candidato_actual.get("racha_actual", 0) + 1
                candidato_actual["flag_racha"] = True
            else:
                candidato_actual["racha_actual"] = 0

    @staticmethod
    def _actualizar_puntajes(puntaje):
        candidato_actual["suma_puntaje_nivel"] = candidato_actual.get("suma_puntaje_nivel", 0.0) + float(puntaje)
        candidato_actual["suma_puntaje_total"] = candidato_actual.get("suma_puntaje_total", 0.0) + float(puntaje)
        
        if puntaje >= 1:
            candidato_actual["errores_consecutivos"] = 0
        else:
            candidato_actual["errores_consecutivos"] = candidato_actual.get("errores_consecutivos", 0) + 1

    @staticmethod
    def _verificar_terminacion_errores():
        errores_limite = Config.EVALUACION_CONFIG.get("terminacion_temprana", {}).get("errores_consecutivos")
        if errores_limite and candidato_actual.get("errores_consecutivos", 0) >= errores_limite:
            candidato_actual["evaluacion_completa"] = True
            candidato_actual["razon_finalizacion"] = "Terminación temprana por errores consecutivos"

    @staticmethod
    def _verificar_avance_nivel():
        nivel_actual = candidato_actual.get("nivel_actual", 1)
        preguntas_nivel = candidato_actual.get("preguntas_nivel", 0)
        preguntas_por_nivel = Config.EVALUACION_CONFIG.get("preguntas_por_nivel", 8)
        
        if preguntas_nivel >= preguntas_por_nivel:
            min_req_avance = Config.EVALUACION_CONFIG.get("min_correctas_para_avanzar", 4)
            suma_puntaje = candidato_actual.get("suma_puntaje_nivel", 0.0)
            flag_racha = candidato_actual.get("flag_racha", False)
            
            correctas_nivel = candidato_actual.get("correctas_nivel", 0)
            regla_correctas_mas_parcial = (correctas_nivel >= 3 and suma_puntaje >= 3.5)

            if suma_puntaje >= float(min_req_avance) or flag_racha or regla_correctas_mas_parcial:
                candidato_actual["nivel_actual"] += 1
                candidato_actual["preguntas_nivel"] = 0
                candidato_actual["correctas_nivel"] = 0
                candidato_actual["suma_puntaje_nivel"] = 0.0
                candidato_actual["racha_actual"] = 0
                candidato_actual["flag_racha"] = False
                candidato_actual["errores_consecutivos"] = 0
                
                if candidato_actual["nivel_actual"] > Config.EVALUACION_CONFIG.get("niveles_maximos", 5):
                    candidato_actual["nivel_actual"] = Config.EVALUACION_CONFIG.get("niveles_maximos", 5)
            else:
                if nivel_actual > 1:
                    candidato_actual["nivel_actual"] = max(1, nivel_actual - 1)
                    candidato_actual["preguntas_nivel"] = 0
                    candidato_actual["correctas_nivel"] = 0
                    candidato_actual["suma_puntaje_nivel"] = 0.0
                    candidato_actual["errores_consecutivos"] = 0
                    candidato_actual["demoted_times"] = candidato_actual.get("demoted_times", 0) + 1
                else:
                    candidato_actual["preguntas_nivel"] = 0
                    candidato_actual["correctas_nivel"] = 0
                    candidato_actual["suma_puntaje_nivel"] = 0.0
                    candidato_actual["errores_consecutivos"] = 0

    @staticmethod
    def obtener_estado() -> Tuple[Dict[str, Any], int]:
        if not candidato_actual:
            return {"error": "No hay evaluación activa"}, 400
        
        adaptativo = candidato_actual.get("adaptativo", False)
        
        estado = {
            "candidato": candidato_actual.get("datos_personales", {}),
            "preguntas_respondidas": len(candidato_actual.get("preguntas_mostradas", [])),
            "total_preguntas": Config.TOTAL_PREGUNTAS,
            "puntos_totales": candidato_actual.get("puntos", 0),
            "evaluacion_completa": candidato_actual.get("evaluacion_completa", False),
            "adaptativo": adaptativo
        }
        
        if adaptativo:
            estado.update({
                "nivel_actual": candidato_actual.get("nivel_actual", 1),
                "preguntas_nivel_actual": candidato_actual.get("preguntas_nivel", 0),
                "correctas_nivel_actual": candidato_actual.get("correctas_nivel", 0),
                "necesitas_para_avanzar": max(0, 5 - candidato_actual.get("correctas_nivel", 0)),
                "preguntas_restantes_nivel": max(0, 8 - candidato_actual.get("preguntas_nivel", 0))
            })
        
        return estado, 200
