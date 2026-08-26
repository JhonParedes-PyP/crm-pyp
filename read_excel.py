import pandas as pd
import os

filename = "REPORTE DE GESTIONES JUDICALES Y EXTRAJUDICIALES AG. SAN BORJA.xlsx"
filepath = os.path.join(r"C:\CRM PYP", filename)

df = pd.read_excel(filepath, header=None)
print("Primeras 15 filas del Excel:")
for i in range(min(15, len(df))):
    row = df.iloc[i]
    print(f"Fila {i}: {list(row)}")
