# CREAR debug_niveles_rapido.py
import pandas as pd

def verificar_niveles_excel():
    archivo = 'Evaluación FWS PAN V2.xlsx'
    df = pd.read_excel(archivo)
    
    print("🔍 VERIFICACIÓN DE NIVELES EN EXCEL")
    print("=" * 50)
    
    # Contar por nivel
    conteo = df['NIVEL'].value_counts().sort_index()
    print("📊 Distribución por nivel:")
    for nivel, cantidad in conteo.items():
        print(f"   Nivel {nivel}: {cantidad} preguntas")
    
    # Mostrar primeras 5 preguntas de nivel 1
    nivel_1 = df[df['NIVEL'] == 1]
    print(f"\n🎯 PRIMERAS 5 PREGUNTAS DE NIVEL 1:")
    for i, (index, row) in enumerate(nivel_1.head(5).iterrows()):
        pregunta = str(row.get('PREGUNTA', ''))[:60]
        print(f"   {i+1}. Fila {index+2}: {pregunta}...")
    
    # Verificar la pregunta problemática
    pregunta_problema = df[df['PREGUNTA'].str.contains('differentiator between the Palo Alto', na=False)]
    if not pregunta_problema.empty:
        nivel_problema = pregunta_problema.iloc[0]['NIVEL']
        fila_problema = pregunta_problema.index[0] + 2
        print(f"\n🚨 PREGUNTA PROBLEMÁTICA:")
        print(f"   Fila Excel: {fila_problema}")
        print(f"   Nivel asignado: {nivel_problema}")
        print(f"   ⚠️ Debería ser nivel 1, no {nivel_problema}")

if __name__ == "__main__":
    verificar_niveles_excel()