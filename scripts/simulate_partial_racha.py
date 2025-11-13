# Simula el caso: 2 correctas completas, 1 parcial (multiple), verificar flag_racha
from pprint import pprint

# Simular estado del candidato
c = {
    'preguntas_nivel': 0,
    'correctas_nivel': 0,
    'suma_puntaje_nivel': 0.0,
    'suma_puntaje_total': 0.0,
    'racha_actual': 0,
    'flag_racha': False
}

# configuración
racha_cfg = 3

# respuestas: 1,1,0.5 (parcial multiple)
respuestas = [1,1,0.5]

for i, puntaje in enumerate(respuestas, start=1):
    c['preguntas_nivel'] += 1
    if puntaje == 1:
        c['correctas_nivel'] += 1
        c['racha_actual'] += 1
        if c['racha_actual'] >= racha_cfg:
            c['flag_racha'] = True
    else:
        # aplicar la nueva regla: si es parcial y viene después de racha_cfg-1
        if puntaje > 0 and c['racha_actual'] >= (racha_cfg - 1):
            c['racha_actual'] += 1
            c['flag_racha'] = True
            # no incrementamos correctas_nivel
        else:
            c['racha_actual'] = 0
    c['suma_puntaje_nivel'] += puntaje
    c['suma_puntaje_total'] += puntaje
    print(f"Tras respuesta {i}: puntaje={puntaje}, correctas_nivel={c['correctas_nivel']}, racha_actual={c['racha_actual']}, flag_racha={c['flag_racha']}, suma_puntaje_nivel={c['suma_puntaje_nivel']}")
