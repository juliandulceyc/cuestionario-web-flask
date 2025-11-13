# Simula una secuencia donde hay 3 correctas no consecutivas y además un parcial
# Patrón de respuestas en el bloque de 8 preguntas (1=full, 0.5=parcial, 0=wrong):
# Ejemplo: [1,0,1,0,1,0.5,0,0] => 3 correctas no consecutivas + 1 parcial

pattern = [1,0,1,0,1,0.5,0,0]

suma = 0.0
correctas = 0
racha = 0
flag_racha = False

for i, p in enumerate(pattern, start=1):
    suma += p
    if p == 1:
        correctas += 1
        racha += 1
        if racha >= 3:
            flag_racha = True
    else:
        # Parcial or wrong breaks racha unless special rule applies (not here)
        racha = 0
    print(f"Resp {i}: puntaje={p}, suma={suma}, correctas={correctas}, racha={racha}, flag_racha={flag_racha}")

# Decisión al final del bloque
min_req_avance = 4
regla_correctas_mas_parcial = (correctas >= 3 and suma >= 3.5)
print('\nDecision:')
print('suma_puntaje=', suma)
print('correctas=', correctas)
print('regla_correctas_mas_parcial=', regla_correctas_mas_parcial)
print('avanza=', (suma >= min_req_avance) or flag_racha or regla_correctas_mas_parcial)
