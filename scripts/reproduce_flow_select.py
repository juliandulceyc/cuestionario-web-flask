import random
import pandas as pd
import os

# Cargar preguntas usando la misma lógica simplificada
def load_preguntas():
    ruta = os.path.join('temas','Tenable.xlsx')
    df = pd.read_excel(ruta)
    preguntas = []
    used_ids = set()
    for idx, row in df.iterrows():
        opciones = []
        for letra in ['A','B','C','D','E']:
            if letra in df.columns:
                opt = str(row.get(letra,'' )).strip()
                if opt:
                    opciones.append(opt)
        if len(opciones) < 2:
            continue
        respuestas_correctas = []
        for col in ['RESPUESTA CORRECTA', 'RESPUESTA CORRECTA 1', 'RESPUESTA CORRECTA 2']:
            val = row.get(col)
            if val and not pd.isna(val):
                val_str = str(val).strip().upper()
                if val_str in ['A','B','C','D','E']:
                    respuestas_correctas.append(val_str)
        if not respuestas_correctas:
            continue
        pregunta_id_raw = row.get('NUM')
        try:
            pregunta_id = int(''.join(filter(str.isdigit, str(pregunta_id_raw))))
        except:
            pregunta_id = idx+1
        while pregunta_id in used_ids or pregunta_id == 0:
            pregunta_id += 1
        used_ids.add(pregunta_id)
        nivel_raw = row.get('NIVEL', 1)
        try:
            nivel_str = str(nivel_raw)
            nivel_num = int(''.join(filter(str.isdigit, nivel_str)))
            if nivel_num < 1 or nivel_num > 5:
                nivel_num = 1
        except:
            nivel_num = 1
        pregunta_texto = row.get('PREGUNTA', row.get('TIPO DE PREGUNTA', ''))
        preguntas.append({'id':pregunta_id,'nivel':nivel_num,'pregunta':pregunta_texto})
    return preguntas

# Fallback search same order as app
def buscar_pregunta_fallback(preguntas, preguntas_mostradas, nivel_busqueda):
    for nivel_alt in [nivel_busqueda-1, nivel_busqueda+1, 1,2,3,4,5]:
        if nivel_alt < 1 or nivel_alt > 5:
            continue
        preguntas_alt = [p for p in preguntas if p['id'] not in preguntas_mostradas and p['nivel']==nivel_alt]
        if preguntas_alt:
            return random.choice(preguntas_alt)
    return None

# Simular flujo: obtengo pregunta, luego respondemos segun pattern
def simulate():
    preguntas = load_preguntas()
    random.seed(0)
    # sort to have deterministic selection when choice happens
    # but the app uses random.choice; keep it
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

    # pattern per block: first 3 correct (1), then 5 wrong (0)
    pattern = [1,1,1,0,0,0,0,0]
    logs = []
    total_questions = 40
    i = 0
    while i < total_questions:
        # obtener_pregunta logic
        nivel_actual = estado['nivel_actual']
        preguntas_disponibles = [p for p in preguntas if p['id'] not in estado['preguntas_mostradas'] and p['nivel']==nivel_actual]
        if not preguntas_disponibles:
            # fallback
            candidate = buscar_pregunta_fallback(preguntas, estado['preguntas_mostradas'], nivel_actual)
            if not candidate:
                logs.append(('no_more_questions',))
                break
            pregunta_sel = candidate
        else:
            pregunta_sel = random.choice(preguntas_disponibles)
        estado['preguntas_mostradas'].append(pregunta_sel['id'])
        pregunta_num = len(estado['preguntas_mostradas'])
        # Determine pattern response
        respuesta = pattern[(pregunta_num-1) % len(pattern)]
        # process response similar to app
        if respuesta == 1:
            estado['suma_puntaje_nivel'] += 1
            estado['racha_actual'] += 1
            if estado['racha_actual'] >= 3:
                estado['flag_racha'] = True
        else:
            estado['racha_actual'] = 0
        estado['preguntas_nivel'] += 1
        logs.append((pregunta_num, pregunta_sel['id'], pregunta_sel['nivel'], nivel_actual, respuesta, estado['suma_puntaje_nivel'], estado['flag_racha']))

        # if finished block then decide
        if estado['preguntas_nivel'] >= preguntas_por_nivel:
            suma = estado['suma_puntaje_nivel']
            flag = estado['flag_racha']
            if suma >= min_req_avance or flag:
                # advance
                old = estado['nivel_actual']
                estado['nivel_actual'] += 1
                logs.append(('DECISION', 'AVANZA', old, estado['nivel_actual'], suma, flag))
            else:
                # demote if possible
                old = estado['nivel_actual']
                if estado['nivel_actual'] > 1:
                    estado['nivel_actual'] -= 1
                logs.append(('DECISION','NO_AVANZA', old, estado['nivel_actual'], suma, flag))
            # reset counters for next block
            estado['preguntas_nivel'] = 0
            estado['suma_puntaje_nivel'] = 0.0
            estado['racha_actual'] = 0
            estado['flag_racha'] = False
        i += 1
    return logs

if __name__ == '__main__':
    logs = simulate()
    for entry in logs:
        print(entry)
    # show which question 16 was
    q16 = [l for l in logs if isinstance(l, tuple) and len(l)>=3 and l[0]==16]
    print('\nQuestion 16 entries:', q16)
