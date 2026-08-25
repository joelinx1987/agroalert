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

logo_path = "logo.png" if os.path.exists("logo.png") else ("logo.jpg" if os.path.exists("logo.jpg") else None)

st.set_page_config(
    page_title="AgroAlert | El Asistente del Agricultor",
    page_icon=logo_path if logo_path else "🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #f1f5f9 100%) !important; background-attachment: fixed !important; color: #0f172a; }
    div[data-testid="stRadio"] > div { flex-direction: column !important; gap: 10px !important; }
    div[data-testid="stRadio"] label {
        background: #ffffff !important; border: 2px solid #e2e8f0 !important; border-radius: 16px !important;
        padding: 16px 20px !important; width: 100% !important; cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important; transition: all 0.15s ease !important;
    }
    div[data-testid="stRadio"] label:hover { background-color: #f0fdf4 !important; border-color: #16a34a !important; }
    div[data-testid="stRadio"] label div p { font-size: 1.1rem !important; font-weight: 800 !important; color: #0f172a !important; }
    .semaforo-ok { background: #dcfce7; border: 3px solid #22c55e; border-radius: 20px; padding: 24px; text-align: center; color: #064e3b; box-shadow: 0 10px 25px rgba(34, 197, 94, 0.15); }
    .semaforo-bad { background: #fee2e2; border: 3px solid #ef4444; border-radius: 20px; padding: 24px; text-align: center; color: #7f1d1d; box-shadow: 0 10px 25px rgba(239, 68, 68, 0.15); }
    .stButton>button { font-size: 1.1rem !important; font-weight: 800 !important; padding: 14px 20px !important; border-radius: 14px !important; border: none !important; box-shadow: 0 4px 15px rgba(0,0,0,0.06) !important; }
</style>
""", unsafe_allow_html=True)

USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"
FITOS_FILE = "fitosanitarios_db.json"

CATALOGO_MAPA = {
    "ES-00123": {"producto": "Oxicloruro de Cobre 50%", "plazo": 14},
    "ES-00456": {"producto": "Azufre Moable 80%", "plazo": 5},
    "ES-00789": {"producto": "Cipermetrina 10%", "plazo": 21}
}

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
    except Exception:
        pass

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

DEFAULT_USERS = {
    "admin1987": {"pwd": "admin1987", "nombre": "Joel (La Rioja)", "telegram_id": "5473461038", "telegram_token": "8717165365:AAEqfcf5KKG0f6yVDAvrdW4QhxQLLV7IsSs"}
}
DEFAULT_FINCAS = {
    "joel": {
        "🍇 Viñedo Principal": {"lat": 42.4658, "lon": -2.4499, "variedad": "Tempranillo", "ha": 3.5, "poligono": "12", "parcela": "104"},
        "🫒 Olivar": {"lat": 42.4500, "lon": -2.4300, "variedad": "Arbequina", "ha": 1.5, "poligono": "8", "parcela": "42"}
    }
}

if entrar:
                if usuario in st.session_state.usuarios_db and st.session_state.usuarios_db[usuario]["pwd"] == pwd:
                    st.session_state.usuario_autenticado = usuario
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

def disparar_telegram(token, chat_id, mensaje):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'Markdown'}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, "¡Mensaje enviado con éxito a tu Telegram!"
    except Exception as e:
        return False, f"Error al enviar: {str(e)}"

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if not st.session_state.usuario_autenticado:
    c1, col_login, c2 = st.columns([1, 1.6, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, width=180)
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #15803d; font-weight: 900;">AgroAlert</h1>
            <p style="font-weight: 600; color: #475569;">Tu asistente de confianza para el campo</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            usuario = st.text_input("Usuario", value="joel").strip().lower()
            pwd = st.text_input("Contraseña", type="password", value="1234")
            entrar = st.form_submit_button("🚜 ENTRAR A MI EXPLOTACIÓN", use_container_width=True, type="primary")
            if entrar:
                if usuario in st.session_state.usuarios_db and st.session_state.usuarios_db[usuario]["pwd"] == make_hash(pwd):
                    st.session_state.usuario_autenticado = usuario
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

user = st.session_state.usuario_autenticado
info_user = st.session_state.usuarios_db.get(user, {})
fincas_usuario = st.session_state.db_privada.get(user, {"🍇 Mi Viña": {"lat": 42.46, "lon": -2.44, "ha": 2.0}})
telegram_token = info_user.get("telegram_token", "8717165365:AAEqfcf5KKG0f6yVDAvrdW4QhxQLLV7IsSs")
telegram_id = info_user.get("telegram_id", "5473461038")

c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    st.markdown(f"### 🚜 Hola, {info_user.get('nombre', 'Agricultor')}")
with c_h2:
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.usuario_autenticado = None
        st.rerun()

st.write("---")

nombres_fincas = list(fincas_usuario.keys())
parcela_activa = st.selectbox("📍 SELECCIONA TU PARCELA:", nombres_fincas)
datos_parcela = fincas_usuario[parcela_activa]
viento_hoy = 8.0
lluvia_hoy = 0.0

st.write("")

menu = st.radio("Menú:", [
    "🟢 ¿Puedo Sulfatar Hoy?",
    "🧪 Cuenta de la Vieja (Calculadora de Cuba)",
    "📋 Cuaderno de Campo (PAC sin multas)",
    "📲 Avisos Automáticos a las 11:55"
], label_visibility="collapsed")

st.write("---")

if "Puedo Sulfatar" in menu:
    st.markdown(f"### 🎯 Estado del tiempo para hoy en **{parcela_activa}**")
    if viento_hoy > 15 or lluvia_hoy > 2.0:
        st.markdown(f'<div class="semaforo-bad"><h2 style="margin:0; font-weight:900;">⛔ HOY NO ES BUEN DÍA</h2><p style="font-size:1.1rem; margin-top:8px;">Viento a {viento_hoy:.0f} km/h o previsión de lluvia.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="semaforo-ok"><h2 style="margin:0; font-weight:900;">✅ DÍA PERFECTO PARA ENTRAR</h2><p style="font-size:1.1rem; margin-top:8px;">Viento en calma ({viento_hoy:.0f} km/h) y sin lluvia.</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c_m1, c_m2 = st.columns(2)
    with c_m1: st.metric("💨 Viento actual", f"{viento_hoy:.0f} km/h", "Ideal < 15")
    with c_m2: st.metric("🌧️ Lluvia prevista", f"{lluvia_hoy:.1f} L/m²", "Sin riesgo")

elif "Calculadora de Cuba" in menu:
    st.markdown("### 🧪 ¿Cuánto producto echo a la cuba?")
    with st.form("form_cuba"):
        c_c1, c_c2 = st.columns(2)
        with c_c1:
            litros_cuba = st.selectbox("Litros de tu depósito o cuba:", [500, 600, 800, 1000, 1500, 2000], index=3)
            gasto_por_ha = st.number_input("Litros de caldo que gastas por hectárea:", value=400, step=50)
        with c_c2:
            dosis_ha = st.number_input("Dosis recomendada por hectárea (kg o L):", value=2.5, step=0.5)
            ha_finca = st.number_input("Hectáreas que vas a tratar:", value=float(datos_parcela["ha"]), step=0.5)
        calcular = st.form_submit_button("🧮 CALCULÁMELO", use_container_width=True, type="primary")
        if calcular:
            ha_por_cuba = litros_cuba / gasto_por_ha if gasto_por_ha > 0 else 0
            producto_por_cuba = dosis_ha * ha_por_cuba
            total_cubas = (ha_finca * gasto_por_ha) / litros_cuba if litros_cuba > 0 else 0
            total_producto = dosis_ha * ha_finca
            st.markdown(f'<div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 16px; padding: 20px; margin-top: 15px; color: #065f46;"><h3 style="margin:0; color:#047857;">📌 RESULTADO:</h3><p style="font-size: 1.3rem; font-weight: 800; margin: 10px 0;">👉 Echa <b>{producto_por_cuba:.2f} kg/L</b> por cuba de {litros_cuba} L.</p><p style="font-size: 1rem; margin: 0;">🚜 Total para {ha_finca} ha: <b>{total_cubas:.1f} cubas</b> ({total_producto:.2f} kg/L totales).</p></div>', unsafe_allow_html=True)

elif "Cuaderno de Campo" in menu:
    st.markdown("### 📋 Tu Cuaderno de Explotación")
    with st.form("form_cuaderno"):
        f_apli = st.date_input("Fecha de aplicación:", date.today())
        motivo = st.text_input("¿Qué has tratado?:", value="Mildiu preventivo")
        reg_mapa = st.text_input("Nº Registro MAPA:", value="ES-00123")
        guardar_fito = st.form_submit_button("💾 GUARDAR APUNTE", use_container_width=True, type="primary")
        if guardar_fito:
            if user not in st.session_state.fitos_db: st.session_state.fitos_db[user] = []
            plazo_dias = CATALOGO_MAPA.get(reg_mapa.strip().upper(), {"plazo": 14})["plazo"]
            librede = f_apli + timedelta(days=plazo_dias)
            st.session_state.fitos_db[user].append({"Fecha": str(f_apli), "Parcela": parcela_activa, "Tratamiento": motivo, "MAPA": reg_mapa.upper(), "Libre recolección": str(librede)})
            guardar_json(FITOS_FILE, st.session_state.fitos_db)
            st.success("¡Apuntado correctamente!")
    mis_datos = st.session_state.fitos_db.get(user, [])
    if mis_datos: st.dataframe(pd.DataFrame(mis_datos), use_container_width=True, hide_index=True)

elif "Avisos Automáticos a las 11:55" in menu:
    st.markdown("### 📲 Aviso Diario en tu Telegram a las 11:55")
    st.write("Recibirás un aviso automático en Telegram con los datos de tu parcela activa.")
    st.info(f"🤖 Chat ID configurado: **{telegram_id}**")
    msg_prueba = f"🚜 *AGROALERT - PARTE DE LAS 11:55*\n📍 *Parcela:* {parcela_activa} ({datos_parcela['ha']} ha)\n🟢 *Estado:* Día perfecto para sulfatar.\n💨 *Viento:* {viento_hoy} km/h (Calma).\n🌧️ *Lluvia:* {lluvia_hoy} mm."
    if st.button("📲 PROBAR ENVÍO A TELEGRAM AHORA", use_container_width=True, type="primary"):
        ok, res = disparar_telegram(telegram_token, telegram_id, msg_prueba)
        if ok: st.success(res)
        else: st.error(res)
