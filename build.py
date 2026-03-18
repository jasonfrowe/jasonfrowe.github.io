import os
import re
import shutil
from datetime import datetime
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

SITE_NAME = "Jason Rowe"
SITE_SUBTITLE = "Professor of Physics & Astronomy, Bishop's University"

NAV_ITEMS = [
    {"slug": "home", "label": "Home", "href": "index.html"},
    {"slug": "publications", "label": "Publications", "href": "publications.html"},
    {"slug": "projects", "label": "Projects", "href": "projects.html"},
    {"slug": "cv", "label": "CV", "href": "cv.html"},
    {"slug": "talks", "label": "Talks & Teaching", "href": "talks-teaching.html"},
    {"slug": "contact", "label": "Contact", "href": "contact.html"},
]

CV_SOURCE = os.path.expanduser("~/Documents/LaTeX/CV/rowe-cv.1page.tex")
CV_DIR = "content/cv"
CV_REPO_TEX = os.path.join(CV_DIR, "rowe-cv.1page.tex")
CV_REPO_MD = os.path.join(CV_DIR, "index.md")

PAGES_DIR = "content/pages"


def markdown_to_html(text):
    if not text:
        return ""
    return markdown.markdown(text, extensions=["extra", "sane_lists"])

def clean_latex(text):
    if not text: return ""
    text = str(text).replace("{", "").replace("}", "")
    text = re.sub(r'\\textit\{(.*?)\}', r'<i>\1</i>', text)
    text = text.replace("\\", "").replace("$", "")
    return text.strip()


def latex_inline_to_markdown(text):
    if not text:
        return ""
    cleaned = text
    if cleaned.lstrip().startswith("%"):
        return ""
    cleaned = re.sub(r"(?<!\\)%.*$", "", cleaned)
    cleaned = re.sub(r"\\href\{([^}]+)\}\{([^}]+)\}", r"[\2](\1)", cleaned)
    cleaned = re.sub(r"\\textbf\{([^}]+)\}", r"**\1**", cleaned)
    cleaned = re.sub(r"\\textit\{([^}]+)\}", r"*\1*", cleaned)
    cleaned = re.sub(r"\\emph\{([^}]+)\}", r"*\1*", cleaned)
    cleaned = re.sub(r"\\sc\b", "", cleaned)
    cleaned = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", "", cleaned)
    cleaned = cleaned.replace(r"\\", " ")
    cleaned = cleaned.replace(r"\&", "&")
    cleaned = cleaned.replace(r"\$", "$")
    cleaned = re.sub(r"\\['`\^\"~]\{?([A-Za-z])\}?", r"\1", cleaned)
    cleaned = cleaned.replace("@p3inp4in", "")
    cleaned = cleaned.replace("{", "").replace("}", "")
    cleaned = cleaned.replace("~", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def latex_section_to_markdown(title, body):
    lines = [f"## {title}"]
    title_lower = title.lower()
    in_items = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("\\begin{itemize}"):
            in_items = True
            continue
        if line.startswith("\\end{itemize}"):
            in_items = False
            lines.append("")
            continue
        if line.startswith("\\item"):
            item_text = latex_inline_to_markdown(line.replace("\\item", "", 1).strip())
            if item_text:
                item_text = re.sub(r"^\[\]\s*", "", item_text)
                lines.append(f"- {item_text}")
            continue
        parsed = latex_inline_to_markdown(line)
        if parsed:
            if parsed.startswith("@p"):
                continue
            parsed = re.sub(r"^\[\]\s*", "", parsed)
            if title_lower.startswith("contact") and " & " in line:
                left, right = line.split("&", 1)
                left_clean = latex_inline_to_markdown(left)
                right_clean = latex_inline_to_markdown(right)
                combined = " | ".join([p for p in [left_clean, right_clean] if p])
                if combined:
                    lines.append(f"- {combined}")
                continue
            if in_items:
                lines.append(f"- {parsed}")
            else:
                if title_lower in ["research interests"]:
                    lines.append(parsed)
                else:
                    lines.append(f"- {parsed}")
    lines.append("")
    return "\n".join(lines)


def import_cv_once():
    os.makedirs(CV_DIR, exist_ok=True)
    force_import = os.getenv("CV_FORCE_IMPORT") == "1"

    if os.path.exists(CV_REPO_MD) and not force_import:
        return "existing"

    if not os.path.exists(CV_SOURCE):
        return "missing-source"

    with open(CV_SOURCE, "r", encoding="utf-8") as f:
        tex = f.read()

    shutil.copyfile(CV_SOURCE, CV_REPO_TEX)

    sections = re.findall(r"\\section\{([^}]+)\}(.*?)(?=\\section\{|\\end\{document\}|\Z)", tex, flags=re.DOTALL)
    md_parts = ["---", "title: Curriculum Vitae", "---", ""]

    if sections:
        for section_title, section_body in sections:
            normalized_title = clean_latex(section_title)
            normalized_title = re.sub(r"^sc\s+", "", normalized_title, flags=re.IGNORECASE)
            md_parts.append(latex_section_to_markdown(normalized_title, section_body))
    else:
        md_parts.extend([
            "## Curriculum Vitae",
            "CV source was imported, but structured sections were not detected.",
            "Please edit this page directly in markdown.",
            "",
        ])

    with open(CV_REPO_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_parts).strip() + "\n")

    return "imported"

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
        return header, markdown_to_html(body.strip()) if body.strip() else ""
    return {}, ""


def read_page_markdown(filename, fallback_title, fallback_body):
    path = os.path.join(PAGES_DIR, filename)
    if os.path.exists(path):
        header, body_html = parse_md(path)
        return {
            "title": header.get("title", fallback_title),
            "intro": header.get("summary", ""),
            "html": body_html,
        }
    return {
        "title": fallback_title,
        "intro": "",
        "html": markdown_to_html(fallback_body),
    }


def build_publications_html():
    pubs_by_year = defaultdict(list)
    pub_dir = "content/publication"

    if os.path.exists(pub_dir):
        for root, dirs, files in os.walk(pub_dir):
            if "index.md" in files:
                header, body_html = parse_md(os.path.join(root, "index.md"))
                year = str(header.get("date", "1900-01-01"))[:4]
                title = clean_latex(header.get("title", "Untitled Paper"))
                venue = clean_latex(header.get("publication", header.get("journal", "Unknown Journal")))

                cleaned_authors = [clean_latex(a) for a in header.get("authors", [])]
                author_str = ", ".join(cleaned_authors)
                for name in ["Jason Rowe", "Jason F. Rowe", "Rowe, J. F.", "Rowe, J."]:
                    author_str = author_str.replace(name, f"<strong>{name}</strong>")

                url = header.get("url_pdf", header.get("adsurl", "#"))
                pubs_by_year[year].append(f"""
                <article class='pub-card'>
                    <h3 class='card-title'>{title}</h3>
                    <p class='card-meta'>{author_str}</p>
                    <p class='card-submeta'><em>{venue} ({year})</em></p>
                    {f"<div class='card-body'>{body_html}</div>" if body_html else ""}
                    <p><a class='btn-link' href='{url}' target='_blank' rel='noopener noreferrer'>View Paper</a></p>
                </article>
                """)

    sorted_years = sorted(pubs_by_year.keys(), reverse=True)
    return "".join([f"<h2 class='year-label'>{y}</h2>" + "".join(pubs_by_year[y]) for y in sorted_years])


def build_projects_html():
    pro_cards = ""
    for repo in PRO_REPOS:
        pro_cards += f"""
        <article class='project-card'>
            <h3>{repo}</h3>
            <p>Professional software repository.</p>
            <p><a class='btn-link' href='https://github.com/jasonfrowe/{repo}' target='_blank' rel='noopener noreferrer'>Open on GitHub</a></p>
        </article>
        """

    retro_cards = ""
    for repo in RETRO_REPOS:
        retro_cards += f"""
        <article class='project-card personal'>
            <h3>{repo}</h3>
            <p>Personal or retro-computing project.</p>
            <p><a class='btn-link' href='https://github.com/jasonfrowe/{repo}' target='_blank' rel='noopener noreferrer'>Open on GitHub</a></p>
        </article>
        """

    proj_dir = "content/project"
    if os.path.exists(proj_dir):
        for root, dirs, files in os.walk(proj_dir):
            for file in files:
                if file.endswith(".md"):
                    header, html = parse_md(os.path.join(root, file))
                    title = header.get("title", "Project")
                    tags = "".join([f"<span class='tag'>{t}</span>" for t in header.get("tags", [])])
                    link = header.get("external_link", "#")
                    retro_cards += (
                        f"<article class='project-card personal'><h3>{title}</h3>"
                        f"<p>{tags}</p>{html}"
                        f"<p><a class='btn-link' href='{link}' target='_blank' rel='noopener noreferrer'>Open Project</a></p></article>"
                    )

    return f"""
    <section>
        <h2>Professional Software</h2>
        <div class='projects-grid'>{pro_cards}</div>
    </section>
    <section>
        <h2>Personal and Retro-Computing</h2>
        <div class='projects-grid'>{retro_cards}</div>
    </section>
    """


def build_cv_html(cv_status):
    if os.path.exists(CV_REPO_MD):
        header, body_html = parse_md(CV_REPO_MD)
        title = header.get("title", "Curriculum Vitae")
        subtitle = "This page is maintained in-repo at content/cv/index.md."
        if cv_status == "imported":
            subtitle = "Initial CV import complete. You can now edit this page directly in markdown."
        return f"<section><h2>{title}</h2><p class='note'>{subtitle}</p>{body_html}</section>"

    return (
        "<section><h2>Curriculum Vitae</h2>"
        "<p class='note'>CV source was not found at ~/Documents/LaTeX/CV/rowe-cv.1page.tex. "
        "Create content/cv/index.md to maintain this page in-repo.</p></section>"
    )


def render_page(template, output_file, active_slug, page_title, page_intro, content_html):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template.render(
            title=f"{page_title} | {SITE_NAME}",
            page_title=page_title,
            page_intro=page_intro,
            site_name=SITE_NAME,
            site_subtitle=SITE_SUBTITLE,
            nav_items=NAV_ITEMS,
            active_page=active_slug,
            content_html=content_html,
            current_year=str(datetime.now().year),
        ))


def ensure_page_content_files():
    os.makedirs(PAGES_DIR, exist_ok=True)

    defaults = {
        "home.md": """---
title: About
summary: Exoplanets, software, and hands-on engineering.
---

I am a professor and builder who works at the intersection of astronomy, data analysis, and practical software engineering.

This site is designed as a lightweight, easy-to-navigate hub for my research output and active code projects.

### Highlights

- Research profile focused on exoplanet discovery and characterization
- Open-source tooling for astronomy workflows
- Ongoing retro-computing and embedded systems projects
""",
        "talks-teaching.md": """---
title: Talks and Teaching
summary: Talks, mentorship, and classroom work.
---

Add invited talks, conference presentations, courses, and mentorship highlights here.

### Suggested Structure

- Invited talks
- Conference contributions
- Courses taught
- Student supervision
""",
        "contact.md": """---
title: Contact
summary: Ways to connect.
---

- Email: [jrowe@ubishops.ca](mailto:jrowe@ubishops.ca)
- GitHub: [github.com/jasonfrowe](https://github.com/jasonfrowe)
- ADS profile and publication links are available on the Publications page.
""",
    }

    for filename, content in defaults.items():
        path = os.path.join(PAGES_DIR, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")


def main():
    ensure_page_content_files()
    cv_status = import_cv_once()

    with open("template.html", "r", encoding="utf-8") as f:
        template = Template(f.read())

    home_page = read_page_markdown(
        "home.md",
        fallback_title="About",
        fallback_body="Welcome to my academic and software portfolio.",
    )
    talks_page = read_page_markdown(
        "talks-teaching.md",
        fallback_title="Talks and Teaching",
        fallback_body="Add talks and teaching content in content/pages/talks-teaching.md.",
    )
    contact_page = read_page_markdown(
        "contact.md",
        fallback_title="Contact",
        fallback_body="Add contact details in content/pages/contact.md.",
    )

    pages = [
        {
            "output": "index.html",
            "slug": "home",
            "title": home_page["title"],
            "intro": home_page["intro"],
            "html": home_page["html"],
        },
        {
            "output": "publications.html",
            "slug": "publications",
            "title": "Publications",
            "intro": "Peer-reviewed publications and conference contributions.",
            "html": build_publications_html(),
        },
        {
            "output": "projects.html",
            "slug": "projects",
            "title": "Projects",
            "intro": "Selected software repositories and personal engineering projects.",
            "html": build_projects_html(),
        },
        {
            "output": "cv.html",
            "slug": "cv",
            "title": "Curriculum Vitae",
            "intro": "Academic and professional background.",
            "html": build_cv_html(cv_status),
        },
        {
            "output": "talks-teaching.html",
            "slug": "talks",
            "title": talks_page["title"],
            "intro": talks_page["intro"],
            "html": talks_page["html"],
        },
        {
            "output": "contact.html",
            "slug": "contact",
            "title": contact_page["title"],
            "intro": contact_page["intro"],
            "html": contact_page["html"],
        },
    ]

    for page in pages:
        render_page(
            template=template,
            output_file=page["output"],
            active_slug=page["slug"],
            page_title=page["title"],
            page_intro=page["intro"],
            content_html=page["html"],
        )

    print(f"Built {len(pages)} pages.")
    if cv_status == "imported":
        print(f"Imported CV from {CV_SOURCE} to {CV_REPO_MD}.")
    elif cv_status == "existing":
        print(f"Using existing in-repo CV at {CV_REPO_MD}.")
    else:
        print("CV source not found and no in-repo CV exists yet.")


if __name__ == "__main__":
    main()