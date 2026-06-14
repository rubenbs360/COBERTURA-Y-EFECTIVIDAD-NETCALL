import pandas as pd

CSV_PATH = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - 2026-05-26T112722.355.csv"
XLSX_PATH = r"C:\Users\USUARIO\Downloads\DIRECTORIO TIENDAS MAYO 2026 (1).xlsx"

xl = pd.ExcelFile(XLSX_PATH)
for sheet in xl.sheet_names:
    df = xl.parse(sheet)
    print(f"\n--- SHEET: {sheet} (rows={len(df)}, cols={len(df.columns)}) ---")
    print("Columns:", df.columns.tolist()[:15])
    print(df.head(2))
