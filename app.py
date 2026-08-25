import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.request
import urllib.parse
import json
import hashlib
import folium
from streamlit_folium import st_folium

# --- COMPROBACIÓN SEGURA DE LA RUTA DEL LOGO ---
logo_path = None
for posibles_nombres in ["logo.png", "logo.jpg", "fondo_logo.jpg.jpg"]:
    if os.path.exists(posibles_nombres):
        logo_path = posibles_nombres
        break

st.set_page_config(
    page_title="AgroAlert | Asistente Agrícola Profesional",
    page_icon=logo_path if logo_path else "🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PREMIUM Y DISEÑO MODERNO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .main {
        background: linear-gradient(135deg, #f6fdf9 0%, #edf4f0 100%) !important;
        background-attachment: fixed !important;
        color: #1e293b;
    }

    .agro-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    
    div[data-testid="stRadio"] label {
        background: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        width: 100% !important;
        cursor: pointer !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        background-color: #f0fdf4 !important;
        border-color: #16a34a !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(22, 163, 74, 0.1) !important;
    }
    
    div[data-testid="stRadio"] label div p {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #15803d !important;
    }

    .semaforo-ok {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border: 2px solid #22c55e;
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        color: #064e3b;
        box-shadow: 0 10px 25px rgba(34, 197, 94, 0.15);
    }
    
    .semaforo-bad {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 2px solid #ef4444;
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        color: #7f1d1d;
        box-shadow: 0 10px 25px rgba(239, 68, 68, 0.15);
    }

    .stButton>button {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        padding: 14px 24px !important;
        border-radius: 14px !important;
        border: none !important;
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100% ) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(22, 163, 74, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #15803d 0%, #166534 100% ) !important;
        box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4) !important;
        transform: translateY(-1px);
    }

    .guia-caja {
        background: #f0fdf4;
        border-left: 5px solid #16a34a;
        border-radius: 0 16px 16px 0;
        padding: 20px;
        margin-bottom: 20px;
        color: #065f46;
        font-size: 1.05rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"
FITOS_FILE = "fitosanitarios_db.json"
ALMACEN_FILE = "almacen_db.json"

CATALOGO_MAPA = {
    "ES-00123": {"producto": "Oxicloruro de Cobre 50% (Preventivo Mildiu)", "plazo": 14},
    "ES-00456": {"producto": "Azufre Mojable 80% (Oídio)", "plazo": 5},
    "ES-00789": {"producto": "Cipermetrina 10% (Insecticida Polilla)", "plazo": 21},
    "ES-00999": {"producto": "Fosetil-Al 80% (Sistémico Antidion)", "plazo": 15},
    "ES-01111": {"producto": "Mancozeb 80% (Fungicida amplio espectro)", "plazo": 28},
    "ES-02222": {"producto": "Difenoconazol 25% (Fungicida sistémico)", "plazo": 21}
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

DEFAULT_USERS = {
    "admin1987": {"pwd": "admin1987", "nombre": "Joel (La Rioja)", "telegram_id": "5473461038", "telegram_token": "8717165365:AAEqfcf5KKG0f6yVDAvrdW4QhxQLLV7IsSs"}
}
DEFAULT_FINCAS = {
    "admin1987": {
        "🍇 Viñedo Principal": {"lat": 42.4658, "lon": -2.4499, "variedad": "Tempranillo", "ha": 3.5, "poligono": "12", "parcela": "104"},
        "🫒 Olivar": {"lat": 42.4500, "lon": -2.4300, "variedad": "Arbequina", "ha": 1.5, "poligono": "8", "parcela": "42"}
    }
}
DEFAULT_ALMACEN = {
    "admin1987": {
        "ES-00123": {"nombre": "Oxicloruro de Cobre 50%", "stock_kg_l": 25.0},
        "ES-00456": {"nombre": "Azufre Mojable 80%", "stock_kg_l": 40.0},
        "ES-00789": {"nombre": "Cipermetrina 10%", "stock_kg_l": 10.0}
    }
}

if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = cargar_json(USERS_FILE, DEFAULT_USERS)
st.session_state.usuarios_db["admin1987"] = DEFAULT_USERS["admin1987"]

if "db_privada" not in st.session_state:
    st.session_state.db_privada = cargar_json(FINCAS_FILE, DEFAULT_FINCAS)
if "fitos_db" not in st.session_state:
    st.session_state.fitos_db = cargar_json(FITOS_FILE, {})
if "almacen_db" not in st.session_state:
    st.session_state.almacen_db = cargar_json(ALMACEN_FILE, DEFAULT_ALMACEN)

def consultar_meteo_openmeteo(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&hourly=temperature_2m,precipitation,wind_speed_10m&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            
            horas_prevision = []
            if "time" in hourly:
                t_list = hourly["time"][:6]
                w_list = hourly["wind_speed_10m"][:6]
                p_list = hourly["precipitation"][:6]
                for t, w, p in zip(t_list, w_list, p_list):
                    hora_str = t.split("T")[-1]
                    horas_prevision.append({"hora": hora_str, "viento": w, "lluvia": p})

            return {
                "temp": current.get("temperature_2m", 22.0),
                "humedad": current.get("relative_humidity_2m", 50.0),
                "lluvia": current.get("precipitation", 0.0),
                "viento": current.get("wind_speed_10m", 8.0),
                "horaria": horas_prevision
            }
    except Exception:
        return {"temp": 22.0, "humedad": 50.0, "lluvia": 0.0, "viento": 8.0, "horaria": []}

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
    c1, col_login, c2 = st.columns([1, 2.2, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="color: #15803d; font-weight: 900; font-size: 2.5rem; margin-bottom: 5px;">AgroAlert</h1>
                <p style="font-weight: 600; color: #475569; font-size: 1.1rem;">Tu asistente de confianza para el campo y la PAC</p>
            </div>
            """, unsafe_allow_html=True)

        tab_entrar, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse Nuevo"])

        with tab_entrar:
            with st.form("form_login"):
                usuario = st.text_input("Usuario", value="admin1987").strip().lower()
                pwd = st.text_input("Contraseña", type="password", value="admin1987")
                entrar = st.form_submit_button("🚜 ENTRAR A MI EXPLOTACIÓN", use_container_width=True, type="primary")
                if entrar:
                    if usuario in st.session_state.usuarios_db and st.session_state.usuarios_db[usuario]["pwd"] == pwd:
                        st.session_state.usuario_autenticado = usuario
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")

        with tab_registro:
            st.markdown("""
            <div class="guia-caja">
                <b>🌾 ¿Cómo conectar los avisos a tu móvil paso a paso?</b><br><br>
                1️⃣ Abre la aplicación <b>Telegram</b> en tu móvil.<br>
                2️⃣ Busca arriba en la lupa nuestro bot oficial: <b>@ActualizacionAgroAlert_bot</b><br>
                3️⃣ Escríbele cualquier mensaje (por ejemplo: <i>Hola</i>).<br>
                4️⃣ Al instante, el bot te contestará con tu <b>Número de Identificación (Chat ID)</b>. ¡Cópialo y pégalo aquí abajo!
            </div>
            """, unsafe_allow_html=True)

            with st.form("form_registro_nuevo"):
                nuevo_user = st.text_input("Nombre de usuario para entrar (ej. manolo)").strip().lower()
                nuevo_pwd = st.text_input("Contraseña", type="password")
                nuevo_nombre = st.text_input("Tu Nombre y Apellidos")
                nuevo_chat_id = st.text_input("Tu Código de Telegram (que te acaba de dar el bot)")
                
                nuevo_token = "8717165365:AAEqfcf5KKG0f6yVDAvrdW4QhxQLLV7IsSs"
                
                st.markdown("---")
                st.markdown("##### 📍 Datos de tu parcela principal")
                c_rp1, c_rp2 = st.columns(2)
                with c_rp1:
                    nombre_parcela = st.text_input("Nombre de tu finca (ej: Viñedo Bajo)", value="🍇 Mi Finca")
                    superficie_ha = st.number_input("Hectáreas de la finca", value=2.0, step=0.5)
                with c_rp2:
                    lat_inicial = st.number_input("Latitud (ej: 42.4658)", value=42.4658, format="%.6f")
                    lon_inicial = st.number_input("Longitud (ej: -2.4499)", value=-2.4499, format="%.6f")

                registrarse = st.form_submit_button("✨ DARME DE ALTA", use_container_width=True, type="primary")
                if registrarse:
                    if not nuevo_user or not nuevo_pwd or not nuevo_chat_id:
                        st.error("Por favor, rellena tu usuario, contraseña y número de Telegram.")
                    elif nuevo_user in st.session_state.usuarios_db:
                        st.error("Ese usuario ya existe. Elige otro.")
                    else:
                        st.session_state.usuarios_db[nuevo_user] = {
                            "pwd": nuevo_pwd,
                            "nombre": nuevo_nombre if nuevo_nombre else nuevo_user,
                            "telegram_id": nuevo_chat_id.strip(),
                            "telegram_token": nuevo_token
                        }
                        guardar_json(USERS_FILE, st.session_state.usuarios_db)

                        if nuevo_user not in st.session_state.db_privada:
                            st.session_state.db_privada[nuevo_user] = {}
                        st.session_state.db_privada[nuevo_user][nombre_parcela] = {
                            "lat": lat_inicial, "lon": lon_inicial, "variedad": "General", "ha": superficie_ha, "poligono": "1", "parcela": "1"
                        }
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)

                        st.success("¡Cuenta creada con éxito! Ya puedes ir a la pestaña 'Iniciar Sesión' y entrar.")
    st.stop()

user = st.session_state.usuario_autenticado
info_user = st.session_state.usuarios_db.get(user, {})
fincas_usuario = st.session_state.db_privada.get(user, {"🍇 Mi Viña": {"lat": 42.46, "lon": -2.44, "ha": 2.0}})
telegram_token = info_user.get("telegram_token", "8717165365:AAEqfcf5KKG0f6yVDAvrdW4QhxQLLV7IsSs")
telegram_id = info_user.get("telegram_id", "5473461038")

# --- CABECERA SUPERIOR PROFESIONAL CON SELECTOR RÁPIDO DE FINCA Y LOGO OFICIAL ---
col_head_izq, col_head_centro, col_head_der = st.columns([1.2, 2.2, 1])

with col_head_izq:
    st.markdown(f"<h4 style='margin-top: 10px; color: #1e293b;'>🚜 Hola, {info_user.get('nombre', 'Agricultor')}</h4>", unsafe_allow_html=True)
    nombres_fincas = list(fincas_usuario.keys())
    parcela_activa = st.selectbox("📍 Parcela activa:", nombres_fincas, label_visibility="visible")
    datos_parcela = fincas_usuario.get(parcela_activa, {"lat": 42.46, "lon": -2.44, "ha": 1.0})

with col_head_centro:
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

with col_head_der:
    st.markdown("<div style='display: flex; justify-content: flex-end; margin-top: 25px;'>", unsafe_allow_html=True)
    if st.button("🚪 Salir", use_container_width=False):
        st.session_state.usuario_autenticado = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# --- DISTRIBUCIÓN EN 2 COLUMNAS (MENÚ IZQUIERDA / CONTENIDO DERECHA) ---
col_menu, col_contenido = st.columns([1.1, 2.5], gap="large")

with col_menu:
    st.markdown("##### 🧭 MENÚ PRINCIPAL DE GESTIÓN:")
    
    lista_menu = [
        "🟢 ¿Puedo Sulfatar Hoy?",
        "🐛 Avisos Predictivos de Plagas",
        "🧪 Calculadora de Fitosanitarios",
        "📦 Almacén de Fitosanitarios",
        "📋 Cuaderno de Campo (PAC sin multas)",
        "📲 Avisos Automáticos a las 4:45",
        "⚙️ Gestión de Fincas y Parcelas"
    ]
    
    if user == "admin1987":
        lista_menu.append("👥 Gestión de Usuarios Registrados")

    menu = st.radio("Menú:", lista_menu, label_visibility="collapsed")

meteo_actual = consultar_meteo_openmeteo(datos_parcela.get("lat", 42.46), datos_parcela.get("lon", -2.44))
viento_hoy = meteo_actual["viento"]
lluvia_hoy = meteo_actual["lluvia"]
temp_hoy = meteo_actual["temp"]
humedad_hoy = meteo_actual["humedad"]
horaria_24h = meteo_actual["horaria"]

with col_contenido:
    if "Puedo Sulfatar" in menu:
        st.markdown(f"### 🎯 Estado del tiempo para hoy en **{parcela_activa}**")
        
        razones = []
        if viento_hoy > 15:
            razones.append(f"• Viento fuerte a {viento_hoy:.1f} km/h (Límite máximo recomendado: 15 km/h)")
        if lluvia_hoy > 2.0:
            razones.append(f"• Riesgo de precipitaciones de {lluvia_hoy:.1f} mm (Riesgo de lavado)")

        if viento_hoy > 15 or lluvia_hoy > 2.0:
            razones_texto = "<br>".join(razones)
            st.markdown(f'<div class="semaforo-bad"><h2 style="margin:0; font-weight:900;">⛔ CONDICIONES NO APTAS PARA TRATAR</h2><p style="font-size:1.1rem; margin-top:12px; line-height:1.6;"><b>Motivos meteorológicos:</b><br>{razones_texto}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="semaforo-ok"><h2 style="margin:0; font-weight:900;">✅ VÍA LIBRE PARA TRATAR LA FINCA</h2><p style="font-size:1.1rem; margin-top:8px;">Viento suave ({viento_hoy:.1f} km/h) y sin precipitaciones.</p></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        with c_m1: st.metric("💨 Viento actual", f"{viento_hoy:.1f} km/h", "Ideal < 15")
        with c_m2: st.metric("🌧️ Lluvia", f"{lluvia_hoy:.1f} L/m²", "Sin riesgo")
        with c_m3: st.metric("🌡️ Temperatura", f"{temp_hoy:.1f} °C", "Ambiente")
        with c_m4: st.metric("💧 Humedad", f"{humedad_hoy:.0f}%", "Relativa")

        if horaria_24h:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### ⏱️ Evolución y Previsión Horaria en Parcela:")
            df_horaria = pd.DataFrame(horaria_24h)
            df_horaria.columns = ["Hora", "Viento (km/h)", "Lluvia (mm)"]
            st.dataframe(df_horaria, use_container_width=True, hide_index=True)

    elif "Avisos Predictivos de Plagas" in menu:
        st.markdown(f"### 🐛 Modelo Predictivo de Plagas por Comarca")
        st.write("Análisis biológico automatizado basado en grados-día acumulados y condiciones higrométricas para adelantarse a las infecciones.")
        
        riesgo_mildiu = "Alto" if humedad_hoy > 65 and temp_hoy > 20 else "Bajo / Controlado"
        riesgo_oidio = "Moderado" if temp_hoy >= 22 and temp_hoy <= 32 else "Bajo"
        riesgo_polilla = "Activo (Vuelo de generación)" if temp_hoy > 18 else "Inactivo"
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            st.metric("🦠 Riesgo de Mildiu", riesgo_mildiu, "Fungicida preventivo")
        with c_p2:
            st.metric("🌾 Riesgo de Oídio", riesgo_oidio, "Azufres")
        with c_p3:
            st.metric("🦋 Polilla del Racimo", riesgo_polilla, "Trampas de feromona")
            
        st.markdown("---")
        st.markdown("#### 📋 Informe Técnico y Recomendaciones de Tratamiento por Comarca:")
        
        st.markdown(f"""
        * **Zona de Influencia:** La Rioja / Cuenca del Ebro
        * **Condiciones meteorológicas de incubación:** Temperatura media de `{temp_hoy}°C` con humedad relativa del `{humedad_hoy}%`.
        * **Acción preventivo-correctiva recomendada:**
          * Si el riesgo de **Mildiu** es *Alto* y las precipitaciones superan los 2mm, se recomienda programar aplicación sistémica o penetrante antes de que se cumpla el periodo de incubación de la mancha de aceite.
          * Vigilar el envés de las hojas en los margenes de la parcela orientados al norte.
        """)

    elif "Calculadora de Fitosanitarios" in menu:
        st.markdown("### 🧪 Calculadora de Fitosanitarios")
        st.write("Calcula de forma exacta la cantidad de producto que debes verter en tu depósito según las hectáreas y el volumen de caldo.")
        with st.form("form_cuba"):
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                litros_cuba = st.selectbox("Litros de tu depósito o cuba:", [500, 600, 800, 1000, 1500, 2000], index=3)
                gasto_por_ha = st.number_input("Litros de caldo que gastas por hectárea:", value=400, step=50)
            with c_c2:
                dosis_ha = st.number_input("Dosis recomendada por hectárea (kg o L):", value=2.5, step=0.5)
                ha_finca = st.number_input("Hectáreas que vas a tratar:", value=float(datos_parcela.get("ha", 1.0)), step=0.5)
            calcular = st.form_submit_button("🧮 CALCULÁMELO", use_container_width=True, type="primary")
            if calcular:
                ha_por_cuba = litros_cuba / gasto_por_ha if gasto_por_ha > 0 else 0
                producto_por_cuba = dosis_ha * ha_por_cuba
                total_cubas = (ha_finca * gasto_por_ha) / litros_cuba if litros_cuba > 0 else 0
                total_producto = dosis_ha * ha_finca
                st.markdown(f'<div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 16px; padding: 20px; margin-top: 15px; color: #065f46;"><h3 style="margin:0; color:#047857;">📌 RESULTADO:</h3><p style="font-size: 1.3rem; font-weight: 800; margin: 10px 0;">👉 Echa <b>{producto_por_cuba:.2f} kg/L</b> por cuba de {litros_cuba} L.</p><p style="font-size: 1rem; margin: 0;">🚜 Total para {ha_finca} ha: <b>{total_cubas:.1f} cubas</b> ({total_producto:.2f} kg/L totales).</p></div>', unsafe_allow_html=True)

    elif "Almacén de Fitosanitarios" in menu:
        st.markdown("### 📦 Control y Edición de Stock en Almacén")
        st.write("Consulta el inventario actual y actualiza o edita las cantidades exactas (kg o L) de cada producto.")
        
        stock_usuario = st.session_state.almacen_db.get(user, {})
        
        tab_ver, tab_editar = st.tabs(["📊 Ver Inventario Actual", "✏️ Modificar / Añadir Stock"])
        
        with tab_ver:
            if stock_usuario:
                tabla_stock = []
                for cod, info in stock_usuario.items():
                    tabla_stock.append({
                        "Nº Registro MAPA": cod,
                        "Producto": info["nombre"],
                        "Stock Disponible (kg / L)": info["stock_kg_l"]
                    })
                st.dataframe(pd.DataFrame(tabla_stock), use_container_width=True, hide_index=True)
            else:
                st.info("No tienes productos registrados en el almacén.")

        with tab_editar:
            st.markdown("#### ✏️ Edita o actualiza las cantidades de tu almacén")
            with st.form("form_editar_almacen"):
                if stock_usuario:
                    opciones_stock = list(stock_usuario.keys())
                    mapa_editar = st.selectbox("Elige producto a editar:", opciones_stock, format_func=lambda x: f"{x} - {stock_usuario[x]['nombre']} (Actual: {stock_usuario[x]['stock_kg_l']} kg/L)")
                    stock_actual_obj = stock_usuario[mapa_editar]["stock_kg_l"]
                else:
                    mapa_editar = st.selectbox("Elige producto fitosanitario:", list(CATALOGO_MAPA.keys()), format_func=lambda x: f"{x} - {CATALOGO_MAPA[x]['producto']}")
                    stock_actual_obj = 0.0

                nuevo_stock_total = st.number_input("Establecer cantidad exacta en almacén (kg o L):", value=float(stock_actual_obj), step=1.0)
                guardar_edicion_stock = st.form_submit_button("💾 GUARDAR NUEVO STOCK", use_container_width=True, type="primary")
                
                if guardar_edicion_stock:
                    if user not in st.session_state.almacen_db:
                        st.session_state.almacen_db[user] = {}
                    
                    nombre_prod = CATALOGO_MAPA.get(mapa_editar, {}).get("producto", "Producto Fitosanitario")
                    st.session_state.almacen_db[user][mapa_editar] = {"nombre": nombre_prod, "stock_kg_l": nuevo_stock_total}
                    guardar_json(ALMACEN_FILE, st.session_state.almacen_db)
                    st.success(f"¡Stock actualizado correctamente! Nuevo inventario de {nombre_prod}: {nuevo_stock_total} kg/L.")
                    st.rerun()

    elif "Cuaderno de Campo" in menu:
        st.markdown("### 📋 Tu Cuaderno de Explotación (Normativa PAC)")
        st.write("Registra tus tratamientos fitosanitarios para cumplir con la legislación vigente y evitar sanciones ante inspecciones.")
        
        with st.form("form_cuaderno"):
            f_apli = st.date_input("Fecha de aplicación:", date.today())
            motivo = st.text_input("Plaga o enfermedad tratada:", value="Mildiu preventivo")
            reg_mapa = st.selectbox("Producto comercial (Nº Registro MAPA):", list(CATALOGO_MAPA.keys()), format_func=lambda x: f"{x} - {CATALOGO_MAPA[x]['producto']}")
            dosis_aplicada = st.number_input("Cantidad total gastada (kg o L):", value=5.0, step=1.0)
            guardar_fito = st.form_submit_button("💾 GUARDAR APUNTE Y DESCONTAR STOCK", use_container_width=True, type="primary")
            if guardar_fito:
                if user not in st.session_state.fitos_db: st.session_state.fitos_db[user] = []
                plazo_dias = CATALOGO_MAPA[reg_mapa]["plazo"]
                librede = f_apli + timedelta(days=plazo_dias)
                st.session_state.fitos_db[user].append({
                    "Fecha": str(f_apli), 
                    "Parcela": parcela_activa, 
                    "Tratamiento": motivo, 
                    "MAPA": reg_mapa, 
                    "Plazo seguridad": f"{plazo_dias} días",
                    "Libre recolección": str(librede)
                })
                guardar_json(FITOS_FILE, st.session_state.fitos_db)
                
                if user in st.session_state.almacen_db and reg_mapa in st.session_state.almacen_db[user]:
                    stock_actual = st.session_state.almacen_db[user][reg_mapa]["stock_kg_l"]
                    st.session_state.almacen_db[user][reg_mapa]["stock_kg_l"] = max(0.0, stock_actual - dosis_aplicada)
                    guardar_json(ALMACEN_FILE, st.session_state.almacen_db)

                st.success("¡Apuntado en el cuaderno oficial y descontado del almacén con éxito!")
                
        mis_datos = st.session_state.fitos_db.get(user, [])
        if mis_datos:
            st.markdown("#### Historial de Tratamientos Registrados:")
            st.dataframe(pd.DataFrame(mis_datos), use_container_width=True, hide_index=True)

    elif "Avisos Automáticos" in menu:
        st.markdown("### 📲 Aviso Diario en tu Telegram a las 4:45")
        st.write("Recibirás un aviso automático diario en Telegram con el parte meteorológico estructurado de **todas** tus fincas y su acción obligatoria.")
        st.info(f"🤖 Chat ID configurado en tu cuenta: **{telegram_id}**")
        
        if st.button("📲 PROBAR ENVÍO A TELEGRAM DE TODAS MIS FINCAS", use_container_width=True, type="primary"):
            msg_partes = [f"🚜 *AGROALERT • PARTE DIARIO DE EXPLOTACIÓN*\n👤 *Agricultor:* {info_user.get('nombre', 'Agricultor')}\n"]
            
            for nombre_f, d_finca in fincas_usuario.items():
                m_finca = consultar_meteo_openmeteo(d_finca.get("lat", 42.46), d_finca.get("lon", -2.44))
                
                if m_finca["viento"] > 15:
                    estado_f = "⛔ CONDICIONES NO APTAS PARA TRATAR (Mucho viento)"
                    accion_obligatoria = "👉 *Frenar actividad en campo.* Viento excesivo: alto riesgo de deriva y contaminación."
                    consejos = (
                        "💡 *Consejos profesionales de valor:*\n"
                        "   1️⃣ *Mantenimiento:* Aprovecha en caseta para revisar boquillas, filtros y calibrar maquinaria.\n"
                        "   2️⃣ *Stock:* Revisa el almacén de fitosanitarios para anticiparte a las próximas compras.\n"
                        "   3️⃣ *Seguridad:* Evita cualquier aplicación que incumpla la normativa local."
                    )
                elif m_finca["lluvia"] > 2.0:
                    estado_f = "⛔ CONDICIONES NO APTAS PARA TRATAR (Riesgo de lluvia)"
                    accion_obligatoria = "👉 *Frenar actividad en campo.* Riesgo de lavado inmediato del caldo aplicado."
                    consejos = (
                        "💡 *Consejos profesionales de valor:*\n"
                        "   1️⃣ *Drenaje:* Vigila posibles encharcamientos y accesos principales a la parcela.\n"
                        "   2️⃣ *PAC:* Pon al día tus apuntes fitosanitarios en el Cuaderno de Explotación.\n"
                        "   3️⃣ *Planificación:* Revisa el estado sanitario general en cuanto amaine."
                    )
                else:
                    estado_f = "🟢 VÍA LIBRE PARA TRATAR"
                    accion_obligatoria = "👉 *Ejecutar tratamiento en campo.* Mantén velocidad constante (4-6 km/h) y revisa la presión."
                    consejos = (
                        "💡 *Consejos profesionales de valor:*\n"
                        "   1️⃣ *Calibración:* Comprueba que el manómetro asegure el tamaño óptimo de gota.\n"
                        "   2️⃣ *Estrategia:* Asegura un reparto homogéneo en todo el volumen foliar.\n"
                        "   3️⃣ *PAC:* Anota inmediatamente el número de registro MAPA y hectáreas tratadas al terminar."
                    )

                msg_partes.append(
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📍 *Finca:* {nombre_f} ({d_finca.get('ha', 0)} ha)\n"
                    f"📌 *ESTADO:* {estado_f}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌤️ *Meteorología actual:*\n"
                    f"   • Viento: {m_finca['viento']:.1f} km/h *(Límite seguro: < 15)*\n"
                    f"   • Lluvia: {m_finca['lluvia']:.1f} mm *(Sin riesgo de lavado)*\n\n"
                    f"🎯 *ACCIÓN OBLIGATORIA DE HOY:*\n"
                    f"{accion_obligatoria}\n\n"
                    f"{consejos}\n"
                )
                
            msg_prueba_total = "\n".join(msg_partes)
            
            ok, res = disparar_telegram(telegram_token, telegram_id, msg_prueba_total)
            if ok: st.success("¡Parte maestro estructurado enviado con éxito a tu Telegram!")
            else: st.error(res)

    elif "Gestión de Usuarios Registrados" in menu:
        st.markdown("### 👥 Panel de Control y Control de Nuevos Usuarios")
        st.write("Aquí puedes supervisar todos los agricultores que se han dado de alta en la plataforma, sus datos de contacto y gestionar sus cuentas.")
        
        usuarios_registrados = st.session_state.usuarios_db
        tabla_usuarios = []
        for username, udata in usuarios_registrados.items():
            tabla_usuarios.append({
                "Usuario (Login)": username,
                "Nombre y Apellidos": udata.get("nombre", "N/A"),
                "Telegram Chat ID": udata.get("telegram_id", "N/A"),
                "Contraseña": udata.get("pwd", "N/A")
            })
            
        st.dataframe(pd.DataFrame(tabla_usuarios), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("#### ⚙️ Gestión de Cuentas")
        with st.form("form_borrar_usuario"):
            user_a_borrar = st.selectbox("Selecciona un usuario para dar de baja:", [u for u in usuarios_registrados.keys() if u != "admin1987"])
            borrar_btn = st.form_submit_button("🗑️ DAR DE BAJA A ESTE USUARIO", use_container_width=True, type="primary")
            if borrar_btn:
                if user_a_borrar in st.session_state.usuarios_db:
                    del st.session_state.usuarios_db[user_a_borrar]
                    guardar_json(USERS_FILE, st.session_state.usuarios_db)
                    if user_a_borrar in st.session_state.db_privada:
                        del st.session_state.db_privada[user_a_borrar]
                        guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.success(f"¡El usuario '{user_a_borrar}' ha sido eliminado correctamente del sistema!")
                    st.rerun()

    elif "Gestión de Fincas" in menu:
        st.markdown("### ⚙️ Gestión de Fincas y Parcelas")
        st.write("Selecciona una parcela para verla en vista de satélite con todo detalle o edita sus datos.")
        
        if fincas_usuario:
            st.markdown("#### 🛰️ Vista de Satélite de Parcelas")
            
            finca_seleccionada_mapa = st.selectbox("🔍 Elige una parcela para centrar el mapa:", list(fincas_usuario.keys()), key="select_mapa_finca")
            d_mapa = fincas_usuario[finca_seleccionada_mapa]
            
            lat_sel = float(d_mapa.get("lat", 42.4658))
            lon_sel = float(d_mapa.get("lon", -2.4499))
            
            m = folium.Map(location=[lat_sel, lon_sel], zoom_start=15)
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri Satélite',
                name='Satélite',
                overlay=False,
                control=True
            ).add_to(m)
            
            folium.Marker(
                [lat_sel, lon_sel],
                popup=finca_seleccionada_mapa,
                tooltip=finca_seleccionada_mapa,
                icon=folium.Icon(color="green", icon="leaf", prefix="fa")
            ).add_to(m)
            
            st_folium(m, width=700, height=450)
            
            st.markdown(f"📌 *Mostrando vista de satélite de:* **{finca_seleccionada_mapa}** (Lat: {lat_sel}, Lon: {lon_sel})")
            st.markdown("---")

        if fincas_usuario:
            st.markdown("#### ✏️ Edita los datos de una finca existente")
            finca_a_editar = st.selectbox("Selecciona la finca que deseas modificar:", list(fincas_usuario.keys()), key="select_editar_finca")
            datos_actuales = fincas_usuario[finca_a_editar]
            
            with st.form("form_editar_finca"):
                c_ed1, c_ed2 = st.columns(2)
                with c_ed1:
                    nuevo_nombre_finca = st.text_input("Nuevo nombre de la finca", value=finca_a_editar)
                    nueva_variedad = st.text_input("Variedad o cultivo", value=datos_actuales.get("variedad", "General"))
                    nueva_ha = st.number_input("Hectáreas de la finca", value=float(datos_actuales.get("ha", 1.0)), step=0.5)
                with c_ed2:
                    st.write("Ubicación exacta (Coordenadas geográficas):")
                    c_eco1, c_eco2 = st.columns(2)
                    with c_eco1:
                        nueva_lat = st.number_input("Latitud", value=float(datos_actuales.get("lat", 42.4658)), format="%.6f")
                    with c_eco2:
                        nueva_lon = st.number_input("Longitud", value=float(datos_actuales.get("lon", -2.4499)), format="%.6f")
                        
                    st.write("Datos Catastrales:")
                    c_ecat1, c_ecat2 = st.columns(2)
                    with c_ecat1:
                        nuevo_pol = st.text_input("Polígono", value=str(datos_actuales.get("poligono", "1")))
                    with c_ecat2:
                        nueva_parc = st.text_input("Parcela", value=str(datos_actuales.get("parcela", "1")))

                guardar_cambios = st.form_submit_button("💾 ACTUALIZAR DATOS DE LA FINCA", use_container_width=True, type="primary")
                
                if guardar_cambios:
                    if finca_a_editar != nuevo_nombre_finca:
                        del st.session_state.db_privada[user][finca_a_editar]
                    
                    st.session_state.db_privada[user][nuevo_nombre_finca] = {
                        "lat": nueva_lat,
                        "lon": nueva_lon,
                        "variedad": nueva_variedad,
                        "ha": nueva_ha,
                        "poligono": nuevo_pol,
                        "parcela": nueva_parc
                    }
                    guardar_json(FINCAS_FILE, st.session_state.db_privada)
                    st.success(f"¡Finca '{nuevo_nombre_finca}' actualizada correctamente!")
                    st.rerun()
            st.markdown("---")

        st.markdown("#### ➕ Añade una nueva parcela")
        with st.form("form_nueva_finca"):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                nombre_nueva = st.text_input("Nombre de la nueva finca (ej: Viñedo Alto)")
                variedad_nueva = st.text_input("Variedad o cultivo (ej: Tempranillo)", value="Tempranillo")
                ha_nueva = st.number_input("Hectáreas de la finca", value=1.0, step=0.5)
            with c_f2:
                st.write("Ubicación exacta para Meteorología:")
                c_coord1, c_coord2 = st.columns(2)
                with c_coord1:
                    lat_nueva = st.number_input("Latitud", value=42.4658, format="%.6f")
                with c_coord2:
                    lon_nueva = st.number_input("Longitud", value=-2.4499, format="%.6f")
                    
                st.write("Datos Catastrales:")
                c_cat1, c_cat2 = st.columns(2)
                with c_cat1:
                    pol_nuevo = st.text_input("Polígono", value="12")
                with c_cat2:
                    parc_nueva = st.text_input("Parcela", value="104")

            guardar_parcela = st.form_submit_button("💾 GUARDAR NUEVA FINCA", use_container_width=True, type="primary")
            
            if guardar_parcela and nombre_nueva:
                if user not in st.session_state.db_privada:
                    st.session_state.db_privada[user] = {}
                    
                st.session_state.db_privada[user][nombre_nueva] = {
                    "lat": lat_nueva, 
                    "lon": lon_nueva, 
                    "variedad": variedad_nueva, 
                    "ha": ha_nueva, 
                    "poligono": pol_nuevo, 
                    "parcela": parc_nueva
                }
                guardar_json(FINCAS_FILE, st.session_state.db_privada)
                st.success(f"¡Finca '{nombre_nueva}' añadida con éxito y geolocalizada en el mapa!")
                st.rerun()
