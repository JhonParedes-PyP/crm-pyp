import pandas as pd
import json

filename = "REPORTE DE SALDO CARTERA LORENA PRADA - JULIO 2026.xlsx"
df = pd.read_excel(filename, header=0)

garantias = df['Garantia'].dropna().unique()
print("Garantias encontradas:", garantias)
