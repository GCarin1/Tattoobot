"""Tema visual do TattooBot - estilo Blackwork (preto + vermelho sangue).

Paleta inspirada em estudios de tatuagem: fundo quase preto, acentos em
vermelho escuro e textos off-white. Sem cores vivas - tudo sombrio e serio.
"""

# ─── Paleta principal ─────────────────────────────────────────────────────

BLACK_PURE = "#000000"
BLACK_SOFT = "#0a0a0a"      # Fundo principal da janela
BLACK_PANEL = "#141414"     # Fundo de sidebar
BLACK_CARD = "#1a1a1a"      # Cards e elementos elevados
BLACK_HOVER = "#242424"     # Hover states
BLACK_BORDER = "#2a2a2a"    # Bordas sutis

# Vermelhos (blackwork bleed)
RED_PRIMARY = "#B00020"     # Vermelho principal
RED_HOVER = "#D32F2F"       # Hover em botoes vermelhos
RED_DEEP = "#7a0016"        # Pressed state / ativo
RED_BLOOD = "#8B0000"       # Variacao escura
RED_GLOW = "#FF1744"        # Destaque muito sutil

# Textos
TEXT_PRIMARY = "#EDEDED"    # Texto principal
TEXT_SECONDARY = "#A8A8A8"  # Texto secundario
TEXT_MUTED = "#707070"      # Texto apagado / placeholder
TEXT_DANGER = "#FF5252"
TEXT_SUCCESS = "#4CAF50"
TEXT_WARNING = "#FFB74D"
TEXT_INFO = "#64B5F6"

# Status indicators
STATUS_ONLINE = "#4CAF50"
STATUS_OFFLINE = "#E53935"
STATUS_UNKNOWN = "#9E9E9E"

# ─── Fontes ───────────────────────────────────────────────────────────────

FONT_FAMILY = "Segoe UI"            # Windows default bonito
FONT_FAMILY_MONO = "Consolas"       # Monospace para output

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
FONT_BRAND = (FONT_FAMILY, 20, "bold")

# ─── Dimensoes ────────────────────────────────────────────────────────────

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 640

SIDEBAR_WIDTH = 230
PADDING = 18
PADDING_SMALL = 10
CORNER_RADIUS = 8
CARD_RADIUS = 10

# ─── Ascii brand (sidebar) ────────────────────────────────────────────────

BRAND_ART = "TATTOOBOT"
BRAND_TAGLINE = "BLACKWORK COPILOT"
