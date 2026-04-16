"""Pagina de Templates de Atendimento (DM / WhatsApp)."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard
from utils import storage


class DmPage(BasePage):
    TITLE = "Templates de Atendimento"
    DESCRIPTION = (
        "Mensagens prontas para DM e WhatsApp: orcamento, agendamento, pos-cuidados e mais. "
        "Gere templates customizados com IA."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Tabs: Ver Templates | Gerar Customizado
        tabs = ctk.CTkTabview(
            parent,
            fg_color=theme.BLACK_CARD,
            segmented_button_fg_color=theme.BLACK_PANEL,
            segmented_button_selected_color=theme.RED_PRIMARY,
            segmented_button_selected_hover_color=theme.RED_HOVER,
            segmented_button_unselected_color=theme.BLACK_PANEL,
            segmented_button_unselected_hover_color=theme.BLACK_HOVER,
            text_color=theme.TEXT_PRIMARY,
        )
        tabs.pack(fill="both", expand=True)
        tabs.add("Templates Prontos")
        tabs.add("Gerar com IA")

        self._build_templates_tab(tabs.tab("Templates Prontos"))
        self._build_generate_tab(tabs.tab("Gerar com IA"))

    def _build_templates_tab(self, parent) -> None:
        from modules.dm_templates import BUILTIN_TEMPLATES

        custom = storage.load_dm_templates()
        all_t = {**BUILTIN_TEMPLATES, **custom}

        if not all_t:
            ctk.CTkLabel(
                parent, text="Nenhum template disponivel.",
                font=theme.FONT_BODY, text_color=theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=theme.RED_DEEP,
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        for key, tmpl in all_t.items():
            card = ctk.CTkFrame(
                scroll,
                fg_color=theme.BLACK_HOVER,
                corner_radius=6,
                border_color=theme.BLACK_BORDER,
                border_width=1,
            )
            card.pack(fill="x", pady=4, padx=4)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                header,
                text=tmpl.get("subject", key),
                font=theme.FONT_SUBHEADING,
                text_color=theme.RED_GLOW,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                header,
                text=f"{tmpl.get('category', '')} — {tmpl.get('channel', '')}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="e",
            ).pack(side="right")

            ctk.CTkLabel(
                card,
                text=tmpl.get("template", ""),
                font=theme.FONT_BODY,
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=880,
            ).pack(fill="x", padx=12, pady=(0, 8))

            def _copy(t=tmpl.get("template", "")):
                self.app.clipboard_clear()
                self.app.clipboard_append(t)

            ctk.CTkButton(
                card, text="Copiar",
                height=28, width=80,
                fg_color=theme.BLACK_CARD,
                hover_color=theme.RED_DEEP,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_SMALL,
                command=_copy,
            ).pack(anchor="e", padx=12, pady=(0, 10))

    def _build_generate_tab(self, parent) -> None:
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", pady=(8, 16))

        ctk.CTkLabel(
            form, text="CENARIO",
            font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
        ).pack(fill="x", padx=4, pady=(0, 4))

        self.scenario_entry = ctk.CTkTextbox(
            form, font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT, border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY, height=70, wrap="word",
        )
        self.scenario_entry.pack(fill="x", padx=4)
        self.scenario_entry.insert("1.0", "Ex: cliente pediu orcamento de tatuagem colorida mas eu faço só blackwork")

        ctk.CTkLabel(
            form, text="TOM",
            font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
        ).pack(fill="x", padx=4, pady=(12, 4))

        self.tone_var = ctk.StringVar(value="informal")
        tone_frame = ctk.CTkFrame(form, fg_color="transparent")
        tone_frame.pack(fill="x", padx=4)
        for val, lbl in [("informal", "Informal"), ("formal", "Formal"), ("artistico", "Artistico")]:
            ctk.CTkRadioButton(
                tone_frame, text=lbl, variable=self.tone_var, value=val,
                font=theme.FONT_BODY, text_color=theme.TEXT_PRIMARY,
                fg_color=theme.RED_PRIMARY, hover_color=theme.RED_HOVER,
            ).pack(side="left", padx=(0, 16))

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=4, pady=(12, 0))

        self.gen_btn = ctk.CTkButton(
            btns, text="▶  Gerar Template",
            height=40, fg_color=theme.RED_PRIMARY, hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY, font=theme.FONT_BODY_BOLD,
            command=self._generate,
        )
        self.gen_btn.pack(side="left")

        self.gen_status = ctk.CTkLabel(
            btns, text="", font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED, anchor="w",
        )
        self.gen_status.pack(side="left", padx=14, fill="x", expand=True)

        self.gen_result = ctk.CTkTextbox(
            parent, font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT, border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY, height=180, wrap="word",
            state="disabled",
        )
        self.gen_result.pack(fill="x", pady=(4, 0), padx=4)

        copy_btn = ctk.CTkButton(
            parent, text="Copiar Template Gerado",
            height=34, fg_color=theme.BLACK_HOVER, hover_color=theme.RED_DEEP,
            text_color=theme.TEXT_PRIMARY, font=theme.FONT_BODY,
            command=self._copy_generated,
        )
        copy_btn.pack(anchor="e", pady=(6, 0), padx=4)

    def _generate(self) -> None:
        scenario = self.scenario_entry.get("1.0", "end").strip()
        if not scenario or scenario.startswith("Ex:"):
            self.gen_status.configure(text="Descreva o cenario.", text_color=theme.TEXT_WARNING)
            return

        self._set_btn_loading(self.gen_btn, "Gerando...")
        self.gen_status.configure(text="IA criando template...", text_color=theme.TEXT_INFO)

        tone = self.tone_var.get()
        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._gen_flow(settings, scenario, tone),
            on_result=self._on_gen_done,
            on_error=lambda e: self.gen_status.configure(
                text=f"Erro: {e}", text_color=theme.TEXT_DANGER
            ),
            on_done=lambda: self._set_btn_ready(self.gen_btn, "▶  Gerar Template"),
        )

    async def _gen_flow(self, settings, scenario, tone):
        from modules.dm_templates import _build_custom_template_prompt
        from modules import ai_client

        tattoo_style = settings.get("tattoo_style", "blackwork")
        artist_name = settings.get("artist_name", "")
        artist_city = settings.get("artist_city", "")

        prompt = _build_custom_template_prompt(scenario, tone, tattoo_style, artist_name, artist_city)
        response = await ai_client.generate(prompt, settings, temperature=0.8)
        return response

    def _on_gen_done(self, response) -> None:
        if not response:
            self.gen_status.configure(text="Sem resposta.", text_color=theme.TEXT_WARNING)
            return
        self.gen_status.configure(text="Template gerado!", text_color=theme.TEXT_SUCCESS)
        self.gen_result.configure(state="normal")
        self.gen_result.delete("1.0", "end")
        self.gen_result.insert("1.0", response)
        self.gen_result.configure(state="disabled")
        self._last_generated = response

    def _copy_generated(self) -> None:
        text = getattr(self, "_last_generated", "")
        if text:
            self.app.clipboard_clear()
            self.app.clipboard_append(text)
