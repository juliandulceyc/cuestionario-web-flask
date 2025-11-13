import pandas as pd
import os

def parse():
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
        preguntas.append({'id':pregunta_id,'nivel':nivel_num,'pregunta':row.get('PREGUNTA','')})
    from collections import Counter
    print('Loaded', len(preguntas), 'questions')
    print('Level counts:', Counter([q['nivel'] for q in preguntas]))
    # print sample
    for q in preguntas[:10]:
        print(q)

if __name__ == '__main__':
    parse()
