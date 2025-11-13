import pandas as pd
import sys

def main():
    df = pd.read_excel('temas/Tenable.xlsx')
    matches = df[df['PREGUNTA'].str.contains('cumplimiento normativo', na=False, case=False)]
    if matches.empty:
        print('No encontrada')
    else:
        for _, row in matches.iterrows():
            print(row.get('NUM', ''), '|', row.get('PREGUNTA','')[:120], '| NIVEL:', row.get('NIVEL',''))

if __name__ == '__main__':
    main()
