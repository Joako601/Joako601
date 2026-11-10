# Automatización del perfil

Varias secciones del README se generan con GitHub Actions. Los horarios están en UTC y GitHub puede ejecutarlos con varias horas de retraso.

## Workflows

| Workflow | Cuándo corre | Qué hace | Archivos que cambia |
| --- | --- | --- | --- |
| `update-dev-stats.yml` | Todos los días, 07:00, o manual | Genera las tarjetas de estadísticas, lenguajes y actividad, y actualiza la fecha | `README.md`, `assets/stats-card.svg`, `assets/top-langs.svg`, `assets/activity-graph.svg` |
| `update-collaborators.yml` | Lunes, 06:00, o manual | Genera el carrusel con quienes contribuyeron a mis repositorios | `README.md`, `assets/collaborators-marquee.svg` |
| `update-certs.yml` | Lunes, 08:00, o manual | Reconstruye la tabla de certificaciones desde Credly | `README.md` |
| `check-links.yml` | Lunes, 09:00, y con cada push a `main` | Revisa los links de los archivos Markdown | Ninguno |
| `update-date.yml` | Con cada push a `main` que no toque solo workflows | Actualiza la fecha del README | `README.md` |

Los commits hechos con `GITHUB_TOKEN` no disparan otros workflows. Por eso `update-dev-stats.yml` actualiza la fecha por su cuenta.

## Scripts

Están en `.github/scripts/`.

| Script | Uso |
| --- | --- |
| `gen_dev_stats.py` | Tarjetas de estadísticas. Usa `PAT_STATS` si existe y, si no, `GITHUB_TOKEN` |
| `gen_collaborators.py` | Carrusel de colaboradores |
| `gen_certs.py` | Tabla de certificaciones, a partir de `badges.json` |
| `gen_projects.py` | Tarjetas de proyectos. Se corre a mano después de editar la lista `PROJECTS` |
| `svg_theme.py` | Paleta y utilidades compartidas para los SVG |
| `update_date.sh` | Escribe la fecha actual en el README |

## Cuando algo falla

Los scripts terminan en error antes de escribir archivos si no pueden obtener datos válidos. Una corrida en rojo deja publicada la versión anterior, y se puede relanzar desde la pestaña **Actions**.

## Mensajes de commit

| Workflow | Mensaje |
| --- | --- |
| `update-dev-stats.yml` | `chore(stats): actualizar estadísticas de desarrollo` |
| `update-collaborators.yml` | `chore(collaborators): actualizar colaboradores` |
| `update-certs.yml` | `chore(certs): actualizar certificaciones desde Credly` |
| `update-date.yml` | `chore(date): actualizar fecha` |
