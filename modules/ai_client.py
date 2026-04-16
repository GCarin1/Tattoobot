"""Abstração unificada de providers de IA: Ollama (padrão), OpenAI, Anthropic.

Todos os módulos novos usam este client. Fallback automático para Ollama
caso API key inválida ou ausente.
"""

import httpx

from config import OLLAMA_TIMEOUT
from utils.display import get_spinner, show_error, show_warning


async def generate(
    prompt: str,
    settings: dict,
    system_prompt: str = "",
    temperature: float = 0.8,
    top_p: float = 0.9,
) -> str | None:
    """Gera texto via provider configurado nas settings.

    Ordem de tentativa:
    1. OpenAI  — se ai_provider == 'openai' e openai_api_key preenchida
    2. Anthropic — se ai_provider == 'anthropic' e anthropic_api_key preenchida
    3. Ollama  — padrão / fallback sempre disponível
    """
    provider = settings.get("ai_provider", "ollama")

    if provider == "openai":
        api_key = settings.get("openai_api_key", "").strip()
        if api_key:
            result = await _generate_openai(prompt, api_key, settings, system_prompt, temperature)
            if result:
                return result
        show_warning("Chave OpenAI ausente ou inválida. Usando Ollama como fallback.")

    elif provider == "anthropic":
        api_key = settings.get("anthropic_api_key", "").strip()
        if api_key:
            result = await _generate_anthropic(prompt, api_key, settings, system_prompt, temperature)
            if result:
                return result
        show_warning("Chave Anthropic ausente ou inválida. Usando Ollama como fallback.")

    # Padrão / fallback: Ollama
    from modules import ollama_client
    return await ollama_client.generate(
        prompt,
        settings.get("ollama_url", "http://localhost:11434"),
        settings.get("ollama_model", "llama3"),
        system_prompt=system_prompt,
        temperature=temperature,
        top_p=top_p,
    )


async def generate_with_image(
    prompt: str,
    image_base64: str,
    settings: dict,
    system_prompt: str = "",
) -> str | None:
    """Gera texto com imagem. Apenas Ollama suporta visão local neste momento.

    OpenAI GPT-4o também suporta visão — será adicionado se provider == 'openai'.
    """
    provider = settings.get("ai_provider", "ollama")

    if provider == "openai":
        api_key = settings.get("openai_api_key", "").strip()
        if api_key:
            result = await _generate_openai_vision(
                prompt, image_base64, api_key, settings, system_prompt
            )
            if result:
                return result
        show_warning("Chave OpenAI ausente ou inválida. Usando Ollama visão como fallback.")

    # Fallback: Ollama (local ou cloud)
    from modules import ollama_client
    vision_model = settings.get("ollama_vision_model") or settings.get("ollama_model", "llava")
    return await ollama_client.generate_with_image(
        prompt,
        image_base64,
        settings.get("ollama_url", "http://localhost:11434"),
        vision_model,
        system_prompt=system_prompt,
    )


# ─── Backends privados ────────────────────────────────────────────────────────


async def _generate_openai(
    prompt: str,
    api_key: str,
    settings: dict,
    system_prompt: str = "",
    temperature: float = 0.8,
) -> str | None:
    """Gera texto via OpenAI Chat Completions API."""
    model = settings.get("openai_model", "gpt-4o-mini")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": min(max(temperature, 0.0), 2.0),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            with get_spinner() as progress:
                progress.add_task(description=f"Gerando com OpenAI ({model})...", total=None)
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        show_error(f"OpenAI retornou status {response.status_code}: {response.text[:300]}")
        return None
    except httpx.TimeoutException:
        show_error("Timeout na chamada OpenAI.")
        return None
    except Exception as exc:
        show_error(f"Erro com OpenAI: {exc}")
        return None


async def _generate_anthropic(
    prompt: str,
    api_key: str,
    settings: dict,
    system_prompt: str = "",
    temperature: float = 0.8,
) -> str | None:
    """Gera texto via Anthropic Messages API."""
    model = settings.get("anthropic_model", "claude-haiku-4-5-20251001")

    payload: dict = {
        "model": model,
        "max_tokens": 4096,
        "temperature": min(max(temperature, 0.0), 1.0),
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        payload["system"] = system_prompt

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            with get_spinner() as progress:
                progress.add_task(description=f"Gerando com Anthropic ({model})...", total=None)
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=payload,
                    headers=headers,
                )
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"].strip()
        show_error(f"Anthropic retornou status {response.status_code}: {response.text[:300]}")
        return None
    except httpx.TimeoutException:
        show_error("Timeout na chamada Anthropic.")
        return None
    except Exception as exc:
        show_error(f"Erro com Anthropic: {exc}")
        return None


async def _generate_openai_vision(
    prompt: str,
    image_base64: str,
    api_key: str,
    settings: dict,
    system_prompt: str = "",
) -> str | None:
    """Gera texto com imagem via OpenAI GPT-4o Vision."""
    model = settings.get("openai_model", "gpt-4o-mini")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            },
        ],
    })

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            with get_spinner() as progress:
                progress.add_task(description="Analisando imagem com OpenAI...", total=None)
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        show_error(f"OpenAI Vision retornou status {response.status_code}: {response.text[:300]}")
        return None
    except Exception as exc:
        show_error(f"Erro com OpenAI Vision: {exc}")
        return None


# ─── Geração de vídeo (Layer 3) ───────────────────────────────────────────────


async def generate_video_clip(
    prompt: str,
    settings: dict,
    image_base64: str | None = None,
    duration_seconds: int = 4,
) -> str | None:
    """Gera clipe de vídeo curto via API de vídeo configurada.

    Retorna URL do vídeo gerado, ou None se não disponível/erro.
    Suporta: Runway ML, Pika Labs.
    """
    provider = settings.get("video_api_provider", "").strip().lower()
    api_key = settings.get("video_api_key", "").strip()

    if not provider or not api_key:
        show_warning(
            "Nenhuma API de vídeo configurada. "
            "Configure 'video_api_provider' e 'video_api_key' nas Configurações."
        )
        return None

    if provider == "runway":
        return await _generate_runway(prompt, api_key, image_base64, duration_seconds)
    elif provider == "pika":
        return await _generate_pika(prompt, api_key, image_base64, duration_seconds)
    else:
        show_error(f"Provider de vídeo '{provider}' não suportado. Use: runway, pika")
        return None


async def _generate_runway(
    prompt: str,
    api_key: str,
    image_base64: str | None,
    duration_seconds: int,
) -> str | None:
    """Gera vídeo via Runway Gen-3 Alpha API."""
    import asyncio

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": "2024-11-06",
        "Content-Type": "application/json",
    }

    # Monta payload (image-to-video ou text-to-video)
    payload: dict = {
        "model": "gen3a_turbo",
        "promptText": prompt,
        "duration": min(duration_seconds, 10),
        "ratio": "720:1280",  # Vertical para Instagram Reels
    }
    if image_base64:
        payload["promptImage"] = f"data:image/jpeg;base64,{image_base64}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            with get_spinner() as progress:
                progress.add_task(description="Enviando para Runway ML...", total=None)
                response = await client.post(
                    "https://api.runwayml.com/v1/image_to_video",
                    json=payload,
                    headers=headers,
                )

        if response.status_code not in (200, 201):
            show_error(f"Runway retornou status {response.status_code}: {response.text[:300]}")
            return None

        task_id = response.json().get("id")
        if not task_id:
            show_error("Runway não retornou ID de tarefa.")
            return None

        # Polling até o vídeo ficar pronto (máx 3 min)
        from utils.display import console
        console.print(f"[dim]Runway processando tarefa {task_id}... aguardando...[/dim]")
        for _ in range(36):  # 36 × 5s = 3 min
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=10) as client:
                poll = await client.get(
                    f"https://api.runwayml.com/v1/tasks/{task_id}",
                    headers=headers,
                )
            if poll.status_code == 200:
                data = poll.json()
                status = data.get("status", "")
                if status == "SUCCEEDED":
                    outputs = data.get("output", [])
                    if outputs:
                        return outputs[0]
                elif status == "FAILED":
                    show_error(f"Runway falhou: {data.get('failure', 'erro desconhecido')}")
                    return None

        show_error("Timeout aguardando Runway ML (máx 3 min).")
        return None

    except Exception as exc:
        show_error(f"Erro com Runway ML: {exc}")
        return None


async def _generate_pika(
    prompt: str,
    api_key: str,
    image_base64: str | None,
    duration_seconds: int,
) -> str | None:
    """Gera vídeo via Pika Labs API."""
    import asyncio

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict = {
        "prompt": prompt,
        "options": {
            "aspectRatio": "9:16",
            "frameRate": 24,
            "duration": min(duration_seconds, 10),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            with get_spinner() as progress:
                progress.add_task(description="Enviando para Pika Labs...", total=None)
                response = await client.post(
                    "https://api.pika.art/generate",
                    json=payload,
                    headers=headers,
                )

        if response.status_code not in (200, 201, 202):
            show_error(f"Pika retornou status {response.status_code}: {response.text[:300]}")
            return None

        data = response.json()
        video_url = data.get("video_url") or data.get("url")
        if video_url:
            return video_url

        # Algumas versões da API Pika retornam ID para polling
        job_id = data.get("id") or data.get("job_id")
        if not job_id:
            show_error("Pika não retornou URL nem ID de tarefa.")
            return None

        from utils.display import console
        console.print(f"[dim]Pika processando... aguardando...[/dim]")
        for _ in range(24):
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=10) as client:
                poll = await client.get(
                    f"https://api.pika.art/jobs/{job_id}",
                    headers=headers,
                )
            if poll.status_code == 200:
                pdata = poll.json()
                url = pdata.get("video_url") or pdata.get("url")
                if url:
                    return url
                if pdata.get("status") in ("failed", "error"):
                    show_error("Pika falhou ao gerar vídeo.")
                    return None

        show_error("Timeout aguardando Pika Labs (máx 2 min).")
        return None

    except Exception as exc:
        show_error(f"Erro com Pika Labs: {exc}")
        return None
