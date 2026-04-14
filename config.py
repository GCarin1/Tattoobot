"""Configuracoes globais do TattooBot Copilot."""

import os
from pathlib import Path

# Diretorio raiz do projeto
BASE_DIR: Path = Path(__file__).resolve().parent

# Arquivos de dados
DATA_DIR: Path = BASE_DIR / "data"
SETTINGS_FILE: Path = BASE_DIR / "settings.json"
HISTORY_FILE: Path = DATA_DIR / "history.json"
COMPETITORS_FILE: Path = DATA_DIR / "competitors.json"
GROWTH_FILE: Path = DATA_DIR / "growth.json"
IDEAS_HISTORY_FILE: Path = DATA_DIR / "ideas_history.json"

# Configuracoes de scraping
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Limites de seguranca
MAX_REQUESTS_PER_SESSION: int = 30
OLLAMA_TIMEOUT: int = 180

# Versao
VERSION: str = "1.0.0"
APP_NAME: str = "TattooBot Copilot"
