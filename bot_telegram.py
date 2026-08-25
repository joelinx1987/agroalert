import os
import json
import urllib.request
import urllib.parse
import time

TOKEN = "8717165365:AAEqfcf5KKG0f6yVDAvrdW4QhxQLLV7IsSs"

def enviar_mensaje(chat_id, texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'User-Agent': 'AgroAlert/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return False

def verificar_mensajes():
    print("🤖 Bot de Telegram escuchando para dar códigos de ID...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/1.0'})
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get("ok"):
                    for result in data.get("result", []):
                        offset = result["update_id"] + 1
                        message = result.get("message")
                        if message and "chat" in message:
                            chat_id = message["chat"]["id"]
                            nombre = message["chat"].get("first_name", "Amigo")
                            
                            texto_respuesta = (
                                f"🌾 ¡Hola {nombre}!\n\n"
                                f"Tu número de identificación (Chat ID) para registrarte en AgroAlert es:\n\n"
                                f"👉 `{chat_id}` 👈\n\n"
                                f"Copia este número y ponlo en la aplicación web."
                            )
                            enviar_mensaje(chat_id, texto_respuesta)
        except Exception as e:
            print(f"Bucle de escucha: {e}")
            time.sleep(5)

if __name__ == "__main__":
    verificar_mensajes()
