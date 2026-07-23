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


def escape_xml_text(text):
    """Escapa caracteres reservados de XML para usar el login como texto SVG."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def make_avatar_group(login, avatar_bytes, x, size=90, uid=""):
    """
    Genera un <g> (grupo SVG) con: avatar circular + borde spinner animado +
    nombre con color oscilante. Pensado para insertarse dentro de un SVG más
    grande (el marquee), por eso usa <g transform="translate(x,0)"> en vez
    de ser un <svg> independiente. `uid` evita colisiones de id cuando el
    mismo colaborador aparece duplicado (para el loop infinito del marquee).
    """
    b64 = base64.b64encode(avatar_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"
    cx = cy = size / 2
    r_avatar = size / 2 - 4
    r_spinner = size / 2 - 1
    text_y = size + 20
    safe_login = escape_xml_text(login)
    clip_id = f"clip-{login}-{uid}"

    return f'''<g transform="translate({x},0)">
    <defs>
      <clipPath id="{clip_id}">
        <circle cx="{cx}" cy="{cy}" r="{r_avatar - 3}"/>
      </clipPath>
    </defs>
    <circle cx="{cx}" cy="{cy}" r="{r_avatar}" fill="#0d0221"/>
    <image href="{data_uri}" xlink:href="{data_uri}" x="4" y="4" width="{size - 8}" height="{size - 8}" clip-path="url(#{clip_id})"/>
    <circle cx="{cx}" cy="{cy}" r="{r_spinner}" fill="none" stroke="#F2A93B"
            stroke-width="2.5" stroke-linecap="round"
            stroke-dasharray="{r_spinner * 2.5} {r_spinner * 3.8}">
      <animateTransform attributeName="transform" type="rotate"
                         from="0 {cx} {cy}" to="360 {cx} {cy}"
                         dur="3s" repeatCount="indefinite"/>
    </circle>
    <text x="{cx}" y="{text_y}" text-anchor="middle" font-family="monospace"
          font-size="11" font-weight="bold" fill="#F2A93B">{safe_login}
      <animate attributeName="fill" values="#F2A93B;#B084F2;#F2A93B"
               dur="3s" repeatCount="indefinite"/>
    </text>
  </g>'''


def build_marquee_svg(collaborators, avatar_bytes_map, size=90, gap=40,
                      speed_px_per_sec=45, viewport_width=700):
    """
    Arma un SVG único con todos los colaboradores en fila, duplicados una
    vez para que el desplazamiento sea un loop perfecto (sin salto visible),
    y los anima deslizándose de derecha a izquierda sin parar.
    """
    step = size + gap
    seq_width = len(collaborators) * step
    height = size + 32

    groups = []
    for i, c in enumerate(collaborators):
        login = c["login"]
        groups.append(make_avatar_group(login, avatar_bytes_map[login], i * step, size=size, uid="a"))
    for i, c in enumerate(collaborators):
        login = c["login"]
        groups.append(make_avatar_group(login, avatar_bytes_map[login], seq_width + i * step, size=size, uid="b"))

    duration = max(seq_width / speed_px_per_sec, 4)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{viewport_width}" height="{height}" viewBox="0 0 {viewport_width} {height}">
  <clipPath id="marquee-viewport">
    <rect x="0" y="0" width="{viewport_width}" height="{height}"/>
  </clipPath>
  <g clip-path="url(#marquee-viewport)">
    <g>
      {"".join(groups)}
      <animateTransform attributeName="transform" type="translate"
                         from="0 0" to="{-seq_width} 0"
                         dur="{duration}s" repeatCount="indefinite" calcMode="linear"/>
    </g>
  </g>
</svg>'''


def build_marquee_block():
    return (
        '<div align="center">\n'
        f'<img src="./{ASSETS_DIR}/collaborators-marquee.svg" alt="Colaboradores" width="100%"/>\n'
        "</div>"
    )


def update_readme(block_html):
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # Matchea todo lo que haya entre el header de la sección y el próximo
    # separador "---", sea la tabla vieja de avatares sueltos o el div del
    # marquee ya generado en una corrida anterior.
    pattern = r'(## ⏾ Con quién colaboré\s*\n\s*).*?(\n\s*---)'
    if not re.search(pattern, readme, flags=re.DOTALL):
        print("[WARN] No se encontró la sección '## ⏾ Con quién colaboré' en README.md")
        return

    readme_new = re.sub(pattern, r"\1" + block_html + r"\2", readme, flags=re.DOTALL)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme_new)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    collaborators = collect_collaborators()
    print(f"Colaboradores detectados: {[c['login'] for c in collaborators]}")

    if not collaborators:
        print("[WARN] No se detectaron colaboradores. No se actualiza el README.")
        return

    avatar_bytes_map = {}
    valid_collaborators = []
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
        avatar_bytes_map[login] = img_resp.content
        valid_collaborators.append(c)
        print(f"[INFO] Avatar descargado: {login}")

    if not valid_collaborators:
        print("[WARN] Ningún avatar se pudo descargar. No se actualiza el README.")
        return

    marquee_svg = build_marquee_svg(valid_collaborators, avatar_bytes_map)
    marquee_path = os.path.join(ASSETS_DIR, "collaborators-marquee.svg")
    with open(marquee_path, "w", encoding="utf-8") as f:
        f.write(marquee_svg)
    print(f"[INFO] Marquee generado: {marquee_path}")

    block_html = build_marquee_block()
    update_readme(block_html)
    print("README actualizado.")


if __name__ == "__main__":
    main()
