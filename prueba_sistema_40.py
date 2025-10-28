"""
Script de prueba para verificar la lógica de acumulación de correctas
Con límite TOTAL de 40 preguntas y cálculo dinámico de intentos disponibles
"""

def simular_evaluacion():
    """Simula el comportamiento del sistema con cálculo dinámico"""
    
    # Estado inicial
    nivel_actual = 1
    preguntas_nivel = 0
    correctas_nivel = 0
    intentos_nivel = 0
    preguntas_totales = 0
    max_intentos_config = 2
    limite_total = 40
    
    print("=" * 70)
    print("SIMULACIÓN DE EVALUACIÓN CON LÍMITE TOTAL DE 40 PREGUNTAS")
    print("Sistema inteligente que calcula intentos disponibles dinámicamente")
    print("=" * 70)
    print(f"\nObjetivo: 5 respuestas correctas para avanzar de nivel")
    print(f"Límite total: {limite_total} preguntas")
    print(f"Máximo intentos por nivel (configurado): {max_intentos_config}\n")
    
    # Simular escenario: candidato que necesita 2 intentos en niveles 1 y 2
    respuestas_simuladas = [
        # Nivel 1 - Intento 1
        1, 0, 1, 0, 0, 0, 1, 0,  # 3 correctas
        # Nivel 1 - Intento 2
        1, 1, 0, 0, 0, 0, 0, 0,  # 2 correctas (total: 5, avanza!)
        # Nivel 2 - Intento 1
        1, 1, 0, 0, 1, 0, 0, 0,  # 3 correctas
        # Nivel 2 - Intento 2
        1, 1, 0, 0, 0, 0, 0, 0,  # 2 correctas (total: 5, avanza!)
        # Nivel 3 - Intento 1
        1, 1, 1, 1, 1, 0, 0, 0,  # 5 correctas (avanza!)
    ]
    
    for i, respuesta in enumerate(respuestas_simuladas, 1):
        preguntas_nivel += 1
        preguntas_totales += 1
        
        if respuesta == 1:
            correctas_nivel += 1
            print(f"P{preguntas_totales}: ✅ CORRECTA | Nivel {nivel_actual} | Correctas: {correctas_nivel}/5")
        else:
            print(f"P{preguntas_totales}: ❌ INCORRECTA | Nivel {nivel_actual} | Correctas: {correctas_nivel}/5")
        
        # Verificar si alcanzó 5 correctas
        if correctas_nivel >= 5:
            print(f"\n🎉 ¡AVANZA! Nivel {nivel_actual} -> {nivel_actual + 1} con {correctas_nivel} correctas en {intentos_nivel + 1} intento(s)")
            print(f"   Preguntas usadas: {preguntas_totales}/{limite_total}\n")
            nivel_actual += 1
            preguntas_nivel = 0
            correctas_nivel = 0
            intentos_nivel = 0
            
            if nivel_actual > 5:
                print("✅ ¡EVALUACIÓN COMPLETADA! Alcanzó nivel máximo")
                break
            continue
        
        # Verificar si completó 8 preguntas del nivel
        if preguntas_nivel >= 8:
            intentos_nivel += 1
            preguntas_restantes = limite_total - preguntas_totales
            niveles_futuros = 5 - nivel_actual
            preguntas_necesarias_futuros = niveles_futuros * 8
            puede_continuar = preguntas_restantes >= (8 + preguntas_necesarias_futuros)
            
            print(f"\n📊 Intento {intentos_nivel} completado - Nivel {nivel_actual}")
            print(f"   Correctas acumuladas: {correctas_nivel}/5")
            print(f"   Preguntas usadas: {preguntas_totales}/{limite_total}")
            print(f"   Preguntas restantes: {preguntas_restantes}")
            print(f"   Niveles futuros: {niveles_futuros} (necesitan {preguntas_necesarias_futuros} preguntas)")
            print(f"   Para otro intento necesita: {8 + preguntas_necesarias_futuros} preguntas")
            
            if correctas_nivel < 5:
                if intentos_nivel >= max_intentos_config:
                    print(f"   ❌ Máximo de intentos ({max_intentos_config}) alcanzado")
                    print(f"   🛑 EVALUACIÓN FINALIZADA en nivel {nivel_actual}\n")
                    break
                elif not puede_continuar:
                    print(f"   ❌ Preguntas insuficientes para otro intento")
                    print(f"   🛑 EVALUACIÓN FINALIZADA (necesita {8 + preguntas_necesarias_futuros}, tiene {preguntas_restantes})\n")
                    break
                else:
                    print(f"   ⚠️  No alcanzó 5 correctas, CONTINÚA intento {intentos_nivel + 1}\n")
                    preguntas_nivel = 0
    
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    print(f"Nivel alcanzado: {nivel_actual}")
    print(f"Preguntas totales: {preguntas_totales}/{limite_total}")
    print(f"Eficiencia: {(preguntas_totales/limite_total)*100:.1f}% del límite usado")


if __name__ == "__main__":
    simular_evaluacion()
