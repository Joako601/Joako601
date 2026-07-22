import json
import re

with open("badges.json", "r") as f:
    data = json.load(f)

badges = data.get("data", [])

rows = []
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
    rows.append(cell)

table = "<table align=\"center\">\n<tr>\n" + "\n".join(rows) + "\n</tr>\n</table>"

with open("README.md", "r") as f:
    readme = f.read()

pattern = r'(## ✓ Certificaciones\s*\n\s*)<table align="center">.*?</table>'
readme_new = re.sub(pattern, r'\1' + table, readme, flags=re.DOTALL)

with open("README.md", "w") as f:
    f.write(readme_new)
