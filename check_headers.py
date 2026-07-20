import pandas as pd
import json

filename = "INFORME PROCESAL JUNIO 2026 ALE LORENA PRADA.xlsx"
df = pd.read_excel(filename, sheet_name='Hoja1', header=1) # Try reading row 2 as header

columns = list(df.columns)
print(json.dumps(columns, indent=2, ensure_ascii=False))
