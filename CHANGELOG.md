# Changelog

Los cambios relevantes de este repositorio se documentan en este archivo. Los commits automáticos de los bots no se incluyen.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

- **MAJOR:** rediseño completo del perfil.
- **MINOR:** una sección o un workflow nuevo.
- **PATCH:** correcciones.

## [1.0.0] - 2026-11-10

Primera versión etiquetada. Reúne el trabajo hecho hasta esta fecha.

### Agregado

- README de perfil con banners para tema claro y oscuro, stack por categorías y navegación rápida.
- Tarjetas de proyectos destacados.
- Tabla de certificaciones generada desde Credly.
- Carrusel de colaboradores generado automáticamente.
- Tarjetas propias de estadísticas, lenguajes y actividad, sin depender de servicios externos.
- Workflows para actualizar estadísticas, certificaciones, colaboradores y fecha, y para revisar links.
- Documentación del repositorio, plantillas de issues y PR, y Dependabot.

### Cambiado

- Los mensajes de los commits automáticos siguen Conventional Commits.
- `actions/checkout` y `actions/setup-python` pasan a v7.
- La revisión de links usa `tcort/github-action-markdown-link-check`.
- La versión de `requests` queda fijada en `requirements.txt`.

### Corregido

- La tabla de certificaciones ya no se desborda.
- Las estadísticas ya no se publican en cero si falla la API de GitHub.
- La tabla de certificaciones ya no se vacía si Credly no devuelve badges.
- La fecha del README se actualiza con los commits diarios de estadísticas.

### Eliminado

- Contador de visitas del README.
