"""Modulo principal: selecao de perfis e sugestoes de engajamento."""

import asyncio
from datetime import datetime

from modules import ollama_client, scraper
from utils import storage, display


def _build_comment_prompt(
    tattoo_style: str,
    post_context: str,
) -> str:
    """Monta prompt para geracao de comentarios."""
    return (
        f"Voce e um tatuador brasileiro especializado em {tattoo_style}.\n"
        f"Voce esta vendo o post de um potencial cliente no Instagram.\n\n"
        f"Contexto do post: {post_context}\n\n"
        f"Gere 3 comentarios curtos (5-20 palavras cada) em portugues brasileiro que:\n"
        f"- Sejam genuinos e naturais (nao parecam bot)\n"
        f"- Sejam relevantes ao conteudo do post\n"
        f"- Mostrem interesse real ou elogiem algo especifico\n"
        f"- Nao sejam genericos como 'que legal!' ou 'show!'\n"
        f"- Nao mencionem diretamente que voce e tatuador (sutileza)\n"
        f"- Nao usem emojis em excesso (maximo 1 por comentario)\n\n"
        f"Responda APENAS com os 3 comentarios, um por linha, numerados."
    )


def _parse_comments(response: str) -> list[str]:
    """Extrai comentarios da resposta do Ollama."""
    comments = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove numeracao
        for prefix in ["1.", "2.", "3.", "1)", "2)", "3)", "- "]:
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        # Remove aspas
        line = line.strip('"').strip("'").strip()
        if line and len(line) > 3:
            comments.append(line)
    return comments[:3]


async def run_engagement(settings: dict) -> None:
    """Executa o fluxo completo de engajamento."""
    scraper.reset_request_count()
    hashtags = settings.get("hashtags", [])
    profiles_per_day = settings.get("profiles_per_day", 10)
    delay = settings.get("scraping_delay_seconds", 3)
    tattoo_style = settings.get("tattoo_style", "blackwork")
    ollama_url = settings.get("ollama_url", "http://localhost:11434")
    ollama_model = settings.get("ollama_model", "llama3")

    if not hashtags:
        display.show_error("Nenhuma hashtag configurada. Use 'tattoobot config set hashtags' para configurar.")
        return

    today = datetime.now().strftime("%d/%m/%Y")
    already_suggested = storage.get_history_usernames()

    # Fase 1: Coletar posts de todas as hashtags
    all_posts: list[scraper.ScrapedPost] = []

    with display.get_spinner() as progress:
        task = progress.add_task("Coletando dados de hashtags...", total=len(hashtags))
        for hashtag in hashtags:
            progress.update(task, description=f"Buscando #{hashtag}...")
            posts = await scraper.scrape_hashtag_page(hashtag, delay)
            all_posts.extend(posts)
            progress.advance(task)

    if not all_posts:
        display.show_warning(
            "Nao foi possivel coletar posts. O Instagram pode estar bloqueando.\n"
            "Tente novamente mais tarde ou verifique sua conexao."
        )
        return

    display.show_info(f"{len(all_posts)} posts coletados de {len(hashtags)} hashtags.")

    # Fase 2: Filtrar perfis
    seen_usernames: set[str] = set()
    selected_posts: list[scraper.ScrapedPost] = []

    for post in all_posts:
        username = post.username
        if not username:
            continue
        if username in already_suggested:
            continue
        if username in seen_usernames:
            continue
        if scraper.is_likely_bot(username):
            continue
        seen_usernames.add(username)
        selected_posts.append(post)
        if len(selected_posts) >= profiles_per_day:
            break

    if not selected_posts:
        display.show_warning(
            "Nenhum perfil novo encontrado. Todos ja foram sugeridos anteriormente.\n"
            "Tente adicionar novas hashtags ou aguarde novos posts."
        )
        return

    # Exibir cabecalho
    display.show_engagement_header(today, len(selected_posts))

    # Fase 3: Gerar comentarios para cada perfil
    profiles_to_save: list[dict] = []

    for post in selected_posts:
        context = post.caption or post.alt_text or f"Post sobre tattoo/arte em #{hashtags[0]}"

        # Gerar comentarios via Ollama
        prompt = _build_comment_prompt(tattoo_style, context)
        response = await ollama_client.generate(prompt, ollama_url, ollama_model)

        if response:
            comments = _parse_comments(response)
        else:
            comments = [
                "Ficou incrivel esse trabalho!",
                "Que nivel de detalhe, parabens",
                "Resultado muito limpo",
            ]

        display.show_profile_card(
            username=post.username,
            post_link=post.link or f"https://www.instagram.com/{post.username}/",
            post_caption=context,
            comments=comments,
        )

        profiles_to_save.append({
            "username": post.username,
            "link": post.link,
            "context": context[:100],
        })

    # Fase 4: Salvar no historico
    storage.add_to_history(profiles_to_save)

    # Rodape
    display.show_engagement_footer()
    display.show_success(f"{len(profiles_to_save)} perfis salvos no historico.")
