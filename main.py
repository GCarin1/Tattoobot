"""TattooBot Copilot - Entry point CLI com Typer."""

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
        "de forma 100% segura, sem automacao na conta do Instagram."
    ),
    no_args_is_help=True,
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


@app.command()
def engage() -> None:
    """Gera lista diaria de perfis pra engajar com sugestoes de comentarios."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.engagement import run_engagement
    _run_async(run_engagement(settings))


@app.command()
def caption() -> None:
    """Gera legendas otimizadas com SEO, hashtags e CTA."""
    display.show_banner()
    settings = storage.load_settings()
    from modules.caption import run_caption
    _run_async(run_caption(settings))


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

    # Converte tipo baseado no valor atual
    if isinstance(current, list):
        settings[key] = [v.strip() for v in value.split(",")]
    elif isinstance(current, int):
        try:
            settings[key] = int(value)
        except ValueError:
            display.show_error(f"Valor deve ser um numero inteiro.")
            raise typer.Exit(1)
    elif isinstance(current, float):
        try:
            settings[key] = float(value)
        except ValueError:
            display.show_error(f"Valor deve ser um numero.")
            raise typer.Exit(1)
    else:
        settings[key] = value

    storage.save_settings(settings)
    display.show_success(f"{key} = {settings[key]}")


@config_app.command("setup")
def config_setup() -> None:
    """Wizard interativo de primeira configuracao."""
    display.show_banner()
    display.show_panel(
        "Setup Inicial",
        "Vamos configurar seu TattooBot Copilot!",
        style="magenta",
    )

    settings = storage.load_settings()

    settings["artist_name"] = display.ask_input(
        "Seu nome/apelido artistico",
        default=settings.get("artist_name", ""),
    )
    settings["artist_city"] = display.ask_input(
        "Sua cidade",
        default=settings.get("artist_city", ""),
    )
    settings["tattoo_style"] = display.ask_input(
        "Seu estilo principal (ex: blackwork, dotwork, realismo)",
        default=settings.get("tattoo_style", "blackwork"),
    )

    hashtags_str = display.ask_input(
        "Hashtags do seu nicho (separadas por virgula)",
        default=",".join(settings.get("hashtags", [])),
    )
    settings["hashtags"] = [h.strip() for h in hashtags_str.split(",") if h.strip()]

    profiles_str = display.ask_input(
        "Perfis por dia para engajamento",
        default=str(settings.get("profiles_per_day", 10)),
    )
    try:
        settings["profiles_per_day"] = int(profiles_str)
    except ValueError:
        settings["profiles_per_day"] = 10

    settings["ollama_model"] = display.ask_input(
        "Modelo do Ollama (ex: llama3, mistral, gemma)",
        default=settings.get("ollama_model", "llama3"),
    )

    storage.save_settings(settings)

    display.console.print()
    display.show_success("Configuracao salva com sucesso!")
    display.show_tip("Use 'tattoobot engage' para comecar a gerar sugestoes de engajamento.")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Exibe a versao do TattooBot"
    ),
) -> None:
    """TattooBot Copilot - Seu assistente de crescimento no Instagram."""
    if version:
        display.console.print(f"{APP_NAME} v{VERSION}")
        raise typer.Exit()


if __name__ == "__main__":
    # Garante que os diretorios existem
    storage.ensure_data_dir()
    app()
