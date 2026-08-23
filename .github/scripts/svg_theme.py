"""
svg_theme.py

Sistema visual compartido por todos los SVG generados del perfil (stats,
proyectos, y lo que se agregue después): el mismo "cielo nocturno" de
banner-top.svg / collaborators-marquee.svg — fondo #0d0221 -> #1a0a3d,
acentos #F2A93B / #B084F2 / #FCEFCB, tipografía 'Fira Code', estrellas
titilantes, destellos de 4 puntas, spinner de "actualización automática".

Cualquier script nuevo que genere una tarjeta debería importar de acá en
vez de reinventar los mismos degradés/estilos.
"""

# ---- Paleta del perfil ----
BG_1 = "#0d0221"       # vacío
BG_2 = "#1a0a3d"       # índigo
ACCENT = "#F2A93B"     # oro
ACCENT_2 = "#B084F2"   # violeta
CREAM = "#FCEFCB"      # texto principal
MUTED_GOLD = "#E8C978"
LAVENDER_DIM = "#6b6094"   # neutral con sesgo violeta, para texto secundario / estrellas apagadas
FONT_STACK = "'Fira Code', ui-monospace, Menlo, Consolas, monospace"


def escape_xml_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def lerp_color(c1, c2, t):
    """Interpola linealmente entre dos colores hex (#rrggbb), t en [0,1]."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def shared_style():
    """<style> común: tipografía, glow, titileo, spinner, aparición y tipeo."""
    return f'''<style>
    text {{ font-family: {FONT_STACK}; }}
    .title {{ font-size: 16px; font-weight: 700; fill: {CREAM};
              filter: drop-shadow(0 0 4px rgba(242,169,59,0.45)); }}
    .caption {{ font-size: 11px; fill: {LAVENDER_DIM}; }}
    .label {{ font-size: 13px; fill: #d8cdf0; }}
    .value {{ font-size: 13px; font-weight: 700; fill: {ACCENT};
              filter: drop-shadow(0 0 3px rgba(242,169,59,0.35)); }}

    .twinkle-a {{ animation: twinkle 2.5s ease-in-out infinite; }}
    .twinkle-b {{ animation: twinkle 3.2s ease-in-out infinite; }}
    .twinkle-c {{ animation: twinkle 4s ease-in-out infinite; }}
    @keyframes twinkle {{ 0%, 100% {{ opacity: .28; }} 50% {{ opacity: 1; }} }}

    .pulse {{ animation: pulse 2.4s ease-in-out infinite; transform-box: fill-box;
              transform-origin: center; }}
    @keyframes pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.18); }} }}

    .spin {{ animation: rot 3.2s linear infinite; transform-box: fill-box;
             transform-origin: center; }}
    @keyframes rot {{ to {{ transform: rotate(360deg); }} }}

    .reveal {{ opacity: 0; animation: fadeUp .6s ease-out forwards; }}
    @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(6px); }}
                          to {{ opacity: 1; transform: translateY(0); }} }}

    @media (prefers-reduced-motion: reduce) {{
      .twinkle-a, .twinkle-b, .twinkle-c, .pulse, .spin {{ animation: none; }}
      .reveal {{ opacity: 1; animation: none; }}
      .type-wrap {{ animation: none !important; clip-path: none !important; }}
    }}
  </style>'''


def bg_stars(uid, width, height, seed=17, count=9):
    """Estrellitas de fondo dispersas, deterministas (sin random real para no
    depender de una seed compartida entre corridas)."""
    stars = []
    x, y = seed, seed * 7 % 97
    for i in range(count):
        x = (x * 53 + 13) % width
        y = (y * 71 + 29) % max(height - 20, 1)
        r = 1 + (i % 3) * 0.3
        cls = f"twinkle-{'abc'[i % 3]}"
        fill = CREAM if i % 4 == 0 else ACCENT
        stars.append(f'<circle cx="{x}" cy="{max(y, 10)}" r="{r:.1f}" fill="{fill}" '
                      f'opacity="0.35" class="{cls}"/>')
    return f'<g id="{uid}-bgstars">{"".join(stars)}</g>'


def sparkle(cx, cy, s=4, fill=ACCENT, cls=""):
    """Destello de 4 puntas (mismo path que las estrellas brillantes del banner)."""
    return (
        f'<g class="{cls}">'
        f'<path d="M{cx} {cy - s} L{cx + s * 0.3:.1f} {cy} L{cx} {cy + s} L{cx - s * 0.3:.1f} {cy} Z" fill="{fill}"/>'
        f'<path d="M{cx - s} {cy} L{cx} {cy + s * 0.3:.1f} L{cx + s} {cy} L{cx} {cy - s * 0.3:.1f} Z" fill="{fill}"/>'
        f'</g>'
    )


def sync_icon(x, y):
    """Anillo giratorio: usar SOLO en tarjetas que de verdad se actualizan solas
    (stats, certs, colaboradores) — no en contenido curado a mano."""
    return (
        f'<g transform="translate({x},{y})">'
        f'<title>Se actualiza automáticamente todos los días</title>'
        f'<circle r="7" fill="none" stroke="{ACCENT_2}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-dasharray="16 26" class="spin"/>'
        f'<circle r="1.6" fill="{ACCENT_2}"/>'
        f'</g>'
    )


def card_chrome(uid, width, height, glow=("12%", "10%"), glow_color=ACCENT):
    """Fondo cielo nocturno + halo de luz + borde. `glow` es el (cx, cy) del
    halo — por defecto un rincón superior-izquierdo (tarjetas de datos);
    pasale ("50%", "0%") para un halo tipo reflector centrado arriba
    (tarjetas "destacado/spotlight", ej. proyectos)."""
    gx, gy = glow
    return f'''<defs>
    <linearGradient id="{uid}-sky" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{BG_1}"/>
      <stop offset="100%" stop-color="{BG_2}"/>
    </linearGradient>
    <radialGradient id="{uid}-glow" cx="{gx}" cy="{gy}" r="55%">
      <stop offset="0%" stop-color="{glow_color}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{glow_color}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="{uid}-clip"><rect width="{width}" height="{height}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#{uid}-clip)">
    <rect width="{width}" height="{height}" fill="url(#{uid}-sky)"/>
    <rect width="{width}" height="{height}" fill="url(#{uid}-glow)"/>
    {bg_stars(uid, width, height)}
  </g>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14"
        fill="none" stroke="{ACCENT}" stroke-opacity="0.35"/>'''


def title_block(uid, text, width, y=34, size=16, chars=None, with_sync=True):
    """Título con efecto de tipeo (una sola vez) + glow. `with_sync` agrega el
    ícono de auto-actualización — apagalo si el contenido es curado a mano."""
    n = chars or len(text)
    icon = sync_icon(width - 30, y - 10) if with_sync else ""
    return f'''<g class="type-wrap" style="overflow:hidden;animation:type-{uid} 1s steps({n},end) 1 forwards">
    <text x="24" y="{y}" class="title">{escape_xml_text(text)}</text>
  </g>
  <style>@keyframes type-{uid} {{ from {{ clip-path: inset(0 100% 0 0); }} to {{ clip-path: inset(0 0 0 0); }} }}</style>
  {icon}'''
