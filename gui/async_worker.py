"""Helper para rodar coroutines asyncio sem travar a UI do Tkinter.

A GUI precisa chamar funcoes async dos modulos (scraper, ollama_client)
sem bloquear o event loop do Tk. A solucao: rodar a coroutine em uma
thread dedicada, e usar `root.after(0, ...)` para enviar callbacks
de volta pra thread principal do Tk.
"""

from __future__ import annotations

import asyncio
import threading
import traceback
from typing import Any, Awaitable, Callable


class AsyncTask:
    """Executa uma coroutine em thread separada com callbacks no main loop.

    Uso:
        task = AsyncTask(root)
        task.run(
            coro_factory=lambda: minha_funcao_async(args),
            on_result=lambda resultado: mostrar(resultado),
            on_error=lambda erro: mostrar_erro(erro),
        )
    """

    def __init__(self, root) -> None:
        """root e a janela Tk/CTk (precisa do .after)."""
        self.root = root
        self._thread: threading.Thread | None = None
        self._cancel_event = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def cancel(self) -> None:
        """Sinaliza cancelamento. A coro precisa checar `self.cancelled`."""
        self._cancel_event.set()

    def run(
        self,
        coro_factory: Callable[[], Awaitable[Any]],
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """Roda coro_factory() em thread separada.

        `coro_factory` e uma lambda que retorna uma coroutine quando chamada
        (necessario pra criar o coroutine dentro da thread correta).
        """
        if self.running:
            return

        self._cancel_event.clear()

        def _thread_target() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(coro_factory())
                finally:
                    loop.close()
                if on_result and not self.cancelled:
                    self._schedule(lambda: on_result(result))
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                if on_error and not self.cancelled:
                    self._schedule(lambda: on_error(exc))
            finally:
                if on_done:
                    self._schedule(on_done)

        self._thread = threading.Thread(target=_thread_target, daemon=True)
        self._thread.start()

    def _schedule(self, callback: Callable[[], None]) -> None:
        """Envia callback pra thread principal do Tk."""
        try:
            self.root.after(0, callback)
        except Exception:  # noqa: BLE001
            # Janela pode ja ter sido destruida
            pass


def fire_and_forget(root, coro_factory: Callable[[], Awaitable[Any]]) -> AsyncTask:
    """Atalho quando nao precisa de callbacks."""
    task = AsyncTask(root)
    task.run(coro_factory)
    return task
