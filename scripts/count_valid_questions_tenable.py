import os
import pandas as pd

ruta = os.path.join(os.getcwd(), 'temas', 'Tenable.xlsx')
if not os.path.exists(ruta):
    print('ERROR: archivo no encontrado:', ruta)
    raise SystemExit(1)

df = pd.read_excel(ruta)
validas = []
used_ids = set()
for idx, row in df.iterrows():
    opciones = []
    for letra in ['A','B','C','D','E']:
        if letra in df.columns:
            opt = str(row.get(letra, '')).strip()
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
    validas.append((pregunta_id, nivel_num))

from collections import Counter
counts = Counter([v for (_,v) in validas])
print('Preguntas válidas por nivel (aplicando filtros de la app):')
for nivel in sorted(counts.keys()):
    print(f'Nivel {nivel}: {counts[nivel]}')
print('\nTotal válidas:', len(validas))
# listar filas omitidas por nivel
print('\nIDs válidas:', [p for p in validas])
