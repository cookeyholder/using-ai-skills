#!/bin/bash

INPUT=$(cat)
COMMAND=$(printf '%s\n' "$INPUT" | jq -r '.tool_input.command')

DANGEROUS_PATTERNS=(
  "(^|[[:space:]])(git[[:space:]]+)?push([[:space:]]|$)"
  "(^|[[:space:]])(git[[:space:]]+)?reset[[:space:]]+--hard([[:space:]]|$)"
  "(^|[[:space:]])(git[[:space:]]+)?clean[[:space:]]+-f[df]?([[:space:]]|$)"
  "(^|[[:space:]])(git[[:space:]]+)?branch[[:space:]]+-D([[:space:]]|$)"
  "(^|[[:space:]])(git[[:space:]]+)?checkout[[:space:]]+\.([[:space:]]|$)"
  "(^|[[:space:]])(git[[:space:]]+)?restore[[:space:]]+\.([[:space:]]|$)"
  "push[[:space:]]+--force"
  "reset[[:space:]]+--hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if printf '%s\n' "$COMMAND" | grep -qiE "$pattern"; then
    printf 'BLOCKED: command matches dangerous pattern (case-insensitive). The user has prevented you from doing this.\n' >&2
    exit 2
  fi
done

exit 0
