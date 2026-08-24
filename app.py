import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime, date
import urllib.request
import urllib.parse
import json
import hashlib

st.set_page_config(
    page_title="AgroAlert Pro | Gestión Integral de Explotación",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS VISUALES RESPONSIVE MÓVIL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main {
        background-color: #f4f6f8;
        color: #0f172a;
    }

    div[data-testid="stRadio"] > div {
        flex-direction: column !important;
        gap: 10px !important;
    }
    
    div[data-testid="stRadio"] label {
        background: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        width: 100% !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
        transition: all 0.15s ease !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        border-color: #15803d !important;
        background-color: #f0fdf4 !important;
    }

    div[data-testid="stRadio"] label div p {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }

    .traffic-ok {
        background-color: #dcfce7;
        border: 3px solid #16a34a;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(22, 163, 74, 0.15);
    }
    .traffic-danger {
        background-color: #fee2e2;
        border: 3px solid #dc2626;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.15);
    }
    .traffic-warning {
        background-color: #fef3c7;
        border: 3px solid #d97706;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.15);
    }

    .traffic-title {
        font-size: 1.5rem;
        font-weight: 900;
        margin-bottom: 6px;
    }
    .traffic-sub {
        font-size: 1.05rem;
        font-weight: 600;
    }

    .field-card {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
    }
    .field-card-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
    }
    .field-card-value {
        font-size: 1.8rem;
        font-weight: 900;
        color: #0f172a;
        margin-top: 4px;
    }
    .field-card-unit {
        font-size: 0.95rem;
        font-weight: 600;
        color: #64748b;
    }

    .recipe-box {
        background-color: #ecfdf5;
        border: 3px solid #059669;
        border-radius: 18px;
        padding: 20px;
        margin-top: 15px;
    }
    .recipe-big {
        font-size: 2.1rem;
        font-weight: 900;
        color: #047857;
    }
    
    .stButton>button {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        padding: 14px !important;
        border-radius: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA JSON ---
USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"
FITOS_FILE = "fitosanitarios_db.json"
LABORES_FILE = "labores_db.json"

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

def cargar_json(archivo, por_defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return por_defecto
    return por_defecto

def guardar_json(archivo, datos):
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error al guardar: {e}")

DEFAULT_USERS = {
    "admin": {
        "pwd": make_hash("admin123"),
        "nombre": "Joel (Mi Explotación)",
        "telefono": "+34626665232",
        "apikey": "3443251"
    }
}

DEFAULT_FINCAS = {
    "admin": {
        "🍇 Viña": {
            "Frontón Jaime": {"lat": 42.3659, "lon": -2.4235, "variedad": "Tempranillo", "suelo": "Cascajo / Calcáreo", "ha": 2.0, "poligono": "12", "parcela": "104", "riego": "Goteo"}
        },
        "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}
    }
}

if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = cargar_json(USERS_FILE, DEFAULT_USERS)

if "db_privada" not in st.session_state:
    st.session_state.db_privada = cargar_json(FINCAS_FILE, DEFAULT_FINCAS)

if "fitos_db" not in st.session_state:
    st.session_state.fitos_db = cargar_json(FITOS_FILE, {})

if "labores_db" not in st.session_state:
    st.session_state.labores_db = cargar_json(LABORES_FILE, {})

# --- API WHATSAPP ---
def disparar_whatsapp_servidor(telefono, apikey, mensaje):
    try:
        num_limpio = telefono.replace(" ", "").replace("-", "")
        if not num_limpio.startswith("+"):
            num_limpio = "+34" + num_limpio if not num_limpio.startswith("34") else "+" + num_limpio
            
        texto_encoded = urllib.parse.quote(mensaje)
        url = f"https://api.callmebot.com/whatsapp.php?phone={num_limpio}&text={texto_encoded}&apikey={apikey.strip()}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_body = resp.read().decode('utf-8', errors='ignore')
            if "Message queued" in res_body or "Message sent" in res_body or resp.status == 200:
                return True, "¡WhatsApp enviado correctamente!"
            else:
                return False, f"Respuesta: {res_body}"
    except Exception as e:
        return False, f"Error al enviar: {str(e)}"

# --- ACCESO ---
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if not st.session_state.usuario_autenticado:
    c1, col_login, c2 = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 3.8rem; margin-bottom: 5px;">🚜</div>
            <h1 style="font-size: 2.2rem; font-weight: 900; color: #15803d; margin: 0;">AgroAlert Pro</h1>
            <p style="font-size: 1.05rem; color: #475569; font-weight: 600; margin-top: 6px;">Gestión de campo, cuaderno de tratamientos y bot WhatsApp</p>
        </div>
        """, unsafe_allow_html=True)

        modo_acceso = st.radio("Acceso:", ["🔑 Iniciar Sesión", "📝 Registrarme y Activar Bot"], label_visibility="collapsed")
        
        if modo_acceso == "🔑 Iniciar Sesión":
            with st.form("form_auth"):
                u = st.text_input("Usuario", value="admin")
                p = st.text_input("Contraseña", type="password", value="admin123")
                b_in = st.form_submit_button("🚜 ENTRAR A MIS PARCELAS", use_container_width=True, type="primary")
                if b_in:
                    if u in st.session_state.usuarios_db and check_hash(p, st.session_state.usuarios_db[u]["pwd"]):
                        st.session_state.usuario_autenticado = u
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        else:
            st.info("💡 Envía `I allow callmebot to send me messages` por WhatsApp al `+34 623 91 22 04` para recibir tu APIKey.")
            with st.form("form_reg"):
                nu = st.text_input("Usuario")
                nn = st.text_input("Nombre o Explotación")
                ntel = st.text_input("📱 Teléfono (+34)")
                napi = st.text_input("🔑 APIKey WhatsApp")
                np = st.text_input("Contraseña", type="password")
                
                b_up = st.form_submit_button("🚀 CREAR CUENTA", use_container_width=True, type="primary")
                if b_up:
                    if not nu.strip() or not np.strip() or not ntel.strip():
                        st.error("Completa los campos obligatorios.")
                    elif nu in st.session_state.usuarios_db:
                        st.error("Ese usuario ya existe.")
                    else:
                        st.session_state.usuarios_db[nu] = {
                            "pwd": make_hash(np),
                            "nombre": nn,
                            "telefono": ntel.strip(),
                            "apikey": napi.strip()
                        }
                        if nu not in st.session_state.db_privada:
                            st.session_state.db_privada[nu] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}
                        
                        guardar_json(USERS_FILE, st.session_state.usuarios_db)
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        
                        if napi.strip():
                            msg = f"🚜 *¡BIENVENIDO A AGROALERT PRO!*\nHola *{nn}*, tu explotación está vinculada."
                            disparar_whatsapp_servidor(ntel.strip(), napi.strip(), msg)
                        
                        st.session_state.usuario_autenticado = nu
                        st.rerun()
    st.stop()

# ==============================================================================
# PANEL PRINCIPAL
# ==============================================================================
user_activo = st.session_state.usuario_autenticado
datos_usuario = st.session_state.usuarios_db.get(user_activo, {})
nombre_cliente = datos_usuario.get("nombre", "Agricultor")
user_telefono = datos_usuario.get("telefono", "+34626665232")
user_apikey = datos_usuario.get("apikey", "3443251")

if user_activo not in st.session_state.db_privada:
    st.session_state.db_privada[user_activo] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}

fincas_usuario = st.session_state.db_privada[user_activo]

# Selector superior
c_top1, c_top2, c_top3 = st.columns([1.2, 1.4, 0.7])
with c_top1:
    tipo_cultivo = st.selectbox("Cultivo:", ["🍇 Viña", "🫒 Olivo", "🌾 Cereal", "🍑 Frutal"])

if tipo_cultivo not in fincas_usuario:
    fincas_usuario[tipo_cultivo] = {}

fincas_del_cultivo = fincas_usuario.get(tipo_cultivo, {})
nombres_disponibles = list(fincas_del_cultivo.keys())

with c_top2:
    if not nombres_disponibles:
        st.selectbox("Parcela:", ["⚠️ Sin parcelas (Añade una en Gestión)"])
        nombre_parcela = "Sin Parcela"
        lat, lon, variedad, suelo, superficie_ha = 42.4658, -2.4499, "Tempranillo", "Franco", 1.0
        poligono, parcela_cat, riego_tipo = "-", "-", "Secano"
    else:
        seleccion_parcela = st.selectbox("Parcela activa:", nombres_disponibles)
        nombre_parcela = seleccion_parcela
        dp = fincas_del_cultivo[seleccion_parcela]
        lat, lon, variedad, suelo, superficie_ha = dp["lat"], dp["lon"], dp["variedad"], dp["suelo"], dp["ha"]
        poligono = dp.get("poligono", "-")
        parcela_cat = dp.get("parcela", "-")
        riego_tipo = dp.get("riego", "Secano")

with c_top3:
    st.write("")
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.usuario_autenticado = None
        st.rerun()

# --- CONSULTA METEOROLÓGICA ---
dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}

try:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max&timezone=auto"
    req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/Campo'})
    with urllib.request.urlopen(req, timeout=4) as resp:
        data = json.loads(resp.read().decode())
        fechas_raw = data["daily"]["time"]
        fechas_legibles = []
        for f in fechas_raw:
            dt = datetime.strptime(f, "%Y-%m-%d")
            dia_nombre = dias_es.get(dt.strftime("%A"), dt.strftime("%A"))
            fechas_legibles.append(f"{dia_nombre} {dt.strftime('%d/%m')}")
        t_min = data["daily"]["temperature_2m_min"]
        t_max = data["daily"]["temperature_2m_max"]
        lluvia = data["daily"]["precipitation_sum"]
        viento = data["daily"]["wind_speed_10m_max"]
except Exception:
    fechas_legibles = ["Hoy", "Mañana", "Día +2", "Día +3", "Día +4", "Día +5", "Día +6"]
    t_min = [12.0, 11.5, 13.0, 10.5, 11.0, 12.5, 13.0]
    t_max = [24.0, 25.0, 23.5, 22.0, 24.5, 26.0, 25.5]
    lluvia = [0.0, 1.2, 0.0, 0.0, 2.5, 0.0, 0.0]
    viento = [8.0, 10.0, 12.0, 9.0, 7.0, 8.0, 11.0]

min_hoy = t_min[0]
max_hoy = t_max[0]
lluvia_hoy = lluvia[0]
viento_hoy = viento[0]
temp_media_hoy = (min_hoy + max_hoy) / 2

# ==============================================================================
# NAVEGACIÓN EN FILAS
# ==============================================================================
st.markdown("<p style='font-size: 0.95rem; font-weight: 800; color: #64748b; margin-top: 10px; margin-bottom: 6px;'>MÓDULOS DE GESTIÓN:</p>", unsafe_allow_html=True)
seccion_activa = st.radio(
    "Navegación:",
    [
        "🚜 ¿Puedo sulfatar hoy? (Semáforo y Tiempo)",
        "🧪 Calculadora de dosis y depósito / cuba",
        "📋 Cuaderno de tratamientos fitosanitarios",
        "🌾 Labores, riegos y cosecha",
        "📲 Bot de avisos por WhatsApp",
        "🌾 Gestión de mis fincas y parcelas"
    ],
    label_visibility="collapsed"
)

st.write("---")

# ==============================================================================
# 1. SEMÁFORO DIARIO
# ==============================================================================
if "Puedo sulfatar hoy" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>📍 {nombre_parcela} <span style='font-size:1rem; color:#64748b;'>({superficie_ha} ha | Pol. {poligono} Parc. {parcela_cat})</span></h2>", unsafe_allow_html=True)

    if viento_hoy > 15:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-danger">
            <div class="traffic-title" style="color: #991b1b;">⛔ HOY NO SE RECOMIENDA SULFATAR</div>
            <div class="traffic-sub" style="color: #b91c1c;">Viento de {viento_hoy:.0f} km/h (límite 15 km/h). Hay deriva y pérdida de caldo.</div>
        </div>
        """, unsafe_allow_html=True)
    elif lluvia_hoy > 2.0:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-danger">
            <div class="traffic-title" style="color: #991b1b;">⛔ HOY NO SULFATES</div>
            <div class="traffic-sub" style="color: #b91c1c;">Lluvia prevista de {lluvia_hoy:.1f} L/m². El producto se lavará.</div>
        </div>
        """, unsafe_allow_html=True)
    elif max_hoy >= 32:
        semaforo_estado = "AMBAR"
        st.markdown(f"""
        <div class="traffic-warning">
            <div class="traffic-title" style="color: #92400e;">⚠️ TRATAR SOLO A PRIMERA HORA</div>
            <div class="traffic-sub" style="color: #b45309;">Temperatura de {max_hoy:.0f} °C. Evitar horas centrales para no quemar la hoja.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        semaforo_estado = "VERDE"
        st.markdown(f"""
        <div class="traffic-ok">
            <div class="traffic-title" style="color: #166534;">✅ CONDICIONES ÓPTIMAS PARA TRATAR</div>
            <div class="traffic-sub" style="color: #15803d;">Viento en calma ({viento_hoy:.0f} km/h), sin lluvia y {max_hoy:.0f} °C.</div>
        </div>
        """, unsafe_allow_html=True)

    if "Viña" in tipo_cultivo:
        riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and temp_media_hoy >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ LIMPIO")
    else:
        riesgo_txt = "🚨 ATENCIÓN" if lluvia_hoy >= 5 else "✅ LIMPIO"

    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">🌡️ Tª Hoy</div>
            <div class="field-card-value">{min_hoy:.0f}° / {max_hoy:.0f}° <span class="field-card-unit">C</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">💨 Viento</div>
            <div class="field-card-value">{viento_hoy:.0f} <span class="field-card-unit">km/h</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">🌧️ Lluvia</div>
            <div class="field-card-value">{lluvia_hoy:.1f} <span class="field-card-unit">L</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">🛡️ Riesgo Fitosanitario</div>
            <div class="field-card-value" style="font-size:1.4rem; color: {'#dc2626' if 'ALTO' in riesgo_txt else '#15803d'};">{riesgo_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><h3 style='font-size: 1.3rem; font-weight: 800;'>📅 Previsión a 7 días:</h3>", unsafe_allow_html=True)
    df_dias = []
    for i in range(len(fechas_legibles)):
        apto = "✅ Óptimo" if (viento[i] <= 15 and lluvia[i] <= 2.0 and t_max[i] < 32) else ("⛔ No tratar" if (viento[i] > 15 or lluvia[i] > 2.0) else "⚠️ Cuidado")
        df_dias.append({
            "Día": fechas_legibles[i],
            "Tª Min/Max": f"{t_min[i]:.0f}°/{t_max[i]:.0f}°C",
            "Lluvia": f"{lluvia[i]:.1f} L",
            "Viento": f"{viento[i]:.0f} km/h",
            "Condición": apto
        })
    st.dataframe(pd.DataFrame(df_dias), use_container_width=True, hide_index=True)

# ==============================================================================
# 2. CALCULADORA DE CUBA
# ==============================================================================
elif "Calculadora de dosis" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>🧪 Calculadora de Dosis y Tanque / Cuba</h2>", unsafe_allow_html=True)
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.markdown("#### 🚜 Maquinaria:")
        litros_cuba = st.selectbox("Capacidad depósito/cuba (L):", [500, 600, 800, 1000, 1500, 2000, 3000], index=3)
        gasto_caldo = st.number_input("Gasto de caldo por ha (L/ha):", value=400, step=50)
        ha_a_sulfatar = st.number_input("Superficie a tratar (ha):", value=float(superficie_ha), step=0.5)

    with c_c2:
        st.markdown("#### 🏷️ Dosis Producto:")
        formato_dosis = st.radio("Formato de dosis:", [
            "Por 100 Litros de agua (gr o cc / 100 L)",
            "Por Hectárea completa (kg o L / ha)"
        ])
        
        if "100 Litros" in formato_dosis:
            dosis_num = st.number_input("Gramos o cc por cada 100 L:", value=250.0, step=25.0)
        else:
            dosis_num = st.number_input("Kilos o Litros por Hectárea:", value=2.0, step=0.5)

        precio_kilo = st.number_input("Precio producto (€/kg o €/L):", value=18.0, step=1.0)

    caldo_total_necesario = ha_a_sulfatar * gasto_caldo
    num_cubas_necesarias = caldo_total_necesario / litros_cuba if litros_cuba > 0 else 0
    ha_por_cuba = litros_cuba / gasto_caldo if gasto_caldo > 0 else 0

    if "100 Litros" in formato_dosis:
        kilos_por_cuba = (dosis_num * (litros_cuba / 100.0)) / 1000.0
        kilos_totales_finca = (dosis_num * (caldo_total_necesario / 100.0)) / 1000.0
    else:
        kilos_por_cuba = dosis_num * ha_por_cuba
        kilos_totales_finca = dosis_num * ha_a_sulfatar

    coste_total_euros = kilos_totales_finca * precio_kilo

    st.markdown(f"""
    <div class="recipe-box">
        <div style="font-size: 1rem; font-weight: 800; color: #065f46; text-transform: uppercase;">📝 MEZCLA EXACTA POR DEPÓSITO</div>
        <div class="recipe-big">{kilos_por_cuba:.2f} <span style="font-size:1.3rem;">kg/L por depósito lleno de {litros_cuba} L</span></div>
        <hr style="border: 1px solid #a7f3d0; margin: 12px 0;">
        <div style="font-size: 1.15rem; font-weight: 700; color: #047857;">
            🚜 Para <b>{ha_a_sulfatar} ha</b> necesitas <b>{num_cubas_necesarias:.1f} depósitos</b> ({kilos_totales_finca:.2f} kg/L totales).
        </div>
        <div style="font-size: 1rem; font-weight: 600; color: #065f46; margin-top: 4px;">
            💰 Coste total: <b>{coste_total_euros:.2f} €</b> ({(coste_total_euros/ha_a_sulfatar if ha_a_sulfatar>0 else 0):.2f} €/ha).
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. CUADERNO DE FITOSANITARIOS
# ==============================================================================
elif "Cuaderno de tratamientos" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>📋 Registro Oficial de Fitosanitarios</h2>", unsafe_allow_html=True)
    
    with st.form("form_fito"):
        st.markdown("#### ➕ Registrar Tratamiento en Parcela Activa:")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            fecha_fito = st.date_input("Fecha de aplicación:", date.today())
            plaga_tratada = st.text_input("Plaga / Hongo / Motivo:", value="Mildiu")
            producto_fito = st.text_input("Producto Comercial / Materia Activa:", value="Oxicloruro de Cobre 50%")
            num_mapa = st.text_input("Nº Registro MAPA (Opcional):", value="ES-00123")
        with c_f2:
            dosis_fito = st.text_input("Dosis aplicada:", value="2.5 kg/ha")
            caldo_gastado = st.number_input("Gasto total caldo (Litros):", value=800, step=100)
            plazo_seg = st.number_input("Plazo de Seguridad (días):", value=14, step=1)
            aplicador_fito = st.text_input("Aplicador / Carnet:", value="Joel Rodríguez")

        b_guardar_fito = st.form_submit_button("💾 GUARDAR EN EL CUADERNO DE EXPLOTACIÓN", use_container_width=True, type="primary")

        if b_guardar_fito and producto_fito.strip():
            if user_activo not in st.session_state.fitos_db:
                st.session_state.fitos_db[user_activo] = []
            
            registro_nuevo = {
                "Fecha": str(fecha_fito),
                "Cultivo": tipo_cultivo,
                "Parcela": nombre_parcela,
                "Plaga": plaga_tratada,
                "Producto": producto_fito,
                "Registro MAPA": num_mapa,
                "Dosis": dosis_fito,
                "Caldo (L)": caldo_gastado,
                "Plazo Seg. (días)": plazo_seg,
                "Aplicador": aplicador_fito
            }
            st.session_state.fitos_db[user_activo].append(registro_nuevo)
            guardar_json(FITOS_FILE, st.session_state.fitos_db)
            st.success("¡Tratamiento guardado permanentemente!")
            st.rerun()

    st.write("---")
    st.markdown("### 📜 Historial de Tratamientos Realizados:")
    hist_fitos = st.session_state.fitos_db.get(user_activo, [])
    if hist_fitos:
        st.dataframe(pd.DataFrame(hist_fitos), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no has registrado ningún tratamiento en tu cuaderno.")

# ==============================================================================
# 4. LABORES, RIEGOS Y COSECHA
# ==============================================================================
elif "Labores, riegos y cosecha" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>🌾 Labores de Campo, Riegos y Cosecha</h2>", unsafe_allow_html=True)
    
    sub_lab1, sub_lab2 = st.tabs(["🚜 REGISTRAR LABOR / RIEGO", "🍇 REGISTRAR COSECHA / LIQUIDACIÓN"])
    
    with sub_lab1:
        with st.form("form_labor"):
            c_l1, c_l2 = st.columns(2)
            with c_l1:
                fecha_lab = st.date_input("Fecha de labor:", date.today())
                tipo_labor = st.selectbox("Tipo de labor:", ["Poda", "Pase de grada / Chisel", "Desniete / Espergura", "Abonado de fondo", "Riego", "Tratamiento herbicida"])
                horas_maq = st.number_input("Horas de tractor:", value=4.0, step=0.5)
            with c_l2:
                abono_aporte = st.text_input("Abono / Aporte (si aplica):", value="NPK 15-15-15 (200 kg)")
                gasoil_litros = st.number_input("Gasoil gastado (L):", value=30.0, step=5.0)
                coste_mano_obra = st.number_input("Coste mano de obra / Jornales (€):", value=60.0, step=10.0)

            b_guarda_labor = st.form_submit_button("💾 GUARDAR LABOR DE CAMPO", use_container_width=True, type="primary")
            if b_guarda_labor:
                if user_activo not in st.session_state.labores_db:
                    st.session_state.labores_db[user_activo] = {"labores": [], "cosechas": []}
                
                reg_l = {
                    "Fecha": str(fecha_lab),
                    "Cultivo": tipo_cultivo,
                    "Parcela": nombre_parcela,
                    "Labor": tipo_labor,
                    "Horas Tractor": horas_maq,
                    "Aporte": abono_aporte,
                    "Gasoil (L)": gasoil_litros,
                    "Coste (€)": coste_mano_obra
                }
                st.session_state.labores_db[user_activo]["labores"].append(reg_l)
                guardar_json(LABORES_FILE, st.session_state.labores_db)
                st.success("¡Labor guardada!")
                st.rerun()

    with sub_lab2:
        with st.form("form_cosecha"):
            c_cos1, c_cos2 = st.columns(2)
            with c_cos1:
                fecha_cos = st.date_input("Fecha recolección / vendimia:", date.today())
                kilos_totales = st.number_input("Kilos totales recolectados:", value=12000.0, step=500.0)
                calidad_param = st.text_input("Calidad / Grado Baumé / Humedad:", value="13.8° / Grado 1")
            with c_cos2:
                comprador_dest = st.text_input("Destino / Bodega / Cooperativa:", value="Cooperativa Comarcal")
                precio_kilo_venta = st.number_input("Precio venta liquidado (€/kg):", value=0.65, step=0.05, format="%.3f")
            
            ingreso_bruto = kilos_totales * precio_kilo_venta
            rendimiento_ha = kilos_totales / superficie_ha if superficie_ha > 0 else 0
            
            st.info(f"📊 Rendimiento estimado: **{rendimiento_ha:.0f} kg/ha** | Ingreso total: **{ingreso_bruto:.2f} €**")

            b_guarda_cosecha = st.form_submit_button("💾 GUARDAR REGISTRO DE COSECHA", use_container_width=True, type="primary")
            if b_guarda_cosecha:
                if user_activo not in st.session_state.labores_db:
                    st.session_state.labores_db[user_activo] = {"labores": [], "cosechas": []}
                
                reg_c = {
                    "Fecha": str(fecha_cos),
                    "Cultivo": tipo_cultivo,
                    "Parcela": nombre_parcela,
                    "Kilos": kilos_totales,
                    "Rdto (kg/ha)": round(rendimiento_ha, 1),
                    "Calidad": calidad_param,
                    "Comprador": comprador_dest,
                    "Precio (€/kg)": precio_kilo_venta,
                    "Total (€)": round(ingreso_bruto, 2)
                }
                st.session_state.labores_db[user_activo]["cosechas"].append(reg_c)
                guardar_json(LABORES_FILE, st.session_state.labores_db)
                st.success("¡Cosecha guardada!")
                st.rerun()

    st.write("---")
    st.markdown("### 📋 Histórico de Labores y Cosechas:")
    datos_lab_all = st.session_state.labores_db.get(user_activo, {"labores": [], "cosechas": []})
    
    c_tabl1, c_tabl2 = st.columns(2)
    with c_tabl1:
        st.markdown("#### 🚜 Labores registradas:")
        if datos_lab_all.get("labores"):
            st.dataframe(pd.DataFrame(datos_lab_all["labores"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Sin labores aún.")
    with c_tabl2:
        st.markdown("#### 🍇 Cosechas registradas:")
        if datos_lab_all.get("cosechas"):
            st.dataframe(pd.DataFrame(datos_lab_all["cosechas"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Sin cosechas aún.")

# ==============================================================================
# 5. BOT WHATSAPP
# ==============================================================================
elif "Bot de avisos" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>📲 Bot de Avisos por WhatsApp</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.05rem; color: #475569;'>Disparos vinculados al teléfono: <b>{user_telefono}</b> ({nombre_cliente})</p>", unsafe_allow_html=True)

    if "Viña" in tipo_cultivo:
        riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and temp_media_hoy >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ LIMPIO")
    else:
        riesgo_txt = "🚨 ATENCIÓN" if lluvia_hoy >= 5 else "✅ LIMPIO"

    semaforo_estado_txt = "🟢 ÓPTIMO PARA SULFATAR" if (viento_hoy <= 15 and lluvia_hoy <= 2.0 and max_hoy < 32) else "🔴 NO RECOMENDADO SULFATAR"

    msg_parte = f"""🚜 *PARTE MATUTINO AGROALERT*
📍 *Parcela:* {nombre_parcela} ({superficie_ha} ha)

{semaforo_estado_txt}

🌡️ *Temperaturas:* {min_hoy:.0f}°C a {max_hoy:.0f}°C
💨 *Viento:* {viento_hoy:.0f} km/h
🌧️ *Lluvia:* {lluvia_hoy:.1f} mm
🛡️ *Estado:* {riesgo_txt}"""

    msg_helada = f"""🚨 *¡ALERTA ROJA POR HELADA!*
📍 *Parcela:* {nombre_parcela}

⚠️ *Riesgo Inminente:* Previsión de temperatura crítica de *{min_hoy:.1f}°C*.
🛡️ *Acción:* Activar medidas antihelada inmediatamente."""

    if st.button("📲 DISPARAR PARTE MATUTINO", use_container_width=True, type="primary"):
        if not user_apikey:
            st.error("No tienes configurada tu APIKey de WhatsApp.")
        else:
            ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg_parte)
            if ok:
                st.success(res)
            else:
                st.error(res)

    if st.button("🚨 DISPARAR ALERTA HELADA", use_container_width=True):
        if not user_apikey:
            st.error("No tienes configurada tu APIKey de WhatsApp.")
        else:
            ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg_helada)
            if ok:
                st.warning("¡Alerta enviada!")
            else:
                st.error(res)

# ==============================================================================
# 6. GESTIÓN DE FINCAS Y CATASTRO
# ==============================================================================
elif "Gestión de mis fincas" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>🌾 Gestión de Parcelas y Catastro ({tipo_cultivo})</h2>", unsafe_allow_html=True)
    
    fincas_actuales = fincas_usuario.get(tipo_cultivo, {})
    
    if not fincas_actuales:
        st.info(f"👉 No tienes ninguna finca registrada en **{tipo_cultivo}**. Rellena los datos para crear la primera:")
        
        with st.form("form_alta_primera_finca"):
            nom_finca = st.text_input("Nombre de la Parcela:", value="Finca Principal")
            c_lat, c_lon = st.columns(2)
            with c_lat:
                lat_finca = st.number_input("Latitud decimal:", value=42.4658, format="%.4f")
            with c_lon:
                lon_finca = st.number_input("Longitud decimal:", value=-2.4499, format="%.4f")
            
            c_var, c_ha = st.columns(2)
            with c_var:
                var_finca = st.text_input("Variedad:", value="Tempranillo")
            with c_ha:
                ha_finca = st.number_input("Superficie (ha):", value=2.0, min_value=0.1, step=0.5)
            
            c_pol, c_parc = st.columns(2)
            with c_pol:
                pol_finca = st.text_input("Polígono SIGPAC:", value="12")
            with c_parc:
                parc_finca = st.text_input("Parcela SIGPAC:", value="104")

            c_suelo, c_riego = st.columns(2)
            with c_suelo:
                suelo_finca = st.selectbox("Tipo de suelo:", ["Cascajo / Pedregoso", "Cascajo / Calcáreo", "Arcillo-calcáreo", "Arenoso", "Tierra fuerte"])
            with c_riego:
                riego_finca = st.selectbox("Régimen de riego:", ["Secano", "Goteo", "Aspersión", "A pie / Inundación"])

            btn_crear_primera = st.form_submit_button("💾 CREAR Y GUARDAR ESTA PARCELA", use_container_width=True, type="primary")

            if btn_crear_primera and nom_finca.strip():
                if user_activo not in st.session_state.db_privada:
                    st.session_state.db_privada[user_activo] = {}
                if tipo_cultivo not in st.session_state.db_privada[user_activo]:
                    st.session_state.db_privada[user_activo][tipo_cultivo] = {}

                st.session_state.db_privada[user_activo][tipo_cultivo][nom_finca.strip()] = {
                    "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca,
                    "poligono": pol_finca, "parcela": parc_finca, "riego": riego_finca
                }
                guardar_json(FINCAS_FILE, st.session_state.db_privada)
                st.success(f"¡Parcela '{nom_finca}' creada y guardada!")
                st.rerun()

    else:
        modo_finca = st.radio("Acción en Fincas:", ["✏️ Modificar o Eliminar Finca Existente", "➕ Añadir Nueva Finca"], label_visibility="collapsed")
        
        if "Modificar o Eliminar" in modo_finca:
            finca_a_editar = st.selectbox("Selecciona la finca a editar:", list(fincas_actuales.keys()))
            datos_f = fincas_actuales[finca_a_editar]
            
            suelos_lista = ["Cascajo / Pedregoso", "Cascajo / Calcáreo", "Arcillo-calcáreo", "Arenoso", "Tierra fuerte"]
            suelo_index = suelos_lista.index(datos_f.get("suelo", "Cascajo / Pedregoso")) if datos_f.get("suelo") in suelos_lista else 0
            
            riegos_lista = ["Secano", "Goteo", "Aspersión", "A pie / Inundación"]
            riego_index = riegos_lista.index(datos_f.get("riego", "Secano")) if datos_f.get("riego") in riegos_lista else 0

            with st.form("form_editar_finca"):
                nuevo_nombre = st.text_input("Nombre finca:", value=finca_a_editar)
                c_elat, c_elon = st.columns(2)
                with c_elat:
                    nueva_lat = st.number_input("Latitud:", value=float(datos_f["lat"]), format="%.4f")
                with c_elon:
                    nueva_lon = st.number_input("Longitud:", value=float(datos_f["lon"]), format="%.4f")
                
                c_evar, c_eha = st.columns(2)
                with c_evar:
                    nueva_var = st.text_input("Variedad:", value=datos_f["variedad"])
                with c_eha:
                    nueva_ha = st.number_input("Superficie (ha):", value=float(datos_f["ha"]), min_value=0.1, step=0.5)
                
                c_epol, c_eparc = st.columns(2)
                with c_epol:
                    nuevo_pol = st.text_input("Polígono SIGPAC:", value=datos_f.get("poligono", "-"))
                with c_eparc:
                    nuevo_parc = st.text_input("Parcela SIGPAC:", value=datos_f.get("parcela", "-"))

                c_esuelo, c_eriego = st.columns(2)
                with c_esuelo:
                    nuevo_suelo = st.selectbox("Suelo:", suelos_lista, index=suelo_index)
                with c_eriego:
                    nuevo_riego = st.selectbox("Riego:", riegos_lista, index=riego_index)
                
                c_btn_save, c_btn_del = st.columns(2)
                with c_btn_save:
                    guardar_edicion = st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary")
                with c_btn_del:
                    borrar_finca = st.form_submit_button("🗑️ ELIMINAR FINCA", use_container_width=True)
                
                if guardar_edicion:
                    if nuevo_nombre.strip() != finca_a_editar:
                        del st.session_state.db_privada[user_activo][tipo_cultivo][finca_a_editar]
                    st.session_state.db_privada[user_activo][tipo_cultivo][nuevo_nombre.strip()] = {
                        "lat": nueva_lat, "lon": nueva_lon, "variedad": nueva_var, "suelo": nuevo_suelo, "ha": nueva_ha,
                        "poligono": nuevo_pol, "parcela": nuevo_parc, "riego": nuevo_riego
                    }
                    guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.success("¡Finca actualizada!")
                    st.rerun()
                    
                if borrar_finca:
                    del st.session_state.db_privada[user_activo][tipo_cultivo][finca_a_editar]
                    guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.warning("¡Finca eliminada!")
                    st.rerun()

        else:
            with st.form("form_alta_finca_extra"):
                nom_finca = st.text_input("Nombre finca:", value="Parcela Nueva")
                c_alat, c_alon = st.columns(2)
                with c_alat:
                    lat_finca = st.number_input("Latitud decimal:", value=42.4658, format="%.4f")
                with c_alon:
                    lon_finca = st.number_input("Longitud decimal:", value=-2.4499, format="%.4f")
                
                c_avar, c_aha = st.columns(2)
                with c_avar:
                    var_finca = st.text_input("Variedad:", value="Tempranillo")
                with c_aha:
                    ha_finca = st.number_input("Superficie (ha):", value=2.0, min_value=0.1, step=0.5)
                
                c_apol, c_aparc = st.columns(2)
                with c_apol:
                    pol_finca = st.text_input("Polígono SIGPAC:", value="14")
                with c_aparc:
                    parc_finca = st.text_input("Parcela SIGPAC:", value="205")

                c_asuelo, c_ariego = st.columns(2)
                with c_asuelo:
                    suelo_finca = st.selectbox("Terreno:", ["Cascajo / Pedregoso", "Cascajo / Calcáreo", "Arcillo-calcáreo", "Arenoso", "Tierra fuerte"])
                with c_ariego:
                    riego_finca = st.selectbox("Régimen de riego:", ["Secano", "Goteo", "Aspersión", "A pie / Inundación"])

                btn_guardar_f = st.form_submit_button("💾 CREAR NUEVA PARCELA", use_container_width=True, type="primary")

                if btn_guardar_f and nom_finca.strip():
                    st.session_state.db_privada[user_activo][tipo_cultivo][nom_finca.strip()] = {
                        "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca,
                        "poligono": pol_finca, "parcela": parc_finca, "riego": riego_finca
                    }
                    guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.success(f"¡Parcela '{nom_finca}' guardada!")
                    st.rerun()

        st.write("---")
        st.markdown("### 📋 Resumen de Parcelas:")
        tabla_fincas = [
            {
                "Parcela": k,
                "Hectáreas": v["ha"],
                "Variedad": v["variedad"],
                "Polígono": v.get("poligono", "-"),
                "Parcela SIGPAC": v.get("parcela", "-"),
                "Riego": v.get("riego", "Secano"),
                "Terreno": v["suelo"]
            }
            for k, v in fincas_usuario.get(tipo_cultivo, {}).items()
        ]
        if tabla_fincas:
            st.dataframe(pd.DataFrame(tabla_fincas), use_container_width=True, hide_index=True)
