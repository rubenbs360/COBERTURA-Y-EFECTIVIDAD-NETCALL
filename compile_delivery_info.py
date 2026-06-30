import json
import pandas as pd
import re
import os

EXCEL_PATH = r"C:\Users\USUARIO\Downloads\Delivery_2026_Info_Distritos_Tipos_Horarios JUNIO.xlsx"
OUTPUT_PATH = r"data/delivery_info.json"

def normalize_text(text):
    if not text or pd.isna(text):
        return ""
    text = str(text).upper().strip()
    text = text.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    text = text.replace("Ñ", "N")
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    return " ".join(text.split())

def compile_data():
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: Excel file not found at {EXCEL_PATH}")
        return
        
    print(f"Compilando base de delivery desde: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name='DELIVERY 2026')
    
    delivery_map = {}
    for _, row in df.iterrows():
        dist_raw = row.get('DISTRITO', '')
        if pd.isna(dist_raw):
            continue
        dist_norm = normalize_text(dist_raw)
        
        # Build active days
        days = []
        if row.get('LUN') == 'SI': days.append('Lun')
        if row.get('MAR') == 'SI': days.append('Mar')
        if row.get('MIE') == 'SI': days.append('Mie')
        if row.get('JUE') == 'SI': days.append('Jue')
        if row.get('VIE') == 'SI': days.append('Vie')
        if row.get('SAB') == 'SI': days.append('Sab')
        if row.get('DOM') == 'SI': days.append('Dom')
        
        days_str = ", ".join(days) if days else "No registrado"
        
        express_active = str(row.get('EXPRESS', '')).strip().upper() == 'SI'
        prog_active = str(row.get('PROGRAMADO', '')).strip().upper() == 'SI'
        
        exp_range = str(row.get('RANGO_EXP', '')).strip()
        exp_cut = str(row.get('CORTE_REGISTRO_OT_EXPRESS', '')).strip()
        
        prog_range = str(row.get('RANGO_PROGRAMADO', '')).strip()
        prog_cut = str(row.get('CORTE_REGISTRO_OT_PROGRAMADO', '')).strip()
        
        # Clean placeholders
        if exp_range == 'nan' or exp_range == '-': exp_range = "No especificado"
        if exp_cut == 'nan' or exp_cut == '-': exp_cut = ""
        if prog_range == 'nan' or prog_range == '-': prog_range = "No especificado"
        if prog_cut == 'nan' or prog_cut == '-': prog_cut = ""
        
        # Determine Rango/Tipo and Color
        if express_active:
            rango = "CELESTE" # Celeste/Express
            color = "#00f2fe"
        elif prog_active:
            rango = "VERDE" # Verde/Regular
            color = "#10b981"
        else:
            rango = "ROJO" # Sin cobertura
            color = "#ef4444"
            
        delivery_map[dist_norm] = {
            "distrito": dist_raw,
            "provincia": str(row.get('PROVINCIA', '')).strip(),
            "departamento": str(row.get('DEPARTAMENTO', '')).strip(),
            "express": "SI" if express_active else "NO",
            "programado": "SI" if prog_active else "NO",
            "rango_exp": exp_range,
            "corte_exp": exp_cut,
            "rango_prog": prog_range,
            "corte_prog": prog_cut,
            "dias_entrega": days_str,
            "rango_tipo": rango,
            "color_rango": color
        }

        # Apply synonym duplication (e.g. Pariñas -> Talara, Chincha Alta -> Chincha)
        synonyms = {
            "PARINAS": "TALARA",
            "CHINCHA ALTA": "CHINCHA"
        }
        if dist_norm in synonyms:
            syn_to = synonyms[dist_norm]
            delivery_map[syn_to] = delivery_map[dist_norm]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(delivery_map, f, ensure_ascii=False, indent=2)
        
    print(f"Éxito: Se compilaron {len(delivery_map)} distritos en {OUTPUT_PATH}")

if __name__ == "__main__":
    compile_data()
