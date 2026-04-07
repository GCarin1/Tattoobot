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
        "hashtags": [
            "blackworktattoo",
            "tattooart",
            "tattoobrasil",
            "blackworkers",
            "tatuagem",
        ],
        "profiles_per_day": 10,
        "ollama_model": "llama3",
        "ollama_url": "http://localhost:11434",
        "language": "pt-br",
        "competitor_profiles": [],
        "tattoo_style": "blackwork",
        "artist_name": "",
        "artist_city": "",
        "scraping_delay_seconds": 3,
        "ollama_vision_model": "llava",
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
