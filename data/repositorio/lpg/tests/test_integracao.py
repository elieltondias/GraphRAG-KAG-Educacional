#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste de integração do build parcial e do conversor genérico."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "lpg" / "scripts"
BASE = REPO_ROOT / "microdados_censo_da_educacao_superior_2024"
BUILD = SCRIPTS / "construir_lpg.py"
CONVERTER = SCRIPTS / "converter_para_generico.py"


def contar_linhas(caminho: Path) -> int:
    with caminho.open(encoding="utf-8") as arquivo:
        return sum(1 for _ in arquivo) - 1


def ler_header(caminho: Path) -> list[str]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return next(csv.reader(arquivo, delimiter=","))


@unittest.skipUnless(BASE.exists(), "microdados não encontrados")
class TestBuildParcial(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.saida = Path(cls.tmp.name) / "grafo"
        result = subprocess.run(
            [
                sys.executable,
                str(BUILD),
                "--base",
                str(BASE),
                "--saida",
                str(cls.saida),
                "--limite",
                "1000",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"build falhou:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        cls.stdout = result.stdout

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_manifesto(self) -> None:
        manifesto = json.loads((self.saida / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifesto["resumo"]["linhas_curso_lidas"], 1000)
        self.assertEqual(manifesto["resumo"]["ofertas_unicas"], 1000)
        self.assertEqual(manifesto["resumo"]["ies_unicas"], 2561)
        self.assertEqual(manifesto["totais"]["arquivos_nos"], 18)
        self.assertEqual(manifesto["totais"]["arquivos_arestas"], 19)

    def test_contagens_parciais(self) -> None:
        self.assertEqual(
            contar_linhas(self.saida / "nos/academico/oferta_curso.csv"), 1000
        )
        self.assertEqual(
            contar_linhas(self.saida / "nos/institucional/ies.csv"), 2561
        )
        self.assertGreater(
            contar_linhas(self.saida / "nos/classificacoes/modalidade_ensino.csv"),
            0,
        )
        self.assertGreater(
            contar_linhas(self.saida / "nos/classificacoes/dimensao_geografica.csv"),
            0,
        )

    def test_cabecalhos_tipados(self) -> None:
        header = ler_header(self.saida / "nos/academico/oferta_curso.csv")
        self.assertEqual(header[:3], [":ID", ":LABEL", "NU_ANO_CENSO:int"])
        self.assertIn("QT_MAT:long", header)
        self.assertIn("IN_CAPITAL:boolean", header)
        self.assertEqual(
            ler_header(self.saida / "arestas/academico/oferta_curso_oferta_de.csv"),
            [":START_ID", ":END_ID", ":TYPE"],
        )

    def test_schema_e_dicionario(self) -> None:
        dicionario = self.saida / "schema/dicionario_variaveis.csv"
        self.assertTrue(dicionario.exists())
        self.assertEqual(contar_linhas(dicionario), 307)

    def test_conversor_generico(self) -> None:
        destino = self.saida / "generico"
        result = subprocess.run(
            [
                sys.executable,
                str(CONVERTER),
                "--origem",
                str(self.saida),
                "--destino",
                str(destino),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        header = ler_header(destino / "nos/academico/oferta_curso.csv")
        self.assertEqual(header[:2], ["id", "label"])
        self.assertEqual(
            ler_header(destino / "arestas/academico/oferta_curso_oferta_de.csv"),
            ["source", "target", "type"],
        )


if __name__ == "__main__":
    unittest.main()
