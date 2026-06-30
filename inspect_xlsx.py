import pandas as pd

file_path = r"C:\Users\USUARIO\Downloads\Delivery_2026_Info_Distritos_Tipos_Horarios JUNIO.xlsx"
xl = pd.ExcelFile(file_path)
print("Sheet Names:", xl.sheet_names)

for sheet in xl.sheet_names:
    print(f"\n--- Sheet: {sheet} ---")
    df = pd.read_excel(file_path, sheet_name=sheet)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head(5))
