# TattooBot Copilot

Assistente CLI inteligente para tatuadores que querem crescer no Instagram de forma **100% segura** — sem nenhuma automacao na conta do Instagram.

O bot analisa dados publicos, sugere perfis para engajar manualmente, gera comentarios personalizados via IA local (Ollama) e oferece ferramentas de marketing digital integradas.

> **Principio fundamental:** O bot NUNCA executa acoes na sua conta do Instagram. Ele pensa, analisa e sugere. Voce executa manualmente no celular. Risco zero de ban.

## Requisitos

- Python 3.11+
- [Ollama](https://ollama.ai) instalado e rodando localmente

## Instalacao

```bash
# Clone o repositorio
git clone https://github.com/gcarin1/tattoobot.git
cd tattoobot

# Instale as dependencias
pip install -r requirements.txt

# Instale e inicie o Ollama
# Acesse https://ollama.ai para download
ollama serve
ollama pull llama3

# Configure o bot
python main.py config setup
```

## Comandos

### Engajamento Diario
```bash
python main.py engage
```
Gera lista de perfis relevantes para engajar, com sugestoes de comentarios personalizados gerados por IA.

### Gerar Legendas
```bash
python main.py caption
```
Cria legendas otimizadas com SEO, hashtags organizadas por tier e CTAs variados.

### Ideias de Conteudo
```bash
python main.py ideas
python main.py ideas "time-lapse"
```
Sugere ideias criativas de conteudo para Instagram.

### Monitorar Concorrentes
```bash
python main.py spy add @artista_referencia
python main.py spy list
python main.py spy report
python main.py spy remove @artista_referencia
```
Monitora perfis de tatuadores de referencia e gera relatorios de atividade.

### Acompanhar Crescimento
```bash
python main.py growth log      # Registrar metricas de hoje
python main.py growth show     # Ver evolucao
python main.py growth export   # Exportar dados
```
Registra e visualiza metricas de crescimento ao longo do tempo.

### Configuracoes
```bash
python main.py config show
python main.py config setup
python main.py config set hashtags "blackwork,dotwork,tattoo"
python main.py config set artist_name "Carini"
python main.py config set artist_city "Sao Paulo"
python main.py config set ollama_model "mistral"
python main.py config set profiles_per_day 15
```

## Stack Tecnica

- **Typer** — CLI com subcomandos
- **Rich** — Interface bonita no terminal
- **httpx** — Requisicoes HTTP async
- **BeautifulSoup4** — Parsing de HTML
- **Ollama** — IA local para geracao de texto

## Seguranca

- Nunca faz login na conta do usuario
- Scraping apenas de dados publicos
- Rate limiting (max 30 requisicoes por sessao)
- Delays aleatorios entre requisicoes
- Headers de browser realistas rotacionados
