import pandas as pd

try:
    df = pd.read_excel('Plantilla_Base_PyP_COMPLETO.xlsx', nrows=0)
    print("Columnas de Plantilla_Base_PyP_COMPLETO:")
    for col in df.columns:
        if 'convenio' in str(col).lower() or 'pago' in str(col).lower() or 'monto' in str(col).lower() or 'cuota' in str(col).lower() or 'atras' in str(col).lower() or 'negociac' in str(col).lower() or 'fecha' in str(col).lower():
            print(f" - {col}")
            
    df2 = pd.read_excel('Plantilla_Base_PyP NUEVO.xlsx', nrows=0)
    print("\nColumnas de Plantilla_Base_PyP NUEVO:")
    for col in df2.columns:
        if 'convenio' in str(col).lower() or 'pago' in str(col).lower() or 'monto' in str(col).lower() or 'cuota' in str(col).lower() or 'atras' in str(col).lower() or 'negociac' in str(col).lower() or 'fecha' in str(col).lower():
            print(f" - {col}")
except Exception as e:
    print("Error:", e)
