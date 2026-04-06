"""Coleta de dados publicos do Instagram via scraping."""

import asyncio
import random
import re
from dataclasses import dataclass, field
from typing import Any

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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
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
        show_warning(f"Falha na requisicao para {url}: {e}")
        return None


async def scrape_hashtag_page(
    hashtag: str,
    delay: float = 3.0,
) -> list[ScrapedPost]:
    """Tenta coletar posts de uma hashtag do Instagram.

    Faz scraping da pagina publica de hashtag.
    Se falhar, usa fallback de busca web.
    """
    posts: list[ScrapedPost] = []

    async with httpx.AsyncClient(timeout=15) as client:
        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        response = await _safe_request(client, url, delay)

        if response and response.status_code == 200:
            posts = _parse_hashtag_page(response.text, hashtag)

        if not posts:
            show_info(f"Scraping direto falhou para #{hashtag}. Tentando busca alternativa...")
            posts = await _fallback_web_search(client, hashtag, delay)

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
            # Tenta extrair alt text de imagens
            img = link_tag.find("img")
            if img:
                post.alt_text = img.get("alt", "")
                # Tenta extrair username do alt text
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

    return posts


async def _fallback_web_search(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca posts via busca web como fallback."""
    posts: list[ScrapedPost] = []

    # Tenta DuckDuckGo como alternativa
    search_url = f"https://html.duckduckgo.com/html/?q=site%3Ainstagram.com+%23{hashtag}+tattoo"
    response = await _safe_request(client, search_url, delay)

    if not response or response.status_code != 200:
        return posts

    soup = BeautifulSoup(response.text, "html.parser")

    for result in soup.find_all("a", class_="result__a"):
        href = result.get("href", "")
        title = result.get_text(strip=True)

        # Filtra apenas links de posts do Instagram
        ig_match = re.search(r"instagram\.com/p/([A-Za-z0-9_-]+)", href)
        if ig_match:
            shortcode = ig_match.group(1)
            post = ScrapedPost(
                shortcode=shortcode,
                link=f"https://www.instagram.com/p/{shortcode}/",
                caption=title[:200] if title else "",
            )
            # Tenta extrair username do titulo
            username_match = re.search(r"@(\w+)", title)
            if username_match:
                post.username = username_match.group(1)
            posts.append(post)

        # Tambem captura links de perfil
        ig_profile = re.search(r"instagram\.com/([A-Za-z0-9_.]+)/?$", href)
        if ig_profile and not ig_match:
            username = ig_profile.group(1)
            if username not in ("explore", "p", "reel", "stories", "accounts"):
                post = ScrapedPost(
                    shortcode="",
                    link=f"https://www.instagram.com/{username}/",
                    username=username,
                    caption=title[:200] if title else "",
                )
                posts.append(post)

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
            return profile

        soup = BeautifulSoup(response.text, "html.parser")

        # Tenta extrair meta description (bio e stats)
        meta_desc = soup.find("meta", attrs={"property": "og:description"})
        if meta_desc:
            content = meta_desc.get("content", "")
            profile.bio = content

            # Tenta extrair numeros de seguidores/posts
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
    ]
    username_lower = username.lower()
    for pattern in bot_patterns:
        if re.search(pattern, username_lower):
            return True
    # Nomes muito curtos ou so numeros
    if len(username) < 3 or username.isdigit():
        return True
    return False


def reset_request_count() -> None:
    """Reseta contador de requisicoes (chamar no inicio de cada sessao)."""
    global _request_count
    _request_count = 0
