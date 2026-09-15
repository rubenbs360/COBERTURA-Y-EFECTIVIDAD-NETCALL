import zipfile
import json
import xml.etree.ElementTree as ET
import re
import os
import glob
import unicodedata
import pandas as pd

KMZ_PATH = r"C:\Users\USUARIO\Downloads\NUEVO COBERTURERO LOGIXTAL - ENTEL.kmz"
GEOJSON_PATH = r"data/cobertura.json"

def clean_coords(coord_str):
    coords = []
    for token in coord_str.strip().split():
        parts = token.split(',')
        if len(parts) >= 2:
            try:
                lng = float(parts[0])
                lat = float(parts[1])
                coords.append([lng, lat])
            except ValueError:
                continue
    return coords

def clean_string(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s

def get_department(name, desc):
    full_text = clean_string(name + " " + desc)
    tumbes_keys = ["tumbes", "zarumilla", "zorritos", "corrales", "canoas", "trespicos", "la cruz"]
    piura_keys = ["piura", "sullana", "paita", "talara", "morropon", "sechura", "ayabaca", "huancabamba", "catacaos", "tambogrande", "castilla", "lobitos", "mancora", "organos", "bellavista"]
    lambayeque_keys = ["lambayeque", "chiclayo", "ferrenafe", "olmos", "motupe", "pimentel", "reque", "monsefu", "picsi", "jose leonardo ortiz", "la victoria"]
    libertad_keys = ["la libertad", "trujillo", "viru", "chao", "chepen", "pacasmayo", "laredo", "moche", "huanchaco", "el porvenir", "la esperanza", "victor larco", "salaverry"]
    
    if any(k in full_text for k in tumbes_keys): return "Tumbes"
    if any(k in full_text for k in piura_keys): return "Piura"
    if any(k in full_text for k in lambayeque_keys): return "Lambayeque"
    if any(k in full_text for k in libertad_keys): return "La Libertad"
    return "Lima - Callao"

def find_kmz_path():
    possible_dirs = [
        r"C:\Users\USUARIO\Downloads",
        r"REPORTERIA_PROYECTO_COBERTURERO",
        "."
    ]
    kmz_files = []
    for d in possible_dirs:
        if os.path.exists(d):
            kmz_files.extend(glob.glob(os.path.join(d, "*.kmz")))
            kmz_files.extend(glob.glob(os.path.join(d, "*.kml")))
    if kmz_files:
        return max(kmz_files, key=os.path.getmtime)
    return None

def convert_kmz():
    target_path = find_kmz_path()
    if not target_path:
        print(f"Error: No se encontró ningún archivo KMZ o KML en Downloads o REPORTERIA_PROYECTO_COBERTURERO.")
        return

    print(f"Abriendo archivo de mapa en: {target_path}")
    kml_data = None
    if target_path.lower().endswith(".kmz"):
        with zipfile.ZipFile(target_path) as z:
            # Find the main kml file inside zip
            kml_filename = [name for name in z.namelist() if name.endswith('.kml')][0]
            kml_data = z.read(kml_filename)
    else:
        with open(target_path, "rb") as f:
            kml_data = f.read()
        
    print("Analizando KML...")
    root = ET.fromstring(kml_data)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # Extract Styles
    styles = {}
    for style in root.findall('.//kml:Style', ns):
        sid = style.get('id')
        if sid:
            poly_style = style.find('.//kml:PolyStyle', ns)
            if poly_style is not None:
                color_el = poly_style.find('kml:color', ns)
                if color_el is not None and color_el.text:
                    styles[sid] = color_el.text
                    
    # Extract StyleMaps
    style_maps = {}
    for sm in root.findall('.//kml:StyleMap', ns):
        sm_id = sm.get('id')
        if sm_id:
            pairs = sm.findall('kml:Pair', ns)
            for pair in pairs:
                key = pair.find('kml:key', ns)
                if key is not None and key.text == 'normal':
                    url = pair.find('kml:styleUrl', ns)
                    if url is not None:
                        style_maps[sm_id] = url.text.strip('#')
                        
    features = []
    placemarks = root.findall('.//kml:Placemark', ns)
    print(f"Se encontraron {len(placemarks)} elementos (polígonos/puntos) en el KML.")
    
    polygon_count = 0
    point_count = 0
    for p in placemarks:
        name_el = p.find('kml:name', ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else "Zona Sin Nombre"
        
        desc_el = p.find('kml:description', ns)
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        
        polygon_el = p.find('.//kml:Polygon', ns)
        point_el = p.find('.//kml:Point', ns)
        
        if polygon_el is not None:
            polygon_count += 1
            outer_el = polygon_el.find('.//kml:outerBoundaryIs//kml:coordinates', ns)
            if outer_el is not None and outer_el.text:
                outer_coords = clean_coords(outer_el.text)
                if len(outer_coords) < 3:
                    continue
                
                # Default color is Celeste if no style is resolved
                color_hex = "#00d2ff"
                style_url_el = p.find('kml:styleUrl', ns)
                if style_url_el is not None and style_url_el.text:
                    s_id = style_url_el.text.strip('#')
                    actual_style_id = style_maps.get(s_id, s_id)
                    kml_color = styles.get(actual_style_id)
                    if kml_color:
                        if len(kml_color) == 8:
                            a, b, g, r = kml_color[0:2], kml_color[2:4], kml_color[4:6], kml_color[6:8]
                            color_hex = f"#{r}{g}{b}"
                
                # Assign range type and schedule based on KML style colors
                color_lower = color_hex.lower()
                if color_lower in ["#000000", "#ff5252", "#a52714", "#757575"]:
                    tipo_rango = "ROJO (Sin Acceso)"
                    horario_cobertura = "Sin Cobertura / Zona Insegura"
                elif color_lower in ["#f57c00", "#e65100"]:
                    tipo_rango = "NARANJA (Regular)"
                    horario_cobertura = "Rango Regular (Hasta ciertas horas)"
                elif color_lower in ["#0288d1"]:
                    tipo_rango = "CELESTE (Rango Parcial)"
                    horario_cobertura = "Rango Parcial (Solo ciertos días) 24h+"
                else:
                    tipo_rango = "Cobertura KML"
                    horario_cobertura = "Verificar en buscador"
                
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id_zona": f"ZONA_{polygon_count:04d}",
                        "departamento": get_department(name, desc),
                        "provincia": "",
                        "distrito": name,
                        "nombre_comercial": name,
                        "color_default": color_hex,
                        "tipo_rango": tipo_rango,
                        "horario_cobertura": horario_cobertura,
                        "description": desc
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [outer_coords]
                    }
                }
                
                # Check for holes (inner boundaries)
                inner_els = polygon_el.findall('.//kml:innerBoundaryIs//kml:coordinates', ns)
                for inner_el in inner_els:
                    if inner_el.text:
                        inner_coords = clean_coords(inner_el.text)
                        if len(inner_coords) >= 3:
                            feature["geometry"]["coordinates"].append(inner_coords)
                            
                features.append(feature)

        elif point_el is not None:
            point_count += 1
            coords_el = point_el.find('kml:coordinates', ns)
            if coords_el is not None and coords_el.text:
                pt_coords = clean_coords(coords_el.text)
                if pt_coords:
                    lng, lat = pt_coords[0]
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "id_zona": f"PUNTO_{point_count:04d}",
                            "is_punto_encuentro": True,
                            "departamento": get_department(name, desc),
                            "distrito": name,
                            "nombre_comercial": f"📍 Punto de Encuentro: {name}",
                            "color_default": "#0288d1",
                            "tipo_rango": "PUNTO DE ENCUENTRO",
                            "horario_cobertura": "Punto de Encuentro Aprobado",
                            "description": desc
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lng, lat]
                        }
                    }
                    features.append(feature)
                
    # Enrich Puntos de Encuentro with OT Addresses from Excel if present
    pe_files = glob.glob('REPORTERIA_PROYECTO_COBERTURERO/Puntos*.xlsx')
    pe_excel_path = max(pe_files, key=os.path.getmtime) if pe_files else None
    if pe_excel_path and os.path.exists(pe_excel_path):
        try:
            print(f"Cargando direcciones OT desde: {pe_excel_path}...")
            xl = pd.ExcelFile(pe_excel_path)
            all_excel_pes = []
            for sheet in xl.sheet_names:
                df_raw = xl.parse(sheet)
                header_idx = 0
                for idx, row in df_raw.iterrows():
                    row_vals = [str(v).upper() for v in row.values]
                    if any('DIRECCION' in v for v in row_vals) or any('PE' in v for v in row_vals):
                        header_idx = idx
                        break
                df = xl.parse(sheet, skiprows=header_idx + 1)
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                pe_col = [c for c in df.columns if 'PE' in c or 'PUNTO' in c]
                dir_col = [c for c in df.columns if 'DIR' in c]
                dist_col = [c for c in df.columns if 'DIST' in c]
                ref_col = [c for c in df.columns if 'REF' in c]
                
                pe_name = pe_col[0] if pe_col else df.columns[1] if len(df.columns) > 1 else df.columns[0]
                dir_name = dir_col[0] if dir_col else df.columns[2] if len(df.columns) > 2 else df.columns[0]
                dist_name = dist_col[0] if dist_col else df.columns[0]
                ref_name = ref_col[0] if ref_col else (df.columns[3] if len(df.columns) > 3 else None)
                
                curr_dist = ""
                for _, row in df.iterrows():
                    dist_val = str(row.get(dist_name, '')).strip()
                    if dist_val and dist_val.upper() not in ['NAN', 'UNNAMED: 0', '0', 'DISTRITO', 'ZONAS P.E']:
                        curr_dist = dist_val
                        
                    pe_val = str(row.get(pe_name, '')).strip()
                    dir_val = str(row.get(dir_name, '')).strip()
                    ref_val = str(row.get(ref_name, '')).strip() if ref_name else ""
                    
                    if pe_val and pe_val.upper() not in ['NAN', 'PE', '0', 'NONE', 'PUNTO DE ENCUENTRO']:
                        if dir_val and dir_val.upper() not in ['NAN', '0', 'DIRECCION', 'NONE']:
                            all_excel_pes.append({
                                "sheet": sheet,
                                "distrito": curr_dist,
                                "pe_nombre": pe_val,
                                "direccion": dir_val,
                                "referencia": ref_val if ref_val.upper() not in ['NAN', '0', 'NONE', 'REFERENCIA', 'UNNAMED: 4', 'UNNAMED: 5'] else ""
                            })
                            
            def clean_txt(s):
                if not s: return ""
                s = str(s).upper()
                s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                s = re.sub(r'\b(P\.?E\.?|PUNTO DE ENCUENTRO|PARADERO|ESTACION)\b', '', s)
                s = re.sub(r'[^A-Z0-9]', '', s)
                return s.strip()

            map_puntos_indices = [idx for idx, feat in enumerate(features) if feat.get('properties', {}).get('is_punto_encuentro') or feat.get('geometry', {}).get('type') == 'Point']
            matched_count = 0
            
            for idx_m in map_puntos_indices:
                feat = features[idx_m]
                m_name = feat['properties'].get('distrito', '') or feat['properties'].get('nombre_comercial', '')
                m_clean = clean_txt(m_name)
                
                best_match = None
                for idx_e, e_item in enumerate(all_excel_pes):
                    e_clean = clean_txt(e_item['pe_nombre'])
                    if e_clean and e_clean == m_clean:
                        best_match = e_item
                        break
                if not best_match:
                    for idx_e, e_item in enumerate(all_excel_pes):
                        e_clean = clean_txt(e_item['pe_nombre'])
                        if e_clean and len(e_clean) > 3 and (e_clean in m_clean or m_clean in e_clean):
                            best_match = e_item
                            break
                            
                if best_match:
                    matched_count += 1
                    feat['properties']['direccion_ot'] = best_match['direccion']
                    feat['properties']['referencia_ot'] = best_match['referencia']
                    feat['properties']['distrito_ot'] = best_match['distrito']
            print(f"Éxito: {matched_count} Puntos de Encuentro enriquecidos con Dirección y Referencia OT.")
        except Exception as ex:
            print(f"Error procesando Puntos de Encuentro Excel: {ex}")

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    print(f"Conversión finalizada. Se procesaron {polygon_count} polígonos y {point_count} Puntos de Encuentro.")
    os.makedirs(os.path.dirname(GEOJSON_PATH), exist_ok=True)
    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"Archivo guardado con éxito en: {GEOJSON_PATH}")

if __name__ == "__main__":
    convert_kmz()
