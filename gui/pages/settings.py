"""Pagina de configuracoes."""

from __future__ import annotations

import tkinter.messagebox as messagebox

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from utils import storage


FIELD_SPECS = [
    # (key, label, widget_type, help_text, category)
    # Usuario / Perfil
    ("artist_name",          "Nome artistico",               "entry",       "Como voce assina o trabalho",               "usuario"),
    ("artist_city",          "Cidade",                       "entry",       "Para SEO em legendas",                       "usuario"),
    ("tattoo_style",         "Estilo principal",             "entry",       "Ex: blackwork, dotwork, realismo",           "usuario"),
    ("tattoo_style_secondary","Estilo secundario (opcional)","entry",       "Ex: aquarela, old school",                    "usuario"),
    ("hashtags",             "Hashtags (virgula)",           "list_entry",  "Ex: blackwork, tattoo, tatuagembr",           "usuario"),
    ("language",             "Idioma",                       "entry",       "Padrao: pt-br",                                "usuario"),
    # Aparencia
    ("theme_preset",         "Tema do app",                  "theme_select",     "Muda cores em tempo real.",              "aparencia"),
    ("window_resolution",    "Resolucao da janela",          "resolution_select","Tamanho padrao ao abrir o app.",         "aparencia"),
    # Scraping
    ("profiles_per_day",     "Perfis por dia",               "int_entry",   "Quantos perfis buscar por sessao",           "scraping"),
    ("scraping_delay_seconds","Delay entre requisicoes (s)", "int_entry",   "Recomendado 3-5s",                            "scraping"),
    # IA — Ollama
    ("ai_provider",          "Provider de IA",               "entry",       "ollama | openai | anthropic",                "ia"),
    ("ollama_url",           "URL do Ollama",                "entry",       "Padrao: http://localhost:11434",             "ia"),
    ("ollama_model",         "Modelo Ollama (texto)",        "entry",       "Ex: llama3, gemma2:27b-cloud",               "ia"),
    ("ollama_vision_model",  "Modelo Ollama (visao)",        "entry",       "Para Avaliar Tattoo. Ex: llava, gemma3",     "ia"),
    ("openai_api_key",       "OpenAI API Key",               "entry",       "sk-... (deixe vazio para usar Ollama)",       "ia"),
    ("openai_model",         "Modelo OpenAI",                "entry",       "Ex: gpt-4o-mini, gpt-4o",                     "ia"),
    ("anthropic_api_key",    "Anthropic API Key",            "entry",       "sk-ant-... (deixe vazio para usar Ollama)",   "ia"),
    ("anthropic_model",      "Modelo Anthropic",             "entry",       "Ex: claude-haiku-4-5-20251001",               "ia"),
    # Video
    ("video_api_provider",   "Provider de Video",            "entry",       "runway | pika (deixe vazio para desativar)", "video"),
    ("video_api_key",        "API Key de Video",             "entry",       "Chave do Runway ML ou Pika Labs",             "video"),
]


CATEGORIES = [
    ("usuario",   "Usuario"),
    ("aparencia", "Aparencia"),
    ("scraping",  "Scraping"),
    ("ia",        "IA"),
    ("video",     "Video"),
]


class SettingsPage(BasePage):
    TITLE = "Configuracoes"
    DESCRIPTION = (
        "Configure seu perfil, integracao de IA (Ollama/OpenAI/Anthropic) e APIs de video. "
        "Ollama e o padrao gratuito. OpenAI/Anthropic requerem chave de API paga."
    )
    ACCENT = theme.RED_PRIMARY

    def _build_scroll_area(self) -> None:
        # Substitui o scrollable frame padrao por um frame simples:
        # cada aba gerencia seu proprio scroll.
        self.body = ctk.CTkFrame(
            self,
            fg_color=theme.BLACK_SOFT,
            corner_radius=0,
        )
        self.body.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8, 0))

    def build_body(self, parent) -> None:
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._theme_combo: ctk.CTkOptionMenu | None = None
        self._theme_preset_ids: list[str] = []
        self._resolution_combo: ctk.CTkOptionMenu | None = None
        self._resolution_ids: list[str] = []

        tabs = ctk.CTkTabview(
            parent,
            fg_color=theme.BLACK_CARD,
            segmented_button_fg_color=theme.BLACK_PANEL,
            segmented_button_selected_color=theme.RED_PRIMARY,
            segmented_button_selected_hover_color=theme.RED_HOVER,
            segmented_button_unselected_color=theme.BLACK_PANEL,
            segmented_button_unselected_hover_color=theme.BLACK_HOVER,
            text_color=theme.TEXT_PRIMARY,
            text_color_disabled=theme.TEXT_MUTED,
            corner_radius=8,
        )
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        for cat_id, cat_label in CATEGORIES:
            tabs.add(cat_label)
            self._build_category_tab(tabs.tab(cat_label), cat_id)

        # Barra de acoes global (fora das abas, sempre visivel)
        actions_bar = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        actions_bar.pack(fill="x", padx=16, pady=(0, 16))

        btns = ctk.CTkFrame(actions_bar, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkButton(
            btns,
            text="Salvar Configuracoes",
            height=40,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._save,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns,
            text="Recarregar",
            height=40,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_BODY,
            command=self._reload,
        ).pack(side="left", padx=8)

        self.status_label = ctk.CTkLabel(
            actions_bar,
            text="",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self.status_label.pack(fill="x", padx=16, pady=(4, 12))

        # Popula com valores atuais
        self._load_values()

    def _build_category_tab(self, parent: ctk.CTkFrame, category: str) -> None:
        scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color=theme.BLACK_HOVER,
            scrollbar_button_hover_color=theme.RED_DEEP,
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        for key, label, wtype, helptext, cat in FIELD_SPECS:
            if cat != category:
                continue
            self._build_field_row(scroll, key, label, wtype, helptext)

        # Extras especificos da aba IA
        if category == "ia":
            self._build_ia_extras(scroll)

    def _build_field_row(self, parent, key: str, label: str, wtype: str, helptext: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row,
            text=label,
            font=theme.FONT_BODY_BOLD,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            width=220,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        if wtype == "theme_select":
            presets = theme.available_presets()
            self._theme_preset_ids = [pid for pid, _ in presets]
            labels = [plabel for _, plabel in presets]
            self._theme_combo = ctk.CTkOptionMenu(
                row,
                values=labels,
                font=theme.FONT_BODY,
                fg_color=theme.BLACK_SOFT,
                button_color=theme.RED_DEEP,
                button_hover_color=theme.RED_PRIMARY,
                text_color=theme.TEXT_PRIMARY,
                dropdown_fg_color=theme.BLACK_CARD,
                dropdown_text_color=theme.TEXT_PRIMARY,
                height=34,
                command=self._on_theme_selected,
            )
            self._theme_combo.grid(row=0, column=1, sticky="ew")
        elif wtype == "resolution_select":
            resolutions = theme.available_resolutions()
            self._resolution_ids = [rid for rid, _ in resolutions]
            labels = [rlabel for _, rlabel in resolutions]
            self._resolution_combo = ctk.CTkOptionMenu(
                row,
                values=labels,
                font=theme.FONT_BODY,
                fg_color=theme.BLACK_SOFT,
                button_color=theme.RED_DEEP,
                button_hover_color=theme.RED_PRIMARY,
                text_color=theme.TEXT_PRIMARY,
                dropdown_fg_color=theme.BLACK_CARD,
                dropdown_text_color=theme.TEXT_PRIMARY,
                height=34,
                command=self._on_resolution_selected,
            )
            self._resolution_combo.grid(row=0, column=1, sticky="ew")
        else:
            entry = ctk.CTkEntry(
                row,
                font=theme.FONT_BODY,
                fg_color=theme.BLACK_SOFT,
                border_color=theme.BLACK_BORDER,
                text_color=theme.TEXT_PRIMARY,
                placeholder_text=helptext,
                height=34,
            )
            entry.grid(row=0, column=1, sticky="ew")
            self._entries[key] = entry

        ctk.CTkLabel(
            row,
            text=helptext,
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

    def _build_ia_extras(self, parent) -> None:
        # Botao de teste do Ollama
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkButton(
            btn_row,
            text="Testar Ollama",
            height=36,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.RED_DEEP,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._test_ollama,
        ).pack(side="left")

        # Card de ajuda sobre Ollama Cloud
        help_card = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.RED_DEEP,
            border_width=1,
        )
        help_card.pack(fill="x", padx=16, pady=(12, 16))

        ctk.CTkLabel(
            help_card,
            text="USANDO OLLAMA CLOUD",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 8))

        ctk.CTkLabel(
            help_card,
            text=(
                "O Ollama suporta modelos cloud hospedados (sufixo -cloud). "
                "Exemplos: gpt-oss:20b-cloud, gpt-oss:120b-cloud, "
                "qwen3-coder:480b-cloud, kimi-k2:1t-cloud.\n\n"
                "Para usar:\n"
                "  1. Faca login:  ollama signin\n"
                "  2. Baixe o modelo cloud:  ollama pull gpt-oss:20b-cloud\n"
                "  3. Coloque o nome exato no campo 'Modelo Ollama'\n\n"
                "Tambem funciona com modelos locais (ex: llama3, mistral, gemma2)."
            ),
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=980,
        ).pack(fill="x", padx=20, pady=(0, 16))

    # ─── Acoes ─────────────────────────────────────────────────────────

    def on_show(self) -> None:
        self._load_values()

    def _load_values(self) -> None:
        settings = self.app.settings
        for key, entry in self._entries.items():
            entry.delete(0, "end")
            value = settings.get(key, "")
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif value is None:
                value = ""
            entry.insert(0, str(value))

        if self._theme_combo is not None:
            current = settings.get("theme_preset", theme.DEFAULT_PRESET)
            if current not in self._theme_preset_ids:
                current = theme.DEFAULT_PRESET
            idx = self._theme_preset_ids.index(current)
            labels = [plabel for _, plabel in theme.available_presets()]
            self._theme_combo.set(labels[idx])

        if self._resolution_combo is not None:
            current = settings.get("window_resolution", theme.DEFAULT_RESOLUTION)
            if current not in self._resolution_ids:
                current = theme.DEFAULT_RESOLUTION
            idx = self._resolution_ids.index(current)
            labels = [rlabel for _, rlabel in theme.available_resolutions()]
            self._resolution_combo.set(labels[idx])

    def _gather_values(self) -> dict:
        settings = dict(self.app.settings)
        for key, _, wtype, _, _ in FIELD_SPECS:
            if wtype == "theme_select":
                if self._theme_combo is None:
                    continue
                selected_label = self._theme_combo.get()
                labels = [plabel for _, plabel in theme.available_presets()]
                try:
                    idx = labels.index(selected_label)
                    settings[key] = self._theme_preset_ids[idx]
                except ValueError:
                    settings[key] = theme.DEFAULT_PRESET
                continue

            if wtype == "resolution_select":
                if self._resolution_combo is None:
                    continue
                selected_label = self._resolution_combo.get()
                labels = [rlabel for _, rlabel in theme.available_resolutions()]
                try:
                    idx = labels.index(selected_label)
                    settings[key] = self._resolution_ids[idx]
                except ValueError:
                    settings[key] = theme.DEFAULT_RESOLUTION
                continue

            entry = self._entries.get(key)
            if entry is None:
                continue
            raw = entry.get().strip()
            if wtype == "list_entry":
                settings[key] = [v.strip() for v in raw.split(",") if v.strip()]
            elif wtype == "int_entry":
                try:
                    settings[key] = int(raw) if raw else 0
                except ValueError:
                    settings[key] = 0
            else:
                settings[key] = raw
        return settings

    def _save(self) -> None:
        try:
            new_settings = self._gather_values()
            storage.save_settings(new_settings)
            self.app.reload_settings()
            self.status_label.configure(
                text="Configuracoes salvas com sucesso.",
                text_color=theme.TEXT_SUCCESS,
            )
            # Atualiza status do Ollama com a nova URL
            self.app.check_ollama_status()
        except Exception as exc:  # noqa: BLE001
            self.status_label.configure(
                text=f"Erro ao salvar: {exc}",
                text_color=theme.TEXT_DANGER,
            )

    def _reload(self) -> None:
        self.app.reload_settings()
        self._load_values()
        self.status_label.configure(
            text="Valores recarregados do disco.",
            text_color=theme.TEXT_INFO,
        )

    def _on_theme_selected(self, selected_label: str) -> None:
        """Aplica o tema escolhido imediatamente (hot reload)."""
        labels = [plabel for _, plabel in theme.available_presets()]
        try:
            idx = labels.index(selected_label)
        except ValueError:
            return
        preset_id = self._theme_preset_ids[idx]
        # Rebuild destroi esta pagina — agendamos pra rodar depois do evento atual
        self.after(50, lambda: self.app.apply_theme_preset(preset_id))

    def _on_resolution_selected(self, selected_label: str) -> None:
        """Aplica a resolucao escolhida imediatamente."""
        labels = [rlabel for _, rlabel in theme.available_resolutions()]
        try:
            idx = labels.index(selected_label)
        except ValueError:
            return
        resolution_id = self._resolution_ids[idx]
        self.app.apply_resolution_preset(resolution_id)

    def _test_ollama(self) -> None:
        from modules import ollama_client

        url = self._entries["ollama_url"].get().strip() or "http://localhost:11434"
        model = self._entries["ollama_model"].get().strip() or "llama3"

        self.status_label.configure(
            text="Testando conexao com Ollama...",
            text_color=theme.TEXT_INFO,
        )

        def on_result(result) -> None:
            is_online, models = result
            if not is_online:
                self.status_label.configure(
                    text=(
                        f"Nao foi possivel conectar em {url}.\n"
                        f"Verifique se o Ollama esta rodando (ollama serve)."
                    ),
                    text_color=theme.TEXT_DANGER,
                )
                return
            if model and models and model not in models:
                self.status_label.configure(
                    text=(
                        f"Ollama online, mas o modelo '{model}' nao foi encontrado.\n"
                        f"Modelos disponiveis: {', '.join(models[:10])}"
                    ),
                    text_color=theme.TEXT_WARNING,
                )
            else:
                self.status_label.configure(
                    text=(
                        f"Ollama online. {len(models)} modelo(s) disponivel(is).\n"
                        f"Modelo configurado: {model or '—'}"
                    ),
                    text_color=theme.TEXT_SUCCESS,
                )

        async def _check():
            online = await ollama_client.check_ollama(url)
            if not online:
                return (False, [])
            models = await ollama_client.list_models(url)
            return (True, models)

        self.run_async(
            coro_factory=lambda: _check(),
            on_result=on_result,
            on_error=lambda e: self.status_label.configure(
                text=f"Erro: {e}",
                text_color=theme.TEXT_DANGER,
            ),
        )
