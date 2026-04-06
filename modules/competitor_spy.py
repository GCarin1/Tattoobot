"""Monitoramento de perfis de concorrentes."""

import asyncio

from modules import ollama_client, scraper
from utils import storage, display


def _build_spy_prompt(
    username: str,
    bio: str,
    post_count: int,
    followers: int,
    recent_captions: list[str],
) -> str:
    """Monta prompt para analise de concorrente."""
    captions_text = "\n".join(f"- {c[:100]}" for c in recent_captions) if recent_captions else "Nao disponivel"
    return (
        f"Voce e um analista de marketing digital para Instagram.\n"
        f"Analise o perfil do tatuador @{username} com base nos dados abaixo.\n\n"
        f"Bio: {bio or 'Nao disponivel'}\n"
        f"Posts: {post_count or 'N/A'}\n"
        f"Seguidores: {followers or 'N/A'}\n"
        f"Legendas recentes:\n{captions_text}\n\n"
        f"Analise de forma concisa (3-5 frases):\n"
        f"- Frequencia de postagem estimada\n"
        f"- Tipos de conteudo que parecem funcionar melhor\n"
        f"- Hashtags ou estrategias visiveis\n"
        f"- Uma sugestao do que o artista pode aprender com esse perfil\n\n"
        f"Responda em portugues brasileiro, de forma direta."
    )


async def add_competitor(username: str) -> None:
    """Adiciona perfil a lista de concorrentes."""
    username = username.lstrip("@").strip()
    competitors = storage.load_competitors()
    if username in competitors:
        display.show_warning(f"@{username} ja esta na lista de concorrentes.")
        return
    competitors.append(username)
    storage.save_competitors(competitors)
    display.show_success(f"@{username} adicionado a lista de concorrentes.")


async def remove_competitor(username: str) -> None:
    """Remove perfil da lista de concorrentes."""
    username = username.lstrip("@").strip()
    competitors = storage.load_competitors()
    if username not in competitors:
        display.show_warning(f"@{username} nao esta na lista de concorrentes.")
        return
    competitors.remove(username)
    storage.save_competitors(competitors)
    display.show_success(f"@{username} removido da lista de concorrentes.")


async def list_competitors() -> None:
    """Lista perfis monitorados."""
    competitors = storage.load_competitors()
    if not competitors:
        display.show_info("Nenhum concorrente monitorado.")
        display.show_tip("Use 'tattoobot spy add @username' para adicionar.")
        return

    display.console.print()
    display.show_panel(
        "Concorrentes Monitorados",
        "\n".join(f"  @{c}" for c in competitors),
        style="red",
    )
    display.console.print(f"  Total: {len(competitors)} perfis", style="dim")


async def run_spy_report(settings: dict) -> None:
    """Gera relatorio de atividade dos concorrentes."""
    scraper.reset_request_count()
    competitors = storage.load_competitors()
    delay = settings.get("scraping_delay_seconds", 3)
    ollama_url = settings.get("ollama_url", "http://localhost:11434")
    ollama_model = settings.get("ollama_model", "llama3")

    if not competitors:
        display.show_info("Nenhum concorrente monitorado.")
        display.show_tip("Use 'tattoobot spy add @username' para adicionar concorrentes.")
        return

    display.console.print()
    display.show_panel(
        "TattooBot Copilot - Spy Report",
        f"Analisando {len(competitors)} concorrentes...",
        style="red",
    )

    for username in competitors:
        display.console.print()
        with display.get_spinner() as progress:
            progress.add_task(f"Coletando dados de @{username}...", total=None)
            profile = await scraper.scrape_profile_page(username, delay)

        # Monta stats
        stats_lines = []
        if profile.post_count:
            stats_lines.append(f"Total de posts: {profile.post_count}")
        if profile.followers:
            stats_lines.append(f"Seguidores: {profile.followers:,}")
        stats_lines.append(f"Posts coletados: {len(profile.posts)}")

        if profile.bio:
            bio_preview = profile.bio[:150]
            stats_lines.append(f"Bio: {bio_preview}")

        stats = "\n".join(stats_lines) if stats_lines else "Dados limitados disponiveis"

        # Coleta captions dos posts
        recent_captions = [
            p.alt_text or p.caption
            for p in profile.posts[:5]
            if p.alt_text or p.caption
        ]

        # Analise via Ollama
        prompt = _build_spy_prompt(
            username, profile.bio, profile.post_count,
            profile.followers, recent_captions,
        )
        analysis = await ollama_client.generate(prompt, ollama_url, ollama_model)

        if not analysis:
            analysis = "Analise IA indisponivel. Verifique o Ollama."

        display.show_spy_card(username, stats, analysis)

    display.show_tip(
        "Compare a estrategia dos concorrentes com a sua. "
        "Adapte o que funciona, mas mantenha sua identidade!"
    )
