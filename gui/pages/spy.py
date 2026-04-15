"""Pagina de Spy de Concorrentes - add/remove/list/report."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import SpyCard, InfoCard
from utils import storage


class SpyPage(BasePage):
    TITLE = "Spy de Rivais"
    DESCRIPTION = (
        "Monitore tatuadores de referencia. A IA analisa bio, seguidores "
        "e posts publicos pra gerar insights de estrategia."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Add/remove box
        control = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        control.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            control,
            text="GERENCIAR LISTA",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 8))

        row = ctk.CTkFrame(control, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 10))

        self.username_entry = ctk.CTkEntry(
            row,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text="@username do concorrente",
            height=36,
        )
        self.username_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Adicionar",
            height=36,
            width=100,
            fg_color=theme.RED_DEEP,
            hover_color=theme.RED_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._add,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            row,
            text="Remover",
            height=36,
            width=100,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.RED_DEEP,
            font=theme.FONT_BODY,
            command=self._remove,
        ).pack(side="left", padx=4)

        self.action_status = ctk.CTkLabel(
            control,
            text="",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.action_status.pack(fill="x", padx=20, pady=(0, 10))

        # Lista atual + botao gerar relatorio
        list_frame = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        list_frame.pack(fill="x", pady=(0, 16))

        list_header = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=20, pady=(14, 6))

        ctk.CTkLabel(
            list_header,
            text="CONCORRENTES MONITORADOS",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        self.run_btn = ctk.CTkButton(
            list_header,
            text="▶  Gerar Relatorio",
            height=36,
            width=170,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._start_report,
        )
        self.run_btn.pack(side="right")

        self.list_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        self.list_container.pack(fill="x", padx=20, pady=(4, 14))

        self.report_status = ctk.CTkLabel(
            list_frame,
            text="",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.report_status.pack(fill="x", padx=20, pady=(0, 10))

        # Results
        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

        self._refresh_list()

    def on_show(self) -> None:
        self._refresh_list()

    # ─── Lista ─────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        for w in self.list_container.winfo_children():
            w.destroy()
        competitors = storage.load_competitors()
        if not competitors:
            ctk.CTkLabel(
                self.list_container,
                text="Nenhum concorrente na lista. Adicione um acima.",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=4)
            return

        for c in competitors:
            item = ctk.CTkFrame(
                self.list_container,
                fg_color=theme.BLACK_SOFT,
                corner_radius=6,
            )
            item.pack(fill="x", pady=2)
            ctk.CTkLabel(
                item,
                text=f"  @{c}",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=8, pady=6)

    def _add(self) -> None:
        username = self.username_entry.get().strip().lstrip("@")
        if not username:
            self.action_status.configure(
                text="Digite um username.",
                text_color=theme.TEXT_DANGER,
            )
            return
        competitors = storage.load_competitors()
        if username in competitors:
            self.action_status.configure(
                text=f"@{username} ja esta na lista.",
                text_color=theme.TEXT_WARNING,
            )
            return
        competitors.append(username)
        storage.save_competitors(competitors)
        self.username_entry.delete(0, "end")
        self.action_status.configure(
            text=f"@{username} adicionado.",
            text_color=theme.TEXT_SUCCESS,
        )
        self._refresh_list()

    def _remove(self) -> None:
        username = self.username_entry.get().strip().lstrip("@")
        if not username:
            self.action_status.configure(
                text="Digite o username a remover.",
                text_color=theme.TEXT_DANGER,
            )
            return
        competitors = storage.load_competitors()
        if username not in competitors:
            self.action_status.configure(
                text=f"@{username} nao esta na lista.",
                text_color=theme.TEXT_WARNING,
            )
            return
        competitors.remove(username)
        storage.save_competitors(competitors)
        self.username_entry.delete(0, "end")
        self.action_status.configure(
            text=f"@{username} removido.",
            text_color=theme.TEXT_SUCCESS,
        )
        self._refresh_list()

    # ─── Relatorio ─────────────────────────────────────────────────────

    def _start_report(self) -> None:
        competitors = storage.load_competitors()
        if not competitors:
            self.report_status.configure(
                text="Adicione pelo menos um concorrente antes de gerar relatorio.",
                text_color=theme.TEXT_DANGER,
            )
            return

        self._clear_results()
        self.run_btn.configure(state="disabled", text="Analisando...")
        self.report_status.configure(
            text=(
                f"Coletando dados e analisando {len(competitors)} perfil(s). "
                f"Isso leva ~{len(competitors) * 30} segundos."
            ),
            text_color=theme.TEXT_INFO,
        )

        settings = self.app.settings
        self.run_async(
            coro_factory=lambda: self._report_flow(settings, competitors),
            on_result=self._on_report_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(
                state="normal", text="▶  Gerar Relatorio"
            ),
        )

    async def _report_flow(self, settings, competitors):
        import httpx
        from modules import ollama_client, scraper
        from modules.competitor_spy import _build_spy_prompt, _collect_web_info

        scraper.reset_request_count()
        delay = float(settings.get("scraping_delay_seconds", 3))
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ollama_model", "llama3")

        results: list[dict] = []
        total = len(competitors)

        for idx, username in enumerate(competitors):
            self._update_status(
                f"Coletando @{username} ({idx + 1}/{total})...",
            )
            profile = await scraper.scrape_profile_page(username, delay)

            async with httpx.AsyncClient(timeout=15) as client:
                extra_info = await _collect_web_info(client, username, delay)

            stats_lines: list[str] = []
            if profile.followers:
                stats_lines.append(f"Seguidores: {profile.followers:,}")
            if profile.post_count:
                stats_lines.append(f"Total de posts: {profile.post_count}")
            if profile.posts:
                stats_lines.append(f"Posts coletados: {len(profile.posts)}")
            if profile.bio:
                stats_lines.append(f"Bio: {profile.bio[:200]}")

            recent_captions = [
                p.alt_text or p.caption
                for p in profile.posts[:5]
                if p.alt_text or p.caption
            ]

            self._update_status(f"Analisando @{username} com IA...")
            prompt = _build_spy_prompt(
                username, profile.bio, profile.post_count,
                profile.followers, recent_captions, extra_info,
            )
            analysis = await ollama_client.generate(prompt, ollama_url, ollama_model)
            if not analysis:
                analysis = "Analise IA indisponivel. Verifique se o Ollama esta rodando."

            results.append({
                "username": username,
                "stats_lines": stats_lines or ["Dados limitados coletados."],
                "analysis": analysis,
            })

        return results

    def _update_status(self, text: str) -> None:
        def _do():
            self.report_status.configure(text=text, text_color=theme.TEXT_INFO)
        try:
            self.app.after(0, _do)
        except Exception:  # noqa: BLE001
            pass

    def _on_report_done(self, results: list[dict]) -> None:
        self.report_status.configure(
            text=f"{len(results)} analise(s) concluida(s).",
            text_color=theme.TEXT_SUCCESS,
        )
        for r in results:
            SpyCard(
                self.results_frame,
                username=r["username"],
                stats_lines=r["stats_lines"],
                analysis=r["analysis"],
            ).pack(fill="x", pady=6)

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.report_status.configure(
            text=f"Erro: {exc}",
            text_color=theme.TEXT_DANGER,
        )
