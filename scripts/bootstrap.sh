#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${OMNICLI_PYTHON:-python3}"
VENV_DIR="${OMNICLI_VENV_DIR:-$ROOT_DIR/.venv}"
CONFIG_PATH="${OMNICLI_CONFIG:-$ROOT_DIR/omnicli.yaml}"
MODE="${OMNICLI_BOOTSTRAP_MODE:-plan}"
RUN_CHECKS=false
RUN_PROVIDERS=false
RUN_OFFICIAL_DOCS=false
IDEA=""
LOOPS=1
OUTPUT="proposta.md"
REFINE=false

usage() {
  cat <<'EOF'
Uso:
  scripts/bootstrap.sh [opções]

Por padrão o script apenas exibe o plano. Nenhuma instalação ou alteração é feita.

Opções:
  --apply                 cria/atualiza o ambiente local e instala o projeto
  --check                 executa testes, Ruff e mypy depois da instalação
  --providers             verifica versão e contrato de ajuda das CLIs, sem gerar conteúdo
  --official-docs         verifica se as fontes oficiais registradas estão acessíveis
  --config PATH           caminho da configuração YAML
  --venv PATH             diretório do ambiente virtual
  --idea TEXT             executa conceive explicitamente após o bootstrap
  --loops N               ciclos usados com --idea (padrão: 1)
  --output PATH           saída usada com --idea (padrão: proposta.md)
  --refine                usa o loop condicional de qualidade com --idea
  --help                  exibe esta ajuda

Variáveis:
  OMNICLI_BOOTSTRAP_MODE=apply  equivalente a --apply
  OMNICLI_PYTHON=python3        interpretador base para criar o venv
  OMNICLI_VENV_DIR=.venv        diretório do venv
  OMNICLI_CONFIG=omnicli.yaml   configuração usada pelo projeto

Exemplos:
  scripts/bootstrap.sh
  scripts/bootstrap.sh --apply --check
  scripts/bootstrap.sh --apply --providers --official-docs
  scripts/bootstrap.sh --apply --idea "Meu produto" --output proposta.md
EOF
}

log() {
  printf '[bootstrap] %s\n' "$*"
}

fail() {
  printf '[bootstrap] erro: %s\n' "$*" >&2
  exit 1
}

require_python() {
  command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "Python não encontrado: $PYTHON_BIN"
  "$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit(
        f"Python 3.10+ é necessário; versão encontrada: {sys.version.split()[0]}"
    )
PY
}

normalize_path() {
  local value="$1"
  if [[ "$value" = /* ]]; then
    printf '%s\n' "$value"
  else
    printf '%s\n' "$ROOT_DIR/$value"
  fi
}

plan() {
  log "modo plan: nenhuma alteração será feita"
  log "raiz: $ROOT_DIR"
  log "python base: $PYTHON_BIN"
  log "venv: $VENV_DIR"
  log "configuração: $CONFIG_PATH"
  log "ações previstas com --apply:"
  log "1. criar ou reutilizar o ambiente virtual"
  log "2. instalar o projeto com dependências de desenvolvimento"
  [[ "$RUN_CHECKS" = true ]] && log "3. executar pytest, Ruff e mypy"
  [[ "$RUN_PROVIDERS" = true ]] && log "4. diagnosticar versões e contratos das CLIs configuradas"
  [[ "$RUN_OFFICIAL_DOCS" = true ]] && log "5. verificar fontes oficiais registradas"
  [[ -n "$IDEA" ]] && log "executar concepção somente após aprovação explícita (--apply)"
  return 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      MODE=apply
      shift
      ;;
    --check)
      RUN_CHECKS=true
      shift
      ;;
    --providers)
      RUN_PROVIDERS=true
      shift
      ;;
    --official-docs)
      RUN_OFFICIAL_DOCS=true
      shift
      ;;
    --config)
      [[ $# -ge 2 ]] || fail "--config exige um caminho"
      CONFIG_PATH="$(normalize_path "$2")"
      shift 2
      ;;
    --venv)
      [[ $# -ge 2 ]] || fail "--venv exige um caminho"
      VENV_DIR="$(normalize_path "$2")"
      shift 2
      ;;
    --idea)
      [[ $# -ge 2 ]] || fail "--idea exige um texto"
      IDEA="$2"
      shift 2
      ;;
    --loops)
      [[ $# -ge 2 ]] || fail "--loops exige um número"
      LOOPS="$2"
      shift 2
      ;;
    --output)
      [[ $# -ge 2 ]] || fail "--output exige um caminho"
      OUTPUT="$2"
      shift 2
      ;;
    --refine)
      REFINE=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "opção desconhecida: $1"
      ;;
  esac
done

[[ "$MODE" = plan || "$MODE" = apply ]] || fail "OMNICLI_BOOTSTRAP_MODE deve ser plan ou apply"
[[ "$LOOPS" =~ ^[1-9][0-9]*$ ]] || fail "--loops deve ser um inteiro positivo"
CONFIG_PATH="$(normalize_path "$CONFIG_PATH")"

if [[ "$MODE" = plan ]]; then
  plan
  exit 0
fi

require_python
mkdir -p "$VENV_DIR"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  log "criando ambiente virtual em $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  log "reutilizando ambiente virtual em $VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
log "atualizando o instalador do ambiente virtual"
PIP_DISABLE_PIP_VERSION_CHECK=1 "$VENV_PYTHON" -m pip install --upgrade pip
log "instalando OmniCLI e dependências de desenvolvimento"
(
  cd "$ROOT_DIR"
  PIP_DISABLE_PIP_VERSION_CHECK=1 "$VENV_PYTHON" -m pip install -e '.[dev]'
)

if [[ ! -f "$CONFIG_PATH" ]]; then
  log "criando configuração inicial em $CONFIG_PATH"
  "$VENV_PYTHON" -m omnicli init "$CONFIG_PATH"
else
  log "reutilizando configuração existente: $CONFIG_PATH"
fi

if [[ "$RUN_CHECKS" = true ]]; then
  log "executando validações locais"
  (
    cd "$ROOT_DIR"
    "$VENV_PYTHON" -m pytest --cov=omnicli --cov-report=term-missing
    "$VENV_PYTHON" -m omnicli lab verify --json
    "$VENV_PYTHON" -m omnicli conceive "offline bootstrap validation" --dry-run --json
    "$VENV_PYTHON" -m omnicli doctor --offline --config "$CONFIG_PATH" --json
    "$VENV_PYTHON" -m ruff check .
    "$VENV_PYTHON" -m mypy
    "$VENV_PYTHON" -m pip_audit
  )
fi

if [[ "$RUN_PROVIDERS" = true ]]; then
  log "validando configuração e provedores; nenhuma geração de conteúdo será iniciada"
  "$VENV_PYTHON" -m omnicli doctor --config "$CONFIG_PATH" --capabilities
fi

if [[ "$RUN_OFFICIAL_DOCS" = true ]]; then
  log "verificando fontes oficiais; nenhum provedor será executado"
  bash "$ROOT_DIR/scripts/check-official-docs.sh"
fi

if [[ -n "$IDEA" ]]; then
  log "executando pipeline de concepção explicitamente solicitado"
  CONCEIVE_ARGS=("$VENV_PYTHON" -m omnicli conceive "$IDEA" \
    --config "$CONFIG_PATH" \
    --loops "$LOOPS" \
    --output "$OUTPUT")
  [[ "$REFINE" = true ]] && CONCEIVE_ARGS+=(--refine)
  "${CONCEIVE_ARGS[@]}"
fi

log "bootstrap concluído"
