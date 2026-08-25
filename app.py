import os
import json
import hashlib
import urllib.request
import urllib.parse
from datetime import date, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AgroAlert | Centro de control agrícola", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# CONFIGURACIÓN SEGURA
# ============================================================
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")

# Usuario administrador solicitado. La contraseña no se guarda en texto plano:
# se compara contra su hash SHA-256.
ADMIN_USER = "admin1987"
ADMIN_PASSWORD_HASH = "c499244afdc389678cb2273a31fed27655e86a42a6f1fa2fdb112f73da8a5acb"

# ============================================================
# DATOS
# ============================================================
USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"
FITOS_FILE = "fitosanitarios_db.json"
ALMACEN_FILE = "almacen_db.json"
CATALOGO = {
    "ES-00123": {"producto":"Oxicloruro de Cobre 50%", "plazo":14},
    "ES-00456": {"producto":"Azufre Mojable 80%", "plazo":5},
    "ES-00789": {"producto":"Cipermetrina 10%", "plazo":21},
    "ES-00999": {"producto":"Fosetil-Al 80%", "plazo":15},
    "ES-01111": {"producto":"Mancozeb 80%", "plazo":28},
    "ES-02222": {"producto":"Difenoconazol 25%", "plazo":21},
}

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def password_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def usuario_valido(usuario, password):
    if usuario == ADMIN_USER:
        return password_hash(password) == ADMIN_PASSWORD_HASH
    datos = st.session_state.usuarios_db.get(usuario, {})
    if datos.get("pwd_hash"):
        return password_hash(password) == datos["pwd_hash"]
    return datos.get("pwd") == password

if "usuarios_db" not in st.session_state: st.session_state.usuarios_db = load_json(USERS_FILE,{})
if "db_privada" not in st.session_state: st.session_state.db_privada = load_json(FINCAS_FILE,{})
if "fitos_db" not in st.session_state: st.session_state.fitos_db = load_json(FITOS_FILE,{})
if "almacen_db" not in st.session_state: st.session_state.almacen_db = load_json(ALMACEN_FILE,{})
if "usuario_autenticado" not in st.session_state: st.session_state.usuario_autenticado = None

# Garantiza que el administrador exista, conservando datos previos como Telegram.
_admin = st.session_state.usuarios_db.get(ADMIN_USER, {})
_admin["nombre"] = _admin.get("nombre", "Joel (La Rioja)")
_admin["pwd_hash"] = ADMIN_PASSWORD_HASH
_admin.pop("pwd", None)
st.session_state.usuarios_db[ADMIN_USER] = _admin

# ============================================================
# DISEÑO AGROALERT 2.0
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--g:#176b45;--g2:#238657;--soft:#eaf7ef;--ink:#17352a;--muted:#718078;--line:#e4ebe6}
html,body,[class*="css"]{font-family:Inter,sans-serif!important}
.stApp{background:linear-gradient(180deg,#f7faf7,#f1f5f1);color:var(--ink)}
.block-container{max-width:1450px;padding-top:1.2rem;padding-bottom:3rem}
#MainMenu,footer{visibility:hidden}
.hero{background:linear-gradient(135deg,#123f2c,#176b45 60%,#2b9662);color:white;border-radius:26px;padding:28px 30px;margin-bottom:20px;box-shadow:0 18px 45px rgba(23,107,69,.15)}
.hero h1{margin:0;font-size:2.15rem;font-weight:800;letter-spacing:-.04em}.hero p{margin:7px 0 0;opacity:.84}
.section{font-size:1.15rem;font-weight:800;margin:22px 0 10px;color:var(--ink)}
.card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:19px;box-shadow:0 5px 20px rgba(20,50,35,.045);height:100%}
.kicker{font-size:.76rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}.value{font-size:1.75rem;font-weight:800;margin-top:4px}.sub{font-size:.8rem;color:var(--muted);margin-top:3px}
.ok{background:linear-gradient(135deg,#eaf8ef,#d9f2e2);border:1px solid #a9ddbd;color:#155b38;border-radius:22px;padding:22px}.bad{background:linear-gradient(135deg,#fff0ef,#ffe2e0);border:1px solid #f0b3ae;color:#8e302b;border-radius:22px;padding:22px}.status{font-size:1.35rem;font-weight:800}
.alert{border:1px solid var(--line);border-left:4px solid #38a169;background:#fff;border-radius:14px;padding:12px 14px;margin-bottom:8px}.alert.warn{border-left-color:#e9a23b}.alert.red{border-left-color:#d9534f}.alert strong{display:block;font-size:.88rem}.alert span{font-size:.78rem;color:var(--muted)}
.weather{background:#fff;border:1px solid var(--line);border-radius:17px;padding:13px;text-align:center}.weather small{color:var(--muted);font-weight:700}.weather b{display:block;font-size:1.1rem;margin-top:5px}
.quick{background:#fff;border:1px solid var(--line);border-radius:17px;padding:16px;text-align:center}.quick div:first-child{font-size:1.6rem}.quick div:last-child{font-size:.8rem;font-weight:700;margin-top:5px}
div[data-testid="stButton"] button{border-radius:12px!important;font-weight:700!important;min-height:42px}div[data-testid="stButton"] button[kind="primary"]{background:linear-gradient(135deg,#1d7b4f,#176b45)!important;color:#fff!important;border:0!important}
.stTabs [data-baseweb="tab"]{font-weight:700;border-radius:10px}.stTabs [aria-selected="true"]{background:var(--soft);color:var(--g)}
@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.hero{padding:22px}.hero h1{font-size:1.7rem}}
</style>
""",unsafe_allow_html=True)

# ============================================================
# SERVICIOS
# ============================================================
def meteo(lat,lon):
    try:
        url=(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
             "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
             "&hourly=temperature_2m,precipitation,wind_speed_10m&timezone=auto")
        req=urllib.request.Request(url,headers={"User-Agent":"AgroAlert/2.0"})
        with urllib.request.urlopen(req,timeout=6) as r: d=json.loads(r.read().decode())
        c=d.get("current",{}); h=d.get("hourly",{})
        rows=[]
        for t,x,w,p in zip(h.get("time",[])[:8],h.get("temperature_2m",[])[:8],h.get("wind_speed_10m",[])[:8],h.get("precipitation",[])[:8]):
            rows.append({"hora":t.split("T")[-1][:5],"temp":x,"viento":w,"lluvia":p})
        return {"temp":c.get("temperature_2m",22),"hum":c.get("relative_humidity_2m",50),"rain":c.get("precipitation",0),"wind":c.get("wind_speed_10m",8),"rows":rows}
    except Exception:
        return {"temp":22,"hum":50,"rain":0,"wind":8,"rows":[]}

def enviar_telegram(chat_id, mensaje):
    if not TELEGRAM_TOKEN:
        return False, "El token de Telegram no está configurado en Streamlit Secrets."
    if not chat_id:
        return False, "Este usuario no tiene un Chat ID de Telegram configurado."
    try:
        url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data=urllib.parse.urlencode({"chat_id":chat_id,"text":mensaje,"parse_mode":"Markdown"}).encode("utf-8")
        req=urllib.request.Request(url,data=data,headers={"User-Agent":"AgroAlert/2.0"})
        with urllib.request.urlopen(req,timeout=10):
            return True,"Aviso enviado correctamente."
    except Exception as e:
        return False,f"No se pudo enviar el aviso: {e}"

# ============================================================
# LOGIN
# ============================================================
if not st.session_state.usuario_autenticado:
    st.markdown("<div class='hero'><div style='font-weight:700;opacity:.7'>AGROALERT 2.0</div><h1>Tu explotación, bajo control.</h1><p>Clima, tratamientos, parcelas, almacén y cuaderno de campo en un solo lugar.</p></div>",unsafe_allow_html=True)
    _,col,_=st.columns([1,1.2,1])
    with col:
        st.markdown("<div class='card'>",unsafe_allow_html=True)
        tab1,tab2=st.tabs(["🔐 Acceder","✨ Crear cuenta"])
        with tab1:
            with st.form("login"):
                u=st.text_input("Usuario", value=ADMIN_USER).strip().lower()
                pwd=st.text_input("Contraseña",type="password", value="admin1987")
                if st.form_submit_button("Entrar a mi explotación",use_container_width=True,type="primary"):
                    if usuario_valido(u, pwd):
                        st.session_state.usuario_autenticado=u
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        with tab2:
            with st.form("registro"):
                u=st.text_input("Nombre de usuario").strip().lower(); pwd=st.text_input("Contraseña",type="password"); n=st.text_input("Nombre y apellidos")
                chat_id=st.text_input("Chat ID de Telegram (opcional)")
                finca=st.text_input("Nombre de la primera parcela",value="🌾 Mi finca"); ha=st.number_input("Superficie (ha)",min_value=.1,value=2.0,step=.5); lat=st.number_input("Latitud",value=42.4658); lon=st.number_input("Longitud",value=-2.4499)
                if st.form_submit_button("Crear mi cuenta",use_container_width=True,type="primary"):
                    if not u or not pwd: st.error("Indica usuario y contraseña.")
                    elif u in st.session_state.usuarios_db: st.error("Ese usuario ya existe.")
                    else:
                        st.session_state.usuarios_db[u]={"pwd_hash":password_hash(pwd),"nombre":n or u,"telegram_id":chat_id.strip()}
                        st.session_state.db_privada[u]={finca:{"lat":lat,"lon":lon,"ha":ha,"variedad":"General","poligono":"1","parcela":"1"}}
                        save_json(USERS_FILE,st.session_state.usuarios_db); save_json(FINCAS_FILE,st.session_state.db_privada); st.success("Cuenta creada. Ya puedes acceder.")
        st.markdown("</div>",unsafe_allow_html=True)
    st.stop()

# ============================================================
# CONTEXTO
# ============================================================
user=st.session_state.usuario_autenticado; ui=st.session_state.usuarios_db.get(user,{})
fincas=st.session_state.db_privada.get(user,{})
if not fincas:
    fincas={"🌾 Mi finca":{"lat":42.4658,"lon":-2.4499,"ha":1,"variedad":"General"}}; st.session_state.db_privada[user]=fincas
parcela=st.selectbox("Parcela activa",list(fincas),label_visibility="collapsed")
p=fincas[parcela]; w=meteo(p.get("lat",42.46),p.get("lon",-2.44)); stock=st.session_state.almacen_db.get(user,{})
registros=st.session_state.fitos_db.get(user,[])

h1,h2,h3=st.columns([2.2,3,1])
with h1: st.markdown(f"<div class='kicker'>CENTRO DE CONTROL</div><div style='font-size:1.5rem;font-weight:800'>Hola, {ui.get('nombre',user).split('(')[0].strip()} 👋</div>",unsafe_allow_html=True)
with h2: st.markdown(f"<div class='card' style='padding:10px 14px'>📍 <b>{parcela}</b><br><span class='sub'>{p.get('ha',0)} ha · {p.get('variedad','Cultivo')}</span></div>",unsafe_allow_html=True)
with h3:
    if st.button("Cerrar sesión",use_container_width=True): st.session_state.usuario_autenticado=None; st.rerun()

menu=st.radio("",["🏠 Inicio","🌦️ Clima","🌾 Parcelas","🧪 Tratamientos","📋 Cuaderno","📦 Almacén","🔔 Avisos"],horizontal=True,label_visibility="collapsed")

# ============================================================
# INICIO
# ============================================================
if menu=="🏠 Inicio":
    st.markdown("<div class='section'>Resumen de hoy</div>",unsafe_allow_html=True)
    cols=st.columns(4)
    for c,k,v,s in zip(cols,["🌡️ Temperatura","💨 Viento","💧 Humedad","🌧️ Lluvia"],[f"{w['temp']:.0f} °C",f"{w['wind']:.0f} km/h",f"{w['hum']:.0f}%",f"{w['rain']:.1f} mm"],["Ahora","Límite recomendado: 15","Humedad relativa","Precipitación actual"]):
        with c: st.markdown(f"<div class='card'><div class='kicker'>{k}</div><div class='value'>{v}</div><div class='sub'>{s}</div></div>",unsafe_allow_html=True)
    st.markdown("<div class='section'>Decisión rápida</div>",unsafe_allow_html=True)
    ok=w['wind']<=15 and w['rain']<=2
    if ok: st.markdown(f"<div class='ok'><div class='status'>✅ PUEDES VALORAR UN TRATAMIENTO</div><div>Condiciones actuales favorables en <b>{parcela}</b>: viento {w['wind']:.1f} km/h y lluvia {w['rain']:.1f} mm.</div></div>",unsafe_allow_html=True)
    else: st.markdown(f"<div class='bad'><div class='status'>⛔ MEJOR NO TRATAR AHORA</div><div>Revisa las condiciones antes de aplicar. Viento {w['wind']:.1f} km/h · lluvia {w['rain']:.1f} mm.</div></div>",unsafe_allow_html=True)
    st.markdown("<div class='section'>Estado de la explotación</div>",unsafe_allow_html=True)
    a,b=st.columns([1.2,1])
    with a:
        st.markdown("<div class='card'><div class='kicker'>🌾 PARCELAS</div>",unsafe_allow_html=True)
        for name,d in fincas.items(): st.markdown(f"<div style='padding:11px 0;border-bottom:1px solid #edf1ee'><b>{name}</b><br><span class='sub'>{d.get('ha',0)} ha · {d.get('variedad','Cultivo')}</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with b:
        st.markdown("<div class='card'><div class='kicker'>🔔 AVISOS</div>",unsafe_allow_html=True)
        st.markdown("<div class='alert'><strong>🟢 Meteorología actualizada</strong><span>Datos de Open-Meteo para la parcela activa.</span></div>",unsafe_allow_html=True)
        st.markdown(f"<div class='alert warn'><strong>📦 {len(stock)} productos en almacén</strong><span>Comprueba el stock antes de aplicar.</span></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# ============================================================
# CLIMA
# ============================================================
elif menu=="🌦️ Clima":
    st.markdown("<div class='section'>🌦️ Meteorología de tu parcela</div>",unsafe_allow_html=True)
    ok=w['wind']<=15 and w['rain']<=2
    st.markdown(("<div class='ok'><div class='status'>✅ Ventana favorable</div><div>Las condiciones actuales permiten valorar un tratamiento.</div></div>" if ok else "<div class='bad'><div class='status'>⛔ Condiciones desfavorables</div><div>Revisa viento y precipitación antes de tratar.</div></div>"),unsafe_allow_html=True)
    cs=st.columns(4)
    for c,ico,t,val in zip(cs,["🌡️","💨","💧","🌧️"],["Temperatura","Viento","Humedad","Lluvia"],[f"{w['temp']:.1f} °C",f"{w['wind']:.1f} km/h",f"{w['hum']:.0f}%",f"{w['rain']:.1f} mm"]):
        with c: st.markdown(f"<div class='card' style='text-align:center'><div style='font-size:1.5rem'>{ico}</div><div class='kicker'>{t}</div><div class='value'>{val}</div></div>",unsafe_allow_html=True)
    if w['rows']:
        st.markdown("<div class='section'>Previsión horaria</div>",unsafe_allow_html=True)
        cs=st.columns(len(w['rows']))
        for c,r in zip(cs,w['rows']):
            icon='🌧️' if r['lluvia']>0 else ('💨' if r['viento']>15 else '☀️')
            with c: st.markdown(f"<div class='weather'><small>{r['hora']}</small><div>{icon}</div><b>{r['temp']:.0f}°</b><small>💨 {r['viento']:.0f}</small></div>",unsafe_allow_html=True)
        df=pd.DataFrame(w['rows']).set_index('hora'); st.line_chart(df[['viento','lluvia']],height=240)

# ============================================================
# PARCELAS
# ============================================================
elif menu=="🌾 Parcelas":
    st.markdown("<div class='section'>🌾 Gestión de parcelas</div>",unsafe_allow_html=True)

    tab_ver, tab_anadir, tab_modificar, tab_eliminar = st.tabs([
        "🌾 Ver parcelas",
        "➕ Añadir",
        "✏️ Modificar",
        "🗑️ Eliminar"
    ])

    # --------------------------------------------------------
    # VER PARCELAS
    # --------------------------------------------------------
    with tab_ver:
        if fincas:
            cs=st.columns(min(3,max(1,len(fincas))))
            for c,(name,d) in zip(cs,fincas.items()):
                with c:
                    st.markdown(
                        f"<div class='card'>"
                        f"<div style='font-size:1.7rem'>🌱</div>"
                        f"<h3>{name}</h3>"
                        f"<div class='value'>{d.get('ha',0)} ha</div>"
                        f"<div class='sub'>{d.get('variedad','Cultivo')}</div>"
                        f"<hr>"
                        f"<div class='sub'>📍 {d.get('lat',0):.5f}, {d.get('lon',0):.5f}</div>"
                        f"<div class='sub'>Polígono {d.get('poligono','—')} · Parcela {d.get('parcela','—')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("<div class='section'>Mapa de explotación</div>",unsafe_allow_html=True)
            md=pd.DataFrame([
                {"lat":d.get("lat"),"lon":d.get("lon")}
                for d in fincas.values()
                if d.get("lat") is not None and d.get("lon") is not None
            ])
            if not md.empty:
                st.map(md,zoom=11)
        else:
            st.info("Todavía no tienes parcelas registradas.")

    # --------------------------------------------------------
    # AÑADIR PARCELA
    # --------------------------------------------------------
    with tab_anadir:
        st.markdown("### ➕ Añadir nueva parcela")

        with st.form("form_anadir_parcela"):
            nombre_nuevo = st.text_input(
                "Nombre de la parcela",
                placeholder="Ej. 🍇 Viñedo Norte"
            )
            c1,c2 = st.columns(2)

            with c1:
                variedad_nueva = st.text_input(
                    "Cultivo / variedad",
                    placeholder="Ej. Tempranillo"
                )
                ha_nuevas = st.number_input(
                    "Superficie (ha)",
                    min_value=0.01,
                    value=1.0,
                    step=0.1
                )
                poligono_nuevo = st.text_input(
                    "Polígono",
                    placeholder="Ej. 12"
                )

            with c2:
                lat_nueva = st.number_input(
                    "Latitud",
                    value=42.4658,
                    format="%.6f"
                )
                lon_nueva = st.number_input(
                    "Longitud",
                    value=-2.4499,
                    format="%.6f"
                )
                parcela_nueva = st.text_input(
                    "Nº de parcela",
                    placeholder="Ej. 104"
                )

            guardar_nueva = st.form_submit_button(
                "➕ Añadir parcela",
                use_container_width=True,
                type="primary"
            )

            if guardar_nueva:
                nombre_nuevo = nombre_nuevo.strip()

                if not nombre_nuevo:
                    st.error("Escribe un nombre para la parcela.")
                elif nombre_nuevo in fincas:
                    st.error("Ya existe una parcela con ese nombre.")
                else:
                    st.session_state.db_privada.setdefault(user,{})
                    st.session_state.db_privada[user][nombre_nuevo] = {
                        "lat": float(lat_nueva),
                        "lon": float(lon_nueva),
                        "ha": float(ha_nuevas),
                        "variedad": variedad_nueva.strip() or "General",
                        "poligono": poligono_nuevo.strip() or "—",
                        "parcela": parcela_nueva.strip() or "—"
                    }
                    save_json(FINCAS_FILE,st.session_state.db_privada)
                    st.success(f"Parcela «{nombre_nuevo}» añadida correctamente.")
                    st.rerun()

    # --------------------------------------------------------
    # MODIFICAR PARCELA
    # --------------------------------------------------------
    with tab_modificar:
        st.markdown("### ✏️ Modificar parcela")

        if fincas:
            parcela_editar = st.selectbox(
                "Selecciona la parcela que quieres modificar",
                list(fincas.keys()),
                key="parcela_editar"
            )
            datos_editar = fincas[parcela_editar]

            with st.form("form_modificar_parcela"):
                nuevo_nombre = st.text_input(
                    "Nombre",
                    value=parcela_editar
                )

                c1,c2 = st.columns(2)

                with c1:
                    nueva_variedad = st.text_input(
                        "Cultivo / variedad",
                        value=str(datos_editar.get("variedad","General"))
                    )
                    nuevas_ha = st.number_input(
                        "Superficie (ha)",
                        min_value=0.01,
                        value=float(datos_editar.get("ha",1.0)),
                        step=0.1
                    )
                    nuevo_poligono = st.text_input(
                        "Polígono",
                        value=str(datos_editar.get("poligono",""))
                    )

                with c2:
                    nueva_lat = st.number_input(
                        "Latitud",
                        value=float(datos_editar.get("lat",42.4658)),
                        format="%.6f"
                    )
                    nueva_lon = st.number_input(
                        "Longitud",
                        value=float(datos_editar.get("lon",-2.4499)),
                        format="%.6f"
                    )
                    nuevo_num_parcela = st.text_input(
                        "Nº de parcela",
                        value=str(datos_editar.get("parcela",""))
                    )

                guardar_cambios = st.form_submit_button(
                    "💾 Guardar cambios",
                    use_container_width=True,
                    type="primary"
                )

                if guardar_cambios:
                    nuevo_nombre = nuevo_nombre.strip()

                    if not nuevo_nombre:
                        st.error("El nombre de la parcela no puede quedar vacío.")
                    elif nuevo_nombre != parcela_editar and nuevo_nombre in fincas:
                        st.error("Ya existe otra parcela con ese nombre.")
                    else:
                        nuevos_datos = {
                            "lat": float(nueva_lat),
                            "lon": float(nueva_lon),
                            "ha": float(nuevas_ha),
                            "variedad": nueva_variedad.strip() or "General",
                            "poligono": nuevo_poligono.strip() or "—",
                            "parcela": nuevo_num_parcela.strip() or "—"
                        }

                        if nuevo_nombre != parcela_editar:
                            datos_usuario = st.session_state.db_privada[user]
                            nuevo_orden = {}
                            for nombre_existente, datos_existentes in datos_usuario.items():
                                if nombre_existente == parcela_editar:
                                    nuevo_orden[nuevo_nombre] = nuevos_datos
                                else:
                                    nuevo_orden[nombre_existente] = datos_existentes
                            st.session_state.db_privada[user] = nuevo_orden
                        else:
                            st.session_state.db_privada[user][parcela_editar] = nuevos_datos

                        save_json(FINCAS_FILE,st.session_state.db_privada)
                        st.success("Parcela actualizada correctamente.")
                        st.rerun()
        else:
            st.info("No hay parcelas que modificar.")

    # --------------------------------------------------------
    # ELIMINAR PARCELA
    # --------------------------------------------------------
    with tab_eliminar:
        st.markdown("### 🗑️ Eliminar parcela")

        if len(fincas) > 1:
            parcela_eliminar = st.selectbox(
                "Selecciona la parcela que quieres eliminar",
                list(fincas.keys()),
                key="parcela_eliminar"
            )

            datos_eliminar = fincas[parcela_eliminar]

            st.warning(
                f"Vas a eliminar «{parcela_eliminar}» "
                f"({datos_eliminar.get('ha',0)} ha). Esta acción no se puede deshacer."
            )

            confirmar_eliminar = st.checkbox(
                "Confirmo que quiero eliminar esta parcela"
            )

            if st.button(
                "🗑️ Eliminar definitivamente",
                use_container_width=True,
                disabled=not confirmar_eliminar
            ):
                del st.session_state.db_privada[user][parcela_eliminar]
                save_json(FINCAS_FILE,st.session_state.db_privada)
                st.success(f"Parcela «{parcela_eliminar}» eliminada.")
                st.rerun()

        elif len(fincas) == 1:
            st.info(
                "Debes conservar al menos una parcela. "
                "Añade otra antes de eliminar la única parcela existente."
            )
        else:
            st.info("No hay parcelas que eliminar.")

# ============================================================
# TRATAMIENTOS
# ============================================================
elif menu=="🧪 Tratamientos":
    st.markdown("<div class='section'>🧪 Calculadora de tratamiento</div>",unsafe_allow_html=True)
    st.markdown("<div class='card'>Calcula rápidamente producto por cuba, número de cubas y cantidad total.<br><span class='sub'>Consulta siempre la etiqueta y autorización oficial del producto antes de aplicar.</span></div>",unsafe_allow_html=True)
    with st.form("calc"):
        a,b=st.columns(2)
        with a: cuba=st.number_input("Litros de la cuba",min_value=100,value=1000,step=100); gasto=st.number_input("Litros de caldo/ha",min_value=1,value=400,step=50)
        with b: dosis=st.number_input("Dosis por hectárea (kg/L)",min_value=0.0,value=2.5,step=.5); superficie=st.number_input("Hectáreas",min_value=.1,value=float(p.get('ha',1)),step=.5)
        if st.form_submit_button("Calcular tratamiento",use_container_width=True,type="primary"):
            ha_cuba=cuba/gasto; cubas=superficie/ha_cuba; total=dosis*superficie; por_cuba=dosis*ha_cuba
            st.markdown(f"<div class='ok' style='margin-top:15px'><div class='status'>{por_cuba:.2f} kg/L por cuba</div><div>{cubas:.1f} cubas para {superficie:.1f} ha · {total:.2f} kg/L de producto total.</div></div>",unsafe_allow_html=True)

# ============================================================
# CUADERNO
# ============================================================
elif menu=="📋 Cuaderno":
    st.markdown("<div class='section'>📋 Cuaderno de campo</div>",unsafe_allow_html=True)
    with st.form("cuaderno"):
        a,b=st.columns(2)
        with a: f=st.date_input("Fecha",date.today()); motivo=st.text_input("Plaga o enfermedad",value="Mildiu preventivo")
        with b: codigo=st.selectbox("Producto",list(CATALOGO),format_func=lambda x:f"{x} · {CATALOGO[x]['producto']}"); cantidad=st.number_input("Cantidad utilizada (kg/L)",min_value=0.0,value=5.0,step=1.0)
        if st.form_submit_button("Guardar tratamiento",use_container_width=True,type="primary"):
            st.session_state.fitos_db.setdefault(user,[]).append({"fecha":str(f),"parcela":parcela,"motivo":motivo,"registro":codigo,"producto":CATALOGO[codigo]['producto'],"cantidad":cantidad,"plazo":CATALOGO[codigo]['plazo'],"libre_de":str(f+timedelta(days=CATALOGO[codigo]['plazo']))})
            save_json(FITOS_FILE,st.session_state.fitos_db); st.success("Tratamiento guardado correctamente.")
    if registros: st.dataframe(pd.DataFrame(registros).tail(15).iloc[::-1],use_container_width=True,hide_index=True)

# ============================================================
# ALMACÉN
# ============================================================
elif menu=="📦 Almacén":
    st.markdown("<div class='section'>📦 Almacén de fitosanitarios</div>",unsafe_allow_html=True)
    if stock:
        cs=st.columns(min(3,max(1,len(stock))))
        for c,(cod,d) in zip(cs,stock.items()):
            n=float(d.get('stock_kg_l',0)); estado='🟢 Stock disponible' if n>10 else ('🟠 Stock bajo' if n>0 else '🔴 Sin stock')
            with c: st.markdown(f"<div class='card'><div class='kicker'>{cod}</div><h3>{d.get('nombre','Producto')}</h3><div class='value'>{n:g} <span style='font-size:.8rem'>kg/L</span></div><div class='sub'>{estado}</div></div>",unsafe_allow_html=True)
    else: st.info("Todavía no tienes productos registrados.")
    st.markdown("<div class='section'>Actualizar stock</div>",unsafe_allow_html=True)
    with st.form("stock"):
        codigo=st.selectbox("Producto",list(CATALOGO),format_func=lambda x:f"{x} · {CATALOGO[x]['producto']}")
        actual=float(stock.get(codigo,{}).get('stock_kg_l',0)); nuevo=st.number_input("Stock actual (kg/L)",min_value=0.0,value=actual,step=1.0)
        if st.form_submit_button("Guardar stock",use_container_width=True,type="primary"):
            st.session_state.almacen_db.setdefault(user,{})[codigo]={"nombre":CATALOGO[codigo]['producto'],"stock_kg_l":nuevo}; save_json(ALMACEN_FILE,st.session_state.almacen_db); st.success("Stock actualizado."); st.rerun()

# ============================================================
# AVISOS TELEGRAM
# ============================================================
elif menu=="🔔 Avisos":
    st.markdown("<div class='section'>🔔 Avisos de Telegram</div>",unsafe_allow_html=True)
    if TELEGRAM_TOKEN:
        st.markdown("<div class='ok'><div class='status'>🔐 Telegram conectado de forma segura</div><div>AgroAlert está leyendo el token desde Streamlit Secrets. El token no está almacenado en GitHub.</div></div>",unsafe_allow_html=True)
    else:
        st.markdown("<div class='bad'><div class='status'>⚠️ Telegram no está configurado</div><div>Añade TELEGRAM_TOKEN en Streamlit Secrets.</div></div>",unsafe_allow_html=True)
    chat_id=ui.get("telegram_id","")
    st.markdown(f"<div class='card' style='margin-top:16px'><div class='kicker'>ESTADO DEL USUARIO</div><div class='sub'>{'Chat ID configurado' if chat_id else 'Falta configurar el Chat ID de Telegram'}</div></div>",unsafe_allow_html=True)
    if st.button("Enviar aviso de prueba",use_container_width=True,type="primary"):
        ok,msg=enviar_telegram(chat_id,f"🌱 *AgroAlert*\nPrueba correcta para {parcela}.")
        st.success(msg) if ok else st.error(msg)

st.markdown("<div style='text-align:center;color:#93a09a;font-size:.72rem;margin-top:35px'>AgroAlert 2.0 · Centro de control agrícola</div>",unsafe_allow_html=True)
