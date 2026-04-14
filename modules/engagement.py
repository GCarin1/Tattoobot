"""Modulo principal: selecao de perfis e sugestoes de engajamento."""

from datetime import datetime

from modules import ollama_client, scraper
from utils import storage, display


# Palavras/expressoes batidas que devem ser evitadas nos comentarios.
# A IA tende a cair sempre nelas quando o contexto e generico.
BANNED_PHRASES: list[str] = [
    "contraste",
    "saturação",
    "saturacao",
    "absurdo",
    "absurda",
    "impecável",
    "impecavel",
    "anatomia",
    "composição",
    "composicao",
    "precisão",
    "precisao",
    "surreal",
    "nível altíssimo",
    "nivel altissimo",
    "nível de detalhe",
    "nivel de detalhe",
    "parabéns pelo trabalho",
    "parabens pelo trabalho",
    "valorizou demais",
    "ficou animal",
    "referência pesada",
    "referencia pesada",
]


def _build_comment_prompt(
    tattoo_style: str,
    post_context: str,
    username: str,
    session_history: list[str],
) -> str:
    """Monta prompt para geracao de comentarios.

    session_history: lista de comentarios ja gerados na sessao atual
        (sera injetada para a IA evitar repetir estrutura/vocabulario).
    """
    banned_str = ", ".join(f'"{w}"' for w in BANNED_PHRASES)

    if session_history:
        # Limita a ultimas 30 para nao estourar contexto
        recent = session_history[-30:]
        prev_block = "\n".join(f"- {c}" for c in recent)
        history_section = (
            "\nComentarios JA gerados nesta sessao "
            "(NAO repita vocabulario, estrutura ou ideia parecida):\n"
            f"{prev_block}\n"
        )
    else:
        history_section = ""

    return (
        f"Voce e um tatuador brasileiro especializado em {tattoo_style}.\n"
        f"Esta vendo um post do perfil @{username} no Instagram.\n\n"
        f"Contexto real observado no post: {post_context}\n"
        f"{history_section}\n"
        f"Gere 3 comentarios curtos (5-20 palavras cada) em portugues brasileiro que:\n"
        f"- Sejam ESPECIFICOS a este post (cite algo concreto do contexto acima)\n"
        f"- Sejam genuinos e naturais, como uma pessoa real comentaria\n"
        f"- Variem entre si em ESTRUTURA: por exemplo, 1 elogio tecnico a um detalhe, "
        f"1 pergunta curta ao artista, 1 observacao pessoal/emocional\n"
        f"- NAO usem estas palavras/expressoes batidas: {banned_str}\n"
        f"- Nao sejam genericos como 'que legal!', 'show!', 'ficou top!'\n"
        f"- Nao mencionem diretamente que voce e tatuador (sutileza)\n"
        f"- Usem no maximo 1 emoji por comentario (pode ser zero)\n"
        f"- Nao se repitam entre si, e nao imitem os comentarios anteriores da sessao\n\n"
        f"Responda APENAS com os 3 comentarios, um por linha, numerados 1., 2., 3."
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


def _is_generic_context(context: str, username: str) -> bool:
    """Detecta se o contexto coletado e apenas titulo generico da busca."""
    if not context:
        return True
    low = context.lower()
    # Padroes de titulo generico de busca
    generic_markers = [
        "• instagram",
        "- instagram",
        "| instagram",
        "instagram photos and videos",
        "(@",
    ]
    if any(m in low for m in generic_markers):
        return True
    if username.lower() in low and len(context) < 80:
        return True
    return False


async def run_engagement(settings: dict) -> None:
    """Executa o fluxo completo de engajamento.

    O historico de comentarios e mantido APENAS dentro desta sessao:
    a cada execucao comeca vazio para nao limitar a IA entre dias.
    """
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

    # Fase 2: Filtrar perfis priorizando quem tem link de post real
    seen_usernames: set[str] = set()
    posts_with_real_link: list[scraper.ScrapedPost] = []
    posts_profile_only: list[scraper.ScrapedPost] = []

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
        if scraper.has_real_post_link(post):
            posts_with_real_link.append(post)
        else:
            posts_profile_only.append(post)

    # Prioridade: primeiro os que tem link de post real, depois perfis
    selected_posts = (posts_with_real_link + posts_profile_only)[:profiles_per_day]

    if not selected_posts:
        display.show_warning(
            "Nenhum perfil novo encontrado. Todos ja foram sugeridos anteriormente.\n"
            "Tente adicionar novas hashtags ou aguarde novos posts."
        )
        return

    # Exibir cabecalho
    display.show_engagement_header(today, len(selected_posts))

    # Fase 3: Gerar comentarios para cada perfil
    # session_history comeca vazio: nao herda nada de sessoes anteriores
    session_history: list[str] = []
    profiles_to_save: list[dict] = []

    for post in selected_posts:
        # Tenta enriquecer com dados reais do post se o contexto parece generico
        # ou se nao temos link de post
        needs_enrichment = (
            not scraper.has_real_post_link(post)
            or _is_generic_context(post.caption or post.alt_text, post.username)
        )

        if needs_enrichment:
            latest = await scraper.fetch_latest_post_for_profile(post.username, delay)
            if latest:
                # Adota link de post real se encontrado
                if scraper.has_real_post_link(latest):
                    post.shortcode = latest.shortcode
                    post.link = latest.link
                # Contexto real do post (alt_text descreve a imagem)
                if latest.alt_text and not _is_generic_context(latest.alt_text, post.username):
                    post.alt_text = latest.alt_text
                elif latest.caption and not _is_generic_context(latest.caption, post.username):
                    post.caption = latest.caption

        # Monta contexto final, priorizando descricao real da imagem
        context_parts: list[str] = []
        if post.alt_text and not _is_generic_context(post.alt_text, post.username):
            context_parts.append(post.alt_text)
        if post.caption and not _is_generic_context(post.caption, post.username):
            context_parts.append(post.caption)
        if not context_parts:
            # Ultimo recurso: pede comentarios sem contexto real,
            # forcando a IA a ser mais cautelosa/generica
            context = (
                f"Perfil de tatuador. Sem contexto especifico do post disponivel. "
                f"Gere comentarios neutros que funcionariam para um post de tattoo "
                f"em geral (sem citar cores, formas ou detalhes especificos)."
            )
        else:
            context = " | ".join(context_parts)[:500]

        # Gerar comentarios via Ollama com temperatura mais alta
        prompt = _build_comment_prompt(
            tattoo_style=tattoo_style,
            post_context=context,
            username=post.username,
            session_history=session_history,
        )
        response = await ollama_client.generate(
            prompt,
            ollama_url,
            ollama_model,
            temperature=1.0,
            top_p=0.95,
        )

        if response:
            comments = _parse_comments(response)
        else:
            comments = [
                "Ficou incrivel esse trabalho!",
                "Que nivel de detalhe, parabens",
                "Resultado muito limpo",
            ]

        # Adiciona ao historico da sessao para influenciar os proximos prompts
        session_history.extend(comments)

        post_link = post.link or f"https://www.instagram.com/{post.username}/"
        display.show_profile_card(
            username=post.username,
            post_link=post_link,
            post_caption=context,
            comments=comments,
        )

        profiles_to_save.append({
            "username": post.username,
            "link": post_link,
            "context": context[:100],
        })

    # Fase 4: Salvar no historico (apenas perfis, nao comentarios)
    storage.add_to_history(profiles_to_save)

    # Rodape
    display.show_engagement_footer()
    display.show_success(f"{len(profiles_to_save)} perfis salvos no historico.")
