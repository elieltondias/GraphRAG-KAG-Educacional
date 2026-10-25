#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constrói um Labeled Property Graph (LPG) a partir dos microdados do
Censo da Educação Superior 2024 (INEP/MEC).

O grafo é exportado em CSV no formato aceito pelo neo4j-admin import:
  - nós:            :ID,:LABEL,<propriedades>
  - relacionamentos: :START_ID,:END_ID,:TYPE

Os CSVs são gravados em UTF-8, com separador vírgula e quebra de linha LF.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

from lpg_dominio import (
    ARESTAS,
    ARQ_CURSOS,
    ARQ_DICIONARIO,
    ARQ_IES,
    BASE_PADRAO,
    CAMPOS_IES_OFERTA,
    CLASSIFICACOES_IES,
    CODIGOS_DIMENSAO,
    CODIGOS_GRAU,
    CODIGOS_MODALIDADE,
    CODIGOS_NIVEL,
    CONTROLE_COLS,
    CURSO_PROPS,
    ESPERADO_CURSOS_COLUNAS,
    ESPERADO_IES_COLUNAS,
    ESPERADO_IES_LINHAS,
    ESPERADO_QT_COLUNAS,
    MAP_CATEGORIA_ADMINISTRATIVA,
    MAP_DIMENSAO,
    MAP_GRAU,
    MAP_MODALIDADE,
    MAP_NIVEL,
    MAP_ORGANIZACAO,
    MAP_REDE,
    MAP_ABRANGENCIA,
    NOS,
    OFERTA_CORE_PROPS,
    REFERENCIAS,
    SAIDA_PADRAO,
    id_categoria,
    id_cine_detalhada,
    id_cine_especifica,
    id_cine_geral,
    id_cine_rotulo,
    id_curso,
    id_dimensao,
    id_grau,
    id_ies,
    id_mantenedora,
    id_municipio,
    id_modalidade,
    id_nivel,
    id_oferta,
    id_organizacao,
    id_rede,
    id_regiao,
    id_uf,
    limpar_codigo_cine,
    valor_propriedade,
)
from lpg_io import (
    EdgeWriter,
    NodeWriter,
    escrever_falhas,
    escrever_manifest,
    escrever_schema,
    ler_csv_completo,
)

# ---------------------------------------------------------------------------
# Configuração declarativa local
# ---------------------------------------------------------------------------

RESOLVEDORES_PROPS = {
    "ies": lambda spec, ies_header, qt_cols: list(ies_header),
    "oferta": lambda spec, ies_header, qt_cols: list(OFERTA_CORE_PROPS) + list(qt_cols),
}
RESOLVEDOR_PROPS_PADRAO = lambda spec, ies_header, qt_cols: list(spec.propriedades)

CINE_CAMPOS = (
    ("geral", "CINE área geral", "CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL", None, str.strip),
    (
        "especifica",
        "CINE área específica",
        "CO_CINE_AREA_ESPECIFICA",
        "NO_CINE_AREA_ESPECIFICA",
        "CO_CINE_AREA_GERAL",
        str.strip,
    ),
    (
        "detalhada",
        "CINE área detalhada",
        "CO_CINE_AREA_DETALHADA",
        "NO_CINE_AREA_DETALHADA",
        "CO_CINE_AREA_ESPECIFICA",
        str.strip,
    ),
    (
        "rotulo",
        "CINE rótulo",
        "CO_CINE_ROTULO",
        "NO_CINE_ROTULO",
        "CO_CINE_AREA_DETALHADA",
        limpar_codigo_cine,
    ),
)

CINE_SAIDA = (
    ("geral", "cine_area_geral", id_cine_geral),
    ("especifica", "cine_area_especifica", id_cine_especifica),
    ("detalhada", "cine_area_detalhada", id_cine_detalhada),
    ("rotulo", "cine_rotulo", id_cine_rotulo),
)

CINE_ARESTAS = (
    ("especifica", "cine_especifica_geral", "geral", id_cine_especifica, id_cine_geral),
    ("detalhada", "cine_detalhada_especifica", "especifica", id_cine_detalhada, id_cine_especifica),
    ("rotulo", "cine_rotulo_detalhada", "detalhada", id_cine_rotulo, id_cine_detalhada),
)


def resolver_propriedades(spec, ies_header: list[str], qt_cols: list[str]) -> list[str]:
    resolvedor = RESOLVEDORES_PROPS.get(spec.fonte_props, RESOLVEDOR_PROPS_PADRAO)
    return resolvedor(spec, ies_header, qt_cols)


# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------

class ColetorErros:
    def __init__(self, limite: int = 500):
        self.falhas: list[str] = []
        self.avisos: list[str] = []
        self._limite = limite

    def falha(self, mensagem: str) -> None:
        if len(self.falhas) < self._limite:
            self.falhas.append(mensagem)

    def aviso(self, mensagem: str) -> None:
        if len(self.avisos) < self._limite:
            self.avisos.append(mensagem)

    def exigir(self, condicao: bool, mensagem: str) -> bool:
        if not condicao:
            self.falha(mensagem)
        return condicao


# ---------------------------------------------------------------------------
# Localização da oferta: polimorfismo
# ---------------------------------------------------------------------------

class LocalizacaoOferta:
    def __init__(self, d: dict[str, str], oferta_id: str, coletor: Coletor):
        self.d = d
        self.oferta_id = oferta_id
        self.coletor = coletor

    @property
    def origem(self) -> str:
        return f"Oferta {self.d['CO_IES']}/{self.d['CO_CURSO']}"

    def registrar(self) -> None:
        raise NotImplementedError


class SemMunicipio(LocalizacaoOferta):
    def registrar(self) -> None:
        self.coletor.ofertas_sem_municipio += 1
        self.coletor.erros.exigir(
            not self.d["CO_UF"].strip() and not self.d["CO_REGIAO"].strip(),
            f"Oferta {self.oferta_id}: sem município, mas com UF/região preenchida",
        )
        self.coletor.erros.exigir(
            not self.d["IN_CAPITAL"].strip(),
            f"Oferta {self.oferta_id}: sem município, mas com IN_CAPITAL preenchido",
        )


class ComMunicipio(LocalizacaoOferta):
    def registrar(self) -> None:
        co_municipio = self.d["CO_MUNICIPIO"].strip()
        self.coletor.edge_writers["oferta_municipio"].escrever(
            self.oferta_id, id_municipio(co_municipio)
        )
        self.coletor.registrar_municipio(
            co_municipio,
            self.d["NO_MUNICIPIO"],
            self.d["CO_UF"],
            self.d["SG_UF"],
            self.d["IN_CAPITAL"],
            self.origem,
        )
        self.coletor.registrar_uf(
            self.d["CO_UF"],
            self.d["SG_UF"],
            self.d["NO_UF"],
            self.d["CO_REGIAO"],
            self.d["NO_REGIAO"],
            self.origem,
        )
        municipio = self.coletor.municipios.get(co_municipio)
        self.coletor.erros.exigir(
            municipio is not None
            and municipio["CO_UF"] == self.d["CO_UF"].strip(),
            f"Oferta {self.oferta_id}: município {co_municipio} com UF divergente",
        )


CLASSES_LOCALIZACAO = {True: ComMunicipio, False: SemMunicipio}


def criar_localizacao(
    d: dict[str, str], oferta_id: str, coletor: Coletor
) -> LocalizacaoOferta:
    classe = CLASSES_LOCALIZACAO[bool(d["CO_MUNICIPIO"].strip())]
    return classe(d, oferta_id, coletor)


# ---------------------------------------------------------------------------
# Coletor
# ---------------------------------------------------------------------------

class Coletor:
    def __init__(self, saida: Path, ies_header: list[str], cursos_header: list[str]):
        self.saida = saida
        self.ies_header = ies_header
        self.cursos_header = cursos_header
        self.qt_cols = [c for c in cursos_header if c.startswith("QT_")]
        self.curso_props = list(CURSO_PROPS)
        self.oferta_props = list(OFERTA_CORE_PROPS) + self.qt_cols
        self.erros = ColetorErros()

        self.node_writers: dict[str, NodeWriter] = {}
        self.edge_writers: dict[str, EdgeWriter] = {}
        self._criar_writers()

        self.ies: dict[str, dict[str, str]] = {}
        self.mantenedoras: dict[str, str] = {}
        self.municipios: dict[str, dict] = {}
        self.ufs: dict[str, dict[str, str]] = {}
        self.regioes: dict[str, str] = {}
        self.cursos: dict[tuple[str, str], dict[str, str]] = {}
        self.curso_ies: dict[str, str] = {}
        self.cine: dict[str, dict[str, tuple[str, str | None]]] = {
            "geral": {},
            "especifica": {},
            "detalhada": {},
            "rotulo": {},
        }

        self.graus: set[str] = set()
        self.niveis: set[str] = set()
        self.modalidades: set[str] = set()
        self.dimensoes: set[str] = set()
        self.organizacoes: set[str] = set()
        self.redes: set[str] = set()
        self.categorias: set[str] = set()

        self.ofertas_ids: set[str] = set()
        self.ofertas_sem_municipio = 0
        self.ofertas_por_dimensao: Counter[str] = Counter()
        self.ofertas_por_modalidade: Counter[str] = Counter()
        self.cursos_por_grau: Counter[str] = Counter()
        self.cursos_por_nivel: Counter[str] = Counter()
        self.ies_por_rede: Counter[str] = Counter()
        self.ies_por_categoria: Counter[str] = Counter()
        self.ies_por_organizacao: Counter[str] = Counter()
        self.cursos_sem_grau = 0
        self.divergencias_ies = 0
        self.municipios_capital_misto = 0
        self.linhas_curso = 0
        self.controle: Counter[str] = Counter()

    @property
    def cine_rotulo(self) -> dict[str, tuple[str, str | None]]:
        return self.cine["rotulo"]

    # -- writers ----------------------------------------------------------

    def _criar_writers(self) -> None:
        for spec in NOS:
            propriedades = resolver_propriedades(spec, self.ies_header, self.qt_cols)
            self.node_writers[spec.chave] = NodeWriter(
                self.saida / spec.caminho, spec.label, propriedades
            )
        for spec in ARESTAS:
            self.edge_writers[spec.chave] = EdgeWriter(
                self.saida / spec.caminho, spec.tipo
            )

    # -- utilidades de consistência ---------------------------------------

    def _comparar_registro(
        self,
        anterior: dict,
        novo: dict,
        campos: tuple[str, ...],
        mensagem: str,
    ) -> None:
        divergentes = [campo for campo in campos if anterior[campo] != novo[campo]]
        if divergentes:
            self.erros.falha(f"{mensagem}: {divergentes}")

    def registrar_regiao(self, co_regiao: str, no_regiao: str, origem: str) -> None:
        co_regiao = co_regiao.strip()
        no_regiao = no_regiao.strip()
        if not co_regiao:
            self.erros.falha(f"{origem}: CO_REGIAO vazio")
            return
        if not no_regiao:
            self.erros.falha(f"{origem}: NO_REGIAO vazio para CO_REGIAO={co_regiao}")
            return
        anterior = self.regioes.get(co_regiao)
        if anterior is not None and anterior != no_regiao:
            self.erros.falha(
                f"{origem}: região {co_regiao} com nomes divergentes: "
                f"{anterior!r} e {no_regiao!r}"
            )
        self.regioes[co_regiao] = no_regiao

    def registrar_uf(
        self,
        co_uf: str,
        sg_uf: str,
        no_uf: str,
        co_regiao: str,
        no_regiao: str,
        origem: str,
    ) -> None:
        co_uf = co_uf.strip()
        sg_uf = sg_uf.strip()
        no_uf = no_uf.strip()
        co_regiao = co_regiao.strip()
        if not co_uf:
            self.erros.falha(f"{origem}: CO_UF vazio")
            return
        if not sg_uf or not no_uf:
            self.erros.falha(f"{origem}: UF {co_uf} sem sigla/nome")
        if not co_regiao:
            self.erros.falha(f"{origem}: UF {co_uf} sem CO_REGIAO")
            return
        self.registrar_regiao(co_regiao, no_regiao, origem)
        novo = {"SG_UF": sg_uf, "NO_UF": no_uf, "CO_REGIAO": co_regiao}
        anterior = self.ufs.get(co_uf)
        if anterior is not None:
            self._comparar_registro(
                anterior,
                novo,
                ("SG_UF", "NO_UF", "CO_REGIAO"),
                f"{origem}: UF {co_uf} com dados divergentes",
            )
        self.ufs[co_uf] = novo

    def registrar_municipio(
        self,
        co_municipio: str,
        no_municipio: str,
        co_uf: str,
        sg_uf: str,
        in_capital: str,
        origem: str,
    ) -> None:
        co_municipio = co_municipio.strip()
        no_municipio = no_municipio.strip()
        co_uf = co_uf.strip()
        sg_uf = sg_uf.strip()
        if not co_municipio:
            return
        if not no_municipio:
            self.erros.falha(f"{origem}: município {co_municipio} sem nome")
            return
        if not co_uf or not sg_uf:
            self.erros.falha(f"{origem}: município {co_municipio} sem UF")
            return

        novo = {
            "NO_MUNICIPIO": no_municipio,
            "CO_UF": co_uf,
            "SG_UF": sg_uf,
            "CAPITAL": set(),
        }
        dados = self.municipios.setdefault(co_municipio, novo)
        self._comparar_registro(
            dados,
            novo,
            ("NO_MUNICIPIO", "CO_UF", "SG_UF"),
            f"{origem}: município {co_municipio} com dados divergentes",
        )
        valor = str(in_capital).strip()
        if valor:
            dados["CAPITAL"].add(valor)

    def registrar_mantenedora(self, co_mantenedora: str, no_mantenedora: str) -> None:
        anterior = self.mantenedoras.get(co_mantenedora)
        if anterior is not None:
            self.erros.exigir(
                anterior == no_mantenedora,
                f"Mantenedora {co_mantenedora} com nomes divergentes: "
                f"{anterior!r} e {no_mantenedora!r}",
            )
        self.mantenedoras[co_mantenedora] = no_mantenedora

    def registrar_classificacao_ies(self, spec, codigo: str, co_ies: str) -> None:
        if codigo not in spec.codigos_validos:
            self.erros.falha(f"IES {co_ies}: {spec.campo} inválido: {codigo}")
            return
        getattr(self, spec.conjunto).add(codigo)
        getattr(self, spec.contador)[codigo] += 1
        self.edge_writers[spec.writer].escrever(
            id_ies(co_ies), f"{spec.prefixo}_{codigo}"
        )

    # -- IES ---------------------------------------------------------------

    def registrar_ies(self, d: dict[str, str]) -> None:
        co_ies = d["CO_IES"].strip()
        if not co_ies:
            self.erros.falha("IES: CO_IES vazio")
            return
        if co_ies in self.ies:
            self.erros.falha(f"IES duplicada no arquivo de IES: {co_ies}")
            return
        self.ies[co_ies] = d

        self.node_writers["ies"].escrever(
            id_ies(co_ies),
            [valor_propriedade(c, d[c]) for c in self.ies_header],
        )

        co_municipio = d["CO_MUNICIPIO_IES"].strip()
        co_mantenedora = d["CO_MANTENEDORA"].strip()

        if not co_municipio:
            self.erros.falha(f"IES {co_ies}: CO_MUNICIPIO_IES vazio")
        else:
            self.edge_writers["ies_municipio"].escrever(
                id_ies(co_ies), id_municipio(co_municipio)
            )

        if not co_mantenedora:
            self.erros.falha(f"IES {co_ies}: CO_MANTENEDORA vazio")
        else:
            self.registrar_mantenedora(
                co_mantenedora, d["NO_MANTENEDORA"].strip()
            )
            self.edge_writers["ies_mantenedora"].escrever(
                id_ies(co_ies), id_mantenedora(co_mantenedora)
            )

        for spec in CLASSIFICACOES_IES:
            self.registrar_classificacao_ies(
                spec, d[spec.campo].strip(), co_ies
            )

        self.registrar_municipio(
            co_municipio,
            d["NO_MUNICIPIO_IES"],
            d["CO_UF_IES"],
            d["SG_UF_IES"],
            d["IN_CAPITAL_IES"],
            f"IES {co_ies}",
        )
        self.registrar_uf(
            d["CO_UF_IES"],
            d["SG_UF_IES"],
            d["NO_UF_IES"],
            d["CO_REGIAO_IES"],
            d["NO_REGIAO_IES"],
            f"IES {co_ies}",
        )

    # -- Curso e CINE ------------------------------------------------------

    def registrar_curso(self, d: dict[str, str]) -> None:
        co_ies = d["CO_IES"].strip()
        co_curso = d["CO_CURSO"].strip()
        if not co_ies or not co_curso:
            self.erros.falha("Curso com CO_IES/CO_CURSO vazio")
            return
        if not d["NO_CURSO"].strip():
            self.erros.falha(f"Curso {co_ies}/{co_curso} sem NO_CURSO")

        grau = d["TP_GRAU_ACADEMICO"].strip() or "NA"
        nivel = d["TP_NIVEL_ACADEMICO"].strip()
        for campo, codigo, validos in (
            ("grau", grau, CODIGOS_GRAU),
            ("nível", nivel, CODIGOS_NIVEL),
        ):
            self.erros.exigir(
                codigo in validos,
                f"Curso {co_ies}/{co_curso}: {campo} inválido: {codigo}",
            )

        atributos = {c: d[c] for c in self.curso_props}
        atributos["CO_CINE_ROTULO"] = limpar_codigo_cine(d["CO_CINE_ROTULO"])
        chave = (co_ies, co_curso)
        anterior = self.cursos.get(chave)
        if anterior is not None:
            self.erros.exigir(
                anterior == atributos,
                f"Curso {co_ies}/{co_curso} com atributos divergentes entre ofertas",
            )
            return

        self.cursos[chave] = atributos
        outro_ies = self.curso_ies.get(co_curso)
        if outro_ies is not None:
            self.erros.exigir(
                outro_ies == co_ies,
                f"CO_CURSO {co_curso} associado a mais de uma IES: "
                f"{outro_ies} e {co_ies}",
            )
        self.curso_ies[co_curso] = co_ies
        self.graus.add(grau)
        self.niveis.add(nivel)
        self.cursos_por_grau[grau] += 1
        self.cursos_por_nivel[nivel] += 1
        self.cursos_sem_grau += grau == "NA"

    def registrar_cine(self, d: dict[str, str]) -> None:
        definicoes = []
        for nivel, descricao, campo_codigo, campo_nome, campo_pai, normalizador in CINE_CAMPOS:
            codigo = normalizador(d[campo_codigo])
            nome = d[campo_nome].strip()
            if not codigo or not nome:
                self.erros.falha(
                    f"{descricao} vazio em curso {d['CO_IES']}/{d['CO_CURSO']}"
                )
                return
            pai = d[campo_pai].strip() if campo_pai else None
            definicoes.append((nivel, codigo, nome, pai))

        for nivel, codigo, nome, pai in definicoes:
            colecao = self.cine[nivel]
            atual = colecao.get(codigo)
            if atual is not None:
                self.erros.exigir(
                    atual == (nome, pai),
                    f"CINE {nivel} {codigo} com pai/nome divergente",
                )
            colecao[codigo] = (nome, pai)

    # -- Oferta ------------------------------------------------------------

    def _validar_ies_oferta(
        self, d: dict[str, str], oferta_id: str, co_ies: str
    ) -> None:
        ies = self.ies.get(co_ies)
        if ies is None:
            self.erros.falha(f"Oferta {oferta_id}: IES {co_ies} não encontrada")
            return
        divergentes = [c for c in CAMPOS_IES_OFERTA if d[c] != ies[c]]
        self.divergencias_ies += len(divergentes)
        for coluna in divergentes:
            self.erros.falha(
                f"Oferta {oferta_id}: {coluna} diverge da IES "
                f"({d[coluna]!r} vs {ies[coluna]!r})"
            )

    def processar_curso(self, linha: list[str]) -> None:
        if len(linha) != len(self.cursos_header):
            self.erros.falha(
                f"Linha de curso {self.linhas_curso + 1}: "
                f"{len(linha)} campos; esperado {len(self.cursos_header)}"
            )
            return
        self.linhas_curso += 1
        d = dict(zip(self.cursos_header, linha))

        co_ies = d["CO_IES"].strip()
        co_curso = d["CO_CURSO"].strip()
        co_municipio = d["CO_MUNICIPIO"].strip()
        tp_dim = d["TP_DIMENSAO"].strip()
        tp_mod = d["TP_MODALIDADE_ENSINO"].strip()

        if not co_ies or not co_curso:
            self.erros.falha(
                f"Oferta na linha {self.linhas_curso}: CO_IES/CO_CURSO vazio"
            )
            return

        for campo, valor, validos, conjunto in (
            ("TP_DIMENSAO", tp_dim, CODIGOS_DIMENSAO, self.dimensoes),
            ("TP_MODALIDADE_ENSINO", tp_mod, CODIGOS_MODALIDADE, self.modalidades),
        ):
            if valor not in validos:
                self.erros.falha(
                    f"Oferta {co_ies}/{co_curso}: {campo} inválido: {valor}"
                )
                continue
            conjunto.add(valor)

        oferta_id = id_oferta(co_ies, co_curso, co_municipio, tp_dim, tp_mod)
        self.erros.exigir(
            oferta_id not in self.ofertas_ids, f"Oferta duplicada: {oferta_id}"
        )
        self.ofertas_ids.add(oferta_id)

        self.node_writers["oferta"].escrever(
            oferta_id,
            [valor_propriedade(c, d[c]) for c in self.oferta_props],
        )

        for chave, destino in (
            ("oferta_curso", id_curso(co_ies, co_curso)),
            ("oferta_ies", id_ies(co_ies)),
            ("oferta_modalidade", id_modalidade(tp_mod)),
            ("oferta_dimensao", id_dimensao(tp_dim)),
        ):
            self.edge_writers[chave].escrever(oferta_id, destino)

        criar_localizacao(d, oferta_id, self).registrar()

        self.ofertas_por_dimensao[tp_dim] += 1
        self.ofertas_por_modalidade[tp_mod] += 1

        for coluna in CONTROLE_COLS:
            try:
                self.controle[coluna] += int(d[coluna] or 0)
            except ValueError:
                self.erros.falha(
                    f"Oferta {oferta_id}: valor não inteiro em {coluna}: "
                    f"{d[coluna]!r}"
                )

        self._validar_ies_oferta(d, oferta_id, co_ies)
        self.registrar_curso(d)
        self.registrar_cine(d)

    # -- escrita final -----------------------------------------------------

    def finalizar(self) -> None:
        self._escrever_regioes()
        self._escrever_ufs()
        self._escrever_municipios()
        self._escrever_mantenedoras()
        self._escrever_cursos()
        self._escrever_cine()
        self._escrever_classificacoes()
        self._escrever_arestas_geografia()
        self._escrever_arestas_cine()
        self._validar_referencias()

    def _escrever_regioes(self) -> None:
        for codigo in sorted(self.regioes, key=int):
            self.node_writers["regiao"].escrever(
                id_regiao(codigo), [codigo, self.regioes[codigo]]
            )

    def _escrever_ufs(self) -> None:
        for codigo in sorted(self.ufs, key=int):
            dados = self.ufs[codigo]
            self.node_writers["uf"].escrever(
                id_uf(codigo),
                [codigo, dados["SG_UF"], dados["NO_UF"], dados["CO_REGIAO"]],
            )

    def _escrever_municipios(self) -> None:
        for codigo in sorted(self.municipios):
            dados = self.municipios[codigo]
            capitais = dados["CAPITAL"]
            self.municipios_capital_misto += len(capitais) > 1
            self.node_writers["municipio"].escrever(
                id_municipio(codigo),
                [
                    codigo,
                    dados["NO_MUNICIPIO"],
                    dados["CO_UF"],
                    dados["SG_UF"],
                    "true" if "1" in capitais else "false",
                ],
            )

    def _escrever_mantenedoras(self) -> None:
        for codigo in sorted(self.mantenedoras):
            self.node_writers["mantenedora"].escrever(
                id_mantenedora(codigo),
                [codigo, self.mantenedoras[codigo]],
            )

    def _escrever_cursos(self) -> None:
        for chave in sorted(self.cursos, key=lambda k: (k[1], k[0])):
            d = self.cursos[chave]
            co_ies = d["CO_IES"].strip()
            co_curso = d["CO_CURSO"].strip()
            curso_id = id_curso(co_ies, co_curso)

            self.node_writers["curso"].escrever(
                curso_id,
                [valor_propriedade(c, d[c]) for c in self.curso_props],
            )
            for chave_aresta, destino in (
                ("curso_ies", id_ies(co_ies)),
                ("curso_grau", id_grau(d["TP_GRAU_ACADEMICO"])),
                ("curso_nivel", id_nivel(d["TP_NIVEL_ACADEMICO"])),
                ("curso_cine", id_cine_rotulo(d["CO_CINE_ROTULO"])),
            ):
                self.edge_writers[chave_aresta].escrever(curso_id, destino)

    def _escrever_cine(self) -> None:
        for nivel, writer, id_fn in CINE_SAIDA:
            for codigo in sorted(self.cine[nivel]):
                nome, pai = self.cine[nivel][codigo]
                valores = [codigo, nome] if pai is None else [codigo, nome, pai]
                self.node_writers[writer].escrever(id_fn(codigo), valores)

    def _escrever_classificacoes(self) -> None:
        for codigo in sorted(self.graus, key=lambda x: 0 if x == "NA" else int(x)):
            nome = MAP_GRAU["NA"] if codigo == "NA" else MAP_GRAU[int(codigo)]
            self.node_writers["grau"].escrever(id_grau(codigo), [codigo, nome])

        for codigo in sorted(self.modalidades, key=int):
            self.node_writers["modalidade"].escrever(
                id_modalidade(codigo),
                [codigo, MAP_MODALIDADE[int(codigo)]],
            )

        for codigo in sorted(self.niveis, key=int):
            self.node_writers["nivel"].escrever(
                id_nivel(codigo), [codigo, MAP_NIVEL[int(codigo)]]
            )

        for codigo in sorted(self.organizacoes, key=int):
            self.node_writers["organizacao"].escrever(
                id_organizacao(codigo),
                [codigo, MAP_ORGANIZACAO[int(codigo)]],
            )

        for codigo in sorted(self.redes, key=int):
            self.node_writers["rede"].escrever(
                id_rede(codigo), [codigo, MAP_REDE[int(codigo)]]
            )

        for codigo in sorted(self.categorias, key=int):
            self.node_writers["categoria"].escrever(
                id_categoria(codigo),
                [codigo, MAP_CATEGORIA_ADMINISTRATIVA[int(codigo)]],
            )

        for codigo in sorted(self.dimensoes, key=int):
            self.node_writers["dimensao"].escrever(
                id_dimensao(codigo),
                [codigo, MAP_DIMENSAO[int(codigo)], MAP_ABRANGENCIA[int(codigo)]],
            )

    def _escrever_arestas_geografia(self) -> None:
        for codigo, dados in self.ufs.items():
            self.edge_writers["uf_regiao"].escrever(
                id_uf(codigo), id_regiao(dados["CO_REGIAO"])
            )
        for codigo, dados in self.municipios.items():
            self.edge_writers["municipio_uf"].escrever(
                id_municipio(codigo), id_uf(dados["CO_UF"])
            )

    def _escrever_arestas_cine(self) -> None:
        for nivel, writer, pai_nivel, id_fn, pai_id_fn in CINE_ARESTAS:
            for codigo, (_, pai) in self.cine[nivel].items():
                self.edge_writers[writer].escrever(id_fn(codigo), pai_id_fn(pai))

    def _validar_referencias(self) -> None:
        for referencia in REFERENCIAS:
            colecao = getattr(self, referencia.colecao)
            destino = getattr(self, referencia.destino)
            for chave, dados in colecao.items():
                if dados[referencia.campo] not in destino:
                    self.erros.falha(
                        f"{referencia.descricao}: {chave} -> "
                        f"{dados[referencia.campo]}"
                    )

        for chave, dados in self.cursos.items():
            if dados["TP_NIVEL_ACADEMICO"] not in self.niveis:
                self.erros.falha(
                    f"Curso {chave}: nível {dados['TP_NIVEL_ACADEMICO']} "
                    "não encontrado"
                )

        for nivel, _, pai_nivel, _, _ in CINE_ARESTAS:
            for chave, (_, pai) in self.cine[nivel].items():
                if pai not in self.cine[pai_nivel]:
                    self.erros.falha(
                        f"CINE {nivel} {chave}: pai {pai} não encontrado"
                    )

    def fechar(self) -> None:
        for writer in self.node_writers.values():
            writer.fechar()
        for writer in self.edge_writers.values():
            writer.fechar()

    def resumo(self) -> dict:
        return {
            "linhas_curso_lidas": self.linhas_curso,
            "ofertas_unicas": len(self.ofertas_ids),
            "ofertas_sem_municipio": self.ofertas_sem_municipio,
            "cursos_unicos": len(self.cursos),
            "cursos_sem_grau": self.cursos_sem_grau,
            "ies_unicas": len(self.ies),
            "municipios": len(self.municipios),
            "ufs": len(self.ufs),
            "regioes": len(self.regioes),
            "mantenedoras": len(self.mantenedoras),
            "cine_rotulos": len(self.cine["rotulo"]),
            "cine_areas_detalhadas": len(self.cine["detalhada"]),
            "cine_areas_especificas": len(self.cine["especifica"]),
            "cine_areas_gerais": len(self.cine["geral"]),
            "divergencias_ies": self.divergencias_ies,
            "municipios_capital_misto": self.municipios_capital_misto,
            "controle": dict(sorted(self.controle.items())),
            "distribuicoes": {
                "TP_DIMENSAO": dict(sorted(self.ofertas_por_dimensao.items())),
                "TP_MODALIDADE_ENSINO": dict(
                    sorted(self.ofertas_por_modalidade.items())
                ),
                "TP_GRAU_ACADEMICO": dict(sorted(self.cursos_por_grau.items())),
                "TP_NIVEL_ACADEMICO": dict(sorted(self.cursos_por_nivel.items())),
                "TP_REDE_IES": dict(sorted(self.ies_por_rede.items())),
                "TP_CATEGORIA_ADMINISTRATIVA_IES": dict(
                    sorted(self.ies_por_categoria.items())
                ),
                "TP_ORGANIZACAO_ACADEMICA_IES": dict(
                    sorted(self.ies_por_organizacao.items())
                ),
            },
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def validar_headers(cursos_header: list[str], ies_header: list[str]) -> None:
    if len(cursos_header) != ESPERADO_CURSOS_COLUNAS:
        raise ValueError(
            f"CSV de cursos com {len(cursos_header)} colunas; "
            f"esperado {ESPERADO_CURSOS_COLUNAS}"
        )
    if len(ies_header) != ESPERADO_IES_COLUNAS:
        raise ValueError(
            f"CSV de IES com {len(ies_header)} colunas; "
            f"esperado {ESPERADO_IES_COLUNAS}"
        )
    qt = [c for c in cursos_header if c.startswith("QT_")]
    if len(qt) != ESPERADO_QT_COLUNAS:
        raise ValueError(
            f"CSV de cursos com {len(qt)} colunas QT_*; "
            f"esperado {ESPERADO_QT_COLUNAS}"
        )
    obrigatorias_cursos = set(CURSO_PROPS) | set(OFERTA_CORE_PROPS) | {
        "TP_ORGANIZACAO_ACADEMICA",
        "TP_REDE",
        "TP_CATEGORIA_ADMINISTRATIVA",
        "IN_COMUNITARIA",
        "IN_CONFESSIONAL",
        "NO_REGIAO",
        "CO_REGIAO",
        "NO_UF",
        "SG_UF",
        "CO_UF",
        "NO_MUNICIPIO",
        "CO_MUNICIPIO",
    }
    faltantes = obrigatorias_cursos - set(cursos_header)
    if faltantes:
        raise ValueError(f"CSV de cursos sem colunas: {sorted(faltantes)}")

    obrigatorias_ies = {
        "NU_ANO_CENSO",
        "CO_IES",
        "NO_IES",
        "SG_IES",
        "CO_MUNICIPIO_IES",
        "NO_MUNICIPIO_IES",
        "CO_UF_IES",
        "SG_UF_IES",
        "NO_UF_IES",
        "CO_REGIAO_IES",
        "NO_REGIAO_IES",
        "CO_MANTENEDORA",
        "NO_MANTENEDORA",
        "TP_ORGANIZACAO_ACADEMICA",
        "TP_REDE",
        "TP_CATEGORIA_ADMINISTRATIVA",
        "IN_CAPITAL_IES",
        "IN_COMUNITARIA",
        "IN_CONFESSIONAL",
    }
    faltantes = obrigatorias_ies - set(ies_header)
    if faltantes:
        raise ValueError(f"CSV de IES sem colunas: {sorted(faltantes)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Constrói o LPG do Censo da Educação Superior 2024 em CSV."
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=BASE_PADRAO,
        help=f"Pasta dos microdados (padrão: {BASE_PADRAO})",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=SAIDA_PADRAO,
        help=f"Pasta de saída (padrão: {SAIDA_PADRAO})",
    )
    parser.add_argument("--cursos", type=Path, help="CSV de cursos (opcional)")
    parser.add_argument("--ies", type=Path, help="CSV de IES (opcional)")
    parser.add_argument(
        "--dicionario", type=Path, help="XLSX do dicionário (opcional)"
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=0,
        help="Processa apenas N linhas de curso (útil para teste).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = args.base
    saida = args.saida
    cursos_path = args.cursos or base / ARQ_CURSOS
    ies_path = args.ies or base / ARQ_IES
    dicionario_path = args.dicionario or base / ARQ_DICIONARIO

    for caminho in (cursos_path, ies_path):
        if not caminho.exists():
            print(f"ERRO: arquivo não encontrado: {caminho}", file=sys.stderr)
            return 1

    saida.mkdir(parents=True, exist_ok=True)

    print(f"Lendo IES: {ies_path}")
    ies_header, ies_registros = ler_csv_completo(ies_path)
    if len(ies_registros) != ESPERADO_IES_LINHAS:
        print(
            f"AVISO: {len(ies_registros)} IES lidas; esperado {ESPERADO_IES_LINHAS}",
            file=sys.stderr,
        )

    print(f"Lendo cabeçalho de cursos: {cursos_path}")
    with cursos_path.open(encoding="latin-1", newline="") as arquivo_cursos:
        reader = csv.reader(arquivo_cursos, delimiter=";")
        try:
            cursos_header = next(reader)
        except StopIteration:
            print("ERRO: CSV de cursos vazio", file=sys.stderr)
            return 1

        validar_headers(cursos_header, ies_header)
        builder = Coletor(saida, ies_header, cursos_header)
        try:
            print(f"Processando {len(ies_registros)} IES...")
            for registro in ies_registros:
                builder.registrar_ies(registro)

            print("Processando ofertas de curso...")
            for numero, linha in enumerate(reader, start=1):
                builder.processar_curso(linha)
                if numero % 50_000 == 0:
                    print(f"  {numero:,} linhas de curso processadas")
                if args.limite and numero >= args.limite:
                    print(f"  limite de teste atingido: {numero:,} linhas")
                    break

            print("Gravando nós e arestas restantes...")
            builder.finalizar()
        finally:
            builder.fechar()

    if builder.erros.falhas:
        escrever_falhas(saida, builder.erros.falhas)
        print(
            f"ERRO: {len(builder.erros.falhas)} falha(s) encontrada(s). "
            f"Veja {saida / 'validacao' / 'falhas_build.txt'}",
            file=sys.stderr,
        )
        for falha in builder.erros.falhas[:20]:
            print(f"  - {falha}", file=sys.stderr)
        return 1

    print("Gerando arquivos de schema...")
    escrever_schema(
        saida,
        dicionario_path,
        cursos_header,
        ies_header,
        builder.erros.falhas,
    )
    if builder.erros.falhas:
        escrever_falhas(saida, builder.erros.falhas)
        print(
            f"ERRO: {len(builder.erros.falhas)} falha(s) ao gerar schema. "
            f"Veja {saida / 'validacao' / 'falhas_build.txt'}",
            file=sys.stderr,
        )
        return 1

    print("Gerando manifesto...")
    escrever_manifest(
        saida,
        builder.node_writers,
        builder.edge_writers,
        builder.resumo(),
        cursos_header,
        ies_header,
        builder.qt_cols,
        builder.erros.avisos,
    )

    resumo = builder.resumo()
    total_nos = sum(w.count for w in builder.node_writers.values())
    total_arestas = sum(w.count for w in builder.edge_writers.values())

    print()
    print("=" * 72)
    print("LPG gerado com sucesso")
    print("=" * 72)
    print(f"Saída: {saida}")
    print(f"Linhas de curso lidas: {resumo['linhas_curso_lidas']:,}")
    print(f"Ofertas únicas: {resumo['ofertas_unicas']:,}")
    print(f"Cursos únicos: {resumo['cursos_unicos']:,}")
    print(f"IES únicas: {resumo['ies_unicas']:,}")
    print(f"Municípios: {resumo['municipios']:,}")
    print(f"UFs: {resumo['ufs']} | Regiões: {resumo['regioes']}")
    print(f"Mantenedoras: {resumo['mantenedoras']:,}")
    print(f"Nós: {total_nos:,}")
    print(f"Arestas: {total_arestas:,}")
    print(f"Ofertas sem município: {resumo['ofertas_sem_municipio']:,}")
    print(f"Cursos sem grau acadêmico: {resumo['cursos_sem_grau']:,}")
    print(f"Divergências IES/curso: {resumo['divergencias_ies']:,}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
