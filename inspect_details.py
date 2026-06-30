import json
import pandas as pd
import re

def normalize_text(text):
    if not text:
        return ""
    # Convert to uppercase
    text = str(text).upper()
    # Fix encoding problems
    text = text.replace("", "Ñ")
    # Replace common accents
    text = text.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    # Remove non-alphanumeric characters
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    return " ".join(text.split())

# Load Excel
file_path = r"C:\Users\USUARIO\Downloads\Delivery_2026_Info_Distritos_Tipos_Horarios JUNIO.xlsx"
df = pd.read_excel(file_path, sheet_name='DELIVERY 2026')

df['dist_norm'] = df['DISTRITO'].apply(normalize_text)
excel_norms = set(df['dist_norm'].tolist())

# Load GeoJSON
with open('data/cobertura.json', 'r', encoding='utf-8') as f:
    geojson = json.load(f)

matched_features = []
unmatched_excel = set(excel_norms)

for feat in geojson['features']:
    props = feat['properties']
    dist = normalize_text(props.get('distrito', ''))
    name_com = normalize_text(props.get('nombre_comercial', ''))
    
    # Try exact match first
    matched = False
    if dist in excel_norms:
        matched_features.append((props.get('id_zona'), props.get('nombre_comercial'), dist, dist))
        unmatched_excel.discard(dist)
        matched = True
    else:
        # Try substring match
        for ex_dist in excel_norms:
            if ex_dist in dist or ex_dist in name_com:
                matched_features.append((props.get('id_zona'), props.get('nombre_comercial'), props.get('distrito'), ex_dist))
                unmatched_excel.discard(ex_dist)
                matched = True
                break

print(f"Total GeoJSON features: {len(geojson['features'])}")
print(f"Total Excel unique districts: {len(excel_norms)}")
print(f"Matched GeoJSON features: {len(matched_features)}")
print(f"Excel districts not matched ({len(unmatched_excel)}):")
print(sorted(list(unmatched_excel))[:30])
