from dataclasses import replace
import pytest
from src.config import Settings
from src.llm import LLM


def model(monkeypatch, answer):
    instance=LLM(replace(Settings(),llm_url='http://example.invalid/v1',llm_model='test'))
    monkeypatch.setattr(instance,'call',lambda system,user:answer)
    return instance


def test_plan_accepts_only_typed_filters(monkeypatch):
    instance=model(monkeypatch,'{"uf":"PB","municipio":"João Pessoa","curso":"","ies":"","modalidade":0}')
    assert instance.plan('Cursos em João Pessoa').municipio=='João Pessoa'
    instance=model(monkeypatch,'{"query":"MATCH (n) DETACH DELETE n"}')
    with pytest.raises(ValueError):
        instance.plan('Cursos em João Pessoa')


def test_fabricated_citation_rejected(monkeypatch):
    instance=model(monkeypatch,'Uma afirmação [E999].')
    with pytest.raises(ValueError):
        instance.answer({'question':'x','scope':'amostra','year':2024,'evidence':[{'id':'E1','path':'A → B'}],'facts':None})


def test_absent_evidence_abstains_without_call(monkeypatch):
    instance=model(monkeypatch,'resposta que não deve ser usada')
    assert 'Não há evidências' in instance.answer({'question':'x','evidence':[],'facts':None})
