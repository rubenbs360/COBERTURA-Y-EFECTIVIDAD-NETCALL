import os
import glob
import pandas as pd

# Load latest CSV
csv_pattern = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - *.csv"
csv_files = glob.glob(csv_pattern)
if csv_files:
    CSV_PATH = max(csv_files, key=os.path.getmtime)
else:
    CSV_PATH = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - 2026-06-14T131227.720.csv"

print(f"Loading CSV from: {CSV_PATH}")
df = pd.read_csv(CSV_PATH, encoding='utf-8', encoding_errors='ignore')

# Check FRM_Distrito column unique values containing TALARA or PARIÑAS
dist_col = 'FRM_Distrito' if 'FRM_Distrito' in df.columns else 'FRM_Departamento_de_entrega'
print(f"Distrito column: {dist_col}")

matches_talara = df[df[dist_col].astype(str).str.contains('TALARA', case=False)]
matches_parinas = df[df[dist_col].astype(str).str.contains('PARI', case=False)]

print(f"Rows matching 'TALARA' in {dist_col}: {len(matches_talara)}")
if len(matches_talara) > 0:
    print(matches_talara[dist_col].value_counts())
    
print(f"Rows matching 'PARIÑAS/PARI' in {dist_col}: {len(matches_parinas)}")
if len(matches_parinas) > 0:
    print(matches_parinas[dist_col].value_counts())
