import os
import json
import smtplib
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from zoneinfo import ZoneInfo

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_SENDER = os.environ.get("GMAIL_SENDER", "agroalertsoporte@gmail.com")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY.")
if not GMAIL_APP_PASSWORD:
    raise RuntimeError("Falta GMAIL_APP_PASSWORD.")


def supabase_request(method, table, query="", payload=None, prefer=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if query:
        url += f"?{query}"
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def open_meteo(lat, lon):
    params = urllib.parse.urlencode({
        "latitude": float(lat),
        "longitude": float(lon),
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "auto",
        "forecast_days": 1,
    })
    req = urllib.request.Request(
        f"https://api.open-meteo.com/v1/forecast?{params}",
        headers={"User-Agent": "AgroAlert-Scheduler/1.0 contact=agroalertsoporte@gmail.com"},
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    current = data.get("current") or {}
    required = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]
    if any(current.get(k) is None for k in required):
        raise ValueError("Open-Meteo devolvió datos incompletos")
    return {
        "temp": float(current["temperature_2m"]),
        "humedad": float(current["relative_humidity_2m"]),
        "lluvia": float(current["precipitation"]),
        "viento": float(current["wind_speed_10m"]),
        "proveedor": "Open-Meteo",
    }


def met_norway(lat, lon):
    lat = round(float(lat), 4)
    lon = round(float(lon), 4)
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AgroAlert/1.0 agroalertsoporte@gmail.com",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    series = (((data.get("properties") or {}).get("timeseries")) or [])
    if not series:
        raise ValueError("MET Norway no devolvió previsión")
    first = series[0].get("data") or {}
    details = (first.get("instant") or {}).get("details") or {}
    next1 = (first.get("next_1_hours") or {}).get("details") or {}
    temp = details.get("air_temperature")
    hum = details.get("relative_humidity")
    wind_ms = details.get("wind_speed")
    precip = next1.get("precipitation_amount", 0.0)
    if temp is None or hum is None or wind_ms is None:
        raise ValueError("MET Norway devolvió datos incompletos")
    return {
        "temp": float(temp),
        "humedad": float(hum),
        "lluvia": float(precip or 0.0),
        "viento": float(wind_ms) * 3.6,
        "proveedor": "MET Norway",
    }


def meteorologia(lat, lon):
    errores = []
    try:
        return open_meteo(lat, lon)
    except Exception as e:
        errores.append(f"Open-Meteo: {e}")
    try:
        return met_norway(lat, lon)
    except Exception as e:
        errores.append(f"MET Norway: {e}")
    raise RuntimeError(" | ".join(errores))


def construir_parte(row):
    lineas = [
        "AGROALERT - PARTE DIARIO AUTOMÁTICO",
        f"Agricultor: {row.get('nombre') or row.get('username')}",
        "",
    ]
    fincas = row.get("fincas") or []
    if not fincas:
        lineas.append("No hay fincas activas asociadas a este aviso.")
        return "\n".join(lineas)

    for finca in fincas:
        nombre = finca.get("nombre", "Finca")
        ha = finca.get("ha", 0)
        lineas.append("----------------------------------------")
        lineas.append(f"Finca: {nombre} ({ha} ha)")
        try:
            m = meteorologia(finca.get("lat"), finca.get("lon"))
            if m["viento"] > 15:
                estado = "⛔ CONDICIONES NO APTAS PARA TRATAR"
                accion = "Viento excesivo: alto riesgo de deriva."
            elif m["lluvia"] > 2.0:
                estado = "⛔ CONDICIONES NO APTAS PARA TRATAR"
                accion = "Riesgo de lavado por precipitación."
            else:
                estado = "🟢 VÍA LIBRE METEOROLÓGICA PARA TRATAR"
                accion = "Condiciones meteorológicas compatibles con el tratamiento."
            lineas.extend([
                f"ESTADO: {estado}",
                f"Temperatura: {m['temp']:.1f} °C",
                f"Humedad: {m['humedad']:.0f}%",
                f"Viento: {m['viento']:.1f} km/h",
                f"Precipitación: {m['lluvia']:.1f} mm",
                f"Proveedor meteorológico: {m['proveedor']}",
                f"Acción recomendada: {accion}",
            ])
        except Exception as e:
            lineas.extend([
                "ESTADO: ⚠️ DATOS METEOROLÓGICOS NO DISPONIBLES",
                f"Detalle técnico: {e}",
            ])
        lineas.append("")
    return "\n".join(lineas)


def enviar_email(destinatario, asunto, cuerpo, timezone_name="Europe/Madrid"):
    tz = ZoneInfo(timezone_name)
    now_local = datetime.now(tz)
    msg = EmailMessage()
    msg["From"] = f"AgroAlert <{GMAIL_SENDER}>"
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg["Date"] = format_datetime(now_local)
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    msg["Reply-To"] = GMAIL_SENDER
    msg["Auto-Submitted"] = "auto-generated"
    msg.set_content(
        cuerpo
        + f"\n\nHora de emisión: {now_local.strftime('%d/%m/%Y %H:%M:%S %Z')}"
        + "\n\nEste correo ha sido generado automáticamente por AgroAlert.",
        charset="utf-8",
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        rejected = server.send_message(msg, from_addr=GMAIL_SENDER, to_addrs=[destinatario])
    if rejected:
        raise RuntimeError(f"Destinatario rechazado: {rejected}")


def parse_hhmm(value):
    hour, minute = value.split(":", 1)
    return int(hour), int(minute)


def is_due(row, now_utc):
    if not row.get("activo") or not row.get("email") or not row.get("fincas"):
        return False, None, None
    tz_name = row.get("timezone") or "Europe/Madrid"
    tz = ZoneInfo(tz_name)
    now_local = now_utc.astimezone(tz)
    h, m = parse_hhmm(row.get("hora_aviso") or "08:00")
    target = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
    delta = now_local - target
    if delta < timedelta(0) or delta >= timedelta(minutes=30):
        return False, now_local, target
    if row.get("last_sent_local_date") == now_local.date().isoformat():
        return False, now_local, target
    return True, now_local, target


def actualizar_estado(username, payload):
    username_q = urllib.parse.quote(username, safe="")
    supabase_request(
        "PATCH",
        "agroalert_schedules",
        query=f"username=eq.{username_q}",
        payload=payload,
        prefer="return=minimal",
    )


def main():
    now_utc = datetime.now(ZoneInfo("UTC"))
    rows = supabase_request(
        "GET",
        "agroalert_schedules",
        query="select=username,nombre,email,hora_aviso,timezone,fincas,activo,last_sent_local_date",
    ) or []
    print(f"AgroAlert scheduler: {len(rows)} configuraciones revisadas.")

    for row in rows:
        username = row.get("username")
        try:
            due, now_local, target = is_due(row, now_utc)
            if not due:
                continue
            print(f"Enviando a {username} ({row.get('email')}) para horario {target.strftime('%H:%M')}")
            cuerpo = construir_parte(row)
            enviar_email(
                row["email"],
                "🚜 AgroAlert: Tu parte diario de fincas",
                cuerpo,
                row.get("timezone") or "Europe/Madrid",
            )
            actualizar_estado(username, {
                "last_sent_local_date": now_local.date().isoformat(),
                "last_sent_at": now_utc.isoformat(),
                "last_attempt_at": now_utc.isoformat(),
                "last_error": None,
            })
            print(f"OK: {username}")
        except Exception as e:
            print(f"ERROR {username}: {e}")
            try:
                actualizar_estado(username, {
                    "last_error": str(e)[:2000],
                    "last_attempt_at": now_utc.isoformat(),
                })
            except Exception as update_error:
                print(f"No se pudo registrar el error de {username}: {update_error}")


if __name__ == "__main__":
    main()
