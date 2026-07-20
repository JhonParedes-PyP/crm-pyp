import pandas as pd
import json

filename = "INFORME PROCESAL JUNIO 2026 ALE LORENA PRADA.xlsx"
df_dict = pd.read_excel(filename, sheet_name=None)

for sheet_name, df in df_dict.items():
    print(f"--- Hoja: {sheet_name} ---")
    columns = list(df.columns)
    print(json.dumps(columns, indent=2, ensure_ascii=False))
    print("\n")
