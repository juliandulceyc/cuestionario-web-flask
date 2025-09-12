# Script para verificar el archivo Excel de preguntas
import os
import pandas as pd

TEMAS_DIR = os.path.join(os.getcwd(), 'temas')
config_path = os.path.join(os.getcwd(), 'config_tema.json')

if not os.path.exists(config_path):
    print('No existe config_tema.json. Selecciona un tema desde el panel de administración.')
    exit(1)

import json
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
archivo_excel = config.get('archivo_excel')
if not archivo_excel:
    print('No hay archivo de tema activo configurado.')
    exit(1)

ruta_excel = os.path.join(TEMAS_DIR, archivo_excel)
if not os.path.exists(ruta_excel):
    print(f'No se encontró el archivo: {ruta_excel}')
    exit(1)

try:
    df = pd.read_excel(ruta_excel)
except Exception as e:
    print(f'Error leyendo el archivo Excel: {e}')
    exit(1)

if df.empty:
    print('El archivo Excel está vacío.')
    exit(1)

print(f'Archivo Excel cargado correctamente: {archivo_excel}')
print(f'Cantidad de preguntas detectadas: {len(df)}')
print('Primeras filas:')
print(df.head())
