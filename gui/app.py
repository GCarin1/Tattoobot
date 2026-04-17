"""Janela principal do TattooBot Desktop com sidebar accordion e paginas.

Suporta 3 modos responsivos (desktop/tablet/mobile) ajustados automaticamente
pela largura da janela, tema escolhido nas configuracoes (aplicado no boot)
e logo customizado acima do titulo.
"""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui import branding
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
from gui.pages.reels import ReelsPage
from gui.pages.calendar_page import CalendarPage
from gui.pages.dm_page import DmPage
from gui.pages.bio_page import BioPage
from gui.pages.portfolio_page import PortfolioPage
from gui.pages.estoque_page import EstoquePage
from utils import storage


# ─── Estrutura de navegacao ───────────────────────────────────────────────────
# Icones unicodes escolhidos por legibilidade em monospace/Segoe UI Symbol.

NAV_STANDALONE_TOP = [
    ("home",     "Dashboard",      "⌂", HomePage),
    ("evaluate", "Avaliar Tattoo", "✦", EvaluatePage),
]

NAV_GROUPS = [
    {
        "id": "social",
        "label": "Social Media",
        "icon": "◎",
        "children": [
            ("engage",    "Engajamento",     "♥", EngagementPage),
            ("caption",   "Gerar Legendas",  "✎", CaptionPage),
            ("ideas",     "Ideias",          "✧", IdeasPage),
            ("spy",       "Spy de Rivais",   "⦿", SpyPage),
            ("compare",   "Comparar Perfis", "⇌", ComparePage),
            ("reels",     "Reels",           "▶", ReelsPage),
            ("dm",        "Templates DM",    "✉", DmPage),
            ("bio",       "Bio Optimizer",   "✺", BioPage),
            ("portfolio", "Portfolio",       "▦", PortfolioPage),
        ],
        "expanded": False,
    },
    {
        "id": "negocios",
        "label": "Negocios",
        "icon": "▣",
        "children": [
            ("growth",   "Growth Tracker", "↗", GrowthPage),
            ("calendar", "Calendario",     "▤", CalendarPage),
            ("estoque",  "Estoque",        "☰", EstoquePage),
        ],
        "expanded": False,
    },
]

NAV_STANDALONE_BOTTOM = [
    ("settings", "Configuracoes", "⚙", SettingsPage),
]


def _all_nav_items():
    items = list(NAV_STANDALONE_TOP)
    for group in NAV_GROUPS:
        items.extend(group["children"])
    items.extend(NAV_STANDALONE_BOTTOM)
    return items


def _find_group_for_page(page_id: str) -> str | None:
    for group in NAV_GROUPS:
        if any(child[0] == page_id for child in group["children"]):
            return group["id"]
    return None


# ─── Modos responsivos ────────────────────────────────────────────────────────

MODE_DESKTOP = "desktop"
MODE_TABLET = "tablet"
MODE_MOBILE = "mobile"


def _mode_for_width(width: int) -> str:
    if width < theme.BREAKPOINT_MOBILE:
        return MODE_MOBILE
    if width < theme.BREAKPOINT_TABLET:
        return MODE_TABLET
    return MODE_DESKTOP


class TattooBotApp(ctk.CTk):
    """Aplicacao desktop principal."""

    def __init__(self) -> None:
        super().__init__()

        # Carrega settings e aplica tema ANTES de construir widgets
        storage.ensure_data_dir()
        self.settings: dict = storage.load_settings()
        preset = self.settings.get("theme_preset", theme.DEFAULT_PRESET)
        theme.apply_theme_preset(preset)

        # Tema claro pra preset bone_white, escuro nos demais
        appearance = "light" if preset == "bone_white" else "dark"
        ctk.set_appearance_mode(appearance)
        ctk.set_default_color_theme("dark-blue")

        # Gera assets de marca (idempotente)
        branding.ensure_brand_assets()

        self.title("TattooBot Copilot - Blackwork Desktop")
        resolution_id = self.settings.get("window_resolution", theme.DEFAULT_RESOLUTION)
        w, h = theme.resolution_size(resolution_id)
        self.geometry(f"{w}x{h}")
        self.minsize(theme.WINDOW_MIN_WIDTH, theme.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=theme.BLACK_SOFT)
        self._apply_window_icon()

        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._nav_button_specs: dict[str, tuple[str, str]] = {}  # pid -> (label, icon)
        self._group_frames: dict[str, ctk.CTkFrame] = {}
        self._group_headers: dict[str, ctk.CTkButton] = {}
        self._group_header_specs: dict[str, tuple[str, str]] = {}
        self._current_page: str | None = None

        self._mode: str = MODE_DESKTOP
        self._sidebar_visible: bool = True  # relevante no modo mobile

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)

        self._build_sidebar()
        self._build_content_area()
        self._build_pages()

        self.show_page("home")

        self.bind("<Configure>", self._on_root_resize)
        self.after(50, lambda: self._apply_mode(_mode_for_width(self.winfo_width())))

    # ─── Window icon ────────────────────────────────────────────────────────

    def _apply_window_icon(self) -> None:
        try:
            if theme.BRAND_LOGO_ICO.exists():
                self.iconbitmap(str(theme.BRAND_LOGO_ICO))
                return
        except Exception:  # noqa: BLE001
            pass
        # Fallback: iconphoto com PNG
        try:
            if theme.BRAND_LOGO_PNG.exists():
                from tkinter import PhotoImage
                img = PhotoImage(file=str(theme.BRAND_LOGO_PNG))
                self.iconphoto(True, img)
                self._icon_ref = img  # keep reference
        except Exception:  # noqa: BLE001
            pass

    # ─── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self,
            width=theme.SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=theme.BLACK_PANEL,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(2, weight=1)

        # Brand com logo
        self.brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 6))

        self._brand_logo_img = branding.load_brand_ctk_image(size=48)
        self.brand_logo_label = ctk.CTkLabel(
            self.brand_frame,
            text="" if self._brand_logo_img else "TB",
            image=self._brand_logo_img,
            width=48,
            height=48,
            font=theme.FONT_BRAND,
            text_color=theme.RED_PRIMARY,
        )
        self.brand_logo_label.pack(anchor="w", pady=(0, 6))

        self.brand_title_label = ctk.CTkLabel(
            self.brand_frame,
            text=theme.BRAND_ART,
            font=theme.FONT_BRAND,
            text_color=theme.RED_PRIMARY,
            anchor="w",
        )
        self.brand_title_label.pack(fill="x")

        self.brand_tagline_label = ctk.CTkLabel(
            self.brand_frame,
            text=theme.BRAND_TAGLINE,
            font=(theme.FONT_FAMILY, 9),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.brand_tagline_label.pack(fill="x")

        # Separador
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=theme.BLACK_BORDER,
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(12, 8))

        # Conteiner de navegacao
        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.grid(row=2, column=0, sticky="nsew", padx=8)

        for page_id, label, icon, _ in NAV_STANDALONE_TOP:
            btn = self._make_nav_button(self.nav_container, page_id, label, icon)
            btn.pack(fill="x", pady=2)

        self._sep_top = ctk.CTkFrame(self.nav_container, height=1, fg_color=theme.BLACK_BORDER)
        self._sep_top.pack(fill="x", pady=(6, 2))

        for group in NAV_GROUPS:
            gid = group["id"]
            glabel = group["label"]
            gicon = group["icon"]

            header_text = f"  {gicon}  {glabel}  ▸"
            header_btn = ctk.CTkButton(
                self.nav_container,
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
            self._group_header_specs[gid] = (glabel, gicon)

            child_frame = ctk.CTkFrame(self.nav_container, fg_color="transparent")
            for page_id, label, icon, _ in group["children"]:
                btn = self._make_nav_button(child_frame, page_id, label, icon, indent=True)
                btn.pack(fill="x", pady=1)
            self._group_frames[gid] = child_frame

        self._sep_bottom = ctk.CTkFrame(self.nav_container, height=1, fg_color=theme.BLACK_BORDER)
        self._sep_bottom.pack(fill="x", pady=(4, 2))

        for page_id, label, icon, _ in NAV_STANDALONE_BOTTOM:
            btn = self._make_nav_button(self.nav_container, page_id, label, icon)
            btn.pack(fill="x", pady=2)

        # Footer: status Ollama
        self.footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.footer.grid(row=3, column=0, sticky="sew", padx=16, pady=14)

        self.status_dot = ctk.CTkLabel(
            self.footer,
            text="●",
            text_color=theme.STATUS_UNKNOWN,
            font=(theme.FONT_FAMILY, 14, "bold"),
        )
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            self.footer,
            text=" Verificando Ollama...",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v3.0  ·  100% seguro",
            font=(theme.FONT_FAMILY, 9),
            text_color=theme.TEXT_MUTED,
        )
        self.version_label.grid(row=4, column=0, sticky="sew", pady=(0, 8))

        self.check_ollama_status()

    def _make_nav_button(
        self,
        parent: ctk.CTkFrame,
        page_id: str,
        label: str,
        icon: str,
        indent: bool = False,
    ) -> ctk.CTkButton:
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
            command=lambda pid=page_id: self._on_nav_click(pid),
        )
        self._nav_buttons[page_id] = btn
        self._nav_button_specs[page_id] = (label, icon)
        return btn

    def _on_nav_click(self, page_id: str) -> None:
        self.show_page(page_id)
        # No mobile, fecha o drawer ao navegar
        if self._mode == MODE_MOBILE and self._sidebar_visible:
            self._toggle_mobile_sidebar()

    def _toggle_group(self, group_id: str) -> None:
        frame = self._group_frames[group_id]
        header = self._group_headers[group_id]
        current_text = header.cget("text")
        if frame.winfo_ismapped():
            frame.pack_forget()
            header.configure(text=current_text.replace("▾", "▸"))
        else:
            frame.pack(fill="x", after=header)
            header.configure(text=current_text.replace("▸", "▾"))

    def _expand_group(self, group_id: str) -> None:
        frame = self._group_frames.get(group_id)
        header = self._group_headers.get(group_id)
        if frame and header and not frame.winfo_ismapped():
            frame.pack(fill="x", after=header)
            header.configure(text=header.cget("text").replace("▸", "▾"))

    # ─── Conteudo ──────────────────────────────────────────────────────────

    def _build_content_area(self) -> None:
        self.content_area = ctk.CTkFrame(
            self,
            fg_color=theme.BLACK_SOFT,
            corner_radius=0,
        )
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(1, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Topbar mobile (botao hamburger + titulo da pagina)
        self.topbar = ctk.CTkFrame(
            self.content_area,
            fg_color=theme.BLACK_PANEL,
            height=44,
            corner_radius=0,
        )
        self.topbar.grid_columnconfigure(1, weight=1)

        self.hamburger_btn = ctk.CTkButton(
            self.topbar,
            text="☰",
            width=44,
            height=44,
            corner_radius=0,
            fg_color="transparent",
            hover_color=theme.BLACK_HOVER,
            text_color=theme.RED_PRIMARY,
            font=(theme.FONT_FAMILY, 18, "bold"),
            command=self._toggle_mobile_sidebar,
        )
        self.hamburger_btn.grid(row=0, column=0, sticky="w")

        self.topbar_title = ctk.CTkLabel(
            self.topbar,
            text=theme.BRAND_ART,
            font=(theme.FONT_FAMILY, 13, "bold"),
            text_color=theme.RED_PRIMARY,
            anchor="w",
        )
        self.topbar_title.grid(row=0, column=1, sticky="ew", padx=(8, 12))
        # topbar so aparece em mobile — nao grid por padrao

        self.page_host = ctk.CTkFrame(
            self.content_area,
            fg_color=theme.BLACK_SOFT,
            corner_radius=0,
        )
        self.page_host.grid(row=1, column=0, sticky="nsew")
        self.page_host.grid_rowconfigure(0, weight=1)
        self.page_host.grid_columnconfigure(0, weight=1)

    def _build_pages(self) -> None:
        for page_id, _, _, page_cls in _all_nav_items():
            page = page_cls(self.page_host, app=self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[page_id] = page

    # ─── Responsividade ────────────────────────────────────────────────────

    def _on_root_resize(self, event) -> None:
        # Tkinter dispara <Configure> pra qualquer widget filho; filtramos
        if event.widget is not self:
            return
        new_mode = _mode_for_width(event.width)
        if new_mode != self._mode:
            self._apply_mode(new_mode)

    def _apply_mode(self, mode: str) -> None:
        self._mode = mode

        if mode == MODE_DESKTOP:
            self._set_sidebar_full()
            self.topbar.grid_forget()
            self.sidebar.grid(row=0, column=0, sticky="nsw")
            self._sidebar_visible = True
        elif mode == MODE_TABLET:
            self._set_sidebar_compact()
            self.topbar.grid_forget()
            self.sidebar.grid(row=0, column=0, sticky="nsw")
            self._sidebar_visible = True
        else:  # mobile
            self._set_sidebar_full()  # quando aparecer, mostra full
            self.topbar.grid(row=0, column=0, sticky="new")
            # Esconde sidebar por padrao no mobile
            self.sidebar.grid_forget()
            self._sidebar_visible = False

    def _set_sidebar_full(self) -> None:
        self.sidebar.configure(width=theme.SIDEBAR_WIDTH)
        # Restaura textos completos
        for pid, btn in self._nav_buttons.items():
            label, icon = self._nav_button_specs[pid]
            btn.configure(text=f"  {icon}   {label}", anchor="w")
        for gid, header in self._group_headers.items():
            glabel, gicon = self._group_header_specs[gid]
            mark = "▾" if self._group_frames[gid].winfo_ismapped() else "▸"
            header.configure(text=f"  {gicon}  {glabel}  {mark}", anchor="w")
        # Restaura brand com texto
        self.brand_title_label.pack(fill="x")
        self.brand_tagline_label.pack(fill="x")
        # Footer com texto
        try:
            self.status_label.pack(side="left", fill="x", expand=True)
        except Exception:  # noqa: BLE001
            pass
        self.version_label.configure(text="v3.0  ·  100% seguro")

    def _set_sidebar_compact(self) -> None:
        """Sidebar modo tablet: so icones, sem labels, largura reduzida."""
        self.sidebar.configure(width=theme.SIDEBAR_WIDTH_TABLET)
        for pid, btn in self._nav_buttons.items():
            _, icon = self._nav_button_specs[pid]
            btn.configure(text=f" {icon}", anchor="center")
        for gid, header in self._group_headers.items():
            _, gicon = self._group_header_specs[gid]
            mark = "▾" if self._group_frames[gid].winfo_ismapped() else "▸"
            header.configure(text=f" {gicon}", anchor="center")
        # Esconde textos da brand, deixa so o logo
        self.brand_title_label.pack_forget()
        self.brand_tagline_label.pack_forget()
        # Esconde label do footer, deixa so o dot
        try:
            self.status_label.pack_forget()
        except Exception:  # noqa: BLE001
            pass
        self.version_label.configure(text="v3.0")

    def _toggle_mobile_sidebar(self) -> None:
        if self._mode != MODE_MOBILE:
            return
        if self._sidebar_visible:
            self.sidebar.grid_forget()
            self._sidebar_visible = False
        else:
            self.sidebar.grid(row=0, column=0, rowspan=1, sticky="nsw")
            self._sidebar_visible = True

    # ─── Navegacao ─────────────────────────────────────────────────────────

    def show_page(self, page_id: str) -> None:
        if page_id not in self._pages:
            return

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

        group_id = _find_group_for_page(page_id)
        if group_id and self._mode != MODE_TABLET:
            # No tablet deixa os grupos colapsados (economia de espaco)
            self._expand_group(group_id)

        page = self._pages[page_id]
        page.tkraise()
        self._current_page = page_id

        # Atualiza topbar title (para mobile)
        if hasattr(page, "TITLE"):
            try:
                self.topbar_title.configure(text=page.TITLE)
            except Exception:  # noqa: BLE001
                pass

        if hasattr(page, "on_show"):
            try:
                page.on_show()
            except Exception:  # noqa: BLE001
                pass

    # ─── Settings helpers ──────────────────────────────────────────────────

    def reload_settings(self) -> None:
        self.settings = storage.load_settings()

    # ─── Hot reload de tema ────────────────────────────────────────────────

    def apply_theme_preset(self, preset_name: str, save: bool = True) -> None:
        """Troca o tema em tempo real reconstruindo a UI.

        Se `save` for True, persiste a escolha em settings.json.
        """
        theme.apply_theme_preset(preset_name)

        if save:
            self.settings["theme_preset"] = preset_name
            try:
                storage.save_settings(self.settings)
            except OSError:
                pass

        appearance = "light" if preset_name == "bone_white" else "dark"
        ctk.set_appearance_mode(appearance)

        # Regera logo com a nova cor de destaque
        branding.ensure_brand_assets(force=True)

        self._rebuild_ui()

    def apply_resolution_preset(self, resolution_id: str, save: bool = True) -> None:
        """Redimensiona a janela para a resolucao escolhida.

        Centraliza na tela. Modo responsivo (mobile/tablet/desktop) eh
        ajustado pelo handler de <Configure>.
        """
        w, h = theme.resolution_size(resolution_id)

        if save:
            self.settings["window_resolution"] = resolution_id
            try:
                storage.save_settings(self.settings)
            except OSError:
                pass

        # Centraliza na tela
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Forca reavaliacao do modo responsivo agora mesmo
        self.after(80, lambda: self._apply_mode(_mode_for_width(w)))

    def _rebuild_ui(self) -> None:
        """Destroi e recria sidebar + paginas para refletir o tema ativo.

        Mantem a janela raiz e o estado de navegacao (pagina atual).
        """
        target_page = self._current_page or "home"

        # Limpa referencias de widgets antigos
        self._pages.clear()
        self._nav_buttons.clear()
        self._nav_button_specs.clear()
        self._group_frames.clear()
        self._group_headers.clear()
        self._group_header_specs.clear()

        # Destroi containers antigos
        try:
            self.sidebar.destroy()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.content_area.destroy()
        except Exception:  # noqa: BLE001
            pass

        self.configure(fg_color=theme.BLACK_SOFT)

        # Reconstroi
        self._build_sidebar()
        self._build_content_area()
        self._build_pages()

        # Reaplica modo responsivo
        self._apply_mode(_mode_for_width(self.winfo_width() or theme.WINDOW_WIDTH))

        # Volta pra mesma pagina
        self.show_page(target_page)

    # ─── Ollama status ─────────────────────────────────────────────────────

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
    app = TattooBotApp()
    app.mainloop()
