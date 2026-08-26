from pathlib import Path

path = Path("app.py")
lines = path.read_text(encoding="utf-8").splitlines()

if any('help="Puedes elegir cualquier minuto, por ejemplo 03:23."' in line for line in lines):
    print("La app ya permite cualquier minuto.")
    raise SystemExit(0)

start = next((i for i, line in enumerate(lines) if "horas_opciones = [time(h, m) for h in range(24) for m in (0, 30)]" in line), None)
if start is None:
    raise SystemExit("No se encontró el selector antiguo.")

end = next((i for i in range(start, len(lines)) if "format_func=lambda t: t.strftime" in lines[i]), None)
if end is None:
    raise SystemExit("No se encontró el final del selector antiguo.")
end += 2

indent = "            "
replacement = [
    indent + "nueva_hora_sel = st.time_input(",
    indent + "    \"⏰ Elige la hora exacta para recibir tu parte:\",",
    indent + "    value=t_default,",
    indent + "    step=60,",
    indent + "    help=\"Puedes elegir cualquier minuto, por ejemplo 03:23.\"",
    indent + ")",
]

lines[start:end] = replacement
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Selector horario actualizado correctamente.")
