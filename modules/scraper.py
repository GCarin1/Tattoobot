"""Coleta de dados publicos do Instagram via scraping e busca web."""

import asyncio
import random
import re
import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus, unquote

import httpx
from bs4 import BeautifulSoup

from config import USER_AGENTS, MAX_REQUESTS_PER_SESSION
from utils.display import show_warning, show_info, get_spinner, console


@dataclass
class ScrapedPost:
    """Dados de um post coletado."""
    shortcode: str = ""
    link: str = ""
    caption: str = ""
    alt_text: str = ""
    username: str = ""
    likes: int = 0
    comments: int = 0


@dataclass
class ScrapedProfile:
    """Dados de um perfil coletado."""
    username: str = ""
    profile_link: str = ""
    posts: list[ScrapedPost] = field(default_factory=list)
    bio: str = ""
    followers: int = 0
    post_count: int = 0


_request_count: int = 0


def _get_headers() -> dict[str, str]:
    """Retorna headers com User-Agent aleatorio."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }


async def _safe_request(
    client: httpx.AsyncClient,
    url: str,
    delay: float = 2.0,
) -> httpx.Response | None:
    """Faz requisicao HTTP com controle de rate limiting."""
    global _request_count
    if _request_count >= MAX_REQUESTS_PER_SESSION:
        show_warning(f"Limite de {MAX_REQUESTS_PER_SESSION} requisicoes por sessao atingido.")
        return None

    # Delay aleatorio entre requisicoes
    jitter = random.uniform(0.5, 1.5)
    await asyncio.sleep(delay * jitter)

    try:
        _request_count += 1
        response = await client.get(url, headers=_get_headers(), follow_redirects=True)
        return response
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        return None


async def scrape_hashtag_page(
    hashtag: str,
    delay: float = 3.0,
) -> list[ScrapedPost]:
    """Tenta coletar posts de uma hashtag do Instagram.

    Tenta scraping direto primeiro, depois fallback via multiplas engines de busca.
    """
    posts: list[ScrapedPost] = []

    async with httpx.AsyncClient(timeout=15) as client:
        # Tentativa 1: Scraping direto do Instagram
        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        response = await _safe_request(client, url, delay)

        if response and response.status_code == 200:
            posts = _parse_hashtag_page(response.text, hashtag)

        # Tentativa 2: Busca via Bing
        if not posts:
            posts = await _search_bing(client, hashtag, delay)

        # Tentativa 3: Busca via DuckDuckGo
        if not posts:
            posts = await _search_duckduckgo(client, hashtag, delay)

        # Tentativa 4: Busca via Google (lite)
        if not posts:
            posts = await _search_google(client, hashtag, delay)

        # Tentativa 5: Gerar perfis a partir de hashtags conhecidas do nicho
        if not posts:
            show_info(f"Buscas web falharam para #{hashtag}. Usando base de perfis do nicho...")
            posts = _generate_niche_suggestions(hashtag)

    return posts


def _parse_hashtag_page(html: str, hashtag: str) -> list[ScrapedPost]:
    """Faz parsing do HTML da pagina de hashtag."""
    posts: list[ScrapedPost] = []
    soup = BeautifulSoup(html, "html.parser")

    # Busca links de posts
    for link_tag in soup.find_all("a", href=True):
        href = link_tag.get("href", "")
        if "/p/" in href:
            shortcode = href.split("/p/")[1].strip("/")
            post = ScrapedPost(
                shortcode=shortcode,
                link=f"https://www.instagram.com/p/{shortcode}/",
            )
            img = link_tag.find("img")
            if img:
                post.alt_text = img.get("alt", "")
                alt = post.alt_text
                if " by " in alt:
                    post.username = alt.split(" by ")[-1].split(" ")[0].strip("@")
                elif " de " in alt:
                    post.username = alt.split(" de ")[-1].split(" ")[0].strip("@")
            posts.append(post)

    # Busca dados em meta tags
    for meta in soup.find_all("meta", attrs={"property": "og:description"}):
        content = meta.get("content", "")
        if content:
            for post in posts:
                if not post.caption:
                    post.caption = content[:200]
                    break

    # Tenta extrair dados de JSON embutido (shared_data)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                name = data.get("author", {}).get("alternateName", "")
                if name:
                    for post in posts:
                        if not post.username:
                            post.username = name.lstrip("@")
        except (json.JSONDecodeError, AttributeError):
            pass

    return posts


def _extract_instagram_data(href: str, title: str) -> ScrapedPost | None:
    """Extrai dados de um resultado de busca que aponta para o Instagram."""
    # Decodifica URL se necessario
    href = unquote(href)

    # Captura link de post
    ig_match = re.search(r"instagram\.com/p/([A-Za-z0-9_-]+)", href)
    if ig_match:
        shortcode = ig_match.group(1)
        username = ""
        # Tenta extrair username do titulo
        username_match = re.search(r"@([A-Za-z0-9_.]+)", title)
        if username_match:
            username = username_match.group(1)
        else:
            # Formato comum: "Foto de Username no Instagram"
            for pattern in [
                r"(?:Foto|Photo|Post|Publicacao)\s+(?:de|by|from)\s+([A-Za-z0-9_.]+)",
                r"([A-Za-z0-9_.]+)\s+(?:on|no|en)\s+Instagram",
                r"([A-Za-z0-9_.]+)\s*[\(\|•:]\s*Instagram",
            ]:
                m = re.search(pattern, title, re.IGNORECASE)
                if m:
                    username = m.group(1).strip()
                    break

        return ScrapedPost(
            shortcode=shortcode,
            link=f"https://www.instagram.com/p/{shortcode}/",
            caption=title[:200] if title else "",
            username=username,
        )

    # Captura link de perfil
    ig_profile = re.search(r"instagram\.com/([A-Za-z0-9_.]+)/?(?:\?|$)", href)
    if ig_profile:
        username = ig_profile.group(1)
        excluded = {"explore", "p", "reel", "reels", "stories", "accounts", "tags", "about", "legal", "developer"}
        if username.lower() not in excluded and len(username) >= 3:
            return ScrapedPost(
                shortcode="",
                link=f"https://www.instagram.com/{username}/",
                username=username,
                caption=title[:200] if title else "",
            )

    return None


async def _search_bing(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca posts via Bing."""
    posts: list[ScrapedPost] = []
    query = quote_plus(f"site:instagram.com #{hashtag} tattoo")
    search_url = f"https://www.bing.com/search?q={query}&count=20"

    response = await _safe_request(client, search_url, delay)
    if not response or response.status_code != 200:
        return posts

    soup = BeautifulSoup(response.text, "html.parser")

    # Bing usa <li class="b_algo"> para resultados
    for result in soup.find_all("li", class_="b_algo"):
        link_tag = result.find("a")
        if not link_tag:
            continue
        href = link_tag.get("href", "")
        title = link_tag.get_text(strip=True)

        post = _extract_instagram_data(href, title)
        if post:
            posts.append(post)

    # Fallback: busca em todos os links da pagina
    if not posts:
        for link_tag in soup.find_all("a", href=True):
            href = link_tag.get("href", "")
            if "instagram.com" in href:
                title = link_tag.get_text(strip=True)
                post = _extract_instagram_data(href, title)
                if post and post not in posts:
                    posts.append(post)

    return posts


async def _search_duckduckgo(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca posts via DuckDuckGo HTML."""
    posts: list[ScrapedPost] = []
    query = quote_plus(f"site:instagram.com #{hashtag} tattoo")
    search_url = f"https://html.duckduckgo.com/html/?q={query}"

    response = await _safe_request(client, search_url, delay)
    if not response or response.status_code != 200:
        return posts

    soup = BeautifulSoup(response.text, "html.parser")

    for result in soup.find_all("a", class_="result__a"):
        href = result.get("href", "")
        title = result.get_text(strip=True)

        post = _extract_instagram_data(href, title)
        if post:
            posts.append(post)

    return posts


async def _search_google(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca posts via Google (versao lite/html)."""
    posts: list[ScrapedPost] = []
    query = quote_plus(f"site:instagram.com #{hashtag} tattoo")
    search_url = f"https://www.google.com/search?q={query}&num=20&hl=pt-BR"

    response = await _safe_request(client, search_url, delay)
    if not response or response.status_code != 200:
        return posts

    soup = BeautifulSoup(response.text, "html.parser")

    for link_tag in soup.find_all("a", href=True):
        href = link_tag.get("href", "")
        title = link_tag.get_text(strip=True)

        # Google wraps URLs in /url?q=...
        url_match = re.search(r"/url\?q=(https?://[^&]+)", href)
        if url_match:
            href = unquote(url_match.group(1))

        if "instagram.com" in href:
            post = _extract_instagram_data(href, title)
            if post:
                posts.append(post)

    return posts


def _generate_niche_suggestions(hashtag: str) -> list[ScrapedPost]:
    """Gera sugestoes baseadas em hashtags conhecidas quando tudo falha.

    Cria perfis 'placeholder' para que o usuario possa buscar manualmente
    usando as hashtags sugeridas no Instagram.
    """
    # Base de hashtags relacionadas por nicho
    niche_hashtags: dict[str, list[str]] = {
        "blackwork": ["blackworktattoo", "blackworkers", "btattooing", "darkartists", "blackworkerssubmission"],
        "dotwork": ["dotworktattoo", "dotwork", "pontilhismo", "dotworkart"],
        "tattoo": ["tattooartist", "tattooed", "tattooart", "tattoodesign", "tattooideas"],
        "tatuagem": ["tatuagembrasil", "tatuagemfeminina", "tatuagemmasculina", "tatuagemdelicada"],
    }

    related = []
    for key, tags in niche_hashtags.items():
        if key in hashtag.lower():
            related = tags
            break

    if not related:
        related = ["tattooartist", "tattooart", "inked", "tattooideas", "tattoodesign"]

    posts = []
    for tag in related[:5]:
        posts.append(ScrapedPost(
            shortcode="",
            link=f"https://www.instagram.com/explore/tags/{tag}/",
            caption=f"Explore a hashtag #{tag} no Instagram para encontrar perfis do nicho",
            alt_text=f"Hashtag #{tag}",
            username=f"_explore_{tag}",
        ))

    return posts


async def scrape_profile_page(
    username: str,
    delay: float = 3.0,
) -> ScrapedProfile:
    """Coleta dados publicos de um perfil do Instagram."""
    profile = ScrapedProfile(
        username=username,
        profile_link=f"https://www.instagram.com/{username}/",
    )

    async with httpx.AsyncClient(timeout=15) as client:
        response = await _safe_request(
            client,
            f"https://www.instagram.com/{username}/",
            delay,
        )

        if not response or response.status_code != 200:
            # Fallback: tenta buscar info via busca web
            profile = await _profile_fallback_search(client, username, delay, profile)
            return profile

        soup = BeautifulSoup(response.text, "html.parser")

        # Tenta extrair meta description (bio e stats)
        meta_desc = soup.find("meta", attrs={"property": "og:description"})
        if meta_desc:
            content = meta_desc.get("content", "")
            profile.bio = content

            numbers = re.findall(r"([\d,.]+[KkMm]?)\s+(Followers|Seguidores)", content)
            if numbers:
                profile.followers = _parse_number(numbers[0][0])

            posts_match = re.findall(r"([\d,.]+[KkMm]?)\s+(Posts|Publicacoes)", content)
            if posts_match:
                profile.post_count = _parse_number(posts_match[0][0])

        # Coleta links de posts recentes
        for link_tag in soup.find_all("a", href=True):
            href = link_tag.get("href", "")
            if "/p/" in href and len(profile.posts) < 10:
                shortcode = href.split("/p/")[1].strip("/")
                post = ScrapedPost(
                    shortcode=shortcode,
                    link=f"https://www.instagram.com/p/{shortcode}/",
                    username=username,
                )
                img = link_tag.find("img")
                if img:
                    post.alt_text = img.get("alt", "")
                profile.posts.append(post)

    return profile


async def _profile_fallback_search(
    client: httpx.AsyncClient,
    username: str,
    delay: float,
    profile: ScrapedProfile,
) -> ScrapedProfile:
    """Tenta coletar info de perfil via busca web."""
    query = quote_plus(f"instagram.com/{username} tattoo artist")
    search_url = f"https://www.bing.com/search?q={query}"

    response = await _safe_request(client, search_url, delay)
    if response and response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # Tenta extrair snippet com informacoes
        for snippet in soup.find_all("p"):
            text = snippet.get_text(strip=True)
            if "followers" in text.lower() or "seguidores" in text.lower():
                profile.bio = text[:300]
                numbers = re.findall(r"([\d,.]+[KkMm]?)\s+(?:followers|seguidores)", text, re.IGNORECASE)
                if numbers:
                    profile.followers = _parse_number(numbers[0])
                break

    return profile


def _parse_number(text: str) -> int:
    """Converte string de numero (1.2K, 3.5M) para inteiro."""
    text = text.strip().replace(",", "").replace(".", "")
    multiplier = 1
    if text.upper().endswith("K"):
        multiplier = 1000
        text = text[:-1]
    elif text.upper().endswith("M"):
        multiplier = 1000000
        text = text[:-1]
    try:
        return int(float(text) * multiplier)
    except (ValueError, TypeError):
        return 0


def is_likely_bot(username: str) -> bool:
    """Verifica se um username parece ser bot."""
    bot_patterns = [
        r"^\d{5,}$",
        r"^follow",
        r"^get_?followers",
        r"^free_?likes",
        r"^promo_",
        r"shop\d{3,}$",
        r"^bot_",
        r"marketing\d{3,}$",
        r"^_explore_",  # Nossos placeholders internos
    ]
    username_lower = username.lower()
    for pattern in bot_patterns:
        if re.search(pattern, username_lower):
            return True
    if len(username) < 3 or username.isdigit():
        return True
    return False


def reset_request_count() -> None:
    """Reseta contador de requisicoes (chamar no inicio de cada sessao)."""
    global _request_count
    _request_count = 0
