#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida o LPG do Censo da Educação Superior 2024 gerado por construir_lpg.py.

Verifica:
  - contagem de nós e arestas;
  - unicidade de IDs;
  - integridade referencial de todas as arestas;
  - cardinalidade das relações;
  - correspondência entre propriedades e arestas;
  - hierarquia CINE;
  - totais de controle das métricas;
  - distribuições das principais categorias.

Gera um relatório Markdown e retorna código 1 se alguma verificação falhar.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from lpg_dominio import (
    ARESTAS,
    CONTROLE_COLS,
    CONTROLE_ESPERADO,
    DISTRIBUICOES_ESPERADAS,
    IDENTIDADES_CONTROLE,
    NOS,
    id_cine_detalhada,
    id_cine_especifica,
    id_cine_geral,
    id_cine_rotulo,
    id_curso,
    id_dimensao,
    id_grau,
    id_ies,
    id_modalidade,
    id_municipio,
    id_nivel,
    id_regiao,
    id_uf,
    nome_base,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAFO_PADRAO = REPO_ROOT / "lpg"

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def indices(header: list[str]) -> dict[str, int]:
    return {nome_base(h): i for i, h in enumerate(header)}


def adicionar(
    checks: list[dict],
    nome: str,
    esperado,
    encontrado,
    ok: bool,
    detalhe: str = "",
) -> None:
    checks.append(
        {
            "nome": nome,
            "esperado": str(esperado),
            "encontrado": str(encontrado),
            "ok": bool(ok),
            "detalhe": detalhe,
        }
    )


def fmt_numero(valor) -> str:
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".")
    return str(valor)


# ---------------------------------------------------------------------------
# Estado da validação
# ---------------------------------------------------------------------------

class Dados:
    def __init__(self) -> None:
        self.ids_por_label: dict[str, set[str]] = defaultdict(set)
        self.global_ids: set[str] = set()
        self.node_counts: dict[str, int] = {}
        self.duplicados: list[str] = []
        self.labels_errados: list[str] = []

        self.offers_com_municipio: set[str] = set()
        self.offers_sem_municipio = 0
        self.offers_sem_municipio_com_capital = 0
        self.offers_com_municipio_sem_capital = 0
        self.ofertas_por_dimensao: Counter[str] = Counter()
        self.ofertas_por_modalidade: Counter[str] = Counter()
        self.metricas: Counter[str] = Counter()

        self.blank_grau_courses: set[str] = set()
        self.cursos_por_grau: Counter[str] = Counter()
        self.cursos_por_nivel: Counter[str] = Counter()
        self.course_expected_ies: dict[str, str] = {}
        self.course_expected_grau: dict[str, str] = {}
        self.course_expected_nivel: dict[str, str] = {}
        self.course_expected_cine: dict[str, str] = {}

        self.ies_por_rede: Counter[str] = Counter()
        self.ies_por_categoria: Counter[str] = Counter()
        self.ies_por_organizacao: Counter[str] = Counter()
        self.ies_expected_municipio: dict[str, str] = {}
        self.ies_expected_mantenedora: dict[str, str] = {}
        self.ies_expected_organizacao: dict[str, str] = {}
        self.ies_expected_categoria: dict[str, str] = {}
        self.ies_expected_rede: dict[str, str] = {}

        self.municipio_expected_uf: dict[str, str] = {}
        self.uf_expected_regiao: dict[str, str] = {}

        self.cine_rotulo_expected_parent: dict[str, str] = {}
        self.cine_detalhada_expected_parent: dict[str, str] = {}
        self.cine_especifica_expected_parent: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Processadores de nós (registry)
# ---------------------------------------------------------------------------

def _processador_nulo(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    return None


def _processar_oferta(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    co_municipio = linha[idx["CO_MUNICIPIO"]].strip()
    in_capital = linha[idx["IN_CAPITAL"]].strip()
    tp_dim = linha[idx["TP_DIMENSAO"]].strip()
    tp_mod = linha[idx["TP_MODALIDADE_ENSINO"]].strip()

    dados.ofertas_por_dimensao[tp_dim] += 1
    dados.ofertas_por_modalidade[tp_mod] += 1

    tem_municipio = bool(co_municipio)
    dados.offers_com_municipio.update((node_id,) if tem_municipio else ())
    dados.offers_sem_municipio += not tem_municipio
    dados.offers_com_municipio_sem_capital += tem_municipio and not in_capital
    dados.offers_sem_municipio_com_capital += not tem_municipio and bool(in_capital)

    for coluna in CONTROLE_COLS:
        dados.metricas[coluna] += int(linha[idx[coluna]] or 0)


def _processar_curso(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    co_ies = linha[idx["CO_IES"]].strip()
    co_curso = linha[idx["CO_CURSO"]].strip()
    grau = linha[idx["TP_GRAU_ACADEMICO"]].strip()
    nivel = linha[idx["TP_NIVEL_ACADEMICO"]].strip()
    cine = linha[idx["CO_CINE_ROTULO"]].strip()

    dados.course_expected_ies[node_id] = id_ies(co_ies)
    dados.course_expected_grau[node_id] = id_grau(grau)
    dados.course_expected_nivel[node_id] = id_nivel(nivel)
    dados.course_expected_cine[node_id] = id_cine_rotulo(cine)

    chave_grau = grau or "NA"
    dados.blank_grau_courses.update((node_id,) if not grau else ())
    dados.cursos_por_grau[chave_grau] += 1
    dados.cursos_por_nivel[nivel] += 1


def _processar_ies(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    dados.ies_expected_municipio[node_id] = id_municipio(
        linha[idx["CO_MUNICIPIO_IES"]]
    )
    dados.ies_expected_mantenedora[node_id] = (
        f"mantenedora_{linha[idx['CO_MANTENEDORA']].strip()}"
    )
    tp_org = linha[idx["TP_ORGANIZACAO_ACADEMICA"]].strip()
    tp_rede = linha[idx["TP_REDE"]].strip()
    tp_cat = linha[idx["TP_CATEGORIA_ADMINISTRATIVA"]].strip()
    dados.ies_expected_organizacao[node_id] = f"organizacao_{tp_org}"
    dados.ies_expected_rede[node_id] = f"rede_{tp_rede}"
    dados.ies_expected_categoria[node_id] = f"categoria_{tp_cat}"
    dados.ies_por_organizacao[tp_org] += 1
    dados.ies_por_rede[tp_rede] += 1
    dados.ies_por_categoria[tp_cat] += 1


def _processar_municipio(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    dados.municipio_expected_uf[node_id] = id_uf(linha[idx["CO_UF"]])


def _processar_uf(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    dados.uf_expected_regiao[node_id] = id_regiao(linha[idx["CO_REGIAO"]])


def _processar_cine_rotulo(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    dados.cine_rotulo_expected_parent[node_id] = id_cine_detalhada(
        linha[idx["CO_CINE_AREA_DETALHADA"]]
    )


def _processar_cine_detalhada(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    dados.cine_detalhada_expected_parent[node_id] = id_cine_especifica(
        linha[idx["CO_CINE_AREA_ESPECIFICA"]]
    )


def _processar_cine_especifica(
    node_id: str, linha: list[str], idx: dict[str, int], dados: Dados
) -> None:
    dados.cine_especifica_expected_parent[node_id] = id_cine_geral(
        linha[idx["CO_CINE_AREA_GERAL"]]
    )


PROCESSADORES = {
    "OfertaCurso": _processar_oferta,
    "Curso": _processar_curso,
    "IES": _processar_ies,
    "Municipio": _processar_municipio,
    "UF": _processar_uf,
    "CineRotulo": _processar_cine_rotulo,
    "CineAreaDetalhada": _processar_cine_detalhada,
    "CineAreaEspecifica": _processar_cine_especifica,
}


def carregar_nos(grafo: Path, dados: Dados, checks: list[dict]) -> None:
    print("Lendo nós...")
    for spec in NOS:
        caminho = grafo / spec.caminho
        if not caminho.exists():
            adicionar(
                checks,
                f"Arquivo de nó existe: {spec.caminho}",
                "sim",
                "não",
                False,
            )
            continue
        with caminho.open(encoding="utf-8", newline="") as arquivo:
            reader = csv.reader(arquivo, delimiter=",")
            try:
                header = next(reader)
            except StopIteration:
                adicionar(
                    checks,
                    f"Cabeçalho de {spec.caminho}",
                    "presente",
                    "vazio",
                    False,
                )
                continue
            if header[:2] != [":ID", ":LABEL"]:
                adicionar(
                    checks,
                    f"Cabeçalho de {spec.caminho}",
                    ":ID,:LABEL,...",
                    ",".join(header[:2]),
                    False,
                )
                continue

            idx = indices(header)
            label_esperado = spec.label
            count = 0
            label_erros = 0
            for linha in reader:
                count += 1
                node_id = linha[0]
                label = linha[1]
                if label != label_esperado:
                    label_erros += 1
                    if len(dados.labels_errados) < 20:
                        dados.labels_errados.append(
                            f"{spec.caminho}: {node_id} tem label {label!r}"
                        )
                if node_id in dados.global_ids:
                    if len(dados.duplicados) < 20:
                        dados.duplicados.append(f"{spec.caminho}: {node_id}")
                else:
                    dados.global_ids.add(node_id)
                dados.ids_por_label[label].add(node_id)

                PROCESSADORES.get(label, _processador_nulo)(
                    node_id, linha, idx, dados
                )

            dados.node_counts[spec.caminho] = count
            adicionar(
                checks,
                f"Linhas do nó {spec.caminho}",
                fmt_numero(spec.linhas_esperadas),
                fmt_numero(count),
                count == spec.linhas_esperadas,
            )
            adicionar(
                checks,
                f"Label do arquivo {spec.caminho}",
                label_esperado,
                f"{count - label_erros}/{count} corretos",
                label_erros == 0,
            )

    adicionar(
        checks,
        "IDs duplicados entre todos os nós",
        "0",
        len(dados.duplicados),
        not dados.duplicados,
        "; ".join(dados.duplicados[:5]),
    )
    adicionar(
        checks,
        "Labels divergentes",
        "0",
        len(dados.labels_errados),
        not dados.labels_errados,
        "; ".join(dados.labels_errados[:5]),
    )


# ---------------------------------------------------------------------------
# Estratégias de validação de arestas
# ---------------------------------------------------------------------------

class ValidadorDestino(Protocol):
    def ok(self, origem: str, destino: str) -> bool:
        ...


class SemValidadorDestino:
    def ok(self, origem: str, destino: str) -> bool:
        return True


@dataclass(frozen=True)
class MapaDestino:
    mapa: dict[str, str]

    def ok(self, origem: str, destino: str) -> bool:
        return self.mapa.get(origem) == destino


class ColetorAresta(Protocol):
    def coletar(self, origem: str, destino: str) -> None:
        ...


class ColetorNulo:
    def coletar(self, origem: str, destino: str) -> None:
        return None


@dataclass
class ColetorLocalizacao:
    destinos: set[str]

    def coletar(self, origem: str, destino: str) -> None:
        self.destinos.add(origem)


@dataclass
class ColetorGrauNa:
    destinos: set[str]

    def coletar(self, origem: str, destino: str) -> None:
        self.destinos.update((origem,) if destino == "grau_NA" else ())


SEM_VALIDADOR = SemValidadorDestino()
COLETOR_NULO = ColetorNulo()


def validar_arestas(
    grafo: Path, dados: Dados, checks: list[dict]
) -> tuple[set[str], set[str]]:
    print("Lendo arestas...")
    mapas = {
        "uf_regiao": dados.uf_expected_regiao,
        "municipio_uf": dados.municipio_expected_uf,
        "ies_municipio": dados.ies_expected_municipio,
        "ies_mantenedora": dados.ies_expected_mantenedora,
        "ies_organizacao": dados.ies_expected_organizacao,
        "ies_categoria": dados.ies_expected_categoria,
        "ies_rede": dados.ies_expected_rede,
        "curso_ies": dados.course_expected_ies,
        "curso_grau": dados.course_expected_grau,
        "curso_nivel": dados.course_expected_nivel,
        "curso_cine": dados.course_expected_cine,
        "cine_rotulo_detalhada": dados.cine_rotulo_expected_parent,
        "cine_detalhada_especifica": dados.cine_detalhada_expected_parent,
        "cine_especifica_geral": dados.cine_especifica_expected_parent,
    }
    validadores = {
        chave: MapaDestino(mapa) for chave, mapa in mapas.items()
    }

    location_starts: set[str] = set()
    grau_na_starts: set[str] = set()
    coletores = {
        "localizada": ColetorLocalizacao(location_starts),
        "grau_na": ColetorGrauNa(grau_na_starts),
    }

    for spec in ARESTAS:
        caminho = grafo / spec.caminho
        if not caminho.exists():
            adicionar(
                checks,
                f"Arquivo de aresta existe: {spec.caminho}",
                "sim",
                "não",
                False,
            )
            continue
        with caminho.open(encoding="utf-8", newline="") as arquivo:
            reader = csv.reader(arquivo, delimiter=",")
            try:
                header = next(reader)
            except StopIteration:
                adicionar(
                    checks,
                    f"Cabeçalho de {spec.caminho}",
                    "presente",
                    "vazio",
                    False,
                )
                continue
            if header != [":START_ID", ":END_ID", ":TYPE"]:
                adicionar(
                    checks,
                    f"Cabeçalho de {spec.caminho}",
                    ":START_ID,:END_ID,:TYPE",
                    ",".join(header),
                    False,
                )
                continue

            count = 0
            erros_tipo = 0
            erros_endpoint = 0
            erros_duplicado = 0
            erros_mapa = 0
            vistos: set[str] = set()
            ids_origem = dados.ids_por_label[spec.origem]
            ids_destino = dados.ids_por_label[spec.destino]
            validador = validadores.get(spec.mapa, SEM_VALIDADOR)
            coletor = coletores.get(spec.coletor, COLETOR_NULO)

            for linha in reader:
                if len(linha) != 3:
                    adicionar(
                        checks,
                        f"Formato de linha em {spec.caminho}",
                        "3 campos",
                        f"{len(linha)} campos",
                        False,
                    )
                    continue
                count += 1
                origem, destino, tipo = linha
                erros_tipo += tipo != spec.tipo
                erros_endpoint += (
                    origem not in ids_origem or destino not in ids_destino
                )
                erros_duplicado += origem in vistos
                vistos.add(origem)
                erros_mapa += not validador.ok(origem, destino)
                coletor.coletar(origem, destino)

            adicionar(
                checks,
                f"Linhas da aresta {spec.caminho}",
                fmt_numero(spec.linhas_esperadas),
                fmt_numero(count),
                count == spec.linhas_esperadas,
            )
            adicionar(
                checks,
                f"Tipo das arestas {spec.caminho}",
                spec.tipo,
                f"{count - erros_tipo}/{count} corretos",
                erros_tipo == 0,
            )
            adicionar(
                checks,
                f"Integridade referencial {spec.caminho}",
                "0 erros",
                f"{erros_endpoint} erros",
                erros_endpoint == 0,
            )
            adicionar(
                checks,
                f"Origem única {spec.caminho}",
                "0 duplicadas",
                f"{erros_duplicado} duplicadas",
                erros_duplicado == 0,
            )
            if spec.mapa is not None:
                adicionar(
                    checks,
                    f"Destino exato {spec.caminho}",
                    "0 divergências",
                    f"{erros_mapa} divergências",
                    erros_mapa == 0,
                )

    return location_starts, grau_na_starts


# ---------------------------------------------------------------------------
# Arestas 1:1 das ofertas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OfertaResumo:
    id: str
    co_ies: str
    co_curso: str
    tp_dim: str
    tp_mod: str


@dataclass(frozen=True)
class OfertaArestaSpec:
    arquivo: str
    tipo: str
    alvo: Callable[[OfertaResumo], str]


OFERTA_ARESTAS_VALIDACAO = (
    OfertaArestaSpec(
        "arestas/academico/oferta_curso_oferta_de.csv",
        "OFERTA_DE",
        lambda o: id_curso(o.co_ies, o.co_curso),
    ),
    OfertaArestaSpec(
        "arestas/academico/oferta_curso_ofertada_por_ies.csv",
        "OFERTADA_POR",
        lambda o: id_ies(o.co_ies),
    ),
    OfertaArestaSpec(
        "arestas/academico/oferta_curso_tem_modalidade_ensino.csv",
        "TEM_MODALIDADE_ENSINO",
        lambda o: id_modalidade(o.tp_mod),
    ),
    OfertaArestaSpec(
        "arestas/academico/oferta_curso_tem_dimensao_geografica.csv",
        "TEM_DIMENSAO_GEOGRAFICA",
        lambda o: id_dimensao(o.tp_dim),
    ),
)


def validar_arestas_oferta_exatas(grafo: Path, checks: list[dict]) -> None:
    """Compara, linha a linha, as quatro arestas 1:1 de cada oferta."""
    print("Conferindo arestas 1:1 das ofertas...")
    caminho_oferta = grafo / "nos/academico/oferta_curso.csv"
    if not caminho_oferta.exists():
        adicionar(checks, "Ofertas para conferência 1:1", "presente", "ausente", False)
        return

    with ExitStack() as stack:
        arquivo_oferta = stack.enter_context(
            caminho_oferta.open(encoding="utf-8", newline="")
        )
        reader_oferta = csv.reader(arquivo_oferta, delimiter=",")
        header_oferta = next(reader_oferta)
        idx = indices(header_oferta)

        leitores = []
        for spec in OFERTA_ARESTAS_VALIDACAO:
            caminho = grafo / spec.arquivo
            if not caminho.exists():
                adicionar(
                    checks,
                    f"Aresta 1:1 existe: {spec.arquivo}",
                    "sim",
                    "não",
                    False,
                )
                return
            arquivo = stack.enter_context(caminho.open(encoding="utf-8", newline=""))
            reader = csv.reader(arquivo, delimiter=",")
            header = next(reader)
            if header != [":START_ID", ":END_ID", ":TYPE"]:
                adicionar(
                    checks,
                    f"Cabeçalho de {spec.arquivo}",
                    "padrão",
                    "divergente",
                    False,
                )
                return
            leitores.append(reader)

        count = 0
        erros = 0
        exemplos: list[str] = []

        while True:
            linha_oferta = next(reader_oferta, None)
            linhas_arestas = [next(reader, None) for reader in leitores]
            if linha_oferta is None and all(l is None for l in linhas_arestas):
                break
            if linha_oferta is None or any(l is None for l in linhas_arestas):
                erros += 1
                if len(exemplos) < 5:
                    exemplos.append("quantidade de linhas divergente")
                break

            count += 1
            oferta = OfertaResumo(
                id=linha_oferta[0],
                co_ies=linha_oferta[idx["CO_IES"]].strip(),
                co_curso=linha_oferta[idx["CO_CURSO"]].strip(),
                tp_dim=linha_oferta[idx["TP_DIMENSAO"]].strip(),
                tp_mod=linha_oferta[idx["TP_MODALIDADE_ENSINO"]].strip(),
            )
            for spec, linha_aresta in zip(OFERTA_ARESTAS_VALIDACAO, linhas_arestas):
                origem, destino, tipo_lido = linha_aresta
                esperado = spec.alvo(oferta)
                correto = (
                    origem == oferta.id
                    and destino == esperado
                    and tipo_lido == spec.tipo
                )
                erros += not correto
                if not correto and len(exemplos) < 5:
                    exemplos.append(
                        f"{oferta.id}: {spec.arquivo} -> {destino} "
                        f"(esperado {esperado})"
                    )

    adicionar(
        checks,
        "Arestas 1:1 das ofertas (curso, IES, modalidade, dimensão)",
        "0 divergências",
        f"{erros} divergências em {fmt_numero(count)} ofertas",
        erros == 0,
        "; ".join(exemplos),
    )


# ---------------------------------------------------------------------------
# Totais e distribuições
# ---------------------------------------------------------------------------

def validar_totais(dados: Dados, checks: list[dict]) -> None:
    print("Conferindo totais e distribuições...")
    for coluna, esperado in CONTROLE_ESPERADO.items():
        encontrado = dados.metricas[coluna]
        adicionar(
            checks,
            f"Total de {coluna}",
            fmt_numero(esperado),
            fmt_numero(encontrado),
            encontrado == esperado,
        )

    for nome, partes, total in IDENTIDADES_CONTROLE:
        encontrado = sum(dados.metricas[parte] for parte in partes)
        adicionar(
            checks,
            nome,
            fmt_numero(dados.metricas[total]),
            fmt_numero(encontrado),
            encontrado == dados.metricas[total],
        )

    adicionar(
        checks,
        "Ofertas com município",
        "708.571",
        fmt_numero(len(dados.offers_com_municipio)),
        len(dados.offers_com_municipio) == 708_571,
    )
    adicionar(
        checks,
        "Ofertas sem município",
        "11.778",
        fmt_numero(dados.offers_sem_municipio),
        dados.offers_sem_municipio == 11_778,
    )
    adicionar(
        checks,
        "Ofertas sem município com IN_CAPITAL preenchido",
        "0",
        fmt_numero(dados.offers_sem_municipio_com_capital),
        dados.offers_sem_municipio_com_capital == 0,
    )
    adicionar(
        checks,
        "Ofertas com município e IN_CAPITAL vazio",
        "0",
        fmt_numero(dados.offers_com_municipio_sem_capital),
        dados.offers_com_municipio_sem_capital == 0,
    )
    adicionar(
        checks,
        "Cursos sem TP_GRAU_ACADEMICO",
        "378",
        fmt_numero(len(dados.blank_grau_courses)),
        len(dados.blank_grau_courses) == 378,
    )

    encontrados = {
        "ofertas_por_dimensao": dados.ofertas_por_dimensao,
        "ofertas_por_modalidade": dados.ofertas_por_modalidade,
        "cursos_por_grau": dados.cursos_por_grau,
        "cursos_por_nivel": dados.cursos_por_nivel,
        "ies_por_rede": dados.ies_por_rede,
        "ies_por_categoria": dados.ies_por_categoria,
        "ies_por_organizacao": dados.ies_por_organizacao,
    }
    for nome, esperado in DISTRIBUICOES_ESPERADAS.items():
        obtido = dict(sorted(encontrados[nome].items()))
        adicionar(
            checks,
            f"Distribuição {nome}",
            str(esperado),
            str(obtido),
            obtido == esperado,
        )


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------

def limpar_celula(texto: str, limite: int = 300) -> str:
    texto = str(texto).replace("|", "\\|").replace("\n", " ")
    if len(texto) > limite:
        texto = texto[: limite - 1] + "…"
    return texto


def escrever_relatorio(
    caminho: Path,
    checks: list[dict],
    dados: Dados,
    grafo: Path,
) -> int:
    total = len(checks)
    aprovadas = sum(1 for c in checks if c["ok"])
    falhas = total - aprovadas
    status = "APROVADO" if falhas == 0 else "REPROVADO"

    linhas = [
        "# Relatório de validação do LPG",
        "",
        "- **Dataset:** Censo da Educação Superior 2024",
        f"- **Grafo:** `{grafo}`",
        f"- **Gerado em:** {datetime.now(timezone.utc).isoformat()}",
        f"- **Status:** **{status}**",
        f"- **Verificações:** {total}",
        f"- **Aprovadas:** {aprovadas}",
        f"- **Falhas:** {falhas}",
        "",
        "## Contagens",
        "",
        "| Item | Quantidade |",
        "|---|---:|",
    ]
    for spec in NOS:
        linhas.append(
            f"| Nó `{spec.label}` (`{spec.caminho}`) | "
            f"{fmt_numero(dados.node_counts.get(spec.caminho, 0))} |"
        )
    for spec in ARESTAS:
        linhas.append(
            f"| Aresta `{spec.tipo}` (`{spec.caminho}`) | "
            f"{fmt_numero(spec.linhas_esperadas)} |"
        )
    linhas.extend(
        [
            "",
            "## Verificações",
            "",
            "| Verificação | Esperado | Encontrado | Status | Detalhe |",
            "|---|---|---|---|---|",
        ]
    )
    for check in checks:
        status_check = "OK" if check["ok"] else "FALHOU"
        linhas.append(
            "| {nome} | {esperado} | {encontrado} | {status} | {detalhe} |".format(
                nome=limpar_celula(check["nome"]),
                esperado=limpar_celula(check["esperado"]),
                encontrado=limpar_celula(check["encontrado"]),
                status=status_check,
                detalhe=limpar_celula(check["detalhe"]),
            )
        )

    if falhas:
        linhas.extend(["", "## Falhas", ""])
        for check in checks:
            if not check["ok"]:
                linhas.append(
                    f"- **{check['nome']}**: esperado `{check['esperado']}`, "
                    f"encontrado `{check['encontrado']}`"
                    + (f" — {check['detalhe']}" if check["detalhe"] else "")
                )
    else:
        linhas.extend(
            [
                "",
                "## Observações",
                "",
                "- Todas as verificações de contagem, integridade referencial, "
                "cardinalidade, hierarquia CINE e totais de controle passaram.",
                "- As arestas 1:1 das ofertas foram conferidas linha a linha.",
                "- A aresta `LOCALIZADA_EM` foi comparada com o conjunto de ofertas "
                "que possuem `CO_MUNICIPIO` preenchido.",
                "- As arestas de grau foram conferidas contra os cursos com "
                "`TP_GRAU_ACADEMICO` vazio (nó `GrauAcademico` “Não aplicável”).",
            ]
        )

    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return falhas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida o LPG do Censo 2024.")
    parser.add_argument(
        "--grafo",
        type=Path,
        default=GRAFO_PADRAO,
        help=f"Pasta do grafo (padrão: {GRAFO_PADRAO})",
    )
    parser.add_argument(
        "--relatorio",
        type=Path,
        help="Caminho do relatório Markdown "
        "(padrão: <grafo>/validacao/relatorio_validacao.md)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    grafo = args.grafo
    relatorio = args.relatorio or grafo / "validacao" / "relatorio_validacao.md"

    if not grafo.exists():
        print(f"ERRO: pasta do grafo não encontrada: {grafo}", file=sys.stderr)
        return 1

    checks: list[dict] = []
    dados = Dados()

    carregar_nos(grafo, dados, checks)
    location_starts, grau_na_starts = validar_arestas(grafo, dados, checks)

    adicionar(
        checks,
        "LOCALIZADA_EM cobre exatamente as ofertas com município",
        "conjuntos iguais",
        f"{fmt_numero(len(location_starts))} arestas; "
        f"{fmt_numero(len(dados.offers_com_municipio))} ofertas com município",
        location_starts == dados.offers_com_municipio,
    )
    adicionar(
        checks,
        "TEM_GRAU_ACADEMICO -> grau_NA cobre exatamente os cursos sem grau",
        "conjuntos iguais",
        f"{fmt_numero(len(grau_na_starts))} arestas; "
        f"{fmt_numero(len(dados.blank_grau_courses))} cursos sem grau",
        grau_na_starts == dados.blank_grau_courses,
    )

    validar_arestas_oferta_exatas(grafo, checks)
    validar_totais(dados, checks)

    falhas = escrever_relatorio(relatorio, checks, dados, grafo)
    total = len(checks)
    aprovadas = total - falhas

    print()
    print("=" * 72)
    print("Validação concluída")
    print("=" * 72)
    print(f"Verificações: {total}")
    print(f"Aprovadas:    {aprovadas}")
    print(f"Falhas:       {falhas}")
    print(f"Relatório:    {relatorio}")
    print("=" * 72)

    if falhas:
        print("\nFalhas:")
        for check in checks:
            if not check["ok"]:
                print(
                    f"  - {check['nome']}: esperado {check['esperado']}, "
                    f"encontrado {check['encontrado']}"
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
