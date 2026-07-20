import pandas as pd
import json

filename = "INFORME PROCESAL JUNIO 2026 ALE LORENA PRADA.xlsx"
df = pd.read_excel(filename, sheet_name='Hoja1', header=None, nrows=10)

# Print first 10 rows as list of lists
data = df.fillna("").values.tolist()
for idx, row in enumerate(data):
    print(f"Row {idx}: {row}")
