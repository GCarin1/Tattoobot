"""Utilitarios de renderizacao CLI com Rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()


def show_banner() -> None:
    """Exibe banner do TattooBot."""
    banner = Text()
    banner.append("  TattooBot Copilot  ", style="bold white on rgb(80,20,120)")
    banner.append(" v1.0", style="dim")
    console.print()
    console.print(banner)
    console.print("  Seu assistente de crescimento no Instagram", style="dim italic")
    console.print()


def show_panel(title: str, content: str, style: str = "cyan") -> None:
    """Exibe um painel estilizado."""
    console.print(Panel(content, title=title, border_style=style, padding=(1, 2)))


def show_error(message: str) -> None:
    """Exibe mensagem de erro."""
    console.print(f"[bold red]Erro:[/bold red] {message}")


def show_warning(message: str) -> None:
    """Exibe mensagem de aviso."""
    console.print(f"[bold yellow]Aviso:[/bold yellow] {message}")


def show_success(message: str) -> None:
    """Exibe mensagem de sucesso."""
    console.print(f"[bold green]OK:[/bold green] {message}")


def show_info(message: str) -> None:
    """Exibe mensagem informativa."""
    console.print(f"[bold blue]Info:[/bold blue] {message}")


def show_tip(message: str) -> None:
    """Exibe uma dica."""
    console.print(f"\n[bold yellow]Dica:[/bold yellow] {message}\n")


def show_profile_card(
    username: str,
    post_link: str,
    post_caption: str,
    comments: list[str],
) -> None:
    """Exibe card de perfil com sugestoes de comentario."""
    content_lines = []
    content_lines.append(f"[cyan]Link:[/cyan] {post_link}")
    if post_caption:
        caption_preview = post_caption[:80] + "..." if len(post_caption) > 80 else post_caption
        content_lines.append(f'[cyan]Post:[/cyan] "{caption_preview}"')
    content_lines.append("")
    content_lines.append("[bold]Sugestoes de comentario:[/bold]")
    for i, comment in enumerate(comments, 1):
        content_lines.append(f"  {i}. {comment}")

    panel_content = "\n".join(content_lines)
    console.print(Panel(
        panel_content,
        title=f"[bold]@{username}[/bold]",
        border_style="green",
        padding=(1, 2),
    ))


def show_engagement_header(date: str, count: int) -> None:
    """Exibe cabecalho do modulo de engajamento."""
    header = (
        f"  [bold]TattooBot Copilot - Engajamento Diario[/bold]\n"
        f"  {date} - {count} perfis selecionados"
    )
    console.print(Panel(header, border_style="magenta", padding=(1, 2)))


def show_engagement_footer() -> None:
    """Exibe rodape do modulo de engajamento."""
    console.print()
    console.print(
        "[bold yellow]Dica:[/bold yellow] Abra o Instagram no celular e interaja com esses perfis!"
    )
    console.print("   Tempo estimado: ~15 minutos", style="dim")
    console.print()


def create_table(title: str, columns: list[tuple[str, str]]) -> Table:
    """Cria tabela estilizada.

    columns: lista de (nome, style)
    """
    table = Table(title=title, box=box.ROUNDED, border_style="cyan")
    for name, style in columns:
        table.add_column(name, style=style)
    return table


def get_spinner() -> Progress:
    """Retorna progress bar com spinner."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def show_caption_result(
    captions: list[str],
    hashtags: str,
    ctas: list[str],
) -> None:
    """Exibe resultado do gerador de legendas."""
    for i, caption in enumerate(captions, 1):
        console.print(Panel(
            caption,
            title=f"[bold]Legenda {i}[/bold]",
            border_style="green",
            padding=(1, 2),
        ))

    console.print(Panel(
        hashtags,
        title="[bold]Hashtags[/bold]",
        border_style="blue",
        padding=(1, 2),
    ))

    for i, cta in enumerate(ctas, 1):
        console.print(f"  [bold cyan]CTA {i}:[/bold cyan] {cta}")
    console.print()


def show_idea_card(
    index: int,
    format_type: str,
    title: str,
    description: str,
    tip: str,
    hashtag: str,
) -> None:
    """Exibe card de ideia de conteudo."""
    format_icons = {
        "reel": "[red]REEL[/red]",
        "carrossel": "[blue]CARROSSEL[/blue]",
        "carousel": "[blue]CARROSSEL[/blue]",
        "story": "[magenta]STORY[/magenta]",
        "post": "[green]POST[/green]",
    }
    icon = format_icons.get(format_type.lower().strip(), format_type.upper())

    content = (
        f"[bold]{title}[/bold]\n"
        f"{description}\n"
        f"[yellow]Dica:[/yellow] {tip}\n"
        f"[dim]#{hashtag}[/dim]"
    )
    console.print(Panel(
        content,
        title=f"[bold]{index}. [{icon}][/bold]",
        border_style="cyan",
        padding=(0, 2),
    ))


def show_spy_card(
    username: str,
    stats: str,
    analysis: str,
) -> None:
    """Exibe card de analise de concorrente."""
    content = f"{stats}\n\n[bold]Analise IA:[/bold]\n{analysis}"
    console.print(Panel(
        content,
        title=f"[bold]@{username}[/bold]",
        border_style="red",
        padding=(1, 2),
    ))


def show_growth_chart(data: list[int], label: str = "seguidores") -> None:
    """Exibe grafico ASCII simples de evolucao."""
    if not data:
        return
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val if max_val != min_val else 1
    blocks = " _.:!|"
    chart = ""
    for val in data:
        level = int((val - min_val) / range_val * (len(blocks) - 1))
        chart += blocks[level]
    console.print(f"\n  {chart} <- tendencia de {label}\n", style="bold green")


def ask_input(prompt: str, default: str = "") -> str:
    """Solicita input do usuario com prompt estilizado."""
    if default:
        result = console.input(f"[bold cyan]{prompt}[/bold cyan] [{default}]: ")
        return result.strip() or default
    return console.input(f"[bold cyan]{prompt}[/bold cyan]: ").strip()


def ask_choice(prompt: str, choices: list[str]) -> str:
    """Solicita escolha do usuario."""
    console.print(f"\n[bold cyan]{prompt}[/bold cyan]")
    for i, choice in enumerate(choices, 1):
        console.print(f"  {i}. {choice}")
    while True:
        answer = console.input("[bold]Escolha (numero): [/bold]").strip()
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        console.print("[red]Opcao invalida. Tente novamente.[/red]")
