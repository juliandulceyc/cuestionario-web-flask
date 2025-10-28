# Lógica de Evaluación - Sistema Simplificado

## 📋 Configuración Actual

```python
preguntas_por_nivel = 8
min_correctas_avance = 5
niveles_maximos = 5
limite_preguntas_total = 40
```

## 🔄 Flujo de Evaluación Simplificado

### **Regla Principal: 8 Preguntas por Nivel**

```
Candidato responde 8 preguntas del nivel actual
│
├─→ ¿Obtuvo 5 o más correctas?
│   │
│   ├─→ SÍ → ✅ AVANZA AL SIGUIENTE NIVEL
│   │         - Nivel actual += 1
│   │         - Resetea contador de preguntas (0)
│   │         - Resetea contador de correctas (0)
│   │         │
│   │         └─→ ¿Nivel > 5?
│   │             │
│   │             ├─→ SÍ → ✅ EVALUACIÓN COMPLETADA (Éxito)
│   │             └─→ NO → Continúa al siguiente nivel
│   │
│   └─→ NO → ❌ EVALUACIÓN TERMINADA
│             Razón: "No alcanzó 5 respuestas correctas en nivel X"
```

## 🎯 Sistema de Puntuación

### **Preguntas de Respuesta Única**
```python
Respuesta correcta = 1.0 punto
Respuesta incorrecta = 0 puntos
```

### **Preguntas de Respuesta Múltiple**

#### Ejemplo: Pregunta con 2 respuestas correctas (A, C)

| Usuario selecciona | Puntaje | Cuenta como correcta? |
|-------------------|---------|----------------------|
| A, C              | 1.0     | ✅ SÍ               |
| A                 | 0.5     | ❌ NO               |
| C                 | 0.5     | ❌ NO               |
| A, B              | 0.5     | ❌ NO               |
| B, D              | 0.0     | ❌ NO               |

#### Lógica del Código

```python
if es_multiple:
    if set(respuestas_usuario) == set(respuestas_correctas):
        puntaje = 1.0  # Todas correctas
    elif any(r in respuestas_correctas for r in respuestas_usuario):
        puntaje = 0.5  # Al menos una correcta
    else:
        puntaje = 0.0  # Ninguna correcta

# Para avance de nivel
es_correcta = (puntaje >= 1.0)  # Solo 1.0 cuenta como correcta
```

## 📊 Ejemplo de Evaluación Completa

### **Escenario 1: Candidato Exitoso**

```
NIVEL 1:
P1: ✅ 1.0 → Correctas: 1/5
P2: ✅ 1.0 → Correctas: 2/5
P3: ❌ 0.0 → Correctas: 2/5
P4: ✅ 1.0 → Correctas: 3/5
P5: ⚠️  0.5 → Correctas: 3/5 (puntaje parcial, NO cuenta)
P6: ✅ 1.0 → Correctas: 4/5
P7: ✅ 1.0 → Correctas: 5/5
P8: ❌ 0.0 → Correctas: 5/5

Resultado: 5/8 correctas → ✅ AVANZA A NIVEL 2
Puntaje acumulado: 5.5 puntos
```

```
NIVEL 2:
P9-P16: 6/8 correctas → ✅ AVANZA A NIVEL 3
```

```
NIVEL 3:
P17-P24: 5/8 correctas → ✅ AVANZA A NIVEL 4
```

```
NIVEL 4:
P25-P32: 5/8 correctas → ✅ AVANZA A NIVEL 5
```

```
NIVEL 5:
P33-P40: 5/8 correctas → ✅ EVALUACIÓN COMPLETADA
Nivel final: 5 (Máximo alcanzado)
```

### **Escenario 2: Candidato que No Alcanza el Mínimo**

```
NIVEL 1:
P1: ✅ 1.0 → Correctas: 1/5
P2: ❌ 0.0 → Correctas: 1/5
P3: ⚠️  0.5 → Correctas: 1/5 (NO cuenta)
P4: ✅ 1.0 → Correctas: 2/5
P5: ❌ 0.0 → Correctas: 2/5
P6: ⚠️  0.5 → Correctas: 2/5 (NO cuenta)
P7: ✅ 1.0 → Correctas: 3/5
P8: ❌ 0.0 → Correctas: 3/5

Resultado: 3/8 correctas → ❌ EVALUACIÓN TERMINADA
Razón: "No alcanzó el mínimo de 5 respuestas correctas en nivel 1 (3/8 correctas)"
Puntaje final: 4.0 puntos
```

### **Escenario 3: Candidato que Falla en Nivel Intermedio**

```
NIVEL 1: 5/8 correctas → ✅ AVANZA
NIVEL 2: 6/8 correctas → ✅ AVANZA
NIVEL 3: 4/8 correctas → ❌ EVALUACIÓN TERMINADA

Razón: "No alcanzó el mínimo de 5 respuestas correctas en nivel 3 (4/8 correctas)"
Nivel alcanzado: 2
Preguntas respondidas: 24/40
```

## 🔍 Diferencia Clave: Puntaje vs. Correctas

### **Puntaje Acumulado (puntos)**
- Se usa para el puntaje total del candidato
- Incluye puntos parciales (0.5)
- Aparece en el reporte final
- Ejemplo: Un candidato puede tener 32.5 puntos de 40

### **Contador de Correctas (correctas_nivel)**
- Se usa SOLO para determinar avance de nivel
- Solo incrementa con puntaje = 1.0
- **NO** incrementa con puntaje = 0.5
- Debe llegar a 5 para avanzar

## ✅ Ventajas de Este Sistema

1. **Simple y claro**: 8 preguntas por nivel, 5 correctas para avanzar
2. **Justo en puntuación**: Otorga puntos parciales por respuestas parcialmente correctas
3. **Estricto en avance**: Solo respuestas completamente correctas cuentan para avanzar
4. **Predecible**: El candidato sabe exactamente qué esperar

## 📝 Cambios Realizados

### **Eliminado**
- ❌ Sistema de múltiples intentos por nivel
- ❌ Acumulación de correctas entre intentos
- ❌ Cálculo dinámico de preguntas disponibles

### **Mantenido**
- ✅ Sistema de puntuación parcial (0.5 puntos)
- ✅ Contador estricto de correctas (solo 1.0 cuenta)
- ✅ Límite de 40 preguntas total
- ✅ 5 niveles máximos

## 🎮 Comportamiento en el Frontend

El sistema muestra:
- Nivel actual del candidato
- Preguntas respondidas en el nivel (X/8)
- Correctas obtenidas en el nivel (X/5)
- Puntaje acumulado total

Cuando la evaluación termina:
- Muestra el reporte final con nivel alcanzado
- Muestra puntaje total (incluyendo 0.5)
- Muestra razón de finalización si no completó
