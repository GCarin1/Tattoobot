"""Pagina de Engajamento Diario - gera lista de perfis + comentarios IA."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import ProfileCard, InfoCard
from utils import storage


class EngagementPage(BasePage):
    TITLE = "Engajamento Diario"
    DESCRIPTION = (
        "Busca perfis reais em hashtags configuradas, evita repetidos e gera "
        "comentarios unicos via IA. Depois e so abrir o Instagram no celular "
        "e engajar manualmente."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Barra de controle
        control = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        control.pack(fill="x", pady=(0, 16))

        inner = ctk.CTkFrame(control, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        self.info_label = ctk.CTkLabel(
            inner,
            text="Pronto para buscar perfis das suas hashtags configuradas.",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=700,
        )
        self.info_label.pack(side="left", fill="x", expand=True)

        self.run_btn = ctk.CTkButton(
            inner,
            text="▶  Buscar Perfis",
            height=40,
            width=180,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._start,
        )
        self.run_btn.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            control,
            height=4,
            fg_color=theme.BLACK_SOFT,
            progress_color=theme.RED_PRIMARY,
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 14))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            control,
            text="",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 10))

        # Frame para resultados (cards)
        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    # ─── Execucao ──────────────────────────────────────────────────────

    def _start(self) -> None:
        # Validacoes
        settings = self.app.settings
        hashtags = settings.get("hashtags", [])
        if not hashtags:
            self._show_error(
                "Nenhuma hashtag configurada. "
                "Va em Configuracoes e preencha o campo 'Hashtags'."
            )
            return

        self._clear_results()
        self.run_btn.configure(state="disabled", text="Buscando...")
        self.progress_bar.set(0)
        self.status_label.configure(
            text="Iniciando scraping das hashtags... isso pode levar ~1-3 minutos.",
            text_color=theme.TEXT_INFO,
        )

        self.run_async(
            coro_factory=lambda: self._engagement_flow(settings),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(
                state="normal", text="▶  Buscar Perfis"
            ),
        )

    async def _engagement_flow(self, settings: dict) -> list[dict]:
        """Fluxo completo de engajamento, reaproveitando helpers do modulo CLI."""
        from modules import scraper, ollama_client
        from modules.engagement import (
            _build_comment_prompt,
            _parse_comments,
            _is_generic_context,
        )

        scraper.reset_request_count()
        hashtags = settings.get("hashtags", [])
        profiles_per_day = int(settings.get("profiles_per_day", 10))
        delay = float(settings.get("scraping_delay_seconds", 3))
        tattoo_style = settings.get("tattoo_style", "blackwork")
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ollama_model", "llama3")

        already_suggested = storage.get_history_usernames()

        # Fase 1: Coleta posts
        all_posts: list[scraper.ScrapedPost] = []
        total_hashtags = len(hashtags)
        for i, hashtag in enumerate(hashtags):
            self._update_status(
                f"Coletando #{hashtag} ({i + 1}/{total_hashtags})...",
                progress=(i / max(total_hashtags, 1)) * 0.4,
            )
            posts = await scraper.scrape_hashtag_page(hashtag, delay)
            all_posts.extend(posts)

        if not all_posts:
            raise RuntimeError(
                "Nao foi possivel coletar posts. "
                "O Instagram pode estar bloqueando. Tente novamente em alguns minutos."
            )

        self._update_status(
            f"{len(all_posts)} posts coletados. Filtrando novos perfis...",
            progress=0.4,
        )

        # Fase 2: Filtra
        seen: set[str] = set()
        with_link: list[scraper.ScrapedPost] = []
        profile_only: list[scraper.ScrapedPost] = []
        for post in all_posts:
            u = post.username
            if (not u or u in already_suggested or u in seen
                    or scraper.is_likely_bot(u)):
                continue
            seen.add(u)
            if scraper.has_real_post_link(post):
                with_link.append(post)
            else:
                profile_only.append(post)

        selected = (with_link + profile_only)[:profiles_per_day]
        if not selected:
            raise RuntimeError(
                "Nenhum perfil novo encontrado. Todos ja foram sugeridos. "
                "Adicione mais hashtags ou aguarde novos posts."
            )

        # Fase 3: Gera comentarios
        total = len(selected)
        session_history: list[str] = []
        profiles_out: list[dict] = []

        for idx, post in enumerate(selected):
            base_progress = 0.4 + (idx / total) * 0.6
            self._update_status(
                f"Gerando comentarios IA para @{post.username} ({idx + 1}/{total})...",
                progress=base_progress,
            )

            # Enriquecimento
            needs = (
                not scraper.has_real_post_link(post)
                or _is_generic_context(post.caption or post.alt_text, post.username)
            )
            if needs:
                latest = await scraper.fetch_latest_post_for_profile(post.username, delay)
                if latest:
                    if scraper.has_real_post_link(latest):
                        post.shortcode = latest.shortcode
                        post.link = latest.link
                    if (latest.alt_text
                            and not _is_generic_context(latest.alt_text, post.username)):
                        post.alt_text = latest.alt_text
                    elif (latest.caption
                          and not _is_generic_context(latest.caption, post.username)):
                        post.caption = latest.caption

            parts: list[str] = []
            if post.alt_text and not _is_generic_context(post.alt_text, post.username):
                parts.append(post.alt_text)
            if post.caption and not _is_generic_context(post.caption, post.username):
                parts.append(post.caption)

            if not parts:
                context = (
                    "Perfil de tatuador. Sem contexto especifico do post disponivel. "
                    "Gere comentarios neutros que funcionariam para um post de tattoo "
                    "em geral (sem citar cores, formas ou detalhes especificos)."
                )
            else:
                context = " | ".join(parts)[:500]

            prompt = _build_comment_prompt(
                tattoo_style=tattoo_style,
                post_context=context,
                username=post.username,
                session_history=session_history,
            )
            response = await ollama_client.generate(
                prompt, ollama_url, ollama_model,
                temperature=1.0, top_p=0.95,
            )
            if response:
                comments = _parse_comments(response)
            else:
                comments = [
                    "Ficou incrivel esse trabalho!",
                    "Que nivel de detalhe, parabens",
                    "Resultado muito limpo",
                ]
            if not comments:
                comments = ["(IA nao retornou comentarios - verifique modelo)"]
            session_history.extend(comments)

            post_link = post.link or f"https://www.instagram.com/{post.username}/"
            profiles_out.append({
                "username": post.username,
                "link": post_link,
                "context": context,
                "comments": comments,
            })

        # Fase 4: Salva historico
        storage.add_to_history([
            {"username": p["username"], "link": p["link"], "context": p["context"][:100]}
            for p in profiles_out
        ])

        self._update_status("Concluido!", progress=1.0)
        return profiles_out

    # ─── UI updates ────────────────────────────────────────────────────

    def _update_status(self, text: str, progress: float | None = None) -> None:
        """Chamado da thread da coroutine - usa after() pra seguranca."""
        def _do():
            self.status_label.configure(
                text=text,
                text_color=theme.TEXT_INFO,
            )
            if progress is not None:
                self.progress_bar.set(max(0.0, min(1.0, progress)))
        try:
            self.app.after(0, _do)
        except Exception:  # noqa: BLE001
            pass

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_done(self, profiles: list[dict]) -> None:
        self.status_label.configure(
            text=f"{len(profiles)} perfil(s) sugerido(s) - abra o Instagram no celular!",
            text_color=theme.TEXT_SUCCESS,
        )
        today = datetime.now().strftime("%d/%m/%Y")

        header = InfoCard(
            self.results_frame,
            title=f"Engajamento de {today}",
            body=(
                f"{len(profiles)} perfis selecionados. Tempo estimado: "
                f"~{len(profiles) * 2} minutos engajando manualmente."
            ),
            accent=theme.RED_PRIMARY,
        )
        header.pack(fill="x", pady=(0, 12))

        for p in profiles:
            card = ProfileCard(
                self.results_frame,
                username=p["username"],
                link=p["link"],
                context=p["context"],
                comments=p["comments"],
                on_copy=self._copy_to_clipboard,
                on_open=self._open_link,
            )
            card.pack(fill="x", pady=6)

    def _on_error(self, exc: Exception) -> None:
        self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        self.status_label.configure(
            text=f"Erro: {message}",
            text_color=theme.TEXT_DANGER,
        )

    def _copy_to_clipboard(self, text: str) -> None:
        self.app.clipboard_clear()
        self.app.clipboard_append(text)
        self.status_label.configure(
            text="Comentario copiado para a area de transferencia.",
            text_color=theme.TEXT_SUCCESS,
        )

    def _open_link(self, url: str) -> None:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
