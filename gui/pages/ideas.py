"""Pagina de Ideias de Conteudo."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import IdeaCard, InfoCard
from utils import storage


class IdeasPage(BasePage):
    TITLE = "Ideias de Conteudo"
    DESCRIPTION = (
        "Gera 7 ideias originais para Instagram (Reels, Carrossel, Story, Post). "
        "A IA leva em conta sazonalidade e evita repetir ideias ja sugeridas."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        form = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        form.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            form,
            text="TEMA (opcional)",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 8))

        self.theme_entry = ctk.CTkEntry(
            form,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text="Ex: time-lapse, antes e depois, aftercare (deixe vazio para geral)",
            height=34,
        )
        self.theme_entry.pack(fill="x", padx=20, pady=(0, 14))

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns,
            text="▶  Gerar 7 Ideias",
            height=40,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._start,
        )
        self.run_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            btns,
            text="",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_label.pack(side="left", padx=14, fill="x", expand=True)

        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def _start(self) -> None:
        self._clear_results()
        self._set_btn_loading(self.run_btn, "Gerando...")
        self.status_label.configure(
            text="IA pensando em ideias originais... ~30-60s.",
            text_color=theme.TEXT_INFO,
        )

        theme_text = self.theme_entry.get().strip()
        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._ideas_flow(settings, theme_text),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self._set_btn_ready(self.run_btn, "▶  Gerar 7 Ideias"),
        )

    async def _ideas_flow(self, settings, theme_text):
        from modules import ollama_client
        from modules.content_ideas import _build_ideas_prompt, _parse_ideas

        tattoo_style = settings.get("tattoo_style", "blackwork")
        artist_city = settings.get("artist_city", "")
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ollama_model", "llama3")

        recent_titles = storage.get_recent_idea_titles(limit=30)
        prompt = _build_ideas_prompt(tattoo_style, artist_city, theme_text, recent_titles)
        response = await ollama_client.generate(
            prompt, ollama_url, ollama_model,
            temperature=1.0, top_p=0.95,
        )
        if not response:
            raise RuntimeError(
                "Nao foi possivel gerar ideias. Verifique o Ollama e o modelo."
            )
        ideas = _parse_ideas(response)
        if not ideas:
            return {"ideas": [], "raw": response}

        storage.add_to_ideas_history(ideas)
        return {"ideas": ideas, "raw": response}

    def _on_done(self, result) -> None:
        ideas = result["ideas"]

        if not ideas:
            self.status_label.configure(
                text="IA retornou formato inesperado. Veja resposta bruta abaixo.",
                text_color=theme.TEXT_WARNING,
            )
            InfoCard(
                self.results_frame,
                title="Resposta bruta",
                body=result["raw"],
                accent=theme.RED_PRIMARY,
            ).pack(fill="x", pady=6)
            return

        self.status_label.configure(
            text=f"{len(ideas)} ideias geradas. Escolha 2-3 para executar esta semana.",
            text_color=theme.TEXT_SUCCESS,
        )

        for i, idea in enumerate(ideas, 1):
            card = IdeaCard(
                self.results_frame,
                index=i,
                format_type=idea.get("format", "Post"),
                title=idea.get("title", "Sem titulo"),
                description=idea.get("description", ""),
                tip=idea.get("tip", ""),
                hashtag=idea.get("hashtag", ""),
            )
            card.pack(fill="x", pady=6)

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(
            text=f"Erro: {exc}",
            text_color=theme.TEXT_DANGER,
        )
