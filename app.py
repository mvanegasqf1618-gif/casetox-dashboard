import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ─── Configuración de página ───
st.set_page_config(
    page_title="CaseTox Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Autenticación ───
# Usuarios autorizados: usuario -> contraseña
USUARIOS = {
    "admin": st.secrets.get("ADMIN_PASS", "CaseTox2026*"),
    "toxicologia": st.secrets.get("TOX_PASS", "LabTox2026*"),
}

def check_login():
    """Pantalla de login"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""

    if st.session_state.authenticated:
        return True

    st.markdown(
        "<div style='text-align: center; margin-top: 50px;'>"
        "<h1>🧪 CaseTox Manager</h1>"
        "<h3>Dashboard de Tamizaje — Laboratorio de Toxicología</h3>"
        "<p style='color: gray;'>Acceso restringido. Ingrese sus credenciales.</p>"
        "</div>",
        unsafe_allow_html=True
    )

    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("---")
        usuario = st.text_input("👤 Usuario", key="login_user")
        password = st.text_input("🔒 Contraseña", type="password", key="login_pass")

        if st.button("Iniciar sesión", use_container_width=True, type="primary"):
            if usuario in USUARIOS and USUARIOS[usuario] == password:
                st.session_state.authenticated = True
                st.session_state.username = usuario
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

        st.markdown(
            "<div style='text-align: center; color: gray; font-size: 11px; margin-top: 30px;'>"
            "INML · Laboratorio de Toxicología · Acceso autorizado únicamente"
            "</div>",
            unsafe_allow_html=True
        )
    return False

if not check_login():
    st.stop()

# ─── Cargar datos desde CSV ───
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data(ttl=300)
def load_data():
    df_tam = pd.read_csv(DATA_DIR / "tamizaje.csv", dtype=str)
    df_asig = pd.read_csv(DATA_DIR / "asignacion.csv", dtype=str)
    df_asig["fecha_asignacion"] = pd.to_datetime(df_asig["fecha_asignacion"], errors="coerce")
    return df_tam, df_asig

df_tam, df_asig = load_data()

# ─── Sidebar: Filtros ───
st.sidebar.markdown(f"**Sesión:** {st.session_state.username}")
if st.sidebar.button("🚪 Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("🔬 Filtros")

# Filtro de perito
peritos = sorted(df_asig["perito"].dropna().unique())
perito_sel = st.sidebar.multiselect("Perito", peritos, default=[])

# Filtro de análisis
analisis_list = sorted(df_asig["analisis"].dropna().unique())
analisis_sel = st.sidebar.multiselect("Tipo de Análisis", analisis_list, default=[])

# Filtro de manera de muerte
maneras = sorted(df_tam["manera_de_muerte"].dropna().unique())
manera_sel = st.sidebar.multiselect("Manera de Muerte", maneras, default=[])

# Filtro de fecha
fecha_rango = None
fechas_validas = df_asig["fecha_asignacion"].dropna()
if fechas_validas.shape[0] > 0:
    fecha_min = fechas_validas.min().date()
    fecha_max = fechas_validas.max().date()
    fecha_rango = st.sidebar.date_input(
        "Rango de Fecha Asignación",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

# Botón refrescar
if st.sidebar.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.rerun()

# ─── Aplicar filtros ───
df_asig_f = df_asig.copy()
df_tam_f = df_tam.copy()

if perito_sel:
    df_asig_f = df_asig_f[df_asig_f["perito"].isin(perito_sel)]
if analisis_sel:
    df_asig_f = df_asig_f[df_asig_f["analisis"].isin(analisis_sel)]
if manera_sel:
    df_tam_f = df_tam_f[df_tam_f["manera_de_muerte"].isin(manera_sel)]

if fecha_rango is not None and len(fecha_rango) == 2:
    mask = df_asig_f["fecha_asignacion"].notna()
    df_asig_f = df_asig_f[
        mask &
        (df_asig_f["fecha_asignacion"].dt.date >= fecha_rango[0]) &
        (df_asig_f["fecha_asignacion"].dt.date <= fecha_rango[1])
    ]

# Si hay filtro de perito/análisis, filtrar también tamizaje por los casos resultantes
if perito_sel or analisis_sel:
    casos_filtrados = df_asig_f["caso_id"].unique()
    df_tam_f = df_tam_f[df_tam_f["caso_id"].isin(casos_filtrados)]

# ─── Header ───
st.title("🧪 CaseTox Manager — Dashboard de Tamizaje")
st.markdown("---")

# ─── KPIs principales ───
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📁 Total Casos", f"{df_tam_f.shape[0]:,}")
with col2:
    st.metric("📋 Total Asignaciones", f"{df_asig_f.shape[0]:,}")
with col3:
    n_peritos = df_asig_f["perito"].nunique()
    st.metric("👨‍🔬 Peritos Activos", n_peritos)
with col4:
    n_analisis = df_asig_f["analisis"].nunique()
    st.metric("🔬 Tipos de Análisis", n_analisis)
with col5:
    casos_con_prueba = df_tam_f[df_tam_f["prueba_rapida"].notna()].shape[0]
    st.metric("🧪 Con Prueba Rápida", f"{casos_con_prueba:,}")

st.markdown("---")

# ─── Fila 1: Manera de muerte + Causa de muerte ───
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Distribución por Manera de Muerte")
    manera_counts = df_tam_f["manera_de_muerte"].dropna().value_counts().reset_index()
    manera_counts.columns = ["Manera de Muerte", "Cantidad"]
    if not manera_counts.empty:
        fig = px.pie(manera_counts, names="Manera de Muerte", values="Cantidad",
                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textposition="inside", textinfo="percent+value")
        fig.update_layout(height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para mostrar")

with col_b:
    st.subheader("Top 15 — Causa de Muerte")
    causa_counts = df_tam_f["causa_de_muerte"].dropna().value_counts().head(15).reset_index()
    causa_counts.columns = ["Causa de Muerte", "Cantidad"]
    if not causa_counts.empty:
        fig = px.bar(causa_counts, x="Cantidad", y="Causa de Muerte", orientation="h",
                     color="Cantidad", color_continuous_scale="Reds")
        fig.update_layout(height=400, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para mostrar")

# ─── Fila 2: Carga por perito + Tipos de análisis ───
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Carga de Asignaciones por Perito")
    perito_counts = df_asig_f["perito"].value_counts().reset_index()
    perito_counts.columns = ["Perito", "Asignaciones"]
    if not perito_counts.empty:
        fig = px.bar(perito_counts, x="Asignaciones", y="Perito", orientation="h",
                     color="Asignaciones", color_continuous_scale="Blues")
        fig.update_layout(height=450, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para mostrar")

with col_d:
    st.subheader("Distribución por Tipo de Análisis")
    analisis_counts = df_asig_f["analisis"].dropna().value_counts().reset_index()
    analisis_counts.columns = ["Análisis", "Cantidad"]
    if not analisis_counts.empty:
        fig = px.pie(analisis_counts, names="Análisis", values="Cantidad",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition="inside", textinfo="percent+value")
        fig.update_layout(height=450, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para mostrar")

# ─── Fila 3: Tendencia temporal ───
st.subheader("📅 Asignaciones por Mes")
df_temporal = df_asig_f.dropna(subset=["fecha_asignacion"]).copy()
if not df_temporal.empty:
    df_temporal["mes"] = df_temporal["fecha_asignacion"].dt.to_period("M").astype(str)
    tendencia = df_temporal.groupby("mes").size().reset_index(name="Asignaciones")
    fig = px.area(tendencia, x="mes", y="Asignaciones",
                  color_discrete_sequence=["#636EFA"])
    fig.update_layout(height=350, xaxis_title="Mes", yaxis_title="Cantidad",
                      margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sin datos temporales para mostrar")

# ─── Fila 4: Heatmap Perito x Análisis ───
st.subheader("🗺️ Mapa de Calor: Perito × Tipo de Análisis")
if not df_asig_f.empty:
    pivot = df_asig_f.groupby(["perito", "analisis"]).size().reset_index(name="count")
    pivot_table = pivot.pivot_table(index="perito", columns="analisis", values="count", fill_value=0)
    fig = px.imshow(pivot_table, text_auto=True, aspect="auto",
                    color_continuous_scale="YlOrRd")
    fig.update_layout(height=500, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ─── Fila 5: Pruebas rápidas ───
st.subheader("🧪 Resultados de Prueba Rápida")
col_e, col_f = st.columns(2)
with col_e:
    prueba_counts = df_tam_f["prueba_rapida"].dropna().value_counts().head(15).reset_index()
    prueba_counts.columns = ["Prueba Rápida", "Cantidad"]
    if not prueba_counts.empty:
        fig = px.bar(prueba_counts, x="Cantidad", y="Prueba Rápida", orientation="h",
                     color="Cantidad", color_continuous_scale="Greens")
        fig.update_layout(height=400, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

with col_f:
    con_prueba = df_tam_f["prueba_rapida"].notna().sum()
    sin_prueba = df_tam_f["prueba_rapida"].isna().sum()
    fig = px.pie(values=[con_prueba, sin_prueba], names=["Con prueba", "Sin prueba"],
                 hole=0.5, color_discrete_sequence=["#2ecc71", "#e74c3c"])
    fig.update_layout(height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ─── Buscador de casos ───
st.subheader("🔍 Buscador de Casos")
busqueda = st.text_input("Ingrese el caso_id para consultar:")
if busqueda:
    caso_tam = df_tam[df_tam["caso_id"].str.contains(busqueda, case=False, na=False)]
    caso_asig = df_asig[df_asig["caso_id"].str.contains(busqueda, case=False, na=False)]

    if caso_tam.empty and caso_asig.empty:
        st.warning("No se encontraron resultados.")
    else:
        if not caso_tam.empty:
            st.markdown("**Datos del caso (Tamizaje):**")
            st.dataframe(caso_tam, use_container_width=True, hide_index=True)
        if not caso_asig.empty:
            st.markdown("**Asignaciones del caso:**")
            st.dataframe(caso_asig, use_container_width=True, hide_index=True)

st.markdown("---")

# ─── Tablas completas (expandibles) ───
with st.expander("📋 Ver tabla completa de Asignaciones"):
    st.dataframe(df_asig_f, use_container_width=True, hide_index=True)

with st.expander("📁 Ver tabla completa de Tamizaje"):
    st.dataframe(df_tam_f, use_container_width=True, hide_index=True)

# ─── Footer ───
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "CaseTox Manager Dashboard · Laboratorio de Toxicología · INML · Acceso restringido"
    "</div>",
    unsafe_allow_html=True
)
