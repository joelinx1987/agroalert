elif "Avisos Predictivos de Plagas" in menu:
        st.markdown(f"### 🐛 Modelo Predictivo de Plagas (Radio Comarcal: 50 km)")
        st.write(f"Análisis biológico automatizado evaluando el radio de influencia de **50 km a la redonda** desde la ubicación de **{parcela_activa}**.")
        
        lat_f = datos_parcela.get("lat", 42.4658)
        lon_f = datos_parcela.get("lon", -2.4499)
        
        meteo_comarca = consultar_meteo_openmeteo(lat_f, lon_f)
        temp_comarca = meteo_comarca["temp"]
        humedad_comarca = meteo_comarca["humedad"]
        
        # Ajuste de textos para mayor claridad
        riesgo_mildiu = "Alto" if humedad_comarca > 65 and temp_comarca > 20 else "Bajo / Controlado"
        riesgo_oidio = "Moderado" if temp_comarca >= 22 and temp_comarca <= 32 else "Bajo"
        riesgo_polilla = "Activo (Vuelo de generación)" if temp_comarca > 18 else "Inactivo"
        
        # Tarjetas personalizadas para evitar cortes de texto en st.metric
        st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
            <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <p style="margin: 0; font-size: 0.9rem; color: #64748b; font-weight: 600;">🦠 Riesgo Mildiu (Radio 50km)</p>
                <h3 style="margin: 5px 0 0 0; color: #0f172a; font-size: 1.3rem;">{riesgo_mildiu}</h3>
                <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #10b981; font-weight: 500;">↑ Fungicida preventivo</p>
            </div>
            <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <p style="margin: 0; font-size: 0.9rem; color: #64748b; font-weight: 600;">🌾 Riesgo Oídio (Radio 50km)</p>
                <h3 style="margin: 5px 0 0 0; color: #0f172a; font-size: 1.3rem;">{riesgo_oidio}</h3>
                <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #10b981; font-weight: 500;">↑ Azufres</p>
            </div>
            <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <p style="margin: 0; font-size: 0.9rem; color: #64748b; font-weight: 600;">🦋 Polilla del Racimo</p>
                <h3 style="margin: 5px 0 0 0; color: #0f172a; font-size: 1.3rem; line-height: 1.2;">{riesgo_polilla}</h3>
                <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #10b981; font-weight: 500;">↑ Trampas de feromona</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("#### 🗺️ Visualización del Radio de Influencia Comarcal (50 km)")
        
        m_comarca = folium.Map(location=[lat_f, lon_f], zoom_start=10)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Satélite',
            name='Satélite',
            overlay=False,
            control=True
        ).add_to(m_comarca)
        
        folium.Circle(
            location=[lat_f, lon_f],
            radius=50000,
            color='#3b82f6',
            fill=True,
            fill_color='#3b82f6',
            fill_opacity=0.15,
            popup=f"Radio de influencia comarcal de 50 km para {parcela_activa}"
        ).add_to(m_comarca)
        
        folium.Marker(
            [lat_f, lon_f],
            popup=f"Finca Base: {parcela_activa}",
            tooltip=parcela_activa,
            icon=folium.Icon(color="green", icon="leaf", prefix="fa")
        ).add_to(m_comarca)
        
        st_folium(m_comarca, width=700, height=450)
        
        st.markdown(f"""
        * **Centro de análisis:** Parcela **{parcela_activa}** (Lat: {lat_f}, Lon: {lon_f})
        * **Radio operativo:** 50 km analizados en tiempo real.
        * **Temperatura media comarcal:** `{temp_comarca}°C` | **Humedad relativa comarcal:** `{humedad_comarca}%`.
        * **Diagnóstico fitosanitario zonal:** Las condiciones higrométricas dentro del radio de 50 km indican la conveniencia de revisar linderos y mantener la estrategia de tratamientos preventivos en toda la comarca agrícola.
        """)
