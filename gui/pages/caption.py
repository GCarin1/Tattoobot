"""Pagina de Gerador de Legendas."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard


POST_TYPES = [
    "Foto de tattoo finalizada",
    "Processo / making of",
    "Healed (cicatrizada)",
    "Flash / disponivel",
    "Reel / video",
    "Carrossel",
]

GOALS = [
    "Engajamento (curtidas e comentarios)",
    "Agendamento (atrair clientes)",
    "Portfolio (mostrar trabalho)",
]


class CaptionPage(BasePage):
    TITLE = "Gerador de Legendas"
    DESCRIPTION = (
        "Cria legendas otimizadas com SEO, 30 hashtags organizadas por tier e CTAs. "
        "Basta preencher os campos abaixo."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Form
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
            text="PARAMETROS DO POST",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 10))

        # Tipo de post
        self._add_label(form, "Tipo de post")
        self.post_type_var = ctk.StringVar(value=POST_TYPES[0])
        self.post_type_menu = ctk.CTkOptionMenu(
            form,
            values=POST_TYPES,
            variable=self.post_type_var,
            fg_color=theme.BLACK_SOFT,
            button_color=theme.RED_DEEP,
            button_hover_color=theme.RED_PRIMARY,
            dropdown_fg_color=theme.BLACK_CARD,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY,
            height=34,
        )
        self.post_type_menu.pack(fill="x", padx=20, pady=(0, 10))

        # Descricao
        self._add_label(form, "Descricao do post")
        self.description_entry = ctk.CTkEntry(
            form,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text="Ex: blackwork de lobo no antebraco, sessao de 4 horas",
            height=34,
        )
        self.description_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Objetivo
        self._add_label(form, "Objetivo")
        self.goal_var = ctk.StringVar(value=GOALS[0])
        self.goal_menu = ctk.CTkOptionMenu(
            form,
            values=GOALS,
            variable=self.goal_var,
            fg_color=theme.BLACK_SOFT,
            button_color=theme.RED_DEEP,
            button_hover_color=theme.RED_PRIMARY,
            dropdown_fg_color=theme.BLACK_CARD,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY,
            height=34,
        )
        self.goal_menu.pack(fill="x", padx=20, pady=(0, 14))

        # Botao
        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns,
            text="▶  Gerar Legendas",
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

        # Results
        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def _add_label(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=theme.FONT_BODY_BOLD,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(4, 4))

    def _start(self) -> None:
        description = self.description_entry.get().strip()
        if not description:
            self.status_label.configure(
                text="Preencha a descricao do post.",
                text_color=theme.TEXT_DANGER,
            )
            return

        self._clear_results()
        self._set_btn_loading(self.run_btn, "Gerando...")
        self.status_label.configure(
            text="Chamando IA... pode levar ate 1 minuto.",
            text_color=theme.TEXT_INFO,
        )

        post_type = self.post_type_var.get()
        goal = self.goal_var.get()
        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._caption_flow(settings, post_type, description, goal),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self._set_btn_ready(self.run_btn, "▶  Gerar Legendas"),
        )

    async def _caption_flow(self, settings, post_type, description, goal):
        from modules import ollama_client
        from modules.caption import _build_caption_prompt, _parse_caption_response

        tattoo_style = settings.get("tattoo_style", "blackwork")
        artist_city = settings.get("artist_city", "")
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ollama_model", "llama3")

        prompt = _build_caption_prompt(
            tattoo_style, artist_city, post_type, description, goal,
        )
        response = await ollama_client.generate(prompt, ollama_url, ollama_model)
        if not response:
            raise RuntimeError(
                "Nao foi possivel gerar legendas. Verifique se o Ollama esta rodando "
                "e se o modelo configurado existe."
            )
        captions, hashtags, ctas = _parse_caption_response(response)
        return {
            "captions": captions,
            "hashtags": hashtags,
            "ctas": ctas,
            "raw": response,
        }

    def _on_done(self, result) -> None:
        self.status_label.configure(
            text="Copie as legendas e cole no Instagram.",
            text_color=theme.TEXT_SUCCESS,
        )

        captions = result["captions"]
        hashtags = result["hashtags"]
        ctas = result["ctas"]

        if not captions:
            InfoCard(
                self.results_frame,
                title="Resposta bruta da IA",
                body=result["raw"],
                accent=theme.RED_PRIMARY,
            ).pack(fill="x", pady=6)
            return

        for i, caption in enumerate(captions, 1):
            self._result_card(
                title=f"Legenda {i}",
                body=caption,
                copy_text=caption,
                accent=theme.RED_PRIMARY,
            )

        if hashtags:
            self._result_card(
                title="Hashtags",
                body=hashtags,
                copy_text=hashtags,
                accent=theme.RED_PRIMARY,
            )

        if ctas:
            ctas_text = "\n\n".join(f"CTA {i}: {c}" for i, c in enumerate(ctas, 1))
            self._result_card(
                title="Calls to Action",
                body=ctas_text,
                copy_text=ctas_text,
                accent=theme.RED_PRIMARY,
            )

    def _result_card(self, title: str, body: str, copy_text: str, accent: str) -> None:
        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=accent,
            border_width=1,
        )
        card.pack(fill="x", pady=6)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header,
            text=title,
            font=theme.FONT_SUBHEADING,
            text_color=accent,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            header,
            text="Copiar",
            width=80,
            height=28,
            font=theme.FONT_SMALL,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.RED_DEEP,
            command=lambda: self._copy(copy_text),
        ).pack(side="right")

        ctk.CTkLabel(
            card,
            text=body,
            font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=980,
        ).pack(fill="x", padx=16, pady=(0, 14))

    def _copy(self, text: str) -> None:
        self.app.clipboard_clear()
        self.app.clipboard_append(text)
        self.status_label.configure(
            text="Copiado para a area de transferencia.",
            text_color=theme.TEXT_SUCCESS,
        )

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(
            text=f"Erro: {exc}",
            text_color=theme.TEXT_DANGER,
        )
