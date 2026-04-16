"""Tab 1 do Estoque: tabela editavel de insumos com import/export CSV/XLSX."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from gui import theme
from modules import stock_manager
from utils import storage


def build_planilha_tab(parent: ctk.CTkFrame, app: Any, page_ref: Any) -> None:
    """Monta a aba de planilha de estoque dentro do frame pai (aba do CTkTabview)."""
    state = {"rows": []}  # lista de dicts com widgets de cada linha

    # ── Toolbar ────────────────────────────────────────────────────────────────
    toolbar = ctk.CTkFrame(parent, fg_color="transparent")
    toolbar.pack(fill="x", padx=16, pady=(12, 6))

    def _btn(text: str, cmd, color=theme.RED_PRIMARY) -> ctk.CTkButton:
        return ctk.CTkButton(
            toolbar,
            text=text,
            command=cmd,
            height=32,
            corner_radius=6,
            fg_color=color,
            hover_color=theme.RED_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_SMALL,
        )

    _btn("Importar CSV", lambda: _import_file("csv")).pack(side="left", padx=(0, 6))
    _btn("Importar XLSX", lambda: _import_file("xlsx")).pack(side="left", padx=(0, 6))
    _btn("Exportar CSV", _export_csv, color=theme.BLACK_HOVER).pack(side="left", padx=(0, 6))
    _btn("+ Novo Item", _add_new_row).pack(side="left", padx=(0, 6))

    total_label = ctk.CTkLabel(
        toolbar,
        text="Total: R$ 0,00",
        font=theme.FONT_BODY_BOLD,
        text_color=theme.TEXT_SUCCESS,
    )
    total_label.pack(side="right")

    # ── Cabecalho da tabela ────────────────────────────────────────────────────
    header_frame = ctk.CTkFrame(parent, fg_color=theme.BLACK_PANEL, corner_radius=6)
    header_frame.pack(fill="x", padx=16, pady=(0, 4))

    _COL_WIDTHS = [160, 100, 70, 80, 90, 80, 36, 36]
    _COL_LABELS = ["Nome", "Categoria", "Qtd", "Unidade", "Preco Unit.", "Total", "", ""]

    for col_idx, (label, width) in enumerate(zip(_COL_LABELS, _COL_WIDTHS)):
        ctk.CTkLabel(
            header_frame,
            text=label,
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            width=width,
            anchor="w" if col_idx < 6 else "center",
        ).pack(side="left", padx=(8 if col_idx == 0 else 4, 4), pady=4)

    # ── Tabela scrollavel ──────────────────────────────────────────────────────
    scroll = ctk.CTkScrollableFrame(
        parent,
        fg_color=theme.BLACK_SOFT,
        corner_radius=0,
        scrollbar_button_color=theme.RED_DEEP,
        scrollbar_button_hover_color=theme.RED_PRIMARY,
    )
    scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    # ── Funcoes internas ───────────────────────────────────────────────────────

    def _update_total() -> None:
        items = _collect_items_from_rows()
        total = stock_manager.calculate_total_value(items)
        total_label.configure(text=f"Total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    def _collect_items_from_rows() -> list[dict[str, Any]]:
        items = []
        for row in state["rows"]:
            try:
                qty = float(row["qty_var"].get().replace(",", ".") or 0)
                price = float(row["price_var"].get().replace(",", ".") or 0)
            except ValueError:
                qty, price = 0.0, 0.0
            items.append({
                "id": row["item_id"],
                "name": row["name_var"].get(),
                "category": row["cat_var"].get(),
                "quantity": qty,
                "unit": row["unit_var"].get() or "unidades",
                "unit_price": price,
                "supplier": row.get("supplier", ""),
                "notes": row.get("notes", ""),
                "last_updated": row.get("last_updated", ""),
            })
        return items

    def _render_rows(items: list[dict[str, Any]]) -> None:
        for w in scroll.winfo_children():
            w.destroy()
        state["rows"].clear()
        for item in items:
            _append_row(item)
        _update_total()

    def _append_row(item: dict[str, Any]) -> None:
        row_frame = ctk.CTkFrame(scroll, fg_color=theme.BLACK_CARD, corner_radius=6)
        row_frame.pack(fill="x", pady=2)

        name_var = tk.StringVar(value=item.get("name", ""))
        cat_var = tk.StringVar(value=item.get("category", ""))
        qty_var = tk.StringVar(value=str(item.get("quantity", 0)))
        unit_var = tk.StringVar(value=item.get("unit", "unidades"))
        price_var = tk.StringVar(value=str(item.get("unit_price", 0)))

        def _make_entry(var: tk.StringVar, width: int) -> ctk.CTkEntry:
            e = ctk.CTkEntry(
                row_frame,
                textvariable=var,
                width=width,
                height=30,
                corner_radius=4,
                fg_color=theme.BLACK_HOVER,
                border_color=theme.BLACK_BORDER,
                text_color=theme.TEXT_PRIMARY,
                font=theme.FONT_SMALL,
            )
            var.trace_add("write", lambda *_: _update_total_label(row_data))
            return e

        total_var = tk.StringVar(value="R$ 0,00")

        name_entry = _make_entry(name_var, 160)
        cat_entry = _make_entry(cat_var, 100)
        qty_entry = _make_entry(qty_var, 70)
        unit_entry = _make_entry(unit_var, 80)
        price_entry = _make_entry(price_var, 90)

        total_lbl = ctk.CTkLabel(
            row_frame,
            textvariable=total_var,
            width=80,
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_SUCCESS,
            anchor="w",
        )

        save_btn = ctk.CTkButton(
            row_frame,
            text="✓",
            width=36,
            height=30,
            corner_radius=4,
            fg_color=theme.RED_DEEP,
            hover_color=theme.RED_PRIMARY,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_SMALL,
        )
        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            width=36,
            height=30,
            corner_radius=4,
            fg_color=theme.BLACK_HOVER,
            hover_color="#5a0010",
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL,
        )

        for widget in [name_entry, cat_entry, qty_entry, unit_entry, price_entry, total_lbl, save_btn, del_btn]:
            widget.pack(side="left", padx=4, pady=4)

        row_data: dict[str, Any] = {
            "frame": row_frame,
            "item_id": item.get("id", ""),
            "name_var": name_var,
            "cat_var": cat_var,
            "qty_var": qty_var,
            "unit_var": unit_var,
            "price_var": price_var,
            "total_var": total_var,
            "supplier": item.get("supplier", ""),
            "notes": item.get("notes", ""),
            "last_updated": item.get("last_updated", ""),
        }

        def _update_total_label(row: dict[str, Any]) -> None:
            try:
                qty = float(row["qty_var"].get().replace(",", ".") or 0)
                price = float(row["price_var"].get().replace(",", ".") or 0)
                total = qty * price
                row["total_var"].set(f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            except ValueError:
                pass
            _update_total()

        # Bind save/delete with closures
        def _save_row(row: dict[str, Any]) -> None:
            items_all = _collect_items_from_rows()
            data = storage.load_estoque()
            data["items"] = items_all
            data["updated_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
            storage.save_estoque(data)
            history = storage.load_estoque_history()
            history = stock_manager.upsert_monthly_snapshot(history, items_all)
            storage.save_estoque_history(history)
            page_ref._price_results = []
            _update_total()

        def _delete_row(row: dict[str, Any]) -> None:
            if not messagebox.askyesno("Confirmar", f"Deletar '{row['name_var'].get()}'?"):
                return
            row["frame"].destroy()
            state["rows"] = [r for r in state["rows"] if r is not row]
            _save_row(None)  # type: ignore[arg-type]

        save_btn.configure(command=lambda r=row_data: _save_row(r))
        del_btn.configure(command=lambda r=row_data: _delete_row(r))

        _update_total_label(row_data)
        state["rows"].append(row_data)

    def _add_new_row() -> None:
        item = stock_manager.new_item("Novo Item", 1, 0.0)
        _append_row(item)
        _update_total()

    def _import_file(fmt: str) -> None:
        filetypes = (
            [("CSV files", "*.csv"), ("All files", "*.*")]
            if fmt == "csv"
            else [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        path = filedialog.askopenfilename(
            title="Importar Planilha de Estoque",
            filetypes=filetypes,
        )
        if not path:
            return
        try:
            if fmt == "csv":
                with open(path, encoding="utf-8-sig") as f:
                    imported = stock_manager.parse_csv_text(f.read())
            else:
                with open(path, "rb") as f:
                    imported = stock_manager.parse_xlsx_bytes(f.read())
        except Exception as exc:
            messagebox.showerror("Erro ao importar", str(exc))
            return

        if not imported:
            messagebox.showinfo("Importar", "Nenhum item encontrado na planilha.")
            return

        data = storage.load_estoque()
        existing_names = {it["name"].lower() for it in data["items"]}
        added = 0
        for item in imported:
            if item["name"].lower() not in existing_names:
                data["items"].append(item)
                existing_names.add(item["name"].lower())
                added += 1

        data["updated_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
        storage.save_estoque(data)
        _render_rows(data["items"])
        messagebox.showinfo("Importar", f"{added} item(ns) importado(s).")

    def _export_csv() -> None:
        path = filedialog.asksaveasfilename(
            title="Exportar Estoque CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="estoque.csv",
        )
        if not path:
            return
        items = _collect_items_from_rows()
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(stock_manager.export_to_csv(items))
            messagebox.showinfo("Exportar", f"Estoque exportado para:\n{path}")
        except Exception as exc:
            messagebox.showerror("Erro ao exportar", str(exc))

    # ── Carrega dados iniciais ─────────────────────────────────────────────────
    data = storage.load_estoque()
    _render_rows(data.get("items", []))
