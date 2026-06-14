import pandas as pd

xlsx_path = r"C:\Users\USUARIO\Downloads\DIRECTORIO TIENDAS JUNIO.xlsx"
xl = pd.ExcelFile(xlsx_path)

df1 = xl.parse("Directorio LIMA ")
df2 = xl.parse("Directorio Provincia")

print("Lima stores count:", len(df1))
print("Lima missing lat:", df1['LATITUD'].isna().sum())
print("Lima '-' lat:", (df1['LATITUD'].astype(str).str.strip() == '-').sum())

print("Prov stores count:", len(df2))
print("Prov missing lat:", df2['LATITUD'].isna().sum())
print("Prov '-' lat:", (df2['LATITUD'].astype(str).str.strip() == '-').sum())

print("\nRows with invalid or '-' coordinates in Lima:")
invalid_lima = df1[df1['LATITUD'].isna() | (df1['LATITUD'].astype(str).str.strip() == '-')]
print(invalid_lima[['NOMBRE PDV', 'LATITUD', 'LONGITUD']])

print("\nRows with invalid or '-' coordinates in Provincia:")
invalid_prov = df2[df2['LATITUD'].isna() | (df2['LATITUD'].astype(str).str.strip() == '-')]
print(invalid_prov[['NOMBRE PDV', 'LATITUD', 'LONGITUD']])
