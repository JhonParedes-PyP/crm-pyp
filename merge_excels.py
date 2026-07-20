import pandas as pd
import numpy as np

# 1. Cargar las bases
plantilla_file = "Plantilla_Base_PyP_ACTUALIZADO_CAMPANAS.xlsx"
reporte_file = "REPORTE DE SALDO CARTERA LORENA PRADA - JULIO 2026.xlsx"
informe_file = "INFORME PROCESAL JUNIO 2026 ALE LORENA PRADA.xlsx"
output_file = "Plantilla_Base_PyP_COMPLETO.xlsx"

print("Cargando archivos...")
df_plantilla_dict = pd.read_excel(plantilla_file, sheet_name=None, dtype=str)
sheet_name = list(df_plantilla_dict.keys())[0]
df_plantilla = df_plantilla_dict[sheet_name]

df_reporte = pd.read_excel(reporte_file, header=0, dtype=str)
df_informe = pd.read_excel(informe_file, sheet_name='Hoja1', header=1, dtype=str)

# Limpiar las columnas clave
df_plantilla['COD_CREDITO'] = df_plantilla['COD_CREDITO'].str.strip()
df_reporte['Cuenta'] = df_reporte['Cuenta'].str.strip()
df_informe['CUENTA'] = df_informe['CUENTA'].str.strip()

# 2. Hacer el cruce con el REPORTE DE SALDO (para sacar Saldo Interes, Saldo Mora, Saldo Gastos)
print("Cruzando con REPORTE DE SALDO...")
df_merged = df_plantilla.merge(
    df_reporte[['Cuenta', 'Saldo Interes', 'Saldo Mora', 'Saldo Gastos']], 
    left_on='COD_CREDITO', 
    right_on='Cuenta', 
    how='left'
)

# Llenar las columnas de la plantilla
df_merged['INTERES_COMPENSATORIO'] = df_merged['Saldo Interes']
df_merged['INTERES_MORATORIO'] = df_merged['Saldo Mora']
df_merged['GASTOS_COMISIONES'] = df_merged['Saldo Gastos']

# 3. Hacer el cruce con el INFORME PROCESAL (para sacar DETALLE DEL BIEN -> GARANTIA)
print("Cruzando con INFORME PROCESAL...")
df_merged = df_merged.merge(
    df_informe[['CUENTA', 'DETALLE DEL BIEN']],
    left_on='COD_CREDITO',
    right_on='CUENTA',
    how='left'
)

# Lógica para GARANTIA_REALIZABLE
def determinar_garantia(detalle):
    if pd.isna(detalle) or str(detalle).strip() == "" or str(detalle).strip().upper() == "NINGUNO":
        return "NO"
    return "SI"

df_merged['GARANTIA_REALIZABLE'] = df_merged['DETALLE DEL BIEN'].apply(determinar_garantia)

# Eliminar columnas auxiliares del cruce
columnas_a_eliminar = ['Cuenta', 'Saldo Interes', 'Saldo Mora', 'Saldo Gastos', 'CUENTA', 'DETALLE DEL BIEN']
for col in columnas_a_eliminar:
    if col in df_merged.columns:
        df_merged = df_merged.drop(columns=[col])

# Guardar el resultado en el mismo archivo
print(f"Guardando archivo final en {output_file}...")
with pd.ExcelWriter(output_file) as writer:
    df_merged.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Guardar el resto de hojas si existian
    for s_name, s_df in df_plantilla_dict.items():
        if s_name != sheet_name:
            s_df.to_excel(writer, sheet_name=s_name, index=False)

print(f"¡Listo! El archivo {output_file} ha sido cruzado y llenado con éxito.")
