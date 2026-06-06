import streamlit as st
import pandas as pd

# 1. Configuración de la interfaz y la página
st.set_page_config(
    page_title="Dashboard de Investigaciones - Facultad",
    page_icon="🎓",
    layout="wide"
)

# 2. Módulo de Carga y Limpieza Crítica de Datos
@st.cache_data
def load_and_audit_data():
    # Cadena de búsqueda prioritaria para la versión 3
    posibles_archivos = [
        "ParaDashboard_Actualizado_hP_3.xlsx",
        "ParaDashboard_Actualizado_hP_2.xlsx",
        "ParaDashboard_Actualizado_hP.xlsx"
    ]
    
    file_path = None
    for archivo in posibles_archivos:
        try:
            with open(archivo, "rb"):
                file_path = archivo
                break
        except FileNotFoundError:
            continue
            
    if file_path is None:
        st.error("No se encontró ninguna versión del archivo Excel en el directorio.")
        st.stop()
        
    # Leer el documento (asume la primera hoja como fuente principal)
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])
    
    # --- AUDITORÍA Y NORMALIZACIÓN DE TEXTO ---
    # Limpiar espacios en blanco al inicio/final y asegurar formato string
    columnas_a_limpiar = [
        'Programa académico en el que se encuentra', 
        'Mesa', 
        'CódigoProyecto', 
        'Semestre académico en el que se encuentra el proyecto',
        'Jefe de Salon',
        '#'
    ]
    
    for col in columnas_a_limpiar:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Reemplazar valores nulos simulados por texto vacío limpio
            df[col] = df[col].replace({'nan': '', 'None': '', '<NA>': ''})

    # 3. Regla algorítmica para Clasificación del Tipo de Proyecto
    def clasificar_proyecto(row):
        semestre = str(row.get('Semestre académico en el que se encuentra el proyecto', '')).lower()
        otro_programa = str(row.get('Programa académico en el que se encuentra [Otro]', '')).lower()
        codigo = str(row.get('CódigoProyecto', '')).lower()
        
        if 'sustent' in semestre or 'sustent' in codigo:
            return 'Sustentación'
        elif 'cog' in codigo or 'cogrado' in otro_programa or 'cogrado' in semestre:
            return 'Cogrado'
        else:
            return 'Otros Proyectos'

    df['Tipo_Proyecto'] = df.apply(clasificar_proyecto, axis=1)
    
    # 4. Enrutador Dinámico de Maestrías (Captura variaciones de escritura)
    def normalizar_maestria(val):
        val_upper = str(val).upper()
        if "MDO" in val_upper or "DOCENCIA" in val_upper: 
            return "Maestría en Docencia (MDO)"
        if "MDL" in val_upper or "LENGUAS" in val_upper or "DIDACTICA DE LAS L" in val_upper: 
            return "Maestría en Didáctica de las Lenguas (MDL)"
        if "MLGE" in val_upper or "LIDERAZGO" in val_upper: 
            return "Maestría en Liderazgo y Gestión Educativa (MLGE)"
        if "MDGEVA" in val_upper or "ESCENARIOS VIRTUALES" in val_upper: 
            return "Maestría en Diseño y Gestión de Escenarios Virtuales (MDGEVA)"
        if val_upper in ['', 'NAN', 'NONE']: 
            return "Programa por Clasificar"
        return f"Programa: {val}" # Flexibilidad total para nuevos programas

    df['Maestria_Procesada'] = df['Programa académico en el que se encuentra'].apply(normalizar_maestria)
    
    # Ajustar valores faltantes en Jefes de Salón y Mesas temáticas
    df['Mesa'] = df['Mesa'].replace({'': 'Por Asignar / Sin Mesa'})
    df['Jefe de Salon'] = df['Jefe de Salon'].replace({'': 'Por Designar'})
    df['#'] = df['#'].replace({'': 'S.A.'}) # Sin Aula / Espacio
    
    # Mapeo y renombrado de columnas expuestas
    columnas_finales = {
        'Maestria_Procesada': 'Maestría',
        'CódigoProyecto': 'Código',
        'Nombre Completo y Consolidado del Proyecto': 'Proyecto',
        'Tipo_Proyecto': 'Clasificación',
        'Jefe de Salon': 'Jefe de Salón',
        'Mesa': 'Temática / Mesa',
        '#': 'Espacio / Mesa #',
        'Enlace': 'Enlace Virtual'
    }
    
    # Validar que la columna esencial del nombre del proyecto exista
    if 'Nombre Completo y Consolidado del Proyecto' not in df.columns:
        st.error("La estructura de columnas cambió. No se encuentra la columna del nombre del proyecto.")
        st.stop()
        
    df_clean = df[list(columnas_finales.keys())].rename(columns=columnas_finales)
    df_clean = df_clean.dropna(subset=['Proyecto'])
    
    # DEDUPLICACIÓN CRÍTICA: Elimina filas idénticas de coautores para no inflar estadísticas
    df_clean = df_clean.drop_duplicates(subset=['Código', 'Proyecto', 'Maestría', 'Temática / Mesa'])
    
    return df_clean, file_path

# Ejecutar la carga controlada
data, archivo_activo = load_and_audit_data()

# --- VISTA PRINCIPAL DEL APLICATIVO ---
st.title("🎓 Sistema Integrado de Investigaciones - Facultad de Ciencias de la Educación")
st.markdown(f"**Origen de datos activo:** `{archivo_activo}` | Monitoreo en tiempo real de agendas y mesas virtuales.")
st.write("---")

# --- 📊 CONTROL DE ESTADÍSTICAS (KPIs) ---
st.subheader("📈 Indicadores Consolidados de la Facultad")
total_p = len(data)
total_s = len(data[data['Clasificación'] == 'Sustentación'])
total_c = len(data[data['Clasificación'] == 'Cogrado'])
total_t = data['Temática / Mesa'].nunique()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.info(f"**Total Proyectos Únicos**\n# {total_p}")
with c2:
    st.success(f"**Sustentaciones**\n# {total_s}")
with c3:
    st.warning(f"**Cogrados**\n# {total_c}")
with c4:
    st.metric(label="Líneas / Temáticas en uso", value=total_t)

st.write("---")

# --- FILTROS GLOBALES ---
st.sidebar.header("🔍 Herramientas de Filtro")
search_query = st.sidebar.text_input("Buscar por palabra clave, título o código")

if search_query:
    data_filtered = data[
        data['Proyecto'].str.contains(search_query, case=False, na=False) |
        data['Código'].str.contains(search_query, case=False, na=False) |
        data['Jefe de Salón'].str.contains(search_query, case=False, na=False)
    ]
else:
    data_filtered = data

# --- CONSTRUCCIÓN DE PESTAÑAS (MAESTRÍAS ➡️ TEMÁTICAS) ---
maestrias_disponibles = sorted(data_filtered['Maestría'].unique())

if maestrias_disponibles:
    tabs_maestrias = st.tabs(maestrias_disponibles)
    
    for index, maestria in enumerate(maestrias_disponibles):
        with tabs_maestrias[index]:
            st.header(f"📊 {maestria}")
            
            df_maestria = data_filtered[data_filtered['Maestría'] == maestria]
            
            # Métricas locales del programa académico seleccionado
            m1, m2, m3 = st.columns(3)
            m1.metric("Proyectos Únicos", len(df_maestria))
            m2.metric("Sustentaciones", len(df_maestria[df_maestria['Clasificación'] == 'Sustentación']))
            m3.metric("Cogrados", len(df_maestria[df_maestria['Clasificación'] == 'Cogrado']))
            
            st.write("---")
            
            # Despliegue por Temática / Mesa
            st.subheader("🎯 Distribución por Temáticas y Mesas de Trabajo")
            tematicas_locales = sorted(df_maestria['Temática / Mesa'].unique())
            
            for tematica in tematicas_locales:
                df_tematica = df_maestria[df_maestria['Temática / Mesa'] == tematica]
                
                with st.expander(f"📘 Temática: {tematica} ({len(df_tematica)} Proyectos)", expanded=True):
                    st.dataframe(
                        df_tematica[[
                            'Código', 'Proyecto', 'Clasificación', 
                            'Jefe de Salón', 'Espacio / Mesa #', 'Enlace Virtual'
                        ]],
                        column_config={
                            "Enlace Virtual": st.column_config.LinkColumn("Enlace de Reunión", display_text="Acceder a Sala Virtual")
                        },
                        use_container_width=True,
                        hide_index=True
                    )
else:
    st.warning("No se encontraron registros que coincidan con los criterios de búsqueda.")

# --- SECCIÓN DE AUTORÍA INSTITUCIONAL ---
st.sidebar.write("---")
st.sidebar.markdown(
    """
    <div style='font-size: 0.85rem; color: #555555; text-align: center;'>
        <p>© 2026 <b>Jairo Alberto Galindo Cuesta</b></p>
        <p>Coordinador de Investigación MDGEVA<br>
        <a href="https://www.unisalle.edu.co" target="_blank" style="color: #00A86B; text-decoration: none; font-weight: bold;">Universidad de La Salle</a></p>
        <p><a href="https://escrituradigital.net" target="_blank" style="color: #0066cc; text-decoration: none;">escrituradigital.net</a></p>
    </div>
    """, 
    unsafe_allow_html=True
)
