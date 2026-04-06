"""Monitoramento de perfis de concorrentes."""

import asyncio
import re
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from modules import ollama_client, scraper
from utils import storage, display


def _build_spy_prompt(
    username: str,
    bio: str,
    post_count: int,
    followers: int,
    recent_captions: list[str],
    extra_info: list[str],
) -> str:
    """Monta prompt para analise de concorrente."""
    captions_text = "\n".join(f"- {c[:150]}" for c in recent_captions) if recent_captions else "Nao coletadas diretamente"
    extra_text = "\n".join(f"- {e}" for e in extra_info) if extra_info else ""

    info_parts = []
    if bio:
        info_parts.append(f"Bio/Descricao: {bio}")
    if post_count:
        info_parts.append(f"Total de posts: {post_count}")
    if followers:
        info_parts.append(f"Seguidores: {followers}")
    if recent_captions:
        info_parts.append(f"Legendas/descricoes recentes:\n{captions_text}")
    if extra_text:
        info_parts.append(f"Informacoes adicionais encontradas na web:\n{extra_text}")

    info_block = "\n".join(info_parts) if info_parts else "Dados limitados disponiveis"

    return (
        f"Voce e um analista de marketing digital para Instagram especializado em tatuadores.\n"
        f"Analise o perfil do tatuador @{username} com base nos dados coletados abaixo.\n\n"
        f"{info_block}\n\n"
        f"Com base nas informacoes disponiveis, forneca uma analise pratica e util (4-6 frases):\n"
        f"- O que se pode inferir sobre a estrategia deste perfil\n"
        f"- Frequencia de postagem estimada (se houver dados)\n"
        f"- Pontos fortes visiveis\n"
        f"- Uma sugestao concreta do que o artista pode aprender com esse perfil\n"
        f"- Se os dados sao limitados, foque no que a bio e o nicho revelam sobre posicionamento\n\n"
        f"Responda em portugues brasileiro, de forma direta e pratica. "
        f"NAO diga que nao pode analisar. Use os dados disponiveis para dar o melhor conselho possivel."
    )


async def _collect_web_info(
    client: httpx.AsyncClient,
    username: str,
    delay: float,
) -> list[str]:
    """Coleta informacoes adicionais sobre o perfil via busca web."""
    info: list[str] = []

    # Busca no DuckDuckGo por conteudo recente
    queries = [
        f"instagram.com/{username}",
        f"@{username} tattoo instagram",
    ]

    for query_text in queries:
        query = quote_plus(query_text)
        search_url = f"https://html.duckduckgo.com/html/?q={query}"

        response = await scraper._safe_request(client, search_url, delay)
        if not response or response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Coleta snippets relevantes ao perfil buscado
        username_lower = username.lower().replace(".", "")
        for snippet in soup.find_all(class_="result__snippet"):
            text = snippet.get_text(strip=True)
            if not text or len(text) < 20:
                continue
            text_lower = text.lower()
            # Filtra: deve conter o username ou ser claramente sobre o perfil
            is_relevant = (
                username_lower in text_lower.replace(".", "")
                or f"@{username}" in text
            )
            if is_relevant:
                clean_text = text[:250]
                if clean_text not in info:
                    info.append(clean_text)

        if len(info) >= 6:
            break

    return info[:8]


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
        f"Analisando {len(competitors)} concorrente(s)...",
        style="red",
    )

    for username in competitors:
        display.console.print()

        # Fase 1: Coletar dados do perfil
        with display.get_spinner() as progress:
            progress.add_task(f"Coletando dados de @{username}...", total=None)
            profile = await scraper.scrape_profile_page(username, delay)

        # Fase 2: Buscar informacoes extras na web
        extra_info: list[str] = []
        async with httpx.AsyncClient(timeout=15) as client:
            with display.get_spinner() as progress:
                progress.add_task(f"Buscando informacoes na web sobre @{username}...", total=None)
                extra_info = await _collect_web_info(client, username, delay)

        # Monta stats para exibicao
        stats_lines = []
        if profile.followers:
            stats_lines.append(f"Seguidores: {profile.followers:,}")
        if profile.post_count:
            stats_lines.append(f"Total de posts: {profile.post_count}")
        if profile.posts:
            stats_lines.append(f"Posts coletados: {len(profile.posts)}")
        if profile.bio:
            # Limpa bio para exibicao
            bio_clean = profile.bio[:200]
            stats_lines.append(f"Bio: {bio_clean}")
        if extra_info:
            stats_lines.append(f"Infos web encontradas: {len(extra_info)}")

        stats = "\n".join(stats_lines) if stats_lines else "Perfil: instagram.com/" + username

        # Coleta captions dos posts (se houver)
        recent_captions = [
            p.alt_text or p.caption
            for p in profile.posts[:5]
            if p.alt_text or p.caption
        ]

        # Fase 3: Analise via Ollama
        prompt = _build_spy_prompt(
            username, profile.bio, profile.post_count,
            profile.followers, recent_captions, extra_info,
        )
        analysis = await ollama_client.generate(prompt, ollama_url, ollama_model)

        if not analysis:
            analysis = "Analise IA indisponivel. Verifique se o Ollama esta rodando."

        display.show_spy_card(username, stats, analysis)

    display.show_tip(
        "Compare a estrategia dos concorrentes com a sua. "
        "Adapte o que funciona, mas mantenha sua identidade!"
    )
