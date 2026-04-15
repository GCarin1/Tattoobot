# TattooBot Copilot

Assistente para tatuadores que querem crescer no Instagram de forma **100% segura** — sem nenhuma automacao na conta do Instagram. Funciona como **app de desktop** (Windows) e tambem como **CLI** para quem prefere terminal.

O bot analisa dados publicos, sugere perfis para engajar manualmente, gera comentarios personalizados via IA (Ollama local ou cloud) e oferece ferramentas de marketing digital integradas.

> **Principio fundamental:** O bot NUNCA executa acoes na sua conta do Instagram. Ele pensa, analisa e sugere. Voce executa manualmente no celular. Risco zero de ban.

## Duas formas de uso

O TattooBot pode ser usado de duas formas - as duas compartilham os mesmos dados e configuracoes.

### 1. Desktop (GUI) — recomendado

App bonito com tema blackwork (preto + vermelho sangue), menu lateral e visualizacoes ricas. Ideal para o dia a dia.

```bash
python gui_main.py
```

No Windows, voce pode dar duplo clique em `start-gui.bat`.

Para gerar um **executavel distribuivel (.exe)** veja a secao "Build" abaixo.

### 2. CLI (terminal)

Util para automatizar, scriptar ou usar em ambiente sem UI.

```bash
python main.py                    # menu interativo
python main.py engage             # comando direto
python main.py caption
python main.py ideas "time-lapse"
```

## Requisitos

- Python 3.11+
- [Ollama](https://ollama.ai) instalado e rodando

## Instalacao

```bash
git clone https://github.com/gcarin1/tattoobot.git
cd tattoobot

pip install -r requirements.txt

# Inicie o Ollama (em outro terminal)
ollama serve

# Baixe um modelo local...
ollama pull llama3

# ...ou use um modelo cloud (nao pago, usa sua conta Ollama)
ollama signin
ollama pull gpt-oss:20b-cloud

# Configure (via GUI em Configuracoes, ou via CLI):
python main.py config setup
```

## Funcionalidades

Todas funcionam tanto na GUI quanto na CLI:

| Modulo | O que faz |
|---|---|
| **Engajamento Diario** | Busca perfis em hashtags + gera 3 comentarios IA por perfil |
| **Gerar Legendas** | Legendas com SEO + 30 hashtags por tier + CTAs |
| **Ideias de Conteudo** | 7 ideias originais (Reels/Carrossel/Story/Post) |
| **Spy de Rivais** | Monitora concorrentes e gera analise de estrategia |
| **Comparador de Perfis** | Seu perfil vs rival + plano de acao concreto |
| **Growth Tracker** | Registra metricas semanais + analise IA de tendencia |
| **Avaliar Tatuagem** | IA de visao analisa foto, marca pontos de melhoria na grade |
| **Configuracoes** | Gerencia perfil, hashtags e integracao Ollama |

## Usando Ollama Cloud

O TattooBot funciona tanto com modelos **locais** (rodam na sua maquina) quanto **cloud** (hospedados pela Ollama, nao pago). Para usar cloud:

```bash
ollama signin                          # login na Ollama
ollama pull gpt-oss:20b-cloud          # ou 120b-cloud, kimi-k2, etc.
```

Depois coloque o nome exato do modelo (ex: `gpt-oss:20b-cloud`) no campo **Modelo Ollama (texto)** nas Configuracoes.

## CLI — comandos completos

```bash
python main.py                          # menu interativo

python main.py engage                   # engajamento diario
python main.py caption                  # gerar legenda
python main.py ideas [tema]             # ideias de conteudo
python main.py compare                  # comparar perfis
python main.py evaluate                 # avaliar tattoo

python main.py spy add @user            # adicionar rival
python main.py spy remove @user
python main.py spy list
python main.py spy report               # gerar relatorio

python main.py growth log               # registrar metricas
python main.py growth show              # ver evolucao
python main.py growth export

python main.py config show
python main.py config setup             # wizard
python main.py config set hashtags "blackwork,tattoo,dotwork"
```

## Build do executavel Windows (.exe)

Para gerar um `.exe` autonomo que nao precisa de Python instalado:

```bash
# No Windows, num prompt com Python 3.11+
build.bat
```

O executavel sai em `dist/TattooBot/TattooBot.exe`. Voce pode zipar a pasta `dist/TattooBot` inteira e distribuir.

No Linux/macOS rode `./build.sh` (gera binario nativo do seu SO - nao serve pra Windows).

O build usa `PyInstaller` com o `tattoobot.spec` deste repo. O tema blackwork e todo o CustomTkinter sao empacotados junto.

> **Importante:** o `.exe` nao inclui o Ollama. O usuario final precisa instalar o Ollama separadamente (https://ollama.ai) e rodar `ollama serve` antes de abrir o app. Isso e sinalizado na propria UI do app (indicador verde/vermelho na sidebar).

## Arquitetura

```
Tattoobot/
├── main.py              # Entry CLI (Typer + Rich)
├── gui_main.py          # Entry GUI (CustomTkinter)
├── config.py            # Constantes globais
├── modules/             # Logica de negocio (compartilhada CLI + GUI)
│   ├── engagement.py
│   ├── caption.py
│   ├── content_ideas.py
│   ├── competitor_spy.py
│   ├── profile_comparator.py
│   ├── growth_tracker.py
│   ├── tattoo_evaluator.py
│   ├── ollama_client.py
│   └── scraper.py
├── utils/
│   ├── display.py       # Helpers Rich (CLI)
│   └── storage.py       # Persistencia JSON
├── gui/                 # Camada desktop (CustomTkinter)
│   ├── app.py           # Janela principal + sidebar
│   ├── theme.py         # Paleta blackwork (preto + vermelho)
│   ├── async_worker.py  # Executa asyncio sem travar UI
│   ├── pages/           # Uma pagina por funcionalidade
│   └── widgets/         # Cards e componentes reutilizaveis
├── data/                # JSONs de historico (gerados em runtime)
├── tattoobot.spec       # Config do PyInstaller
├── build.bat            # Build do .exe (Windows)
└── build.sh             # Build (Linux/macOS)
```

A GUI reaproveita os prompts, parsers e scrapers dos modulos - nenhuma logica de negocio e duplicada. A CLI continua funcionando sem modificacoes.

## Seguranca

- Nunca faz login na conta do usuario
- Scraping apenas de dados publicos
- Rate limiting (max 30 requisicoes por sessao)
- Delays aleatorios entre requisicoes
- Headers de browser realistas rotacionados

## Stack Tecnica

- **CustomTkinter** — GUI moderna com tema escuro
- **Typer + Rich** — CLI com subcomandos e terminal bonito
- **httpx** — Requisicoes HTTP async
- **BeautifulSoup4** — Parsing de HTML
- **Ollama** — IA local ou cloud
- **Pillow** — Manipulacao de imagens (anotacao da avaliacao)
- **PyInstaller** — Empacotamento .exe
