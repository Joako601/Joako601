# Cómo contribuir

Este es el repositorio de mi perfil de GitHub, así que el contenido personal lo mantengo yo. Las correcciones de errores, links rotos o mejoras a los workflows son bienvenidas.

## Flujo de trabajo

1. Crea una rama desde `main`.
2. Haz tus cambios y pruébalos.
3. Abre un Pull Request hacia `main`. Se integra con squash merge.

## Commits

Los mensajes siguen [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/) y se escriben en español.

| Tipo | Uso |
| --- | --- |
| `feat` | Una sección o un workflow nuevo |
| `fix` | Una corrección |
| `style` | Cambios visuales, sin cambiar el contenido |
| `docs` | Documentación |
| `refactor` | Cambios internos en los scripts |
| `chore` | Mantenimiento y commits automáticos |

Ejemplo: `fix: corregir desborde en la tabla de certificaciones`.

## Correr los scripts

Se ejecutan desde la raíz del repositorio y requieren Python 3.11 o superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r .github/scripts/requirements.txt

export GITHUB_TOKEN="$(gh auth token)"
export GITHUB_USERNAME=Joako601

python .github/scripts/gen_dev_stats.py
python .github/scripts/gen_collaborators.py
```

Estos scripts modifican el README y los archivos de `assets/`. Revisa `git diff` antes de hacer commit.

El detalle de cada workflow está en [docs/AUTOMATIZACION.md](docs/AUTOMATIZACION.md).
