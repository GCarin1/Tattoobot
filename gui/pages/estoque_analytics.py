"""Tab 4 do Estoque: graficos de analytics com matplotlib."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from gui import theme
from modules import stock_manager
from utils import storage

# Matplotlib deve ser configurado antes de qualquer pyplot import
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


_DARK = {
    "fig_bg": "#0a0a0a",
    "ax_bg": "#1a1a1a",
    "spine": "#2a2a2a",
    "tick": "#A8A8A8",
    "title": "#B00020",
    "bar_color": "#B00020",
    "line_color": "#FF1744",
    "bar2_current": "#7a0016",
    "bar2_found": "#4CAF50",
    "label": "#A8A8A8",
}


def _apply_dark(ax: Any, fig: Any) -> None:
    fig.patch.set_facecolor(_DARK["fig_bg"])
    ax.set_facecolor(_DARK["ax_bg"])
    for spine in ax.spines.values():
        spine.set_edgecolor(_DARK["spine"])
    ax.tick_params(colors=_DARK["tick"])
    ax.xaxis.label.set_color(_DARK["label"])
    ax.yaxis.label.set_color(_DARK["label"])
    ax.title.set_color(_DARK["title"])


def _embed_figure(fig: Figure, parent: ctk.CTkFrame) -> FigureCanvasTkAgg:
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    return canvas


def build_analytics_tab(parent: ctk.CTkFrame, app: Any, page_ref: Any) -> None:
    """Monta a aba de analytics do estoque."""

    # ── Toolbar ────────────────────────────────────────────────────────────────
    toolbar = ctk.CTkFrame(parent, fg_color="transparent")
    toolbar.pack(fill="x", padx=16, pady=(10, 6))

    ctk.CTkLabel(
        toolbar,
        text="Analytics de Estoque",
        font=theme.FONT_BODY_BOLD,
        text_color=theme.RED_PRIMARY,
        anchor="w",
    ).pack(side="left")

    snapshot_btn = ctk.CTkButton(
        toolbar,
        text="Atualizar Snapshot",
        height=32,
        corner_radius=6,
        fg_color=theme.RED_PRIMARY,
        hover_color=theme.RED_HOVER,
        text_color=theme.TEXT_PRIMARY,
        font=theme.FONT_SMALL,
    )
    snapshot_btn.pack(side="right")

    ctk.CTkFrame(parent, height=1, fg_color=theme.BLACK_BORDER).pack(fill="x", padx=16, pady=(0, 8))

    # ── Area de graficos ──────────────────────────────────────────────────────
    charts_scroll = ctk.CTkScrollableFrame(
        parent,
        fg_color="transparent",
        scrollbar_button_color=theme.RED_DEEP,
        scrollbar_button_hover_color=theme.RED_PRIMARY,
    )
    charts_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    state: dict[str, Any] = {"canvases": []}

    def _clear_charts() -> None:
        for canvas in state["canvases"]:
            canvas.get_tk_widget().destroy()
        state["canvases"].clear()
        for w in charts_scroll.winfo_children():
            w.destroy()

    def _render_charts() -> None:
        _clear_charts()
        history = storage.load_estoque_history()

        if not history:
            ctk.CTkLabel(
                charts_scroll,
                text=(
                    "Nenhum historico disponivel.\n"
                    "Clique em 'Atualizar Snapshot' para registrar o estado atual do estoque."
                ),
                font=theme.FONT_BODY,
                text_color=theme.TEXT_MUTED,
                justify="center",
            ).pack(pady=40)
            return

        # ── Grafico 1: Valor total por mes ─────────────────────────────────────
        trend = stock_manager.compute_monthly_trend(history)
        months = trend["months"]
        total_values = trend["total_values"]

        sec1_lbl = ctk.CTkLabel(
            charts_scroll,
            text="Valor Total do Estoque por Mes",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_PRIMARY,
            anchor="w",
        )
        sec1_lbl.pack(fill="x", pady=(4, 2))

        chart1_frame = ctk.CTkFrame(charts_scroll, fg_color=theme.BLACK_CARD, corner_radius=8, height=260)
        chart1_frame.pack(fill="x", pady=(0, 12))
        chart1_frame.pack_propagate(False)

        if months:
            fig1 = Figure(figsize=(8, 2.8), dpi=96, facecolor=_DARK["fig_bg"])
            ax1 = fig1.add_subplot(111, facecolor=_DARK["ax_bg"])
            bars = ax1.bar(months, total_values, color=_DARK["bar_color"], edgecolor=_DARK["spine"], linewidth=0.5)
            ax1.set_ylabel("R$", color=_DARK["label"])
            ax1.set_title("Valor Total do Estoque", color=_DARK["title"], pad=8)
            for bar, val in zip(bars, total_values):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(total_values) * 0.01,
                    f"R${val:.0f}",
                    ha="center", va="bottom",
                    color=_DARK["tick"], fontsize=7,
                )
            _apply_dark(ax1, fig1)
            fig1.tight_layout(pad=0.8)
            c1 = _embed_figure(fig1, chart1_frame)
            state["canvases"].append(c1)
        else:
            ctk.CTkLabel(chart1_frame, text="Sem dados de historico.", font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED).pack(pady=40)

        # ── Grafico 2: Evolucao por item ───────────────────────────────────────
        all_names = stock_manager.get_all_item_names(history)

        sec2_lbl = ctk.CTkLabel(
            charts_scroll,
            text="Evolucao do Preco por Item",
            font=theme.FONT_SUBHEADING,
            text_color=theme.RED_PRIMARY,
            anchor="w",
        )
        sec2_lbl.pack(fill="x", pady=(4, 2))

        if all_names:
            import tkinter as tk
            item_var = tk.StringVar(value=all_names[0])

            dropdown_row = ctk.CTkFrame(charts_scroll, fg_color="transparent")
            dropdown_row.pack(fill="x", pady=(0, 4))

            ctk.CTkLabel(dropdown_row, text="Item:", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(side="left", padx=(0, 8))
            item_dropdown = ctk.CTkOptionMenu(
                dropdown_row,
                variable=item_var,
                values=all_names,
                width=220,
                height=30,
                corner_radius=6,
                fg_color=theme.BLACK_HOVER,
                button_color=theme.RED_DEEP,
                button_hover_color=theme.RED_PRIMARY,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_SMALL,
            )
            item_dropdown.pack(side="left")

            chart2_frame = ctk.CTkFrame(charts_scroll, fg_color=theme.BLACK_CARD, corner_radius=8, height=260)
            chart2_frame.pack(fill="x", pady=(4, 12))
            chart2_frame.pack_propagate(False)

            canvas2_state: dict[str, Any] = {"canvas": None}

            def _update_item_chart(*_) -> None:
                if canvas2_state["canvas"]:
                    canvas2_state["canvas"].get_tk_widget().destroy()
                for w in chart2_frame.winfo_children():
                    w.destroy()

                item_data = stock_manager.compute_per_item_trend(history, item_var.get())
                imonths = item_data["months"]
                prices = [p if p is not None else 0 for p in item_data["prices"]]

                if imonths:
                    fig2 = Figure(figsize=(8, 2.8), dpi=96, facecolor=_DARK["fig_bg"])
                    ax2 = fig2.add_subplot(111, facecolor=_DARK["ax_bg"])
                    ax2.plot(imonths, prices, color=_DARK["line_color"], marker="o", linewidth=2, markersize=5)
                    ax2.fill_between(imonths, prices, alpha=0.15, color=_DARK["line_color"])
                    ax2.set_ylabel("R$ / unidade", color=_DARK["label"])
                    ax2.set_title(f"Preco Unitario: {item_var.get()}", color=_DARK["title"], pad=8)
                    _apply_dark(ax2, fig2)
                    fig2.tight_layout(pad=0.8)
                    c2 = _embed_figure(fig2, chart2_frame)
                    canvas2_state["canvas"] = c2
                    if c2 not in state["canvases"]:
                        state["canvases"].append(c2)
                else:
                    ctk.CTkLabel(chart2_frame, text="Sem historico para este item.", font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED).pack(pady=40)

            item_dropdown.configure(command=_update_item_chart)
            _update_item_chart()

        # ── Grafico 3: Comparativo preco atual vs encontrado ───────────────────
        price_results = getattr(page_ref, "_price_results", [])
        if price_results:
            data = storage.load_estoque()
            prices_map = {it["name"]: float(it.get("unit_price", 0)) for it in data.get("items", [])}

            names_cmp = []
            current_vals = []
            found_vals = []
            for res in price_results:
                name = res.get("item_name", "")
                found = res.get("found_price")
                if found is not None:
                    names_cmp.append(name[:20])
                    current_vals.append(prices_map.get(name, 0.0))
                    found_vals.append(found)

            if names_cmp:
                sec3_lbl = ctk.CTkLabel(
                    charts_scroll,
                    text="Comparativo: Preco Atual vs Encontrado",
                    font=theme.FONT_SUBHEADING,
                    text_color=theme.RED_PRIMARY,
                    anchor="w",
                )
                sec3_lbl.pack(fill="x", pady=(4, 2))

                chart3_height = max(200, len(names_cmp) * 38 + 40)
                chart3_frame = ctk.CTkFrame(charts_scroll, fg_color=theme.BLACK_CARD, corner_radius=8, height=chart3_height)
                chart3_frame.pack(fill="x", pady=(0, 12))
                chart3_frame.pack_propagate(False)

                fig3_h = max(2.5, len(names_cmp) * 0.5)
                fig3 = Figure(figsize=(8, fig3_h), dpi=96, facecolor=_DARK["fig_bg"])
                ax3 = fig3.add_subplot(111, facecolor=_DARK["ax_bg"])

                import numpy as np
                y_pos = range(len(names_cmp))
                bar_h = 0.35
                ax3.barh([y + bar_h / 2 for y in y_pos], current_vals, height=bar_h,
                         color=_DARK["bar2_current"], label="Atual")
                ax3.barh([y - bar_h / 2 for y in y_pos], found_vals, height=bar_h,
                         color=_DARK["bar2_found"], label="Encontrado")
                ax3.set_yticks(list(y_pos))
                ax3.set_yticklabels(names_cmp, color=_DARK["tick"], fontsize=8)
                ax3.set_xlabel("R$", color=_DARK["label"])
                ax3.set_title("Preco Atual vs Encontrado", color=_DARK["title"], pad=8)
                ax3.legend(facecolor=_DARK["ax_bg"], edgecolor=_DARK["spine"], labelcolor=_DARK["tick"])
                _apply_dark(ax3, fig3)
                fig3.tight_layout(pad=0.8)
                c3 = _embed_figure(fig3, chart3_frame)
                state["canvases"].append(c3)

    def _take_snapshot() -> None:
        data = storage.load_estoque()
        items = data.get("items", [])
        if not items:
            return
        history = storage.load_estoque_history()
        history = stock_manager.upsert_monthly_snapshot(history, items)
        storage.save_estoque_history(history)
        _render_charts()

    snapshot_btn.configure(command=_take_snapshot)
    _render_charts()
    page_ref._analytics_refresh = _render_charts
