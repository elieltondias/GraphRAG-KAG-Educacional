#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camada de I/O do LPG do Censo da Educação Superior 2024.

Concentra leitura de CSV/XLSX, escritores CSV no formato Neo4j,
geração de schema, hashes e manifesto.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from lpg_dominio import (
    ARESTAS,
    CATEGORIAS_ARQUIVO,
    NOS,
    com_tipo,
    destino_variavel,
    no_grafo_variavel,
    normalizar_texto,
)

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

# ---------------------------------------------------------------------------
# Escritores CSV
# ---------------------------------------------------------------------------

class NodeWriter:
    def __init__(self, caminho: Path, label: str, propriedades: list[str]):
        self.caminho = caminho
        self.label = label
        self.propriedades = propriedades
        self.count = 0
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self._arquivo = caminho.open("w", encoding="utf-8", newline="")
        self._writer = csv.writer(
            self._arquivo,
            delimiter=",",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        self._writer.writerow([":ID", ":LABEL"] + [com_tipo(p) for p in propriedades])

    def escrever(self, node_id: str, valores: list[str]) -> None:
        self._writer.writerow([node_id, self.label] + valores)
        self.count += 1

    def fechar(self) -> None:
        self._arquivo.close()


class EdgeWriter:
    def __init__(self, caminho: Path, tipo: str):
        self.caminho = caminho
        self.tipo = tipo
        self.count = 0
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self._arquivo = caminho.open("w", encoding="utf-8", newline="")
        self._writer = csv.writer(
            self._arquivo,
            delimiter=",",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        self._writer.writerow([":START_ID", ":END_ID", ":TYPE"])

    def escrever(self, origem: str, destino: str) -> None:
        self._writer.writerow([origem, destino, self.tipo])
        self.count += 1

    def fechar(self) -> None:
        self._arquivo.close()


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------

def ler_csv_completo(caminho: Path) -> tuple[list[str], list[dict[str, str]]]:
    with caminho.open(encoding="latin-1", newline="") as arquivo:
        reader = csv.reader(arquivo, delimiter=";")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"{caminho}: arquivo vazio") from exc
        registros = []
        for numero, linha in enumerate(reader, start=2):
            if len(linha) != len(header):
                raise ValueError(
                    f"{caminho}:{numero}: {len(linha)} campos; esperado {len(header)}"
                )
            registros.append(dict(zip(header, linha)))
        return header, registros


def _indice_coluna(ref: str) -> int:
    letras = re.match(r"[A-Z]+", ref)
    if not letras:
        return 1
    n = 0
    for caractere in letras.group(0):
        n = n * 26 + (ord(caractere) - 64)
    return n


def _valor_celula(celula, shared: list[str]) -> str:
    tipo = celula.get("t")
    valor = celula.find(f"{NS_MAIN}v")
    if valor is not None:
        texto = valor.text or ""
        return shared[int(texto)] if tipo == "s" else texto
    inline = celula.find(f"{NS_MAIN}is")
    return (
        "".join(t.text or "" for t in inline.iter(f"{NS_MAIN}t"))
        if inline is not None
        else ""
    )


def ler_xlsx(caminho: Path) -> dict[str, list[list[str]]]:
    """Lê as planilhas de um .xlsx usando apenas a biblioteca padrão."""
    with zipfile.ZipFile(caminho) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [
                "".join(t.text or "" for t in si.iter(f"{NS_MAIN}t"))
                for si in root
            ]

        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.get("Id"): r.get("Target") for r in rels}

        planilhas: dict[str, list[list[str]]] = {}
        elementos = workbook.find(f"{NS_MAIN}sheets")
        if elementos is None:
            return planilhas

        for sheet in elementos:
            nome = sheet.get("name")
            rid = sheet.get(f"{NS_REL}id")
            alvo = rel_map.get(rid)
            if not alvo:
                continue
            alvo = alvo.lstrip("/")
            if not alvo.startswith("xl/"):
                alvo = "xl/" + alvo

            root = ET.fromstring(z.read(alvo))
            linhas: list[list[str]] = []
            for row in root.iter(f"{NS_MAIN}row"):
                celulas: dict[int, str] = {}
                for cell in row.iter(f"{NS_MAIN}c"):
                    ref = cell.get("r")
                    if ref:
                        celulas[_indice_coluna(ref)] = _valor_celula(cell, shared)
                if celulas:
                    maximo = max(celulas)
                    linhas.append([celulas.get(i, "") for i in range(1, maximo + 1)])
            planilhas[nome] = linhas
        return planilhas


def _registro_dicionario(linha: list[str]) -> dict[str, str] | None:
    if len(linha) < 2:
        return None
    ordem = linha[0].strip()
    variavel = linha[1].strip()
    if not ordem.isdigit() or not variavel:
        return None

    def campo(i: int) -> str:
        return normalizar_texto(linha[i]) if i < len(linha) else ""

    return {
        "ORDEM": ordem,
        "VARIAVEL": variavel,
        "DESCRICAO": campo(2),
        "TIPO": campo(3),
        "TAMANHO": campo(4),
        "CATEGORIA": campo(5),
        "OBSERVACAO": campo(6),
    }


def extrair_dicionario(linhas: list[list[str]]) -> list[dict[str, str]]:
    return [
        registro
        for linha in linhas
        if (registro := _registro_dicionario(linha)) is not None
    ]


# ---------------------------------------------------------------------------
# Hashes e manifesto
# ---------------------------------------------------------------------------

def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def escrever_manifest(
    saida: Path,
    node_writers: dict,
    edge_writers: dict,
    resumo: dict,
    cursos_header: list[str],
    ies_header: list[str],
    qt_cols: list[str],
    avisos: list[str],
) -> None:
    nos = {}
    for spec in NOS:
        writer = node_writers[spec.chave]
        caminho = writer.caminho
        nos[spec.caminho] = {
            "label": writer.label,
            "linhas": writer.count,
            "bytes": caminho.stat().st_size,
            "sha256": sha256_arquivo(caminho),
        }

    arestas = {}
    for spec in ARESTAS:
        writer = edge_writers[spec.chave]
        caminho = writer.caminho
        arestas[spec.caminho] = {
            "tipo": writer.tipo,
            "linhas": writer.count,
            "bytes": caminho.stat().st_size,
            "sha256": sha256_arquivo(caminho),
        }

    manifesto = {
        "dataset": "Censo da Educação Superior 2024",
        "ano": 2024,
        "fonte": "INEP/MEC - Microdados do Censo da Educação Superior 2024",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "formato_csv": "neo4j-admin import",
        "encoding": "utf-8",
        "delimiter": ",",
        "quebra_linha": "LF",
        "colunas_origem": {
            "cursos": len(cursos_header),
            "ies": len(ies_header),
            "qt_cursos": len(qt_cols),
        },
        "resumo": resumo,
        "nos": nos,
        "arestas": arestas,
        "totais": {
            "nos": sum(w.count for w in node_writers.values()),
            "arestas": sum(w.count for w in edge_writers.values()),
            "arquivos_nos": len(nos),
            "arquivos_arestas": len(arestas),
        },
        "avisos": avisos,
    }
    (saida / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def escrever_falhas(saida: Path, falhas: list[str]) -> None:
    caminho = saida / "validacao" / "falhas_build.txt"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(falhas) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def escrever_schema(
    saida: Path,
    dicionario_path: Path,
    cursos_header: list[str],
    ies_header: list[str],
    falhas: list[str],
) -> None:
    schema = saida / "schema"
    schema.mkdir(parents=True, exist_ok=True)

    planilhas: dict[str, list[list[str]]] = {}
    try:
        planilhas = ler_xlsx(dicionario_path)
    except FileNotFoundError:
        falhas.append(f"Dicionário XLSX não encontrado: {dicionario_path}")
    except Exception as exc:  # noqa: BLE001 - queremos continuar o build
        falhas.append(f"Falha ao ler o dicionário XLSX: {exc}")

    registros = {
        "cadastro_ies": extrair_dicionario(planilhas.get("cadastro_ies", [])),
        "cadastro_cursos": extrair_dicionario(planilhas.get("cadastro_cursos", [])),
    }
    variaveis_por_arquivo = {
        "cadastro_ies": set(ies_header),
        "cadastro_cursos": set(cursos_header),
    }

    with (schema / "dicionario_variaveis.csv").open(
        "w", encoding="utf-8", newline=""
    ) as arquivo:
        writer = csv.writer(arquivo, delimiter=",", lineterminator="\n")
        writer.writerow(
            [
                "ARQUIVO",
                "ORDEM",
                "VARIAVEL",
                "DESCRICAO",
                "TIPO",
                "TAMANHO",
                "CATEGORIA",
                "OBSERVACAO",
                "DESTINO",
            ]
        )
        for arquivo_origem, registros_arquivo in registros.items():
            for registro in registros_arquivo:
                if registro["VARIAVEL"] not in variaveis_por_arquivo[arquivo_origem]:
                    continue
                writer.writerow(
                    [
                        arquivo_origem,
                        registro["ORDEM"],
                        registro["VARIAVEL"],
                        registro["DESCRICAO"],
                        registro["TIPO"],
                        registro["TAMANHO"],
                        registro["CATEGORIA"],
                        registro["OBSERVACAO"],
                        destino_variavel(arquivo_origem, registro["VARIAVEL"]),
                    ]
                )

    with (schema / "mapeamento_variaveis.csv").open(
        "w", encoding="utf-8", newline=""
    ) as arquivo:
        writer = csv.writer(arquivo, delimiter=",", lineterminator="\n")
        writer.writerow(["ARQUIVO", "VARIAVEL", "NO_GRAFO", "NO_DICIONARIO"])
        for arquivo_origem, header in (
            ("cadastro_ies", ies_header),
            ("cadastro_cursos", cursos_header),
        ):
            for variavel in header:
                writer.writerow(
                    [
                        arquivo_origem,
                        variavel,
                        no_grafo_variavel(arquivo_origem, variavel),
                        "sim",
                    ]
                )

    with (schema / "categorias.csv").open(
        "w", encoding="utf-8", newline=""
    ) as arquivo:
        writer = csv.writer(arquivo, delimiter=",", lineterminator="\n")
        writer.writerow(["ARQUIVO", "VARIAVEL", "CODIGO", "ROTULO", "OBSERVACAO"])
        for arquivo_origem, variavel, mapa in CATEGORIAS_ARQUIVO:
            for codigo, rotulo in mapa.items():
                observacao = (
                    "Não presente no Censo 2024"
                    if variavel == "TP_CATEGORIA_ADMINISTRATIVA"
                    and str(codigo) in {"6", "8", "9"}
                    else ""
                )
                writer.writerow(
                    [arquivo_origem, variavel, str(codigo), rotulo, observacao]
                )
