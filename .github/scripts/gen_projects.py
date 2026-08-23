"""
gen_projects.py

Genera una tarjeta SVG por proyecto para "## Proyectos Destacados", con el
mismo sistema visual que assets/stats-card.svg (ver svg_theme.py).

A diferencia de gen_dev_stats.py, esto NO se ejecuta solo por un workflow:
el contenido (nombre, descripción, tags, link) es curado a mano acá abajo,
no viene de la API de GitHub, así que no hay nada que "desactualizarse"
todos los días. Cuando agregues/edites un proyecto, editá PROJECTS y
corré:

    python .github/scripts/gen_projects.py

Por eso las tarjetas NO llevan el ícono de "se actualiza sola" (sync_icon):
sería mentir sobre el origen de los datos.
"""

import os
import re
import textwrap

from svg_theme import (
    ACCENT, ACCENT_2, CREAM, LAVENDER_DIM,
    escape_xml_text, shared_style, card_chrome, title_block,
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


def build_chip_row(tags, x0, y, width, gap=8, colors=(ACCENT, ACCENT_2)):
    """Fila de chips (pastillas con borde) que envuelve a la siguiente línea
    si no entran en el ancho disponible. Devuelve (svg, altura_usada)."""
    pad_x = 10
    height = 22
    x, row_y = x0, y
    chips = []
    for i, tag in enumerate(tags):
        w = len(tag) * 6.6 + pad_x * 2
        if x + w > width - 24 and x > x0:
            x = x0
            row_y += height + 8
        color = colors[i % len(colors)]
        chips.append(
            f'<rect x="{x:.1f}" y="{row_y}" width="{w:.1f}" height="{height}" rx="{height / 2}" '
            f'fill="{color}" fill-opacity="0.10" stroke="{color}" stroke-opacity="0.55"/>'
            f'<text x="{x + w / 2:.1f}" y="{row_y + height / 2 + 4:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{color}">{escape_xml_text(tag)}</text>'
        )
        x += w + gap
    used_height = (row_y - y) + height
    return "".join(chips), used_height


def build_project_card_svg(project, uid, width=640):
    desc_lines = textwrap.wrap(project["tagline"], width=74)[:3]

    title_pad = 62
    desc_line_h = 20
    desc_h = len(desc_lines) * desc_line_h
    chips_y = title_pad + desc_h + 14
    chip_row_svg, chips_h = build_chip_row(project["tags"], 24, chips_y, width)
    footer_h = 34
    height = chips_y + chips_h + footer_h

    desc_svg = "".join(
        f'<text x="24" y="{title_pad + i * desc_line_h}" class="label">{escape_xml_text(line)}</text>'
        for i, line in enumerate(desc_lines)
    )

    footer_y = height - 16
    footer = (
        f'<text x="{width - 24}" y="{footer_y}" text-anchor="end" font-size="12" '
        f'fill="{ACCENT}" class="reveal" style="animation-delay:.4s">Ver repositorio &#8594;</text>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {shared_style()}
  {card_chrome(uid, width, height)}
  {title_block(uid, project["name"], width, with_sync=False)}
  <g class="reveal" style="animation-delay:.15s">{desc_svg}</g>
  <g class="reveal" style="animation-delay:.3s">{chip_row_svg}</g>
  {footer}
</svg>'''


def update_readme_section():
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # width fijo (no "100%"): así no se estira/desenfoca en pantallas anchas —
    # GitHub igual la achica en mobile porque su CSS aplica max-width:100% a
    # las imágenes del README.
    cards = "\n\n".join(
        f'<a href="{p["url"]}">\n'
        f'  <img src="./{ASSETS_DIR}/project-{p["slug"]}.svg" width="640" alt="{escape_xml_text(p["name"])}"/>\n'
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
