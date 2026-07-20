import pandas as pd

# Load the file
filename = 'Plantilla_Base_PyP NUEVO.xlsx'
df_dict = pd.read_excel(filename, sheet_name=None)

# Get the first sheet (which is usually the data sheet)
first_sheet_name = list(df_dict.keys())[0]
df = df_dict[first_sheet_name]

# Add new columns
df['INTERES_COMPENSATORIO'] = ''
df['INTERES_MORATORIO'] = ''
df['GASTOS_COMISIONES'] = ''
df['GARANTIA_REALIZABLE'] = ''

# Save to a new file
output_filename = 'Plantilla_Base_PyP_ACTUALIZADO_CAMPANAS.xlsx'
with pd.ExcelWriter(output_filename) as writer:
    for sheet_name, sheet_df in df_dict.items():
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Modificado exitosamente y guardado como {output_filename}")
