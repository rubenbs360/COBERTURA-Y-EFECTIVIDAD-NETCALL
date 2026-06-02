import pandas as pd

CSV_PATH = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - 2026-05-26T112722.355.csv"

df = pd.read_csv(CSV_PATH, encoding='utf-8', encoding_errors='ignore')
print("Total rows:", len(df))
print("\n--- Distribution of Estado_T ---")
print(df['Estado_T'].value_counts(dropna=False))

print("\n--- Distribution of FRM_Departamento_de_entrega ---")
print(df['FRM_Departamento_de_entrega'].value_counts().head(10))

print("\n--- Distribution of Tipo_Despacho_Detalle ---")
print(df['Tipo_Despacho_Detalle'].value_counts().head(10))

print("\n--- Distribution of Centro ---")
print(df['Centro'].value_counts(dropna=False))
