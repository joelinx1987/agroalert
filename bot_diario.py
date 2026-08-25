import urllib.request
import urllib.parse

telefono = "+34626665232"  # Tu número
apikey = "3443251"         # Tu clave de CallMeBot

mensaje = "🚜 *AGROALERT - PARTE DE LAS 11:55*\n📍 *Parcela:* Viñedo Principal\n🟢 *Estado:* Día perfecto para sulfatar.\n💨 *Viento:* 8 km/h (Calma).\n🌧️ *Lluvia:* 0 mm."

try:
    num_limpio = telefono.replace(" ", "").replace("+", "").replace("-", "")
    texto_encoded = urllib.parse.quote(mensaje)
    url = f"https://api.callmebot.com/whatsapp.php?phone={num_limpio}&text={texto_encoded}&apikey={apikey}"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'AgroAlert/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("¡Mensaje enviado con éxito!")
except Exception as e:
    print(f"Error al enviar: {e}")
