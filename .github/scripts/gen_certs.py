import json
import re

PER_ROW = 4  # coincide con width="25%" por celda; si cambia, ajustar ambos

with open("badges.json", "r", encoding="utf-8") as f:
    data = json.load(f)

badges = data.get("data", [])

cells = []
for badge in badges:
    name = badge.get("badge_template", {}).get("name", "Certificación")
    image_url = badge.get("badge_template", {}).get("image_url", "")
    badge_id = badge.get("id", "")
    link = f"https://www.credly.com/badges/{badge_id}/linked_in_profile"

    cell = f'''<td align="center" width="25%">
<a href="{link}">
<img src="{image_url}" width="160" alt="{name}"/>
</a>
</td>'''
    cells.append(cell)

# Filas de PER_ROW celdas: con todo en una sola <tr>, width="25%" x N celdas
# suma más de 100% apenas hay más de 4 badges y la fila termina desbordando
# (scroll horizontal en vez de bajar de línea). Partir en filas de a 4 evita eso.
rows = []
for i in range(0, len(cells), PER_ROW):
    chunk = cells[i:i + PER_ROW]
    rows.append("<tr>\n" + "\n".join(chunk) + "\n</tr>")

table = "<table align=\"center\">\n" + "\n".join(rows) + "\n</table>"

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

pattern = r'(## ✓ Certificaciones\s*\n\s*)<table align="center">.*?</table>'
readme_new = re.sub(pattern, r'\1' + table, readme, flags=re.DOTALL)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_new)
