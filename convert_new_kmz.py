import zipfile
import json
import xml.etree.ElementTree as ET
import re
import os
import unicodedata

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

def convert_kmz():
    if not os.path.exists(KMZ_PATH):
        print(f"Error: No se encontró el archivo KMZ en: {KMZ_PATH}")
        return

    print(f"Abriendo archivo KMZ en: {KMZ_PATH}")
    with zipfile.ZipFile(KMZ_PATH) as z:
        kml_data = z.read("doc.kml")
        
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
    print(f"Se encontraron {len(placemarks)} marcadores/polígonos en el KML.")
    
    polygon_count = 0
    for p in placemarks:
        name_el = p.find('kml:name', ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else "Zona Sin Nombre"
        
        desc_el = p.find('kml:description', ns)
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        
        polygon_el = p.find('.//kml:Polygon', ns)
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
                            # Convert KML aabbggrr hex format to standard rrggbb hex
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
                
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    print(f"Conversión finalizada. Se procesaron {len(features)} polígonos.")
    os.makedirs(os.path.dirname(GEOJSON_PATH), exist_ok=True)
    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"Archivo guardado con éxito en: {GEOJSON_PATH}")

if __name__ == "__main__":
    convert_kmz()
