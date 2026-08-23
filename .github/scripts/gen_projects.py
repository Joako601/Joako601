"""
gen_projects.py

Genera una tarjeta SVG "spotlight" por proyecto para "## Proyectos
Destacados". Usa la misma paleta que assets/stats-card.svg (ver
svg_theme.py) pero un layout propio y distinto — centrado, más vertical,
con un halo tipo reflector arriba en vez del rincón de las tarjetas de
datos — para que no se lea como un clon de las stats.

A diferencia de gen_dev_stats.py, esto NO corre solo por un workflow: el
contenido (nombre, descripción, tags, link) es curado a mano acá abajo, no
viene de la API de GitHub. Cuando agregues/edites un proyecto, editá
PROJECTS y corré:

    python .github/scripts/gen_projects.py

Por eso las tarjetas NO llevan el ícono de "se actualiza sola" (sync_icon):
sería mentir sobre el origen de los datos.
"""

import os
import re
import textwrap

from svg_theme import (
    ACCENT, ACCENT_2, CREAM,
    escape_xml_text, shared_style, card_chrome,
)

ASSETS_DIR = "assets"
README_PATH = "README.md"

PROJECTS = [
    {
        "name": "market-backend",
        "slug": "market-backend",
        "tagline": (
            "API REST en Java + Spring Boot con arquitectura limpia por capas, "
            "relaciones JPA y mapeo vía MapStruct."
        ),
        "tags": ["Java", "Spring Boot", "JPA", "MapStruct", "REST"],
        "url": "https://github.com/Joako601/market-backend",
    },
    {
        "name": "Proyecto Jo'",
        "slug": "proyecto-jo",
        "tagline": (
            "Gestión financiera para negocios en ASP.NET Core (.NET 10), "
            "arquitectura hexagonal, tiempo real con SignalR y 26 tests con xUnit."
        ),
        "tags": ["ASP.NET Core", ".NET 10", "SignalR", "Swagger", "xUnit"],
        "url": "https://github.com/Joako601/Proyecto-Jo",
    },
]


def _text_w(text, font_size):
    """Ancho aproximado de texto monoespaciado (Fira Code ~0.6em por char)."""
    return len(text) * font_size * 0.6


def sparkle(cx, cy, s=4, fill=ACCENT):
    return (
        f'<path d="M{cx} {cy - s} L{cx + s * 0.3:.1f} {cy} L{cx} {cy + s} L{cx - s * 0.3:.1f} {cy} Z" fill="{fill}"/>'
        f'<path d="M{cx - s} {cy} L{cx} {cy + s * 0.3:.1f} L{cx + s} {cy} L{cx} {cy - s * 0.3:.1f} Z" fill="{fill}"/>'
    )


def build_centered_title(text, width, y=42, size=20):
    """Título centrado, flanqueado por destellos, con tipeo una sola vez."""
    n = len(text)
    text_w = _text_w(text, size)
    gap = 16
    left_x = width / 2 - text_w / 2 - gap
    right_x = width / 2 + text_w / 2 + gap
    star_y = y - size * 0.32
    uid_anim = re.sub(r"[^a-z0-9]", "", text.lower())[:12] or "t"
    return f'''<g class="type-wrap" style="overflow:hidden;animation:type-{uid_anim} 1s steps({n},end) 1 forwards">
    <text x="{width / 2}" y="{y}" text-anchor="middle" class="title" style="font-size:{size}px">{escape_xml_text(text)}</text>
  </g>
  <style>@keyframes type-{uid_anim} {{ from {{ clip-path: inset(0 100% 0 0); }} to {{ clip-path: inset(0 0 0 0); }} }}</style>
  <g class="twinkle-b">{sparkle(left_x, star_y, 4.5)}</g>
  <g class="twinkle-c">{sparkle(right_x, star_y, 4.5)}</g>'''


def build_centered_chip_rows(tags, y, width, gap=8, colors=(ACCENT, ACCENT_2)):
    """Chips centrados, envolviendo a una nueva línea si no entran."""
    pad_x, height = 10, 22
    max_w = width - 64
    widths = [len(t) * 6.6 + pad_x * 2 for t in tags]

    rows, cur, cur_w = [], [], 0
    for tag, w in zip(tags, widths):
        add = w if not cur else w + gap
        if cur and cur_w + add > max_w:
            rows.append(cur)
            cur, cur_w, add = [], 0, w
        cur.append((tag, w))
        cur_w += add
    if cur:
        rows.append(cur)

    svg_parts, row_y, idx = [], y, 0
    for row in rows:
        total_w = sum(w for _, w in row) + gap * (len(row) - 1)
        x = (width - total_w) / 2
        for tag, w in row:
            color = colors[idx % len(colors)]
            svg_parts.append(
                f'<rect x="{x:.1f}" y="{row_y}" width="{w:.1f}" height="{height}" rx="{height / 2}" '
                f'fill="{color}" fill-opacity="0.10" stroke="{color}" stroke-opacity="0.55"/>'
                f'<text x="{x + w / 2:.1f}" y="{row_y + height / 2 + 4:.1f}" text-anchor="middle" '
                f'font-size="11" fill="{color}">{escape_xml_text(tag)}</text>'
            )
            x += w + gap
            idx += 1
        row_y += height + 8

    used_height = (row_y - y - 8) if rows else 0
    return "".join(svg_parts), used_height


def build_project_card_svg(project, uid, width=520):
    desc_lines = textwrap.wrap(project["tagline"], width=58)[:3]
    y = 0

    title_y = 42
    divider_y = title_y + 18
    y = divider_y + 26

    desc_line_h = 19
    desc_svg = "".join(
        f'<text x="{width / 2}" y="{y + i * desc_line_h}" text-anchor="middle" class="label">'
        f'{escape_xml_text(line)}</text>'
        for i, line in enumerate(desc_lines)
    )
    y += len(desc_lines) * desc_line_h + 18

    chips_svg, chips_h = build_centered_chip_rows(project["tags"], y, width)
    y += chips_h + 30

    btn_label = "Ver repositorio →"
    btn_w = _text_w(btn_label, 12) + 32
    btn_x = (width - btn_w) / 2
    btn = (
        f'<g class="reveal" style="animation-delay:.5s">'
        f'<rect x="{btn_x:.1f}" y="{y - 17}" width="{btn_w:.1f}" height="28" rx="14" '
        f'fill="none" stroke="{ACCENT}" stroke-opacity="0.6"/>'
        f'<text x="{width / 2}" y="{y}" text-anchor="middle" font-size="12" fill="{ACCENT}">'
        f'{btn_label}</text></g>'
    )
    y += 14 + 24  # cierre del botón + padding inferior
    height = y

    divider = (
        f'<line x1="{width / 2 - 35}" y1="{divider_y}" x2="{width / 2 + 35}" y2="{divider_y}" '
        f'stroke="{ACCENT}" stroke-opacity="0.4"/>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {shared_style()}
  {card_chrome(uid, width, height, glow=("50%", "0%"))}
  {build_centered_title(project["name"], width, y=title_y)}
  {divider}
  <g class="reveal" style="animation-delay:.2s">{desc_svg}</g>
  <g class="reveal" style="animation-delay:.35s">{chips_svg}</g>
  {btn}
</svg>'''


def update_readme_section():
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # Apiladas una debajo de otra (no lado a lado): con solo 48%/48% se
    # confundía con el layout de stats-card + top-langs. width fijo (no
    # "100%") para que no se estire en pantallas anchas — GitHub igual la
    # achica en mobile porque su CSS aplica max-width:100% a las imágenes.
    cards = "\n\n".join(
        f'<a href="{p["url"]}">\n'
        f'  <img src="./{ASSETS_DIR}/project-{p["slug"]}.svg" width="520" alt="{escape_xml_text(p["name"])}"/>\n'
        f'</a>'
        for p in PROJECTS
    )
    block = f'<div align="center">\n\n{cards}\n\n</div>'

    pattern = r'(## ☕︎ Proyectos Destacados\s*\n\s*).*?(\n\s*---)'
    if not re.search(pattern, readme, flags=re.DOTALL):
        print("[WARN] No se encontró la sección '## ☕︎ Proyectos Destacados' en README.md")
        return

    readme_new = re.sub(pattern, r"\1" + block + r"\2", readme, flags=re.DOTALL)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme_new)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    for project in PROJECTS:
        uid = f"proj-{project['slug']}"
        svg = build_project_card_svg(project, uid)
        path = os.path.join(ASSETS_DIR, f"project-{project['slug']}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"[INFO] Generado {path}")

    update_readme_section()
    print("README y tarjetas de proyectos actualizados.")


if __name__ == "__main__":
    main()
