from pathlib import Path
import shutil
import re

cfg = Path('.streamlit/config.toml')
text = cfg.read_text(encoding='utf-8') if cfg.exists() else ''
if '[server]' not in text:
    text += '\n[server]\nenableStaticServing = true\n'
elif 'enableStaticServing' not in text:
    text = text.replace('[server]', '[server]\nenableStaticServing = true', 1)
else:
    text = re.sub(r'enableStaticServing\s*=\s*(true|false)', 'enableStaticServing = true', text)
cfg.parent.mkdir(parents=True, exist_ok=True)
cfg.write_text(text, encoding='utf-8')

static = Path('static')
static.mkdir(exist_ok=True)
logo_candidates = [Path('logo.png.jpg'), Path('logo.png'), Path('logo.jpg'), Path('fondo_logo.jpg.jpg')]
logo = next((p for p in logo_candidates if p.exists()), None)
if logo:
    shutil.copyfile(logo, static / 'agroalert-icon.jpg')

manifest = '''{
  "name": "AgroAlert",
  "short_name": "AgroAlert",
  "description": "Asistente agrícola profesional",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#f8fafc",
  "theme_color": "#16a34a",
  "icons": [{"src":"/app/static/agroalert-icon.jpg","sizes":"512x512","type":"image/jpeg","purpose":"any maskable"}]
}\n'''
(static / 'manifest.webmanifest').write_text(manifest, encoding='utf-8')

app = Path('app.py')
code = app.read_text(encoding='utf-8')
code = code.replace('for posibles_nombres in ["logo.png", "logo.jpg", "fondo_logo.jpg.jpg"]:', 'for posibles_nombres in ["logo.png.jpg", "logo.png", "logo.jpg", "fondo_logo.jpg.jpg"]:', 1)
code = code.replace('page_title="AgroAlert | Asistente Agrícola Profesional"', 'page_title="AgroAlert"', 1)
app.write_text(code, encoding='utf-8')
