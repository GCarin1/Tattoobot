"""Cards reutilizaveis para resultados (perfis, ideias, spy, etc)."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme


class BaseCard(ctk.CTkFrame):
    """Card base com estilo blackwork (fundo escuro, borda vermelha sutil)."""

    def __init__(
        self,
        parent,
        title: str = "",
        accent: str = theme.RED_PRIMARY,
        **kwargs,
    ) -> None:
        kwargs.setdefault("fg_color", theme.BLACK_CARD)
        kwargs.setdefault("border_color", accent)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", theme.CARD_RADIUS)
        super().__init__(parent, **kwargs)

        if title:
            self.header = ctk.CTkLabel(
                self,
                text=title,
                font=theme.FONT_SUBHEADING,
                text_color=accent,
                anchor="w",
            )
            self.header.pack(fill="x", padx=16, pady=(12, 6))


class InfoCard(BaseCard):
    """Card simples com titulo e corpo de texto."""

    def __init__(
        self,
        parent,
        title: str,
        body: str,
        accent: str = theme.RED_PRIMARY,
        **kwargs,
    ) -> None:
        super().__init__(parent, title=title, accent=accent, **kwargs)
        self.body_label = ctk.CTkLabel(
            self,
            text=body,
            font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self.body_label.pack(fill="x", padx=16, pady=(0, 14))


class StatsCard(BaseCard):
    """Card com uma metrica grande (usado no dashboard)."""

    def __init__(
        self,
        parent,
        label: str,
        value: str,
        subtitle: str = "",
        accent: str = theme.RED_PRIMARY,
        **kwargs,
    ) -> None:
        super().__init__(parent, accent=accent, **kwargs)

        ctk.CTkLabel(
            self,
            text=label.upper(),
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            self,
            text=value,
            font=(theme.FONT_FAMILY, 28, "bold"),
            text_color=accent,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 2))

        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 12))
        else:
            ctk.CTkFrame(self, fg_color="transparent", height=10).pack()


class ProfileCard(BaseCard):
    """Card de perfil com link + contexto + sugestoes de comentario."""

    def __init__(
        self,
        parent,
        username: str,
        link: str,
        context: str,
        comments: list[str],
        on_copy=None,
        on_open=None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            title=f"@{username}",
            accent=theme.RED_PRIMARY,
            **kwargs,
        )

        # Link
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            link_frame,
            text=link,
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_INFO,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        if on_open:
            ctk.CTkButton(
                link_frame,
                text="Abrir",
                width=70,
                height=24,
                font=theme.FONT_SMALL,
                fg_color=theme.BLACK_HOVER,
                hover_color=theme.RED_DEEP,
                command=lambda: on_open(link),
            ).pack(side="right")

        # Contexto
        if context:
            preview = (context[:200] + "...") if len(context) > 200 else context
            ctk.CTkLabel(
                self,
                text=f'"{preview}"',
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=900,
            ).pack(fill="x", padx=16, pady=(0, 8))

        # Comentarios
        ctk.CTkLabel(
            self,
            text="SUGESTOES DE COMENTARIO",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(4, 2))

        for i, comment in enumerate(comments, 1):
            row = ctk.CTkFrame(self, fg_color=theme.BLACK_HOVER, corner_radius=6)
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                row,
                text=f"{i}. {comment}",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
                justify="left",
                wraplength=780,
            ).pack(side="left", fill="x", expand=True, padx=10, pady=6)
            if on_copy:
                ctk.CTkButton(
                    row,
                    text="Copiar",
                    width=70,
                    height=24,
                    font=theme.FONT_SMALL,
                    fg_color=theme.BLACK_CARD,
                    hover_color=theme.RED_DEEP,
                    command=lambda c=comment: on_copy(c),
                ).pack(side="right", padx=6, pady=4)

        ctk.CTkFrame(self, fg_color="transparent", height=6).pack()


class IdeaCard(BaseCard):
    """Card de ideia de conteudo."""

    def __init__(
        self,
        parent,
        index: int,
        format_type: str,
        title: str,
        description: str,
        tip: str,
        hashtag: str,
        **kwargs,
    ) -> None:
        accent = theme.RED_PRIMARY
        super().__init__(parent, accent=accent, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        badge = ctk.CTkLabel(
            header,
            text=f"[{format_type.upper()}]",
            font=theme.FONT_SMALL,
            text_color=theme.RED_GLOW,
        )
        badge.pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"  {index}. {title}",
            font=theme.FONT_SUBHEADING,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=theme.FONT_BODY,
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=900,
            ).pack(fill="x", padx=16, pady=(0, 6))

        if tip:
            ctk.CTkLabel(
                self,
                text=f"Dica: {tip}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_WARNING,
                anchor="w",
                justify="left",
                wraplength=900,
            ).pack(fill="x", padx=16, pady=(0, 4))

        if hashtag:
            ctk.CTkLabel(
                self,
                text=f"#{hashtag}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 12))


class SpyCard(BaseCard):
    """Card de analise de concorrente."""

    def __init__(
        self,
        parent,
        username: str,
        stats_lines: list[str],
        analysis: str,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            title=f"@{username}",
            accent=theme.RED_PRIMARY,
            **kwargs,
        )

        if stats_lines:
            stats_frame = ctk.CTkFrame(self, fg_color=theme.BLACK_HOVER, corner_radius=6)
            stats_frame.pack(fill="x", padx=16, pady=(0, 8))
            for line in stats_lines:
                ctk.CTkLabel(
                    stats_frame,
                    text=f"  {line}",
                    font=theme.FONT_BODY,
                    text_color=theme.TEXT_PRIMARY,
                    anchor="w",
                    justify="left",
                    wraplength=880,
                ).pack(fill="x", padx=6, pady=2)

        ctk.CTkLabel(
            self,
            text="ANALISE IA",
            font=theme.FONT_SMALL,
            text_color=theme.RED_GLOW,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(
            self,
            text=analysis,
            font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=16, pady=(0, 14))


class ProblemCard(BaseCard):
    """Card de problema encontrado em avaliacao de tattoo."""

    def __init__(
        self,
        parent,
        index: int,
        title: str,
        grid_row: int,
        grid_col: int,
        description: str,
        fix: str,
        color_hex: str,
        **kwargs,
    ) -> None:
        super().__init__(parent, accent=color_hex, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header,
            text=f"#{index}  {title}",
            font=theme.FONT_SUBHEADING,
            text_color=color_hex,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"Grade: L{grid_row}C{grid_col}",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="e",
        ).pack(side="right")

        ctk.CTkLabel(
            self,
            text=f"Problema: {description}",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            self,
            text=f"Como corrigir: {fix}",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SUCCESS,
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=16, pady=(0, 14))
