import pandas as pd
import os

ruta = os.path.join('temas','Tenable.xlsx')
if not os.path.exists(ruta):
    print('ERROR: No se encuentra', ruta)
else:
    df = pd.read_excel(ruta)
    # intentamos normalizar columna NIVEL
    if 'NIVEL' not in df.columns:
        print('ERROR: columna "NIVEL" no encontrada en el Excel. Columnas:', list(df.columns))
    else:
        niveles = df['NIVEL'].fillna('1').apply(lambda x: str(x).strip())
        # convertir a entero si es posible
        def conv(v):
            try:
                return int(''.join([c for c in v if c.isdigit()]) or 1)
            except:
                return 1
        niveles_int = niveles.apply(conv)
        counts = niveles_int.value_counts().sort_index()
        print('Cuenta de preguntas por NIVEL en temas/Tenable.xlsx:')
        for nivel, cnt in counts.items():
            print(f'Nivel {nivel}: {cnt}')
        # mostrar totales y filas sin nivel válido
        print('\nTotal filas leídas:', len(df))
        # detectar filas excluidas por falta de opciones/respuestas (si aplica)
        # (no hacemos filtrado aquí, sólo el conteo bruto de la columna NIVEL)
