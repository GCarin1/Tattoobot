"""Gerador de legendas com SEO, hashtags e CTA."""

import asyncio

from modules import ollama_client
from utils import display


POST_TYPES = [
    "Foto de tattoo finalizada",
    "Processo / making of",
    "Healed (cicatrizada)",
    "Flash / disponivel",
    "Reel / video",
    "Carrossel",
]

GOALS = [
    "Engajamento (curtidas e comentarios)",
    "Agendamento (atrair clientes)",
    "Portfolio (mostrar trabalho)",
]


def _build_caption_prompt(
    tattoo_style: str,
    artist_city: str,
    post_type: str,
    description: str,
    goal: str,
) -> str:
    """Monta prompt para geracao de legendas."""
    return (
        f"Voce e um especialista em marketing digital para tatuadores no Instagram.\n\n"
        f"Informacoes:\n"
        f"- Estilo: {tattoo_style}\n"
        f"- Cidade: {artist_city or 'nao informada'}\n"
        f"- Tipo de post: {post_type}\n"
        f"- Descricao: {description}\n"
        f"- Objetivo: {goal}\n\n"
        f"Gere:\n\n"
        f"1. LEGENDAS (2 opcoes):\n"
        f"- Em portugues brasileiro\n"
        f"- Inclua palavras-chave de SEO naturalmente no texto (ex: '{tattoo_style} tattoo {artist_city}')\n"
        f"- Tom autentico de tatuador, nao corporativo\n"
        f"- Entre 100-200 palavras cada\n\n"
        f"2. HASHTAGS (30):\n"
        f"- 5 hashtags grandes (500k+ posts): ex #tattoo #inked\n"
        f"- 10 hashtags medias (50k-500k): ex #blackworktattoo\n"
        f"- 10 hashtags pequenas/nicho (1k-50k): ex #blackworkbrasil\n"
        f"- 5 hashtags locais: ex #tattoo{artist_city.replace(' ', '').lower() if artist_city else 'brasil'}\n"
        f"- Formato: um bloco unico separado por espaco\n\n"
        f"3. CTAs (2 opcoes):\n"
        f"- Frases que incentivem comentario, salvamento ou compartilhamento\n"
        f"- Variados (nao repetir 'marque um amigo')\n\n"
        f"Formate a saida de forma clara e organizada.\n"
        f"Use marcadores como LEGENDA 1:, LEGENDA 2:, HASHTAGS:, CTA 1:, CTA 2:"
    )


def _parse_caption_response(response: str) -> tuple[list[str], str, list[str]]:
    """Extrai legendas, hashtags e CTAs da resposta do Ollama."""
    captions: list[str] = []
    hashtags: str = ""
    ctas: list[str] = []

    lines = response.split("\n")
    current_section = ""
    current_text: list[str] = []

    for line in lines:
        line_upper = line.strip().upper()

        if "LEGENDA 1" in line_upper or "LEGENDA 1" in line_upper.replace("Ã", "A"):
            if current_section == "caption" and current_text:
                captions.append("\n".join(current_text).strip())
            current_section = "caption"
            current_text = []
            # Se tem conteudo na mesma linha apos ":"
            after_colon = line.split(":", 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                current_text.append(after_colon[1].strip())
        elif "LEGENDA 2" in line_upper:
            if current_section == "caption" and current_text:
                captions.append("\n".join(current_text).strip())
            current_section = "caption"
            current_text = []
            after_colon = line.split(":", 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                current_text.append(after_colon[1].strip())
        elif "HASHTAG" in line_upper:
            if current_section == "caption" and current_text:
                captions.append("\n".join(current_text).strip())
            current_section = "hashtags"
            current_text = []
            after_colon = line.split(":", 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                current_text.append(after_colon[1].strip())
        elif "CTA 1" in line_upper:
            if current_section == "hashtags" and current_text:
                hashtags = " ".join(current_text).strip()
            elif current_section == "caption" and current_text:
                captions.append("\n".join(current_text).strip())
            current_section = "cta"
            current_text = []
            after_colon = line.split(":", 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                ctas.append(after_colon[1].strip())
                current_text = []
        elif "CTA 2" in line_upper:
            if current_section == "cta" and current_text:
                ctas.append("\n".join(current_text).strip())
            current_section = "cta"
            current_text = []
            after_colon = line.split(":", 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                ctas.append(after_colon[1].strip())
                current_text = []
        else:
            if line.strip():
                current_text.append(line.strip())

    # Captura ultimo bloco
    if current_section == "caption" and current_text:
        captions.append("\n".join(current_text).strip())
    elif current_section == "hashtags" and current_text:
        hashtags = " ".join(current_text).strip()
    elif current_section == "cta" and current_text:
        ctas.append("\n".join(current_text).strip())

    return captions, hashtags, ctas


async def run_caption(settings: dict) -> None:
    """Executa o fluxo de geracao de legendas."""
    tattoo_style = settings.get("tattoo_style", "blackwork")
    artist_city = settings.get("artist_city", "")
    ollama_url = settings.get("ollama_url", "http://localhost:11434")
    ollama_model = settings.get("ollama_model", "llama3")

    display.console.print()
    display.show_panel(
        "TattooBot Copilot - Gerador de Legendas",
        "Vamos criar uma legenda otimizada para seu post!",
        style="magenta",
    )

    # Inputs do usuario
    post_type = display.ask_choice("Tipo de post:", POST_TYPES)
    description = display.ask_input("Descreva o conteudo do post (ex: blackwork de lobo no antebraco)")
    goal = display.ask_choice("Objetivo:", GOALS)

    if not description:
        display.show_error("Descricao e obrigatoria.")
        return

    display.console.print()

    # Gerar via Ollama
    prompt = _build_caption_prompt(tattoo_style, artist_city, post_type, description, goal)
    response = await ollama_client.generate(prompt, ollama_url, ollama_model)

    if not response:
        display.show_error("Nao foi possivel gerar legendas. Verifique o Ollama.")
        return

    # Parse e exibicao
    captions, hashtags, ctas = _parse_caption_response(response)

    display.console.print()
    display.show_panel(
        "Resultado",
        "Copie e cole no seu post do Instagram!",
        style="green",
    )

    if captions:
        display.show_caption_result(captions, hashtags, ctas)
    else:
        # Se o parse falhou, exibe resposta bruta
        display.console.print(response)

    display.show_tip("Salve esse post pra usar depois! Voce pode rodar o comando novamente a qualquer momento.")
