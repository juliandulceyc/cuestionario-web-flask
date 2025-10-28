# Sistema de Evaluación con Acumulación de Respuestas Correctas

## Configuración Actual

### Parámetros Principales
- **Límite total de preguntas**: 40
- **Máximo intentos por nivel**: 2
- **Preguntas por intento**: 8
- **Respuestas correctas requeridas**: 5 (para avanzar de nivel)
- **Niveles totales**: 5

## Funcionamiento del Sistema

### Lógica de Acumulación
1. El candidato responde 8 preguntas por intento
2. Las respuestas correctas se **acumulan** entre intentos del mismo nivel
3. Cuando alcanza 5 correctas acumuladas, avanza al siguiente nivel
4. Si no alcanza 5 correctas, puede intentar de nuevo (si hay intentos disponibles)

### Sistema Inteligente de Distribución de Preguntas

El sistema calcula dinámicamente si puede dar otro intento basándose en:

```python
preguntas_usadas = len(preguntas_mostradas)
preguntas_restantes = 40 - preguntas_usadas
niveles_futuros = 5 - nivel_actual  # Niveles DESPUÉS del actual
preguntas_necesarias_para_futuros = niveles_futuros * 8
puede_dar_otro_intento = preguntas_restantes >= (8 + preguntas_necesarias_para_futuros)
```

### Criterios de Finalización

La evaluación termina cuando:

1. **Máximo de intentos alcanzado**: El candidato usó los 2 intentos permitidos sin lograr 5 correctas
2. **Preguntas insuficientes**: No hay suficientes preguntas para otro intento sin comprometer niveles futuros
3. **Límite total alcanzado**: Se respondieron las 40 preguntas
4. **Evaluación completada**: Se alcanzó el nivel 5 (máximo)

## Ejemplos de Escenarios

### Escenario 1: Candidato Exitoso
```
Nivel 1 - Intento 1: 3/8 correctas
Nivel 1 - Intento 2: 2/8 correctas → Total: 5/16 → ✅ AVANZA
Preguntas usadas: 16/40

Nivel 2 - Intento 1: 5/8 correctas → ✅ AVANZA
Preguntas usadas: 24/40

Nivel 3 - Intento 1: 5/8 correctas → ✅ AVANZA
Preguntas usadas: 32/40

Nivel 4 - Intento 1: 5/8 correctas → ✅ AVANZA
Preguntas usadas: 40/40

✅ EVALUACIÓN COMPLETADA: Nivel 4 alcanzado (40 preguntas exactas)
```

### Escenario 2: Finalización por Intentos
```
Nivel 1 - Intento 1: 3/8 correctas
Nivel 1 - Intento 2: 1/8 correctas → Total: 4/16
❌ FINALIZADA: Máximo de intentos (2) alcanzado en nivel 1
```

### Escenario 3: Finalización por Preguntas Insuficientes
```
Nivel 1 - Intento 1: 3/8 correctas
Preguntas restantes: 32
Niveles futuros: 4 (necesitan 32 preguntas)
Para otro intento necesita: 8 + 32 = 40 preguntas
❌ FINALIZADA: Preguntas insuficientes (necesita 40, tiene 32)
```

## Ventajas del Sistema

1. **Justo**: Permite múltiples intentos cuando hay recursos disponibles
2. **Eficiente**: No desperdicia preguntas cuando no hay suficientes para completar
3. **Adaptativo**: Ajusta los intentos disponibles según la progresión del candidato
4. **Predecible**: Siempre reserva suficientes preguntas para niveles futuros

## Logging y Depuración

El sistema registra en `evaluacion_system.log`:
- Intentos completados por nivel
- Correctas acumuladas
- Preguntas restantes
- Decisiones de continuación/finalización

Ejemplo de log:
```
INFO: Candidato en nivel 1: Intento 1, 3/5 correctas | Preguntas restantes: 32
```

## Archivos Modificados

- `app.py`: Lógica principal de evaluación (líneas 85-106, 410-470)
- `EVALUACION_CONFIG`: Configuración centralizada
- `obtener_pregunta()`: Gestión de límite de 40 preguntas
- `responder()`: Lógica de acumulación y decisión de continuación

## Pruebas

Para probar el sistema:
```bash
python prueba_sistema_40.py
```

Este script simula diferentes escenarios y muestra el comportamiento del sistema.
