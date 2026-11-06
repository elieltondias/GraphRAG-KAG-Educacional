#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converte os CSVs do formato Neo4j import para um formato genérico.

Formato de saída:
  - nós:    id,label,<propriedades>
  - arestas: source,target,type

Uso:
    python3 lpg/scripts/converter_para_generico.py
    python3 lpg/scripts/converter_para_generico.py --origem lpg --destino lpg/generico
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from lpg_dominio import nome_base

REPO_ROOT = Path(__file__).resolve().parents[2]
ORIGEM_PADRAO = REPO_ROOT / "lpg"


@dataclass(frozen=True, slots=True)
class ConversorSpec:
    prefixo: tuple[str, ...]
    novo_header: Callable[[list[str]], list[str]]


def _header_no(header: list[str]) -> list[str]:
    return ["id", "label"] + [nome_base(h) for h in header[2:]]


def _header_aresta(header: list[str]) -> list[str]:
    return ["source", "target", "type"]


CONVERSOR_NO = ConversorSpec((":ID", ":LABEL"), _header_no)
CONVERSOR_ARESTA = ConversorSpec((":START_ID", ":END_ID", ":TYPE"), _header_aresta)
CONVERSOES = (
    ("nos", CONVERSOR_NO),
    ("arestas", CONVERSOR_ARESTA),
)


def converter_csv(
    origem: Path, destino: Path, spec: ConversorSpec
) -> int:
    with origem.open(encoding="utf-8", newline="") as arquivo:
        reader = csv.reader(arquivo, delimiter=",")
        header = next(reader)
        if header[: len(spec.prefixo)] != list(spec.prefixo):
            raise ValueError(f"{origem}: cabeçalho inesperado: {header[:3]}")

        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8", newline="") as saida:
            writer = csv.writer(saida, delimiter=",", lineterminator="\n")
            writer.writerow(spec.novo_header(header))
            count = 0
            for linha in reader:
                writer.writerow(linha)
                count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Converte o LPG de Neo4j import para CSV genérico."
    )
    parser.add_argument(
        "--origem",
        type=Path,
        default=ORIGEM_PADRAO,
        help=f"Pasta do grafo no formato Neo4j (padrão: {ORIGEM_PADRAO})",
    )
    parser.add_argument(
        "--destino",
        type=Path,
        default=ORIGEM_PADRAO / "generico",
        help="Pasta de saída no formato genérico (padrão: <origem>/generico)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    origem = args.origem.resolve()
    destino = args.destino.resolve()

    if not origem.exists():
        print(f"ERRO: pasta de origem não encontrada: {origem}")
        return 1
    if destino == origem:
        print("ERRO: a pasta de destino deve ser diferente da origem")
        return 1

    totais = defaultdict(int)
    arquivos = defaultdict(int)
    for pasta, spec in CONVERSOES:
        for caminho in sorted((origem / pasta).rglob("*.csv")):
            relativo = caminho.relative_to(origem)
            totais[pasta] += converter_csv(caminho, destino / relativo, spec)
            arquivos[pasta] += 1

    print("Conversão concluída")
    print(f"  Origem:  {origem}")
    print(f"  Destino: {destino}")
    print(f"  Arquivos de nós: {arquivos['nos']} ({totais['nos']:,} linhas)")
    print(
        f"  Arquivos de arestas: {arquivos['arestas']} "
        f"({totais['arestas']:,} linhas)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
