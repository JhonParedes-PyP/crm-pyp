import pandas as pd
df = pd.read_excel('CONVENIOS.xlsx')
print(df[df['Cuenta'].astype(str).str.contains('107172101000809573')])
