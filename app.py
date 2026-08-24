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
    page_title="AgroAlert Campo | Monitor Diario & Bot",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS VISUALES DE ALTO CONTRASTE Y LETRA GRANDE ---
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
        font-size: 1.6rem;
        font-weight: 900;
        margin-bottom: 6px;
    }
    .traffic-sub {
        font-size: 1.15rem;
        font-weight: 600;
    }

    /* TARJETAS DE DATOS METEOROLÓGICOS */
    .field-card {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
    }
    .field-card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
    }
    .field-card-value {
        font-size: 2.1rem;
        font-weight: 900;
        color: #0f172a;
        margin-top: 4px;
    }
    .field-card-unit {
        font-size: 1.1rem;
        font-weight: 600;
        color: #64748b;
    }

    /* RECETA DE LA CUBA */
    .recipe-box {
        background-color: #ecfdf5;
        border: 3px solid #059669;
        border-radius: 18px;
        padding: 24px;
        margin-top: 15px;
    }
    .recipe-big {
        font-size: 2.4rem;
        font-weight: 900;
        color: #047857;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #ffffff;
        padding: 8px;
        border-radius: 16px;
        border: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        padding: 12px 20px !important;
        border-radius: 12px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #15803d !important;
        color: #ffffff !important;
    }
    
    .stButton>button {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        padding: 14px !important;
        border-radius: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN PARA ENVIAR MENSAJES DE TELEGRAM ---
def enviar_alerta_telegram(bot_token, chat_id, mensaje):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = urllib.parse.urlencode({"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={'User-Agent': 'AgroAlert/Bot'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True, "Mensaje enviado correctamente."
    except Exception as e:
        return False, f"Error al enviar: {str(e)}"

# --- AUTENTICACIÓN ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "admin": {"pwd": make_hash("admin123"), "nombre": "Joel (Mi Explotación)"},
        "demo": {"pwd": make_hash("demo123"), "nombre": "Agricultor Invitado"}
    }

if "db_privada" not in st.session_state:
    st.session_state.db_privada = {
        "admin": {
            "🍇 Viña": {
                "Frontón Jaime": {"lat": 42.3659, "lon": -2.4235, "variedad": "Tempranillo", "suelo": "Cascajo / Calcáreo", "ha": 2.0},
                "Finca Valdegón": {"lat": 42.4658, "lon": -2.4499, "variedad": "Tempranillo", "suelo": "Arcillo-calcáreo", "ha": 2.5}
            },
            "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}
        },
        "demo": {
            "🍇 Viña": {
                "Parcela La Llana": {"lat": 42.4658, "lon": -2.4499, "variedad": "Garnacha", "suelo": "Arcilloso", "ha": 3.0}
            },
            "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}
        }
    }

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if not st.session_state.usuario_autenticado:
    c1, col_login, c2 = st.columns([1, 1.6, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 3.8rem; margin-bottom: 5px;">🚜</div>
            <h1 style="font-size: 2.3rem; font-weight: 900; color: #15803d; margin: 0;">AgroAlert Campo</h1>
            <p style="font-size: 1.15rem; color: #475569; font-weight: 600; margin-top: 6px;">El aviso diario del campo, cálculo de cubas y alertas Telegram</p>
        </div>
        """, unsafe_allow_html=True)

        tab_in, tab_up = st.tabs(["🔑 ENTRAR", "📝 REGISTRARME"])
        with tab_in:
            with st.form("form_auth"):
                u = st.text_input("Usuario o Teléfono", value="admin")
                p = st.text_input("Contraseña", type="password", value="admin123")
                b_in = st.form_submit_button("🚜 ENTRAR A MIS PARCELAS", use_container_width=True, type="primary")
                if b_in:
                    if u in st.session_state.usuarios_db and check_hash(p, st.session_state.usuarios_db[u]["pwd"]):
                        st.session_state.usuario_autenticado = u
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        with tab_up:
            with st.form("form_reg"):
                nu = st.text_input("Nuevo Usuario")
                nn = st.text_input("Tu Nombre o Explotación (ej: Hnos. García)")
                np = st.text_input("Contraseña", type="password")
                b_up = st.form_submit_button("CREAR CUENTA GRATIS", use_container_width=True)
                if b_up and nu.strip() and np.strip():
                    if nu in st.session_state.usuarios_db:
                        st.error("Ese usuario ya existe.")
                    else:
                        st.session_state.usuarios_db[nu] = {"pwd": make_hash(np), "nombre": nn}
                        st.session_state.db_privada[nu] = {"🍇 Viña": {}, "🫒 Olivo": {}, "🌾 Cereal": {}, "🍑 Frutal": {}}
                        st.success("Cuenta creada. Ya puedes pulsar en ENTRAR.")
    st.stop()

# ==============================================================================
# PANEL PRINCIPAL
# ==============================================================================
user_activo = st.session_state.usuario_autenticado
nombre_cliente = st.session_state.usuarios_db[user_activo]["nombre"]
fincas_usuario = st.session_state.db_privada[user_activo]

c_top1, c_top2, c_top3 = st.columns([1.5, 1.5, 0.8])
with c_top1:
    tipo_cultivo = st.selectbox("1️⃣ Cultivo:", ["🍇 Viña", "🫒 Olivo", "🌾 Cereal", "🍑 Frutal"])

fincas_del_cultivo = fincas_usuario.get(tipo_cultivo, {})
nombres_disponibles = list(fincas_del_cultivo.keys())

with c_top2:
    if not nombres_disponibles:
        st.selectbox("2️⃣ Parcela:", ["(Sin parcelas en este cultivo)"])
        nombre_parcela = "Sin Parcela"
        lat, lon, variedad, suelo, superficie_ha = 42.3659, -2.4235, "Tempranillo", "Franco", 2.0
    else:
        seleccion_parcela = st.selectbox("2️⃣ Parcela activa:", nombres_disponibles)
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

# PESTAÑAS PRINCIPALES
tab1, tab2, tab3, tab4 = st.tabs([
    "🚜 ¿PUEDO SULFATAR HOY?",
    "🧪 CUÁNTO ECHAR A LA CUBA",
    "🔔 BOT DE AVISOS & ALERTAS",
    "➕ MIS FINCAS"
])

# ==============================================================================
# PESTAÑA 1: SEMÁFORO DIARIO
# ==============================================================================
with tab1:
    st.markdown(f"<h2 style='font-size: 1.8rem; font-weight: 900; color: #1e293b; margin-top: 10px;'>📍 {nombre_parcela} <span style='font-size:1.1rem; color:#64748b;'>({superficie_ha} ha | {variedad})</span></h2>", unsafe_allow_html=True)

    if viento_hoy > 15:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-danger">
            <div class="traffic-title" style="color: #991b1b;">⛔ HOY NO SE RECOMIENDA SULFATAR</div>
            <div class="traffic-sub" style="color: #b91c1c;">Hay demasiado viento ({viento_hoy:.0f} km/h). El producto se va a volar y vas a perder dinero.</div>
        </div>
        """, unsafe_allow_html=True)
    elif lluvia_hoy > 2.0:
        semaforo_estado = "ROJO"
        st.markdown(f"""
        <div class="traffic-danger">
            <div class="traffic-title" style="color: #991b1b;">⛔ HOY NO SULFATES</div>
            <div class="traffic-sub" style="color: #b91c1c;">Viene lluvia prevista ({lluvia_hoy:.1f} litros/m²). El agua va a lavar el producto.</div>
        </div>
        """, unsafe_allow_html=True)
    elif max_hoy >= 32:
        semaforo_estado = "AMBAR"
        st.markdown(f"""
        <div class="traffic-warning">
            <div class="traffic-title" style="color: #92400e;">⚠️ TRATAR SOLO A PRIMERA HORA DE LA MAÑANA</div>
            <div class="traffic-sub" style="color: #b45309;">Hará mucho calor ({max_hoy:.0f} °C). Sulfata entre las 7:00 y las 11:00 para no quemar la hoja.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        semaforo_estado = "VERDE"
        st.markdown(f"""
        <div class="traffic-ok">
            <div class="traffic-title" style="color: #166534;">✅ DÍA PERFECTO PARA SULFATAR Y TRABAJAR</div>
            <div class="traffic-sub" style="color: #15803d;">Viento en calma ({viento_hoy:.0f} km/h), sin riesgo de lluvia y temperatura ideal ({max_hoy:.0f} °C).</div>
        </div>
        """, unsafe_allow_html=True)

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">🌡️ Temperatura Hoy</div>
            <div class="field-card-value">{min_hoy:.0f}° / {max_hoy:.0f}° <span class="field-card-unit">C</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">🌧️ Lluvia Hoy</div>
            <div class="field-card-value">{lluvia_hoy:.1f} <span class="field-card-unit">litros</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m3:
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">💨 Viento</div>
            <div class="field-card-value">{viento_hoy:.0f} <span class="field-card-unit">km/h</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_m4:
        if "Viña" in tipo_cultivo:
            riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and temp_media_hoy >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ LIMPIO")
        else:
            riesgo_txt = "🚨 ATENCIÓN" if lluvia_hoy >= 5 else "✅ LIMPIO"
        st.markdown(f"""
        <div class="field-card">
            <div class="field-card-title">🛡️ Estado Hongos</div>
            <div class="field-card-value" style="font-size:1.6rem; color: {'#dc2626' if 'ALTO' in riesgo_txt else '#15803d'};">{riesgo_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><h3 style='font-size: 1.4rem; font-weight: 800;'>📅 Previsión Semanal:</h3>", unsafe_allow_html=True)
    df_dias = []
    for i in range(len(fechas_legibles)):
        apto = "✅ Óptimo" if (viento[i] <= 15 and lluvia[i] <= 2.0 and t_max[i] < 32) else ("⛔ No tratar" if (viento[i] > 15 or lluvia[i] > 2.0) else "⚠️ Cuidado")
        df_dias.append({
            "Día": fechas_legibles[i],
            "Tª Mín / Máx": f"{t_min[i]:.0f}°C / {t_max[i]:.0f}°C",
            "Lluvia": f"{lluvia[i]:.1f} L",
            "Viento": f"{viento[i]:.0f} km/h",
            "¿Se puede tratar?": apto
        })
    st.dataframe(pd.DataFrame(df_dias), use_container_width=True, hide_index=True)

# ==============================================================================
# PESTAÑA 2: CALCULADORA DE CUBA
# ==============================================================================
with tab2:
    st.markdown(f"<h2 style='font-size: 1.8rem; font-weight: 900; color: #1e293b; margin-top: 10px;'>🧪 Calculadora para la Cuba del Tractor</h2>", unsafe_allow_html=True)
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.markdown("#### 🚜 Tu Maquinaria:")
        litros_cuba = st.selectbox("Capacidad cuba:", [500, 600, 800, 1000, 1500, 2000, 3000], index=3)
        gasto_caldo = st.number_input("Gasto de caldo por hectárea (L/ha):", value=400, step=50)
        ha_a_sulfatar = st.number_input("Hectáreas a tratar:", value=float(superficie_ha), step=0.5)

    with c_c2:
        st.markdown("#### 🏷️ Dosis de la Etiqueta:")
        formato_dosis = st.radio("Formato de dosis:", [
            "Por cada 100 Litros de agua (gr o cc / 100 L)",
            "Por Hectárea completa (kg o L / ha)"
        ])
        
        if "100 Litros" in formato_dosis:
            dosis_num = st.number_input("Gramos o cc por cada 100 L:", value=250.0, step=25.0)
        else:
            dosis_num = st.number_input("Kilos o Litros por Hectárea:", value=2.0, step=0.5)

        precio_kilo = st.number_input("Precio producto (€ / kg o L):", value=18.0, step=1.0)

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
        <div style="font-size: 1.15rem; font-weight: 800; color: #065f46; text-transform: uppercase;">📝 RECETA DIRECTA PARA LA CUBA</div>
        <div class="recipe-big">{kilos_por_cuba:.2f} <span style="font-size:1.6rem;">Kilos (o Litros) por cada CUBA LLENA de {litros_cuba} L</span></div>
        <hr style="border: 1px solid #a7f3d0; margin: 16px 0;">
        <div style="font-size: 1.25rem; font-weight: 700; color: #047857;">
            🚜 Para <b>{ha_a_sulfatar} ha</b> necesitas <b>{num_cubas_necesarias:.1f} cubas</b> (Total: <b>{kilos_totales_finca:.2f} kg/L</b>).
        </div>
        <div style="font-size: 1.05rem; font-weight: 600; color: #065f46; margin-top: 6px;">
            💰 Coste: <b>{coste_total_euros:.2f} €</b> ({(coste_total_euros/ha_a_sulfatar if ha_a_sulfatar>0 else 0):.2f} €/ha).
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# PESTAÑA 3: BOT DE AVISOS DIARIOS Y EMERGENCIAS (TELEGRAM SEGURO)
# ==============================================================================
with tab3:
    st.markdown(f"<h2 style='font-size: 1.8rem; font-weight: 900; color: #1e293b; margin-top: 10px;'>🔔 Bot de Avisos al Móvil (Telegram)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1rem; color: #475569;'>Recibe el <b>Parte Matutino a las 7:00 AM</b> y <b>Alertas Rojas de Helada</b> directo a tu teléfono.</p>", unsafe_allow_html=True)

    # Comprobamos si existen secretos en Streamlit Cloud o usamos campos de texto
    token_defecto = st.secrets.get("TELEGRAM_TOKEN", "") if hasattr(st, "secrets") else ""
    chat_defecto = st.secrets.get("TELEGRAM_CHAT_ID", "5473461038") if hasattr(st, "secrets") else "5473461038"

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("#### ⚙️ Configuración del Bot")
        bot_token_input = st.text_input("Token de Telegram (de @BotFather):", value=token_defecto, type="password", placeholder="Pega tu token aquí")
        chat_id_input = st.text_input("Tu Chat ID de Telegram:", value=chat_defecto)
        st.caption("🔒 El token no se almacena en el código público.")

    with col_b2:
        st.markdown("#### 📲 Ejemplo del Mensaje que recibirás:")
        st.info(f"""
        🚜 <b>PARTE MATUTINO AGROALERT - 07:00 AM</b>
        📍 Parcela: <b>{nombre_parcela}</b>
        
        {'✅ CONDICIÓN ÓPTIMA PARA SULFATAR' if semaforo_estado == 'VERDE' else '⛔ PRECAUCIÓN / NO SULFATAR HOY'}
        🌡️ Tª Hoy: {min_hoy:.0f}°C a {max_hoy:.0f}°C
        💨 Viento máx: {viento_hoy:.0f} km/h
        🌧️ Lluvia prevista: {lluvia_hoy:.1f} mm
        🛡️ Riesgo Hongos: {'Bajo' if lluvia_hoy < 5 else 'Elevado'}
        """)

    st.write("---")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("📲 ENVIAR PARTE MATUTINO AHORA", use_container_width=True, type="primary"):
            if not bot_token_input:
                st.error("Por favor, introduce tu Token de Telegram en la casilla de la izquierda.")
            else:
                txt_parte = f"""🚜 <b>PARTE MATUTINO AGROALERT (07:00 AM)</b>
📍 Parcela: <b>{nombre_parcela}</b> ({superficie_ha} ha)

{'✅ DÍA PERFECTO PARA SULFATAR Y TRABAJAR' if semaforo_estado == 'VERDE' else ('⚠️ ATENCIÓN: TRATAR SOLO TEMPRANO' if semaforo_estado == 'AMBAR' else '⛔ NO SULFATAR HOY')}

🌡️ <b>Temperaturas:</b> Mín {min_hoy:.0f}°C / Máx {max_hoy:.0f}°C
💨 <b>Viento máx:</b> {viento_hoy:.0f} km/h
🌧️ <b>Lluvia:</b> {lluvia_hoy:.1f} litros/m²
🛡️ <b>Alerta Fitosanitaria:</b> {'Condición segura' if lluvia_hoy < 5 else 'Riesgo fúngico activo por humedad'}

<i>AgroAlert Pro - Monitor Agrícola de Precisión</i>"""
                ok, res_msg = enviar_alerta_telegram(bot_token_input, chat_id_input, txt_parte)
                if ok:
                    st.success("¡Parte diario enviado a tu Telegram con éxito! Revisa tu móvil.")
                else:
                    st.error(res_msg)

    with c_btn2:
        if st.button("🚨 PROBAR ALERTA DE EMERGENCIA (HELADA)", use_container_width=True):
            if not bot_token_input:
                st.error("Por favor, introduce tu Token de Telegram en la casilla de la izquierda.")
            else:
                txt_emergencia = f"""🚨 <b>¡ALERTA ROJA DE EMERGENCIA POR HELADA!</b>
📍 Parcela: <b>{nombre_parcela}</b>

⚠️ <b>Riesgo Inminente:</b> Se prevén temperaturas de <b>{min_hoy:.1f}°C</b> en las próximas horas.
🛡️ <b>Acción recomendada:</b> Activar quemadores/molinos antihelada y suspender labores de deshierbe."""
                ok, res_msg = enviar_alerta_telegram(bot_token_input, chat_id_input, txt_emergencia)
                if ok:
                    st.warning("¡Alerta de emergencia enviada a tu móvil!")
                else:
                    st.error(res_msg)

# ==============================================================================
# PESTAÑA 4: GESTIÓN DE FINCAS
# ==============================================================================
with tab4:
    st.markdown(f"<h2 style='font-size: 1.8rem; font-weight: 900; color: #1e293b; margin-top: 10px;'>➕ Añadir una Nueva Parcela</h2>", unsafe_allow_html=True)
    with st.form("form_alta_finca"):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            nom_finca = st.text_input("Nombre finca:", value="Viña Nueva")
            lat_finca = st.number_input("Latitud decimal:", value=42.3659, format="%.4f")
            lon_finca = st.number_input("Longitud decimal:", value=-2.4235, format="%.4f")
        with c_f2:
            var_finca = st.text_input("Variedad:", value="Tempranillo")
            ha_finca = st.number_input("Superficie (ha):", value=2.0, min_value=0.1, step=0.5)
            suelo_finca = st.selectbox("Terreno:", ["Cascajo / Pedregoso", "Arcillo-calcáreo", "Arenoso", "Tierra fuerte"])

        btn_guardar_f = st.form_submit_button("💾 GUARDAR ESTA PARCELA EN MI CUENTA", use_container_width=True, type="primary")

        if btn_guardar_f and nom_finca.strip():
            st.session_state.db_privada[user_activo][tipo_cultivo][nom_finca.strip()] = {
                "lat": lat_finca, "lon": lon_finca, "variedad": var_finca, "suelo": suelo_finca, "ha": ha_finca
            }
            st.success(f"¡Parcela '{nom_finca}' guardada!")
            st.rerun()

    st.write("---")
    st.markdown("### 📋 Tus Parcelas Registradas:")
    tabla_fincas = [
        {"Parcela": k, "Hectáreas": v["ha"], "Variedad": v["variedad"], "Terreno": v["suelo"]}
        for k, v in fincas_usuario.get(tipo_cultivo, {}).items()
    ]
    if tabla_fincas:
        st.dataframe(pd.DataFrame(tabla_fincas), use_container_width=True, hide_index=True)
