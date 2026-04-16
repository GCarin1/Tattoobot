"""Dashboard com estatisticas gerais."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import StatsCard, InfoCard
from utils import storage


class HomePage(BasePage):
    TITLE = "Dashboard"
    DESCRIPTION = (
        "Visao geral do seu crescimento e atalhos rapidos. "
        "Escolha uma acao no menu lateral para comecar."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Stats cards em grid
        stats_row = ctk.CTkFrame(parent, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 20))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1, uniform="stats")

        self.stats_widgets = {}
        specs = [
            ("history", "Perfis sugeridos", "—", "no historico total"),
            ("competitors", "Rivais monitorados", "—", "perfis no spy"),
            ("growth", "Registros de growth", "—", "entradas salvas"),
            ("followers", "Seguidores atuais", "—", "ultimo registro"),
        ]
        for col, (key, label, value, sub) in enumerate(specs):
            card = StatsCard(
                stats_row,
                label=label,
                value=value,
                subtitle=sub,
                accent=theme.RED_PRIMARY,
            )
            card.grid(row=0, column=col, sticky="nsew", padx=6, pady=0)
            self.stats_widgets[key] = card

        # Atalhos rapidos
        ctk.CTkLabel(
            parent,
            text="ATALHOS RAPIDOS",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(4, 8))

        shortcuts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        shortcuts_frame.pack(fill="x", pady=(0, 20))
        shortcuts = [
            ("engage", "Engajamento Diario", "Buscar perfis e gerar comentarios"),
            ("caption", "Gerar Legendas", "Texto + hashtags + CTA"),
            ("ideas", "Ideias de Conteudo", "7 sugestoes criativas"),
            ("evaluate", "Avaliar Tattoo", "IA analisa sua foto"),
        ]
        for i in range(len(shortcuts)):
            shortcuts_frame.grid_columnconfigure(i, weight=1, uniform="sc")

        for col, (pid, title, desc) in enumerate(shortcuts):
            btn_frame = ctk.CTkFrame(
                shortcuts_frame,
                fg_color=theme.BLACK_CARD,
                corner_radius=theme.CARD_RADIUS,
                border_color=theme.BLACK_BORDER,
                border_width=1,
            )
            btn_frame.grid(row=0, column=col, sticky="nsew", padx=6)

            ctk.CTkLabel(
                btn_frame,
                text=title,
                font=theme.FONT_BODY_BOLD,
                text_color=theme.RED_GLOW,
                anchor="w",
            ).pack(fill="x", padx=14, pady=(12, 2))

            ctk.CTkLabel(
                btn_frame,
                text=desc,
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=220,
            ).pack(fill="x", padx=14, pady=(0, 8))

            ctk.CTkButton(
                btn_frame,
                text="Abrir",
                height=30,
                fg_color=theme.RED_DEEP,
                hover_color=theme.RED_PRIMARY,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_BODY_BOLD,
                command=lambda p=pid: self.app.show_page(p),
            ).pack(fill="x", padx=14, pady=(0, 12))

        # Info geral sobre o app
        about = InfoCard(
            parent,
            title="Sobre o TattooBot",
            body=(
                "Assistente para tatuadores que usa IA local (Ollama) para gerar "
                "comentarios, legendas e ideias — 100% seguro, sem automacao na "
                "sua conta do Instagram. Voce executa manualmente no celular; "
                "o bot so pensa, analisa e sugere."
            ),
            accent=theme.RED_PRIMARY,
        )
        about.pack(fill="x", pady=(8, 0))

        # Secao de Analytics do Estoque embutida no dashboard
        ctk.CTkLabel(
            parent,
            text="ANALYTICS DE ESTOQUE",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(24, 8))

        analytics_panel = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        analytics_panel.pack(fill="x", pady=(0, 8))

        from gui.pages.estoque_analytics import build_analytics_tab
        build_analytics_tab(analytics_panel, app=self.app, page_ref=self, use_scroll=False, padx=12)

    def on_show(self) -> None:
        """Atualiza stats sempre que abrir o dashboard."""
        try:
            history = storage.load_history()
            competitors = storage.load_competitors()
            growth = storage.load_growth()
        except Exception:  # noqa: BLE001
            history, competitors, growth = [], [], []

        self._update_stat("history", str(len(history)))
        self._update_stat("competitors", str(len(competitors)))
        self._update_stat("growth", str(len(growth)))

        if growth:
            try:
                last = growth[-1].get("followers", 0)
                self._update_stat("followers", f"{last:,}".replace(",", "."))
            except Exception:  # noqa: BLE001
                self._update_stat("followers", "—")
        else:
            self._update_stat("followers", "—")

    def _update_stat(self, key: str, value: str) -> None:
        card = self.stats_widgets.get(key)
        if not card:
            return
        # Pega o segundo label (o valor grande)
        labels = [w for w in card.winfo_children() if isinstance(w, ctk.CTkLabel)]
        if len(labels) >= 2:
            labels[1].configure(text=value)
