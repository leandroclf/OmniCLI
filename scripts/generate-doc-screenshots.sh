#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${OMNICLI_SCREENSHOT_PYTHON:-$ROOT_DIR/.venv/bin/python}"
OUTPUT_DIR="$ROOT_DIR/docs/assets/screenshots"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${OMNICLI_PYTHON:-python3}"
fi
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  printf '[screenshots] erro: Python não encontrado: %s\n' "$PYTHON_BIN" >&2
  exit 1
}

command -v convert >/dev/null 2>&1 || {
  printf '[screenshots] erro: ImageMagick (convert) não encontrado\n' >&2
  exit 1
}
command -v iconv >/dev/null 2>&1 || {
  printf '[screenshots] erro: iconv não encontrado\n' >&2
  exit 1
}

if [[ -x "$ROOT_DIR/.venv/bin/omnicli" ]]; then
  run_cli() { "$ROOT_DIR/.venv/bin/omnicli" "$@"; }
else
  run_cli() { "$PYTHON_BIN" -m omnicli "$@"; }
fi

mkdir -p "$OUTPUT_DIR"

capture() {
  local name="$1"
  local prompt="$2"
  shift 2
  {
    printf '$ %s\n\n' "$prompt"
    "$@"
  } > "$TEMP_DIR/$name.txt" 2>&1 || true
}

render_terminal() {
  local source="$1"
  local destination="$2"
  local title="$3"
  local body="$TEMP_DIR/body.png"
  local content
  content="$(sed -E 's/[[:space:]]+$//' "$source" \
    | sed -e 's/[╭╮╰╯├┤┬┴┼]/+/g' -e 's/─/-/g' -e 's/│/|/g' \
    | iconv -c -f UTF-8 -t ASCII//TRANSLIT)"

  convert \
    -background '#0d1117' \
    -fill '#e6edf3' \
    -font 'DejaVu-Sans-Mono' \
    -pointsize 22 \
    -size 1720x \
    "label:$content" \
    "$body"
  convert \
    "$body" \
    -background '#161b22' \
    -gravity north \
    -splice 0x78 \
    -fill '#ff7b72' -draw 'circle 28,39 28,31' \
    -fill '#d29922' -draw 'circle 54,39 54,31' \
    -fill '#3fb950' -draw 'circle 80,39 80,31' \
    -fill '#8b949e' \
    -font 'DejaVu-Sans' \
    -pointsize 20 \
    -annotate +0+47 "$title" \
    -bordercolor '#30363d' \
    -border 28 \
    "$destination"
}

capture help "omnicli --help" run_cli --help
capture conceive-help "omnicli conceive --help" run_cli conceive --help
capture doctor "omnicli doctor --skip-version --json" run_cli doctor --skip-version --json
capture bootstrap-help "bash scripts/bootstrap.sh --help" bash "$ROOT_DIR/scripts/bootstrap.sh" --help

render_terminal "$TEMP_DIR/help.txt" "$OUTPUT_DIR/omnicli-help.png" "OmniCLI · comandos disponíveis"
render_terminal "$TEMP_DIR/conceive-help.txt" "$OUTPUT_DIR/omnicli-conceive.png" "OmniCLI · conceive"
render_terminal "$TEMP_DIR/doctor.txt" "$OUTPUT_DIR/omnicli-doctor.png" "OmniCLI · diagnóstico"
render_terminal "$TEMP_DIR/bootstrap-help.txt" "$OUTPUT_DIR/omnicli-bootstrap.png" "OmniCLI · bootstrap"

printf '[screenshots] imagens geradas em %s\n' "$OUTPUT_DIR"
