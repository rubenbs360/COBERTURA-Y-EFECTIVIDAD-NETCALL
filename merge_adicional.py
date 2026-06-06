import zipfile
import json
import xml.etree.ElementTree as ET
import re
import unicodedata

NEW_KMZ_PATH = r"C:\Users\USUARIO\Downloads\ADICIONAL LOGX.kmz"
GEOJSON_PATH = r"c:\Users\USUARIO\OneDrive\Escritorio\RUBEN DOC\NETCALL\data\cobertura.json"

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

def get_department_by_coords(lat, lng):
    if -15.5 <= lat <= -13.0 and -77.0 <= lng <= -74.0:
        return "Ica"
    if -13.5 <= lat <= -12.5 and -77.0 <= lng <= -76.0:
        return "Lima - Callao"
    if -6.0 <= lat <= -4.0 and -82.0 <= lng <= -80.0:
        return "Piura"
    if -8.0 <= lat <= -5.0 and -80.0 <= lng <= -78.0:
        return "Cajamarca"
    return "Otros"

def get_department(name, desc, first_coord=None):
    full_text = clean_string(name + " " + desc)
    
    # Skipped departments
    lima_keys = ["lima", "callao", "chorrillos", "miraflores", "ate", "surco", "smp", "comas", "carabayllo", "ventanilla", "lurin", "pachacamac", "san isidro", "canete", "imperial", "chancay", "huaral", "barranca"]
    piura_keys = ["piura", "sullana", "paita", "talara", "morpon", "morropon", "sechura", "catacaos", "tambogrande", "castilla", "lobitos", "mancora", "organos", "chulucanas", "chuyllache", "rivera rio"]
    lambayeque_keys = ["lambayeque", "chiclayo", "ferrenafe", "olmos", "motupe", "pimentel", "reque", "monsefu", "jose leonardo ortiz", "la victoria", "pomalca"]
    libertad_keys = ["la libertad", "trujillo", "viru", "chao", "chepen", "pacasmayo", "otuzco", "huamachuco", "santiago de chuco", "ascope", "laredo", "moche", "huanchaco", "el porvenir", "la esperanza", "salaverry", "guadalupe", "paijan", "casa grande", "chicama", "pesqueda", "dominguito", "wiesse", "paoli", "mampuesto", "moyano", "sanchez carrion"]
    tumbes_keys = ["tumbes", "zarumilla", "zorritos", "corrales"]
    arequipa_keys = ["arequipa", "cayma", "yanahuara", "selva alegre", "miraflores", "bustamante", "cerro colorado", "socabaya", "paucarpata", "aqp"]

    # Target departments
    tacna_keys = ["tacna", "pocollay", "calana", "ciudad nueva", "alto de la alianza", "gregorio albarraci"]
    puno_keys = ["puno", "juliaca", "san roman", "caracoto"]
    ucayali_keys = ["pucallpa", "ucayali", "coronel portillo", "manantay", "yarinacocha"]
    cusco_keys = ["cusco", "cuzco", "wanchaq", "san jeronimo", "santiago", "san sebastian", "poroy", "quillabamba", "la convencion"]
    ica_keys = ["ica", "chincha", "laran", "nasca", "pisco", "paracas", "grocio prado", "pueblo nuevo", "tambo de mora", "sunampe", "alameda", "pascana", "nazca"]
    huanuco_keys = ["huanuco", "amarilis", "pillco marca"]
    ayacucho_keys = ["ayacucho", "huamanga", "jesus nazareno", "san juan bautista", "carmen alto"]
    cajamarca_keys = ["cajamarca", "banos del inca", "chota", "cajabamba"]
    ancash_keys = ["ancash", "huaraz", "chimbote", "nuevo chimbote", "independencia"]
    moquegua_keys = ["moquegua", "ilo", "samegua"]
    loreto_keys = ["loreto", "iquitos", "punchana", "belen", "san juan bautista", "nauta", "yurimaguas"]
    junin_keys = ["junin", "huancayo", "el tambo", "chilca", "pilcomayo", "chanchamayo", "pichanaqui", "satipo", "mazamori", "tarma", "jauja"]
    apurimac_keys = ["apurimac", "abancay", "andahuaylas"]
    amazonas_keys = ["amazonas", "chachapoyas", "bagua", "uctubamba"]
    san_martin_keys = ["san martin", "tarapoto", "morales", "banda de shilcayo", "moyobamba", "rioja"]
    pasco_keys = ["pasco", "cerro de pasco"]
    huancavelica_keys = ["huancavelica"]
    madre_de_dios_keys = ["madre de dios", "puerto maldonado", "tambopata"]

    # 1. Check skipped departments first
    if any(k in full_text for k in lima_keys): return "Lima - Callao"
    if any(k in full_text for k in piura_keys): return "Piura"
    if any(k in full_text for k in lambayeque_keys): return "Lambayeque"
    if any(k in full_text for k in libertad_keys): return "La Libertad"
    if any(k in full_text for k in tumbes_keys): return "Tumbes"
    if any(k in full_text for k in arequipa_keys): return "Arequipa"

    # 2. Check target departments
    if any(k in full_text for k in tacna_keys): return "Tacna"
    if any(k in full_text for k in puno_keys): return "Puno"
    if any(k in full_text for k in ucayali_keys): return "Ucayali"
    if any(k in full_text for k in cusco_keys): return "Cusco"
    if any(k in full_text for k in ica_keys): return "Ica"
    if any(k in full_text for k in huanuco_keys): return "Huánuco"
    if any(k in full_text for k in ayacucho_keys): return "Ayacucho"
    if any(k in full_text for k in cajamarca_keys): return "Cajamarca"
    if any(k in full_text for k in ancash_keys): return "Ancash"
    if any(k in full_text for k in moquegua_keys): return "Moquegua"
    if any(k in full_text for k in loreto_keys): return "Loreto"
    if any(k in full_text for k in junin_keys): return "Junín"
    if any(k in full_text for k in apurimac_keys): return "Apurímac"
    if any(k in full_text for k in amazonas_keys): return "Amazonas"
    if any(k in full_text for k in san_martin_keys): return "San Martín"
    if any(k in full_text for k in pasco_keys): return "Pasco"
    if any(k in full_text for k in huancavelica_keys): return "Huancavelica"
    if any(k in full_text for k in madre_de_dios_keys): return "Madre de Dios"

    # 3. Fallback to coordinate bounding boxes if available
    if first_coord:
        try:
            lng, lat = first_coord[0], first_coord[1]
            coord_dept = get_department_by_coords(lat, lng)
            if coord_dept != "Otros":
                return coord_dept
        except Exception:
            pass

    return "Otros"

def merge_adicional():
    print("Loading existing cobertura.json...")
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    
    # Store existing features and find max id_zona to continue sequence
    existing_features = geojson.get("features", [])
    max_id = 0
    for feat in existing_features:
        id_str = feat["properties"].get("id_zona", "")
        m = re.match(r"ZONA_(\d+)", id_str)
        if m:
            max_id = max(max_id, int(m.group(1)))
    
    print(f"Loaded {len(existing_features)} existing features. Next ID number: {max_id + 1}")
    
    # Keep track of existing departments (skipped list)
    skipped_departments = ["Lima - Callao", "Lambayeque", "La Libertad", "Piura", "Tumbes", "Arequipa"]
    
    print("Extracting doc.kml from new KMZ...")
    with zipfile.ZipFile(NEW_KMZ_PATH) as z:
        kml_data = z.read("doc.kml")
        
    print("Parsing KML XML...")
    root = ET.fromstring(kml_data)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # Extract KML Styles and StyleMaps
    styles = {}
    for style in root.findall('.//kml:Style', ns):
        sid = style.get('id')
        if sid:
            poly_style = style.find('.//kml:PolyStyle', ns)
            if poly_style is not None:
                color_el = poly_style.find('kml:color', ns)
                if color_el is not None and color_el.text:
                    styles[sid] = color_el.text
                    
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
                        
    placemarks = root.findall('.//kml:Placemark', ns)
    print(f"Found {len(placemarks)} placemarks in the new KMZ.")
    
    new_features_added = 0
    skipped_by_department = 0
    unclassified_skipped = 0
    
    for p in placemarks:
        name_el = p.find('kml:name', ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else "Zona Sin Nombre"
        
        name_lower = name.lower()
        if any(del_name in name_lower for del_name in ["zona no cubrible", "zona no accesible", "zona inaccesible", "polígono 51", "poligono 51", "lagunas", "la unión", "la union"]):
            continue
            
        desc_el = p.find('kml:description', ns)
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        
        polygon_el = p.find('.//kml:Polygon', ns)
        if polygon_el is not None:
            outer_el = polygon_el.find('.//kml:outerBoundaryIs//kml:coordinates', ns)
            if outer_el is not None and outer_el.text:
                outer_coords = clean_coords(outer_el.text)
                if len(outer_coords) < 3:
                    continue
                
                # 1. Elimination Check
                name_clean = clean_string(name)
                to_delete = [
                    "mapa completo", "pasco 1", "pasco 3", "tarma", "jauja", "huancavelica",
                    "jaen", "rioja", "nauta", "yurimaguas", "pasco 2", "zona peligrosa iquitos 1"
                ]
                if any(del_kw in name_clean for del_kw in to_delete):
                    continue
                
                # 2. Rename Check
                nombre_comercial = name
                if "zona de coberturada iquitos" in name_clean:
                    nombre_comercial = "IQUITOS"
                    name = "IQUITOS"

                # Determine department
                dept = get_department(name, desc, outer_coords[0] if outer_coords else None)
                
                # Skip if it's an existing department or Unclassified
                if dept in skipped_departments:
                    skipped_by_department += 1
                    continue
                if dept == "Otros":
                    unclassified_skipped += 1
                    continue
                
                # Determine style colors
                color_hex = "#00d2ff" # Default celeste
                style_url_el = p.find('kml:styleUrl', ns)
                if style_url_el is not None and style_url_el.text:
                    s_id = style_url_el.text.strip('#')
                    actual_style_id = style_maps.get(s_id, s_id)
                    kml_color = styles.get(actual_style_id)
                    if kml_color and len(kml_color) == 8:
                        a, b, g, r = kml_color[0:2], kml_color[2:4], kml_color[4:6], kml_color[6:8]
                        color_hex = f"#{r}{g}{b}"
                
                color_lower = color_hex.lower()
                text_says_no_coverage = any(k in name.lower() or k in desc.lower() for k in ["no accesible", "inaccessible", "no cubre", "no se cubre", "no coberturable", "fuera de cobertura", "no se cubra", "no se cubri", "no coberturada", "peligrosa", "zona peligrosa", "sin cobertura"])
                
                # Map KML colors or names to delivery levels
                # Black styles (#000000) correspond to ROJO (Sin Acceso) in this KML file.
                if color_lower in ["#ff5252", "#a52714", "#000000"] or text_says_no_coverage:
                    tipo_rango = "ROJO (Sin Acceso)"
                    horario_cobertura = "Sin Cobertura / Zona Insegura"
                    color_hex = "#ef4444"
                elif color_lower in ["#e65100", "#f57c00", "#f9a825"]:
                    tipo_rango = "NARANJA (12h)"
                    horario_cobertura = "12 Horas (8:00 AM - 8:00 PM)"
                    color_hex = "#ffa500"
                else:
                    tipo_rango = "CELESTE"
                    horario_cobertura = "24 Horas"
                    color_hex = "#00d2ff"

                # 3. No Color (Transparent Fill) Check
                no_color_kws = [
                    "san martin zonas a visitar", "abancay", "andahuaylas", "limite de ica",
                    "ica limite de subtanjalla", "ica limite de tinguina", "ica limite de parcona",
                    "moyobamba", "huanuco limite", "huanuco limite de amarilis", "huanuco limite pillco marca",
                    "iquitos", "pisco", "moquegua zona entregable", "zona entregable juliaca",
                    "tacna limite de tacna", "tacna limite de gregorio albarraci", "tacna limite de pocollay",
                    "tacna limite de ciudad nueva", "tacna limite de alto de la alianza", "zona chincha"
                ]
                no_color_flag = False
                if any(nc_kw in name_clean for nc_kw in no_color_kws):
                    no_color_flag = True
                
                max_id += 1
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id_zona": f"ZONA_{max_id:04d}",
                        "departamento": dept,
                        "provincia": "",
                        "distrito": name,
                        "nombre_comercial": nombre_comercial,
                        "color_default": color_hex,
                        "tipo_rango": tipo_rango,
                        "horario_cobertura": horario_cobertura,
                        "description": desc,
                        "no_color": no_color_flag
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [outer_coords]
                    }
                }
                
                # Add inner boundaries (holes)
                inner_els = polygon_el.findall('.//kml:innerBoundaryIs//kml:coordinates', ns)
                for inner_el in inner_els:
                    if inner_el.text:
                        inner_coords = clean_coords(inner_el.text)
                        if len(inner_coords) >= 3:
                            feature["geometry"]["coordinates"].append(inner_coords)
                            
                existing_features.append(feature)
                new_features_added += 1
                
    geojson["features"] = existing_features
    print(f"Skipped by department check: {skipped_by_department}")
    print(f"Skipped unclassified/other: {unclassified_skipped}")
    print(f"Successfully added {new_features_added} new polygons.")
    print(f"Total polygons in database now: {len(existing_features)}")
    
    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print("Combined GeoJSON saved successfully!")

if __name__ == "__main__":
    merge_adicional()
