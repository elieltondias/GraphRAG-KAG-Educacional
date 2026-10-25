#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domínio declarativo do LPG do Censo da Educação Superior 2024.

Este módulo concentra a fonte única de verdade para:
  - labels, caminhos e propriedades dos nós;
  - tipos e cardinalidades das arestas;
  - mapeamentos código -> rótulo;
  - regras de tipagem e de destino das variáveis;
  - contagens esperadas e distribuições de controle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Caminhos e constantes
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_PADRAO = REPO_ROOT / "microdados_censo_da_educacao_superior_2024"
SAIDA_PADRAO = REPO_ROOT / "lpg"

ARQ_CURSOS = "dados/MICRODADOS_CADASTRO_CURSOS_2024.CSV"
ARQ_IES = "dados/MICRODADOS_ED_SUP_IES_2024.CSV"
ARQ_DICIONARIO = (
    "Anexos/ANEXO I - Dicionário de Dados/"
    "dicionário_dados_educação_superior.xlsx"
)

ESPERADO_CURSOS_LINHAS = 720_349
ESPERADO_IES_LINHAS = 2_561
ESPERADO_CURSOS_COLUNAS = 223
ESPERADO_IES_COLUNAS = 84
ESPERADO_QT_COLUNAS = 193

# ---------------------------------------------------------------------------
# Domínios
# ---------------------------------------------------------------------------

MAP_ORGANIZACAO = {
    1: "Universidade",
    2: "Centro Universitário",
    3: "Faculdade",
    4: "Instituto Federal de Educação, Ciência e Tecnologia",
    5: "Centro Federal de Educação Tecnológica",
}

MAP_REDE = {
    1: "Pública",
    2: "Privada",
}

MAP_CATEGORIA_ADMINISTRATIVA = {
    1: "Pública Federal",
    2: "Pública Estadual",
    3: "Pública Municipal",
    4: "Privada com fins lucrativos",
    5: "Privada sem fins lucrativos",
    6: "Privada - Particular em sentido estrito",
    7: "Especial",
    8: "Privada comunitária",
    9: "Privada confessional",
}

MAP_GRAU = {
    1: "Bacharelado",
    2: "Licenciatura",
    3: "Tecnológico",
    4: "Bacharelado e Licenciatura",
    "NA": "Não aplicável",
}

MAP_MODALIDADE = {
    1: "Presencial",
    2: "Curso a distância",
}

MAP_NIVEL = {
    1: "Graduação",
    2: "Sequencial de Formação Específica",
}

MAP_DIMENSAO = {
    1: "Cursos presenciais ofertados no Brasil",
    2: "Cursos a distância ofertados no Brasil",
    3: "Cursos a distância com dimensão de dados somente a nível Brasil",
    4: "Cursos a distância ofertados por instituições brasileiras no exterior",
}

MAP_ABRANGENCIA = {
    1: "Municipal (presencial)",
    2: "Municipal (EAD)",
    3: "Nacional (EAD)",
    4: "Exterior (EAD)",
}

GEOGRAFIA_CURSO = frozenset(
    {
        "NO_REGIAO",
        "CO_REGIAO",
        "NO_UF",
        "SG_UF",
        "CO_UF",
        "NO_MUNICIPIO",
        "CO_MUNICIPIO",
        "IN_CAPITAL",
    }
)

GEOGRAFIA_IES = frozenset(
    {
        "NO_REGIAO_IES",
        "CO_REGIAO_IES",
        "NO_UF_IES",
        "SG_UF_IES",
        "CO_UF_IES",
        "NO_MUNICIPIO_IES",
        "CO_MUNICIPIO_IES",
        "IN_CAPITAL_IES",
        "NO_MESORREGIAO_IES",
        "CO_MESORREGIAO_IES",
        "NO_MICRORREGIAO_IES",
        "CO_MICRORREGIAO_IES",
    }
)

CODIGOS_DIMENSAO = frozenset(str(k) for k in MAP_DIMENSAO)
CODIGOS_MODALIDADE = frozenset(str(k) for k in MAP_MODALIDADE)
CODIGOS_GRAU = frozenset(str(k) for k in MAP_GRAU)
CODIGOS_NIVEL = frozenset(str(k) for k in MAP_NIVEL)
CODIGOS_ORGANIZACAO = frozenset(str(k) for k in MAP_ORGANIZACAO)
CODIGOS_REDE = frozenset(str(k) for k in MAP_REDE)
CODIGOS_CATEGORIA = frozenset(str(k) for k in MAP_CATEGORIA_ADMINISTRATIVA)

CAMPOS_IES_OFERTA = (
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_REDE",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "IN_COMUNITARIA",
    "IN_CONFESSIONAL",
)

CURSO_PROPS = (
    "NU_ANO_CENSO",
    "CO_IES",
    "CO_CURSO",
    "NO_CURSO",
    "CO_CINE_ROTULO",
    "NO_CINE_ROTULO",
    "CO_CINE_AREA_DETALHADA",
    "NO_CINE_AREA_DETALHADA",
    "CO_CINE_AREA_ESPECIFICA",
    "NO_CINE_AREA_ESPECIFICA",
    "CO_CINE_AREA_GERAL",
    "NO_CINE_AREA_GERAL",
    "TP_GRAU_ACADEMICO",
    "TP_NIVEL_ACADEMICO",
    "IN_GRATUITO",
)

OFERTA_CORE_PROPS = (
    "NU_ANO_CENSO",
    "CO_IES",
    "CO_CURSO",
    "CO_MUNICIPIO",
    "IN_CAPITAL",
    "TP_DIMENSAO",
    "TP_MODALIDADE_ENSINO",
)

CONTROLE_COLS = (
    "QT_ING",
    "QT_ING_FEM",
    "QT_ING_MASC",
    "QT_MAT",
    "QT_MAT_FEM",
    "QT_MAT_MASC",
    "QT_CONC",
    "QT_CONC_FEM",
    "QT_CONC_MASC",
    "QT_VG_TOTAL",
)

CONTROLE_ESPERADO = {
    "QT_ING": 5_010_613,
    "QT_ING_FEM": 2_994_997,
    "QT_ING_MASC": 2_015_616,
    "QT_MAT": 10_227_266,
    "QT_MAT_FEM": 6_088_602,
    "QT_MAT_MASC": 4_138_664,
    "QT_CONC": 1_333_988,
    "QT_CONC_FEM": 793_161,
    "QT_CONC_MASC": 540_827,
    "QT_VG_TOTAL": 23_665_419,
}

IDENTIDADES_CONTROLE = (
    ("QT_ING_FEM + QT_ING_MASC = QT_ING", ("QT_ING_FEM", "QT_ING_MASC"), "QT_ING"),
    ("QT_MAT_FEM + QT_MAT_MASC = QT_MAT", ("QT_MAT_FEM", "QT_MAT_MASC"), "QT_MAT"),
    ("QT_CONC_FEM + QT_CONC_MASC = QT_CONC", ("QT_CONC_FEM", "QT_CONC_MASC"), "QT_CONC"),
)

DISTRIBUICOES_ESPERADAS = {
    "ofertas_por_dimensao": {"1": 34_824, "2": 673_756, "3": 11_319, "4": 450},
    "ofertas_por_modalidade": {"1": 34_824, "2": 685_525},
    "cursos_por_grau": {"1": 27_453, "2": 7_789, "3": 10_530, "NA": 378},
    "cursos_por_nivel": {"1": 46_146, "2": 4},
    "ies_por_rede": {"1": 317, "2": 2_244},
    "ies_por_categoria": {
        "1": 122,
        "2": 139,
        "3": 28,
        "4": 1_486,
        "5": 758,
        "7": 28,
    },
    "ies_por_organizacao": {"1": 206, "2": 417, "3": 1_897, "4": 39, "5": 2},
}

# ---------------------------------------------------------------------------
# Especificações de nós e arestas
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NoSpec:
    chave: str
    label: str
    caminho: str
    linhas_esperadas: int
    propriedades: tuple[str, ...] = ()
    fonte_props: str | None = None


@dataclass(frozen=True, slots=True)
class ArestaSpec:
    chave: str
    tipo: str
    caminho: str
    origem: str
    destino: str
    linhas_esperadas: int
    mapa: str | None = None
    coletor: str | None = None


@dataclass(frozen=True, slots=True)
class ClassificacaoIesSpec:
    campo: str
    prefixo: str
    writer: str
    conjunto: str
    contador: str
    codigos_validos: frozenset[str]


@dataclass(frozen=True, slots=True)
class ReferenciaSpec:
    colecao: str
    campo: str
    destino: str
    descricao: str


NOS = (
    NoSpec("regiao", "Regiao", "nos/geografia/regiao.csv", 5, ("CO_REGIAO", "NO_REGIAO")),
    NoSpec("uf", "UF", "nos/geografia/uf.csv", 27, ("CO_UF", "SG_UF", "NO_UF", "CO_REGIAO")),
    NoSpec(
        "municipio",
        "Municipio",
        "nos/geografia/municipio.csv",
        3_551,
        ("CO_MUNICIPIO", "NO_MUNICIPIO", "CO_UF", "SG_UF", "IN_CAPITAL"),
    ),
    NoSpec("ies", "IES", "nos/institucional/ies.csv", 2_561, fonte_props="ies"),
    NoSpec(
        "mantenedora",
        "Mantenedora",
        "nos/institucional/mantenedora.csv",
        1_755,
        ("CO_MANTENEDORA", "NO_MANTENEDORA"),
    ),
    NoSpec("curso", "Curso", "nos/academico/curso.csv", 46_150, CURSO_PROPS),
    NoSpec("oferta", "OfertaCurso", "nos/academico/oferta_curso.csv", 720_349, fonte_props="oferta"),
    NoSpec(
        "cine_area_geral",
        "CineAreaGeral",
        "nos/classificacoes/cine_area_geral.csv",
        11,
        ("CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL"),
    ),
    NoSpec(
        "cine_area_especifica",
        "CineAreaEspecifica",
        "nos/classificacoes/cine_area_especifica.csv",
        39,
        ("CO_CINE_AREA_ESPECIFICA", "NO_CINE_AREA_ESPECIFICA", "CO_CINE_AREA_GERAL"),
    ),
    NoSpec(
        "cine_area_detalhada",
        "CineAreaDetalhada",
        "nos/classificacoes/cine_area_detalhada.csv",
        89,
        ("CO_CINE_AREA_DETALHADA", "NO_CINE_AREA_DETALHADA", "CO_CINE_AREA_ESPECIFICA"),
    ),
    NoSpec(
        "cine_rotulo",
        "CineRotulo",
        "nos/classificacoes/cine_rotulo.csv",
        353,
        ("CO_CINE_ROTULO", "NO_CINE_ROTULO", "CO_CINE_AREA_DETALHADA"),
    ),
    NoSpec(
        "grau",
        "GrauAcademico",
        "nos/classificacoes/grau_academico.csv",
        4,
        ("CO_GRAU", "NO_GRAU"),
    ),
    NoSpec(
        "modalidade",
        "ModalidadeEnsino",
        "nos/classificacoes/modalidade_ensino.csv",
        2,
        ("CO_MODALIDADE_ENSINO", "NO_MODALIDADE_ENSINO"),
    ),
    NoSpec(
        "nivel",
        "NivelAcademico",
        "nos/classificacoes/nivel_academico.csv",
        2,
        ("CO_NIVEL_ACADEMICO", "NO_NIVEL_ACADEMICO"),
    ),
    NoSpec(
        "organizacao",
        "OrganizacaoAcademica",
        "nos/classificacoes/organizacao_academica.csv",
        5,
        ("CO_ORGANIZACAO_ACADEMICA", "NO_ORGANIZACAO_ACADEMICA"),
    ),
    NoSpec("rede", "Rede", "nos/classificacoes/rede.csv", 2, ("CO_REDE", "NO_REDE")),
    NoSpec(
        "categoria",
        "CategoriaAdministrativa",
        "nos/classificacoes/categoria_administrativa.csv",
        6,
        ("CO_CATEGORIA_ADMINISTRATIVA", "NO_CATEGORIA_ADMINISTRATIVA"),
    ),
    NoSpec(
        "dimensao",
        "DimensaoGeografica",
        "nos/classificacoes/dimensao_geografica.csv",
        4,
        ("CO_DIMENSAO", "NO_DIMENSAO", "ABRANGENCIA"),
    ),
)

ARESTAS = (
    ArestaSpec(
        "uf_regiao",
        "PERTENCE_A_REGIAO",
        "arestas/geografia/uf_pertence_regiao.csv",
        "UF",
        "Regiao",
        27,
        mapa="uf_regiao",
    ),
    ArestaSpec(
        "municipio_uf",
        "PERTENCE_A_UF",
        "arestas/geografia/municipio_pertence_uf.csv",
        "Municipio",
        "UF",
        3_551,
        mapa="municipio_uf",
    ),
    ArestaSpec(
        "ies_municipio",
        "SEDIADA_EM",
        "arestas/institucional/ies_sediada_em_municipio.csv",
        "IES",
        "Municipio",
        2_561,
        mapa="ies_municipio",
    ),
    ArestaSpec(
        "ies_mantenedora",
        "MANTIDA_POR",
        "arestas/institucional/ies_mantida_por_mantenedora.csv",
        "IES",
        "Mantenedora",
        2_561,
        mapa="ies_mantenedora",
    ),
    ArestaSpec(
        "ies_organizacao",
        "TEM_ORGANIZACAO_ACADEMICA",
        "arestas/institucional/ies_tem_organizacao_academica.csv",
        "IES",
        "OrganizacaoAcademica",
        2_561,
        mapa="ies_organizacao",
    ),
    ArestaSpec(
        "ies_categoria",
        "TEM_CATEGORIA_ADMINISTRATIVA",
        "arestas/institucional/ies_tem_categoria_administrativa.csv",
        "IES",
        "CategoriaAdministrativa",
        2_561,
        mapa="ies_categoria",
    ),
    ArestaSpec(
        "ies_rede",
        "PERTENCE_A_REDE",
        "arestas/institucional/ies_pertence_rede.csv",
        "IES",
        "Rede",
        2_561,
        mapa="ies_rede",
    ),
    ArestaSpec(
        "curso_ies",
        "OFERTADO_POR",
        "arestas/academico/curso_ofertado_por_ies.csv",
        "Curso",
        "IES",
        46_150,
        mapa="curso_ies",
    ),
    ArestaSpec(
        "curso_grau",
        "TEM_GRAU_ACADEMICO",
        "arestas/academico/curso_tem_grau_academico.csv",
        "Curso",
        "GrauAcademico",
        46_150,
        mapa="curso_grau",
        coletor="grau_na",
    ),
    ArestaSpec(
        "curso_nivel",
        "TEM_NIVEL_ACADEMICO",
        "arestas/academico/curso_tem_nivel_academico.csv",
        "Curso",
        "NivelAcademico",
        46_150,
        mapa="curso_nivel",
    ),
    ArestaSpec(
        "curso_cine",
        "CLASSIFICADO_EM",
        "arestas/academico/curso_classificado_em_cine_rotulo.csv",
        "Curso",
        "CineRotulo",
        46_150,
        mapa="curso_cine",
    ),
    ArestaSpec(
        "oferta_curso",
        "OFERTA_DE",
        "arestas/academico/oferta_curso_oferta_de.csv",
        "OfertaCurso",
        "Curso",
        720_349,
    ),
    ArestaSpec(
        "oferta_ies",
        "OFERTADA_POR",
        "arestas/academico/oferta_curso_ofertada_por_ies.csv",
        "OfertaCurso",
        "IES",
        720_349,
    ),
    ArestaSpec(
        "oferta_municipio",
        "LOCALIZADA_EM",
        "arestas/academico/oferta_curso_localizada_em_municipio.csv",
        "OfertaCurso",
        "Municipio",
        708_571,
        coletor="localizada",
    ),
    ArestaSpec(
        "oferta_modalidade",
        "TEM_MODALIDADE_ENSINO",
        "arestas/academico/oferta_curso_tem_modalidade_ensino.csv",
        "OfertaCurso",
        "ModalidadeEnsino",
        720_349,
    ),
    ArestaSpec(
        "oferta_dimensao",
        "TEM_DIMENSAO_GEOGRAFICA",
        "arestas/academico/oferta_curso_tem_dimensao_geografica.csv",
        "OfertaCurso",
        "DimensaoGeografica",
        720_349,
    ),
    ArestaSpec(
        "cine_rotulo_detalhada",
        "PERTENCE_A_AREA_DETALHADA",
        "arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv",
        "CineRotulo",
        "CineAreaDetalhada",
        353,
        mapa="cine_rotulo_detalhada",
    ),
    ArestaSpec(
        "cine_detalhada_especifica",
        "PERTENCE_A_AREA_ESPECIFICA",
        "arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv",
        "CineAreaDetalhada",
        "CineAreaEspecifica",
        89,
        mapa="cine_detalhada_especifica",
    ),
    ArestaSpec(
        "cine_especifica_geral",
        "PERTENCE_A_AREA_GERAL",
        "arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv",
        "CineAreaEspecifica",
        "CineAreaGeral",
        39,
        mapa="cine_especifica_geral",
    ),
)

NOS_POR_CHAVE = {spec.chave: spec for spec in NOS}
ARESTAS_POR_CHAVE = {spec.chave: spec for spec in ARESTAS}

CLASSIFICACOES_IES = (
    ClassificacaoIesSpec(
        "TP_ORGANIZACAO_ACADEMICA",
        "organizacao",
        "ies_organizacao",
        "organizacoes",
        "ies_por_organizacao",
        frozenset(str(k) for k in MAP_ORGANIZACAO),
    ),
    ClassificacaoIesSpec(
        "TP_REDE",
        "rede",
        "ies_rede",
        "redes",
        "ies_por_rede",
        frozenset(str(k) for k in MAP_REDE),
    ),
    ClassificacaoIesSpec(
        "TP_CATEGORIA_ADMINISTRATIVA",
        "categoria",
        "ies_categoria",
        "categorias",
        "ies_por_categoria",
        frozenset(str(k) for k in MAP_CATEGORIA_ADMINISTRATIVA),
    ),
)

REFERENCIAS = (
    ReferenciaSpec("ufs", "CO_REGIAO", "regioes", "UF sem região"),
    ReferenciaSpec("municipios", "CO_UF", "ufs", "Município sem UF"),
    ReferenciaSpec("cursos", "CO_IES", "ies", "Curso sem IES"),
    ReferenciaSpec("cursos", "CO_CINE_ROTULO", "cine_rotulo", "Curso sem rótulo CINE"),
)

CATEGORIAS_ARQUIVO = (
    ("cadastro_cursos", "TP_DIMENSAO", MAP_DIMENSAO),
    ("cadastro_cursos", "TP_GRAU_ACADEMICO", MAP_GRAU),
    ("cadastro_cursos", "TP_MODALIDADE_ENSINO", MAP_MODALIDADE),
    ("cadastro_cursos", "TP_NIVEL_ACADEMICO", MAP_NIVEL),
    ("cadastro_cursos", "IN_CAPITAL", {0: "Não", 1: "Sim", "": "Não aplicável (curso a distância)"}),
    ("cadastro_cursos", "IN_GRATUITO", {0: "Não", 1: "Sim"}),
    ("ambos", "IN_COMUNITARIA", {0: "Não", 1: "Sim"}),
    ("ambos", "IN_CONFESSIONAL", {0: "Não", 1: "Sim"}),
    ("ambos", "TP_ORGANIZACAO_ACADEMICA", MAP_ORGANIZACAO),
    ("ambos", "TP_REDE", MAP_REDE),
    ("ambos", "TP_CATEGORIA_ADMINISTRATIVA", MAP_CATEGORIA_ADMINISTRATIVA),
)

# ---------------------------------------------------------------------------
# Regras de tipagem e formatação
# ---------------------------------------------------------------------------

def fmt_bool(valor) -> str:
    valor = str(valor).strip().lower()
    if valor in {"1", "true", "sim"}:
        return "true"
    if valor in {"0", "false", "não", "nao"}:
        return "false"
    return ""


def fmt_int(valor) -> str:
    return str(valor).strip()


@dataclass(frozen=True, slots=True)
class RegraTipo:
    prefixos: tuple[str, ...] = ()
    exatos: frozenset[str] = frozenset()
    sufixo: str = ""
    formatador: Callable[[str], str] = str

    def aplica(self, coluna: str) -> bool:
        return coluna in self.exatos or coluna.startswith(self.prefixos)


REGRAS_TIPO = (
    RegraTipo(exatos=frozenset({"NU_ANO_CENSO"}), sufixo="int", formatador=fmt_int),
    RegraTipo(prefixos=("TP_",), sufixo="int", formatador=fmt_int),
    RegraTipo(prefixos=("IN_",), sufixo="boolean", formatador=fmt_bool),
    RegraTipo(prefixos=("QT_",), sufixo="long", formatador=fmt_int),
)

REGRA_TIPO_PADRAO = RegraTipo(sufixo="", formatador=str)


def resolver_tipo(coluna: str) -> RegraTipo:
    return next((regra for regra in REGRAS_TIPO if regra.aplica(coluna)), REGRA_TIPO_PADRAO)


def com_tipo(coluna: str) -> str:
    sufixo = resolver_tipo(coluna).sufixo
    return f"{coluna}:{sufixo}" if sufixo else coluna


def valor_propriedade(coluna: str, valor) -> str:
    return resolver_tipo(coluna).formatador(valor)


# ---------------------------------------------------------------------------
# Regras de mapeamento das variáveis
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RegraMapeamento:
    prefixos: tuple[str, ...] = ()
    exatos: frozenset[str] = frozenset()
    destino: str = ""
    no_grafo: str = ""
    padrao: bool = False

    def aplica(self, variavel: str) -> bool:
        return self.padrao or variavel in self.exatos or variavel.startswith(self.prefixos)


REGRAS_MAPEAMENTO = {
    "cadastro_cursos": (
        RegraMapeamento(
            exatos=frozenset({"NU_ANO_CENSO"}),
            destino="OfertaCurso.NU_ANO_CENSO",
            no_grafo="OfertaCurso",
        ),
        RegraMapeamento(
            prefixos=("QT_",),
            destino="OfertaCurso.{variavel}",
            no_grafo="OfertaCurso",
        ),
        RegraMapeamento(
            exatos=frozenset({"CO_IES"}),
            destino="OfertaCurso.CO_IES + Curso.CO_IES + IES.CO_IES",
            no_grafo="OfertaCurso / Curso / IES",
        ),
        RegraMapeamento(
            exatos=frozenset({"CO_CURSO", "NO_CURSO"}),
            destino="Curso.{variavel}",
            no_grafo="Curso",
        ),
        RegraMapeamento(
            prefixos=("CO_CINE", "NO_CINE"),
            destino="Curso.{variavel} + nó CINE",
            no_grafo="Curso / Cine*",
        ),
        RegraMapeamento(
            exatos=frozenset({"TP_GRAU_ACADEMICO", "TP_NIVEL_ACADEMICO", "IN_GRATUITO"}),
            destino="Curso.{variavel} + nó de classificação",
            no_grafo="Curso / Classificacao",
        ),
        RegraMapeamento(
            exatos=frozenset({"TP_MODALIDADE_ENSINO"}),
            destino="OfertaCurso.TP_MODALIDADE_ENSINO + ModalidadeEnsino",
            no_grafo="OfertaCurso / ModalidadeEnsino",
        ),
        RegraMapeamento(
            exatos=frozenset({"TP_DIMENSAO"}),
            destino="OfertaCurso.TP_DIMENSAO + DimensaoGeografica",
            no_grafo="OfertaCurso / DimensaoGeografica",
        ),
        RegraMapeamento(
            exatos=frozenset(
                {
                    "TP_ORGANIZACAO_ACADEMICA",
                    "TP_REDE",
                    "TP_CATEGORIA_ADMINISTRATIVA",
                    "IN_COMUNITARIA",
                    "IN_CONFESSIONAL",
                }
            ),
            destino="IES.{variavel} + nó de classificação",
            no_grafo="IES / Classificacao",
        ),
        RegraMapeamento(
            exatos=GEOGRAFIA_CURSO,
            destino="OfertaCurso / nós de geografia",
            no_grafo="OfertaCurso / Geografia",
        ),
        RegraMapeamento(
            padrao=True,
            destino="OfertaCurso.{variavel}",
            no_grafo="OfertaCurso",
        ),
    ),
    "cadastro_ies": (
        RegraMapeamento(prefixos=("QT_",), destino="IES.{variavel}", no_grafo="IES"),
        RegraMapeamento(
            exatos=frozenset({"CO_MANTENEDORA", "NO_MANTENEDORA"}),
            destino="IES + Mantenedora",
            no_grafo="IES / Mantenedora",
        ),
        RegraMapeamento(
            exatos=GEOGRAFIA_IES,
            destino="IES / nós de geografia",
            no_grafo="IES / Geografia",
        ),
        RegraMapeamento(
            prefixos=("TP_",),
            destino="IES.{variavel} + nó de classificação",
            no_grafo="IES / Classificacao",
        ),
        RegraMapeamento(
            prefixos=("IN_",),
            destino="IES.{variavel}",
            no_grafo="IES / Classificacao",
        ),
        RegraMapeamento(padrao=True, destino="IES.{variavel}", no_grafo="IES"),
    ),
}


def resolver_mapeamento(arquivo: str, variavel: str) -> RegraMapeamento:
    return next(
        regra for regra in REGRAS_MAPEAMENTO[arquivo] if regra.aplica(variavel)
    )


def destino_variavel(arquivo: str, variavel: str) -> str:
    return resolver_mapeamento(arquivo, variavel).destino.format(variavel=variavel)


def no_grafo_variavel(arquivo: str, variavel: str) -> str:
    return resolver_mapeamento(arquivo, variavel).no_grafo.format(variavel=variavel)


# ---------------------------------------------------------------------------
# IDs e normalizações
# ---------------------------------------------------------------------------

def id_regiao(codigo: str) -> str:
    return f"regiao_{codigo}"


def id_uf(codigo: str) -> str:
    return f"uf_{codigo}"


def id_municipio(codigo: str) -> str:
    return f"municipio_{codigo}"


def id_ies(codigo: str) -> str:
    return f"ies_{codigo}"


def id_mantenedora(codigo: str) -> str:
    return f"mantenedora_{codigo}"


def id_curso(co_ies: str, co_curso: str) -> str:
    return f"curso_{co_ies}_{co_curso}"


def id_oferta(
    co_ies: str,
    co_curso: str,
    co_municipio: str,
    tp_dim: str,
    tp_mod: str,
) -> str:
    municipio = co_municipio.strip() or "SEM_MUN"
    return f"oferta_{co_ies}_{co_curso}_{municipio}_{tp_dim}_{tp_mod}"


def id_cine_rotulo(codigo: str) -> str:
    return f"cine_rotulo_{codigo}"


def id_cine_detalhada(codigo: str) -> str:
    return f"cine_area_detalhada_{codigo}"


def id_cine_especifica(codigo: str) -> str:
    return f"cine_area_especifica_{codigo}"


def id_cine_geral(codigo: str) -> str:
    return f"cine_area_geral_{codigo}"


def id_grau(codigo: str) -> str:
    codigo = str(codigo).strip()
    return f"grau_{codigo}" if codigo else "grau_NA"


def id_modalidade(codigo: str) -> str:
    return f"modalidade_{codigo}"


def id_nivel(codigo: str) -> str:
    return f"nivel_{codigo}"


def id_organizacao(codigo: str) -> str:
    return f"organizacao_{codigo}"


def id_rede(codigo: str) -> str:
    return f"rede_{codigo}"


def id_categoria(codigo: str) -> str:
    return f"categoria_{codigo}"


def id_dimensao(codigo: str) -> str:
    return f"dimensao_{codigo}"


def limpar_codigo_cine(codigo: str) -> str:
    """O CSV de origem traz o CO_CINE_ROTULO entre aspas literais."""
    return str(codigo).strip().strip('"').strip()


def nome_base(header: str) -> str:
    return header if header.startswith(":") else header.split(":", 1)[0]


def normalizar_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto)).strip()
