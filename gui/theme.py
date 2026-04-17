"""Tema visual do TattooBot - presets de cores com suporte a troca via settings.

O tema eh definido como um conjunto de constantes no modulo. Para permitir
trocar de tema sem precisar reescrever os importadores (`from gui import theme`
e acesso direto como `theme.BLACK_SOFT`), o dict ativo eh aplicado como
atributos do modulo via `apply_theme_preset()` no boot da GUI.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ─── Presets de tema ──────────────────────────────────────────────────────

THEME_PRESETS: dict[str, dict[str, str]] = {
    "blackwork": {
        "label": "Blackwork (padrao)",
        "description": "Preto profundo com sangue vermelho. Classico de estudio.",
        "BLACK_PURE": "#000000",
        "BLACK_SOFT": "#0a0a0a",
        "BLACK_PANEL": "#141414",
        "BLACK_CARD": "#1a1a1a",
        "BLACK_HOVER": "#242424",
        "BLACK_BORDER": "#2a2a2a",
        "RED_PRIMARY": "#B00020",
        "RED_HOVER": "#D32F2F",
        "RED_DEEP": "#7a0016",
        "RED_BLOOD": "#8B0000",
        "RED_GLOW": "#FF1744",
        "TEXT_PRIMARY": "#EDEDED",
        "TEXT_SECONDARY": "#A8A8A8",
        "TEXT_MUTED": "#707070",
    },
    "oxblood": {
        "label": "Oxblood",
        "description": "Preto com bordô queimado. Mais maduro, menos neon.",
        "BLACK_PURE": "#000000",
        "BLACK_SOFT": "#0b0707",
        "BLACK_PANEL": "#150f0f",
        "BLACK_CARD": "#1d1515",
        "BLACK_HOVER": "#2a1d1d",
        "BLACK_BORDER": "#3a2626",
        "RED_PRIMARY": "#7d1a1a",
        "RED_HOVER": "#a02424",
        "RED_DEEP": "#4f0f0f",
        "RED_BLOOD": "#5c1414",
        "RED_GLOW": "#c2402f",
        "TEXT_PRIMARY": "#ecdfdf",
        "TEXT_SECONDARY": "#a89999",
        "TEXT_MUTED": "#766666",
    },
    "ink_blue": {
        "label": "Ink Blue",
        "description": "Tinta azul nanquim. Frio e cirurgico.",
        "BLACK_PURE": "#000000",
        "BLACK_SOFT": "#060a12",
        "BLACK_PANEL": "#0d1522",
        "BLACK_CARD": "#121c2e",
        "BLACK_HOVER": "#1b2840",
        "BLACK_BORDER": "#233253",
        "RED_PRIMARY": "#2563eb",
        "RED_HOVER": "#3b82f6",
        "RED_DEEP": "#1e40af",
        "RED_BLOOD": "#1e3a8a",
        "RED_GLOW": "#60a5fa",
        "TEXT_PRIMARY": "#e6eefc",
        "TEXT_SECONDARY": "#a7b6cf",
        "TEXT_MUTED": "#6c7a97",
    },
    "bone_white": {
        "label": "Bone White (claro)",
        "description": "Fundo osso, linhas pretas. Inverte o esquema.",
        "BLACK_PURE": "#ffffff",
        "BLACK_SOFT": "#f3f0ea",
        "BLACK_PANEL": "#e9e4d9",
        "BLACK_CARD": "#ffffff",
        "BLACK_HOVER": "#ddd6c6",
        "BLACK_BORDER": "#c9c0ad",
        "RED_PRIMARY": "#8b0000",
        "RED_HOVER": "#a52a2a",
        "RED_DEEP": "#5c0000",
        "RED_BLOOD": "#5c0000",
        "RED_GLOW": "#b91c1c",
        "TEXT_PRIMARY": "#1a1612",
        "TEXT_SECONDARY": "#4a433b",
        "TEXT_MUTED": "#7a7167",
    },
    "midnight": {
        "label": "Midnight",
        "description": "Preto absoluto com violeta profundo. Blackwork gotico.",
        "BLACK_PURE": "#000000",
        "BLACK_SOFT": "#08060f",
        "BLACK_PANEL": "#120d1d",
        "BLACK_CARD": "#191225",
        "BLACK_HOVER": "#251a35",
        "BLACK_BORDER": "#332349",
        "RED_PRIMARY": "#8b5cf6",
        "RED_HOVER": "#a78bfa",
        "RED_DEEP": "#5b21b6",
        "RED_BLOOD": "#4c1d95",
        "RED_GLOW": "#c084fc",
        "TEXT_PRIMARY": "#efe9fa",
        "TEXT_SECONDARY": "#b4a8d0",
        "TEXT_MUTED": "#7c7296",
    },
}

DEFAULT_PRESET = "blackwork"


# ─── Constantes aplicadas (valores reescritos por apply_theme_preset) ──

# Paleta principal (placeholders — serao sobrescritos no boot)
BLACK_PURE = "#000000"
BLACK_SOFT = "#0a0a0a"
BLACK_PANEL = "#141414"
BLACK_CARD = "#1a1a1a"
BLACK_HOVER = "#242424"
BLACK_BORDER = "#2a2a2a"

RED_PRIMARY = "#B00020"
RED_HOVER = "#D32F2F"
RED_DEEP = "#7a0016"
RED_BLOOD = "#8B0000"
RED_GLOW = "#FF1744"

# Textos gerais (nao mudam entre presets, exceto os tres principais)
TEXT_PRIMARY = "#EDEDED"
TEXT_SECONDARY = "#A8A8A8"
TEXT_MUTED = "#707070"
TEXT_DANGER = "#FF5252"
TEXT_SUCCESS = "#4CAF50"
TEXT_WARNING = "#FFB74D"
TEXT_INFO = "#64B5F6"

STATUS_ONLINE = "#4CAF50"
STATUS_OFFLINE = "#E53935"
STATUS_UNKNOWN = "#9E9E9E"

# Nome do preset ativo (atualizado ao aplicar)
ACTIVE_PRESET = DEFAULT_PRESET


def apply_theme_preset(preset_name: str) -> str:
    """Aplica um preset mutando as constantes globais do modulo.

    Retorna o nome do preset efetivamente aplicado (fallback para o default
    se o nome nao existir).
    """
    global ACTIVE_PRESET

    preset = THEME_PRESETS.get(preset_name)
    if preset is None:
        preset = THEME_PRESETS[DEFAULT_PRESET]
        preset_name = DEFAULT_PRESET

    mod = sys.modules[__name__]
    for key in (
        "BLACK_PURE", "BLACK_SOFT", "BLACK_PANEL", "BLACK_CARD",
        "BLACK_HOVER", "BLACK_BORDER",
        "RED_PRIMARY", "RED_HOVER", "RED_DEEP", "RED_BLOOD", "RED_GLOW",
        "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED",
    ):
        if key in preset:
            setattr(mod, key, preset[key])

    ACTIVE_PRESET = preset_name
    return preset_name


def available_presets() -> list[tuple[str, str]]:
    """Lista (id, label) dos presets disponiveis para UI."""
    return [(pid, data["label"]) for pid, data in THEME_PRESETS.items()]


# ─── Fontes ───────────────────────────────────────────────────────────────

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_SMALL = (FONT_FAMILY, 10)
FONT_MONO = (FONT_FAMILY_MONO, 11)
FONT_MONO_BOLD = (FONT_FAMILY_MONO, 11, "bold")
FONT_SIDEBAR = (FONT_FAMILY, 12)
FONT_SIDEBAR_ACTIVE = (FONT_FAMILY, 12, "bold")
FONT_GROUP_HEADER = (FONT_FAMILY, 11, "bold")
FONT_BRAND = (FONT_FAMILY, 20, "bold")

# ─── Dimensoes e breakpoints ──────────────────────────────────────────────

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 360
WINDOW_MIN_HEIGHT = 560

SIDEBAR_WIDTH = 240          # Desktop
SIDEBAR_WIDTH_TABLET = 68    # Tablet: so icones
SIDEBAR_WIDTH_MOBILE = 0     # Mobile: escondida (vira drawer)

# Breakpoints (em pixels)
BREAKPOINT_MOBILE = 720
BREAKPOINT_TABLET = 1060

# ─── Resolucoes predefinidas ─────────────────────────────────────────────
# (id, label, width, height)
RESOLUTION_PRESETS: list[tuple[str, str, int, int]] = [
    ("mobile",     "Mobile (400x720)",         400,  720),
    ("tablet",     "Tablet (900x1000)",        900,  1000),
    ("hd",         "HD (1280x800)",            1280, 800),
    ("fullhd",     "Full HD (1440x900)",       1440, 900),
    ("large",      "Large (1680x1000)",        1680, 1000),
    ("ultrawide",  "Ultrawide (1920x1080)",    1920, 1080),
]

DEFAULT_RESOLUTION = "hd"


def available_resolutions() -> list[tuple[str, str]]:
    """Lista (id, label) de resolucoes pra UI."""
    return [(rid, rlabel) for rid, rlabel, _, _ in RESOLUTION_PRESETS]


def resolution_size(preset_id: str) -> tuple[int, int]:
    """Retorna (width, height) de um preset. Fallback para HD."""
    for rid, _, w, h in RESOLUTION_PRESETS:
        if rid == preset_id:
            return w, h
    for rid, _, w, h in RESOLUTION_PRESETS:
        if rid == DEFAULT_RESOLUTION:
            return w, h
    return 1280, 800

PADDING = 18
PADDING_SMALL = 10
CORNER_RADIUS = 8
CARD_RADIUS = 10

# ─── Marca ────────────────────────────────────────────────────────────────

BRAND_ART = "TATTOOBOT"
BRAND_TAGLINE = "BLACKWORK COPILOT"

ICONS_DIR: Path = Path(__file__).resolve().parent.parent / "icons"
BRAND_LOGO_PNG: Path = ICONS_DIR / "logo_brand.png"
BRAND_LOGO_ICO: Path = ICONS_DIR / "logo_brand.ico"


# Aplica o preset padrao no import (sobrescrito depois pelo app se settings
# especificar outro)
apply_theme_preset(DEFAULT_PRESET)
