import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json
import hashlib

st.set_page_config(
    page_title="AgroAlert Pro | Decision Support System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS (MODERN DARK UI & GLASSMORPHISM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main {
        background: radial-gradient(circle at top right, #111a16, #090e0c 60%, #050807);
        color: #e2e8f0;
    }

    /* Tarjetas estilo Glassmorphism */
    .glass-card {
        background: rgba(18, 28, 23, 0.65);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(52, 211, 153, 0.15);
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(52, 211, 153, 0.35);
        transform: translateY(-2px);
    }

    /* Semáforo de Tratamiento */
    .status-badge-ok {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.1));
        border: 1px solid #10b981;
        color: #34d399;
        padding: 16px 20px;
        border-radius: 14px;
        font-weight: 700;
        font-size: 1.15rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .status-badge-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.1));
        border: 1px solid #f59e0b;
        color: #fbbf24;
        padding: 16px 20px;
        border-radius: 14px;
        font-weight: 700;
        font-size: 1.15rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .status-badge-danger {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.1));
        border: 1px solid #ef4444;
        color: #f87171;
        padding: 16px 20px;
        border-radius: 14px;
        font-weight: 700;
        font-size: 1.15rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Métricas destacadas */
    .metric-container {
        background: rgba(13, 20, 17, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 600;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #059669, #10b981) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
    }

    /* Botones principales */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. SEGURIDAD Y GESTIÓN DE USUARIOS ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "admin": {"pwd": make_hash("admin123"), "nombre": "Joel (Administrador)"},
        "demo": {"pwd": make_hash("demo123"), "nombre": "Bodega Demo"}
    }

if "db_privada" not in st.session_state:
    st.session_state.db_privada = {
        "admin": {
            "🍇 Viñedo": {
                "Frontón Jaime (Logroño)": {"lat": 42.3659, "lon": -2.4235, "variedad": "Tempranillo", "suelo": "Arcillo-calcáreo", "ha": 2.0}
            },
            "🫒 Olivar": {},
            "🌾 Cereal (Trigo/Cebada)": {},
            "🍑 Frutales / Almendro": {}
        },
        "demo": {
            "🍇 Viñedo": {
                "Finca Valdegón": {"lat": 42.4658, "lon": -2.4499, "variedad": "Tempranillo", "suelo": "Arcillo-calcáreo", "ha": 3.5}
            },
            "🫒 Olivar": {},
            "🌾 Cereal (Trigo/Cebada)": {},
            "🍑 Frutales / Almendro": {}
        }
    }

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

# --- PANTALLA DE ACCESO (LOGIN / REGISTRO) ---
if not st.session_state.usuario_autenticado:
    col_vacio1, col_login, col_vacio2 = st.columns([1, 1.4, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 3rem; margin-bottom: 8px;">🌱</div>
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #34d399, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AgroAlert Pro</h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px;">Monitor Fitosanitario & Soporte Agronómico de Precisión</p>
        </div>
        """, unsafe_allow_html=True)

        tab_in, tab_up = st.tabs(["🔑 Acceder", "📝 Crear Cuenta"])
        with tab_in:
            with st.form("form_auth"):
                u = st.text_input("Usuario", value="admin")
                p = st.text_input("Contraseña", type="password", value="admin123")
                b_in = st.form_submit_button("Entrar a mi Panel Privado", use_container_width=True, type="primary")
                if b_in:
                    if u in st.session_state.usuarios_db and check_hash(p, st.session_state.usuarios_db[u]["pwd"]):
                        st.session_state.usuario_autenticado = u
                        st.rerun()
                    else:
                        st.error("Credenciales no válidas.")
        with tab_up:
            with st.form("form_reg"):
                nu = st.text_input("Usuario deseado")
                nn = st.text_input("Nombre o Razón Social (ej: Bodega San Mateo)")
                np = st.text_input("Contraseña", type="password")
                b_up = st.form_submit_button("Registrar Cuenta", use_container_width=True)
                if b_up and nu.strip() and np.strip():
                    if nu in st.session_state.usuarios_db:
                        st.error("Ese usuario ya existe.")
                    else:
                        st.session_state.usuarios_db[nu] = {"pwd": make_hash(np), "nombre": nn}
                        st.session_state.db_privada[nu] = {"🍇 Viñedo": {}, "🫒 Olivar": {}, "🌾 Cereal (Trigo/Cebada)": {}, "🍑 Frutales / Almendro": {}}
                        st.success("Cuenta creada. Ya puedes iniciar sesión.")
    st.stop()

# ==============================================================================
# DASHBOARD PRINCIPAL
# ==============================================================================
user_activo = st.session_state.usuario_autenticado
nombre_cliente = st.session_state.usuarios_db[user_activo]["nombre"]
fincas_usuario = st.session_state.db_privada[user_activo]

# BARRA LATERAL
with st.sidebar:
    st.markdown(f"""
    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 12px 16px; margin-bottom: 15px;">
        <div style="font-size: 0.75rem; color: #34d399; font-weight: 700; text-transform: uppercase;">Cuenta Activa</div>
        <div style="font-size: 1.05rem; font-weight: 800; color: #f8fafc;">{nombre_cliente}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_autenticado = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 🌾 Configuración Agronómica")
    tipo_cultivo = st.selectbox(
        "Cultivo:",
        ["🍇 Viñedo", "🫒 Olivar", "🌾 Cereal (Trigo/Cebada)", "🍑 Frutales / Almendro"]
    )

    fincas_del_cultivo = fincas_usuario.get(tipo_cultivo, {})
    nombres_disponibles = list(fincas_del_cultivo.keys())

    if not nombres_disponibles:
        st.warning("⚠️ Sin fincas en este cultivo. Añade una en 'Gestionar Fincas'.")
        nombre_parcela = "Sin Parcela"
        lat, lon, variedad, suelo, superficie_ha = 42.3659, -2.4235, "Tempranillo", "Franco", 2.0
    else:
        seleccion_parcela = st.selectbox("Parcela Activa:", nombres_disponibles)
        nombre_parcela = seleccion_parcela
        dp = fincas_del_cultivo[seleccion_parcela]
        lat, lon, variedad, suelo, superficie_ha = dp["lat"], dp["lon"], dp["variedad"], dp["suelo"], dp["ha"]

    if "Viñedo" in tipo_cultivo:
        fases = ["Brotación / Desarrollo vegetativo", "Floración / Cuajado", "Envero / Maduración", "Pre-Vendimia"]
    elif "Olivar" in tipo_cultivo:
        fases = ["Brotación / Movimiento de savia", "Floración (Trama)", "Endurecimiento de hueso", "Envero / Recolección"]
    elif "Cereal" in tipo_cultivo:
        fases = ["Ahijamiento", "Encañado", "Espigado / Floración", "Llenado de grano / Maduración"]
    else:
        fases = ["Reposo invernal", "Apertura de yemas / Floración", "Cuajado / Engorde de fruto", "Maduración / Cosecha"]

    fase_fenologica = st.selectbox("Estado Fenológico:", fases)

    st.markdown("---")
    st.markdown("### 📡 Estación Meteorológica")
    modo_datos = st.radio("Fuente:", ["🛰️ Open-Meteo (Satélite en Vivo)", "🧪 Modo Simulación"])

# --- CONSULTA DE DATOS METEOROLÓGICOS ---
hoy = datetime.now()
fechas = [(hoy + timedelta(days=i)).strftime("%d/%m") for i in range(7)]
datos_reales_ok = False

if modo_datos == "🛰️ Open-Meteo (Satélite en Vivo)":
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/2.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            fechas_raw = data["daily"]["time"]
            fechas = [datetime.strptime(f, "%Y-%m-%d").strftime("%d/%m") for f in fechas_raw]
            t_min = data["daily"]["temperature_2m_min"]
            t_max = data["daily"]["temperature_2m_max"]
            lluvia = data["daily"]["precipitation_sum"]
            viento = data["daily"]["wind_speed_10m_max"]
            datos_reales_ok = True
    except Exception:
        t_min = [12.0, 11.5, 13.0, 10.5, 11.0, 12.5, 13.0]
        t_max = [24.0, 25.0, 23.5, 22.0, 24.5, 26.0, 25.5]
        lluvia = [0.0, 1.2, 0.0, 0.0, 2.5, 0.0, 0.0]
        viento = [8.0, 10.0, 12.0, 9.0, 7.0, 8.0, 11.0]
else:
    t_min = [12.0, 11.5, 13.0, 10.5, 11.0, 12.5, 13.0]
    t_max = [24.0, 25.0, 23.5, 22.0, 24.5, 26.0, 25.5]
    lluvia = [0.0, 1.2, 0.0, 0.0, 2.5, 0.0, 0.0]
    viento = [8.0, 10.0, 12.0, 9.0, 7.0, 8.0, 11.0]

min_hoy = t_min[0]
max_hoy = t_max[0]
lluvia_hoy = lluvia[0]
viento_hoy = viento[0]
temp_media_hoy = (min_hoy + max_hoy) / 2
gdd = sum([max(0, ((t_min[i] + t_max[i]) / 2) - 10) for i in range(len(t_min))])

# ==========================================
# ESTRUCTURA PRINCIPAL DE PESTAÑAS
# ==========================================
tab_monitor, tab_calculadora, tab_fincas = st.tabs([
    "🛡️ Monitor & Alertas",
    "🧪 Calculadora de Cuba y Dosis",
    "➕ Añadir / Gestionar Fincas"
])

# -----------------------------------------------------------------------------
# TAB 1: MONITOR & ALERTAS
# -----------------------------------------------------------------------------
with tab_monitor:
    # Encabezado con información de la parcela
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 12px;">
            <h2 style="margin: 0; font-size: 1.8rem; font-weight: 800;">📍 {nombre_parcela}</h2>
            <span style="background: rgba(52, 211, 153, 0.15); border: 1px solid #10b981; color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">
                {superficie_ha} Hectáreas
            </span>
        </div>
        <p style="color: #94a3b8; font-size: 0.95rem; margin-top: -6px;">
            <b>Cultivo:</b> {tipo_cultivo} &nbsp;|&nbsp; <b>Variedad:</b> {variedad} &nbsp;|&nbsp; <b>Suelo:</b> {suelo} &nbsp;|&nbsp; <b>Fase:</b> {fase_fenologica}
        </p>
        """, unsafe_allow_html=True)
    with col_t2:
        st.markdown(f"""
        <div style="text-align: right; color: #64748b; font-size: 0.85rem; margin-top: 10px;">
            Lat: <code style="color:#cbd5e1;">{lat:.4f}</code> | Lon: <code style="color:#cbd5e1;">{lon:.4f}</code><br>
            <span style="color: {'#34d399' if datos_reales_ok else '#38bdf8'}; font-weight: 600;">
                ● {'Datos Satelitales en Vivo' if datos_reales_ok else 'Simulación Local'}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # SEMÁFORO DE APLICACIÓN FITOSANITARIA
    if viento_hoy > 15:
        st.markdown(f"""
        <div class="status-badge-danger">
            ⛔ CONDICIONES ADVERSAS PARA TRATAR &nbsp;|&nbsp; Viento excesivo ({viento_hoy:.1f} km/h > 15 km/h). Alto riesgo de deriva.
        </div>
        """, unsafe_allow_html=True)
    elif lluvia_hoy > 2.5:
        st.markdown(f"""
        <div class="status-badge-danger">
            ⛔ CONDICIONES ADVERSAS PARA TRATAR &nbsp;|&nbsp; Precipitación prevista ({lluvia_hoy:.1f} mm). Lavado inminente de producto.
        </div>
        """, unsafe_allow_html=True)
    elif max_hoy >= 32:
        st.markdown(f"""
        <div class="status-badge-warning">
            ⚠️ VENTANA DE TRATAMIENTO RESTRINGIDA &nbsp;|&nbsp; Tª Máxima alta ({max_hoy:.1f} °C). Aplicar exclusivamente al amanecer.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-badge-ok">
            ✅ VENTANA DE TRATAMIENTO ÓPTIMA &nbsp;|&nbsp; Viento en calma ({viento_hoy:.1f} km/h) y sin riesgo de lavado.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 MÉTRICAS PRINCIPALES EN TARJETAS DE CRISTAL
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">🌡️ Rango Térmico Hoy</div>
            <div class="metric-value">{min_hoy:.1f} / {max_hoy:.1f} <span style="font-size:1rem;color:#94a3b8;">°C</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">🌧️ Lluvia Prevista</div>
            <div class="metric-value">{lluvia_hoy:.1f} <span style="font-size:1rem;color:#94a3b8;">mm</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">💨 Viento Máximo</div>
            <div class="metric-value">{viento_hoy:.1f} <span style="font-size:1rem;color:#94a3b8;">km/h</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">📈 Grados Día (GDD 10°C)</div>
            <div class="metric-value">{gdd:.1f} <span style="font-size:1rem;color:#94a3b8;">acum</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # DIAGNÓSTICO FITOSANITARIO Y MAPA EN 2 COLUMNAS
    c_diag, c_map = st.columns([1.3, 1])

    with c_diag:
        st.markdown("### 🛡️ Diagnóstico Fitosanitario y Plagas")
        
        # Helada
        if min_hoy <= 0:
            st.error(f"🚨 **Helada Crítica ({min_hoy:.1f} °C):** Daño celular en brotes verdes. Activar sistemas antihelada.")
        elif min_hoy <= 2:
            st.warning(f"⚠️ **Alerta Inversión Térmica ({min_hoy:.1f} °C):** Precaución en fondos de valle.")

        # Mildiu / Hongos según cultivo
        if "Viñedo" in tipo_cultivo:
            if lluvia_hoy >= 10 and temp_media_hoy >= 10:
                st.error(f"🚨 **Alerta Mildiu (Regla 10-10-10):** Lluvia ({lluvia_hoy:.1f} mm) con Tª media de {temp_media_hoy:.1f} °C. Infección primaria en marcha.")
            elif lluvia_hoy >= 4 and temp_media_hoy >= 10:
                st.warning(f"⚠️ **Riesgo Medio de Mildiu:** Monitorear haz de hojas en las zonas más sombrías.")
            else:
                st.success("✅ **Mildiu:** Presión infectiva controlada.")
                
            if 22 <= temp_media_hoy <= 28 and lluvia_hoy == 0:
                st.warning(f"⚠️ **Presión Óptima para Oídio:** Tª media ({temp_media_hoy:.1f} °C) idónea para esporulación.")
        else:
            if lluvia_hoy >= 5 and 10 <= temp_media_hoy <= 22:
                st.error("🚨 **Riesgo Fúngico Elevado:** Humedad y temperatura propicias para ataque foliar.")
            else:
                st.success("✅ **Estado Fitosanitario:** Sin presión fúngica crítica.")

    with c_map:
        st.markdown("### 🗺️ Geoposicionamiento")
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=12)

    # GRÁFICA SEMANAL
    st.markdown("### 📊 Evolución Térmica y Pluviométrica a 7 Días")
    df_chart = pd.DataFrame({
        "Fecha": fechas,
        "T. Mínima (°C)": t_min,
        "T. Máxima (°C)": t_max,
        "Lluvia (mm)": lluvia
    }).set_index("Fecha")
    st.line_chart(df_chart[["T. Mínima (°C)", "T. Máxima (°C)"]])

# -----------------------------------------------------------------------------
# TAB 2: CALCULADORA DE CUBA Y DOSIS
# -----------------------------------------------------------------------------
with tab_calculadora:
    st.markdown(f"## 🧪 Dosificación de Fitosanitarios & Abonado Foliar")
    st.caption(f"Cálculo exacto para la parcela activa: **{nombre_parcela}** ({superficie_ha} ha)")

    c_calc1, c_calc2 = st.columns(2)
    with c_calc1:
        st.markdown("#### 🚜 Maquinaria y Volumen")
        vol_cuba = st.number_input("Capacidad de la cuba / atomizador (Litros)", value=1000, step=100, min_value=50)
        gasto_ha = st.number_input("Gasto de caldo por hectárea (L/ha)", value=400, step=50, min_value=50)
        sup_tratar = st.number_input("Superficie a tratar (ha)", value=float(superficie_ha), step=0.5, min_value=0.1)

    with c_calc2:
        st.markdown("#### 🏷️ Ficha del Producto Comercial")
        prod_nombre = st.text_input("Nombre del producto comercial", value="Fungicida Cobre / Sistémico")
        tipo_dosis = st.radio("Formato de dosis:", ["Concentración (gr o cc por 100 L)", "Por Superficie (kg o L por ha)"])
        
        if "Concentración" in tipo_dosis:
            dosis_val = st.number_input("Dosis por 100 L de agua (gr o cc)", value=250.0, step=25.0)
        else:
            dosis_val = st.number_input("Dosis por hectárea (kg o L / ha)", value=2.0, step=0.5)

        precio_unit = st.number_input("Precio (€ / kg o Litro)", value=18.5, step=1.0, min_value=0.0)

    # CÁLCULOS
    caldo_total = sup_tratar * gasto_ha
    num_cubas = caldo_total / vol_cuba
    ha_por_cuba = vol_cuba / gasto_ha

    if "Concentración" in tipo_dosis:
        prod_por_cuba = (dosis_val * (vol_cuba / 100.0)) / 1000.0
        prod_total = (dosis_val * (caldo_total / 100.0)) / 1000.0
    else:
        prod_por_cuba = dosis_val * ha_por_cuba
        prod_total = dosis_val * sup_tratar

    coste_total = prod_total * precio_unit
    coste_ha = coste_total / sup_tratar if sup_tratar > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Hoja de Preparación de Mezcla")

    cr1, cr2, cr3, cr4 = st.columns(4)
    with cr1:
        st.markdown(f"""
        <div class="metric-container" style="border-color: rgba(52, 211, 153, 0.3);">
            <div class="metric-label" style="color:#34d399;">📦 Producto / Cuba Llena</div>
            <div class="metric-value">{prod_por_cuba:.2f} <span style="font-size:1rem;color:#94a3b8;">kg / L</span></div>
        </div>
        """, unsafe_allow_html=True)
    with cr2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">🚜 Cubas Totales</div>
            <div class="metric-value">{num_cubas:.2f} <span style="font-size:1rem;color:#94a3b8;">cubas</span></div>
        </div>
        """, unsafe_allow_html=True)
    with cr3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">🧪 Total Finca</div>
            <div class="metric-value">{prod_total:.2f} <span style="font-size:1rem;color:#94a3b8;">kg / L</span></div>
        </div>
        """, unsafe_allow_html=True)
    with cr4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">💰 Coste Total</div>
            <div class="metric-value">{coste_total:.2f} <span style="font-size:1rem;color:#94a3b8;">€</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"""
    **📝 Instrucciones de carga para el tractorista:**
    1. Llenar la cuba de agua hasta la mitad (**{vol_cuba // 2} litros**) con el agitador hidráulico encendido.
    2. Incorporar lentamente **{prod_por_cuba:.2f} kg o Litros** de **{prod_nombre}**.
    3. Rellenar hasta el nivel total (**{vol_cuba} litros**).
    4. Cada cuba rinde exactamente para **{ha_por_cuba:.2f} hectáreas** a **{gasto_ha} L/ha**.
    """)

# -----------------------------------------------------------------------------
# TAB 3: GESTIÓN DE FINCAS
# -----------------------------------------------------------------------------
with tab_fincas:
    st.markdown(f"## ➕ Registrar Nueva Finca en {tipo_cultivo}")
    st.caption("Esta parcela solo será visible bajo tu cuenta y protegida con contraseña.")

    with st.form("form_nueva_finca_dashboard"):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            fn = st.text_input("Nombre de la Parcela", value="Viña El Roble")
            flat = st.number_input("Latitud Decimal", value=42.3659, format="%.4f")
            flon = st.number_input("Longitud Decimal", value=-2.4235, format="%.4f")
        with c_f2:
            fvar = st.text_input("Variedad Principal", value="Tempranillo")
            fsuelo = st.selectbox("Tipo de Suelo", ["Arcillo-calcáreo", "Aluvial", "Arenoso", "Franco", "Ferroso-arcilloso"])
            fha = st.number_input("Superficie Total (ha)", value=2.5, min_value=0.1, step=0.5)

        btn_guardar_finca = st.form_submit_button("💾 REGISTRAR FINCA EN MI CUENTA", use_container_width=True, type="primary")

        if btn_guardar_finca and fn.strip():
            st.session_state.db_privada[user_activo][tipo_cultivo][fn.strip()] = {
                "lat": flat, "lon": flon, "variedad": fvar, "suelo": fsuelo, "ha": fha
            }
            st.success(f"¡Finca '{fn}' dada de alta y activada con éxito!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Fincas Registradas en Tu Espacio Privado")
    lista_fincas_tabla = [
        {"Nombre": k, "Latitud": v["lat"], "Longitud": v["lon"], "Variedad": v["variedad"], "Suelo": v["suelo"], "Hectáreas": v["ha"]}
        for k, v in fincas_usuario.get(tipo_cultivo, {}).items()
    ]
    if lista_fincas_tabla:
        st.dataframe(pd.DataFrame(lista_fincas_tabla), use_container_width=True)
    else:
        st.info("No tienes fincas registradas aún en este cultivo.")
