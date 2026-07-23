"""
gen_collaborators.py

Detecta colaboradores reales (contributors) de todos tus repos públicos,
descarga su avatar de GitHub, lo convierte a un .svg circular con el
mismo estilo visual del README (fondo #0d0221, borde #F2A93B), y
actualiza la sección "## ⏾ Con quién colaboré" del README.md.

Requiere la variable de entorno GITHUB_TOKEN (el workflow ya la provee
automáticamente vía secrets.GITHUB_TOKEN) y GITHUB_USERNAME.
"""

import os
import re
import base64
import requests

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "Joako601")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
API_BASE = "https://api.github.com"
ASSETS_DIR = "assets"
README_PATH = "README.md"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
}

# Cuentas a ignorar siempre (bots, la tuya propia, etc.)
IGNORE_LOGINS = {
    GITHUB_USERNAME.lower(),
    "dependabot[bot]",
    "github-actions[bot]",
}


def get_all_repos():
    """Trae todos los repos públicos donde participaste (propios + donde contribuiste)."""
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"{API_BASE}/users/{GITHUB_USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        if r.status_code != 200:
            print(f"[WARN] get_all_repos falló (status {r.status_code}): {r.text[:200]}")
            break
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    print(f"[INFO] Repos encontrados: {[repo['name'] for repo in repos]}")
    return repos


def get_contributors(owner, repo):
    """Trae contributors reales de un repo (excluye forks vacíos y bots)."""
    contributors = []
    page = 1
    while True:
        r = requests.get(
            f"{API_BASE}/repos/{owner}/{repo}/contributors",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "anon": "false"},
        )
        if r.status_code != 200:
            print(f"[WARN] get_contributors({owner}/{repo}) falló (status {r.status_code}): {r.text[:200]}")
            break
        batch = r.json()
        if not batch:
            break
        contributors.extend(batch)
        page += 1
    print(f"[INFO] {owner}/{repo} -> contributors: {[c.get('login') for c in contributors]}")
    return contributors


def collect_collaborators():
    """Recorre todos los repos y arma un set único de colaboradores reales."""
    seen = {}
    for repo in get_all_repos():
        if repo.get("fork"):
            continue
        owner = repo["owner"]["login"]
        name = repo["name"]
        for c in get_contributors(owner, name):
            login = c.get("login", "")
            if not login or login.lower() in IGNORE_LOGINS:
                continue
            # nos quedamos con el que más contribuciones tenga si se repite
            if login not in seen or c.get("contributions", 0) > seen[login].get("contributions", 0):
                seen[login] = c
    print(f"[INFO] Colaboradores únicos detectados: {list(seen.keys())}")
    return list(seen.values())


def make_styled_svg(login, avatar_bytes, size=90):
    """Genera un .svg circular con el avatar embebido en base64, estilo README."""
    b64 = base64.b64encode(avatar_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <defs>
    <clipPath id="clip-{login}">
      <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 4}"/>
    </clipPath>
  </defs>
  <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 1}" fill="#0d0221" stroke="#F2A93B" stroke-width="2.5"/>
  <image href="{data_uri}" xlink:href="{data_uri}" x="4" y="4" width="{size-8}" height="{size-8}" clip-path="url(#clip-{login})"/>
</svg>'''
    return svg


from urllib.parse import quote


def build_table(collaborators):
    cells = []
    for c in collaborators:
        login = c["login"]
        encoded_login = quote(login, safe="")
        badge_url = (
            f"https://img.shields.io/static/v1?"
            f"label=&message={encoded_login}&color=0d0221&style=flat-square"
        )
        cell = f'''<td align="center">
<a href="https://github.com/{login}">
<img src="./{ASSETS_DIR}/avatar-{login.lower()}.svg" width="90"/>
<br/>
<img src="{badge_url}" />
</a>
</td>'''
        cells.append(cell)

    # 4 por fila
    rows = []
    for i in range(0, len(cells), 4):
        rows.append("<tr>\n" + "\n".join(cells[i:i + 4]) + "\n</tr>")

    return '<table align="center">\n' + "\n".join(rows) + "\n</table>"


def update_readme(table_html):
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r'(## ⏾ Con quién colaboré\s*\n\s*)<table align="center">.*?</table>'
    if not re.search(pattern, readme, flags=re.DOTALL):
        print("[WARN] No se encontró la sección '## ⏾ Con quién colaboré' con el formato esperado en README.md")
        return

    readme_new = re.sub(pattern, r"\1" + table_html, readme, flags=re.DOTALL)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme_new)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    collaborators = collect_collaborators()
    print(f"Colaboradores detectados: {[c['login'] for c in collaborators]}")

    if not collaborators:
        print("[WARN] No se detectaron colaboradores. No se actualiza el README.")
        return

    for c in collaborators:
        login = c["login"]
        avatar_url = c.get("avatar_url")
        if not avatar_url:
            print(f"[WARN] {login} no tiene avatar_url, se omite.")
            continue
        try:
            img_resp = requests.get(avatar_url)
            img_resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[WARN] No se pudo descargar el avatar de {login}: {e}")
            continue
        svg = make_styled_svg(login, img_resp.content)
        svg_path = os.path.join(ASSETS_DIR, f"avatar-{login.lower()}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"[INFO] Avatar generado: {svg_path}")

    table_html = build_table(collaborators)
    update_readme(table_html)
    print("README actualizado.")


if __name__ == "__main__":
    main()
