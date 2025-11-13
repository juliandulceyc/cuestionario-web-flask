# Simulación: cada bloque de 8 -> 3 correctas (1) luego 5 incorrectas (0)
CONFIG = {
    'preguntas_por_nivel': 8,
    'racha_para_flag': 3,
    'min_correctas_para_avanzar': 4,  # suma de puntajes necesaria para avanzar
}

def simulate_blocks(num_blocks=5):
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
    seq_block = [1,1,1,0,0,0,0,0]
    for b in range(num_blocks):
        logs.append(f"--- Inicio bloque {b+1} (nivel {estado['nivel_actual']}) ---")
        for i,p in enumerate(seq_block, start=1):
            estado['preguntas_nivel'] += 1
            estado['preguntas_mostradas'] += 1
            estado['suma_puntaje_nivel'] += p
            estado['suma_puntaje_total'] += p
            if p == 1:
                estado['correctas_nivel'] += 1
                estado['racha_actual'] += 1
                if estado['racha_actual'] >= CONFIG['racha_para_flag']:
                    estado['flag_racha'] = True
            else:
                estado['racha_actual'] = 0
            logs.append({
                'pregunta_num': estado['preguntas_mostradas'],
                'nivel_mostrado': estado['nivel_actual'],
                'puntaje': p,
                'racha_actual': estado['racha_actual'],
                'flag_racha': estado['flag_racha'],
                'suma_puntaje_nivel': estado['suma_puntaje_nivel']
            })
        # Fin de bloque: evaluar
        suma = estado['suma_puntaje_nivel']
        min_req = CONFIG['min_correctas_para_avanzar']
        logs.append(f"Fin bloque {b+1} nivel {estado['nivel_actual']}: suma_puntaje={suma}")
        flag_racha = estado.get('flag_racha', False)
        if suma >= min_req or flag_racha:
            logs.append(f"DECISIÓN: AVANZA de nivel {estado['nivel_actual']} a {estado['nivel_actual']+1} (suma={suma}, flag_racha={flag_racha})")
            estado['nivel_actual'] += 1
            estado['preguntas_nivel'] = 0
            estado['correctas_nivel'] = 0
            estado['suma_puntaje_nivel'] = 0.0
            estado['racha_actual'] = 0
            estado['flag_racha'] = False
        else:
            logs.append(f"DECISIÓN: NO alcanza min ({suma} < {min_req}) -> DEMOTAR si posible")
            if estado['nivel_actual'] > 1:
                estado['nivel_actual'] = max(1, estado['nivel_actual'] - 1)
                estado['demoted_times'] += 1
                logs.append(f"DEMOTADO a nivel {estado['nivel_actual']}")
            else:
                logs.append(f"PERMANECE en nivel 1")
            estado['preguntas_nivel'] = 0
            estado['correctas_nivel'] = 0
            estado['suma_puntaje_nivel'] = 0.0
            estado['racha_actual'] = 0
            estado['flag_racha'] = False
    return estado, logs

if __name__ == '__main__':
    estado, logs = simulate_blocks(num_blocks=5)
    for item in logs:
        print(item)
    print('\nEstado final:')
    print(estado)
