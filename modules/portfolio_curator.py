"""Curador de portfolio — sugere quais fotos postar e identifica gaps."""

import base64
import json
import re
from datetime import datetime
from pathlib import Path

from modules import ai_client
from utils import display, storage


BEST_DAYS_TIP = {
    "blackwork": "Terca, Quarta e Sabado costumam ter melhor alcance para tatuagem.",
    "realismo": "Quarta e Sexta sao bons para realismo (audiencia mais engajada).",
    "aquarela": "Quinta e Sabado funcionam bem para estilos coloridos.",
    "default": "Terca a Quinta costumam ter melhor alcance medio no Instagram.",
}

BEST_TIMES_TIP = "Melhores horarios: 9h-11h ou 19h-21h (horario de Brasilia)."


def _build_curator_prompt(
    image_descriptions: list[str],
    tattoo_style: str,
    recent_posts_info: str,
) -> str:
    items = "\n".join(f"{i+1}. {desc}" for i, desc in enumerate(image_descriptions))

    return (
        f"Voce e um curador de portfolio para tatuadores no Instagram.\n"
        f"Estilo predominante: {tattoo_style or 'tatuagem'}.\n\n"
        f"O artista tem as seguintes fotos disponiveis:\n{items}\n\n"
        f"Posts recentes (para evitar repeticao de tema):\n"
        f"{recent_posts_info or 'Nenhuma informacao disponivel.'}\n\n"
        f"Com base nas descricoes, faca uma curadoria:\n\n"
        f"Retorne APENAS um JSON no formato:\n"
        f'{{\n'
        f'  "recommended_order": [\n'
        f'    {{\n'
        f'      "position": 1,\n'
        f'      "image_index": 2,\n'
        f'      "reason": "por que esta foto deve ser postada nesta posicao",\n'
        f'      "best_day": "Segunda / Terca / ...",\n'
        f'      "caption_angle": "angulo sugerido para a legenda (nao a legenda completa)"\n'
        f'    }}\n'
        f'  ],\n'
        f'  "hold_for_now": [1, 3],\n'
        f'  "hold_reasons": {{"1": "muito similar ao ultimo post", "3": "qualidade tecnica inferior"}},\n'
        f'  "gaps": [\n'
        f'    {{\n'
        f'      "gap": "sem nenhum trabalho de serpente nos ultimos 3 meses",\n'
        f'      "suggestion": "o que criar para preencher esse gap"\n'
        f'    }}\n'
        f'  ],\n'
        f'  "feed_tip": "dica de coesao visual do feed"\n'
        f'}}\n\n'
        f"Regras:\n"
        f"- Priorize variedade de temas e posicoes do corpo\n"
        f"- Identifique pelo menos 2-3 gaps no portfolio\n"
        f"- Seja especifico nas razoes (nao generico)\n"
        f"- Retorne APENAS o JSON"
    )


def _build_single_eval_prompt(tattoo_style: str) -> str:
    return (
        f"Voce e um especialista em tatuagem estilo {tattoo_style or 'blackwork'}.\n"
        f"Analise esta foto de tatuagem e retorne um JSON com:\n"
        f'{{\n'
        f'  "description": "descricao objetiva da tatuagem (motivo, posicao no corpo, estilo)",\n'
        f'  "quality_score": 8,\n'
        f'  "strengths": ["ponto forte 1", "ponto forte 2"],\n'
        f'  "instagram_potential": "alto / medio / baixo",\n'
        f'  "themes": ["tema1", "tema2"]\n'
        f'}}\n'
        f"Retorne APENAS o JSON."
    )


def _parse_json(response: str) -> dict | None:
    """Extrai JSON da resposta."""
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


def _display_curation(result: dict, image_paths: list[Path]) -> None:
    """Exibe o resultado da curadoria no terminal."""
    from rich.panel import Panel
    from rich.table import Table

    console = display.console

    recommended = result.get("recommended_order", [])
    hold = result.get("hold_for_now", [])
    hold_reasons = result.get("hold_reasons", {})
    gaps = result.get("gaps", [])
    feed_tip = result.get("feed_tip", "")

    # Ordem recomendada
    if recommended:
        console.print()
        table = Table(
            title="ORDEM DE POSTAGEM RECOMENDADA",
            header_style="bold red",
            border_style="dim",
            show_lines=True,
        )
        table.add_column("Pos.", style="yellow", width=5)
        table.add_column("Imagem", style="cyan", width=30)
        table.add_column("Dia Sugerido", style="white", width=12)
        table.add_column("Por que", style="dim white", min_width=25)
        table.add_column("Angulo da Legenda", style="dim", min_width=20)

        for item in recommended:
            idx = item.get("image_index", 1) - 1
            img_name = image_paths[idx].name if 0 <= idx < len(image_paths) else f"Foto {idx+1}"
            table.add_row(
                str(item.get("position", "")),
                img_name,
                item.get("best_day", "—"),
                item.get("reason", ""),
                item.get("caption_angle", ""),
            )
        console.print(table)

    # Fotos em espera
    if hold:
        console.print()
        console.print("[bold yellow]FOTOS PARA SEGURAR POR AGORA:[/bold yellow]")
        for idx in hold:
            path_idx = int(str(idx)) - 1
            img_name = image_paths[path_idx].name if 0 <= path_idx < len(image_paths) else f"Foto {idx}"
            reason = hold_reasons.get(str(idx), "sem motivo informado")
            console.print(f"  [dim]• {img_name} — {reason}[/dim]")

    # Gaps identificados
    if gaps:
        console.print()
        console.print(Panel(
            "\n".join(
                f"[bold]• {g.get('gap', '')}[/bold]\n  Sugestao: {g.get('suggestion', '')}"
                for g in gaps
            ),
            title="[bold yellow]GAPS NO PORTFOLIO[/bold yellow]",
            border_style="yellow",
        ))

    # Dica de feed
    if feed_tip:
        console.print()
        display.show_tip(f"Feed: {feed_tip}")


async def run_portfolio_curator(settings: dict) -> None:
    """Executa o curador de portfolio."""
    tattoo_style = settings.get("tattoo_style", "blackwork")

    display.console.print()
    display.show_panel(
        "Curador de Portfolio",
        "Analisa suas fotos com IA de visao e sugere o que e quando postar.",
        style="cyan",
    )

    # Input: pasta de imagens
    display.console.print()
    display.console.print("[bold]Informe o caminho da pasta com as fotos das tatuagens:[/bold]")
    display.console.print("[dim]Ex: C:\\Fotos\\Tattoos ou /home/usuario/fotos[/dim]")
    display.console.print()
    images_dir = display.console.input("[bold cyan]Pasta de imagens > [/bold cyan]").strip()

    if not images_dir:
        display.show_error("Caminho vazio. Operacao cancelada.")
        return

    img_dir = Path(images_dir.strip('"').strip("'"))
    if not img_dir.exists():
        display.show_error(f"Pasta nao encontrada: {img_dir}")
        return

    image_paths = sorted([
        f for f in img_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    ])

    if not image_paths:
        display.show_error("Nenhuma imagem JPG/PNG encontrada na pasta.")
        return

    max_images = 10
    if len(image_paths) > max_images:
        display.show_warning(
            f"Encontradas {len(image_paths)} imagens. Usando as primeiras {max_images} para nao sobrecarregar a IA."
        )
        image_paths = image_paths[:max_images]

    display.console.print(
        f"[dim]{len(image_paths)} imagens encontradas. Analisando com IA de visao...[/dim]"
    )
    display.console.print()

    # Analisa cada imagem com visao
    image_descriptions: list[str] = []
    vision_model = settings.get("ollama_vision_model") or settings.get("ollama_model", "llava")
    eval_prompt = _build_single_eval_prompt(tattoo_style)

    for i, img_path in enumerate(image_paths, 1):
        display.console.print(f"[dim]Analisando {i}/{len(image_paths)}: {img_path.name}...[/dim]")
        try:
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            response = await ai_client.generate_with_image(
                eval_prompt, img_b64, settings
            )
            if response:
                parsed = _parse_json(response)
                if parsed:
                    desc = parsed.get("description", img_path.name)
                    score = parsed.get("quality_score", "?")
                    potential = parsed.get("instagram_potential", "?")
                    themes = ", ".join(parsed.get("themes", []))
                    image_descriptions.append(
                        f"{img_path.name} — {desc} "
                        f"(qualidade: {score}/10, potencial IG: {potential}"
                        f"{', temas: ' + themes if themes else ''})"
                    )
                else:
                    image_descriptions.append(f"{img_path.name} — {response[:150]}")
            else:
                image_descriptions.append(f"{img_path.name} — nao foi possivel analisar")
        except Exception as e:
            image_descriptions.append(f"{img_path.name} — erro: {e}")

    # Curadoria com base nas descrições
    display.console.print()
    display.console.print("[dim]Realizando curadoria com IA...[/dim]")
    recent_posts_info = ""
    history = storage.load_history()
    if history:
        recent = history[-5:]
        recent_posts_info = "; ".join(
            f"{h.get('username', '')} ({h.get('date', '')})" for h in recent
        )

    curation_prompt = _build_curator_prompt(
        image_descriptions, tattoo_style, recent_posts_info
    )
    curation_response = await ai_client.generate(curation_prompt, settings, temperature=0.75)

    if not curation_response:
        display.show_error("Nao foi possivel gerar a curadoria.")
        return

    result = _parse_json(curation_response)
    if not result:
        display.console.print(curation_response)
        display.show_warning("Nao foi possivel parsear o JSON. Exibindo resposta bruta.")
        return

    _display_curation(result, image_paths)

    # Dica de horarios
    style_tip = BEST_DAYS_TIP.get(tattoo_style.lower(), BEST_DAYS_TIP["default"])
    console = display.console
    console.print()
    display.show_tip(f"{style_tip} {BEST_TIMES_TIP}")

    # Salva no portfolio storage
    portfolio_data = storage.load_portfolio_data()
    portfolio_data["sessions"].append({
        "date": datetime.now().isoformat(),
        "images_analyzed": len(image_paths),
        "gaps": result.get("gaps", []),
        "recommended_count": len(result.get("recommended_order", [])),
    })
    if len(portfolio_data["sessions"]) > 20:
        portfolio_data["sessions"] = portfolio_data["sessions"][-20:]
    portfolio_data["gaps"] = result.get("gaps", [])
    storage.save_portfolio_data(portfolio_data)
