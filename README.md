# `consensus-llm`: MCP local com Arena multi-model

Este repositório contém o servidor MCP `consensus-llm`, em Python, que o ChatGPT pode chamar por meio do **Secure MCP Tunnel** da OpenAI. A interface pública atual expõe somente a ferramenta `arena(prompt)`, que integra o OpenRouter e faz geração, revisão por pares e síntese final no lado do servidor.

O servidor escuta somente em `127.0.0.1`; o `tunnel-client` abre uma conexão HTTPS de saída com a OpenAI. Não é necessário abrir uma porta pública.

> **Escopo.** O Secure MCP Tunnel é adequado para desenvolvimento e teste privados. Ele **não** é um mecanismo de publicação ou distribuição pública de plugins. Para uma publicação pública futura, será necessário um endpoint MCP HTTPS público, estável e com a autenticação exigida pelo processo de publicação.

## Ferramentas MCP

| Ferramenta | Entrada | Comportamento |
| --- | --- | --- |
| `arena` | `prompt: str` | Executa a orquestração multi-modelo no servidor e retorna uma única resposta consolidada. |

As tools `hello`, `echo` e `ask_model` pertencem a marcos anteriores e não são expostas pelo MCP atual. A função interna `openrouter_client.ask_model(prompt, model)` permanece necessária: `arena.py` a usa para realizar as chamadas ao OpenRouter; ela não é uma tool MCP.

## Como a Arena funciona

`arena(prompt)` delega para `run_arena` em `arena.py`. A orquestração ocorre no servidor MCP, não no ChatGPT:

1. **Round 1 — geração independente:** os três modelos configurados respondem ao prompt original em paralelo.
2. **Round 2 — revisão por pares:** os mesmos três modelos recebem as respostas disponíveis e fazem revisões independentes, também em paralelo.
3. **Round 3 — síntese:** o modelo sintetizador recebe as respostas iniciais e as revisões disponíveis e produz apenas a resposta final ao prompt original.

Os rounds concorrentes usam `ThreadPoolExecutor`, com uma tarefa por modelo. O resultado preserva a ordem configurada dos modelos que concluíram com sucesso.

Há degradação controlada: cada um dos dois primeiros rounds exige no mínimo duas respostas bem-sucedidas. Se houver menos de duas gerações ou menos de duas revisões, a Arena falha explicitamente. O sintetizador tem até duas tentativas; se ambas falharem, a Arena também falha explicitamente, sem inventar uma resposta consolidada.

As respostas e revisões fornecidas aos modelos nos rounds seguintes são tratadas nos prompts internos como material de avaliação não confiável, e não como instruções.

## Pré-requisitos

- macOS com Homebrew;
- Python 3.12;
- acesso ao OpenRouter e uma chave de API para uso local;
- acesso à conta/organização OpenAI que permite criar um tunnel e gerar uma **runtime API key** para ele;
- acesso ao modo de desenvolvedor e à criação de conexões MCP no ChatGPT. Essas permissões de ChatGPT e as permissões de tunnel na plataforma OpenAI são independentes;
- Node.js para executar o MCP Inspector via `npx`.

Cada pessoa deve criar e usar suas próprias chaves e seu próprio tunnel. Não compartilhe nem grave credenciais, chaves administrativas ou identificadores de tunnel neste repositório.

## Estrutura do projeto

```text
chatgpt-mcp-test/           # pasta local preservada; nome técnico do MCP: consensus-llm
├── .env                    # local e ignorado pelo Git
├── .gitignore
├── arena.py                # orquestração dos três rounds
├── openrouter_client.py    # cliente HTTP do OpenRouter
├── server.py               # servidor MCP e tools
├── test_openrouter.py      # teste manual de conectividade com OpenRouter
└── README.md
```

## 1. Criar o ambiente e instalar as dependências

No diretório do projeto:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "mcp>=2,<3" httpx python-dotenv
```

O projeto não possui arquivo de dependências versionado; o comando acima cobre os imports atuais de `server.py`, `openrouter_client.py` e `test_openrouter.py`.

## 2. Configurar o OpenRouter e a Arena

Crie localmente o arquivo `.env`. Ele é ignorado pelo Git e é carregado por `python-dotenv` quando `openrouter_client.py` ou `test_openrouter.py` são importados/executados.

```dotenv
OPENROUTER_API_KEY_PLUGIN='sua_chave_do_openrouter'

ARENA_MODEL_1='provedor/modelo-1'
ARENA_MODEL_2='provedor/modelo-2'
ARENA_MODEL_3='provedor/modelo-3'
ARENA_SYNTHESIZER_MODEL='provedor/modelo-sintetizador'
```

Os quatro identificadores de modelo são consumidos em tempo de execução. `ARENA_MODEL_1`, `ARENA_MODEL_2` e `ARENA_MODEL_3` precisam estar definidos para a Arena iniciar; `ARENA_SYNTHESIZER_MODEL` é obrigatório para o Round 3.

Na configuração local atual, os modelos são `qwen/qwen3.8-flash`, `openai/gpt-5.6-luna` e `google/gemini-3.8-flash`; o sintetizador é `deepseek/deepseek-v4-flash-0731`. A chave do OpenRouter é secreta e não deve ser documentada, versionada nem compartilhada.

`OPENROUTER_API_KEY_PLUGIN` é enviada como Bearer token para `https://openrouter.ai/api/v1/chat/completions`. A implementação usa timeout HTTP de 60 segundos e propaga erros HTTP ou respostas inválidas ao chamador.

## 3. Testar a conectividade com o OpenRouter

Com o ambiente ativado e `.env` configurado:

```bash
python test_openrouter.py
```

O teste usa `ARENA_MODEL_1` e a primitive interna `openrouter_client.ask_model` para pedir a resposta exata `OpenRouter funcionando`. Ele é um teste manual de conectividade, não uma suíte automatizada nem um teste da Arena, e não expõe uma tool MCP adicional.

## 4. Executar o servidor MCP

```bash
source .venv/bin/activate
python server.py
```

O transporte é **Streamable HTTP** e o endpoint MCP é:

```text
http://127.0.0.1:3000/mcp
```

## 5. Validar localmente com o MCP Inspector

Antes de envolver o ChatGPT ou o tunnel, valide o servidor local:

```bash
npx @modelcontextprotocol/inspector
```

No Inspector, selecione **Streamable HTTP** e informe:

```text
http://127.0.0.1:3000/mcp
```

Conecte-se, liste as tools e teste:

```text
arena("<um prompt de teste>")
```

`arena` exige a configuração completa do `.env` e pode executar até sete chamadas ao OpenRouter quando todos os modelos respondem e o sintetizador conclui na primeira tentativa.

## 6. Instalar e configurar o Secure MCP Tunnel

Instale o cliente oficial:

```bash
brew install openai/tools/tunnel-client
```

Na área de configurações de tunnels da OpenAI, crie um tunnel para seu próprio uso e crie uma runtime API key destinada ao `tunnel-client`. Guarde a chave em local seguro; não a cole no código, em commits ou em arquivos de configuração versionados.

O `tunnel-client` espera essa credencial na variável de ambiente `CONTROL_PLANE_API_KEY`. No terminal usado para inicializar, diagnosticar ou executar o cliente:

```bash
export CONTROL_PLANE_API_KEY='cole_aqui_a_sua_runtime_api_key'
```

Esse `export` vale apenas para a sessão atual. Por segurança, não acrescente a chave a `.env` versionado, a arquivos do projeto ou a arquivos de inicialização do shell. Ao abrir outro terminal para executar o `tunnel-client`, exporte a variável novamente nele ou use o gerenciador de segredos aprovado no seu ambiente.

Inicialize um perfil local chamado `chatgpt-local` usando o cenário de **remote HTTP MCP sem OAuth**. A nomenclatura dos cenários pode evoluir; confira as opções instaladas antes de inicializar:

```bash
tunnel-client help quickstart
```

Para a versão que oferece o sample `sample_mcp_remote_http_noauth`:

```bash
tunnel-client init \
  --sample sample_mcp_remote_http_noauth \
  --profile chatgpt-local \
  --tunnel-id '<ID_DO_SEU_TUNNEL>' \
  --mcp-server-url http://127.0.0.1:3000/mcp
```

Diagnostique a configuração:

```bash
tunnel-client doctor --profile chatgpt-local --explain
```

Em outro terminal, com `python server.py` em execução, inicie o tunnel:

```bash
tunnel-client run --profile chatgpt-local
```

Verifique a readiness local:

```bash
curl -i http://127.0.0.1:8080/readyz
```

Enquanto criar a conexão e testar no ChatGPT, mantenha ativos os dois processos:

```text
python server.py
tunnel-client run --profile chatgpt-local
```

## 7. Criar e atualizar a conexão no ChatGPT

A interface pode mudar, mas o fluxo é criar uma app/conexão MCP em modo de desenvolvedor e fazer a descoberta das tools:

1. Habilite o modo de desenvolvedor se a sua conta/workspace exigir.
2. Em **Settings/Workspace settings → Apps → Create**, crie uma conexão/app MCP.
3. Dê o nome `consensus-llm`.
4. Escolha **Tunnel** como forma de conexão e selecione o tunnel criado.
5. Para autenticação do MCP, escolha **sem OAuth**: este servidor não implementa OAuth.
6. Execute **Scan Tools** e confira somente `arena`.
7. Crie/salve a conexão. Em workspaces, ela pode aparecer inicialmente como rascunho e a publicação pode exigir um administrador.

Depois de adicionar ou alterar uma tool, seus metadados ou as `instructions` do servidor, reiniciar `python server.py` e `tunnel-client run --profile chatgpt-local` pode não bastar. Na configuração da conexão/plugin `consensus-llm` no ChatGPT, use **Refresh** para redescobrir o catálogo e os metadados MCP. Chats já abertos podem manter o catálogo anterior; depois do Refresh, abra um novo chat para testar.

## 8. Testar no ChatGPT

Abra um novo chat, ative a conexão `consensus-llm` e faça um pedido explícito:

```text
Use a ferramenta arena do plugin consensus-llm para responder: <seu prompt>.
```

As `instructions` do servidor pedem que, quando o usuário solicitar a Arena, o ChatGPT chame `arena` com o prompt original e devolva a resposta final produzida por ela, sem fazer outra comparação ou síntese no cliente.

## Troubleshooting

### `GET /` retorna 404

É esperado. Este projeto só expõe o endpoint MCP em `/mcp`; ele não oferece uma página inicial.

### `curl` ou `tunnel-client doctor` recebe HTTP 406 em `/mcp`

Isso pode ser normal para um endpoint Streamable HTTP MCP quando a requisição não traz os cabeçalhos/protocolo MCP esperados. Valide a conexão com o MCP Inspector e, depois, pelo fluxo do `tunnel-client`; não conclua que o servidor está inválido apenas pelo 406 cru.

### `connection refused` no `tunnel-client doctor`

O servidor MCP local provavelmente não está em execução, está usando outra porta ou não está no endereço configurado. Inicie `python server.py`, confirme `http://127.0.0.1:3000/mcp` no Inspector e repita o `doctor`.

### A nova tool não aparece no ChatGPT

Confirme a tool no Inspector e mantenha o tunnel ativo. Depois de qualquer mudança, reinicie `python server.py` e `tunnel-client run --profile chatgpt-local`, use **Refresh** na configuração da conexão/plugin e teste em um novo chat.

### A Arena falha antes da síntese

Confira se os quatro `ARENA_MODEL_*` estão definidos no `.env`. Depois verifique os erros registrados no terminal: cada chamada de geração ou revisão que falha é registrada como `[Arena] Model failed`. A execução exige pelo menos duas gerações e duas revisões concluídas.

### A Arena falha na síntese

Confira `ARENA_SYNTHESIZER_MODEL`, a chave do OpenRouter e os erros no terminal. A implementação registra até duas falhas como `[Arena] Synthesizer failed (attempt 1/2)` e `(attempt 2/2)` antes de abortar a execução.

### Preciso instalar o plugin de tunnel do Codex?

Não. Este fluxo usa o binário `tunnel-client`, o servidor Python MCP e a criação da conexão no ChatGPT. Nenhum plugin de tunnel do Codex é necessário.

## Referências oficiais

- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [MCP servers](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
- [Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt)
- [Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
