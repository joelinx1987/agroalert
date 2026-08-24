import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date
import urllib.request
import urllib.parse
import json
import hashlib

st.set_page_config(
    page_title="AgroAlert Pro | Smart Farming Suite",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PROFESIONAL AGTECH ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    .top-badge-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 20px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12);
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
    }
    
    div[data-testid="stRadio"] label {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        width: 100% !important;
        cursor: pointer !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        border-color: #10b981 !important;
        background: #f0fdf4 !important;
        transform: translateY(-2px);
    }

    div[data-testid="stRadio"] label div p {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    .traffic-banner {
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        border-left: 8px solid;
    }
    
    .traffic-green { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-left-color: #059669; color: #064e3b; }
    .traffic-amber { background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-left-color: #d97706; color: #78350f; }
    .traffic-red { background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-left-color: #dc2626; color: #7f1d1d; }

    .traffic-title { font-size: 1.45rem; font-weight: 900; }
    .traffic-sub { font-size: 1.05rem; font-weight: 600; opacity: 0.95; }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 20px 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 14px;
    }
    
    .metric-title { font-size: 0.85rem; font-weight: 800; color: #64748b; text-transform: uppercase; }
    .metric-val { font-size: 2.1rem; font-weight: 900; color: #0f172a; margin-top: 6px; }
    .metric-unit { font-size: 1rem; font-weight: 700; color: #94a3b8; }

    .recipe-card {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        border-radius: 22px;
        padding: 26px;
        color: #ffffff;
        margin-top: 15px;
    }
    
    .recipe-tag {
        background: rgba(255, 255, 255, 0.18);
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 14px;
    }
    
    .recipe-amount { font-size: 2.5rem; font-weight: 900; line-height: 1.1; }

    .guide-card {
        background: #ffffff;
        border: 2px solid #22c55e;
        border-radius: 18px;
        padding: 20px 22px;
        margin-bottom: 22px;
        box-shadow: 0 8px 20px -4px rgba(34, 197, 94, 0.15);
    }

    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 14px 20px !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25) !important;
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

def normalizar_telefono(tel):
    t = tel.replace(" ", "").replace("-", "").replace(".", "")
    if not t.startswith("+"):
        t = "+34" + t if not t.startswith("34") else "+" + t
    return t

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

def render_google_map(latitud, longitud, zoom=16, height=380):
    gmaps_url = f"https://maps.google.com/maps?q={latitud},{longitud}&hl=es&z={zoom}&t=k&output=embed"
    iframe_html = f"""
    <div style="border-radius: 20px; overflow: hidden; border: 2px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.08);">
        <iframe width="100%" height="{height}" src="{gmaps_url}" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"></iframe>
    </div>
    """
    components.html(iframe_html, height=height + 10)

def render_copy_box(texto_a_copiar):
    html_code = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: #f1f5f9; border: 1.5px solid #cbd5e1; border-radius: 12px; padding: 10px 14px; margin: 8px 0 12px 0;">
        <span id="target-text" style="font-style: italic; font-size: 1rem; color: #0f172a; font-weight: 600;">{texto_a_copiar}</span>
        <button onclick="copiarAlPortapapeles()" style="background: #10b981; color: #ffffff; border: none; border-radius: 8px; padding: 6px 12px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: background 0.2s;">
            <span id="btn-label">📋 Copiar texto</span>
        </button>
    </div>
    <script>
    function copiarAlPortapapeles() {{
        const text = "{texto_a_copiar}";
        navigator.clipboard.writeText(text).then(function() {{
            document.getElementById('btn-label').innerText = '✅ ¡Copiado!';
            setTimeout(function() {{
                document.getElementById('btn-label').innerText = '📋 Copiar texto';
            }}, 2500);
        }});
    }}
    </script>
    """
    components.html(html_code, height=62)

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
        num_limpio = normalizar_telefono(telefono)
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

# --- ACCESO / REGISTRO ---
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if not st.session_state.usuario_autenticado:
    c1, col_login, c2 = st.columns([1, 1.9, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 3.6rem; margin-bottom: 6px;">🌱</div>
            <h1 style="font-size: 2.3rem; font-weight: 900; color: #0f172a; margin: 0;">AgroAlert Pro</h1>
            <p style="font-size: 1.1rem; color: #64748b; font-weight: 600; margin-top: 4px;">Suite Agrícola y Bot de Avisos por WhatsApp</p>
        </div>
        """, unsafe_allow_html=True)

        modo_acceso = st.radio("Acceso:", ["🔑 Iniciar Sesión", "📝 Registrar Explotación y Activar Bot"], label_visibility="collapsed")
        st.session_state.usuarios_db = cargar_json(USERS_FILE, DEFAULT_USERS)
        
        if "Iniciar Sesión" in modo_acceso:
            with st.form("form_auth"):
                u = st.text_input("Usuario", value="admin").strip().lower()
                p = st.text_input("Contraseña", type="password", value="admin123")
                b_in = st.form_submit_button("🚜 ENTRAR AL PANEL DE CAMPO", use_container_width=True)
                if b_in:
                    usuarios_lower = {k.lower(): (k, v) for k, v in st.session_state.usuarios_db.items()}
                    if u in usuarios_lower and check_hash(p, usuarios_lower[u][1]["pwd"]):
                        st.session_state.usuario_autenticado = usuarios_lower[u][0]
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        else:
            # TARJETA CON INSTRUCCIONES CLARAS, NÚMERO Y BOTÓN DE COPIADO
            st.markdown("""
            <div class="guide-card">
                <div style="font-size: 1.1rem; font-weight: 900; color: #15803d; margin-bottom: 8px;">
                    🔑 CÓMO OBTENER TU APIKEY (PASO A PASO):
                </div>
                <div style="font-size: 0.95rem; color: #334155; line-height: 1.55;">
                    <b>1.</b> Abre un chat en WhatsApp con el número oficial del bot: 
                    <span style="background: #e2e8f0; color: #0f172a; font-weight: 800; padding: 2px 8px; border-radius: 6px;">+34 623 91 22 04</span><br>
                    <b>2.</b> Envía este mensaje exacto:
                </div>
            </div>
            """, unsafe_allow_html=True)

            render_copy_box("I allow callmebot to send me messages")

            st.markdown("""
            <div style="margin-top: -10px; margin-bottom: 16px;">
                <a href="https://api.whatsapp.com/send?phone=34623912204&text=I%20allow%20callmebot%20to%20send%20me%20messages" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #22c55e; color: #ffffff; text-align: center; padding: 12px; border-radius: 12px; font-weight: 800; font-size: 1rem; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);">
                        📲 TOCAR AQUÍ PARA ABRIR WHATSAPP AUTOMÁTICAMENTE
                    </div>
                </a>
                <p style="font-size: 0.88rem; color: #64748b; margin-top: 8px; text-align: center;">
                    <b>3.</b> El bot te contestará con tu número de <b>apikey</b>. Pégalo a continuación:
                </p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("form_reg"):
                nu = st.text_input("Usuario (ej: jgarcia)").strip()
                nn = st.text_input("Nombre de Explotación (ej: Bodega San Juan)").strip()
                ntel = st.text_input("📱 Teléfono Móvil (ej: +34 612 34 56 78)").strip()
                napi = st.text_input("🔑 APIKey WhatsApp (el código numérico que te respondió el bot)").strip()
                np = st.text_input("Contraseña", type="password")
                
                b_up = st.form_submit_button("🚀 CREAR CUENTA Y ENTRAR", use_container_width=True)
                if b_up:
                    nu_clean = nu.lower()
                    tel_clean = normalizar_telefono(ntel) if ntel else ""
                    
                    if not nu_clean or not np.strip() or not ntel or not napi:
                        st.error("Por favor, rellena todos los campos incluyendo la APIKey de WhatsApp.")
                    elif any(k.lower() == nu_clean for k in st.session_state.usuarios_db.keys()):
                        st.error(f"El usuario '{nu}' ya existe.")
                    elif any(normalizar_telefono(u_data.get("telefono", "")) == tel_clean for u_data in st.session_state.usuarios_db.values() if u_data.get("telefono")):
                        st.error(f"El teléfono '{ntel}' ya está registrado.")
                    else:
                        st.session_state.usuarios_db[nu] = {
                            "pwd": make_hash(np),
                            "nombre": nn if nn else nu,
                            "telefono": tel_clean,
                            "apikey": napi
                        }
                        if nu not in st.session_state.db_privada:
                            st.session_state.db_privada[nu] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}
                        
                        guardar_json(USERS_FILE, st.session_state.usuarios_db)
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        
                        msg = f"🚜 *¡BIENVENIDO A AGROALERT PRO!*\nHola *{nn}*, tu explotación ha sido activada y vinculada a este móvil."
                        disparar_whatsapp_servidor(tel_clean, napi, msg)
                        
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

st.markdown(f"""
<div class="top-badge-container">
    <div>
        <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; color: #10b981; font-weight: 800;">EXPLOTACIÓN AGRÍCOLA</div>
        <div style="font-size: 1.5rem; font-weight: 900; letter-spacing: -0.02em;">{nombre_cliente}</div>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 6px 14px; border-radius: 9999px; font-weight: 800; font-size: 0.85rem;">● SISTEMA CONECTADO</span>
    </div>
</div>
""", unsafe_allow_html=True)

c_top1, c_top2, c_top3 = st.columns([1.2, 1.4, 0.7])
with c_top1:
    tipo_cultivo = st.selectbox("Cultivo activo:", ["🍇 Viña", "🫒 Olivo", "🌾 Cereal", "🍑 Frutal"])

if tipo_cultivo not in fincas_usuario:
    fincas_usuario[tipo_cultivo] = {}

fincas_del_cultivo = fincas_usuario.get(tipo_cultivo, {})
nombres_disponibles = list(fincas_del_cultivo.keys())

with c_top2:
    if not nombres_disponibles:
        st.selectbox("Parcela activa:", ["⚠️ Sin parcelas registradas"])
        nombre_parcela = "Sin Parcela"
        lat, lon, variedad, suelo, superficie_ha = 42.4658, -2.4499, "Tempranillo", "Franco", 1.0
        poligono, parcela_cat, riego_tipo = "-", "-", "Secano"
    else:
        seleccion_parcela = st.selectbox("Parcela activa:", nombres_disponibles)
        nombre_parcela = seleccion_parcela
        dp = fincas_del_cultivo[seleccion_parcela]
        lat, lon, variedad, suelo, superficie_ha = dp["lat"], dp["lon"], dp.get("variedad", "Tempranillo"), dp["suelo"], dp["ha"]
        poligono = dp.get("poligono", "-")
        parcela_cat = dp.get("parcela", "-")
        riego_tipo = dp.get("riego", "Secano")

with c_top3:
    st.write("")
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.usuario_autenticado = None
        st.rerun()

# --- METEOROLOGÍA ---
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

# --- MENÚ TÁCTIL ---
st.markdown("<p style='font-size: 0.85rem; font-weight: 800; color: #94a3b8; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 15px; margin-bottom: 8px;'>MÓDULOS ACTIVOS:</p>", unsafe_allow_html=True)

opciones_menu = [
    "🚜 Semáforo y Previsión de Tratamiento",
    "🧪 Calculadora de Mezcla y Depósito",
    "📋 Cuaderno Oficial de Fitosanitarios",
    "🌾 Control de Labores y Rendimientos",
    "📲 Centro de Alertas y WhatsApp Bot",
    "🗺️ Gestión de Fincas y Visor Satelital"
]

if user_activo == "admin":
    opciones_menu.append("🛠️ Panel de Control Administrador")

seccion_activa = st.radio("Navegación:", opciones_menu, label_visibility="collapsed")
st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 1. SEMÁFORO
# ==============================================================================
if "Semáforo y Previsión" in seccion_activa:
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px;">
        <h2 style="font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0;">📍 {nombre_parcela}</h2>
        <span style="font-size: 1rem; color: #64748b; font-weight: 700;">{superficie_ha} ha | {variedad}</span>
    </div>
    """, unsafe_allow_html=True)

    if viento_hoy > 15:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-banner traffic-red">
            <div class="traffic-title">⛔ TRATAMIENTO DESACONSEJADO HOY</div>
            <div class="traffic-sub">Viento excesivo ({viento_hoy:.0f} km/h). Límite técnico 15 km/h para evitar deriva foliar.</div>
        </div>
        """, unsafe_allow_html=True)
    elif lluvia_hoy > 2.0:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-banner traffic-red">
            <div class="traffic-title">⛔ RIESGO DE LAVADO POR LLUVIA</div>
            <div class="traffic-sub">Previsión de {lluvia_hoy:.1f} L/m² de precipitación. El producto no fijará en la hoja.</div>
        </div>
        """, unsafe_allow_html=True)
    elif max_hoy >= 32:
        semaforo_estado = "AMBAR"
        st.markdown(f"""
        <div class="traffic-banner traffic-amber">
            <div class="traffic-title">⚠️ VENTANA DE APLICACIÓN TEMPRANA</div>
            <div class="traffic-sub">Temperaturas de {max_hoy:.0f} °C. Trata únicamente de 7:00 a 11:00 para evitar fitotoxicidad.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        semaforo_estado = "VERDE"
        st.markdown(f"""
        <div class="traffic-banner traffic-green">
            <div class="traffic-title">✅ VENTANA DE TRATAMIENTO ÓPTIMA</div>
            <div class="traffic-sub">Viento en calma ({viento_hoy:.0f} km/h), sin lluvia y temperatura ideal ({max_hoy:.0f} °C).</div>
        </div>
        """, unsafe_allow_html=True)

    if "Viña" in tipo_cultivo:
        riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and temp_media_hoy >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ BAJO")
    else:
        riesgo_txt = "🚨 ATENCIÓN" if lluvia_hoy >= 5 else "✅ BAJO"

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🌡️ Tª Hoy</div>
            <div class="metric-val">{min_hoy:.0f}° / {max_hoy:.0f}° <span class="metric-unit">C</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💨 Viento</div>
            <div class="metric-val">{viento_hoy:.0f} <span class="metric-unit">km/h</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🌧️ Lluvia</div>
            <div class="metric-val">{lluvia_hoy:.1f} <span class="metric-unit">L</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m4:
        color_r = '#dc2626' if 'ALTO' in riesgo_txt or 'ATENCIÓN' in riesgo_txt else ('#d97706' if 'Oídio' in riesgo_txt else '#059669')
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🛡️ Riesgo Fitosanitario</div>
            <div class="metric-val" style="font-size:1.45rem; color: {color_r};">{riesgo_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<h3 style='font-size: 1.25rem; font-weight: 800; margin-top: 15px;'>📅 Previsión de Tratabilidad (7 Días):</h3>", unsafe_allow_html=True)
    df_dias = []
    for i in range(len(fechas_legibles)):
        apto = "✅ Óptimo" if (viento[i] <= 15 and lluvia[i] <= 2.0 and t_max[i] < 32) else ("⛔ No tratar" if (viento[i] > 15 or lluvia[i] > 2.0) else "⚠️ Precaución")
        df_dias.append({
            "Día": fechas_legibles[i],
            "Tª Min/Max": f"{t_min[i]:.0f}° / {t_max[i]:.0f}°C",
            "Lluvia": f"{lluvia[i]:.1f} L",
            "Viento": f"{viento[i]:.0f} km/h",
            "Estado": apto
        })
    st.dataframe(pd.DataFrame(df_dias), use_container_width=True, hide_index=True)

# ==============================================================================
# 2. CALCULADORA
# ==============================================================================
elif "Calculadora de Mezcla" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0 0 15px 0;'>🧪 Dosificación y Calibración de Depósito</h2>", unsafe_allow_html=True)
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.markdown("#### 🚜 Maquinaria:")
        litros_cuba = st.selectbox("Capacidad depósito/cuba (L):", [500, 600, 800, 1000, 1500, 2000, 3000], index=3)
        gasto_caldo = st.number_input("Gasto de caldo por ha (L/ha):", value=400, step=50)
        ha_a_sulfatar = st.number_input("Superficie a tratar (ha):", value=float(superficie_ha), step=0.5)

    with c_c2:
        st.markdown("#### 🏷️ Producto y Dosis:")
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
    <div class="recipe-card">
        <div class="recipe-tag">Orden de Mezcla Directa</div>
        <div class="recipe-amount">{kilos_por_cuba:.2f} <span style="font-size: 1.4rem; font-weight: 700; opacity: 0.9;">kg o Litros por depósito lleno ({litros_cuba} L)</span></div>
        <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 18px 0;">
        <div style="font-size: 1.15rem; font-weight: 700;">
            🚜 Para <b>{ha_a_sulfatar} ha</b> necesitas <b>{num_cubas_necesarias:.1f} depósitos</b> ({kilos_totales_finca:.2f} kg/L totales).
        </div>
        <div style="font-size: 1rem; font-weight: 600; opacity: 0.9; margin-top: 6px;">
            💰 Inversión estimada: <b>{coste_total_euros:.2f} €</b> ({(coste_total_euros/ha_a_sulfatar if ha_a_sulfatar>0 else 0):.2f} €/ha).
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. CUADERNO DE FITOSANITARIOS
# ==============================================================================
elif "Cuaderno Oficial" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0 0 15px 0;'>📋 Registro Oficial de Fitosanitarios</h2>", unsafe_allow_html=True)
    
    with st.form("form_fito"):
        st.markdown("#### ➕ Registrar Aplicación:")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            fecha_fito = st.date_input("Fecha:", date.today())
            plaga_tratada = st.text_input("Plaga / Justificación:", value="Mildiu")
            producto_fito = st.text_input("Producto / Materia Activa:", value="Oxicloruro de Cobre 50%")
            num_mapa = st.text_input("Nº Registro MAPA:", value="ES-00123")
        with c_f2:
            dosis_fito = st.text_input("Dosis aplicada:", value="2.5 kg/ha")
            caldo_gastado = st.number_input("Gasto de caldo (L):", value=800, step=100)
            plazo_seg = st.number_input("Plazo de Seguridad (días):", value=14, step=1)
            aplicador_fito = st.text_input("Aplicador / Carnet:", value=nombre_cliente)

        b_guardar_fito = st.form_submit_button("💾 GUARDAR EN EL CUADERNO", use_container_width=True)

        if b_guardar_fito and producto_fito.strip():
            if user_activo not in st.session_state.fitos_db:
                st.session_state.fitos_db[user_activo] = []
            
            reg = {
                "Fecha": str(fecha_fito),
                "Cultivo": tipo_cultivo,
                "Parcela": nombre_parcela,
                "Plaga": plaga_tratada,
                "Producto": producto_fito,
                "Nº MAPA": num_mapa,
                "Dosis": dosis_fito,
                "Caldo (L)": caldo_gastado,
                "Plazo Seg.": f"{plazo_seg} días",
                "Aplicador": aplicador_fito
            }
            st.session_state.fitos_db[user_activo].append(reg)
            guardar_json(FITOS_FILE, st.session_state.fitos_db)
            st.success("¡Tratamiento guardado permanentemente!")
            st.rerun()

    st.markdown("<br><h3 style='font-size: 1.25rem; font-weight: 800;'>📜 Historial de Aplicaciones:</h3>", unsafe_allow_html=True)
    hist_fitos = st.session_state.fitos_db.get(user_activo, [])
    if hist_fitos:
        st.dataframe(pd.DataFrame(hist_fitos), use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros de tratamiento aún.")

# ==============================================================================
# 4. LABORES Y RENDIMIENTOS
# ==============================================================================
elif "Control de Labores" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0 0 15px 0;'>🌾 Labores y Liquidaciones de Cosecha</h2>", unsafe_allow_html=True)
    sub_lab1, sub_lab2 = st.tabs(["🚜 REGISTRAR LABOR / RIEGO", "🍇 REGISTRAR COSECHA / VENTA"])
    
    with sub_lab1:
        with st.form("form_labor"):
            c_l1, c_l2 = st.columns(2)
            with c_l1:
                fecha_lab = st.date_input("Fecha labor:", date.today())
                tipo_labor = st.selectbox("Tipo de labor:", ["Poda", "Pase de grada / Chisel", "Desniete / Espergura", "Abonado de fondo", "Riego", "Herbicida"])
                horas_maq = st.number_input("Horas tractor:", value=4.0, step=0.5)
            with c_l2:
                abono_aporte = st.text_input("Abono / Aporte:", value="NPK 15-15-15 (200 kg)")
                gasoil_litros = st.number_input("Gasoil gastado (L):", value=30.0, step=5.0)
                coste_mano_obra = st.number_input("Coste mano de obra (€):", value=60.0, step=10.0)

            b_guarda_labor = st.form_submit_button("💾 GUARDAR LABOR", use_container_width=True)
            if b_guarda_labor:
                if user_activo not in st.session_state.labores_db:
                    st.session_state.labores_db[user_activo] = {"labores": [], "cosechas": []}
                
                reg_l = {
                    "Fecha": str(fecha_lab), "Cultivo": tipo_cultivo, "Parcela": nombre_parcela,
                    "Labor": tipo_labor, "Horas": horas_maq, "Aporte": abono_aporte, "Gasoil (L)": gasoil_litros, "Coste (€)": coste_mano_obra
                }
                st.session_state.labores_db[user_activo]["labores"].append(reg_l)
                guardar_json(LABORES_FILE, st.session_state.labores_db)
                st.success("¡Labor guardada!")
                st.rerun()

    with sub_lab2:
        with st.form("form_cosecha"):
            c_cos1, c_cos2 = st.columns(2)
            with c_cos1:
                fecha_cos = st.date_input("Fecha recolección:", date.today())
                kilos_totales = st.number_input("Kilos totales cosechados:", value=12000.0, step=500.0)
                calidad_param = st.text_input("Calidad / Grado:", value="13.8° Baumé")
            with c_cos2:
                comprador_dest = st.text_input("Comprador / Bodega:", value="Cooperativa")
                precio_kilo_venta = st.number_input("Precio (€/kg):", value=0.65, step=0.05, format="%.3f")
            
            ingreso_bruto = kilos_totales * precio_kilo_venta
            rendimiento_ha = kilos_totales / superficie_ha if superficie_ha > 0 else 0
            
            st.info(f"📊 Rendimiento: **{rendimiento_ha:.0f} kg/ha** | Liquidación total: **{ingreso_bruto:.2f} €**")

            b_guarda_cosecha = st.form_submit_button("💾 GUARDAR COSECHA", use_container_width=True)
            if b_guarda_cosecha:
                if user_activo not in st.session_state.labores_db:
                    st.session_state.labores_db[user_activo] = {"labores": [], "cosechas": []}
                
                reg_c = {
                    "Fecha": str(fecha_cos), "Cultivo": tipo_cultivo, "Parcela": nombre_parcela,
                    "Kilos": kilos_totales, "kg/ha": round(rendimiento_ha, 1), "Calidad": calidad_param,
                    "Comprador": comprador_dest, "Precio (€/kg)": precio_kilo_venta, "Total (€)": round(ingreso_bruto, 2)
                }
                st.session_state.labores_db[user_activo]["cosechas"].append(reg_c)
                guardar_json(LABORES_FILE, st.session_state.labores_db)
                st.success("¡Cosecha guardada!")
                st.rerun()

    st.markdown("<br><h3 style='font-size: 1.25rem; font-weight: 800;'>📋 Resumen Histórico:</h3>", unsafe_allow_html=True)
    datos_lab_all = st.session_state.labores_db.get(user_activo, {"labores": [], "cosechas": []})
    c_tabl1, c_tabl2 = st.columns(2)
    with c_tabl1:
        st.markdown("#### 🚜 Labores:")
        if datos_lab_all.get("labores"):
            st.dataframe(pd.DataFrame(datos_lab_all["labores"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Sin labores aún.")
    with c_tabl2:
        st.markdown("#### 🍇 Cosechas:")
        if datos_lab_all.get("cosechas"):
            st.dataframe(pd.DataFrame(datos_lab_all["cosechas"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Sin cosechas aún.")

# ==============================================================================
# 5. BOT WHATSAPP
# ==============================================================================
elif "Centro de Alertas" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0 0 15px 0;'>📲 Centro de Disparos WhatsApp</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.05rem; color: #64748b;'>Teléfono receptor: <b>{user_telefono}</b> ({nombre_cliente})</p>", unsafe_allow_html=True)

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

    c_w1, c_w2 = st.columns(2)
    with c_w1:
        if st.button("📲 ENVIAR PARTE MATUTINO AHORA", use_container_width=True):
            if not user_apikey:
                st.error("Configura tu APIKey de WhatsApp.")
            else:
                ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg_parte)
                if ok:
                    st.success(res)
                else:
                    st.error(res)
    with c_w2:
        if st.button("🚨 DISPARAR ALERTA DE HELADA", use_container_width=True):
            if not user_apikey:
                st.error("Configura tu APIKey de WhatsApp.")
            else:
                ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg_helada)
                if ok:
                    st.warning("¡Alerta enviada!")
                else:
                    st.error(res)

# ==============================================================================
# 6. GESTIÓN DE FINCAS Y SATÉLITE
# ==============================================================================
elif "Gestión de Fincas" in seccion_activa:
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #0f172a; margin: 0 0 15px 0;'>🗺️ Gestión Catastral y Satélite ({tipo_cultivo})</h2>", unsafe_allow_html=True)
    
    fincas_actuales = fincas_usuario.get(tipo_cultivo, {})
    
    if not fincas_actuales:
        st.info(f"👉 No tienes ninguna finca en **{tipo_cultivo}**. Rellena los datos para crear la primera:")
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

            btn_crear_primera = st.form_submit_button("💾 CREAR Y GUARDAR ESTA PARCELA", use_container_width=True)

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
                st.success(f"¡Parcela '{nom_finca}' guardada!")
                st.rerun()

    else:
        modo_finca = st.radio("Acción:", ["✏️ Modificar o Ver Satélite", "➕ Añadir Nueva Parcela"], label_visibility="collapsed")
        
        if "Modificar" in modo_finca:
            finca_a_editar = st.selectbox("Selecciona la finca a editar / ver satélite:", list(fincas_actuales.keys()))
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
                    nueva_var = st.text_input("Variedad:", value=datos_f.get("variedad", "Tempranillo"))
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
                    guardar_edicion = st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True)
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

            st.markdown(f"#### 🛰️ Vista Satelital de: **{finca_a_editar}**")
            url_gmaps_app = f"https://www.google.com/maps/search/?api=1&query={datos_f['lat']},{datos_f['lon']}"
            st.markdown(f"""
            <a href="{url_gmaps_app}" target="_blank" style="text-decoration: none;">
                <div style="background-color: #1e293b; color: #ffffff; text-align: center; padding: 10px; border-radius: 12px; font-weight: 800; font-size: 0.95rem; margin-bottom: 12px;">
                    🚗 ABRIR EN APP DE GOOGLE MAPS (GPS)
                </div>
            </a>
            """, unsafe_allow_html=True)
            render_google_map(datos_f["lat"], datos_f["lon"], zoom=16, height=360)

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

                btn_guardar_f = st.form_submit_button("💾 CREAR NUEVA PARCELA", use_container_width=True)

                if btn_guardar_f and nom_finca.strip():
                    st.session_state.db_privada[user_activo][tipo_cultivo][nom_finca.strip()] = {
                        "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca,
                        "poligono": pol_finca, "parcela": parc_finca, "riego": riego_finca
                    }
                    guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.success(f"¡Parcela '{nom_finca}' guardada!")
                    st.rerun()

        st.markdown("<br><h3 style='font-size: 1.25rem; font-weight: 800;'>📋 Resumen de Parcelas:</h3>", unsafe_allow_html=True)
        tabla_fincas = [
            {
                "Parcela": k,
                "Hectáreas": v["ha"],
                "Variedad": v.get("variedad", "-"),
                "Polígono": v.get("poligono", "-"),
                "Parcela SIGPAC": v.get("parcela", "-"),
                "Riego": v.get("riego", "Secano"),
                "Terreno": v["suelo"]
            }
            for k, v in fincas_usuario.get(tipo_cultivo, {}).items()
        ]
        if tabla_fincas:
            st.dataframe(pd.DataFrame(tabla_fincas), use_container_width=True, hide_index=True)

# ==============================================================================
# 7. PANEL ADMINISTRADOR
# ==============================================================================
elif "Panel de Control Administrador" in seccion_activa and user_activo == "admin":
    st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: #991b1b; margin: 0 0 15px 0;'>🛠️ Panel de Control y Borrado de Usuarios</h2>", unsafe_allow_html=True)
    
    st.session_state.usuarios_db = cargar_json(USERS_FILE, DEFAULT_USERS)
    todos_los_usuarios = list(st.session_state.usuarios_db.keys())
    usuarios_borrables = [u for u in todos_los_usuarios if u != "admin"]
    
    if not usuarios_borrables:
        st.info("No hay otros usuarios registrados en el sistema.")
    else:
        st.markdown("#### 🗑️ Eliminar una cuenta de usuario:")
        usuario_a_borrar = st.selectbox("Selecciona el usuario que quieres eliminar:", usuarios_borrables)
        datos_u_borrar = st.session_state.usuarios_db[usuario_a_borrar]
        
        st.warning(f"⚠️ Vas a eliminar a **{usuario_a_borrar}** ({datos_u_borrar.get('nombre', '')} | Tel: {datos_u_borrar.get('telefono', '')}).")
        
        if st.button(f"❌ CONFIRMAR Y ELIMINAR A '{usuario_a_borrar}'", type="primary"):
            del st.session_state.usuarios_db[usuario_a_borrar]
            guardar_json(USERS_FILE, st.session_state.usuarios_db)
            
            if usuario_a_borrar in st.session_state.db_privada:
                del st.session_state.db_privada[usuario_a_borrar]
                guardar_json(FINCAS_FILE, st.session_state.db_privada)
                
            if usuario_a_borrar in st.session_state.fitos_db:
                del st.session_state.fitos_db[usuario_a_borrar]
                guardar_json(FITOS_FILE, st.session_state.fitos_db)
                
            if usuario_a_borrar in st.session_state.labores_db:
                del st.session_state.labores_db[usuario_a_borrar]
                guardar_json(LABORES_FILE, st.session_state.labores_db)
                
            st.success(f"¡Usuario '{usuario_a_borrar}' eliminado!")
            st.rerun()

    st.markdown("<br><h3 style='font-size: 1.25rem; font-weight: 800;'>👥 Cuentas Registradas:</h3>", unsafe_allow_html=True)
    resumen_users = [
        {"Usuario": k, "Nombre / Explotación": v.get("nombre", ""), "Teléfono": v.get("telefono", ""), "Tiene APIKey": "✅ Sí" if v.get("apikey") else "❌ No"}
        for k, v in st.session_state.usuarios_db.items()
    ]
    st.dataframe(pd.DataFrame(resumen_users), use_container_width=True, hide_index=True)
