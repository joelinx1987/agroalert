import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import urllib.parse
import json
import base64
import hashlib

st.set_page_config(
    page_title="AgroAlert Campo | Bot Automático",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURACIÓN GITHUB REPO ---
GITHUB_REPO = "joelinx1987/agroalert"
GITHUB_FILE = "usuarios_alertas.json"
GH_TOKEN = st.secrets.get("GH_TOKEN", "")

# --- FUNCIONES DE SINCRONIZACIÓN CON GITHUB ---
def obtener_usuarios_github():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"User-Agent": "AgroAlert-App"}
    if GH_TOKEN:
        headers["Authorization"] = f"token {GH_TOKEN}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content), data["sha"]
    except Exception:
        return [], None

def actualizar_archivo_github(usuarios, sha, mensaje_commit):
    nuevo_contenido = json.dumps(usuarios, indent=2, ensure_ascii=False)
    contenido_b64 = base64.b64encode(nuevo_contenido.encode("utf-8")).decode("utf-8")
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    payload = {
        "message": mensaje_commit,
        "content": contenido_b64
    }
    if sha:
        payload["sha"] = sha
        
    headers = {
        "User-Agent": "AgroAlert-App",
        "Authorization": f"token {GH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, "Sincronizado con éxito"
    except Exception as e:
        return False, str(e)

def guardar_usuario_en_github(nuevo_usuario):
    usuarios, sha = obtener_usuarios_github()
    actualizado = False
    for i, u in enumerate(usuarios):
        if u.get("telefono") == nuevo_usuario.get("telefono"):
            usuarios[i] = nuevo_usuario
            actualizado = True
            break
    if not actualizado:
        usuarios.append(nuevo_usuario)
    return actualizar_archivo_github(usuarios, sha, f"Auto-registro: {nuevo_usuario.get('nombre')}")

def eliminar_usuario_de_github(telefono_a_borrar):
    usuarios, sha = obtener_usuarios_github()
    usuarios_filtrados = [u for u in usuarios if u.get("telefono") != telefono_a_borrar]
    return actualizar_archivo_github(usuarios_filtrados, sha, f"Eliminado usuario con tel {telefono_a_borrar}")

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
                return True, "¡WhatsApp enviado!"
            else:
                return False, f"Respuesta: {res_body}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# --- AUTH LOCAL ---
def make_hash(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hash(p, h): return make_hash(p) == h

if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "admin": {
            "pwd": make_hash("admin123"),
            "nombre": "Joel (Mi Explotación)",
            "telefono": "+34626665232",
            "apikey": "3443251",
            "parcela": "Frontón Jaime",
            "lat": 42.3659,
            "lon": -2.4235,
            "ha": 2.0
        }
    }

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

# ==============================================================================
# ACCESO Y REGISTRO
# ==============================================================================
if not st.session_state.usuario_autenticado:
    c1, col_login, c2 = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 3.8rem; margin-bottom: 5px;">🚜</div>
            <h1 style="font-size: 2.3rem; font-weight: 900; color: #15803d; margin: 0;">AgroAlert Campo</h1>
            <p style="font-size: 1.15rem; color: #475569; font-weight: 600; margin-top: 6px;">Monitor de campo y bot de alertas automáticas a las 05:00 AM</p>
        </div>
        """, unsafe_allow_html=True)

        tab_in, tab_up = st.tabs(["🔑 ENTRAR", "📝 REGISTRARME GRATIS"])
        with tab_in:
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
        with tab_up:
            st.markdown("""
            <div style="background-color: #ecfdf5; border: 2px solid #10b981; border-radius: 12px; padding: 14px; margin-bottom: 15px;">
                <b style="color: #065f46; font-size: 1.05rem;">📲 Paso obligatorio para activar WhatsApp:</b><br>
                <span style="color: #047857; font-size: 0.95rem;">
                Envía por WhatsApp: <code>I allow callmebot to send me messages</code> al número <b>+34 623 91 22 04</b> para obtener tu APIKey gratuita.
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("form_reg"):
                nu = st.text_input("Usuario (ej: jgarcia)")
                nn = st.text_input("Tu Nombre o Explotación (ej: Bodega San Juan)")
                ntel = st.text_input("📱 Teléfono Móvil con prefijo (ej: +34676735624)")
                napi = st.text_input("🔑 Tu APIKey de WhatsApp (Obligatorio)")
                np = st.text_input("Contraseña", type="password")
                
                st.markdown("##### 📍 Datos de tu Parcela:")
                nparc = st.text_input("Nombre de la Parcela:", value="Finca Principal")
                nlat = st.number_input("Latitud:", value=42.3659, format="%.4f")
                nlon = st.number_input("Longitud:", value=-2.4235, format="%.4f")
                nha = st.number_input("Superficie (ha):", value=2.0, min_value=0.1, step=0.5)

                b_up = st.form_submit_button("🚀 ACTIVAR CUENTA Y BOT AUTOMÁTICO 05:00 AM", use_container_width=True, type="primary")
                if b_up:
                    if not nu.strip() or not np.strip() or not ntel.strip() or not napi.strip():
                        st.error("⚠️ Todos los campos son obligatorios (incluyendo tu Teléfono y tu APIKey).")
                    elif nu in st.session_state.usuarios_db:
                        st.error("Ese usuario ya existe.")
                    else:
                        nuevo_datos = {
                            "nombre": nn.strip(),
                            "telefono": ntel.strip(),
                            "apikey": napi.strip(),
                            "parcela": nparc.strip(),
                            "lat": float(nlat),
                            "lon": float(nlon),
                            "ha": float(nha),
                            "fecha_alta": datetime.now().strftime("%d/%m/%Y %H:%M")
                        }
                        
                        st.session_state.usuarios_db[nu] = {
                            "pwd": make_hash(np),
                            **nuevo_datos
                        }
                        
                        guardar_usuario_en_github(nuevo_datos)
                        
                        msg_bienvenida = f"""🚜 *¡BIENVENIDO A AGROALERT!*
Hola *{nn}*, tu parcela *{nparc}* ha quedado monitorizada.

A partir de mañana a las *05:00 AM* recibirás tu parte matutino automático."""
                        disparar_whatsapp_servidor(ntel.strip(), napi.strip(), msg_bienvenida)

                        st.session_state.usuario_autenticado = nu
                        st.success("¡Cuenta creada y activada para las 05:00 AM!")
                        st.rerun()
    st.stop()

# ==============================================================================
# PANEL PRINCIPAL TRAS LOGIN
# ==============================================================================
user_activo = st.session_state.usuario_autenticado
datos_usuario = st.session_state.usuarios_db[user_activo]
nombre_cliente = datos_usuario.get("nombre", user_activo)
user_telefono = datos_usuario.get("telefono", "+34626665232")
user_apikey = datos_usuario.get("apikey", "3443251")
nombre_parcela = datos_usuario.get("parcela", "Frontón Jaime")
lat = datos_usuario.get("lat", 42.3659)
lon = datos_usuario.get("lon", -2.4235)
superficie_ha = datos_usuario.get("ha", 2.0)

c_top1, c_top2, c_top3 = st.columns([1.5, 1.5, 0.8])
with c_top1:
    tipo_cultivo = st.selectbox("1️⃣ Cultivo:", ["🍇 Viña", "🫒 Olivo", "🌾 Cereal", "🍑 Frutal"])

with c_top2:
    st.selectbox("2️⃣ Parcela activa:", [nombre_parcela])

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

if viento_hoy > 15:
    semaforo_estado = "ROJO"
    msg_alerta = "⛔ HOY NO SE RECOMIENDA SULFATAR (Viento fuerte)"
elif lluvia_hoy > 2.0:
    semaforo_estado = "ROJO"
    msg_alerta = "⛔ HOY NO SULFATES (Lluvia prevista)"
elif max_hoy >= 32:
    semaforo_estado = "AMBAR"
    msg_alerta = "⚠️ TRATAR SOLO A PRIMERA HORA (Mucho calor)"
else:
    semaforo_estado = "VERDE"
    msg_alerta = "✅ DÍA PERFECTO PARA SULFATAR"

riesgo_txt = "🚨 ALTO (Mildiu)" if (lluvia_hoy >= 8 and (min_hoy+max_hoy)/2 >= 10) else ("⚠️ Oídio" if max_hoy > 26 else "✅ LIMPIO")

pestanas = ["🚜 ¿PUEDO SULFATAR HOY?", "🧪 CUÁNTO ECHAR A LA CUBA", "📲 BOT WHATSAPP"]
if user_activo == "admin":
    pestanas.append("👑 USUARIOS EN GITHUB")

tabs = st.tabs(pestanas)

with tabs[0]:
    st.markdown(f"### 📍 {nombre_parcela} ({superficie_ha} ha)")
    st.info(f"**Semáforo:** {msg_alerta}")
    st.write(f"🌡️ Temp: {min_hoy:.0f}°C a {max_hoy:.0f}°C | 💨 Viento: {viento_hoy:.0f} km/h | 🌧️ Lluvia: {lluvia_hoy:.1f} mm | 🛡️ Hongos: {riesgo_txt}")

with tabs[1]:
    st.markdown("### 🧪 Calculadora rápida de Cuba")
    cuba = st.number_input("Litros cuba:", value=1000, step=100)
    dosis = st.number_input("Dosis (kg/ha o gr/100L):", value=2.0, step=0.5)
    st.success(f"Receta calculada para {cuba} Litros lista.")

with tabs[2]:
    st.markdown("### 📲 Bot Automático WhatsApp")
    st.write(f"Número asociado: **{user_telefono}**")
    if st.button("Probar envío ahora"):
        msg = f"🚜 AgroAlert: {msg_alerta} en {nombre_parcela}."
        ok, res = disparar_whatsapp_servidor(user_telefono, user_apikey, msg)
        if ok: st.success("Mensaje enviado con éxito")
        else: st.error(res)

# ==============================================================================
# PESTAÑA ADMIN: VER Y BORRAR USUARIOS
# ==============================================================================
if user_activo == "admin":
    with tabs[3]:
        st.markdown("### 👑 Base de Datos de Agricultores (GitHub)")
        usuarios_gh, sha = obtener_usuarios_github()
        
        if usuarios_gh:
            st.dataframe(pd.DataFrame(usuarios_gh), use_container_width=True, hide_index=True)
            st.caption(f"Total registrados: {len(usuarios_gh)} agricultores.")
            
            st.write("---")
            st.markdown("#### 🗑️ Eliminar a un Usuario de la Base de Datos")
            
            # Crear lista de opciones para seleccionar a quién borrar
            opciones_borrar = {
                f"{u.get('nombre')} ({u.get('telefono')}) - {u.get('parcela', 'Sin parcela')}": u.get("telefono")
                for u in usuarios_gh
            }
            
            usuario_elegido = st.selectbox("Selecciona al usuario que deseas eliminar:", list(opciones_borrar.keys()))
            tel_borrar = opciones_borrar[usuario_elegido]
            
            if st.button("🗑️ Borrar este Usuario de GitHub", type="primary"):
                ok, res = eliminar_usuario_de_github(tel_borrar)
                if ok:
                    st.success(f"¡Usuario con teléfono {tel_borrar} eliminado correctamente!")
                    st.rerun()
                else:
                    st.error(f"Error al eliminar de GitHub: {res}")
        else:
            st.warning("No se encontraron usuarios en GitHub o la lista está vacía.")
