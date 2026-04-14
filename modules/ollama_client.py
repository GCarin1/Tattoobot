"""Client para API local do Ollama."""

import httpx
from utils.display import console, show_error, show_warning, get_spinner
from config import OLLAMA_TIMEOUT


async def check_ollama(ollama_url: str) -> bool:
    """Verifica se o Ollama esta rodando e acessivel."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def show_ollama_install_help() -> None:
    """Exibe instrucoes de como instalar e iniciar o Ollama."""
    show_error("Ollama nao esta rodando ou nao foi encontrado.")
    console.print()
    console.print("[bold]Como instalar o Ollama:[/bold]")
    console.print("  1. Acesse: https://ollama.ai")
    console.print("  2. Baixe e instale para seu sistema")
    console.print("  3. Execute: [cyan]ollama serve[/cyan]")
    console.print("  4. Baixe um modelo: [cyan]ollama pull llama3[/cyan]")
    console.print()
    console.print("[dim]Voce pode configurar o modelo no settings.json (campo ollama_model)[/dim]")


async def generate(
    prompt: str,
    ollama_url: str,
    model: str,
    system_prompt: str = "",
    temperature: float = 0.8,
    top_p: float = 0.9,
) -> str | None:
    """Envia prompt ao Ollama e retorna a resposta gerada.

    Retorna None se houver erro.
    """
    if not await check_ollama(ollama_url):
        show_ollama_install_help()
        return None

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
        },
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            with get_spinner() as progress:
                progress.add_task(description="Gerando com IA...", total=None)
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json=payload,
                )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                show_error(f"Ollama retornou status {response.status_code}")
                return None

    except httpx.TimeoutException:
        show_error(
            f"Timeout ao gerar resposta (limite: {OLLAMA_TIMEOUT}s). "
            "Tente um modelo menor ou aumente o timeout."
        )
        return None
    except httpx.ConnectError:
        show_ollama_install_help()
        return None
    except Exception as e:
        show_error(f"Erro inesperado com Ollama: {e}")
        return None


async def generate_with_image(
    prompt: str,
    image_base64: str,
    ollama_url: str,
    model: str,
    system_prompt: str = "",
) -> str | None:
    """Envia prompt com imagem ao Ollama (modelos de visao) e retorna a resposta.

    Tenta primeiro /api/chat (compativel com modelos mais novos como gemma3,
    llama3.2-vision) e faz fallback para /api/generate se necessario.
    Retorna None se houver erro.
    """
    if not await check_ollama(ollama_url):
        show_ollama_install_help()
        return None

    # Payload para /api/chat (formato preferido para modelos de visao)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({
        "role": "user",
        "content": prompt,
        "images": [image_base64],
    })

    chat_payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }

    # Payload para /api/generate (fallback)
    generate_payload: dict = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }
    if system_prompt:
        generate_payload["system"] = system_prompt

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            # Tenta /api/chat primeiro (modelos mais novos)
            with get_spinner() as progress:
                progress.add_task(description="Analisando imagem com IA...", total=None)
                response = await client.post(
                    f"{ollama_url}/api/chat",
                    json=chat_payload,
                )

            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                return message.get("content", "").strip()

            # Fallback para /api/generate se /api/chat falhou
            with get_spinner() as progress:
                progress.add_task(description="Tentando via endpoint alternativo...", total=None)
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json=generate_payload,
                )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                show_error(f"Ollama retornou status {response.status_code}")
                show_warning(
                    f"Verifique se o modelo '{model}' esta instalado.\n"
                    f"  Execute: [cyan]ollama list[/cyan] para ver modelos disponiveis.\n"
                    f"  Execute: [cyan]ollama pull {model}[/cyan] para baixar o modelo."
                )
                return None

    except httpx.TimeoutException:
        show_error(
            f"Timeout ao analisar imagem (limite: {OLLAMA_TIMEOUT}s). "
            "Modelos de visao podem ser mais lentos. Tente um modelo menor."
        )
        return None
    except httpx.ConnectError:
        show_ollama_install_help()
        return None
    except Exception as e:
        show_error(f"Erro inesperado com Ollama: {e}")
        return None


async def list_models(ollama_url: str) -> list[str]:
    """Lista modelos disponiveis no Ollama."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
    except (httpx.ConnectError, httpx.TimeoutException):
        pass
    return []
