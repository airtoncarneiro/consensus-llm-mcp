PYTHON ?= python3.12
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
DEPS_STAMP := $(VENV)/.requirements-installed
TUNNEL_PROFILE ?= consensus-local
TUNNEL_ID ?=

.DEFAULT_GOAL := help
.PHONY: help setup test check run inspector tunnel-init tunnel-doctor tunnel

help: ## Exibe os comandos disponíveis.
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

$(DEPS_STAMP): requirements.txt $(VENV_PYTHON)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	touch $(DEPS_STAMP)

setup: $(DEPS_STAMP) ## Cria o ambiente virtual e instala as dependências.

test: $(DEPS_STAMP) ## Executa os testes unitários sem chamadas de rede.
	$(VENV_PYTHON) -m unittest -v test_consensus.py

check: test ## Executa testes, valida sintaxe e verifica o diff.
	$(VENV_PYTHON) -m py_compile consensus.py server.py test_consensus.py
	git diff --check

run: $(DEPS_STAMP) ## Inicia o servidor MCP em http://127.0.0.1:3000/mcp.
	$(VENV_PYTHON) server.py

inspector: ## Abre o MCP Inspector; use o endpoint http://127.0.0.1:3000/mcp.
	npx @modelcontextprotocol/inspector

tunnel-init: ## Cria o perfil do tunnel; requer TUNNEL_ID=tunnel_... e CONTROL_PLANE_API_KEY.
	@test -n "$(TUNNEL_ID)" || (echo "Use: make tunnel-init TUNNEL_ID=tunnel_..."; exit 2)
	tunnel-client init --sample sample_mcp_remote_no_auth --profile $(TUNNEL_PROFILE) --tunnel-id $(TUNNEL_ID) --mcp-server-url http://127.0.0.1:3000/mcp

tunnel-doctor: ## Valida o perfil do tunnel configurado.
	tunnel-client doctor --profile $(TUNNEL_PROFILE) --explain

tunnel: ## Inicia o Secure MCP Tunnel com TUNNEL_PROFILE (padrão: consensus-local).
	tunnel-client run --profile $(TUNNEL_PROFILE)
