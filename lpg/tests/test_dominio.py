#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes das regras puras do domínio do LPG."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lpg_dominio as d  # noqa: E402


class TestTipagem(unittest.TestCase):
    def test_com_tipo(self) -> None:
        self.assertEqual(d.com_tipo("NU_ANO_CENSO"), "NU_ANO_CENSO:int")
        self.assertEqual(d.com_tipo("TP_GRAU_ACADEMICO"), "TP_GRAU_ACADEMICO:int")
        self.assertEqual(d.com_tipo("IN_CAPITAL"), "IN_CAPITAL:boolean")
        self.assertEqual(d.com_tipo("QT_MAT"), "QT_MAT:long")
        self.assertEqual(d.com_tipo("CO_IES"), "CO_IES")
        self.assertEqual(d.com_tipo("NO_IES"), "NO_IES")

    def test_valor_propriedade(self) -> None:
        self.assertEqual(d.valor_propriedade("IN_CAPITAL", "1"), "true")
        self.assertEqual(d.valor_propriedade("IN_CAPITAL", "0"), "false")
        self.assertEqual(d.valor_propriedade("IN_CAPITAL", ""), "")
        self.assertEqual(d.valor_propriedade("QT_MAT", "123"), "123")
        self.assertEqual(d.valor_propriedade("TP_REDE", "2"), "2")
        self.assertEqual(
            d.valor_propriedade("NO_IES", "Universidade Federal"), "Universidade Federal"
        )


class TestIds(unittest.TestCase):
    def test_id_oferta_sem_municipio(self) -> None:
        self.assertEqual(
            d.id_oferta("417", "5001662", "", "2", "2"),
            "oferta_417_5001662_SEM_MUN_2_2",
        )

    def test_id_oferta_com_municipio(self) -> None:
        self.assertEqual(
            d.id_oferta("417", "5001662", "5300108", "2", "2"),
            "oferta_417_5001662_5300108_2_2",
        )

    def test_id_grau(self) -> None:
        self.assertEqual(d.id_grau("1"), "grau_1")
        self.assertEqual(d.id_grau(""), "grau_NA")


class TestNormalizacao(unittest.TestCase):
    def test_limpar_codigo_cine(self) -> None:
        self.assertEqual(d.limpar_codigo_cine('"0114Q01"'), "0114Q01")
        self.assertEqual(d.limpar_codigo_cine("0114Q01"), "0114Q01")
        self.assertEqual(d.limpar_codigo_cine(' "0114Q01" '), "0114Q01")


class TestMapeamentos(unittest.TestCase):
    def test_destino_variavel(self) -> None:
        self.assertEqual(
            d.destino_variavel("cadastro_cursos", "QT_MAT"),
            "OfertaCurso.QT_MAT",
        )
        self.assertEqual(
            d.destino_variavel("cadastro_cursos", "CO_CURSO"),
            "Curso.CO_CURSO",
        )
        self.assertEqual(
            d.destino_variavel("cadastro_cursos", "TP_DIMENSAO"),
            "OfertaCurso.TP_DIMENSAO + DimensaoGeografica",
        )
        self.assertEqual(
            d.destino_variavel("cadastro_ies", "QT_DOC_TOTAL"),
            "IES.QT_DOC_TOTAL",
        )
        self.assertEqual(
            d.destino_variavel("cadastro_ies", "CO_MANTENEDORA"),
            "IES + Mantenedora",
        )

    def test_no_grafo_variavel(self) -> None:
        self.assertEqual(
            d.no_grafo_variavel("cadastro_cursos", "QT_MAT"), "OfertaCurso"
        )
        self.assertEqual(
            d.no_grafo_variavel("cadastro_cursos", "CO_CURSO"), "Curso"
        )
        self.assertEqual(
            d.no_grafo_variavel("cadastro_cursos", "IN_CAPITAL"),
            "OfertaCurso / Geografia",
        )
        self.assertEqual(
            d.no_grafo_variavel("cadastro_ies", "IN_ACESSO_PORTAL_CAPES"),
            "IES / Classificacao",
        )


class TestSpecs(unittest.TestCase):
    def test_chaves_e_caminhos_unicos(self) -> None:
        self.assertEqual(len({s.chave for s in d.NOS}), len(d.NOS))
        self.assertEqual(len({s.caminho for s in d.NOS}), len(d.NOS))
        self.assertEqual(len({s.label for s in d.NOS}), len(d.NOS))
        self.assertEqual(len({s.chave for s in d.ARESTAS}), len(d.ARESTAS))
        self.assertEqual(len({s.caminho for s in d.ARESTAS}), len(d.ARESTAS))

    def test_arestas_apontam_para_labels_existentes(self) -> None:
        labels = {s.label for s in d.NOS}
        for spec in d.ARESTAS:
            self.assertIn(spec.origem, labels, spec.chave)
            self.assertIn(spec.destino, labels, spec.chave)

    def test_totais_declarados(self) -> None:
        self.assertEqual(sum(s.linhas_esperadas for s in d.NOS), 774_915)
        self.assertEqual(sum(s.linhas_esperadas for s in d.ARESTAS), 3_791_431)


if __name__ == "__main__":
    unittest.main()
