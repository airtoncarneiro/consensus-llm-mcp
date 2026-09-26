# `consensus-llm`: MCP local de consenso multi-modelo

`consensus-llm` é um servidor MCP em Python. Sua única interface pública é `consensus(prompt)`: ela consulta três LLMs via OpenRouter, coordena revisão por pares e devolve uma única resposta final consolidada.

O servidor escuta apenas em `127.0.0.1`. Para uso privado no ChatGPT, o **Secure MCP Tunnel** cria uma conexão HTTPS de saída; não há porta pública exposta. Esse fluxo é adequado a desenvolvimento e teste privados, não à publicação pública de um plugin.

## Ferramenta MCP

| Ferramenta | Entrada | Resultado |
| --- | --- | --- |
| `consensus` | `prompt: str` | Uma resposta única, consolidada a partir de geração, peer review e síntese. |

`hello`, `echo` e `ask_model` não são tools do MCP atual. `openrouter_client.ask_model(prompt, model)` é uma primitive interna usada por `consensus.py` para acessar o OpenRouter.

## Arquitetura

`consensus(prompt)` chama `run_consensus` em `consensus.py`:

1. **Round 1 — geração independente:** os três modelos configurados respondem ao prompt original em paralelo.
2. **Round 2 — revisão por pares:** os três modelos recebem as respostas disponíveis e fazem revisões independentes, também em paralelo.
3. **Round 3 — síntese:** o sintetizador configurado recebe as respostas e revisões disponíveis e retorna somente a resposta final ao prompt original.

Os dois primeiros rounds usam `ThreadPoolExecutor`, com uma tarefa por modelo, preservando a ordem configurada entre os resultados bem-sucedidos. Cada um exige pelo menos duas respostas. O sintetizador faz até duas tentativas; se não concluir, a execução falha explicitamente, sem inventar uma resposta. Respostas e revisões são apresentadas aos modelos como material de avaliação não confiável, nunca como instruções.

## Estrutura do projeto

```text
projeto local/
├── .env                    # local, ignorado pelo Git; contém segredos
├── .env.example            # modelo versionado, sem segredo
├── consensus.py            # orquestração dos três rounds
├── openrouter_client.py    # cliente HTTP do OpenRouter
├── server.py               # servidor MCP e tool consensus
├── test_openrouter.py      # teste manual de conectividade
└── README.md
```

## Instalação

Requer Python 3.12, acesso ao OpenRouter, Node.js para o MCP Inspector e permissões na conta OpenAI/ChatGPT para criar e usar um Secure MCP Tunnel.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "mcp>=2,<3" httpx python-dotenv
```

## Configurar o OpenRouter

Crie o `.env` local a partir do arquivo de exemplo e preencha sua chave, que jamais deve ser versionada ou compartilhada:

```bash
cp .env.example .env
```

```dotenv
OPENROUTER_API_KEY_PLUGIN='sua_chave_do_openrouter'

CONSENSUS_MODEL_1='provedor/modelo-1'
CONSENSUS_MODEL_2='provedor/modelo-2'
CONSENSUS_MODEL_3='provedor/modelo-3'
CONSENSUS_SYNTHESIZER_MODEL='provedor/modelo-sintetizador'
```

As quatro variáveis são obrigatórias em tempo de execução. Os três `CONSENSUS_MODEL_*` participam dos rounds 1 e 2; `CONSENSUS_SYNTHESIZER_MODEL` executa o Round 3. Se seu `.env` local já tiver as variáveis antigas, renomeie apenas os identificadores para os nomes acima e preserve seus valores. O código não lê nomes antigos.

Na configuração de exemplo, os modelos são `qwen/qwen3.8-flash`, `openai/gpt-5.6-luna` e `google/gemini-3.8-flash`; o sintetizador é `deepseek/deepseek-v4-flash-0731`. A chave é enviada como Bearer token para `https://openrouter.ai/api/v1/chat/completions`, com timeout HTTP de 60 segundos.

## Executar e validar localmente

O teste de conectividade usa `CONSENSUS_MODEL_1` e não expõe uma tool adicional:

```bash
python test_openrouter.py
```

Inicie o servidor:

```bash
python server.py
```

Ele usa Streamable HTTP em `http://127.0.0.1:3000/mcp`. Antes de configurar o tunnel, valide-o no MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Selecione **Streamable HTTP**, use esse endpoint, liste as tools e teste:

```text
consensus("<um prompt de teste>")
```

Uma execução completa pode fazer até sete chamadas ao OpenRouter: três gerações, três revisões e uma síntese na primeira tentativa.

## Secure MCP Tunnel e ChatGPT

Instale o cliente oficial, crie seu próprio tunnel e uma runtime API key. Guarde a credencial fora do repositório:

```bash
brew install openai/tools/tunnel-client
export CONTROL_PLANE_API_KEY='cole_aqui_a_sua_runtime_api_key'
```

Inicialize um perfil local, conforme as opções exibidas pela versão instalada de `tunnel-client`:

```bash
tunnel-client help quickstart
tunnel-client init \
  --sample sample_mcp_remote_http_noauth \
  --profile consensus-local \
  --tunnel-id '<ID_DO_SEU_TUNNEL>' \
  --mcp-server-url http://127.0.0.1:3000/mcp
tunnel-client doctor --profile consensus-local --explain
tunnel-client run --profile consensus-local
```

No ChatGPT, crie uma conexão/app em modo de desenvolvedor, dê-lhe o nome `consensus-llm`, selecione o tunnel, configure MCP sem OAuth e execute **Scan Tools**. A lista deve conter somente `consensus`. Após alterar tools, metadados ou `instructions`, reinicie o servidor e o tunnel, use **Refresh** na conexão e teste em um novo chat.

Exemplo de pedido:

```text
Use a ferramenta consensus do plugin consensus-llm para responder: <seu prompt>.
```

## Troubleshooting

- `GET /` retornar 404 é esperado: o único endpoint é `/mcp`.
- HTTP 406 em uma chamada manual a `/mcp` pode ocorrer quando faltam os cabeçalhos/protocolo MCP; valide pelo Inspector.
- `connection refused` no `tunnel-client doctor` normalmente indica que `python server.py` não está executando no endereço configurado.
- Se a tool não aparecer no ChatGPT, confirme-a no Inspector, mantenha o tunnel ativo, execute **Refresh** e abra um novo chat.
- Se a execução falhar antes da síntese, confirme os quatro `CONSENSUS_MODEL_*` no `.env`; cada falha de modelo aparece como `[Consensus] Model failed` e são exigidos dois resultados em cada round concorrente.
- Se a síntese falhar, confira `CONSENSUS_SYNTHESIZER_MODEL`, a chave do OpenRouter e os logs `[Consensus] Synthesizer failed`; são feitas no máximo duas tentativas.

## Referências oficiais

- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [MCP servers](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
- [Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt)
