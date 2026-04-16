"""Tab 2 do Estoque: busca inteligente de precos (web + IA)."""

from __future__ import annotations

import webbrowser
from typing import Any

import customtkinter as ctk

from gui import theme
from gui.async_worker import AsyncTask
from modules import stock_manager
from utils import storage


def build_preco_tab(parent: ctk.CTkFrame, app: Any, page_ref: Any) -> None:
    """Monta a aba de busca de precos."""

    main = ctk.CTkFrame(parent, fg_color="transparent")
    main.pack(fill="both", expand=True, padx=8, pady=8)
    main.grid_columnconfigure(0, weight=1)
    main.grid_columnconfigure(1, weight=2)
    main.grid_rowconfigure(0, weight=1)

    # ── Painel esquerdo: seletor de itens ──────────────────────────────────────
    left = ctk.CTkFrame(main, fg_color=theme.BLACK_PANEL, corner_radius=8)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

    ctk.CTkLabel(
        left,
        text="Selecionar Itens",
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

    btn_frame = ctk.CTkFrame(left, fg_color="transparent")
    btn_frame.pack(fill="x", padx=8, pady=(0, 10))

    web_btn = ctk.CTkButton(
        btn_frame,
        text="Buscar na Web",
        height=34,
        corner_radius=6,
        fg_color=theme.RED_PRIMARY,
        hover_color=theme.RED_HOVER,
        text_color=theme.TEXT_PRIMARY,
        font=theme.FONT_SMALL,
    )
    web_btn.pack(fill="x", pady=(0, 4))

    ai_btn = ctk.CTkButton(
        btn_frame,
        text="Sugerir via IA",
        height=34,
        corner_radius=6,
        fg_color=theme.RED_DEEP,
        hover_color=theme.RED_PRIMARY,
        text_color=theme.TEXT_PRIMARY,
        font=theme.FONT_SMALL,
    )
    ai_btn.pack(fill="x")

    # ── Painel direito: resultados ─────────────────────────────────────────────
    right = ctk.CTkFrame(main, fg_color=theme.BLACK_PANEL, corner_radius=8)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    ctk.CTkLabel(
        right,
        text="Resultados",
        font=theme.FONT_BODY_BOLD,
        text_color=theme.RED_PRIMARY,
        anchor="w",
    ).pack(fill="x", padx=12, pady=(10, 6))

    ctk.CTkFrame(right, height=1, fg_color=theme.BLACK_BORDER).pack(fill="x", padx=12, pady=(0, 6))

    results_scroll = ctk.CTkScrollableFrame(
        right,
        fg_color="transparent",
        scrollbar_button_color=theme.RED_DEEP,
        scrollbar_button_hover_color=theme.RED_PRIMARY,
    )
    results_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    status_lbl = ctk.CTkLabel(
        right,
        text="",
        font=theme.FONT_SMALL,
        text_color=theme.TEXT_MUTED,
    )
    status_lbl.pack(pady=(0, 8))

    # ── Estado ────────────────────────────────────────────────────────────────
    state: dict[str, Any] = {"check_vars": []}

    def _load_items() -> None:
        for w in items_scroll.winfo_children():
            w.destroy()
        state["check_vars"].clear()
        data = storage.load_estoque()
        items = data.get("items", [])
        if not items:
            ctk.CTkLabel(
                items_scroll,
                text="Nenhum item no estoque.",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
            ).pack(pady=20)
            return
        for item in items:
            import tkinter as tk
            check_var = tk.BooleanVar(value=True)
            row = ctk.CTkFrame(items_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkCheckBox(
                row,
                text=item.get("name", ""),
                variable=check_var,
                height=24,
                corner_radius=4,
                fg_color=theme.RED_DEEP,
                hover_color=theme.RED_PRIMARY,
                checkmark_color=theme.TEXT_PRIMARY,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_SMALL,
            ).pack(side="left", padx=4)
            ctk.CTkLabel(
                row,
                text=f"R$ {float(item.get('unit_price', 0)):.2f}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                anchor="e",
            ).pack(side="right", padx=4)
            state["check_vars"].append({"item": item, "check_var": check_var})

    def _get_selected() -> list[dict[str, Any]]:
        return [cv["item"] for cv in state["check_vars"] if cv["check_var"].get()]

    def _set_loading(loading: bool) -> None:
        state_text = "disabled" if loading else "normal"
        web_btn.configure(state=state_text)
        ai_btn.configure(state=state_text)
        if loading:
            status_lbl.configure(text="Buscando...", text_color=theme.TEXT_WARNING)
        else:
            status_lbl.configure(text="")

    def _clear_results() -> None:
        for w in results_scroll.winfo_children():
            w.destroy()

    def _render_web_results(results: list[dict[str, Any]]) -> None:
        _clear_results()
        if not results:
            ctk.CTkLabel(
                results_scroll,
                text="Nenhum resultado encontrado.",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        page_ref._price_results = results

        data = storage.load_estoque()
        prices_map = {it["name"]: float(it.get("unit_price", 0)) for it in data.get("items", [])}

        for res in results:
            name = res.get("item_name", "")
            current = prices_map.get(name, 0.0)
            found = res.get("found_price")
            url = res.get("source_url", "")

            card = ctk.CTkFrame(results_scroll, fg_color=theme.BLACK_CARD, corner_radius=6)
            card.pack(fill="x", pady=3, padx=2)

            ctk.CTkLabel(
                card,
                text=name,
                font=theme.FONT_BODY_BOLD,
                text_color=theme.TEXT_PRIMARY,
                anchor="w",
            ).pack(fill="x", padx=10, pady=(8, 2))

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=(0, 6))

            ctk.CTkLabel(
                row,
                text=f"Atual: R$ {current:.2f}",
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_SECONDARY,
            ).pack(side="left")

            if found is not None:
                savings_pct = ((current - found) / current * 100) if current > 0 else 0
                color = theme.TEXT_SUCCESS if savings_pct > 10 else (theme.TEXT_WARNING if savings_pct > 5 else theme.TEXT_PRIMARY)
                ctk.CTkLabel(
                    row,
                    text=f"   Encontrado: R$ {found:.2f}",
                    font=theme.FONT_SMALL,
                    text_color=color,
                ).pack(side="left")
                if savings_pct > 0:
                    ctk.CTkLabel(
                        row,
                        text=f"   -{savings_pct:.0f}%",
                        font=theme.FONT_BODY_BOLD,
                        text_color=color,
                    ).pack(side="left")
            else:
                ctk.CTkLabel(
                    row,
                    text="   Preco nao encontrado",
                    font=theme.FONT_SMALL,
                    text_color=theme.TEXT_MUTED,
                ).pack(side="left")

            if url:
                ctk.CTkButton(
                    row,
                    text="Abrir",
                    width=60,
                    height=24,
                    corner_radius=4,
                    fg_color=theme.BLACK_HOVER,
                    hover_color=theme.BLACK_BORDER,
                    text_color=theme.TEXT_SECONDARY,
                    font=theme.FONT_SMALL,
                    command=lambda u=url: webbrowser.open(u),
                ).pack(side="right")

        status_lbl.configure(
            text=f"{len(results)} resultado(s) — {res.get('source', '')}",
            text_color=theme.TEXT_SUCCESS,
        )

    def _render_ai_result(text: str) -> None:
        _clear_results()
        box = ctk.CTkTextbox(
            results_scroll,
            fg_color=theme.BLACK_CARD,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_MONO,
            corner_radius=6,
            wrap="word",
            activate_scrollbars=True,
        )
        box.pack(fill="both", expand=True, padx=2, pady=2)
        box.insert("1.0", text)
        box.configure(state="disabled")
        status_lbl.configure(text="Sugestoes da IA geradas.", text_color=theme.TEXT_SUCCESS)

    def _search_web() -> None:
        selected = _get_selected()
        if not selected:
            return
        item_names = [it["name"] for it in selected]
        _set_loading(True)
        _clear_results()

        task = AsyncTask(app)
        task.run(
            coro_factory=lambda: stock_manager.search_prices_web(item_names),
            on_result=lambda r: (_render_web_results(r), _set_loading(False)),
            on_error=lambda e: (
                status_lbl.configure(text=f"Erro: {e}", text_color=theme.TEXT_DANGER),
                _set_loading(False),
            ),
        )

    def _search_ai() -> None:
        selected = _get_selected()
        if not selected:
            return
        item_names = [it["name"] for it in selected]
        current_prices = {it["name"]: float(it.get("unit_price", 0)) for it in selected}
        settings = app.settings
        _set_loading(True)
        _clear_results()

        task = AsyncTask(app)
        task.run(
            coro_factory=lambda: stock_manager.search_prices_ai(item_names, current_prices, settings),
            on_result=lambda r: (_render_ai_result(r), _set_loading(False)),
            on_error=lambda e: (
                status_lbl.configure(text=f"Erro: {e}", text_color=theme.TEXT_DANGER),
                _set_loading(False),
            ),
        )

    web_btn.configure(command=_search_web)
    ai_btn.configure(command=_search_ai)

    _load_items()
    page_ref._preco_reload = _load_items
