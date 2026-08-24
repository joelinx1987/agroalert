import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json
import hashlib

st.set_page_config(
    page_title="AgroAlert Campo | Monitor & WhatsApp Bot",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS VISUALES ADAPTADOS A MÓVIL (FILAS Y ALTO CONTRASTE) ---
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

    /* MENÚ VERTICAL TIPO APP MÓVIL */
    div[data-testid="stRadio"] > div {
        flex-direction: column !important;
        gap: 8px !important;
    }
    
    div[data-testid="stRadio"] label {
        background: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        width: 100% !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
        margin-bottom: 4px !important;
        transition: all 0.15s ease !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        border-color: #15803d !important;
        background-color: #f0fdf4 !important;
    }

    div[data-testid="stRadio"] label span {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }

    /* SEMÁFOROS */
    .traffic-ok {
        background-color: #dcfce7;
        border: 3px solid #16a34a;
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(22, 163, 74, 0.15);
    }
    .traffic-danger {
        background-color: #fee2e2;
        border: 3px solid #dc2626;
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.15);
    }
    .traffic-warning {
        background-color: #fef3c7;
        border: 3px solid #d97706;
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.15);
    }

    .traffic-title {
        font-size: 1.5rem;
        font-weight: 900;
        margin-bottom: 6px;
    }
    .traffic-sub {
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* TARJETAS */
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
        font-size: 0.9rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
    }
    .field-card-value {
        font-size: 1.9rem;
        font-weight: 900;
        color: #0f172a;
        margin-top: 4px;
    }
    .field-card-unit {
        font-size: 1rem;
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

# --- GESTIÓN PERSISTENTE DE ARCHIVOS JSON ---
USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"

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
        st.error(f"Error al guardar datos: {e}")

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
            "Frontón Jaime": {"lat": 42.3659, "lon": -2.4235, "variedad": "Tempranillo", "suelo": "Cascajo / Calcáreo", "ha": 2.0}
        },
        "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}
    }
}

if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = cargar_json(USERS_FILE, DEFAULT_USERS)

if "db_privada" not in st.session_state:
    st.session_state.db_privada = cargar_json(FINCAS_FILE, DEFAULT_FINCAS)

# --- FUNCIÓN DE DISPARO DE WHATSAPP ---
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

# --- AUTENTICACIÓN ---
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if not st.session_state.usuario_autenticado:
    c1, col_login, c2 = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 3.8rem; margin-bottom: 5px;">🚜</div>
            <h1 style="font-size: 2.2rem; font-weight: 900; color: #15803d; margin: 0;">AgroAlert Campo</h1>
            <p style="font-size: 1.1rem; color: #475569; font-weight: 600; margin-top: 6px;">Monitor de campo y bot de alertas diarias por WhatsApp</p>
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
            st.info("💡 **Para recibir alertas:** Envía `I allow callmebot to send me messages` por WhatsApp al `+34 623 91 22 04` para obtener tu APIKey.")
            with st.form("form_reg"):
                nu = st.text_input("Usuario")
                nn = st.text_input("Tu Nombre o Explotación")
                ntel = st.text_input("📱 Teléfono Móvil (con +34)")
                napi = st.text_input("🔑 APIKey de WhatsApp")
                np = st.text_input("Contraseña", type="password")
                
                b_up = st.form_submit_button("🚀 CREAR CUENTA", use_container_width=True, type="primary")
                if b_up:
                    if not nu.strip() or not np.strip() or not ntel.strip():
                        st.error("Por favor, completa los campos requeridos.")
                    elif nu in st.session_state.usuarios_db:
                        st.error("Ese usuario ya existe.")
                    else:
                        st.session_state.usuarios_db[nu] = {
                            "pwd": make_hash(np),
                            "nombre": nn,
                            "telefono": ntel.strip(),
                            "apikey": napi.strip()
                        }
                        st.session_state.db_privada[nu] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}
                        
                        guardar_json(USERS_FILE, st.session_state.usuarios_db)
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        
                        if napi.strip():
                            msg_bienvenida = f"🚜 *¡BIENVENIDO A AGROALERT!*\nHola *{nn}*, tu cuenta ha quedado vinculada."
                            disparar_whatsapp_servidor(ntel.strip(), napi.strip(), msg_bienvenida)
                        
                        st.session_state.usuario_autenticado = nu
                        st.success("¡Cuenta creada con éxito!")
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

fincas_usuario = st.session_state.db_privada.get(user_activo, {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}})

# Selectores superiores
c_top1, c_top2, c_top3 = st.columns([1.2, 1.4, 0.7])
with c_top1:
    tipo_cultivo = st.selectbox("Cultivo:", ["🍇 Viña", "🫒 Olivo", "🌾 Cereal", "🍑 Frutal"])

fincas_del_cultivo = fincas_usuario.get(tipo_cultivo, {})
nombres_disponibles = list(fincas_del_cultivo.keys())

with c_top2:
    if not nombres_disponibles:
        st.selectbox("Parcela:", ["(Sin parcelas)"])
        nombre_parcela = "Sin Parcela Registrada"
        lat, lon, variedad, suelo, superficie_ha = 42.3659, -2.4235, "Tempranillo", "Franco", 2.0
    else:
        seleccion_parcela = st.selectbox("Parcela activa:", nombres_disponibles)
        nombre_parcela = seleccion_parcela
        dp = fincas_del_cultivo[seleccion_parcela]
        lat, lon, variedad, suelo, superficie_ha = dp["lat"], dp["lon"], dp["variedad"], dp["suelo"], dp["ha"]

with c_top3:
    st.write("")
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.usuario_autenticado = None
        st.rerun()

# --- CONSULTA METEOROLÓGICA ---
hoy = datetime.now()
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
# NAVEGACIÓN EN FILAS VERTICALES (RESPONSIVE MÓVIL)
# ==============================================================================
st.markdown("<p style='font-size: 0.95rem; font-weight: 800; color: #64748b; margin-top: 15px; margin-bottom: 6px;'>SECCIONES:</p>", unsafe_allow_html=True)
seccion_activa = st.radio(
    "Navegación:",
    [
        "🚜 ¿PUEDO SULFATAR HOY?",
        "🧪 CUÁNTO ECHAR A LA CUBA",
        "📲 BOT AUTOMÁTICO WHATSAPP",
        "🌾 GESTIÓN DE MIS FINCAS"
    ],
    label_visibility="collapsed"
)

st.write("---")

# ==============================================================================
# SECCIÓN 1: SEMÁFORO DIARIO
# ==============================================================================
if seccion_activa == "🚜 ¿PUEDO SULFATAR HOY?":
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>📍 {nombre_parcela} <span style='font-size:1rem; color:#64748b;'>({superficie_ha} ha | {variedad})</span></h2>", unsafe_allow_html=True)

    if viento_hoy > 15:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-danger">
            <div class="traffic-title" style="color: #991b1b;">⛔ HOY NO SE RECOMIENDA SULFATAR</div>
            <div class="traffic-sub" style="color: #b91c1c;">Viento excesivo ({viento_hoy:.0f} km/h). Vas a perder producto por deriva.</div>
        </div>
        """, unsafe_allow_html=True)
    elif lluvia_hoy > 2.0:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-danger">
            <div class="traffic-title" style="color: #991b1b;">⛔ HOY NO SULFATES</div>
            <div class="traffic-sub" style="color: #b91c1c;">Lluvia prevista ({lluvia_hoy:.1f} L/m²). Se lavará el tratamiento.</div>
        </div>
        """, unsafe_allow_html=True)
    elif max_hoy >= 32:
        semaforo_estado = "AMBAR"
        st.markdown(f"""
        <div class="traffic-warning">
            <div class="traffic-title" style="color: #92400e;">⚠️ TRATAR SOLO TEMPRANO</div>
            <div class="traffic-sub" style="color: #b45309;">Calor fuerte ({max_hoy:.0f} °C). Tratar solo de 7:00 a 11:00.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        semaforo_estado = "VERDE"
        st.markdown(f"""
        <div class="traffic-ok">
            <div class="traffic-title" style="color: #166534;">✅ DÍA PERFECTO PARA SULFATAR</div>
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
            <div class="field-card-title">🛡️ Hongos</div>
            <div class="field-card-value" style="font-size:1.5rem; color: {'#dc2626' if 'ALTO' in riesgo_txt else '#15803d'};">{riesgo_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><h3 style='font-size: 1.3rem; font-weight: 800;'>📅 Previsión Semanal:</h3>", unsafe_allow_html=True)
    df_dias = []
    for i in range(len(fechas_legibles)):
        apto = "✅ Óptimo" if (viento[i] <= 15 and lluvia[i] <= 2.0 and t_max[i] < 32) else ("⛔ No tratar" if (viento[i] > 15 or lluvia[i] > 2.0) else "⚠️ Cuidado")
        df_dias.append({
            "Día": fechas_legibles[i],
            "Tª Min/Max": f"{t_min[i]:.0f}°/{t_max[i]:.0f}°C",
            "Lluvia": f"{lluvia[i]:.1f} L",
            "Viento": f"{viento[i]:.0f} km/h",
            "Estado": apto
        })
    st.dataframe(pd.DataFrame(df_dias), use_container_width=True, hide_index=True)

# ==============================================================================
# SECCIÓN 2: CALCULADORA DE CUBA
# ==============================================================================
elif seccion_activa == "🧪 CUÁNTO ECHAR A LA CUBA":
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>🧪 Calculadora para la Cuba</h2>", unsafe_allow_html=True)
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.markdown("#### 🚜 Maquinaria:")
        litros_cuba = st.selectbox("Capacidad cuba:", [500, 600, 800, 1000, 1500, 2000, 3000], index=3)
        gasto_caldo = st.number_input("Gasto caldo (L/ha):", value=400, step=50)
        ha_a_sulfatar = st.number_input("Hectáreas a tratar:", value=float(superficie_ha), step=0.5)

    with c_c2:
        st.markdown("#### 🏷️ Dosis de Producto:")
        formato_dosis = st.radio("Tipo de dosis:", [
            "Por 100 Litros (gr o cc / 100 L)",
            "Por Hectárea (kg o L / ha)"
        ])
        
        if "100 Litros" in formato_dosis:
            dosis_num = st.number_input("Gramos o cc / 100 L:", value=250.0, step=25.0)
        else:
            dosis_num = st.number_input("Kilos o Litros / ha:", value=2.0, step=0.5)

        precio_kilo = st.number_input("Precio (€ / kg o L):", value=18.0, step=1.0)

    caldo_total_necesario = ha_a_sulfatar * gasto_caldo
    num_cubas_necesarias = caldo_total_necesario / litros_cuba
    ha_por_cuba = litros_cuba / gasto_caldo

    if "100 Litros" in formato_dosis:
        kilos_por_cuba = (dosis_num * (litros_cuba / 100.0)) / 1000.0
        kilos_totales_finca = (dosis_num * (caldo_total_necesario / 100.0)) / 1000.0
    else:
        kilos_por_cuba = dosis_num * ha_por_cuba
        kilos_totales_finca = dosis_num * ha_a_sulfatar

    coste_total_euros = kilos_totales_finca * precio_kilo

    st.markdown(f"""
    <div class="recipe-box">
        <div style="font-size: 1rem; font-weight: 800; color: #065f46; text-transform: uppercase;">📝 RECETA DIRECTA</div>
        <div class="recipe-big">{kilos_por_cuba:.2f} <span style="font-size:1.3rem;">kg/L por CUBA de {litros_cuba} L</span></div>
        <hr style="border: 1px solid #a7f3d0; margin: 12px 0;">
        <div style="font-size: 1.15rem; font-weight: 700; color: #047857;">
            🚜 {ha_a_sulfatar} ha = {num_cubas_necesarias:.1f} cubas ({kilos_totales_finca:.2f} kg/L totales).
        </div>
        <div style="font-size: 1rem; font-weight: 600; color: #065f46; margin-top: 4px;">
            💰 Coste: {coste_total_euros:.2f} € ({(coste_total_euros/ha_a_sulfatar if ha_a_sulfatar>0 else 0):.2f} €/ha).
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# SECCIÓN 3: BOT WHATSAPP
# ==============================================================================
elif seccion_activa == "📲 BOT AUTOMÁTICO WHATSAPP":
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>📲 Bot de Alertas WhatsApp</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.05rem; color: #475569;'>Alertas vinculadas a: <b>{user_telefono}</b> ({nombre_cliente})</p>", unsafe_allow_html=True)

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
# SECCIÓN 4: GESTIÓN DE FINCAS
# ==============================================================================
elif seccion_activa == "🌾 GESTIÓN DE MIS FINCAS":
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #1e293b; margin: 0 0 15px 0;'>🌾 Gestión de Fincas</h2>", unsafe_allow_html=True)
    
    modo_finca = st.radio("Acción en Fincas:", ["✏️ Modificar o Eliminar Finca", "➕ Añadir Nueva Finca"], label_visibility="collapsed")
    
    if modo_finca == "✏️ Modificar o Eliminar Finca":
        fincas_actuales = fincas_usuario.get(tipo_cultivo, {})
        if not fincas_actuales:
            st.info(f"No tienes parcelas registradas en {tipo_cultivo}.")
        else:
            finca_a_editar = st.selectbox("Selecciona la finca a editar:", list(fincas_actuales.keys()))
            datos_f = fincas_actuales[finca_a_editar]
            
            suelos_lista = ["Cascajo / Calcáreo", "Cascajo / Pedregoso", "Arcillo-calcáreo", "Arenoso", "Tierra fuerte"]
            suelo_index = suelos_lista.index(datos_f["suelo"]) if datos_f["suelo"] in suelos_lista else 0
            
            with st.form("form_editar_finca"):
                nuevo_nombre = st.text_input("Nombre finca:", value=finca_a_editar)
                nueva_lat = st.number_input("Latitud:", value=float(datos_f["lat"]), format="%.4f")
                nueva_lon = st.number_input("Longitud:", value=float(datos_f["lon"]), format="%.4f")
                nueva_var = st.text_input("Variedad:", value=datos_f["variedad"])
                nueva_ha = st.number_input("Superficie (ha):", value=float(datos_f["ha"]), min_value=0.1, step=0.5)
                nuevo_suelo = st.selectbox("Suelo:", suelos_lista, index=suelo_index)
                
                c_btn_save, c_btn_del = st.columns(2)
                with c_btn_save:
                    guardar_edicion = st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary")
                with c_btn_del:
                    borrar_finca = st.form_submit_button("🗑️ ELIMINAR FINCA", use_container_width=True)
                
                if guardar_edicion:
                    if nuevo_nombre.strip() != finca_a_editar:
                        del st.session_state.db_privada[user_activo][tipo_cultivo][finca_a_editar]
                    st.session_state.db_privada[user_activo][tipo_cultivo][nuevo_nombre.strip()] = {
                        "lat": nueva_lat, "lon": nueva_lon, "variedad": nueva_var, "suelo": nuevo_suelo, "ha": nueva_ha
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
        with st.form("form_alta_finca"):
            nom_finca = st.text_input("Nombre finca:", value="Parcela Alta")
            lat_finca = st.number_input("Latitud decimal:", value=42.3659, format="%.4f")
            lon_finca = st.number_input("Longitud decimal:", value=-2.4235, format="%.4f")
            var_finca = st.text_input("Variedad:", value="Tempranillo")
            ha_finca = st.number_input("Superficie (ha):", value=2.0, min_value=0.1, step=0.5)
            suelo_finca = st.selectbox("Terreno:", ["Cascajo / Calcáreo", "Cascajo / Pedregoso", "Arcillo-calcáreo", "Arenoso", "Tierra fuerte"])

            btn_guardar_f = st.form_submit_button("💾 CREAR NUEVA PARCELA", use_container_width=True, type="primary")

            if btn_guardar_f and nom_finca.strip():
                st.session_state.db_privada[user_activo][tipo_cultivo][nom_finca.strip()] = {
                    "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca
                }
                guardar_json(FINCAS_FILE, st.session_state.db_privada)
                st.success(f"¡Parcela '{nom_finca}' guardada!")
                st.rerun()

    st.write("---")
    st.markdown("### 📋 Resumen de Parcelas:")
    tabla_fincas = [
        {"Parcela": k, "Hectáreas": v["ha"], "Variedad": v["variedad"], "Terreno": v["suelo"]}
        for k, v in fincas_usuario.get(tipo_cultivo, {}).items()
    ]
    if tabla_fincas:
        st.dataframe(pd.DataFrame(tabla_fincas), use_container_width=True, hide_index=True)
