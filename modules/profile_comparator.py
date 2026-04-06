"""Comparador de perfis - Analisa seu perfil vs concorrente."""

import asyncio
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from modules import ollama_client, scraper
from modules.competitor_spy import _collect_web_info
from utils import storage, display


def _build_comparison_prompt(
    my_username: str,
    my_profile: scraper.ScrapedProfile,
    my_extra_info: list[str],
    rival_username: str,
    rival_profile: scraper.ScrapedProfile,
    rival_extra_info: list[str],
) -> str:
    """Monta prompt para comparacao entre dois perfis."""

    def _format_profile(
        username: str,
        profile: scraper.ScrapedProfile,
        extra_info: list[str],
    ) -> str:
        parts = []
        if profile.bio:
            parts.append(f"Bio: {profile.bio[:300]}")
        if profile.followers:
            parts.append(f"Seguidores: {profile.followers:,}")
        if profile.post_count:
            parts.append(f"Total de posts: {profile.post_count}")

        captions = [
            p.alt_text or p.caption
            for p in profile.posts[:5]
            if p.alt_text or p.caption
        ]
        if captions:
            captions_text = "\n".join(f"  - {c[:150]}" for c in captions)
            parts.append(f"Legendas recentes:\n{captions_text}")

        if extra_info:
            extra_text = "\n".join(f"  - {e[:200]}" for e in extra_info)
            parts.append(f"Informacoes extras da web:\n{extra_text}")

        return "\n".join(parts) if parts else "Dados limitados disponiveis"

    my_block = _format_profile(my_username, my_profile, my_extra_info)
    rival_block = _format_profile(rival_username, rival_profile, rival_extra_info)

    return (
        f"Voce e um consultor de marketing digital para Instagram, especializado em tatuadores.\n\n"
        f"Compare os dois perfis abaixo e faca uma analise completa e pratica.\n\n"
        f"=== MEU PERFIL: @{my_username} ===\n{my_block}\n\n"
        f"=== PERFIL RIVAL: @{rival_username} ===\n{rival_block}\n\n"
        f"Faca a analise seguindo EXATAMENTE esta estrutura:\n\n"
        f"1. COMPARATIVO GERAL (2-3 frases)\n"
        f"   Compare os dois perfis de forma resumida.\n\n"
        f"2. O QUE O RIVAL FAZ MELHOR (liste cada ponto)\n"
        f"   Identifique aspectos em que @{rival_username} se destaca em relacao a @{my_username}.\n"
        f"   Pode ser: bio mais otimizada, mais posts, melhor frequencia, hashtags, engajamento, "
        f"posicionamento de nicho, variedade de conteudo, etc.\n\n"
        f"3. O QUE EU FACO MELHOR (liste cada ponto)\n"
        f"   Identifique aspectos em que @{my_username} se destaca.\n\n"
        f"4. PLANO DE ACAO PARA SUPERAR O RIVAL\n"
        f"   Para CADA ponto em que o rival e melhor, de uma acao concreta e especifica:\n"
        f"   - O que fazer\n"
        f"   - Como fazer\n"
        f"   - Resultado esperado\n\n"
        f"5. RESUMO FINAL (1-2 frases)\n"
        f"   Prioridade numero 1 para @{my_username} melhorar imediatamente.\n\n"
        f"Responda em portugues brasileiro, de forma direta e pratica. "
        f"Use os dados disponiveis para dar o melhor conselho possivel. "
        f"NAO diga que nao pode analisar."
    )


async def _collect_profile_data(
    username: str,
    delay: float,
) -> tuple[scraper.ScrapedProfile, list[str]]:
    """Coleta dados de um perfil (scraping + info web)."""
    profile = await scraper.scrape_profile_page(username, delay)

    extra_info: list[str] = []
    async with httpx.AsyncClient(timeout=15) as client:
        extra_info = await _collect_web_info(client, username, delay)

    return profile, extra_info


async def run_profile_comparison(settings: dict) -> None:
    """Executa comparacao entre meu perfil e um rival."""
    scraper.reset_request_count()
    delay = settings.get("scraping_delay_seconds", 3)
    ollama_url = settings.get("ollama_url", "http://localhost:11434")
    ollama_model = settings.get("ollama_model", "llama3")

    display.console.print()
    display.show_panel(
        "Comparador de Perfis",
        "Compare seu perfil com um concorrente e descubra como superá-lo!",
        style="yellow",
    )
    display.console.print()

    # Pede os usernames
    my_username = display.ask_input(
        "Seu username do Instagram (com ou sem @)",
        default=settings.get("instagram_username", ""),
    )
    if not my_username:
        display.show_error("Username obrigatorio.")
        return
    my_username = my_username.lstrip("@").strip()

    rival_username = display.ask_input("Username do rival/concorrente (com ou sem @)")
    if not rival_username:
        display.show_error("Username do rival obrigatorio.")
        return
    rival_username = rival_username.lstrip("@").strip()

    if my_username.lower() == rival_username.lower():
        display.show_error("Os perfis devem ser diferentes!")
        return

    # Coleta dados dos dois perfis em paralelo
    display.console.print()
    with display.get_spinner() as progress:
        progress.add_task(
            f"Coletando dados de @{my_username} e @{rival_username}...",
            total=None,
        )
        my_profile, my_extra = await _collect_profile_data(my_username, delay)
        rival_profile, rival_extra = await _collect_profile_data(rival_username, delay)

    # Exibe resumo dos dados coletados
    display.console.print()

    def _format_stats(username: str, profile: scraper.ScrapedProfile, extra: list[str]) -> str:
        lines = []
        if profile.bio:
            lines.append(f"Bio: {profile.bio[:150]}")
        if profile.followers:
            lines.append(f"Seguidores: {profile.followers:,}")
        if profile.post_count:
            lines.append(f"Posts: {profile.post_count}")
        if extra:
            lines.append(f"Infos web: {len(extra)} encontradas")
        if not lines:
            lines.append("Dados limitados (perfil pode ser privado)")
        return "\n".join(lines)

    my_stats = _format_stats(my_username, my_profile, my_extra)
    rival_stats = _format_stats(rival_username, rival_profile, rival_extra)

    display.console.print(display.Panel(
        f"[bold cyan]@{my_username}[/bold cyan]\n{my_stats}\n\n"
        f"[bold red]@{rival_username}[/bold red]\n{rival_stats}",
        title="[bold]Dados Coletados[/bold]",
        border_style="yellow",
        padding=(1, 2),
    ))

    # Gera analise comparativa via Ollama
    display.console.print()
    prompt = _build_comparison_prompt(
        my_username, my_profile, my_extra,
        rival_username, rival_profile, rival_extra,
    )

    analysis = await ollama_client.generate(prompt, ollama_url, ollama_model)

    if not analysis:
        display.show_error("Analise IA indisponivel. Verifique se o Ollama esta rodando.")
        return

    # Exibe resultado
    display.console.print()
    display.console.print(display.Panel(
        f"[bold]@{my_username}  vs  @{rival_username}[/bold]\n\n{analysis}",
        title="[bold yellow]Analise Comparativa[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))

    display.show_tip(
        "Foque em uma melhoria de cada vez. "
        "Consistencia e mais importante que mudar tudo de uma vez!"
    )
