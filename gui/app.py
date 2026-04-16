"""Janela principal do TattooBot Desktop com sidebar accordion e paginas."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.async_worker import AsyncTask
from gui.pages.home import HomePage
from gui.pages.engagement import EngagementPage
from gui.pages.caption import CaptionPage
from gui.pages.ideas import IdeasPage
from gui.pages.spy import SpyPage
from gui.pages.compare import ComparePage
from gui.pages.growth import GrowthPage
from gui.pages.evaluate import EvaluatePage
from gui.pages.settings import SettingsPage
# v2.0 — novas paginas
from gui.pages.reels import ReelsPage
from gui.pages.calendar_page import CalendarPage
from gui.pages.dm_page import DmPage
from gui.pages.bio_page import BioPage
from gui.pages.portfolio_page import PortfolioPage
# v3.0 — Estoque
from gui.pages.estoque_page import EstoquePage
from utils import storage


# ─── Estrutura de navegacao ───────────────────────────────────────────────────

# Itens avulsos sempre visiveis no topo (id, label, icone, classe)
NAV_STANDALONE_TOP = [
    ("home",     "Dashboard",    "▲", HomePage),
    ("evaluate", "Avaliar Tattoo", "▬", EvaluatePage),
]

# Grupos recoliveis (accordion)
NAV_GROUPS = [
    {
        "id": "social",
        "label": "Social Media",
        "icon": "◎",
        "children": [
            ("engage",    "Engajamento",    "●", EngagementPage),
            ("caption",   "Gerar Legendas", "▼", CaptionPage),
            ("ideas",     "Ideias",         "◆", IdeasPage),
            ("spy",       "Spy de Rivais",  "▲", SpyPage),
            ("compare",   "Comparar Perfis","◎", ComparePage),
            ("reels",     "Reels",          "▶", ReelsPage),
            ("dm",        "Templates DM",   "✉", DmPage),
            ("bio",       "Bio Optimizer",  "◉", BioPage),
            ("portfolio", "Portfolio",      "▰", PortfolioPage),
        ],
        "expanded": False,
    },
    {
        "id": "negocios",
        "label": "Negocios",
        "icon": "▣",
        "children": [
            ("growth",   "Growth Tracker", "▣", GrowthPage),
            ("calendar", "Calendario",     "◈", CalendarPage),
            ("estoque",  "Estoque",        "◧", EstoquePage),
        ],
        "expanded": False,
    },
]

# Item avulso sempre visivel no rodape
NAV_STANDALONE_BOTTOM = [
    ("settings", "Configuracoes", "⚙", SettingsPage),
]


def _all_nav_items():
    """Retorna todos os itens de navegacao (avulsos + filhos de grupos)."""
    items = list(NAV_STANDALONE_TOP)
    for group in NAV_GROUPS:
        items.extend(group["children"])
    items.extend(NAV_STANDALONE_BOTTOM)
    return items


def _find_group_for_page(page_id: str) -> str | None:
    """Retorna o id do grupo que contem page_id, ou None se for avulso."""
    for group in NAV_GROUPS:
        if any(child[0] == page_id for child in group["children"]):
            return group["id"]
    return None


class TattooBotApp(ctk.CTk):
    """Aplicacao desktop principal."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("TattooBot Copilot — Blackwork Desktop")
        self.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}")
        self.minsize(theme.WINDOW_MIN_WIDTH, theme.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=theme.BLACK_SOFT)

        storage.ensure_data_dir()

        self.settings: dict = storage.load_settings()
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._group_frames: dict[str, ctk.CTkFrame] = {}
        self._group_headers: dict[str, ctk.CTkButton] = {}
        self._current_page: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._build_pages()

        self.show_page("home")

    # ─── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            width=theme.SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=theme.BLACK_PANEL,
        )
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)

        # Brand
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 6))

        ctk.CTkLabel(
            brand_frame,
            text=theme.BRAND_ART,
            font=theme.FONT_BRAND,
            text_color=theme.RED_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            brand_frame,
            text=theme.BRAND_TAGLINE,
            font=(theme.FONT_FAMILY, 9),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

        # Separador
        ctk.CTkFrame(
            sidebar,
            height=1,
            fg_color=theme.BLACK_BORDER,
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 8))

        # Conteiner de navegacao
        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.grid(row=2, column=0, sticky="nsew", padx=10)

        # ── Itens avulsos do topo ──────────────────────────────────────────────
        for page_id, label, icon, _ in NAV_STANDALONE_TOP:
            btn = self._make_nav_button(nav_container, page_id, label, icon)
            btn.pack(fill="x", pady=2)

        # Separador sutil
        ctk.CTkFrame(nav_container, height=1, fg_color=theme.BLACK_BORDER).pack(
            fill="x", pady=(6, 2)
        )

        # ── Grupos accordion ───────────────────────────────────────────────────
        for group in NAV_GROUPS:
            gid = group["id"]
            glabel = group["label"]
            gicon = group["icon"]

            # Header do grupo (clicavel para expandir/recolher)
            header_text = f"  {gicon}  {glabel}  ▸"
            header_btn = ctk.CTkButton(
                nav_container,
                text=header_text,
                anchor="w",
                height=36,
                corner_radius=6,
                fg_color=theme.BLACK_CARD,
                hover_color=theme.BLACK_HOVER,
                text_color=theme.RED_PRIMARY,
                font=theme.FONT_GROUP_HEADER,
                command=lambda gid_=gid: self._toggle_group(gid_),
            )
            header_btn.pack(fill="x", pady=(4, 1))
            self._group_headers[gid] = header_btn

            # Frame filho (inicialmente oculto)
            child_frame = ctk.CTkFrame(nav_container, fg_color="transparent")
            for page_id, label, icon, _ in group["children"]:
                btn = self._make_nav_button(child_frame, page_id, label, icon, indent=True)
                btn.pack(fill="x", pady=1)
            self._group_frames[gid] = child_frame
            # Nao faz pack ainda (recolhido por padrao)

        # Separador sutil
        ctk.CTkFrame(nav_container, height=1, fg_color=theme.BLACK_BORDER).pack(
            fill="x", pady=(4, 2)
        )

        # ── Itens avulsos do rodape ────────────────────────────────────────────
        for page_id, label, icon, _ in NAV_STANDALONE_BOTTOM:
            btn = self._make_nav_button(nav_container, page_id, label, icon)
            btn.pack(fill="x", pady=2)

        # Footer: status Ollama
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="sew", padx=16, pady=14)

        self.status_dot = ctk.CTkLabel(
            footer,
            text="●",
            text_color=theme.STATUS_UNKNOWN,
            font=(theme.FONT_FAMILY, 14, "bold"),
        )
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            footer,
            text=" Verificando Ollama...",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            sidebar,
            text="v3.0  ·  100% seguro",
            font=(theme.FONT_FAMILY, 9),
            text_color=theme.TEXT_MUTED,
        ).grid(row=4, column=0, sticky="sew", pady=(0, 8))

        self.check_ollama_status()

    def _make_nav_button(
        self,
        parent: ctk.CTkFrame,
        page_id: str,
        label: str,
        icon: str,
        indent: bool = False,
    ) -> ctk.CTkButton:
        padx_left = 18 if indent else 2
        btn = ctk.CTkButton(
            parent,
            text=f"  {icon}   {label}",
            anchor="w",
            height=34,
            corner_radius=6,
            fg_color="transparent",
            hover_color=theme.BLACK_HOVER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_SIDEBAR,
            command=lambda pid=page_id: self.show_page(pid),
        )
        if indent:
            btn.configure(
                width=theme.SIDEBAR_WIDTH - 40,
                fg_color="transparent",
            )
        self._nav_buttons[page_id] = btn
        return btn

    def _toggle_group(self, group_id: str) -> None:
        frame = self._group_frames[group_id]
        header = self._group_headers[group_id]
        current_text = header.cget("text")
        if frame.winfo_ismapped():
            frame.pack_forget()
            header.configure(text=current_text.replace("▾", "▸"))
        else:
            # Inserir apos o header
            frame.pack(fill="x", after=header)
            header.configure(text=current_text.replace("▸", "▾"))

    def _expand_group(self, group_id: str) -> None:
        """Expande o grupo se ainda estiver recolhido."""
        frame = self._group_frames.get(group_id)
        header = self._group_headers.get(group_id)
        if frame and header and not frame.winfo_ismapped():
            frame.pack(fill="x", after=header)
            header.configure(text=header.cget("text").replace("▸", "▾"))

    def _build_content_area(self) -> None:
        self.content_area = ctk.CTkFrame(
            self,
            fg_color=theme.BLACK_SOFT,
            corner_radius=0,
        )
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

    def _build_pages(self) -> None:
        for page_id, _, _, page_cls in _all_nav_items():
            page = page_cls(self.content_area, app=self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[page_id] = page

    # ─── Navegacao ─────────────────────────────────────────────────────────────

    def show_page(self, page_id: str) -> None:
        if page_id not in self._pages:
            return

        # Atualiza botoes
        for pid, btn in self._nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=theme.RED_DEEP,
                    text_color=theme.TEXT_PRIMARY,
                    font=theme.FONT_SIDEBAR_ACTIVE,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=theme.TEXT_SECONDARY,
                    font=theme.FONT_SIDEBAR,
                )

        # Auto-expande o grupo que contem a pagina
        group_id = _find_group_for_page(page_id)
        if group_id:
            self._expand_group(group_id)

        # Sobe a pagina
        page = self._pages[page_id]
        page.tkraise()
        self._current_page = page_id

        if hasattr(page, "on_show"):
            try:
                page.on_show()
            except Exception:  # noqa: BLE001
                pass

    # ─── Settings helpers ──────────────────────────────────────────────────────

    def reload_settings(self) -> None:
        self.settings = storage.load_settings()

    # ─── Ollama status ─────────────────────────────────────────────────────────

    def check_ollama_status(self) -> None:
        from modules import ollama_client

        url = self.settings.get("ollama_url", "http://localhost:11434")
        task = AsyncTask(self)

        def on_result(is_online: bool) -> None:
            if is_online:
                self.status_dot.configure(text_color=theme.STATUS_ONLINE)
                self.status_label.configure(
                    text=" Ollama online",
                    text_color=theme.TEXT_SUCCESS,
                )
            else:
                self.status_dot.configure(text_color=theme.STATUS_OFFLINE)
                self.status_label.configure(
                    text=" Ollama offline",
                    text_color=theme.TEXT_DANGER,
                )

        def on_error(_exc: Exception) -> None:
            self.status_dot.configure(text_color=theme.STATUS_OFFLINE)
            self.status_label.configure(
                text=" Ollama offline",
                text_color=theme.TEXT_DANGER,
            )

        task.run(
            coro_factory=lambda: ollama_client.check_ollama(url),
            on_result=on_result,
            on_error=on_error,
        )


def launch() -> None:
    """Ponto de entrada do app GUI."""
    app = TattooBotApp()
    app.mainloop()
