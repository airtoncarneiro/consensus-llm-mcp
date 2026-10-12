# Guia do usuário: consensus-llm

Este guia explica como instalar e usar o `consensus-llm` em macOS, Windows e
Linux, mesmo sem conhecimento prévio de Python ou MCP.

## O que você vai configurar

O projeto usa duas contas diferentes:

- **OpenRouter**: fornece os modelos de IA e pode cobrar pelas chamadas;
- **OpenAI/ChatGPT**: fornece o Secure MCP Tunnel para o ChatGPT alcançar seu
  servidor local.

O tunnel é opcional para testar localmente no MCP Inspector, mas é necessário
para usar este servidor privado a partir do ChatGPT.

## 1. Pré-requisitos

Você precisará de:

- Python 3.12;
- Node.js e `npx`, usados pelo MCP Inspector;
- uma conta OpenRouter com uma chave e créditos ou limite disponível;
- uma conta OpenAI Platform com permissão para criar/usar um Secure MCP Tunnel;
- acesso a apps MCP personalizados no workspace do ChatGPT, se quiser usar o
  servidor no ChatGPT.

### Verificar Python e Node.js

Abra o terminal e entre na pasta do projeto. Em qualquer sistema, verifique:

```text
python --version
node --version
npx --version
```

Se algum comando não existir, instale Python 3.12 e Node.js pelo instalador
oficial do seu sistema. No macOS com Homebrew, por exemplo:

```bash
brew install python@3.12 node
```

No Linux, use o gerenciador de pacotes da sua distribuição ou os instaladores
oficiais. No Windows, use os instaladores oficiais e marque a opção de
adicionar os programas ao `PATH`.

## 2. Instalar o projeto

### macOS e Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Se `python3.12` não existir, tente `python3` e confirme que a versão exibida é
3.12 ou mais recente compatível.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se o PowerShell bloquear a ativação, use diretamente
`.\.venv\Scripts\python.exe` nos comandos Python ou consulte a política de
execução do Windows.

### Atalho com Make

Em macOS/Linux, `make setup` cria o ambiente virtual e instala as dependências:

```bash
make setup
cp .env.example .env
```

No Windows, use os comandos manuais acima.

## 3. Configurar o OpenRouter

Edite o arquivo `.env` criado no passo anterior. Preencha a chave do OpenRouter
e substitua os quatro identificadores por modelos disponíveis no catálogo da
sua conta. Copie os identificadores exatamente como aparecem no OpenRouter.

```dotenv
OPENROUTER_API_KEY_PLUGIN='sua_chave_do_openrouter'

CONSENSUS_MODEL_1='provedor/modelo-1'
CONSENSUS_MODEL_2='provedor/modelo-2'
CONSENSUS_MODEL_3='provedor/modelo-3'
CONSENSUS_SYNTHESIZER_MODEL='provedor/modelo-sintetizador'
```

Os três `CONSENSUS_MODEL_*` devem ser diferentes. `consensus` requer as quatro
variáveis; `consensus_deliberate` usa apenas os três modelos participantes e
não usa o sintetizador.

Nunca envie a chave em mensagens, commits ou screenshots. O `.env` é ignorado
pelo Git e não deve ser versionado.

## 4. Testar localmente

O teste abaixo faz uma chamada real ao OpenRouter e pode gerar cobrança. Para evitar conflito com as variáveis de ambiente do seu sistema, use o comando `env -u` no macOS/Linux ou defina as variáveis temporariamente no PowerShell.

macOS/Linux:

```bash
make check

env -u OPENROUTER_API_KEY_PLUGIN \
    -u CONSENSUS_MODEL_1 \
    -u CONSENSUS_MODEL_2 \
    -u CONSENSUS_MODEL_3 \
    -u CONSENSUS_SYNTHESIZER_MODEL \
    .venv/bin/python test_openrouter.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_consensus.py
.\.venv\Scripts\python.exe test_openrouter.py
```

Se aparecer `OpenRouter funcionando`, a configuração básica está correta.

## 5. Abrir o servidor e usar o Inspector

Use um primeiro terminal e mantenha-o aberto.

macOS/Linux:

```bash
make run
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe server.py
```

O servidor ficará disponível em:

```text
http://127.0.0.1:3000/mcp
```

Se quiser testar localmente se o MCP está funcionando, abra um segundo terminal e inicie o Inspector.

macOS/Linux:

```bash
cd /caminho/para/chatgpt-mcp-test
npx @modelcontextprotocol/inspector
```

Windows PowerShell:

```powershell
Set-Location C:\caminho\para\chatgpt-mcp-test
npx @modelcontextprotocol/inspector
```

No Inspector:

1. selecione **Streamable HTTP**;
2. informe `http://127.0.0.1:3000/mcp`;
3. liste as tools;
4. teste `consensus` ou `consensus_deliberate` com um prompt simples.

Uma chamada de `consensus` normalmente faz sete chamadas ao OpenRouter. Uma
chamada de `consensus_deliberate` normalmente faz nove. Ambas podem gerar
custos na conta OpenRouter.

Pode fechar o segundo terminal.

## 6. Usar no ChatGPT com Secure MCP Tunnel

O tunnel permite que o ChatGPT use o servidor privado sem abrir uma porta
pública na Internet.

### Criar o tunnel

Antes dos comandos abaixo, crie um tunnel nas [**Platform tunnel settings**](https://platform.openai.com/settings/organization/tunnels) e copie o `tunnel_id` e associe-o à organização Platform e ao workspace ChatGPT
que serão usados.

A criação ou associação pode exigir as permissões `Tunnels Read + Manage` e
`Tunnels Read + Use`. Se essas opções não aparecerem, peça ajuda ao
administrador da organização ou consulte a [documentação oficial do Secure MCP
Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels). Ela começa com `tunnel_`.

### Instalar o tunnel-client

Instale a versão do `tunnel-client` compatível com seu sistema operacional. A
página oficial oferece o download da versão atual.

No macOS, uma opção é:

```bash
brew install openai/tools/tunnel-client
```

No Windows e no Linux, baixe a versão correspondente na [documentação oficial
do Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
ou na página de releases indicada por ela. Coloque o executável no `PATH` e
confirme:

```text
tunnel-client help quickstart
```

### Configurar e iniciar o tunnel

Configure uma runtime API key. Ela é diferente da chave do OpenRouter.
A API Key (`CONTROL_PLANE_API_KEY`) pode ser criada/obtida na [**Platform API keys**](https://platform.openai.com/api-keys). Ela começa com `sk-`.

macOS/Linux:

```bash
export CONTROL_PLANE_API_KEY='sua_runtime_api_key'
tunnel-client init --sample sample_mcp_remote_no_auth --profile consensus-local --tunnel-id '<SEU_TUNNEL_ID>' --mcp-server-url http://127.0.0.1:3000/mcp
tunnel-client doctor --profile consensus-local --explain
```

Windows PowerShell:

```powershell
$env:CONTROL_PLANE_API_KEY = 'sua_runtime_api_key'
tunnel-client init --sample sample_mcp_remote_no_auth --profile consensus-local --tunnel-id '<SEU_TUNNEL_ID>' --mcp-server-url http://127.0.0.1:3000/mcp
tunnel-client doctor --profile consensus-local --explain
```

O comando `init` normalmente só precisa ser executado uma vez. O `doctor`
deve indicar que o perfil está válido.

Com o servidor ainda rodando no primeiro terminal, abra um terceiro terminal e
defina novamente a runtime API key antes de iniciar o tunnel.

macOS/Linux:

```bash
export CONTROL_PLANE_API_KEY='sua_runtime_api_key'
cd /caminho/para/chatgpt-mcp-test
tunnel-client run --profile consensus-local
```

Windows PowerShell:

```powershell
$env:CONTROL_PLANE_API_KEY = 'sua_runtime_api_key'
Set-Location C:\caminho\para\chatgpt-mcp-test
tunnel-client run --profile consensus-local
```

Mantenha o servidor e o tunnel rodando durante o uso.

### Conectar no ChatGPT

No ChatGPT, abra a área de criação de apps/conexões em modo desenvolvedor:

1. escolha **Tunnel** como conexão;
2. selecione o tunnel associado ao workspace;
3. configure MCP sem OAuth;
4. execute **Scan Tools**;
5. confirme que aparecem `consensus` e `consensus_deliberate`.

Depois, teste em um novo chat:

```text
Use a ferramenta consensus do app consensus-llm para responder: <seu prompt>.
```

Para deixar a síntese final a cargo do ChatGPT:

```text
Use consensus_deliberate e sintetize uma resposta final com base nas respostas revisadas e no revision_summary.
```

## Problemas comuns

- **`python3.12` não encontrado:** instale Python 3.12 ou use o comando
  específico do seu sistema, como `py -3.12` no Windows.
- **`make` não encontrado:** use os comandos manuais da seção de instalação.
- **Chave do OpenRouter não encontrada:** confirme o nome
  `OPENROUTER_API_KEY_PLUGIN` e se o `.env` está na pasta do projeto.
- **Modelo inválido ou indisponível:** confira os quatro IDs no catálogo do
  OpenRouter; os três modelos participantes devem ser diferentes.
- **`connection refused`:** confirme que `server.py` está rodando em
  `127.0.0.1:3000`.
- **Tool não aparece no Inspector:** confira o endpoint `/mcp` e selecione
  **Streamable HTTP**.
- **Tunnel não aparece no ChatGPT:** confirme que ele está associado ao
  workspace correto e que o tunnel-client continua rodando.
- **`consensus_deliberate` falha:** confira os três modelos distintos e os
  logs `[Consensus] Model failed`; são necessários dois resultados válidos em
  cada round.
- **Síntese falha:** confira `CONSENSUS_SYNTHESIZER_MODEL`, a chave do
  OpenRouter e os logs `[Consensus] Synthesizer failed`.

Para detalhes técnicos, consulte o [README técnico](README.md).
