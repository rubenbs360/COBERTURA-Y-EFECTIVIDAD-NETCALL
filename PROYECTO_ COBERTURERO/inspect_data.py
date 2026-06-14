import os
import pandas as pd

CSV_PATH = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - 2026-05-26T112722.355.csv"
XLSX_PATH = r"C:\Users\USUARIO\Downloads\DIRECTORIO TIENDAS MAYO 2026 (1).xlsx"

print("--- Inspecting CSV ---")
df_csv = pd.read_csv(CSV_PATH, encoding='utf-8', encoding_errors='ignore', nrows=100)
print("CSV Columns:", df_csv.columns.tolist())
print("CSV Sample data:")
print(df_csv[['FRM_N_DNI_Asesor', 'EOC_ID_TIENDA', 'EOC_DELIVERYSTOREID', 'FRM_Departamento_de_entrega', 'Estado_T']].head(10))

print("\n--- Inspecting XLSX ---")
xl = pd.ExcelFile(XLSX_PATH)
for sheet in xl.sheet_names:
    df_sheet = xl.parse(sheet, nrows=5)
    print(f"Sheet '{sheet}': columns={df_sheet.columns.tolist()[:8]}... Total columns={len(df_sheet.columns)}")
