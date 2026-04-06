# TattooBot Copilot - Diario de Alteracoes

## 06/04/2026 - Criacao inicial do projeto completo

### O que foi feito
- Criado toda a estrutura do projeto TattooBot Copilot do zero
- O projeto e um assistente CLI em Python para tatuadores (nicho blackwork) que ajuda a crescer no Instagram de forma segura, sem nenhuma automacao na conta do usuario
- O bot apenas analisa, sugere e gera conteudo. O usuario executa manualmente

### Estrutura criada
- **config.py**: Configuracoes globais do projeto (paths, user agents, limites de seguranca, versao)
- **settings.json**: Arquivo de configuracoes do usuario com valores padrao (hashtags, modelo Ollama, cidade, estilo, etc)
- **requirements.txt**: Dependencias do projeto (typer, rich, httpx, beautifulsoup4)

### Utilitarios criados
- **utils/storage.py**: Funcoes para ler/escrever arquivos JSON com backup automatico (.bak), carregar/salvar historico, concorrentes, crescimento e configuracoes
- **utils/display.py**: Todas as funcoes de renderizacao no terminal usando Rich (paineis, tabelas, cards de perfil, graficos ASCII, inputs interativos, spinners)

### Modulos criados
- **modules/ollama_client.py**: Client para API local do Ollama com health check, geracao de texto, listagem de modelos, timeout configuravel e mensagens amigaveis de erro
- **modules/scraper.py**: Coleta de dados publicos do Instagram via scraping de paginas de hashtag, com fallback para busca web (DuckDuckGo), rate limiting, deteccao de bots, headers realistas rotacionados
- **modules/engagement.py**: Modulo principal - coleta perfis de hashtags, filtra repetidos e bots, gera sugestoes de comentarios personalizados via Ollama, salva historico
- **modules/caption.py**: Gerador de legendas otimizadas com SEO, 30 hashtags organizadas por tier e CTAs variados, tudo via input interativo
- **modules/content_ideas.py**: Gerador de 7 ideias de conteudo para Instagram com formato, titulo, descricao, dica e hashtag principal
- **modules/competitor_spy.py**: Monitoramento de concorrentes com coleta de dados de perfil e analise via IA (frequencia, tipos de conteudo, estrategias)
- **modules/growth_tracker.py**: Registro de metricas (seguidores, alcance, engajamento), visualizacao com tabelas e grafico ASCII, analise de tendencia via IA

### CLI criado
- **main.py**: Entry point com Typer, todos os comandos e subcomandos:
  - `tattoobot engage` - engajamento diario
  - `tattoobot caption` - gerar legendas
  - `tattoobot ideas [tema]` - ideias de conteudo
  - `tattoobot spy add/remove/list/report` - monitorar concorrentes
  - `tattoobot growth log/show/export` - acompanhar crescimento
  - `tattoobot config show/set/setup` - gerenciar configuracoes

### Dados inicializados
- Criados arquivos JSON vazios em data/ (history.json, competitors.json, growth.json)

### Principios seguidos
- Nenhuma automacao na conta do Instagram (risco zero de ban)
- Scraping apenas de dados publicos
- Rate limiting e delays entre requisicoes
- Tratamento de erros em todos os modulos
- Backup automatico de arquivos JSON
- Interface bonita com Rich
- Ollama como IA local (sem dependencia de APIs externas pagas)
