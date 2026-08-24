import urllib.request
import urllib.parse
import json
from datetime import datetime

# Lista de usuarios a los que se enviará el WhatsApp
USUARIOS = [
    {
        "nombre": "Joel",
        "telefono": "+34626665232",
        "apikey": "3443251",
        "parcela": "Frontón Jaime",
        "lat": 42.3659,
        "lon": -2.4235,
        "ha": 2.0
    }
]

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
    num_limpio = telefono.replace(" ", "").replace("-", "")
    if not num_limpio.startswith("+"):
        num_limpio = "+34" + num_limpio if not num_limpio.startswith("34") else "+" + num_limpio
    texto_encoded = urllib.parse.quote(mensaje)
    url = f"https://api.callmebot.com/whatsapp.php?phone={num_limpio}&text={texto_encoded}&apikey={apikey.strip()}"
    req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/Cron'})
    urllib.request.urlopen(req, timeout=10)

def main():
    for u in USUARIOS:
        if not u["apikey"]:
            continue
        clima = obtener_tiempo(u["lat"], u["lon"])

        if clima["viento"] > 15 or clima["lluvia"] > 2.0:
            estado = "🔴 *NO SULFATAR HOY (VIENTO/LLUVIA)*"
        elif clima["t_max"] >= 32:
            estado = "🟠 *ATENCIÓN: TRATAR SOLO A PRIMERA HORA*"
        else:
            estado = "🟢 *DÍA PERFECTO PARA SULFATAR*"

        mensaje = f"""🚜 *PARTE MATUTINO AGROALERT (05:00 AM)*
📍 *Parcela:* {u['parcela']} ({u['ha']} ha)

{estado}

🌡️ *Temperaturas:* {clima['t_min']:.0f}°C a {clima['t_max']:.0f}°C
💨 *Viento máx:* {clima['viento']:.0f} km/h
🌧️ *Lluvia prevista:* {clima['lluvia']:.1f} mm

_Que tengas buena jornada en el campo._"""

        try:
            enviar_whatsapp(u["telefono"], u["apikey"], mensaje)
            print(f"Enviado con éxito a {u['nombre']}")
        except Exception as e:
            print(f"Error al enviar a {u['nombre']}: {e}")

if __name__ == "__main__":
    main()
