"""Modulo de avaliacao de tatuagens com IA de visao."""

import base64
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from modules import ollama_client
from utils.display import (
    console,
    ask_input,
    ask_choice,
    show_error,
    show_warning,
    show_success,
    show_info,
    show_panel,
    get_spinner,
)

# Diretorio para salvar imagens anotadas
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "avaliacoes"

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

SYSTEM_PROMPT = """\
Voce e um especialista em tatuagem com mais de 20 anos de experiencia. \
Voce avalia tatuagens com olhar tecnico e construtivo, identificando \
problemas e sugerindo melhorias praticas. Seja direto, tecnico e \
respeitoso. Responda SEMPRE em portugues brasileiro."""

EVALUATION_PROMPT = """\
Analise esta imagem de tatuagem de forma tecnica e detalhada.

A imagem foi dividida em uma grade 3x3 (linhas 1-3 de cima para baixo, \
colunas 1-3 da esquerda para direita).

Responda EXATAMENTE neste formato JSON (sem texto antes ou depois):

{{
  "nota_geral": <numero de 1 a 10>,
  "resumo": "<avaliacao geral em 2-3 frases>",
  "pontos_positivos": [
    "<ponto positivo 1>",
    "<ponto positivo 2>"
  ],
  "problemas": [
    {{
      "grid_linha": <1-3>,
      "grid_coluna": <1-3>,
      "titulo": "<nome curto do problema>",
      "descricao": "<o que esta errado>",
      "como_corrigir": "<instrucao pratica de como melhorar>"
    }}
  ],
  "dicas_gerais": [
    "<dica geral de melhoria 1>",
    "<dica geral de melhoria 2>"
  ]
}}

Avalie os seguintes aspectos tecnicos:
- Qualidade das linhas (firmeza, uniformidade, tremidas)
- Preenchimento e sombreamento (homogeneidade, manchas)
- Proporcoes e simetria
- Saturacao da tinta (profundidade, falhas)
- Contornos (limpeza, bleeding/espalhamento)
- Cicatrizacao visivel (problemas de aplicacao)

Se nao houver problemas em alguma area, deixe a lista de problemas vazia.
Seja honesto mas construtivo. Identifique pelo menos os problemas mais \
evidentes com localizacao na grade."""


def _load_image_as_base64(image_path: Path) -> str | None:
    """Carrega imagem e converte para base64."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except OSError as e:
        show_error(f"Nao foi possivel ler a imagem: {e}")
        return None


def _extract_json(text: str) -> dict | None:
    """Extrai JSON da resposta do modelo, mesmo com texto extra."""
    # Tenta parse direto
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Procura bloco JSON na resposta
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"(\{[\s\S]*\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    return None


def _get_marker_color(index: int) -> tuple[int, int, int]:
    """Retorna cor do marcador baseado no indice."""
    colors = [
        (255, 50, 50),    # vermelho
        (255, 165, 0),    # laranja
        (255, 255, 0),    # amarelo
        (50, 200, 255),   # azul claro
        (255, 100, 200),  # rosa
        (150, 50, 255),   # roxo
        (0, 255, 150),    # verde claro
        (255, 80, 80),    # vermelho claro
        (0, 200, 255),    # ciano
    ]
    return colors[index % len(colors)]


def _annotate_image(image_path: Path, problems: list[dict]) -> Path | None:
    """Marca pontos de problema na imagem e salva versao anotada."""
    try:
        img = Image.open(image_path).convert("RGB")
    except OSError as e:
        show_error(f"Erro ao abrir imagem para anotacao: {e}")
        return None

    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Tamanho do marcador proporcional a imagem
    marker_radius = max(min(width, height) // 25, 15)
    font_size = max(marker_radius, 14)

    # Tenta carregar fonte
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Calcula tamanho de cada celula na grade 3x3
    cell_w = width / 3
    cell_h = height / 3

    for i, problem in enumerate(problems):
        row = problem.get("grid_linha", 2)
        col = problem.get("grid_coluna", 2)

        # Garante que row/col sao inteiros validos
        try:
            row = max(1, min(3, int(row)))
            col = max(1, min(3, int(col)))
        except (TypeError, ValueError):
            row, col = 2, 2

        # Centro da celula na grade
        cx = int((col - 1) * cell_w + cell_w / 2)
        cy = int((row - 1) * cell_h + cell_h / 2)

        color = _get_marker_color(i)
        num = str(i + 1)

        # Circulo externo (borda branca para contraste)
        draw.ellipse(
            [cx - marker_radius - 2, cy - marker_radius - 2,
             cx + marker_radius + 2, cy + marker_radius + 2],
            outline=(255, 255, 255),
            width=3,
        )

        # Circulo do marcador
        draw.ellipse(
            [cx - marker_radius, cy - marker_radius,
             cx + marker_radius, cy + marker_radius],
            outline=color,
            width=4,
        )

        # Numero dentro do circulo
        bbox = font.getbbox(num)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (cx - text_w // 2, cy - text_h // 2),
            num,
            fill=color,
            font=font,
        )

        # Label com titulo ao lado do circulo
        title = problem.get("titulo", "")
        if title:
            label = f" {num}. {title}"
            label_x = cx + marker_radius + 6
            label_y = cy - font_size // 2

            # Fundo escuro para legibilidade
            lbbox = font.getbbox(label)
            lw = lbbox[2] - lbbox[0]
            lh = lbbox[3] - lbbox[1]

            # Ajusta posicao se sair da imagem
            if label_x + lw > width:
                label_x = cx - marker_radius - lw - 10

            draw.rectangle(
                [label_x - 2, label_y - 2, label_x + lw + 4, label_y + lh + 4],
                fill=(0, 0, 0, 180),
            )
            draw.text((label_x, label_y), label, fill=color, font=font)

    # Salva imagem anotada
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_name = f"avaliacao_{image_path.stem}.png"
    output_path = OUTPUT_DIR / output_name
    img.save(output_path, "PNG")
    return output_path


def _display_evaluation(evaluation: dict, annotated_path: Path | None) -> None:
    """Exibe resultado da avaliacao no terminal."""
    nota = evaluation.get("nota_geral", "?")
    resumo = evaluation.get("resumo", "Sem resumo disponivel.")

    # Cor baseada na nota
    try:
        nota_num = float(nota)
        if nota_num >= 8:
            nota_color = "green"
        elif nota_num >= 5:
            nota_color = "yellow"
        else:
            nota_color = "red"
    except (TypeError, ValueError):
        nota_color = "white"

    # Cabecalho com nota
    console.print()
    console.print(
        f"  [bold {nota_color}]NOTA GERAL: {nota}/10[/bold {nota_color}]",
        justify="center",
    )
    console.print()

    # Resumo
    show_panel("Resumo da Avaliacao", resumo, style="cyan")

    # Pontos positivos
    positivos = evaluation.get("pontos_positivos", [])
    if positivos:
        content = "\n".join(f"  [green]+[/green] {p}" for p in positivos)
        show_panel("Pontos Positivos", content, style="green")

    # Problemas encontrados
    problemas = evaluation.get("problemas", [])
    if problemas:
        console.print()
        console.print("[bold red]Problemas Encontrados:[/bold red]")
        console.print()

        for i, prob in enumerate(problemas, 1):
            color = "#{:02x}{:02x}{:02x}".format(*_get_marker_color(i - 1))
            titulo = prob.get("titulo", "Problema")
            descricao = prob.get("descricao", "")
            correcao = prob.get("como_corrigir", "")
            grid_r = prob.get("grid_linha", "?")
            grid_c = prob.get("grid_coluna", "?")

            content = (
                f"[bold]Local na grade:[/bold] Linha {grid_r}, Coluna {grid_c}\n"
                f"\n"
                f"[bold]Problema:[/bold] {descricao}\n"
                f"\n"
                f"[bold green]Como corrigir:[/bold green] {correcao}"
            )
            from rich.panel import Panel
            console.print(Panel(
                content,
                title=f"[bold [{color}]]{i}. {titulo}[/bold [{color}]]",
                border_style="red",
                padding=(1, 2),
            ))
    else:
        show_success("Nenhum problema significativo encontrado! Otima tatuagem!")

    # Dicas gerais
    dicas = evaluation.get("dicas_gerais", [])
    if dicas:
        content = "\n".join(f"  [yellow]*[/yellow] {d}" for d in dicas)
        show_panel("Dicas Gerais", content, style="yellow")

    # Caminho da imagem anotada
    if annotated_path:
        console.print()
        show_success(f"Imagem anotada salva em: {annotated_path}")
        console.print("[dim]Abra a imagem para ver os pontos marcados.[/dim]")


async def run_tattoo_evaluation(settings: dict) -> None:
    """Executa o fluxo completo de avaliacao de tatuagem."""
    show_panel(
        "Avaliacao de Tatuagem",
        "Insira o caminho de uma imagem de tatuagem para receber\n"
        "uma avaliacao profissional com pontos de melhoria marcados.",
        style="magenta",
    )

    # Solicita caminho da imagem
    image_input = ask_input(
        "Caminho da imagem (arraste o arquivo para o terminal)"
    )

    if not image_input:
        show_warning("Nenhuma imagem fornecida.")
        return

    # Limpa path (remove aspas e espacos extras de drag-and-drop)
    image_input = image_input.strip().strip("'\"")
    image_path = Path(image_input).expanduser().resolve()

    # Validacoes
    if not image_path.exists():
        show_error(f"Arquivo nao encontrado: {image_path}")
        return

    if image_path.suffix.lower() not in SUPPORTED_FORMATS:
        show_error(
            f"Formato nao suportado: {image_path.suffix}\n"
            f"Formatos aceitos: {', '.join(SUPPORTED_FORMATS)}"
        )
        return

    # Verifica tamanho do arquivo (max 20MB)
    file_size_mb = image_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 20:
        show_error(f"Imagem muito grande ({file_size_mb:.1f}MB). Maximo: 20MB.")
        return

    show_info(f"Imagem carregada: {image_path.name} ({file_size_mb:.1f}MB)")

    # Modelo de visao
    vision_model = settings.get("ollama_vision_model", "llava")
    ollama_url = settings.get("ollama_url", "http://localhost:11434")

    console.print(f"[dim]Usando modelo de visao: {vision_model}[/dim]")
    console.print(
        "[dim]Isso pode levar alguns minutos dependendo do modelo...[/dim]"
    )
    console.print()

    # Carrega imagem como base64
    image_b64 = _load_image_as_base64(image_path)
    if not image_b64:
        return

    # Envia para avaliacao
    response = await ollama_client.generate_with_image(
        prompt=EVALUATION_PROMPT,
        image_base64=image_b64,
        ollama_url=ollama_url,
        model=vision_model,
        system_prompt=SYSTEM_PROMPT,
    )

    if not response:
        show_error("Nao foi possivel obter a avaliacao da IA.")
        console.print()
        show_warning(
            "Certifique-se de ter um modelo de visao instalado no Ollama.\n"
            "  Execute: [cyan]ollama pull llava[/cyan]\n"
            "  Ou configure outro modelo em: Configuracoes > ollama_vision_model"
        )
        return

    # Parse da resposta JSON
    evaluation = _extract_json(response)

    if not evaluation:
        # Se nao conseguiu parsear JSON, exibe resposta bruta
        show_warning("A IA nao retornou no formato esperado. Exibindo resposta completa:")
        console.print()
        from rich.markdown import Markdown
        console.print(Markdown(response))
        return

    # Anota imagem com marcadores nos problemas
    problems = evaluation.get("problemas", [])
    annotated_path = None
    if problems:
        console.print("[dim]Marcando pontos na imagem...[/dim]")
        annotated_path = _annotate_image(image_path, problems)

    # Exibe resultado
    _display_evaluation(evaluation, annotated_path)
