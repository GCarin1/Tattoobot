"""TattooBot Copilot - Entry point CLI com Typer e menu interativo."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Adiciona diretorio raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import VERSION, APP_NAME
from utils import storage, display

app = typer.Typer(
    name="tattoobot",
    help=(
        "TattooBot Copilot - Seu assistente de crescimento no Instagram\n\n"
        "Assistente CLI para tatuadores que ajuda a ganhar seguidores "
        "de forma 100% segura, sem automacao na conta do Instagram.\n\n"
        "Execute sem argumentos para abrir o menu interativo."
    ),
    invoke_without_command=True,
    rich_markup_mode="rich",
)

# Subcomandos para spy
spy_app = typer.Typer(
    help="Monitora perfis de concorrentes",
    no_args_is_help=True,
)
app.add_typer(spy_app, name="spy")

# Subcomandos para growth
growth_app = typer.Typer(
    help="Registra e acompanha metricas de crescimento",
    no_args_is_help=True,
)
app.add_typer(growth_app, name="growth")

# Subcomandos para config
config_app = typer.Typer(
    help="Gerencia configuracoes do bot",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


def _run_async(coro) -> None:
    """Executa coroutine async de forma sincrona."""
    asyncio.run(coro)


# ─── Menu interativo ───


def _run_engage() -> None:
    """Executa modulo de engajamento."""
    settings = storage.load_settings()
    from modules.engagement import run_engagement
    _run_async(run_engagement(settings))


def _run_caption() -> None:
    """Executa modulo de legendas."""
    settings = storage.load_settings()
    from modules.caption import run_caption
    _run_async(run_caption(settings))


def _run_ideas_interactive() -> None:
    """Executa modulo de ideias (modo interativo)."""
    settings = storage.load_settings()
    from modules.content_ideas import run_ideas
    _run_async(run_ideas(settings, ""))


def _run_compare() -> None:
    """Executa modulo de comparacao de perfis."""
    settings = storage.load_settings()
    from modules.profile_comparator import run_profile_comparison
    _run_async(run_profile_comparison(settings))


def _run_evaluate() -> None:
    """Executa modulo de avaliacao de tatuagem."""
    settings = storage.load_settings()
    from modules.tattoo_evaluator import run_tattoo_evaluation
    _run_async(run_tattoo_evaluation(settings))


def _run_reels_menu() -> None:
    """Submenu do Assistente de Reels."""
    display.console.print()
    display.show_panel("Assistente de Reels", "Escolha o modo:", style="red")

    display.console.print("  [yellow]1[/yellow]  Criar Reel (so roteiro/script)")
    display.console.print("  [yellow]2[/yellow]  Criar Reel + video basico (moviepy)")
    display.console.print("  [yellow]3[/yellow]  Criar Reel + IA generativa de video (Runway/Pika)")
    display.console.print("  [yellow]4[/yellow]  Ver historico de roteiros")
    display.console.print("  [yellow]0[/yellow]  Voltar")
    display.console.print()

    choice = display.console.input("[bold cyan]Escolha > [/bold cyan]").strip()
    settings = storage.load_settings()
    from modules.reels_assistant import run_reels, run_reels_history

    if choice == "1":
        _run_async(run_reels(settings, mode="script"))
    elif choice == "2":
        _run_async(run_reels(settings, mode="video"))
    elif choice == "3":
        _run_async(run_reels(settings, mode="ai"))
    elif choice == "4":
        _run_async(run_reels_history(settings))


def _run_calendar() -> None:
    """Executa modulo de calendario de conteudo."""
    settings = storage.load_settings()
    from modules.content_calendar import run_content_calendar
    _run_async(run_content_calendar(settings))


def _run_dm_templates() -> None:
    """Executa modulo de templates de atendimento."""
    settings = storage.load_settings()
    from modules.dm_templates import run_dm_templates
    _run_async(run_dm_templates(settings))


def _run_bio_optimizer() -> None:
    """Executa modulo de otimizacao de bio."""
    settings = storage.load_settings()
    from modules.bio_optimizer import run_bio_optimizer
    _run_async(run_bio_optimizer(settings))


def _run_portfolio() -> None:
    """Executa modulo de curadoria de portfolio."""
    settings = storage.load_settings()
    from modules.portfolio_curator import run_portfolio_curator
    _run_async(run_portfolio_curator(settings))


def _run_spy_menu() -> None:
    """Submenu de spy."""
    from modules import competitor_spy

    display.console.print()
    display.show_panel("Spy de Concorrentes", "Escolha uma opcao:", style="red")

    choices = [
        ("1", "Adicionar concorrente"),
        ("2", "Remover concorrente"),
        ("3", "Listar concorrentes"),
        ("4", "Gerar relatorio"),
        ("0", "Voltar"),
    ]
    for key, label in choices:
        color = "red" if key == "0" else "white"
        display.console.print(f"  [bold yellow]{key}[/bold yellow]  [{color}]{label}[/{color}]")
    display.console.print()

    answer = display.console.input("[bold cyan]Escolha > [/bold cyan]").strip()

    if answer == "1":
        username = display.ask_input("Username do perfil (com ou sem @)")
        if username:
            _run_async(competitor_spy.add_competitor(username))
    elif answer == "2":
        username = display.ask_input("Username do perfil (com ou sem @)")
        if username:
            _run_async(competitor_spy.remove_competitor(username))
    elif answer == "3":
        _run_async(competitor_spy.list_competitors())
    elif answer == "4":
        settings = storage.load_settings()
        _run_async(competitor_spy.run_spy_report(settings))


def _run_growth_menu() -> None:
    """Submenu de growth."""
    from modules import growth_tracker

    display.console.print()
    display.show_panel("Growth Tracker", "Escolha uma opcao:", style="green")

    choices = [
        ("1", "Registrar metricas de hoje"),
        ("2", "Ver evolucao"),
        ("3", "Exportar dados"),
        ("0", "Voltar"),
    ]
    for key, label in choices:
        color = "red" if key == "0" else "white"
        display.console.print(f"  [bold yellow]{key}[/bold yellow]  [{color}]{label}[/{color}]")
    display.console.print()

    answer = display.console.input("[bold cyan]Escolha > [/bold cyan]").strip()

    settings = storage.load_settings()
    if answer == "1":
        _run_async(growth_tracker.log_growth(settings))
    elif answer == "2":
        _run_async(growth_tracker.show_growth(settings))
    elif answer == "3":
        _run_async(growth_tracker.export_growth())


def _run_config_menu() -> None:
    """Submenu de configuracoes."""
    display.console.print()
    display.show_panel("Configuracoes", "Escolha uma opcao:", style="blue")

    choices = [
        ("1", "Ver configuracoes atuais"),
        ("2", "Alterar uma configuracao"),
        ("3", "Wizard de setup inicial"),
        ("0", "Voltar"),
    ]
    for key, label in choices:
        color = "red" if key == "0" else "white"
        display.console.print(f"  [bold yellow]{key}[/bold yellow]  [{color}]{label}[/{color}]")
    display.console.print()

    answer = display.console.input("[bold cyan]Escolha > [/bold cyan]").strip()

    if answer == "1":
        _show_config()
    elif answer == "2":
        _interactive_config_set()
    elif answer == "3":
        _interactive_setup()


def _show_config() -> None:
    """Exibe configuracoes."""
    settings = storage.load_settings()
    table = display.create_table(
        "Configuracoes",
        [("Chave", "cyan"), ("Valor", "green")],
    )
    for key, value in settings.items():
        if isinstance(value, list):
            table.add_row(key, ", ".join(str(v) for v in value))
        else:
            table.add_row(key, str(value))
    display.console.print(table)


def _interactive_config_set() -> None:
    """Altera config de forma interativa."""
    settings = storage.load_settings()
    keys = list(settings.keys())

    display.console.print()
    for i, key in enumerate(keys, 1):
        val = settings[key]
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        display.console.print(f"  [bold yellow]{i}[/bold yellow]  [cyan]{key}[/cyan] = [dim]{val}[/dim]")
    display.console.print()

    answer = display.console.input("[bold cyan]Qual configuracao alterar (numero) > [/bold cyan]").strip()
    try:
        idx = int(answer) - 1
        if 0 <= idx < len(keys):
            key = keys[idx]
            current = settings[key]
            new_value = display.ask_input(f"Novo valor para {key}")
            if new_value:
                if isinstance(current, list):
                    settings[key] = [v.strip() for v in new_value.split(",")]
                elif isinstance(current, int):
                    settings[key] = int(new_value)
                else:
                    settings[key] = new_value
                storage.save_settings(settings)
                display.show_success(f"{key} = {settings[key]}")
            else:
                display.show_warning("Valor vazio, nada alterado.")
        else:
            display.show_error("Opcao invalida.")
    except ValueError:
        display.show_error("Opcao invalida.")


def _interactive_setup() -> None:
    """Wizard de setup."""
    display.show_panel("Setup Inicial", "Vamos configurar seu TattooBot Copilot!", style="magenta")
    settings = storage.load_settings()

    settings["artist_name"] = display.ask_input("Seu nome/apelido artistico", default=settings.get("artist_name", ""))
    settings["artist_city"] = display.ask_input("Sua cidade", default=settings.get("artist_city", ""))
    settings["tattoo_style"] = display.ask_input("Estilo principal (ex: blackwork, dotwork)", default=settings.get("tattoo_style", "blackwork"))

    hashtags_str = display.ask_input("Hashtags (separadas por virgula)", default=",".join(settings.get("hashtags", [])))
    settings["hashtags"] = [h.strip() for h in hashtags_str.split(",") if h.strip()]

    profiles_str = display.ask_input("Perfis por dia", default=str(settings.get("profiles_per_day", 10)))
    try:
        settings["profiles_per_day"] = int(profiles_str)
    except ValueError:
        settings["profiles_per_day"] = 10

    settings["ollama_model"] = display.ask_input("Modelo Ollama (ex: llama3, mistral)", default=settings.get("ollama_model", "llama3"))

    storage.save_settings(settings)
    display.console.print()
    display.show_success("Configuracao salva com sucesso!")


def run_interactive_menu() -> None:
    """Loop principal do menu interativo."""
    menu_actions = {
        "engage": _run_engage,
        "caption": _run_caption,
        "ideas": _run_ideas_interactive,
        "spy": _run_spy_menu,
        "compare": _run_compare,
        "growth": _run_growth_menu,
        "evaluate": _run_evaluate,
        "reels": _run_reels_menu,
        "calendar": _run_calendar,
        "dm": _run_dm_templates,
        "bio": _run_bio_optimizer,
        "portfolio": _run_portfolio,
        "config": _run_config_menu,
    }

    while True:
        display.show_banner()
        action = display.show_menu()

        if action == "exit":
            display.console.print()
            display.console.print("[bold magenta]Ate a proxima! Boas tattoos![/bold magenta]")
            display.console.print()
            break

        handler = menu_actions.get(action)
        if handler:
            display.console.print()
            try:
                handler()
            except KeyboardInterrupt:
                display.console.print("\n[dim]Operacao cancelada.[/dim]")
            except Exception as e:
                display.show_error(f"Erro: {e}")

            display.console.print()
            display.console.input("[dim]Pressione Enter para voltar ao menu...[/dim]")
            # Limpa tela antes de mostrar menu de novo
            display.console.clear()


# ─── Comandos CLI diretos (para uso via terminal sem menu) ───


@app.command()
def engage() -> None:
    """Gera lista diaria de perfis pra engajar com sugestoes de comentarios."""
    display.show_banner()
    _run_engage()


@app.command()
def caption() -> None:
    """Gera legendas otimizadas com SEO, hashtags e CTA."""
    display.show_banner()
    _run_caption()


@app.command()
def compare() -> None:
    """Compara seu perfil com um rival e gera plano de acao para supera-lo."""
    display.show_banner()
    _run_compare()


@app.command()
def evaluate() -> None:
    """Avalia uma imagem de tatuagem com IA e marca pontos de melhoria."""
    display.show_banner()
    _run_evaluate()


@app.command()
def reels(
    mode: Optional[str] = typer.Argument(
        None,
        help="Modo: 'script' (padrao), 'video' (moviepy), 'ai' (IA generativa)",
    ),
) -> None:
    """Cria roteiro completo de Reel (script, texto, hashtags e opcao de video)."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.reels_assistant import run_reels
    _run_async(run_reels(settings, mode=mode or "script"))


@app.command()
def calendar() -> None:
    """Gera calendario de conteudo semanal ou mensal."""
    display.show_banner()
    _run_calendar()


@app.command()
def dm() -> None:
    """Gerencia templates de atendimento para DM e WhatsApp."""
    display.show_banner()
    _run_dm_templates()


@app.command()
def bio() -> None:
    """Analisa e otimiza sua bio do Instagram."""
    display.show_banner()
    _run_bio_optimizer()


@app.command()
def portfolio() -> None:
    """Curadoria de portfolio: analisa fotos e sugere o que e quando postar."""
    display.show_banner()
    _run_portfolio()


@app.command()
def ideas(
    theme: Optional[str] = typer.Argument(
        None, help="Tema especifico para as ideias (opcional)"
    ),
) -> None:
    """Sugere ideias de conteudo para Instagram."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.content_ideas import run_ideas
    _run_async(run_ideas(settings, theme or ""))


# ─── Spy subcomandos ───


@spy_app.command("add")
def spy_add(
    username: str = typer.Argument(..., help="Username do perfil (com ou sem @)"),
) -> None:
    """Adiciona perfil a lista de monitoramento."""
    display.show_banner()
    from modules.competitor_spy import add_competitor
    _run_async(add_competitor(username))


@spy_app.command("remove")
def spy_remove(
    username: str = typer.Argument(..., help="Username do perfil (com ou sem @)"),
) -> None:
    """Remove perfil da lista de monitoramento."""
    display.show_banner()
    from modules.competitor_spy import remove_competitor
    _run_async(remove_competitor(username))


@spy_app.command("list")
def spy_list() -> None:
    """Lista perfis monitorados."""
    display.show_banner()
    from modules.competitor_spy import list_competitors
    _run_async(list_competitors())


@spy_app.command("report")
def spy_report() -> None:
    """Gera relatorio de atividade dos concorrentes."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.competitor_spy import run_spy_report
    _run_async(run_spy_report(settings))


# ─── Growth subcomandos ───


@growth_app.command("log")
def growth_log() -> None:
    """Registrar metricas de hoje."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.growth_tracker import log_growth
    _run_async(log_growth(settings))


@growth_app.command("show")
def growth_show() -> None:
    """Exibir evolucao de crescimento."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.growth_tracker import show_growth
    _run_async(show_growth(settings))


@growth_app.command("export")
def growth_export() -> None:
    """Exportar dados como tabela."""
    display.show_banner()
    from modules.growth_tracker import export_growth
    _run_async(export_growth())


# ─── Config subcomandos ───


@config_app.command("show")
def config_show() -> None:
    """Exibe configuracoes atuais."""
    display.show_banner()
    _show_config()


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Nome da configuracao"),
    value: str = typer.Argument(..., help="Novo valor"),
) -> None:
    """Atualiza uma configuracao especifica."""
    display.show_banner()
    settings = storage.load_settings()

    if key not in settings:
        display.show_error(f"Chave '{key}' nao encontrada. Use 'tattoobot config show' para ver as chaves disponiveis.")
        raise typer.Exit(1)

    current = settings[key]

    if isinstance(current, list):
        settings[key] = [v.strip() for v in value.split(",")]
    elif isinstance(current, int):
        try:
            settings[key] = int(value)
        except ValueError:
            display.show_error("Valor deve ser um numero inteiro.")
            raise typer.Exit(1)
    elif isinstance(current, float):
        try:
            settings[key] = float(value)
        except ValueError:
            display.show_error("Valor deve ser um numero.")
            raise typer.Exit(1)
    else:
        settings[key] = value

    storage.save_settings(settings)
    display.show_success(f"{key} = {settings[key]}")


@config_app.command("setup")
def config_setup() -> None:
    """Wizard interativo de primeira configuracao."""
    display.show_banner()
    _interactive_setup()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Exibe a versao do TattooBot"
    ),
) -> None:
    """TattooBot Copilot - Seu assistente de crescimento no Instagram."""
    if version:
        display.console.print(f"{APP_NAME} v{VERSION}")
        raise typer.Exit()
    # Se nenhum subcomando foi passado, abre o menu interativo
    if ctx.invoked_subcommand is None:
        storage.ensure_data_dir()
        run_interactive_menu()


if __name__ == "__main__":
    storage.ensure_data_dir()
    app()
