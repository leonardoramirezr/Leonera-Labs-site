#!/usr/bin/env python3
"""Genera los logos (logo.svg) y favicons (favicon.svg) de las cuatro opciones.

Las letras se convierten a trazos (paths) para que los SVG se vean igual en
cualquier lugar (GitHub, redes sociales, editores) sin depender de que la
fuente esté instalada.

Uso:
    pip install fonttools uharfbuzz
    python3 tools/generar_logos.py

Las fuentes se descargan de Google Fonts a tools/.fonts/ (ignorado por git).
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(__file__).resolve().parent / ".fonts"

# Clave -> consulta de la API CSS de Google Fonts (una sola variante por clave).
FONTS = {
    "jbm-700": "JetBrains+Mono:wght@700",
    "plexmono-600": "IBM+Plex+Mono:wght@600",
    "plexsans-700": "IBM+Plex+Sans:wght@700",
    "bricolage-800": "Bricolage+Grotesque:opsz,wght@96,800",
    "bricolage-500": "Bricolage+Grotesque:opsz,wght@96,500",
    "fraunces-600": "Fraunces:opsz,wght@144,600",
    "fraunces-600i": "Fraunces:ital,opsz,wght@1,144,600",
    "instrument-600": "Instrument+Sans:wght@600",
}


def font_path(key: str) -> Path:
    path = FONT_DIR / f"{key}.ttf"
    if not path.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        css_url = f"https://fonts.googleapis.com/css2?family={FONTS[key]}"
        # Sin user-agent de navegador, Google Fonts responde con archivos .ttf.
        css = urllib.request.urlopen(css_url).read().decode()
        ttf_url = re.search(r"url\((https://[^)]+\.ttf)\)", css).group(1)
        path.write_bytes(urllib.request.urlopen(ttf_url).read())
    return path


class Font:
    _cache: dict[str, "Font"] = {}

    def __init__(self, key: str):
        path = font_path(key)
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        os2 = self.tt["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", 0) or 0.7 * self.upem
        self.x_height = getattr(os2, "sxHeight", 0) or 0.5 * self.upem

    @classmethod
    def get(cls, key: str) -> "Font":
        if key not in cls._cache:
            cls._cache[key] = Font(key)
        return cls._cache[key]


def text_path(key: str, text: str, size: float, x: float, y: float,
              tracking: float = 0.0) -> tuple[str, float]:
    """Devuelve (d, ancho) del texto con la línea base en (x, y).

    tracking se expresa en em (p. ej. -0.02).
    """
    font = Font.get(key)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font.hb_font, buf, {"kern": True, "liga": True})
    scale = size / font.upem
    pen = SVGPathPen(font.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    cursor = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = font.order[info.codepoint]
        gx = x + (cursor + pos.x_offset) * scale
        gy = y - pos.y_offset * scale
        font.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
        cursor += pos.x_advance + tracking * font.upem
    width = (cursor - tracking * font.upem) * scale
    return pen.getCommands(), width


def svg(width: float, height: float, body: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-label="{title}">\n'
        f"<title>{title}</title>\n{body}\n</svg>\n"
    )


def write(folder: str, name: str, content: str) -> None:
    out = ROOT / folder / name
    out.write_text(content, encoding="utf-8")
    print(f"✓ {out.relative_to(ROOT)}")


# ---------------------------------------------------------------- Opción 1
def opcion_1() -> None:
    bg, text, muted, accent = "#0e0d0b", "#ece6da", "#9a9284", "#ffb547"
    size, pad, h = 64, 44, 150
    base = h / 2 + 22
    char = 0.6 * size  # JetBrains Mono: cada letra mide 600/1000 em
    x = pad
    p_prompt, _ = text_path("jbm-700", ">", size, x, base)
    x += 2 * char
    p_name, w = text_path("jbm-700", "leoneralabs", size, x, base)
    x += w
    p_tld, w = text_path("jbm-700", ".com", size, x, base)
    x += w + 0.12 * size
    cursor = (f'<rect x="{x:.1f}" y="{base - 0.73 * size:.1f}" width="{0.5 * size:.1f}" '
              f'height="{0.9 * size:.1f}" fill="{accent}"/>')
    width = x + 0.5 * size + pad
    body = (
        f'<rect width="{width:.0f}" height="{h}" rx="20" fill="{bg}"/>\n'
        f'<path fill="{accent}" d="{p_prompt}"/>\n'
        f'<path fill="{text}" d="{p_name}"/>\n'
        f'<path fill="{muted}" d="{p_tld}"/>\n{cursor}'
    )
    write("opcion-1-terminal", "logo.svg", svg(width, h, body, "leoneralabs.com"))

    p_fav, w = text_path("jbm-700", ">", 40, 10, 44)
    fav = (
        f'<rect width="64" height="64" rx="14" fill="{bg}"/>\n'
        f'<path fill="{accent}" d="{p_fav}"/>\n'
        f'<rect x="36" y="38" width="18" height="7" rx="1" fill="{text}"/>'
    )
    write("opcion-1-terminal", "favicon.svg", svg(64, 64, fav, "leoneralabs.com"))


# ---------------------------------------------------------------- Opción 2
def opcion_2() -> None:
    paper, ink, accent = "#f3f1ec", "#121212", "#ff4d00"

    def tile(x: float, y: float, s: float) -> str:
        """Ventana de código: barra con tres puntos y «{L}» en el cuerpo."""
        bar = s * 0.22
        size = s * 0.36
        sym, w = text_path("plexmono-600", "{L}", size, 0, 0, -0.04)
        body_mid = y + bar + (s - bar) / 2
        sym, _ = text_path("plexmono-600", "{L}", size, x + (s - w) / 2,
                           body_mid + size * 0.36, -0.04)
        dots = "".join(
            f'<circle cx="{x + s * (0.13 + 0.1 * i):.1f}" cy="{y + bar / 2:.1f}" '
            f'r="{s * 0.035:.1f}" fill="{paper}"/>'
            for i in range(3)
        )
        sw = s * 0.035
        return (
            f'<rect x="{x + sw / 2:.1f}" y="{y + sw / 2:.1f}" width="{s - sw:.1f}" '
            f'height="{s - sw:.1f}" fill="{accent}" stroke="{ink}" stroke-width="{sw:.1f}"/>\n'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{s:.1f}" height="{bar:.1f}" fill="{ink}"/>\n'
            f'{dots}\n<path fill="{ink}" d="{sym}"/>'
        )

    pad, s, h = 40, 104, 184
    size = 54
    base = h / 2 + size * 0.36
    x = pad + s + 30
    p_name, w = text_path("plexmono-600", "leoneralabs", size, x, base, -0.01)
    p_tld, w2 = text_path("plexmono-600", ".com", size, x + w - 0.01 * size, base, -0.01)
    width = x + w + w2 + pad
    body = (
        f'<rect width="{width:.0f}" height="{h}" fill="{paper}"/>\n'
        f'{tile(pad, (h - s) / 2, s)}\n'
        f'<path fill="{ink}" d="{p_name}"/>\n<path fill="{accent}" d="{p_tld}"/>'
    )
    write("opcion-2-laboratorio", "logo.svg", svg(width, h, body, "leoneralabs.com"))
    write("opcion-2-laboratorio", "favicon.svg", svg(64, 64, tile(0, 0, 64), "leoneralabs.com"))


# ---------------------------------------------------------------- Opción 3
def mane(cx: float, cy: float, r: float, gid: str) -> str:
    """Melena geométrica: 12 rayos redondeados alrededor de un círculo."""
    rays = []
    for i in range(12):
        long = i % 2 == 0
        w = r * 0.26
        inner, outer = r * 0.5, r * (1.0 if long else 0.84)
        rays.append(
            f'<rect x="{cx - w / 2:.2f}" y="{cy - outer:.2f}" width="{w:.2f}" '
            f'height="{outer - inner:.2f}" rx="{w / 2:.2f}" '
            f'transform="rotate({i * 30} {cx:.2f} {cy:.2f})"/>'
        )
    return (
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#ffb238"/><stop offset=".5" stop-color="#ff6a3d"/>'
        f'<stop offset="1" stop-color="#e8336d"/></linearGradient></defs>\n'
        f'<g fill="url(#{gid})">{"".join(rays)}'
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.36:.2f}"/></g>'
    )


def opcion_3() -> None:
    text, muted = "#17141f", "#8a8496"
    pad, h, size = 36, 150, 72
    r = 46
    base = h / 2 + size * 0.34
    x = pad + 2 * r + 22
    p_name, w = text_path("bricolage-800", "leoneralabs", size, x, base, -0.03)
    p_tld, w2 = text_path("bricolage-500", ".com", size, x + w + 2, base, -0.02)
    width = x + w + 2 + w2 + pad
    body = (
        f'{mane(pad + r, h / 2, r, "g")}\n'
        f'<path fill="{text}" d="{p_name}"/>\n<path fill="{muted}" d="{p_tld}"/>'
    )
    write("opcion-3-estudio", "logo.svg", svg(width, h, body, "leoneralabs.com"))
    write("opcion-3-estudio", "favicon.svg", svg(64, 64, mane(32, 32, 31, "g"), "leoneralabs.com"))


# ---------------------------------------------------------------- Opción 4
def opcion_4() -> None:
    paper, ink, accent, ochre = "#f5efe4", "#1f1a15", "#b4441f", "#8a6a3b"
    pad, h, size = 44, 170, 84
    base = h / 2 + size * 0.22
    x = pad
    p_a, w = text_path("fraunces-600", "leonera", size, x, base, -0.01)
    x += w + size * 0.03
    p_b, w = text_path("fraunces-600i", "labs", size, x, base, -0.01)
    labs_x, labs_w = x, w
    x += w + size * 0.1
    p_c, w = text_path("instrument-600", ".COM", size * 0.26, x, base, 0.18)
    x += w
    # Trazo curvo bajo «labs», como subrayado hecho a mano.
    sy = base + size * 0.2
    swash = (
        f'<path d="M{labs_x + size * 0.04:.1f} {sy:.1f} '
        f'Q{labs_x + labs_w * 0.55:.1f} {sy + size * 0.11:.1f} '
        f'{labs_x + labs_w + size * 0.02:.1f} {sy - size * 0.03:.1f}" '
        f'fill="none" stroke="{accent}" stroke-width="{size * 0.045:.1f}" stroke-linecap="round"/>'
    )
    width = x + pad
    body = (
        f'<rect width="{width:.0f}" height="{h}" fill="{paper}"/>\n'
        f'<path fill="{ink}" d="{p_a}"/>\n<path fill="{accent}" d="{p_b}"/>\n'
        f'<path fill="{ochre}" d="{p_c}"/>\n{swash}'
    )
    write("opcion-4-editorial", "logo.svg", svg(width, h, body, "leoneralabs.com"))

    p_l, w = text_path("fraunces-600i", "L", 50, 0, 0)
    p_l, _ = text_path("fraunces-600i", "L", 50, (64 - w) / 2 - 1, 48)
    fav = (
        f'<rect width="64" height="64" rx="10" fill="{paper}"/>\n'
        f'<path fill="{accent}" d="{p_l}"/>\n'
        f'<circle cx="48" cy="45" r="4" fill="{ink}"/>'
    )
    write("opcion-4-editorial", "favicon.svg", svg(64, 64, fav, "leoneralabs.com"))


if __name__ == "__main__":
    opcion_1()
    opcion_2()
    opcion_3()
    opcion_4()
