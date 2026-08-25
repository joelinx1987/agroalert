import os
import json
import urllib.request
import urllib.parse

USERS_FILE = "usuarios_db.json"
FINCAS_FILE = "fincas_db.json"

def cargar_json(archivo, por_defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return por_defecto
    return por_defecto

def consultar_meteo_openmeteo(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            current = data.get("current", {})
            return {
                "temp": current.get("temperature_2m", 22.0),
                "lluvia": current.get("precipitation", 0.0),
                "viento": current.get("wind_speed_10m", 8.0)
            }
    except Exception:
        return {"temp": 22.0, "lluvia": 0.0, "viento": 8.0}

def enviar_telegram(token, chat_id, mensaje):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id, 
            'text': mensaje, 
            'parse_mode': 'Markdown'
        }).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True
    except Exception as e:
        print(f"Error al enviar a {chat_id}: {e}")
        return False

def ejecutar_alertas_diarias():
    usuarios = cargar_json(USERS_FILE, {})
    fincas_db = cargar_json(FINCAS_FILE, {})
    
    if not usuarios:
        print("No hay usuarios registrados.")
        return

    for username, info in usuarios.items():
        token = info.get("telegram_token")
        chat_id = info.get("telegram_id")
        nombre = info.get("nombre", username)
        
        if not token or not chat_id:
            continue
            
        fincas_usuario = fincas_db.get(username, {})
        if not fincas_usuario:
            continue
            
        # Construir mensaje claro y detallado con TODAS las fincas
        msg_partes = [f"🚜 *AGROALERT - ESTADO DE TUS FINCAS HOY*\n👤 *Agricultor:* {nombre}"]
        
        for nombre_finca, d_finca in fincas_usuario.items():
            meteo = consultar_meteo_openmeteo(d_finca.get("lat", 42.46), d_finca.get("lon", -2.44))
            
            if meteo["viento"] > 15:
                estado = "⛔ PROHIBIDO SULFATAR (Mucho viento)"
            elif meteo["lluvia"] > 2.0:
                estado = "⛔ PROHIBIDO SULFATAR (Riesgo de lluvia)"
            else:
                estado = "✅ DÍA BUENO PARA ENTRAR"
            
            msg_partes.append(
                f"\n📍 *Finca:* {nombre_finca} ({d_finca.get('ha', 0)} ha)\n"
                f"   • *Consejo:* {estado}\n"
                f"   • *Viento:* {meteo['viento']:.1f} km/h *(Límite: 15)*\n"
                f"   • *Lluvia:* {meteo['lluvia']:.1f} mm"
            )
            
        mensaje_final = "\n".join(msg_partes)
        enviar_telegram(token, chat_id, mensaje_final)

if __name__ == "__main__":
    ejecutar_alertas_diarias()
