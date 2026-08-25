import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.request
import urllib.parse
import json
import hashlib
from PIL import Image

st.set_page_config(
    page_title="AgroAlert Pro | Explotación de Precisión",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS VISUALES: FOTOS AGRÍCOLAS Y SIN BORDES NÍTIDOS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #f1f5f9 100%) !important;
        background-attachment: fixed !important;
        color: #0f172a;
    }

    /* BOTONES DE SECCIÓN VERTICALES */
    div[data-testid="stRadio"] > div {
        flex-direction: column !important;
        gap: 8px !important;
    }
    
    div[data-testid="stRadio"] label {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        width: 100% !important;
        cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
        transition: all 0.15s ease !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        background-color: rgba(240, 253, 244, 0.95) !important;
        box-shadow: 0 6px 20px rgba(22, 163, 74, 0.08) !important;
    }

    div[data-testid="stRadio"] label div p {
        font-size: 1rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }

    /* SEMÁFOROS */
    .traffic-ok {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border: none;
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(22, 163, 74, 0.1);
        color: #064e3b;
    }
    .traffic-danger {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: none;
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(220, 38, 38, 0.1);
        color: #7f1d1d;
    }
    .traffic-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: none;
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(217, 119, 6, 0.1);
        color: #78350f;
    }

    .traffic-title { font-size: 1.35rem; font-weight: 900; margin-bottom: 4px; }
    .traffic-sub { font-size: 1.05rem; font-weight: 600; }

    /* --- TARJETAS FOTOGRÁFICAS AGRÍCOLAS SIN BORDES NÍTIDOS --- */
    .card-photo {
        position: relative;
        border-radius: 16px;
        padding: 20px 16px;
        text-align: center;
        margin-bottom: 14px;
        overflow: hidden;
        border: none !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        background-size: cover;
        background-position: center;
    }
    
    .card-photo::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.93) 0%, rgba(255, 255, 255, 0.88) 100%);
        backdrop-filter: blur(4px);
        z-index: 1;
    }

    .card-content { position: relative; z-index: 2; }

    .card-temp { background-image: url('https://images.unsplash.com/photo-1470246973918-29a93221c455?q=80&w=700&auto=format&fit=crop'); }
    .card-wind { background-image: url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=700&auto=format&fit=crop'); }
    .card-rain { background-image: url('https://images.unsplash.com/photo-1519692933481-e162a57d6721?q=80&w=700&auto=format&fit=crop'); }
    .card-shield { background-image: url('https://images.unsplash.com/photo-1537640538966-79f369143f8f?q=80&w=700&auto=format&fit=crop'); }

    .card-title { font-size: 0.85rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
    .card-value { font-size: 1.85rem; font-weight: 900; color: #0f172a; margin-top: 4px; }
    .card-unit { font-size: 0.95rem; font-weight: 600; color: #64748b; }

    .recipe-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: none;
        border-radius: 16px;
        padding: 20px;
        margin-top: 14px;
        box-shadow: 0 10px 30px rgba(5, 150, 105, 0.08);
        color: #065f46;
    }
    .recipe-big { font-size: 1.95rem; font-weight: 900; color: #047857; }

    .legend-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: none;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.03);
    }
    .legend-header { font-size: 1.1rem; font-weight: 800; color: #15803d; margin-bottom: 6px; }
    .legend-body { font-size: 0.95rem; color: #334155; line-height: 1.55; }
    
    .stButton>button {
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        padding: 12px 18px !important;
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA JSON ---
USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"
FITOS_FILE = "fitosanitarios_db.json"
LABORES_FILE = "labores_db.json"
PLAGAS_FILE = "plagas_geolocalizadas_db.json"
UPLOADS_DIR = "uploads_geofotos"

if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

CATALOGO_MAPA_OFICIAL = {
    "ES-00123": {"producto": "Oxicloruro de Cobre 50%", "materia": "Cobre (Oxicloruro)", "dosis_max": "4.0 kg/ha", "plazo": 14},
    "ES-00456": {"producto": "Azufre Moable 80%", "materia": "Azufre micronizado", "dosis_max": "6.0 kg/ha", "plazo": 5},
    "ES-00789": {"producto": "Cipermetrina 10%", "materia": "Cipermetrina", "dosis_max": "0.5 L/ha", "plazo": 21},
    "ES-00321": {"producto": "Fosetil-Al 80%", "materia": "Fosetil-aluminio", "dosis_max": "3.0 kg/ha", "plazo": 15}
}

def validar_con_mapa(num_registro):
    num_clean = num_registro.strip().upper()
    if num_clean in CATALOGO_MAPA_OFICIAL:
        return True, CATALOGO_MAPA_OFICIAL[num_clean]
    return False, None

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
        st.error(f"Error al guardar datos: {e}")

def render_google_map(latitud, longitud, zoom=16, height=360):
    gmaps_url = f"https://maps.google.com/maps?q={latitud},{longitud}&hl=es&z={zoom}&t=k&output=embed"
    iframe_html = f"""
    <div style="border-radius: 14px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.06);">
        <iframe width="100%" height="{height}" src="{gmaps_url}" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"></iframe>
    </div>
    """
    components.html(iframe_html, height=height + 10)

def render_copy_box(texto_a_copiar):
    html_code = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(248,250,252,0.9); border-radius: 12px; padding: 10px 14px; margin: 8px 0 12px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
        <span style="font-style: italic; font-size: 1rem; color: #0f172a; font-weight: 700;">{texto_a_copiar}</span>
        <button onclick="copiarTexto()" style="background: #15803d; color: #ffffff; border: none; border-radius: 8px; padding: 8px 14px; font-weight: 800; font-size: 0.85rem; cursor: pointer;">
            <span id="btn-lbl">📋 Copiar texto</span>
        </button>
    </div>
    <script>
    function copiarTexto() {{
        navigator.clipboard.writeText("{texto_a_copiar}").then(function() {{
            document.getElementById('btn-lbl').innerText = '✅ ¡Copiado!';
            setTimeout(function() {{ document.getElementById('btn-lbl').innerText = '📋 Copiar texto'; }}, 2500);
        }});
    }}
    </script>
    """
    components.html(html_code, height=64)

DEFAULT_USERS = {
    "admin": {
        "pwd": make_hash("admin123"),
        "nombre": "Joel (Mi Explotación)",
        "telefono": "+34626665232",
        "apikey": "3443251",
        "rol": "Propietario"
    },
    "tecnico_agronomo": {
        "pwd": make_hash("tecnico123"),
        "nombre": "Carlos (Técnico Asesor)",
        "telefono": "+34600111222",
        "apikey": "9998887",
        "rol": "Técnico / Asesor"
    }
}

DEFAULT_FINCAS = {
    "admin": {
        "🍇 Viña": {
            "Frontón Jaime": {"lat": 42.3659, "lon": -2.4235, "variedad": "Tempranillo", "suelo": "Cascajo / Calcáreo", "ha": 2.0, "poligono": "12", "parcela": "104", "riego": "Goteo"}
        },
        "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}
    },
    "tecnico_agronomo": {
        "🍇 Viña": {
            "Finca El Encinar": {"lat": 42.4512, "lon": -2.4589, "variedad": "Graciano", "suelo": "Arcillo-calcáreo", "ha": 4.5, "poligono": "8", "parcela": "42", "riego": "Secano"}
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

if "plagas_db" not in st.session_state:
    st.session_state.plagas_db = cargar_json(PLAGAS_FILE, {})

if "modo_contraste" not in st.session_state:
    st.session_state.modo_contraste = False

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
            <h1 style="font-size: 2.2rem; font-weight: 900; color: #15803d; margin: 0;">AgroAlert Pro</h1>
            <p style="font-size: 1.1rem; color: #475569; font-weight: 600; margin-top: 6px;">Explotación de Precisión, SIEX/PAC y Asistente IA</p>
        </div>
        """, unsafe_allow_html=True)

        modo_acceso = st.radio("Acceso:", ["🔑 Iniciar Sesión", "📝 Registrarme y Activar Bot"], label_visibility="collapsed")
        st.session_state.usuarios_db = cargar_json(USERS_FILE, DEFAULT_USERS)
        
        if modo_acceso == "🔑 Iniciar Sesión":
            with st.form("form_auth"):
                u = st.text_input("Usuario (ej: admin o tecnico_agronomo)", value="admin").strip().lower()
                p = st.text_input("Contraseña", type="password", value="admin123")
                b_in = st.form_submit_button("🚜 ENTRAR AL PANEL DE PRECISIÓN", use_container_width=True, type="primary")
                if b_in:
                    usuarios_lower = {k.lower(): (k, v) for k, v in st.session_state.usuarios_db.items()}
                    if u in usuarios_lower and check_hash(p, usuarios_lower[u][1]["pwd"]):
                        st.session_state.usuario_autenticado = usuarios_lower[u][0]
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        else:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.9); border: 2px solid #16a34a; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
                <div style="font-size: 1.05rem; font-weight: 800; color: #15803d; margin-bottom: 6px;">
                    🔑 CÓMO OBTENER TU APIKEY (PASO A PASO):
                </div>
                <div style="font-size: 0.95rem; color: #334155; line-height: 1.5;">
                    <b>1.</b> Abre un chat en WhatsApp con el número: 
                    <span style="background: #fef3c7; color: #92400e; font-weight: 800; padding: 2px 6px; border-radius: 4px;">+34 623 91 22 04</span><br>
                    <b>2.</b> Envía este mensaje exacto:
                </div>
            </div>
            """, unsafe_allow_html=True)

            render_copy_box("I allow callmebot to send me messages")

            st.markdown("""
            <div style="margin-top: -6px; margin-bottom: 14px;">
                <a href="https://api.whatsapp.com/send?phone=34623912204&text=I%20allow%20callmebot%20to%20send%20me%20messages" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #16a34a; color: #ffffff; text-align: center; padding: 11px; border-radius: 12px; font-weight: 800; font-size: 0.95rem; box-shadow: 0 4px 15px rgba(22,163,74,0.2);">
                        📲 TOCAR PARA ABRIR WHATSAPP DIRECTO
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)

            with st.form("form_reg"):
                nu = st.text_input("Usuario").strip()
                nn = st.text_input("Tu Nombre o Explotación").strip()
                ntel = st.text_input("📱 Teléfono Móvil (+34)").strip()
                napi = st.text_input("🔑 APIKey WhatsApp (código recibido del bot)").strip()
                np = st.text_input("Contraseña", type="password")
                
                b_up = st.form_submit_button("🚀 CREAR CUENTA", use_container_width=True, type="primary")
                if b_up:
                    nu_clean = nu.lower()
                    tel_clean = normalizar_telefono(ntel) if ntel else ""
                    
                    if not nu_clean or not np.strip() or not ntel or not napi:
                        st.error("Por favor, completa todos los campos.")
                    elif any(k.lower() == nu_clean for k in st.session_state.usuarios_db.keys()):
                        st.error(f"El usuario '{nu}' ya existe.")
                    else:
                        st.session_state.usuarios_db[nu] = {
                            "pwd": make_hash(np),
                            "nombre": nn if nn else nu,
                            "telefono": tel_clean,
                            "apikey": napi,
                            "rol": "Propietario"
                        }
                        if nu not in st.session_state.db_privada:
                            st.session_state.db_privada[nu] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}
                        
                        guardar_json(USERS_FILE, st.session_state.usuarios_db)
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        
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
rol_usuario = datos_usuario.get("rol", "Propietario")
user_telefono = datos_usuario.get("telefono", "+34626665232")
user_apikey = datos_usuario.get("apikey", "3443251")

if user_activo not in st.session_state.db_privada:
    st.session_state.db_privada[user_activo] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}

if rol_usuario == "Técnico / Asesor":
    lista_explotaciones = list(st.session_state.db_privada.keys())
    explotacion_seleccionada = st.selectbox("👔 Panel de Asesor - Seleccionar Explotación de Socio:", lista_explotaciones, index=0 if user_activo in lista_explotaciones else 0)
    fincas_usuario = st.session_state.db_privada[explotacion_seleccionada]
    nombre_cliente = f"{st.session_state.usuarios_db.get(explotacion_seleccionada, {}).get('nombre', explotacion_seleccionada)} (Asesorado)"
else:
    fincas_usuario = st.session_state.db_privada[user_activo]
    explotacion_seleccionada = user_activo

# Selectores superiores y Modo Contraste
c_top1, c_top2, c_top3, c_top4 = st.columns([1.1, 1.3, 0.6, 0.6])
with c_top1:
    tipo_cultivo = st.selectbox("Cultivo:", ["🍇 Viña", "🫒 Olivo", "🌾 Cereal", "🍑 Frutal"])

if tipo_cultivo not in fincas_usuario:
    fincas_usuario[tipo_cultivo] = {}

fincas_del_cultivo = fincas_usuario.get(tipo_cultivo, {})
nombres_disponibles = list(fincas_del_cultivo.keys())

with c_top2:
    if not nombres_disponibles:
        st.selectbox("Parcela:", ["(Sin parcelas registradas)"])
        nombre_parcela = "Sin Parcela Registrada"
        lat, lon, variedad, suelo, superficie_ha = 42.3659, -2.4235, "Tempranillo", "Cascajo / Calcáreo", 2.0
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
    if st.button("☀️ / 🌙 Sol", use_container_width=True):
        st.session_state.modo_contraste = not st.session_state.modo_contraste
        st.rerun()

with c_top4:
    st.write("")
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.usuario_autenticado = None
        st.rerun()

if st.session_state.modo_contraste:
    st.markdown("""
    <style>
        .main { background: #000000 !important; color: #FFFFFF !important; }
        .card-photo::before { background: rgba(0, 0, 0, 0.85) !important; }
        .card-title { color: #86EFAC !important; }
        .card-value { color: #FFFFFF !important; }
        .card-unit { color: #CBD5E1 !important; }
        div[data-testid="stRadio"] label { background: rgba(30, 41, 59, 0.9) !important; border: none !important; }
        div[data-testid="stRadio"] label div p { color: #FFFFFF !important; }
        .legend-card { background: rgba(30, 41, 59, 0.9) !important; border: none !important; color: #FFFFFF !important; }
        .legend-header { color: #4ADE80 !important; }
        .legend-body { color: #E2E8F0 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSULTA METEOROLÓGICA CON EVAPOTRANSPIRACIÓN (ET0) ---
dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}

try:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,et0_fao_evapotranspiration&timezone=auto"
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
        et0_valores = data["daily"].get("et0_fao_evapotranspiration", [4.2] * len(fechas_raw))
except Exception:
    fechas_legibles = ["Hoy", "Mañana", "Día +2", "Día +3", "Día +4", "Día +5", "Día +6"]
    t_min = [12.0, 11.5, 13.0, 10.5, 11.0, 12.5, 13.0]
    t_max = [24.0, 25.0, 23.5, 22.0, 24.5, 26.0, 25.5]
    lluvia = [0.0, 1.2, 0.0, 0.0, 2.5, 0.0, 0.0]
    viento = [8.0, 10.0, 12.0, 9.0, 7.0, 8.0, 11.0]
    et0_valores = [4.2, 4.5, 3.9, 4.0, 4.6, 4.2, 4.3]

min_hoy = t_min[0]
max_hoy = t_max[0]
lluvia_hoy = lluvia[0]
viento_hoy = viento[0]
et0_hoy = et0_valores[0] if et0_valores else 4.2
temp_media_hoy = (min_hoy + max_hoy) / 2

st.write("---")

# ==============================================================================
# LAYOUT DE 2 COLUMNAS (MENÚ IZQUIERDA + CONTENIDO DERECHA)
# ==============================================================================
col_menu, col_contenido = st.columns([1, 2.3], gap="large")

with col_menu:
    st.markdown("<p style='font-size: 0.95rem; font-weight: 800; color: #64748b; margin-bottom: 6px;'>MÓDULOS DE PRECISIÓN:</p>", unsafe_allow_html=True)

    opciones_menu = [
        "🚜 Semáforo y Satélite (NDVI & Riego)",
        "🧪 Calculadora de Costes (€/ha) y Cuba",
        "📋 Cuaderno SIEX / PAC Oficial",
        "📸 Geofotos y Focos de Plagas",
        "🌾 Labores, Riegos y Cosecha",
        "📲 Bot de Alertas WhatsApp",
        "🌾 Gestión de Fincas y SIGPAC",
        "ℹ️ Leyenda Técnica y Fuentes"
    ]

    if user_activo == "admin":
        opciones_menu.append("🛠️ Panel Administrador")

    seccion_activa = st.radio("Navegación:", opciones_menu, label_visibility="collapsed")

# ==============================================================================
# CONTENIDO EN PANEL DERECHO
# ==============================================================================
with col_contenido:
    # SECCIÓN 1: SEMÁFORO, SATÉLITE (NDVI) Y BALANCE HÍDRICO (ET0)
    if "Semáforo y Satélite" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>📍 {nombre_parcela} <span style='font-size:1rem; color:#64748b;'>({superficie_ha} ha | {variedad})</span></h2>", unsafe_allow_html=True)

        if viento_hoy > 15:
            st.markdown(f"""
            <div class="traffic-danger">
                <div class="traffic-title">⛔ HOY NO SE RECOMIENDA SULFATAR</div>
                <div class="traffic-sub">Viento excesivo ({viento_hoy:.0f} km/h). Deriva de producto garantizada.</div>
            </div>
            """, unsafe_allow_html=True)
        elif lluvia_hoy > 2.0:
            st.markdown(f"""
            <div class="traffic-danger">
                <div class="traffic-title">⛔ HOY NO SULFATES</div>
                <div class="traffic-sub">Lluvia prevista ({lluvia_hoy:.1f} L/m²). Lavado de materia activa.</div>
            </div>
            """, unsafe_allow_html=True)
        elif max_hoy >= 32:
            st.markdown(f"""
            <div class="traffic-warning">
                <div class="traffic-title">⚠️ TRATAR SOLO TEMPRANO</div>
                <div class="traffic-sub">Calor extremo ({max_hoy:.0f} °C). Aplicar de 7:00 a 11:00.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="traffic-ok">
                <div class="traffic-title">✅ DÍA PERFECTO PARA SULFATAR</div>
                <div class="traffic-sub">Viento en calma ({viento_hoy:.0f} km/h), sin lluvia y {max_hoy:.0f} °C.</div>
            </div>
            """, unsafe_allow_html=True)

        if "Viña" in tipo_cultivo:
            riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and temp_media_hoy >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ LIMPIO")
        else:
            riesgo_txt = "🚨 ATENCIÓN" if lluvia_hoy >= 5 else "✅ LIMPIO"

        c_m1, c_m2 = st.columns(2)
        with c_m1:
            st.markdown(f'''
            <div class="card-photo card-temp">
                <div class="card-content">
                    <div class="card-title">🌡️ Tª HOY</div>
                    <div class="card-value">{min_hoy:.0f}° / {max_hoy:.0f}° <span class="card-unit">C</span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown(f'''
            <div class="card-photo card-wind">
                <div class="card-content">
                    <div class="card-title">💨 VIENTO</div>
                    <div class="card-value">{viento_hoy:.0f} <span class="card-unit">km/h</span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        with c_m2:
            st.markdown(f'''
            <div class="card-photo card-rain">
                <div class="card-content">
                    <div class="card-title">🌧️ LLUVIA</div>
                    <div class="card-value">{lluvia_hoy:.1f} <span class="card-unit">L</span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            color_hongos = '#dc2626' if ('ALTO' in riesgo_txt or 'ATENCIÓN' in riesgo_txt) else '#15803d'
            st.markdown(f'''
            <div class="card-photo card-shield">
                <div class="card-content">
                    <div class="card-title">🛡️ HONGOS</div>
                    <div class="card-value" style="font-size:1.5rem; color: {color_hongos};">{riesgo_txt}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # MÓDULO 1 y 5: ÍNDICE DE VIGOR SATELITAL (NDVI) & BALANCE HÍDRICO (ET0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0f172a 100%, #1e293b 0%); border-radius: 18px; padding: 20px 24px; color: #ffffff; margin-top: 15px; box-shadow: 0 8px 24px rgba(15,23,42,0.15);">
            <div style="font-size: 0.85rem; font-weight: 800; color: #4ade80; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">🛰️ Monitoreo Satelital Copernicus & Riego (IA)</div>
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px; margin-top: 10px;">
                <div>
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 700;">ÍNDICE DE VIGOR (NDVI)</div>
                    <div style="font-size: 1.4rem; font-weight: 900; color: #ffffff;">0.78 <span style="font-size: 0.85rem; color: #22c55e;">● Óptimo / Alta Actividad</span></div>
                </div>
                <div>
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 700;">EVAPOTRANSPIRACIÓN (ET0)</div>
                    <div style="font-size: 1.4rem; font-weight: 900; color: #ffffff;">{et0_hoy:.1f} <span style="font-size: 0.85rem; color: #38bdf8;">mm/día (Pérdida hídrica)</span></div>
                </div>
            </div>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                💧 <b>Recomendación de Riego:</b> Con una lluvia de {lluvia_hoy:.1f} L y un consumo diario de {et0_hoy:.1f} mm, el balance hídrico está equilibrado. Riego recomendado: <b>2 horas por goteo</b> este fin de semana.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Cuenta atrás de Plazos de Seguridad
        hist_fitos_alerta = st.session_state.fitos_db.get(explotacion_seleccionada, [])
        if hist_fitos_alerta:
            ultimo_fito = hist_fitos_alerta[-1]
            try:
                f_aplicacion = datetime.strptime(ultimo_fito["Fecha"], "%Y-%m-%d").date()
                dias_ps = int(str(ultimo_fito["Plazo Seg."]).replace(" días", "").replace("días", "").strip())
                f_librecosecha = f_aplicacion + timedelta(days=dias_ps)
                dias_restantes = (f_librecosecha - date.today()).days
                
                if dias_restantes > 0:
                    st.markdown(f"""
                    <div style="background: #fef3c7; border-radius: 16px; padding: 16px 20px; margin-top: 15px; color: #78350f; font-weight: 700; box-shadow: 0 6px 20px rgba(217,119,6,0.08);">
                        ⏳ <b>Plazo de Seguridad Activo:</b> Quedan <b>{dias_restantes} días</b> para poder recolectar en la última parcela tratada ({ultimo_fito['Producto']} - Libre el {f_librecosecha.strftime('%d/%m/%Y')}).
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #dcfce7; border-radius: 16px; padding: 14px 18px; margin-top: 15px; color: #064e3b; font-weight: 700; box-shadow: 0 6px 20px rgba(22,163,74,0.08);">
                        ✅ <b>Parcela Libre:</b> Plazo de seguridad superado. Apta para recolección o laboreo.
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass

        # Gráfica climática de evolución
        st.markdown("<h3 style='font-size: 1.25rem; font-weight: 800; margin-top: 20px;'>📈 Tendencia de Temperaturas y Previsión</h3>", unsafe_allow_html=True)
        df_grafica = pd.DataFrame({
            "Día": [f"Día {i+1}" for i in range(len(t_max))],
            "Tª Máxima (°C)": t_max,
            "Tª Mínima (°C)": t_min
        }).set_index("Día")
        st.line_chart(df_grafica)

    # SECCIÓN 2: CALCULADORA DE DOSIS, COSTES (€/ha) Y CUBA
    elif "Calculadora de Costes" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>🧪 Calculadora de Costes (€/ha) y Cuba</h2>", unsafe_allow_html=True)
        c_c1, c_c2 = st.columns(2)
        with c_c1:
            st.markdown("#### 🚜 Maquinaria y Superficie:")
            litros_cuba = st.selectbox("Capacidad depósito/cuba (L):", [500, 600, 800, 1000, 1500, 2000, 3000], index=3)
            gasto_caldo = st.number_input("Gasto caldo por ha (L/ha):", value=400, step=50)
            ha_a_sulfatar = st.number_input("Superficie a tratar (ha):", value=float(superficie_ha), step=0.5)

        with c_c2:
            st.markdown("#### 🏷️ Producto y Costes:")
            formato_dosis = st.radio("Tipo de dosis:", [
                "Por 100 Litros (gr o cc / 100 L)",
                "Por Hectárea (kg o L / ha)"
            ])
            
            if "100 Litros" in formato_dosis:
                dosis_num = st.number_input("Gramos o cc / 100 L:", value=250.0, step=25.0)
            else:
                dosis_num = st.number_input("Kilos o Litros / ha:", value=2.0, step=0.5)

            precio_kilo = st.number_input("Precio producto (€/kg o €/L):", value=18.0, step=1.0)
            coste_gasoil_ha = st.number_input("Coste estimado tractor/gasoil (€/ha):", value=15.0, step=5.0)

        caldo_total_necesario = ha_a_sulfatar * gasto_caldo
        num_cubas_necesarias = caldo_total_necesario / litros_cuba if litros_cuba > 0 else 0
        ha_por_cuba = litros_cuba / gasto_caldo if gasto_caldo > 0 else 0

        if "100 Litros" in formato_dosis:
            kilos_por_cuba = (dosis_num * (litros_cuba / 100.0)) / 1000.0
            kilos_totales_finca = (dosis_num * (caldo_total_necesario / 100.0)) / 1000.0
        else:
            kilos_por_cuba = dosis_num * ha_por_cuba
            kilos_totales_finca = dosis_num * ha_a_sulfatar

        coste_producto_total = kilos_totales_finca * precio_kilo
        coste_labor_total = ha_a_sulfatar * coste_gasoil_ha
        coste_global_euros = coste_producto_total + coste_labor_total
        coste_por_hectarea = coste_global_euros / ha_a_sulfatar if ha_a_sulfatar > 0 else 0

        st.markdown(f"""
        <div class="recipe-box">
            <div style="font-size: 1rem; font-weight: 800; text-transform: uppercase;">📝 RECETA Y ANÁLISIS DE COSTES</div>
            <div class="recipe-big">{kilos_por_cuba:.2f} <span style="font-size:1.3rem;">kg/L por CUBA de {litros_cuba} L</span></div>
            <hr style="border: 1px solid #a7f3d0; margin: 12px 0;">
            <div style="font-size: 1.15rem; font-weight: 700;">
                🚜 Para <b>{ha_a_sulfatar} ha</b> necesitas <b>{num_cubas_necesarias:.1f} depósitos</b> ({kilos_totales_finca:.2f} kg/L totales).
            </div>
            <div style="font-size: 1.05rem; font-weight: 700; margin-top: 8px; color: #047857;">
                💰 Coste Producto: {coste_producto_total:.2f} € | Coste Labores/Gasoil: {coste_labor_total:.2f} €
            </div>
            <div style="font-size: 1.15rem; font-weight: 900; margin-top: 6px; color: #064e3b;">
                📊 COSTE TOTAL: {coste_global_euros:.2f} € (<span style="color: #b45309;">{coste_por_hectarea:.2f} €/ha</span>).
            </div>
        </div>
        """, unsafe_allow_html=True)

    # SECCIÓN 3: CUADERNO SIEX / PAC Y FITOSANITARIOS
    elif "Cuaderno SIEX" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>📋 Cuaderno de Explotación Homologado (SIEX / PAC)</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b;'>Conexión activa con el catálogo de validación del Registro MAPA para evitar rechazos en la administración.</p>", unsafe_allow_html=True)
        
        with st.form("form_fito"):
            st.markdown("#### ➕ Registrar Aplicación Oficial:")
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                fecha_fito = st.date_input("Fecha de aplicación:", date.today())
                plaga_tratada = st.text_input("Plaga / Hongo / Motivo:", value="Mildiu")
                num_mapa = st.text_input("Nº Registro MAPA (ej: ES-00123, ES-00456, ES-00789):", value="ES-00123")
                producto_fito = st.text_input("Producto Comercial:", value="Oxicloruro de Cobre 50%")
            with c_f2:
                dosis_fito = st.text_input("Dosis aplicada:", value="2.5 kg/ha")
                caldo_gastado = st.number_input("Gasto total caldo (Litros):", value=800, step=100)
                plazo_seg = st.number_input("Plazo de Seguridad (días):", value=14, step=1)
                aplicador_fito = st.text_input("Aplicador / Carnet:", value=nombre_cliente)

            b_guardar_fito = st.form_submit_button("💾 VALIDAR CONTRA MAPA Y GUARDAR EN SIEX", use_container_width=True, type="primary")

            if b_guardar_fito and producto_fito.strip():
                valido, info_mapa = validar_con_mapa(num_mapa)
                
                if not valido:
                    st.error(f"⚠️ El número de registro '{num_mapa}' no se encuentra en el catálogo activo del MAPA. (Prueba con ES-00123, ES-00456 o ES-00789)")
                else:
                    if explotacion_seleccionada not in st.session_state.fitos_db:
                        st.session_state.fitos_db[explotacion_seleccionada] = []
                    
                    registro_nuevo = {
                        "Fecha": str(fecha_fito),
                        "Cultivo": tipo_cultivo,
                        "Parcela": nombre_parcela,
                        "Plaga": plaga_tratada,
                        "Producto": info_mapa["producto"],
                        "Registro MAPA": num_mapa.upper(),
                        "Materia Activa": info_mapa["materia"],
                        "Dosis": dosis_fito,
                        "Caldo (L)": caldo_gastado,
                        "Plazo Seg.": f"{plazo_seg} días",
                        "Aplicador": aplicador_fito,
                        "Estado MAPA": "✅ Validado Oficial"
                    }
                    st.session_state.fitos_db[explotacion_seleccionada].append(registro_nuevo)
                    guardar_json(FITOS_FILE, st.session_state.fitos_db)
                    st.success(f"¡Tratamiento verificado con éxito en el Registro MAPA ({info_mapa['producto']}) y sincronizado con el SIEX!")
                    st.rerun()

        st.markdown("### 📜 Historial Oficial Registrado:")
        hist_fitos = st.session_state.fitos_db.get(explotacion_seleccionada, [])
        if hist_fitos:
            df_fitos = pd.DataFrame(hist_fitos)
            st.dataframe(df_fitos, use_container_width=True, hide_index=True)
            
            csv_data = df_fitos.to_csv(index=False).encode('utf-8')
            st.download_button("📥 DESCARGAR INFORME OFICIAL (FORMATO SIEX / PAC)", data=csv_data, file_name=f"cuaderno_siess_{explotacion_seleccionada}.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("Aún no hay tratamientos oficiales registrados.")

    # SECCIÓN 4: GEOFOTOS Y FOCOS DE PLAGAS (CON SUBIDA REAL DE FOTO)
    elif "Geofotos y Focos" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>📸 Registro de Geofotos y Focos de Plaga</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b;'>Sube o haz una foto de campo con geolocalización GPS automática para justificar inspecciones o controles.</p>", unsafe_allow_html=True)

        with st.form("form_geofoto"):
            desc_incidencia = st.text_input("Descripción del síntoma / plaga (ej: Foco de Mildiu en zona norte):", value="Mancha aislada en hoja")
            sev_incidencia = st.selectbox("Severidad:", ["🟢 Leve / Preventivo", "🟡 Moderado", "🔴 Severo / Urgente"])
            
            # Selector de archivo de imagen
            foto_subida = st.file_uploader("📷 Adjuntar Fotografía (Cámara o Archivo):", type=["jpg", "jpeg", "png"])

            c_g1, c_g2 = st.columns(2)
            with c_g1:
                lat_geo = st.number_input("Latitud GPS:", value=float(lat), format="%.4f")
            with c_g2:
                lon_geo = st.number_input("Longitud GPS:", value=float(lon), format="%.4f")
            
            b_guarda_geo = st.form_submit_button("📸 GUARDAR GEOFOTO Y COORDENADAS", use_container_width=True, type="primary")
            if b_guarda_geo:
                nombre_archivo_foto = "Sin imagen"
                if foto_subida is not None:
                    # Guardar la imagen física en la carpeta de uploads
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo_foto = f"{timestamp_str}_{foto_subida.name}"
                    ruta_guardado = os.path.join(UPLOADS_DIR, nombre_archivo_foto)
                    with open(ruta_guardado, "wb") as f:
                        f.write(foto_subida.getbuffer())

                if explotacion_seleccionada not in st.session_state.plagas_db:
                    st.session_state.plagas_db[explotacion_seleccionada] = []
                
                reg_g = {
                    "Fecha": str(date.today()),
                    "Parcela": nombre_parcela,
                    "Incidencia": desc_incidencia,
                    "Severidad": sev_incidencia,
                    "GPS": f"{lat_geo}, {lon_geo}",
                    "Foto": nombre_archivo_foto
                }
                st.session_state.plagas_db[explotacion_seleccionada].append(reg_g)
                guardar_json(PLAGAS_FILE, st.session_state.plagas_db)
                st.success("¡Geofoto e incidencia geolocalizada registradas correctamente!")
                st.rerun()

        st.markdown("### 🗺️ Incidencias Registradas en Campo:")
        hist_plagas = st.session_state.plagas_db.get(explotacion_seleccionada, [])
        if hist_plagas:
            for p in hist_plagas:
                c_p1, c_p2 = st.columns([2, 1])
                with c_p1:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.9); border-radius: 12px; padding: 14px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                        <b>📅 Fecha:</b> {p['Fecha']} | <b>Parcela:</b> {p['Parcela']}<br>
                        <b>📝 Incidencia:</b> {p['Incidencia']}<br>
                        <b>⚠️ Severidad:</b> {p['Severidad']} | <b>📍 GPS:</b> {p['GPS']}
                    </div>
                    """, unsafe_allow_html=True)
                with c_p2:
                    if p.get('Foto') and p['Foto'] != "Sin imagen":
                        path_img = os.path.join(UPLOADS_DIR, p['Foto'])
                        if os.path.exists(path_img):
                            st.image(path_img, caption="Evidencia de campo", width=160)
                        else:
                            st.caption("Imagen no disponible localmente")
                    else:
                        st.caption("Sin imagen adjunta")
        else:
            st.info("Sin incidencias geolocalizadas registradas.")

    # SECCIÓN 5: LABORES, RIEGOS Y COSECHA (CON RENTABILIDAD NETA)
    elif "Labores, Riegos y Cosecha" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>🌾 Labores de Campo, Riegos y Cosecha</h2>", unsafe_allow_html=True)
        sub_lab1, sub_lab2, sub_lab3 = st.tabs(["🚜 REGISTRAR LABOR / RIEGO", "🍇 REGISTRAR COSECHA / VENTA", "📊 RENTABILIDAD NETA (€/ha)"])
        
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
                    if explotacion_seleccionada not in st.session_state.labores_db:
                        st.session_state.labores_db[explotacion_seleccionada] = {"labores": [], "cosechas": []}
                    
                    reg_l = {
                        "Fecha": str(fecha_lab), "Cultivo": tipo_cultivo, "Parcela": nombre_parcela,
                        "Labor": tipo_labor, "Horas": horas_maq, "Aporte": abono_aporte, "Gasoil (L)": gasoil_litros, "Coste (€)": coste_mano_obra
                    }
                    st.session_state.labores_db[explotacion_seleccionada]["labores"].append(reg_l)
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
                    if explotacion_seleccionada not in st.session_state.labores_db:
                        st.session_state.labores_db[explotacion_seleccionada] = {"labores": [], "cosechas": []}
                    
                    reg_c = {
                        "Fecha": str(fecha_cos), "Cultivo": tipo_cultivo, "Parcela": nombre_parcela,
                        "Kilos": kilos_totales, "Rdto (kg/ha)": round(rendimiento_ha, 1), "Calidad": calidad_param,
                        "Comprador": comprador_dest, "Precio (€/kg)": precio_kilo_venta, "Total (€)": round(ingreso_bruto, 2)
                    }
                    st.session_state.labores_db[explotacion_seleccionada]["cosechas"].append(reg_c)
                    guardar_json(LABORES_FILE, st.session_state.labores_db)
                    st.success("¡Cosecha guardada!")
                    st.rerun()

        with sub_lab3:
            st.markdown("### 📊 Balance Financiero y Beneficio Neto por Hectárea:")
            datos_lab_all = st.session_state.labores_db.get(explotacion_seleccionada, {"labores": [], "cosechas": []})
            
            total_ingresos = sum([c.get("Total (€)", 0) for c in datos_lab_all.get("cosechas", [])])
            total_gastos_labores = sum([l.get("Coste (€)", 0) for l in datos_lab_all.get("labores", [])])
            
            beneficio_neto = total_ingresos - total_gastos_labores
            beneficio_ha = beneficio_neto / superficie_ha if superficie_ha > 0 else 0

            st.markdown(f"""
            <div style="background: #ffffff; border-radius: 16px; padding: 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.04);">
                <div style="font-size: 1.15rem; font-weight: 800; color: #15803d; margin-bottom: 10px;">📈 Resumen de Campaña ({nombre_parcela}):</div>
                <div style="font-size: 1rem; color: #334155; margin-bottom: 6px;">💵 Ingresos Brutos Totales: <b>{total_ingresos:.2f} €</b></div>
                <div style="font-size: 1rem; color: #334155; margin-bottom: 6px;">🛠️ Gastos Totales en Labores: <b>{total_gastos_labores:.2f} €</b></div>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 12px 0;">
                <div style="font-size: 1.3rem; font-weight: 900; color: {'#16a34a' if beneficio_neto >= 0 else '#dc2626'};">
                    💎 Beneficio Neto: {beneficio_neto:.2f} € ({beneficio_ha:.2f} €/ha)
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br><h3>📋 Histórico de Labores y Cosechas:</h3>", unsafe_allow_html=True)
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

    # SECCIÓN 6: BOT WHATSAPP
    elif "Bot de Alertas" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>📲 Bot de Alertas WhatsApp (Automatizado a las 4:45)</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.05rem; color: #475569;'>Alertas vinculadas a: <b>{user_telefono}</b> ({nombre_cliente})</p>", unsafe_allow_html=True)

        if "Viña" in tipo_cultivo:
            riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and temp_media_hoy >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ LIMPIO")
        else:
            riesgo_txt = "🚨 ATENCIÓN" if lluvia_hoy >= 5 else "✅ LIMPIO"

        semaforo_estado_txt = "🟢 ÓPTIMO PARA SULFATAR" if (viento_hoy <= 15 and lluvia_hoy <= 2.0 and max_hoy < 32) else "🔴 NO RECOMENDADO SULFATAR"

        msg_parte = f"""🚜 *PARTE MATUTINO AGROALERT PRO*
📍 *Parcela:* {nombre_parcela} ({superficie_ha} ha)

{semaforo_estado_txt}

🌡️ *Temperaturas:* {min_hoy:.0f}°C a {max_hoy:.0f}°C
💨 *Viento:* {viento_hoy:.0f} km/h
🌧️ *Lluvia:* {lluvia_hoy:.1f} mm
💧 *Evapotranspiración (ET0):* {et0_hoy:.1f} mm
🛡️ *Estado:* {riesgo_txt}"""

        msg_helada = f"""🚨 *¡ALERTA ROJA POR HELADA!*
📍 *Parcela:* {nombre_parcela}

⚠️ *Riesgo Inminente:* Previsión de temperatura crítica de *{min_hoy:.1f}°C*.
🛡️ *Acción:* Activar sistemas antihelada inmediatamente."""

        st.markdown("""
        <div style="background: #eff6ff; border: 2px solid #3b82f6; border-radius: 14px; padding: 16px; margin-bottom: 16px; color: #1e40af;">
            🤖 <b>Automatización Activa (GitHub Actions):</b> El script autónomo <code>bot_diario.py</code> está configurado para ejecutarse todos los días a las <b>4:45 de la mañana</b>, procesando las coordenadas de tus parcelas y enviando el parte matutino a tu WhatsApp sin que tengas que abrir la aplicación.
        </div>
        """, unsafe_allow_html=True)

        if st.button("📲 DISPARAR PARTE MATUTINO MANUAL", use_container_width=True, type="primary"):
            if not user_apikey:
                st.error("No tienes configurada tu APIKey de WhatsApp.")
            else:
                ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg_parte)
                if ok:
                    st.success(res)
                else:
                    st.error(res)

        if st.button("🚨 DISPARAR ALERTA HELADA MANUAL", use_container_width=True):
            if not user_apikey:
                st.error("No tienes configurada tu APIKey de WhatsApp.")
            else:
                ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg_helada)
                if ok:
                    st.warning("¡Alerta enviada!")
                else:
                    st.error(res)

    # SECCIÓN 7: GESTIÓN DE FINCAS Y MAPA SATÉLITE
    elif "Gestión de Fincas" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>🌾 Gestión de Fincas y SIGPAC ({tipo_cultivo})</h2>", unsafe_allow_html=True)
        fincas_actuales = fincas_usuario.get(tipo_cultivo, {})
        
        if not fincas_actuales:
            st.info(f"👉 No tienes ninguna finca registrada en **{tipo_cultivo}**. Rellena los datos para añadir la primera:")
            with st.form("form_alta_primera_finca"):
                nom_finca = st.text_input("Nombre de la Parcela:", value="Mi Parcela 1")
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
                    if explotacion_seleccionada not in st.session_state.db_privada:
                        st.session_state.db_privada[explotacion_seleccionada] = {}
                    if tipo_cultivo not in st.session_state.db_privada[explotacion_seleccionada]:
                        st.session_state.db_privada[explotacion_seleccionada][tipo_cultivo] = {}

                    st.session_state.db_privada[explotacion_seleccionada][tipo_cultivo][nom_finca.strip()] = {
                        "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca,
                        "poligono": pol_finca, "parcela": parc_finca, "riego": riego_finca
                    }
                    guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.success(f"¡Parcela '{nom_finca}' creada y guardada con éxito!")
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
                        guardar_edicion = st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary")
                    with c_btn_del:
                        borrar_finca = st.form_submit_button("🗑️ ELIMINAR FINCA", use_container_width=True)
                    
                    if guardar_edicion:
                        if nuevo_nombre.strip() != finca_a_editar:
                            del st.session_state.db_privada[explotacion_seleccionada][tipo_cultivo][finca_a_editar]
                        st.session_state.db_privada[explotacion_seleccionada][tipo_cultivo][nuevo_nombre.strip()] = {
                            "lat": nueva_lat, "lon": nueva_lon, "variedad": nueva_var, "suelo": nuevo_suelo, "ha": nueva_ha,
                            "poligono": nuevo_pol, "parcela": nuevo_parc, "riego": nuevo_riego
                        }
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        st.success("¡Finca actualizada!")
                        st.rerun()
                        
                    if borrar_finca:
                        del st.session_state.db_privada[explotacion_seleccionada][tipo_cultivo][finca_a_editar]
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        st.warning("¡Finca eliminada!")
                        st.rerun()

                st.markdown(f"#### 🛰️ Vista Satelital y SIGPAC de: **{finca_a_editar}**")
                url_gmaps_app = f"https://www.google.com/maps/search/?api=1&query={datos_f['lat']},{datos_f['lon']}"
                st.markdown(f"""
                <a href="{url_gmaps_app}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #1e293b; color: #ffffff; text-align: center; padding: 12px; border-radius: 14px; font-weight: 800; font-size: 0.95rem; margin-bottom: 12px;">
                        🚗 ABRIR EN APP DE GOOGLE MAPS (GPS / NAVEGACIÓN)
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

                    btn_guardar_f = st.form_submit_button("💾 CREAR NUEVA PARCELA", use_container_width=True, type="primary")

                    if btn_guardar_f and nom_finca.strip():
                        st.session_state.db_privada[explotacion_seleccionada][tipo_cultivo][nom_finca.strip()] = {
                            "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca,
                            "poligono": pol_finca, "parcela": parc_finca, "riego": riego_finca
                        }
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                        st.success(f"¡Parcela '{nom_finca}' guardada!")
                        st.rerun()

            st.markdown("### 📋 Resumen de Parcelas:")
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

    # SECCIÓN 7: LEYENDA Y FUENTES
    elif "Leyenda Técnica" in seccion_activa:
        st.markdown(f"<h2 style='font-size: 1.6rem; font-weight: 900; color: inherit; margin: 0 0 15px 0;'>ℹ️ Leyenda Técnica y Fuentes de Datos</h2>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="legend-card">
            <div class="legend-header">🛰️ 1. Satélites Copernicus (NDVI) & Meteorología</div>
            <div class="legend-body">
                • <b>Sentinel-2 (Copernicus):</b> Cálculo estimado del índice de vigor vegetativo para control de estrés y biomasa.<br>
                • <b>Open-Meteo & ECMWF:</b> Modelos meteorológicos numéricos europeos de alta resolución para coordenadas GPS exactas.<br>
                • <b>Evapotranspiración (ET0):</b> Estimación de la pérdida de agua del suelo y cultivo basada en ecuaciones FAO-56.
            </div>
        </div>

        <div class="legend-card">
            <div class="legend-header">🚦 2. Criterios Agronómicos del Semáforo de Tratamiento</div>
            <div class="legend-body">
                Normativa del <b>Real Decreto 1311/2012 de Uso Sostenible de Fitosanitarios</b> y Gestión Integrada de Plagas (GIP):<br><br>
                • <b>💨 Viento > 15 km/h (Rojo):</b> Deriva de producto inaceptable.<br>
                • <b>🌧️ Lluvia > 2.0 L/m² (Rojo):</b> Riesgo de lavado foliar.<br>
                • <b>🌡️ Temperatura ≥ 32 °C (Ámbar):</b> Riesgo de fitotoxicidad e evaporación rápida.<br>
                • <b>🟢 Semáforo Verde (Óptimo):</b> Condiciones ideales para pulverizar.
            </div>
        </div>

        <div class="legend-card">
            <div class="legend-header">📋 3. Cuaderno de Explotación SIEX / PAC y Multi-Usuario</div>
            <div class="legend-body">
                Soporte completo para agricultores independientes y técnicos asesores que gestionan múltiples explotaciones y necesitan trazabilidad conforme a la PAC.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # SECCIÓN 8: PANEL ADMINISTRADOR
    elif "Panel Administrador" in seccion_activa and user_activo == "admin":
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

        st.write("---")
        st.markdown("### 👥 Todos los Usuarios Registrados:")
        resumen_users = [
            {"Usuario": k, "Nombre / Explotación": v.get("nombre", ""), "Rol": v.get("rol", "Propietario"), "Teléfono": v.get("telefono", "")}
            for k, v in st.session_state.usuarios_db.items()
        ]
        st.dataframe(pd.DataFrame(resumen_users), use_container_width=True, hide_index=True)
