"""Pagina do Bio Optimizer."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard


class BioPage(BasePage):
    TITLE = "Bio Optimizer"
    DESCRIPTION = (
        "Analisa sua bio atual e gera 3 versoes otimizadas com palavras-chave, "
        "CTA e SEO local. Compara com perfis do nicho quando disponivel."
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
            form, text="SUA BIO ATUAL",
            font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        ctk.CTkLabel(
            form,
            text="Cole sua bio atual (ou deixe vazio se ainda nao tem)",
            font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=20)

        self.bio_entry = ctk.CTkTextbox(
            form, font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT, border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY, height=80, wrap="word",
        )
        self.bio_entry.pack(fill="x", padx=20, pady=(6, 14))

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns, text="▶  Otimizar Bio",
            height=40, fg_color=theme.RED_PRIMARY, hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY, font=theme.FONT_BODY_BOLD,
            command=self._start,
        )
        self.run_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            btns, text="", font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED, anchor="w",
        )
        self.status_label.pack(side="left", padx=14, fill="x", expand=True)

        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def _start(self) -> None:
        self._clear_results()
        self.run_btn.configure(state="disabled", text="Otimizando...")
        self.status_label.configure(
            text="IA analisando e gerando bios otimizadas...",
            text_color=theme.TEXT_INFO,
        )

        current_bio = self.bio_entry.get("1.0", "end").strip()
        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._bio_flow(settings, current_bio),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(state="normal", text="▶  Otimizar Bio"),
        )

    async def _bio_flow(self, settings, current_bio):
        from modules.bio_optimizer import _build_bio_prompt, _parse_bio_json
        from modules import ai_client
        from utils import storage

        tattoo_style = settings.get("tattoo_style", "blackwork")
        secondary_style = settings.get("tattoo_style_secondary", "")
        artist_city = settings.get("artist_city", "")
        artist_name = settings.get("artist_name", "")

        # Tenta pegar bios de concorrentes
        competitor_bios: list[str] = []
        competitors = storage.load_competitors()
        if competitors:
            from modules.scraper import get_profile_data
            for username in competitors[:3]:
                try:
                    data = await get_profile_data(username, settings.get("ollama_url", ""))
                    bio = data.get("bio", "")
                    if bio:
                        competitor_bios.append(bio[:200])
                except Exception:
                    pass

        prompt = _build_bio_prompt(
            current_bio, tattoo_style, artist_city, artist_name,
            secondary_style, competitor_bios,
        )
        response = await ai_client.generate(prompt, settings, temperature=0.85)
        if not response:
            raise RuntimeError("Nao foi possivel gerar as bios.")

        result = _parse_bio_json(response)
        if not result:
            return {"result": None, "raw": response, "current_bio": current_bio}

        # Salva historico
        variants = [v.get("bio", "") for v in result.get("variants", [])]
        storage.add_to_bio_history(variants, current_bio)

        return {"result": result, "raw": response, "current_bio": current_bio}

    def _on_done(self, data) -> None:
        result = data.get("result")

        if not result:
            self.status_label.configure(
                text="IA retornou formato inesperado.",
                text_color=theme.TEXT_WARNING,
            )
            InfoCard(
                self.results_frame, title="Resposta bruta",
                body=data.get("raw", ""), accent=theme.RED_PRIMARY,
            ).pack(fill="x", pady=6)
            return

        variants = result.get("variants", [])
        self.status_label.configure(
            text=f"{len(variants)} versoes de bio geradas.",
            text_color=theme.TEXT_SUCCESS,
        )

        # Analise
        analysis = result.get("analysis", "")
        if analysis:
            InfoCard(
                self.results_frame,
                title="Analise da Bio Atual",
                body=analysis,
                accent="#E6B800",
            ).pack(fill="x", pady=(0, 8))

        # Variantes
        for v in variants:
            bio_text = v.get("bio", "")
            focus = v.get("focus", "")
            char_count = len(bio_text)
            color = theme.TEXT_SUCCESS if char_count <= 150 else theme.TEXT_DANGER

            card = ctk.CTkFrame(
                self.results_frame,
                fg_color=theme.BLACK_CARD,
                corner_radius=theme.CARD_RADIUS,
                border_color=theme.RED_PRIMARY,
                border_width=1,
            )
            card.pack(fill="x", pady=4)

            ctk.CTkLabel(
                card,
                text=f"Versao {v.get('version', '')} — {focus}",
                font=theme.FONT_SUBHEADING,
                text_color=theme.RED_GLOW,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(12, 4))

            bio_box = ctk.CTkTextbox(
                card, font=theme.FONT_BODY,
                fg_color=theme.BLACK_SOFT,
                text_color=theme.TEXT_PRIMARY,
                height=60, wrap="word",
                state="normal",
            )
            bio_box.pack(fill="x", padx=16, pady=(0, 4))
            bio_box.insert("1.0", bio_text)
            bio_box.configure(state="disabled")

            footer = ctk.CTkFrame(card, fg_color="transparent")
            footer.pack(fill="x", padx=16, pady=(0, 10))

            ctk.CTkLabel(
                footer, text=f"{char_count} / 150 chars",
                font=theme.FONT_SMALL, text_color=color, anchor="w",
            ).pack(side="left")

            keywords = v.get("keywords", [])
            if keywords:
                ctk.CTkLabel(
                    footer,
                    text=f"Palavras-chave: {', '.join(keywords)}",
                    font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, anchor="w",
                ).pack(side="left", padx=12)

            def _copy(t=bio_text):
                self.app.clipboard_clear()
                self.app.clipboard_append(t)

            ctk.CTkButton(
                footer, text="Copiar",
                height=26, width=70,
                fg_color=theme.BLACK_HOVER, hover_color=theme.RED_DEEP,
                text_color=theme.TEXT_PRIMARY, font=theme.FONT_SMALL,
                command=_copy,
            ).pack(side="right")

        # Dicas extras
        cta_tip = result.get("cta_tip", "")
        emoji_tip = result.get("emoji_tip", "")
        if cta_tip:
            ctk.CTkLabel(
                self.results_frame,
                text=f"CTA sugerido: {cta_tip}",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_INFO,
                anchor="w", wraplength=900,
            ).pack(fill="x", pady=(8, 2))
        if emoji_tip:
            ctk.CTkLabel(
                self.results_frame,
                text=f"Emojis: {emoji_tip}",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_INFO,
                anchor="w", wraplength=900,
            ).pack(fill="x", pady=(0, 4))

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(text=f"Erro: {exc}", text_color=theme.TEXT_DANGER)
