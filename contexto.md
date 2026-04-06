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

---

## 06/04/2026 - Menu interativo + correcao do scraper

### Menu interativo com ASCII art
- Adicionado um logo ASCII grande do TattooBot no banner (display.py)
- Criado menu interativo que aparece quando o usuario roda `python main.py` sem argumentos
- O menu mostra todas as opcoes numeradas (1 a 6 + 0 para sair) em uma tabela estilizada
- Cada modulo (spy, growth, config) ganhou submenu proprio com opcoes numeradas
- Apos cada acao, o usuario pressiona Enter para voltar ao menu principal
- Os comandos diretos (ex: `python main.py engage`) continuam funcionando normalmente

### Correcao do scraper
- Problema: tanto o Instagram quanto o DuckDuckGo estavam bloqueando as requisicoes, fazendo o comando `engage` falhar sempre
- Solucao: adicionados multiplos fallbacks de busca web em cadeia:
  1. Scraping direto do Instagram (tentativa original)
  2. Busca via Bing (novo)
  3. Busca via DuckDuckGo (ja existia)
  4. Busca via Google (novo)
  5. Sugestoes de hashtags do nicho como ultimo recurso (novo)
- Criada funcao generica `_extract_instagram_data()` para extrair username e dados de qualquer resultado de busca
- Melhorados os headers HTTP para parecerem mais com um navegador real
- Adicionado fallback de busca web tambem para o scraping de perfis de concorrentes
- O scraper agora nao depende de uma unica fonte e tenta varias alternativas antes de desistir

---

## 06/04/2026 - Correcao definitiva do scraper (webscraping funcionando)

### Problema diagnosticado
- Testei todas as fontes de dados e descobri que:
  - Instagram retorna 403 (bloqueio total para scraping direto sem login)
  - Bing retorna 403 nesse ambiente
  - DuckDuckGo funciona mas os URLs estavam em formato redirect (`//duckduckgo.com/l/?uddg=URL_REAL_ENCODED`), o scraper nao estava decodificando esses URLs
  - Google retorna HTML mas sem links uteis no formato esperado
  - Os perfis placeholder `_explore_*` que eram gerados como fallback eram filtrados pelo detector de bots, fazendo o engage sempre falhar

### O que foi corrigido
- Criada funcao `_resolve_redirect_url()` que decodifica URLs de redirect do DuckDuckGo, Google e Bing para o URL real do Instagram
- `_extract_instagram_data()` agora chama o resolver antes de tentar extrair dados
- Reorganizada ordem de busca: DuckDuckGo primeiro (unica fonte que funciona de forma confiavel), depois query alternativa no DDG, depois Bing, Google e por ultimo Instagram direto
- Removido o sistema de placeholders `_explore_*` que nunca funcionava
- Scraping de perfil de concorrente agora usa DuckDuckGo como fallback (ao inves de Bing que retorna 403)
- Criada funcao `_extract_username_from_title()` mais robusta para extrair usernames de titulos de resultados

### Testes realizados
- blackworktattoo: 8 perfis reais encontrados
- tattooart: 1 perfil encontrado
- tattoobrasil: 7 perfis encontrados
- blackworkers: 7 perfis encontrados
- tatuagem: 8 perfis encontrados
- Total: 11 perfis unicos apos filtragem (bots removidos, duplicatas removidas)
- Scraping de perfil (@florio.tattoo): bio, seguidores e contagem de posts extraidos com sucesso via DuckDuckGo

---

## 06/04/2026 - Correcao do Spy de Concorrentes

### Problema
- O comando spy report mostrava "Nao e possivel analisar" porque o Ollama recebia todos os dados como N/A
- O scraper coletava a bio do perfil via DuckDuckGo, mas o modulo spy nao passava os dados corretamente ao prompt
- Nao havia busca de informacoes extras sobre o perfil

### O que foi corrigido
- Reescrito o modulo competitor_spy.py
- Adicionada funcao `_collect_web_info()` que busca informacoes extras sobre o perfil no DuckDuckGo (snippets com posts recentes, engagement rate, etc)
- Filtro inteligente: so coleta snippets que mencionam o username do perfil buscado (evita dados de outros perfis)
- Prompt do Ollama reescrito para ser mais pratico: instrui a IA a usar os dados disponiveis e nunca dizer que nao pode analisar
- Stats exibidos no card agora mostram bio, seguidores e quantidade de infos web encontradas

### Teste realizado
- Spy de @florio.tattoo: coletou bio ("BlackWork & Preto e Vermelho"), 292 seguidores, 23 posts, um post recente com legenda real ("Se voce ta vendo esse video..."), e info sobre reels
