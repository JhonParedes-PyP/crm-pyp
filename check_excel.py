import pandas as pd

try:
    df = pd.read_excel('ANEXOS Y CLAVES.xlsx')
    print("Columns:", df.columns.tolist())
    print(df.to_string())
except Exception as e:
    print("Error:", e)
