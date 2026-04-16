"""TattooBot Desktop - Entry point do app grafico.

Este script lanca a interface CustomTkinter. O modo CLI continua disponivel
via `python main.py <comando>`.

Quando empacotado com PyInstaller em modo --windowed, o stdout/stderr
podem ser None, o que quebra libs como Rich. Redirecionamos pra um
buffer silencioso antes de qualquer import dos modulos do TattooBot.

Quando rodado via `pythonw.exe`, qualquer excecao de import/startup some
silenciosamente. Por isso gravamos um log em `data/gui_error.log` e
mostramos um messagebox Tk (quando possivel) com o erro.
"""

from __future__ import annotations

import io
import sys
import traceback
from datetime import datetime
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


def _add_project_root_to_path() -> Path:
    """Garante que os modulos do projeto sao importaveis.

    Funciona tanto rodando via `python gui_main.py` quanto empacotado
    com PyInstaller (usando sys._MEIPASS como raiz). Retorna o caminho
    da raiz para uso em logging.
    """
    if hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        root = Path(__file__).resolve().parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def _report_fatal_error(root: Path, exc: BaseException) -> None:
    """Grava stacktrace em log e tenta mostrar messagebox ao usuario.

    Sem isso, rodando via pythonw.exe o processo morre silencioso e o
    usuario so ve o eco do .bat sem nenhuma pista do que deu errado.
    """
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    timestamp = datetime.now().isoformat(timespec="seconds")
    log_path = root / "data" / "gui_error.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n===== {timestamp} =====\n{tb}\n")
    except OSError:
        pass

    try:
        import tkinter as tk
        from tkinter import messagebox

        root_tk = tk.Tk()
        root_tk.withdraw()
        messagebox.showerror(
            "TattooBot — falha ao iniciar",
            f"Nao foi possivel abrir a interface grafica.\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            f"Detalhes em: {log_path}",
        )
        root_tk.destroy()
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    _ensure_silent_std_streams()
    root = _add_project_root_to_path()

    try:
        # Imports depois do setup para evitar side effects com stdout None
        from gui.app import launch

        launch()
    except BaseException as exc:  # noqa: BLE001
        _report_fatal_error(root, exc)
        raise


if __name__ == "__main__":
    main()
