import pandas as pd
import json

filename = "REPORTE DE SALDO CARTERA LORENA PRADA - JULIO 2026.xlsx"
df = pd.read_excel(filename, header=0) # Read the first row as header

columns = [str(c) for c in df.columns]
print(json.dumps(columns, indent=2, ensure_ascii=False))
