# Simulación de la política B (no interrumpir bloque)
from math import ceil

CONFIG = {
    'preguntas_por_nivel': 8,
    'racha_para_flag': 3,
    'min_correctas_para_avanzar': 4,  # suma de puntajes (parciales 0.5)
}


def simulate(sequence, name="Sim"):
    estado = {
        'nivel_actual': 1,
        'preguntas_nivel': 0,
        'correctas_nivel': 0,
        'suma_puntaje_nivel': 0.0,
        'suma_puntaje_total': 0.0,
        'racha_actual': 0,
        'flag_racha': False,
        'demoted_times': 0,
        'preguntas_mostradas': 0,
    }
    logs = []
    for puntaje in sequence:
        nivel = estado['nivel_actual']
        estado['preguntas_nivel'] += 1
        estado['preguntas_mostradas'] += 1
        estado['suma_puntaje_nivel'] += puntaje
        estado['suma_puntaje_total'] += puntaje
        if puntaje == 1:
            estado['correctas_nivel'] += 1
            estado['racha_actual'] += 1
            if estado['racha_actual'] >= CONFIG['racha_para_flag']:
                estado['flag_racha'] = True
        else:
            estado['racha_actual'] = 0
        logs.append((estado['preguntas_mostradas'], nivel, puntaje, estado['racha_actual'], estado['flag_racha'], estado['suma_puntaje_nivel']))

        # si se completa el bloque, evaluar
        if estado['preguntas_nivel'] >= CONFIG['preguntas_por_nivel']:
            suma = estado['suma_puntaje_nivel']
            min_req = CONFIG['min_correctas_para_avanzar']
            if suma >= min_req:
                # avanza
                logs.append((f"Bloque completo nivel {nivel}: suma={suma} >= {min_req} -> AVANZA"))
                estado['nivel_actual'] += 1
                estado['preguntas_nivel'] = 0
                estado['correctas_nivel'] = 0
                estado['suma_puntaje_nivel'] = 0.0
                estado['racha_actual'] = 0
                estado['flag_racha'] = False
            else:
                # demota si es posible
                logs.append((f"Bloque completo nivel {nivel}: suma={suma} < {min_req} -> DEMORA/DEMOTE"))
                if estado['nivel_actual'] > 1:
                    estado['nivel_actual'] = max(1, estado['nivel_actual'] - 1)
                    estado['demoted_times'] += 1
                # reset counters
                estado['preguntas_nivel'] = 0
                estado['correctas_nivel'] = 0
                estado['suma_puntaje_nivel'] = 0.0
                estado['racha_actual'] = 0
                estado['flag_racha'] = False

    return estado, logs


if __name__ == '__main__':
    # Escenario A: candidato fuerte (todas correctas)
    seqA = [1]*40
    estadoA, logsA = simulate(seqA, "Fuerte")
    print("--- Escenario A: Candidato fuerte ---")
    for l in logsA[:20]:
        print(l)
    print('...')
    print('Resultado A:', estadoA)

    # Escenario B: racha inicial de 3 pero no alcanza 4 en el bloque
    # Simulamos bloque: 1,1,1,0.0,0.0,0.5,0.0,0.0 -> suma = 3 + 0.5 = 3.5 < 4 -> no avanza
    seqB = [1,1,1,0,0,0.5,0,0]  # primer bloque
    # follow with more blocks to reach 40 total
    seqB = seqB * 5  # 40 preguntas
    estadoB, logsB = simulate(seqB, "Debil")
    print('\n--- Escenario B: Racha 3 pero suma insuficiente ---')
    for l in logsB[:20]:
        print(l)
    print('...')
    print('Resultado B:', estadoB)
