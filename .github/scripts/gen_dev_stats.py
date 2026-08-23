"""
gen_dev_stats.py

Genera las 3 imágenes de la sección "## ▣ Estadísticas de Desarrollo" a partir
de datos reales de la API de GitHub (REST + GraphQL), sin depender de
servicios de terceros (github-readme-stats, github-readme-activity-graph, etc.):

  - assets/stats-card.svg    -> repos, seguidores, estrellas, commits, PRs, issues
  - assets/top-langs.svg     -> lenguajes más usados (bytes de código) por repo propio
  - assets/activity-graph.svg -> calendario de contribuciones del último año

Usa el mismo estilo visual que el resto del README (fondo #0d0221, acento
#F2A93B, acento secundario #B084F2).

Requiere GITHUB_TOKEN (provisto automáticamente por el workflow vía
secrets.GITHUB_TOKEN) y GITHUB_USERNAME.
"""

import os
import re
import requests

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "Joako601")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
API_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
ASSETS_DIR = "assets"
README_PATH = "README.md"

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

BG = "#0d0221"
ACCENT = "#F2A93B"
ACCENT_2 = "#B084F2"
TEXT = "#e6e6e6"

# Colores reales por lenguaje para las barras de top-langs (fallback: se
# alternan ACCENT/ACCENT_2 si el lenguaje no está en el mapa).
LANG_COLORS = {
    "C#": "#178600",
    "Java": "#b07219",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Dockerfile": "#384d54",
    "Shell": "#89e051",
    "PowerShell": "#012456",
    "PLpgSQL": "#336790",
    "SCSS": "#c6538c",
    "Vue": "#41b883",
    "Gherkin": "#5B2063",
}


def get_owned_repos():
    """Todos los repos propios (no forks) de GITHUB_USERNAME."""
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"{API_BASE}/users/{GITHUB_USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        if r.status_code != 200:
            print(f"[WARN] get_owned_repos falló (status {r.status_code}): {r.text[:200]}")
            break
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [repo for repo in repos if not repo.get("fork")]


def get_user_profile():
    r = requests.get(f"{API_BASE}/users/{GITHUB_USERNAME}", headers=HEADERS)
    if r.status_code != 200:
        print(f"[WARN] get_user_profile falló (status {r.status_code}): {r.text[:200]}")
        return {}
    return r.json()


def search_count(endpoint, query):
    """Total_count de /search/commits o /search/issues."""
    r = requests.get(
        f"{API_BASE}/search/{endpoint}",
        headers={**HEADERS, "Accept": "application/vnd.github.cloak-preview+json"},
        params={"q": query, "per_page": 1},
    )
    if r.status_code != 200:
        print(f"[WARN] search_count({endpoint!r}, {query!r}) falló (status {r.status_code}): {r.text[:200]}")
        return 0
    return r.json().get("total_count", 0)


def get_total_commits():
    return search_count("commits", f"author:{GITHUB_USERNAME}")


def get_total_prs():
    return search_count("issues", f"author:{GITHUB_USERNAME} type:pr")


def get_total_issues():
    return search_count("issues", f"author:{GITHUB_USERNAME} type:issue")


def get_language_bytes(repos):
    totals = {}
    for repo in repos:
        url = repo.get("languages_url")
        if not url:
            continue
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"[WARN] languages_url de {repo['name']} falló (status {r.status_code})")
            continue
        for lang, count in r.json().items():
            totals[lang] = totals.get(lang, 0) + count
    return totals


def get_contribution_calendar():
    """Calendario de contribuciones del último año vía GraphQL."""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                weekday
              }
            }
          }
        }
      }
    }
    """
    r = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": {"login": GITHUB_USERNAME}},
    )
    if r.status_code != 200:
        print(f"[WARN] get_contribution_calendar falló (status {r.status_code}): {r.text[:200]}")
        return None
    data = r.json()
    if "errors" in data:
        print(f"[WARN] get_contribution_calendar devolvió errores: {data['errors']}")
        return None
    try:
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except (KeyError, TypeError):
        print("[WARN] Respuesta de GraphQL sin el shape esperado.")
        return None


def escape_xml_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_stats_card_svg(stats, width=450):
    rows = [
        ("Repositorios públicos", stats["public_repos"]),
        ("Seguidores", stats["followers"]),
        ("Total de estrellas", stats["total_stars"]),
        ("Total de commits", stats["total_commits"]),
        ("Pull Requests", stats["total_prs"]),
        ("Issues", stats["total_issues"]),
    ]
    row_h = 34
    top_pad = 62
    bottom_pad = 20
    height = top_pad + row_h * len(rows) + bottom_pad

    lines = []
    for i, (label, value) in enumerate(rows):
        y = top_pad + i * row_h
        lines.append(f'''
    <text x="24" y="{y}" font-family="monospace" font-size="14" fill="{TEXT}">⟡ {escape_xml_text(label)}</text>
    <text x="{width - 24}" y="{y}" font-family="monospace" font-size="14" font-weight="bold"
          text-anchor="end" fill="{ACCENT}">{escape_xml_text(value)}</text>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"
        fill="{BG}" stroke="{ACCENT}" stroke-opacity="0.4"/>
  <text x="24" y="34" font-family="monospace" font-size="16" font-weight="bold" fill="{ACCENT}">
    {escape_xml_text(GITHUB_USERNAME)}'s GitHub Stats
  </text>
  {"".join(lines)}
</svg>'''


def build_top_langs_svg(lang_bytes, width=450, top_n=6):
    total = sum(lang_bytes.values()) or 1
    top = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    row_h = 34
    top_pad = 62
    bottom_pad = 20
    height = top_pad + row_h * len(top) + bottom_pad
    bar_max_w = width - 48

    lines = []
    for i, (lang, count) in enumerate(top):
        pct = count / total * 100
        y = top_pad + i * row_h
        bar_w = max(bar_max_w * (pct / 100), 2)
        color = LANG_COLORS.get(lang, ACCENT if i % 2 == 0 else ACCENT_2)
        lines.append(f'''
    <text x="24" y="{y}" font-family="monospace" font-size="13" fill="{TEXT}">{escape_xml_text(lang)}</text>
    <text x="{width - 24}" y="{y}" font-family="monospace" font-size="13"
          text-anchor="end" fill="{TEXT}">{pct:.1f}%</text>
    <rect x="24" y="{y + 8}" width="{bar_max_w}" height="6" rx="3" fill="{ACCENT}" fill-opacity="0.12"/>
    <rect x="24" y="{y + 8}" width="{bar_w:.1f}" height="6" rx="3" fill="{color}"/>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"
        fill="{BG}" stroke="{ACCENT}" stroke-opacity="0.4"/>
  <text x="24" y="34" font-family="monospace" font-size="16" font-weight="bold" fill="{ACCENT}">
    Lenguajes más usados
  </text>
  {"".join(lines)}
</svg>'''


def build_activity_svg(calendar, size=10, gap=3, width_hint=900):
    weeks = calendar["weeks"] if calendar else []
    total = calendar["totalContributions"] if calendar else 0
    step = size + gap
    grid_w = len(weeks) * step
    grid_h = 7 * step
    pad_x = 24
    top_pad = 50
    bottom_pad = 20
    width = grid_w + pad_x * 2
    height = top_pad + grid_h + bottom_pad

    def bucket_color(count):
        if count <= 0:
            return f"{ACCENT}1a"  # muy tenue
        if count <= 3:
            return f"{ACCENT}55"
        if count <= 6:
            return f"{ACCENT}99"
        if count <= 9:
            return ACCENT
        return ACCENT_2

    cells = []
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = pad_x + wi * step
            y = top_pad + day["weekday"] * step
            count = day["contributionCount"]
            cells.append(
                f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2" '
                f'fill="{bucket_color(count)}"><title>{escape_xml_text(day["date"])}: '
                f'{count} contribuciones</title></rect>'
            )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"
        fill="{BG}" stroke="{ACCENT}" stroke-opacity="0.4"/>
  <text x="{pad_x}" y="32" font-family="monospace" font-size="16" font-weight="bold" fill="{ACCENT}">
    {total} contribuciones en el último año
  </text>
  {"".join(cells)}
</svg>'''


def update_readme_section():
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    block = (
        '<div align="center">\n'
        f'  <img src="./{ASSETS_DIR}/stats-card.svg" width="48%" alt="Estadísticas de GitHub"/>\n'
        f'  <img src="./{ASSETS_DIR}/top-langs.svg" width="48%" alt="Lenguajes más usados"/>\n'
        '</div>\n\n'
        '<div align="center">\n'
        f'  <img src="./{ASSETS_DIR}/activity-graph.svg" width="97%" alt="Calendario de contribuciones"/>\n'
        '</div>'
    )

    pattern = r'(## ▣ Estadísticas de Desarrollo\s*\n\s*).*?(\n\s*---)'
    if not re.search(pattern, readme, flags=re.DOTALL):
        print("[WARN] No se encontró la sección '## ▣ Estadísticas de Desarrollo' en README.md")
        return

    readme_new = re.sub(pattern, r"\1" + block + r"\2", readme, flags=re.DOTALL)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme_new)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    profile = get_user_profile()
    repos = get_owned_repos()
    print(f"[INFO] Repos propios (no fork): {[r['name'] for r in repos]}")

    stats = {
        "public_repos": profile.get("public_repos", len(repos)),
        "followers": profile.get("followers", 0),
        "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
        "total_commits": get_total_commits(),
        "total_prs": get_total_prs(),
        "total_issues": get_total_issues(),
    }
    print(f"[INFO] Stats: {stats}")

    lang_bytes = get_language_bytes(repos)
    print(f"[INFO] Bytes por lenguaje: {lang_bytes}")

    calendar = get_contribution_calendar()

    with open(os.path.join(ASSETS_DIR, "stats-card.svg"), "w", encoding="utf-8") as f:
        f.write(build_stats_card_svg(stats))

    with open(os.path.join(ASSETS_DIR, "top-langs.svg"), "w", encoding="utf-8") as f:
        f.write(build_top_langs_svg(lang_bytes))

    # Si el GraphQL falló (rate limit, permisos, etc.) preferimos conservar
    # el activity-graph.svg de la corrida anterior antes que pisarlo con una
    # tarjeta vacía/rota.
    if calendar and calendar.get("weeks"):
        with open(os.path.join(ASSETS_DIR, "activity-graph.svg"), "w", encoding="utf-8") as f:
            f.write(build_activity_svg(calendar))
    else:
        print("[WARN] No se pudo obtener el calendario de contribuciones; se conserva activity-graph.svg existente.")

    update_readme_section()
    print("README y SVGs de estadísticas actualizados.")


if __name__ == "__main__":
    main()
