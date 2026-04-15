"""Pagina de Avaliacao de Tatuagem com IA de visao."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import ProblemCard, InfoCard


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


class EvaluatePage(BasePage):
    TITLE = "Avaliar Tatuagem"
    DESCRIPTION = (
        "IA de visao analisa sua foto de tattoo e marca os pontos de melhoria "
        "com uma grade numerada. Precisa de um modelo de visao no Ollama (ex: llava)."
    )
    ACCENT = theme.RED_PRIMARY

    def build_body(self, parent) -> None:
        # Upload box
        upload = ctk.CTkFrame(
            parent,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=theme.BLACK_BORDER,
            border_width=1,
        )
        upload.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            upload,
            text="SELECIONAR IMAGEM",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 10))

        row = ctk.CTkFrame(upload, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))
        row.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(
            row,
            font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT,
            border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text="Caminho da imagem (.jpg, .png, .webp...)",
            height=36,
        )
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Escolher Arquivo",
            height=36,
            width=140,
            fg_color=theme.BLACK_HOVER,
            hover_color=theme.RED_DEEP,
            font=theme.FONT_BODY_BOLD,
            command=self._pick_file,
        ).grid(row=0, column=1)

        btns = ctk.CTkFrame(upload, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(6, 16))

        self.run_btn = ctk.CTkButton(
            btns,
            text="▶  Avaliar com IA",
            height=40,
            fg_color=theme.RED_PRIMARY,
            hover_color=theme.RED_HOVER,
            font=theme.FONT_BODY_BOLD,
            command=self._start,
        )
        self.run_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            btns,
            text=(
                "Dica: configure um modelo de visao em Configuracoes > "
                "Modelo Ollama (visao). Ex: llava, gemma3, llama3.2-vision."
            ),
            font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED,
            anchor="w",
            wraplength=700,
            justify="left",
        )
        self.status_label.pack(side="left", padx=14, fill="x", expand=True)

        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def _pick_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Escolher imagem de tatuagem",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("Todos", "*.*"),
            ],
        )
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    def _start(self) -> None:
        path_str = self.path_entry.get().strip().strip("'\"")
        if not path_str:
            self.status_label.configure(
                text="Escolha uma imagem primeiro.",
                text_color=theme.TEXT_DANGER,
            )
            return
        image_path = Path(path_str).expanduser().resolve()
        if not image_path.exists():
            self.status_label.configure(
                text=f"Arquivo nao encontrado: {image_path}",
                text_color=theme.TEXT_DANGER,
            )
            return
        if image_path.suffix.lower() not in SUPPORTED_FORMATS:
            self.status_label.configure(
                text=f"Formato nao suportado. Use: {', '.join(SUPPORTED_FORMATS)}",
                text_color=theme.TEXT_DANGER,
            )
            return
        size_mb = image_path.stat().st_size / (1024 * 1024)
        if size_mb > 20:
            self.status_label.configure(
                text=f"Imagem muito grande ({size_mb:.1f}MB). Maximo 20MB.",
                text_color=theme.TEXT_DANGER,
            )
            return

        self._clear_results()
        self.run_btn.configure(state="disabled", text="Analisando...")
        self.status_label.configure(
            text="IA de visao processando... pode levar alguns minutos.",
            text_color=theme.TEXT_INFO,
        )

        settings = self.app.settings
        self.run_async(
            coro_factory=lambda: self._evaluate_flow(settings, image_path),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(
                state="normal", text="▶  Avaliar com IA"
            ),
        )

    async def _evaluate_flow(self, settings, image_path: Path):
        from modules import ollama_client
        from modules.tattoo_evaluator import (
            EVALUATION_PROMPT,
            SYSTEM_PROMPT,
            _extract_json,
            _annotate_image,
        )

        default_model = settings.get("ollama_model", "llava")
        vision_model = settings.get("ollama_vision_model") or default_model
        ollama_url = settings.get("ollama_url", "http://localhost:11434")

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        response = await ollama_client.generate_with_image(
            prompt=EVALUATION_PROMPT,
            image_base64=image_b64,
            ollama_url=ollama_url,
            model=vision_model,
            system_prompt=SYSTEM_PROMPT,
        )
        if not response:
            raise RuntimeError(
                "IA de visao nao retornou resposta. "
                "Certifique-se de ter um modelo de visao (ex: ollama pull llava) "
                "e configure-o em Configuracoes > ollama_vision_model."
            )
        evaluation = _extract_json(response)
        if not evaluation:
            return {"evaluation": None, "raw": response, "annotated": None}

        annotated_path = None
        problems = evaluation.get("problemas", [])
        if problems:
            annotated_path = _annotate_image(image_path, problems)

        return {
            "evaluation": evaluation,
            "raw": response,
            "annotated": annotated_path,
            "model_used": vision_model,
        }

    def _on_done(self, result) -> None:
        evaluation = result["evaluation"]
        if evaluation is None:
            self.status_label.configure(
                text="IA nao retornou JSON valido. Veja resposta bruta.",
                text_color=theme.TEXT_WARNING,
            )
            InfoCard(
                self.results_frame,
                title="Resposta bruta",
                body=result["raw"],
                accent=theme.RED_PRIMARY,
            ).pack(fill="x", pady=6)
            return

        self.status_label.configure(
            text=f"Avaliacao concluida (modelo: {result.get('model_used', '?')}).",
            text_color=theme.TEXT_SUCCESS,
        )

        nota = evaluation.get("nota_geral", "?")
        try:
            nota_num = float(nota)
            if nota_num >= 8:
                nota_color = theme.TEXT_SUCCESS
            elif nota_num >= 5:
                nota_color = theme.TEXT_WARNING
            else:
                nota_color = theme.TEXT_DANGER
        except (TypeError, ValueError):
            nota_color = theme.TEXT_PRIMARY

        # Card com nota + resumo
        header = ctk.CTkFrame(
            self.results_frame,
            fg_color=theme.BLACK_CARD,
            corner_radius=theme.CARD_RADIUS,
            border_color=nota_color,
            border_width=1,
        )
        header.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            header,
            text=f"NOTA GERAL: {nota}/10",
            font=(theme.FONT_FAMILY, 24, "bold"),
            text_color=nota_color,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            header,
            text=evaluation.get("resumo", "Sem resumo disponivel."),
            font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=960,
        ).pack(fill="x", padx=20, pady=(0, 18))

        # Imagem anotada
        annotated = result.get("annotated")
        if annotated:
            img_card = ctk.CTkFrame(
                self.results_frame,
                fg_color=theme.BLACK_CARD,
                corner_radius=theme.CARD_RADIUS,
                border_color=theme.BLACK_BORDER,
                border_width=1,
            )
            img_card.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                img_card,
                text="IMAGEM ANOTADA",
                font=theme.FONT_SUBHEADING,
                text_color=theme.RED_GLOW,
                anchor="w",
            ).pack(fill="x", padx=20, pady=(14, 6))
            ctk.CTkLabel(
                img_card,
                text=f"Salva em: {annotated}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_INFO,
                anchor="w",
                justify="left",
                wraplength=960,
            ).pack(fill="x", padx=20, pady=(0, 6))
            ctk.CTkButton(
                img_card,
                text="Abrir imagem anotada",
                height=32,
                fg_color=theme.RED_DEEP,
                hover_color=theme.RED_PRIMARY,
                font=theme.FONT_BODY_BOLD,
                command=lambda: self._open_file(annotated),
            ).pack(anchor="w", padx=20, pady=(0, 14))

        # Pontos positivos
        positivos = evaluation.get("pontos_positivos", [])
        if positivos:
            body = "\n".join(f"  + {p}" for p in positivos)
            InfoCard(
                self.results_frame,
                title="Pontos Positivos",
                body=body,
                accent=theme.TEXT_SUCCESS,
            ).pack(fill="x", pady=6)

        # Problemas
        problemas = evaluation.get("problemas", [])
        if problemas:
            from modules.tattoo_evaluator import _get_marker_color

            ctk.CTkLabel(
                self.results_frame,
                text="PROBLEMAS ENCONTRADOS",
                font=theme.FONT_SUBHEADING,
                text_color=theme.RED_GLOW,
                anchor="w",
            ).pack(fill="x", pady=(10, 4))

            for i, prob in enumerate(problemas, 1):
                color_rgb = _get_marker_color(i - 1)
                color_hex = "#{:02x}{:02x}{:02x}".format(*color_rgb)
                ProblemCard(
                    self.results_frame,
                    index=i,
                    title=prob.get("titulo", "Problema"),
                    grid_row=prob.get("grid_linha", "?"),
                    grid_col=prob.get("grid_coluna", "?"),
                    description=prob.get("descricao", ""),
                    fix=prob.get("como_corrigir", ""),
                    color_hex=color_hex,
                ).pack(fill="x", pady=6)
        else:
            InfoCard(
                self.results_frame,
                title="Sem problemas significativos",
                body="Otima tatuagem! Nada de critico identificado.",
                accent=theme.TEXT_SUCCESS,
            ).pack(fill="x", pady=6)

        # Dicas gerais
        dicas = evaluation.get("dicas_gerais", [])
        if dicas:
            body = "\n".join(f"  * {d}" for d in dicas)
            InfoCard(
                self.results_frame,
                title="Dicas Gerais",
                body=body,
                accent=theme.TEXT_WARNING,
            ).pack(fill="x", pady=6)

    def _open_file(self, path) -> None:
        """Abre arquivo no visualizador padrao do sistema."""
        import subprocess
        import sys
        try:
            p = str(path)
            if sys.platform.startswith("win"):
                os.startfile(p)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])
        except Exception:  # noqa: BLE001
            pass

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(text=f"Erro: {exc}", text_color=theme.TEXT_DANGER)
