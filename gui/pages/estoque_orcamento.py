"""Tab 3 do Estoque: calculadora de orcamento de sessao de tatuagem."""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from gui import theme
from modules import stock_manager
from utils import storage


def build_orcamento_tab(parent: ctk.CTkFrame, app: Any, page_ref: Any) -> None:
    """Monta a aba de orcamento de sessao."""

    main = ctk.CTkFrame(parent, fg_color="transparent")
    main.pack(fill="both", expand=True, padx=8, pady=8)
    main.grid_columnconfigure(0, weight=1)
    main.grid_columnconfigure(1, weight=2)
    main.grid_rowconfigure(0, weight=1)

    # ── Painel esquerdo: seletor de itens ──────────────────────────────────────
    left = ctk.CTkFrame(main, fg_color=theme.BLACK_PANEL, corner_radius=8)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

    ctk.CTkLabel(
        left,
        text="Selecionar Insumos",
        font=theme.FONT_BODY_BOLD,
        text_color=theme.RED_PRIMARY,
        anchor="w",
    ).pack(fill="x", padx=12, pady=(10, 6))

    ctk.CTkFrame(left, height=1, fg_color=theme.BLACK_BORDER).pack(fill="x", padx=12, pady=(0, 6))

    items_scroll = ctk.CTkScrollableFrame(
        left,
        fg_color="transparent",
        scrollbar_button_color=theme.RED_DEEP,
        scrollbar_button_hover_color=theme.RED_PRIMARY,
    )
    items_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # Mao de obra
    labor_frame = ctk.CTkFrame(left, fg_color=theme.BLACK_CARD, corner_radius=6)
    labor_frame.pack(fill="x", padx=8, pady=(0, 10))

    ctk.CTkLabel(
        labor_frame,
        text="Mao de obra",
        font=theme.FONT_SMALL,
        text_color=theme.TEXT_MUTED,
        anchor="w",
    ).pack(fill="x", padx=10, pady=(8, 2))

    labor_row = ctk.CTkFrame(labor_frame, fg_color="transparent")
    labor_row.pack(fill="x", padx=8, pady=(0, 8))

    ctk.CTkLabel(labor_row, text="Min:", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY, width=30).pack(side="left")
    labor_min_var = tk.StringVar(value="0")
    ctk.CTkEntry(labor_row, textvariable=labor_min_var, width=55, height=28, corner_radius=4,
                 fg_color=theme.BLACK_HOVER, border_color=theme.BLACK_BORDER,
                 text_color=theme.TEXT_PRIMARY, font=theme.FONT_SMALL).pack(side="left", padx=4)

    ctk.CTkLabel(labor_row, text="R$/h:", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY, width=40).pack(side="left")
    labor_rate_var = tk.StringVar(value="0")
    ctk.CTkEntry(labor_row, textvariable=labor_rate_var, width=65, height=28, corner_radius=4,
                 fg_color=theme.BLACK_HOVER, border_color=theme.BLACK_BORDER,
                 text_color=theme.TEXT_PRIMARY, font=theme.FONT_SMALL).pack(side="left", padx=4)

    calc_btn = ctk.CTkButton(
        left,
        text="Calcular Orcamento",
        height=36,
        corner_radius=6,
        fg_color=theme.RED_PRIMARY,
        hover_color=theme.RED_HOVER,
        text_color=theme.TEXT_PRIMARY,
        font=theme.FONT_BODY_BOLD,
    )
    calc_btn.pack(fill="x", padx=8, pady=(0, 10))

    # ── Painel direito: resultado ──────────────────────────────────────────────
    right = ctk.CTkFrame(main, fg_color=theme.BLACK_PANEL, corner_radius=8)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

    ctk.CTkLabel(
        right,
        text="Resumo do Orcamento",
        font=theme.FONT_BODY_BOLD,
        text_color=theme.RED_PRIMARY,
        anchor="w",
    ).pack(fill="x", padx=12, pady=(10, 6))

    ctk.CTkFrame(right, height=1, fg_color=theme.BLACK_BORDER).pack(fill="x", padx=12, pady=(0, 6))

    result_scroll = ctk.CTkScrollableFrame(
        right,
        fg_color="transparent",
        scrollbar_button_color=theme.RED_DEEP,
        scrollbar_button_hover_color=theme.RED_PRIMARY,
    )
    result_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    copy_btn = ctk.CTkButton(
        right,
        text="Copiar Resumo",
        height=32,
        corner_radius=6,
        fg_color=theme.BLACK_HOVER,
        hover_color=theme.BLACK_BORDER,
        text_color=theme.TEXT_SECONDARY,
        font=theme.FONT_SMALL,
        state="disabled",
    )
    copy_btn.pack(fill="x", padx=8, pady=(0, 10))

    # ── Estado interno ─────────────────────────────────────────────────────────
    state: dict[str, Any] = {"budget_text": "", "check_vars": []}

    def _load_items() -> None:
        for w in items_scroll.winfo_children():
            w.destroy()
        state["check_vars"].clear()
        data = storage.load_estoque()
        items = data.get("items", [])
        if not items:
            ctk.CTkLabel(
                items_scroll,
                text="Nenhum item no estoque.\nImporte uma planilha primeiro.",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                justify="center",
            ).pack(pady=20)
            return
        for item in items:
            row = ctk.CTkFrame(items_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            check_var = tk.BooleanVar(value=False)
            qty_var = tk.StringVar(value="1")
            ctk.CTkCheckBox(
                row,
                text=item.get("name", ""),
                variable=check_var,
                width=140,
                height=24,
                corner_radius=4,
                fg_color=theme.RED_DEEP,
                hover_color=theme.RED_PRIMARY,
                checkmark_color=theme.TEXT_PRIMARY,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_SMALL,
            ).pack(side="left", padx=(4, 2))
            ctk.CTkEntry(
                row,
                textvariable=qty_var,
                width=50,
                height=24,
                corner_radius=4,
                fg_color=theme.BLACK_HOVER,
                border_color=theme.BLACK_BORDER,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_SMALL,
            ).pack(side="left", padx=2)
            ctk.CTkLabel(
                row,
                text=item.get("unit", "un"),
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                width=60,
                anchor="w",
            ).pack(side="left", padx=2)
            state["check_vars"].append({"item": item, "check_var": check_var, "qty_var": qty_var})

    def _calculate() -> None:
        selections = []
        data = storage.load_estoque()
        items_map = {it["id"]: it for it in data.get("items", [])}
        for cv in state["check_vars"]:
            if cv["check_var"].get():
                item = items_map.get(cv["item"]["id"], cv["item"])
                try:
                    qty = float(cv["qty_var"].get().replace(",", ".") or 1)
                except ValueError:
                    qty = 1.0
                selections.append({"item": item, "quantity_used": qty})

        if not selections:
            return

        try:
            labor_min = int(float(labor_min_var.get() or 0))
        except ValueError:
            labor_min = 0
        try:
            labor_rate = float(labor_rate_var.get().replace(",", ".") or 0)
        except ValueError:
            labor_rate = 0.0

        budget = stock_manager.calculate_budget(selections, labor_min, labor_rate)
        state["budget_text"] = stock_manager.format_budget_text(budget)
        _render_result(budget)
        copy_btn.configure(state="normal")

    def _render_result(budget: dict[str, Any]) -> None:
        for w in result_scroll.winfo_children():
            w.destroy()

        for line in budget["lines"]:
            row = ctk.CTkFrame(result_scroll, fg_color=theme.BLACK_CARD, corner_radius=4)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(
                row,
                text=f"{line['qty']:.1f}x {line['name']}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
            ).pack(side="left", padx=8, pady=4)
            ctk.CTkLabel(
                row,
                text=f"R$ {line['subtotal']:.2f}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_SUCCESS,
                anchor="e",
            ).pack(side="right", padx=8)

        ctk.CTkFrame(result_scroll, height=1, fg_color=theme.BLACK_BORDER).pack(fill="x", pady=4)

        def _total_row(label: str, value: float, color: str = theme.TEXT_PRIMARY) -> None:
            row = ctk.CTkFrame(result_scroll, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=1)
            ctk.CTkLabel(row, text=label, font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"R$ {value:.2f}", font=theme.FONT_BODY_BOLD, text_color=color, anchor="e").pack(side="right")

        _total_row("Material total:", budget["material_total"])
        if budget["labor_total"] > 0:
            label = f"Mao de obra ({budget['labor_minutes']}min @ R${budget['labor_rate_per_hour']:.0f}/h):"
            _total_row(label, budget["labor_total"])

        ctk.CTkFrame(result_scroll, height=1, fg_color=theme.RED_DEEP).pack(fill="x", pady=4)

        row = ctk.CTkFrame(result_scroll, fg_color=theme.BLACK_CARD, corner_radius=4)
        row.pack(fill="x", pady=2, padx=2)
        ctk.CTkLabel(row, text="TOTAL DA SESSAO", font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=8, pady=6)
        ctk.CTkLabel(row, text=f"R$ {budget['grand_total']:.2f}", font=theme.FONT_HEADING, text_color=theme.RED_PRIMARY, anchor="e").pack(side="right", padx=8)

    def _copy_to_clipboard() -> None:
        app.clipboard_clear()
        app.clipboard_append(state["budget_text"])

    calc_btn.configure(command=_calculate)
    copy_btn.configure(command=_copy_to_clipboard)

    _load_items()
    # Reload items when tab becomes visible
    page_ref._orcamento_reload = _load_items
