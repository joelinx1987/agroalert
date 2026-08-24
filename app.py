import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json

st.set_page_config(page_title="AgroAlert MultiCultivo Pro", page_icon="🌱", layout="wide")

st.title("🌱 AgroAlert Pro - Monitor Integral & Soporte de Tratamiento")
st.caption("Sistema de soporte a la decisión (DSS) multicultivo y dosificación agronómica")

# --- 1. BASE DE DATOS Y GESTIÓN DE PARCELAS ---
PARCELAS_DEFAULT = {
    "🍇 Viñedo": {
        "Frontón Jaime (Logroño)": {"lat": 42.3659, "lon": -2.4235, "variedad": "Tempranillo", "suelo": "Arcillo-calcáreo", "ha": 2.0},
        "Finca Valdegón (Logroño)": {"lat": 42.4658, "lon": -2.4499, "variedad": "Tempranillo", "suelo": "Arcillo-calcáreo", "ha": 2.5},
        "Viña El Poyo (Haro)": {"lat": 42.5764, "lon": -2.8465, "variedad": "Graciano", "suelo": "Aluvial", "ha": 4.0}
    },
    "🫒 Olivar": {
        "Finca La Solana (Jaén)": {"lat": 37.7796, "lon": -3.7849, "variedad": "Picual", "suelo": "Arcilloso profundo", "ha": 6.0},
        "El Soto (Tarragona)": {"lat": 41.1561, "lon": 1.1069, "variedad": "Arbequina", "suelo": "Franco-arenoso", "ha": 3.2}
    },
    "🌾 Cereal (Trigo/Cebada)": {
        "Campiña Alta (Burgos)": {"lat": 42.3439, "lon": -3.6969, "variedad": "Trigo Blando", "suelo": "Franco-arcilloso", "ha": 15.0},
        "Tierra de Campos (Palencia)": {"lat": 42.0095, "lon": -4.5288, "variedad": "Cebada", "suelo": "Sedimentario", "ha": 22.0}
    },
    "🍑 Frutales / Almendro": {
        "Valle del Cinca (Lleida)": {"lat": 41.6176, "lon": 0.6200, "variedad": "Melocotonero", "suelo": "Aluvial fértil", "ha": 3.8},
        "Vega Alta (Murcia)": {"lat": 38.2342, "lon": -1.4168, "variedad": "Almendro", "suelo": "Calizo pedregoso", "ha": 5.5}
    }
}

if "db_parcelas" not in st.session_state:
    st.session_state.db_parcelas = PARCELAS_DEFAULT.copy()

st.sidebar.header("📍 1. Cultivo y Parcela")

tipo_cultivo = st.sidebar.selectbox(
    "Selecciona Tipo de Cultivo:",
    ["🍇 Viñedo", "🫒 Olivar", "🌾 Cereal (Trigo/Cebada)", "🍑 Frutales / Almendro"]
)

if tipo_cultivo not in st.session_state.db_parcelas:
    st.session_state.db_parcelas[tipo_cultivo] = {}

fincas_actuales = st.session_state.db_parcelas[tipo_cultivo]
lista_parcelas = list(fincas_actuales.keys()) + ["➕ Añadir Nueva Parcela"]
seleccion_parcela = st.sidebar.selectbox("Selecciona Parcela:", lista_parcelas)

if seleccion_parcela == "➕ Añadir Nueva Parcela":
    with st.sidebar.expander("📝 Formulario Nueva Parcela", expanded=True):
        nuevo_nombre = st.text_input("Nombre de la parcela", value="Mi Nueva Parcela")
        nuevo_lat = st.number_input("Latitud (ej: 42.3659)", value=42.3659, format="%.4f")
        nuevo_lon = st.number_input("Longitud (ej: -2.4235)", value=-2.4235, format="%.4f")
        nuevo_var = st.text_input("Variedad", value="Tempranillo")
        nuevo_suelo = st.selectbox("Tipo de suelo", ["Arcillo-calcáreo", "Aluvial", "Arenoso", "Franco", "Ferroso-arcilloso"])
        nuevo_ha = st.number_input("Superficie (Hectáreas)", value=2.0, min_value=0.1, step=0.5)

        if st.button("💾 Guardar Parcela"):
            if nuevo_nombre.strip():
                st.session_state.db_parcelas[tipo_cultivo][nuevo_nombre.strip()] = {
                    "lat": nuevo_lat,
                    "lon": nuevo_lon,
                    "variedad": nuevo_var,
                    "suelo": nuevo_suelo,
                    "ha": nuevo_ha
                }
                st.success(f"¡{nuevo_nombre} guardada!")
                st.rerun()

    # Valores provisionales mientras se edita
    nombre_parcela = nuevo_nombre
    lat = nuevo_lat
    lon = nuevo_lon
    variedad = nuevo_var
    suelo = nuevo_suelo
    superficie_ha = nuevo_ha
else:
    nombre_parcela = seleccion_parcela
    datos_p = fincas_actuales[seleccion_parcela]
    lat = datos_p.get("lat", 42.3659)
    lon = datos_p.get("lon", -2.4235)
    variedad = datos_p.get("variedad", "Tempranillo")
    suelo = datos_p.get("suelo", "Arcillo-calcáreo")
    superficie_ha = datos_p.get("ha", 2.0)

    if seleccion_parcela not in PARCELAS_DEFAULT.get(tipo_cultivo, {}):
        if st.sidebar.button("🗑️ Eliminar esta Parcela"):
            del st.session_state.db_parcelas[tipo_cultivo][seleccion_parcela]
            st.sidebar.warning("Parcela eliminada.")
            st.rerun()

# Fases fenológicas
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
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            fechas = data["daily"]["time"]
            t_min = data["daily"]["temperature_2m_min"]
            t_max = data["daily"]["temperature_2m_max"]
            lluvia = data["daily"]["precipitation_sum"]
            viento = data["daily"]["wind_speed_10m_max"]
            datos_reales_ok = True
    except Exception:
        st.sidebar.warning("⚠️ Sin conexión con estación externa. Usando modelo predictivo local.")
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
    else:
        t_min = [21.0, 22.0, 21.5, 20.0, 21.0, 22.5, 22.0]
        t_max = [37.5, 38.0, 36.5, 35.0, 36.0, 39.0, 38.5]
        lluvia = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        viento = [14.0, 15.0, 11.0, 10.0, 13.0, 12.0, 9.0]

min_hoy = t_min[0]
max_hoy = t_max[0]
lluvia_hoy = lluvia[0]
viento_hoy = viento[0]
temp_media_hoy = (min_hoy + max_hoy) / 2

# --- PESTAÑAS PRINCIPALES ---
tab_alertas, tab_calculadora = st.tabs(["🛡️ Diagnóstico y Alertas", "🧪 Calculadora de Caldo y Dosis"])

# ==========================================
# PESTAÑA 1: DIAGNÓSTICO Y ALERTAS
# ==========================================
with tab_alertas:
    col_info, col_mapa = st.columns([1.4, 1])

    with col_info:
        st.subheader(f"📍 {nombre_parcela}")
        st.write(f"**Cultivo:** {tipo_cultivo} | **Variedad:** {variedad} | **Superficie:** {superficie_ha} ha")
        st.write(f"**Fase actual:** {fase_fenologica} | **Suelo:** {suelo}")
        st.caption(f"Coordenadas: Lat {lat:.4f}, Lon {lon:.4f} | Origen: {'🟢 Datos en tiempo real (Open-Meteo)' if datos_reales_ok else '🔵 Datos simulados'}")

    with col_mapa:
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
            st.map(df_map, zoom=12)
        else:
            st.error("Coordenadas fuera de rango.")

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
        gdd = sum([max(0, 7 - t_min[i]) * 3 for i in range(len(t_min))])
        texto_gdd = "Horas Frío Estimadas (<7°C)"

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Tª Mín / Máx Hoy", f"{min_hoy:.1f} / {max_hoy:.1f} °C")
    col_m2.metric("Lluvia Prevista Hoy", f"{lluvia_hoy:.1f} mm")
    col_m3.metric("Viento Máximo", f"{viento_hoy:.1f} km/h")
    col_m4.metric(texto_gdd, f"{gdd:.1f}")

    st.write("---")
    st.write("### 🛡️ Diagnóstico Fitosanitario y Operativo")
    col1, col2 = st.columns(2)
    acciones_recomendadas = []

    with col1:
        st.markdown("**1. Riesgo Térmico (Helada / Golpe de Calor)**")
        if min_hoy <= 0:
            st.error(f"🚨 HELADA CRÍTICA ({min_hoy:.1f} °C): Daño en brotes y flor.")
            acciones_recomendadas.append("Activar medidas antihelada y suspender labores de suelo.")
        elif min_hoy <= 2:
            st.warning(f"⚠️ PRECAUCIÓN ({min_hoy:.1f} °C): Inversión térmica posible.")
        elif max_hoy >= 36:
            st.error(f"🔥 GOLPE DE CALOR ({max_hoy:.1f} °C): Parada vegetativa.")
            acciones_recomendadas.append("Aportar riego de apoyo si dispone de dotación.")
        else:
            st.success(f"✅ Rango térmico seguro ({min_hoy:.1f} a {max_hoy:.1f} °C).")

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
                st.error(f"🚨 RIESGO ALTO REPILO: Lluvia y Tª óptima ({temp_media_hoy:.1f} °C).")
                acciones_recomendadas.append("Aplicar tratamiento preventivo de cobre al cesar la lluvia.")
            else:
                st.success("✅ Presión de repilo baja.")
        elif "Cereal" in tipo_cultivo:
            st.markdown("**2. Septoria y Roya**")
            if sum(lluvia[:3]) >= 10 and 12 <= temp_media_hoy <= 22:
                st.error(f"🚨 ALERTA SEPTORIA: Humedad continua.")
                acciones_recomendadas.append("Revisar hoja bandera y valorar fungicida.")
            else:
                st.success("✅ Follaje sin presión fúngica crítica.")
        else:
            st.markdown("**2. Monilia y Moteado**")
            if lluvia_hoy >= 5 and 12 <= temp_media_hoy <= 22:
                st.error(f"🚨 RIESGO MONILIA: Lluvia en periodo receptivo.")
                acciones_recomendadas.append("Tratamiento fungicida de protección de fruto.")
            else:
                st.success("✅ Presión de monilia baja.")

    with col2:
        if "Viñedo" in tipo_cultivo:
            st.markdown("**3. Oídio & Botritis**")
            if sum(lluvia[:3]) >= 15 and 15 <= temp_media_hoy <= 24:
                st.error(f"🚨 RIESGO BOTRITIS: Humedad acumulada ({sum(lluvia[:3]):.1f} mm en 72h).")
                acciones_recomendadas.append("Deshojado basal para ventilar racimos y aplicar antibotritis.")
            elif 22 <= temp_media_hoy <= 28 and lluvia_hoy == 0:
                st.warning(f"⚠️ CONDICIÓN ÓPTIMA OÍDIO: Tª media de {temp_media_hoy:.1f} °C.")
                acciones_recomendadas.append("Mantener coberturas antioídio.")
            else:
                st.success("✅ Riesgo secundario bajo.")
        elif "Olivar" in tipo_cultivo:
            st.markdown("**3. Mosca del Olivo (*Bactrocera oleae*)**")
            if 20 <= temp_media_hoy <= 30 and max_hoy < 35:
                st.warning(f"⚠️ ACTIVIDAD DE MOSCA: Rango óptimo ({temp_media_hoy:.1f} °C).")
                acciones_recomendadas.append("Revisar trampas cromotrópicas.")
            elif max_hoy >= 35:
                st.success("✅ Parada biológica de mosca (>35 °C).")
            else:
                st.success("✅ Sin riesgo de vuelo.")
        elif "Cereal" in tipo_cultivo:
            st.markdown("**3. Asurado / Golpe de Secado**")
            if max_hoy >= 32 and viento_hoy >= 15:
                st.error(f"🚨 RIESGO ASURADO: Calor ({max_hoy:.1f} °C) y viento ({viento_hoy:.1f} km/h).")
                acciones_recomendadas.append("Anticipar cosecha en parcelas maduras.")
            else:
                st.success("✅ Llenado de grano estable.")
        else:
            st.markdown("**3. Pulgón y Ácaros**")
            if 24 <= temp_media_hoy <= 32 and lluvia_hoy == 0:
                st.warning(f"⚠️ CONDICIÓN PROPICIA ÁCAROS: Ambiente seco.")
                acciones_recomendadas.append("Monitorear brotes tiernos.")
            else:
                st.success("✅ Plagas controladas.")

        st.markdown("**4. Ventana de Tratamiento Fitosanitario**")
        if viento_hoy > 15:
            st.error(f"⛔ NO TRATAR: Viento ({viento_hoy:.1f} km/h > 15 km/h).")
            acciones_recomendadas.append("Suspender pulverización por exceso de viento.")
        elif lluvia_hoy > 2:
            st.error(f"⛔ NO TRATAR: Lluvia prevista ({lluvia_hoy:.1f} mm).")
            acciones_recomendadas.append("Suspender tratamientos por riesgo de lavado.")
        elif max_hoy > 30:
            st.warning(f"⚠️ HORARIO RESTRINGIDO: Tª > 30 °C.")
            acciones_recomendadas.append("Tratar a primera hora de la mañana.")
        else:
            st.success("✅ CONDICIONES ÓPTIMAS para pulverizar.")

    if not acciones_recomendadas:
        acciones_recomendadas.append("Sin intervenciones urgentes requeridas. Labores habituales.")

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

    df_export = df.copy()
    df_export["Parcela"] = nombre_parcela
    df_export["Cultivo"] = tipo_cultivo
    df_export["Variedad"] = variedad
    df_export["Superficie_ha"] = superficie_ha
    df_export["Prescripcion_Tecnica"] = " | ".join(acciones_recomendadas)

    csv_data = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Registro para Cuaderno de Campo (CSV)",
        data=csv_data,
        file_name=f"cuaderno_{nombre_parcela.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ==========================================
# PESTAÑA 2: CALCULADORA DE CALDO Y DOSIS
# ==========================================
with tab_calculadora:
    st.subheader(f"🧪 Calculadora de Mezcla y Dosificación - {nombre_parcela}")
    st.caption("Ajusta los parámetros de tu cuba y de la etiqueta del producto fitosanitario o abono foliar.")

    c_p1, c_p2 = st.columns(2)

    with c_p1:
        st.markdown("#### 🚜 Parámetros de Aplicación y Maquinaria")
        volumen_cuba = st.number_input("Capacidad de la cuba / atomizador (Litros)", value=1000, step=100, min_value=50)
        gasto_ha = st.number_input("Volumen de caldo por hectárea (L/ha)", value=400, step=50, min_value=50)
        ha_a_tratar = st.number_input("Superficie a tratar (Hectáreas)", value=float(superficie_ha), step=0.5, min_value=0.1)

    with c_p2:
        st.markdown("#### 🏷️ Ficha del Producto Comercial")
        nombre_prod = st.text_input("Nombre comercial del producto", value="Fungicida Cobre / Sistémico")
        tipo_dosis = st.radio("Formato de dosis según etiqueta:", ["Concentración (% o gr/cc por 100 L)", "Dosis por Superficie (kg o L por Hectárea)"])
        
        if "Concentración" in tipo_dosis:
            dosis_valor = st.number_input("Dosis recomendada (en gramos o cc por cada 100 L de agua)", value=250.0, step=25.0)
            st.caption(f"Equivale a una concentración del **{dosis_valor / 1000:.3f}%** en masa/volumen.")
        else:
            dosis_valor = st.number_input("Dosis recomendada por hectárea (kg o L / ha)", value=2.0, step=0.5)

        precio_unitario = st.number_input("Precio del producto (€ por kg o Litro)", value=18.5, step=1.0, min_value=0.0)

    st.write("---")
    st.markdown("### 📊 Resultado de la Preparación de Caldo")

    caldo_total_necesario = ha_a_tratar * gasto_ha
    numero_cubas = caldo_total_necesario / volumen_cuba
    ha_por_cuba = volumen_cuba / gasto_ha

    if "Concentración" in tipo_dosis:
        prod_por_cuba = (dosis_valor * (volumen_cuba / 100.0)) / 1000.0
        prod_total_finca = (dosis_valor * (caldo_total_necesario / 100.0)) / 1000.0
    else:
        prod_por_cuba = dosis_valor * ha_por_cuba
        prod_total_finca = dosis_valor * ha_a_tratar

    coste_total = prod_total_finca * precio_unitario
    coste_ha = coste_total / ha_a_tratar if ha_a_tratar > 0 else 0

    res1, res2, res3, res4 = st.columns(4)
    res1.metric("📦 Producto por CUBA LLENA", f"{prod_por_cuba:.2f} kg / L")
    res2.metric("🚜 Cubas necesarias", f"{numero_cubas:.2f} cubas", f"{ha_por_cuba:.2f} ha/cuba")
    res3.metric("🧪 Producto total Parcela", f"{prod_total_finca:.2f} kg / L", f"Caldo: {caldo_total_necesario:.0f} L")
    res4.metric("💰 Coste Tratamiento", f"{coste_total:.2f} €", f"{coste_ha:.2f} €/ha")

    st.write("")
    st.success(f"""
    **📝 Instrucciones de carga para el aplicador:**
    1. Llenar la cuba de agua hasta la mitad (**{volumen_cuba // 2} litros**) con el agitador en marcha.
    2. Verter **{prod_por_cuba:.2f} kg o Litros** de **{nombre_prod}**.
    3. Completar con agua hasta los **{volumen_cuba} litros**.
    4. Cada cuba completa cubre **{ha_por_cuba:.2f} hectáreas** a un gasto de **{gasto_ha} L/ha**.
    """)
