"""
gen_dev_stats.py

Genera las 3 imágenes de la sección "## ▣ Estadísticas de Desarrollo" a partir
de datos reales de la API de GitHub (REST + GraphQL), sin depender de
servicios de terceros (github-readme-stats, github-readme-activity-graph, etc.):

  - assets/stats-card.svg     -> repos, seguidores, estrellas, commits, PRs, issues
  - assets/top-langs.svg      -> lenguajes más usados (bytes de código) por repo propio
  - assets/activity-graph.svg -> calendario de contribuciones del último año, como
                                  un campo de estrellas (cada día es una estrella;
                                  su tamaño/brillo escala con los commits de ese día)

Continúa el mismo lenguaje visual del resto del perfil (cielo nocturno de
banner-top.svg: fondo #0d0221 -> #1a0a3d, acentos #F2A93B / #B084F2 / #FCEFCB,
tipografía 'Fira Code', estrellas titilantes, destellos de 4 puntas, spinner
como el de collaborators-marquee.svg).

Requiere GITHUB_TOKEN (provisto automáticamente por el workflow vía
secrets.GITHUB_TOKEN) y GITHUB_USERNAME.
"""

import os
import re
import requests

from svg_theme import (
    BG_1, BG_2, ACCENT, ACCENT_2, CREAM, MUTED_GOLD, LAVENDER_DIM, FONT_STACK,
    escape_xml_text, lerp_color, shared_style, bg_stars, sparkle, sync_icon,
    card_chrome, title_block,
)

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "Joako601")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
API_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
ASSETS_DIR = "assets"
README_PATH = "README.md"

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# Colores reales por lenguaje para las barras de top-langs (semántico, separado
# del acento de marca; fallback: alterna ACCENT/ACCENT_2 si no está mapeado).
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


# ---------------------------------------------------------------------------
# Fetch de datos (sin cambios de comportamiento)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tarjetas
# ---------------------------------------------------------------------------

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
    uid = "stats"

    lines = []
    for i, (label, value) in enumerate(rows):
        y = top_pad + i * row_h
        delay = 0.15 + i * 0.08
        lines.append(f'''
    <g class="reveal" style="animation-delay:{delay:.2f}s">
      {sparkle(30, y - 4, 3.6, ACCENT, f"twinkle-{'abc'[i % 3]}")}
      <text x="42" y="{y}" class="label">{escape_xml_text(label)}</text>
      <text x="{width - 24}" y="{y}" class="value" text-anchor="end">{escape_xml_text(value)}</text>
    </g>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {shared_style()}
  {card_chrome(uid, width, height)}
  {title_block(uid, f"{GITHUB_USERNAME}'s GitHub Stats", width)}
  {"".join(lines)}
</svg>'''


def build_top_langs_svg(lang_bytes, width=450, top_n=6):
    total = sum(lang_bytes.values()) or 1
    top = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    row_h = 34
    top_pad = 62
    bottom_pad = 20
    height = top_pad + row_h * len(top) + bottom_pad
    bar_max_w = width - 66
    uid = "langs"

    lines = []
    for i, (lang, count) in enumerate(top):
        pct = count / total * 100
        y = top_pad + i * row_h
        bar_w = max(bar_max_w * (pct / 100), 2)
        bar_y = y + 8
        color = LANG_COLORS.get(lang, ACCENT if i % 2 == 0 else ACCENT_2)
        delay = 0.15 + i * 0.08
        grow_delay = delay + 0.15
        lines.append(f'''
    <g class="reveal" style="animation-delay:{delay:.2f}s">
      {sparkle(30, y - 4, 3.2, color, "")}
      <text x="42" y="{y}" class="label">{escape_xml_text(lang)}</text>
      <text x="{width - 24}" y="{y}" class="label" text-anchor="end">{pct:.1f}%</text>
      <rect x="42" y="{bar_y}" width="{bar_max_w - 18}" height="6" rx="3" fill="{ACCENT}" fill-opacity="0.12"/>
      <rect x="42" y="{bar_y}" width="0" height="6" rx="3" fill="{color}">
        <animate attributeName="width" from="0" to="{bar_w - 18:.1f}" dur="0.9s"
                 begin="{grow_delay:.2f}s" fill="freeze"
                 calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
      </rect>
      <circle r="2.4" fill="#ffffff" opacity="0">
        <animateMotion path="M42 {bar_y + 3} L{42 + bar_w - 18:.1f} {bar_y + 3}"
                        dur="0.9s" begin="{grow_delay:.2f}s" fill="freeze"/>
        <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.85;1"
                  dur="0.9s" begin="{grow_delay:.2f}s" fill="freeze"/>
      </circle>
    </g>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {shared_style()}
  {card_chrome(uid, width, height)}
  {title_block(uid, "Lenguajes más usados", width)}
  {"".join(lines)}
</svg>'''


def build_activity_svg(calendar, size=10, gap=4):
    weeks = calendar["weeks"] if calendar else []
    total = calendar["totalContributions"] if calendar else 0
    step = size + gap
    grid_w = max(len(weeks) * step, 1)
    grid_h = 7 * step
    pad_x = 24
    top_pad = 60
    bottom_pad = 22
    width = grid_w + pad_x * 2
    height = top_pad + grid_h + bottom_pad
    uid = "activity"

    # días con conteo real, para escalar tamaño/brillo y encontrar el pico
    all_days = [d for w in weeks for d in w["contributionDays"]]
    max_count = max((d["contributionCount"] for d in all_days), default=0)
    peak = max(all_days, key=lambda d: d["contributionCount"], default=None) if all_days else None

    stars = []
    peak_candidates = sorted(
        [d for d in all_days if d["contributionCount"] > 0],
        key=lambda d: d["contributionCount"], reverse=True,
    )[:3]
    peak_dates = {d["date"] for d in peak_candidates}

    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = pad_x + wi * step + size / 2
            y = top_pad + day["weekday"] * step + size / 2
            count = day["contributionCount"]
            title = f'{escape_xml_text(day["date"])}: {count} contribuciones'

            if count <= 0:
                stars.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.1" fill="{LAVENDER_DIM}" '
                    f'opacity="0.3"><title>{title}</title></circle>'
                )
                continue

            t = count / max_count if max_count else 0
            r = 1.6 + 3 * t
            op = 0.4 + 0.6 * t
            color = lerp_color(CREAM, ACCENT, min(t * 2, 1)) if t < 0.5 else lerp_color(ACCENT, ACCENT_2, (t - 0.5) * 2)
            cls = "" if day["date"] in peak_dates else f"twinkle-{'abc'[(wi + day['weekday']) % 3]}"
            extra = ""
            if day["date"] in peak_dates:
                cls = "pulse"
                extra = sparkle(x, y, 5.5, color, "pulse")
            stars.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" '
                f'opacity="{op:.2f}" class="{cls}"><title>{title}</title></circle>{extra}'
            )

    caption = "Sin datos de contribuciones todavía" if not peak else (
        f'Pico: {escape_xml_text(peak["date"])} ({peak["contributionCount"]} en un día)'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {shared_style()}
  {card_chrome(uid, width, height)}
  {title_block(uid, f"{total} contribuciones en el último año", width, chars=len(str(total)) + 30)}
  <text x="{pad_x}" y="48" class="caption">{caption}</text>
  {"".join(stars)}
</svg>'''


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------

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
