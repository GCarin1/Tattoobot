"""Pagina de Comparador de Perfis."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard


class ComparePage(BasePage):
    TITLE = "Comparador de Perfis"
    DESCRIPTION = (
        "Compara seu perfil com um rival e gera um plano de acao concreto "
        "para voce supera-lo."
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
            text="USERNAMES PARA COMPARAR",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 8))

        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(0, 8))
        row1.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            row1,
            text="Seu perfil:",
            font=theme.FONT_BODY_BOLD,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            width=120,
        ).grid(row=0, column=0, sticky="w")
        self.me_entry = ctk.CTkEntry(
            row1,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            placeholder_text="@seu_user",
            height=34,
        )
        self.me_entry.grid(row=0, column=1, sticky="ew")

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(4, 14))
        row2.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            row2,
            text="Rival:",
            font=theme.FONT_BODY_BOLD,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            width=120,
        ).grid(row=0, column=0, sticky="w")
        self.rival_entry = ctk.CTkEntry(
            row2,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            placeholder_text="@rival",
            height=34,
        )
        self.rival_entry.grid(row=0, column=1, sticky="ew")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns,
            text="▶  Comparar",
            height=40,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
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

        # Pre-popula com artist_name
        suggested = self.app.settings.get("artist_name", "")
        if suggested:
            self.me_entry.insert(0, suggested)

        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def on_show(self) -> None:
        if not self.me_entry.get().strip():
            suggested = self.app.settings.get("artist_name", "")
            if suggested:
                self.me_entry.insert(0, suggested)

    def _start(self) -> None:
        me = self.me_entry.get().strip().lstrip("@")
        rival = self.rival_entry.get().strip().lstrip("@")
        if not me or not rival:
            self.status_label.configure(
                text="Preencha os dois usernames.",
                text_color=theme.TEXT_DANGER,
            )
            return
        if me.lower() == rival.lower():
            self.status_label.configure(
                text="Os perfis devem ser diferentes.",
                text_color=theme.TEXT_DANGER,
            )
            return

        self._clear_results()
        self._set_btn_loading(self.run_btn, "Analisando...")
        self.status_label.configure(
            text="Coletando dados dos dois perfis... ~1 minuto.",
            text_color=theme.TEXT_INFO,
        )

        settings = self.app.settings
        self.run_async(
            coro_factory=lambda: self._compare_flow(settings, me, rival),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self._set_btn_ready(self.run_btn, "▶  Comparar"),
        )

    async def _compare_flow(self, settings, me, rival):
        from modules import ollama_client, scraper
        from modules.profile_comparator import _build_comparison_prompt, _collect_profile_data

        scraper.reset_request_count()
        delay = float(settings.get("scraping_delay_seconds", 3))
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ollama_model", "llama3")

        self._update_status(f"Coletando @{me}...")
        my_profile, my_extra = await _collect_profile_data(me, delay)

        self._update_status(f"Coletando @{rival}...")
        rival_profile, rival_extra = await _collect_profile_data(rival, delay)

        self._update_status("Gerando analise comparativa com IA...")
        prompt = _build_comparison_prompt(
            me, my_profile, my_extra,
            rival, rival_profile, rival_extra,
        )
        analysis = await ollama_client.generate(prompt, ollama_url, ollama_model)
        if not analysis:
            raise RuntimeError(
                "Nao foi possivel gerar a analise. Verifique o Ollama."
            )

        return {
            "me": me,
            "rival": rival,
            "my_profile": my_profile,
            "rival_profile": rival_profile,
            "my_extra": my_extra,
            "rival_extra": rival_extra,
            "analysis": analysis,
        }

    def _update_status(self, text: str) -> None:
        def _do():
            self.status_label.configure(text=text, text_color=theme.TEXT_INFO)
        try:
            self.app.after(0, _do)
        except Exception:  # noqa: BLE001
            pass

    def _on_done(self, result) -> None:
        self.status_label.configure(
            text="Analise concluida.",
            text_color=theme.TEXT_SUCCESS,
        )

        def _fmt(username, profile, extra):
            parts = []
            if profile.bio:
                parts.append(f"Bio: {profile.bio[:200]}")
            if profile.followers:
                parts.append(f"Seguidores: {profile.followers:,}")
            if profile.post_count:
                parts.append(f"Posts: {profile.post_count}")
            if extra:
                parts.append(f"Infos web: {len(extra)}")
            if not parts:
                parts.append("Dados limitados (perfil pode ser privado).")
            return "\n".join(parts)

        # Dados coletados
        data_card = ctk.CTkFrame(
            self.results_frame,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.RED_DEEP,
            border_width=1,
        )
        data_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            data_card,
            text="DADOS COLETADOS",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

        cols = ctk.CTkFrame(data_card, fg_color="transparent")
        cols.pack(fill="x", padx=16, pady=(0, 14))
        cols.grid_columnconfigure(0, weight=1)
        cols.grid_columnconfigure(1, weight=1)

        for col, (username, profile, extra, label_color) in enumerate([
            (result["me"], result["my_profile"], result["my_extra"], theme.TEXT_INFO),
            (result["rival"], result["rival_profile"], result["rival_extra"], theme.TEXT_DANGER),
        ]):
            inner = ctk.CTkFrame(cols, fg_color=theme.BLACK_SOFT, corner_radius=6)
            inner.grid(row=0, column=col, sticky="nsew", padx=4)
            ctk.CTkLabel(
                inner,
                text=f"@{username}",
                font=theme.FONT_BODY_BOLD,
                text_color=label_color,
                anchor="w",
            ).pack(fill="x", padx=10, pady=(8, 4))
            ctk.CTkLabel(
                inner,
                text=_fmt(username, profile, extra),
                font=theme.FONT_BODY,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                justify="left",
                wraplength=440,
            ).pack(fill="x", padx=10, pady=(0, 10))

        # Analise
        InfoCard(
            self.results_frame,
            title=f"Analise Comparativa  (@{result['me']}  vs  @{result['rival']})",
            body=result["analysis"],
            accent=theme.RED_PRIMARY,
        ).pack(fill="x", pady=6)

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(text=f"Erro: {exc}", text_color=theme.TEXT_DANGER)
