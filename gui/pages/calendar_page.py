"""Pagina de Calendario de Conteudo."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard
from utils import storage


class CalendarPage(BasePage):
    TITLE = "Calendario de Conteudo"
    DESCRIPTION = (
        "Gera um plano de posts semanal ou mensal com formato, objetivo e dica de execucao. "
        "Exporta como CSV para planilha."
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
            form, text="PERIODO",
            font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        self.period_var = ctk.StringVar(value="1 semana")
        period_frame = ctk.CTkFrame(form, fg_color="transparent")
        period_frame.pack(fill="x", padx=20, pady=(0, 8))
        for p in ["1 semana", "2 semanas", "1 mes"]:
            ctk.CTkRadioButton(
                period_frame, text=p, variable=self.period_var, value=p,
                font=theme.FONT_BODY, text_color=theme.TEXT_PRIMARY,
                fg_color=theme.RED_PRIMARY, hover_color=theme.RED_HOVER,
            ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            form, text="POSTS POR SEMANA",
            font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
        ).pack(fill="x", padx=20, pady=(8, 4))

        self.posts_entry = ctk.CTkEntry(
            form, font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT, border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text="Ex: 4", height=34, width=120,
        )
        self.posts_entry.pack(anchor="w", padx=20, pady=(0, 14))
        self.posts_entry.insert(0, "4")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns, text="▶  Gerar Calendario",
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
        self.run_btn.configure(state="disabled", text="Gerando...")
        self.status_label.configure(
            text="IA montando calendario... ~30-60s.",
            text_color=theme.TEXT_INFO,
        )

        period = self.period_var.get()
        try:
            posts_per_week = int(self.posts_entry.get().strip() or "4")
        except ValueError:
            posts_per_week = 4
        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._calendar_flow(settings, period, posts_per_week),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(state="normal", text="▶  Gerar Calendario"),
        )

    async def _calendar_flow(self, settings, period, posts_per_week):
        from datetime import datetime
        from modules.content_calendar import _build_calendar_prompt, _parse_calendar_json
        from modules import ai_client

        now = datetime.now()
        tattoo_style = settings.get("tattoo_style", "blackwork")
        secondary_style = settings.get("tattoo_style_secondary", "")
        artist_city = settings.get("artist_city", "")

        prompt = _build_calendar_prompt(
            tattoo_style, artist_city, posts_per_week, period,
            now.month, now.year, secondary_style,
        )
        response = await ai_client.generate(prompt, settings, temperature=0.85)
        if not response:
            raise RuntimeError("Nao foi possivel gerar o calendario.")

        calendar = _parse_calendar_json(response)
        if not calendar:
            return {"calendar": None, "raw": response}

        storage.save_calendar(
            storage.load_calendar() + [{"generated_at": now.isoformat(), **calendar}]
        )
        return {"calendar": calendar, "raw": response}

    def _on_done(self, result) -> None:
        calendar = result.get("calendar")

        if not calendar:
            self.status_label.configure(
                text="IA retornou formato inesperado.",
                text_color=theme.TEXT_WARNING,
            )
            InfoCard(
                self.results_frame, title="Resposta bruta",
                body=result.get("raw", ""), accent=theme.RED_PRIMARY,
            ).pack(fill="x", pady=6)
            return

        posts = calendar.get("posts", [])
        self.status_label.configure(
            text=f"Calendario gerado: {len(posts)} posts.",
            text_color=theme.TEXT_SUCCESS,
        )

        FORMAT_COLORS = {
            "Reel": theme.RED_PRIMARY,
            "Carrossel": "#E6B800",
            "Story": theme.TEXT_INFO,
            "Post": theme.TEXT_PRIMARY,
        }

        # Renderiza posts em cards compactos
        for post in posts:
            fmt = post.get("format", "Post")
            color = FORMAT_COLORS.get(fmt, theme.TEXT_PRIMARY)

            card = ctk.CTkFrame(
                self.results_frame,
                fg_color=theme.BLACK_CARD,
                corner_radius=6,
                border_color=theme.BLACK_BORDER,
                border_width=1,
            )
            card.pack(fill="x", pady=3)
            card.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(
                card, text=f"Sem. {post.get('week', '')}",
                font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, width=55, anchor="w",
            ).grid(row=0, column=0, padx=(12, 4), pady=8, sticky="w")

            ctk.CTkLabel(
                card, text=post.get("day", ""),
                font=theme.FONT_BODY, text_color=theme.TEXT_SECONDARY, width=80, anchor="w",
            ).grid(row=0, column=1, padx=4, pady=8, sticky="w")

            ctk.CTkLabel(
                card, text=f"[{fmt}]",
                font=theme.FONT_SMALL, text_color=color, width=90, anchor="w",
            ).grid(row=0, column=2, padx=4, pady=8, sticky="w")

            ctk.CTkLabel(
                card, text=post.get("title", ""),
                font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_PRIMARY,
                anchor="w", wraplength=400,
            ).grid(row=0, column=3, padx=(4, 12), pady=8, sticky="w")

        # Export CSV hint
        if posts:
            ctk.CTkLabel(
                self.results_frame,
                text="Para exportar como CSV, use: python main.py calendar",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=(8, 0))

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(text=f"Erro: {exc}", text_color=theme.TEXT_DANGER)
