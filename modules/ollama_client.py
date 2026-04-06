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
            "temperature": 0.8,
            "top_p": 0.9,
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
