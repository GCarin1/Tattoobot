"""Pagina principal de Estoque com 4 abas: Planilha, Busca, Orcamento, Analytics."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage


class EstoquePage(BasePage):
    TITLE = "Estoque"
    DESCRIPTION = "Gestao de insumos: planilha, busca de preco, orcamento e analytics."
    ACCENT = theme.RED_PRIMARY

    def __init__(self, parent, app, **kwargs) -> None:
        self._price_results: list = []
        super().__init__(parent, app, **kwargs)

    def _build_scroll_area(self) -> None:
        # Substitui o CTkScrollableFrame padrao por um CTkFrame simples
        # pois cada aba gerencia seu proprio scroll internamente.
        self.body = ctk.CTkFrame(
            self,
            fg_color=theme.BLACK_SOFT,
            corner_radius=0,
        )
        self.body.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8, 0))

    def build_body(self, parent) -> None:
        from gui.pages.estoque_planilha import build_planilha_tab
        from gui.pages.estoque_preco import build_preco_tab
        from gui.pages.estoque_orcamento import build_orcamento_tab

        tabs = ctk.CTkTabview(
            parent,
            fg_color=theme.BLACK_CARD,
            segmented_button_fg_color=theme.BLACK_PANEL,
            segmented_button_selected_color=theme.RED_PRIMARY,
            segmented_button_selected_hover_color=theme.RED_HOVER,
            segmented_button_unselected_color=theme.BLACK_PANEL,
            segmented_button_unselected_hover_color=theme.BLACK_HOVER,
            text_color=theme.TEXT_PRIMARY,
            text_color_disabled=theme.TEXT_MUTED,
            corner_radius=8,
        )
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        tabs.add("Planilha")
        tabs.add("Busca de Precos")
        tabs.add("Orcamento")

        build_planilha_tab(tabs.tab("Planilha"), app=self.app, page_ref=self)
        build_preco_tab(tabs.tab("Busca de Precos"), app=self.app, page_ref=self)
        build_orcamento_tab(tabs.tab("Orcamento"), app=self.app, page_ref=self)

    def on_show(self) -> None:
        if hasattr(self, "_orcamento_reload"):
            self._orcamento_reload()
        if hasattr(self, "_preco_reload"):
            self._preco_reload()
