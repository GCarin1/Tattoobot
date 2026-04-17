"""Geracao e carregamento do logo do TattooBot.

Prioridade: usa `icons/logo_brand.png` pre-rasterizado do SVG oficial (e
`icons/logo_brand.ico` para o window icon).

Se esses assets nao existirem e `svglib` estiver disponivel, rasteriza o
`icons/logo.svg` na hora. Como ultimo fallback, gera um monograma "TB" via
Pillow. Todas as etapas sao tolerantes a falta de dependencia — nesse caso
a UI mostra so texto.
"""

from __future__ import annotations

from pathlib import Path

from gui import theme


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _draw_brand(size: int = 256, bg: str = None, fg: str = None, accent: str = None):
    """Desenha o logo in-memory e retorna um PIL.Image.

    Estilo: fundo escuro, moldura vermelha dupla, letras "TB" em serif bold
    com faixa vermelha atravessando no baixo (estilo blackwork/bandeira).
    """
    from PIL import Image, ImageDraw, ImageFont

    bg = bg or theme.BLACK_PANEL
    fg = fg or theme.TEXT_PRIMARY
    accent = accent or theme.RED_PRIMARY
    accent_deep = theme.RED_DEEP

    img = Image.new("RGBA", (size, size), _hex_to_rgb(bg) + (255,))
    d = ImageDraw.Draw(img)

    # Moldura externa dupla
    pad = int(size * 0.06)
    d.rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        outline=_hex_to_rgb(accent),
        width=max(2, size // 60),
    )
    inner = int(size * 0.11)
    d.rectangle(
        [inner, inner, size - inner - 1, size - inner - 1],
        outline=_hex_to_rgb(accent_deep),
        width=max(1, size // 90),
    )

    # Letras TB centrais
    font = None
    for name in ("impact.ttf", "seguibl.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, int(size * 0.48))
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    text = "TB"
    try:
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx, ty = (size - tw) // 2 - bbox[0], (size - th) // 2 - bbox[1] - int(size * 0.03)
    except AttributeError:
        tw, th = d.textsize(text, font=font)  # type: ignore[attr-defined]
        tx, ty = (size - tw) // 2, (size - th) // 2

    # Sombra vermelha atras da letra
    d.text((tx + 3, ty + 3), text, font=font, fill=_hex_to_rgb(accent_deep))
    d.text((tx, ty), text, font=font, fill=_hex_to_rgb(fg))

    # Faixa vermelha inferior com "COPILOT"
    band_y = int(size * 0.78)
    band_h = int(size * 0.11)
    d.rectangle(
        [inner + 1, band_y, size - inner - 2, band_y + band_h],
        fill=_hex_to_rgb(accent),
    )
    try:
        sub_font = ImageFont.truetype("arialbd.ttf", int(size * 0.075))
    except (OSError, IOError):
        sub_font = ImageFont.load_default()
    sub = "COPILOT"
    try:
        sb = d.textbbox((0, 0), sub, font=sub_font)
        sw = sb[2] - sb[0]
        d.text(
            ((size - sw) // 2 - sb[0], band_y + band_h // 2 - (sb[3] - sb[1]) // 2 - sb[1]),
            sub,
            font=sub_font,
            fill=_hex_to_rgb(bg),
        )
    except AttributeError:
        pass

    return img


SVG_SOURCE: Path = theme.ICONS_DIR / "logo.svg"


def _rasterize_svg(svg_path: Path, size: int = 512) -> "Image.Image | None":
    """Tenta rasterizar o SVG via svglib+reportlab. Retorna None se falhar.

    O SVG oficial tem fill preto, entao pos-processamos para:
      - Fundo transparente
      - Pixels escuros viram vermelho primario do tema (com alpha proporcional)
    Assim o logo funciona tanto no tema escuro quanto claro.
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        from PIL import Image
    except ImportError:
        return None

    try:
        drawing = svg2rlg(str(svg_path))
        scale = size / drawing.width
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)

        tmp_path = svg_path.parent / "_raw_logo.png"
        renderPM.drawToFile(drawing, str(tmp_path), fmt="PNG", bg=0xFFFFFF)

        src = Image.open(tmp_path).convert("RGBA")
        out = Image.new("RGBA", src.size, (0, 0, 0, 0))

        accent_rgb = _hex_to_rgb(theme.RED_PRIMARY)
        src_pixels = src.load()
        out_pixels = out.load()
        w, h = src.size
        for y in range(h):
            for x in range(w):
                r, g, b, _a = src_pixels[x, y]
                lum = (r + g + b) / 3
                if lum < 200:
                    alpha = int(255 * (1 - lum / 200))
                    out_pixels[x, y] = (accent_rgb[0], accent_rgb[1], accent_rgb[2], alpha)

        try:
            tmp_path.unlink()
        except OSError:
            pass
        return out
    except Exception:  # noqa: BLE001
        return None


def ensure_brand_assets(force: bool = False) -> Path | None:
    """Garante que o PNG/ICO da marca existem. Retorna o path do PNG.

    Ordem de resolucao:
      1. Se os arquivos ja existem (e nao `force`), usa como estao.
      2. Tenta rasterizar `icons/logo.svg` com svglib.
      3. Ultimo recurso: desenha monograma "TB" via Pillow.
    """
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return None

    theme.ICONS_DIR.mkdir(parents=True, exist_ok=True)
    png_path = theme.BRAND_LOGO_PNG
    ico_path = theme.BRAND_LOGO_ICO

    if not force and png_path.exists() and ico_path.exists():
        return png_path

    img = None
    if SVG_SOURCE.exists():
        img = _rasterize_svg(SVG_SOURCE, size=512)

    if img is None:
        try:
            img = _draw_brand(size=256)
        except Exception:  # noqa: BLE001
            return None

    try:
        img.save(png_path, format="PNG")
        img.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        return png_path
    except Exception:  # noqa: BLE001
        return None


def load_brand_ctk_image(size: int = 36):
    """Carrega o logo como CTkImage para uso em labels. Retorna None se falhar."""
    try:
        import customtkinter as ctk
        from PIL import Image
    except ImportError:
        return None

    png_path = ensure_brand_assets()
    if png_path is None or not png_path.exists():
        return None

    try:
        pil_img = Image.open(png_path).convert("RGBA")
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
    except Exception:  # noqa: BLE001
        return None
