"""Sugestao de ideias de conteudo para Instagram."""

import re
from datetime import datetime

from modules import ollama_client
from utils import display, storage


PT_MONTHS = {
    1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def _seasonal_hook() -> str:
    """Retorna nota sazonal breve do mes atual (Brasil) para inspirar angulos frescos."""
    month = datetime.now().month
    seasonal = {
        1: "ferias, virada de ano, metas, projetos grandes de corpo inteiro",
        2: "carnaval, pele exposta, cuidados com sol e cicatrizacao no calor",
        3: "volta as aulas, outono comecando, retomada de rotina",
        4: "outono, pascoa, clima mais ameno, oportunidade de sessoes longas",
        5: "dia das maes, homenagens familiares, outono avancado",
        6: "festa junina, dia dos namorados, tatuagens em casal",
        7: "ferias de julho, inverno, pele coberta (ideal para sessoes extensas)",
        8: "dia dos pais, inverno, projetos de longa duracao",
        9: "primavera, renovacao, floral, cores vibrantes",
        10: "outubro rosa, halloween/dark art, conscientizacao",
        11: "black friday, promocoes de estudio, flash day",
        12: "fim de ano, retrospectiva, agenda cheia, presentes",
    }
    return seasonal.get(month, "")


def _build_ideas_prompt(
    tattoo_style: str,
    artist_city: str,
    theme: str,
    recent_titles: list[str],
) -> str:
    """Monta prompt para geracao de ideias, evitando categorias prontas e repeticao."""
    today = datetime.now()
    month_pt = PT_MONTHS.get(today.month, "")
    optional_theme = f"Tema solicitado: {theme}\n" if theme else ""

    seasonal = _seasonal_hook()
    seasonal_section = f"Contexto sazonal (use como inspiracao, NAO obrigatorio): {seasonal}\n" if seasonal else ""

    if recent_titles:
        recent_block = "\n".join(f"- {t}" for t in recent_titles)
        history_section = (
            "\nIdeias ja sugeridas em sessoes anteriores (NAO repita nem gere variacoes "
            "proximas destas — busque angulos totalmente diferentes):\n"
            f"{recent_block}\n"
        )
    else:
        history_section = ""

    return (
        f"Voce e um consultor de conteudo para tatuadores no Instagram em {today.year}.\n"
        f"O artista trabalha com {tattoo_style} em {artist_city or 'Brasil'}.\n"
        f"Estamos no mes de {month_pt}.\n"
        f"{seasonal_section}"
        f"{optional_theme}"
        f"{history_section}\n"
        f"Gere 7 ideias de conteudo ORIGINAIS e VARIADAS para Instagram.\n"
        f"NAO use categorias obvias e batidas (processo stencil-outline-shading, antes/depois, "
        f"aftercare generico, flash day generico, bastidores generico). "
        f"Busque angulos menos explorados, historias reais, ganchos emocionais, "
        f"observacoes tecnicas curiosas, comparacoes, experimentos, formatos hibridos.\n\n"
        f"Para cada ideia, forneca:\n"
        f"- FORMATO: (Reel / Carrossel / Story / Post estatico)\n"
        f"- TITULO: nome curto e especifico da ideia (evite titulos genericos)\n"
        f"- DESCRICAO: o que mostrar/filmar (2-3 frases concretas)\n"
        f"- DICA: como executar bem (1-2 frases)\n"
        f"- HASHTAG PRINCIPAL: a hashtag mais relevante\n\n"
        f"Regras:\n"
        f"- Varie o FORMATO entre as 7 ideias (nao sejam todas Reels)\n"
        f"- Cada ideia deve ser CLARAMENTE diferente das outras em angulo e formato\n"
        f"- Nada de repetir as ideias listadas no historico acima\n"
        f"- Portugues brasileiro, tom de quem entende o dia a dia do tatuador\n\n"
        f"Formate cada ideia claramente com os campos acima, numeradas de 1 a 7."
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
    month_year = datetime.now().strftime("%B %Y").title()

    display.show_panel(
        f"TattooBot Copilot - Ideias de Conteudo",
        f"Gerando ideias criativas para {month_year}...",
        style="cyan",
    )

    if not theme:
        theme = display.ask_input("Tema especifico (ou Enter para ideias gerais)", default="")

    # Pega titulos de ideias recentes para nao repetir
    recent_titles = storage.get_recent_idea_titles(limit=30)

    # Gerar via Ollama com temperatura alta para mais variacao
    prompt = _build_ideas_prompt(tattoo_style, artist_city, theme, recent_titles)
    response = await ollama_client.generate(
        prompt,
        ollama_url,
        ollama_model,
        temperature=1.0,
        top_p=0.95,
    )

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

    # Salva historico (mantem apenas as ultimas 80) para evitar repetir nas proximas sessoes
    storage.add_to_ideas_history(ideas)

    display.show_tip(
        "Escolha 2-3 ideias e planeje a execucao para a proxima semana. "
        "Consistencia e mais importante que quantidade!"
    )
