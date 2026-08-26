import pandas as pd

try:
    df2 = pd.read_excel('Plantilla_Base_PyP NUEVO.xlsx', nrows=0)
    print("\nColumnas de Plantilla_Base_PyP NUEVO:")
    for col in df2.columns:
        print(f" - {col}")
except Exception as e:
    print("Error:", e)
