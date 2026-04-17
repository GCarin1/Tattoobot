"""Classe base para todas as paginas da GUI."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.async_worker import AsyncTask


class BasePage(ctk.CTkFrame):
    """Pagina base com cabecalho (titulo + descricao) e corpo scrollavel.

    Subclasses podem sobrescrever `build_body(parent)` para montar o conteudo
    dentro de um frame scrollavel.

    Atributos:
        app: referencia ao TattooBotApp principal (para settings, etc).
        body: frame onde o conteudo deve ser adicionado.
    """

    TITLE: str = "Pagina"
    DESCRIPTION: str = ""
    ACCENT: str = theme.RED_PRIMARY

    def __init__(self, parent, app, **kwargs) -> None:
        kwargs.setdefault("fg_color", theme.BLACK_SOFT)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(parent, **kwargs)

        self.app = app
        self._task: AsyncTask | None = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_scroll_area()
        self.build_body(self.body)

    # ─── Layout ────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        # ACCENT na classe e congelado no import — resolvemos a cor viva agora.
        accent = theme.RED_PRIMARY

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 4))

        ctk.CTkLabel(
            header,
            text=self.TITLE,
            font=theme.FONT_TITLE,
            text_color=accent,
            anchor="w",
        ).pack(fill="x")

        if self.DESCRIPTION:
            ctk.CTkLabel(
                header,
                text=self.DESCRIPTION,
                font=theme.FONT_BODY,
                text_color=theme.TEXT_MUTED,
                anchor="w",
                justify="left",
                wraplength=1000,
            ).pack(fill="x", pady=(2, 0))

        # Linha separadora vermelha sutil
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=accent,
        ).grid(row=0, column=0, sticky="ews", padx=32, pady=(0, 0))

    def _build_scroll_area(self) -> None:
        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.BLACK_SOFT,
            corner_radius=0,
            scrollbar_button_color=theme.RED_DEEP,
            scrollbar_button_hover_color=theme.RED_PRIMARY,
        )
        self.body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(16, 24))

    # ─── Subclasses sobrescrevem ──────────────────────────────────────

    def build_body(self, parent) -> None:
        """Monta o conteudo dentro do frame scrollavel.

        Deve ser sobrescrito pelas subclasses.
        """
        pass

    def on_show(self) -> None:
        """Chamado toda vez que a pagina e exibida. Sobrescreva se precisar."""
        pass

    # ─── Utilitarios ───────────────────────────────────────────────────

    def clear_body(self) -> None:
        """Remove todos os widgets do body."""
        for widget in self.body.winfo_children():
            widget.destroy()

    def run_async(
        self,
        coro_factory,
        on_result=None,
        on_error=None,
        on_done=None,
    ) -> None:
        """Roda coroutine em background."""
        if self._task and self._task.running:
            return
        self._task = AsyncTask(self.app)
        self._task.run(
            coro_factory=coro_factory,
            on_result=on_result,
            on_error=on_error,
            on_done=on_done,
        )

    def _set_btn_loading(self, btn: ctk.CTkButton, text: str = "Gerando...") -> None:
        """Desativa botao com visual de carregamento (cinza)."""
        btn.configure(
            state="disabled",
            text=text,
            fg_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_MUTED,
            hover_color=theme.BLACK_BORDER,
        )

    def _set_btn_ready(self, btn: ctk.CTkButton, text: str) -> None:
        """Restaura botao para estado ativo (vermelho)."""
        btn.configure(
            state="normal",
            text=text,
            fg_color=theme.RED_PRIMARY,
            text_color=theme.TEXT_PRIMARY,
            hover_color=theme.RED_HOVER,
        )
