#!/usr/bin/env bash
# Importa o LPG do Censo 2024 em um banco Neo4j vazio.
#
# Uso:
#   ./lpg/scripts/importar_neo4j.sh [nome_do_banco]
#
# Requisitos:
#   - Neo4j 5.x com neo4j-admin no PATH;
#   - banco de destino parado e ainda não existente;
#   - execute como o usuário do Neo4j (ou com permissões adequadas).
#
# Para Neo4j 4.x, troque:
#   neo4j-admin database import full ...
# por:
#   neo4j-admin import ...

set -euo pipefail

GRAFO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANCO="${1:-neo4j}"

if ! command -v neo4j-admin >/dev/null 2>&1; then
  echo "ERRO: neo4j-admin não encontrado no PATH." >&2
  exit 1
fi

ARGS=()
while IFS= read -r -d '' arquivo; do
  ARGS+=(--nodes="$arquivo")
done < <(find "$GRAFO_DIR/nos" -type f -name '*.csv' -print0 | sort -z)

while IFS= read -r -d '' arquivo; do
  ARGS+=(--relationships="$arquivo")
done < <(find "$GRAFO_DIR/arestas" -type f -name '*.csv' -print0 | sort -z)

echo "Importando ${#ARGS[@]} arquivos no banco '$BANCO'..."
neo4j-admin database import full \
  --verbose \
  --id-type=STRING \
  --ignore-empty-strings=true \
  "${ARGS[@]}" \
  "$BANCO"
