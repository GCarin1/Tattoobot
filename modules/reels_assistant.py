"""Assistente de criacao de Reels para tatuadores.

Tres camadas:
  Camada 1 — Script & Roteiro (sempre disponivel via Ollama/OpenAI/Anthropic)
  Camada 2 — Edicao basica de video com moviepy (sem IA)
  Camada 3 — IA generativa de video via Runway ML ou Pika Labs
"""

import json
import re
from datetime import datetime
from pathlib import Path

from modules import ai_client
from utils import display, storage


# ─── Prompts ─────────────────────────────────────────────────────────────────


def _build_script_prompt(
    description: str,
    tattoo_style: str,
    artist_city: str,
    duration_target: str,
) -> str:
    today = datetime.now()
    style_ctx = tattoo_style or "tatuagem"
    city_ctx = f" em {artist_city}" if artist_city else ""

    return (
        f"Voce e um diretor criativo especializado em Reels para tatuadores no Instagram em {today.year}.\n"
        f"O artista trabalha com {style_ctx}{city_ctx}.\n\n"
        f"BRIEFING DO REEL:\n{description}\n\n"
        f"Duracao alvo: {duration_target}\n\n"
        f"Crie um roteiro completo e detalhado para este Reel. Retorne APENAS um JSON valido no formato abaixo:\n\n"
        f'{{\n'
        f'  "title": "titulo curto e chamativo do reel",\n'
        f'  "hook": "frase de abertura impactante (0-3 segundos) que para o scroll",\n'
        f'  "duration_estimate": "ex: 20-30 segundos",\n'
        f'  "scenes": [\n'
        f'    {{\n'
        f'      "scene_number": 1,\n'
        f'      "timing": "0:00 - 0:03",\n'
        f'      "visual": "o que filmar ou mostrar nesta cena (seja especifico)",\n'
        f'      "voiceover": "o que falar em voz over (ou vazio se so musica)",\n'
        f'      "text_overlay": "texto que aparece na tela nesta cena (legenda animada)"\n'
        f'    }}\n'
        f'  ],\n'
        f'  "music_mood": "descricao do tipo de musica ideal (ex: instrumental dark, trap lento, ambient)",\n'
        f'  "music_bpm": "BPM estimado ideal (ex: 80-100 BPM)",\n'
        f'  "caption": "legenda completa otimizada para o post (2-4 paragrafos, com emojis e CTA)",\n'
        f'  "hashtags": ["hashtag1", "hashtag2", "...30 hashtags no total..."],\n'
        f'  "cta": "call-to-action especifico para o final do video e legenda"\n'
        f'}}\n\n'
        f"Regras:\n"
        f"- O hook DEVE parar o scroll nos primeiros 3 segundos\n"
        f"- As cenas devem ser cinematograficas e especificas (nao generico)\n"
        f"- O text_overlay deve ser curto, impactante, em PT-BR\n"
        f"- Gere exatamente 30 hashtags organizadas (mix de nicho/micro/macro)\n"
        f"- A legenda deve ter tom autentico de tatuador, nao de marketing\n"
        f"- Retorne APENAS o JSON, sem texto antes ou depois\n"
    )


# ─── Parsing do JSON ──────────────────────────────────────────────────────────


def _parse_reel_json(response: str) -> dict | None:
    """Extrai JSON do roteiro da resposta do LLM."""
    # Tentativa 1: parse direto
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    # Tentativa 2: bloco ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Tentativa 3: primeiro objeto JSON na string
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ─── Display do roteiro ───────────────────────────────────────────────────────


def _display_reel(reel: dict) -> None:
    """Exibe o roteiro formatado no terminal."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = display.console

    console.print()
    console.print(Panel(
        f"[bold red]{reel.get('title', 'Reel')}[/bold red]",
        title="[bold]ROTEIRO DE REEL[/bold]",
        border_style="red",
    ))

    # Hook e metadados
    console.print()
    console.print(f"[bold yellow]HOOK (0-3s):[/bold yellow] [white]{reel.get('hook', '')}[/white]")
    console.print(f"[bold yellow]DURACAO:[/bold yellow]     [white]{reel.get('duration_estimate', '')}[/white]")
    console.print(f"[bold yellow]MUSICA:[/bold yellow]      [white]{reel.get('music_mood', '')} — {reel.get('music_bpm', '')}[/white]")
    console.print(f"[bold yellow]CTA:[/bold yellow]         [white]{reel.get('cta', '')}[/white]")

    # Cenas
    scenes = reel.get("scenes", [])
    if scenes:
        console.print()
        table = Table(
            title="CENAS",
            show_header=True,
            header_style="bold red",
            border_style="dim",
        )
        table.add_column("Cena", style="yellow", width=6)
        table.add_column("Timing", style="cyan", width=14)
        table.add_column("Visual", style="white", min_width=20)
        table.add_column("Voz Over", style="dim white", min_width=18)
        table.add_column("Text Overlay", style="bold white", min_width=18)

        for scene in scenes:
            table.add_row(
                str(scene.get("scene_number", "")),
                scene.get("timing", ""),
                scene.get("visual", ""),
                scene.get("voiceover", "") or "—",
                scene.get("text_overlay", "") or "—",
            )
        console.print(table)

    # Legenda
    caption = reel.get("caption", "")
    if caption:
        console.print()
        console.print(Panel(
            caption,
            title="[bold yellow]LEGENDA DO POST[/bold yellow]",
            border_style="yellow",
        ))

    # Hashtags
    hashtags = reel.get("hashtags", [])
    if hashtags:
        console.print()
        tags_text = "  ".join(f"#{h.lstrip('#')}" for h in hashtags)
        console.print(Panel(
            f"[dim]{tags_text}[/dim]",
            title="[bold]HASHTAGS (30)[/bold]",
            border_style="dim",
        ))


# ─── Camada 2: Edição básica de vídeo ─────────────────────────────────────────


def _build_slideshow(images: list[Path], reel: dict, output_path: Path) -> bool:
    """Monta slideshow/timelapse a partir de fotos usando moviepy.

    Retorna True se gerou com sucesso, False se moviepy nao disponivel.
    """
    try:
        from moviepy.editor import (
            ImageClip,
            TextClip,
            CompositeVideoClip,
            concatenate_videoclips,
            ColorClip,
        )
    except ImportError:
        display.show_warning(
            "moviepy nao instalado. Para gerar video basico execute:\n"
            "  pip install moviepy"
        )
        return False

    if not images:
        display.show_error("Nenhuma imagem fornecida para o slideshow.")
        return False

    display.console.print("[dim]Montando slideshow com moviepy...[/dim]")

    scenes = reel.get("scenes", [])
    n_scenes = max(len(scenes), 1)
    duration_per_image = max(2.0, 30.0 / max(len(images), 1))

    clips = []
    for i, img_path in enumerate(images):
        try:
            clip = ImageClip(str(img_path), duration=duration_per_image)
            clip = clip.resize(height=1280)
            # Centraliza horizontalmente (9:16 vertical = 720x1280)
            clip = clip.crop(
                x_center=clip.w / 2,
                width=720,
                height=1280,
                y_center=clip.h / 2,
            )

            # Text overlay da cena correspondente
            if i < len(scenes):
                overlay_text = scenes[i].get("text_overlay", "")
                if overlay_text:
                    try:
                        txt = TextClip(
                            overlay_text,
                            fontsize=52,
                            color="white",
                            stroke_color="black",
                            stroke_width=2,
                            method="caption",
                            size=(680, None),
                        ).set_position(("center", 0.75), relative=True).set_duration(duration_per_image)
                        clip = CompositeVideoClip([clip, txt])
                    except Exception:
                        pass  # Se ImageMagick nao disponivel, continua sem texto

            clips.append(clip)
        except Exception as e:
            display.show_warning(f"Pulando imagem {img_path.name}: {e}")

    if not clips:
        display.show_error("Nenhuma imagem valida processada.")
        return False

    # Adiciona hook como cartao de abertura
    hook_text = reel.get("hook", "")
    if hook_text:
        try:
            intro = ColorClip(size=(720, 1280), color=(10, 10, 10), duration=3)
            txt = TextClip(
                hook_text,
                fontsize=58,
                color="white",
                stroke_color="#B00020",
                stroke_width=2,
                method="caption",
                size=(640, None),
            ).set_position("center").set_duration(3)
            intro = CompositeVideoClip([intro, txt])
            clips.insert(0, intro)
        except Exception:
            pass

    final = concatenate_videoclips(clips, method="compose")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    display.console.print(f"[dim]Exportando para {output_path}...[/dim]")
    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio=False,
        verbose=False,
        logger=None,
    )
    return True


# ─── Camada 3: IA generativa de vídeo ────────────────────────────────────────


async def _generate_ai_video(reel: dict, settings: dict) -> str | None:
    """Gera clipe de video via API externa (Runway/Pika)."""
    scenes = reel.get("scenes", [])
    if not scenes:
        return None

    # Monta prompt baseado no primeiro hook + primeira cena visual
    hook = reel.get("hook", "")
    first_visual = scenes[0].get("visual", "") if scenes else ""
    style = settings.get("tattoo_style", "blackwork tattoo")

    video_prompt = (
        f"Cinematic Instagram Reel for a {style} tattoo artist. "
        f"{hook}. "
        f"{first_visual}. "
        f"Dark aesthetic, black and red tones, 9:16 vertical format, professional quality."
    )

    display.console.print(f"[dim]Enviando para API de video: {video_prompt[:100]}...[/dim]")
    return await ai_client.generate_video_clip(video_prompt, settings, duration_seconds=5)


# ─── Fluxo principal ─────────────────────────────────────────────────────────


async def run_reels(settings: dict, mode: str = "script") -> None:
    """Executa o assistente de criacao de Reels.

    mode:
      'script'  — apenas gera roteiro (padrao)
      'video'   — roteiro + slideshow com moviepy (Layer 2)
      'ai'      — roteiro + IA generativa de video (Layer 3)
    """
    tattoo_style = settings.get("tattoo_style", "blackwork")
    artist_city = settings.get("artist_city", "")

    display.console.print()
    display.show_panel(
        "TattooBot Copilot — Assistente de Reels",
        "Vamos criar um roteiro completo para seu proximo Reel!",
        style="red",
    )

    # Input: descrição do Reel
    display.console.print()
    display.console.print("[bold]Descreva o Reel que voce quer criar:[/bold]")
    display.console.print("[dim]Ex: time-lapse da tatuagem geométrica no antebraço, processo completo de 4h[/dim]")
    display.console.print()
    description = display.console.input("[bold cyan]Descricao > [/bold cyan]").strip()

    if not description:
        display.show_error("Descricao vazia. Operacao cancelada.")
        return

    # Duração alvo
    display.console.print()
    display.console.print("[bold]Duracao alvo do Reel:[/bold]")
    display.console.print("  [yellow]1[/yellow]  15-30 segundos (ideal para alcance)")
    display.console.print("  [yellow]2[/yellow]  30-60 segundos (engajamento médio)")
    display.console.print("  [yellow]3[/yellow]  60-90 segundos (processo completo)")
    display.console.print()
    dur_choice = display.console.input("[bold cyan]Duracao (1-3) > [/bold cyan]").strip()
    duration_map = {"1": "15-30 segundos", "2": "30-60 segundos", "3": "60-90 segundos"}
    duration_target = duration_map.get(dur_choice, "15-30 segundos")

    # Gera script via LLM
    display.console.print()
    display.console.print("[dim]Gerando roteiro com IA...[/dim]")

    prompt = _build_script_prompt(description, tattoo_style, artist_city, duration_target)
    response = await ai_client.generate(
        prompt,
        settings,
        temperature=0.85,
        top_p=0.95,
    )

    if not response:
        display.show_error("Nao foi possivel gerar o roteiro. Verifique a conexao com a IA.")
        return

    reel = _parse_reel_json(response)

    if not reel:
        display.console.print()
        display.console.print("[bold yellow]Resposta bruta da IA:[/bold yellow]")
        display.console.print(response)
        display.show_warning("Nao foi possivel parsear o JSON. Exibindo resposta bruta.")
        return

    # Exibe roteiro
    _display_reel(reel)

    # Salva
    saved_path = storage.save_reel(reel)
    display.show_success(f"Roteiro salvo em: {saved_path}")

    # ── Camada 2: Slideshow com moviepy ──────────────────────────────────
    if mode == "video":
        display.console.print()
        display.console.print("[bold]Modo: Edicao Basica de Video (moviepy)[/bold]")
        display.console.print("[dim]Informe o caminho de uma pasta com fotos do processo (JPG/PNG).[/dim]")
        images_dir = display.console.input("[bold cyan]Pasta de imagens > [/bold cyan]").strip()

        if not images_dir:
            display.show_warning("Nenhuma pasta informada. Pulando edicao de video.")
        else:
            img_dir = Path(images_dir.strip('"').strip("'"))
            if not img_dir.exists():
                display.show_error(f"Pasta nao encontrada: {img_dir}")
            else:
                images = sorted([
                    f for f in img_dir.iterdir()
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
                ])
                if not images:
                    display.show_error("Nenhuma imagem JPG/PNG encontrada na pasta.")
                else:
                    display.console.print(f"[dim]{len(images)} imagens encontradas. Montando slideshow...[/dim]")
                    from config import REELS_DIR
                    today = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out = REELS_DIR / f"{today}_slideshow.mp4"
                    success = _build_slideshow(images, reel, out)
                    if success:
                        display.show_success(f"Video gerado: {out}")
                    else:
                        display.show_warning("Nao foi possivel gerar o video. Verifique se moviepy esta instalado.")

    # ── Camada 3: IA generativa ──────────────────────────────────────────
    elif mode == "ai":
        video_provider = settings.get("video_api_provider", "")
        video_key = settings.get("video_api_key", "")

        if not video_provider or not video_key:
            display.show_warning(
                "Nenhuma API de video configurada.\n"
                "Configure 'video_api_provider' (runway ou pika) e 'video_api_key' nas Configuracoes.\n"
                "O roteiro foi gerado e salvo — voce pode usa-lo sem IA generativa de video."
            )
        else:
            display.console.print(f"[dim]Gerando clip de video com {video_provider}...[/dim]")
            video_url = await _generate_ai_video(reel, settings)
            if video_url:
                display.show_success(f"Video gerado! URL: {video_url}")
                reel["video_url"] = video_url
                storage.save_reel(reel)
            else:
                display.show_warning(
                    "Nao foi possivel gerar o video com IA. "
                    "O roteiro foi salvo e esta pronto para uso."
                )

    display.show_tip(
        "Dica: use o roteiro como guia ao filmar. "
        "O hook e o mais importante — grave-o primeiro e filtre o melhor take!"
    )


async def run_reels_history(settings: dict) -> None:
    """Exibe historico de roteiros de Reels salvos."""
    reels = storage.get_recent_reels(limit=10)

    if not reels:
        display.show_warning("Nenhum roteiro salvo ainda. Execute 'Criar Reel' para comecar.")
        return

    display.console.print()
    display.show_panel(
        "Historico de Reels",
        f"{len(reels)} roteiro(s) salvo(s) mais recentes",
        style="red",
    )

    for i, reel in enumerate(reels, 1):
        title = reel.get("title", "Sem titulo")
        hook = reel.get("hook", "")[:60]
        file_path = reel.get("_file", "")
        n_scenes = len(reel.get("scenes", []))
        display.console.print(
            f"  [yellow]{i}.[/yellow] [bold white]{title}[/bold white] — "
            f"[dim]{n_scenes} cenas[/dim]"
        )
        if hook:
            display.console.print(f"     [dim]{hook}...[/dim]")
        if file_path:
            display.console.print(f"     [dim]{Path(file_path).name}[/dim]")
        display.console.print()
