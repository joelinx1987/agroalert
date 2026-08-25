import urllib.request
import urllib.parse
import json
import os
from datetime import datetime

def obtener_tiempo(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/Cron'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                "t_min": data["daily"]["temperature_2m_min"][0],
                "t_max": data["daily"]["temperature_2m_max"][0],
                "lluvia": data["daily"]["precipitation_sum"][0],
                "viento": data["daily"]["wind_speed_10m_max"][0]
            }
    except Exception:
        return {"t_min": 12.0, "t_max": 24.0, "lluvia": 0.0, "viento": 8.0}

def enviar_whatsapp(telefono, apikey, mensaje):
    num_limpio = telefono.replace(" ", "").replace("-", "").replace(".", "")
    if not num_limpio.startswith("+"):
        num_limpio = "+34" + num_limpio if not num_limpio.startswith("34") else "+" + num_limpio
    texto_encoded = urllib.parse.quote(mensaje)
    url = f"https://api.callmebot.com/whatsapp.php?phone={num_limpio}&text={texto_encoded}&apikey={apikey.strip()}"
    req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/Cron'})
    urllib.request.urlopen(req, timeout=10)

def main():
    users_file = "usuarios_db.json"
    fincas_file = "fincas_db.json"
    
    # Cargar usuarios reales de la app
    if os.path.exists(users_file):
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                usuarios_db = json.load(f)
        except Exception:
            usuarios_db = {}
    else:
        usuarios_db = {}

    # Cargar fincas reales de la app
    if os.path.exists(fincas_file):
        try:
            with open(fincas_file, "r", encoding="utf-8") as f:
                fincas_db = json.load(f)
        except Exception:
            fincas_db = {}
    else:
        fincas_db = {}

    if not usuarios_db:
        print("No hay usuarios en la base de datos.")
        return

    enviados = 0

    for username, u_data in usuarios_db.items():
        telefono = u_data.get("telefono", "")
        apikey = u_data.get("apikey", "")
        nombre = u_data.get("nombre", username)

        if not telefono or not apikey:
            continue

        # Obtener las fincas de este usuario
        fincas_usuario = fincas_db.get(username, {})
        
        # Si no tiene fincas registradas, usamos una por defecto para no dejarlo sin parte
        parcelas_a_procesar = []
        for cultivo, lista_fincas in fincas_usuario.items():
            for nom_finca, datos_finca in lista_fincas.items():
                parcelas_a_procesar.append({
                    "parcela": nom_finca,
                    "lat": datos_finca.get("lat", 42.3659),
                    "lon": datos_finca.get("lon", -2.4235),
                    "ha": datos_finca.get("ha", 2.0)
                })

        if not parcelas_a_procesar:
            parcelas_a_procesar.append({
                "parcela": "Parcela Principal",
                "lat": 42.3659,
                "lon": -2.4235,
                "ha": 2.0
            })

        # Enviar parte por cada parcela del usuario
        for p in parcelas_a_procesar:
            clima = obtener_tiempo(p["lat"], p["lon"])
            
            if clima["viento"] > 15 or clima["lluvia"] > 2.0:
                estado = "🔴 *NO SULFATAR HOY (VIENTO/LLUVIA)*"
            elif clima["t_max"] >= 32:
                estado = "🟠 *ATENCIÓN: TRATAR SOLO A PRIMERA HORA*"
            else:
                estado = "🟢 *DÍA PERFECTO PARA SULFATAR*"

            mensaje = f"""🚜 *PARTE MATUTINO AGROALERT PRO (04:45 AM)*
👤 *Titular:* {nombre}
📍 *Parcela:* {p['parcela']} ({p['ha']} ha)

{estado}

🌡️ *Temperaturas:* {clima['t_min']:.0f}°C a {clima['t_max']:.0f}°C
💨 *Viento máx:* {clima['viento']:.0f} km/h
🌧️ *Lluvia prevista:* {clima['lluvia']:.1f} mm

_Que tengas excelente jornada en el campo._"""
            
            try:
                enviar_whatsapp(telefono, apikey, mensaje)
                print(f"Parte enviado con éxito a {nombre} ({p['parcela']})")
                enviados += 1
            except Exception as e:
                print(f"Error al enviar a {nombre}: {e}")

    print(f"Proceso finalizado. Total de partes enviados: {enviados}")

if __name__ == "__main__":
    main()
