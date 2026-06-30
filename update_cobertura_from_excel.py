import json
import pandas as pd
import re
import os

EXCEL_PATH = r"C:\Users\USUARIO\Downloads\Delivery_2026_Info_Distritos_Tipos_Horarios JUNIO.xlsx"
GEOJSON_PATH = r"data/cobertura.json"

# Manual overrides to preserve specific district settings requested by the user
MANUAL_OVERRIDES = {
    "CAJAMARQUILLA": {
        "color_default": "#ef4444",
        "tipo_rango": "ROJO (Sin Acceso)",
        "horario_cobertura": "Sin Cobertura / Zona Insegura",
        "description": "No se cubre zona"
    },
    "ALTO LAREDO": {
        "color_default": "#ef4444",
        "tipo_rango": "ROJO (Sin Acceso)",
        "horario_cobertura": "Sin Cobertura / Zona Insegura"
    },
    "FERREÑAFE": {
        "color_default": "#ef4444",
        "tipo_rango": "ROJO (Sin Acceso)",
        "horario_cobertura": "Sin Cobertura / Zona Insegura"
    },
    "MESONES MURO": {
        "color_default": "#ef4444",
        "tipo_rango": "ROJO (Sin Acceso)",
        "horario_cobertura": "Sin Cobertura / Zona Insegura"
    },
    "PICSI": {
        "color_default": "#ef4444",
        "tipo_rango": "ROJO (Sin Acceso)",
        "horario_cobertura": "Sin Cobertura / Zona Insegura"
    },
    "CURA MORI": {
        "color_default": "#ef4444",
        "tipo_rango": "ROJO (Sin Acceso)",
        "horario_cobertura": "Sin Cobertura / Zona Insegura"
    },
    "VIRU": {
        "color_default": "#3b82f6", # Celeste/Blue
        "tipo_rango": "CELESTE (Viru)"
    }
}

def normalize_text(text):
    if not text or pd.isna(text):
        return ""
    text = str(text).upper().strip()
    text = text.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    text = text.replace("Ñ", "N") # Normalize Ñ to N for easier matching if needed
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    return " ".join(text.split())

def process_merging():
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encontró el archivo Excel en {EXCEL_PATH}")
        return

    print(f"Leyendo Excel de Delivery desde: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name='DELIVERY 2026')
    
    # Parse excel rows into a dictionary map
    delivery_map = {}
    for _, row in df.iterrows():
        dist_raw = row.get('DISTRITO', '')
        if pd.isna(dist_raw):
            continue
        dist_norm = normalize_text(dist_raw)
        
        # Build active days string
        days = []
        if row.get('LUN') == 'SI': days.append('Lun')
        if row.get('MAR') == 'SI': days.append('Mar')
        if row.get('MIE') == 'SI': days.append('Mie')
        if row.get('JUE') == 'SI': days.append('Jue')
        if row.get('VIE') == 'SI': days.append('Vie')
        if row.get('SAB') == 'SI': days.append('Sab')
        if row.get('DOM') == 'SI': days.append('Dom')
        
        days_str = ", ".join(days) if days else "No especificado"
        
        express_active = str(row.get('EXPRESS', '')).strip().upper() == 'SI'
        prog_active = str(row.get('PROGRAMADO', '')).strip().upper() == 'SI'
        
        # Choose schedule text
        schedules = []
        if express_active:
            exp_range = row.get('RANGO_EXP', '9am - 6pm')
            exp_cut = row.get('CORTE_REGISTRO_OT_EXPRESS', '')
            exp_cut_str = f" (Corte: {exp_cut})" if pd.notna(exp_cut) and str(exp_cut).strip() != '' else ""
            schedules.append(f"Express: {exp_range}{exp_cut_str}")
        if prog_active:
            prog_range = row.get('RANGO_PROGRAMADO', '9am - 8pm')
            prog_cut = row.get('CORTE_REGISTRO_OT_PROGRAMADO', '')
            prog_cut_str = f" (Corte: {prog_cut})" if pd.notna(prog_cut) and str(prog_cut).strip() != '' else ""
            schedules.append(f"Regular: {prog_range}{prog_cut_str}")
            
        schedule_text = " / ".join(schedules) if schedules else "Sin cobertura regular registrada"
        
        # Determine rango and color
        if express_active:
            rango = "EXPRESS"
            color = "#2563eb" # Clean blue for Express
        elif prog_active:
            rango = "REGULAR"
            color = "#10b981" # Green for Regular
        else:
            rango = "ROJO (Sin Acceso)"
            color = "#ef4444"
            schedule_text = "Sin Cobertura / Zona Insegura"
            
        delivery_map[dist_norm] = {
            "distrito_orig": dist_raw,
            "tipo_rango": rango,
            "color_default": color,
            "horario_cobertura": schedule_text,
            "dias_entrega": days_str,
            "provincia": row.get('PROVINCIA', ''),
            "departamento": row.get('DEPARTAMENTO', '')
        }

    print(f"Cargando GeoJSON actual desde: {GEOJSON_PATH}")
    with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
        geojson = json.load(f)

    updated_count = 0
    overridden_count = 0
    
    for feat in geojson['features']:
        props = feat['properties']
        dist_name = props.get('distrito', '')
        name_com = props.get('nombre_comercial', '')
        
        dist_norm = normalize_text(dist_name)
        name_com_norm = normalize_text(name_com)
        
        # Check manual overrides first
        matched_override = None
        for key in MANUAL_OVERRIDES:
            norm_key = normalize_text(key)
            if norm_key == dist_norm or norm_key == name_com_norm:
                matched_override = MANUAL_OVERRIDES[key]
                break
                
        if matched_override:
            props.update(matched_override)
            overridden_count += 1
            continue
            
        # Try matching with Excel dictionary
        matched_data = None
        if dist_norm in delivery_map:
            matched_data = delivery_map[dist_norm]
        else:
            # Try substring matching
            for ex_key in delivery_map:
                if ex_key != "" and (ex_key in dist_norm or ex_key in name_com_norm):
                    matched_data = delivery_map[ex_key]
                    break
                    
        if matched_data:
            props['tipo_rango'] = matched_data['tipo_rango']
            props['color_default'] = matched_data['color_default']
            props['horario_cobertura'] = matched_data['horario_cobertura']
            
            # Update description to include delivery days
            props['description'] = f"Entregas: {matched_data['dias_entrega']}."
            updated_count += 1

    print(f"Proceso de fusión completado:")
    print(f" - Polígonos actualizados con información del Excel: {updated_count}")
    print(f" - Polígonos protegidos con reglas manuales/overrides: {overridden_count}")

    # Save the updated GeoJSON
    with open(GEOJSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"Guardado archivo cobertura.json actualizado con éxito!")

if __name__ == "__main__":
    process_merging()
