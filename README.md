# `consensus-llm`

Servidor MCP local em Python para consenso multi-modelo via OpenRouter.

Este é o documento técnico do projeto. Para instalar e usar o servidor sem
conhecimento prévio de Python ou MCP, consulte o [Guia do usuário](USER_GUIDE.md).

## Interfaces públicas

| Ferramenta | Entrada | Resultado |
| --- | --- | --- |
| `consensus` | `prompt: str` | Uma resposta única, consolidada a partir de geração, peer review e síntese. |
| `consensus_deliberate` | `prompt: str` | Registro estruturado de geração, peer review, revisão e justificativas materiais; não produz síntese final. |

As duas tools enviam o prompt aos modelos configurados via OpenRouter e podem
gerar consumo nessa conta. Não alteram dados do projeto nem dados de usuários.
O prompt aceito pelo MCP tem entre 1 e 8.000 caracteres. Não envie segredos ou
dados pessoais desnecessários.

`hello`, `echo` e `ask_model` não são tools do MCP. `openrouter_client.ask_model`
é uma primitive interna usada por `consensus.py`.

## Arquitetura

### `consensus`

1. **Round 1 — geração:** os três modelos configurados respondem em paralelo.
2. **Round 2 — peer review:** os modelos revisam as respostas disponíveis em
   paralelo.
3. **Round 3 — síntese:** o modelo sintetizador retorna a resposta final.

Os dois primeiros rounds usam `ThreadPoolExecutor`, preservam a ordem de
configuração entre resultados bem-sucedidos e exigem pelo menos dois resultados.
O sintetizador faz até duas tentativas.

### `consensus_deliberate`

Executa três rounds sem usar o sintetizador:

1. geração independente;
2. peer review das respostas dos outros modelos;
3. revisão da resposta própria com JSON validado.

O resultado tem exatamente estas chaves:

```json
{
  "initial_responses": {"provider/model-a": "..."},
  "peer_reviews": {"provider/model-a": "..."},
  "revised_responses": {"provider/model-a": "..."},
  "revision_summary": {
    "provider/model-a": [
      {
        "initial_position": "posição inicial material",
        "feedback": "feedback que levou à reconsideração",
        "final_position": "posição final material",
        "reason": "por que a mudança foi feita"
      }
    ]
  }
}
```

Os mapas preservam a ordem de `CONSENSUS_MODEL_1`, `CONSENSUS_MODEL_2` e
`CONSENSUS_MODEL_3`. Os três identificadores devem ser distintos. Apenas
modelos que concluíram a geração participam dos rounds posteriores. Menos de
dois resultados válidos em qualquer round encerra a execução com erro.

Respostas iniciais e peer reviews são material não confiável: entram nos
prompts como JSON delimitado e nunca devem ser tratados como instruções. O JSON
do Round 3 é aceito somente quando obedece ao schema fechado de
`parse_revision_output`.

## Configuração técnica

O servidor lê estas variáveis do `.env`:

- `OPENROUTER_API_KEY_PLUGIN`: chave do OpenRouter;
- `CONSENSUS_MODEL_1`;
- `CONSENSUS_MODEL_2`;
- `CONSENSUS_MODEL_3`;
- `CONSENSUS_SYNTHESIZER_MODEL`.

`consensus` requer todas as variáveis. `consensus_deliberate` requer os três
modelos participantes, mas não usa `CONSENSUS_SYNTHESIZER_MODEL`.

Nunca solicite, imprima, versione ou registre valores de chaves. O arquivo
`.env` é ignorado pelo Git; [.env.example](.env.example) contém apenas
placeholders.

## Estrutura do projeto

```text
projeto local/
├── .env.example          # modelo de configuração sem segredos
├── consensus.py          # orquestração dos rounds
├── openrouter_client.py  # cliente HTTP do OpenRouter
├── requirements.txt      # dependências Python
├── server.py             # servidor MCP e tools públicas
├── test_consensus.py     # testes unitários sem rede
├── test_openrouter.py    # teste manual de conectividade
├── Makefile              # automação local
├── USER_GUIDE.md         # documentação para usuários
└── README.md             # documentação técnica
```

## Desenvolvimento local

Requer Python 3.12. Em macOS/Linux:

```bash
make setup
make check
```

O equivalente manual é:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_consensus.py
.venv/bin/python -m py_compile consensus.py server.py test_consensus.py
git diff --check
```

No Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v test_consensus.py
.\.venv\Scripts\python.exe -m py_compile consensus.py server.py test_consensus.py
git diff --check
```

Os testes de orquestração não fazem chamadas de rede. O teste de conectividade
é manual e usa `CONSENSUS_MODEL_1`, podendo gerar cobrança:

macOS/Linux:

```bash
.venv/bin/python test_openrouter.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe test_openrouter.py
```

## Execução

O servidor usa Streamable HTTP em `http://127.0.0.1:3000/mcp`.

macOS/Linux:

```bash
make run
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe server.py
```

O servidor escuta somente em `127.0.0.1`. Para conectá-lo ao ChatGPT sem
publicar uma porta, use o Secure MCP Tunnel conforme o [Guia do usuário](USER_GUIDE.md).

## Logs

Além dos logs HTTP do `httpx` e do servidor MCP, cada execução imprime eventos
descritivos com um identificador curto:

```text
[Consensus][run=8f31c2] Round 1/3: generating independent responses
[Consensus][run=8f31c2] Round 1/3 completed: 3 successful responses
[Consensus][run=8f31c2] Round 2/3: running peer reviews
[Consensus][run=8f31c2] Round 3/3: synthesizing the final answer
[Consensus][run=8f31c2] completed successfully
```

`Deliberate` usa o mesmo formato para `consensus_deliberate`. Os logs não
registram prompts, respostas completas ou valores de credenciais.

## Referências oficiais

- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [MCP servers](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
- [Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt)
