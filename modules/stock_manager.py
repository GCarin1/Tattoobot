"""Logica de negocio para gestao de estoque do tatuador."""

from __future__ import annotations

import csv
import re
import unicodedata
import uuid
from datetime import datetime
from io import StringIO
from typing import Any


# ─── CRUD ─────────────────────────────────────────────────────────────────────


def new_item(
    name: str,
    quantity: float,
    unit_price: float,
    category: str = "",
    unit: str = "unidades",
    supplier: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "category": category.strip(),
        "quantity": float(quantity),
        "unit": unit.strip() or "unidades",
        "unit_price": float(unit_price),
        "supplier": supplier.strip(),
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "notes": notes.strip(),
    }


def validate_item(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(item.get("name", "")).strip():
        errors.append("Nome nao pode ser vazio.")
    try:
        qty = float(item.get("quantity", 0))
        if qty < 0:
            errors.append("Quantidade nao pode ser negativa.")
    except (ValueError, TypeError):
        errors.append("Quantidade deve ser um numero.")
    try:
        price = float(item.get("unit_price", 0))
        if price < 0:
            errors.append("Preco unitario nao pode ser negativo.")
    except (ValueError, TypeError):
        errors.append("Preco unitario deve ser um numero.")
    return errors


def calculate_total_value(items: list[dict[str, Any]]) -> float:
    total = 0.0
    for item in items:
        try:
            total += float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
        except (ValueError, TypeError):
            pass
    return round(total, 2)


# ─── CSV / XLSX import ────────────────────────────────────────────────────────

_CSV_ALIASES: dict[str, list[str]] = {
    "name":       ["name", "nome", "produto", "item", "descricao", "description"],
    "quantity":   [
        "quantity", "quantidade", "qtd", "qty", "estoque",
        "qtd_atual", "quantidade_atual", "estoque_atual", "current_stock",
    ],
    "unit_price": [
        "unit_price", "preco", "price", "preco_unitario", "valor", "custo",
        "preco_unit", "valor_unitario", "preco_unit_",
    ],
    "category":   ["category", "categoria", "cat"],
    "unit":       ["unit", "unidade", "medida"],
    "supplier":   ["supplier", "fornecedor"],
    "notes":      ["notes", "nota", "observacao", "obs"],
}


def _strip_accents(text: str) -> str:
    """Remove acentos (NFKD + descarta combining chars)."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def _normalize_header(raw: str) -> str:
    key = _strip_accents(raw.strip().lower()).replace(" ", "_")
    for field, aliases in _CSV_ALIASES.items():
        if key in aliases:
            return field
    return key


def _parse_number(raw: Any, default: float = 0.0) -> float:
    """Converte string/numero em float, tolerante a formato BR.

    Aceita: '5', '5.75', '5,75', 'R$ 5,75', '1.234,56', '1,234.56'.
    Retorna `default` se nao for possivel converter.
    """
    if raw is None or raw == "":
        return default
    if isinstance(raw, (int, float)):
        return float(raw)
    s = re.sub(r"[^\d.,\-]", "", str(raw))
    if not s or s in {"-", ".", ","}:
        return default
    if "," in s and "." in s:
        # Se virgula vem depois do ponto: formato BR (1.234,56)
        # Se ponto vem depois da virgula: formato US (1,234.56)
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return default


def _parse_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in rows:
        norm = {_normalize_header(k): v for k, v in row.items()}
        name = str(norm.get("name", "") or "").strip()
        if not name:
            continue
        qty = _parse_number(norm.get("quantity"))
        price = _parse_number(norm.get("unit_price"))
        items.append(new_item(
            name=name,
            quantity=qty,
            unit_price=price,
            category=str(norm.get("category", "") or ""),
            unit=str(norm.get("unit", "") or "") or "unidades",
            supplier=str(norm.get("supplier", "") or ""),
            notes=str(norm.get("notes", "") or ""),
        ))
    return items


def parse_csv_text(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(text))
    return _parse_rows(list(reader))


def parse_xlsx_bytes(data: bytes) -> list[dict[str, Any]]:
    try:
        import openpyxl
    except ImportError as e:
        raise ImportError(
            "openpyxl nao instalado. Execute: pip install openpyxl"
        ) from e
    from io import BytesIO
    wb = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(c).strip() if c is not None else "" for c in rows[0]]
    dicts = [
        {
            headers[i]: cell if cell is not None else ""
            for i, cell in enumerate(row)
            if i < len(headers) and headers[i]
        }
        for row in rows[1:]
    ]
    return _parse_rows(dicts)


def export_to_csv(items: list[dict[str, Any]]) -> str:
    fields = ["name", "category", "quantity", "unit", "unit_price", "supplier", "notes"]
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(items)
    return out.getvalue()


# ─── Busca de precos ──────────────────────────────────────────────────────────


async def search_prices_web(
    item_names: list[str],
    delay: float = 1.5,
) -> list[dict[str, Any]]:
    """Busca precos no Mercado Livre para cada item."""
    import asyncio
    import httpx
    from bs4 import BeautifulSoup

    results: list[dict[str, Any]] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for name in item_names:
            query = name.replace(" ", "-")
            url = f"https://lista.mercadolivre.com.br/{query}"
            found_price: float | None = None
            found_url = url

            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Tenta seletores conhecidos do ML
                    price_tag = (
                        soup.select_one(".poly-price__current .andes-money-amount__fraction")
                        or soup.select_one(".price-tag-fraction")
                        or soup.select_one("[class*='price-tag-fraction']")
                    )
                    if price_tag:
                        raw = price_tag.get_text(strip=True).replace(".", "").replace(",", ".")
                        try:
                            found_price = float(raw)
                        except ValueError:
                            found_price = None
                    # Pega link do primeiro resultado
                    link = soup.select_one("a.poly-component__title") or soup.select_one("a.item__info-title")
                    if link and link.get("href"):
                        found_url = str(link["href"])
            except Exception:
                pass

            results.append({
                "item_name": name,
                "found_price": found_price,
                "source_url": found_url,
                "source": "Mercado Livre",
            })
            await asyncio.sleep(delay)

    return results


async def search_prices_ai(
    item_names: list[str],
    current_prices: dict[str, float],
    settings: dict[str, Any],
) -> str:
    """Usa IA (Ollama/OpenAI/Anthropic) para sugerir fornecedores mais baratos."""
    from modules.ollama_client import ask_ollama

    lines = []
    for name in item_names:
        price = current_prices.get(name)
        if price is not None:
            lines.append(f"- {name}: R$ {price:.2f}")
        else:
            lines.append(f"- {name}")

    item_list = "\n".join(lines)
    prompt = (
        "Voce e um especialista em compras para studios de tatuagem no Brasil.\n"
        "Analise esta lista de insumos com seus precos atuais e sugira:\n"
        "1. Onde comprar mais barato (sites, distribuidoras, atacadistas no Brasil)\n"
        "2. Preco estimado que voce encontraria\n"
        "3. Dica de economia\n\n"
        f"Insumos:\n{item_list}\n\n"
        "Responda em portugues, de forma objetiva e pratica."
    )

    url = settings.get("ollama_url", "http://localhost:11434")
    model = settings.get("ollama_model", "llama3")
    return await ask_ollama(prompt, url=url, model=model)


# ─── Orcamento ────────────────────────────────────────────────────────────────


def calculate_budget(
    selections: list[dict[str, Any]],
    labor_minutes: int = 0,
    labor_rate_per_hour: float = 0.0,
) -> dict[str, Any]:
    """
    selections: [{"item": item_dict, "quantity_used": float}]
    Retorna dicionario com linhas detalhadas e totais.
    """
    lines: list[dict[str, Any]] = []
    material_total = 0.0

    for sel in selections:
        item = sel["item"]
        qty_used = float(sel.get("quantity_used", 1))
        unit_price = float(item.get("unit_price", 0))
        subtotal = round(qty_used * unit_price, 2)
        material_total += subtotal
        lines.append({
            "name": item.get("name", ""),
            "unit": item.get("unit", "un"),
            "qty": qty_used,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    material_total = round(material_total, 2)
    labor_total = round((labor_minutes / 60.0) * labor_rate_per_hour, 2) if labor_minutes > 0 else 0.0
    grand_total = round(material_total + labor_total, 2)

    return {
        "lines": lines,
        "material_total": material_total,
        "labor_minutes": labor_minutes,
        "labor_rate_per_hour": labor_rate_per_hour,
        "labor_total": labor_total,
        "grand_total": grand_total,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def format_budget_text(budget: dict[str, Any]) -> str:
    lines = [
        f"Orcamento de Material — {budget['date']}",
        "=" * 40,
    ]
    for line in budget["lines"]:
        lines.append(
            f"  {line['qty']:.1f}x {line['name']:<22} R$ {line['subtotal']:>7.2f}"
        )
    lines.append("-" * 40)
    lines.append(f"  {'Material total:':<26} R$ {budget['material_total']:>7.2f}")
    if budget["labor_total"] > 0:
        lines.append(
            f"  {'Mao de obra'} ({budget['labor_minutes']}min "
            f"@ R${budget['labor_rate_per_hour']:.0f}/h):"
            f"  R$ {budget['labor_total']:>7.2f}"
        )
    lines.append("=" * 40)
    lines.append(f"  {'TOTAL DA SESSAO:':<26} R$ {budget['grand_total']:>7.2f}")
    return "\n".join(lines)


# ─── Analytics / Snapshots ────────────────────────────────────────────────────


def take_monthly_snapshot(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Cria snapshot do estado atual do estoque para historico mensal."""
    month = datetime.now().strftime("%Y-%m")
    total = calculate_total_value(items)
    return {
        "snapshot_date": month,
        "total_value": total,
        "item_count": len(items),
        "items_snapshot": [
            {
                "id": it.get("id", ""),
                "name": it.get("name", ""),
                "unit_price": float(it.get("unit_price", 0)),
                "quantity": float(it.get("quantity", 0)),
            }
            for it in items
        ],
    }


def upsert_monthly_snapshot(
    history: list[dict[str, Any]],
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Insere ou atualiza snapshot do mes atual no historico."""
    snapshot = take_monthly_snapshot(items)
    month = snapshot["snapshot_date"]
    for i, entry in enumerate(history):
        if entry.get("snapshot_date") == month:
            history[i] = snapshot
            return history
    history.append(snapshot)
    return history


def compute_monthly_trend(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Retorna dados prontos para grafico de valor total mensal."""
    sorted_history = sorted(history, key=lambda x: x.get("snapshot_date", ""))
    months: list[str] = []
    total_values: list[float] = []
    for entry in sorted_history:
        raw = entry.get("snapshot_date", "")
        try:
            dt = datetime.strptime(raw, "%Y-%m")
            label = dt.strftime("%b/%Y")
        except ValueError:
            label = raw
        months.append(label)
        total_values.append(float(entry.get("total_value", 0)))
    return {"months": months, "total_values": total_values}


def compute_per_item_trend(
    history: list[dict[str, Any]],
    item_name: str,
) -> dict[str, Any]:
    """Retorna evolucao do preco unitario de um item ao longo dos meses."""
    sorted_history = sorted(history, key=lambda x: x.get("snapshot_date", ""))
    months: list[str] = []
    prices: list[float | None] = []
    for entry in sorted_history:
        raw = entry.get("snapshot_date", "")
        try:
            dt = datetime.strptime(raw, "%Y-%m")
            label = dt.strftime("%b/%Y")
        except ValueError:
            label = raw
        months.append(label)
        found = None
        for snap_item in entry.get("items_snapshot", []):
            if snap_item.get("name", "").lower() == item_name.lower():
                found = float(snap_item.get("unit_price", 0))
                break
        prices.append(found)
    return {"months": months, "prices": prices, "item_name": item_name}


def get_all_item_names(history: list[dict[str, Any]]) -> list[str]:
    """Retorna todos os nomes de itens que apareceram no historico."""
    names: set[str] = set()
    for entry in history:
        for snap_item in entry.get("items_snapshot", []):
            name = snap_item.get("name", "").strip()
            if name:
                names.add(name)
    return sorted(names)
