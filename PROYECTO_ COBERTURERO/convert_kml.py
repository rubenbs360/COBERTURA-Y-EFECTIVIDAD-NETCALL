import zipfile
import json
import xml.etree.ElementTree as ET
import re

KMZ_PATH = r"C:\Users\USUARIO\Downloads\MAPA_ENTEL_LOGX.kmz"
GEOJSON_PATH = r"c:\Users\USUARIO\OneDrive\Escritorio\RUBEN DOC\NETCALL\data\cobertura.json"

def clean_coords(coord_str):
    coords = []
    # Coordinates are separated by spaces or newlines
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

import unicodedata

def clean_string(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s

def get_department(name, desc):
    full_text = clean_string(name + " " + desc)
    
    tumbes_keys = ["tumbes", "zarumilla", "zorritos", "corrales", "canoas", "trespicos", "pampa grande", "la cruz"]
    piura_keys = ["piura", "sullana", "paita", "talara", "morropon", "sechura", "ayabaca", "huancabamba", "marcavelica", "catacaos", "tambogrande", "castilla", "colan", "lobitos", "el alto", "mancora", "organos", "bellavista", "querecotillo", "salitral", "ignacio escudero", "lancones", "vice", "bernal", "rinconada", "sojo", "mallares", "jibito", "la golondrina", "amotan"]
    lambayeque_keys = ["lambayeque", "chiclayo", "ferrenafe", "olmos", "motupe", "illimo", "jayanca", "pacora", "tucume", "mochumi", "morrope", "pimentel", "reque", "monsefu", "chongoyape", "patapo", "pomalca", "tuman", "picsi", "jose leonardo ortiz", "la victoria", "cayalti", "zania", "sana", "eteten", "puerto eten"]
    libertad_keys = ["la libertad", "trujillo", "viru", "chao", "chepen", "pacasmayo", "otuzco", "sanchez carrion", "huamachuco", "santiago de chuco", "ascope", "gran chimu", "bolivar", "pataz", "julcan", "laredo", "moche", "huanchaco", "el porvenir", "florencia de mora", "la esperanza", "victor larco", "salaverry", "guadalupe", "santiago de cao", "paijan", "casa grande", "chicama", "chocope"]
    
    if any(k in full_text for k in tumbes_keys):
        return "Tumbes"
    if any(k in full_text for k in piura_keys):
        return "Piura"
    if any(k in full_text for k in lambayeque_keys):
        return "Lambayeque"
    if any(k in full_text for k in libertad_keys):
        return "La Libertad"
        
    return "Lima - Callao"

def convert_kml():
    print("Extracting doc.kml from KMZ...")
    with zipfile.ZipFile(KMZ_PATH) as z:
        kml_data = z.read("doc.kml")
        
    print("Parsing KML XML...")
    root = ET.fromstring(kml_data)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # Let's extract Styles first to get colors if possible
    styles = {}
    for style in root.findall('.//kml:Style', ns):
        sid = style.get('id')
        if sid:
            # Check for PolyStyle color
            poly_style = style.find('.//kml:PolyStyle', ns)
            if poly_style is not None:
                color_el = poly_style.find('kml:color', ns)
                if color_el is not None and color_el.text:
                    styles[sid] = color_el.text # KML color is aabbggrr in hex
                    
    # Also handle StyleMap
    style_maps = {}
    for sm in root.findall('.//kml:StyleMap', ns):
        sm_id = sm.get('id')
        if sm_id:
            # Find normal pair style url
            pairs = sm.findall('kml:Pair', ns)
            for pair in pairs:
                key = pair.find('kml:key', ns)
                if key is not None and key.text == 'normal':
                    url = pair.find('kml:styleUrl', ns)
                    if url is not None:
                        style_maps[sm_id] = url.text.strip('#')
                        
    features = []
    placemarks = root.findall('.//kml:Placemark', ns)
    print(f"Found {len(placemarks)} placemarks.")
    
    polygon_count = 0
    for p in placemarks:
        name_el = p.find('kml:name', ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else "Zona Sin Nombre"
        
        name_lower = name.lower()
        # Skip/delete specific polygons requested by the user
        if any(del_name in name_lower for del_name in ["zona no cubrible", "zona no accesible", "zona inaccesible", "polígono 51", "poligono 51", "lagunas", "la unión", "la union"]):
            continue
            
        desc_el = p.find('kml:description', ns)
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        
        # Check for Polygon
        polygon_el = p.find('.//kml:Polygon', ns)
        if polygon_el is not None:
            polygon_count += 1
            # Get outer coordinates
            outer_el = polygon_el.find('.//kml:outerBoundaryIs//kml:coordinates', ns)
            if outer_el is not None and outer_el.text:
                outer_coords = clean_coords(outer_el.text)
                if len(outer_coords) < 3:
                    continue
                
                # Check styleUrl to get color
                color_hex = "#00FFFF" # Default celeste
                style_url_el = p.find('kml:styleUrl', ns)
                if style_url_el is not None and style_url_el.text:
                    s_id = style_url_el.text.strip('#')
                    # Follow style map if needed
                    actual_style_id = style_maps.get(s_id, s_id)
                    kml_color = styles.get(actual_style_id)
                    if kml_color:
                        # Convert aabbggrr (KML hex) to rrggbb (standard hex)
                        # e.g. "ff0000ff" (blue in KML) -> "ff0000" or similar
                        if len(kml_color) == 8:
                            # aabbggrr -> #rrggbb
                            a, b, g, r = kml_color[0:2], kml_color[2:4], kml_color[4:6], kml_color[6:8]
                            color_hex = f"#{r}{g}{b}"
                            
                # Business values mapped by Style Color hex
                color_lower = color_hex.lower()
                
                # Check text flags first for safety
                text_says_no_coverage = any(k in name.lower() or k in desc.lower() for k in ["no accesible", "inaccessible", "no cubre", "no se cubre", "no coberturable", "fuera de cobertura", "no se cubra", "no se cubri", "no coberturada"])
                
                # Force red list requested by user
                is_forced_red = any(red_name in name_lower for red_name in ["c hao", "salaverry alto", "virú - fábricas", "viru - fabricas", "alto salaverry", "panamerica norte"])
                
                if color_lower in ["#ff5252", "#a52714"] or text_says_no_coverage or is_forced_red:
                    tipo_rango = "ROJO (Sin Acceso)"
                    horario_cobertura = "Sin Cobertura / Zona Insegura"
                    color_hex = "#ef4444"
                elif color_lower in ["#e65100", "#f57c00"]:
                    tipo_rango = "NARANJA (12h)"
                    horario_cobertura = "12 Horas (8:00 AM - 8:00 PM)"
                    color_hex = "#ffa500"
                elif "express" in desc.lower() or "express" in name.lower():
                    tipo_rango = "MAGENTA (Express)"
                    horario_cobertura = "Express (9:00 AM - 10:00 PM)"
                    color_hex = "#d946ef"
                else:
                    tipo_rango = "CELESTE"
                    horario_cobertura = "24 Horas"
                    color_hex = "#00d2ff" # Clean celeste
                
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
                
                # Check if there are inner boundaries (holes) and add them
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
    
    print(f"Successfully converted {len(features)} Polygons to GeoJSON.")
    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print("Saved conversion results.")

if __name__ == "__main__":
    convert_kml()
