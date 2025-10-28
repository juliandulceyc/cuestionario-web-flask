"""
Script de prueba para la lógica simplificada
8 preguntas por nivel, 5 correctas para avanzar, si no termina
"""

def simular_evaluacion_simple():
    """Simula diferentes escenarios con la lógica simplificada"""
    
    print("=" * 70)
    print("SIMULACIÓN - LÓGICA SIMPLIFICADA")
    print("=" * 70)
    print("Regla: 8 preguntas por nivel, 5 correctas para avanzar\n")
    
    escenarios = [
        {
            "nombre": "Escenario 1: Candidato Exitoso (completa todos los niveles)",
            "niveles": [
                [1, 1, 0, 1, 1, 1, 0, 0],  # Nivel 1: 5/8
                [1, 1, 1, 1, 1, 0, 0, 1],  # Nivel 2: 6/8
                [1, 1, 1, 0, 1, 1, 0, 0],  # Nivel 3: 5/8
                [1, 1, 1, 1, 0, 1, 0, 0],  # Nivel 4: 5/8
                [1, 0, 1, 1, 1, 1, 0, 0],  # Nivel 5: 5/8
            ]
        },
        {
            "nombre": "Escenario 2: Falla en Nivel 1",
            "niveles": [
                [1, 0, 1, 0, 0, 0, 1, 0],  # Nivel 1: 3/8
            ]
        },
        {
            "nombre": "Escenario 3: Falla en Nivel 3",
            "niveles": [
                [1, 1, 1, 1, 1, 0, 0, 0],  # Nivel 1: 5/8
                [1, 1, 1, 1, 1, 1, 0, 0],  # Nivel 2: 6/8
                [1, 0, 1, 0, 1, 0, 1, 0],  # Nivel 3: 4/8
            ]
        },
        {
            "nombre": "Escenario 4: Con respuestas parciales (0.5)",
            "niveles": [
                [1, 0.5, 1, 0.5, 1, 1, 1, 0],  # Nivel 1: 5 correctas completas
            ]
        }
    ]
    
    for escenario in escenarios:
        print("\n" + "=" * 70)
        print(escenario["nombre"])
        print("=" * 70)
        
        nivel_actual = 1
        preguntas_totales = 0
        puntaje_total = 0
        
        for nivel_respuestas in escenario["niveles"]:
            correctas = sum(1 for r in nivel_respuestas if r == 1)
            puntaje_nivel = sum(nivel_respuestas)
            preguntas_totales += 8
            puntaje_total += puntaje_nivel
            
            print(f"\nNIVEL {nivel_actual}:")
            print(f"  Respuestas: {nivel_respuestas}")
            print(f"  Correctas completas: {correctas}/8")
            print(f"  Puntaje del nivel: {puntaje_nivel:.1f}/8")
            print(f"  Preguntas totales: {preguntas_totales}/40")
            print(f"  Puntaje acumulado: {puntaje_total:.1f}")
            
            if correctas >= 5:
                if nivel_actual < 5:
                    print(f"  ✅ AVANZA A NIVEL {nivel_actual + 1}")
                    nivel_actual += 1
                else:
                    print(f"  ✅ EVALUACIÓN COMPLETADA (Nivel máximo alcanzado)")
                    break
            else:
                print(f"  ❌ EVALUACIÓN TERMINADA")
                print(f"  Razón: No alcanzó 5 respuestas correctas ({correctas}/8)")
                break
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"  Nivel alcanzado: {nivel_actual}")
        print(f"  Preguntas respondidas: {preguntas_totales}/40")
        print(f"  Puntaje final: {puntaje_total:.1f}")
        print(f"  Porcentaje: {(puntaje_total/preguntas_totales)*100:.1f}%")


if __name__ == "__main__":
    simular_evaluacion_simple()
