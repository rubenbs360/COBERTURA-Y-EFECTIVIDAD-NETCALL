import pandas as pd

XLSX_PATH = r"C:\Users\USUARIO\Downloads\DIRECTORIO TIENDAS MAYO 2026 (1).xlsx"
xl = pd.ExcelFile(XLSX_PATH)

for sheet in ['PROV SUP', 'LIMA SUP']:
    df = xl.parse(sheet)
    print(f"\n=== Columns in {sheet} ===")
    for c in df.columns:
        # Check if there is data in the column
        non_null_count = df[c].notna().sum()
        if non_null_count > 0:
            print(f" - {c} (non-null: {non_null_count}) sample: {df[c].dropna().head(1).tolist()}")
