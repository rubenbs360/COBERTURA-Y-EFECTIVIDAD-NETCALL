import pandas as pd

file_path = r"C:\Users\USUARIO\OneDrive\Escritorio\RUBEN DOC\NETCALL\REPORTERIA\NOMINA_NETCALL_03.06.xlsx"
df = pd.read_excel(file_path, sheet_name='NOMINA BO')
print(f"Total rows: {len(df)}")
print("\nUnique Campaigns (CAMPANA_NOMINA):")
print(df['CAMPANA_NOMINA'].value_counts())
print("\nFirst 10 usernames (USUARIO):")
print(df['USUARIO'].dropna().head(10).tolist())
print("\nMissing values in USUARIO column:", df['USUARIO'].isna().sum())
print("\nUnique supervisors:")
print(df['SUPERVISOR'].value_counts().head(5))
