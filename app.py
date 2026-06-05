import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Investigaciones - Facultad",
    page_icon="🎓",
    layout="wide"
)

# Cargar y procesar los datos
@st.cache_data
def load_data():
    file_path = "ParaDashboard_Actualizado_hP.xlsx"
    df = pd.read_excel(file_path, sheet_name="Investigaciones en la Facultad")
    
    # 1. Clasificación inteligente del Tipo de Proyecto
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
    
    # 2. Limpieza de nombres de maestrías para mejor legibilidad
    def limpiar_maestria(val):
        val_str = str(val)
        if "MDO" in val_str: return "Maestría en Docencia (MDO)"
        if "MDL" in val_str: return "Maestría en Didáctica de las Lenguas (MDL)"
        if "MLGE" in val_str: return "Maestría en Liderazgo y Gestión Educativa (MLGE)"
        if "MDGEVA" in val_str: return "Maestría en Diseño y Gestión de Escenarios Virtuales (MDGEVA)"
        return "Otros Programas"

    df['Maestria'] = df['Programa académico en el que se encuentra'].apply(limpiar_maestria)
    
    # Renombrar columnas clave
    columnas_clave = {
        'Maestria': 'Maestría',
        'CódigoProyecto': 'Código',
        'Nombre Completo y Consolidado del Proyecto': 'Proyecto',
        'Tipo_Proyecto': 'Clasificación',
        'Jefe de Salon': 'Jefe de Salón',
        'Mesa': 'Temática / Mesa',
        '#': 'Espacio / Mesa #',
        'Enlace': 'Enlace Virtual'
    }
    
    df_clean = df[list(columnas_clave.keys())].rename(columns=columnas_clave)
    df_clean = df_clean.dropna(subset=['Proyecto']).drop_duplicates()
    return df_clean

try:
    data = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo de datos: {e}")
    st.stop()

# --- INTERFAZ DE USUARIO ---
st.title("🎓 Sistema de Gestión de Proyectos por Maestría")
st.markdown("Consulta y organización de proyectos segmentados por programa académico, temáticas y asignaciones logísticas.")
st.write("---")

# --- 📊 NUEVO CONTADOR DE ESTADÍSTICAS GLOBALES ---
st.subheader("📈 Indicadores y Estadísticas Generales (Facultad)")
total_proyectos = len(data)
total_sustentaciones = len(data[data['Clasificación'] == 'Sustentación'])
total_cogrados = len(data[data['Clasificación'] == 'Cogrado'])
total_tematicas = data['Temática / Mesa'].nunique()

# Diseño de tarjetas en columnas para las métricas
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.info(f"**Total Proyectos**\n# {total_proyectos}")
with col_stat2:
    st.success(f"**Sustentaciones**\n# {total_sustentaciones}")
with col_stat3:
    st.warning(f"**Cogrados**\n# {total_cogrados}")
with col_stat4:
    st.metric(label="Líneas/Temáticas", value=total_tematicas)

st.write("---")

# --- FILTROS LATERALES ---
st.sidebar.header("🔍 Filtros Globales")
search_query = st.sidebar.text_input("Buscar por palabra clave o código")

# Aplicar filtro de búsqueda de texto si existe
if search_query:
    data_filtered = data[
        data['Proyecto'].str.contains(search_query, case=False, na=False) |
        data['Código'].str.contains(search_query, case=False, na=False)
    ]
else:
    data_filtered = data

# --- NAVEGACIÓN PRINCIPAL POR MAESTRÍAS ---
maestrias_disponibles = sorted(data_filtered['Maestría'].unique())

if maestrias_disponibles:
    tabs_maestrias = st.tabs(maestrias_disponibles)
    
    for index, maestria in enumerate(maestrias_disponibles):
        with tabs_maestrias[index]:
            st.header(f"📊 {maestria}")
            
            df_maestria = data_filtered[data_filtered['Maestría'] == maestria]
            
            # Métricas locales por maestría seleccionada
            m1, m2, m3 = st.columns(3)
            m1.metric("Proyectos en este programa", len(df_maestria))
            m2.metric("Sustentaciones", len(df_maestria[df_maestria['Clasificación'] == 'Sustentación']))
            m3.metric("Cogrados", len(df_maestria[df_maestria['Clasificación'] == 'Cogrado']))
            
            st.write("---")
            
            # --- SUB-NIVEL: ORGANIZACIÓN POR TEMÁTICA ---
            st.subheader("🎯 Distribución por Temáticas y Mesas de Trabajo")
            tematicas_de_maestria = sorted(df_maestria['Temática / Mesa'].dropna().unique())
            
            if not tematicas_de_maestria:
                st.info("No se encontraron temáticas registradas para los criterios seleccionados.")
            
            for tematica in tematicas_de_maestria:
                df_tematica = df_maestria[df_maestria['Temática / Mesa'] == tematica]
                
                with st.expander(f"📘 Temática: {tematica} ({len(df_tematica)} Proyectos)", expanded=True):
                    st.dataframe(
                        df_tematica[[
                            'Código', 'Proyecto', 'Clasificación', 
                            'Jefe de Salón', 'Espacio / Mesa #', 'Enlace Virtual'
                        ]],
                        column_config={
                            "Clasificación": st.column_config.TextColumn("Tipo"),
                            "Enlace Virtual": st.column_config.LinkColumn("Enlace de Reunión", display_text="Acceder a Sala")
                        },
                        use_container_width=True,
                        hide_index=True
                    )
else:
    st.warning("No se encontraron datos que coincidan con los filtros aplicados.")

# --- SECCIÓN DE CRÉDITOS Y ENLACES (BARRA LATERAL Y PIE DE PÁGINA) ---
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

st.write("---")
st.markdown(
    """
    <div style='text-align: center; padding: 15px; color: #777777; font-size: 0.9rem;'>
        Copyright © 2026 | Desarrollado para la <b>Facultad de Ciencias de la Educación</b> por <b>Jairo Alberto Galindo Cuesta</b> | 
        <a href="https://www.unisalle.edu.co" target="_blank" style="color: #00A86B; text-decoration: none; font-weight: bold;">Unisalle</a>
    </div>
    """, 
    unsafe_allow_html=True
)
