"""Utilitarios de leitura e escrita de arquivos JSON."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_DIR, SETTINGS_FILE


def ensure_data_dir() -> None:
    """Garante que o diretorio de dados existe."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _backup_file(file_path: Path) -> None:
    """Cria backup do arquivo antes de sobrescrever."""
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)


def read_json(file_path: Path, default: Any = None) -> Any:
    """Le um arquivo JSON e retorna seu conteudo.

    Se o arquivo nao existir ou estiver corrompido, retorna o valor padrao.
    """
    if default is None:
        default = {}
    try:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            if content.strip():
                return json.loads(content)
        return default
    except (json.JSONDecodeError, OSError):
        return default


def write_json(file_path: Path, data: Any) -> None:
    """Escreve dados em um arquivo JSON com backup."""
    ensure_data_dir()
    _backup_file(file_path)
    try:
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        raise OSError(f"Erro ao salvar {file_path.name}: {e}") from e


def load_settings() -> dict[str, Any]:
    """Carrega configuracoes do settings.json.

    Se o arquivo nao existir, cria com valores padrao.
    """
    defaults = {
        # Perfil do artista
        "artist_name": "",
        "artist_city": "",
        "tattoo_style": "blackwork",
        "tattoo_style_secondary": "",  # v2.0: estilo secundario opcional
        # Instagram
        "hashtags": [
            "blackworktattoo",
            "tattooart",
            "tattoobrasil",
            "blackworkers",
            "tatuagem",
        ],
        "profiles_per_day": 10,
        # Ollama (padrao / fallback)
        "ollama_url": "http://localhost:11434",
        "ollama_model": "llama3",
        "ollama_vision_model": "",
        # v2.0: providers de IA opcionais
        "ai_provider": "ollama",          # "ollama" | "openai" | "anthropic"
        "openai_api_key": "",
        "openai_model": "gpt-4o-mini",
        "anthropic_api_key": "",
        "anthropic_model": "claude-haiku-4-5-20251001",
        # v2.0: provider de video opcional
        "video_api_provider": "",         # "runway" | "pika"
        "video_api_key": "",
        # Geral
        "language": "pt-br",
        "scraping_delay_seconds": 3,
        "competitor_profiles": [],
    }
    settings = read_json(SETTINGS_FILE, defaults)
    # Garante que todas as chaves padrao existam
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    """Salva configuracoes no settings.json."""
    _backup_file(SETTINGS_FILE)
    try:
        SETTINGS_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        raise OSError(f"Erro ao salvar settings.json: {e}") from e


def load_history() -> list[dict[str, Any]]:
    """Carrega historico de perfis ja sugeridos."""
    from config import HISTORY_FILE
    return read_json(HISTORY_FILE, [])


def save_history(history: list[dict[str, Any]]) -> None:
    """Salva historico de perfis sugeridos."""
    from config import HISTORY_FILE
    write_json(HISTORY_FILE, history)


def load_competitors() -> list[str]:
    """Carrega lista de perfis de concorrentes."""
    from config import COMPETITORS_FILE
    return read_json(COMPETITORS_FILE, [])


def save_competitors(competitors: list[str]) -> None:
    """Salva lista de concorrentes."""
    from config import COMPETITORS_FILE
    write_json(COMPETITORS_FILE, competitors)


def load_growth() -> list[dict[str, Any]]:
    """Carrega dados de crescimento."""
    from config import GROWTH_FILE
    return read_json(GROWTH_FILE, [])


def save_growth(growth: list[dict[str, Any]]) -> None:
    """Salva dados de crescimento."""
    from config import GROWTH_FILE
    write_json(GROWTH_FILE, growth)


def add_to_history(profiles: list[dict[str, Any]]) -> None:
    """Adiciona perfis ao historico com data atual."""
    history = load_history()
    today = datetime.now().strftime("%d/%m/%Y")
    for profile in profiles:
        profile["date"] = today
        history.append(profile)
    save_history(history)


def get_history_usernames() -> set[str]:
    """Retorna conjunto de usernames ja sugeridos."""
    history = load_history()
    return {entry.get("username", "") for entry in history}


def load_ideas_history() -> list[dict[str, Any]]:
    """Carrega historico de ideias de conteudo ja geradas."""
    from config import IDEAS_HISTORY_FILE
    return read_json(IDEAS_HISTORY_FILE, [])


def save_ideas_history(ideas: list[dict[str, Any]]) -> None:
    """Salva historico de ideias de conteudo."""
    from config import IDEAS_HISTORY_FILE
    write_json(IDEAS_HISTORY_FILE, ideas)


def add_to_ideas_history(ideas: list[dict[str, Any]], keep_last: int = 80) -> None:
    """Adiciona ideias ao historico mantendo apenas as ultimas N."""
    history = load_ideas_history()
    today = datetime.now().strftime("%d/%m/%Y")
    for idea in ideas:
        entry = dict(idea)
        entry["date"] = today
        history.append(entry)
    # Mantem somente as N mais recentes para nao engessar muito a IA
    if len(history) > keep_last:
        history = history[-keep_last:]
    save_ideas_history(history)


def get_recent_idea_titles(limit: int = 30) -> list[str]:
    """Retorna titulos das ultimas ideias geradas (para evitar repeticao)."""
    history = load_ideas_history()
    titles = [h.get("title", "").strip() for h in history if h.get("title")]
    return [t for t in titles[-limit:] if t]


# ─── v2.0: Reels ─────────────────────────────────────────────────────────────


def ensure_reels_dir() -> None:
    """Garante que o diretorio de reels existe."""
    from config import REELS_DIR
    REELS_DIR.mkdir(parents=True, exist_ok=True)


def save_reel(reel: dict[str, Any]) -> str:
    """Salva roteiro de Reel em arquivo JSON. Retorna caminho do arquivo."""
    from config import REELS_DIR
    ensure_reels_dir()
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = reel.get("title", "reel")[:30].lower().replace(" ", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    file_path = REELS_DIR / f"{today}_{slug}.json"
    file_path.write_text(
        json.dumps(reel, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(file_path)


def get_recent_reels(limit: int = 10) -> list[dict[str, Any]]:
    """Retorna os ultimos roteiros de Reels salvos."""
    from config import REELS_DIR
    if not REELS_DIR.exists():
        return []
    files = sorted(REELS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    reels = []
    for f in files[:limit]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = str(f)
            reels.append(data)
        except (json.JSONDecodeError, OSError):
            pass
    return reels


# ─── v2.0: Calendario ────────────────────────────────────────────────────────


def load_calendar() -> list[dict[str, Any]]:
    """Carrega calendario de conteudo."""
    from config import CALENDAR_FILE
    return read_json(CALENDAR_FILE, [])


def save_calendar(calendar: list[dict[str, Any]]) -> None:
    """Salva calendario de conteudo."""
    from config import CALENDAR_FILE
    write_json(CALENDAR_FILE, calendar)


# ─── v2.0: Templates de Atendimento ─────────────────────────────────────────


def load_dm_templates() -> dict[str, Any]:
    """Carrega templates de DM/WhatsApp salvos pelo usuario."""
    from config import DM_TEMPLATES_FILE
    return read_json(DM_TEMPLATES_FILE, {})


def save_dm_templates(templates: dict[str, Any]) -> None:
    """Salva templates de DM/WhatsApp."""
    from config import DM_TEMPLATES_FILE
    write_json(DM_TEMPLATES_FILE, templates)


# ─── v2.0: Bio History ───────────────────────────────────────────────────────


def load_bio_history() -> list[dict[str, Any]]:
    """Carrega historico de bios geradas."""
    from config import BIO_HISTORY_FILE
    return read_json(BIO_HISTORY_FILE, [])


def save_bio_history(history: list[dict[str, Any]]) -> None:
    """Salva historico de bios geradas."""
    from config import BIO_HISTORY_FILE
    write_json(BIO_HISTORY_FILE, history)


def add_to_bio_history(bio_variants: list[str], original_bio: str) -> None:
    """Adiciona variantes de bio ao historico."""
    history = load_bio_history()
    entry = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "original": original_bio,
        "variants": bio_variants,
    }
    history.append(entry)
    if len(history) > 50:
        history = history[-50:]
    save_bio_history(history)


# ─── v2.0: Portfolio ─────────────────────────────────────────────────────────


def load_portfolio_data() -> dict[str, Any]:
    """Carrega dados do curador de portfolio."""
    from config import PORTFOLIO_FILE
    return read_json(PORTFOLIO_FILE, {"sessions": [], "gaps": []})


def save_portfolio_data(data: dict[str, Any]) -> None:
    """Salva dados do curador de portfolio."""
    from config import PORTFOLIO_FILE
    write_json(PORTFOLIO_FILE, data)
