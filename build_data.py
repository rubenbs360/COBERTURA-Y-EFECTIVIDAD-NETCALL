import os
import json
import pandas as pd
import numpy as np
import glob

# Paths
csv_pattern = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - *.csv"
csv_files = glob.glob(csv_pattern)
if csv_files:
    CSV_PATH = max(csv_files, key=os.path.getmtime)
else:
    CSV_PATH = r"C:\Users\USUARIO\Downloads\Dashboard Outbound Netcall- Entel V3_Post - Válidas_Tabla - 2026-06-14T131227.720.csv"

XLSX_PATH = r"C:\Users\USUARIO\Downloads\DIRECTORIO TIENDAS JUNIO.xlsx"

OUTPUT_DIRS = [
    r"c:\Users\USUARIO\OneDrive\Escritorio\RUBEN DOC\NETCALL\data"
]

for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

def clean_time(val):
    if pd.isna(val):
        return ""
    if isinstance(val, str):
        return val.strip()
    return val.strftime("%H:%M") if hasattr(val, 'strftime') else str(val)

def process_data():
    print(f"Loading CSV Outbound Netcall from: {CSV_PATH}")
    # Read the large CSV file
    df_csv = pd.read_csv(CSV_PATH, encoding='utf-8', encoding_errors='ignore')
    
    print(f"Loading Excel Store Directory from: {XLSX_PATH}")
    xl = pd.ExcelFile(XLSX_PATH)
    
    # 1. Process Advisors (Lima + Prov)
    print("Processing Advisors...")
    adv_lima_sheet = "Padrón Asesores LIMA" if "Padrón Asesores LIMA" in xl.sheet_names else "ASESORES LIMA"
    adv_prov_sheet = "Padrón Asesores Prov" if "Padrón Asesores Prov" in xl.sheet_names else "ASESORES PROV"
    
    df_adv_lima = xl.parse(adv_lima_sheet)
    df_adv_prov = xl.parse(adv_prov_sheet)
    df_adv = pd.concat([df_adv_lima, df_adv_prov], ignore_index=True)
    
    # Standardize types
    df_adv['ID_PDV'] = pd.to_numeric(df_adv['ID_PDV'], errors='coerce')
    df_adv = df_adv.dropna(subset=['ID_PDV'])
    df_adv['ID_PDV'] = df_adv['ID_PDV'].astype(int)
    
    # Clean email and phone
    df_adv['CORREO'] = df_adv['CORREO'].fillna("").astype(str).str.strip()
    df_adv['CELULAR'] = df_adv['CELULAR'].fillna("").astype(str).str.strip()
    df_adv['NOMBRES_APELLIDOS'] = df_adv['NOMBRES_APELLIDOS'].fillna("").astype(str).str.strip()
    df_adv['PUESTO'] = df_adv['PUESTO'].fillna("ASESOR").astype(str).str.strip()
    df_adv['ESTADO'] = df_adv['ESTADO'].fillna("").astype(str).str.upper().str.strip()
    df_adv['USUARIO_PORTAL'] = df_adv['USUARIO_PORTAL'].fillna("").astype(str).str.strip()
    
    # Group advisors by store (active only)
    advisors_by_store = {}
    active_advs = df_adv[~df_adv['ESTADO'].str.contains('INACTIVO|BAJA|CESE', na=False, case=False)]
    
    for _, row in active_advs.iterrows():
        store_id = int(row['ID_PDV'])
        adv_info = {
            "nombre": row['NOMBRES_APELLIDOS'],
            "puesto": row['PUESTO'],
            "celular": row['CELULAR'],
            "correo": row['CORREO'],
            "usuario": row['USUARIO_PORTAL']
        }
        if store_id not in advisors_by_store:
            advisors_by_store[store_id] = []
        advisors_by_store[store_id].append(adv_info)

    # 2. Process Stores (Directorio LIMA + Directorio Provincia)
    print("Processing Stores...")
    dir_lima_sheet = "Directorio LIMA " if "Directorio LIMA " in xl.sheet_names else "LIMA SUP"
    dir_prov_sheet = "Directorio Provincia" if "Directorio Provincia" in xl.sheet_names else "PROV SUP"
    
    df_sup_lima = xl.parse(dir_lima_sheet)
    df_sup_prov = xl.parse(dir_prov_sheet)
    
    # Standardize column names
    df_sup_lima = df_sup_lima.rename(columns={'# PDV': 'ID_PDV', 'NOMBRE PDV': 'PDV', 'DEPARTAMENTO2': 'DEPARTAMENTO_2'})
    df_sup_prov = df_sup_prov.rename(columns={'# PDV': 'ID_PDV', 'NOMBRE PDV': 'PDV', 'DEPARTAMENTO.1': 'DEPARTAMENTO_2'})
    
    df_sup = pd.concat([df_sup_lima, df_sup_prov], ignore_index=True)
    df_sup['ID_PDV'] = pd.to_numeric(df_sup['ID_PDV'], errors='coerce')
    df_sup = df_sup.dropna(subset=['ID_PDV'])
    df_sup['ID_PDV'] = df_sup['ID_PDV'].astype(int)
    
    # 3. Calculate CSV metrics
    print("Calculating effectiveness metrics...")
    total_orders = len(df_csv)
    estado_counts = df_csv['Estado_T'].value_counts().to_dict()
    
    # Calculate global indicators
    delivered = estado_counts.get('Entregado', 0)
    anulado = estado_counts.get('Anulado', 0)
    cancelado = estado_counts.get('Cancelado', 0)
    pendiente = estado_counts.get('Pendiente Entrega', 0)
    no_bop = estado_counts.get('No bop', 0)
    
    denom = delivered + anulado + cancelado
    global_effectiveness = (delivered / denom * 100) if denom > 0 else 0.0
    
    summary_data = {
        "total_orders": total_orders,
        "delivered": delivered,
        "anulado": anulado,
        "cancelado": cancelado,
        "pendiente": pendiente,
        "no_bop": no_bop,
        "effectiveness": round(global_effectiveness, 2),
        "dispatch_types": df_csv['Tipo_Despacho_Detalle'].value_counts().to_dict(),
        "negocios": df_csv['Tipo_de_Negocio'].value_counts().to_dict(),
    }
    
    # District / Department effectiveness (group by FRM_Distrito if present)
    dept_stats = []
    group_col = 'FRM_Distrito' if 'FRM_Distrito' in df_csv.columns else 'FRM_Departamento_de_entrega'
    print(f"Grouping CSV metrics by column: {group_col}")
    df_csv[group_col] = df_csv[group_col].fillna("No especificado")
    
    for key, group in df_csv.groupby(group_col):
        d_total = len(group)
        d_counts = group['Estado_T'].value_counts().to_dict()
        d_delivered = d_counts.get('Entregado', 0)
        d_anulado = d_counts.get('Anulado', 0)
        d_cancelado = d_counts.get('Cancelado', 0)
        d_denom = d_delivered + d_anulado + d_cancelado
        d_eff = (d_delivered / d_denom * 100) if d_denom > 0 else 0.0
        
        # Dispatch breakdown
        dispatch_breakdown = {}
        for dtype, dgroup in group.groupby('Tipo_Despacho_Detalle'):
            dt_counts = dgroup['Estado_T'].value_counts().to_dict()
            dt_delivered = dt_counts.get('Entregado', 0)
            dt_anulado = dt_counts.get('Anulado', 0)
            dt_cancelado = dt_counts.get('Cancelado', 0)
            dispatch_breakdown[str(dtype)] = {
                "total": len(dgroup),
                "delivered": dt_delivered,
                "anulado": dt_anulado,
                "cancelado": dt_cancelado
            }
        
        dept_stats.append({
            "departamento": str(key),  # Keeping key name "departamento" for frontend compatibility
            "total": d_total,
            "delivered": d_delivered,
            "anulado": d_anulado,
            "cancelado": d_cancelado,
            "pendiente": d_counts.get('Pendiente Entrega', 0),
            "effectiveness": round(d_eff, 2),
            "dispatch": dispatch_breakdown
        })
    
    # Store effectiveness (EOC_DELIVERYSTOREID)
    store_eff_dict = {}
    df_csv['EOC_DELIVERYSTOREID'] = pd.to_numeric(df_csv['EOC_DELIVERYSTOREID'], errors='coerce')
    csv_stores = df_csv.dropna(subset=['EOC_DELIVERYSTOREID'])
    csv_stores['EOC_DELIVERYSTOREID'] = csv_stores['EOC_DELIVERYSTOREID'].astype(int)
    
    for store_id, group in csv_stores.groupby('EOC_DELIVERYSTOREID'):
        s_total = len(group)
        s_counts = group['Estado_T'].value_counts().to_dict()
        s_delivered = s_counts.get('Entregado', 0)
        s_anulado = s_counts.get('Anulado', 0)
        s_cancelado = s_counts.get('Cancelado', 0)
        s_denom = s_delivered + s_anulado + s_cancelado
        s_eff = (s_delivered / s_denom * 100) if s_denom > 0 else 0.0
        
        store_eff_dict[int(store_id)] = {
            "total": s_total,
            "delivered": s_delivered,
            "anulado": s_anulado,
            "cancelado": s_cancelado,
            "effectiveness": round(s_eff, 2)
        }
        
    # Advisor effectiveness
    advisor_stats = []
    df_csv['FRM_N_DNI_Asesor'] = df_csv['FRM_N_DNI_Asesor'].fillna("No especificado")
    for adv, group in df_csv.groupby('FRM_N_DNI_Asesor'):
        a_total = len(group)
        a_counts = group['Estado_T'].value_counts().to_dict()
        a_delivered = a_counts.get('Entregado', 0)
        a_anulado = a_counts.get('Anulado', 0)
        a_cancelado = a_counts.get('Cancelado', 0)
        a_denom = a_delivered + a_anulado + a_cancelado
        a_eff = (a_delivered / a_denom * 100) if a_denom > 0 else 0.0
        
        advisor_stats.append({
            "usuario": str(adv),
            "total": a_total,
            "delivered": a_delivered,
            "anulado": a_anulado,
            "cancelado": a_cancelado,
            "effectiveness": round(a_eff, 2)
        })

    # 4. Consolidate Stores
    consolidated_stores = []
    for _, row in df_sup.iterrows():
        sid = int(row['ID_PDV'])
        
        # Look up effectiveness
        eff_info = store_eff_dict.get(sid, {
            "total": 0,
            "delivered": 0,
            "anulado": 0,
            "cancelado": 0,
            "effectiveness": None
        })
        
        # Clean address, coordinates, hours
        lat = row.get('LATITUD', None)
        lng = row.get('LONGITUD', None)
        
        # Convert lat/lng to float if possible
        try:
            lat = float(lat) if pd.notna(lat) and str(lat).strip() not in ['', '-'] else None
        except ValueError:
            lat = None
            
        try:
            lng = float(lng) if pd.notna(lng) and str(lng).strip() not in ['', '-'] else None
        except ValueError:
            lng = None
            
        # Timings
        h_entry_lv = clean_time(row.get('Horario Entrada (L-V)', ''))
        h_exit_lv = clean_time(row.get('Horario Salida (L-V)', ''))
        h_entry_s = clean_time(row.get('Horario Entrada (S)', ''))
        h_exit_s = clean_time(row.get('Horario Salida (S)', ''))
        h_entry_d = clean_time(row.get('Horario Entrada (D)', ''))
        h_exit_d = clean_time(row.get('Horario Salida (D)', ''))
        
        hours_lv = f"{h_entry_lv} - {h_exit_lv}" if h_entry_lv and h_exit_lv else "No registrado"
        hours_s = f"{h_entry_s} - {h_exit_s}" if h_entry_s and h_exit_s else "No registrado"
        hours_d = f"{h_entry_d} - {h_exit_d}" if h_entry_d and h_exit_d else "Cerrado"

        # Supervisor and KAM
        sup_name = row.get('JEFE DE CLUSTER', '')
        if pd.isna(sup_name) or str(sup_name).strip() in ['', '-']:
            sup_name = row.get('GNT', '')
        sup_name = str(sup_name).strip() if pd.notna(sup_name) else "No especificado"
        
        sup_cel = str(row.get('CELULAR JEFE DE CLUSTER', '')).strip()
        sup_cel = sup_cel.replace(".0", "") if ".0" in sup_cel else sup_cel
        if sup_cel in ['', '-', 'nan']:
            sup_cel = "No especificado"
            
        sup_email = str(row.get('CORREO JEFE DE CLUSTER', '')).strip()
        if sup_email in ['', '-', 'nan']:
            sup_email = "No especificado"
            
        # Overrides for specific store IDs requested by user
        if sid == 3057:
            sup_name = "James Riega"
            sup_cel = "+51 947 811 842"
            sup_email = "james.riega@netcall.pe"
        elif sid == 3031:
            sup_name = "Nivar Trejo"
            sup_cel = "+51 996 245 323"
            sup_email = "nivar.trejo@netcall.pe"
            
        kam_name = str(row.get('KAM ENTEL', '')).strip()
        if pd.isna(kam_name) or kam_name in ['', '-', 'nan']:
            kam_name = str(row.get('KAM SN', '')).strip()
        if kam_name in ['', '-', 'nan']:
            kam_name = "No especificado"
            
        kam_email = str(row.get('CORREO KAM SN', '')).strip()
        if kam_email in ['', '-', 'nan']:
            kam_email = "No especificado"
            
        jefe_comercial = str(row.get('JEFE COMERCIAL SN', '')).strip()
        if jefe_comercial in ['', '-', 'nan']:
            jefe_comercial = "No especificado"
            
        jefe_comercial_email = str(row.get('CORREO JEFE COMERCIAL SN', '')).strip()
        if jefe_comercial_email in ['', '-', 'nan']:
            jefe_comercial_email = "No especificado"

        store_data = {
            "id_pdv": sid,
            "nombre": str(row.get('PDV', f"PDV {sid}")).strip(),
            "canal": str(row.get('CANAL', '')).strip(),
            "subcanal": str(row.get('SUBCANAL', '')).strip(),
            "departamento": str(row.get('DEPARTAMENTO', '')).strip(),
            "provincia": str(row.get('PROVINCIA', '')).strip() if pd.notna(row.get('PROVINCIA')) else "",
            "distrito": str(row.get('DISTRITO', '')).strip() if pd.notna(row.get('DISTRITO')) else "",
            "direccion": str(row.get('DIRECCION ', '')).strip() if pd.notna(row.get('DIRECCION ')) else "",
            "referencia": str(row.get('REFERENCIA', '')).strip() if pd.notna(row.get('REFERENCIA')) else "",
            "latitud": lat,
            "longitud": lng,
            "horario_lv": hours_lv,
            "horario_s": hours_s,
            "horario_d": hours_d,
            "pickup": str(row.get('Tienda PickUp', 'No')).strip(),
            "pickup_priorizado": str(row.get('Tienda PickUp Priorizada', 'No')).strip(),
            "horario_pickup": str(row.get('Horario Recomendado PickUp', '')).strip(),
            "cobertura_hogar": str(row.get('Cobertura Hogar en Tiendas', 'No')).strip(),
            "caja_tienda": str(row.get('CAJA EN TIENDA', 'No')).strip(),
            "supervisor": {
                "nombre": sup_name,
                "celular": sup_cel,
                "correo": sup_email
            },
            "kam": {
                "nombre": kam_name,
                "correo": kam_email
            },
            "jefe_comercial": {
                "nombre": jefe_comercial,
                "correo": jefe_comercial_email
            },
            "asesores": advisors_by_store.get(sid, []),
            "metricas": eff_info
        }
        consolidated_stores.append(store_data)

    # Output JSONs
    for out_dir in OUTPUT_DIRS:
        print(f"Writing output files to {out_dir}...")
        with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(out_dir, "departments.json"), "w", encoding="utf-8") as f:
            json.dump(dept_stats, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(out_dir, "stores.json"), "w", encoding="utf-8") as f:
            json.dump(consolidated_stores, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(out_dir, "advisors.json"), "w", encoding="utf-8") as f:
            json.dump(advisor_stats, f, ensure_ascii=False, indent=2)

    print("Success! Data building complete.")

if __name__ == "__main__":
    process_data()
