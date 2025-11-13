import os
import pandas as pd

ruta = os.path.join(os.getcwd(), 'temas', 'Tenable.xlsx')
if not os.path.exists(ruta):
    print('ERROR: archivo no encontrado:', ruta)
    raise SystemExit(1)

df = pd.read_excel(ruta)
print('Columnas en el Excel:', list(df.columns))

issues = []
for idx, row in df.iterrows():
    rownum = idx + 2  # approximate Excel row (header row 1)
    razones = []
    opciones = []
    for letra in ['A','B','C','D','E']:
        if letra in df.columns:
            opt = str(row.get(letra, '')).strip()
            if opt and opt.upper() not in ['NAN','NONE']:
                opciones.append(opt)
    if len(opciones) < 2:
        razones.append(f'Opciones insuficientes ({len(opciones)})')
    # comprobar respuestas
    respuestas_validas = []
    for col in ['RESPUESTA CORRECTA', 'RESPUESTA CORRECTA 1', 'RESPUESTA CORRECTA 2']:
        if col in df.columns:
            val = row.get(col)
            if val and not pd.isna(val):
                val_str = str(val).strip().upper()
                if val_str in ['A','B','C','D','E']:
                    respuestas_validas.append(val_str)
    if not respuestas_validas:
        razones.append('Sin respuesta correcta válida')
    nivel = row.get('NIVEL', '')
    if razones:
        issues.append({'excel_row': rownum, 'idx': idx, 'nivel': nivel, 'razones': razones, 'pregunta': row.get('PREGUNTA',''), 'raw': row.to_dict()})

print('\nFilas con problemas detectadas por el loader:')
for it in issues:
    print(f"Row {it['excel_row']} (idx {it['idx']}), NIVEL={it['nivel']}, razones={it['razones']}")
    preg = it.get('pregunta')
    if pd.notna(preg):
        print('  Pregunta:', str(preg)[:120])
    print('')

print('Total filas problemáticas:', len(issues))
