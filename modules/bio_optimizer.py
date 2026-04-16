"""Otimizador de bio para Instagram de tatuadores."""

import json
import re
from datetime import datetime

from modules import ai_client
from utils import display, storage


def _build_bio_prompt(
    current_bio: str,
    tattoo_style: str,
    artist_city: str,
    artist_name: str,
    secondary_style: str,
    competitor_bios: list[str],
) -> str:
    style_ctx = tattoo_style
    if secondary_style:
        style_ctx += f" / {secondary_style}"
    name_ctx = artist_name or "o artista"

    comp_section = ""
    if competitor_bios:
        comp_section = (
            "\nBIOS DE REFERENCIA (top perfis do nicho para inspiracao — NAO copiar):\n"
            + "\n".join(f"- {b}" for b in competitor_bios[:5])
            + "\n"
        )

    return (
        f"Voce e um especialista em marketing digital para tatuadores no Instagram.\n"
        f"Artista: {name_ctx}. Estilo: {style_ctx}. Cidade: {artist_city or 'Brasil'}.\n\n"
        f"BIO ATUAL:\n{current_bio or '(bio vazia)'}\n\n"
        f"{comp_section}\n"
        f"Problemas comuns em bios de tatuadores:\n"
        f"- Muito generica (nao diferencia o artista)\n"
        f"- Sem CTA claro (nao diz como agendar)\n"
        f"- Sem palavras-chave de busca (dificulta ser encontrado)\n"
        f"- Muito longa ou confusa\n\n"
        f"Crie 3 versoes de bio otimizada (max 150 caracteres cada).\n\n"
        f"Retorne APENAS um JSON no formato:\n"
        f'{{\n'
        f'  "analysis": "analise da bio atual (2-3 frases do que esta bom e o que falta)",\n'
        f'  "variants": [\n'
        f'    {{\n'
        f'      "version": 1,\n'
        f'      "bio": "texto da bio (max 150 chars)",\n'
        f'      "focus": "qual aspecto esta versao prioriza (ex: alcance, conversao, autoridade)",\n'
        f'      "keywords": ["palavra1", "palavra2"]\n'
        f'    }}\n'
        f'  ],\n'
        f'  "cta_tip": "sugestao de CTA para o link na bio",\n'
        f'  "emoji_tip": "sugestao de emojis estrategicos para o nicho tattoo"\n'
        f'}}\n\n'
        f"Regras:\n"
        f"- Cada versao deve ter angulo diferente (nao sejam similares)\n"
        f"- Use emojis com moderacao e estrategia\n"
        f"- Inclua localizacao em pelo menos 1 versao (SEO local)\n"
        f"- Inclua CTA claro em todas (ex: link no perfil, DM aberto)\n"
        f"- PT-BR, tom autentico de artista\n"
        f"- Retorne APENAS o JSON"
    )


def _parse_bio_json(response: str) -> dict | None:
    """Extrai JSON da resposta do LLM."""
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _display_bio_result(result: dict) -> None:
    """Exibe o resultado da otimizacao de bio."""
    from rich.panel import Panel
    from rich.table import Table

    console = display.console

    # Analise da bio atual
    analysis = result.get("analysis", "")
    if analysis:
        console.print()
        console.print(Panel(
            analysis,
            title="[bold yellow]ANALISE DA BIO ATUAL[/bold yellow]",
            border_style="yellow",
        ))

    # Variantes
    variants = result.get("variants", [])
    console.print()
    for v in variants:
        version = v.get("version", "")
        bio_text = v.get("bio", "")
        focus = v.get("focus", "")
        keywords = v.get("keywords", [])
        char_count = len(bio_text)

        color = "green" if char_count <= 150 else "red"
        console.print(Panel(
            f"[bold white]{bio_text}[/bold white]\n\n"
            f"[dim]Foco: {focus}[/dim]\n"
            f"[dim]Palavras-chave: {', '.join(keywords)}[/dim]\n"
            f"[{color}]{char_count} caracteres[/{color}]",
            title=f"[bold red]VERSAO {version}[/bold red]",
            border_style="red",
        ))

    # Dicas extras
    cta_tip = result.get("cta_tip", "")
    emoji_tip = result.get("emoji_tip", "")
    if cta_tip or emoji_tip:
        console.print()
        if cta_tip:
            console.print(f"[bold yellow]CTA na bio:[/bold yellow] {cta_tip}")
        if emoji_tip:
            console.print(f"[bold yellow]Emojis:[/bold yellow] {emoji_tip}")


async def run_bio_optimizer(settings: dict) -> None:
    """Executa o otimizador de bio."""
    tattoo_style = settings.get("tattoo_style", "blackwork")
    secondary_style = settings.get("tattoo_style_secondary", "")
    artist_city = settings.get("artist_city", "")
    artist_name = settings.get("artist_name", "")

    display.console.print()
    display.show_panel(
        "Bio Optimizer",
        "Analisa e otimiza sua bio do Instagram com SEO e CTA.",
        style="cyan",
    )

    # Input: bio atual
    display.console.print()
    display.console.print("[bold]Cole sua bio atual (ou deixe vazio se ainda nao tem):[/bold]")
    display.console.print()
    current_bio = display.console.input("[bold cyan]Bio atual > [/bold cyan]").strip()

    # Coleta bios de concorrentes como referencia (opcional)
    competitor_bios: list[str] = []
    competitors = storage.load_competitors()
    if competitors:
        display.console.print()
        display.console.print(
            f"[dim]Voce tem {len(competitors)} concorrente(s) monitorado(s). "
            "Usando como referencia de nicho...[/dim]"
        )
        from modules.scraper import get_profile_data
        for username in competitors[:3]:
            try:
                data = await get_profile_data(username, settings.get("ollama_url", ""))
                bio = data.get("bio", "")
                if bio and bio not in competitor_bios:
                    competitor_bios.append(bio[:200])
            except Exception:
                pass

    prompt = _build_bio_prompt(
        current_bio, tattoo_style, artist_city, artist_name,
        secondary_style, competitor_bios
    )

    display.console.print("[dim]Analisando e gerando bios otimizadas...[/dim]")
    response = await ai_client.generate(prompt, settings, temperature=0.85)

    if not response:
        display.show_error("Nao foi possivel gerar as bios. Verifique a conexao com a IA.")
        return

    result = _parse_bio_json(response)

    if not result:
        display.console.print(response)
        display.show_warning("Nao foi possivel parsear o resultado. Exibindo resposta bruta.")
        return

    _display_bio_result(result)

    # Salva historico
    variants_text = [v.get("bio", "") for v in result.get("variants", [])]
    storage.add_to_bio_history(variants_text, current_bio)

    display.show_tip(
        "Dica: teste diferentes versoes por 2-4 semanas e veja qual converte mais "
        "cliques no link e mensagens diretas!"
    )
