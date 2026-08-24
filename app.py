import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json

st.set_page_config(page_title="AgroAlert MultiCultivo Pro", page_icon="🌱", layout="wide")

st.title("🌱 AgroAlert Pro - Monitor Integral de Riesgo Agrícola")
st.caption("Sistema de soporte a la decisión (DSS) multicultivo: Viñedo, Olivar, Cereal y Frutales")

# --- 1. CONFIGURACIÓN Y PARCELAS ---
st.sidebar.header("📍 1. Cultivo y Parcela")

tipo_cultivo = st.sidebar.selectbox(
    "Selecciona Tipo de Cultivo:",
    ["🍇 Viñedo", "🫒 Olivar", "🌾 Cereal (Trigo/Cebada)", "🍑 Frutales / Almendro"]
)

# Diccionario de parcelas preconfiguradas según cultivo
parcelas_cultivo = {
    "🍇 Viñedo": {
        "Finca Valdegón (Logroño)": {"lat": 42.4658, "lon": -2.4499, "variedad": "Tempranillo", "suelo": "Arcillo-calcáreo"},
        "Viña El Poyo (Haro)": {"lat": 42.5764, "lon": -2.8465, "variedad": "Graciano", "suelo": "Aluvial"}
    },
    "🫒 Olivar": {
        "Finca La Solana (Jaén)": {"lat": 37.7796, "lon": -3.7849, "variedad": "Picual", "suelo": "Arcilloso profundo"},
        "El Soto (Tarragona / Siurana)": {"lat": 41.1561, "lon": 1.1069, "variedad": "Arbequina", "suelo": "Franco-arenoso"}
    },
    "🌾 Cereal (Trigo/Cebada)": {
        "Campiña Alta (Burgos)": {"lat": 42.3439, "lon": -3.6969, "variedad": "Trigo Blando (Berdún)", "suelo": "Franco-arcilloso"},
        "Tierra de Campos (Palencia)": {"lat": 42.0095, "lon": -4.5288, "variedad": "Cebada 2 Carreras", "suelo": "Sedimentario"}
    },
    "🍑 Frutales / Almendro": {
        "Valle del Cinca (Lleida)": {"lat": 41.6176, "lon": 0.6200, "variedad": "Melocotonero (Paraguayo)", "suelo": "Aluvial fértil"},
        "Vega Alta (Murcia)": {"lat": 38.2342, "lon": -1.4168, "variedad": "Almendro (Guara)", "suelo": "Calizo pedregoso"}
    }
}

lista_parcelas = list(parcelas_cultivo[tipo_cultivo].keys()) + ["➕ Añadir Parcela Personalizada"]
seleccion_parcela = st.sidebar.selectbox("Selecciona Parcela:", lista_parcelas)

if seleccion_parcela == "➕ Añadir Parcela Personalizada":
    nombre_parcela = st.sidebar.text_input("Nombre de la parcela", value="Mi Finca")
    lat = st.sidebar.number_input("Latitud", value=42.4658, format="%.4f")
    lon = st.sidebar.number_input("Longitud", value=-2.4499, format="%.4f")
    variedad = st.sidebar.text_input("Variedad", value="Estándar")
    suelo = st.sidebar.selectbox("Tipo de suelo", ["Arcillo-calcáreo", "Aluvial", "Arenoso", "Franco", "Ferroso-arcilloso"])
else:
    nombre_parcela = seleccion_parcela
    lat = parcelas_cultivo[tipo_cultivo][seleccion_parcela]["lat"]
    lon = parcelas_cultivo[tipo_cultivo][seleccion_parcela]["lon"]
    variedad = parcelas_cultivo[tipo_cultivo][seleccion_parcela]["variedad"]
    suelo = parcelas_cultivo[tipo_cultivo][seleccion_parcela]["suelo"]

# Fases fenológicas adaptadas
if "Viñedo" in tipo_cultivo:
    fases = ["Brotación / Desarrollo vegetativo", "Floración / Cuajado", "Envero / Maduración", "Pre-Vendimia"]
elif "Olivar" in tipo_cultivo:
    fases = ["Brotación / Movimiento de savia", "Floración (Trama)", "Endurecimiento de hueso", "Envero / Recolección"]
elif "Cereal" in tipo_cultivo:
    fases = ["Ahijamiento", "Encañado", "Espigado / Floración", "Llenado de grano / Maduración"]
else:
    fases = ["Reposo invernal", "Apertura de yemas / Floración", "Cuajado / Engorde de fruto", "Maduración / Cosecha"]

fase_fenologica = st.sidebar.selectbox("Fase fenológica actual:", fases)

st.sidebar.write("---")
st.sidebar.header("🌦️ 2. Fuente Meteorológica")
modo_datos = st.sidebar.radio("Modo de operación:", ["🛰️ Previsión en Vivo (Open-Meteo)", "🧪 Simulación de Escenarios"])

# --- 2. OBTENCIÓN DE DATOS METEOROLÓGICOS ---
hoy = datetime.now()
fechas = [(hoy + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
datos_reales_ok = False

if modo_datos == "🛰️ Previsión en Vivo (Open-Meteo)":
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            fechas = data["daily"]["time"]
            t_min = data["daily"]["temperature_2m_min"]
            t_max = data["daily"]["temperature_2m_max"]
            lluvia = data["daily"]["precipitation_sum"]
            viento = data["daily"]["wind_speed_10m_max"]
            datos_reales_ok = True
    except Exception:
        st.sidebar.warning("⚠️ Sin conexión con estación externa. Usando modelo simulado local.")
        t_min = [12.0, 11.5, 13.0, 10.5, 11.0, 12.5, 13.0]
        t_max = [24.0, 25.0, 23.5, 22.0, 24.5, 26.0, 25.5]
        lluvia = [0.0, 1.2, 0.0, 0.0, 2.5, 0.0, 0.0]
        viento = [8.0, 10.0, 12.0, 9.0, 7.0, 8.0, 11.0]
else:
    escenario = st.sidebar.selectbox(
        "Selecciona escenario de riesgo:",
        ["Condición Normal", "Alerta de Helada Primaveral", "Lluvia Persistente (Riesgo Fúngico)", "Golpe de Calor / Estrés Hídrico"]
    )
    if escenario == "Condición Normal":
        t_min = [12.0, 11.5, 13.0, 10.5, 11.0, 12.5, 13.0]
        t_max = [24.0, 25.0, 23.5, 22.0, 24.5, 26.0, 25.5]
        lluvia = [0.0, 1.2, 0.0, 0.0, 2.5, 0.0, 0.0]
        viento = [8.0, 10.0, 12.0, 9.0, 7.0, 8.0, 11.0]
    elif escenario == "Alerta de Helada Primaveral":
        t_min = [-2.0, -0.5, 1.5, 3.0, 5.0, 7.5, 9.0]
        t_max = [13.0, 14.5, 16.0, 17.5, 19.0, 20.0, 21.0]
        lluvia = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        viento = [3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 7.0]
    elif escenario == "Lluvia Persistente (Riesgo Fúngico)":
        t_min = [13.5, 14.0, 13.0, 12.5, 13.0, 14.0, 13.5]
        t_max = [21.0, 20.5, 22.0, 21.5, 22.5, 21.0, 20.0]
        lluvia = [14.0, 18.5, 9.0, 12.0, 6.0, 1.0, 0.0]
        viento = [12.0, 14.0, 11.0, 9.0, 8.0, 7.0, 9.0]
    else: # Golpe de calor
        t_min = [21.0, 22.0, 21.5, 20.0, 21.0, 22.5, 22.0]
        t_max = [37.5, 38.0, 36.5, 35.0, 36.0, 39.0, 38.5]
        lluvia = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        viento = [14.0, 15.0, 11.0, 10.0, 13.0, 12.0, 9.0]

min_hoy = t_min[0]
max_hoy = t_max[0]
lluvia_hoy = lluvia[0]
viento_hoy = viento[0]
temp_media_hoy = (min_hoy + max_hoy) / 2

# --- 3. PANEL DE INFORMACIÓN Y MAPA ---
col_info, col_mapa = st.columns([1.4, 1])

with col_info:
    st.subheader(f"📍 {nombre_parcela}")
    st.write(f"**Cultivo:** {tipo_cultivo} | **Variedad:** {variedad} | **Suelo:** {suelo}")
    st.write(f"**Fase actual:** {fase_fenologica}")
    st.caption(f"Coordenadas: Lat {lat:.4f}, Lon {lon:.4f} | Origen: {'🟢 Datos en tiempo real' if datos_reales_ok else '🔵 Datos simulados'}")

with col_mapa:
    df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.map(df_map, zoom=11)

# Cálculo de integrales térmicas según el cultivo
if "Viñedo" in tipo_cultivo:
    gdd = sum([max(0, ((t_min[i] + t_max[i]) / 2) - 10) for i in range(len(t_min))])
    texto_gdd = "GDD (Base 10°C)"
elif "Olivar" in tipo_cultivo:
    gdd = sum([max(0, ((t_min[i] + t_max[i]) / 2) - 12.5) for i in range(len(t_min))])
    texto_gdd = "GDD (Base 12.5°C)"
elif "Cereal" in tipo_cultivo:
    gdd = sum([max(0, ((t_min[i] + t_max[i]) / 2) - 0) for i in range(len(t_min))])
    texto_gdd = "Integral Térmica (Base 0°C)"
else:
    # Horas frío aproximadas por debajo de 7°C
    gdd = sum([max(0, 7 - t_min[i]) * 3 for i in range(len(t_min))])
    texto_gdd = "Horas Frío Estimadas (<7°C)"

# Métricas principales
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Tª Mín / Máx Hoy", f"{min_hoy:.1f} / {max_hoy:.1f} °C")
col_m2.metric("Lluvia Prevista Hoy", f"{lluvia_hoy:.1f} mm")
col_m3.metric("Viento Máximo", f"{viento_hoy:.1f} km/h")
col_m4.metric(texto_gdd, f"{gdd:.1f}")

st.write("---")

# --- 4. MOTOR DE REGLAS AGRONÓMICAS POR CULTIVO ---
st.write("### 🛡️ Diagnóstico Fitosanitario y Operativo")
col1, col2 = st.columns(2)
acciones_recomendadas = []

with col1:
    st.markdown("**1. Riesgo por Temperatura Extrema (Helada / Golpe de Calor)**")
    if min_hoy <= 0:
        st.error(f"🚨 HELADA CRÍTICA ({min_hoy:.1f} °C): Daño en brotes y flor.")
        acciones_recomendadas.append("Activar medidas antihelada y suspender labores mecánicas de suelo.")
    elif min_hoy <= 2:
        st.warning(f"⚠️ PRECAUCIÓN ({min_hoy:.1f} °C): Riesgo de helada por inversión térmica.")
    elif max_hoy >= 36:
        st.error(f"🔥 GOLPE DE CALOR ({max_hoy:.1f} °C): Parada vegetativa y estrés hídrico.")
        acciones_recomendadas.append("Aportar riego de apoyo si dispone de dotación y evitar tratamientos fitosanitarios.")
    else:
        st.success(f"✅ Rango térmico vegetativo seguro ({min_hoy:.1f} a {max_hoy:.1f} °C).")

    # Regla 2 según cultivo
    if "Viñedo" in tipo_cultivo:
        st.markdown("**2. Mildiu (*Plasmopara viticola*)**")
        if lluvia_hoy >= 10 and temp_media_hoy >= 10:
            st.error(f"🚨 INFECCIÓN PRIMARIA: Lluvia ({lluvia_hoy:.1f} mm) y Tª media ({temp_media_hoy:.1f} °C).")
            acciones_recomendadas.append("Aplicar fungicida sistémico/penetrante contra mildiu tras la lluvia.")
        elif lluvia_hoy >= 5 and temp_media_hoy >= 10:
            st.warning("⚠️ RIESGO MEDIO: Monitorear hojas basales.")
        else:
            st.success("✅ Presión de mildiu baja.")

    elif "Olivar" in tipo_cultivo:
        st.markdown("**2. Repilo (*Venturia oleaginea*)**")
        if lluvia_hoy >= 5 and 10 <= temp_media_hoy <= 20:
            st.error(f"🚨 RIESGO ALTO DE REPILO: Lluvia continuada con Tª óptima ({temp_media_hoy:.1f} °C).")
            acciones_recomendadas.append("Aplicar tratamiento preventivo de cobre o fungicida fijador al cesar el agua.")
        else:
            st.success("✅ Presión de repilo baja.")

    elif "Cereal" in tipo_cultivo:
        st.markdown("**2. Septoria y Roya**")
        if sum(lluvia[:3]) >= 10 and 12 <= temp_media_hoy <= 22:
            st.error(f"🚨 ALERTA SEPTORIA: Humedad en hoja y temperatura favorable para esporulación.")
            acciones_recomendadas.append("Revisar hoja bandera y valorar pase de fungicida si está en encañado.")
        else:
            st.success("✅ Follaje sin presión fúngica crítica.")

    else: # Frutales
        st.markdown("**2. Monilia y Moteado**")
        if lluvia_hoy >= 5 and 12 <= temp_media_hoy <= 22:
            st.error(f"🚨 RIESGO MONILIA: Lluvia durante periodo receptivo de fruto/flor.")
            acciones_recomendadas.append("Aplicar tratamiento fungicida específico para protección de fruto.")
        else:
            st.success("✅ Presión de monilia/moteado baja.")

with col2:
    # Regla 3 según cultivo
    if "Viñedo" in tipo_cultivo:
        st.markdown("**3. Oídio & Botritis**")
        if sum(lluvia[:3]) >= 15 and 15 <= temp_media_hoy <= 24:
            st.error(f"🚨 RIESGO ELEVADO DE BOTRITIS: Humedad acumulada ({sum(lluvia[:3]):.1f} mm en 72h).")
            acciones_recomendadas.append("Deshojado basal para ventilar racimos y aplicación de antibotritis.")
        elif 22 <= temp_media_hoy <= 28 and lluvia_hoy == 0:
            st.warning(f"⚠️ CONDICIÓN ÓPTIMA PARA OÍDIO: Tª media de {temp_media_hoy:.1f} °C.")
            acciones_recomendadas.append("Mantener coberturas antioídio.")
        else:
            st.success("✅ Riesgo fúngico secundario controlado.")

    elif "Olivar" in tipo_cultivo:
        st.markdown("**3. Mosca del Olivo (*Bactrocera oleae*)**")
        if 20 <= temp_media_hoy <= 30 and max_hoy < 35:
            st.warning(f"⚠️ ACTIVIDAD DE MOSCA: Rango óptimo ({temp_media_hoy:.1f} °C).")
            acciones_recomendadas.append("Revisar mosqueros y trampas cromotrópicas para conteo de capturas.")
        elif max_hoy >= 35:
            st.success("✅ Parada biológica de mosca por altas temperaturas (>35 °C).")
        else:
            st.success("✅ Sin riesgo de vuelo significativo.")

    elif "Cereal" in tipo_cultivo:
        st.markdown("**3. Asurado / Golpe de Secado**")
        if max_hoy >= 32 and viento_hoy >= 15:
            st.error(f"🚨 RIESGO DE ASURADO: Calor ({max_hoy:.1f} °C) y viento ({viento_hoy:.1f} km/h) aceleran la desecación.")
            acciones_recomendadas.append("Corte prematuro de forraje o anticipar cosecha en parcelas maduras.")
        else:
            st.success("✅ Llenado de grano en condiciones estables.")

    else: # Frutales
        st.markdown("**3. Pulgón y Araña Roja**")
        if 24 <= temp_media_hoy <= 32 and lluvia_hoy == 0:
            st.warning(f"⚠️ CONDICIÓN PROPICIA PARA ÁCAROS/PULGÓN: Ambiente seco y cálido.")
            acciones_recomendadas.append("Monitorear brotes tiernos y envés de las hojas.")
        else:
            st.success("✅ Presión de plagas controlada.")

    st.markdown("**4. Ventana de Tratamiento Fitosanitario**")
    if viento_hoy > 15:
        st.error(f"⛔ NO TRATAR: Viento excesivo ({viento_hoy:.1f} km/h > 15 km/h, riesgo de deriva).")
        acciones_recomendadas.append("Suspender pulverización por exceso de viento.")
    elif lluvia_hoy > 2:
        st.error(f"⛔ NO TRATAR: Lluvia prevista ({lluvia_hoy:.1f} mm, riesgo de lavado foliar).")
        acciones_recomendadas.append("Suspender tratamientos hasta cese de precipitaciones.")
    elif max_hoy > 30:
        st.warning(f"⚠️ HORARIO RESTRINGIDO: Tª máxima > 30 °C.")
        acciones_recomendadas.append("Tratar únicamente a primera hora de la mañana.")
    else:
        st.success("✅ CONDICIONES ÓPTIMAS: Apta para pulverización.")

if not acciones_recomendadas:
    acciones_recomendadas.append("Sin intervenciones urgentes requeridas. Continuar con labores habituales.")

st.write("---")
st.write("### 📋 Prescripción Técnica para Hoy")
for i, act in enumerate(acciones_recomendadas, 1):
    st.info(f"**Paso {i}:** {act}")

st.write("---")
st.write("### 📅 Previsión a 7 Días y Cuaderno de Explotación")

df = pd.DataFrame({
    "Fecha": fechas,
    "T. Mínima (°C)": t_min,
    "T. Máxima (°C)": t_max,
    "Lluvia (mm)": lluvia,
    "Viento (km/h)": viento
})

st.dataframe(df, use_container_width=True)
st.line_chart(df.set_index("Fecha")[["T. Mínima (°C)", "T. Máxima (°C)"]])

# Generador de registro exportable para el Cuaderno Digital de Explotación
df_export = df.copy()
df_export["Parcela"] = nombre_parcela
df_export["Cultivo"] = tipo_cultivo
df_export["Variedad"] = variedad
df_export["Suelo"] = suelo
df_export["Fase_Fenologica"] = fase_fenologica
df_export["Prescripcion_Tecnica"] = " | ".join(acciones_recomendadas)

csv_data = df_export.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Descargar Registro Oficial para Cuaderno de Campo (CSV)",
    data=csv_data,
    file_name=f"cuaderno_{tipo_cultivo.split()[1].lower()}_{nombre_parcela.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)