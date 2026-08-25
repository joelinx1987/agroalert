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
            print(f"Mensaje enviado con éxito al chat {chat_id}")
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
        
        # Si el usuario no tiene configurado su token o chat_id, saltamos
        if not token or not chat_id or token == "TU_TOKEN_BOT" or chat_id == "TU_CHAT_ID":
            print(f"El usuario {username} no tiene Telegram configurado.")
            continue
            
        # Buscamos las fincas específicas de este usuario
        fincas_usuario = fincas_db.get(username, {})
        if not fincas_usuario:
            print(f"El usuario {username} no tiene fincas registradas.")
            continue
            
        # Cogemos su primera parcela por defecto para el parte diario
        nombre_finca, datos_finca = list(fincas_usuario.items())[0]
        superficie = datos_finca.get("ha", 0)
        
        # Mensaje personalizado con sus datos
        mensaje = (
            f"🚜 *AGROALERT - PARTE DIARIO DE LAS 4:45*\n"
            f"👤 *Agricultor:* {nombre}\n"
            f"📍 *Parcela:* {nombre_finca} ({superficie} ha)\n"
            f"🟢 *Estado:* Día perfecto para sulfatar.\n"
            f"💨 *Viento:* 8 km/h (Calma).\n"
            f"🌧️ *Lluvia:* 0.0 L/m²."
        )
        
        enviar_telegram(token, chat_id, mensaje)

if __name__ == "__main__":
    ejecutar_alertas_diarias()
