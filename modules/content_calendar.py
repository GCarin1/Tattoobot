"""Gerador de calendario de conteudo mensal/semanal para Instagram."""

import csv
import json
import re
from datetime import datetime, timedelta
from io import StringIO

from modules import ai_client
from utils import display, storage


PT_MONTHS = {
    1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

SEASONAL = {
    1: "ferias de verao, virada de ano, metas novas, projetos grandes",
    2: "carnaval, pele exposta, cuidados pos-tattoo no calor",
    3: "volta as aulas, outono chegando, retomada de agenda",
    4: "outono, pascoa, clima ameno ideal para sessoes longas",
    5: "dia das maes, homenagens familiares, outono pleno",
    6: "festa junina, dia dos namorados, tattoos de casal",
    7: "ferias de julho, inverno, pele coberta (ideal pra sessoes extensas)",
    8: "dia dos pais, inverno, projetos longos, manga comprida",
    9: "primavera, renovacao, temas florais, cores",
    10: "outubro rosa, halloween, dark art, conscientizacao",
    11: "black friday, flash day, promocoes de estudio",
    12: "fim de ano, retrospectiva, agenda cheia, presentes",
}

CONTENT_TYPES = ["Reel", "Carrossel", "Story", "Post"]


def _get_week_days(start_date: datetime, post_days: list[int]) -> list[datetime]:
    """Retorna datas da semana que correspondem aos dias de postagem.

    post_days: lista de ints (0=seg, 1=ter, ..., 6=dom)
    """
    days = []
    for offset in range(7):
        d = start_date + timedelta(days=offset)
        if d.weekday() in post_days:
            days.append(d)
    return days


def _build_calendar_prompt(
    tattoo_style: str,
    artist_city: str,
    posts_per_week: int,
    period: str,
    month: int,
    year: int,
    secondary_style: str,
) -> str:
    month_pt = PT_MONTHS.get(month, "")
    seasonal = SEASONAL.get(month, "")
    style_ctx = tattoo_style
    if secondary_style:
        style_ctx += f" e {secondary_style}"

    return (
        f"Voce e um estrategista de conteudo para tatuadores no Instagram em {year}.\n"
        f"O artista trabalha com {style_ctx}{' em ' + artist_city if artist_city else ''}.\n"
        f"Mes: {month_pt}/{year}. Contexto sazonal: {seasonal}.\n\n"
        f"Crie um calendario de conteudo para {period} com exatamente {posts_per_week} posts por semana.\n\n"
        f"Para cada post, forneca:\n"
        f"- DIA: dia da semana (ex: Segunda, Terca, ...)\n"
        f"- FORMATO: Reel / Carrossel / Story / Post\n"
        f"- TITULO: titulo especifico e criativo\n"
        f"- OBJETIVO: engajamento / alcance / conversao / autoridade\n"
        f"- DICA: como executar bem (1 frase)\n\n"
        f"Distribua os formatos de forma equilibrada (nao coloque so Reels).\n"
        f"Considere o contexto sazonal em pelo menos 2 posts.\n"
        f"Retorne em JSON no formato:\n"
        f'{{\n'
        f'  "period": "{period}",\n'
        f'  "month": "{month_pt}/{year}",\n'
        f'  "posts": [\n'
        f'    {{\n'
        f'      "week": 1,\n'
        f'      "day": "Segunda",\n'
        f'      "format": "Reel",\n'
        f'      "title": "...",\n'
        f'      "objective": "alcance",\n'
        f'      "tip": "..."\n'
        f'    }}\n'
        f'  ]\n'
        f'}}\n\n'
        f"Retorne APENAS o JSON, sem texto adicional."
    )


def _parse_calendar_json(response: str) -> dict | None:
    """Extrai JSON do calendario da resposta do LLM."""
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _display_calendar(calendar: dict) -> None:
    """Exibe o calendario formatado no terminal."""
    from rich.table import Table
    from rich.panel import Panel

    console = display.console
    period = calendar.get("period", "")
    month = calendar.get("month", "")
    posts = calendar.get("posts", [])

    console.print()
    console.print(Panel(
        f"[bold]{period}[/bold] — {month}",
        title="[bold red]CALENDARIO DE CONTEUDO[/bold red]",
        border_style="red",
    ))

    if not posts:
        display.show_warning("Nenhum post no calendario gerado.")
        return

    FORMAT_COLORS = {
        "Reel": "bold red",
        "Carrossel": "bold yellow",
        "Story": "bold cyan",
        "Post": "bold white",
    }

    table = Table(
        show_header=True,
        header_style="bold red",
        border_style="dim",
        show_lines=True,
    )
    table.add_column("Sem.", style="dim", width=5)
    table.add_column("Dia", style="cyan", width=10)
    table.add_column("Formato", width=11)
    table.add_column("Titulo", style="white", min_width=25)
    table.add_column("Objetivo", style="dim", width=12)
    table.add_column("Dica", style="dim white", min_width=20)

    for post in posts:
        fmt = post.get("format", "Post")
        color = FORMAT_COLORS.get(fmt, "white")
        table.add_row(
            str(post.get("week", "")),
            post.get("day", ""),
            f"[{color}]{fmt}[/{color}]",
            post.get("title", ""),
            post.get("objective", ""),
            post.get("tip", ""),
        )

    console.print(table)

    # Resumo por formato
    console.print()
    from collections import Counter
    fmt_counts = Counter(p.get("format", "Post") for p in posts)
    summary = "  ".join(f"[bold]{fmt}[/bold]: {count}" for fmt, count in fmt_counts.items())
    console.print(f"[dim]Distribuicao:[/dim] {summary}")


def _export_csv(calendar: dict) -> str:
    """Exporta calendario como CSV. Retorna caminho do arquivo."""
    from config import DATA_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    month = calendar.get("month", "mes").replace("/", "-")
    out_path = DATA_DIR / f"calendario_{month}_{today}.csv"

    posts = calendar.get("posts", [])
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["week", "day", "format", "title", "objective", "tip"],
        )
        writer.writeheader()
        for post in posts:
            writer.writerow({
                "week": post.get("week", ""),
                "day": post.get("day", ""),
                "format": post.get("format", ""),
                "title": post.get("title", ""),
                "objective": post.get("objective", ""),
                "tip": post.get("tip", ""),
            })

    return str(out_path)


async def run_content_calendar(settings: dict) -> None:
    """Executa o gerador de calendario de conteudo."""
    tattoo_style = settings.get("tattoo_style", "blackwork")
    secondary_style = settings.get("tattoo_style_secondary", "")
    artist_city = settings.get("artist_city", "")

    display.console.print()
    display.show_panel(
        "Calendario de Conteudo",
        "Gera um plano de posts organizado por semana com formato e objetivo.",
        style="cyan",
    )

    # Periodo
    display.console.print()
    display.console.print("[bold]Periodo do calendario:[/bold]")
    display.console.print("  [yellow]1[/yellow]  1 semana")
    display.console.print("  [yellow]2[/yellow]  2 semanas")
    display.console.print("  [yellow]3[/yellow]  1 mes completo")
    display.console.print()
    period_choice = display.console.input("[bold cyan]Periodo (1-3) > [/bold cyan]").strip()
    period_map = {"1": "1 semana", "2": "2 semanas", "3": "1 mes"}
    period = period_map.get(period_choice, "1 semana")

    # Posts por semana
    posts_str = display.ask_input("Quantos posts por semana?", default="4")
    try:
        posts_per_week = int(posts_str)
    except ValueError:
        posts_per_week = 4

    now = datetime.now()

    prompt = _build_calendar_prompt(
        tattoo_style, artist_city, posts_per_week, period,
        now.month, now.year, secondary_style
    )

    display.console.print("[dim]Gerando calendario com IA...[/dim]")
    response = await ai_client.generate(prompt, settings, temperature=0.85)

    if not response:
        display.show_error("Nao foi possivel gerar o calendario.")
        return

    calendar = _parse_calendar_json(response)

    if not calendar:
        display.console.print(response)
        display.show_warning("Nao foi possivel parsear o JSON. Exibindo resposta bruta.")
        return

    _display_calendar(calendar)

    # Salva no storage
    saved = storage.load_calendar()
    saved.append({
        "generated_at": now.isoformat(),
        **calendar,
    })
    if len(saved) > 12:
        saved = saved[-12:]
    storage.save_calendar(saved)

    # Exportar CSV?
    display.console.print()
    export = display.console.input("[bold cyan]Exportar como CSV? (s/N) > [/bold cyan]").strip().lower()
    if export == "s":
        csv_path = _export_csv(calendar)
        display.show_success(f"CSV exportado: {csv_path}")

    display.show_tip(
        "Dica: salve o calendario num app de notas ou planilha. "
        "Consistencia de postagem e mais importante que perfeicao!"
    )
