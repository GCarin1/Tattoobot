"""Sugestao de ideias de conteudo para Instagram."""

import asyncio
import re

from modules import ollama_client
from utils import display


def _build_ideas_prompt(
    tattoo_style: str,
    artist_city: str,
    theme: str = "",
) -> str:
    """Monta prompt para geracao de ideias."""
    optional_theme = f"Tema especifico solicitado: {theme}\n" if theme else ""
    return (
        f"Voce e um consultor de conteudo para tatuadores no Instagram em 2026.\n"
        f"O artista e especializado em {tattoo_style} na cidade de {artist_city or 'Brasil'}.\n\n"
        f"{optional_theme}"
        f"Gere 7 ideias de conteudo para Instagram que maximizem alcance e engajamento.\n\n"
        f"Para cada ideia, forneca:\n"
        f"- FORMATO: (Reel / Carrossel / Story / Post estatico)\n"
        f"- TITULO: nome curto da ideia\n"
        f"- DESCRICAO: o que mostrar/filmar (2-3 frases)\n"
        f"- DICA: como executar bem (1-2 frases)\n"
        f"- HASHTAG PRINCIPAL: a hashtag mais relevante\n\n"
        f"Priorize formatos que geram mais alcance em 2026:\n"
        f"- Reels com hook nos primeiros 2 segundos\n"
        f"- Carrosseis de processo (stencil -> outline -> shading -> healed)\n"
        f"- Antes/depois\n"
        f"- Time-lapse de sessao\n"
        f"- Reacao do cliente\n"
        f"- Dicas de cuidados (aftercare)\n"
        f"- Flash day / promocoes\n"
        f"- Bastidores do estudio\n\n"
        f"Responda em portugues brasileiro.\n"
        f"Formate cada ideia claramente com os campos acima."
    )


def _parse_ideas(response: str) -> list[dict[str, str]]:
    """Extrai ideias estruturadas da resposta do Ollama."""
    ideas: list[dict[str, str]] = []
    current_idea: dict[str, str] = {}

    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue

        line_upper = line.upper()

        # Detecta inicio de nova ideia (numero ou FORMATO)
        if re.match(r"^\d+[.)]\s*", line) and "FORMATO" not in line_upper:
            if current_idea and "title" in current_idea:
                ideas.append(current_idea)
            current_idea = {}
            # Tenta extrair titulo inline
            title_match = re.sub(r"^\d+[.)]\s*", "", line).strip()
            if title_match and "formato" not in title_match.lower():
                current_idea["title"] = title_match

        if "FORMATO" in line_upper:
            if current_idea and "title" in current_idea and "format" in current_idea:
                ideas.append(current_idea)
                current_idea = {}
            value = line.split(":", 1)[-1].strip() if ":" in line else ""
            # Limpa formato
            for fmt in ["Reel", "Carrossel", "Carousel", "Story", "Post"]:
                if fmt.lower() in value.lower():
                    value = fmt
                    break
            current_idea["format"] = value
        elif "TITULO" in line_upper or "TÍTULO" in line_upper:
            current_idea["title"] = line.split(":", 1)[-1].strip() if ":" in line else ""
        elif "DESCRICAO" in line_upper or "DESCRIÇÃO" in line_upper:
            current_idea["description"] = line.split(":", 1)[-1].strip() if ":" in line else ""
        elif "DICA" in line_upper:
            current_idea["tip"] = line.split(":", 1)[-1].strip() if ":" in line else ""
        elif "HASHTAG" in line_upper:
            tag = line.split(":", 1)[-1].strip() if ":" in line else ""
            current_idea["hashtag"] = tag.lstrip("#")
        elif current_idea:
            # Adiciona texto a campo anterior
            if "description" in current_idea and "tip" not in current_idea:
                current_idea["description"] += " " + line
            elif "tip" in current_idea and "hashtag" not in current_idea:
                current_idea["tip"] += " " + line

    # Ultima ideia
    if current_idea and ("title" in current_idea or "format" in current_idea):
        ideas.append(current_idea)

    return ideas


async def run_ideas(settings: dict, theme: str = "") -> None:
    """Executa o fluxo de geracao de ideias de conteudo."""
    tattoo_style = settings.get("tattoo_style", "blackwork")
    artist_city = settings.get("artist_city", "")
    ollama_url = settings.get("ollama_url", "http://localhost:11434")
    ollama_model = settings.get("ollama_model", "llama3")

    display.console.print()
    from datetime import datetime
    month_year = datetime.now().strftime("%B %Y").title()

    display.show_panel(
        f"TattooBot Copilot - Ideias de Conteudo",
        f"Gerando ideias criativas para {month_year}...",
        style="cyan",
    )

    if not theme:
        theme = display.ask_input("Tema especifico (ou Enter para ideias gerais)", default="")

    # Gerar via Ollama
    prompt = _build_ideas_prompt(tattoo_style, artist_city, theme)
    response = await ollama_client.generate(prompt, ollama_url, ollama_model)

    if not response:
        display.show_error("Nao foi possivel gerar ideias. Verifique o Ollama.")
        return

    ideas = _parse_ideas(response)

    if not ideas:
        # Se o parse falhou, exibe bruto
        display.console.print()
        display.console.print(response)
        return

    display.console.print()
    for i, idea in enumerate(ideas, 1):
        display.show_idea_card(
            index=i,
            format_type=idea.get("format", "Post"),
            title=idea.get("title", "Sem titulo"),
            description=idea.get("description", ""),
            tip=idea.get("tip", ""),
            hashtag=idea.get("hashtag", ""),
        )

    display.show_tip(
        "Escolha 2-3 ideias e planeje a execucao para a proxima semana. "
        "Consistencia e mais importante que quantidade!"
    )
