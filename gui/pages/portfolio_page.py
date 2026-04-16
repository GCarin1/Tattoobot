"""Pagina do Curador de Portfolio."""

from __future__ import annotations

import customtkinter as ctk
import tkinter.filedialog as filedialog

from gui import theme
from gui.pages.base import BasePage
from gui.widgets import InfoCard


class PortfolioPage(BasePage):
    TITLE = "Curador de Portfolio"
    DESCRIPTION = (
        "Analisa suas fotos de tatuagem com IA de visao, sugere quais postar e quando, "
        "e identifica gaps no portfolio."
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
            form, text="PASTA COM AS FOTOS",
            font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        ctk.CTkLabel(
            form,
            text="Selecione uma pasta com as fotos das tatuagens (JPG, PNG, WEBP)",
            font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=20)

        path_row = ctk.CTkFrame(form, fg_color="transparent")
        path_row.pack(fill="x", padx=20, pady=(6, 14))
        path_row.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(
            path_row, font=theme.FONT_BODY,
            fg_color=theme.BLACK_SOFT, border_color=theme.BLACK_BORDER,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text="Caminho da pasta...",
            height=34,
        )
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            path_row, text="Procurar",
            height=34, width=90,
            fg_color=theme.BLACK_HOVER, hover_color=theme.RED_DEEP,
            text_color=theme.TEXT_PRIMARY, font=theme.FONT_BODY,
            command=self._browse,
        ).grid(row=0, column=1)

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(0, 16))

        self.run_btn = ctk.CTkButton(
            btns, text="▶  Analisar Portfolio",
            height=40, fg_color=theme.RED_PRIMARY, hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY, font=theme.FONT_BODY_BOLD,
            command=self._start,
        )
        self.run_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            btns, text="",
            font=theme.FONT_BODY, text_color=theme.TEXT_MUTED, anchor="w",
        )
        self.status_label.pack(side="left", padx=14, fill="x", expand=True)

        self.results_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title="Selecione a pasta com as fotos")
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def _start(self) -> None:
        images_dir = self.path_entry.get().strip()
        if not images_dir:
            self.status_label.configure(
                text="Selecione uma pasta de imagens.",
                text_color=theme.TEXT_WARNING,
            )
            return

        self._clear_results()
        self.run_btn.configure(state="disabled", text="Analisando...")
        self.status_label.configure(
            text="Analisando fotos com IA de visao... pode demorar.",
            text_color=theme.TEXT_INFO,
        )

        settings = self.app.settings

        self.run_async(
            coro_factory=lambda: self._portfolio_flow(settings, images_dir),
            on_result=self._on_done,
            on_error=self._on_error,
            on_done=lambda: self.run_btn.configure(state="normal", text="▶  Analisar Portfolio"),
        )

    async def _portfolio_flow(self, settings, images_dir):
        import base64
        from pathlib import Path
        from modules.portfolio_curator import (
            _build_single_eval_prompt, _build_curator_prompt, _parse_json
        )
        from modules import ai_client
        from utils import storage

        img_dir = Path(images_dir)
        image_paths = sorted([
            f for f in img_dir.iterdir()
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        ])

        if not image_paths:
            raise RuntimeError("Nenhuma imagem JPG/PNG encontrada na pasta.")

        image_paths = image_paths[:10]
        tattoo_style = settings.get("tattoo_style", "blackwork")
        eval_prompt = _build_single_eval_prompt(tattoo_style)

        image_descriptions = []
        for img_path in image_paths:
            try:
                with open(img_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                response = await ai_client.generate_with_image(eval_prompt, img_b64, settings)
                if response:
                    parsed = _parse_json(response)
                    if parsed:
                        desc = parsed.get("description", img_path.name)
                        score = parsed.get("quality_score", "?")
                        potential = parsed.get("instagram_potential", "?")
                        image_descriptions.append(
                            f"{img_path.name} — {desc} (qualidade: {score}/10, IG: {potential})"
                        )
                    else:
                        image_descriptions.append(f"{img_path.name} — {response[:100]}")
                else:
                    image_descriptions.append(f"{img_path.name} — analise indisponivel")
            except Exception as e:
                image_descriptions.append(f"{img_path.name} — erro: {e}")

        curation_prompt = _build_curator_prompt(image_descriptions, tattoo_style, "")
        curation_response = await ai_client.generate(curation_prompt, settings, temperature=0.75)
        if not curation_response:
            raise RuntimeError("Nao foi possivel gerar a curadoria.")

        result = _parse_json(curation_response)
        return {
            "result": result,
            "raw": curation_response,
            "image_paths": image_paths,
        }

    def _on_done(self, data) -> None:
        from pathlib import Path
        result = data.get("result")
        image_paths = data.get("image_paths", [])

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

        n_recommended = len(result.get("recommended_order", []))
        n_gaps = len(result.get("gaps", []))
        self.status_label.configure(
            text=f"{n_recommended} fotos para postar, {n_gaps} gaps identificados.",
            text_color=theme.TEXT_SUCCESS,
        )

        # Ordem recomendada
        recommended = result.get("recommended_order", [])
        if recommended:
            ctk.CTkLabel(
                self.results_frame, text="ORDEM DE POSTAGEM RECOMENDADA",
                font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
            ).pack(fill="x", pady=(0, 6))

            for item in recommended:
                idx = item.get("image_index", 1) - 1
                img_name = Path(image_paths[idx]).name if 0 <= idx < len(image_paths) else f"Foto {idx+1}"

                card = ctk.CTkFrame(
                    self.results_frame,
                    fg_color=theme.BLACK_HOVER,
                    corner_radius=6,
                )
                card.pack(fill="x", pady=3)

                header = ctk.CTkFrame(card, fg_color="transparent")
                header.pack(fill="x", padx=12, pady=(8, 2))

                ctk.CTkLabel(
                    header, text=f"#{item.get('position', '')}",
                    font=theme.FONT_SMALL, text_color=theme.RED_GLOW, width=30,
                ).pack(side="left")
                ctk.CTkLabel(
                    header, text=img_name,
                    font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_PRIMARY,
                ).pack(side="left", padx=8)
                ctk.CTkLabel(
                    header, text=item.get("best_day", ""),
                    font=theme.FONT_SMALL, text_color=theme.TEXT_INFO, anchor="e",
                ).pack(side="right")

                ctk.CTkLabel(
                    card, text=item.get("reason", ""),
                    font=theme.FONT_BODY, text_color=theme.TEXT_SECONDARY,
                    anchor="w", wraplength=850, justify="left",
                ).pack(fill="x", padx=12, pady=(0, 4))

                angle = item.get("caption_angle", "")
                if angle:
                    ctk.CTkLabel(
                        card, text=f"Angulo da legenda: {angle}",
                        font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED,
                        anchor="w", wraplength=850,
                    ).pack(fill="x", padx=12, pady=(0, 8))

        # Gaps
        gaps = result.get("gaps", [])
        if gaps:
            ctk.CTkLabel(
                self.results_frame, text="GAPS IDENTIFICADOS NO PORTFOLIO",
                font=theme.FONT_SUBHEADING, text_color=theme.RED_GLOW, anchor="w",
            ).pack(fill="x", pady=(12, 6))

            for gap in gaps:
                InfoCard(
                    self.results_frame,
                    title=gap.get("gap", "Gap"),
                    body=f"Sugestao: {gap.get('suggestion', '')}",
                    accent="#E6B800",
                ).pack(fill="x", pady=4)

        # Feed tip
        feed_tip = result.get("feed_tip", "")
        if feed_tip:
            ctk.CTkLabel(
                self.results_frame,
                text=f"Dica de feed: {feed_tip}",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_INFO,
                anchor="w", wraplength=900,
            ).pack(fill="x", pady=(8, 0))

    def _clear_results(self) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

    def _on_error(self, exc: Exception) -> None:
        self.status_label.configure(text=f"Erro: {exc}", text_color=theme.TEXT_DANGER)
