#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_FILE="$ROOT_DIR/docs/provider-sources.txt"

command -v curl >/dev/null 2>&1 || {
  printf '[official-docs] erro: curl não encontrado\n' >&2
  exit 1
}

[[ -f "$SOURCE_FILE" ]] || {
  printf '[official-docs] erro: lista de fontes não encontrada: %s\n' "$SOURCE_FILE" >&2
  exit 1
}

failed=0
while IFS= read -r url || [[ -n "$url" ]]; do
  [[ -z "$url" || "$url" == \#* ]] && continue
  if curl --fail --silent --show-error --location --max-time 20 "$url" -o /dev/null; then
    printf '[official-docs] ok: %s\n' "$url"
  else
    printf '[official-docs] falha: %s\n' "$url" >&2
    failed=1
  fi
done < "$SOURCE_FILE"

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi
