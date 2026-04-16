"""Janela principal do TattooBot Desktop com sidebar e paginas."""

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
from utils import storage


# Lista de itens do menu lateral: (id, label, icone-texto, classe)
NAV_ITEMS = [
    # v1.0
    ("home",       "Dashboard",          "▲",  HomePage),
    ("engage",     "Engajamento",        "●",  EngagementPage),
    ("caption",    "Gerar Legendas",     "▼",  CaptionPage),
    ("ideas",      "Ideias",             "◆",  IdeasPage),
    ("spy",        "Spy de Rivais",      "▲",  SpyPage),
    ("compare",    "Comparar Perfis",    "◎",  ComparePage),
    ("growth",     "Growth Tracker",     "▣",  GrowthPage),
    ("evaluate",   "Avaliar Tattoo",     "▬",  EvaluatePage),
    # v2.0
    ("reels",      "Reels",              "▶",  ReelsPage),
    ("calendar",   "Calendario",         "◈",  CalendarPage),
    ("dm",         "Templates DM",       "✉",  DmPage),
    ("bio",        "Bio Optimizer",      "◉",  BioPage),
    ("portfolio",  "Portfolio",          "▰",  PortfolioPage),
    # config
    ("settings",   "Configuracoes",      "⚙",  SettingsPage),
]


class TattooBotApp(ctk.CTk):
    """Aplicacao desktop principal."""

    def __init__(self) -> None:
        super().__init__()

        # Configuracao base
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")  # base, mas sobrescrevemos cores

        self.title("TattooBot Copilot — Blackwork Desktop")
        self.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}")
        self.minsize(theme.WINDOW_MIN_WIDTH, theme.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=theme.BLACK_SOFT)

        # Garante dir de dados
        storage.ensure_data_dir()

        # Estado
        self.settings: dict = storage.load_settings()
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._current_page: str | None = None

        # Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._build_pages()

        # Abre home por padrao
        self.show_page("home")

    # ─── Sidebar ───────────────────────────────────────────────────────

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

        # Nav buttons
        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.grid(row=2, column=0, sticky="nsew", padx=10)

        for page_id, label, icon, _ in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_container,
                text=f"  {icon}   {label}",
                anchor="w",
                height=38,
                corner_radius=6,
                fg_color="transparent",
                hover_color=theme.BLACK_HOVER,
                text_color=theme.TEXT_SECONDARY,
                font=theme.FONT_SIDEBAR,
                command=lambda pid=page_id: self.show_page(pid),
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[page_id] = btn

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
            text="v2.0  ·  100% seguro",
            font=(theme.FONT_FAMILY, 9),
            text_color=theme.TEXT_MUTED,
        ).grid(row=4, column=0, sticky="sew", pady=(0, 8))

        # Checa status
        self.check_ollama_status()

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
        for page_id, _, _, page_cls in NAV_ITEMS:
            page = page_cls(self.content_area, app=self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[page_id] = page

    # ─── Navegacao ─────────────────────────────────────────────────────

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

        # Sobe a pagina
        page = self._pages[page_id]
        page.tkraise()
        self._current_page = page_id

        # Notifica pagina (caso precise atualizar dados)
        if hasattr(page, "on_show"):
            try:
                page.on_show()
            except Exception:  # noqa: BLE001
                pass

    # ─── Settings helpers ──────────────────────────────────────────────

    def reload_settings(self) -> None:
        """Recarrega settings do disco. Chamado depois de salvar."""
        self.settings = storage.load_settings()

    # ─── Ollama status ─────────────────────────────────────────────────

    def check_ollama_status(self) -> None:
        """Checa se o Ollama esta rodando e atualiza indicador."""
        from modules import ollama_client

        url = self.settings.get("ollama_url", "http://localhost:11434")

        task = AsyncTask(self)

        def on_result(is_online: bool) -> None:
            if is_online:
                self.status_dot.configure(text_color=theme.STATUS_ONLINE)
                self.status_label.configure(
                    text=f" Ollama online",
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
