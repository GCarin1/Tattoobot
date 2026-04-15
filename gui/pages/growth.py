"""Pagina de Growth Tracker - log/show/export."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import StatsCard, InfoCard
from utils import storage


class GrowthPage(BasePage):
    TITLE = "Growth Tracker"
    DESCRIPTION = (
        "Registre metricas semanais e acompanhe sua evolucao. "
        "A IA sugere ajustes de estrategia com base nos dados."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Form de log
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
            text="REGISTRAR METRICAS DE HOJE",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 10))

        self._fields = {}
        specs = [
            ("followers", "Seguidores (obrigatorio)", "Ex: 1250"),
            ("reach", "Alcance semanal", "Opcional - ex: 8500"),
            ("engagement", "Engajamento medio %", "Opcional - ex: 4.2"),
            ("bookings", "Novos agendamentos", "Opcional - ex: 3"),
            ("notes", "Observacoes", "Opcional - ex: fiz flash day dia 10"),
        ]
        for key, label, placeholder in specs:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row,
                text=label,
                font=theme.FONT_BODY_BOLD,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                width=220,
            ).grid(row=0, column=0, sticky="w", padx=(0, 12))
            entry = ctk.CTkEntry(
                row,
                font=theme.FONT_BODY,
                fg_color=theme.BLACK_SOFT,
                border_color=theme.BLACK_BORDER,
                text_color=theme.TEXT_PRIMARY,
                placeholder_text=placeholder,
                height=34,
            )
            entry.grid(row=0, column=1, sticky="ew")
            self._fields[key] = entry

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(12, 16))

        ctk.CTkButton(
            btns,
            text="Registrar",
            height=38,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
            font=theme.FONT_BODY_BOLD,
            command=self._save,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns,
            text="Gerar Analise IA",
            height=38,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.RED_DEEP,
            font=theme.FONT_BODY,
            command=self._analyze,
        ).pack(side="left", padx=8)

        self.action_status = ctk.CTkLabel(
            btns,
            text="",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.action_status.pack(side="left", padx=14, fill="x", expand=True)

        # Stats + historico
        self.stats_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.stats_container.pack(fill="x", pady=(0, 10))

        self.history_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.history_container.pack(fill="both", expand=True)

        self._render_history()

    def on_show(self) -> None:
        self._render_history()

    # ─── Save ──────────────────────────────────────────────────────────

    def _save(self) -> None:
        followers_str = self._fields["followers"].get().strip()
        if not followers_str:
            self.action_status.configure(
                text="Numero de seguidores e obrigatorio.",
                text_color=theme.TEXT_DANGER,
            )
            return
        try:
            followers = int(followers_str.replace(".", "").replace(",", ""))
        except ValueError:
            self.action_status.configure(
                text="Seguidores deve ser numero inteiro.",
                text_color=theme.TEXT_DANGER,
            )
            return

        def _int_or(val, default=0):
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        def _float_or(val, default=0.0):
            try:
                return float(str(val).replace(",", "."))
            except (ValueError, TypeError):
                return default

        entry = {
            "date": datetime.now().strftime("%d/%m/%Y"),
            "timestamp": datetime.now().isoformat(),
            "followers": followers,
            "reach": _int_or(self._fields["reach"].get().strip(), 0),
            "engagement": _float_or(self._fields["engagement"].get().strip(), 0.0),
            "bookings": _int_or(self._fields["bookings"].get().strip(), 0),
            "notes": self._fields["notes"].get().strip(),
        }

        growth = storage.load_growth()
        growth.append(entry)
        storage.save_growth(growth)

        # Limpa campos
        for k in ["reach", "engagement", "bookings", "notes"]:
            self._fields[k].delete(0, "end")
        self._fields["followers"].delete(0, "end")

        msg = f"Registrado! Seguidores: {followers:,}"
        if len(growth) >= 2:
            diff = followers - growth[-2]["followers"]
            sign = "+" if diff >= 0 else ""
            msg += f" ({sign}{diff} desde ultimo)"

        self.action_status.configure(
            text=msg,
            text_color=theme.TEXT_SUCCESS,
        )
        self._render_history()

    # ─── History ───────────────────────────────────────────────────────

    def _render_history(self) -> None:
        for w in self.stats_container.winfo_children():
            w.destroy()
        for w in self.history_container.winfo_children():
            w.destroy()

        growth = storage.load_growth()
        if not growth:
            ctk.CTkLabel(
                self.history_container,
                text="Nenhum registro ainda. Preencha os campos acima e clique em Registrar.",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=10)
            return

        # Stats cards
        first = growth[0]
        last = growth[-1]
        total_diff = last["followers"] - first["followers"]
        total_pct = (total_diff / first["followers"] * 100) if first["followers"] else 0
        weekly_diff = 0
        if len(growth) >= 7:
            last_7 = growth[-7:]
            weekly_diff = last_7[-1]["followers"] - last_7[0]["followers"]

        for i in range(4):
            self.stats_container.grid_columnconfigure(i, weight=1, uniform="gs")

        specs = [
            ("Registros", f"{len(growth)}", "entradas salvas"),
            ("Seguidores", f"{last['followers']:,}".replace(",", "."), f"em {last['date']}"),
            ("Variacao Total", f"{'+' if total_diff >= 0 else ''}{total_diff:,}".replace(",", "."),
             f"{'+' if total_pct >= 0 else ''}{total_pct:.1f}%"),
            ("Ultima Semana", f"{'+' if weekly_diff >= 0 else ''}{weekly_diff}".replace(",", "."),
             "seguidores em 7 registros" if len(growth) >= 7 else "precisa 7+ registros"),
        ]
        for col, (label, value, sub) in enumerate(specs):
            card = StatsCard(
                self.stats_container,
                label=label,
                value=value,
                subtitle=sub,
                accent=theme.RED_PRIMARY,
            )
            card.grid(row=0, column=col, sticky="nsew", padx=6, pady=0)

        # Historico em lista compacta
        history_card = ctk.CTkFrame(
            self.history_container,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        history_card.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            history_card,
            text="HISTORICO (mais recentes primeiro)",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 8))

        # Header
        head = ctk.CTkFrame(history_card, fg_color=theme.BLACK_SOFT, corner_radius=6)
        head.pack(fill="x", padx=20, pady=2)
        for i, (txt, w) in enumerate([("Data", 120), ("Seguidores", 140),
                                       ("Alcance", 120), ("Eng.%", 90),
                                       ("Agend.", 80), ("Variacao", 100)]):
            ctk.CTkLabel(
                head,
                text=txt,
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                width=w,
                anchor="w",
            ).grid(row=0, column=i, sticky="w", padx=6, pady=4)
        ctk.CTkLabel(
            head,
            text="Obs.",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=6, sticky="ew", padx=6, pady=4)
        head.grid_columnconfigure(6, weight=1)

        entries = list(reversed(growth[-30:]))
        for i, entry in enumerate(entries):
            row = ctk.CTkFrame(history_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=1)
            row.grid_columnconfigure(6, weight=1)

            # Calcular variacao
            idx_in_growth = len(growth) - 1 - i
            diff = ""
            if idx_in_growth > 0:
                d = growth[idx_in_growth]["followers"] - growth[idx_in_growth - 1]["followers"]
                diff = f"{'+' if d >= 0 else ''}{d}"

            values = [
                (entry["date"], 120, theme.TEXT_PRIMARY),
                (f"{entry['followers']:,}".replace(",", "."), 140, theme.TEXT_SUCCESS),
                (f"{entry.get('reach', 0):,}".replace(",", ".") if entry.get("reach") else "—", 120, theme.TEXT_PRIMARY),
                (f"{entry.get('engagement', 0):.1f}%" if entry.get("engagement") else "—", 90, theme.TEXT_PRIMARY),
                (str(entry.get("bookings", 0)) if entry.get("bookings") else "—", 80, theme.TEXT_PRIMARY),
                (diff or "—", 100, theme.TEXT_WARNING if diff.startswith("-") else theme.TEXT_SUCCESS),
            ]
            for col, (txt, w, color) in enumerate(values):
                ctk.CTkLabel(
                    row,
                    text=txt,
                    font=theme.FONT_BODY,
                    text_color=color,
                    width=w,
                    anchor="w",
                ).grid(row=0, column=col, sticky="w", padx=6, pady=2)
            notes = entry.get("notes", "")[:80]
            ctk.CTkLabel(
                row,
                text=notes,
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).grid(row=0, column=6, sticky="ew", padx=6, pady=2)

        ctk.CTkFrame(history_card, fg_color="transparent", height=12).pack()

    # ─── Analise IA ────────────────────────────────────────────────────

    def _analyze(self) -> None:
        growth = storage.load_growth()
        if len(growth) < 3:
            self.action_status.configure(
                text="Precisa de pelo menos 3 registros para gerar analise IA.",
                text_color=theme.TEXT_WARNING,
            )
            return

        self.action_status.configure(
            text="Gerando analise com IA...",
            text_color=theme.TEXT_INFO,
        )
        settings = self.app.settings

        async def _run():
            from modules import ollama_client

            ollama_url = settings.get("ollama_url", "http://localhost:11434")
            ollama_model = settings.get("ollama_model", "llama3")

            recent = growth[-7:] if len(growth) >= 7 else growth[-3:]
            summary = ", ".join(
                f"{e['date']}: {e['followers']} seg"
                + (f" (nota: {e.get('notes', '')})" if e.get("notes") else "")
                for e in recent
            )
            prompt = (
                f"Voce e um analista de crescimento no Instagram.\n"
                f"Dados recentes do perfil de um tatuador:\n{summary}\n\n"
                f"Em 3-4 frases, analise a tendencia e de 2 dicas praticas "
                f"para melhorar o crescimento. Responda em portugues brasileiro."
            )
            return await ollama_client.generate(prompt, ollama_url, ollama_model)

        def on_result(analysis):
            if not analysis:
                self.action_status.configure(
                    text="IA indisponivel. Verifique o Ollama.",
                    text_color=theme.TEXT_DANGER,
                )
                return
            self.action_status.configure(
                text="Analise gerada abaixo.",
                text_color=theme.TEXT_SUCCESS,
            )
            # Remove analises anteriores
            for w in self.stats_container.master.winfo_children():
                if getattr(w, "_is_analysis", False):
                    w.destroy()

            # Pega o parent do stats_container (= body da pagina)
            body = self.stats_container.master
            card = InfoCard(
                body,
                title="Analise IA",
                body=analysis,
                accent=theme.RED_GLOW,
            )
            card._is_analysis = True
            # Posiciona a analise logo apos os stats, antes do historico
            card.pack(fill="x", pady=(0, 10), before=self.history_container)

        self.run_async(
            coro_factory=lambda: _run(),
            on_result=on_result,
            on_error=lambda e: self.action_status.configure(
                text=f"Erro: {e}", text_color=theme.TEXT_DANGER,
            ),
        )
