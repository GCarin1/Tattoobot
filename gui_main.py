"""TattooBot Desktop - Entry point do app grafico.

Este script lanca a interface CustomTkinter. O modo CLI continua disponivel
via `python main.py <comando>`.

Quando empacotado com PyInstaller em modo --windowed, o stdout/stderr
podem ser None, o que quebra libs como Rich. Redirecionamos pra um
buffer silencioso antes de qualquer import dos modulos do TattooBot.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path


def _ensure_silent_std_streams() -> None:
    """Em builds --windowed, sys.stdout/stderr podem ser None.

    Como os modulos internos usam Rich (que precisa de um arquivo valido
    para escrever), trocamos por um StringIO silencioso se necessario.
    """
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()


def _add_project_root_to_path() -> None:
    """Garante que os modulos do projeto sao importaveis.

    Funciona tanto rodando via `python gui_main.py` quanto empacotado
    com PyInstaller (usando sys._MEIPASS como raiz).
    """
    if hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        root = Path(__file__).resolve().parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def main() -> None:
    _ensure_silent_std_streams()
    _add_project_root_to_path()

    # Imports depois do setup para evitar side effects com stdout None
    from gui.app import launch

    launch()


if __name__ == "__main__":
    main()
