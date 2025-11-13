import random
import pandas as pd
import os

# Cargar preguntas
def load_preguntas():
    ruta = os.path.join('temas','Tenable.xlsx')
    df = pd.read_excel(ruta)
    preguntas = []
    used_ids = set()
    for idx, row in df.iterrows():
        pregunta_id_raw = row.get('NUM')
        try:
            pregunta_id = int(''.join(filter(str.isdigit, str(pregunta_id_raw))))
        except:
            pregunta_id = idx+1
        while pregunta_id in used_ids or pregunta_id == 0:
            pregunta_id += 1
        used_ids.add(pregunta_id)
        try:
            nivel_raw = row.get('NIVEL', 1)
            nivel_num = int(''.join(filter(str.isdigit, str(nivel_raw))))
            if nivel_num < 1 or nivel_num > 5:
                nivel_num = 1
        except:
            nivel_num = 1
        pregunta_texto = row.get('PREGUNTA', row.get('TIPO DE PREGUNTA', ''))
        preguntas.append({'id':pregunta_id,'nivel':nivel_num,'pregunta':pregunta_texto})
    return preguntas

# nuevo fallback: preferir niveles inferiores, luego superiores
def fallback(preguntas, preguntas_mostradas, nivel_busqueda, max_nivel=5):
    for lvl in range(nivel_busqueda-1, 0, -1):
        cand = [p for p in preguntas if p['id'] not in preguntas_mostradas and p.get('nivel',1)==lvl]
        if cand:
            return cand, lvl
    for lvl in range(nivel_busqueda+1, max_nivel+1):
        cand = [p for p in preguntas if p['id'] not in preguntas_mostradas and p.get('nivel',1)==lvl]
        if cand:
            return cand, lvl
    return [], None


def simulate():
    preguntas = load_preguntas()
    random.seed(0)
    estado = {
        'preguntas_mostradas': [],
        'nivel_actual': 1,
        'preguntas_nivel': 0,
        'suma_puntaje_nivel': 0.0,
        'racha_actual': 0,
        'flag_racha': False,
    }
    preguntas_por_nivel = 8
    min_req_avance = 4
    pattern = [1,1,1,0,0,0,0,0]
    logs = []
    total_questions = 40
    i = 0
    while i < total_questions:
        nivel_actual = estado['nivel_actual']
        disponibles = [p for p in preguntas if p['id'] not in estado['preguntas_mostradas'] and p.get('nivel',1)==nivel_actual]
        if not disponibles:
            candidatos, nivel_usado = fallback(preguntas, estado['preguntas_mostradas'], nivel_actual)
            if not candidatos:
                logs.append(('no_more',))
                break
            pregunta_sel = random.choice(candidatos)
            motivo = f'fallback nivel {nivel_usado}'
        else:
            pregunta_sel = random.choice(disponibles)
            motivo = 'mismo nivel'
        estado['preguntas_mostradas'].append(pregunta_sel['id'])
        pregunta_num = len(estado['preguntas_mostradas'])
        respuesta = pattern[(pregunta_num-1) % len(pattern)]
        if respuesta == 1:
            estado['suma_puntaje_nivel'] += 1
            estado['racha_actual'] += 1
            if estado['racha_actual'] >= 3:
                estado['flag_racha'] = True
        else:
            estado['racha_actual'] = 0
        estado['preguntas_nivel'] += 1
        logs.append((pregunta_num, pregunta_sel['id'], pregunta_sel['nivel'], nivel_actual, respuesta, estado['suma_puntaje_nivel'], estado['flag_racha'], motivo))
        if estado['preguntas_nivel'] >= preguntas_por_nivel:
            suma = estado['suma_puntaje_nivel']
            flag = estado['flag_racha']
            if suma >= min_req_avance or flag:
                old = estado['nivel_actual']
                estado['nivel_actual'] += 1
                logs.append(('DECISION','AVANZA',old,estado['nivel_actual'],suma,flag))
            else:
                old = estado['nivel_actual']
                if estado['nivel_actual'] > 1:
                    estado['nivel_actual'] -= 1
                logs.append(('DECISION','NO_AVANZA',old,estado['nivel_actual'],suma,flag))
            estado['preguntas_nivel'] = 0
            estado['suma_puntaje_nivel'] = 0.0
            estado['racha_actual'] = 0
            estado['flag_racha'] = False
        i += 1
    return logs

if __name__ == '__main__':
    logs = simulate()
    for l in logs:
        print(l)
    q16 = [l for l in logs if isinstance(l, tuple) and l[0]==16]
    print('\nPregunta 16:', q16)
