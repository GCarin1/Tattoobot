"""Pagina de configuracoes."""

from __future__ import annotations

import tkinter.messagebox as messagebox

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from utils import storage


FIELD_SPECS = [
    # (key, label, widget_type, help_text)
    ("artist_name", "Nome artistico", "entry", "Como voce assina o trabalho"),
    ("artist_city", "Cidade", "entry", "Para SEO em legendas"),
    ("tattoo_style", "Estilo principal", "entry", "Ex: blackwork, dotwork, realismo"),
    ("hashtags", "Hashtags (vírgula)", "list_entry", "Ex: blackwork, tattoo, tatuagembr"),
    ("profiles_per_day", "Perfis por dia", "int_entry", "Quantos perfis buscar por sessao"),
    ("scraping_delay_seconds", "Delay entre requisicoes (s)", "int_entry", "Recomendado 3-5s"),
    ("ollama_url", "URL do Ollama", "entry", "Padrao: http://localhost:11434"),
    ("ollama_model", "Modelo Ollama (texto)", "entry", "Ex: llama3, mistral, gemma2:27b-cloud"),
    ("ollama_vision_model", "Modelo Ollama (visao)", "entry", "Para Avaliar Tattoo. Ex: llava, gemma3"),
    ("language", "Idioma", "entry", "Padrao: pt-br"),
]


class SettingsPage(BasePage):
    TITLE = "Configuracoes"
    DESCRIPTION = (
        "Configure seu perfil e a conexao com o Ollama. "
        "Voce pode usar modelos locais ou cloud (Ollama suporta os dois)."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        self._entries: dict[str, ctk.CTkEntry] = {}

        # Card com formulario
        form_card = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        form_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            form_card,
            text="PERFIL E INTEGRACAO",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 12))

        for key, label, wtype, helptext in FIELD_SPECS:
            row = ctk.CTkFrame(form_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)
            row.grid_columnconfigure(1, weight=1)

            lbl = ctk.CTkLabel(
                row,
                text=label,
                font=theme.FONT_BODY_BOLD,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                width=220,
            )
            lbl.grid(row=0, column=0, sticky="w", padx=(0, 12))

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

            help_lbl = ctk.CTkLabel(
                row,
                text=helptext,
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            )
            help_lbl.grid(row=1, column=1, sticky="w", pady=(2, 0))

        # Action buttons
        btns = ctk.CTkFrame(form_card, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(14, 18))

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
            text="Testar Ollama",
            height=40,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.RED_DEEP,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            command=self._test_ollama,
        ).pack(side="left", padx=8)

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

        # Status area
        self.status_label = ctk.CTkLabel(
            form_card,
            text="",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 14))

        # Ajuda sobre Ollama Cloud
        help_card = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.RED_DEEP,
            border_width=1,
        )
        help_card.pack(fill="x", pady=(8, 0))

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

        # Popula com valores atuais
        self._load_values()

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

    def _gather_values(self) -> dict:
        settings = dict(self.app.settings)
        for (key, _, wtype, _), entry in zip(FIELD_SPECS, self._entries.values()):
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
