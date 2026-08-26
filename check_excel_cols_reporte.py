import pandas as pd

try:
    df2 = pd.read_excel('REPORTE DE SALDO CARTERA LORENA PRADA - JULIO 2026.xlsx', nrows=0)
    print("\nColumnas de REPORTE DE SALDO:")
    for col in df2.columns:
        print(f" - {col}")
except Exception as e:
    print("Error:", e)
