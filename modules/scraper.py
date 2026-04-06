"""Coleta de dados publicos do Instagram via busca web."""

import asyncio
import random
import re
import json
from dataclasses import dataclass, field
from urllib.parse import quote_plus, unquote, parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from config import USER_AGENTS, MAX_REQUESTS_PER_SESSION
from utils.display import show_warning, show_info, console


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
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
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

    jitter = random.uniform(0.5, 1.5)
    await asyncio.sleep(delay * jitter)

    try:
        _request_count += 1
        response = await client.get(url, headers=_get_headers(), follow_redirects=True)
        return response
    except (httpx.TimeoutException, httpx.ConnectError):
        return None


def _resolve_redirect_url(href: str) -> str:
    """Resolve URLs de redirect de search engines para o URL real.

    DuckDuckGo: //duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.instagram.com%2Fuser%2F
    Google: /url?q=https://www.instagram.com/user/
    Bing: direct URLs
    """
    # DuckDuckGo redirect
    uddg_match = re.search(r"uddg=([^&]+)", href)
    if uddg_match:
        return unquote(uddg_match.group(1))

    # Google redirect
    url_match = re.search(r"/url\?q=(https?://[^&]+)", href)
    if url_match:
        return unquote(url_match.group(1))

    return unquote(href)


def _extract_instagram_data(raw_href: str, title: str) -> ScrapedPost | None:
    """Extrai dados de um resultado de busca que aponta para o Instagram."""
    # Resolve redirects primeiro
    href = _resolve_redirect_url(raw_href)

    # Verifica se e um link do Instagram
    if "instagram.com" not in href:
        return None

    excluded_paths = {
        "explore", "p", "reel", "reels", "stories", "accounts",
        "tags", "about", "legal", "developer", "directory", "popular",
    }

    # Captura link de post
    ig_post = re.search(r"instagram\.com/p/([A-Za-z0-9_-]+)", href)
    if ig_post:
        shortcode = ig_post.group(1)
        username = _extract_username_from_title(title)
        return ScrapedPost(
            shortcode=shortcode,
            link=f"https://www.instagram.com/p/{shortcode}/",
            caption=title[:200] if title else "",
            username=username,
        )

    # Captura link de reel
    ig_reel = re.search(r"instagram\.com/reel/([A-Za-z0-9_-]+)", href)
    if ig_reel:
        shortcode = ig_reel.group(1)
        username = _extract_username_from_title(title)
        return ScrapedPost(
            shortcode=shortcode,
            link=f"https://www.instagram.com/reel/{shortcode}/",
            caption=title[:200] if title else "",
            username=username,
        )

    # Captura link de perfil
    ig_profile = re.search(r"instagram\.com/([A-Za-z0-9_.]+)/?(?:\?|$|#)", href)
    if ig_profile:
        username = ig_profile.group(1)
        if username.lower() not in excluded_paths and len(username) >= 3:
            return ScrapedPost(
                shortcode="",
                link=f"https://www.instagram.com/{username}/",
                username=username,
                caption=title[:200] if title else "",
            )

    return None


def _extract_username_from_title(title: str) -> str:
    """Extrai username de um titulo de resultado de busca."""
    # @username
    m = re.search(r"@([A-Za-z0-9_.]+)", title)
    if m:
        return m.group(1)

    # "Fulano on Instagram" / "Fulano no Instagram"
    for pattern in [
        r"([A-Za-z0-9_.]+)\s+(?:on|no|en|sur)\s+Instagram",
        r"([A-Za-z0-9_.]+)\s*[\(\|•:]\s*Instagram",
        r"(?:Foto|Photo|Post)\s+(?:de|by|from)\s+([A-Za-z0-9_.]+)",
        r"Instagram\s*[-–:]\s*([A-Za-z0-9_.]+)",
    ]:
        m = re.search(pattern, title, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if len(name) >= 3 and name.lower() not in {"instagram", "the", "foto", "photo"}:
                return name

    return ""


async def scrape_hashtag_page(
    hashtag: str,
    delay: float = 3.0,
) -> list[ScrapedPost]:
    """Coleta perfis relacionados a uma hashtag via busca web.

    Ordem de tentativa: DuckDuckGo > Bing > Google > Instagram direto.
    DuckDuckGo e a fonte mais confiavel nos testes.
    """
    posts: list[ScrapedPost] = []

    async with httpx.AsyncClient(timeout=15) as client:
        # Tentativa 1: DuckDuckGo (fonte mais confiavel)
        posts = await _search_duckduckgo(client, hashtag, delay)

        # Tentativa 2: DuckDuckGo com query alternativa
        if not posts:
            posts = await _search_duckduckgo_alt(client, hashtag, delay)

        # Tentativa 3: Bing
        if not posts:
            posts = await _search_bing(client, hashtag, delay)

        # Tentativa 4: Google
        if not posts:
            posts = await _search_google(client, hashtag, delay)

        # Tentativa 5: Scraping direto do Instagram
        if not posts:
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            response = await _safe_request(client, url, delay)
            if response and response.status_code == 200:
                posts = _parse_instagram_html(response.text)

    return posts


async def _search_duckduckgo(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca perfis via DuckDuckGo HTML."""
    posts: list[ScrapedPost] = []
    query = quote_plus(f"site:instagram.com #{hashtag} tattoo")
    search_url = f"https://html.duckduckgo.com/html/?q={query}"

    response = await _safe_request(client, search_url, delay)
    if not response or response.status_code != 200:
        return posts

    soup = BeautifulSoup(response.text, "html.parser")

    # Resultados principais
    for result in soup.find_all("a", class_="result__a"):
        href = result.get("href", "")
        title = result.get_text(strip=True)
        post = _extract_instagram_data(href, title)
        if post:
            posts.append(post)

    # Tenta tambem nos snippets
    if not posts:
        for result in soup.find_all("a", href=True):
            href = result.get("href", "")
            resolved = _resolve_redirect_url(href)
            if "instagram.com" in resolved:
                title = result.get_text(strip=True)
                post = _extract_instagram_data(href, title)
                if post:
                    posts.append(post)

    return posts


async def _search_duckduckgo_alt(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca alternativa no DuckDuckGo com query diferente."""
    posts: list[ScrapedPost] = []
    # Query sem site: para resultados mais amplos
    query = quote_plus(f"instagram {hashtag} tattoo artist profile")
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

    for result in soup.find_all("li", class_="b_algo"):
        link_tag = result.find("a")
        if not link_tag:
            continue
        href = link_tag.get("href", "")
        title = link_tag.get_text(strip=True)
        post = _extract_instagram_data(href, title)
        if post:
            posts.append(post)

    # Fallback generico
    if not posts:
        for link_tag in soup.find_all("a", href=True):
            href = link_tag.get("href", "")
            if "instagram.com" in href:
                title = link_tag.get_text(strip=True)
                post = _extract_instagram_data(href, title)
                if post:
                    posts.append(post)

    return posts


async def _search_google(
    client: httpx.AsyncClient,
    hashtag: str,
    delay: float,
) -> list[ScrapedPost]:
    """Busca posts via Google."""
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
        post = _extract_instagram_data(href, title)
        if post:
            posts.append(post)

    return posts


def _parse_instagram_html(html: str) -> list[ScrapedPost]:
    """Faz parsing do HTML direto do Instagram."""
    posts: list[ScrapedPost] = []
    soup = BeautifulSoup(html, "html.parser")

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
        # Tenta Instagram direto
        response = await _safe_request(
            client,
            f"https://www.instagram.com/{username}/",
            delay,
        )

        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

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

        # Fallback: busca info via DuckDuckGo
        profile = await _profile_via_duckduckgo(client, username, delay, profile)

    return profile


async def _profile_via_duckduckgo(
    client: httpx.AsyncClient,
    username: str,
    delay: float,
    profile: ScrapedProfile,
) -> ScrapedProfile:
    """Coleta info de perfil via DuckDuckGo."""
    query = quote_plus(f"instagram.com {username} tattoo")
    search_url = f"https://html.duckduckgo.com/html/?q={query}"

    response = await _safe_request(client, search_url, delay)
    if not response or response.status_code != 200:
        return profile

    soup = BeautifulSoup(response.text, "html.parser")

    # Busca no snippet descricao com dados do perfil
    for snippet in soup.find_all("a", class_="result__snippet"):
        text = snippet.get_text(strip=True)
        if not text:
            continue

        # Tenta extrair seguidores
        followers_match = re.search(
            r"([\d,.]+[KkMm]?)\s*(?:Followers|Seguidores|followers|seguidores)",
            text,
        )
        if followers_match:
            profile.followers = _parse_number(followers_match.group(1))

        # Tenta extrair contagem de posts
        posts_match = re.search(
            r"([\d,.]+[KkMm]?)\s*(?:Posts|Publicacoes|posts|publicacoes)",
            text,
        )
        if posts_match:
            profile.post_count = _parse_number(posts_match.group(1))

        if not profile.bio:
            profile.bio = text[:300]

    # Busca tambem no result__snippet de classe diferente
    for snippet in soup.find_all(class_="result__snippet"):
        text = snippet.get_text(strip=True)
        if ("follower" in text.lower() or "seguidor" in text.lower()) and not profile.bio:
            profile.bio = text[:300]
            followers_match = re.search(r"([\d,.]+[KkMm]?)\s*(?:followers|seguidores)", text, re.IGNORECASE)
            if followers_match:
                profile.followers = _parse_number(followers_match.group(1))

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
    if len(username) < 3 or username.isdigit():
        return True
    return False


def reset_request_count() -> None:
    """Reseta contador de requisicoes."""
    global _request_count
    _request_count = 0
