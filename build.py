import os
import re
import markdown
import yaml
from jinja2 import Template
from collections import defaultdict

# --- NEW: HARDCODED GITHUB REPOSITORIES ---
PRO_REPOS = [
    "bls_cuda", "Pandora_AUX_Tools", "Kepler_TTV", "poet", 
    "neossat", "autotransit", "Kepler", "jwst", "Neptune", 
    "MOST", "JWSTNIRISS", "gprocess", "home_monitor"
]

RETRO_REPOS = [
    "Astrowing", "RPMegaFighter", "RPTracker", "RPMegaChopper",
    "Atari7800_AstroCart", "RPMegaRacer", "MySegaGame", "RP6502-Cosmic-Arc",
    "RP6502_OPL2", "RPGalaxy", "PicoOPL2", "Atari7800_ROM_Emulator", 
    "RP6502_OPL2_FPGA", "pico_jukebox", "fpga_opl2", "2600MultiCart", 
    "midisequencer"
]

def clean_latex(text):
    if not text: return ""
    text = str(text).replace("{", "").replace("}", "")
    text = re.sub(r'\\textit\{(.*?)\}', r'<i>\1</i>', text)
    text = text.replace("\\", "").replace("$", "")
    return text.strip()

def parse_md(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    parts = re.split(r'^---', content, maxsplit=2, flags=re.MULTILINE)
    
    if len(parts) >= 3:
        try:
            header = yaml.safe_load(parts[1]) or {}
        except Exception:
            header = {}
        body = parts[2]
        body = re.sub(r'(?i).*Add the full text.*', '', body)
        body = re.sub(r'(?i).*supplementary notes.*', '', body)
        return header, markdown.markdown(body.strip()) if body.strip() else ""
    return {}, ""

# 1. Process Publications (Unchanged)
pubs_by_year = defaultdict(list)
pub_dir = "content/publication"

if os.path.exists(pub_dir):
    for root, dirs, files in os.walk(pub_dir):
        if "index.md" in files:
            header, body_html = parse_md(os.path.join(root, "index.md"))
            year = str(header.get('date', '1900-01-01'))[:4]
            title = clean_latex(header.get('title', 'Untitled Paper'))
            venue = clean_latex(header.get('publication', header.get('journal', 'Unknown Journal')))
            
            cleaned_authors = [clean_latex(a) for a in header.get('authors', [])]
            author_str = ", ".join(cleaned_authors)
            for name in ["Jason Rowe", "Jason F. Rowe", "Rowe, J. F.", "Rowe, J."]:
                author_str = author_str.replace(name, f"<strong>{name}</strong>")

            url = header.get('url_pdf', header.get('adsurl', '#'))
            pubs_by_year[year].append(f"""
            <div class='pub-card'>
                <div style="font-weight: bold; font-size: 1.1em; color: var(--accent);">{title}</div>
                <div style="font-size: 0.9em; margin: 5px 0; color: #444;">{author_str}</div>
                <div style="font-style: italic; color: #777; font-size: 0.85em;">{venue} ({year})</div>
                {f"<div style='font-size: 0.85em; margin-top: 10px; color: #555;'>{body_html}</div>" if body_html else ""}
                <div style="margin-top: 10px;"><a href='{url}' target='_blank' style='font-size: 0.8em; text-decoration: none; border: 1px solid var(--accent); padding: 2px 8px; border-radius: 3px; color: var(--accent);'>View on ADS/PDF</a></div>
            </div>
            """)

# 2. Process Auto-Generated Repositories
pro_html = ""
for repo in PRO_REPOS:
    pro_html += f"""
    <div class='pro-card'>
        <a href='https://github.com/jasonfrowe/{repo}' target='_blank'>🗄️ {repo}</a>
    </div>
    """

retro_html = ""
for repo in RETRO_REPOS:
    retro_html += f"""
    <div class='game-card'>
        <h3>{repo}</h3>
        <a href='https://github.com/jasonfrowe/{repo}' target='_blank'>ACCESS_SOURCE</a>
    </div>
    """

# Add in any custom Markdown projects you wrote earlier (like the expanded Astrowing notes)
proj_dir = "content/project"
if os.path.exists(proj_dir):
    for root, dirs, files in os.walk(proj_dir):
        for file in files:
            if file.endswith(".md"):
                header, html = parse_md(os.path.join(root, file))
                title = header.get('title', 'Project')
                tags = "".join([f"<span class='tag' style='background: var(--accent); color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-right: 5px;'>{t}</span>" for t in header.get('tags', [])])
                link = header.get('external_link', '#')
                retro_html += f"<div class='game-card'><h3>{title}</h3><div style='margin-bottom: 10px;'>{tags}</div>{html}<a href='{link}' target='_blank'>ACCESS_SOURCE</a></div>"

# 3. Sort and Render
sorted_years = sorted(pubs_by_year.keys(), reverse=True)
pubs_output = "".join([f"<span class='year-label'>{y}</span>" + "".join(pubs_by_year[y]) for y in sorted_years])

with open('template.html', 'r') as f:
    template = Template(f.read())

with open('index.html', 'w') as f:
    f.write(template.render(
        title="Jason Rowe | Repos & Research", 
        pubs_html=pubs_output, 
        pro_html=pro_html,
        retro_html=retro_html
    ))

print(f"Site built successfully! Added {len(PRO_REPOS)} Professional repos and {len(RETRO_REPOS)} Retro repos.")