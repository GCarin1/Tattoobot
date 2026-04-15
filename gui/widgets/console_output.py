"""Area de output estilizada (textbox scrollavel com fonte monospace)."""

from __future__ import annotations

import customtkinter as ctk

from gui import theme


class ConsoleOutput(ctk.CTkTextbox):
    """Textbox estilizada como terminal blackwork (fundo preto, texto claro)."""

    def __init__(self, parent, **kwargs) -> None:
        kwargs.setdefault("fg_color", theme.BLACK_CARD)
        kwargs.setdefault("border_color", theme.BLACK_BORDER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", theme.CARD_RADIUS)
        kwargs.setdefault("text_color", theme.TEXT_PRIMARY)
        kwargs.setdefault("font", theme.FONT_MONO)
        kwargs.setdefault("wrap", "word")
        super().__init__(parent, **kwargs)

        # Cores para tags
        self._configure_tags()

    def _configure_tags(self) -> None:
        """Define cores para tags de texto."""
        try:
            self.tag_config("success", foreground=theme.TEXT_SUCCESS)
            self.tag_config("error", foreground=theme.TEXT_DANGER)
            self.tag_config("warning", foreground=theme.TEXT_WARNING)
            self.tag_config("info", foreground=theme.TEXT_INFO)
            self.tag_config("muted", foreground=theme.TEXT_MUTED)
            self.tag_config("accent", foreground=theme.RED_GLOW)
            self.tag_config("bold", font=theme.FONT_MONO_BOLD)
        except Exception:  # noqa: BLE001
            pass

    def clear(self) -> None:
        """Limpa o conteudo."""
        self.configure(state="normal")
        self.delete("1.0", "end")

    def write(self, text: str, tag: str | None = None) -> None:
        """Adiciona texto no final."""
        self.configure(state="normal")
        if tag:
            self.insert("end", text, tag)
        else:
            self.insert("end", text)
        self.see("end")

    def writeln(self, text: str = "", tag: str | None = None) -> None:
        """Adiciona texto com quebra de linha."""
        self.write(text + "\n", tag)

    def write_header(self, text: str) -> None:
        """Escreve cabecalho em vermelho."""
        self.writeln()
        self.writeln(f"  {text}", tag="accent")
        self.writeln("  " + "─" * min(len(text), 70), tag="muted")

    def write_success(self, text: str) -> None:
        self.writeln(f"  [OK] {text}", tag="success")

    def write_error(self, text: str) -> None:
        self.writeln(f"  [ERRO] {text}", tag="error")

    def write_warning(self, text: str) -> None:
        self.writeln(f"  [AVISO] {text}", tag="warning")

    def write_info(self, text: str) -> None:
        self.writeln(f"  {text}", tag="info")

    def write_muted(self, text: str) -> None:
        self.writeln(f"  {text}", tag="muted")
