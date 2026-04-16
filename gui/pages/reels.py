"""Pagina do Assistente de Reels."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard
from utils import storage


class ReelsPage(BasePage):
    TITLE = "Assistente de Reels"
    DESCRIPTION = (
        "Gera roteiro completo para Reels: hook, cenas com timing, text overlays, trilha e hashtags. "
        "Opcional: monta slideshow (moviepy) ou gera clipe com IA generativa (Runway/Pika)."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Formulario de input
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
            text="DESCRICAO DO REEL",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        ctk.CTkLabel(
            form,
            text="Descreva o Reel que voce quer criar (1-2 frases)",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=20)

        self.desc_entry = ctk.CTkTextbox(
            form,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            height=70,
            wrap="word",
        )
        self.desc_entry.pack(fill="x", padx=20, pady=(6, 0))
        self.desc_entry.insert("1.0", "Ex: time-lapse da tatuagem geométrica no antebraço, processo completo de 4h")

        # Duracao
        ctk.CTkLabel(
            form,
            text="DURACAO ALVO",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        self.duration_var = ctk.StringVar(value="15-30 segundos")
        dur_frame = ctk.CTkFrame(form, fg_color="transparent")
        dur_frame.pack(fill="x", padx=20, pady=(0, 4))
        for dur in ["15-30 segundos", "30-60 segundos", "60-90 segundos"]:
            ctk.CTkRadioButton(
                dur_frame,
                text=dur,
                variable=self.duration_var,
                value=dur,
                font=theme.FONT_BODY,
                text_color=theme.TEXT_PRIMARY,
                fg_color=theme.RED_PRIMARY,
                hover_color=theme.RED_HOVER,
            ).pack(side="left", padx=(0, 16))

        # Modo de geracao
        ctk.CTkLabel(
            form,
            text="MODO DE GERACAO",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        self.mode_var = ctk.StringVar(value="script")
        modes = [
            ("script", "Apenas roteiro (recomendado)"),
            ("video", "Roteiro + slideshow basico (requer moviepy)"),
            ("ai", "Roteiro + IA generativa de video (requer API Runway/Pika)"),
        ]
        mode_frame = ctk.CTkFrame(form, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=(0, 14))
        for value, label in modes:
            ctk.CTkRadioButton(
                mode_frame,
                text=label,
                variable=self.mode_var,
                value=value,
                font=theme.FONT_BODY,
                text_color=theme.TEXT_PRIMARY,
                fg_color=theme.RED_PRIMARY,
                hover_color=theme.RED_HOVER,
            ).pack(anchor="w", pady=2)

        # Botoes
        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns,
            text="▶  Gerar Roteiro",
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
        desc = self.desc_entry.get("1.0", "end").strip()
        if not desc or desc.startswith("Ex:"):
            self.status_label.configure(
                text="Informe a descricao do Reel.",
                text_color=theme.TEXT_WARNING,
            )
            return

        self._clear_results()
        self.run_btn.configure(state="disabled", text="Gerando...")
        self.status_label.configure(
            text="IA criando roteiro completo... ~30-60s.",
            text_color=theme.TEXT_INFO,
        )

        duration = self.duration_var.get()
        mode = self.mode_var.get()
        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._reels_flow(settings, desc, duration, mode),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(
                state="normal", text="▶  Gerar Roteiro"
            ),
        )

    async def _reels_flow(self, settings, description, duration, mode):
        from modules.reels_assistant import _build_script_prompt, _parse_reel_json
        from modules import ai_client
        from utils import storage

        tattoo_style = settings.get("tattoo_style", "blackwork")
        artist_city = settings.get("artist_city", "")

        prompt = _build_script_prompt(description, tattoo_style, artist_city, duration)
        response = await ai_client.generate(prompt, settings, temperature=0.85, top_p=0.95)

        if not response:
            raise RuntimeError("Nao foi possivel gerar o roteiro. Verifique a IA configurada.")

        reel = _parse_reel_json(response)
        if not reel:
            return {"reel": None, "raw": response, "mode": mode}

        # Salva JSON
        saved_path = storage.save_reel(reel)
        reel["_saved_path"] = saved_path

        return {"reel": reel, "raw": response, "mode": mode}

    def _on_done(self, result) -> None:
        reel = result.get("reel")
        mode = result.get("mode", "script")

        if not reel:
            self.status_label.configure(
                text="IA retornou formato inesperado. Exibindo resposta bruta.",
                text_color=theme.TEXT_WARNING,
            )
            InfoCard(
                self.results_frame,
                title="Resposta bruta da IA",
                body=result.get("raw", ""),
                accent=theme.RED_PRIMARY,
            ).pack(fill="x", pady=6)
            return

        self.status_label.configure(
            text=f"Roteiro gerado! {len(reel.get('scenes', []))} cenas. Salvo em data/reels/",
            text_color=theme.TEXT_SUCCESS,
        )

        self._render_reel(reel)

        if mode in ("video", "ai"):
            InfoCard(
                self.results_frame,
                title="Geracao de Video",
                body=(
                    "Para gerar o video, use o comando CLI:\n"
                    f"  python main.py reels {mode}\n\n"
                    "A geracao de video requer moviepy (modo 'video') ou "
                    "API de video configurada (modo 'ai') e e feita no terminal."
                ),
                accent=theme.RED_DEEP,
            ).pack(fill="x", pady=6)

    def _render_reel(self, reel: dict) -> None:
        """Renderiza o roteiro em cards na GUI."""
        # Hook e metadados
        meta_card = ctk.CTkFrame(
            self.results_frame,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.RED_PRIMARY,
            border_width=1,
        )
        meta_card.pack(fill="x", pady=(0, 8))

        title = reel.get("title", "Reel")
        ctk.CTkLabel(
            meta_card,
            text=title,
            font=theme.FONT_TITLE,
            text_color=theme.RED_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 4))

        for label, key in [
            ("Hook (0-3s)", "hook"),
            ("Duracao", "duration_estimate"),
            ("Musica", "music_mood"),
            ("CTA", "cta"),
        ]:
            val = reel.get(key, "")
            if val:
                row = ctk.CTkFrame(meta_card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=2)
                ctk.CTkLabel(
                    row, text=f"{label}:", font=theme.FONT_SMALL,
                    text_color=theme.RED_GLOW, width=110, anchor="w",
                ).pack(side="left")
                ctk.CTkLabel(
                    row, text=val, font=theme.FONT_BODY,
                    text_color=theme.TEXT_PRIMARY, anchor="w", wraplength=750,
                ).pack(side="left", fill="x", expand=True)
        ctk.CTkFrame(meta_card, fg_color="transparent", height=8).pack()

        # Cenas
        scenes = reel.get("scenes", [])
        if scenes:
            scenes_header = ctk.CTkLabel(
                self.results_frame,
                text="CENAS",
                font=theme.FONT_SUBHEADING,
                text_color=theme.RED_GLOW,
                anchor="w",
            )
            scenes_header.pack(fill="x", pady=(8, 4))

            for scene in scenes:
                scene_card = ctk.CTkFrame(
                    self.results_frame,
                    fg_color=theme.BLACK_HOVER,
                    corner_radius=6,
                )
                scene_card.pack(fill="x", pady=3)
                scene_card.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    scene_card,
                    text=f"Cena {scene.get('scene_number', '')}",
                    font=theme.FONT_SMALL,
                    text_color=theme.RED_GLOW,
                    width=70,
                    anchor="w",
                ).grid(row=0, column=0, padx=(10, 6), pady=(8, 2), sticky="nw")

                info_frame = ctk.CTkFrame(scene_card, fg_color="transparent")
                info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(6, 8))
                info_frame.grid_columnconfigure(0, weight=1)

                timing = scene.get("timing", "")
                if timing:
                    ctk.CTkLabel(
                        info_frame, text=f"[{timing}]",
                        font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, anchor="w",
                    ).grid(row=0, column=0, sticky="w")

                for r, (lbl, skey) in enumerate([
                    ("Visual:", "visual"),
                    ("Voz:", "voiceover"),
                    ("Texto:", "text_overlay"),
                ], start=1):
                    val = scene.get(skey, "")
                    if val:
                        ctk.CTkLabel(
                            info_frame,
                            text=f"{lbl} {val}",
                            font=theme.FONT_BODY,
                            text_color=theme.TEXT_PRIMARY if lbl == "Visual:" else theme.TEXT_SECONDARY,
                            anchor="w",
                            wraplength=700,
                            justify="left",
                        ).grid(row=r, column=0, sticky="w")

        # Legenda
        caption = reel.get("caption", "")
        if caption:
            InfoCard(
                self.results_frame,
                title="Legenda do Post",
                body=caption,
                accent=theme.RED_DEEP,
            ).pack(fill="x", pady=(8, 4))

        # Hashtags
        hashtags = reel.get("hashtags", [])
        if hashtags:
            tags_text = "  ".join(f"#{h.lstrip('#')}" for h in hashtags)
            InfoCard(
                self.results_frame,
                title=f"Hashtags ({len(hashtags)})",
                body=tags_text,
                accent=theme.BLACK_BORDER,
            ).pack(fill="x", pady=4)

        # Salvo
        saved = reel.get("_saved_path", "")
        if saved:
            ctk.CTkLabel(
                self.results_frame,
                text=f"Salvo em: {saved}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=(4, 0))

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(
            text=f"Erro: {exc}",
            text_color=theme.TEXT_DANGER,
        )
