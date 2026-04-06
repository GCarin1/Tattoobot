"""Registro e visualizacao de crescimento."""

from datetime import datetime

from modules import ollama_client
from utils import storage, display


async def log_growth(settings: dict) -> None:
    """Registra metricas de hoje via input interativo."""
    display.console.print()
    display.show_panel(
        "TattooBot Copilot - Registrar Metricas",
        "Preencha as metricas de hoje. Campos opcionais podem ficar em branco.",
        style="green",
    )

    followers_str = display.ask_input("Numero de seguidores atual")
    if not followers_str:
        display.show_error("Numero de seguidores e obrigatorio.")
        return

    try:
        followers = int(followers_str.replace(".", "").replace(",", ""))
    except ValueError:
        display.show_error("Valor invalido para seguidores. Use apenas numeros.")
        return

    reach_str = display.ask_input("Alcance da ultima semana (opcional)", default="0")
    engagement_str = display.ask_input("Engajamento medio % (opcional)", default="0")
    bookings_str = display.ask_input("Novos agendamentos (opcional)", default="0")
    notes = display.ask_input("Observacoes (opcional)", default="")

    entry = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "timestamp": datetime.now().isoformat(),
        "followers": followers,
        "reach": int(reach_str) if reach_str.isdigit() else 0,
        "engagement": float(engagement_str.replace(",", ".")) if engagement_str.replace(",", "").replace(".", "").isdigit() else 0.0,
        "bookings": int(bookings_str) if bookings_str.isdigit() else 0,
        "notes": notes,
    }

    growth = storage.load_growth()
    growth.append(entry)
    storage.save_growth(growth)

    display.show_success(f"Metricas de hoje registradas! Seguidores: {followers:,}")

    # Mostrar variacao se tiver dados anteriores
    if len(growth) >= 2:
        prev = growth[-2]["followers"]
        diff = followers - prev
        pct = (diff / prev * 100) if prev else 0
        sign = "+" if diff >= 0 else ""
        display.show_info(f"Variacao: {sign}{diff} ({sign}{pct:.1f}%) desde ultimo registro")


async def show_growth(settings: dict) -> None:
    """Exibe evolucao de metricas."""
    growth = storage.load_growth()

    if not growth:
        display.show_info("Nenhum registro de crescimento ainda.")
        display.show_tip("Use 'tattoobot growth log' para registrar as metricas de hoje.")
        return

    display.console.print()
    display.show_panel(
        "TattooBot Copilot - Growth Tracker",
        f"{len(growth)} registros encontrados",
        style="green",
    )

    # Calcular metricas gerais
    first = growth[0]
    last = growth[-1]
    total_diff = last["followers"] - first["followers"]
    total_pct = (total_diff / first["followers"] * 100) if first["followers"] else 0

    display.console.print()
    display.console.print(
        f"  Seguidores: [bold]{first['followers']:,}[/bold] -> "
        f"[bold green]{last['followers']:,}[/bold green] "
        f"({'+' if total_diff >= 0 else ''}{total_diff:,}, "
        f"{'+' if total_pct >= 0 else ''}{total_pct:.1f}%)"
    )

    if len(growth) >= 2:
        period_text = f"  Periodo: {first['date']} ate {last['date']}"
        display.console.print(period_text, style="dim")

    # Calcular media semanal
    if len(growth) >= 7:
        last_7 = growth[-7:]
        weekly_diff = last_7[-1]["followers"] - last_7[0]["followers"]
        display.console.print(f"  Media semanal: {'+' if weekly_diff >= 0 else ''}{weekly_diff} seguidores")

    # Grafico ASCII
    follower_data = [e["followers"] for e in growth[-30:]]
    display.show_growth_chart(follower_data)

    # Tabela com ultimos registros
    table = display.create_table(
        "Historico de Crescimento",
        [
            ("Data", "cyan"),
            ("Seguidores", "green"),
            ("Alcance", "yellow"),
            ("+/-", "bold"),
        ],
    )

    entries = growth[-30:]  # Ultimos 30
    for i, entry in enumerate(entries):
        diff = ""
        if i > 0:
            d = entry["followers"] - entries[i - 1]["followers"]
            diff = f"{'+'if d >= 0 else ''}{d}"

        table.add_row(
            entry["date"],
            f"{entry['followers']:,}",
            f"{entry.get('reach', 0):,}" if entry.get("reach") else "-",
            diff,
        )

    display.console.print(table)

    # Analise IA (se tiver dados suficientes)
    if len(growth) >= 5:
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        ollama_model = settings.get("ollama_model", "llama3")

        recent = growth[-7:]
        data_summary = ", ".join(
            f"{e['date']}: {e['followers']} seg" + (f" (nota: {e['notes']})" if e.get("notes") else "")
            for e in recent
        )

        prompt = (
            f"Voce e um analista de crescimento no Instagram.\n"
            f"Dados recentes do perfil de um tatuador:\n{data_summary}\n\n"
            f"Em 2-3 frases curtas, analise a tendencia e de uma dica pratica "
            f"para melhorar o crescimento. Responda em portugues brasileiro."
        )
        analysis = await ollama_client.generate(prompt, ollama_url, ollama_model)
        if analysis:
            display.show_tip(f"Analise IA: {analysis}")


async def export_growth() -> None:
    """Exporta dados de crescimento como tabela formatada."""
    growth = storage.load_growth()

    if not growth:
        display.show_info("Nenhum registro para exportar.")
        return

    table = display.create_table(
        "Exportacao de Dados",
        [
            ("Data", "cyan"),
            ("Seguidores", "green"),
            ("Alcance", "yellow"),
            ("Engajamento %", "magenta"),
            ("Agendamentos", "blue"),
            ("Notas", "dim"),
        ],
    )

    for entry in growth:
        table.add_row(
            entry["date"],
            f"{entry['followers']:,}",
            f"{entry.get('reach', 0):,}" if entry.get("reach") else "-",
            f"{entry.get('engagement', 0):.1f}%" if entry.get("engagement") else "-",
            str(entry.get("bookings", 0)) if entry.get("bookings") else "-",
            entry.get("notes", "")[:40],
        )

    display.console.print(table)
    display.show_info(f"Total: {len(growth)} registros")
